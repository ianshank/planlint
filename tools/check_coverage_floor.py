"""Enforce the line-coverage floor, read from pyproject.toml at run time.

coverage.py's ``--cov-fail-under`` CLI flag takes a number, which would hard-code
the threshold into the Makefile — exactly the anti-pattern rule G003 / C-CH-2
forbids. The thresholds live in pyproject.toml, never in CI config.

One run writes ``coverage.json`` for every tree in ``[tool.coverage.run]
source``; this script reads that one report under ``--scope`` for each
measured tree. The floor for a scope is its own ``[tool.specgraph]
<scope>_line_fail_under`` key or, for the FIRST ``source`` entry without one,
``[tool.coverage.report] fail_under`` — the locator that has always gated it
and that coverage.py itself reads (measure-coverage-once, R-MCO-3). Every
later entry needs its own key and exits 2 without it.

With ``--per-file-min`` the script is a report, not a gate: it lists every
module (under ``--scope``, or in every measured tree) whose line coverage is
below ``[tool.specgraph] per_file_line_min``, lowest first, and exits 1 when
the list is non-empty. ``make coverage-per-file`` runs it; nothing in ``ci``
or ``pre-pr`` does (measure-coverage-once, R-MCO-11, DEC-MCO-009).

Usage::

    python -m pytest --cov --cov-report=json:coverage.json
    python tools/check_coverage_floor.py [coverage.json] [--scope NAME]
    python tools/check_coverage_floor.py [coverage.json] [--scope NAME] --per-file-min
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    SCOPED_FLOOR_SECTION,
    UNSCOPED_FLOOR_LOCATORS,
    coverage_totals,
    logger,
    missing_floor_message,
    parse_coverage_argv,
    read_pyproject_int,
    scoped_floor,
)

#: The report mode's flag and its threshold key. The flag is consumed here,
#: before ``parse_coverage_argv``, so that parser's ``(path, scope)`` contract
#: is unchanged for both checkers (R-MCO-11).
PER_FILE_FLAG = "--per-file-min"
PER_FILE_KEY = "per_file_line_min"


def _read_floor(pyproject: Path, scope: str | None = None) -> int | None:
    """The line floor for ``scope``, or the repo-wide one when ``scope`` is None.

    The unscoped floor stays in ``[tool.coverage.report] fail_under``, which is
    also what coverage.py itself reads -- one locator, so the gate and the
    library cannot drift. A scoped floor is specgraph's own key and lives in
    ``[tool.specgraph]`` alongside the branch floor, for the same reason that
    one does: coverage.py would warn about an option it does not know. The
    first ``[tool.coverage.run] source`` entry without a scoped key falls back
    to the unscoped locator; see :func:`_common.scoped_floor` for the rule.
    """
    if scope is None:
        return read_pyproject_int(pyproject, *UNSCOPED_FLOOR_LOCATORS["line"])
    return scoped_floor(pyproject, scope, "line")


def line_coverage(cov_path: Path, scope: str | None = None) -> tuple[float, int, int]:
    covered, num = coverage_totals(cov_path, "covered_lines", "num_statements", scope)
    pct = (100.0 * covered / num) if num else 0.0
    return pct, covered, num


def per_file_report(
    cov_path: Path, minimum: int, scope: str | None = None
) -> list[tuple[float, str, int, int]]:
    """``(pct, path, covered, total)`` for every file under ``scope`` below ``minimum``.

    Every measured file when ``scope`` is None; separators are normalised the
    way :func:`_common.coverage_totals` normalises them, so the same ``--scope``
    selects the same files in both modes. Sorted by ``(pct, path)`` -- lowest
    first, ties by name -- so the list reads as a worklist.
    """
    data = json.loads(cov_path.read_text(encoding="utf-8"))
    prefix = None if scope is None else scope.replace("\\", "/").rstrip("/") + "/"
    below: list[tuple[float, str, int, int]] = []
    for raw_path, entry in data.get("files", {}).items():
        path = raw_path.replace("\\", "/")
        if prefix is not None and not path.startswith(prefix):
            continue
        summary = entry.get("summary", {})
        covered = int(summary.get("covered_lines", 0))
        total = int(summary.get("num_statements", 0))
        pct = (100.0 * covered / total) if total else 0.0
        if pct < minimum:
            below.append((pct, path, covered, total))
    logger.debug("per_file_report: %d file(s) below %d%% under %s", len(below), minimum, scope)
    return sorted(below)


def _report_per_file(cov_path: Path, scope: str | None) -> int:
    """The ``--per-file-min`` mode: list, don't gate (DEC-MCO-009)."""
    minimum = read_pyproject_int(Path("pyproject.toml"), SCOPED_FLOOR_SECTION, PER_FILE_KEY)
    if minimum is None:
        print(f"no {PER_FILE_KEY} set in pyproject.toml {SCOPED_FLOOR_SECTION}", file=sys.stderr)
        return 2
    if not cov_path.exists():
        print(f"coverage file not found: {cov_path}; run coverage first", file=sys.stderr)
        return 2
    _, measured = coverage_totals(cov_path, "covered_lines", "num_statements", scope)
    if measured == 0:
        # R-GTC-10's posture: a scope that matches nothing is a report pointed
        # at nothing, never an empty (and therefore clean) list.
        subject = "statements" if scope is None else f"statements under {scope}/"
        print(f"no {subject} measured; is coverage configured for the source?", file=sys.stderr)
        return 2
    below = per_file_report(cov_path, minimum, scope)
    where = "every measured tree" if scope is None else f"{scope}/"
    print(f"modules in {where} below {minimum}% line coverage ({PER_FILE_KEY}):")
    for pct, path, covered, total in below:
        print(f"{pct:5.1f}%  {path}  ({covered}/{total})")
    if below:
        return 1
    print(f"no module below {minimum}% line coverage")
    return 0


def main(argv: list[str]) -> int:
    report_mode = PER_FILE_FLAG in argv
    try:
        cov_path, scope = parse_coverage_argv([arg for arg in argv if arg != PER_FILE_FLAG])
    except ValueError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    if report_mode:
        return _report_per_file(cov_path, scope)
    floor = _read_floor(Path("pyproject.toml"), scope)

    if floor is None:
        # A repo that turns this gate on MUST configure fail_under. Missing it is
        # a misconfiguration, not a skip — fail loud so CI never passes silently.
        where = (
            " ".join(UNSCOPED_FLOOR_LOCATORS["line"]) if scope is None
            else missing_floor_message(Path("pyproject.toml"), scope, "line")
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
