"""Authentication request and response schemas."""

from datetime import datetime
import re
from typing import Optional
import uuid
from pydantic import BaseModel, Field, field_validator

# Standard RFC 5322 compatible email regex for offline validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class RegisterRequest(BaseModel):
    """Payload for user registration."""

    email: str = Field(..., max_length=255, description="User's primary email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Secure account password (min 8 chars)"
    )
    display_name: Optional[str] = Field(
        None, min_length=2, max_length=50, description="Optional public display name"
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email address format")
        return cleaned


class LoginRequest(BaseModel):
    """Payload for user authentication."""

    email: str = Field(..., max_length=255, description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email address format")
        return cleaned


class RefreshTokenRequest(BaseModel):
    """Payload for renewing an access token."""

    refresh_token: str = Field(..., min_length=1, description="Supabase refresh token string")


class UserUpdateRequest(BaseModel):
    """Payload for updating user profile."""

    display_name: str = Field(
        ..., min_length=2, max_length=50, description="New display name for the user"
    )


class UserResponse(BaseModel):
    """Safe public user profile data model."""

    id: uuid.UUID = Field(..., description="Unique user identifier (Supabase Auth UID)")
    email: str = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User's public display name")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile last update timestamp")


class AuthTokens(BaseModel):
    """Authentication token details provided by Supabase Auth."""

    access_token: str = Field(..., description="JWT Bearer access token")
    refresh_token: str = Field(..., description="Opaque refresh token for session renewal")
    token_type: str = Field(default="bearer", description="Token authentication scheme")
    expires_in: int = Field(default=3600, description="Access token expiration window in seconds")


class AuthResponseData(BaseModel):
    """Combined profile and session payload returned upon successful auth."""

    user: UserResponse = Field(..., description="Authenticated user profile")
    session: AuthTokens = Field(..., description="Active session tokens")


class MessageResponse(BaseModel):
    """Simple confirmation message response."""

    message: str = Field(..., description="Informational result message")
