"""Repository for VerificationJob, Claim, Evidence, and AuditRecord persistence."""

import logging
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError
from app.models.verification import (
    ExtractedClaim,
    VerificationJob,
)

logger = logging.getLogger("verifai.repositories.verification")


class VerificationRepository:
    """Manages persistence for verification jobs, claims, evidence, and audits."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_verification_job(self, job: VerificationJob) -> VerificationJob:
        """Persist a complete verification job and all its related child entities."""
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_verification_job(
        self,
        verification_id: uuid.UUID,
        owner_id: str | None = None,
        load_details: bool = True,
    ) -> VerificationJob | None:
        """Retrieve verification job by ID, asserting ownership if owner_id given."""
        stmt = select(VerificationJob).where(VerificationJob.id == verification_id)
        if load_details:
            stmt = stmt.options(
                selectinload(VerificationJob.claims).selectinload(
                    ExtractedClaim.evidence_items
                ),
                selectinload(VerificationJob.claims).selectinload(
                    ExtractedClaim.judge_evaluations
                ),
                selectinload(VerificationJob.audit_records),
            )

        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            return None

        if owner_id is not None and job.owner_id != owner_id:
            raise ForbiddenError(
                message="Access denied to verification job.",
                details={"verification_id": str(verification_id)},
            )
        return job

    async def list_verification_jobs(
        self,
        owner_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[VerificationJob], int]:
        """List verification jobs for a given owner with pagination."""
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        count_stmt = select(func.count()).where(VerificationJob.owner_id == owner_id)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(VerificationJob)
            .where(VerificationJob.owner_id == owner_id)
            .order_by(desc(VerificationJob.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def delete_verification_job(
        self,
        verification_id: uuid.UUID,
        owner_id: str,
    ) -> bool:
        """Delete verification job and cascade child entities."""
        job = await self.get_verification_job(
            verification_id, owner_id=owner_id, load_details=False
        )
        if not job:
            return False

        await self.session.delete(job)
        await self.session.commit()
        return True
