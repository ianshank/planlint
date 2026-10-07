"""The composite action's contract, exercised locally (change: add-github-action-contract).

The action is YAML, so the usual failure mode is that nobody finds out it is
wrong until a runner says so -- and the current action shipped with an install
line that resolves to nothing, no outputs at all, and a fork guard that could
never fire, none of which any gate in this repository could see.

Two halves, and the second is the point:

* **Declarative.** The input and output names, the absence of a token input or
  ``pull_request_target``, evidence rooted outside the workspace. Text-level,
  because no test in this repository imports a YAML parser and
  ``C-GA-3`` keeps it that way -- the block extractor below is the same
  line-scanning approach ``tests.support.workflow_job_blocks`` already uses on
  ``ci.yml`` (DEC-AQA-005).
* **Executable.** The action's own ``run:`` blocks are extracted and run
  against the labelled fixture targets with GitHub's environment simulated, so
  the status derivation, the evidence bundle and the three gate messages are
  covered by ``make test`` rather than discovered on a runner. A hosted job
  still proves the parts only a runner has (``uses:`` steps, artifact upload,
  the action path); this proves the logic.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from tests.action_support import REPO_ROOT, ActionRun, _action_text, _drive, _needs_bash, _steps

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "action"

# The v1 contract. Adding an output is allowed within a major version; renaming
# or removing one is not, which is why the set is pinned rather than sampled.
EXPECTED_INPUTS = {
    "target", "version", "fail-on", "python-version", "upload-artifact", "artifact-name",
    "change", "dialect",
}

EXPECTED_OUTPUTS = {
    "status", "exit-code", "errors", "warnings", "infos", "findings", "blocking",
    "specs-checked", "rules-triggered", "dialect", "make-targets", "coverage-floor",
    "discovery-warnings", "version", "evidence-dir", "json-path", "sarif-path",
    "evidence-sha256",
}

def _top_level_keys(text: str, section: str) -> set[str]:
    """The two-space-indented keys under a top-level mapping.

    A line scan rather than a parse, for the reason this module's docstring
    gives. Exact about indentation so a nested key cannot be mistaken for a
    declared input or output.
    """
    lines = text.splitlines()
    try:
        start = lines.index(f"{section}:") + 1
    except ValueError:
        return set()
    found: set[str] = set()
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break
        match = re.match(r"^  ([a-z][\w-]*):\s*$", line)
        if match:
            found.add(match.group(1))
    return found

# --- the declarative half ----------------------------------------------------


@pytest.mark.integration
def test_the_action_declares_exactly_the_v1_inputs() -> None:
    """The closed list grew by two named flags (`change`, `dialect`).
    Adding an input is the stronger change; outputs may still grow."""
    assert _top_level_keys(_action_text(), "inputs") == EXPECTED_INPUTS

@pytest.mark.integration
def test_the_action_declares_every_v1_output() -> None:
    """Superset rather than equality: an output may be added inside a major
    version, and pinning equality would turn that into a test failure instead
    of the compatible change it is."""
    declared = _top_level_keys(_action_text(), "outputs")
    assert declared >= EXPECTED_OUTPUTS, f"missing: {sorted(EXPECTED_OUTPUTS - declared)}"

@pytest.mark.integration
def test_the_action_runs_validate_once_and_projects_the_rest() -> None:
    """The property that makes every surface agree: one rule-engine run, and
    every other rendering a projection of the file it wrote."""
    text = _action_text()
    scan = next(step for step in _steps(text) if step.get("id") == "scan")
    body = str(scan["run"])
    assert body.count('planlint "${args[@]}"') == 1
    assert "validate --format sarif" not in text, (
        "SARIF must be projected from the envelope by `report`, not produced by a "
        "second validate run that could disagree with the first"
    )
    for fmt in ("sarif", "github-annotations", "github-summary", "github-outputs"):
        assert f"--format {fmt}" in text, fmt

@pytest.mark.integration
def test_evidence_is_written_outside_the_workspace() -> None:
    """Non-success: the adapter must not write into the repository it scans.
    The CLI's read-only guarantee is the product; breaking it one directory up
    would be the same defect with a different owner."""
    text = _action_text()
    assert "RUNNER_TEMP" in text
    assert "GITHUB_WORKSPACE" not in text

@pytest.mark.integration
def test_the_action_writes_only_to_evidence_and_the_runner_command_files() -> None:
    """Non-success: every redirection in the action has an approved target.

    "Evidence lives outside the workspace" is easy to assert about the
    directory and easy to break with one stray redirection somewhere else. The
    two exemptions are the runner's own command files, which are how a step
    reports anything at all and are not the action's to relocate.
    """
    allowed_prefixes = ("${EVIDENCE}", "${RUNNER_TEMP}", "${OUT_DIR}", "$evidence")
    allowed_exact = ("$GITHUB_OUTPUT", "$GITHUB_STEP_SUMMARY")

    offenders: list[str] = []
    for step in _steps(_action_text()):
        body = step.get("run")
        if not isinstance(body, str):
            continue
        for target in re.findall(r">>?\s*(\S+)", body):
            target = target.strip('"')
            # `2>&1` duplicates a descriptor and `>/dev/null` discards; neither
            # creates a file, so neither is this check's subject.
            if target.startswith(("&", "/dev/")):
                continue
            if target in allowed_exact or target.startswith(allowed_prefixes):
                continue
            offenders.append(f"{step.get('id')}: {target}")
    assert not offenders, f"the action redirects to unapproved path(s): {offenders}"

@pytest.mark.integration
def test_an_index_install_refuses_a_release_without_the_report_verb() -> None:
    """A version predating this contract installs cleanly and then has no verb
    to project with, so the run would die mid-projection with a usage error
    about a subcommand. The check is against the installed CLI, not a pinned
    version number, so the floor moves by itself when the verb does."""
    text = _action_text()
    assert "planlint report --help" in text
    assert "has no 'report' verb" in text

@pytest.mark.integration
def test_the_template_grants_what_a_private_repository_needs() -> None:
    """`upload-sarif` needs a second read permission on a private repository,
    so an adopter who enabled the documented option would otherwise fail in the
    upload step rather than on anything about their specs."""
    template = (REPO_ROOT / "templates" / "spec-gate.yml").read_text(encoding="utf-8")
    block = template.split("permissions:", 1)[1].split("jobs:", 1)[0]
    for permission in ("contents: read", "security-events: write", "actions: read"):
        assert permission in block, permission

@pytest.mark.integration
def test_the_artifact_upload_survives_a_failing_gate() -> None:
    """A red run is exactly when somebody needs the evidence."""
    text = _action_text()
    assert "always() && inputs.upload-artifact == 'true'" in text

@pytest.mark.integration
def test_the_action_needs_no_token_and_no_privileged_permission() -> None:
    """The scan reads untrusted repository content, so it holds nothing worth
    stealing: no token input, and no step that needs a write permission. SARIF
    upload lives in the consumer workflow, where the permission it needs is
    visible to the person who granted it."""
    text = _action_text()
    assert not re.search(r"^  \S*token\S*:", text, re.MULTILINE)
    # Scoped to declarations, not prose: the header comment explains why the
    # upload lives in the consumer workflow, and a guard that failed on its own
    # rationale would be deleted rather than read.
    directives = [
        line for line in text.splitlines()
        if re.match(r"^\s*(-\s*)?(uses|permissions):", line)
    ]
    assert not [line for line in directives if "codeql" in line or "upload-sarif" in line]
    assert not [line for line in directives if line.strip().startswith("permissions:")]

@pytest.mark.integration
@pytest.mark.parametrize(
    "path",
    sorted(
        set(REPO_ROOT.glob(".github/**/*.yml"))
        | set(REPO_ROOT.glob("templates/*.yml"))
        | set(REPO_ROOT.glob("skills/**/*.yml"))
    ),
    ids=lambda p: p.relative_to(REPO_ROOT).as_posix(),
)
def test_no_workflow_or_template_uses_pull_request_target(path: Path) -> None:
    """Non-success, and forbidden by a test rather than by review because the
    failure is silent: `pull_request_target` hands a workflow write permissions
    and secrets while checking out attacker-controlled content, and a template
    that used it would look identical to one that does not.

    Comments included deliberately -- a commented-out example is one paste away
    from being real.
    """
    assert "pull_request_target" not in path.read_text(encoding="utf-8")

@pytest.mark.integration
def test_the_install_override_names_the_published_distribution() -> None:
    """The index-install line has to be visible to the adopter install-line
    guard. It was not: `_requirements()` stopped at `[<>=!~;`, so
    `planlint${INPUT_VERSION}` parsed as a package nobody publishes and the
    line was skipped as somebody else's."""
    from tests.test_adopter_urls import _requirements

    line = next(
        line for line in _action_text().splitlines()
        if "pip install" in line and "planlint" in line
    )
    assert _requirements(line) == ["planlint"], line

@pytest.mark.integration
def test_action_inputs_include_change_and_dialect() -> None:
    declared = _top_level_keys(_action_text(), "inputs")
    assert declared == EXPECTED_INPUTS
    assert {"change", "dialect"} <= declared
    assert not any("token" in name for name in declared)
    text = _action_text()
    # Both new inputs default to empty so templates that omit them keep working.
    assert re.search(r"^  change:$", text, re.MULTILINE)
    assert re.search(r"^  dialect:$", text, re.MULTILINE)

@pytest.mark.integration
def test_action_does_not_pass_require_witness() -> None:
    text = _action_text()
    declared = _top_level_keys(text, "inputs")
    assert "extra-args" not in declared
    assert "args" not in declared
    assert "--require-witness" not in text
    assert not (REPO_ROOT / "action.yml").exists()

@pytest.mark.integration
def test_the_step_extractor_sees_the_whole_action() -> None:
    """Guard the guard: a parser that silently found nothing would make every
    execution test below pass by running no shell at all."""
    steps = _steps(_action_text())
    ids = [step.get("id") for step in steps if step.get("id")]
    assert ids == ["paths", "install", "scan", "project", "gate"], ids
    assert all(isinstance(steps[i].get("run"), str) for i, _ in enumerate(steps) if steps[i].get("run"))
    scan = next(step for step in steps if step.get("id") == "scan")
    assert "planlint --target" in str(scan["run"])
    assert set(scan["env"]) >= {
        "INPUT_TARGET", "INPUT_FAIL_ON", "INPUT_CHANGE", "INPUT_DIALECT", "EVIDENCE",
    }

ACTION_CONTRACT = (
    # (fixture target, status, gate exit, a phrase the gate must explain with)
    ("tests/fixtures/action/passing", "pass", 0, "no findings at or above"),
    ("tests/fixtures/action/failing", "fail", 1, "finding(s) at or above"),
    ("tests/fixtures/action/empty-tree", "indeterminate", 1, "gates nothing"),
    ("tests/fixtures/action/no-tree", "error", 1, "precondition or usage error"),
    ("tests/fixtures/action/nested/sub", "pass", 0, "no findings at or above"),
)

@pytest.mark.e2e
@pytest.mark.parametrize(
    "target,status,gate_exit,phrase",
    ACTION_CONTRACT,
    ids=[row[0].rsplit("/", 1)[-1] for row in ACTION_CONTRACT],
)
@_needs_bash
def test_the_action_reports_each_fixtures_labelled_status(
    tmp_path: Path, target: str, status: str, gate_exit: int, phrase: str
) -> None:
    """The whole point of the rewrite, asserted end to end.

    `empty-tree` and `no-tree` are the two rows that matter most: both exit the
    gate non-zero, and each explains itself differently, because "there was
    nothing to check" and "the tool could not run" need different things done
    about them -- and neither is a pass.
    """
    run = _drive(tmp_path, target)
    assert run.outputs("project").get("status") == status

    gate = run.run_step("gate")
    assert gate == gate_exit, run.logs["gate"]
    assert phrase in run.logs["gate"], run.logs["gate"]

@pytest.mark.e2e
@_needs_bash
def test_a_failing_run_populates_the_whole_evidence_bundle(tmp_path: Path) -> None:
    run = _drive(tmp_path, "tests/fixtures/action/failing")
    evidence = Path(run.outputs("paths")["evidence-dir"])

    for name in ("findings.json", "findings.sarif", "dialect-card.json", "detect.txt",
                 "run.json", "annotations.txt", "summary.md"):
        assert (evidence / name).is_file(), f"{name} missing from the evidence bundle"

    envelope = json.loads((evidence / "findings.json").read_text(encoding="utf-8"))
    assert envelope["blocking"] > 0
    metadata = json.loads((evidence / "run.json").read_text(encoding="utf-8"))
    assert metadata["validate_exit_code"] == 1
    assert metadata["fail_on"] == "ERROR"

    outputs = run.outputs("project")
    assert outputs["blocking"] == str(envelope["blocking"])
    assert outputs["evidence-sha256"], "the envelope must be hashed for the artifact"
    assert (evidence / "annotations.txt").read_text(encoding="utf-8").startswith("::error ")

@pytest.mark.e2e
@_needs_bash
def test_an_unscannable_target_produces_the_error_status_and_no_envelope(tmp_path: Path) -> None:
    """Non-success: the one status the envelope cannot describe. `validate`
    exits 2 writing nothing to stdout, so there is no envelope to read, and the
    adapter -- not the projection -- has to say so."""
    run = _drive(tmp_path, "tests/fixtures/action/no-tree")
    evidence = Path(run.outputs("paths")["evidence-dir"])

    assert run.outputs("scan")["exit-code"] == "2"
    assert not (evidence / "findings.json").exists()
    assert run.outputs("project")["status"] == "error"
    assert "no openspec/ directory" in (evidence / "validate.stderr.txt").read_text(encoding="utf-8")
    assert json.loads((evidence / "run.json").read_text(encoding="utf-8"))["validate_exit_code"] == 2

@pytest.mark.e2e
@_needs_bash
def test_annotation_paths_resolve_from_the_repository_root(tmp_path: Path) -> None:
    """A finding's path is relative to the target; GitHub resolves an
    annotation's ``file=`` against the repository root. The action passes the
    difference to ``report --path-prefix``, so the assertion that matters is
    not the shape of the string but that joining it to the checkout reaches the
    spec the finding is actually about.
    """
    run = _drive(tmp_path, "tests/fixtures/action/failing")
    annotations = (
        Path(run.outputs("paths")["evidence-dir"]) / "annotations.txt"
    ).read_text(encoding="utf-8")

    cited = re.findall(r"file=([^,]+)", annotations)
    assert cited, "the failing fixture must produce located annotations"
    for path in cited:
        assert path.startswith("tests/fixtures/action/failing/"), path
        assert (REPO_ROOT / path).is_file(), f"{path} does not resolve from the repository root"

@pytest.mark.e2e
@_needs_bash
def test_a_nested_target_is_scanned_at_its_own_root(tmp_path: Path) -> None:
    """The target one directory down is a real target: it detects its own
    machinery rather than the repository's."""
    nested = tmp_path / "nested"
    nested.mkdir()
    run = ActionRun(REPO_ROOT, nested, target="tests/fixtures/action/nested/sub")
    assert run.run_step("paths") == 0
    assert run.run_step("scan") == 0, run.logs["scan"]
    assert run.run_step("project") == 0, run.logs["project"]

    card = Path(run.outputs("paths")["evidence-dir"]) / "dialect-card.json"
    assert json.loads(card.read_text(encoding="utf-8"))["dialect"] == "harness"
    assert run.outputs("project")["status"] == "pass"
    assert run.outputs("project")["specs-checked"] == "1"

@pytest.mark.e2e
@_needs_bash
def test_the_step_summary_reaches_the_job_summary_file(tmp_path: Path) -> None:
    run = _drive(tmp_path, "tests/fixtures/action/failing")
    summary = run.summary.read_text(encoding="utf-8")
    assert "## planlint" in summary
    assert "`fail`" in summary

@pytest.mark.e2e
@_needs_bash
def test_the_evidence_directory_is_outside_the_scanned_tree(tmp_path: Path) -> None:
    """Non-success, observed rather than asserted from the YAML: the scanned
    fixture must be byte-identical before and after a run."""
    target = REPO_ROOT / "tests" / "fixtures" / "action" / "failing"
    before = {p: p.read_bytes() for p in sorted(target.rglob("*")) if p.is_file()}
    assert before, "fixture is empty; the comparison would be vacuous"

    run = _drive(tmp_path, "tests/fixtures/action/failing")
    run.run_step("gate")

    after = {p: p.read_bytes() for p in sorted(target.rglob("*")) if p.is_file()}
    assert after == before, "the action modified the repository it was scanning"
    evidence = Path(run.outputs("paths")["evidence-dir"]).resolve()
    assert evidence.is_relative_to(tmp_path.resolve())
    assert not evidence.is_relative_to(target.resolve())

def _capture_validate_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **inputs: str
) -> list[str]:
    """Run the scan step against a shim ``planlint`` that records argv.

    The shim exits 0 without importing the real CLI: these tests are about
    which flags the adapter appended, not about evaluating rules.
    """
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    log_path = tmp_path / "planlint-argv.jsonl"
    script = shim_dir / "planlint"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"log = {str(log_path)!r}\n"
        "if '--version' in sys.argv:\n"
        "    print('planlint 0.0.0-shim')\n"
        "    raise SystemExit(0)\n"
        "with open(log, 'a', encoding='utf-8') as fh:\n"
        "    json.dump(sys.argv[1:], fh)\n"
        "    fh.write('\\n')\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    runner_temp = tmp_path / "runner"
    runner_temp.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    # Construct before PATH is patched: ActionRun seeds the install version
    # from the real `planlint --version`.
    run = ActionRun(workspace, runner_temp, **inputs)
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ['PATH']}")
    assert run.run_step("paths") == 0, run.logs.get("paths")
    assert run.run_step("scan") == 0, run.logs.get("scan")
    rows = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    validate_rows = [row for row in rows if "validate" in row]
    assert len(validate_rows) == 1, rows
    return validate_rows[0]

@pytest.mark.integration
def test_empty_change_and_dialect_inputs_omit_cli_flags() -> None:
    scan = next(step for step in _steps(_action_text()) if step.get("id") == "scan")
    body = str(scan["run"])
    assert '[ -n "$INPUT_CHANGE" ]' in body
    assert '[ -n "$INPUT_DIALECT" ]' in body
    assert 'args+=( --change "$INPUT_CHANGE" )' in body
    assert 'args+=( --dialect "$INPUT_DIALECT" )' in body
    # The auto override is a real CLI choice; it must not appear as a
    # fallback in the script, only as `$INPUT_DIALECT` when the input is set.
    assert "--dialect auto" not in body

@pytest.mark.e2e
@_needs_bash
def test_empty_change_and_dialect_inputs_omit_cli_flags_on_the_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv = _capture_validate_argv(tmp_path, monkeypatch)
    assert "--change" not in argv
    assert "--dialect" not in argv

@pytest.mark.e2e
@_needs_bash
def test_nonempty_change_input_passes_change_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv = _capture_validate_argv(tmp_path, monkeypatch, change="add-thing")
    assert argv.count("validate") == 1
    assert "--change" in argv
    assert argv[argv.index("--change") + 1] == "add-thing"
    assert "--dialect" not in argv

@pytest.mark.e2e
@_needs_bash
def test_nonempty_dialect_input_passes_dialect_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv = _capture_validate_argv(tmp_path, monkeypatch, dialect="harness")
    assert "--dialect" in argv
    assert argv[argv.index("--dialect") + 1] == "harness"
    assert "--change" not in argv
