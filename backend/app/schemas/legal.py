"""Pydantic schemas for Legal policy versions and User Consent records."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LegalVersionsResponse(BaseModel):
    """Authoritative active versions and metadata for legal documents."""

    model_config = ConfigDict(from_attributes=True)

    terms_version: str = Field(..., description="Active version of Terms & Conditions.")
    privacy_version: str = Field(..., description="Active version of Privacy Policy.")
    terms_effective_date: str = Field(..., description="Effective date for Terms & Conditions.")
    privacy_effective_date: str = Field(..., description="Effective date for Privacy Policy.")
    legal_contact_email: str = Field(..., description="Configured operator legal contact address.")
    governing_law: str = Field(..., description="Designated governing jurisdiction placeholder.")
    minimum_age_requirement: str = Field(..., description="Configured minimum age requirement.")


class ConsentCreateRequest(BaseModel):
    """Payload for submitting or re-accepting terms and privacy policy consent."""

    model_config = ConfigDict(extra="forbid")

    terms_version: str = Field(..., min_length=1, max_length=32, description="Agreed Terms & Conditions version.")
    privacy_version: str = Field(..., min_length=1, max_length=32, description="Agreed Privacy Policy version.")
    action_source: str = Field(default="user_settings", max_length=64, description="Context or origin of consent action.")


class UserConsentResponse(BaseModel):
    """Public representation of an immutable user consent audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    terms_version: str
    privacy_version: str
    consented_at: datetime
    action_source: str
