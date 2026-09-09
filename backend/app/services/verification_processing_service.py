"""Verification processing service — Phase 2C/2D lifecycle orchestration.

Responsibilities:
- Enforce state-transition rules (pending → processing → completed/failed)
- Delegate all database mutations to the repository's atomic transition_status
- Call the Phase 2D verification engine for real claim verification
- Persist engine results via update_verification()
- Never expose stack traces or internal errors to callers
"""

import logging
import uuid
from typing import Any, Dict, Optional

from app.repositories.verification_repository import (
    VerificationRepository,
    verification_repository,
)
from app.schemas.verification import VerificationStatus

# Import here (module level) so tests can patch
# app.services.verification_processing_service.verification_engine
from app.engine.engine import verification_engine as verification_engine  # noqa: F401

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
    claim: str,
    repo: VerificationRepository,
) -> Dict[str, Any]:
    """Run the real verification engine and persist results.

    Phase 2D: replaces the deterministic stub with the actual pipeline:
        extract → classify → search → score → judge → decide → persist

    Args:
        verification_id: UUID of the verification record.
        claim:           The raw claim text from the database record.
        repo:            Repository for persisting the result.

    Returns:
        The final persisted verification record dict.

    Raises:
        Any exception from the engine propagates to the caller
        (VerificationProcessingService) which handles the failed transition.
    """
    logger.info("Engine starting for verification %s", verification_id)
    engine_result = await verification_engine.verify(
        claim_text=claim,
        verification_id=verification_id,
    )

    logger.info(
        "Engine completed verification %s: verdict=%s confidence=%s",
        verification_id,
        engine_result.verdict.value,
        engine_result.trust_score,
    )

    # Persist result fields using the existing repository method.
    # Status remains 'processing' — the caller's lifecycle management will
    # transition to 'completed' via transition_status after this returns.
    persisted = await repo.update_verification(
        verification_id=verification_id,
        status="processing",          # kept; CAS to completed happens next
        verdict=engine_result.verdict.value,
        trust_score=engine_result.trust_score,
        evidence=engine_result.evidence,
    )
    return persisted if persisted is not None else {}


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

        # ── 3. Run real engine (Phase 2D) ──────────────────────────────────
        try:
            await _process_verification_core(
                verification_id=verification_id,
                claim=record["claim"],
                repo=self._repo,
            )
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
