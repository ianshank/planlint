"""Diff two spec dependency graphs. Fails if a PR regresses the graph (AC-CH-5,
AC-CH-6).

Exit non-zero if, comparing base -> head:

- ``broken_links`` increased, OR
- a new orphan requirement appears in head that was not in base.

Fixing an existing orphan or reducing broken_links is allowed (the gate only
fails on regressions, never on improvements).

Exit codes: 0 clean or improved, 1 regression, 2 usage error (argparse's own,
with the usage text on stderr). The ``graph-diff`` CI job invokes this as
``python tools/diff_spec_graph.py base.json head.json`` and greps stdout for
the ``PASS:`` / ``FAIL:`` line, so stdout carries that line and nothing else;
debugging detail goes to the ``planlint.tools`` logger (stderr, silent unless
``PLANLINT_LOG_LEVEL=DEBUG``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import logger, read_json


def orphan_ids(graph: dict[str, Any]) -> set[str]:
    return {n["id"] for n in graph["nodes"] if n.get("orphan")}


def diff(base: dict[str, Any], head: dict[str, Any]) -> list[str]:
    """Return a list of human-readable regressions; empty if the graph improved or held."""
    regressions: list[str] = []
    if head["broken_links"] > base["broken_links"]:
        regressions.append(
            f"broken_links increased: {base['broken_links']} -> {head['broken_links']}"
        )
    new_orphans = orphan_ids(head) - orphan_ids(base)
    if new_orphans:
        regressions.append(f"new orphan requirements: {sorted(new_orphans)}")
    return regressions


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diff_spec_graph.py",
        description="Fail if head's spec graph regressed against base's.",
    )
    parser.add_argument("base", type=Path, help="`planlint graph --format json` output for the base commit")
    parser.add_argument("head", type=Path, help="the same, for the head commit")
    return parser


def main(argv: list[str]) -> int:
    # ``argv`` arrives with the program name first, as every caller passes
    # ``sys.argv``; argparse strips it here (see tools/AGENTS.md on the argv
    # conventions). A usage error is argparse's ``SystemExit(2)``, which the
    # ``__main__`` guard below lets through unchanged.
    args = _parser().parse_args(argv[1:])
    base = read_json(args.base)
    head = read_json(args.head)

    regressions = diff(base, head)
    logger.debug(
        "diff_spec_graph: broken_links %s -> %s, %d new orphan(s), %d regression(s)",
        base["broken_links"],
        head["broken_links"],
        len(orphan_ids(head) - orphan_ids(base)),
        len(regressions),
    )
    if regressions:
        for message in regressions:
            print(f"FAIL: {message}")
        return 1

    print(
        f"PASS: broken_links {base['broken_links']} -> {head['broken_links']}, "
        f"no new orphan requirements"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
