"""Render a saved ``graph --format json`` file as a Mermaid flowchart.

A thin, separate consumer of the JSON graph, per docs/next-steps.md's own
guidance -- kept out of the core `graph` projection. `planlint graph
--format mermaid` covers the common case directly; this script covers the
other real one: rendering an artifact saved from a previous run (e.g. a CI
job's uploaded `spec-graph.json`) without re-running `planlint` at all.

Unlike most tools/ gate scripts, this one imports openspec_graph --
deliberately: it exists purely to expose mermaid.to_mermaid() for this one
use case, and duplicating that function's logic here would be exactly the
kind of two-copies-drift-apart problem this project's own rules elsewhere
exist to catch. The ``sys.path`` bootstrap below is what lets it run as
``python tools/render_mermaid.py`` from a checkout where the package is not
installed, the same way ``matcher_accuracy.py`` and ``stage_citations.py``
do.

Stdout is the rendering and nothing else -- byte-identical to
``to_mermaid(graph)`` -- so it can be redirected straight into a ``.mmd``
file. Debugging detail goes to the ``planlint.tools`` logger (stderr, silent
unless ``PLANLINT_LOG_LEVEL=DEBUG``). Exit codes: 0 rendered, 2 usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import logger, read_json, repo_root

sys.path.insert(0, str(repo_root()))

from openspec_graph.mermaid import to_mermaid


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="render_mermaid.py",
        description="Render a saved `planlint graph --format json` file as a Mermaid flowchart.",
    )
    parser.add_argument("graph", type=Path, help="the saved graph JSON file")
    return parser


def main(argv: list[str]) -> int:
    # Program name first, stripped here -- see tools/AGENTS.md on the argv
    # conventions. A usage error is argparse's own ``SystemExit(2)``.
    args = _parser().parse_args(argv[1:])
    graph = read_json(args.graph)
    logger.debug(
        "render_mermaid: %s -> %d node(s), %d edge(s)",
        args.graph,
        len(graph.get("nodes", ())),
        len(graph.get("edges", ())),
    )
    print(to_mermaid(graph), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
