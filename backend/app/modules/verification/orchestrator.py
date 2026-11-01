"""Pipeline orchestrator coordinating the verification lifecycle."""

import asyncio
import logging
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ServiceUnavailableError
from app.models.verification import (
    AuditRecord,
    ExtractedClaim,
    JudgeVerdict,
    RetrievedEvidence,
    VerificationJob,
)
from app.modules.chat.safety import assert_safe_outbound_prompt
from app.modules.claims.classifier import ContentClassifier
from app.modules.claims.extractor import (
    BaseClaimExtractor,
    DeterministicClaimExtractor,
)
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.live_retriever import LiveWebRetriever
from app.modules.evidence.local_retriever import LocalPassageRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.decision import DecisionEngine
from app.modules.judging.deterministic_judge import DeterministicRuleJudge
from app.modules.judging.disagreement import DisagreementEngine
from app.modules.judging.injection_detector import detect_injection_markers
from app.modules.judging.interface import BaseJudge
from app.modules.judging.model_judge import OpenSourceModelJudge
from app.modules.judging.models import JudgeEvaluationData
from app.modules.judging.semantic_judge import SecondarySemanticJudge
from app.modules.knowledge.retriever import KBSearchResult, PrivateKBRetriever
from app.modules.knowledge.service import KnowledgeBaseService
from app.modules.token_budget import (
    AnalysisBudgetManager,
    AnalysisCacheService,
    BudgetExhaustedError,
    UserDailyBudgetTracker,
)
from app.repositories.token_usage import TokenUsageRepository
from app.schemas.knowledge import KBSufficiencyStatus
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


class _NoEvidenceRetriever(BaseEvidenceRetriever):
    """Null object used when no evidence source is configured (e.g. production).

    Returns no passages, so claims that need external evidence resolve to UNKNOWN.
    """

    @property
    def name(self) -> str:
        return "NO_EVIDENCE_SOURCE"

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        return []


class VerificationOrchestrator:
    """Coordinates extraction, retrieval, judging, and audit lifecycle."""

    def __init__(
        self,
        extractor: BaseClaimExtractor | None = None,
        classifier: ContentClassifier | None = None,
        retriever: BaseEvidenceRetriever | None = None,
        kb_retriever: PrivateKBRetriever | None = None,
        kb_service: KnowledgeBaseService | None = None,
        judges: list[BaseJudge] | None = None,
        tie_breaker_judge: BaseJudge | None = None,
        disagreement_engine: DisagreementEngine | None = None,
        decision_engine: DecisionEngine | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.extractor = extractor or DeterministicClaimExtractor()
        self.classifier = classifier or ContentClassifier()
        # The bundled demo passage index is for development/testing only. In
        # production it must not be presented as evidence; with no retriever,
        # claims resolve to UNKNOWN instead of citing demo text.
        if retriever is None:
            retriever = (
                LocalPassageRetriever()
                if self.settings.is_development
                else _NoEvidenceRetriever()
            )
        self.retriever = retriever
        self.kb_retriever = kb_retriever
        self.kb_service = kb_service
        self.judges = judges or [
            DeterministicRuleJudge(name="Judge-Primary-Deterministic"),
            SecondarySemanticJudge(name="Judge-Secondary-Semantic"),
        ]
        self.tie_breaker_judge = tie_breaker_judge
        if self.tie_breaker_judge is None and self.settings.JUDGE_MODEL_ENDPOINT:
            self.tie_breaker_judge = OpenSourceModelJudge(
                endpoint_url=self.settings.JUDGE_MODEL_ENDPOINT,
                model_name=self.settings.JUDGE_MODEL_NAME,
            )
        self.disagreement_engine = disagreement_engine or DisagreementEngine()
        self.decision_engine = decision_engine or DecisionEngine()

    async def verify(
        self,
        request: VerificationCreateRequest,
        db_session: AsyncSession | None = None,
    ) -> VerificationResponse:
        """Execute full verification pipeline for the given input text."""
        # Operator input cap (VERIFICATION_MAX_INPUT_CHARS) is enforced before any
        # cache lookup, extraction, or retrieval work starts.
        if len(request.text) > self.settings.VERIFICATION_MAX_INPUT_CHARS:
            raise AppError(
                message=(
                    "Input exceeds the configured maximum of "
                    f"{self.settings.VERIFICATION_MAX_INPUT_CHARS} characters."
                ),
                code="VALIDATION_ERROR",
                status_code=422,
            )
        # Credentials must never reach a model judge, retrieval query, the cache,
        # or the persisted input_text. Block before any of those run.
        assert_safe_outbound_prompt(request.text)
        # ── Cache lookup ────────────────────────────────────────────────────────
        effective_owner_early = request.options.owner_id or "anonymous"
        _cache = AnalysisCacheService.get_instance()
        _cache_hash = AnalysisCacheService.compute_hash(
            text=request.text,
            query=request.query,
            options=request.options.model_dump(exclude_none=True),
        )
        cached_response = _cache.get(effective_owner_early, _cache_hash)
        if cached_response is not None:
            logger.info(
                "Cache HIT for owner=%s — returning cached analysis (hash=%s).",
                effective_owner_early,
                _cache_hash[:12],
            )
            return cached_response

        # ── Daily budget guard ─────────────────────────────────────────────────
        _daily_tracker = UserDailyBudgetTracker.get_instance()
        await _daily_tracker.check_and_increment_analysis(
            user_id=effective_owner_early,
            daily_max_analyses=self.settings.USER_DAILY_ANALYSIS_LIMIT,
        )

        # ── Per-analysis token budget ─────────────────────────────────────────
        budget_limit = getattr(self.settings, "MAX_TOKENS_PER_ANALYSIS", 20_000)
        budget = AnalysisBudgetManager(
            analysis_id=uuid.uuid4(),  # separate from verification_id
            owner_id=effective_owner_early,
            budget_limit=budget_limit,
            settings=self.settings,
        )

        verification_id = uuid.uuid4()
        now_utc = datetime.now(UTC)
        audit_records: list[AuditRecord] = []
        # Isolate audit records per task; consolidate in claim order after gather.
        audit_sink: ContextVar[list[AuditRecord] | None] = ContextVar(
            "verification_claim_audit", default=None
        )

        def log_audit(
            stage: str,
            event_type: str,
            status: str,
            message: str,
            details: dict[str, Any] | None = None,
        ) -> None:
            sink = audit_sink.get()
            (sink if sink is not None else audit_records).append(
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

        # Operator cap (VERIFICATION_MAX_CLAIMS) bounds whatever the client asks for.
        max_claims = min(
            request.options.max_claims,
            self.settings.VERIFICATION_MAX_CLAIMS,
        )
        extracted_items = self.extractor.extract(request.text, max_claims=max_claims)

        log_audit(
            stage="EXTRACTION",
            event_type="STAGE_COMPLETED",
            status="SUCCESS",
            message=f"Extracted {len(extracted_items)} atomic claims.",
            details={"claims_count": len(extracted_items)},
        )

        # Configure external evidence retriever (live web or local index)
        active_retriever = self.retriever
        live_search_enabled = (
            request.options.enable_live_search or self.settings.ENABLE_LIVE_SEARCH
        )
        if live_search_enabled:
            active_retriever = LiveWebRetriever.from_settings()
            log_audit(
                stage="RETRIEVAL",
                event_type="PROVIDER_SELECTED",
                status="SUCCESS",
                message=(
                    "Live web search enabled: "
                    "Tavily → DuckDuckGo → Nightcrawler cascade."
                ),
                details={"retriever": active_retriever.name},
            )

        # Configure private knowledge base service and retriever for this execution
        active_kb_service = self.kb_service or KnowledgeBaseService(
            db_session=db_session
        )
        active_kb_retriever = self.kb_retriever or PrivateKBRetriever(
            service=active_kb_service,
            owner_id=request.options.owner_id,
        )

        # Process each claim through classification, retrieval, and judging
        claims_processed: list[dict[str, Any]] = []
        db_claims: list[ExtractedClaim] = []

        async def process_claim(
            item: Any,
        ) -> tuple[dict[str, Any], ExtractedClaim, list[AuditRecord]]:
            claim_audit: list[AuditRecord] = []
            audit_token = audit_sink.set(claim_audit)
            # Step 2: Content Classification
            classification = self.classifier.classify(item.text)

            evidence_items: list[RetrievedEvidenceItem] = []
            judge_evaluations: list[JudgeEvaluationData] = []
            claim_verdict = classification.verdict
            unknown_reason = None
            explanation = classification.explanation

            if classification.is_verifiable:
                kb_evidence: list[RetrievedEvidenceItem] = []
                external_evidence: list[RetrievedEvidenceItem] = []
                kb_hit = False

                # Step 3A: Search Private Knowledge Base
                if request.options.enable_kb_search:
                    log_audit(
                        stage="RETRIEVAL",
                        event_type="KB_SEARCH_STARTED",
                        status="SUCCESS",
                        message=f"Searching private KB for claim {item.index}.",
                        details={
                            "claim_index": item.index,
                            "owner_id": request.options.owner_id,
                        },
                    )
                    try:
                        kb_result: KBSearchResult = await active_kb_retriever.search(
                            claim_text=item.text,
                            owner_id=request.options.owner_id,
                            threshold=request.options.kb_relevance_threshold,
                        )
                        if kb_result.sufficiency == KBSufficiencyStatus.KB_RELEVANT:
                            kb_hit = True
                            kb_evidence = kb_result.evidence_items
                            log_audit(
                                stage="RETRIEVAL",
                                event_type="KB_HIT",
                                status="SUCCESS",
                                message=(
                                    f"Sufficient KB evidence for claim {item.index}: "
                                    f"{len(kb_evidence)} passage(s)."
                                ),
                                details={
                                    "claim_index": item.index,
                                    "passages": len(kb_evidence),
                                    "top_score": kb_result.top_score,
                                },
                            )
                        else:
                            log_audit(
                                stage="RETRIEVAL",
                                event_type="KB_MISS",
                                status="INFO",
                                message=(
                                    f"Private KB: {kb_result.sufficiency.value} "
                                    f"for claim {item.index}."
                                ),
                                details={
                                    "claim_index": item.index,
                                    "sufficiency": kb_result.sufficiency.value,
                                    "top_score": kb_result.top_score,
                                },
                            )
                    except Exception as kb_exc:
                        logger.warning(
                            "KB retrieval failed for claim %d: %s", item.index, kb_exc
                        )
                        log_audit(
                            stage="RETRIEVAL",
                            event_type="KB_ERROR",
                            status="WARNING",
                            message=f"KB error on claim {item.index}: {kb_exc}",
                            details={"error": type(kb_exc).__name__},
                        )

                # Step 3B: External Retrieval (if KB insufficient or corroboration)
                should_search_external = (
                    not kb_hit or request.options.force_external_retrieval
                )

                if should_search_external:
                    log_audit(
                        stage="RETRIEVAL",
                        event_type="EXTERNAL_RETRIEVAL_STARTED",
                        status="SUCCESS",
                        message=f"Searching external provider for claim {item.index}.",
                        details={
                            "provider": active_retriever.name,
                            "claim_index": item.index,
                        },
                    )
                    try:
                        ext_items = await asyncio.wait_for(
                            active_retriever.retrieve(
                                claim_text=item.text,
                                max_passages=3,
                            ),
                            timeout=self.settings.RETRIEVAL_TIMEOUT_SECONDS,
                        )
                        external_evidence = ext_items
                    except Exception as exc:
                        logger.warning(
                            "External retrieval failed for claim %d: %s",
                            item.index,
                            exc,
                        )
                        log_audit(
                            stage="RETRIEVAL",
                            event_type="DEGRADED_EXECUTION",
                            status="WARNING",
                            message=f"External retrieval failed on claim {item.index}.",
                            details={
                                "error": type(exc).__name__,
                                "claim_text": item.text,
                            },
                        )

                # Combine evidence passages according to orchestration policy
                if kb_hit and not request.options.force_external_retrieval:
                    evidence_items = kb_evidence
                elif request.options.force_external_retrieval:
                    evidence_items = kb_evidence + external_evidence
                else:
                    evidence_items = external_evidence

                if evidence_items:
                    ev_srcs = {ev.evidence_source for ev in evidence_items}
                    srcs = ", ".join(sorted(ev_srcs))
                    # Advisory only: flag instruction-like text in untrusted inputs for
                    # review. Containment is prompt isolation, not this scan.
                    injection_hits = {
                        ev.id: detect_injection_markers(ev.snippet or "")
                        for ev in evidence_items
                    }
                    injection_hits = {k: v for k, v in injection_hits.items() if v}
                    if injection_hits:
                        log_audit(
                            stage="RETRIEVAL",
                            event_type="INJECTION_MARKERS_DETECTED",
                            status="WARNING",
                            message=(
                                f"Instruction-like text found in {len(injection_hits)} "
                                f"evidence passage(s) for claim {item.index}; "
                                "treated as data. Categories: "
                                + "; ".join(
                                    f"{k}={','.join(v)}"
                                    for k, v in injection_hits.items()
                                )
                            ),
                            details={
                                "claim_index": item.index,
                                "passages": {
                                    str(k): v for k, v in injection_hits.items()
                                },
                            },
                        )
                    log_audit(
                        stage="RETRIEVAL",
                        event_type="EVIDENCE_SELECTED",
                        status="SUCCESS",
                        message=(
                            f"Selected {len(evidence_items)} evidence passage(s) "
                            f"for claim {item.index} (sources: {srcs})."
                        ),
                        details={
                            "claim_index": item.index,
                            "evidence_sources": [
                                ev.evidence_source for ev in evidence_items
                            ],
                        },
                    )

                # Step 4: Independent Judge Evaluation (budget-gated)
                if evidence_items:
                    # Evaluate primary 2 judges
                    for judge in self.judges[:2]:
                        # Reserve budget atomically: checking available tokens
                        # separately from reserve() races under concurrency.
                        combined_text = item.text + " ".join(
                            ev.snippet or "" for ev in evidence_items
                        )
                        from app.modules.token_budget.estimator import TokenEstimator

                        est_tokens = TokenEstimator.estimate_tokens(combined_text)
                        try:
                            reservation_id = await budget.reserve(est_tokens)
                        except BudgetExhaustedError:
                            logger.warning(
                                (
                                    "Budget exhausted before judge %s on claim %d; "
                                    "skipping."
                                ),
                                judge.name,
                                item.index,
                            )
                            judge_evaluations.append(
                                JudgeEvaluationData(
                                    judge_id=uuid.uuid4(),
                                    judge_name=judge.name,
                                    judgment=JudgeDecision.UNAVAILABLE,
                                    rationale="Token budget exhausted — judge skipped.",
                                )
                            )
                            continue
                        try:
                            eval_data = await judge.evaluate(item.text, evidence_items)
                            judge_evaluations.append(eval_data)
                            # Record actual usage (use estimate for
                            # deterministic judges)
                            await budget.record_usage(
                                operation="CLAIM_EVALUATION",
                                provider="deterministic",
                                model_name=judge.name,
                                input_tokens=est_tokens,
                                output_tokens=0,
                                is_estimated=True,
                                reservation_id=reservation_id,
                            )
                        except Exception as j_exc:
                            await budget.release_reservation(reservation_id)
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
                    if live_search_enabled:
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
                    evidence_source=ev.evidence_source,
                    document_id=ev.document_id,
                    chunk_id=ev.chunk_id,
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

            audit_sink.reset(audit_token)
            return claim_data, db_claim, claim_audit

        # A shared SQLAlchemy AsyncSession is not safe for concurrent queries.
        # Permit bounded concurrency only when claims need no shared KB session.
        concurrency = max(1, min(self.settings.VERIFICATION_CLAIM_CONCURRENCY, 8))
        if (
            db_session is not None
            or self.kb_service is not None
            or self.kb_retriever is not None
            or request.options.enable_kb_search
        ):
            concurrency = 1
        if concurrency > 1:
            semaphore = asyncio.Semaphore(concurrency)

            async def limited(item: Any):
                async with semaphore:
                    return await process_claim(item)

            completed = await asyncio.gather(
                *(limited(item) for item in extracted_items)
            )
        else:
            completed = [await process_claim(item) for item in extracted_items]

        for claim_data, db_claim, claim_audit in completed:
            claims_processed.append(claim_data)
            db_claims.append(db_claim)
            audit_records.extend(claim_audit)

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

        effective_owner = request.options.owner_id or "anonymous"
        # Step 7: Create VerificationJob Database Entity
        verification_job = VerificationJob(
            id=verification_id,
            owner_id=effective_owner,
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

        # Step 8: Database Persistence
        is_production = self.settings.ENVIRONMENT in ("production", "staging")

        if db_session is None and is_production:
            raise ServiceUnavailableError(
                "Database persistence is required in production; "
                "ephemeral execution is prohibited."
            )

        if db_session is not None:
            try:
                db_session.add(verification_job)
                await db_session.flush()  # flush first so FK exists for token_usages

                # Step 8a: Persist token usage records
                budget_status = budget.get_status()
                if budget_status.records:
                    token_repo = TokenUsageRepository(session=db_session)
                    await token_repo.save_records(
                        records=list(budget._records),  # noqa: SLF001
                        owner_id=effective_owner,
                        verification_id=verification_id,
                    )
                # Flush again to include token usage rows, then commit atomically
                await db_session.commit()

                # Update daily tracker with actual spent tokens
                await _daily_tracker.record_daily_tokens(
                    user_id=effective_owner,
                    tokens=budget_status.total_tokens,
                )

                log_audit(
                    stage="PERSISTENCE",
                    event_type="JOB_SAVED",
                    status="SUCCESS",
                    message=(
                        f"Verification job saved to database. "
                        f"Token usage: {budget_status.total_tokens} tokens, "
                        f"est. cost: ${budget_status.estimated_cost_usd:.6f}."
                    ),
                )
            except Exception as db_exc:
                logger.error("Database persistence failed: %s", db_exc)
                await db_session.rollback()
                if is_production:
                    raise ServiceUnavailableError(
                        f"Database persistence failed: {type(db_exc).__name__}"
                    ) from db_exc
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
                    evidence_source=ev.evidence_source,
                    document_id=ev.document_id,
                    chunk_id=ev.chunk_id,
                    chunk_index=ev.chunk_index,
                    document_title=ev.document_title,
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

        final_response = VerificationResponse(
            verification_id=verification_id,
            owner_id=effective_owner,
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

        # Store in tenant-isolated cache so identical future requests are free
        _cache.set(
            owner_id=effective_owner,
            cache_hash=_cache_hash,
            response=final_response,
            ttl_seconds=3600,
        )
        logger.info(
            "Cache STORE for owner=%s (hash=%s). Budget: %d/%d tokens.",
            effective_owner,
            _cache_hash[:12],
            budget.spent_tokens,
            budget.budget_limit,
        )
        return final_response
