"""Report each change package's Status header beside its evidence.

Usage::

    python tools/spec_status.py                     # this repository
    python tools/spec_status.py --root /path/to/checkout

It is a **report, not a gate** (``DEC-PM-011``, guardrail 7), composed into
neither ``ci`` nor ``pre-pr``, and it **never edits a header**: settling one is
a human decision after review, and the worklist this prints belongs to the
follow-up package ``settle-package-status-headers``
(``report-dead-code-and-spec-status``, DEC-RDS-008). Its exit contract is
planlint's own (R-RDS-12, DEC-RDS-006): **0** when no package carries a
finding, with a line saying so; **1** when one does; **2** when it cannot run
-- no ``openspec/changes/``, no package in it, a package file or
``CHANGELOG.md`` that cannot be read or decoded, a workflow that cannot be
read -- with the file or directory named and never a traceback.

One row per package of ``detect.profile(root).change_dirs``, the packages
``planlint detect`` counts: every directory directly under
``openspec/changes/``, a symlinked alias once, a package with no ``spec.md``
kept. Each row gives the ``Status`` header of each ``spec.md`` and the
proposal's status line; criteria ticked of declared (``- [x] **AC-`` of every
``- [ ] **AC-`` and ``- [x] **AC-`` line); ``## Milestone`` headings carrying
``[DONE]`` of all, else task checkboxes ticked of all, else "none recorded";
the CHANGELOG sections holding an entry naming the package -- a heading
ending in the backticked name in parentheses, or a bullet led by the bold
backticked name, and no other mention; and the stages cited on the package's
verification lines that no scanned workflow invokes directly.

The vocabulary (R-RDS-11): spec ``DRAFT`` is draft and ``APPROVED`` settled;
proposal ``proposed`` is draft and ``implemented`` settled. Words match
case-sensitively. A package carries at most one finding, in this order:

* ``header-unrecognised`` -- a ``spec.md`` with no header or a word outside
  the vocabulary, a proposal word outside it, or no ``spec.md`` at all;
* ``headers-disagree`` -- its headers map to both draft and settled;
* ``draft-but-complete`` -- every header draft, the tasks complete (at least
  one milestone and every one ``[DONE]``, or no milestone and at least one
  checkbox with every one ticked) and the criteria complete (at least one
  declared and every one ticked);
* ``settled-but-empty`` -- every header settled, no milestone ``[DONE]``, no
  checkbox ticked, no criterion ticked.

The CHANGELOG and workflow columns enter no finding (DEC-RDS-007): an entry
naming a package exists for one package in five, and a stage no workflow runs
by name is a fact about the workflows, which ``make stage-citations``
reports. A package whose evidence is partial is listed and is not a finding.

Why the header is read anchored, comment-blind and not through
``parse_spec`` (DEC-RDS-014): ``parse_spec``'s ``STATUS`` is unanchored and
searched over the raw text, so the first ``**Status:**`` anywhere -- in a
waiver, in prose, in a code example -- decides, upper-cased. So every HTML
comment is blanked first, with ``openspec_graph``'s own
``blank_html_comments``, newlines kept; the header block is the lines before
the first ``## `` heading of what is left; and the header is a line that
begins ``> **Status:** ``, its word kept as written. A proposal's status line
is read the same way. Verification lines are read through ``parse_spec``,
because they are what the rules read (DEC-RDS-009).
"""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ReportError, logger, repo_root, workflow_stages

sys.path.insert(0, str(repo_root()))

from openspec_graph import detect
from openspec_graph.parse import MAKE_REF, SpecReadError, parse_spec
from openspec_graph.parse_semantics import blank_html_comments

#: The spec header vocabulary, and the one place its words are written: the
#: follow-up package `settle-package-status-headers` amends it here if the
#: vocabulary gains a value meaning "shipped" (R-RDS-11, R-RDS-22).
VOCABULARY = {"DRAFT": "draft", "APPROVED": "settled"}

#: A proposal's own status line, in its own shape (``> **Status: proposed.**``).
PROPOSAL_VOCABULARY = {"proposed": "draft", "implemented": "settled"}

DRAFT, SETTLED = "draft", "settled"

#: The findings, in the order a package's one finding is chosen.
FINDINGS = ("header-unrecognised", "headers-disagree", "draft-but-complete", "settled-but-empty")

CHANGES = Path("openspec") / "changes"

#: The status word, as written: letters, digits, ``_`` and ``-`` -- so
#: ``in-review``, ``proposed_v2`` and ``DRAFT_2`` are each read whole and
#: judged against the vocabulary, never truncated to a word in it or missed.
_STATUS_WORD = r"([\w-]+)"
HEADER_STATUS = re.compile(r"^> \*\*Status:\*\* " + _STATUS_WORD, re.MULTILINE)
PROPOSAL_STATUS = re.compile(r"^> \*\*Status: " + _STATUS_WORD + r"\.?\*\*", re.MULTILINE)

_CRITERION = re.compile(r"^- \[([ xX])\] \*\*AC-", re.MULTILINE)
_MILESTONE = re.compile(r"^## Milestone\b.*$", re.MULTILINE)
_CHECKBOX = re.compile(r"^\s*[-*] \[([ xX])\]", re.MULTILINE)
_CHANGELOG_SECTION = re.compile(r"^## \[(?P<section>[^\]]+)\]")
_CHANGELOG_HEADING = re.compile(r"^### .*\(`(?P<package>[A-Za-z0-9._-]+)`\)\s*$")
_CHANGELOG_BULLET = re.compile(r"^- \*\*`(?P<package>[A-Za-z0-9._-]+)`\.?\*\*")


def header_block(text: str) -> str:
    """The lines before the first ``## `` heading, after every HTML comment is
    blanked with newlines kept -- so a ``## `` line inside a comment cannot
    end the block early, and no line of a comment can be the header."""
    lines: list[str] = []
    for line in blank_html_comments(text).splitlines():
        if line.startswith("## "):
            break
        lines.append(line)
    return "\n".join(lines)


def read_header(text: str) -> str | None:
    """A spec's ``Status`` word as written, or ``None`` when it has no header."""
    match = HEADER_STATUS.search(header_block(text))
    return match.group(1) if match else None


def read_proposal_status(text: str) -> str | None:
    """A proposal's status word as written, or ``None`` when it has no line."""
    match = PROPOSAL_STATUS.search(header_block(text))
    return match.group(1) if match else None


@dataclasses.dataclass(frozen=True)
class PackageRow:
    """Every column of one package's row (R-RDS-10)."""

    name: str
    spec_headers: tuple[str | None, ...]
    proposal_status: str | None
    criteria_ticked: int
    criteria_declared: int
    milestones_done: int
    milestones_declared: int
    boxes_done: int
    boxes_declared: int
    changelog_sections: tuple[str, ...]
    unrun_stages: tuple[str, ...]

    def headers_cell(self) -> str:
        """Each ``spec.md``'s ``Status`` word, then the proposal's status line."""
        if not self.spec_headers:
            cell = "no spec.md"
        else:
            cell = "spec " + ", ".join(word or "(none)" for word in self.spec_headers)
        if self.proposal_status is not None:
            cell += f"; proposal {self.proposal_status}"
        return cell

    def tasks_cell(self) -> str:
        """Milestones ``[DONE]`` of declared, else task boxes ticked of all, else
        "none recorded"."""
        if self.milestones_declared:
            return f"milestones {self.milestones_done}/{self.milestones_declared}"
        if self.boxes_declared:
            return f"tasks {self.boxes_done}/{self.boxes_declared}"
        return "none recorded"


def _read(path: Path, *, replace: bool = False) -> str | None:
    """``path``'s text, or ``None`` when it does not exist; a failure to read
    or decode is a ``ReportError`` naming the file."""
    if not path.exists():
        return None
    # is_file() before any open: a FIFO passes exists(), and open() on one
    # blocks until a writer appears (the hazard openspec_graph/repo_io.py
    # guards for detect).
    if not path.is_file():
        raise ReportError(f"cannot read {path}: not a regular file")
    try:
        if replace:
            return path.read_text(encoding="utf-8-sig", errors="replace")
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"cannot read {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ReportError(f"cannot decode {path} as UTF-8: {exc}") from exc


def packages(root: Path) -> tuple[Path, ...]:
    """``detect.profile(root).change_dirs``; an absent or empty
    ``openspec/changes/`` is a ``ReportError``, because a report over no
    package is not a clean report (DEC-RDS-006)."""
    changes = root / CHANGES
    if not changes.is_dir():
        raise ReportError(f"no {CHANGES.as_posix()}/ directory under {root}")
    found = detect.profile(root).change_dirs
    if not found:
        raise ReportError(f"{changes} holds no change package")
    return found


def changelog_entries(text: str) -> dict[str, list[str]]:
    """``{package: [section, ...]}`` for every entry naming a package, in the
    two shapes; any other mention is not an entry."""
    entries: dict[str, list[str]] = {}
    section = ""
    for line in text.splitlines():
        heading = _CHANGELOG_SECTION.match(line)
        if heading:
            section = heading.group("section")
            continue
        entry = _CHANGELOG_HEADING.match(line) or _CHANGELOG_BULLET.match(line)
        if entry:
            sections = entries.setdefault(entry.group("package"), [])
            if section not in sections:
                sections.append(section)
    return entries


def _counts(pattern: re.Pattern[str], text: str) -> tuple[int, int]:
    marks = pattern.findall(text)
    return sum(1 for mark in marks if mark in "xX"), len(marks)


def read_package(
    path: Path, dialect: str, runs: set[str], changelog: dict[str, list[str]]
) -> PackageRow:
    """One package's row. ``runs`` is every stage some scanned workflow invokes."""
    headers: list[str | None] = []
    ticked = declared = 0
    cited: set[str] = set()
    for spec_path in sorted(path.glob("specs/*/spec.md")):
        # As `parse_spec` reads it, so the report never refuses a spec the gate accepts.
        text = _read(spec_path, replace=True) or ""
        headers.append(read_header(text))
        more_ticked, more_declared = _counts(_CRITERION, text)
        ticked, declared = ticked + more_ticked, declared + more_declared
        try:
            spec = parse_spec(spec_path, dialect)
        except SpecReadError as exc:
            raise ReportError(f"cannot read {spec_path}: {exc}") from exc
        cited |= {stage for crit in spec.criteria for stage in MAKE_REF.findall(crit.verified_by)}
    proposal = _read(path / "proposal.md")
    tasks = _read(path / "tasks.md") or ""
    milestones = _MILESTONE.findall(tasks)
    boxes_done, boxes_declared = _counts(_CHECKBOX, tasks)
    return PackageRow(
        name=path.name,
        spec_headers=tuple(headers),
        proposal_status=read_proposal_status(proposal) if proposal is not None else None,
        criteria_ticked=ticked,
        criteria_declared=declared,
        milestones_done=sum(1 for heading in milestones if "[DONE]" in heading),
        milestones_declared=len(milestones),
        boxes_done=boxes_done,
        boxes_declared=boxes_declared,
        changelog_sections=tuple(changelog.get(path.name, ())),
        unrun_stages=tuple(sorted(cited - runs)),
    )


def finding(row: PackageRow) -> str | None:
    """The package's one finding, in R-RDS-11's order, or ``None``."""
    proposal_word = row.proposal_status
    if (
        not row.spec_headers
        or any(word is None or word not in VOCABULARY for word in row.spec_headers)
        or (proposal_word is not None and proposal_word not in PROPOSAL_VOCABULARY)
    ):
        return "header-unrecognised"
    kinds = {VOCABULARY[word] for word in row.spec_headers if word is not None}
    if proposal_word is not None:
        kinds.add(PROPOSAL_VOCABULARY[proposal_word])
    if kinds == {DRAFT, SETTLED}:
        return "headers-disagree"
    if row.milestones_declared:
        tasks_complete = row.milestones_done == row.milestones_declared
    else:
        tasks_complete = row.boxes_declared > 0 and row.boxes_done == row.boxes_declared
    criteria_complete = row.criteria_declared > 0 and row.criteria_ticked == row.criteria_declared
    if kinds == {DRAFT} and tasks_complete and criteria_complete:
        return "draft-but-complete"
    nothing_done = row.milestones_done == 0 and row.boxes_done == 0
    if kinds == {SETTLED} and nothing_done and row.criteria_ticked == 0:
        return "settled-but-empty"
    return None


def build_rows(root: Path) -> list[PackageRow]:
    """Every package's row, sorted by name."""
    found = packages(root)
    dialect = detect.profile(root).dialect
    runs: set[str] = set()
    for stages in workflow_stages(root, stage_ref=MAKE_REF).values():
        runs |= stages
    changelog = changelog_entries(_read(root / "CHANGELOG.md") or "")
    rows = [read_package(path, dialect, runs, changelog) for path in found]
    for row in rows:
        logger.debug("spec-status: %s -> %s", row.name, finding(row) or "no finding")
    return sorted(rows, key=lambda row: row.name)


def render(rows: Sequence[PackageRow]) -> tuple[str, int]:
    """The text report and the number of findings."""
    titles = ("package", "headers", "criteria", "tasks", "changelog", "unrun stages", "finding")
    table = [
        (
            row.name,
            row.headers_cell(),
            f"{row.criteria_ticked}/{row.criteria_declared}",
            row.tasks_cell(),
            ", ".join(row.changelog_sections) or "-",
            ", ".join(row.unrun_stages) or "-",
            finding(row) or "-",
        )
        for row in rows
    ]
    widths = [max(len(cells[i]) for cells in (titles, *table)) for i in range(len(titles))]

    def line(cells: Sequence[str]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths, strict=True)).rstrip()

    lines = [line(titles), line(["-" * width for width in widths])]
    lines += [line(cells) for cells in table]
    found = [cells[-1] for cells in table if cells[-1] != "-"]
    by_kind = ", ".join(f"{found.count(kind)} {kind}" for kind in FINDINGS)
    summary = f"{len(rows)} package(s); {len(found)} finding(s): {by_kind}"
    if not found:
        summary += "; no package's Status header disagrees with its evidence"
    lines += ["", summary]
    return "\n".join(lines) + "\n", len(found)


def main(argv: Sequence[str]) -> int:
    """Print the report for ``--root`` (default: this repository) and return
    its exit code: 0 no finding, 1 a finding, 2 could not run."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--root", default=None, help="repository to report on (default: this repository)"
    )
    args = parser.parse_args(list(argv[1:]))
    root = (Path(args.root) if args.root is not None else repo_root()).resolve()
    if not root.is_dir():
        print(f"ERROR not a directory: {root}", file=sys.stderr)
        return 2
    try:
        text, findings = render(build_rows(root))
    except (ReportError, SpecReadError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError) as exc:
        # A read this script does not make itself -- the profile's own -- is
        # still could-not-run, never a traceback.
        print(f"ERROR cannot read {getattr(exc, 'filename', None) or root}: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
