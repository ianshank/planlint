"""Projections of a findings envelope: report.py and the `report` verb (CP-GA).

Unit tests cover the pure module (AC-GA-3..7). End-to-end tests cover the CLI
verb (AC-GA-1, AC-GA-2, AC-GA-18) and the committed action fixtures (AC-GA-16).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from openspec_graph import report
from openspec_graph.cli import FINDINGS_ENVELOPE_KEYS_MESSAGE
from openspec_graph.rule_types import FINDINGS_SCHEMA_VERSION
from tests.support import run_cli, write_spec

FX = Path(__file__).resolve().parent / "fixtures"
ACTION_FX = FX / "action"
FINDING_BEARING = "# Nothing normative here\n\nProse only.\n"

_OUTPUT_KEYS = {
    "status",
    "errors",
    "warnings",
    "findings",
    "blocking",
    "specs-checked",
    "rules-triggered",
    "version",
}


def _envelope(
    *,
    blocking: int = 0,
    specs_checked: int = 1,
    findings: list[dict[str, object]] | None = None,
    tool_version: str = "0.2.0",
    schema_version: int = FINDINGS_SCHEMA_VERSION,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "tool_version": tool_version,
        "target": "repo",
        "specs_checked": specs_checked,
        "findings": findings if findings is not None else [],
        "blocking": blocking,
    }


def _finding(
    *,
    rule: str = "G001",
    severity: str = "ERROR",
    message: str = "broke",
    path: str | None = "openspec/changes/c1/specs/cap/spec.md",
    line: int = 0,
) -> dict[str, object]:
    return {
        "rule": rule,
        "severity": severity,
        "message": message,
        "path": path,
        "line": line,
        "subject": "",
    }


def _copy_machinery(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "Makefile").write_text((FX / "Makefile").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "pyproject.toml").write_text(
        (FX / "pyproject.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )


def _empty_tree(root: Path) -> Path:
    _copy_machinery(root)
    (root / "openspec" / "changes").mkdir(parents=True)
    return root


def _clean_tree(root: Path) -> Path:
    _copy_machinery(root)
    write_spec(root, "c1", "cap", (FX / "good_harness.md").read_text(encoding="utf-8"))
    return root


def _failing_tree(root: Path) -> Path:
    _copy_machinery(root)
    write_spec(root, "ga-fail-one", "cap", FINDING_BEARING)
    write_spec(root, "ga-fail-two", "cap", FINDING_BEARING)
    return root


# --- Pure module -----------------------------------------------------------


def test_status_of_the_four_envelope_statuses() -> None:
    """R-GA-5: fail / indeterminate / pass from the envelope; error is action-only."""
    assert report.status_of(_envelope(blocking=2, specs_checked=3, findings=[_finding()])) == "fail"
    assert report.status_of(_envelope(blocking=0, specs_checked=0)) == "indeterminate"
    assert report.status_of(_envelope(blocking=0, specs_checked=4)) == "pass"
    assert "error" not in {
        report.status_of(_envelope(blocking=1, specs_checked=0, findings=[_finding()])),
        report.status_of(_envelope(blocking=0, specs_checked=0)),
        report.status_of(_envelope(blocking=0, specs_checked=1)),
    }


def test_zero_spec_envelope_from_real_validate_is_indeterminate(tmp_path: Path) -> None:
    """AC-GA-4: a real empty-tree envelope is never pass."""
    repo = _empty_tree(tmp_path)
    result = run_cli(repo, "validate", "--format", "json")
    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["specs_checked"] == 0
    assert envelope["blocking"] == 0
    assert report.status_of(envelope) == "indeterminate"
    assert report.to_outputs(envelope)["status"] == "indeterminate"


def test_github_outputs_key_set_and_derived_counts() -> None:
    """AC-GA-3: derived counts, sorted rules, no embedded newline."""
    envelope = _envelope(
        blocking=2,
        specs_checked=2,
        findings=[
            _finding(rule="G003", severity="ERROR", message="a"),
            _finding(rule="G001", severity="WARN", message="b"),
            _finding(rule="G003", severity="ERROR", message="c"),
        ],
        tool_version="0.2.0",
    )
    outputs = report.to_outputs(envelope)
    assert set(outputs) == _OUTPUT_KEYS
    assert list(outputs) == list(report.OUTPUT_KEYS)
    assert outputs["status"] == "fail"
    assert outputs["errors"] == "2"
    assert outputs["warnings"] == "1"
    assert outputs["findings"] == "3"
    assert outputs["blocking"] == "2"
    assert outputs["specs-checked"] == "2"
    assert outputs["rules-triggered"] == "G001,G003"
    assert outputs["version"] == "0.2.0"
    assert all("\n" not in value and "\r" not in value for value in outputs.values())

    clean = report.to_outputs(_envelope(blocking=0, specs_checked=1))
    assert clean["status"] == "pass"
    assert clean["findings"] == "0"
    assert clean["rules-triggered"] == ""


def test_annotation_escaping_and_location_rules() -> None:
    """AC-GA-5: severity map, file=/line=/title=, workflow-command escaping."""
    message = "pct=% cr=\r nl=\n colon=: comma=,"
    envelope = _envelope(
        blocking=1,
        findings=[
            _finding(rule="G001", severity="ERROR", message=message, path="a:b,c.md", line=4),
            _finding(rule="G002", severity="WARN", message="w", path="b.md", line=0),
            _finding(rule="G003", severity="INFO", message="i", path=None, line=7),
        ],
    )
    lines = report.to_annotations(envelope)
    assert lines[0].startswith("::error ")
    assert "file=a%3Ab%2Cc.md" in lines[0]
    assert "line=4" in lines[0]
    assert "title=G001" in lines[0]
    assert "pct=%25" in lines[0]
    assert "cr=%0D" in lines[0]
    assert "nl=%0A" in lines[0]
    data = lines[0].split("::", 2)[-1]
    assert "colon=:" in data
    assert "comma=," in data
    assert lines[1].startswith("::warning ")
    assert "file=b.md" in lines[1]
    assert "line=" not in lines[1]
    assert lines[2].startswith("::notice ")
    assert "file=" not in lines[2]
    assert "line=7" in lines[2]


def test_annotation_cap_emits_trailing_notice() -> None:
    """AC-GA-6: exactly the cap of finding commands plus one notice; none below."""
    over = _envelope(
        blocking=1,
        findings=[_finding(rule=f"G{i:03d}", message=f"m{i}") for i in range(report.ANNOTATION_LIMIT + 3)],
    )
    lines = report.to_annotations(over)
    finding_cmds = [line for line in lines if not line.startswith("::notice::")]
    notices = [line for line in lines if line.startswith("::notice::")]
    assert len(finding_cmds) == report.ANNOTATION_LIMIT
    assert len(notices) == 1
    assert "3 findings withheld" in notices[0]
    assert "evidence artifact" in notices[0]

    under = _envelope(
        blocking=1,
        findings=[_finding(rule=f"G{i:03d}") for i in range(report.ANNOTATION_LIMIT)],
    )
    under_lines = report.to_annotations(under)
    assert len(under_lines) == report.ANNOTATION_LIMIT
    assert not any(line.startswith("::notice::") for line in under_lines)


def test_step_summary_is_deterministic_and_capped() -> None:
    """AC-GA-7 / AC-GA-17: pure function, names status and counts, same cap."""
    envelope = _envelope(
        blocking=1,
        specs_checked=2,
        findings=[
            _finding(rule="G001", message="has | pipe and\nnewline"),
            *[_finding(rule=f"G{i:03d}") for i in range(2, report.ANNOTATION_LIMIT + 4)],
        ],
    )
    first = report.to_step_summary(envelope)
    second = report.to_step_summary(envelope)
    assert first == second
    assert first.endswith("\n")
    assert "`fail`" in first
    assert "errors:" in first
    assert "\\|" in first
    assert "\nnewline" not in first.split("| Message |", 1)[1].split("\n|")[1]
    assert "3 findings withheld" in first
    assert first.count("| G") == report.ANNOTATION_LIMIT


# --- CLI verb ----------------------------------------------------------------


def test_report_sarif_is_byte_identical_to_validate_sarif(tmp_path: Path) -> None:
    """AC-GA-1: non-empty results first, then a clean tree."""
    failing = _failing_tree(tmp_path / "failing")
    clean = _clean_tree(tmp_path / "clean")

    fail_json = run_cli(failing, "validate", "--format", "json")
    fail_sarif = run_cli(failing, "validate", "--format", "sarif")
    assert fail_json.returncode == 1
    assert fail_sarif.returncode == 1
    envelope_path = tmp_path / "failing.json"
    envelope_path.write_text(fail_json.stdout, encoding="utf-8")
    reported = run_cli(failing, "report", "--findings", str(envelope_path), "--format", "sarif")
    assert reported.returncode == 0, reported.stderr
    assert json.loads(fail_sarif.stdout)["runs"][0]["results"], "vacuous equality guard"
    assert reported.stdout == fail_sarif.stdout

    clean_json = run_cli(clean, "validate", "--format", "json")
    clean_sarif = run_cli(clean, "validate", "--format", "sarif")
    assert clean_json.returncode == 0
    clean_path = tmp_path / "clean.json"
    clean_path.write_text(clean_json.stdout, encoding="utf-8")
    clean_reported = run_cli(clean, "report", "--findings", str(clean_path), "--format", "sarif")
    assert clean_reported.returncode == 0, clean_reported.stderr
    assert clean_reported.stdout == clean_sarif.stdout


def test_report_exit_two_inputs_and_never_exit_one(tmp_path: Path) -> None:
    """AC-GA-2: missing, non-JSON, array, foreign schema, dialect card; never exit 1."""
    missing = tmp_path / "absent.json"
    not_json = tmp_path / "nope.txt"
    not_json.write_text("not json", encoding="utf-8")
    array_path = tmp_path / "array.json"
    array_path.write_text("[]", encoding="utf-8")
    foreign = tmp_path / "foreign.json"
    foreign.write_text(
        json.dumps(_envelope(schema_version=FINDINGS_SCHEMA_VERSION + 1)),
        encoding="utf-8",
    )
    card = tmp_path / "card.json"
    card.write_text(
        json.dumps({"schema_version": FINDINGS_SCHEMA_VERSION, "dialect": "harness"}),
        encoding="utf-8",
    )

    cases = [missing, not_json, array_path, foreign, card]
    for path in cases:
        result = run_cli(tmp_path, "report", "--findings", str(path), "--format", "github-outputs")
        assert result.returncode == 2, (path, result.stderr)
        assert result.stdout == ""
        assert result.stderr.strip().count("\n") == 0
        assert result.stderr.strip()

    assert FINDINGS_ENVELOPE_KEYS_MESSAGE.split("{")[0] in run_cli(
        tmp_path, "report", "--findings", str(card), "--format", "github-outputs"
    ).stderr


def test_report_warns_on_tool_version_mismatch_without_changing_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-GA-18: stderr warning; stdout identical when only the running build differs."""
    from openspec_graph.cli import main

    repo = _clean_tree(tmp_path / "repo")
    produced = run_cli(repo, "validate", "--format", "json")
    assert produced.returncode == 0
    path = tmp_path / "findings.json"
    path.write_text(produced.stdout, encoding="utf-8")
    argv = ["report", "--findings", str(path), "--format", "sarif"]

    try:
        assert main(argv) == 0
        matching = capsys.readouterr()

        monkeypatch.setattr("openspec_graph.cli._package_version", lambda: "9.9.9-not-this-build")
        assert main(argv) == 0
        mismatched = capsys.readouterr()
    finally:
        pkg = logging.getLogger("planlint")
        for handler in list(pkg.handlers):
            pkg.removeHandler(handler)
        pkg.propagate = True
        pkg.setLevel(logging.NOTSET)
    assert mismatched.out == matching.out
    assert "WARNING" in mismatched.err
    assert "9.9.9-not-this-build" in mismatched.err


def test_report_projections_are_deterministic(tmp_path: Path) -> None:
    """AC-GA-17 report half: two CLI calls over one envelope are byte-identical."""
    repo = _failing_tree(tmp_path / "failing")
    produced = run_cli(repo, "validate", "--format", "json")
    path = tmp_path / "findings.json"
    path.write_text(produced.stdout, encoding="utf-8")
    for fmt in ("sarif", "github-annotations", "github-summary", "github-outputs"):
        first = run_cli(repo, "report", "--findings", str(path), "--format", fmt)
        second = run_cli(repo, "report", "--findings", str(path), "--format", fmt)
        assert first.returncode == 0, first.stderr
        assert first.stdout == second.stdout


# --- Committed fixtures (AC-GA-16) -------------------------------------------


def test_action_fixtures_match_their_labels() -> None:
    """AC-GA-16: each committed fixture produces the result its name promises."""
    passing = ACTION_FX / "passing"
    failing = ACTION_FX / "failing"
    empty = ACTION_FX / "empty-tree"
    none = ACTION_FX / "no-tree"
    nested = ACTION_FX / "nested"
    nested_target = nested / "target"

    passed = run_cli(passing, "validate", "--format", "json")
    assert passed.returncode == 0, passed.stderr
    assert json.loads(passed.stdout)["specs_checked"] >= 1

    failed = run_cli(failing, "validate", "--format", "json")
    assert failed.returncode == 1, failed.stderr
    payload = json.loads(failed.stdout)
    assert payload["blocking"] > 0
    paths = {finding["path"] for finding in payload["findings"]}
    assert len(paths) >= 2

    vacant = run_cli(empty, "validate", "--format", "json")
    assert vacant.returncode == 0, vacant.stderr
    assert json.loads(vacant.stdout)["specs_checked"] == 0

    missing = run_cli(none, "validate", "--format", "json")
    assert missing.returncode == 2
    assert "no openspec/ directory" in missing.stderr

    nested_root = run_cli(nested, "validate", "--format", "json")
    nested_ok = run_cli(nested_target, "validate", "--format", "json")
    assert nested_root.returncode != 0
    assert nested_ok.returncode == 0, nested_ok.stderr
    assert json.loads(nested_ok.stdout)["specs_checked"] >= 1
