"""``tools/spec_status.py``: each change package's Status header beside its evidence.

``report-dead-code-and-spec-status`` (R-RDS-9 to R-RDS-12, R-RDS-23). One row
per package of ``detect.profile(root).change_dirs``: the ``Status`` header of
each ``spec.md`` and the proposal's status line, criteria ticked of declared,
milestones ``[DONE]`` (else task boxes), the CHANGELOG sections holding an
entry naming it, and the verification-line stages no scanned workflow runs.
A package carries at most one of four findings, decided from the headers, the
tasks and the criteria alone. Exit 0 no finding, 1 a finding, 2 could not run.

Behaviour is asserted in-process through ``load_tool`` against roots planted
under ``tmp_path``: every ``spec.md`` through ``support.write_spec``, and
``proposal.md``, ``tasks.md``, ``CHANGELOG.md`` and workflows written
directly, since they are not spec paths (DEC-RDS-013). Two tests read this
repository: the header-reader agreement test and the real-tree run. The
``python tools/spec_status.py`` path is covered by
``test_gate_script_is_runnable_as_a_script``.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from openspec_graph import detect
from openspec_graph.parse import parse_spec
from tests.support import load_tool, supports_symlinks, write_spec

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = "spec_status.py"
THIS_PACKAGE = "report-dead-code-and-spec-status"

#: Loaded at collection, so the tools logger's handler is bound to a stream
#: that outlives every test (see ``tests/test_dead_code.py``).
_COMMON = load_tool("common_spec_status", "_common.py")


def _tool() -> ModuleType:
    return load_tool("spec_status", TOOL)


def _spec(
    header: str = "> **Status:** DRAFT",
    *,
    ticked: int = 1,
    declared: int = 1,
    stage: str = "test",
    body: str = "",
) -> str:
    """A planted harness spec: ``header`` in its header block, ``declared``
    criteria of which the first ``ticked`` are ticked, each verified by
    ``make <stage>``, and ``body`` after them."""
    criteria = "".join(
        f"- [{'x' if index < ticked else ' '}] **AC-PL-{index + 1}:** It holds. (R-PL-1)\n"
        f"  _Verified by:_ stage: `make {stage}`\n\n"
        for index in range(declared)
    )
    return (
        "# Spec: Planted\n\n> **Change:** `planted`\n"
        f"{header}\n\n---\n\n## Requirements\n\n- R-PL-1: The system MUST hold.\n\n"
        f"## Acceptance Criteria\n\n{criteria}{body}"
    )


def _tasks(milestones: Sequence[bool] = (), boxes: Sequence[bool] = ()) -> str:
    lines = ["# Tasks: planted", ""]
    for index, done in enumerate(milestones):
        lines += [f"## Milestone {index} — Step{' [DONE]' if done else ''}", "", "- Do it.", ""]
    lines += [f"- [{'x' if done else ' '}] Do a thing." for done in boxes]
    return "\n".join(lines) + "\n"


def _proposal(word: str) -> str:
    return f"# Change: Planted\n\n> **Status: {word}.** Planted.\n\n## Why\n\nBecause.\n"


def _package(
    root: Path,
    name: str,
    *,
    spec: str | None = None,
    tasks: str | None = None,
    proposal: str | None = None,
) -> Path:
    """A planted package; ``spec`` goes through ``write_spec``."""
    if spec is not None:
        write_spec(root, name, "cap", spec)
    package = root / "openspec" / "changes" / name
    package.mkdir(parents=True, exist_ok=True)
    if tasks is not None:
        (package / "tasks.md").write_text(tasks, encoding="utf-8")
    if proposal is not None:
        (package / "proposal.md").write_text(proposal, encoding="utf-8")
    return package


def _rows(root: Path) -> dict[str, Any]:
    tool = _tool()
    return {row.name: row for row in tool.build_rows(root)}


def _finding(root: Path, name: str) -> str | None:
    tool = _tool()
    found: str | None = tool.finding(_rows(root)[name])
    return found


def _main(root: Path) -> int:
    return int(_tool().main([TOOL, "--root", str(root)]))


# --- the four findings (R-RDS-11) ---------------------------------------------


def test_a_draft_package_whose_tasks_and_criteria_are_complete_is_a_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-11: `DRAFT`, every milestone `[DONE]`, every criterion ticked."""
    _package(tmp_path, "done", spec=_spec(ticked=2, declared=2), tasks=_tasks([True, True]))
    assert _finding(tmp_path, "done") == "draft-but-complete"
    assert _main(tmp_path) == 1
    out = capsys.readouterr().out
    row = next(line for line in out.splitlines() if line.startswith("done "))
    assert row.rstrip().endswith("draft-but-complete")
    assert "2/2" in row and "milestones 2/2" in row
    assert "1 draft-but-complete" in out.splitlines()[-1]


def test_task_checkboxes_count_when_a_package_has_no_milestone_headings(
    tmp_path: Path,
) -> None:
    """R-RDS-10, R-RDS-11: no milestone heading, so the task boxes decide."""
    _package(tmp_path, "boxes-done", spec=_spec(), tasks=_tasks(boxes=[True, True]))
    _package(tmp_path, "boxes-open", spec=_spec(), tasks=_tasks(boxes=[True, False]))
    rows = _rows(tmp_path)
    assert (rows["boxes-done"].boxes_done, rows["boxes-done"].boxes_declared) == (2, 2)
    assert _finding(tmp_path, "boxes-done") == "draft-but-complete"
    assert _finding(tmp_path, "boxes-open") is None


def test_a_settled_package_with_no_task_done_and_no_criterion_ticked_is_a_finding(
    tmp_path: Path,
) -> None:
    """R-RDS-11: `APPROVED`, no milestone done, no box ticked, no criterion ticked."""
    _package(
        tmp_path, "empty",
        spec=_spec("> **Status:** APPROVED", ticked=0, declared=2), tasks=_tasks([False, False]),
    )
    _package(
        tmp_path, "settled-and-done",
        spec=_spec("> **Status:** APPROVED", ticked=2, declared=2), tasks=_tasks([True]),
    )
    assert _finding(tmp_path, "empty") == "settled-but-empty"
    assert _finding(tmp_path, "settled-and-done") is None


def test_a_proposal_status_that_disagrees_with_its_spec_header_is_a_finding(
    tmp_path: Path,
) -> None:
    """R-RDS-11: a proposal's `proposed` against a spec's `APPROVED`."""
    _package(
        tmp_path, "split",
        spec=_spec("> **Status:** APPROVED", ticked=0), tasks=_tasks([False]),
        proposal=_proposal("proposed"),
    )
    _package(tmp_path, "agreed", spec=_spec(ticked=0), proposal=_proposal("proposed"))
    assert _rows(tmp_path)["split"].proposal_status == "proposed"
    assert _finding(tmp_path, "split") == "headers-disagree"
    assert _finding(tmp_path, "agreed") is None


@pytest.mark.parametrize(
    ("spec", "proposal"),
    [
        (_spec(""), None),
        (_spec("> **Status:** IMPLEMENTED"), None),
        (_spec("> **Status:** draft"), None),
        (_spec(), _proposal("shipped")),
        (None, None),
    ],
    ids=["no-header", "IMPLEMENTED", "lower-case-draft", "proposal-word", "no-spec"],
)
def test_a_missing_or_unrecognised_status_header_is_a_finding(
    tmp_path: Path, spec: str | None, proposal: str | None
) -> None:
    """R-RDS-11, DEC-RDS-008: words match case-sensitively, and `IMPLEMENTED`
    stays unrecognised until the follow-up amends `VOCABULARY`."""
    _package(tmp_path, "odd", spec=spec, tasks=_tasks([True]), proposal=proposal)
    assert _finding(tmp_path, "odd") == "header-unrecognised"
    assert _main(tmp_path) == 1


# --- the header reader (R-RDS-23, DEC-RDS-014) --------------------------------

_WAIVER_LINE = "<!-- specgraph:allow G002 quoted here: **Status:** APPROVED -->"


@pytest.mark.parametrize(
    ("spec", "expected_header", "expected_finding"),
    [
        (_spec(f"{_WAIVER_LINE}\n> **Status:** DRAFT", ticked=0), "DRAFT", None),
        (_spec("This draft says **Status:** APPROVED in prose."), None, "header-unrecognised"),
        (
            _spec("", body="## Example\n\n```\n> **Status:** DRAFT\n```\n"),
            None,
            "header-unrecognised",
        ),
    ],
    ids=["waiver-above-the-header", "phrase-in-prose", "phrase-in-a-code-example"],
)
def test_a_status_line_outside_the_header_block_is_never_the_header(
    tmp_path: Path, spec: str, expected_header: str | None, expected_finding: str | None
) -> None:
    """R-RDS-23: only a line that begins `> **Status:** `, in the header block,
    is the header -- never a waiver, prose, or a code example."""
    _package(tmp_path, "planted", spec=spec, tasks=_tasks([False]))
    assert _rows(tmp_path)["planted"].spec_headers == (expected_header,)
    assert _finding(tmp_path, "planted") == expected_finding


@pytest.mark.parametrize(
    ("spec", "proposal", "column", "expected"),
    [
        (
            _spec(
                "<!-- specgraph:allow G002 the old header read\n"
                "> **Status:** APPROVED\nand is kept here -->\n> **Status:** DRAFT",
                ticked=0,
            ),
            None, "spec_headers", ("DRAFT",),
        ),
        (
            _spec("<!--\n> **Status:** APPROVED\n-->\n> **Status:** DRAFT", ticked=0),
            None, "spec_headers", ("DRAFT",),
        ),
        (
            _spec(ticked=0),
            (
                "# Change: Planted\n\n<!--\n> **Status: implemented.**\n-->\n"
                "> **Status: proposed.** Planted.\n\n## Why\n\nBecause.\n"
            ),
            "proposal_status", "proposed",
        ),
    ],
    ids=["multi-line-waiver", "commented-out-header", "commented-out-proposal-line"],
)
def test_a_status_line_inside_a_comment_is_never_the_header(
    tmp_path: Path, spec: str, proposal: str | None, column: str, expected: object
) -> None:
    """R-RDS-23: every HTML comment is blanked, newlines kept, before the
    header block is cut and matched -- through `blank_html_comments`."""
    _package(tmp_path, "planted", spec=spec, tasks=_tasks([False]), proposal=proposal)
    assert getattr(_rows(tmp_path)["planted"], column) == expected
    assert _finding(tmp_path, "planted") is None


def test_the_header_reader_agrees_with_parse_spec_on_every_uncommented_real_header() -> None:
    """R-RDS-23: where the anchored reader finds a header and the header block
    holds no comment, its word, upper-cased, is `parse_spec`'s. A spec
    outside that scope is skipped, never failed: header form is the report's
    finding, not this test's."""
    tool = _tool()
    dialect = detect.profile(REPO_ROOT).dialect
    compared: list[str] = []
    for path in sorted((REPO_ROOT / "openspec" / "changes").glob("*/specs/*/spec.md")):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        block = text.split("\n## ", 1)[0]
        header = tool.read_header(text)
        if header is None or "<!--" in block:
            continue
        assert header.upper() == parse_spec(path, dialect).status, path
        compared.append(path.parent.parent.parent.name)
    assert compared, "no real spec was compared: the scope is empty"
    assert THIS_PACKAGE in compared


# --- the packages and the columns (R-RDS-10) ----------------------------------


@pytest.mark.skipif(not supports_symlinks(), reason="this filesystem cannot create a symlink")
def test_a_symlinked_alias_of_a_package_is_one_row(tmp_path: Path) -> None:
    """R-RDS-10: the packages are `detect.profile(root).change_dirs`, which
    count an alias once by real-path identity."""
    real = _package(tmp_path, "real", spec=_spec(), tasks=_tasks([False]))
    (real.parent / "alias").symlink_to(real, target_is_directory=True)
    assert len(_rows(tmp_path)) == 1


def test_partial_evidence_is_listed_and_is_not_a_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-11, DEC-RDS-007: a `DRAFT` package with every criterion ticked and
    a milestone open, and an `APPROVED` one with milestones done and no
    criterion ticked, are rows and not findings."""
    _package(tmp_path, "draft-open", spec=_spec(ticked=1), tasks=_tasks([True, False]))
    _package(
        tmp_path, "approved-unticked",
        spec=_spec("> **Status:** APPROVED", ticked=0), tasks=_tasks([True, True]),
    )
    assert _main(tmp_path) == 0
    out = capsys.readouterr().out.splitlines()
    assert any(line.startswith("draft-open ") for line in out)
    assert any(line.startswith("approved-unticked ") for line in out)
    assert "no package's Status header disagrees with its evidence" in out[-1]


def test_a_changelog_entry_is_read_in_both_shapes_and_a_mention_is_not_an_entry(
    tmp_path: Path,
) -> None:
    """R-RDS-10: a heading ending in the backticked name in parentheses, or a
    bullet led by the bold backticked name, is an entry; a mention is not,
    and a section holding two entries for one package is listed once."""
    for name in ("by-heading", "by-bullet", "mentioned"):
        _package(tmp_path, name, spec=_spec(), tasks=_tasks([False]))
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Added — things\n\n"
        "- **`by-bullet`.** It landed.\n- **`by-bullet`.** And grew.\n"
        "- Three packages, `mentioned` among them, none implemented.\n\n"
        "## [0.2.0] - 2026-01-01\n\n### Added — a feature (`by-heading`)\n\nText.\n",
        encoding="utf-8",
    )
    rows = _rows(tmp_path)
    assert rows["by-bullet"].changelog_sections == ("Unreleased",)
    assert rows["by-heading"].changelog_sections == ("0.2.0",)
    assert rows["mentioned"].changelog_sections == ()


def test_the_workflow_column_names_verification_stages_no_workflow_runs(
    tmp_path: Path,
) -> None:
    """R-RDS-9, R-RDS-10: through `_common.workflow_stages` with `MAKE_REF`, a
    stage a workflow runs in command position is omitted; one it only
    mentions, or none runs, is named."""
    _package(tmp_path, "run", spec=_spec(stage="test"), tasks=_tasks([False]))
    _package(tmp_path, "unrun", spec=_spec(stage="lint"), tasks=_tasks([False]))
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n  test:\n    steps:\n      - name: make lint\n        run: make test\n",
        encoding="utf-8",
    )
    rows = _rows(tmp_path)
    assert rows["run"].unrun_stages == ()
    assert rows["unrun"].unrun_stages == ("lint",)
    assert _finding(tmp_path, "unrun") is None


def test_absent_changelog_and_workflows_are_empty_columns_not_failures(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-12: an absent `CHANGELOG.md`, `proposal.md`, `tasks.md` or
    workflow directory reads as an empty column."""
    _package(tmp_path, "bare", spec=_spec(ticked=0))
    row = _rows(tmp_path)["bare"]
    assert (row.changelog_sections, row.proposal_status) == ((), None)
    assert row.unrun_stages == ("test",)
    assert _main(tmp_path) == 0
    line = next(item for item in capsys.readouterr().out.splitlines() if item.startswith("bare "))
    assert "none recorded" in line


# --- could not run (R-RDS-12) -------------------------------------------------

Spoiler = Callable[[Path, pytest.MonkeyPatch], None]


def _refuse_reading(name: str) -> Spoiler:
    """An injected `PermissionError` on files called ``name``, as
    `tests/test_stage_citations.py` does: as root, a mode of 000 still reads."""

    def spoil(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original = Path.read_text

        def refuse(self: Path, *args: Any, **kwargs: Any) -> str:
            if self.name == name:
                raise PermissionError(13, "Permission denied")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", refuse)

    return spoil


def _undecodable(relative: str) -> Spoiler:
    def spoil(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (root / relative).write_bytes(b"# Planted\n\xff\n")

    return spoil


def _no_changes_directory(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for path in sorted((root / "openspec").rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()


def _no_package(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _no_changes_directory(root, monkeypatch)
    (root / "openspec" / "changes").mkdir()


_CANNOT_RUN: dict[str, tuple[Spoiler, str]] = {
    "no-changes-directory": (_no_changes_directory, "openspec/changes"),
    "no-package": (_no_package, "holds no change package"),
    "undecodable-proposal": (_undecodable("openspec/changes/p/proposal.md"), "proposal.md"),
    "undecodable-tasks": (_undecodable("openspec/changes/p/tasks.md"), "tasks.md"),
    "undecodable-changelog": (_undecodable("CHANGELOG.md"), "CHANGELOG.md"),
    "unreadable-spec": (_refuse_reading("spec.md"), "spec.md"),
    "unreadable-tasks": (_refuse_reading("tasks.md"), "tasks.md"),
}


@pytest.mark.parametrize("case", sorted(_CANNOT_RUN))
def test_spec_status_exits_two_when_it_cannot_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    """R-RDS-12, DEC-RDS-006: exit 2 with the file or directory named and no
    traceback. No `spec.md` decode case: it is read as `parse_spec` reads
    it, with undecodable bytes replaced (DEC-RDS-013)."""
    _package(tmp_path, "p", spec=_spec(), tasks=_tasks([False]), proposal=_proposal("proposed"))
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    spoil, expected = _CANNOT_RUN[case]
    spoil(tmp_path, monkeypatch)
    assert _main(tmp_path) == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert expected in err, err


# --- imports and the real tree ------------------------------------------------


def test_spec_status_imports_only_the_standard_library_common_and_openspec_graph() -> None:
    """C-RDS-8, DEC-RDS-009: no third-party module, and no sibling but `_common`."""
    roots: set[str] = set()
    source = (REPO_ROOT / "tools" / TOOL).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"__future__", "_common", "openspec_graph"}
    assert {"_common", "openspec_graph"} <= roots
    assert roots - allowed == set()


def test_spec_status_runs_over_this_repository(capsys: pytest.CaptureFixture[str]) -> None:
    """R-RDS-10: one row per `detect.profile(REPO_ROOT).change_dirs` entry, this
    package's own among them. It pins no count (C-RDS-4)."""
    code = _main(REPO_ROOT)
    assert code in (0, 1)
    out = capsys.readouterr().out.splitlines()
    names = [path.name for path in detect.profile(REPO_ROOT).change_dirs]
    rows = [line for line in out if line.split(" ", 1)[0] in names]
    assert len(rows) == len(names)
    assert any(line.startswith(f"{THIS_PACKAGE} ") for line in rows)
