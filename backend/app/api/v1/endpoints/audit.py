"""Audit API endpoints for Daranya."""

import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.database import database_manager
from app.schemas.auth import UserResponse
from app.schemas.common import StandardResponse

logger = logging.getLogger("verifai.api.audit")

router = APIRouter()

@router.get(
    "",
    response_model=StandardResponse[List[Dict[str, Any]]],
    summary="Get user audit history",
)
async def get_audit_history(
    current_user: UserResponse = Depends(get_current_user),
) -> StandardResponse[List[Dict[str, Any]]]:
    """Retrieve all audit events for the authenticated user, ordered chronologically."""
    try:
        pool = database_manager.get_pool()
        if not pool:
            raise RuntimeError("Database connection not available")
            
        async with pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT id, verification_id, stage, status, metadata, created_at "
                "FROM audit_events WHERE user_id = $1 ORDER BY created_at ASC",
                current_user.id
            )
            
        results = [
            {
                "id": str(r["id"]),
                "verification_id": str(r["verification_id"]),
                "stage": r["stage"],
                "status": r["status"],
                "metadata": r.get("metadata"),
                "timestamp": r["created_at"]
            }
            for r in records
        ]
            
        return StandardResponse(success=True, data=results)
    except Exception as exc:
        logger.error("Error fetching audit events for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve audit events")
