"""The CI configuration as the workflows and the hooks table state it.

Moved from ``tests/test_ci_hardening.py`` by ``shape-the-test-suite`` (R-TSS-2): the
``ci.yml`` job and step claims, the two-track and one-run workflow guards, the
``docs/hooks.md`` table in both directions, and the ruff / mypy configuration
claims of ``select-zero-cost-guards``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.support import (
    env_without_coverage,
    read_pyproject,
    workflow_job_blocks,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- AC-CH-4 / AC-CH-7: claims about the CI configuration itself -------------
# Both acceptance criteria describe properties of the committed workflow and
# Makefile rather than of any Python function, and both cited tests that were
# never written -- found by tests/test_spec_test_citations.py, the guard that
# now holds every `_Verified by:` citation to a test that exists. Asserted
# against the real files so the criteria stop being prose.


@pytest.mark.integration
def test_t201_is_selected_with_exactly_the_cli_and_tools_exempt() -> None:
    """select-zero-cost-guards R-ZCG-1 / R-ZCG-10: `print` is held to the two
    places stdout is the product. Nothing else about `select` is asserted --
    a second copy of the list would be the drift this test exists to catch."""
    lint = read_pyproject()["tool"]["ruff"]["lint"]
    assert "T201" in lint["select"], "T201 is not selected; a library-module print passes lint"
    exempt = {path for path, rules in lint["per-file-ignores"].items() if "T201" in rules}
    assert exempt == {"openspec_graph/cli.py", "tools/*"}, exempt

@pytest.mark.integration
def test_mypy_is_strict_and_warns_on_unreachable_code() -> None:
    """select-zero-cost-guards R-ZCG-3 / R-ZCG-10: strict is the mode, with
    `warn_unreachable` on its own because `strict` does not include it, and
    the 3.10 floor still the version mypy checks against."""
    mypy = read_pyproject()["tool"]["mypy"]
    assert mypy.get("strict") is True, "mypy is not strict; a bare `dict` annotation passes"
    assert mypy.get("warn_unreachable") is True
    assert mypy.get("python_version") == "3.10"

def _plant_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    """A throwaway checkout carrying this repository's own tool config."""
    (tmp_path / "pyproject.toml").write_text(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for relative, body in files.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return tmp_path

@pytest.mark.e2e
def test_a_print_in_a_library_module_fails_lint(tmp_path: Path) -> None:
    """select-zero-cost-guards R-ZCG-2 / R-ZCG-11 (non-success): under this
    repository's own per-file-ignores, the same `print` is a finding in a
    library module and not at the two exempted paths -- the gate fires, and
    fires only where it should."""
    tree = _plant_tree(tmp_path, {
        "openspec_graph/leak.py": 'print("x")\n',
        "openspec_graph/cli.py": 'print("x")\n',
        "tools/t.py": 'print("x")\n',
    })
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--select", "T201",
         "--output-format", "json", "openspec_graph", "tools"],
        cwd=tree, capture_output=True, text=True, check=False,
        env=env_without_coverage(),
    )
    assert result.returncode == 1, result.stderr
    findings = json.loads(result.stdout)
    located = [(f["code"], Path(f["filename"]).relative_to(tree).as_posix()) for f in findings]
    assert located == [("T201", "openspec_graph/leak.py")], located

@pytest.mark.e2e
def test_a_bare_generic_in_tools_fails_typecheck(tmp_path: Path) -> None:
    """select-zero-cost-guards R-ZCG-4 / R-ZCG-11 (non-success): under this
    repository's own mypy configuration, a parameter annotated as bare `dict`
    is a `type-arg` error -- the exact finding strict mode cleared from
    tools/diff_spec_graph.py, shown to stay a finding."""
    tree = _plant_tree(tmp_path, {"tools/bare.py": "def f(d: dict) -> None: ...\n"})
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--config-file", "pyproject.toml",
         "--cache-dir", os.devnull, "tools/bare.py"],
        cwd=tree, capture_output=True, text=True, check=False,
        env=env_without_coverage(),
    )
    assert result.returncode != 0, result.stdout
    assert "type-arg" in result.stdout, result.stdout

@pytest.mark.integration
def test_lint_is_a_hard_gate() -> None:
    """AC-CH-4 (non-success): `make lint` fails on a violation and offers no
    "skipping" escape hatch.

    The failure mode this forbids is a gate that degrades to a pass when its
    tool is missing -- the "configured but not enforced" class this project
    exists to catch in other repositories.
    """
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    lint_recipe = [
        line for line in makefile.splitlines() if line.startswith("\t") and "ruff" in line
    ]

    assert lint_recipe, "no ruff invocation found in the Makefile's lint target"
    for line in lint_recipe:
        assert not line.lstrip("\t").startswith("-"), (
            f"lint recipe {line!r} is prefixed with '-', which makes make ignore "
            "its exit code -- the gate would pass on a violation"
        )
        assert "|| true" not in line and "|| echo" not in line, (
            f"lint recipe {line!r} swallows its own failure"
        )
        assert "skipping" not in line.lower()

    # And CI runs that same target rather than a laxer inline command.
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "make lint" in workflow, "CI does not run the `make lint` gate"

@pytest.mark.integration
def test_graph_diff_artifact_uploaded() -> None:
    """AC-CH-7: the graph-diff job publishes the graph and its comparison, so a
    reviewer can see what changed rather than taking the job's word for it."""
    blocks = _ci_job_blocks(_ci_workflow_text())
    graph_diff = blocks.get("graph-diff", "")
    assert "upload-artifact" in graph_diff, "graph-diff job uploads no artifact"
    assert "base.json" in graph_diff, "graph-diff never uploads base.json"
    assert "head.json" in graph_diff, "graph-diff never uploads head.json"

# --- harden-two-track-e2e-aqa: the two-track e2e gates exist and stay synced ---


def _ci_workflow_text() -> str:
    return (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

# The parser lives in tests/support.py as `workflow_job_blocks` since
# harden-ci-workflows gave it a second module; the alias keeps this module's
# two parser tests and every call site byte-identical (R-HCW-16).
_ci_job_blocks = workflow_job_blocks

@pytest.mark.unit
def test_ci_job_blocks_returns_empty_when_jobs_key_is_absent() -> None:
    # The guard tests above must fail on a real missing job, not on a parser
    # that silently found nothing.
    assert _ci_job_blocks("name: CI\non: push\n") == {}

@pytest.mark.unit
def test_ci_job_blocks_ignores_comments_mentioning_jobs() -> None:
    text = "jobs:\n  test:\n    # see the other jobs: for context\n    runs-on: ubuntu-latest\n"
    assert set(_ci_job_blocks(text)) == {"test"}

@pytest.mark.integration
def test_ci_workflow_has_a_windows_job() -> None:
    """AC-AQA-2: the platform guard tests (path separators, console encoding,
    symlink privilege) must actually execute on the OS they guard."""
    blocks = _ci_job_blocks(_ci_workflow_text())
    windows = {name: body for name, body in blocks.items() if "windows-latest" in body}
    assert windows, (
        "ci.yml has no windows-latest job -- ubuntu-only CI is how three "
        "Windows-blind defects shipped green"
    )
    body = next(iter(windows.values()))
    for gate in ("make lint", "make typecheck", "make test"):
        assert gate in body, f"the Windows job must run `{gate}`, the same gates as `test`"

@pytest.mark.integration
def test_ci_workflow_has_an_encoding_stress_job() -> None:
    """AC-AQA-3: the encoding crash's original failure environment is itself
    a gate, so a regression can't ship silently the way the original did."""
    blocks = _ci_job_blocks(_ci_workflow_text())
    stressed = {name: body for name, body in blocks.items() if "PYTHONIOENCODING" in body}
    assert stressed, "ci.yml has no job running under an ASCII-only console"
    assert "make e2e-live" in next(iter(stressed.values())), (
        "the encoding-stress job must run the live track (`make e2e-live`)"
    )

@pytest.mark.integration
def test_hooks_ci_table_lists_every_ci_job() -> None:
    """AC-AQA-4 (non-success): a ci.yml job absent from docs/hooks.md's CI
    hooks table fails the suite -- the `packaging` drift this package
    backfills is a hard error on recurrence, never a silent doc gap.

    Matches the job id only as a backtick-quoted table cell, not anywhere in
    prose -- `graph-diff` and `release` are named in the body text below the
    table, so a bare substring check would false-pass on a missing row."""
    jobs = set(_ci_job_blocks(_ci_workflow_text()))
    assert jobs, "parsed no jobs from ci.yml -- the parser, not the table, is broken"
    hooks = (REPO_ROOT / "docs" / "hooks.md").read_text(encoding="utf-8")
    # A job row looks like `| \`job-name\` ... |` in the CI hooks table.
    table_cells = set(re.findall(r"^\|\s*`([\w-]+)`", hooks, re.MULTILINE))
    missing = sorted(job for job in jobs if job not in table_cells)
    assert not missing, f"docs/hooks.md CI hooks table is missing rows for jobs: {missing}"

_SUITE_STEP = "make test"

_COVERAGE_REPORT = "coverage.json"

_UPLOAD_ACTION = "upload-artifact"

def _workflow_steps(job_body: str) -> list[str]:
    """A job's `steps:` list, one text per step, comment lines dropped."""
    steps: list[list[str]] = []
    in_steps = False
    for line in job_body.splitlines():
        if re.match(r"^    steps:\s*$", line):
            in_steps = True
            continue
        if not in_steps or line.lstrip().startswith("#"):
            continue
        if re.match(r"^      - ", line):
            steps.append([line])
        elif steps:
            steps[-1].append(line)
    return ["\n".join(step) for step in steps]

def _uploads_report_always(step: str, report: str) -> bool:
    return (
        _UPLOAD_ACTION in step
        and re.search(r"^\s*if:\s*always\(\)\s*$", step, re.MULTILINE) is not None
        and re.search(rf"^\s*path:\s*{re.escape(report)}\s*$", step, re.MULTILINE) is not None
    )

def _suite_jobs_without_coverage_upload(workflow_text: str) -> list[str]:
    """Every job that runs `make test` and does not, under `if: always()`,
    upload `coverage.json` through the upload-artifact action."""
    return sorted(
        name
        for name, body in workflow_job_blocks(workflow_text).items()
        if _SUITE_STEP in body
        and not any(_uploads_report_always(step, _COVERAGE_REPORT) for step in _workflow_steps(body))
    )

@pytest.mark.integration
def test_every_job_running_the_suite_uploads_its_coverage_report() -> None:
    """R-MCO-7: each leg's coverage.json is what the floor ratchet reads
    (R-MCO-12), so every job that runs `make test` uploads it under
    `if: always()` -- a red leg's report is uploaded on purpose and excluded
    by the ratchet, never lost."""
    text = _ci_workflow_text()
    suite_jobs = [name for name, body in _ci_job_blocks(text).items() if _SUITE_STEP in body]
    assert suite_jobs, f"no ci.yml job runs `{_SUITE_STEP}`"
    assert _suite_jobs_without_coverage_upload(text) == []

_PLANTED_SUITE_JOBS = textwrap.dedent(
    """\
    jobs:
      silent:
        steps:
          - run: make test
      sometimes:
        steps:
          - run: make test
          - uses: actions/upload-artifact@0000000000000000000000000000000000000000 # v7.0.1
            with:
              name: coverage-x
              path: coverage.json
      recorded:
        steps:
          - run: make test
          # the per-leg report, uploaded red or green
          - uses: actions/upload-artifact@0000000000000000000000000000000000000000 # v7.0.1
            if: always()
            with:
              name: coverage-y
              path: coverage.json
      unrelated:
        steps:
          - run: make lint
    """
)

@pytest.mark.unit
def test_a_suite_job_without_a_coverage_upload_is_named() -> None:
    """R-MCO-13: a job running the suite with no upload step is named by id,
    and so is one whose upload step would be skipped on a red leg."""
    assert _suite_jobs_without_coverage_upload(_PLANTED_SUITE_JOBS) == ["silent", "sometimes"]

def _hooks_ci_table_cells(hooks_text: str) -> list[str]:
    """The backticked first cell of every row in docs/hooks.md's CI hooks table."""
    return re.findall(r"^\|\s*`([\w-]+)`", hooks_text, re.MULTILINE)

def _workflow_job_and_file_names() -> tuple[set[str], set[str]]:
    jobs: set[str] = set()
    files: set[str] = set()
    for workflow in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        files.add(workflow.stem)
        jobs.update(workflow_job_blocks(workflow.read_text(encoding="utf-8")))
    return jobs, files

def _hooks_rows_naming_no_job(
    hooks_text: str, job_names: set[str], workflow_names: set[str]
) -> list[str]:
    """Rows whose first cell is neither a job id in any workflow nor a workflow
    file's stem -- which is how the `release` row, naming `release.yml`, is
    allowed."""
    return sorted(
        cell
        for cell in _hooks_ci_table_cells(hooks_text)
        if cell not in job_names and cell not in workflow_names
    )

@pytest.mark.integration
def test_every_hooks_ci_table_row_names_a_job_or_workflow() -> None:
    """R-MCO-7 / AC-MCO-10: the reverse of `test_hooks_ci_table_lists_every_ci_job`
    -- a row for a job that no longer exists is a stale promise, named here."""
    hooks = (REPO_ROOT / "docs" / "hooks.md").read_text(encoding="utf-8")
    assert _hooks_ci_table_cells(hooks), "docs/hooks.md has no CI hooks table rows"
    jobs, files = _workflow_job_and_file_names()
    assert _hooks_rows_naming_no_job(hooks, jobs, files) == []

@pytest.mark.integration
def test_a_hooks_row_naming_no_job_is_named() -> None:
    """R-MCO-13: a planted row for a job no workflow has is named; the row for
    a separate workflow file is not."""
    jobs, files = _workflow_job_and_file_names()
    planted = (
        "| Job | Trigger | Gate |\n|---|---|---|\n"
        "| `test` (3.10 to 3.14) | push + PR | x |\n"
        "| `gone-job` | push + PR | x |\n"
        "| `release` (separate workflow) | `v*` tag | x |\n"
    )
    assert _hooks_rows_naming_no_job(planted, jobs, files) == ["gone-job"]

# --- add-github-action-contract: the composite action is actually executed ----


@pytest.mark.integration
def test_ci_workflow_has_an_action_contract_job() -> None:
    """AC: the action runs somewhere.

    Every other gate in this repository reads `action.yml` as text. The action
    shipped once with an install line that resolved to no published
    distribution, no `outputs:` block at all, and a SARIF-upload guard that
    could never fire -- none of which a text check could see, because each one
    was well-formed YAML saying the wrong thing. This job is the one that runs
    it.
    """
    blocks = _ci_job_blocks(_ci_workflow_text())
    job = blocks.get("action-contract", "")
    assert job, "ci.yml defines no action-contract job"

    assert "uses: ./.github/actions/planlint" in job, (
        "the contract job must run the action in this checkout, not a published ref"
    )
    assert "continue-on-error: true" in job, (
        "a deliberately red fixture must be allowed to report its outputs rather "
        "than ending the job at the first failing leg"
    )
    # The scan must work in the posture a fork pull request gets: a read-only
    # token and no secrets.
    assert "contents: read" in job
    assert "secrets." not in job, "the scan must need no secret"

@pytest.mark.integration
def test_every_action_fixture_has_a_contract_leg() -> None:
    """Non-success: a sixth fixture cannot be added without a leg asserting it.

    Discovered from disk rather than listed, the same design rule
    `tests/test_adopter_urls.py` states for its own corpus -- a fixture outside
    the matrix is a labelled expectation nothing checks.
    """
    fixtures = REPO_ROOT / "tests" / "fixtures" / "action"
    on_disk = {
        # `nested` is scanned at its own subdirectory, so the matrix names the
        # fixture rather than the target path.
        path.name
        for path in fixtures.iterdir()
        if path.is_dir()
    }
    assert on_disk, "no action fixtures found; this guard would be vacuous"

    job = _ci_job_blocks(_ci_workflow_text()).get("action-contract", "")
    declared = set(re.findall(r"^\s+- fixture: ([\w-]+)$", job, re.MULTILINE))
    assert declared == on_disk, (
        f"fixtures without a contract leg: {sorted(on_disk - declared)}; "
        f"legs without a fixture: {sorted(declared - on_disk)}"
    )
