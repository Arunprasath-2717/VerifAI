"""Knowledge Base REST API endpoints for namespace-isolated document management."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_optional_current_user, get_optional_db_session
from app.core.errors import AppError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.rate_limit import enforce_rate_limit
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.modules.knowledge.ingestion import (
    DuplicateDocumentError,
    IngestionValidationError,
)
from app.modules.knowledge.retriever import PrivateKBRetriever
from app.modules.knowledge.service import KnowledgeBaseService
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


def resolve_effective_owner(
    current_user: User | None,
    client_owner_id: str | None,
    settings: Settings,
) -> str:
    """Determine effective owner/namespace ID with strict security enforcement.

    1. If authenticated and non-admin: strictly forces user.id (rejects spoofing).
    2. If authenticated admin: allows inspecting target namespace or defaults
       to admin.id.
    3. If unauthenticated: strictly forbidden in production; permitted only in dev/test.
    """
    if current_user is not None:
        user_id_str = str(current_user.id)
        if current_user.role == "ADMIN":
            if client_owner_id and client_owner_id.strip():
                return client_owner_id.strip()
            return user_id_str

        # Non-admin user: prevent IDOR/spoofing of another user's namespace
        if (
            client_owner_id
            and client_owner_id.strip()
            and client_owner_id.strip() != user_id_str
        ):
            logger.warning(
                "IDOR attempt: User %s attempted to access namespace '%s'",
                user_id_str,
                client_owner_id,
            )
            raise ForbiddenError(
                message=(
                    "Cannot access or specify documents outside your user namespace."
                ),
                details={
                    "user_id": user_id_str,
                    "requested_owner_id": client_owner_id,
                },
            )
        return user_id_str

    # Unauthenticated path: strictly development/testing only
    is_dev = (
        settings.ENVIRONMENT in ("development", "test", "testing") or settings.DEBUG
    )
    if not is_dev:
        raise UnauthorizedError(
            message="Authentication required to access Knowledge Base in production.",
            details={"environment": settings.ENVIRONMENT},
        )

    if client_owner_id and client_owner_id.strip():
        return client_owner_id.strip()
    return settings.DEFAULT_OWNER_ID


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
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    """Add a new document via text payload."""
    effective_owner = resolve_effective_owner(current_user, request.owner_id, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="kb_upload",
            limit=settings.RATE_LIMIT_KB_UPLOAD_PER_MINUTE,
            user_id=effective_owner,
            settings=settings,
        )

    service = KnowledgeBaseService(db_session=db, settings=settings)
    try:
        doc = await service.add_document(
            raw_content=request.text,
            filename=request.filename,
            title=request.title,
            description=request.description,
            content_type=request.content_type,
            owner_id=effective_owner,
        )
        return _format_doc_response(doc)
    except DuplicateDocumentError as exc:
        raise ConflictError(
            message=str(exc),
            details={"content_hash": getattr(exc, "content_hash", None)},
        ) from exc
    except IngestionValidationError as exc:
        raise AppError(
            message=str(exc),
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from exc


@router.post(
    "/knowledge/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document to Knowledge Base (Multipart File)",
    description="Uploads a text or markdown file directly into the owner namespace.",
)
async def upload_document_file(
    http_request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    owner_id: str | None = Form(default=None),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    """Upload a raw document file."""
    effective_owner = resolve_effective_owner(current_user, owner_id, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="kb_upload",
            limit=settings.RATE_LIMIT_KB_UPLOAD_PER_MINUTE,
            user_id=effective_owner,
            settings=settings,
        )

    content_bytes = await file.read(settings.KB_MAX_DOCUMENT_BYTES + 1)
    if len(content_bytes) > settings.KB_MAX_DOCUMENT_BYTES:
        raise AppError(
            message=(
                f"File exceeds maximum size limit of "
                f"{settings.KB_MAX_DOCUMENT_BYTES} bytes."
            ),
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    service = KnowledgeBaseService(db_session=db, settings=settings)
    try:
        doc = await service.add_document(
            raw_content=content_bytes,
            filename=file.filename or "upload.txt",
            title=title or file.filename or "Uploaded Document",
            description=description,
            content_type=file.content_type,
            owner_id=effective_owner,
        )
        return _format_doc_response(doc)
    except DuplicateDocumentError as exc:
        raise ConflictError(message=str(exc)) from exc
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
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentListResponse:
    """List documents for a namespace."""
    effective_owner = resolve_effective_owner(current_user, owner_id, settings)
    service = KnowledgeBaseService(db_session=db, settings=settings)
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
    description="Retrieves document metadata along with all constituent text chunks.",
)
async def get_document_details(
    document_id: uuid.UUID,
    owner_id: str | None = Query(
        default=None, description="Namespace/owner identifier"
    ),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentDetailResponse:
    """Retrieve a single document and its constituent chunks."""
    effective_owner = resolve_effective_owner(current_user, owner_id, settings)
    service = KnowledgeBaseService(db_session=db, settings=settings)
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
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Delete a document and its chunks."""
    effective_owner = resolve_effective_owner(current_user, owner_id, settings)
    service = KnowledgeBaseService(db_session=db, settings=settings)
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
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeSearchResponse:
    """Execute search against private knowledge base."""
    effective_owner = resolve_effective_owner(current_user, request.owner_id, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="kb_search",
            limit=settings.RATE_LIMIT_KB_SEARCH_PER_MINUTE,
            user_id=effective_owner,
            settings=settings,
        )

    service = KnowledgeBaseService(db_session=db, settings=settings)
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
