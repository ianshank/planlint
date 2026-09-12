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
  line-scanning approach ``tests/test_ci_hardening.py`` already uses on
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
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTION = REPO_ROOT / ".github" / "actions" / "planlint" / "action.yml"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "action"

# The v1 contract. Adding an output is allowed within a major version; renaming
# or removing one is not, which is why the set is pinned rather than sampled.
EXPECTED_INPUTS = {
    "target", "version", "fail-on", "python-version", "upload-artifact", "artifact-name",
}
EXPECTED_OUTPUTS = {
    "status", "exit-code", "errors", "warnings", "infos", "findings", "blocking",
    "specs-checked", "rules-triggered", "dialect", "make-targets", "coverage-floor",
    "discovery-warnings", "version", "evidence-dir", "json-path", "sarif-path",
    "evidence-sha256",
}

_EXPRESSION = re.compile(r"\$\{\{\s*([^}]+?)\s*\}\}")


def _github_bash() -> str | None:
    """The interpreter GitHub uses for a ``shell: bash`` step on this platform.

    On Linux and macOS that is plain ``bash``. On Windows it is the bash that
    ships with Git for Windows -- deliberately *not* whatever ``bash`` resolves
    to on PATH, which is System32's WSL launcher. A hosted Windows runner has
    no WSL distribution installed, so that launcher answers every invocation
    with a UTF-16 error and exit 1, and this simulation would be reporting the
    absence of WSL rather than anything about the action.

    Mirroring the runner's own choice keeps the simulation faithful on both
    platforms instead of running on only one. Returns ``None`` when no such
    interpreter exists, so the caller can skip with a reason rather than fail
    with a confusing one.
    """
    if os.name != "nt":
        return "bash"
    roots = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
    ]
    for root in roots:
        candidate = Path(root) / "Git" / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return None


_BASH = _github_bash()

# The executable half only. The declarative assertions above read the YAML and
# run everywhere, including the Windows leg -- it is the contract that has to
# hold on every platform, while the shell body is POSIX and runs where GitHub
# runs it.
_needs_bash = pytest.mark.skipif(
    _BASH is None,
    reason="no Git for Windows bash on this machine; GitHub uses it for `shell: bash` "
    "on Windows runners, and PATH's `bash` there is the WSL launcher",
)


def _posix(path: Path | str) -> str:
    """A path spelled the way the interpreter above expects to read it.

    Git Bash accepts ``D:/a/_temp/x`` and mangles ``D:\\a\\_temp\\x``, whose
    backslashes it reads as escapes. No-op on POSIX.
    """
    return Path(path).as_posix()


def _action_text() -> str:
    return ACTION.read_text(encoding="utf-8")


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


def test_the_action_declares_exactly_the_v1_inputs() -> None:
    assert _top_level_keys(_action_text(), "inputs") == EXPECTED_INPUTS


def test_the_action_declares_every_v1_output() -> None:
    """Superset rather than equality: an output may be added inside a major
    version, and pinning equality would turn that into a test failure instead
    of the compatible change it is."""
    declared = _top_level_keys(_action_text(), "outputs")
    assert declared >= EXPECTED_OUTPUTS, f"missing: {sorted(EXPECTED_OUTPUTS - declared)}"


def test_the_action_runs_validate_once_and_projects_the_rest() -> None:
    """The property that makes every surface agree: one rule-engine run, and
    every other rendering a projection of the file it wrote."""
    text = _action_text()
    assert len(re.findall(r"planlint --target \"\$INPUT_TARGET\" validate", text)) == 1
    assert "validate --format sarif" not in text, (
        "SARIF must be projected from the envelope by `report`, not produced by a "
        "second validate run that could disagree with the first"
    )
    for fmt in ("sarif", "github-annotations", "github-summary", "github-outputs"):
        assert f"--format {fmt}" in text, fmt


def test_evidence_is_written_outside_the_workspace() -> None:
    """Non-success: the adapter must not write into the repository it scans.
    The CLI's read-only guarantee is the product; breaking it one directory up
    would be the same defect with a different owner."""
    text = _action_text()
    assert "RUNNER_TEMP" in text
    assert "GITHUB_WORKSPACE" not in text


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


def test_an_index_install_refuses_a_release_without_the_report_verb() -> None:
    """A version predating this contract installs cleanly and then has no verb
    to project with, so the run would die mid-projection with a usage error
    about a subcommand. The check is against the installed CLI, not a pinned
    version number, so the floor moves by itself when the verb does."""
    text = _action_text()
    assert "planlint report --help" in text
    assert "has no 'report' verb" in text


def test_the_template_grants_what_a_private_repository_needs() -> None:
    """`upload-sarif` needs a second read permission on a private repository,
    so an adopter who enabled the documented option would otherwise fail in the
    upload step rather than on anything about their specs."""
    template = (REPO_ROOT / "templates" / "spec-gate.yml").read_text(encoding="utf-8")
    block = template.split("permissions:", 1)[1].split("jobs:", 1)[0]
    for permission in ("contents: read", "security-events: write", "actions: read"):
        assert permission in block, permission


def test_the_artifact_upload_survives_a_failing_gate() -> None:
    """A red run is exactly when somebody needs the evidence."""
    text = _action_text()
    assert "always() && inputs.upload-artifact == 'true'" in text


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


# --- the executable half -----------------------------------------------------


def _steps(text: str) -> list[dict[str, object]]:
    """Every step under ``runs.steps``, as ``{id, uses, run, env}``.

    Scans the six-space-indented ``- `` items and their keys, and lifts a
    ``run: |`` block scalar by dedenting its body. Narrow on purpose: it
    understands exactly the shapes this action uses, and raises rather than
    guessing at anything else.
    """
    lines = text.splitlines()
    start = lines.index("  steps:") + 1
    steps: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    block_key: str | None = None
    block: list[str] = []
    in_env = False

    def flush() -> None:
        nonlocal block_key, block
        if current is not None and block_key:
            current[block_key] = "\n".join(block).rstrip() + "\n"
        block_key, block = None, []

    for raw in lines[start:]:
        if block_key:
            if raw.strip() and not raw.startswith(" " * 8):
                flush()
            else:
                block.append(raw[8:] if len(raw) > 8 else "")
                continue
        if raw.startswith("    - "):
            flush()
            current = {"env": {}}
            steps.append(current)
            in_env = False
            raw = "      " + raw[6:]
        if current is None:
            continue
        if re.match(r"^      env:\s*$", raw):
            in_env = True
            continue
        if in_env:
            pair = re.match(r"^        ([A-Za-z_][\w-]*):\s*(.+?)\s*$", raw)
            if pair:
                envs = current["env"]
                assert isinstance(envs, dict)
                envs[pair.group(1)] = pair.group(2)
                continue
            in_env = False
        entry = re.match(r"^      (id|uses|shell|if):\s*(.+?)\s*$", raw)
        if entry:
            current[entry.group(1)] = entry.group(2)
            continue
        if re.match(r"^      run:\s*\|\s*$", raw):
            block_key, block = "run", []
    flush()
    return steps


def test_the_step_extractor_sees_the_whole_action() -> None:
    """Guard the guard: a parser that silently found nothing would make every
    execution test below pass by running no shell at all."""
    steps = _steps(_action_text())
    ids = [step.get("id") for step in steps if step.get("id")]
    assert ids == ["paths", "install", "scan", "project", "gate"], ids
    assert all(isinstance(steps[i].get("run"), str) for i, _ in enumerate(steps) if steps[i].get("run"))
    scan = next(step for step in steps if step.get("id") == "scan")
    assert "planlint --target" in str(scan["run"])
    assert set(scan["env"]) >= {"INPUT_TARGET", "INPUT_FAIL_ON", "EVIDENCE"}


def _resolve(expression: str, context: dict[str, object]) -> str:
    """Evaluate the ``${{ ... }}`` forms this action uses, and only those."""
    def substitute(match: re.Match[str]) -> str:
        parts = match.group(1).split(".")
        if parts[0] == "inputs":
            inputs = context["inputs"]
            assert isinstance(inputs, dict)
            return str(inputs.get(parts[1], ""))
        if parts[0] == "steps":
            steps = context["steps"]
            assert isinstance(steps, dict)
            return str(steps.get(parts[1], {}).get(parts[3], ""))
        raise AssertionError(f"unsupported action expression: {match.group(1)}")

    return _EXPRESSION.sub(substitute, expression)


class ActionRun:
    """One simulated invocation of the composite action's shell steps."""

    def __init__(self, workspace: Path, runner_temp: Path, **inputs: str) -> None:
        self.context: dict[str, object] = {
            "inputs": {
                "target": ".", "version": "", "fail-on": "ERROR",
                "python-version": "3.12", "upload-artifact": "true",
                "artifact-name": "planlint-evidence", **inputs,
            },
            # The install step is a `uses:`-adjacent concern (it installs the
            # CLI that is already installed here), so its one output is seeded
            # from the real command rather than by running pip again.
            "steps": {"install": {"version": _installed_version()}},
        }
        self.workspace = workspace
        self.runner_temp = runner_temp
        self.summary = runner_temp / "step-summary.md"
        self.summary.write_text("", encoding="utf-8")
        self.logs: dict[str, str] = {}

    def run_step(self, step_id: str) -> int:
        step = next(s for s in _steps(_action_text()) if s.get("id") == step_id)
        outputs_file = self.runner_temp / f"{step_id}-outputs.txt"
        outputs_file.write_text("", encoding="utf-8")

        env = {
            "PATH": os.environ["PATH"],
            "HOME": _posix(self.runner_temp),
            "RUNNER_TEMP": _posix(self.runner_temp),
            "GITHUB_OUTPUT": _posix(outputs_file),
            "GITHUB_STEP_SUMMARY": _posix(self.summary),
            "GITHUB_ACTION_PATH": _posix(ACTION.parent),
        }
        # Git Bash needs SYSTEMROOT to resolve its own helpers; harmless
        # elsewhere and absent from the minimal env above without it.
        for passthrough in ("SYSTEMROOT", "SystemRoot", "TEMP", "TMP", "COMSPEC"):
            if passthrough in os.environ:
                env.setdefault(passthrough, os.environ[passthrough])
        raw_env = step["env"]
        assert isinstance(raw_env, dict)
        for key, value in raw_env.items():
            env[key] = _resolve(value, self.context)

        assert _BASH is not None, "run_step needs the interpreter the skip guard checks for"
        # `-e` is not decoration: GitHub runs a composite `shell: bash` step as
        # `bash --noprofile --norc -eo pipefail {0}`, so a body that merely
        # omits `set -e` still starts under errexit. Simulating that is what
        # caught the action's fallible steps dying on their first non-zero
        # command before an exit code could be recorded.
        result = subprocess.run(
            [_BASH, "--noprofile", "--norc", "-eo", "pipefail", "-c", str(step["run"])],
            cwd=self.workspace, env=env, capture_output=True, text=True, check=False,
        )
        self.logs[step_id] = result.stdout + result.stderr
        parsed: dict[str, str] = {}
        for line in outputs_file.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                parsed[key] = value
        steps = self.context["steps"]
        assert isinstance(steps, dict)
        steps[step_id] = parsed
        return result.returncode

    def outputs(self, step_id: str) -> dict[str, str]:
        steps = self.context["steps"]
        assert isinstance(steps, dict)
        return dict(steps.get(step_id, {}))


def _installed_version() -> str:
    result = subprocess.run(["planlint", "--version"], capture_output=True, text=True, check=True)
    return result.stdout.split()[-1]


def _drive(tmp_path: Path, target: str) -> ActionRun:
    """Run paths -> scan -> project and return the simulation, gate not yet applied."""
    run = ActionRun(REPO_ROOT, tmp_path, target=target)
    assert run.run_step("paths") == 0, run.logs["paths"]
    assert run.run_step("scan") == 0, run.logs["scan"]
    assert run.run_step("project") == 0, run.logs["project"]
    return run


ACTION_CONTRACT = (
    # (fixture target, status, gate exit, a phrase the gate must explain with)
    ("tests/fixtures/action/passing", "pass", 0, "no findings at or above"),
    ("tests/fixtures/action/failing", "fail", 1, "finding(s) at or above"),
    ("tests/fixtures/action/empty-tree", "indeterminate", 1, "gates nothing"),
    ("tests/fixtures/action/no-tree", "error", 1, "precondition or usage error"),
    ("tests/fixtures/action/nested/sub", "pass", 0, "no findings at or above"),
)


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


@_needs_bash
def test_the_step_summary_reaches_the_job_summary_file(tmp_path: Path) -> None:
    run = _drive(tmp_path, "tests/fixtures/action/failing")
    summary = run.summary.read_text(encoding="utf-8")
    assert "## planlint" in summary
    assert "`fail`" in summary


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
