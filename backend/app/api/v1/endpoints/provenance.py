"""Provenance API endpoints for Daranya."""

import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.repositories.verification_repository import verification_repository, VerificationRepository
from app.schemas.auth import UserResponse
from app.schemas.common import StandardResponse

logger = logging.getLogger("verifai.api.provenance")

router = APIRouter()

@router.get(
    "/{claim_id}/provenance",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get claim provenance",
)
async def get_claim_provenance(
    claim_id: str,
    verification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    repo: VerificationRepository = Depends(lambda: verification_repository),
) -> StandardResponse[Dict[str, Any]]:
    """Retrieve the provenance (Claim -> Evidence -> Source -> Verdict) for a specific claim.
    Requires verification_id to be passed as a query param since claims are stored in verification JSONB.
    """
    try:
        record = await repo.get_verification_by_id(verification_id)
        if not record or str(record["user_id"]) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Verification not found or unauthorized")
            
        evidence = record.get("evidence")
        if not evidence:
            raise HTTPException(status_code=404, detail="No evidence found for this verification")
            
        claim_results = evidence.get("claim_results", [])
        claim_data = next((c for c in claim_results if c.get("claim_id") == claim_id), None)
        
        if not claim_data:
            raise HTTPException(status_code=404, detail="Claim not found in this verification")
            
        # Format the provenance trace
        provenance = {
            "claim_id": claim_data.get("claim_id"),
            "claim_text": claim_data.get("claim_text"),
            "verdict": claim_data.get("verdict"),
            "confidence": claim_data.get("confidence"),
            "decision_basis": claim_data.get("reason"),
            "evidence": []
        }
        
        for judge_res in claim_data.get("judge_results", []):
            source = judge_res.get("source", {})
            provenance["evidence"].append({
                "source_title": source.get("title", source.get("domain", "Unknown Source")),
                "source_url": source.get("url"),
                "source_quality": source.get("quality_score", 0.0),
                "relevance": judge_res.get("relevance_score", 0.0),
                "verdict": judge_res.get("verdict"),
                "confidence": judge_res.get("confidence", 0.0),
                "decision_basis": judge_res.get("reasoning", "")
            })
            
        return StandardResponse(success=True, data=provenance)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching provenance for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve claim provenance")
