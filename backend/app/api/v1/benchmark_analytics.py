from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.benchmark_service import BenchmarkService

router = APIRouter(prefix="/api/v1/benchmark", tags=["Benchmark Analytics"])

# Arun's stub endpoints for completeness
@router.get("")
def list_benchmarks():
    return {
        "benchmarks": BenchmarkService.list_benchmarks()
    }

@router.get("/compare")
def compare_benchmarks(
    benchmark_ids: Optional[str] = Query(None, description="Comma-separated benchmark IDs")
):
    bm_list = [b.strip() for b in benchmark_ids.split(",") if b.strip()] if benchmark_ids else None
    return {
        "comparison": BenchmarkService.compare_benchmarks(bm_list)
    }

@router.get("/{benchmark_id}")
def get_benchmark_detail(benchmark_id: str):
    detail = BenchmarkService.get_benchmark_detail(benchmark_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")
    return detail

@router.get("/{benchmark_id}/metrics")
def get_benchmark_metrics(benchmark_id: str):
    metrics = BenchmarkService.get_benchmark_metrics(benchmark_id)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Metrics for benchmark '{benchmark_id}' not found.")
    return metrics

@router.get("/{benchmark_id}/models")
def get_benchmark_models(benchmark_id: str):
    models = BenchmarkService.get_benchmark_models(benchmark_id)
    return {
        "benchmark_id": benchmark_id,
        "models": models
    }

@router.get("/{benchmark_id}/claims")
def get_benchmark_claims(
    benchmark_id: str,
    model_id: Optional[str] = Query(None, description="Filter claims by model ID")
):
    claims = BenchmarkService.get_benchmark_claims(benchmark_id, model_id=model_id)
    return {
        "benchmark_id": benchmark_id,
        "model_id": model_id,
        "total_claims": len(claims),
        "claims": claims
    }
