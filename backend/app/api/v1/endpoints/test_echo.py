"""Phase 0 validation test endpoint (POST /api/v1/test-validation)."""

from pydantic import BaseModel, Field
from fastapi import APIRouter
from app.schemas.common import StandardResponse

router = APIRouter()


class ValidationTestRequest(BaseModel):
    """Schema for validating Phase 0 validation infrastructure."""

    name: str = Field(..., min_length=2, max_length=50, description="Sample name string")
    score: float = Field(..., ge=0.0, le=100.0, description="Sample score between 0.0 and 100.0")


class ValidationTestResponse(BaseModel):
    """Echo response schema."""

    echo_name: str
    echo_score: float


@router.post(
    "/test-validation",
    response_model=StandardResponse[ValidationTestResponse],
    summary="Phase 0 validation infrastructure test",
    description="Dedicated endpoint for testing Pydantic 422 request validation and error formatting.",
)
async def echo_validation_endpoint(
    payload: ValidationTestRequest,
) -> StandardResponse[ValidationTestResponse]:
    """Echo valid payload to confirm successful schema parsing."""
    return StandardResponse(
        success=True,
        data=ValidationTestResponse(
            echo_name=payload.name,
            echo_score=payload.score,
        ),
    )
