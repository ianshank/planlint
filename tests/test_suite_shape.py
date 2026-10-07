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
from pathlib import Path

import pytest

from tests.shape_support import (
    TIERS,
    Program,
    criterion_disagreements,
    plant,
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
    assert _registration_problems(options) == []
    assert options.get("testpaths") == [TESTS_DIR.name], options.get("testpaths")


def _registration_problems(options: dict[str, object]) -> list[str]:
    """What is wrong with the tier registration in ``[tool.pytest.ini_options]``.

    The names are compared as a list, not a mapping, so a tier registered twice
    is named rather than collapsed into one entry."""
    entries = [str(entry) for entry in options.get("markers", [])]  # type: ignore[attr-defined]
    pairs = [entry.partition(":")[::2] for entry in entries]
    names = [name.strip() for name, _ in pairs]
    problems: list[str] = []
    if sorted(names) != sorted(TIERS):
        problems.append(f"registered markers {sorted(names)} are not exactly the tiers {list(TIERS)}")
    problems += [f"{name} has no criterion" for name, criterion in pairs if not criterion.strip()]
    if "--strict-markers" not in shlex.split(str(options.get("addopts", ""))):
        problems.append("addopts lacks --strict-markers; a misspelt tier is a warning, not an error")
    return problems


_STRICT = "-q --strict-markers"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("markers", "addopts", "named"),
    [
        (["unit: a", "integration: b", "e2e: c", "unit: d"], _STRICT, "not exactly the tiers"),
        (["unit: a", "integration: b"], _STRICT, "not exactly the tiers"),
        (["unit: a", "integration: b", "e2e:  "], _STRICT, "e2e has no criterion"),
        (["unit: a", "integration: b", "e2e: c"], "-q", "lacks --strict-markers"),
    ],
    ids=["a-tier-registered-twice", "a-tier-missing", "a-blank-criterion", "not-strict"],
)
def test_a_duplicated_or_missing_tier_registration_is_named(
    markers: list[str], addopts: str, named: str
) -> None:
    """R-TSS-5: the registration check names a tier registered twice -- which a
    mapping would collapse -- a missing one, a blank criterion and a lax addopts."""
    found = _registration_problems({"markers": markers, "addopts": addopts})
    assert any(named in line for line in found), found


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
        {"test_planted.py": """
            import inspect

            import pytest

            from openspec_graph import parse


            @pytest.mark.unit
            def test_reads_package_source():
                assert "def parse_spec" in inspect.getsource(parse.parse_spec)
        """},
        "criterion", "test_reads_package_source", id="unit-reading-source-through-inspect",
    ),
    pytest.param(
        {"test_planted.py": """
            from pathlib import Path

            import pytest

            ROOT = Path(__file__).resolve().parent.parent


            @pytest.mark.unit
            def test_counts_a_word():
                assert (ROOT / "README.md").read_text().count("fixtures") >= 0
        """},
        "criterion", "test_counts_a_word", id="unit-whose-labelled-word-is-a-method-argument",
    ),
    pytest.param(
        {"test_planted.py": """
            from pathlib import Path

            import pytest

            FIXTURES = Path(__file__).resolve().parent / "fixtures"


            @pytest.mark.unit
            def test_climbs_out():
                assert (FIXTURES.parent.parent / "README.md").name
        """},
        "criterion", "test_climbs_out", id="unit-climbing-out-of-fixtures-by-parent",
    ),
    pytest.param(
        {"test_planted.py": """
            from pathlib import Path

            import pytest


            @pytest.mark.unit
            def test_climbs_out():
                assert (Path(__file__).parent / "fixtures" / ".." / ".." / "README.md").name
        """},
        "criterion", "test_climbs_out", id="unit-climbing-out-of-fixtures-by-dotdot",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest

            import tests.support


            @pytest.mark.unit
            def test_spawns(tmp_path):
                assert tests.support.run_cli(tmp_path, "rules").returncode == 0
        """},
        "criterion", "test_spawns", id="unit-spawning-through-an-unaliased-import",
    ),
    pytest.param(
        {"test_planted.py": """
            import os.path

            import pytest


            @pytest.mark.unit
            def test_spawns():
                assert os.system("true") == 0
        """},
        "criterion", "test_spawns", id="unit-spawning-through-a-dotted-import",
    ),
    pytest.param(
        {"test_planted.py": """
            import multiprocessing

            import pytest


            @pytest.mark.unit
            def test_spawns():
                multiprocessing.Process(target=print).start()
        """},
        "criterion", "test_spawns", id="unit-starting-a-multiprocessing-process",
    ),
    pytest.param(
        {"../tools/planted_script.py": "def main():\n    return 0\n", "test_planted.py": """
            import pytest

            from tools import planted_script


            @pytest.mark.unit
            def test_runs_a_script():
                assert planted_script.main() == 0
        """},
        "criterion", "test_runs_a_script", id="unit-running-a-tools-script-in-process",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest


            class TestHidden:
                @pytest.mark.unit
                def test_in_a_class(self):
                    assert True
        """},
        "tiers", "a test class", id="a-test-class",
    ),
    pytest.param(
        {"test_planted.py": """
            import pytest


            @pytest.mark.unit
            @pytest.mark.parametrize("x", [1, pytest.param(2, marks=pytest.mark.e2e)])
            def test_param(x):
                assert x
        """},
        "tiers", "pytest.param marks", id="a-tier-inside-pytest-param-marks",
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
    plant(root, files)
    if check is None:
        reports = {name: _report(root, name) for name in ("tiers", "criterion", "bound", "flat")}
        assert all(found == [] for found in reports.values()), reports
        return
    found = _report(root, check)
    assert any(offender in line for line in found), f"{check} did not name {offender}: {found}"
