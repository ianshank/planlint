"""The two coverage checkers under ``tools/``, in-process and as scripts.

Moved from ``tests/test_ci_hardening.py`` and ``tests/test_gate_scripts.py`` by
``shape-the-test-suite`` (R-TSS-2): the line and branch floors, the scoped reads of one
report, the per-file report, and the ambient-coverage-file survival run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from tests.support import (
    env_without_coverage,
    load_tool,
    run_tool_main,
)

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
         str(REPO_ROOT / "tests" / Path(__file__).name),  # this module: the floor test now lives here
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


# --- scoped coverage floors: the gate that guards the gate scripts ----------
#
# `make test` gates both trees from one report through the same two checkers
# under `--scope`, and `make coverage-tools` re-reads `tools/` from it. That
# scoping is gate-critical logic: get it
# wrong and the gate silently measures the wrong tree, or nothing at all.


def _cov_json(path: Path, files: dict[str, tuple[int, int, int, int]]) -> Path:
    """Write a coverage.json. Values are (statements, covered, branches, covered)."""
    payload = {
        "files": {
            name: {"summary": {
                "num_statements": stm, "covered_lines": cov,
                "num_branches": br, "covered_branches": bcov,
            }}
            for name, (stm, cov, br, bcov) in files.items()
        },
        "totals": {
            "num_statements": sum(v[0] for v in files.values()),
            "covered_lines": sum(v[1] for v in files.values()),
            "num_branches": sum(v[2] for v in files.values()),
            "covered_branches": sum(v[3] for v in files.values()),
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path

def _pyproject(path: Path, **keys: int) -> Path:
    specgraph = "\n".join(f"{k} = {v}" for k, v in keys.items())
    path.write_text(
        f"[tool.coverage.report]\nfail_under = 90\n[tool.specgraph]\n{specgraph}\n",
        encoding="utf-8",
    )
    return path

def test_scoped_totals_sum_only_the_named_subtree(tmp_path: Path) -> None:
    common = load_tool("common_scope", "_common.py")
    cov = _cov_json(tmp_path / "c.json", {
        "openspec_graph/cli.py": (100, 100, 40, 40),   # perfect, and irrelevant
        "tools/a.py": (10, 5, 4, 2),
        "tools/b.py": (10, 5, 4, 2),
    })
    assert common.coverage_totals(cov, "covered_lines", "num_statements", "tools") == (10, 20)
    # Unscoped still reads the report's own totals, unchanged.
    assert common.coverage_totals(cov, "covered_lines", "num_statements") == (110, 120)

def test_scoped_totals_normalize_windows_separators(tmp_path: Path) -> None:
    """coverage.py writes paths as the platform spells them.

    A backslash-separated path would never match a ``tools/`` prefix, and the
    failure mode is not a crash but a scope that matches nothing -- which on a
    green run looks exactly like a passing gate until the next assertion below
    turns it into exit 2.
    """
    common = load_tool("common_win", "_common.py")
    cov = _cov_json(tmp_path / "c.json", {"tools\\check_docs.py": (10, 9, 2, 2)})
    assert common.coverage_totals(cov, "covered_lines", "num_statements", "tools") == (9, 10)

def test_scoped_totals_are_zero_for_a_subtree_nobody_measured(tmp_path: Path) -> None:
    common = load_tool("common_none", "_common.py")
    cov = _cov_json(tmp_path / "c.json", {"openspec_graph/cli.py": (10, 10, 2, 2)})
    assert common.coverage_totals(cov, "covered_lines", "num_statements", "tools") == (0, 0)

def test_a_scope_matching_nothing_fails_the_gate_rather_than_passing(tmp_path: Path) -> None:
    """The load-bearing case. A prefix typo, a renamed directory, or a run
    that forgot `--cov=tools` all produce 0 measured statements, and 0/0 is
    not 100% -- it is a gate pointed at nothing. It must exit 2."""
    _cov_json(tmp_path / "coverage.json", {"openspec_graph/cli.py": (10, 10, 2, 2)})
    _pyproject(tmp_path / "pyproject.toml", tools_line_fail_under=90, tools_branch_fail_under=80)
    assert run_tool_main(
        "cf_empty", "check_coverage_floor.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2
    assert run_tool_main(
        "bc_empty", "check_branch_coverage.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2

def test_scoped_gate_fails_below_its_own_floor_and_passes_at_it(tmp_path: Path) -> None:
    _pyproject(tmp_path / "pyproject.toml", tools_line_fail_under=90, tools_branch_fail_under=80)
    _cov_json(tmp_path / "coverage.json", {
        # The package is perfect; tools/ is not. A combined number would pass.
        "openspec_graph/cli.py": (900, 900, 200, 200),
        "tools/thin.py": (100, 50, 20, 4),
    })
    assert run_tool_main(
        "cf_below", "check_coverage_floor.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 1
    assert run_tool_main(
        "bc_below", "check_branch_coverage.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 1
    # And the unscoped gate on the same file passes, which is exactly the
    # dilution the scoped floors exist to prevent: 95% overall, 50% in tools/.
    assert run_tool_main(
        "cf_whole", "check_coverage_floor.py", "coverage.json", cwd=tmp_path
    ) == 0

def test_scoped_gate_fails_loudly_when_its_floor_is_not_configured(tmp_path: Path) -> None:
    """A missing scoped floor is a misconfiguration, not a skip -- the same
    rule the unscoped floors already follow."""
    _cov_json(tmp_path / "coverage.json", {"tools/a.py": (10, 10, 2, 2)})
    _pyproject(tmp_path / "pyproject.toml", branch_fail_under=80)  # no tools_* keys
    assert run_tool_main(
        "cf_nofloor", "check_coverage_floor.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2
    assert run_tool_main(
        "bc_nofloor", "check_branch_coverage.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2

@pytest.mark.parametrize(
    ("argv", "expected_path", "expected_scope"),
    [
        (["prog"], "coverage.json", None),
        (["prog", "c.json"], "c.json", None),
        (["prog", "--scope", "tools"], "coverage.json", "tools"),
        (["prog", "--scope=tools"], "coverage.json", "tools"),
        (["prog", "c.json", "--scope", "tools"], "c.json", "tools"),
        (["prog", "--scope", "tools", "c.json"], "c.json", "tools"),
    ],
)
def test_coverage_argv_parses_every_accepted_shape(
    argv: list[str], expected_path: str, expected_scope: str | None
) -> None:
    common = load_tool("common_argv", "_common.py")
    path, scope = common.parse_coverage_argv(argv)
    assert (path.name, scope) == (expected_path, expected_scope)

@pytest.mark.parametrize("argv", [["prog", "--scope"], ["prog", "--scope="], ["prog", "--scope", ""]])
def test_coverage_argv_rejects_a_scope_without_a_value(argv: list[str]) -> None:
    """`--scope` with nothing after it must not be read as scope="" , which
    would build the prefix "/" and match every file in the report."""
    common = load_tool("common_argv_bad", "_common.py")
    with pytest.raises(ValueError, match="requires a directory name"):
        common.parse_coverage_argv(argv)

def test_scoped_gate_reports_a_usage_error_as_exit_2(tmp_path: Path, capsys) -> None:
    _pyproject(tmp_path / "pyproject.toml", tools_line_fail_under=90)
    assert run_tool_main(
        "cf_usage", "check_coverage_floor.py", "--scope", cwd=tmp_path
    ) == 2
    assert "usage error" in capsys.readouterr().err

# --- one coverage run, both floors read scoped (measure-coverage-once) -------
#
# The checkers now read one report for two trees. The floor for a scope is
# its own `[tool.specgraph] <scope>_<kind>_fail_under` key, or -- for the
# FIRST entry of `[tool.coverage.run] source` only, whose floors have always
# been the unscoped locators -- `fail_under` / `branch_fail_under`. Every
# other declared tree still needs its keys and exits 2 without them
# (R-MCO-3, R-MCO-4, R-MCO-5, DEC-MCO-002).


def _pyproject_with_sources(path: Path, sources: list[str], **keys: int) -> Path:
    """A planted pyproject that states which trees one run measures, and in what order."""
    listed = ", ".join(f'"{s}"' for s in sources)
    specgraph = "\n".join(f"{k} = {v}" for k, v in keys.items())
    path.write_text(
        f"[tool.coverage.run]\nsource = [{listed}]\nbranch = true\n"
        f"[tool.coverage.report]\nfail_under = 90\n[tool.specgraph]\n{specgraph}\n",
        encoding="utf-8",
    )
    return path

def _both_checkers(tmp_path: Path, *args: str) -> tuple[int, int]:
    return (
        run_tool_main("cf_scoped", "check_coverage_floor.py", *args, cwd=tmp_path),
        run_tool_main("bc_scoped", "check_branch_coverage.py", *args, cwd=tmp_path),
    )

def test_the_first_source_without_a_scoped_key_reads_the_unscoped_floors(tmp_path: Path) -> None:
    """`--scope openspec_graph` with no `openspec_graph_*` key reads `fail_under` and
    `branch_fail_under`, because the package is the first entry of `source`; the
    second entry keeps reading its own keys."""
    _pyproject_with_sources(
        tmp_path / "pyproject.toml", ["openspec_graph", "tools"],
        branch_fail_under=80, tools_line_fail_under=90, tools_branch_fail_under=80,
    )
    _cov_json(tmp_path / "coverage.json", {
        "openspec_graph/cli.py": (100, 85, 20, 14),   # 85% lines, 70% branches: below 90 / 80
        "tools/a.py": (10, 10, 2, 2),
    })
    assert _both_checkers(tmp_path, "coverage.json", "--scope", "openspec_graph") == (1, 1)
    assert _both_checkers(tmp_path, "coverage.json", "--scope", "tools") == (0, 0)
    _cov_json(tmp_path / "coverage.json", {
        "openspec_graph/cli.py": (100, 95, 20, 18),   # 95% / 90%: at or above both floors
        "tools/a.py": (10, 10, 2, 2),
    })
    assert _both_checkers(tmp_path, "coverage.json", "--scope", "openspec_graph") == (0, 0)

def test_a_scoped_key_on_the_first_source_is_honoured_and_is_the_misconfiguration_the_guard_rejects(
    tmp_path: Path,
) -> None:
    """A scoped key on the first entry is read first (so it cannot be ignored),
    and the duplicate-key helper names it: two places for one threshold."""
    planted = _pyproject_with_sources(
        tmp_path / "pyproject.toml", ["openspec_graph", "tools"],
        branch_fail_under=80, openspec_graph_line_fail_under=95,
        tools_line_fail_under=90, tools_branch_fail_under=80,
    )
    _cov_json(tmp_path / "coverage.json", {"openspec_graph/cli.py": (100, 92, 20, 18)})
    for spelling in ("openspec_graph", "openspec_graph/"):
        assert run_tool_main(
            "cf_dup", "check_coverage_floor.py", "coverage.json", "--scope", spelling, cwd=tmp_path
        ) == 1, f"92% under --scope {spelling} must fail the planted scoped 95, not pass the unscoped 90"
    common = load_tool("common_dup", "_common.py")
    for spelling in ("openspec_graph", "openspec_graph/", "./openspec_graph"):
        assert common.scoped_floor(planted, spelling, "line") == 95, spelling
        assert common.scoped_floor(planted, spelling, "branch") == 80, spelling
    assert common.duplicate_scoped_floor_keys(planted) == ["openspec_graph_line_fail_under"]

def test_a_declared_scope_that_is_not_first_still_exits_2_without_its_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-GTC-11 stands for every tree but the first: `tools` second in `source`
    with no `tools_*` key is a misconfiguration, named with both places."""
    _pyproject_with_sources(tmp_path / "pyproject.toml", ["openspec_graph", "tools"], branch_fail_under=80)
    _cov_json(tmp_path / "coverage.json", {"tools/a.py": (10, 10, 2, 2)})
    assert _both_checkers(tmp_path, "coverage.json", "--scope", "tools") == (2, 2)
    err = capsys.readouterr().err
    assert "tools_line_fail_under" in err and "tools_branch_fail_under" in err
    assert "openspec_graph" in err, "the message must name the first entry the unscoped floors belong to"
    _pyproject_with_sources(
        tmp_path / "pyproject.toml", ["openspec_graph", "tools"],
        branch_fail_under=80, tools_line_fail_under=90, tools_branch_fail_under=80,
    )
    for spelling in ("tools", "tools/"):
        assert _both_checkers(tmp_path, "coverage.json", "--scope", spelling) == (0, 0), spelling

def test_the_first_source_without_its_unscoped_floor_is_named_as_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The other branch of R-MCO-4's message: the first entry with no scoped key
    AND no unscoped floor is told that floor is absent, not sent to the scoped
    key -- for both kinds."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.coverage.run]\nsource = ["openspec_graph", "tools"]\n'
        "[tool.specgraph]\ntools_line_fail_under = 90\ntools_branch_fail_under = 80\n",
        encoding="utf-8",
    )
    _cov_json(tmp_path / "coverage.json", {"openspec_graph/cli.py": (10, 9, 2, 2)})
    assert _both_checkers(tmp_path, "coverage.json", "--scope", "openspec_graph") == (2, 2)
    err = capsys.readouterr().err
    for scoped_key, unscoped in (
        ("openspec_graph_line_fail_under", "[tool.coverage.report] fail_under"),
        ("openspec_graph_branch_fail_under", "[tool.specgraph] branch_fail_under"),
    ):
        assert scoped_key in err and unscoped in err, err
    assert "absent too" in err and "applies only" not in err, err

def test_coverage_sources_reads_the_run_table_array_and_nothing_else(tmp_path: Path) -> None:
    common = load_tool("common_sources", "_common.py")
    p = tmp_path / "pyproject.toml"
    p.write_text('[tool.coverage.run]\nsource = ["a", "b"]\n', encoding="utf-8")
    assert common.coverage_sources(p) == ["a", "b"]
    p.write_text('[tool.coverage.run]\nsource = [\n  "./tools/",\n  "openspec_graph/",\n]\nbranch = true\n', encoding="utf-8")
    assert common.coverage_sources(p) == ["tools", "openspec_graph"], "multi-line array, ./ and trailing / normalised"
    p.write_text('[tool.other]\nsource = ["x"]\n[tool.coverage.run]\nbranch = true\n', encoding="utf-8")
    assert common.coverage_sources(p) == [], "a source key under another table is not this one"
    p.write_text('[tool.coverage]\nrun.source = ["x"]\n', encoding="utf-8")
    assert common.coverage_sources(p) == [], "the dotted form is not read (DEC-MCO-003)"
    p.write_text('[tool.coverage.run]\nsource_pkgs = ["x"]\n', encoding="utf-8")
    assert common.coverage_sources(p) == [], "source_pkgs is a different key"
    assert common.coverage_sources(tmp_path / "absent.toml") == []

def test_the_first_source_declares_no_duplicate_scoped_floor_key(tmp_path: Path) -> None:
    """On this repository's own pyproject the first measured tree's floors live in
    the unscoped locators only; a scoped twin would be two places for one number."""
    common = load_tool("common_dup_real", "_common.py")
    real = REPO_ROOT / "pyproject.toml"
    sources = common.coverage_sources(real)
    assert sources, "pyproject.toml declares no [tool.coverage.run] source; the guard would be vacuous"
    assert common.duplicate_scoped_floor_keys(real) == [], (
        f"{sources[0]} is the first measured tree; its floors are [tool.coverage.report] "
        f"fail_under and [tool.specgraph] branch_fail_under, not a scoped twin"
    )
    planted = _pyproject_with_sources(
        tmp_path / "pyproject.toml", ["openspec_graph"], branch_fail_under=80,
        openspec_graph_line_fail_under=90, openspec_graph_branch_fail_under=80,
    )
    assert common.duplicate_scoped_floor_keys(planted) == [
        "openspec_graph_line_fail_under", "openspec_graph_branch_fail_under",
    ]

# --- the per-file minimum, a report rather than a gate (measure-coverage-once) --
#
# `check_coverage_floor.py --per-file-min` lists every module under
# `[tool.specgraph] per_file_line_min`; `make coverage-per-file` runs it and
# nothing in `ci` or `pre-pr` does (R-MCO-11, DEC-MCO-009).

PER_FILE_KEY = "per_file_line_min"

def _per_file_tree(tmp_path: Path, *, minimum: int | None = 85) -> Path:
    keys = {"tools_line_fail_under": 90, "tools_branch_fail_under": 80}
    if minimum is not None:
        keys[PER_FILE_KEY] = minimum
    _pyproject(tmp_path / "pyproject.toml", **keys)
    _cov_json(
        tmp_path / "coverage.json",
        {
            "openspec_graph/cli.py": (100, 70, 20, 20),  # 70%: below, the other tree
            "tools/a.py": (10, 5, 4, 4),  # 50%
            "tools/b.py": (10, 8, 4, 4),  # 80%
            "tools/c.py": (10, 10, 4, 4),  # 100%
        },
    )
    return tmp_path

def _per_file(tmp_path: Path, *args: str) -> int:
    return run_tool_main(
        "cf_per_file", "check_coverage_floor.py", "coverage.json", "--per-file-min", *args, cwd=tmp_path
    )

def test_per_file_report_names_each_module_below_the_minimum(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both modules under 85 are printed, ascending, each with its percentage,
    path and covered/total; exit 1."""
    assert _per_file(_per_file_tree(tmp_path), "--scope", "tools") == 1
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.lstrip().startswith(("50.0%", "80.0%"))]
    assert lines == [" 50.0%  tools/a.py  (5/10)", " 80.0%  tools/b.py  (8/10)"], out
    assert "tools/c.py" not in out
    assert "85%" in out.splitlines()[0], "the header names the minimum"

def test_per_file_report_exits_zero_when_no_module_is_below(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _per_file_tree(tmp_path, minimum=50)
    assert _per_file(tree, "--scope", "tools") == 0
    assert "no module below 50% line coverage" in capsys.readouterr().out

def test_per_file_report_fails_loudly_without_its_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _per_file(_per_file_tree(tmp_path, minimum=None)) == 2
    assert PER_FILE_KEY in capsys.readouterr().err

def test_per_file_report_respects_the_scope(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--scope tools` lists the tools/ modules below and not the
    openspec_graph/ one; no scope lists every measured tree; a scope matching
    nothing exits 2 rather than reporting a vacuous empty list."""
    tree = _per_file_tree(tmp_path)
    assert _per_file(tree, "--scope", "tools") == 1
    scoped = capsys.readouterr().out
    assert "tools/a.py" in scoped and "openspec_graph/cli.py" not in scoped
    assert _per_file(tree) == 1
    unscoped = capsys.readouterr().out
    assert "openspec_graph/cli.py" in unscoped and "every measured tree" in unscoped
    assert _per_file(tree, "--scope", "nowhere") == 2

def test_per_file_flag_leaves_the_argv_contract_alone(tmp_path: Path) -> None:
    """The flag is consumed before `parse_coverage_argv`, so a path and a scope
    beside it reach the same `(path, scope)`; the branch checker, which shares
    the parser, ignores a trailing flag and gates normally, and given the flag
    first takes it as the path (exit 2, file not found) -- as it does today."""
    tree = _per_file_tree(tmp_path)
    (tree / "coverage.json").rename(tree / "other.json")
    assert run_tool_main(
        "cf_pf_argv", "check_coverage_floor.py", "other.json", "--per-file-min", "--scope", "tools",
        cwd=tree,
    ) == 1
    _cov_json(tree / "coverage.json", {"tools/a.py": (10, 10, 4, 4)})
    assert run_tool_main(
        "bc_pf_trailing", "check_branch_coverage.py", "coverage.json", "--per-file-min",
        "--scope", "tools", cwd=tree,
    ) == 0
    assert run_tool_main(
        "bc_pf_first", "check_branch_coverage.py", "--per-file-min", "coverage.json",
        "--scope", "tools", cwd=tree,
    ) == 2
