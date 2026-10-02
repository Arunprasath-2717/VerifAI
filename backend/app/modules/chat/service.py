"""Chat and Multi-LLM conversation service.

Provides dual persistence (PostgreSQL / In-Memory).
"""

import logging
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.errors import ForbiddenError, NotFoundError
from app.models.chat import Conversation, LLMRun, Message
from app.modules.llm.service import MultiLLMOrchestrator
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.chat import (
    ChatPromptRequest,
    ChatPromptResponse,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    LLMRunResponse,
    MessageResponse,
)
from app.schemas.verification import (
    VerdictType,
    VerificationCreateRequest,
    VerificationOptions,
    VerificationResponse,
)

logger = logging.getLogger("verifai.chat.service")

# ==============================================================================
# In-Memory Fallback Stores for Ephemeral / Hermetic Environments
# ==============================================================================
_EPHEMERAL_CONVERSATIONS: dict[str, dict[uuid.UUID, Conversation]] = defaultdict(dict)
_EPHEMERAL_MESSAGES: dict[uuid.UUID, list[Message]] = defaultdict(list)
_EPHEMERAL_LLM_RUNS: dict[uuid.UUID, list[LLMRun]] = defaultdict(list)


def clear_ephemeral_chat() -> None:
    """Reset all in-memory chat and conversation state."""
    _EPHEMERAL_CONVERSATIONS.clear()
    _EPHEMERAL_MESSAGES.clear()
    _EPHEMERAL_LLM_RUNS.clear()


class ChatService:
    """Manages conversations, messages, multi-LLM runs, and linked verifications."""

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        settings: Settings | None = None,
        llm_orchestrator: MultiLLMOrchestrator | None = None,
        verification_orchestrator: VerificationOrchestrator | None = None,
    ) -> None:
        self.db = db_session
        self.settings = settings or get_settings()
        self.llm_orchestrator = llm_orchestrator or MultiLLMOrchestrator(
            settings=self.settings
        )
        self.verification_orchestrator = (
            verification_orchestrator or VerificationOrchestrator()
        )

    # ==========================================================================
    # Conversation Lifecycle
    # ==========================================================================
    async def create_conversation(
        self,
        owner_id: str,
        request: ConversationCreateRequest,
    ) -> Conversation:
        """Create a new conversation thread owned by owner_id."""
        conv = Conversation(
            id=uuid.uuid4(),
            owner_id=owner_id,
            title=request.title.strip(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        if self.db is not None:
            self.db.add(conv)
            await self.db.commit()
            await self.db.refresh(conv)
        else:
            _EPHEMERAL_CONVERSATIONS[owner_id][conv.id] = conv

        logger.info("Created conversation %s for owner %s", conv.id, owner_id)
        return conv

    async def list_conversations(
        self,
        owner_id: str,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ConversationResponse], int]:
        """List conversations owned by user with pagination and optional search."""
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        if self.db is not None:
            query = select(Conversation).where(Conversation.owner_id == owner_id)
            if search:
                query = query.where(Conversation.title.ilike(f"%{search.strip()}%"))

            count_query = select(func.count()).select_from(query.subquery())
            total = (await self.db.execute(count_query)).scalar_one()

            query = (
                query.options(selectinload(Conversation.messages))
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .offset(offset)
            )
            rows = (await self.db.execute(query)).scalars().all()

            items = [
                ConversationResponse(
                    id=c.id,
                    owner_id=c.owner_id,
                    title=c.title,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=len(c.messages) if c.messages else 0,
                )
                for c in rows
            ]
            return items, total
        else:
            user_convs = list(_EPHEMERAL_CONVERSATIONS.get(owner_id, {}).values())
            if search:
                s_lower = search.strip().lower()
                user_convs = [c for c in user_convs if s_lower in c.title.lower()]

            user_convs.sort(key=lambda c: c.updated_at, reverse=True)
            total = len(user_convs)
            paged = user_convs[offset : offset + limit]

            items = [
                ConversationResponse(
                    id=c.id,
                    owner_id=c.owner_id,
                    title=c.title,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=len(_EPHEMERAL_MESSAGES.get(c.id, [])),
                )
                for c in paged
            ]
            return items, total

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
    ) -> ConversationDetailResponse:
        """Fetch conversation details and messages, enforcing ownership."""
        if self.db is not None:
            query = (
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(
                    selectinload(Conversation.messages).selectinload(Message.llm_runs)
                )
            )
            conv = (await self.db.execute(query)).scalar_one_or_none()
            if not conv:
                raise NotFoundError(
                    message=f"Conversation '{conversation_id}' not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.owner_id != owner_id:
                raise ForbiddenError(
                    message="Access denied: You do not own this conversation.",
                    details={"conversation_id": str(conversation_id)},
                )

            messages_out = [
                MessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    owner_id=m.owner_id,
                    role=m.role,
                    content=m.content,
                    sequence_number=m.sequence_number,
                    created_at=m.created_at,
                    llm_runs=[
                        LLMRunResponse(
                            id=r.id,
                            conversation_id=r.conversation_id,
                            message_id=r.message_id,
                            owner_id=r.owner_id,
                            provider=r.provider,
                            model_name=r.model_name,
                            model_version=r.model_version,
                            prompt=r.prompt,
                            response=r.response,
                            status=r.status,
                            started_at=r.started_at,
                            completed_at=r.completed_at,
                            latency_ms=r.latency_ms,
                            error_code=r.error_code,
                            error_message=r.error_message,
                        )
                        for r in (m.llm_runs or [])
                    ],
                )
                for m in conv.messages
            ]

            return ConversationDetailResponse(
                id=conv.id,
                owner_id=conv.owner_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                messages=messages_out,
            )
        else:
            conv = _EPHEMERAL_CONVERSATIONS.get(owner_id, {}).get(conversation_id)
            if not conv:
                for _other_owner, convs in _EPHEMERAL_CONVERSATIONS.items():
                    if conversation_id in convs:
                        raise ForbiddenError(
                            message="Access denied: You do not own this conversation.",
                            details={"conversation_id": str(conversation_id)},
                        )
                raise NotFoundError(
                    message=f"Conversation '{conversation_id}' not found.",
                    details={"conversation_id": str(conversation_id)},
                )

            raw_msgs = _EPHEMERAL_MESSAGES.get(conversation_id, [])
            messages_out = []
            for m in raw_msgs:
                runs = _EPHEMERAL_LLM_RUNS.get(m.id, [])
                messages_out.append(
                    MessageResponse(
                        id=m.id,
                        conversation_id=m.conversation_id,
                        owner_id=m.owner_id,
                        role=m.role,
                        content=m.content,
                        sequence_number=m.sequence_number,
                        created_at=m.created_at,
                        llm_runs=[
                            LLMRunResponse(
                                id=r.id,
                                conversation_id=r.conversation_id,
                                message_id=r.message_id,
                                owner_id=r.owner_id,
                                provider=r.provider,
                                model_name=r.model_name,
                                model_version=r.model_version,
                                prompt=r.prompt,
                                response=r.response,
                                status=r.status,
                                started_at=r.started_at,
                                completed_at=r.completed_at,
                                latency_ms=r.latency_ms,
                                error_code=r.error_code,
                                error_message=r.error_message,
                            )
                            for r in runs
                        ],
                    )
                )

            return ConversationDetailResponse(
                id=conv.id,
                owner_id=conv.owner_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                messages=messages_out,
            )

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
    ) -> bool:
        """Delete conversation and all linked messages and runs."""
        if self.db is not None:
            conv = (
                await self.db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
            ).scalar_one_or_none()
            if not conv:
                raise NotFoundError(
                    message=f"Conversation '{conversation_id}' not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.owner_id != owner_id:
                raise ForbiddenError(
                    message=(
                        "Access denied: You cannot delete another user's conversation."
                    ),
                    details={"conversation_id": str(conversation_id)},
                )
            await self.db.delete(conv)
            await self.db.commit()
            return True
        else:
            if conversation_id not in _EPHEMERAL_CONVERSATIONS.get(owner_id, {}):
                for _other_owner, convs in _EPHEMERAL_CONVERSATIONS.items():
                    if conversation_id in convs:
                        raise ForbiddenError(
                            message=(
                                "Access denied: You cannot delete another user's "
                                "conversation."
                            ),
                            details={"conversation_id": str(conversation_id)},
                        )
                raise NotFoundError(
                    message=f"Conversation '{conversation_id}' not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            _EPHEMERAL_CONVERSATIONS[owner_id].pop(conversation_id, None)
            msgs = _EPHEMERAL_MESSAGES.pop(conversation_id, [])
            for m in msgs:
                _EPHEMERAL_LLM_RUNS.pop(m.id, None)
            return True

    # ==========================================================================
    # Multi-LLM Execution & Verification Pipeline
    # ==========================================================================
    async def process_prompt(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
        request: ChatPromptRequest,
    ) -> ChatPromptResponse:
        """Execute prompt against 1 to 3 models, run verification, and persist."""
        # 1. Verify conversation ownership
        if self.db is not None:
            conv = (
                await self.db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
            ).scalar_one_or_none()
            if not conv:
                raise NotFoundError(
                    message=f"Conversation '{conversation_id}' not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.owner_id != owner_id:
                raise ForbiddenError(
                    message=(
                        "Access denied: Cannot post to another user's conversation."
                    ),
                    details={"conversation_id": str(conversation_id)},
                )
        else:
            if conversation_id not in _EPHEMERAL_CONVERSATIONS.get(owner_id, {}):
                for _other_owner, convs in _EPHEMERAL_CONVERSATIONS.items():
                    if conversation_id in convs:
                        raise ForbiddenError(
                            message=(
                                "Access denied: Cannot post to another user's "
                                "conversation."
                            ),
                            details={"conversation_id": str(conversation_id)},
                        )
                raise NotFoundError(
                    message=f"Conversation '{conversation_id}' not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            conv = _EPHEMERAL_CONVERSATIONS[owner_id][conversation_id]

        # 2. Record User Message
        user_msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            owner_id=owner_id,
            role="USER",
            content=request.prompt,
            sequence_number=1,
            created_at=datetime.now(UTC),
        )

        if self.db is not None:
            # Determine next sequence number
            seq_stmt = select(
                func.coalesce(func.max(Message.sequence_number), 0)
            ).where(Message.conversation_id == conversation_id)
            max_seq = (await self.db.execute(seq_stmt)).scalar_one()
            user_msg.sequence_number = max_seq + 1
            self.db.add(user_msg)
            conv.updated_at = datetime.now(UTC)
            await self.db.flush()
        else:
            existing_msgs = _EPHEMERAL_MESSAGES[conversation_id]
            user_msg.sequence_number = len(existing_msgs) + 1
            existing_msgs.append(user_msg)
            conv.updated_at = datetime.now(UTC)

        # 3. Parallel Execution across 1 to 3 models
        exec_results = await self.llm_orchestrator.execute_models(
            prompt=request.prompt,
            models=request.models,
        )

        # 4. Process each model result and run shared verification engine
        runs_out: list[LLMRunResponse] = []
        assistant_contents: list[str] = []
        model_verdicts: dict[str, list[str]] = defaultdict(list)

        for res in exec_results:
            run_id = uuid.uuid4()
            verification_resp: VerificationResponse | None = None
            verification_id: uuid.UUID | None = None

            # Shared Verification Engine invocation
            if res.status == "COMPLETED" and res.response and request.verify:
                assistant_contents.append(res.response)
                v_options = request.options or VerificationOptions()
                v_options.owner_id = owner_id

                v_req = VerificationCreateRequest(
                    text=res.response,
                    query=request.prompt,
                    options=v_options,
                )
                try:
                    verification_resp = await self.verification_orchestrator.verify(
                        request=v_req,
                        db_session=self.db,
                    )
                    verification_id = uuid.UUID(str(verification_resp.verification_id))
                    for c in verification_resp.claims:
                        if c.verdict is not None:
                            model_verdicts[res.model_name].append(
                                c.verdict.value
                                if hasattr(c.verdict, "value")
                                else str(c.verdict)
                            )
                except Exception as v_err:
                    logger.warning(
                        "Verification error on model '%s': %s", res.model_name, v_err
                    )

            llm_run_db = LLMRun(
                id=run_id,
                conversation_id=conversation_id,
                message_id=user_msg.id,
                owner_id=owner_id,
                provider=res.provider,
                model_name=res.model_name,
                model_version=res.model_version,
                prompt=res.prompt,
                response=res.response,
                status=res.status,
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                latency_ms=res.latency_ms,
                error_code=res.error_code,
                error_message=res.error_message,
                verification_id=verification_id,
            )

            if self.db is not None:
                self.db.add(llm_run_db)
            else:
                _EPHEMERAL_LLM_RUNS[user_msg.id].append(llm_run_db)

            runs_out.append(
                LLMRunResponse(
                    id=run_id,
                    conversation_id=conversation_id,
                    message_id=user_msg.id,
                    owner_id=owner_id,
                    provider=res.provider,
                    model_name=res.model_name,
                    model_version=res.model_version,
                    prompt=res.prompt,
                    response=res.response,
                    status=res.status,
                    started_at=llm_run_db.started_at,
                    completed_at=llm_run_db.completed_at,
                    latency_ms=res.latency_ms,
                    error_code=res.error_code,
                    error_message=res.error_message,
                    verification=verification_resp,
                )
            )

        # 5. Cross-Model Disagreement Analysis
        cross_disagreement = False
        disagreement_summary: str | None = None
        if len(model_verdicts) >= 2:
            all_verdicts = set()
            for v_list in model_verdicts.values():
                all_verdicts.update(v_list)
            if (
                VerdictType.SUPPORTED.value in all_verdicts
                and VerdictType.CONTRADICTED.value in all_verdicts
            ):
                cross_disagreement = True
                disagreement_summary = (
                    "Cross-generation discrepancy detected: Evaluated models produced "
                    "conflicting factual propositions (one or more asserted "
                    "contradictions)."
                )

        if self.db is not None:
            await self.db.commit()

        return ChatPromptResponse(
            conversation_id=conversation_id,
            user_message_id=user_msg.id,
            prompt=request.prompt,
            runs=runs_out,
            cross_model_disagreement=cross_disagreement,
            disagreement_summary=disagreement_summary,
        )
