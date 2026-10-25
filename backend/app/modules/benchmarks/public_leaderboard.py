"""Public benchmark snapshot, sourced exclusively from LiveBench 2.0.

VerifAI's own accuracy/grounding leaderboard is intentionally separate. These
numbers come from an independent public benchmark, *not* VerifAI model tests.
Snapshot refresh is invoked by a weekly job; HTTP GET never scrapes live sites.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger("verifai.benchmarks.public")

SOURCE_URL = "https://livebench.ai/"
SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "public_model_leaderboard.json"
)
# LiveBench v2 CSV/official suite names. These are not VerifAI claim checks.
SUITES = {
    "agentic": "long_agentic",
    "design": "design",
    "coding": "coding",
    "browser": "browser",
    "data_analysis": "data_analysis",
    "research": "research",
    "reasoning": "reasoning",
}
MIN_MODEL_COUNT = 20
MAX_BYTES = 2_000_000


class PublicBenchmarkRefreshError(ValueError):
    """No partial or made-up leaderboard may replace the last valid snapshot."""


def _get_text(client: httpx.Client, url: str, max_bytes: int = MAX_BYTES) -> str:
    if not url.startswith(SOURCE_URL):
        raise PublicBenchmarkRefreshError("Untrusted leaderboard data origin")
    response = client.get(url, follow_redirects=False)
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise PublicBenchmarkRefreshError("Leaderboard source unexpectedly large")
    return response.text


def _parse_score(raw: str | None) -> float | None:
    if raw is None or raw.strip() in ("", "-", "—", "null"):
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise PublicBenchmarkRefreshError("Unexpected source score") from exc
    if not math.isfinite(value) or value < 0 or value > 100:
        raise PublicBenchmarkRefreshError("Leaderboard score outside 0..100")
    return value


def construct_snapshot(
    *,
    table_csv: str,
    categories_json: str,
    model_metadata: dict[str, tuple[str, str]],
    release_id: str,
    source_last_updated: str,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"20\d{6}", release_id):
        raise PublicBenchmarkRefreshError("Invalid source benchmark release")
    try:
        category_data = json.loads(categories_json)
        if not isinstance(category_data, dict):
            raise ValueError
    except (ValueError, TypeError) as exc:
        raise PublicBenchmarkRefreshError(
            "Invalid LiveBench category metadata"
        ) from exc
    weights = category_data.get("_overall_weights", {})
    if not isinstance(weights, dict):
        weights = {}
    cols: dict[str, tuple[str, float]] = {}
    for display, column in SUITES.items():
        matching = category_data.get(
            {
                "agentic": "Long Agentic",
                "browser": "Browser",
                "data_analysis": "Data Analysis",
            }.get(display, display.title())
        )
        if not isinstance(matching, list) or matching != [column]:
            raise PublicBenchmarkRefreshError(
                "LiveBench suite schema changed; manual review required"
            )
        source_category = {
            "agentic": "Long Agentic",
            "browser": "Browser",
            "data_analysis": "Data Analysis",
        }.get(display, display.title())
        weight = float(weights.get(source_category, 1))
        if not math.isfinite(weight) or weight <= 0:
            raise PublicBenchmarkRefreshError("Invalid LiveBench suite weight")
        cols[display] = (column, weight)
    reader = csv.DictReader(io.StringIO(table_csv))
    if (
        not reader.fieldnames
        or set(SUITES.values()) - set(reader.fieldnames)
        or "model" not in reader.fieldnames
    ):
        raise PublicBenchmarkRefreshError("LiveBench table columns changed")
    gathered = []
    seen = set()
    for line in reader:
        model_id = (line.get("model") or "").strip()
        if model_id in seen:
            raise PublicBenchmarkRefreshError("Duplicated model entry")
        seen.add(model_id)
        # Only use source-declared identity; guessing makers from a slug is unsafe.
        details = model_metadata.get(model_id)
        if not details:
            logger.warning(
                "Skipped public model without source identity metadata: %s", model_id
            )
            continue
        scores = {
            key: _parse_score(line.get(column)) for key, (column, _) in cols.items()
        }
        scored = [
            (score, cols[key][1]) for key, score in scores.items() if score is not None
        ]
        if not scored:
            continue
        overall = sum(score * weight for score, weight in scored) / sum(
            weight for _, weight in scored
        )
        gathered.append(
            {
                "id": model_id,
                "name": details[0],
                "organization": details[1],
                "overall_score": round(overall, 1),
                "suite_scores": scores,
                "suite_coverage": len(scored),
            }
        )
    if len(gathered) < MIN_MODEL_COUNT:
        raise PublicBenchmarkRefreshError("Too few valid models in official release")
    gathered.sort(key=lambda m: (-m["overall_score"], m["name"].lower()))
    for index, model in enumerate(gathered, 1):
        model["rank"] = index
    try:
        updated = datetime.strptime(source_last_updated, "%d %B %Y")
        release = datetime.strptime(release_id, "%Y%m%d")
    except ValueError as exc:
        raise PublicBenchmarkRefreshError("Invalid benchmark publication date") from exc
    if updated < release:
        raise PublicBenchmarkRefreshError("Source update precedes benchmark release")
    retrieved = retrieved_at or datetime.now(UTC)
    if retrieved.tzinfo is None:
        raise PublicBenchmarkRefreshError("Retrieved timestamp must be timezone aware")
    return {
        "schema_version": 1,
        "benchmark": "LiveBench 2.0",
        "benchmark_release": release.strftime("%Y-%m-%d"),
        "source_updated_at": updated.strftime("%Y-%m-%d"),
        "retrieved_at": retrieved.astimezone(UTC).isoformat(),
        "source_url": SOURCE_URL,
        "data_url": f"{SOURCE_URL}data/{release_id}/table.csv",
        "methodology_url": f"{SOURCE_URL}#/methodology",
        "refresh_policy": "weekly",
        "score_description": (
            "Mean of available LiveBench 2.0 task-suite scores (0–100), "
            "weighted only when specified by LiveBench; these are not "
            "VerifAI hallucination, citation, or evidence-verification scores."
        ),
        "total_models": len(gathered),
        "models": gathered,
    }


def fetch_livebench_snapshot(client: httpx.Client | None = None) -> dict[str, Any]:
    """Fetch official CSV and identity metadata. Fail closed if the site changes."""

    def fetch(active: httpx.Client) -> dict[str, Any]:
        html = _get_text(active, SOURCE_URL)
        script_paths = re.findall(
            r'<script[^>]+src="(\./static/js/main\.[a-zA-Z0-9]+\.js)"', html
        )
        if len(script_paths) != 1:
            raise PublicBenchmarkRefreshError(
                "Cannot locate official LiveBench client manifest"
            )
        js = _get_text(active, urljoin(SOURCE_URL, script_paths[0]), 3_000_000)
        releases = re.search(r"Yt=\[([^\]]+)\]", js)
        release_ids = re.findall(r'"(20\d{6})"', releases.group(1)) if releases else []
        if not release_ids:
            raise PublicBenchmarkRefreshError("No LiveBench 2.0 release found")
        release_id = max(release_ids)
        updated_match = re.search(r'Xt="(\d{1,2} [A-Za-z]+ 20\d{2})"', js)
        if not updated_match:
            raise PublicBenchmarkRefreshError("Source update date not published")
        # Model names and organizations are maintained by the LiveBench team in
        # their published client manifest; never execute downloaded JavaScript.
        metadata = {
            slug: (name, maker)
            for slug, name, maker in re.findall(
                r'"([^"\\]+)":\{displayName:"([^"\\]+)",organization:"([^"\\]+)"',
                js,
            )
        }
        if len(metadata) < MIN_MODEL_COUNT:
            raise PublicBenchmarkRefreshError("LiveBench model metadata unavailable")
        prefix = f"{SOURCE_URL}data/{release_id}/"
        return construct_snapshot(
            table_csv=_get_text(active, prefix + "table.csv"),
            categories_json=_get_text(active, prefix + "categories.json"),
            model_metadata=metadata,
            release_id=release_id,
            source_last_updated=updated_match.group(1),
        )

    if client is not None:
        return fetch(client)
    with httpx.Client(
        timeout=httpx.Timeout(20.0),
        trust_env=False,
        headers={
            "User-Agent": "VerifAI-Leaderboard/1.0 (source-attributed weekly fetch)"
        },
    ) as active:
        return fetch(active)


def load_public_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    """Return the last verified release. Never regenerate scores in a read request."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PublicBenchmarkRefreshError(
            "Public leaderboard snapshot unavailable"
        ) from exc
    if (
        not isinstance(doc, dict)
        or doc.get("schema_version") != 1
        or doc.get("benchmark") != "LiveBench 2.0"
        or len(doc.get("models", [])) < MIN_MODEL_COUNT
        or doc.get("total_models") != len(doc["models"])
        or doc.get("source_url") != SOURCE_URL
    ):
        raise PublicBenchmarkRefreshError("Public leaderboard snapshot invalid")
    return doc


def refresh_public_snapshot(
    path: Path = SNAPSHOT_PATH, client: httpx.Client | None = None
) -> tuple[dict[str, Any], bool]:
    """Atomic snapshot swap; retain the previous valid snapshot on failure."""
    snapshot = fetch_livebench_snapshot(client)
    try:
        previous = load_public_snapshot(path)
    except PublicBenchmarkRefreshError:
        previous = None
    if previous and previous["source_updated_at"] > snapshot["source_updated_at"]:
        raise PublicBenchmarkRefreshError("Source is older than last saved benchmark")
    # Avoid noisy weekly commits if upstream has not published new observations.
    same_data = bool(
        previous
        and previous["benchmark_release"] == snapshot["benchmark_release"]
        and previous["source_updated_at"] == snapshot["source_updated_at"]
        and previous["models"] == snapshot["models"]
    )
    if same_data:
        return previous, False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".public-model-leaderboard-",
            suffix=".json",
            delete=False,
        ) as fp:
            tmp_path = Path(fp.name)
            json.dump(snapshot, fp, ensure_ascii=False, indent=2, allow_nan=False)
            fp.write("\n")
            fp.flush()
            os.fsync(fp.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
    return snapshot, True
