"""Verification request and response schemas for Phase 2A."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Lifecycle status of a verification request.

    Mirrors the ``verification_status`` PostgreSQL ENUM exactly so that
    asyncpg-returned values round-trip cleanly through Pydantic.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateVerificationRequest(BaseModel):
    """Payload supplied by the client when submitting a new claim for verification."""

    claim: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="The AI-generated claim or statement to verify",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class VerificationResponse(BaseModel):
    """Complete verification record returned to the client."""

    id: uuid.UUID = Field(..., description="Unique verification identifier")
    user_id: uuid.UUID = Field(..., description="ID of the user who submitted the claim")
    claim: str = Field(..., description="The original claim text submitted for verification")
    status: VerificationStatus = Field(..., description="Current lifecycle status")
    verdict: Optional[str] = Field(None, description="AI verdict: e.g. 'supported', 'refuted', 'inconclusive'")
    trust_score: Optional[Decimal] = Field(
        None,
        description="Trust score in [0.000, 1.000] representing AI confidence",
        ge=0,
        le=1,
    )
    evidence: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Evidence sources used to reach the verdict (array of source objects)",
    )
    error_message: Optional[str] = Field(
        None,
        description="Human-readable error description when status is 'failed'",
    )
    created_at: datetime = Field(..., description="Timestamp when the verification was submitted")
    updated_at: datetime = Field(..., description="Timestamp when the record was last modified")

    model_config = {"from_attributes": True}


class VerificationListResponse(BaseModel):
    """Paginated list of verification records for the authenticated user."""

    items: List[VerificationResponse] = Field(..., description="Verification records for this page")
    total: int = Field(..., description="Total number of verifications for this user")
    limit: int = Field(..., description="Maximum records per page")
    offset: int = Field(..., description="Number of records skipped from the beginning")
