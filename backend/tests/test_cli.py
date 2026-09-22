import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from scripts.verifai_cli import (
    DemoRunner,
    InputReader,
    MenuController,
    ProgressRenderer,
    ResultRenderer,
    TerminalStyler,
    build_parser,
    execute_verification,
    main,
    run_demo_all,
    run_demo_case,
    run_health_check,
    run_verify_command,
    run_version_info,
)


def test_cli_parser_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI parser generates help documentation."""
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "VerifAI" in captured.out
    assert "verify" in captured.out
    assert "demo" in captured.out
    assert "interactive" in captured.out


def test_cli_health_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify health check prints live system metadata."""
    code = run_health_check()
    assert code == 0
    captured = capsys.readouterr()
    assert "VERIFAI SYSTEM HEALTH CHECK" in captured.out
    assert "LIVE (Healthy)" in captured.out
    assert "verifai-backend" in captured.out


def test_cli_version_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify version command outputs release and architecture info."""
    code = run_version_info()
    assert code == 0
    captured = capsys.readouterr()
    assert "VerifAI Backend Console v0.1.0" in captured.out


def test_cli_verify_custom_text(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify custom factual assertion via verify subcommand."""
    parser = build_parser()
    args = parser.parse_args(["verify", "Water freezes at 0 degrees Celsius."])
    code = run_verify_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "CLAIM EXTRACTION" in captured.out
    assert "SUPPORTED" in captured.out
    assert "AUDIT & TRACEABILITY" in captured.out


def test_cli_verify_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify text loaded from a file."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("The Eiffel Tower is located in Berlin.", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(["verify", "--file", str(test_file)])
    code = run_verify_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "CONTRADICTED" in captured.out


def test_cli_verify_empty_input(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify empty input fails gracefully with clean validation error."""
    parser = build_parser()
    args = parser.parse_args(["verify", "   "])
    code = run_verify_command(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err
    assert "empty or whitespace" in captured.err


def test_cli_verify_compact_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify compact summary output mode."""
    parser = build_parser()
    args = parser.parse_args(
        ["verify", "Water freezes at 0 degrees Celsius.", "--compact"]
    )
    code = run_verify_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "VERIFAI COMPACT RESULT" in captured.out
    assert "Claims Total   : 1" in captured.out
    assert "Supported    : 1" in captured.out


def test_cli_verify_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify raw structured JSON output mode."""
    parser = build_parser()
    args = parser.parse_args(
        ["verify", "Water freezes at 0 degrees Celsius.", "--json"]
    )
    code = run_verify_command(args)
    assert code == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "verification_id" in parsed
    assert parsed["status"] == "COMPLETED"
    assert parsed["supported_claims"] == 1


def test_cli_demo_single_case(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify running an individual demo case."""
    code = run_demo_case("contradicted")
    assert code == 0
    captured = capsys.readouterr()
    assert "DEMO CASE: CLEARLY CONTRADICTED FACTUAL STATEMENT" in captured.out
    assert "CONTRADICTED" in captured.out


def test_cli_demo_unknown_display(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify UNKNOWN reasoning view is displayed on insufficient evidence."""
    code = run_demo_case("unknown")
    assert code == 0
    captured = capsys.readouterr()
    assert "UNKNOWN REASONING" in captured.out
    assert "CONTEXT_UNKNOWN" in captured.out
    assert "INSUFFICIENT" in captured.out


def test_cli_demo_opinion_non_factual_display(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify non-factual opinion is properly isolated and explained."""
    code = run_demo_case("opinion")
    assert code == 0
    captured = capsys.readouterr()
    assert "NON-FACTUAL CLAIMS" in captured.out
    assert "OPINION" in captured.out
    assert "Factual Verdict : NOT APPLICABLE" in captured.out


def test_cli_demo_prompt_injection_security_display(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify security isolation callout for prompt injection attempt."""
    code = run_demo_case("injection")
    assert code == 0
    captured = capsys.readouterr()
    assert "SECURITY TEST & PROMPT ISOLATION" in captured.out
    assert "Prompt Injection     : DETECTED / ISOLATED" in captured.out
    assert "Trusted Instructions : PROTECTED" in captured.out


def test_cli_demo_all_batch(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify batch execution of all demo cases producing PASS/FAIL table."""
    code = run_demo_all()
    assert code == 0
    captured = capsys.readouterr()
    assert "VERIFAI DEMO SUITE — AUTOMATED VALIDATION" in captured.out
    assert "TOTAL: 11/11 Passed" in captured.out
    assert "Backend Pipeline: PASS" in captured.out


def test_cli_main_entrypoint_no_args(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify running CLI with no arguments defaults to primary mixed demonstration."""
    with patch("sys.argv", ["verifai_cli.py"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Running primary demonstration ('mixed')" in captured.out
    assert "VERIFAI" in captured.out


def test_cli_unknown_case_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify error output on invalid demo case name."""
    code = run_demo_case("non_existent_case_name")
    assert code == 1
    captured = capsys.readouterr()
    assert "[ERROR] Unknown demo case" in captured.err


@pytest.mark.anyio
async def test_execute_verification_timing() -> None:
    """Verify execute_verification returns payload and positive elapsed time."""
    data, elapsed = await execute_verification("Water freezes at 0C.")
    assert "verification_id" in data
    assert elapsed > 0.0


# =========================================================================
# New Comprehensive Interactive Experience Tests
# =========================================================================


def test_terminal_styler_colors_enabled() -> None:
    """Verify TerminalStyler applies ANSI escape sequences when enabled."""
    styler = TerminalStyler(force_color=True)
    assert styler.enabled is True
    assert "\033[32m" in styler.green("hello")
    assert "\033[31m" in styler.red("alert")
    assert "\033[33m" in styler.yellow("warn")
    assert "\033[36m" in styler.cyan("header")
    assert "\033[35m" in styler.purple("sec")
    assert "[✓ SUPPORTED]" in styler.verdict_badge("SUPPORTED")
    assert "[✗ CONTRADICTED]" in styler.verdict_badge("CONTRADICTED")
    assert "[? UNKNOWN]" in styler.verdict_badge("UNKNOWN")


def test_terminal_styler_colors_disabled() -> None:
    """Verify TerminalStyler emits clean plain text when color is disabled."""
    styler = TerminalStyler(force_color=False)
    assert styler.enabled is False
    assert styler.green("hello") == "hello"
    assert styler.red("alert") == "alert"
    assert styler.yellow("warn") == "warn"
    assert styler.cyan("header") == "header"
    assert styler.verdict_badge("SUPPORTED") == "[✓ SUPPORTED]"
    assert styler.verdict_badge("CONTRADICTED") == "[✗ CONTRADICTED]"


def test_terminal_styler_no_color_env() -> None:
    """Verify NO_COLOR environment variable disables colors automatically."""
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        with patch("sys.stdout.isatty", return_value=True):
            styler = TerminalStyler()
            assert styler.enabled is False
            assert styler.green("text") == "text"


def test_terminal_styler_non_tty() -> None:
    """Verify non-TTY stdout disables colors automatically."""
    with patch.dict(os.environ, {"NO_COLOR": ""}, clear=True):
        with patch("sys.stdout.isatty", return_value=False):
            styler = TerminalStyler()
            assert styler.enabled is False


def test_trust_gauge_with_real_score() -> None:
    """Verify trust gauge renders correctly for a real calibrated score."""
    styler = TerminalStyler(force_color=False)
    gauge = styler.trust_gauge(92.0)
    assert "92.0%" in gauge
    assert "█" in gauge
    assert gauge == "[██████████████████░░] 92.0%"


def test_trust_gauge_with_none() -> None:
    """Verify trust gauge renders [N/A] when trust score is None without inventing values."""  # noqa: E501
    styler = TerminalStyler(force_color=False)
    gauge = styler.trust_gauge(None)
    assert gauge == "[N/A]"


def test_input_reader_multiline() -> None:
    """Verify multi-line input reader accumulates lines until sentinel."""
    mock_inputs = [
        "First line of AI response.",
        "Second line of AI response.",
        "END",
    ]
    with patch("builtins.input", side_effect=mock_inputs):
        text = InputReader.read_multiline(end_sentinel="END")
        assert "First line" in text
        assert "Second line" in text
        assert "END" not in text


def test_input_reader_file_validation(tmp_path: Path) -> None:
    """Verify file input validation against nonexistent, valid, and empty files."""
    content, err = InputReader.read_file("/non_existent_file_verifai.txt")
    assert content is None
    assert "not found" in str(err).lower()

    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("Valid text content for verification.", encoding="utf-8")
    content, err = InputReader.read_file(str(valid_file))
    assert content == "Valid text content for verification."
    assert err is None

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n  \t", encoding="utf-8")
    content, err = InputReader.read_file(str(empty_file))
    assert content is None
    assert "empty" in str(err).lower()


def test_menu_controller_exit(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify MenuController clean exit on option 0."""
    controller = MenuController()
    with patch("builtins.input", return_value="0"):
        code = controller.run_interactive_menu()
        assert code == 0
    captured = capsys.readouterr()
    assert "Exiting VerifAI Console" in captured.out


def test_menu_controller_invalid_choice(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify MenuController handles invalid input gracefully without crashing."""
    controller = MenuController()
    with patch("builtins.input", side_effect=["invalid_option_xyz", "0"]):
        code = controller.run_interactive_menu()
        assert code == 0
    captured = capsys.readouterr()
    assert "Invalid choice 'invalid_option_xyz'" in captured.out


def test_menu_controller_predefined_demos(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify predefined demo scenario menu lists all 11 cases."""
    controller = MenuController()
    with patch("builtins.input", return_value="0"):
        controller.run_predefined_demos_menu()
    captured = capsys.readouterr()
    assert "PREDEFINED DEMONSTRATION CASES" in captured.out
    assert "Clearly Supported Factual Assertion" in captured.out
    assert "Clearly Contradicted Factual Statement" in captured.out


def test_demo_runner_all_suite(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify DemoRunner.run_all_suite executes all 11 cases with PASS tags."""
    styler = TerminalStyler(force_color=False)
    code = DemoRunner.run_all_suite(styler=styler)
    assert code == 0
    captured = capsys.readouterr()
    assert "VERIFAI DEMO TEST SUITE" in captured.out
    assert "Passed: 11" in captured.out
    assert "Failed: 0" in captured.out


def test_result_renderer_unknown_rendering() -> None:
    """Verify ResultRenderer correctly displays UNKNOWN verdicts and missing trust score."""  # noqa: E501
    claims: list[dict[str, Any]] = [
        {
            "claim_index": 0,
            "claim_text": "A hypothetical chronon field permeates space.",
            "content_type": "FACTUAL",
            "verdict": "UNKNOWN",
            "is_verifiable": True,
            "unknown_reason": "INSUFFICIENT_EVIDENCE",
            "start_offset": 0,
            "end_offset": 46,
        }
    ]
    resp: dict[str, Any] = {
        "verification_id": "test-uuid-unknown",
        "status": "COMPLETED",
        "total_claims": 1,
        "supported_claims": 0,
        "contradicted_claims": 0,
        "unknown_claims": 1,
        "non_factual_claims": 0,
        "trust_score": None,
        "calibration_status": "NOT_CALIBRATED",
        "claims": claims,
    }
    scorecard = ResultRenderer.render_scorecard(
        resp, styler=TerminalStyler(force_color=False)
    )
    assert "UNKNOWN        : 1" in scorecard
    assert "Trust Score:" in scorecard
    assert "[N/A]" in scorecard

    claims_view = ResultRenderer.render_claims_summary(
        claims, styler=TerminalStyler(force_color=False)
    )
    assert "UNKNOWN Reason: INSUFFICIENT_EVIDENCE" in claims_view


def test_result_renderer_judge_disagreement() -> None:
    """Verify ResultRenderer detects and surfaces judge disagreement."""
    claims = [
        {
            "claim_index": 0,
            "claim_text": "Sample contested assertion.",
            "content_type": "FACTUAL",
            "judges": [
                {
                    "judge_name": "DeterministicRuleJudge",
                    "judgment": "SUPPORTED",
                    "rationale": "Evidence matches.",
                },
                {
                    "judge_name": "SecondarySemanticJudge",
                    "judgment": "CONTRADICTED",
                    "rationale": "Semantic conflict.",
                },
            ],
        }
    ]
    judges_view = ResultRenderer.render_judges_drilldown(
        claims, styler=TerminalStyler(force_color=False)
    )
    assert "DISAGREEMENT (Arbitrated by Decision Engine)" in judges_view


def test_post_verification_drilldown(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify post-verification drilldown options [V], [J], [A], [R] render properly."""  # noqa: E501
    controller = MenuController()
    controller.styler = TerminalStyler(force_color=False)
    data = {
        "verification_id": "test-drilldown-uuid",
        "status": "COMPLETED",
        "claims": [
            {
                "claim_index": 0,
                "claim_text": "Water freezes at 0C.",
                "content_type": "FACTUAL",
                "evidence": [
                    {
                        "source_title": "Physics Reference",
                        "source_url": "https://example.com/physics",
                        "snippet": "Water freezes at 0 degrees Celsius.",
                        "retriever_name": "Local Inverted Index",
                        "relevance_score": 0.98,
                    }
                ],
                "judges": [
                    {
                        "judge_name": "DeterministicRuleJudge",
                        "judgment": "SUPPORTED",
                        "rationale": "Direct factual confirmation.",
                    }
                ],
            }
        ],
        "audit_trail": [
            {
                "stage": "EXTRACTION",
                "event_type": "STAGE_COMPLETED",
                "message": "Extracted 1 claim.",
            }
        ],
    }
    # Simulate user pressing V, J, A, R, then empty string (Enter) to return
    with patch("builtins.input", side_effect=["v", "j", "a", "r", ""]):
        controller.post_verification_drilldown(data, elapsed=0.12)

    captured = capsys.readouterr()
    assert "EVIDENCE DRILL-DOWN" in captured.out
    assert "Physics Reference" in captured.out
    assert "JUDGE DRILL-DOWN & CONSENSUS" in captured.out
    assert "DeterministicRuleJudge" in captured.out
    assert "AUDIT & TRACEABILITY" in captured.out
    assert "RAW VERIFICATION JSON" in captured.out


def test_progress_renderer_stages() -> None:
    """Verify ProgressRenderer generates all 5 stage indicators."""
    styler = TerminalStyler(force_color=False)
    rendered = ProgressRenderer.render_progress_summary(
        [], total_elapsed=0.25, styler=styler
    )  # noqa: E501
    assert "[1/5] Claims extracted" in rendered
    assert "[2/5] Claims classified" in rendered
    assert "[3/5] Evidence retrieved" in rendered
    assert "[4/5] Judges evaluated" in rendered
    assert "[5/5] Decision completed" in rendered


def test_architecture_guide_display(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify architecture guide explains 5-stage pipeline and UNKNOWN principle."""
    controller = MenuController()
    with patch("builtins.input", return_value=""):
        controller.show_architecture_guide()
    captured = capsys.readouterr()
    assert "VERIFAI ARCHITECTURE & METHODOLOGY" in captured.out
    assert "How VerifAI Works" in captured.out
    assert (
        "UNKNOWN means VerifAI did NOT have sufficient empirical evidence"
        in captured.out
    )  # noqa: E501
