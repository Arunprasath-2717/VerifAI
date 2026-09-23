"""Knowledge Base service for namespace-isolated document storage and management."""

import logging
import uuid
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

# Ephemeral fallback store for development/testing when no database is configured
_EPHEMERAL_DOCS: dict[str, dict[uuid.UUID, KnowledgeDocument]] = {}
_EPHEMERAL_CHUNKS: dict[str, dict[uuid.UUID, list[KnowledgeChunk]]] = {}


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


def clear_ephemeral_kb(owner_id: str | None = None) -> None:
    """Clear in-memory knowledge store (useful for clean unit tests)."""
    global _EPHEMERAL_DOCS, _EPHEMERAL_CHUNKS
    if owner_id is not None:
        _EPHEMERAL_DOCS.pop(owner_id, None)
        _EPHEMERAL_CHUNKS.pop(owner_id, None)
    else:
        _EPHEMERAL_DOCS.clear()
        _EPHEMERAL_CHUNKS.clear()


class KnowledgeBaseService:
    """Namespace-isolated document lifecycle management service.

    Supports dual-mode execution:
    1. Persistent execution via SQLAlchemy AsyncSession (PostgreSQL).
    2. Hermetic ephemeral execution when session is None (development/testing).
    """

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.db = db_session
        self.settings = settings or get_settings()

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

        # 2. Check for duplicate document within the same owner namespace
        if self.db is not None:
            dup_stmt = select(KnowledgeDocument).where(
                KnowledgeDocument.owner_id == effective_owner,
                KnowledgeDocument.content_hash == ingestion.content_hash,
            )
            dup_res = await self.db.execute(dup_stmt)
            if dup_res.scalars().first() is not None:
                raise DuplicateDocumentError(
                    "Document with identical content already exists in namespace "
                    f"'{effective_owner}'."
                )

            # Create document entity
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
            self.db.add(doc)

            # Create chunk entities
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

            await self.db.flush()
            await self.db.commit()
            return doc

        # Ephemeral mode
        owner_docs = _EPHEMERAL_DOCS.setdefault(effective_owner, {})
        for existing_doc in owner_docs.values():
            if existing_doc.content_hash == ingestion.content_hash:
                raise DuplicateDocumentError(
                    "Document with identical content already exists in namespace "
                    f"'{effective_owner}'."
                )

        now = datetime.now(UTC)
        doc_id = uuid.uuid4()
        doc = KnowledgeDocument(
            id=doc_id,
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

        chunk_list: list[KnowledgeChunk] = []
        for chunk_data in ingestion.chunks:
            chunk = KnowledgeChunk(
                id=uuid.uuid4(),
                document_id=doc_id,
                owner_id=effective_owner,
                chunk_index=chunk_data.chunk_index,
                text=chunk_data.text,
                start_offset=chunk_data.start_offset,
                end_offset=chunk_data.end_offset,
                metadata_json=chunk_data.metadata_json,
                created_at=now,
                updated_at=now,
            )
            chunk.document = doc
            chunk_list.append(chunk)

        doc.chunks = chunk_list
        owner_docs[doc_id] = doc
        _EPHEMERAL_CHUNKS.setdefault(effective_owner, {})[doc_id] = chunk_list
        return doc

    async def list_documents(
        self,
        owner_id: str | None = None,
    ) -> list[KnowledgeDocument]:
        """List all knowledge documents strictly isolated to the specified owner."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        if self.db is not None:
            stmt = (
                select(KnowledgeDocument)
                .where(KnowledgeDocument.owner_id == effective_owner)
                .options(selectinload(KnowledgeDocument.chunks))
                .order_by(KnowledgeDocument.created_at.desc())
            )
            res = await self.db.execute(stmt)
            return list(res.scalars().all())

        owner_docs = _EPHEMERAL_DOCS.get(effective_owner, {})
        return sorted(
            owner_docs.values(),
            key=lambda d: d.created_at,
            reverse=True,
        )

    async def get_document(
        self,
        document_id: uuid.UUID,
        owner_id: str | None = None,
    ) -> KnowledgeDocument:
        """Fetch a specific document with chunks, verifying ownership."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        if self.db is not None:
            stmt = (
                select(KnowledgeDocument)
                .where(
                    KnowledgeDocument.id == document_id,
                    KnowledgeDocument.owner_id == effective_owner,
                )
                .options(selectinload(KnowledgeDocument.chunks))
            )
            res = await self.db.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                raise NotFoundError(
                    f"Document '{document_id}' not found in '{effective_owner}'."
                )
            return doc

        owner_docs = _EPHEMERAL_DOCS.get(effective_owner, {})
        doc = owner_docs.get(document_id)
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

        if self.db is not None:
            # Check ownership before deletion
            stmt = select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.owner_id == effective_owner,
            )
            res = await self.db.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                raise NotFoundError(
                    f"Document '{document_id}' not found in '{effective_owner}'."
                )

            # Cascade delete removes chunks automatically
            del_stmt = delete(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.owner_id == effective_owner,
            )
            await self.db.execute(del_stmt)
            await self.db.commit()
            return True

        owner_docs = _EPHEMERAL_DOCS.get(effective_owner, {})
        if document_id not in owner_docs:
            raise NotFoundError(
                f"Document '{document_id}' not found in namespace '{effective_owner}'."
            )

        del owner_docs[document_id]
        if effective_owner in _EPHEMERAL_CHUNKS:
            _EPHEMERAL_CHUNKS[effective_owner].pop(document_id, None)
        return True

    async def get_all_chunks_for_owner(
        self,
        owner_id: str | None = None,
    ) -> list[tuple[KnowledgeChunk, KnowledgeDocument]]:
        """Retrieve all active chunks and associated document metadata for an owner."""
        effective_owner = resolve_owner_id(owner_id, self.settings)

        if self.db is not None:
            try:
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
                res = await self.db.execute(stmt)
                all_records = res.all()
                if hasattr(all_records, "__await__"):
                    all_records = await all_records
                if isinstance(all_records, (list, tuple)):
                    return list(all_records)
            except Exception as exc:
                logger.debug(
                    "Database chunk query error (%s); checking ephemeral store",
                    exc,
                )

        pairs: list[tuple[KnowledgeChunk, KnowledgeDocument]] = []
        owner_docs = _EPHEMERAL_DOCS.get(effective_owner, {})
        owner_chunks_map = _EPHEMERAL_CHUNKS.get(effective_owner, {})

        for doc_id, doc in owner_docs.items():
            chunks = owner_chunks_map.get(doc_id, [])
            for c in chunks:
                pairs.append((c, doc))

        return pairs
