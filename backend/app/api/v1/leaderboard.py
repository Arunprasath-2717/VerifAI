from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.leaderboard_service import LeaderboardService, AVAILABLE_LEADERBOARD_METRICS

router = APIRouter(prefix="/api/v1/leaderboard", tags=["Model Leaderboard"])

@router.get("")
def get_leaderboard(
    sort_by: str = Query("verification_accuracy", description="Metric to sort models by"),
    order: str = Query("desc", description="Sort order: asc or desc")
):
    return {
        "models": LeaderboardService.get_leaderboard(sort_by=sort_by, order=order),
        "sort_by": sort_by,
        "order": order
    }

@router.get("/metrics")
def get_leaderboard_metrics():
    return {
        "metrics": AVAILABLE_LEADERBOARD_METRICS
    }

@router.get("/compare")
def compare_models(
    models: str = Query(..., description="Comma-separated model IDs e.g. llama-3.1-70b,qwen-2.5-72b,gpt-4o")
):
    model_list = [m.strip() for m in models.split(",") if m.strip()]
    if not model_list:
        raise HTTPException(status_code=400, detail="At least one model ID must be specified.")
    return LeaderboardService.compare_models(model_list)

@router.get("/{model_id}")
def get_model_detail(model_id: str):
    detail = LeaderboardService.get_model_detail(model_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in verification logs.")
    return detail
