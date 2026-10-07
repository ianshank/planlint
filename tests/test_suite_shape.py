"""The shape of the test suite: flat, bounded, tiered, routed.

`shape-the-test-suite` (plan W7.4): the guards that hold what the package
changes. Milestone 1 adds the flatness and the module-size bound; later
milestones add the tier markers, the helper routing and the one-subprocess
rule for the converted loops. The constants here mirror ``MAX_NESTED_LINES``
in ``tests/test_agent_artifacts.py``: a bound the suite holds itself to lives
beside the test that enforces it, not in ``pyproject.toml``, because it bounds
this repository's own tests and nothing an adopter configures (DEC-TSS-004).
"""

from __future__ import annotations

from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

#: Inclusive bound on the lines of one ``tests/test_*.py`` module, as
#: ``wc -l tests/test_*.py`` counts them. The plan's W7.4 item splits every
#: module over it by concern; a module at the bound is in bounds.
MAX_TEST_MODULE_LINES = 700


def _flat_test_modules(root: Path = TESTS_DIR) -> list[Path]:
    return sorted(root.glob("test_*.py"))


def _nested_test_modules(root: Path = TESTS_DIR) -> list[Path]:
    """Every ``test_*.py`` below a subdirectory of ``root`` -- what the flat globs miss."""
    return sorted(p for p in root.rglob("test_*.py") if p.parent != root)


def _line_count(path: Path) -> int:
    """What ``wc -l`` prints: newline characters."""
    return path.read_bytes().count(b"\n")


def _modules_over_bound(
    root: Path = TESTS_DIR, bound: int = MAX_TEST_MODULE_LINES
) -> list[tuple[str, int]]:
    return sorted(
        (p.name, _line_count(p)) for p in _flat_test_modules(root) if _line_count(p) > bound
    )


def test_the_tests_directory_stays_flat() -> None:
    """`tests/test_spec_test_citations.py` and `tests/test_decomposition.py` glob
    `test_*.py` non-recursively, so a test module under a subdirectory is
    collected by pytest and seen by neither gate (R-TSS-1, #35)."""
    assert _flat_test_modules(), "no flat test modules found; the glob or the cwd is wrong"
    assert _nested_test_modules() == [], (
        "test modules under a subdirectory of tests/ escape the citation and "
        "decomposition gates; keep tests/ flat"
    )


def test_no_test_module_exceeds_the_line_bound() -> None:
    """R-TSS-1: every `tests/test_*.py` is at most `MAX_TEST_MODULE_LINES` lines
    (`wc -l`); the offenders are named with their counts."""
    over = _modules_over_bound()
    assert over == [], (
        f"test modules over {MAX_TEST_MODULE_LINES} lines (split by concern, keep the names): {over}"
    )
