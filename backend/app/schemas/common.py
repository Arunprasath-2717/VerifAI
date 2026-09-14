"""Standard JSON response envelopes and error models."""

from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetails(BaseModel):
    """Detailed error payload structure."""

    type: str = Field(..., description="Machine-readable error type identifier")
    message: str = Field(..., description="Human-readable error description")
    details: Any = Field(default_factory=dict, description="Additional contextual details")


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = Field(default=False, description="Success status flag")
    error: ErrorDetails = Field(..., description="Error information")


class StandardResponse(BaseModel, Generic[DataT]):
    """Standard success response envelope."""

    success: bool = Field(default=True, description="Success status flag")
    data: DataT = Field(..., description="Response payload")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")
