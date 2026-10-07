"""The static-check ratchets on the tree: mypy over ``tests/`` by a per-code baseline.

``ratchet-test-types-and-docstrings`` (plan W6.5): the guards that verify that
package's criteria against this repository. ``make typecheck`` reads its trees
from ``[tool.mypy] files`` in the configuration file its recipe names. The codes
the one ``tests.*`` override lists are each held to an exact count in
:data:`MYPY_TESTS_CEILINGS`, taken by the gate's own run less that entry under
``--platform linux`` and ``--platform win32``. Every inline ignore under
``tests/`` is a waiver recorded in :data:`MYPY_WAIVERS`, and no comment, stub,
name or condition hides code from mypy.

The helpers live in ``tests/ratchet_support.py`` and are shown red on planted
input by ``tests/test_static_ratchets_planted.py`` (DEC-TDR-012).
"""

from __future__ import annotations

import logging
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from tests.ratchet_support import (
    MYPY_TREES,
    PLATFORMS,
    Ignore,
    ceiling_problems,
    derive_config,
    derived_problems,
    dev_extra_problems,
    hidden_code,
    listed_codes,
    load_mypy_config,
    makefile_recipe,
    mypy_config_problems,
    mypy_errors,
    override_problems,
    platform_only,
    read_comments,
    run_environment,
    stub_problems,
    waiver_problems,
)
from tests.support import env_without_coverage, read_pyproject

LOG = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent

# R-TDR-4: each code the `tests.*` override lists -> its occurrence count under
# tests/, as test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms
# measures it at the commit that lands the override. An entry is lowered or
# removed in the commit that changes its count, and is never added. It is raised
# only to follow a mypy release that changes the count of unchanged code, in the
# pull request where this guard first names that change, with the release named
# beside the entry (DEC-TDR-004).
MYPY_TESTS_CEILINGS: dict[str, int] = {
    "arg-type": 17,
    "attr-defined": 18,
    "index": 7,
    "no-any-return": 8,
    "no-untyped-def": 96,
    "type-arg": 16,
    "union-attr": 4,
}

# R-TDR-7: every inline ignore comment under tests/, as (path, code, waived
# line): the physical line's text before the comment, whitespace collapsed. An
# entry is removed and never added. A commit that edits a waived line's text
# updates that entry's text in the same commit, and one that moves the line to
# another file updates its path (DEC-TDR-006).
MYPY_WAIVERS: tuple[tuple[str, str, str], ...] = (
    ("tests/test_graft_witness.py", "arg-type", "return witness.Witness(**fields)"),
    ("tests/test_matcher_accuracy.py", "arg-type", "assert negation_matches(None, None) == ()"),
    ("tests/test_rules_speckit.py", "arg-type", "return parse_model.ParsedSpec(**defaults)"),
    ("tests/test_stage_citations.py", "arg-type", "return original(self, *args, **kwargs)"),
    ("tests/test_suite_shape.py", "attr-defined", 'entries = [str(entry) for entry in options.get("markers", [])]'),
    ("tests/test_witness.py", "arg-type", "return Witness(**fields)"),
    ("tests/test_witness.py", "attr-defined", 'monkeypatch.setattr(witness.os, "replace", spy_replace)'),
    ("tests/test_witness.py", "attr-defined", 'monkeypatch.setattr(witness.os, "replace", boom)'),
)


# --- the guards on the tree ---------------------------------------------------


def _test_modules() -> list[str]:
    return sorted(f"tests.{path.stem}" for path in (REPO_ROOT / "tests").glob("*.py"))


def _mypy_table() -> dict[str, Any]:
    table = read_pyproject()["tool"]["mypy"]
    assert isinstance(table, dict)
    return table


@pytest.mark.integration
def test_typecheck_reads_its_trees_from_the_mypy_files_list() -> None:
    """R-TDR-1 / AC-TDR-3: the recipe is `python -m mypy --config-file pyproject.toml`
    with no path, and `[tool.mypy]` holds exactly its six keys and the overrides."""
    recipe = makefile_recipe((REPO_ROOT / "Makefile").read_text(encoding="utf-8"), "typecheck")
    problems = mypy_config_problems(recipe, _mypy_table())
    assert problems == [], "\n".join(problems)


@pytest.mark.integration
def test_the_tests_override_is_one_entry_listing_exactly_the_ceilinged_codes() -> None:
    """R-TDR-2 / R-TDR-4 / AC-TDR-4: loaded through mypy, every test module differs
    from the global options only by the listed codes, which are the ceilings' keys."""
    listed, problems = listed_codes(_mypy_table().get("overrides", []))
    problems += ceiling_problems(listed, MYPY_TESTS_CEILINGS)
    options, stderr = load_mypy_config(REPO_ROOT / "pyproject.toml")
    problems += override_problems(options, stderr, _test_modules(), listed)
    assert problems == [], "\n".join(problems)


@pytest.mark.e2e
def test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms(tmp_path: Path) -> None:
    """R-TDR-5 / AC-TDR-5: the gate's own run less the tests entry, re-checked
    through mypy, agrees on both platforms and matches every ceiling exactly."""
    table = _mypy_table()
    listed, problems = listed_codes(table.get("overrides", []))
    derived = tmp_path / "derived.ini"
    derived.write_text(derive_config(table), encoding="utf-8")
    source, _ = load_mypy_config(REPO_ROOT / "pyproject.toml")
    loaded, stderr = load_mypy_config(derived)
    problems += [f"loading the derived configuration wrote {stderr!r}"] if stderr else []
    problems += derived_problems(loaded, source, _test_modules())
    runs: dict[str, list[dict[str, Any]]] = {}
    for platform in PLATFORMS:
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--config-file", str(derived),
             "--cache-dir", str(tmp_path / f"cache-{platform}"), "--platform", platform, "-O", "json"],
            cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=False, env=run_environment(env_without_coverage()),
        )
        runs[platform], failed = mypy_errors(result.stdout, result.stderr, result.returncode)
        problems += [f"{platform}: {problem}" for problem in failed]
    problems += platform_only(runs)
    counts = Counter(error["code"] for error in runs[PLATFORMS[0]])
    LOG.info("per-code counts under tests/: %s", dict(sorted(counts.items())))
    problems += ceiling_problems(listed, MYPY_TESTS_CEILINGS, counts)
    assert problems == [], "\n".join(problems)


@pytest.mark.integration
def test_every_inline_ignore_is_a_recorded_waiver() -> None:
    """R-TDR-7 / AC-TDR-8: every inline ignore under `tests/` is a recorded waiver
    of one code, and no comment or line there configures mypy."""
    listed, _ = listed_codes(_mypy_table().get("overrides", []))
    ignores: list[Ignore] = []
    problems: list[str] = []
    for path in sorted((REPO_ROOT / "tests").rglob("*.py")):
        found, named = read_comments(path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
        ignores += found
        problems += named
    problems += waiver_problems(ignores, MYPY_WAIVERS, listed)
    assert problems == [], "\n".join(problems)


@pytest.mark.integration
def test_no_stub_name_or_condition_hides_code_from_mypy() -> None:
    """R-TDR-7 / AC-TDR-8 / DEC-TDR-016: no stub in the three trees, and no unchecked
    name or version or platform branch under `tests/` but R-TDR-6's one."""
    stubs = [p.relative_to(REPO_ROOT).as_posix() for tree in MYPY_TREES for p in (REPO_ROOT / tree).rglob("*.pyi")]
    problems = stub_problems(stubs)
    for path in sorted((REPO_ROOT / "tests").rglob("*.py")):
        problems += hidden_code(path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
    assert problems == [], "\n".join(problems)


@pytest.mark.integration
def test_the_dev_extra_floors_mypy_and_pins_nothing() -> None:
    """R-TDR-16 / AC-TDR-22: the dev extra floors mypy at the first release with
    `-O json`, read with `packaging`, and pins no tool."""
    problems = dev_extra_problems(read_pyproject()["project"]["optional-dependencies"]["dev"])
    assert problems == [], "\n".join(problems)
