"""Enforce the line-coverage floor, read from pyproject.toml at run time.

coverage.py's ``--cov-fail-under`` CLI flag takes a number, which would hard-code
the threshold into the Makefile — exactly the anti-pattern rule G003 / C-CH-2
forbids. This script reads ``fail_under`` from
``[tool.coverage.report]`` in pyproject.toml and gates line coverage against it,
so the threshold lives in one place (the config), never in CI config.

Usage::

    coverage run ... && coverage json -o coverage.json
    python tools/check_coverage_floor.py [coverage.json]
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


def _read_floor(pyproject: Path, scope: str | None = None) -> int | None:
    """The line floor for ``scope``, or the repo-wide one when ``scope`` is None.

    The unscoped floor stays in ``[tool.coverage.report] fail_under``, which is
    also what coverage.py itself reads -- one locator, so the gate and the
    library cannot drift. A scoped floor is specgraph's own key and lives in
    ``[tool.specgraph]`` alongside the branch floor, for the same reason that
    one does: coverage.py would warn about an option it does not know.
    """
    if scope is None:
        return read_pyproject_int(pyproject, "[tool.coverage.report]", "fail_under")
    return read_pyproject_int(pyproject, SCOPED_FLOOR_SECTION, scoped_floor_key(scope, "line"))


def line_coverage(cov_path: Path, scope: str | None = None) -> tuple[float, int, int]:
    covered, num = coverage_totals(cov_path, "covered_lines", "num_statements", scope)
    pct = (100.0 * covered / num) if num else 0.0
    return pct, covered, num


def main(argv: list[str]) -> int:
    try:
        cov_path, scope = parse_coverage_argv(argv)
    except ValueError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    floor = _read_floor(Path("pyproject.toml"), scope)

    if floor is None:
        # A repo that turns this gate on MUST configure fail_under. Missing it is
        # a misconfiguration, not a skip — fail loud so CI never passes silently.
        where = (
            "[tool.coverage.report] fail_under" if scope is None
            else f"{SCOPED_FLOOR_SECTION} {scoped_floor_key(scope, 'line')}"
        )
        print(f"no line floor set in pyproject.toml {where}", file=sys.stderr)
        return 2

    if not cov_path.exists():
        print(f"coverage file not found: {cov_path}; run coverage first", file=sys.stderr)
        return 2

    pct, covered, num = line_coverage(cov_path, scope)
    if num == 0:
        # For a scope, this also catches a prefix that matches no measured
        # file -- a gate pointed at a tree nobody measured must fail, never
        # report a vacuous 0/0 pass.
        subject = "statements" if scope is None else f"statements under {scope}/"
        print(f"no {subject} measured; is coverage configured for the source?", file=sys.stderr)
        return 2

    label = "line coverage" if scope is None else f"{scope}/ line coverage"
    if pct < floor:
        print(f"{label} {pct:.1f}% ({covered}/{num}) below floor {floor}% from pyproject.toml")
        return 1
    print(f"{label} {pct:.1f}% ({covered}/{num}) meets floor {floor}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
