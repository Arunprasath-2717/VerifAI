"""Knowledge Base service for namespace-isolated document storage and management.

Architecture: A real database session is required. There is no in-memory ephemeral
fallback in production paths. For tests, use a real test DB or SQLite (aiosqlite).
"""

import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.ingestion import (
    DuplicateDocumentError,
    process_document_ingestion,
)

logger = logging.getLogger("verifai.knowledge.service")


def resolve_owner_id(owner_id: str | None, settings: Settings | None = None) -> str:
    """Resolve owner/namespace ID with explicit development mode gating.

    In development/testing, falls back to settings.DEFAULT_OWNER_ID.
    In production, strictly requires an explicit owner/namespace identifier.
    """
    app_settings = settings or get_settings()

    if owner_id and owner_id.strip():
        return owner_id.strip()

    is_dev = (
        app_settings.ENVIRONMENT in ("development", "test", "testing")
        or app_settings.DEBUG
    )
    if is_dev:
        return app_settings.DEFAULT_OWNER_ID

    raise ValueError(
        "Namespace/owner ID is strictly required in production environments. "
        "Anonymous or unauthenticated access is forbidden."
    )


class KnowledgeBaseService:
    """Namespace-isolated document lifecycle management service.

    Requires a valid AsyncSession connected to PostgreSQL, or creates one
    via the session factory. All operations are persisted to the database —
    there is no in-memory fallback.
    """

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.db = db_session
        self.settings = settings or get_settings()

    @asynccontextmanager
    async def _session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.db is not None:
            yield self.db
        else:
            from app.core.database import get_async_session_maker

            maker = get_async_session_maker()
            async with maker() as session:
                yield session

    async def add_document(
        self,
        raw_content: bytes | str,
        filename: str,
        title: str | None = None,
        description: str | None = None,
        content_type: str | None = None,
        owner_id: str | None = None,
    ) -> KnowledgeDocument:
        """Ingest, validate, chunk, and store a new document in the owner namespace."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        # 1. Run ingestion pipeline (validates type, size, bounds, chunks)
        ingestion = process_document_ingestion(
            raw_content=raw_content,
            filename=filename,
            title=title,
            content_type=content_type,
            max_bytes=self.settings.KB_MAX_DOCUMENT_BYTES,
        )

        async with self._session() as session:
            # 2. Check for duplicate document within the same owner namespace
            dup_stmt = select(KnowledgeDocument).where(
                KnowledgeDocument.owner_id == effective_owner,
                KnowledgeDocument.content_hash == ingestion.content_hash,
            )
            dup_res = await session.execute(dup_stmt)
            if dup_res.scalars().first() is not None:
                raise DuplicateDocumentError(
                    "Document with identical content already exists in namespace "
                    f"'{effective_owner}'."
                )

            # 3. Create document entity
            now = datetime.now(UTC)
            doc = KnowledgeDocument(
                id=uuid.uuid4(),
                owner_id=effective_owner,
                filename=ingestion.filename,
                title=ingestion.title,
                description=description.strip() if description else None,
                content_type=ingestion.content_type,
                size_bytes=ingestion.size_bytes,
                content_hash=ingestion.content_hash,
                metadata_json=ingestion.metadata_json,
                created_at=now,
                updated_at=now,
            )
            session.add(doc)

            # 4. Create chunk entities
            for chunk_data in ingestion.chunks:
                chunk = KnowledgeChunk(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    owner_id=effective_owner,
                    chunk_index=chunk_data.chunk_index,
                    text=chunk_data.text,
                    start_offset=chunk_data.start_offset,
                    end_offset=chunk_data.end_offset,
                    metadata_json=chunk_data.metadata_json,
                    created_at=now,
                    updated_at=now,
                )
                doc.chunks.append(chunk)

            await session.flush()
            await session.commit()
            return doc

    async def list_documents(
        self,
        owner_id: str | None = None,
    ) -> list[KnowledgeDocument]:
        """List all knowledge documents strictly isolated to the specified owner."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        async with self._session() as session:
            stmt = (
                select(KnowledgeDocument)
                .where(KnowledgeDocument.owner_id == effective_owner)
                .options(selectinload(KnowledgeDocument.chunks))
                .order_by(KnowledgeDocument.created_at.desc())
            )
            res = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_document(
        self,
        document_id: uuid.UUID,
        owner_id: str | None = None,
    ) -> KnowledgeDocument:
        """Fetch a specific document with chunks, verifying ownership."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        async with self._session() as session:
            stmt = (
                select(KnowledgeDocument)
                .where(
                    KnowledgeDocument.id == document_id,
                    KnowledgeDocument.owner_id == effective_owner,
                )
                .options(selectinload(KnowledgeDocument.chunks))
            )
            res = await session.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                raise NotFoundError(
                    f"Document '{document_id}' not found in '{effective_owner}'."
                )
            return doc

    async def delete_document(
        self,
        document_id: uuid.UUID,
        owner_id: str | None = None,
    ) -> bool:
        """Delete a document and all its chunks from the owner's namespace."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        async with self._session() as session:
            # Check ownership before deletion
            stmt = select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.owner_id == effective_owner,
            )
            res = await session.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                raise NotFoundError(
                    f"Document '{document_id}' not found in '{effective_owner}'."
                )

            # Cascade delete removes chunks automatically via FK constraint
            del_stmt = delete(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.owner_id == effective_owner,
            )
            await session.execute(del_stmt)
            await session.commit()
            return True

    async def get_all_chunks_for_owner(
        self,
        owner_id: str | None = None,
    ) -> list[tuple[KnowledgeChunk, KnowledgeDocument]]:
        """Retrieve all active chunks and associated document metadata for an owner."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        async with self._session() as session:
            stmt = (
                select(KnowledgeChunk, KnowledgeDocument)
                .join(
                    KnowledgeDocument,
                    KnowledgeChunk.document_id == KnowledgeDocument.id,
                )
                .where(
                    KnowledgeChunk.owner_id == effective_owner,
                    KnowledgeDocument.owner_id == effective_owner,
                )
                .order_by(KnowledgeChunk.created_at.asc())
            )
            res = await session.execute(stmt)
            rows = res.all()
            if hasattr(rows, "__iter__"):
                return [(r[0], r[1]) for r in rows]
            return []


def clear_ephemeral_kb() -> None:
    """Clear knowledge tables for testing and teardowns."""
    import asyncio
    import concurrent.futures

    from sqlalchemy import delete

    from app.core.database import get_async_session_maker
    from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

    async def _clean() -> None:
        maker = get_async_session_maker()
        async with maker() as session:
            await session.execute(delete(KnowledgeChunk))
            await session.execute(delete(KnowledgeDocument))
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
