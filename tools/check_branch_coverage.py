"""Enforce a branch-coverage floor, read from pyproject.toml at run time.

coverage.py's ``fail_under`` gates the combined line+branch total. This script
gates branch coverage specifically, so a module with high line coverage but
untested conditional branches still fails the gate (AC-CH-3).

Usage::

    coverage run ... && coverage json -o coverage.json
    python tools/check_branch_coverage.py [coverage.json]

The floor is read from ``[tool.specgraph].branch_fail_under`` in pyproject.toml
— never hard-coded here or in the Makefile (rule G003 / C-CH-2). It lives in
this project's own table rather than ``[tool.coverage.report]`` so coverage.py
does not warn about an option it does not recognize; the function below and
this gate's own failure message have always said so, and only this docstring
disagreed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    SCOPED_FLOOR_SECTION,
    coverage_totals,
    parse_coverage_argv,
    read_pyproject_int,
    scoped_floor_key,
)


def _read_branch_floor(pyproject: Path, scope: str | None = None) -> int | None:
    """Read the branch floor for ``scope``, or the repo-wide one if None.

    Both are specgraph's own gate keys, kept out of ``[tool.coverage.*]`` so
    coverage.py doesn't warn about an unknown option.
    """
    key = "branch_fail_under" if scope is None else scoped_floor_key(scope, "branch")
    return read_pyproject_int(pyproject, SCOPED_FLOOR_SECTION, key)


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
        key = "branch_fail_under" if scope is None else scoped_floor_key(scope, "branch")
        print(f"no {key} set in pyproject.toml {SCOPED_FLOOR_SECTION}", file=sys.stderr)
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
