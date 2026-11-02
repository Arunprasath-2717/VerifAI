"""Regression checks for Vercel Services public routing."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_service_routing_preserves_api_and_spa_deep_links():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert config["services"]["backend"]["root"] == "backend"
    assert config["services"]["backend"]["entrypoint"] == "app.main:app"
    assert config["services"]["frontend"]["root"] == "frontend"
    assert {"source": "/(.*)", "destination": "/index.html"} in config["services"]["frontend"]["rewrites"]
    rewrites = config["rewrites"]
    assert rewrites[0]["source"] == "/api/(.*)"
    assert rewrites[0]["destination"] == {"service": "backend"}
    assert rewrites[-1]["destination"] == {"service": "frontend"}


def test_auth_artwork_is_optimized_and_referenced():
    asset = ROOT / "frontend/src/assets/auth-illustration.webp"
    assert asset.is_file() and asset.stat().st_size < 500_000
    page = (ROOT / "frontend/src/pages/SignupPage.tsx").read_text(encoding="utf-8")
    assert "../assets/auth-illustration.webp" in page
