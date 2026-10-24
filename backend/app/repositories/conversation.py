"""Repository for Conversations, Messages, and LLMRun persistence."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError, NotFoundError
from app.models.chat import Conversation, LLMRun, Message

logger = logging.getLogger("verifai.repositories.conversation")


class ConversationRepository:
    """Persistence manager for conversations, messages, and model runs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_conversation(
        self,
        owner_id: str,
        title: str,
    ) -> Conversation:
        """Create a new conversation thread."""
        now = datetime.now(UTC)
        conv = Conversation(
            id=uuid.uuid4(),
            owner_id=owner_id,
            title=title.strip(),
            created_at=now,
            updated_at=now,
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: str | None = None,
        load_messages: bool = False,
    ) -> Conversation | None:
        """Retrieve conversation by ID, asserting owner_id and loading messages."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        if load_messages:
            stmt = stmt.options(selectinload(Conversation.messages))

        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv:
            return None

        if owner_id is not None and conv.owner_id != owner_id:
            raise ForbiddenError(
                message="Access denied to conversation.",
                details={"conversation_id": str(conversation_id)},
            )
        return conv

    async def list_conversations(
        self,
        owner_id: str,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """List conversations owned by user with pagination and search."""
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        query = select(Conversation).where(Conversation.owner_id == owner_id)
        if search:
            query = query.where(Conversation.title.ilike(f"%{search.strip()}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        query = (
            query.order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
    ) -> bool:
        """Delete a conversation thread and cascade its messages and runs."""
        conv = await self.get_conversation(conversation_id, owner_id=owner_id)
        if not conv:
            return False

        await self.session.delete(conv)
        await self.session.commit()
        return True

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
        role: str,
        content: str,
        metadata_json: dict | None = None,
    ) -> Message:
        """Append message to conversation thread with auto-increment sequence."""
        conv = await self.get_conversation(conversation_id, owner_id=owner_id)
        if not conv:
            raise NotFoundError(
                message="Conversation not found.",
                details={"conversation_id": str(conversation_id)},
            )

        # Compute next sequence number
        seq_stmt = select(func.coalesce(func.max(Message.sequence_number), 0)).where(
            Message.conversation_id == conversation_id
        )
        max_seq = (await self.session.execute(seq_stmt)).scalar_one()
        next_seq = max_seq + 1

        now = datetime.now(UTC)
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            owner_id=owner_id,
            role=role,
            content=content,
            sequence_number=next_seq,
            token_count=len(content.split()),
            metadata_json=metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        self.session.add(msg)

        # Update parent conversation timestamp
        conv.updated_at = now

        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def list_messages(
        self,
        conversation_id: uuid.UUID,
        owner_id: str,
    ) -> list[Message]:
        """List messages in a conversation ordered by sequence number."""
        await self.get_conversation(conversation_id, owner_id=owner_id)

        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.owner_id == owner_id,
            )
            .order_by(Message.sequence_number.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def record_llm_run(self, run: LLMRun) -> LLMRun:
        """Persist an LLMRun execution record."""
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run
