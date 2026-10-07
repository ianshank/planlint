"""``tools/check_no_hardcoded_thresholds.py``: the guard that keeps floors in config.

Moved from ``tests/test_ci_hardening.py`` and ``tests/test_gate_scripts.py`` by
``shape-the-test-suite`` (R-TSS-2).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support import (
    load_tool,
)

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


# --- check_no_hardcoded_thresholds.py: this project's flagship rule ---------
#
# G003 says a threshold belongs in config, and this guard enforces it on the
# repo's own Makefile and workflows. Its failing path had no test: main() was
# exercised only against the repository itself, which passes, so "the guard
# reports FAIL when a threshold is hard-coded" was assumed rather than shown.


def _guard_tree(root: Path, makefile: str = "", workflow: str | None = None,
                makefile_name: str = "Makefile") -> Path:
    (root / makefile_name).write_text(makefile, encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text(workflow or "name: ci\n", encoding="utf-8")
    return root

def test_threshold_guard_passes_on_a_clean_tree(tmp_path: Path, capsys) -> None:
    guard = load_tool("hct_clean", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, makefile="test:\n\tpytest -q\n")
    assert guard.main(["x"], tree) == 0
    assert "PASS" in capsys.readouterr().out

def test_threshold_guard_fails_on_a_hard_coded_coverage_floor(tmp_path: Path, capsys) -> None:
    guard = load_tool("hct_makefile", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, makefile="test:\n\tpytest --cov-fail-under=90\n")
    assert guard.main(["x"], tree) == 1
    assert "hard-coded numeric literal '90'" in capsys.readouterr().out

def test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow(tmp_path: Path, capsys) -> None:
    guard = load_tool("hct_workflow", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, workflow="jobs:\n  t:\n    run: pytest --cov-fail-under=85\n")
    assert guard.main(["x"], tree) == 1
    assert "pinned in workflow, not pyproject" in capsys.readouterr().out

def test_threshold_guard_fails_on_a_pinned_tool_version(tmp_path: Path, capsys) -> None:
    """A pinned ruff/mypy/pytest is the other half of the rule: dev extras are
    deliberately unpinned so contributors and CI resolve the same versions."""
    guard = load_tool("hct_pin", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, workflow="jobs:\n  t:\n    run: pip install ruff==0.4.2\n")
    assert guard.main(["x"], tree) == 1
    assert "tool version pinned in workflow" in capsys.readouterr().out

def test_threshold_guard_dispatches_a_gnumakefile_to_the_makefile_checker(
    tmp_path: Path, capsys
) -> None:
    """Dispatch is by which list the path came from, never by basename.

    A repo using GNUmakefile would otherwise be handed to the *workflow*
    checker, which scans for entirely different shapes and would report PASS
    on a hard-coded floor. The source says so; nothing asserted it.
    """
    guard = load_tool("hct_gnu", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(
        tmp_path, makefile="test:\n\tpytest --cov-fail-under=90\n", makefile_name="GNUmakefile"
    )
    assert guard.main(["x"], tree) == 1
    assert "hard-coded numeric literal '90'" in capsys.readouterr().out

def test_threshold_guard_scans_both_yaml_spellings(tmp_path: Path) -> None:
    """`.yaml` is as valid to GitHub Actions as `.yml`."""
    guard = load_tool("hct_yaml", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path)
    (tree / ".github" / "workflows" / "extra.yaml").write_text(
        "run: pytest --cov-fail-under=70\n", encoding="utf-8"
    )
    assert {p.name for p in guard.targets(tree)} >= {"ci.yml", "extra.yaml"}
    assert guard.main(["x"], tree) == 1

def test_threshold_guard_ignores_comments_and_make_expansions(tmp_path: Path) -> None:
    """The allowlist works by token, not by vetoing whole lines.

    `$(shell ...)` and a leading `@` are stripped before scanning, so a recipe
    that echoes a number computed elsewhere is fine -- but a literal outside
    an expansion on that same line must still be caught, which a line-level
    veto would have missed.
    """
    guard = load_tool("hct_allow", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, makefile=(
        "# fail_under = 90 in a comment is documentation, not a pin\n"
        "check:\n"
        "\t@echo $(shell python -c 'print(90)')\n"
    ))
    assert guard.main(["x"], tree) == 0

def test_threshold_guard_survives_a_makefile_that_is_not_a_regular_file(tmp_path: Path) -> None:
    """A directory carrying the name: nothing to scan, and no fall-through to
    a lower-precedence file -- `make` stops there too."""
    guard = load_tool("hct_notfile", "check_no_hardcoded_thresholds.py")
    (tmp_path / "Makefile").mkdir()
    assert guard.check_makefile(tmp_path / "Makefile") == []

def test_threshold_guard_survives_a_missing_workflow(tmp_path: Path) -> None:
    guard = load_tool("hct_nowf", "check_no_hardcoded_thresholds.py")
    assert guard.check_workflow(tmp_path / "nope.yml") == []
