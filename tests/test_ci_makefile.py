"""The Makefile as the gate ladder's contract.

Moved from ``tests/test_ci_hardening.py`` by ``shape-the-test-suite`` (R-TSS-2): the
one-run shape of ``coverage-run`` / ``test`` / ``coverage-tools`` (measure-coverage-once),
the report targets, and that no make target wires the composite action.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

from tests.support import (
    load_tool,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

@pytest.mark.integration
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

@pytest.mark.integration
def test_makefile_has_matcher_accuracy_report_target() -> None:
    """`make matcher-accuracy` is a report, not a gate: documented, `.PHONY`,
    and composed into neither `ci` nor `pre-pr`. The gate for the same
    numbers is `tests/test_matcher_accuracy.py`, inside `make test`."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^matcher-accuracy:.*?##", makefile, re.MULTILINE), (
        "Makefile has no documented `matcher-accuracy` target"
    )
    # `.PHONY`, and composed into neither aggregate -- now followed through
    # prerequisites transitively -- by the one report-target definition.
    assert _report_target_violations(makefile, "matcher-accuracy") == []

# --- measure-coverage-once: one suite run, two scoped reads ------------------
#
# `make coverage-run` runs the suite once over every tree in
# `[tool.coverage.run] source`; `make test` and `make coverage-tools` depend
# on it and read the one coverage.json under `--scope`. These guards hold
# that shape -- no `--cov=` pin, no floor literal, one pytest line, both
# aggregates on the run -- and hold every CI job that runs the suite to
# uploading its report, which is what the floor ratchet reads (R-MCO-6,
# R-MCO-7, R-MCO-12, R-MCO-13).

#: A rule line: `target: prerequisites ## help`. Variable assignments
#: (`NAME := value`, `NAME:=value`) and `.PHONY` are not rules.
_MAKE_RULE = re.compile(r"^([A-Za-z][\w.-]*):(?![=:])\s*(.*)$")

_COV_SOURCE_PIN = re.compile(r"--cov=\S+")

_COV_FLOOR_LITERAL = re.compile(r"--cov-fail-under=\d+")

_PYTEST_INVOCATION = "python -m pytest"

_SUITE_RUN_TARGET = "coverage-run"

_SUITE_READERS = ("test", "coverage-tools")

_REPORT_TARGET = "coverage-per-file"

_GATE_AGGREGATES = ("ci", "pre-pr")

_COVERAGE_REPORT = "coverage.json"

_CHECKERS = ("check_coverage_floor.py", "check_branch_coverage.py")

def _makefile_text() -> str:
    return (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

def _make_targets(makefile_text: str) -> list[str]:
    """Every rule's target, in file order."""
    targets: list[str] = []
    for line in makefile_text.splitlines():
        match = _MAKE_RULE.match(line)
        if match:
            targets.append(match.group(1))
    return targets

def _prerequisites(makefile_text: str, target: str) -> list[str]:
    """The targets `target` depends on, from its rule line, help text dropped."""
    for line in makefile_text.splitlines():
        match = _MAKE_RULE.match(line)
        if match and match.group(1) == target:
            return match.group(2).split("##", 1)[0].split()
    return []

def _phony_targets(makefile_text: str) -> set[str]:
    """Every target named on a `.PHONY:` line."""
    return {
        name
        for line in makefile_text.splitlines()
        if line.startswith(".PHONY:")
        for name in line.split(":", 1)[1].split()
    }

def _report_targets(makefile_text: str) -> list[str]:
    """Every documented target whose `##` help text begins "Report", in file order."""
    found: list[str] = []
    for line in makefile_text.splitlines():
        match = _MAKE_RULE.match(line)
        help_text = match.group(2).partition("##")[2].strip() if match else ""
        if match and help_text.startswith("Report"):
            found.append(match.group(1))
    return found

def _reachable(makefile_text: str, start: str) -> dict[str, list[str]]:
    """Every target reachable from `start` through prerequisites, followed to a
    fixed point, each with the shortest path that reaches it (`start` first)."""
    paths: dict[str, list[str]] = {}
    frontier = [[start]]
    while frontier:
        path = frontier.pop(0)
        for prerequisite in _prerequisites(makefile_text, path[-1]):
            if prerequisite != start and prerequisite not in paths:
                paths[prerequisite] = [*path, prerequisite]
                frontier.append(paths[prerequisite])
    return paths

def _report_target_violations(makefile_text: str, target: str) -> list[str]:
    """Each way `target` is not a report target, named: no help text beginning
    "Report", missing from `.PHONY`, or reachable from `ci` or `pre-pr` -- the
    last with the path that reaches it (R-RDS-14, DEC-RDS-011)."""
    found: list[str] = []
    if target not in _report_targets(makefile_text):
        found.append(f"{target} is not a report target: its `##` help text does not begin 'Report'")
    if target not in _phony_targets(makefile_text):
        found.append(f"{target} is missing from .PHONY")
    for gate in _GATE_AGGREGATES:
        path = _reachable(makefile_text, gate).get(target)
        if path is not None:
            found.append(f"{gate} composes the {target} report via {' -> '.join(path)}")
    return found

def _recipe_lines(makefile_text: str, target: str) -> list[str]:
    """`target`'s recipe: the tab-indented lines up to the next rule, `@#` and
    `#` comment lines dropped, backslash continuations joined into one line."""
    lines = makefile_text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if (m := _MAKE_RULE.match(ln)) and m.group(1) == target),
        None,
    )
    if start is None:
        return []
    recipe: list[str] = []
    pending = ""
    for line in lines[start + 1 :]:
        if not line.startswith("\t"):
            if line.strip():
                break  # the next rule, variable or comment block
            continue
        body = line[1:].strip()
        if body.startswith(("@#", "#")):
            continue
        if body.endswith("\\"):
            pending += body[:-1].strip() + " "
            continue
        recipe.append((pending + body).strip())
        pending = ""
    return recipe

def _one_run_violations(makefile_text: str) -> list[str]:
    """Every way a Makefile could quietly return to two runs or a pinned floor, named."""
    found: list[str] = []
    pins = sorted(set(_COV_SOURCE_PIN.findall(makefile_text)))
    if pins:
        found.append(f"--cov pins a source instead of reading [tool.coverage.run] source: {pins}")
    literals = sorted(set(_COV_FLOOR_LITERAL.findall(makefile_text)))
    if literals:
        found.append(f"a floor literal on the pytest line: {literals}")
    pytest_lines = [
        (target, line)
        for target in _make_targets(makefile_text)
        for line in _recipe_lines(makefile_text, target)
        if _PYTEST_INVOCATION in line
    ]
    if [target for target, _ in pytest_lines] != [_SUITE_RUN_TARGET]:
        where = [target for target, _ in pytest_lines]
        found.append(
            f"{len(pytest_lines)} pytest lines ({where}); the suite runs once, in {_SUITE_RUN_TARGET}"
        )
    for target in _SUITE_READERS:
        if _SUITE_RUN_TARGET not in _prerequisites(makefile_text, target):
            found.append(f"{target} does not depend on {_SUITE_RUN_TARGET}")
    found += _report_target_violations(makefile_text, _REPORT_TARGET)
    return found

@pytest.mark.integration
def test_the_suite_runs_once_through_coverage_run() -> None:
    """R-MCO-6: `coverage-run` is the one place the suite runs -- in `.PHONY`,
    documented, its recipe the erase and exactly one pytest line carrying a
    bare `--cov` (the trees come from `[tool.coverage.run] source`), the
    disabled total and the JSON report. No other recipe runs pytest."""
    makefile = _makefile_text()
    phony = next(line for line in makefile.splitlines() if line.startswith(".PHONY"))
    assert _SUITE_RUN_TARGET in phony.split(), f"{_SUITE_RUN_TARGET} missing from .PHONY"
    assert re.search(rf"^{_SUITE_RUN_TARGET}:.*?## ", makefile, re.MULTILINE), (
        f"Makefile has no documented `{_SUITE_RUN_TARGET}` target"
    )
    recipe = _recipe_lines(makefile, _SUITE_RUN_TARGET)
    assert len(recipe) == 2 and recipe[0] == "python -m coverage erase", recipe
    tokens = recipe[1].split()
    assert tokens[:4] == ["python", "-m", "pytest", "tests/"], recipe[1]
    for required in (
        "--cov",
        "--cov-branch",
        "--cov-fail-under=$(NO_FLOOR)",
        f"--cov-report=json:{_COVERAGE_REPORT}",
    ):
        assert required in tokens, f"{required!r} missing from {recipe[1]!r}"
    assert "--cov=" not in makefile, "a `--cov=` pin bypasses [tool.coverage.run] source"
    assert _one_run_violations(makefile) == []

@pytest.mark.integration
def test_test_and_coverage_tools_read_the_one_report_scoped() -> None:
    """R-MCO-6: both aggregates depend on the run and read its one report
    scoped -- `test` for every declared tree, `coverage-tools` for `tools/`
    alone -- through the same two checkers; `pre-pr` still composes
    `coverage-tools` and `ci` is unchanged."""
    makefile = _makefile_text()
    common = load_tool("common_mco_sources", "_common.py")
    sources = common.coverage_sources(REPO_ROOT / "pyproject.toml")
    assert len(sources) >= 2, f"one run over {sources}: nothing to read scoped"
    for target in _SUITE_READERS:
        assert _SUITE_RUN_TARGET in _prerequisites(makefile, target), (
            f"{target} must depend on {_SUITE_RUN_TARGET}"
        )
    expected_test = {
        f"python tools/{script} {_COVERAGE_REPORT} --scope {scope}"
        for scope in sources
        for script in _CHECKERS
    }
    assert set(_recipe_lines(makefile, "test")) == expected_test
    expected_tools = {line for line in expected_test if line.endswith("--scope tools")}
    assert set(_recipe_lines(makefile, "coverage-tools")) == expected_tools
    assert "coverage-tools" in _prerequisites(makefile, "pre-pr")
    assert _prerequisites(makefile, "ci") == ["test", "lint", "validate"]

_ONE_RUN_MAKEFILE = textwrap.dedent(
    """\
    .PHONY: coverage-run test coverage-tools coverage-per-file ci pre-pr
    NO_FLOOR := 0
    coverage-run: ## the one run
    \tpython -m coverage erase
    \tpython -m pytest tests/ --cov --cov-branch --cov-fail-under=$(NO_FLOOR) \\
    \t\t--cov-report=json:coverage.json -q
    test: coverage-run ## both trees
    \tpython tools/check_coverage_floor.py coverage.json --scope openspec_graph
    coverage-tools: coverage-run ## tools alone
    \tpython tools/check_coverage_floor.py coverage.json --scope tools
    coverage-per-file: coverage-run ## Report the per-file minimum
    \tpython tools/check_coverage_floor.py coverage.json --per-file-min
    ci: test lint validate ## core
    \t@echo ci
    pre-pr: ci coverage-tools ## full
    \t@echo pre-pr
    """
)

@pytest.mark.unit
@pytest.mark.parametrize(
    ("label", "before", "after", "expected"),
    [
        ("a pinned source", "--cov ", "--cov=openspec_graph ", "--cov pins a source"),
        ("a floor literal", "--cov-fail-under=$(NO_FLOOR)", "--cov-fail-under=90", "floor literal"),
        (
            "two pytest lines",
            "\tpython -m coverage erase\n",
            "\tpython -m coverage erase\n\tpython -m pytest tests/ -q\n",
            "2 pytest lines",
        ),
        ("test off the run", "test: coverage-run", "test:", "test does not depend"),
        (
            "coverage-tools off the run",
            "coverage-tools: coverage-run",
            "coverage-tools:",
            "coverage-tools does not depend",
        ),
        (
            "pre-pr composing the report",
            "pre-pr: ci coverage-tools",
            "pre-pr: ci coverage-tools coverage-per-file",
            "pre-pr composes",
        ),
    ],
)
def test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named(
    label: str, before: str, after: str, expected: str
) -> None:
    """R-MCO-13: each way back to two runs or a pinned floor is named on a
    planted Makefile whose unmutated form is clean."""
    assert _one_run_violations(_ONE_RUN_MAKEFILE) == [], "the planted baseline must be clean"
    assert _ONE_RUN_MAKEFILE.count(before) == 1, f"{label}: anchor {before!r} not unique"
    found = _one_run_violations(_ONE_RUN_MAKEFILE.replace(before, after))
    assert any(expected in item for item in found), f"{label}: {found}"

@pytest.mark.integration
def test_makefile_has_coverage_per_file_report_target() -> None:
    """`make coverage-per-file` is a report, not a gate (DEC-MCO-009): documented,
    `.PHONY`, depending on the run and not on `test` so it can be read while a
    floor is red, and composed into neither `ci` nor `pre-pr`."""
    makefile = _makefile_text()
    assert re.search(rf"^{_REPORT_TARGET}:.*?## ", makefile, re.MULTILINE), (
        f"Makefile has no documented `{_REPORT_TARGET}` target"
    )
    assert _prerequisites(makefile, _REPORT_TARGET) == [_SUITE_RUN_TARGET]
    assert _recipe_lines(makefile, _REPORT_TARGET) == [
        f"python tools/check_coverage_floor.py {_COVERAGE_REPORT} --per-file-min"
    ]
    # `.PHONY`, and composed into neither aggregate -- now followed through
    # prerequisites transitively -- by the one report-target definition.
    assert _report_target_violations(makefile, _REPORT_TARGET) == []

# --- report-dead-code-and-spec-status: one definition of a report target -----
#
# A report target is documented with help text beginning "Report", is in
# `.PHONY`, and is reachable from neither `ci` nor `pre-pr` through
# prerequisites followed transitively -- so a report composed into `test`
# cannot slip into the ladder unseen (R-RDS-14, DEC-RDS-011).

#: The report targets this repository must carry; each is required by name so
#: the test is red before the target exists.
_REQUIRED_REPORT_TARGETS = ("matcher-accuracy", "coverage-per-file", "stage-citations")

@pytest.mark.integration
def test_every_report_target_stays_out_of_the_ladder() -> None:
    """R-RDS-14: every target whose help text begins "Report" is `.PHONY` and
    unreachable from `ci` and `pre-pr`, and the required ones are among them."""
    makefile = _makefile_text()
    reports = _report_targets(makefile)
    missing = [f"{name} is not a report target" for name in _REQUIRED_REPORT_TARGETS
               if name not in reports]
    assert missing == []
    violations = [item for name in reports for item in _report_target_violations(makefile, name)]
    assert violations == []

_PLANTED_REPORT_MAKEFILE = textwrap.dedent(
    """\
    .PHONY: test lint audit ci pre-pr
    test: ## Run the suite
    \tpython -m pytest tests/
    lint: ## Lint
    \tpython -m ruff check .
    audit: ## Report the audited things — a report, not a gate
    \tpython tools/audit.py
    ci: test lint ## core
    \t@echo ci
    pre-pr: ci ## full
    \t@echo pre-pr
    """
)

@pytest.mark.unit
@pytest.mark.parametrize(
    ("label", "before", "after", "expected"),
    [
        (
            "pre-pr composing the report directly",
            "pre-pr: ci ##",
            "pre-pr: ci audit ##",
            ["pre-pr composes the audit report via pre-pr -> audit"],
        ),
        (
            "ci composing it through an intermediate target",
            "test: ##",
            "test: audit ##",
            [
                "ci composes the audit report via ci -> test -> audit",
                "pre-pr composes the audit report via pre-pr -> ci -> test -> audit",
            ],
        ),
        (
            "missing from .PHONY",
            ".PHONY: test lint audit ci pre-pr",
            ".PHONY: test lint ci pre-pr",
            ["audit is missing from .PHONY"],
        ),
        (
            "help text not beginning Report",
            "## Report the audited things",
            "## the audited things",
            ["audit is not a report target: its `##` help text does not begin 'Report'"],
        ),
    ],
)
def test_a_report_target_composed_into_the_ladder_is_named(
    label: str, before: str, after: str, expected: list[str]
) -> None:
    """R-RDS-14, R-RDS-19: each way a report target slips into the ladder, or
    stops being a report, is named with the target and, where it is reached,
    the path -- on a planted Makefile whose unmutated form is clean."""
    assert _report_target_violations(_PLANTED_REPORT_MAKEFILE, "audit") == []
    assert _PLANTED_REPORT_MAKEFILE.count(before) == 1, f"{label}: anchor {before!r} not unique"
    mutated = _PLANTED_REPORT_MAKEFILE.replace(before, after)
    assert _report_target_violations(mutated, "audit") == expected, label

@pytest.mark.integration
def test_the_contract_job_is_not_wired_into_a_make_target() -> None:
    """It needs a runner, so it stays CI-side: folding it into `make pre-pr`
    would make the local gate unrunnable rather than more thorough."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "action-contract" not in makefile
