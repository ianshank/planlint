"""The shape of the test suite: flat, bounded, tiered, routed.

`shape-the-test-suite` (plan W7.4): the guards that hold what the package
changes. Milestone 1 adds the flatness and the module-size bound; later
milestones add the tier markers, the helper routing and the one-subprocess
rule for the converted loops. The constants here mirror ``MAX_NESTED_LINES``
in ``tests/test_agent_artifacts.py``: a bound the suite holds itself to lives
beside the test that enforces it, not in ``pyproject.toml``, because it bounds
this repository's own tests and nothing an adopter configures (DEC-TSS-004).

The tier guards read every test through ``tests/shape_support.py``, the AST
engine that decides a tier from what a test uses (R-TSS-6); this module holds
the assertions and the planted counter-examples.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.shape_support import (
    SUPPORT_MODULE,
    TIERS,
    Program,
    converted_loop_violations,
    criterion_disagreements,
    hand_written_specs,
    inline_cli_spawns,
    routed_shapes,
    tier_count_violations,
    tier_tally,
)
from tests.support import env_without_coverage, read_pyproject

LOG = logging.getLogger(__name__)

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent

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


@pytest.mark.integration
def test_the_tests_directory_stays_flat() -> None:
    """`tests/test_spec_test_citations.py` and `tests/test_decomposition.py` glob
    `test_*.py` non-recursively, so a test module under a subdirectory is
    collected by pytest and seen by neither gate (R-TSS-1, #35)."""
    assert _flat_test_modules(), "no flat test modules found; the glob or the cwd is wrong"
    assert _nested_test_modules() == [], (
        "test modules under a subdirectory of tests/ escape the citation and "
        "decomposition gates; keep tests/ flat"
    )


@pytest.mark.integration
def test_no_test_module_exceeds_the_line_bound() -> None:
    """R-TSS-1: every `tests/test_*.py` is at most `MAX_TEST_MODULE_LINES` lines
    (`wc -l`); the offenders are named with their counts."""
    over = _modules_over_bound()
    assert over == [], (
        f"test modules over {MAX_TEST_MODULE_LINES} lines (split by concern, keep the names): {over}"
    )


# --- Milestone 4: the tiers (R-TSS-5, R-TSS-6) ---------------------------------


def _pytest_options() -> dict[str, object]:
    options = read_pyproject()["tool"]["pytest"]["ini_options"]
    assert isinstance(options, dict)
    return options


@pytest.mark.integration
def test_pytest_registers_exactly_the_three_tier_markers_strictly() -> None:
    """R-TSS-5: the three tiers are registered by name under `markers` -- not
    only through `addopts`, which the durations command clears -- each with
    its criterion, and `--strict-markers` turns any other mark into an error."""
    options = _pytest_options()
    entries = [str(entry) for entry in options.get("markers", [])]  # type: ignore[attr-defined]
    registered = dict(entry.partition(":")[::2] for entry in entries)
    assert sorted(registered) == sorted(TIERS), (
        f"registered markers {sorted(registered)} are not exactly the tiers {list(TIERS)}"
    )
    blank = sorted(name for name, criterion in registered.items() if not criterion.strip())
    assert blank == [], f"tier markers registered without their criterion: {blank}"
    assert "--strict-markers" in shlex.split(str(options.get("addopts", ""))), (
        "addopts lacks --strict-markers; a misspelt tier is a warning, not an error"
    )
    assert options.get("testpaths") == [TESTS_DIR.name], options.get("testpaths")


@pytest.mark.e2e
def test_an_unregistered_marker_fails_collection_under_strict_markers(tmp_path: Path) -> None:
    """R-TSS-5: under this repository's own `pyproject.toml`, a mark nobody
    registered stops collection and is named, rather than passing as a typo."""
    (tmp_path / "pyproject.toml").write_text(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    planted = tmp_path / TESTS_DIR.name / "test_planted.py"
    planted.parent.mkdir()
    planted.write_text(
        "import pytest\n\n\n@pytest.mark.nonsuch\ndef test_planted():\n    pass\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
        env=env_without_coverage(),
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "nonsuch" in output and "markers" in output, output


@pytest.mark.integration
def test_every_test_carries_exactly_one_tier_marker() -> None:
    """R-TSS-5: module `pytestmark` and decorators both count, so every test
    resolves to exactly one tier; a tier written through an alias is named."""
    offenders = tier_count_violations(TESTS_DIR)
    assert offenders == [], (
        f"{len(offenders)} tests or aliases break the one-tier rule "
        f"(mark each with one of {list(TIERS)}; a mixed module marks per function):\n"
        + "\n".join(offenders)
    )


@pytest.mark.integration
def test_every_tier_marker_matches_its_mechanical_criterion() -> None:
    """R-TSS-6: `e2e` iff the test reaches a process start, `integration` iff
    it reads this repository's tree and starts none, `unit` iff neither --
    computed from what each test uses, never from what it is called."""
    program = Program(TESTS_DIR)
    LOG.info("tiers by the criterion:\n%s", tier_tally(program))
    disagreements = criterion_disagreements(program)
    assert disagreements == [], (
        f"{len(disagreements)} tier marks disagree with the criterion:\n"
        + "\n".join(disagreements)
    )


_FIXTURE_TREE_READER = """
    from pathlib import Path

    import pytest


    @pytest.fixture
    def repo_root() -> Path:
        return Path(__file__).resolve().parent.parent
"""

_AUTOUSE_SPAWN = """
    import subprocess

    import pytest


    @pytest.fixture(autouse=True)
    def _probe() -> None:
        subprocess.run(["git", "--version"], check=False)
"""

_CLASS_SPAWN = """
    import subprocess


    class Runner:
        def go(self) -> int:
            return subprocess.run(["git", "--version"], check=False).returncode
"""

#: (planted files under tests/, the report that must name it, the name), or a
#: report of ``None`` for a planted text every report must stay quiet on.
PLANTED = [
    pytest.param(
        {"test_planted.py": "def test_no_tier():\n    assert True\n"},
        "tiers", "test_no_tier", id="an-unmarked-test",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest

            pytestmark = pytest.mark.unit


            @pytest.mark.integration
            def test_two_tiers():
                assert True
        """},
        "tiers", "test_two_tiers", id="two-tiers-across-both-levels",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest

            fast = pytest.mark.unit


            @fast
            def test_aliased():
                assert True
        """},
        "tiers", "fast = pytest.mark.unit", id="a-tier-through-an-alias",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest

            from tests.support import run_cli


            @pytest.mark.unit
            def test_spawns(tmp_path):
                assert run_cli(tmp_path, "validate").returncode == 0
        """},
        "criterion", "test_spawns", id="unit-calling-run-cli",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest


            @pytest.mark.e2e
            def test_starts_nothing():
                assert 1 + 1 == 2
        """},
        "criterion", "test_starts_nothing", id="e2e-naming-no-process-start",
    ),
    pytest.param(
        {"test_planted.py": """
            from pathlib import Path

            import pytest

            ROOT = Path(__file__).resolve().parent.parent
            README = ROOT / "README.md"


            @pytest.mark.unit
            def test_names_a_tree_constant():
                assert README.name
        """},
        "criterion", "test_names_a_tree_constant", id="unit-naming-a-file-bound-constant",
    ),
    pytest.param(
        {"conftest.py": _FIXTURE_TREE_READER, "test_planted.py": """
            import pytest


            @pytest.mark.unit
            def test_through_a_fixture(repo_root):
                assert repo_root.exists()
        """},
        "criterion", "test_through_a_fixture", id="unit-reading-the-tree-through-a-fixture",
    ),
    pytest.param(
        {"conftest.py": _AUTOUSE_SPAWN, "test_planted.py": """
            import pytest


            @pytest.mark.unit
            def test_under_an_autouse_spawn():
                assert True
        """},
        "criterion", "test_under_an_autouse_spawn", id="unit-under-an-autouse-fixture-that-spawns",
    ),
    pytest.param(
        {"planted_support.py": _CLASS_SPAWN, "test_planted.py": """
            import pytest

            from tests.planted_support import Runner


            @pytest.mark.unit
            def test_through_a_class():
                assert Runner().go() == 0
        """},
        "criterion", "test_through_a_class", id="unit-spawning-through-a-support-class-method",
    ),
    pytest.param(
        {"test_planted.py": """
            from pathlib import Path

            import pytest


            @pytest.mark.unit
            def test_reads_and_discards():
                text = (Path(__file__).parent.parent / "README.md").read_text()
        """},
        "criterion", "test_reads_and_discards", id="unit-binding-a-tree-read-it-never-uses",
    ),
    pytest.param(
        {"test_planted.py": "# a line\n" * (MAX_TEST_MODULE_LINES + 1)},
        "bound", "test_planted.py", id="a-module-over-the-bound",
    ),
    pytest.param(
        {"sub/test_x.py": "def test_hidden():\n    pass\n"},
        "flat", "sub/test_x.py", id="a-module-under-a-subdirectory",
    ),
    pytest.param(
        {"test_planted.py": """
            import subprocess
            from pathlib import Path

            import pytest

            FIXTURES = Path(__file__).resolve().parent / "fixtures"


            def _fake() -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(["x"], 0, "", "")


            @pytest.mark.unit
            def test_reads_labelled_input():
                assert (Path(__file__).parent / "fixtures" / "x.md").name == "x.md"


            @pytest.mark.unit
            def test_uses_a_fixtures_rooted_constant():
                assert (FIXTURES / "x.md").suffix == ".md"


            @pytest.mark.unit
            def test_builds_a_fake_result():
                assert _fake().returncode == 0
        """},
        None, None, id="quiet-on-labelled-input-and-a-result-type",
    ),
    pytest.param(
        {"test_planted.py": "# a line\n" * MAX_TEST_MODULE_LINES},
        None, None, id="quiet-on-a-module-exactly-at-the-bound",
    ),
]


def _plant(root: Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def _report(root: Path, check: str) -> list[str]:
    if check == "tiers":
        return tier_count_violations(root)
    if check == "criterion":
        return criterion_disagreements(Program(root, support_root=TESTS_DIR))
    if check == "bound":
        return [name for name, _ in _modules_over_bound(root)]
    return [path.relative_to(root).as_posix() for path in _nested_test_modules(root)]


@pytest.mark.integration
@pytest.mark.parametrize(("files", "check", "offender"), PLANTED)
def test_a_mismarked_or_unmarked_planted_module_is_named(
    tmp_path: Path, files: dict[str, str], check: str | None, offender: str | None
) -> None:
    """R-TSS-1, R-TSS-5, R-TSS-6: each guard's helper names its planted
    counter-example, and stays quiet on labelled input, an annotation, a fake
    result and a module exactly at the bound."""
    root = tmp_path / TESTS_DIR.name
    _plant(root, files)
    if check is None:
        reports = {name: _report(root, name) for name in ("tiers", "criterion", "bound", "flat")}
        assert all(found == [] for found in reports.values()), reports
        return
    found = _report(root, check)
    assert any(offender in line for line in found), f"{check} did not name {offender}: {found}"


# --- Milestone 5: the duplicated shapes route through tests/support.py (R-TSS-8) ---


@pytest.mark.integration
def test_no_test_module_spawns_the_cli_outside_support() -> None:
    """R-TSS-8: `run_cli` is the one place a test spawns the CLI against a
    target; the shape is read from `run_cli` itself, so a copy that drifts
    from it -- the UTF-8 decode, the coverage hand-off -- is named."""
    shapes = routed_shapes(TESTS_DIR / SUPPORT_MODULE)
    inline = inline_cli_spawns(TESTS_DIR, shapes)
    assert inline == [], f"spawn the CLI through tests.support.run_cli, not inline: {inline}"


@pytest.mark.integration
def test_no_test_module_writes_a_spec_path_by_hand() -> None:
    """R-TSS-8: `write_spec` and `write_speckit_spec` are the only writers of
    the harness and SpecKit spec paths; a FIFO, a directory or an assertion at
    such a path is not a write."""
    shapes = routed_shapes(TESTS_DIR / SUPPORT_MODULE)
    by_hand = hand_written_specs(TESTS_DIR, shapes)
    assert by_hand == [], f"write specs through the tests.support writers: {by_hand}"


_PLANTED_ROUTING = {
    "inline-cli-spawn": ("""
        import subprocess
        import sys


        def test_spawns(tmp_path):
            subprocess.run(
                [sys.executable, "-m", "openspec_graph.cli", "--target", str(tmp_path), "validate"],
                check=False,
            )
    """, "spawn", True),
    "version-spawn-without-target": ("""
        import subprocess
        import sys


        def test_version():
            subprocess.run([sys.executable, "-m", "openspec_graph.cli", "--version"], check=False)
    """, "spawn", False),
    "harness-write-through-a-local": ("""
        def test_writes(tmp_path):
            spec = tmp_path / "openspec" / "changes" / "c1" / "specs" / "cap" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("# Spec", encoding="utf-8")
    """, "write", True),
    "speckit-write-through-two-locals": ("""
        def test_writes(tmp_path):
            features = tmp_path / "specs"
            feature = features / "001-demo"
            (feature / "spec.md").write_text("# Spec", encoding="utf-8")
    """, "write", True),
    "fifo-at-a-spec-path": ("""
        import os


        def test_fifo(tmp_path):
            os.mkfifo(tmp_path / "specs" / "001-demo" / "spec.md")
    """, "write", False),
    "assertion-on-a-spec-path": ("""
        def test_exists(tmp_path):
            assert not (tmp_path / "specs" / "001-demo" / "spec.md").exists()
    """, "write", False),
    "main-spec-path-no-writer-routes": ("""
        def test_writes(tmp_path):
            (tmp_path / "openspec" / "specs" / "cap" / "spec.md").write_text("x")
    """, "write", False),
}


@pytest.mark.integration
@pytest.mark.parametrize("case", sorted(_PLANTED_ROUTING))
def test_a_planted_inline_spawn_or_hand_written_spec_is_named(tmp_path: Path, case: str) -> None:
    """R-TSS-8: each routing guard names its planted shape and stays quiet on
    a spawn without `--target`, a FIFO, an assertion and a path no routed
    writer owns."""
    text, guard, named = _PLANTED_ROUTING[case]
    root = tmp_path / TESTS_DIR.name
    _plant(root, {"test_planted.py": text})
    shapes = routed_shapes(TESTS_DIR / SUPPORT_MODULE)
    found = inline_cli_spawns(root, shapes) if guard == "spawn" else hand_written_specs(root, shapes)
    assert bool(found) is named, f"{case}: {found}"


# --- Milestone 6: the converted loops keep one subprocess each (R-TSS-9) -----------

#: The four tests R-TSS-9 converts, by module: each loop runs through
#: `cli.main` in-process, and one `run_cli` stays as the entry-point check.
CONVERTED_LOOPS = {
    "test_report.py": (
        "test_projections_are_byte_stable_across_runs",
        "test_an_unprojectable_file_exits_two_with_an_empty_stdout",
    ),
    "test_sarif.py": ("test_sarif_returns_the_same_exit_code_as_the_text_run",),
    "test_e2e_corpus.py": ("test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict",),
}


@pytest.mark.integration
def test_the_converted_loops_keep_exactly_one_subprocess() -> None:
    """R-TSS-9: each converted body holds exactly one `run_cli`, outside any
    loop, and references `main`, so its verdicts run in-process and stay tied
    to one real process."""
    found = converted_loop_violations(TESTS_DIR, CONVERTED_LOOPS)
    assert found == [], "\n".join(found)


_PLANTED_LOOPS = {
    "two-run-cli-calls": ("""
        def test_loop(tmp_path):
            run_cli(tmp_path, "validate")
            run_cli(tmp_path, "rules")
            main(["--target", str(tmp_path), "validate"])
    """, True),
    "no-run-cli-call": ("""
        def test_loop(tmp_path):
            main(["--target", str(tmp_path), "validate"])
    """, True),
    "run-cli-inside-a-loop": ("""
        def test_loop(tmp_path):
            for fmt in ("a", "b"):
                run_cli(tmp_path, "report", "--format", fmt)
            main(["--target", str(tmp_path), "validate"])
    """, True),
    "no-reference-to-main": ("""
        def test_loop(tmp_path):
            run_cli(tmp_path, "validate")
    """, True),
    "one-entry-check-and-main": ("""
        def test_loop(tmp_path, capsys):
            for fmt in ("a", "b"):
                main(["--target", str(tmp_path), "report", "--format", fmt])
            assert run_cli(tmp_path, "validate").returncode == 0
    """, False),
}


@pytest.mark.integration
@pytest.mark.parametrize("case", sorted(_PLANTED_LOOPS))
def test_a_planted_loop_with_the_wrong_subprocess_count_is_named(tmp_path: Path, case: str) -> None:
    """R-TSS-9, R-TSS-12: the loop guard names a body with two `run_cli`
    calls, with none, with one inside a loop, or with no `main`, and stays
    quiet on the converted shape."""
    text, named = _PLANTED_LOOPS[case]
    root = tmp_path / TESTS_DIR.name
    _plant(root, {"test_planted.py": text})
    found = converted_loop_violations(root, {"test_planted.py": ("test_loop",)})
    assert bool(found) is named, f"{case}: {found}"
