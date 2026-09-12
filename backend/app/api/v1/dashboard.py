from fastapi import APIRouter, Query
from typing import Optional
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Trust Dashboard"])

@router.get("/overview")
def get_overview(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    model_id: Optional[str] = Query(None, description="Model ID filter"),
    verdict: Optional[str] = Query(None, description="Verdict filter (SUPPORTED, CONTRADICTED, INCONCLUSIVE)"),
    domain: Optional[str] = Query(None, description="Domain filter")
):
    return AnalyticsService.get_overview(date_from, date_to, model_id, verdict, domain)

@router.get("/trust-score")
def get_trust_score(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_trust_score(date_from, date_to, model_id, verdict, domain)

@router.get("/verification-stats")
def get_verification_stats(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_verification_stats(date_from, date_to, model_id, verdict, domain)

@router.get("/hallucination-rate")
def get_hallucination_rate(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_hallucination_rate(date_from, date_to, model_id, verdict, domain)

@router.get("/confidence")
def get_confidence(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_confidence(date_from, date_to, model_id, verdict, domain)

@router.get("/signal-quality")
def get_signal_quality(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_signal_quality(date_from, date_to, model_id, verdict, domain)

@router.get("/evidence-quality")
def get_evidence_quality(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_evidence_quality(date_from, date_to, model_id, verdict, domain)

@router.get("/trends")
def get_trends(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_trends(date_from, date_to, model_id, verdict, domain)

@router.get("/domains")
def get_domains(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_domains(date_from, date_to, model_id, verdict, domain)

@router.get("/models")
def get_models(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None),
    domain: Optional[str] = Query(None)
):
    return AnalyticsService.get_models(date_from, date_to, model_id, verdict, domain)

@router.get("/filters")
def get_filters():
    return AnalyticsService.get_filters()
