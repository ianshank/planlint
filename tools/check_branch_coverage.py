"""Enforce a branch-coverage floor, read from pyproject.toml at run time.

coverage.py's ``fail_under`` gates the combined line+branch total. This script
gates branch coverage specifically, so a module with high line coverage but
untested conditional branches still fails the gate (AC-CH-3).

Usage::

    python -m pytest --cov --cov-branch --cov-report=json:coverage.json
    python tools/check_branch_coverage.py [coverage.json] [--scope NAME]

The floor is read from ``[tool.specgraph].branch_fail_under`` in pyproject.toml
— never hard-coded here or in the Makefile (rule G003 / C-CH-2). It lives in
this project's own table rather than ``[tool.coverage.report]`` so coverage.py
does not warn about an option it does not recognize; the function below and
this gate's own failure message have always said so, and only this docstring
disagreed.

One run writes ``coverage.json`` for every tree in ``[tool.coverage.run]
source``; this script reads that one report under ``--scope`` for each
measured tree. The floor for a scope is its own ``<scope>_branch_fail_under``
key or, for the FIRST ``source`` entry without one, ``branch_fail_under`` — the
key that has always gated it (measure-coverage-once, R-MCO-3). Every later
entry needs its own key and exits 2 without it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    SCOPED_FLOOR_SECTION,
    UNSCOPED_FLOOR_LOCATORS,
    coverage_totals,
    missing_floor_message,
    parse_coverage_argv,
    read_pyproject_int,
    scoped_floor,
)


def _read_branch_floor(pyproject: Path, scope: str | None = None) -> int | None:
    """Read the branch floor for ``scope``, or the repo-wide one if None.

    Both are specgraph's own gate keys, kept out of ``[tool.coverage.*]`` so
    coverage.py doesn't warn about an unknown option. The first
    ``[tool.coverage.run] source`` entry without a scoped key falls back to
    ``branch_fail_under``; see :func:`_common.scoped_floor` for the rule.
    """
    if scope is None:
        return read_pyproject_int(pyproject, *UNSCOPED_FLOOR_LOCATORS["branch"])
    return scoped_floor(pyproject, scope, "branch")


def branch_coverage(cov_path: Path, scope: str | None = None) -> tuple[float, int, int]:
    covered, num = coverage_totals(cov_path, "covered_branches", "num_branches", scope)
    pct = (100.0 * covered / num) if num else 0.0
    return pct, covered, num


def main(argv: list[str]) -> int:
    try:
        cov_path, scope = parse_coverage_argv(argv)
    except ValueError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    floor = _read_branch_floor(Path("pyproject.toml"), scope)

    if floor is None:
        # A repo that turns this gate on MUST configure branch_fail_under.
        # Missing it is a misconfiguration, not a skip — fail loud so CI never
        # passes silently on a gate it claims to enforce.
        if scope is None:
            key = UNSCOPED_FLOOR_LOCATORS["branch"][1]
            print(f"no {key} set in pyproject.toml {SCOPED_FLOOR_SECTION}", file=sys.stderr)
        else:
            where = missing_floor_message(Path("pyproject.toml"), scope, "branch")
            print(f"no branch floor set in pyproject.toml {where}", file=sys.stderr)
        return 2

    if not cov_path.exists():
        print(f"coverage file not found: {cov_path}; run coverage first", file=sys.stderr)
        return 2

    pct, covered, num = branch_coverage(cov_path, scope)
    if num == 0:
        # branch=true is set in pyproject; zero branches means coverage didn't
        # instrument the source at all — a real misconfiguration, not a pass.
        print(
            "no branches measured; is branch=true set and source instrumented?",
            file=sys.stderr,
        )
        return 2

    label = "branch coverage" if scope is None else f"{scope}/ branch coverage"
    if pct < floor:
        print(
            f"{label} {pct:.1f}% ({covered}/{num} branches) "
            f"below floor {floor}% from pyproject.toml"
        )
        return 1
    print(f"{label} {pct:.1f}% ({covered}/{num}) meets floor {floor}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
