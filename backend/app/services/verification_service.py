"""Verification service — thin orchestration between endpoints and repository.

Phase 2B scope: persistence and ownership only.
The AI verification pipeline (claim extraction, LLM judging, evidence search,
scoring, verdict) is intentionally NOT implemented here.
"""

import logging
import uuid
from typing import Dict, Any, Optional

from app.repositories.verification_repository import (
    VerificationRepository,
    verification_repository,
)

logger = logging.getLogger("verifai.services.verification")


class VerificationService:
    """Coordinates verification lifecycle operations.

    Responsibilities in Phase 2B:
    - Accept a claim from an authenticated user
    - Persist it via the repository (status starts as ``pending``)
    - Enforce ownership: a user may only read their own records
    - Return plain dicts to endpoints (serialisation handled by Pydantic)

    Responsibilities deferred to later batches:
    - Claim extraction / classification
    - LLM judging / resampling
    - Evidence / source search
    - Trust-score and verdict calculation
    """

    def __init__(self, repo: VerificationRepository = verification_repository) -> None:
        self._repo = repo

    async def submit_verification(
        self,
        user_id: uuid.UUID,
        claim: str,
    ) -> Dict[str, Any]:
        """Create and persist a new verification request.

        The record is inserted with status ``pending``. Processing will be
        triggered in a later batch.

        Args:
            user_id: UUID of the authenticated user submitting the claim.
            claim:   The AI-generated content/statement to verify.

        Returns:
            Full verification record dict.

        Raises:
            RuntimeError: Propagated from the repository when the database
                          pool is unavailable.
        """
        logger.info("Submitting verification for user %s", user_id)
        record = await self._repo.create_verification(user_id=user_id, claim=claim)
        logger.info(
            "Verification %s created for user %s (status=pending)",
            record["id"],
            user_id,
        )
        return record

    async def get_own_verification(
        self,
        verification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a verification by ID, returning it only if it belongs to user_id.

        Ownership is enforced here rather than in the endpoint to keep the
        endpoint function thin and the rule auditable in one place.

        Returns:
            The verification record dict if found and owned by user_id,
            ``None`` otherwise (including when the record belongs to another
            user — callers must NOT distinguish the two cases in HTTP
            responses to avoid information leakage).

        Raises:
            RuntimeError: Propagated from the repository when the database
                          pool is unavailable.
        """
        record = await self._repo.get_verification_by_id(verification_id)
        if record is None:
            return None
        # Strict UUID comparison prevents IDOR
        if record["user_id"] != user_id:
            logger.warning(
                "Ownership violation: user %s attempted to access verification %s "
                "owned by %s",
                user_id,
                verification_id,
                record["user_id"],
            )
            return None
        return record


# Default singleton instance
verification_service = VerificationService()
