#!/usr/bin/env python3
"""CLI demonstration tool for VerifAI claim verification pipeline.

Usage:
    python scripts/verify.py --text "Water has the chemical formula H2O."
    python scripts/verify.py --text "Apollo 11 landed in 1975." --json
    python scripts/verify.py --text "In my view, chocolate is the best flavor."
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure repository root and backend directory are in sys.path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.modules.verification.orchestrator import VerificationOrchestrator  # noqa: E402
from app.schemas.verification import (  # noqa: E402
    VerificationCreateRequest,
    VerificationOptions,
)


def format_report_terminal(resp: dict) -> str:
    """Render a clean, human-readable terminal report."""
    lines = [
        "=" * 74,
        "VerifAI — Claim Verification & Hallucination Risk Report",
        "=" * 74,
        f"Verification ID:    {resp['verification_id']}",
        f"Pipeline Status:    {resp['status']}",
        f"Content Type:       {resp['content_type']}",
        f"Document Trust:     {resp['trust_score']}%"
        if resp["trust_score"] is not None
        else "Document Trust:     N/A (Non-verifiable/exempt)",
        (
            f"Calibration Status: {resp['calibration_status']} "
            f"(is_calibrated={resp['is_calibrated']})"
        ),
        f"Summary:            {resp['summary']}",
        "-" * 74,
        (
            f"CLAIMS SUMMARY ({resp['total_claims']} total: "
            f"{resp['supported_claims']} supported, "
            f"{resp['contradicted_claims']} contradicted, "
            f"{resp['unknown_claims']} unknown, "
            f"{resp['non_factual_claims']} non-factual)"
        ),
        "-" * 74,
    ]

    for c in resp.get("claims", []):
        verdict_color = c["verdict"]
        lines.append(f'[{c["claim_index"] + 1}] Claim: "{c["claim_text"]}"')
        lines.append(
            f"    Offsets: [{c['start_offset']}:{c['end_offset']}] | "
            f"Type: {c['content_type']} | Verdict: {verdict_color}"
        )
        if c.get("unknown_reason"):
            lines.append(f"    Unknown Reason: {c['unknown_reason']}")
        if c.get("explanation"):
            lines.append(f"    Explanation:    {c['explanation']}")

        # Evidence
        evidence = c.get("evidence", [])
        if evidence:
            lines.append(f"    Evidence Passages ({len(evidence)}):")
            for ev in evidence:
                title = ev.get("source_title") or "Source"
                lines.append(f"      * [{ev['retriever_name']}] {title}")
                if ev.get("source_url"):
                    lines.append(f"        URL:       {ev['source_url']}")
                lines.append(f'        Snippet:   "{ev["snippet"][:120]}..."')
                lines.append(
                    f"        Authority: {ev.get('authority_score')} | "
                    f"Relevance: {ev.get('relevance_score')}"
                )
        else:
            lines.append("    Evidence Passages: None retrieved")

        # Judges
        judges = c.get("judges", [])
        if judges:
            lines.append(f"    Judge Evaluations ({len(judges)}):")
            for j in judges:
                lines.append(
                    f"      * {j['judge_name']}: {j['judgment']} — {j.get('rationale')}"
                )

        lines.append("")

    lines.append("-" * 74)
    lines.append(f"AUDIT TRAIL ({len(resp.get('audit_trail', []))} events):")
    for ar in resp.get("audit_trail", []):
        lines.append(
            f"  [{ar['timestamp'][:19]}] [{ar['stage']}] {ar['event_type']} "
            f"({ar['status']}): {ar['message']}"
        )
    lines.append("=" * 74)
    return "\n".join(lines)


async def run_verification(
    text: str,
    query: str | None = None,
    live_search: bool = False,
    as_json: bool = False,
) -> int:
    """Execute verification pipeline and display report."""
    request = VerificationCreateRequest(
        text=text,
        query=query,
        options=VerificationOptions(
            enable_live_search=live_search,
            strict_consensus=True,
        ),
    )

    orchestrator = VerificationOrchestrator()
    response = await orchestrator.verify(request=request, db_session=None)
    data = response.model_dump(mode="json")

    if as_json:
        print(json.dumps(data, indent=2))
    else:
        print(format_report_terminal(data))

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="VerifAI — Claim Verification & Hallucination Risk Pipeline CLI"
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        required=True,
        help="Text to decompose and verify for hallucinations.",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default=None,
        help="Optional original prompt or context query.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Attempt live web retrieval (Wikipedia public API).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw structured JSON envelope.",
    )

    args = parser.parse_args()
    code = asyncio.run(
        run_verification(
            text=args.text,
            query=args.query,
            live_search=args.live,
            as_json=args.json,
        )
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
