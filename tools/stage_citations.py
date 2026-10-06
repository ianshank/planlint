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
import re
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import logger, repo_root

sys.path.insert(0, str(repo_root()))

from openspec_graph import detect
from openspec_graph.parse import MAKE_REF, SpecReadError, parse_spec

# The report's own shape version, announced like every machine-readable output
# in this repository so a consumer can refuse one it does not understand.
SCHEMA_VERSION = 1

WORKFLOW_DIR = Path(".github") / "workflows"

# `run:` is the only workflow key whose value is shell. A step's `name:`, an
# `if:`, a `with:` argument, a comment -- anything else that happens to contain
# `make test` -- is data, so only `run:` scalars are read: the inline form,
# plain or YAML-quoted, and the block forms -- `|` or `>` with their chomping
# and indentation indicators, or a bare `run:` over an indented plain scalar --
# whose body is every following line indented past the key.
_RUN_KEY = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>-[ \t]+)?run:[ \t]*(?P<rest>.*?)[ \t]*$")
_BLOCK_INDICATOR = re.compile(r"[|>][-+0-9]*")
_YAML_QUOTED = re.compile(r"""^(?:"((?:[^"\\]|\\.)*)"|'((?:[^']|'')*)')[ \t]*(?:#.*)?$""")

# Shell operators after which the next word is a command: `;`, `&&`, `||`,
# `|`, `&`, and `(` as in `$(...)`. The lexer hands a run of these over as one
# token; a run ending in `)` closes a subshell instead, and what follows it is
# an argument. A `VAR=value` prefix keeps the word after it in command position.
_SHELL_SEPARATORS = ";&|()"
_SHELL_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")


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


class ReportError(Exception):
    """A precondition failure: the report cannot be produced. Exit 2."""


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


def run_scripts(text: str) -> list[str]:
    """The shell text of every ``run:`` scalar in a workflow file, in order."""
    lines = text.splitlines()
    scripts: list[str] = []
    index = 0
    while index < len(lines):
        match = _RUN_KEY.match(lines[index])
        index += 1
        if match is None:
            continue
        rest = match.group("rest")
        if rest and not _BLOCK_INDICATOR.fullmatch(rest):
            quoted = _YAML_QUOTED.match(rest)
            scripts.append(rest if quoted is None else quoted.group(1) or quoted.group(2) or "")
            continue
        key_column = len(match.group("indent")) + len(match.group("marker") or "")
        body: list[str] = []
        while index < len(lines) and (
            not lines[index].strip() or len(lines[index]) - len(lines[index].lstrip()) > key_column
        ):
            body.append(lines[index])
            index += 1
        scripts.append("\n".join(body))
    return scripts


def _shell_tokens(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=_SHELL_SEPARATORS)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return list(lexer)


def shell_invocations(script: str) -> set[str]:
    """Stages a shell script invokes as ``make <stage>`` in command position.

    Lexed, not pattern-matched: a quoted string is one word whatever it
    contains, a ``#`` comment runs to the end of its line, and only the word
    at a line start or after a separator is a command. A line is lexed on its
    own unless a quote left open carries the string onto the next line; a
    quote still open at the end of the script leaves that tail unread, which
    credits nothing rather than guessing which half of it is data.
    """
    stages: set[str] = set()
    pending = ""
    for line in script.replace("\\\n", " ").split("\n"):
        pending = f"{pending}\n{line}" if pending else line
        try:
            words = _shell_tokens(pending)
        except ValueError:
            continue
        pending = ""
        command_start = True
        for position, word in enumerate(words):
            if word and all(char in _SHELL_SEPARATORS for char in word):
                command_start = not word.endswith(")")
                continue
            if not command_start or _SHELL_ASSIGNMENT.match(word):
                continue
            if word == "make" and position + 1 < len(words):
                # MAKE_REF's own grammar decides what a stage is, so a stage
                # credited here is one a spec could cite.
                cited = MAKE_REF.fullmatch(f"`make {words[position + 1]}`")
                if cited is not None:
                    stages.add(cited.group(1))
            command_start = False
    return stages


def workflow_invocations(text: str) -> set[str]:
    """Stages a workflow file invokes directly as ``make <stage>``."""
    stages: set[str] = set()
    for script in run_scripts(text):
        stages |= shell_invocations(script)
    return stages


def workflow_stages(root: Path, only: Sequence[str] = ()) -> dict[str, set[str]]:
    """``{workflow file name: stages it invokes}`` for ``.github/workflows/``.

    ``only`` restricts the scan to the named files; a name that does not exist
    is a precondition failure rather than an empty result, because a typo'd
    filter would otherwise report every stage as "run by nothing".
    """
    directory = root / WORKFLOW_DIR
    found = sorted(
        p for p in directory.glob("*") if p.is_file() and p.suffix in {".yml", ".yaml"}
    ) if directory.is_dir() else []
    if only:
        names = {p.name for p in found}
        missing = sorted(set(only) - names)
        if missing:
            raise ReportError(f"no such workflow under {directory}: {', '.join(missing)}")
        found = [p for p in found if p.name in set(only)]
    result: dict[str, set[str]] = {}
    for path in found:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            # Same contract as an unreadable spec: could-not-run is exit 2,
            # never a traceback that exits 1.
            raise ReportError(f"cannot read {path}: {exc}") from exc
        result[path.name] = workflow_invocations(text)
        logger.debug("stage-citations: %s invokes %s", path.name, sorted(result[path.name]))
    return result


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
