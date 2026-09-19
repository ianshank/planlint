"""Tests for the CI hardening tooling (change package: harden-ci-gates).

Covers the four implemented behaviors:
- branch-coverage floor (AC-CH-3) via tools/check_branch_coverage.py
- coverage line floor fails below threshold (AC-CH-1, AC-CH-2)
- graph-diff fails on regressions and passes on improvements (AC-CH-5, AC-CH-6)
- rule set matches the committed baseline (AC-CH-8 / C-CH-1: no new rules)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

from openspec_graph import detect
from openspec_graph import graph as graph_module
from openspec_graph.rules import RULES, rule_table
from tests.support import env_without_coverage, load_tool, run_tool_main
from tests.support import write_spec as _write_spec

TOOLS = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent


# --- AC-CH-3: branch-coverage floor ------------------------------------------


def _write_coverage_json(path: Path, branches: int, covered: int) -> Path:
    path.write_text(
        json.dumps({"totals": {"num_branches": branches, "covered_branches": covered}})
    )
    return path


def _write_pyproject(path: Path, floor: int | None) -> Path:
    if floor is None:
        path.write_text("[tool.coverage.report]\nfail_under = 90\n")
    else:
        path.write_text(
            "[tool.coverage.report]\nfail_under = 90\n"
            f"[tool.specgraph]\nbranch_fail_under = {floor}\n"
        )
    return path


def test_branch_check_fails_below_floor(tmp_path: Path, capsys) -> None:
    _write_coverage_json(tmp_path / "coverage.json", branches=10, covered=5)  # 50%
    _write_pyproject(tmp_path / "pyproject.toml", floor=80)
    rc = _run_branch_check(tmp_path)
    out = capsys.readouterr().out
    assert rc == 1
    assert "50.0%" in out
    assert "below floor 80" in out


def test_branch_check_passes_at_or_above_floor(tmp_path: Path, capsys) -> None:
    _write_coverage_json(tmp_path / "coverage.json", branches=10, covered=8)  # 80%
    _write_pyproject(tmp_path / "pyproject.toml", floor=80)
    assert _run_branch_check(tmp_path) == 0
    assert "80.0%" in capsys.readouterr().out


def test_branch_check_fails_when_no_branches_measured(tmp_path: Path) -> None:
    # branch=true is configured but zero branches were measured -> misconfiguration,
    # not a silent pass. The gate fails loud (AC-CH-3: a missing gate is a bug).
    _write_coverage_json(tmp_path / "coverage.json", branches=0, covered=0)
    _write_pyproject(tmp_path / "pyproject.toml", floor=80)
    assert _run_branch_check(tmp_path) == 2


def test_branch_check_fails_when_floor_not_configured(tmp_path: Path) -> None:
    # A repo that turns this gate on MUST set branch_fail_under. Missing it is a
    # misconfiguration, not a skip — CI must not pass silently.
    _write_coverage_json(tmp_path / "coverage.json", branches=10, covered=1)
    _write_pyproject(tmp_path / "pyproject.toml", floor=None)
    assert _run_branch_check(tmp_path) == 2


def _run_branch_check(cwd: Path) -> int:
    return run_tool_main(
        "check_branch_coverage", "check_branch_coverage.py", "coverage.json", cwd=cwd
    )


# --- AC-CH-1 / AC-CH-2: the line-coverage floor (read from pyproject) ---------


def _run_cov_floor_check(cwd: Path) -> int:
    return run_tool_main(
        "check_coverage_floor", "check_coverage_floor.py", "coverage.json", cwd=cwd
    )


def _write_cov_lines(path: Path, statements: int, covered: int) -> Path:
    path.write_text(
        json.dumps({"totals": {"num_statements": statements, "covered_lines": covered}})
    )
    return path


def test_cov_floor_fails_below_threshold(tmp_path: Path) -> None:
    # 50% line coverage against a floor of 90 read from pyproject.
    _write_cov_lines(tmp_path / "coverage.json", statements=100, covered=50)
    _write_pyproject(tmp_path / "pyproject.toml", floor=80)  # sets fail_under=90
    assert _run_cov_floor_check(tmp_path) == 1


def test_cov_floor_passes_at_or_above(tmp_path: Path) -> None:
    _write_cov_lines(tmp_path / "coverage.json", statements=100, covered=92)
    _write_pyproject(tmp_path / "pyproject.toml", floor=80)
    assert _run_cov_floor_check(tmp_path) == 0


def test_cov_floor_fails_loud_when_floor_not_configured(tmp_path: Path) -> None:
    # fail_under missing from pyproject -> misconfiguration, not a skip.
    _write_cov_lines(tmp_path / "coverage.json", statements=100, covered=50)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
    assert _run_cov_floor_check(tmp_path) == 2


def test_cov_floor_threshold_is_read_from_pyproject_not_hardcoded(tmp_path: Path) -> None:
    # The floor is whatever pyproject declares — 95 here, not the repo's 90.
    _write_cov_lines(tmp_path / "coverage.json", statements=100, covered=92)  # 92% < 95
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.report]\nfail_under = 95\n[tool.specgraph]\nbranch_fail_under = 80\n"
    )
    assert _run_cov_floor_check(tmp_path) == 1


def test_coverage_floor_fails_below_threshold_pytest(tmp_path: Path) -> None:
    """A package with uncovered lines fails the --cov-fail-under gate."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "mod.py").write_text("def half(a):\n    if a:\n        return 1\n    return 2\n")
    (pkg / "test_mod.py").write_text("from mod import half\ndef test_half():\n    assert half(True) == 1\n")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts='-q'\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(pkg / "test_mod.py"),
         "--cov=mod", "--cov-fail-under=100", "-q"],
        cwd=pkg.parent, capture_output=True, text=True, check=False,
        # Its own coverage session, not this repo's -- see env_without_coverage.
        env=env_without_coverage(PYTHONPATH=str(pkg)),
    )
    assert result.returncode != 0, "below-floor coverage must fail the gate"


def test_coverage_floor_passes_at_threshold(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "mod.py").write_text("def add(a, b):\n    return a + b\n")
    (pkg / "test_mod.py").write_text("from mod import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(pkg / "test_mod.py"),
         "--cov=mod", "--cov-fail-under=90", "-q"],
        cwd=pkg.parent, capture_output=True, text=True, check=False,
        env=env_without_coverage(PYTHONPATH=str(pkg)),
    )
    assert result.returncode == 0


def test_suite_survives_an_ambient_coverage_file(tmp_path: Path) -> None:
    """An inherited ``COVERAGE_FILE`` must not crash the run at teardown.

    Naming a per-leg coverage data file is the standard way to keep a build
    matrix's coverage separate, and nothing in this repository sets the
    variable, so the trap is entirely ambient. Before ``env_without_coverage``
    the two nested ``pytest --cov`` tests above inherited it and wrote
    statement-only data into this run's data file; with ``parallel = true`` the
    outer run combines every sibling at teardown and raises ``DataError:
    Can't combine branch coverage data with statement data`` from inside
    pytest's own teardown hook. That is INTERNALERROR and exit 3 -- the entire
    suite lost, no test marked red, which is why an ordinary test of those two
    functions could never have caught it.

    Runs them in a nested pytest under the conditions that spring the trap
    (``COVERAGE_FILE`` set, ``--cov-branch`` on the parent) and asserts the
    outcome is a real verdict rather than a crash.
    """
    data_file = tmp_path / "ambient.coverage"
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         str(REPO_ROOT / "tests" / "test_ci_hardening.py"),
         "-k", "coverage_floor_passes_at_threshold",
         # --cov-branch is half the trap: it makes the OUTER data branch-typed,
         # so the nested statement-only data cannot combine with it. The
         # explicit fail-under=0 overrides pyproject's 90 for this nested run
         # only -- it measures `tools` while running one test that touches
         # none of it, so the real floor would fail it at 0% for reasons that
         # have nothing to do with the crash under test, and exit 0 would stop
         # meaning anything.
         "--cov=tools", "--cov-branch", "--cov-fail-under=0",
         "-p", "no:cacheprovider", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        env=env_without_coverage(COVERAGE_FILE=str(data_file)),
    )
    combined = result.stdout + result.stderr
    assert "INTERNALERROR" not in combined, combined[-3000:]
    # Exit 3 is pytest's internal-error code, and it is the whole subject here.
    assert result.returncode != 3, f"INTERNALERROR at teardown:\n{combined[-3000:]}"
    assert result.returncode == 0, combined[-3000:]


def test_env_without_coverage_strips_every_coverage_variable() -> None:
    """The helper removes the whole family and applies overrides on top."""
    from tests.support import COVERAGE_ENV_VARS

    planted = dict.fromkeys(COVERAGE_ENV_VARS, "planted")
    with mock.patch.dict(os.environ, planted):
        env = env_without_coverage(PYTHONPATH="/somewhere")
    assert not [name for name in COVERAGE_ENV_VARS if name in env]
    assert env["PYTHONPATH"] == "/somewhere"
    # Not a whitelist: everything unrelated survives.
    assert "PATH" in env


# --- AC-CH-5 / AC-CH-6: graph-diff fails on regressions, passes on fixes ----


MAKEFILE = textwrap.dedent(
    """\
    .PHONY: test
    test:
    \tpytest
    """
)
PYPROJECT = textwrap.dedent(
    """\
    [project]
    name = "demo"
    [tool.coverage.report]
    fail_under = 90
    """
)
GOOD_HARNESS = textwrap.dedent(
    """\
    # Spec: Demo

    > **Status:** DRAFT

    ## Problem Statement

    **Evidence:** `mod.py::run` does X.

    ## Requirements

    - R-DMO-1: The system MUST do a thing.

    ## Acceptance Criteria

    - [ ] **AC-DMO-1:** The thing is done. (R-DMO-1)
      _Verified by:_ `pytest -k test_thing` · stage: `make test`

    - [ ] **AC-DMO-2 (non-success):** The thing is refused when invalid. (R-DMO-1)
      _Verified by:_ `pytest -k test_refused` · stage: `make test`

    ## Validation Matrix

    | Stage | Make Target | Pass Criteria |
    |---|---|---|
    | Focused | `make test` | AC-DMO-1..2 |
    """
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    return tmp_path


def _graph_json(repo: Path) -> dict:
    return graph_module.build_graph(detect.profile(repo))


def _diff(base: dict, head: dict) -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        bp = Path(d) / "base.json"
        hp = Path(d) / "head.json"
        bp.write_text(json.dumps(base))
        hp.write_text(json.dumps(head))
        # Absolute paths, so no cwd is needed -- unlike the two coverage gates,
        # this script reads nothing relative to where it was started.
        return run_tool_main("diff_spec_graph", "diff_spec_graph.py", str(bp), str(hp))


def test_graph_diff_passes_when_clean(repo: Path) -> None:
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    head = json.loads(json.dumps(base))
    assert _diff(base, head) == 0


def test_graph_diff_fails_on_new_broken_edges(repo: Path) -> None:
    # base: clean spec
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    # head: same spec but the AC cites a stage the repo lacks -> broken edge
    bad = GOOD_HARNESS.replace("make test", "make nope")
    _write_spec(repo, "c1", "cap1", bad)
    head = _graph_json(repo)
    assert head["broken_links"] > base["broken_links"]
    assert _diff(base, head) == 1


def test_graph_diff_fails_on_new_orphan(repo: Path) -> None:
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    # head: add an orphan requirement nothing verifies
    orphan_body = GOOD_HARNESS.replace(
        "- R-DMO-1: The system MUST do a thing.",
        "- R-DMO-1: The system MUST do a thing.\n- R-DMO-9: MUST do an untested thing.",
    )
    _write_spec(repo, "c1", "cap1", orphan_body)
    head = _graph_json(repo)
    assert "R-DMO-9" in {n["id"] for n in head["nodes"] if n.get("orphan")}
    assert _diff(base, head) == 1


def test_graph_diff_passes_when_orphan_fixed(repo: Path) -> None:
    # base has an orphan; head fixes it by adding a criterion that traces to it
    orphan_body = GOOD_HARNESS.replace(
        "- R-DMO-1: The system MUST do a thing.",
        "- R-DMO-1: The system MUST do a thing.\n- R-DMO-9: MUST do an untested thing.",
    )
    _write_spec(repo, "c1", "cap1", orphan_body)
    base = _graph_json(repo)
    assert "R-DMO-9" in {n["id"] for n in base["nodes"] if n.get("orphan")}

    fixed = orphan_body.replace(
        "- [ ] **AC-DMO-2 (non-success):** The thing is refused when invalid. (R-DMO-1)",
        "- [ ] **AC-DMO-2 (non-success):** The thing is refused when invalid. (R-DMO-1)\n- [ ] **AC-DMO-3:** The untested thing is now tested. (R-DMO-9)\n  _Verified by:_ `pytest -k test_now` · stage: `make test`",
    )
    _write_spec(repo, "c1", "cap1", fixed)
    head = _graph_json(repo)
    assert "R-DMO-9" not in {n["id"] for n in head["nodes"] if n.get("orphan")}
    assert _diff(base, head) == 0  # fixing an orphan is an improvement, not a regression


def test_graph_diff_rejects_bad_args() -> None:
    assert run_tool_main("diff_spec_graph", "diff_spec_graph.py", "only-one-arg") == 2


# --- render_mermaid.py: thin consumer of a saved graph.json (CP-GV) ---------


def test_render_mermaid_matches_to_mermaid_byte_for_byte(repo: Path, tmp_path: Path, capsys) -> None:
    from openspec_graph.mermaid import to_mermaid

    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    graph = _graph_json(repo)
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph))

    assert run_tool_main("render_mermaid", "render_mermaid.py", str(graph_path)) == 0
    # `print(..., end="")`, so stdout is the rendering with nothing appended.
    assert capsys.readouterr().out == to_mermaid(graph)


def test_render_mermaid_rejects_bad_args() -> None:
    assert run_tool_main("render_mermaid", "render_mermaid.py") == 2


# --- the executable contract, once rather than per script --------------------


@pytest.mark.parametrize(
    "script",
    [
        "check_branch_coverage.py",
        "check_coverage_floor.py",
        "diff_spec_graph.py",
        "render_mermaid.py",
        "check_docs.py",
        "check_no_hardcoded_thresholds.py",
        "check_secrets.py",
        "check_wheel_metadata.py",
        "matcher_accuracy.py",
        "render_plugin_manifests.py",
        "render_rule_catalog.py",
    ],
)
def test_gate_script_is_runnable_as_a_script(script: str, tmp_path: Path) -> None:
    """``python tools/<script>.py`` starts and returns an exit code.

    Every behaviour of these scripts is asserted in-process, against
    ``main(argv)``, because a subprocess's execution is invisible to coverage
    (see ``run_tool_main``). That leaves exactly one thing in-process testing
    cannot see: whether the file still *runs* as a script -- an import that
    only resolves because pytest put the repo root on ``sys.path``, a
    ``sys.path`` bootstrap line deleted as dead code, a syntax error under the
    ``if __name__ == "__main__"`` guard. The Makefile and the workflows invoke
    every one of these this way, so that path is a real contract.

    Asserted here once for the whole directory rather than once per script, so
    a new gate script is covered by adding one line. Run from a throwaway cwd
    with no arguments: what matters is that the interpreter got far enough to
    reach the script's own argument handling, not which verdict it reached.
    """
    result = subprocess.run(
        [sys.executable, str(TOOLS / script)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
        env=env_without_coverage(),
    )
    # Checked by marker rather than by exit code alone, because the two ways a
    # script fails to load do not agree on either signal. A failed import
    # raises and prints "Traceback (most recent call last)"; a SyntaxError is
    # reported by the compiler in a different format with no such line -- and
    # both exit 1, which is a documented code here (a gate that found a
    # violation). Exit code alone therefore cannot tell "the gate ran and
    # failed the repo" from "the file is not loadable at all".
    for marker in ("Traceback (most recent call last)", "SyntaxError",
                   "ModuleNotFoundError", "ImportError", "IndentationError"):
        assert marker not in result.stderr, f"{script}: {marker}\n{result.stderr}"
    # 0/1/2 are the documented codes. Anything else (a negative code for a
    # fatal signal, or an unhandled SystemExit payload) says the script did
    # not reach its own exit path.
    assert result.returncode in (0, 1, 2), (
        f"{script} exited {result.returncode}\n{result.stdout}\n{result.stderr}"
    )


# --- AC-CH-8 / C-CH-1: the rule set matches the committed baseline -----------
# A future change that adds or removes a rule without updating the baseline
# fails this test — forcing the change to be a conscious decision (C-CH-1).


def test_rule_set_matches_baseline() -> None:
    baseline_path = REPO_ROOT / "tests" / "baseline_rules.json"
    assert baseline_path.exists(), "baseline_rules.json must be committed"
    baseline = json.loads(baseline_path.read_text())
    live = rule_table()
    assert live == baseline, (
        "the rule set changed; if this is intentional, regenerate "
        "tests/baseline_rules.json with `planlint rules --json > tests/baseline_rules.json`"
    )
    # sanity: the baseline is non-empty and covers the rules we rely on
    assert len(baseline) == len(RULES)


# --- AC-CH-4 / AC-CH-7: claims about the CI configuration itself -------------
# Both acceptance criteria describe properties of the committed workflow and
# Makefile rather than of any Python function, and both cited tests that were
# never written -- found by tests/test_spec_test_citations.py, the guard that
# now holds every `_Verified by:` citation to a test that exists. Asserted
# against the real files so the criteria stop being prose.


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


def _ci_job_blocks(text: str) -> dict[str, str]:
    """Job name -> body, line-scanned out of the workflow's `jobs:` mapping.

    Structural, not substring matching (DEC-AQA-005): PyYAML is deliberately
    not a dependency (zero-runtime-deps contract), and `jobs:` keys sit at a
    fixed two-space indent, so a line scan is exact -- a cosmetic reformat
    can't false-fail and a renamed job can't false-pass.
    """
    lines = text.splitlines()
    try:
        start = lines.index("jobs:") + 1
    except ValueError:
        return {}
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break  # left the top-level mapping
        match = re.match(r"^  ([A-Za-z][\w-]*):\s*$", line)
        if match:
            current = match.group(1)
            blocks[current] = []
        elif current is not None:
            blocks[current].append(line)
    return {name: "\n".join(body) for name, body in blocks.items()}


def test_ci_job_blocks_returns_empty_when_jobs_key_is_absent() -> None:
    # The guard tests above must fail on a real missing job, not on a parser
    # that silently found nothing.
    assert _ci_job_blocks("name: CI\non: push\n") == {}


def test_ci_job_blocks_ignores_comments_mentioning_jobs() -> None:
    text = "jobs:\n  test:\n    # see the other jobs: for context\n    runs-on: ubuntu-latest\n"
    assert set(_ci_job_blocks(text)) == {"test"}


def test_makefile_has_e2e_live_target() -> None:
    """AC-AQA-1: the no-mocks live track is one local command, not a recipe
    contributors must copy out of the CI YAML."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^e2e-live:.*?##", makefile, re.MULTILINE), (
        "Makefile has no documented `e2e-live` target"
    )
    phony = next(line for line in makefile.splitlines() if line.startswith(".PHONY"))
    assert "e2e-live" in phony.split(), "e2e-live missing from .PHONY"
    assert "PYTHONIOENCODING=ascii" in makefile, (
        "e2e-live must include one pass under the ASCII-only console that "
        "reproduces the fix-stdout-encoding-crash environment"
    )

    # AC-AQA-7: the pre-PR gate's composition is unchanged -- the live track
    # is additive (its own target and CI jobs), never folded into pre-pr.
    pre_pr = next(
        line for line in makefile.splitlines() if re.match(r"^pre-pr:", line)
    )
    assert "e2e-live" not in pre_pr, "e2e-live must not become part of `make pre-pr`"


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


def test_ci_workflow_has_an_encoding_stress_job() -> None:
    """AC-AQA-3: the encoding crash's original failure environment is itself
    a gate, so a regression can't ship silently the way the original did."""
    blocks = _ci_job_blocks(_ci_workflow_text())
    stressed = {name: body for name, body in blocks.items() if "PYTHONIOENCODING" in body}
    assert stressed, "ci.yml has no job running under an ASCII-only console"
    assert "make e2e-live" in next(iter(stressed.values())), (
        "the encoding-stress job must run the live track (`make e2e-live`)"
    )


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


def test_makefile_has_matcher_accuracy_report_target() -> None:
    """`make matcher-accuracy` is a report, not a gate: documented, `.PHONY`,
    and composed into neither `ci` nor `pre-pr`. The gate for the same
    numbers is `tests/test_matcher_accuracy.py`, inside `make test`."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^matcher-accuracy:.*?##", makefile, re.MULTILINE), (
        "Makefile has no documented `matcher-accuracy` target"
    )
    phony = next(line for line in makefile.splitlines() if line.startswith(".PHONY"))
    assert "matcher-accuracy" in phony.split(), "matcher-accuracy missing from .PHONY"
    for gate in ("ci", "pre-pr"):
        line = next(ln for ln in makefile.splitlines() if ln.startswith(f"{gate}:"))
        assert "matcher-accuracy" not in line.split(), f"{gate} must not compose the report target"



# --- add-github-action-contract: the composite action is actually executed ----


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


def test_the_contract_job_is_not_wired_into_a_make_target() -> None:
    """It needs a runner, so it stays CI-side: folding it into `make pre-pr`
    would make the local gate unrunnable rather than more thorough."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "action-contract" not in makefile


# --- Dependabot: every action-bearing directory must actually be watched -----


DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"


def _dependabot_directories() -> set[str]:
    """The `directory:` values declared in dependabot.yml, as text.

    Parsed with `re` rather than PyYAML for the same reason every other config
    assertion here is: the package declares zero dependencies and the test
    suite does not get to import one the product cannot.
    """
    text = DEPENDABOT.read_text(encoding="utf-8")
    return set(re.findall(r'^\s*directory:\s*"([^"]+)"', text, re.MULTILINE))


def test_dependabot_config_exists_and_watches_github_actions() -> None:
    assert DEPENDABOT.is_file(), "no .github/dependabot.yml; action pins would go stale silently"
    text = DEPENDABOT.read_text(encoding="utf-8")
    assert 'package-ecosystem: "github-actions"' in text


def test_every_composite_action_directory_is_watched_by_dependabot() -> None:
    """A nested composite action is invisible to the root entry.

    Dependabot's github-actions ecosystem discovers workflow files under the
    `/` entry, but an `action.yml` in a subdirectory needs that subdirectory
    declared explicitly. Adding a second composite action without a matching
    entry would leave its pins unwatched, and nothing else in this suite would
    notice -- which is exactly how the floating tags this config exists to
    manage got there in the first place.
    """
    watched = _dependabot_directories()
    assert "/" in watched, watched

    for action_yml in sorted((REPO_ROOT / ".github" / "actions").glob("*/action.yml")):
        rel = "/" + str(action_yml.parent.relative_to(REPO_ROOT)).replace("\\", "/")
        assert rel in watched, (
            f"{rel} holds a composite action but is not a dependabot `directory:` entry; "
            f"its third-party pins would never be updated. Watched: {sorted(watched)}"
        )


def test_dependabot_does_not_add_a_pip_ecosystem() -> None:
    """Non-success: the dev extras are unpinned on purpose.

    `[project] dependencies` is empty and guarded, and
    `tools/check_no_hardcoded_thresholds.py` fails the build on a reintroduced
    `ruff==`/`mypy==`/`pytest==` pin. A pip ecosystem entry would open pull
    requests arguing with that decision every release, so its absence is a
    decision worth pinning rather than an omission.
    """
    text = DEPENDABOT.read_text(encoding="utf-8")
    assert 'package-ecosystem: "pip"' not in text


# --- the threshold guard's own coverage, which was close to inverted --------


@pytest.mark.parametrize(
    "line",
    [
        "python -m pytest --cov-fail-under=90",
        "\t@pytest --cov-fail-under=90",            # was ALLOWED by the `@\w` veto
        "\t$(PY) -m pytest --cov-fail-under=90",    # was ALLOWED by the `$(` veto
        "\tmake-believe --floor 85",                # was ALLOWED: `\bmake\b` at the hyphen
        "\t@ruff check --line-length 100",
    ],
)
def test_threshold_guard_flags_numbers_in_ordinary_recipe_idioms(line: str) -> None:
    """`@`-prefixed and `$(VAR)`-using recipes are the dominant Makefile idiom.

    The allowances used to be whole-line vetoes, so any line containing them
    escaped the scan entirely — the guard enforcing this project's flagship
    rule on itself covered close to the inverse of what it claimed. They are
    token exclusions now: the `$(...)` span and a leading `@` are removed and
    whatever remains is scanned.
    """
    module = load_tool("check_no_hardcoded_thresholds", "check_no_hardcoded_thresholds.py")
    assert not module._is_allowed(line), "only a comment is a whole-line exemption"
    assert list(module._THRESHOLD_TOKEN.finditer(module.scannable(line))), line


@pytest.mark.parametrize(
    "line",
    [
        "# a comment mentioning 90",
        "\t$(PY) tools/check_coverage_floor.py coverage.json",
        "\tpython -m pytest tests/",
    ],
)
def test_threshold_guard_stays_quiet_on_legitimate_lines(line: str) -> None:
    """Non-success: strengthening the scan must not start failing clean recipes.

    A `$(...)` span is genuinely not a literal — its value comes from
    elsewhere — so stripping it rather than vetoing the line keeps the real
    Makefile green, which `make thresholds` confirms end to end.
    """
    module = load_tool("check_no_hardcoded_thresholds", "check_no_hardcoded_thresholds.py")
    if module._is_allowed(line):
        return
    assert not list(module._THRESHOLD_TOKEN.finditer(module.scannable(line))), line


def test_tools_and_package_agree_on_the_makefile_search_order() -> None:
    """The one duplication `tools/` is allowed, pinned so it cannot drift.

    `tools/` is stdlib-only and runs before the package is installed, so it
    cannot import `openspec_graph.detect.MAKEFILE_NAMES` — the gates would
    then depend on the thing they gate. The copy is therefore deliberate, and
    this is what makes a divergence a failure instead of the silent
    single-name lookup that existed in both places at once.
    """
    from openspec_graph import detect as package_detect

    common = load_tool("_common", "_common.py")
    assert common.MAKEFILE_NAMES == package_detect.MAKEFILE_NAMES


def test_threshold_guard_finds_a_makefile_under_every_honoured_name(tmp_path: Path) -> None:
    """Same single-name bug this branch fixed in detect.py, in the guard itself.

    A repo using `GNUmakefile` got a silent PASS: the missing `Makefile` path
    returned [], and the basename dispatch would have routed it to the
    workflow checker anyway.
    """
    common = load_tool("_common", "_common.py")
    # One numbered directory per name, never a directory NAMED after the file:
    # `makefile/` and `Makefile/` are the same path on a case-insensitive
    # filesystem, so the second mkdir raised FileExistsError on the Windows CI
    # leg. A test about case-insensitivity that is itself case-unsafe.
    for index, name in enumerate(common.MAKEFILE_NAMES):
        root = tmp_path / f"case-{index}"
        root.mkdir()
        (root / name).write_text("build:\n\t@echo b\n", encoding="utf-8")
        assert common.resolve_makefile(root) == root / name, name
    assert common.resolve_makefile(tmp_path / "empty") is None


def test_threshold_guard_reports_the_on_disk_makefile_spelling(tmp_path: Path) -> None:
    """Resolution must not leak the candidate's spelling.

    Probing `(root / "makefile").is_file()` succeeds against a file written
    `Makefile` on a case-insensitive filesystem, and the returned path then
    carries the wrong name — which a caller reports on. Matching the directory
    listing returns the real one. This passes trivially on a case-sensitive
    filesystem and is the actual assertion on Windows and macOS.
    """
    common = load_tool("_common", "_common.py")
    (tmp_path / "Makefile").write_text("build:\n\t@echo b\n", encoding="utf-8")
    resolved = common.resolve_makefile(tmp_path)
    assert resolved is not None and resolved.name == "Makefile", resolved


def test_threshold_guard_stops_at_an_unreadable_higher_precedence_candidate(
    tmp_path: Path,
) -> None:
    """Non-success: presence ends the search, not readability.

    `make` stops at the first name that EXISTS even if it cannot open it, so a
    directory named `GNUmakefile` must not let a lower-precedence `Makefile`
    be scanned — reporting on a file `make` would never read. This keeps the
    tool consistent with `detect._resolve_makefile`, which is terminal for the
    same reason.
    """
    common = load_tool("_common", "_common.py")
    nht = load_tool("check_no_hardcoded_thresholds", "check_no_hardcoded_thresholds.py")
    (tmp_path / "GNUmakefile").mkdir()
    (tmp_path / "Makefile").write_text("\t@pytest --cov-fail-under=90\n", encoding="utf-8")

    resolved = common.resolve_makefile(tmp_path)
    assert resolved is not None and resolved.name == "GNUmakefile", resolved
    # And scanning it yields nothing rather than raising or falling through.
    assert nht.check_makefile(resolved) == []
