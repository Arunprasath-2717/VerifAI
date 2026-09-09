"""Verification processing service — Phase 2C lifecycle orchestration.

Responsibilities:
- Enforce state-transition rules (pending → processing → completed/failed)
- Delegate all database mutations to the repository's atomic transition_status
- Run a deterministic processing stub that leaves verdict/trust_score/evidence null
- Never expose stack traces or internal errors to callers

Intentionally NOT implemented here (deferred to later batches):
- Claim extraction / classification
- LLM judging / resampling
- Evidence / source search
- Trust-score and verdict calculation
- Any external API calls (Gemini, Groq, Tavily, DuckDuckGo …)
"""

import logging
import uuid
from typing import Any, Dict, Optional

from app.repositories.verification_repository import (
    VerificationRepository,
    verification_repository,
)
from app.schemas.verification import VerificationStatus

logger = logging.getLogger("verifai.services.processing")


# ---------------------------------------------------------------------------
# Custom exceptions — processed inside the service and never leaked directly
# ---------------------------------------------------------------------------


class VerificationNotFoundError(Exception):
    """Raised when the verification does not exist or is not owned by the caller."""


class InvalidStatusTransitionError(Exception):
    """Raised when the current status does not allow the requested transition."""


# ---------------------------------------------------------------------------
# Processing stub
# ---------------------------------------------------------------------------


async def _process_verification_core(
    verification_id: uuid.UUID,
) -> Dict[str, Any]:
    """Deterministic processing placeholder for Phase 2C.

    Returns minimal stub data.  Verdict, trust_score, and evidence are
    intentionally left absent — those fields are populated by the real
    verification engine in a later batch.

    This function must NOT:
    - call any external LLM or search API
    - produce a verdict, trust score, or evidence list
    - raise exceptions under normal execution
    """
    logger.info(
        "Processing stub executing for verification %s", verification_id
    )
    return {
        "phase": "processing_stub",
        "message": "Verification processing foundation completed",
    }


# ---------------------------------------------------------------------------
# Processing service
# ---------------------------------------------------------------------------


class VerificationProcessingService:
    """Orchestrates the verification lifecycle: pending → processing → completed/failed.

    The service keeps a strict wall between the API layer (ownership, auth) and
    the database (state transitions).  All transitions go through the repository's
    atomic ``transition_status`` method so that concurrent calls cannot produce
    inconsistent final states.
    """

    def __init__(self, repo: VerificationRepository = verification_repository) -> None:
        self._repo = repo

    async def process_verification(
        self,
        verification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Orchestrate the full pending → processing → completed/failed lifecycle.

        Steps:
        1. Fetch the verification and enforce ownership.
        2. Atomically transition pending → processing.
           If the current status is not ``pending``, raise
           ``InvalidStatusTransitionError`` — the endpoint maps this to 409.
        3. Run the processing stub.
        4. On success: transition processing → completed.
        5. On any exception: transition processing → failed with a safe message.

        Returns:
            The final (completed or failed) verification record dict.

        Raises:
            VerificationNotFoundError: Verification does not exist or belongs
                to another user.
            InvalidStatusTransitionError: Current status is not ``pending``.
            RuntimeError: Database pool unavailable (propagated from repo).
        """
        # ── 1. Fetch & verify ownership ───────────────────────────────────
        record = await self._repo.get_verification_by_id(verification_id)
        if record is None or record["user_id"] != user_id:
            raise VerificationNotFoundError(
                f"Verification {verification_id} not found for user {user_id}"
            )

        # ── 2. pending → processing (atomic) ──────────────────────────────
        processing_record = await self._repo.transition_status(
            verification_id=verification_id,
            expected_status=VerificationStatus.PENDING.value,
            new_status=VerificationStatus.PROCESSING.value,
        )
        if processing_record is None:
            # Row exists but was not in pending — another call already moved it
            raise InvalidStatusTransitionError(
                f"Verification {verification_id} is not in pending state "
                f"(current status: {record['status']})"
            )

        # ── 3. Run processing stub ─────────────────────────────────────────
        try:
            await _process_verification_core(verification_id)
        except Exception as exc:
            # ── 5. processing → failed ─────────────────────────────────────
            logger.error(
                "Processing failed for verification %s: %s", verification_id, exc
            )
            safe_message = "Verification processing failed due to an internal error"
            failed_record = await self._repo.transition_status(
                verification_id=verification_id,
                expected_status=VerificationStatus.PROCESSING.value,
                new_status=VerificationStatus.FAILED.value,
                error_message=safe_message,
            )
            # Return the failed record (or fall back to processing_record with
            # status patched) so callers always get a consistent dict back.
            return failed_record if failed_record is not None else {
                **processing_record,
                "status": VerificationStatus.FAILED.value,
                "error_message": safe_message,
            }

        # ── 4. processing → completed ──────────────────────────────────────
        logger.info(
            "Verification %s processing completed successfully", verification_id
        )
        completed_record = await self._repo.transition_status(
            verification_id=verification_id,
            expected_status=VerificationStatus.PROCESSING.value,
            new_status=VerificationStatus.COMPLETED.value,
        )
        # Completed transition should always succeed here since we own this
        # verification and just set it to processing, but guard defensively.
        return completed_record if completed_record is not None else {
            **processing_record,
            "status": VerificationStatus.COMPLETED.value,
        }


# Default singleton instance
verification_processing_service = VerificationProcessingService()
