"""History API endpoints for Daranya."""

import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.dependencies import get_current_user
from app.repositories.verification_repository import (
    VerificationRepository,
    verification_repository,
)
from app.schemas.auth import UserResponse
from app.schemas.common import StandardResponse

logger = logging.getLogger("verifai.api.history")

router = APIRouter()

# ---------------------------------------------------------------------------
# GET /api/v1/history
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=StandardResponse[List[Dict[str, Any]]],
    summary="Get verification history",
)
async def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    model: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    current_user: UserResponse = Depends(get_current_user),
    repo: VerificationRepository = Depends(lambda: verification_repository),
) -> StandardResponse[List[Dict[str, Any]]]:
    """Retrieve paginated verification history for the authenticated user."""
    try:
        offset = (page - 1) * limit
        # For simplicity, we fetch all user verifications and filter in Python
        # if the DB schema doesn't fully support all filters directly.
        # A production app would build a dynamic SQL query.
        records = await repo.get_verifications_by_user(current_user.id, limit=1000, offset=0)
        
        # Apply filters
        if verdict:
            records = [r for r in records if r.get("verdict") == verdict]
        if from_date:
            records = [r for r in records if r["created_at"] >= from_date]
        if to_date:
            records = [r for r in records if r["created_at"] <= to_date]
            
        # Format response
        results = []
        for r in records:
            evidence_data = r.get("evidence") or {}
            claim_count = len(evidence_data.get("claim_results", [])) if evidence_data else 0
            source_count = evidence_data.get("source_count", 0) if evidence_data else 0
            
            # Extract AI response preview (claim text)
            preview = r.get("claim", "")[:100] + "..." if len(r.get("claim", "")) > 100 else r.get("claim", "")
            
            results.append({
                "verification_id": r["id"],
                "model": "gemini",  # Placeholder as it's not in schema
                "response_preview": preview,
                "timestamp": r["created_at"],
                "verdict": r.get("verdict"),
                "confidence": r.get("trust_score"),
                "claim_count": claim_count,
                "source_count": source_count
            })
            
        # Paginate
        total = len(results)
        paginated_results = results[offset:offset+limit]
        
        return StandardResponse(
            success=True, 
            data=paginated_results,
            metadata={"total": total, "page": page, "limit": limit}
        )
    except Exception as exc:
        logger.error("Error fetching history for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

# ---------------------------------------------------------------------------
# GET /api/v1/history/search
# ---------------------------------------------------------------------------

@router.get(
    "/search",
    response_model=StandardResponse[List[Dict[str, Any]]],
    summary="Search verification history",
)
async def search_history(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    repo: VerificationRepository = Depends(lambda: verification_repository),
) -> StandardResponse[List[Dict[str, Any]]]:
    """Search the user's verification history."""
    try:
        offset = (page - 1) * limit
        records = await repo.get_verifications_by_user(current_user.id, limit=1000, offset=0)
        
        q_lower = q.lower()
        filtered = []
        for r in records:
            if q_lower in r.get("claim", "").lower() or q_lower in str(r["id"]).lower():
                filtered.append(r)
                
        results = []
        for r in filtered:
            results.append({
                "verification_id": r["id"],
                "model": "gemini",
                "response_preview": r.get("claim", "")[:100],
                "timestamp": r["created_at"],
                "verdict": r.get("verdict"),
                "confidence": r.get("trust_score"),
            })
            
        return StandardResponse(
            success=True, 
            data=results[offset:offset+limit]
        )
    except Exception as exc:
        logger.error("Error searching history for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to search history")

# ---------------------------------------------------------------------------
# GET /api/v1/history/{verification_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{verification_id}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Retrieve full historical verification details",
)
async def get_history_details(
    verification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    repo: VerificationRepository = Depends(lambda: verification_repository),
) -> StandardResponse[Dict[str, Any]]:
    """Get complete historical verification data, avoiding any regeneration."""
    try:
        record = await repo.get_verification_by_id(verification_id)
        if not record or str(record["user_id"]) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Verification not found or unauthorized")
            
        return StandardResponse(success=True, data=record)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching history details for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve history details")

# ---------------------------------------------------------------------------
# DELETE /api/v1/history/{verification_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{verification_id}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Delete a single history entry",
)
async def delete_history_item(
    verification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    repo: VerificationRepository = Depends(lambda: verification_repository),
) -> StandardResponse[Dict[str, Any]]:
    """Delete a specific verification history entry."""
    try:
        success = await repo.delete_verification(verification_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Verification not found or unauthorized")
            
        return StandardResponse(success=True, data={"deleted": True})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error deleting history for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete history item")

# ---------------------------------------------------------------------------
# DELETE /api/v1/history
# ---------------------------------------------------------------------------

@router.delete(
    "",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Clear all history",
)
async def clear_history(
    current_user: UserResponse = Depends(get_current_user),
    repo: VerificationRepository = Depends(lambda: verification_repository),
) -> StandardResponse[Dict[str, Any]]:
    """Clear all verification history for the authenticated user only."""
    try:
        pool = repo.db.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM verifications WHERE user_id = $1", current_user.id)
            
        return StandardResponse(success=True, data={"deleted": True})
    except Exception as exc:
        logger.error("Error clearing history for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to clear history")
