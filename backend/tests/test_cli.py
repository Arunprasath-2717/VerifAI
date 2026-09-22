import json
from unittest.mock import patch

import pytest
from scripts.verifai_cli import (
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


def test_cli_verify_file(
    tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify text loaded from a file."""
    test_file = tmp_path / "sample.txt"  # type: ignore[operator]
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
