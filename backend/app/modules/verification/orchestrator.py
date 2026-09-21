"""Pipeline orchestrator coordinating the verification lifecycle."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import (
    AuditRecord,
    ExtractedClaim,
    JudgeVerdict,
    RetrievedEvidence,
    VerificationJob,
)
from app.modules.claims.classifier import ContentClassifier
from app.modules.claims.extractor import (
    BaseClaimExtractor,
    DeterministicClaimExtractor,
)
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.local_retriever import LocalPassageRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.web_retriever import SafeWebRetriever
from app.modules.judging.decision import DecisionEngine
from app.modules.judging.deterministic_judge import DeterministicRuleJudge
from app.modules.judging.disagreement import DisagreementEngine
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData
from app.modules.judging.semantic_judge import SecondarySemanticJudge
from app.schemas.verification import (
    AuditRecordSchema,
    ClaimResultSchema,
    EvidenceSchema,
    JudgeDecision,
    JudgeEvaluationSchema,
    UnknownReason,
    VerdictType,
    VerificationCreateRequest,
    VerificationResponse,
    VerificationStatus,
)

logger = logging.getLogger("verifai.orchestrator")


class VerificationOrchestrator:
    """Coordinates extraction, retrieval, judging, and audit lifecycle."""

    def __init__(
        self,
        extractor: BaseClaimExtractor | None = None,
        classifier: ContentClassifier | None = None,
        retriever: BaseEvidenceRetriever | None = None,
        judges: list[BaseJudge] | None = None,
        tie_breaker_judge: BaseJudge | None = None,
        disagreement_engine: DisagreementEngine | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self.extractor = extractor or DeterministicClaimExtractor()
        self.classifier = classifier or ContentClassifier()
        self.retriever = retriever or LocalPassageRetriever()
        self.judges = judges or [
            DeterministicRuleJudge(name="Judge-Primary-Deterministic"),
            SecondarySemanticJudge(name="Judge-Secondary-Semantic"),
        ]
        self.tie_breaker_judge = tie_breaker_judge
        self.disagreement_engine = disagreement_engine or DisagreementEngine()
        self.decision_engine = decision_engine or DecisionEngine()

    async def verify(
        self,
        request: VerificationCreateRequest,
        db_session: AsyncSession | None = None,
    ) -> VerificationResponse:
        """Execute full verification pipeline for the given input text."""
        verification_id = uuid.uuid4()
        now_utc = datetime.now(UTC)
        audit_records: list[AuditRecord] = []

        def log_audit(
            stage: str,
            event_type: str,
            status: str,
            message: str,
            details: dict[str, Any] | None = None,
        ) -> None:
            audit_records.append(
                AuditRecord(
                    id=uuid.uuid4(),
                    verification_id=verification_id,
                    stage=stage,
                    event_type=event_type,
                    status=status,
                    message=message,
                    details=details or {},
                    timestamp=datetime.now(UTC),
                )
            )

        log_audit(
            stage="INITIALIZATION",
            event_type="JOB_STARTED",
            status="SUCCESS",
            message=f"Verification job {verification_id} initiated.",
            details={
                "text_length": len(request.text),
                "has_query": bool(request.query),
            },
        )

        # Step 1: Atomic Claim Extraction
        log_audit(
            stage="EXTRACTION",
            event_type="STAGE_STARTED",
            status="SUCCESS",
            message="Extracting atomic claims from input text.",
        )

        max_claims = request.options.max_claims
        extracted_items = self.extractor.extract(request.text, max_claims=max_claims)

        log_audit(
            stage="EXTRACTION",
            event_type="STAGE_COMPLETED",
            status="SUCCESS",
            message=f"Extracted {len(extracted_items)} atomic claims.",
            details={"claims_count": len(extracted_items)},
        )

        # Configure evidence retriever (select live web retriever if requested)
        active_retriever = self.retriever
        if request.options.enable_live_search:
            active_retriever = SafeWebRetriever()
            log_audit(
                stage="RETRIEVAL",
                event_type="PROVIDER_SELECTED",
                status="SUCCESS",
                message="Live web search enabled for evidence retrieval.",
                details={"retriever": active_retriever.name},
            )

        # Process each claim through classification, retrieval, and judging
        claims_processed: list[dict[str, Any]] = []
        db_claims: list[ExtractedClaim] = []

        for item in extracted_items:
            # Step 2: Content Classification
            classification = self.classifier.classify(item.text)

            evidence_items: list[RetrievedEvidenceItem] = []
            judge_evaluations: list[JudgeEvaluationData] = []
            claim_verdict = classification.verdict
            unknown_reason = None
            explanation = classification.explanation

            if classification.is_verifiable:
                # Step 3: Evidence Retrieval for verifiable factual claims
                try:
                    evidence_items = await active_retriever.retrieve(
                        item.text, max_passages=3
                    )
                except Exception as exc:
                    logger.warning("Retrieval failed for claim %d: %s", item.index, exc)
                    log_audit(
                        stage="RETRIEVAL",
                        event_type="DEGRADED_EXECUTION",
                        status="WARNING",
                        message=(
                            f"Evidence retrieval failed for claim index {item.index}."
                        ),
                        details={"error": type(exc).__name__, "claim_text": item.text},
                    )

                # Step 4: Independent Judge Evaluation
                if evidence_items:
                    # Evaluate primary 2 judges
                    for judge in self.judges[:2]:
                        try:
                            eval_data = await judge.evaluate(item.text, evidence_items)
                            judge_evaluations.append(eval_data)
                        except Exception as j_exc:
                            logger.warning(
                                "Judge %s failed on claim %d: %s",
                                judge.name,
                                item.index,
                                j_exc,
                            )
                            judge_evaluations.append(
                                JudgeEvaluationData(
                                    judge_id=uuid.uuid4(),
                                    judge_name=judge.name,
                                    judgment=JudgeDecision.UNAVAILABLE,
                                    rationale=f"Judge evaluation failed: {j_exc}",
                                )
                            )

                    # Step 5: Disagreement Analysis & Consensus
                    disagreement = self.disagreement_engine.arbitrate(
                        judge_evaluations,
                        strict_consensus=request.options.strict_consensus,
                    )

                    # If primary 2 judges disagreed and tie-breaker is configured
                    if (
                        disagreement.has_disagreement
                        and self.tie_breaker_judge is not None
                    ):
                        try:
                            tb_data = await self.tie_breaker_judge.evaluate(
                                item.text, evidence_items
                            )
                            judge_evaluations.append(tb_data)
                        except Exception as tb_exc:
                            logger.warning(
                                "Tie-breaker judge %s failed on claim %d: %s",
                                self.tie_breaker_judge.name,
                                item.index,
                                tb_exc,
                            )
                            judge_evaluations.append(
                                JudgeEvaluationData(
                                    judge_id=uuid.uuid4(),
                                    judge_name=self.tie_breaker_judge.name,
                                    judgment=JudgeDecision.UNAVAILABLE,
                                    rationale=(
                                        f"Tie-breaker evaluation failed: {tb_exc}"
                                    ),
                                )
                            )

                        # Re-arbitrate with all 3 evaluations
                        disagreement = self.disagreement_engine.arbitrate(
                            judge_evaluations,
                            strict_consensus=request.options.strict_consensus,
                        )

                    claim_verdict = disagreement.consensus_verdict
                    unknown_reason = disagreement.unknown_reason
                    degraded_evaluation = disagreement.degraded_evaluation
                    arbitration_reason = disagreement.arbitration_reason
                    if disagreement.has_disagreement:
                        explanation = (
                            disagreement.disagreement_details
                            or f"Judge disagreement: {arbitration_reason}"
                        )
                    else:
                        explanation = (
                            f"Consensus verdict: {claim_verdict.value} based on "
                            f"{len(evidence_items)} evidence passages."
                        )
                else:
                    claim_verdict = VerdictType.UNKNOWN
                    degraded_evaluation = False
                    arbitration_reason = None
                    if request.options.enable_live_search:
                        unknown_reason = UnknownReason.SEARCH_UNKNOWN
                        explanation = (
                            "External search protocol was attempted but "
                            "failed to produce usable evidence."
                        )
                    else:
                        unknown_reason = UnknownReason.CONTEXT_UNKNOWN
                        explanation = (
                            "Supplied local context or knowledge index does not "
                            "establish or contradict the claim."
                        )
            else:
                # Non-verifiable content receives verdict=None and is_verifiable=False
                claim_verdict = None
                unknown_reason = None
                degraded_evaluation = False
                arbitration_reason = None
                explanation = classification.explanation

            # Construct claim data dictionary
            claim_data = {
                "id": uuid.uuid4(),
                "claim_index": item.index,
                "claim_text": item.text,
                "start_offset": item.start_offset,
                "end_offset": item.end_offset,
                "content_type": classification.content_type,
                "verdict": claim_verdict,
                "is_verifiable": classification.is_verifiable,
                "confidence": None,
                "is_calibrated": False,
                "calibration_status": "NOT_CALIBRATED",
                "unknown_reason": unknown_reason,
                "explanation": explanation,
                "degraded_evaluation": degraded_evaluation,
                "arbitration_reason": arbitration_reason,
                "evidence": evidence_items,
                "judges": judge_evaluations,
            }
            claims_processed.append(claim_data)

            # Build database entity
            db_claim = ExtractedClaim(
                id=claim_data["id"],
                verification_id=verification_id,
                claim_index=item.index,
                claim_text=item.text,
                start_offset=item.start_offset,
                end_offset=item.end_offset,
                content_type=classification.content_type.value,
                verdict=claim_verdict.value if claim_verdict else None,
                is_verifiable=classification.is_verifiable,
                degraded_evaluation=degraded_evaluation,
                arbitration_reason=arbitration_reason,
                confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                unknown_reason=(
                    unknown_reason.value if unknown_reason is not None else None
                ),
                explanation=explanation,
            )

            # Attach evidence entities
            for ev in evidence_items:
                db_ev = RetrievedEvidence(
                    id=ev.id,
                    claim_id=db_claim.id,
                    source_url=ev.source_url,
                    source_title=ev.source_title,
                    publisher=ev.publisher,
                    publication_date=ev.publication_date,
                    retrieval_timestamp=ev.retrieval_timestamp,
                    snippet=ev.snippet,
                    query_used=ev.query_used,
                    retriever_name=ev.retriever_name,
                    relevance_score=ev.relevance_score,
                    authority_score=ev.authority_score,
                    metadata_json=ev.metadata_json,
                )
                db_claim.evidence_items.append(db_ev)

            # Attach judge evaluation entities
            for je in judge_evaluations:
                db_je = JudgeVerdict(
                    id=je.judge_id,
                    claim_id=db_claim.id,
                    judge_name=je.judge_name,
                    model_version=je.model_version,
                    evaluation_type="NLI_ENTAILMENT",
                    judgment=je.judgment.value,
                    confidence=je.confidence,
                    rationale=je.rationale,
                    evidence_references=je.evidence_references,
                    evaluation_metadata=je.metadata,
                )
                db_claim.judge_evaluations.append(db_je)

            db_claims.append(db_claim)

        # Step 6: Document-Level Decision Aggregation
        doc_summary = self.decision_engine.aggregate(claims_processed)

        score_str = (
            f"{doc_summary.trust_score}%"
            if doc_summary.trust_score is not None
            else "N/A (Non-verifiable)"
        )
        log_audit(
            stage="DECISION",
            event_type="STAGE_COMPLETED",
            status="SUCCESS",
            message=f"Document aggregated. Trust Score: {score_str}.",
            details={
                "total_claims": doc_summary.total_claims,
                "supported": doc_summary.supported_claims,
                "contradicted": doc_summary.contradicted_claims,
                "unknown": doc_summary.unknown_claims,
                "non_factual": doc_summary.non_factual_claims,
            },
        )

        completed_at = datetime.now(UTC)

        # Step 7: Create VerificationJob Database Entity
        verification_job = VerificationJob(
            id=verification_id,
            input_text=request.text,
            query=request.query,
            status=VerificationStatus.COMPLETED.value,
            content_type=doc_summary.content_type.value,
            total_claims=doc_summary.total_claims,
            supported_claims=doc_summary.supported_claims,
            contradicted_claims=doc_summary.contradicted_claims,
            unknown_claims=doc_summary.unknown_claims,
            non_factual_claims=doc_summary.non_factual_claims,
            trust_score=doc_summary.trust_score,
            calibrated_confidence=None,
            is_calibrated=False,
            calibration_status="NOT_CALIBRATED",
            degraded_evaluation=any(
                c.get("degraded_evaluation", False) for c in claims_processed
            ),
            summary=doc_summary.summary_text,
            completed_at=completed_at,
            execution_metadata={
                "retriever_used": active_retriever.name,
                "judges_used": [j.name for j in self.judges],
                "extractor": "DeterministicClaimExtractor",
            },
        )
        verification_job.claims = db_claims
        verification_job.audit_records = audit_records

        # Step 8: Database Persistence (if session provided)
        if db_session is not None:
            try:
                db_session.add(verification_job)
                await db_session.commit()
                log_audit(
                    stage="PERSISTENCE",
                    event_type="JOB_SAVED",
                    status="SUCCESS",
                    message="Verification job saved to database.",
                )
            except Exception as db_exc:
                logger.warning("Database persistence failed: %s", db_exc)
                await db_session.rollback()
                log_audit(
                    stage="PERSISTENCE",
                    event_type="DEGRADED_EXECUTION",
                    status="WARNING",
                    message=(
                        "Database persistence failed; execution degraded to ephemeral."
                    ),
                    details={"error": type(db_exc).__name__},
                )

        # Step 9: Assemble Strongly-Typed VerificationResponse
        response_claims: list[ClaimResultSchema] = []
        for c in claims_processed:
            ev_schemas = [
                EvidenceSchema(
                    id=ev.id,
                    source_url=ev.source_url,
                    source_title=ev.source_title,
                    publisher=ev.publisher,
                    publication_date=ev.publication_date,
                    snippet=ev.snippet,
                    retriever_name=ev.retriever_name,
                    relevance_score=ev.relevance_score,
                    authority_score=ev.authority_score,
                )
                for ev in c["evidence"]
            ]

            je_schemas = [
                JudgeEvaluationSchema(
                    id=je.judge_id,
                    judge_name=je.judge_name,
                    judgment=je.judgment.value,
                    confidence=je.confidence,
                    rationale=je.rationale,
                    evidence_references=je.evidence_references,
                )
                for je in c["judges"]
            ]

            response_claims.append(
                ClaimResultSchema(
                    id=c["id"],
                    claim_index=c["claim_index"],
                    claim_text=c["claim_text"],
                    start_offset=c["start_offset"],
                    end_offset=c["end_offset"],
                    content_type=c["content_type"].value,
                    verdict=c["verdict"],
                    is_verifiable=c["is_verifiable"],
                    confidence=c["confidence"],
                    is_calibrated=c["is_calibrated"],
                    calibration_status=c["calibration_status"],
                    unknown_reason=c["unknown_reason"],
                    explanation=c["explanation"],
                    degraded_evaluation=c["degraded_evaluation"],
                    arbitration_reason=c["arbitration_reason"],
                    evidence=ev_schemas,
                    judges=je_schemas,
                )
            )

        response_audit = [
            AuditRecordSchema(
                id=ar.id,
                stage=ar.stage,
                event_type=ar.event_type,
                status=ar.status,
                message=ar.message,
                timestamp=ar.timestamp,
            )
            for ar in audit_records
        ]

        return VerificationResponse(
            verification_id=verification_id,
            status=VerificationStatus.COMPLETED.value,
            input_text=request.text,
            query=request.query,
            content_type=doc_summary.content_type.value,
            total_claims=doc_summary.total_claims,
            supported_claims=doc_summary.supported_claims,
            contradicted_claims=doc_summary.contradicted_claims,
            unknown_claims=doc_summary.unknown_claims,
            non_factual_claims=doc_summary.non_factual_claims,
            trust_score=doc_summary.trust_score,
            calibrated_confidence=None,
            is_calibrated=False,
            calibration_status="NOT_CALIBRATED",
            degraded_evaluation=any(
                c.get("degraded_evaluation", False) for c in claims_processed
            ),
            summary=doc_summary.summary_text,
            created_at=now_utc,
            completed_at=completed_at,
            claims=response_claims,
            audit_trail=response_audit,
        )
