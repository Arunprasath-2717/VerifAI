"""Knowledge Base REST API endpoints for namespace-isolated document management."""

import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_async_session as _get_async_session
from app.core.errors import AppError
from app.models.knowledge import KnowledgeDocument
from app.modules.knowledge.ingestion import (
    DuplicateDocumentError,
    IngestionValidationError,
)
from app.modules.knowledge.retriever import PrivateKBRetriever
from app.modules.knowledge.service import KnowledgeBaseService, resolve_owner_id
from app.schemas.knowledge import (
    ChunkResponse,
    DocumentCreateRequest,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
)

logger = logging.getLogger("verifai.api.knowledge")
router = APIRouter()


async def get_optional_db_session(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession | None, None]:
    """Provide an async database session if configured, or None for ephemeral runs."""
    if not settings.DATABASE_URL:
        yield None
        return

    try:
        async for session in _get_async_session():
            yield session
    except Exception as exc:
        logger.warning(
            "Could not establish database session: %s. Proceeding ephemerally.",
            type(exc).__name__,
        )
        yield None


def _format_doc_response(doc: KnowledgeDocument) -> DocumentResponse:
    """Format SQLAlchemy/in-memory KnowledgeDocument to Pydantic DocumentResponse."""
    return DocumentResponse(
        id=doc.id,
        owner_id=doc.owner_id,
        filename=doc.filename,
        title=doc.title,
        description=doc.description,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        content_hash=doc.content_hash,
        chunk_count=len(doc.chunks) if doc.chunks else 0,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post(
    "/knowledge/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Document to Knowledge Base (JSON)",
    description=(
        "Validates, extracts, hashes, chunks, and stores a document in the caller's "
        "namespace. Detects duplicate content within the same owner namespace."
    ),
)
async def create_document(
    request: DocumentCreateRequest,
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    """Add a new document via text payload."""
    service = KnowledgeBaseService(db_session=db, settings=settings)
    try:
        doc = await service.add_document(
            raw_content=request.text,
            filename=request.filename,
            title=request.title,
            description=request.description,
            content_type=request.content_type,
            owner_id=request.owner_id,
        )
        return _format_doc_response(doc)
    except DuplicateDocumentError as exc:
        raise AppError(
            message=str(exc),
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        ) from exc
    except IngestionValidationError as exc:
        raise AppError(
            message=str(exc),
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from exc


@router.get(
    "/knowledge/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Knowledge Documents",
    description="Retrieves all documents strictly belonging to the owner namespace.",
)
async def list_documents(
    owner_id: str | None = Query(
        default=None, description="Namespace/owner identifier"
    ),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentListResponse:
    """List documents for a namespace."""
    service = KnowledgeBaseService(db_session=db, settings=settings)
    effective_owner = resolve_owner_id(owner_id, settings)
    docs = await service.list_documents(owner_id=effective_owner)

    return DocumentListResponse(
        owner_id=effective_owner,
        total_documents=len(docs),
        documents=[_format_doc_response(d) for d in docs],
    )


@router.get(
    "/knowledge/documents/{document_id}",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Details and Chunks",
    description="Retrieves document metadata along with all extracted text chunks.",
)
async def get_document_details(
    document_id: uuid.UUID,
    owner_id: str | None = Query(
        default=None, description="Namespace/owner identifier"
    ),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentDetailResponse:
    """Retrieve a single document and its constituent chunks."""
    service = KnowledgeBaseService(db_session=db, settings=settings)
    effective_owner = resolve_owner_id(owner_id, settings)
    doc = await service.get_document(document_id=document_id, owner_id=effective_owner)

    chunk_responses = [
        ChunkResponse(
            id=c.id,
            document_id=c.document_id,
            owner_id=c.owner_id,
            chunk_index=c.chunk_index,
            text=c.text,
            start_offset=c.start_offset,
            end_offset=c.end_offset,
            metadata_json=c.metadata_json,
            created_at=c.created_at,
        )
        for c in (doc.chunks or [])
    ]

    base_resp = _format_doc_response(doc)
    return DocumentDetailResponse(
        **base_resp.model_dump(),
        chunks=chunk_responses,
    )


@router.delete(
    "/knowledge/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Knowledge Document",
    description="Deletes a document and all its chunks from the owner namespace.",
)
async def delete_document(
    document_id: uuid.UUID,
    owner_id: str | None = Query(
        default=None, description="Namespace/owner identifier"
    ),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Delete a document and its chunks."""
    service = KnowledgeBaseService(db_session=db, settings=settings)
    effective_owner = resolve_owner_id(owner_id, settings)
    await service.delete_document(document_id=document_id, owner_id=effective_owner)
    return {
        "status": "deleted",
        "document_id": str(document_id),
        "owner_id": effective_owner,
    }


@router.post(
    "/knowledge/search",
    response_model=KnowledgeSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Knowledge Base for Evidence",
    description="Deterministic scored search across owner namespace chunks.",
)
async def search_knowledge_base(
    request: KnowledgeSearchRequest,
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeSearchResponse:
    """Execute search against private knowledge base."""
    service = KnowledgeBaseService(db_session=db, settings=settings)
    effective_owner = resolve_owner_id(request.owner_id, settings)
    retriever = PrivateKBRetriever(
        service=service, owner_id=effective_owner, settings=settings
    )

    search_res = await retriever.search(
        claim_text=request.query,
        owner_id=effective_owner,
        max_passages=request.max_passages,
        threshold=request.threshold,
        min_overlap_tokens=request.min_overlap_tokens,
    )

    result_items: list[KnowledgeSearchResultItem] = []
    for item in search_res.evidence_items:
        meta = item.metadata_json or {}
        result_items.append(
            KnowledgeSearchResultItem(
                document_id=item.document_id or uuid.uuid4(),
                chunk_id=item.chunk_id or uuid.uuid4(),
                owner_id=effective_owner,
                document_title=item.document_title
                or item.source_title
                or "Untitled Document",
                filename=meta.get("filename", "document.txt"),
                chunk_index=item.chunk_index if item.chunk_index is not None else 0,
                snippet=item.snippet,
                relevance_score=item.relevance_score or 0.0,
                overlap_tokens=meta.get("overlap_tokens", 0),
                evidence_source="PRIVATE_KB",
                metadata_json=meta,
            )
        )

    return KnowledgeSearchResponse(
        query=request.query,
        owner_id=effective_owner,
        sufficiency=search_res.sufficiency,
        threshold_used=search_res.threshold_used,
        min_overlap_tokens_used=search_res.min_overlap_tokens_used,
        total_chunks_matched=len(result_items),
        results=result_items,
    )
