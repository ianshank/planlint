"""The `report` verb and its pure projection module (change: add-github-action-contract).

Three layers, in the order they fail:

1. **The envelope gate.** Every malformed payload must become one exit-2
   diagnostic, never a traceback. That matters more than it looks: exit 1 means
   "findings were reported" everywhere else in this CLI, so a renderer that
   crashed on a truncated artifact would report a spec failure that did not
   happen.
2. **The projections.** Pure functions over a parsed envelope -- escaping,
   caps, ordering, determinism -- tested against constructed inputs so a
   criterion cannot pass on an empty set.
3. **The verb, end to end.** The byte-identity between `report --format sarif`
   and `validate --format sarif` is asserted through two real subprocess runs,
   because that identity is what makes "one validate run, every other surface a
   projection of it" a fact rather than an intention.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from openspec_graph import report
from openspec_graph.dialect_card import SCHEMA_VERSION as CARD_SCHEMA
from openspec_graph.rule_types import FINDINGS_SCHEMA_VERSION as ENVELOPE_SCHEMA
from tests.support import run_cli

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "openspec_graph"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "action"

# Each fixture's label, mirroring tests/fixtures/action/README.md's table. The
# duplication is deliberate and one-directional: the README is what a reader
# consults, this is what fails when the behaviour drifts from it.
FIXTURE_CONTRACT = (
    # (directory, validate exit code, status, at least one finding)
    ("passing", 0, report.STATUS_PASS, False),
    ("failing", 1, report.STATUS_FAIL, True),
    ("empty-tree", 0, report.STATUS_INDETERMINATE, False),
    ("nested/sub", 0, report.STATUS_PASS, False),
)


def _envelope(**overrides: object) -> dict[str, object]:
    """A minimal well-formed envelope, before any deliberate corruption."""
    payload: dict[str, object] = {
        "schema_version": ENVELOPE_SCHEMA,
        "tool_version": "0.0.0",
        "target": "/somewhere",
        "specs_checked": 1,
        "findings": [],
        "blocking": 0,
    }
    payload.update(overrides)
    return payload


def _finding(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "rule": "G004",
        "severity": "ERROR",
        "message": "cites `make nope` which is not a target",
        "path": "openspec/changes/c1/specs/cap/spec.md",
        "line": 0,
        "subject": "",
    }
    payload.update(overrides)
    return payload


def _parse(**overrides: object) -> report.Envelope:
    return report.parse_envelope(_envelope(**overrides), schema_version=ENVELOPE_SCHEMA)


# --- 1. the envelope gate ----------------------------------------------------


MALFORMED = {
    "not an object": [1, 2, 3],
    "a bare string": "findings",
    "null": None,
    "missing findings": {k: v for k, v in _envelope().items() if k != "findings"},
    "missing blocking": {k: v for k, v in _envelope().items() if k != "blocking"},
    "missing tool_version": {k: v for k, v in _envelope().items() if k != "tool_version"},
    "missing specs_checked": {k: v for k, v in _envelope().items() if k != "specs_checked"},
    "findings is null": _envelope(findings=None),
    "findings is an object": _envelope(findings={"rule": "G001"}),
    "findings is a string": _envelope(findings="G001"),
    "blocking is a string": _envelope(blocking="0"),
    "blocking is negative": _envelope(blocking=-1),
    "blocking is a bool": _envelope(blocking=True),
    "specs_checked is a float": _envelope(specs_checked=1.5),
    "schema_version is a string": _envelope(schema_version=str(ENVELOPE_SCHEMA)),
    "a future schema": _envelope(schema_version=ENVELOPE_SCHEMA + 1),
    "a finding is not an object": _envelope(findings=["G001"]),
    "a finding lacks severity": _envelope(
        findings=[{k: v for k, v in _finding().items() if k != "severity"}]
    ),
    "a finding lacks rule": _envelope(findings=[{k: v for k, v in _finding().items() if k != "rule"}]),
    "a finding line is a string": _envelope(findings=[_finding(line="7")]),
    "a finding path is a number": _envelope(findings=[_finding(path=7)]),
    "a finding message is null": _envelope(findings=[_finding(message=None)]),
}


@pytest.mark.parametrize("label", sorted(MALFORMED), ids=lambda k: k.replace(" ", "-"))
def test_a_malformed_envelope_raises_rather_than_crashing_a_renderer(label: str) -> None:
    """Every way an envelope can be wrong becomes one typed error.

    The list is long on purpose. Each entry was a real traceback before the
    validator existed: `findings` absent raised `KeyError` inside the SARIF
    projection, `blocking` as a string raised `TypeError` in the status
    comparison, and both surface as exit 1 -- which in this tool means the
    specs failed.
    """
    with pytest.raises(report.EnvelopeError) as caught:
        report.parse_envelope(MALFORMED[label], schema_version=ENVELOPE_SCHEMA)
    assert str(caught.value), "the error must carry a message an operator can act on"


def test_a_well_formed_envelope_parses() -> None:
    """Guard the guard: a validator that rejected everything would make every
    rejection test above pass while the verb worked for nobody."""
    envelope = _parse(findings=[_finding()], blocking=1)
    assert len(envelope.findings) == 1
    assert envelope.findings[0].rule == "G004"


def test_an_unknown_finding_key_is_tolerated() -> None:
    """Additive keys do not bump the schema version, so a newer producer's
    envelope must still project rather than being refused for being richer."""
    envelope = _parse(findings=[_finding(confidence="high")])
    assert len(envelope.findings) == 1


# --- 2. the projections ------------------------------------------------------


def test_blocking_findings_are_a_fail() -> None:
    assert report.status_of(_parse(blocking=2, findings=[_finding()])) == report.STATUS_FAIL


def test_a_checked_clean_tree_is_a_pass() -> None:
    assert report.status_of(_parse(specs_checked=3)) == report.STATUS_PASS


def test_a_tree_with_nothing_to_check_is_indeterminate_not_pass() -> None:
    """The defect this whole change exists to close, at the unit level.

    Zero blocking findings and zero specs checked is not a clean repository --
    it is a repository the gate never measured. Calling it `pass` hands back a
    green check for gating nothing.
    """
    assert report.status_of(_parse(specs_checked=0)) == report.STATUS_INDETERMINATE


def test_an_empty_spec_tree_really_produces_that_envelope() -> None:
    """AC: the indeterminate case is reachable through the real CLI, not only
    through a constructed dict. Without this the unit test above could be
    describing a state `validate` never emits."""
    result = run_cli(FIXTURES / "empty-tree", "validate", "--format", "json")
    assert result.returncode == 0, result.stderr
    envelope = report.parse_envelope(json.loads(result.stdout), schema_version=ENVELOPE_SCHEMA)
    assert envelope.specs_checked == 0
    assert report.status_of(envelope) == report.STATUS_INDETERMINATE


def test_annotation_escaping_covers_every_documented_character() -> None:
    """Message data escapes %, CR and LF; property values escape those plus
    `:` and `,`. Getting this wrong truncates an annotation at the first colon,
    which is the failure mode that makes shell-and-jq implementations of this
    projection quietly lossy."""
    envelope = _parse(
        findings=[_finding(message="100% done: a, b\r\nnext", path="dir:with,commas/f.md")],
        blocking=1,
    )
    line = report.to_annotations(envelope)[0]

    assert "file=dir%3Awith%2Ccommas/f.md" in line
    assert line.endswith("::100%25 done: a, b%0D%0Anext")
    # A colon or comma in the *message* is data, not a delimiter, and must
    # survive unescaped -- over-escaping is as wrong as under-escaping.
    assert ": a, b" in line


def test_a_line_of_zero_emits_no_line_property() -> None:
    """A finding with no locus (line 0) omits the workflow-command line=
    property rather than clamping to 1, which would annotate the first line
    of a real file. Migrated rules fill the field when they hold one."""
    line = report.to_annotations(_parse(findings=[_finding(line=0)], blocking=1))[0]
    assert "line=" not in line


def test_a_real_line_emits_a_line_property() -> None:
    line = report.to_annotations(_parse(findings=[_finding(line=42)], blocking=1))[0]
    assert "line=42" in line


def test_a_pathless_finding_is_annotated_without_a_file() -> None:
    """Non-success: a finding with no path is still emitted. Dropping it to
    satisfy a surface would lose a real result."""
    lines = report.to_annotations(_parse(findings=[_finding(path=None)], blocking=1))
    assert len(lines) == 1
    assert "file=" not in lines[0]
    assert "title=G004" in lines[0]


def test_an_unknown_severity_maps_up_to_error() -> None:
    """Fail upward, never to `notice`: a severity this module has not been
    taught about is a bug, and the safe failure is the loud one."""
    line = report.to_annotations(_parse(findings=[_finding(severity="CRITICAL")], blocking=1))[0]
    assert line.startswith("::error ")


def test_the_annotation_cap_is_per_severity_so_an_error_is_never_starved() -> None:
    """Non-success, and the reason the cap is per severity rather than shared.

    Envelope order is (path, rule), not severity. With one shared budget, a
    tree whose first findings by path are warnings withholds the error that
    actually failed the gate -- a red X with no annotation explaining it.
    """
    limit = report.ANNOTATION_LIMIT_PER_SEVERITY
    findings = [
        _finding(rule="H003", severity="WARN", message=f"warn {i}", path=f"a/{i:03d}.md")
        for i in range(limit * 3)
    ]
    findings.append(_finding(rule="G001", severity="ERROR", message="the real one", path="z.md"))
    lines = report.to_annotations(_parse(findings=findings, blocking=1))

    errors = [line for line in lines if line.startswith("::error ")]
    assert len(errors) == 1, "the sole ERROR must survive a flood of warnings"
    assert "the real one" in errors[0]
    assert sum(1 for line in lines if line.startswith("::warning ")) == limit


def test_a_capped_run_says_how_many_findings_were_withheld() -> None:
    limit = report.ANNOTATION_LIMIT_PER_SEVERITY
    findings = [_finding(message=f"e {i}", path=f"a/{i:03d}.md") for i in range(limit + 3)]
    lines = report.to_annotations(_parse(findings=findings, blocking=1))
    notices = [line for line in lines if line.startswith("::notice ")]
    assert len(notices) == 1
    assert "3 further finding(s)" in notices[0]


def test_an_uncapped_run_emits_no_withheld_notice() -> None:
    """The other half of the boundary: a run under the cap must not claim
    anything was withheld."""
    lines = report.to_annotations(_parse(findings=[_finding()], blocking=1))
    assert not [line for line in lines if line.startswith("::notice ")]


def test_path_prefix_relocates_annotation_paths() -> None:
    """A subdirectory target's finding paths are relative to that target, while
    GitHub resolves `file=` against the repository root."""
    envelope = _parse(findings=[_finding(path="openspec/changes/c1/specs/cap/spec.md")], blocking=1)
    line = report.to_annotations(envelope, path_prefix="services/api")[0]
    assert "file=services/api/openspec/changes/c1/specs/cap/spec.md" in line


def test_outputs_are_single_line_key_value_pairs() -> None:
    """`$GITHUB_OUTPUT` is line-oriented: a newline inside a value ends it
    early and the remainder is read as another key."""
    outputs = report.to_outputs(_parse(findings=[_finding(), _finding(rule="G001")], blocking=2))
    assert outputs["status"] == report.STATUS_FAIL
    assert outputs["errors"] == "2"
    assert outputs["blocking"] == "2"
    assert outputs["findings"] == "2"
    for key, value in outputs.items():
        assert "\n" not in value and "\r" not in value, key
        assert "=" not in key, key


def test_rules_triggered_is_sorted_and_deduplicated() -> None:
    envelope = _parse(
        findings=[_finding(rule="H001"), _finding(rule="G004"), _finding(rule="H001")],
        blocking=3,
    )
    assert report.to_outputs(envelope)["rules-triggered"] == "G004,H001"


def test_counts_cover_every_severity_even_at_zero() -> None:
    """A consumer must never have to tell "no errors" from "the key is
    missing"."""
    counts = report.counts_by_severity(_parse())
    assert set(report.SEVERITIES) <= set(counts)
    assert all(value == 0 for value in counts.values())


def test_step_summary_is_deterministic() -> None:
    envelope = _parse(findings=[_finding()], blocking=1)
    assert report.to_step_summary(envelope) == report.to_step_summary(envelope)


def test_step_summary_escapes_table_breaking_characters() -> None:
    """A `|` in a message would otherwise split the row into extra cells and
    silently shift every column after it."""
    envelope = _parse(findings=[_finding(message="a | b\nc")], blocking=1)
    row = next(
        line for line in report.to_step_summary(envelope).splitlines()
        if line.startswith("| G004 ")
    )
    assert "\\|" in row, row
    delimiters = row.count("|") - row.count("\\|")
    assert delimiters == 5, f"expected four cells between five delimiters, got: {row}"


def test_the_step_summary_table_is_capped_like_the_annotations() -> None:
    """The table would otherwise scroll a job summary past the point of use,
    and a truncated one that did not say so would read as the whole run."""
    limit = report.ANNOTATION_LIMIT_PER_SEVERITY
    findings = [_finding(message=f"e {i}", path=f"a/{i:03d}.md") for i in range(limit + 2)]
    summary = report.to_step_summary(_parse(findings=findings, blocking=limit + 2))

    rows = [line for line in summary.splitlines() if line.startswith("| G004 ")]
    assert len(rows) == limit
    assert "2 further finding(s) not listed" in summary


def test_step_summary_names_the_indeterminate_case() -> None:
    """A reader who sees a red X on an empty tree needs to know why."""
    summary = report.to_step_summary(_parse(specs_checked=0))
    assert report.STATUS_INDETERMINATE in summary
    assert "No spec was checked" in summary


# --- the discovery card ------------------------------------------------------


def _card(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": CARD_SCHEMA,
        "dialect": "harness",
        "make_targets": ["test", "ci"],
        "threshold": {"locator": "pyproject.toml:[tool.coverage.report].fail_under", "value": 90},
    }
    payload.update(overrides)
    return payload


def test_a_target_with_machinery_produces_no_discovery_warning() -> None:
    """The notes must stay quiet on an ordinary repository, or they are noise
    every adopter learns to skip."""
    card = report.parse_card(_card(), schema_version=CARD_SCHEMA)
    assert report.discovery_notes(card) == []


def test_a_target_with_no_make_targets_is_flagged() -> None:
    """The cited-stage rule returns early when the target has no Makefile, so a
    green run over such a repository proves less than it looks like it proves.
    The rule is right to stay silent; the wrapper is wrong to."""
    card = report.parse_card(_card(make_targets=[]), schema_version=CARD_SCHEMA)
    notes = report.discovery_notes(card)
    assert len(notes) == 1
    assert "G004" in notes[0]


def test_a_target_with_no_coverage_floor_is_flagged() -> None:
    card = report.parse_card(_card(threshold=None), schema_version=CARD_SCHEMA)
    notes = report.discovery_notes(card)
    assert len(notes) == 1
    assert "G003" in notes[0]


def test_discovery_warnings_reach_the_annotations_and_the_summary() -> None:
    card = report.parse_card(_card(make_targets=[], threshold=None), schema_version=CARD_SCHEMA)
    envelope = _parse(specs_checked=1)
    warnings = [
        line for line in report.to_annotations(envelope, card=card)
        if line.startswith("::warning ")
    ]
    assert len(warnings) == 2
    assert "[!WARNING]" in report.to_step_summary(envelope, card=card)


def test_discovery_outputs_are_omitted_without_a_card() -> None:
    """Absent is not zero: a consumer must be able to tell "not measured" from
    "measured as none"."""
    bare = report.to_outputs(_parse())
    assert "make-targets" not in bare and "dialect" not in bare

    card = report.parse_card(_card(make_targets=[]), schema_version=CARD_SCHEMA)
    with_card = report.to_outputs(_parse(), card=card)
    assert with_card["make-targets"] == "0"
    assert with_card["dialect"] == "harness"
    assert with_card["discovery-warnings"] == "1"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param([1], id="not-an-object"),
        pytest.param({k: v for k, v in _card().items() if k != "dialect"}, id="missing-dialect"),
        pytest.param({k: v for k, v in _card().items() if k != "threshold"}, id="missing-threshold"),
        pytest.param(_card(schema_version=CARD_SCHEMA + 1), id="future-schema"),
        pytest.param(_card(make_targets="test"), id="make-targets-is-a-string"),
        pytest.param(_card(threshold=90), id="threshold-is-a-number"),
    ],
)
def test_a_malformed_card_is_refused(payload: object) -> None:
    """Strict, like `delta --baseline`: degrading silently would report "no
    machinery detected" for a repository that has plenty, which inverts the
    warning the card exists to raise."""
    with pytest.raises(report.EnvelopeError):
        report.parse_card(payload, schema_version=CARD_SCHEMA)


# --- module purity -----------------------------------------------------------


def test_report_has_no_intra_package_imports() -> None:
    """The zero-intra-package-import posture, checked rather than asserted.

    `test_new_modules_stdlib_only` deliberately drops relative imports when it
    resolves module roots, so it cannot see `from .rules import ...` -- several
    modules on its list have intra-package imports and pass it. This module's
    claim is stronger and needs its own check: it is handed plain data and the
    schema versions it validates against, so it can never depend on evaluation
    order.
    """
    tree = ast.parse((PKG / "report.py").read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                offenders.append(f"relative import of {node.module or '.'}")
            elif node.module and node.module.split(".")[0] == PKG.name:
                offenders.append(f"absolute import of {node.module}")
        elif isinstance(node, ast.Import):
            offenders += [
                f"import of {alias.name}" for alias in node.names
                if alias.name.split(".")[0] == PKG.name
            ]
    assert not offenders, f"openspec_graph/report.py imports its own package: {offenders}"


def test_the_annotation_cap_is_a_named_constant() -> None:
    """A bare number in the action YAML would be exactly the hard-coded
    threshold this project fails other repositories for."""
    assert isinstance(report.ANNOTATION_LIMIT_PER_SEVERITY, int)
    assert report.ANNOTATION_LIMIT_PER_SEVERITY > 0


# --- 3. the verb, end to end -------------------------------------------------


def _written(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_report_sarif_is_byte_identical_to_validate_sarif(tmp_path: Path) -> None:
    """The identity that makes one `validate` run enough for every surface.

    Asserted on a fixture with real findings, and the non-emptiness is checked
    first: two empty SARIF logs are also byte-identical, and that would prove
    nothing.
    """
    target = FIXTURES / "failing"
    envelope = run_cli(target, "validate", "--format", "json")
    direct = run_cli(target, "validate", "--format", "sarif")
    assert envelope.returncode == 1 and direct.returncode == 1

    payload = json.loads(envelope.stdout)
    assert len(payload["findings"]) >= 2, "fixture must produce findings in more than one file"

    saved = _written(tmp_path, "findings.json", envelope.stdout)
    projected = run_cli(target, "report", "--findings", str(saved), "--format", "sarif")
    assert projected.returncode == 0, projected.stderr
    assert projected.stdout == direct.stdout


def test_report_sarif_matches_on_a_clean_tree_too(tmp_path: Path) -> None:
    """The empty case still has to agree -- the driver's rule table is emitted
    whether or not anything fired."""
    target = FIXTURES / "passing"
    envelope = run_cli(target, "validate", "--format", "json")
    direct = run_cli(target, "validate", "--format", "sarif")
    saved = _written(tmp_path, "findings.json", envelope.stdout)
    projected = run_cli(target, "report", "--findings", str(saved), "--format", "sarif")
    assert projected.stdout == direct.stdout


@pytest.mark.parametrize(
    "fixture,exit_code,status,has_findings",
    FIXTURE_CONTRACT,
    ids=[row[0].replace("/", "-") for row in FIXTURE_CONTRACT],
)
def test_each_fixture_produces_the_status_its_label_promises(
    tmp_path: Path, fixture: str, exit_code: int, status: str, has_findings: bool
) -> None:
    """The contract job asserts these same rows against the action's outputs.
    Here they are pinned against the CLI, so a drift is caught locally rather
    than on a runner."""
    target = FIXTURES / fixture
    envelope = run_cli(target, "validate", "--format", "json")
    assert envelope.returncode == exit_code, envelope.stderr

    saved = _written(tmp_path, "findings.json", envelope.stdout)
    outputs = run_cli(target, "report", "--findings", str(saved), "--format", "github-outputs")
    assert outputs.returncode == 0, outputs.stderr
    rendered = dict(line.split("=", 1) for line in outputs.stdout.splitlines())
    assert rendered["status"] == status
    assert (int(rendered["findings"]) > 0) is has_findings


def test_the_no_tree_fixture_writes_no_envelope() -> None:
    """The `error` status has no envelope behind it by construction: exit 2
    prints a diagnostic on stderr and nothing on stdout, so the action's own
    absent-envelope branch is the only thing that can classify it."""
    result = run_cli(FIXTURES / "no-tree", "validate", "--format", "json")
    assert result.returncode == 2
    assert result.stdout.strip() == ""
    assert "no openspec/ directory" in result.stderr


@pytest.mark.parametrize(
    "payload",
    ["not json at all", "[1, 2, 3]", '{"schema_version": 99, "tool_version": "0.0.0"}', "null"],
    ids=["not-json", "an-array", "a-foreign-schema", "json-null"],
)
def test_an_unprojectable_file_exits_two_with_an_empty_stdout(tmp_path: Path, payload: str) -> None:
    """Non-success: never exit 1, and never a half-written document on stdout
    beside a diagnostic."""
    saved = _written(tmp_path, "broken.json", payload)
    for fmt in ("sarif", "github-annotations", "github-summary", "github-outputs"):
        result = run_cli(tmp_path, "report", "--findings", str(saved), "--format", fmt)
        assert result.returncode == 2, f"{fmt}: {result.returncode}"
        assert result.stdout.strip() == "", fmt
        assert result.stderr.strip(), fmt


def test_a_missing_findings_file_exits_two(tmp_path: Path) -> None:
    result = run_cli(tmp_path, "report", "--findings", str(tmp_path / "absent.json"),
                     "--format", "github-outputs")
    assert result.returncode == 2
    assert "cannot read" in result.stderr


def test_a_version_mismatch_warns_but_still_renders(tmp_path: Path) -> None:
    """An envelope from another build is still the honest record of that run --
    a CI job projecting a downloaded artifact has a legitimate reason to read
    it. Warn, never refuse; and stdout must be unaffected by the warning."""
    target = FIXTURES / "failing"
    envelope = json.loads(run_cli(target, "validate", "--format", "json").stdout)
    matching = _written(tmp_path, "same.json", json.dumps(envelope, indent=2))

    envelope["tool_version"] = "0.0.1-from-another-build"
    mismatched = _written(tmp_path, "other.json", json.dumps(envelope, indent=2))

    same = run_cli(target, "report", "--findings", str(matching), "--format", "github-annotations")
    other = run_cli(target, "report", "--findings", str(mismatched), "--format",
                    "github-annotations")

    assert same.returncode == other.returncode == 0
    assert "WARNING" not in same.stderr
    assert "0.0.1-from-another-build" in other.stderr
    assert other.stdout == same.stdout, "the warning must not change what is rendered"


def test_report_ignores_the_global_target(tmp_path: Path) -> None:
    """The one verb that never reads a repository: it must project a saved
    envelope even when --target names a directory with nothing in it."""
    envelope = run_cli(FIXTURES / "failing", "validate", "--format", "json")
    saved = _written(tmp_path, "findings.json", envelope.stdout)
    elsewhere = tmp_path / "empty"
    elsewhere.mkdir()
    result = run_cli(elsewhere, "report", "--findings", str(saved), "--format", "github-outputs")
    assert result.returncode == 0, result.stderr
    assert "status=fail" in result.stdout


def test_a_card_from_detect_projects_without_a_warning(tmp_path: Path) -> None:
    """End to end over the real two files the action writes."""
    target = FIXTURES / "passing"
    envelope = _written(tmp_path, "findings.json",
                        run_cli(target, "validate", "--format", "json").stdout)
    card = _written(tmp_path, "card.json",
                    run_cli(target, "detect", "--format", "json").stdout)
    result = run_cli(target, "report", "--findings", str(envelope), "--card", str(card),
                     "--format", "github-outputs")
    assert result.returncode == 0, result.stderr
    rendered = dict(line.split("=", 1) for line in result.stdout.splitlines())
    assert rendered["dialect"] == "harness"
    assert int(rendered["make-targets"]) > 0
    assert rendered["discovery-warnings"] == "0"


def test_a_malformed_card_exits_two_without_projecting(tmp_path: Path) -> None:
    envelope = _written(tmp_path, "findings.json",
                        run_cli(FIXTURES / "passing", "validate", "--format", "json").stdout)
    card = _written(tmp_path, "card.json", '{"schema_version": 1}')
    result = run_cli(tmp_path, "report", "--findings", str(envelope), "--card", str(card),
                     "--format", "github-outputs")
    assert result.returncode == 2
    assert result.stdout.strip() == ""


def test_projections_are_byte_stable_across_runs(tmp_path: Path) -> None:
    """Two runs over one envelope must agree, or the evidence bundle cannot be
    compared between commits."""
    envelope = _written(tmp_path, "findings.json",
                        run_cli(FIXTURES / "failing", "validate", "--format", "json").stdout)
    for fmt in ("sarif", "github-annotations", "github-summary", "github-outputs"):
        first = run_cli(tmp_path, "report", "--findings", str(envelope), "--format", fmt)
        second = run_cli(tmp_path, "report", "--findings", str(envelope), "--format", fmt)
        assert first.stdout == second.stdout, fmt


def test_report_is_registered_as_a_read_only_verb() -> None:
    """Cross-check against the skill contract's own list, so the two cannot
    drift apart silently."""
    from tests.test_skill_contract import READ_ONLY_INVOCATIONS

    assert "report" in {argv[0] for argv in READ_ONLY_INVOCATIONS}


def test_the_verb_appears_in_the_module_docstring() -> None:
    """The CLI docstring is the verb list a reader meets first."""
    source = (PKG / "cli.py").read_text(encoding="utf-8")
    assert "\n  report    " in source


def test_module_is_importable_without_the_rest_of_the_package() -> None:
    """Purity, observed rather than inferred: the module must import in a
    fresh interpreter with nothing else from this package loaded."""
    module_path = PKG / "report.py"
    program = (
        "import importlib.util,sys;"
        f"spec=importlib.util.spec_from_file_location('r', r'{module_path}');"
        "m=importlib.util.module_from_spec(spec);sys.modules['r']=m;"
        "spec.loader.exec_module(m);"
        "print(sorted(k for k in sys.modules if k.startswith('openspec_graph')))"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", result.stdout
