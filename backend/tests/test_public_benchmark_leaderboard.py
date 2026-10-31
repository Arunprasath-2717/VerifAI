"""Public leaderboard integrity: only source scores, no fabricated VerifAI metrics."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.api.v1.endpoints.models import get_public_benchmarks
from app.modules.benchmarks import public_leaderboard as board


@pytest.fixture()
def livebench_fixture():
    columns = (
        "model,long_agentic,reasoning,coding,browser,data_analysis,research,design"
    )
    records = [f"eval-{i},20,{50 + i},70,80,90,60,40" for i in range(24)]
    names = {f"eval-{i}": (f"Eval Model {i}", "Test Organization") for i in range(24)}
    categories = """{"Long Agentic":["long_agentic"],"Reasoning":["reasoning"],
    "Coding":["coding"],"Browser":["browser"],"Data Analysis":["data_analysis"],
    "Research":["research"],"Design":["design"]}"""
    return (columns + "\n" + "\n".join(records), categories, names)


def test_checked_in_public_snapshot_has_correct_provenance_and_scores():
    snapshot = board.load_public_snapshot()
    assert snapshot["source_url"] == "https://livebench.ai/"
    assert snapshot["benchmark"] == "LiveBench 2.0"
    assert snapshot["total_models"] >= 20
    assert snapshot["source_updated_at"] >= snapshot["benchmark_release"]
    assert all(
        model["rank"] == index for index, model in enumerate(snapshot["models"], 1)
    )
    scores = [model["overall_score"] for model in snapshot["models"]]
    assert scores == sorted(scores, reverse=True)
    for model in snapshot["models"]:
        assert 1 <= model["suite_coverage"] <= 7
        used = [v for v in model["suite_scores"].values() if v is not None]
        assert len(used) == model["suite_coverage"]
        assert all(0 <= value <= 100 for value in used)
        assert abs(sum(used) / len(used) - model["overall_score"]) < 0.06
        assert "factualSupport" not in model
        assert "citationPrecision" not in model


def test_missing_benchmark_is_null_not_zero_or_invented(livebench_fixture):
    csv_text, categories, names = livebench_fixture
    csv_text = csv_text.replace(
        "eval-0,20,50,70,80,90,60,40", "eval-0,20,,70,80,90,60,40", 1
    )
    source = board.construct_snapshot(
        table_csv=csv_text,
        categories_json=categories,
        model_metadata=names,
        release_id="20261014",
        source_last_updated="23 October 2026",
        retrieved_at=datetime(2026, 10, 24, tzinfo=UTC),
    )
    row = next(model for model in source["models"] if model["id"] == "eval-0")
    assert row["suite_scores"]["reasoning"] is None
    assert row["suite_coverage"] == 6
    assert row["overall_score"] == 60.0


def test_invalid_source_never_replaces_last_snapshot(monkeypatch, tmp_path: Path):
    file = tmp_path / "snapshot.json"
    file.write_text('{"last_valid":true}', encoding="utf-8")

    def fail(*args, **kwargs):
        raise board.PublicBenchmarkRefreshError("schema changed")

    monkeypatch.setattr(board, "fetch_livebench_snapshot", fail)
    with pytest.raises(board.PublicBenchmarkRefreshError):
        board.refresh_public_snapshot(file)
    assert file.read_text(encoding="utf-8") == '{"last_valid":true}'


@pytest.mark.parametrize("date_variable", ["Xt", "Zt"])
def test_official_source_fetching_uses_fixed_host_and_validated_metadata(
    livebench_fixture, date_variable
):
    table, categories, names = livebench_fixture
    js = (
        f'const Yt=["20261014"],{date_variable}="23 October 2026";var mn={{'
        + ",".join(
            f'"{slug}":{{displayName:"{name}",organization:"{maker}"}}'
            for slug, (name, maker) in names.items()
        )
        + "};"
    )
    html = '<script defer="defer" src="./static/js/main.test123.js"></script>'

    def handle(req: httpx.Request):
        assert req.url.host == "livebench.ai"
        path = req.url.path
        if path == "/":
            content = html
        elif path.endswith("/static/js/main.test123.js"):
            content = js
        elif path.endswith("/table.csv"):
            content = table
        elif path.endswith("/categories.json"):
            content = categories
        else:
            return httpx.Response(404)
        return httpx.Response(200, text=content)

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = board.fetch_livebench_snapshot(client)
    assert result["total_models"] == 24
    assert result["source_updated_at"] == "2026-10-23"
    assert result["models"][0]["name"] == "Eval Model 23"


def test_api_serves_valid_saved_public_snapshot():
    response = asyncio.run(get_public_benchmarks())
    assert response.total_models >= 20
    assert response.models[0].rank == 1
    assert response.models[0].overall_score > 0
    assert response.benchmark_release[:4] == "2026"
