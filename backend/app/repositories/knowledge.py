"""Repository for KnowledgeDocument and KnowledgeChunk persistence."""

import logging
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger("verifai.repositories.knowledge")


class KnowledgeRepository:
    """Manages database persistence and queries for knowledge documents and chunks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_document(
        self,
        document: KnowledgeDocument,
        chunks: list[KnowledgeChunk],
    ) -> KnowledgeDocument:
        """Persist a new knowledge document and its chunks atomically."""
        self.session.add(document)
        self.session.add_all(chunks)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_document_by_id(
        self,
        document_id: uuid.UUID,
        owner_id: str | None = None,
        load_chunks: bool = False,
    ) -> KnowledgeDocument | None:
        """Retrieve document by ID, asserting ownership if owner_id is provided."""
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        if load_chunks:
            stmt = stmt.options(selectinload(KnowledgeDocument.chunks))

        result = await self.session.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            return None

        if owner_id is not None and doc.owner_id != owner_id:
            raise ForbiddenError(
                message="Access denied to document.",
                details={"document_id": str(document_id)},
            )
        return doc

    async def get_document_by_hash(
        self,
        owner_id: str,
        content_hash: str,
    ) -> KnowledgeDocument | None:
        """Find an existing document by its content SHA-256 hash in a namespace."""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.owner_id == owner_id,
            KnowledgeDocument.content_hash == content_hash,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_documents(
        self,
        owner_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[KnowledgeDocument], int]:
        """List documents owned by the user with pagination."""
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        count_stmt = select(func.count()).where(KnowledgeDocument.owner_id == owner_id)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.owner_id == owner_id)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def delete_document(
        self,
        document_id: uuid.UUID,
        owner_id: str,
    ) -> bool:
        """Delete a document and cascade its chunks."""
        doc = await self.get_document_by_id(document_id, owner_id=owner_id)
        if not doc:
            return False

        # Cascade chunks explicitly
        await self.session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
        )
        await self.session.delete(doc)
        await self.session.commit()
        return True

    async def get_chunks_for_document(
        self,
        document_id: uuid.UUID,
        owner_id: str,
    ) -> list[KnowledgeChunk]:
        """Retrieve all chunks belonging to a document."""
        await self.get_document_by_id(document_id, owner_id=owner_id)

        stmt = (
            select(KnowledgeChunk)
            .where(
                KnowledgeChunk.document_id == document_id,
                KnowledgeChunk.owner_id == owner_id,
            )
            .order_by(KnowledgeChunk.chunk_index.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_chunks_for_owner(
        self,
        owner_id: str,
    ) -> list[KnowledgeChunk]:
        """Retrieve all chunks across all documents owned by user."""
        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.owner_id == owner_id)
            .order_by(KnowledgeChunk.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
