"""Chat and Multi-LLM conversation service.

Architecture: A real database session (PostgreSQL) is required for all operations.
There is no in-memory ephemeral fallback. Data is durable across restarts.
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


class ChatService:
    """Manages conversations, messages, multi-LLM runs, and linked verifications.

    Requires a valid AsyncSession — all state is persisted to PostgreSQL.
    """

    def __init__(
        self,
        db_session: AsyncSession,
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

        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)

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

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
    ) -> ConversationDetailResponse:
        """Fetch conversation details and messages, enforcing ownership."""
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

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
    ) -> bool:
        """Delete conversation and all linked messages and runs (cascade via FK)."""
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
                message="Access denied: You cannot delete another user's conversation.",
                details={"conversation_id": str(conversation_id)},
            )
        await self.db.delete(conv)
        await self.db.commit()
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
                message="Access denied: Cannot post to another user's conversation.",
                details={"conversation_id": str(conversation_id)},
            )

        # 2. Determine next sequence number and record User Message
        seq_stmt = select(
            func.coalesce(func.max(Message.sequence_number), 0)
        ).where(Message.conversation_id == conversation_id)
        max_seq = (await self.db.execute(seq_stmt)).scalar_one()

        user_msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            owner_id=owner_id,
            role="USER",
            content=request.prompt,
            sequence_number=max_seq + 1,
            created_at=datetime.now(UTC),
        )
        self.db.add(user_msg)
        conv.updated_at = datetime.now(UTC)
        await self.db.flush()

        # 3. Parallel Execution across 1 to 3 models
        exec_results = await self.llm_orchestrator.execute_models(
            prompt=request.prompt,
            models=request.models,
        )

        # 4. Process each model result and run shared verification engine
        runs_out: list[LLMRunResponse] = []
        model_verdicts: dict[str, list[str]] = defaultdict(list)

        for res in exec_results:
            run_id = uuid.uuid4()
            verification_resp: VerificationResponse | None = None
            verification_id: uuid.UUID | None = None

            # Shared Verification Engine invocation
            if res.status == "COMPLETED" and res.response and request.verify:
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
            self.db.add(llm_run_db)

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

        await self.db.commit()

        return ChatPromptResponse(
            conversation_id=conversation_id,
            user_message_id=user_msg.id,
            prompt=request.prompt,
            runs=runs_out,
            cross_model_disagreement=cross_disagreement,
            disagreement_summary=disagreement_summary,
        )


def clear_ephemeral_chat() -> None:
    """Clear chat tables for testing and teardowns."""
    import asyncio
    import concurrent.futures

    from sqlalchemy import delete

    from app.core.database import get_async_session_maker
    from app.models.chat import Conversation, LLMRun, Message

    async def _clean() -> None:
        maker = get_async_session_maker()
        async with maker() as session:
            await session.execute(delete(LLMRun))
            await session.execute(delete(Message))
            await session.execute(delete(Conversation))
            await session.commit()

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, _clean()).result()
        else:
            asyncio.run(_clean())
    except Exception:
        pass


