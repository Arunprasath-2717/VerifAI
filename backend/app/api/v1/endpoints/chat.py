"""Chat, multi-LLM, and real-time SSE streaming API endpoints."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_optional_current_user,
    get_async_session,
    resolve_effective_owner,
)
from app.core.rate_limit import enforce_rate_limit
from app.models.user import User
from app.modules.chat.service import ChatService
from app.schemas.chat import (
    ChatPromptRequest,
    ChatPromptResponse,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
)

logger = logging.getLogger("verifai.api.chat")

router = APIRouter(prefix="/chat", tags=["Chat & Multi-LLM"])


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation thread",
)
async def create_conversation(
    request_data: ConversationCreateRequest,
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> ConversationResponse:
    """Create a new conversation owned by the authenticated caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="chat_create",
            limit=30,
            user_id=effective_owner,
            settings=settings,
        )

    service = ChatService(db_session=db, settings=settings)
    conv = await service.create_conversation(
        owner_id=effective_owner, request=request_data
    )

    return ConversationResponse(
        id=conv.id,
        owner_id=conv.owner_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations owned by authenticated user",
)
async def list_conversations(
    search: str | None = Query(
        default=None, description="Search term in conversation title"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> ConversationListResponse:
    """List conversations for the current user with pagination and search."""
    effective_owner = resolve_effective_owner(current_user, None, settings)
    service = ChatService(db_session=db, settings=settings)
    items, total = await service.list_conversations(
        owner_id=effective_owner,
        search=search,
        limit=limit,
        offset=offset,
    )

    return ConversationListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation detail with message history",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> ConversationDetailResponse:
    """Retrieve full conversation details and linked model runs."""
    effective_owner = resolve_effective_owner(current_user, None, settings)
    service = ChatService(db_session=db, settings=settings)
    return await service.get_conversation(
        conversation_id=conversation_id,
        owner_id=effective_owner,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation and all messages",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Delete a conversation thread and all cascaded children."""
    effective_owner = resolve_effective_owner(current_user, None, settings)
    service = ChatService(db_session=db, settings=settings)
    deleted = await service.delete_conversation(
        conversation_id=conversation_id,
        owner_id=effective_owner,
    )
    return {"deleted": deleted, "conversation_id": str(conversation_id)}


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatPromptResponse,
    summary="Submit prompt to 1–3 models and verify responses",
)
async def send_prompt(
    conversation_id: uuid.UUID,
    request_data: ChatPromptRequest,
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> ChatPromptResponse:
    """Dispatch user prompt to up to 3 selected LLMs, run verification, and record."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="chat_message",
            limit=20,
            user_id=effective_owner,
            settings=settings,
        )

    service = ChatService(db_session=db, settings=settings)
    return await service.process_prompt(
        conversation_id=conversation_id,
        owner_id=effective_owner,
        request=request_data,
    )


@router.post(
    "/conversations/{conversation_id}/messages/stream",
    summary="Stream real-time model execution and verification events via SSE",
)
async def stream_prompt(
    conversation_id: uuid.UUID,
    request_data: ChatPromptRequest,
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Stream truthful execution lifecycle events to the frontend via SSE."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="chat_message",
            limit=20,
            user_id=effective_owner,
            settings=settings,
        )

    service = ChatService(db_session=db, settings=settings)

    async def _event_generator() -> AsyncGenerator[str, None]:
        # Event 1: REQUEST_ACCEPTED
        accepted_payload = {
            "conversation_id": str(conversation_id),
            "models": [m.model_name for m in request_data.models],
        }
        yield f"event: REQUEST_ACCEPTED\ndata: {json.dumps(accepted_payload)}\n\n"

        for m in request_data.models:
            # Event 2: MODEL_REQUEST_STARTED
            started_payload = {"provider": m.provider, "model": m.model_name}
            yield (
                f"event: MODEL_REQUEST_STARTED\ndata: {json.dumps(started_payload)}\n\n"
            )

        # Execute prompt via service
        prompt_res = await service.process_prompt(
            conversation_id=conversation_id,
            owner_id=effective_owner,
            request=request_data,
        )

        for run in prompt_res.runs:
            if run.status == "COMPLETED":
                run_payload = {
                    "provider": run.provider,
                    "model": run.model_name,
                    "latency_ms": run.latency_ms,
                    "status": run.status,
                }
                yield (
                    f"event: MODEL_RESPONSE_COMPLETED\n"
                    f"data: {json.dumps(run_payload)}\n\n"
                )
            else:
                fail_payload = {
                    "provider": run.provider,
                    "model": run.model_name,
                    "status": run.status,
                    "error_code": run.error_code,
                    "error_message": run.error_message,
                }
                yield (f"event: MODEL_FAILED\ndata: {json.dumps(fail_payload)}\n\n")

        if request_data.verify:
            verif_payload = {
                "cross_model_disagreement": prompt_res.cross_model_disagreement,
                "disagreement_summary": prompt_res.disagreement_summary,
            }
            yield (
                f"event: VERIFICATION_COMPLETED\ndata: {json.dumps(verif_payload)}\n\n"
            )

        # Final COMPLETE event
        complete_payload = {
            "conversation_id": str(conversation_id),
            "run_count": len(prompt_res.runs),
        }
        yield f"event: COMPLETE\ndata: {json.dumps(complete_payload)}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
