"""Report which make stages this repository's specs cite, and where CI runs them.

Two rules read a spec's ``make`` citations, and they read different text:

* **G004** checks every backticked ``make <stage>`` anywhere in a spec
  (``ParsedSpec.make_refs``) against the Makefile -- does the target exist?
* **W001**, under ``--require-witness``, checks only the stages a criterion
  cites on its verification line (``Criterion.verified_by``) -- did it run?

A stage can be mentioned in forty specs and cited as verification in five, and
only the second number is a claim witness mode will ever check. Counting the
first by mistake is how a planning document overstated what witness mode would
report against this repository (``docs/peer-review-2026-10.md`` N2), so this
tool reports both, per stage, together with the workflow files under
``.github/workflows/`` that invoke the stage directly as ``make <stage>``.

Usage::

    python tools/stage_citations.py                         # text table
    python tools/stage_citations.py --format json           # stable JSON
    python tools/stage_citations.py --workflow ci.yml       # only that workflow
    python tools/stage_citations.py --root /path/to/checkout

It is a **report, not a gate** -- the same shape as ``matcher_accuracy.py``
(``DEC-PM-011``): it exits 0 whatever the numbers say, so it can describe a
repository mid-migration without failing it. It exits 2 when it cannot run: no
spec tree under ``--root``, or a named ``--workflow`` that does not exist.

Limits, stated so the numbers are read correctly. A workflow is credited only
for a *direct* ``make <stage>`` invocation: ``run:`` scripts are read (nothing
else in a workflow is shell), each is lexed with quotes and comments honoured,
and only ``make`` in command position counts. So ``make pre-pr`` running
``test`` transitively is not counted as running ``test``; ``make`` behind a
wrapper such as ``sudo`` or ``env`` is not; text that only mentions ``make
test`` -- printed, quoted, passed as an argument, a step's ``name:``, a
comment -- is never credited; and a script the lexer cannot read (a quote left
open) credits nothing, because guessing which half of it is data is how an
unrun stage gets credited.

Like ``matcher_accuracy.py`` and the ``render_*`` generators, this imports
``openspec_graph`` rather than re-implementing its parser: the point is to
count what the rules see, and a second parser would count something else.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ReportError, logger, repo_root
from _common import run_scripts as run_scripts
from _common import shell_invocations as _shell_invocations
from _common import workflow_invocations as _workflow_invocations
from _common import workflow_stages as _workflow_stages

sys.path.insert(0, str(repo_root()))

from openspec_graph import detect
from openspec_graph.parse import MAKE_REF, SpecReadError, parse_spec

# The report's own shape version, announced like every machine-readable output
# in this repository so a consumer can refuse one it does not understand.
SCHEMA_VERSION = 1


@dataclasses.dataclass(frozen=True)
class StageRow:
    """One cited stage: how many specs mention it, cite it, and who runs it."""

    stage: str
    mentioned: int
    verified: int
    workflows: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "mentioned": self.mentioned,
            "verified": self.verified,
            "workflows": list(self.workflows),
        }


def spec_files(root: Path) -> tuple[detect.StackProfile, list[Path]]:
    """The profile and every spec file the CLI itself would read under ``root``."""
    prof = detect.profile(root)
    files: list[Path] = []
    if prof.openspec_root:
        files.extend(detect.find_spec_files(prof.openspec_root))
    if prof.speckit_root:
        files.extend(detect.find_speckit_spec_files(prof.speckit_root))
    if not prof.openspec_root and not prof.speckit_root:
        raise ReportError(f"no openspec/ directory and no SpecKit specs/ tree under {root}")
    return prof, files


# The workflow lexer -- `run_scripts`, the shell tokeniser, `WORKFLOW_DIR` and
# `ReportError` among it -- lives in `_common` (report-dead-code-and-spec-status,
# R-RDS-24), shared with `spec_status.py`, and takes the stage grammar as a
# parameter so `_common` stays stdlib-only. This module keeps its public names
# and call shapes: `run_scripts(text)` is re-exported as it is, since it needs
# no grammar, and the three wrappers below each pass `MAKE_REF`, the grammar a
# spec cites a stage in, so a stage credited here is one a spec could cite.


def shell_invocations(script: str) -> set[str]:
    """Stages a shell script invokes as ``make <stage>`` in command position."""
    return _shell_invocations(script, stage_ref=MAKE_REF)


def workflow_invocations(text: str) -> set[str]:
    """Stages a workflow file invokes directly as ``make <stage>``."""
    return _workflow_invocations(text, stage_ref=MAKE_REF)


def workflow_stages(root: Path, only: Sequence[str] = ()) -> dict[str, set[str]]:
    """``{workflow file name: stages it invokes}`` for ``.github/workflows/``;
    a name in ``only`` that does not exist raises ``ReportError``."""
    return _workflow_stages(root, only, stage_ref=MAKE_REF)


def build_rows(root: Path, only: Sequence[str] = ()) -> tuple[int, list[StageRow]]:
    """``(spec count, one row per cited stage, sorted by stage name)``."""
    prof, files = spec_files(root)
    mentioned: dict[str, int] = {}
    verified: dict[str, int] = {}
    for path in files:
        try:
            spec = parse_spec(path, prof.dialect)
        except SpecReadError as exc:
            # The CLI maps an unreadable spec to exit 2 (`_report_unreadable`);
            # a report that counts specs must not traceback where the gate it
            # describes would have refused to run.
            raise ReportError(f"cannot read {path}: {exc}") from exc
        for stage in set(spec.make_refs):
            mentioned[stage] = mentioned.get(stage, 0) + 1
        for stage in {s for crit in spec.criteria for s in MAKE_REF.findall(crit.verified_by)}:
            verified[stage] = verified.get(stage, 0) + 1
    runs = workflow_stages(root, only)
    rows = [
        StageRow(
            stage=stage,
            mentioned=mentioned.get(stage, 0),
            verified=verified.get(stage, 0),
            workflows=tuple(sorted(name for name, stages in runs.items() if stage in stages)),
        )
        for stage in sorted(set(mentioned) | set(verified))
    ]
    logger.debug("stage-citations: %d spec(s), %d cited stage(s)", len(files), len(rows))
    return len(files), rows


def render_text(spec_count: int, rows: Sequence[StageRow]) -> str:
    width = max([len("stage"), *(len(r.stage) for r in rows)])
    lines = [
        f"{'stage':<{width}}  {'mentioned':>9}  {'verified':>8}  run directly by",
        f"{'-' * width}  {'-' * 9}  {'-' * 8}  {'-' * 14}",
    ]
    for row in rows:
        runners = ", ".join(row.workflows) or "-"
        lines.append(f"{row.stage:<{width}}  {row.mentioned:>9}  {row.verified:>8}  {runners}")
    on_line = [r for r in rows if r.verified]
    unrun = [r.stage for r in on_line if not r.workflows]
    lines += [
        "",
        f"{spec_count} spec(s); {len(rows)} stage(s) cited; {len(on_line)} on a verification line; "
        f"{len(unrun)} of those invoked by no scanned workflow"
        + (f": {', '.join(unrun)}" if unrun else ""),
    ]
    return "\n".join(lines) + "\n"


def render_json(spec_count: int, rows: Sequence[StageRow], only: Sequence[str]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "specs": spec_count,
        "workflows_scanned": sorted(only) if only else "all",
        "stages": [row.as_dict() for row in rows],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository to scan (default: the current directory)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--workflow", action="append", default=[], metavar="FILE",
        help="restrict the workflow scan to this file name under .github/workflows/ (repeatable)",
    )
    args = parser.parse_args(list(argv[1:]))
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR not a directory: {root}", file=sys.stderr)
        return 2
    try:
        spec_count, rows = build_rows(root, args.workflow)
    except ReportError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    out = render_json(spec_count, rows, args.workflow) if args.format == "json" else render_text(spec_count, rows)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
