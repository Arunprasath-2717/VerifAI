"""Pydantic schemas for request and response models."""

from app.schemas.auth import (
    AuthResponseData,
    AuthTokens,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.common import ErrorDetails, ErrorResponse, StandardResponse
from app.schemas.verification import (
    CreateVerificationRequest,
    VerificationListResponse,
    VerificationResponse,
    VerificationStatus,
)

__all__ = [
    "StandardResponse",
    "ErrorResponse",
    "ErrorDetails",
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "UserUpdateRequest",
    "UserResponse",
    "AuthTokens",
    "AuthResponseData",
    "MessageResponse",
    # Verification schemas (Phase 2A)
    "VerificationStatus",
    "CreateVerificationRequest",
    "VerificationResponse",
    "VerificationListResponse",
]
