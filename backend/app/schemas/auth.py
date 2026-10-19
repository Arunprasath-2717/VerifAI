"""Pydantic schemas for User authentication, registration, and RBAC."""

import re
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRole(StrEnum):
    """PRD role-based access control roles."""

    USER = "USER"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"


EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


class UserRegisterRequest(BaseModel):
    """Payload for user registration. Defaults strictly to USER role."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="User email address.",
        examples=["analyst@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Unique username (alphanumeric, dashes, underscores).",
        examples=["analyst_01"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, containing at least 1 letter and 1 digit).",
    )
    terms_accepted: bool = Field(
        ...,
        description="Explicit acceptance of Terms & Conditions and Privacy Policy.",
    )

    @field_validator("terms_accepted", mode="after")
    @classmethod
    def validate_terms_accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must read and agree to the Terms & Conditions and Privacy Policy.")
        return v

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean

    @field_validator("username", mode="after")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        clean = v.strip()
        if not USERNAME_REGEX.match(clean):
            raise ValueError(
                "Username must be 3-64 characters and contain only "
                "letters, numbers, dashes, or underscores."
            )
        return clean

    @field_validator("password", mode="after")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    model_config = ConfigDict(extra="forbid")

    email_or_username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Email address or username.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Plaintext password to authenticate.",
    )

    @field_validator("email_or_username", mode="after")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Email or username must not be empty.")
        return clean


class TokenResponse(BaseModel):
    """OAuth2 / JWT bearer access token response."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole
    user_id: uuid.UUID


class UserResponse(BaseModel):
    """Public user identity response (never leaks password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime


class FirebaseAuthRequest(BaseModel):
    """Payload containing Firebase ID token for authentication and synchronization."""

    model_config = ConfigDict(extra="ignore")

    id_token: str = Field(
        ...,
        min_length=10,
        description="Firebase Auth ID Token (JWT RS256) issued by Google.",
    )
    display_name: str | None = Field(
        default=None,
        max_length=128,
        description="Optional user display name provided during registration.",
    )
    terms_accepted: bool | None = Field(
        default=None,
        description="Whether user explicitly consented to Terms and Privacy Policy on signup.",
    )
    is_signup: bool = Field(
        default=False,
        description="Whether this request originates from the new account registration flow.",
    )


