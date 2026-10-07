"""``tools/stage_citations.py``: the two citation counts, and who runs each stage.

The tool exists because a planning document counted the wrong one: G004 reads
every backticked ``make <stage>`` in a spec, W001 reads only a criterion's
verification line, and ``docs/peer-review-2026-10.md`` N2 first reported the
whole-spec count as if witness mode would check it. Every test here pins the
distinction, or the conditions under which the report refuses to run.

Behaviour is asserted in-process against ``main(argv)`` and the module's
functions (``support.run_tool_main``/``load_tool``) so coverage sees it; the
``python tools/stage_citations.py`` path is covered once, with every other
script, by ``test_gate_script_is_runnable_as_a_script``.
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import pytest

from openspec_graph import detect
from tests.graft_support import GOOD_SPECKIT
from tests.support import load_tool, run_tool_main, write_spec, write_speckit_spec

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = "stage_citations.py"

sc = load_tool("stage_citations", TOOL)

# A spec that mentions `docs` in prose only, and verifies with `test` and `lint`.
SPEC_A = textwrap.dedent(
    """\
    # Spec: A

    > **Status:** DRAFT

    ## Problem Statement

    The docs stage, `make docs`, is mentioned here and never cited as proof.

    ## Requirements

    - R-STA-1: The system MUST do a thing.

    ## Acceptance Criteria

    - [ ] **AC-STA-1:** The thing happens. (R-STA-1)
      _Verified by:_ stage: `make test`

    - [ ] **AC-STA-2 (non-success):** A bad input is rejected with exit 2. (R-STA-1)
      _Verified by:_ stage: `make lint`
    """
)

# A second spec that verifies with `test` only, so `test` counts twice.
SPEC_B = SPEC_A.replace("`make lint`", "`make test`").replace(
    "The docs stage, `make docs`, is mentioned here and never cited as proof.", "Nothing else."
)

CI_YML = textwrap.dedent(
    """\
    name: CI
    # make docs is explained in this comment and must not count as running it
    jobs:
      a:
        steps:
          - run: choco install make -y
          - run: make test
          - run: cmake build && remake lint
    """
)
RELEASE_YML = "jobs:\n  r:\n    steps:\n      - run: make lint\n"


@pytest.fixture
def labelled(tmp_path: Path) -> Path:
    write_spec(tmp_path, "c-a", "cap-a", SPEC_A)
    write_spec(tmp_path, "c-b", "cap-b", SPEC_B)
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(CI_YML, encoding="utf-8")
    (workflows / "release.yaml").write_text(RELEASE_YML, encoding="utf-8")
    (workflows / "notes.txt").write_text("make docs\n", encoding="utf-8")
    return tmp_path


def _rows(root: Path, only: tuple[str, ...] = ()) -> dict[str, object]:
    count, rows = sc.build_rows(root, only)
    return {"specs": count, **{row.stage: (row.mentioned, row.verified, row.workflows) for row in rows}}


def test_mentions_and_verification_lines_are_counted_separately(labelled: Path) -> None:
    """The distinction the tool exists for: `docs` is mentioned, never verified."""
    assert _rows(labelled) == {
        "specs": 2,
        "docs": (1, 0, ()),
        "lint": (1, 1, ("release.yaml",)),
        "test": (2, 2, ("ci.yml",)),
    }


def test_a_comment_a_flag_and_a_lookalike_command_are_not_invocations() -> None:
    """Non-success: none of these credits a workflow with running a stage."""
    assert sc.workflow_invocations(CI_YML) == {"test"}
    assert sc.workflow_invocations("  # make test\n") == set()
    assert sc.workflow_invocations("run: make -j4\n") == set()


@pytest.mark.parametrize(
    "line",
    [
        'run: echo "make test"',
        "run: printf 'make test\\n'",
        "- name: make test",
        "run: ./notify --message make test",
        "run: true # make test",
    ],
)
def test_make_as_an_argument_or_label_is_not_an_invocation(line: str) -> None:
    """Non-success: only make in command position runs a stage. Text that
    merely contains `make test` -- printed, passed as an argument, a step's
    name, an inline comment -- would credit a workflow with a stage it never
    ran, which is the one error this report exists to avoid."""
    assert sc.workflow_invocations(line) == set()


@pytest.mark.parametrize(
    ("line", "stage"),
    [
        ("run: make test", "test"),
        ("      - run: make test", "test"),
        ("run: |\n          make test", "test"),
        ("run: >-\n          make test", "test"),
        ("run:\n          make test", "test"),
        ('run: "make test"', "test"),
        ("run: 'make test' # note", "test"),
        ("run: cd sub && make test", "test"),
        ("run: make lint; make test", "test"),
        ("run: out=$(make test)", "test"),
        ("run: echo 'a' | make test", "test"),
        ("run: CI=1 make test", "test"),
        ("run: |\n  true # a comment, not a separator\n  make test", "test"),
        ("run: |\n  echo 'spans\n  lines' && make test", "test"),
        ("run: |\n  make \\\n    test", "test"),
        ("run: |\n  true\n\n  make test", "test"),
        ("run: | # a comment after the indicator\n  make test", "test"),
        ("run: 'echo ''hi'' && make test'", "test"),
    ],
)
def test_make_in_command_position_is_an_invocation(line: str, stage: str) -> None:
    assert stage in sc.workflow_invocations(line)


@pytest.mark.parametrize(
    "text",
    [
        "run: true # && make test",
        "run: echo 'x && make test'",
        'run: echo "x; make test"',
        "name: explain; make test",
        "if: make test",
        "with:\n  args: make test\n",
        "run: |\n  # make test\n  true",
        "run: |\n  echo 'open quote && make test",
        'run: ""',
        "run: true;# && make test",
        "run: >\n  echo folded\n  make test",
    ],
)
def test_separators_inside_data_are_not_shell_syntax(text: str) -> None:
    """Non-success (review round 3): a separator inside a comment or a quoted
    string, or in a key that is not shell at all, is data. Crediting a
    workflow with a stage it never ran is the one error this report exists to
    avoid, so each of these yields nothing -- including the open quote, whose
    tail is unreadable rather than guessed at."""
    assert sc.workflow_invocations(text) == set()


def test_a_run_block_ends_where_its_indentation_does() -> None:
    """A sibling key after a block scalar, and the next step, are not part of
    the script; a second run: step is read on its own."""
    text = textwrap.dedent(
        """\
        steps:
          - run: |
              make test
            with:
              cmd: make lint
          - run: make docs-check
        """
    )
    assert sc.run_scripts(text) == ["      make test", "make docs-check"]
    assert sc.workflow_invocations(text) == {"test", "docs-check"}


def test_run_block_commands_are_scanned_but_yaml_fields_are_not() -> None:
    workflow = textwrap.dedent(
        """\
        name: explain; make docs
        jobs:
          test:
            steps:
              - name: explain; make lint
              - run: |
                  echo 'make docs'
                  make test
        """
    )
    assert sc.workflow_invocations(workflow) == {"test"}


def test_a_word_after_a_closing_subshell_is_an_argument() -> None:
    """`$(make test)` runs make; the `make lint` that follows the `)` is an
    argument to whatever that substitution produced, not a second command."""
    assert sc.workflow_invocations("run: $(make test) make lint") == {"test"}


def test_an_unreadable_workflow_exits_two_rather_than_a_traceback(
    labelled: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Non-success: same contract as an unreadable spec. Patched rather than
    chmod'd: as root, chmod 000 still reads fine."""
    original = Path.read_text

    def refuse(self: Path, *args: object, **kwargs: object) -> str:
        if self.name == "ci.yml":
            raise PermissionError(13, "Permission denied")
        return original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", refuse)
    assert run_tool_main("stage_citations", TOOL, "--root", str(labelled)) == 2
    err = capsys.readouterr().err
    assert "cannot read" in err and "ci.yml" in err


def test_only_yaml_files_under_the_workflow_directory_are_scanned(labelled: Path) -> None:
    assert set(sc.workflow_stages(labelled)) == {"ci.yml", "release.yaml"}


def test_the_workflow_filter_restricts_who_is_credited(labelled: Path) -> None:
    rows = _rows(labelled, ("ci.yml",))
    assert rows["lint"] == (1, 1, ())
    assert rows["test"] == (2, 2, ("ci.yml",))


def test_an_unknown_workflow_filter_exits_two(labelled: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Non-success: a typo'd filter must not report every stage as unrun."""
    assert run_tool_main("stage_citations", TOOL, "--root", str(labelled), "--workflow", "cy.yml") == 2
    captured = capsys.readouterr()
    assert "no such workflow" in captured.err and "cy.yml" in captured.err
    assert captured.out == ""


def test_a_tree_with_no_specs_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Non-success: no spec tree is a precondition failure, never an empty pass."""
    assert run_tool_main("stage_citations", TOOL, "--root", str(tmp_path)) == 2
    assert "no openspec/ directory" in capsys.readouterr().err


def test_a_root_that_is_not_a_directory_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "nope"
    assert run_tool_main("stage_citations", TOOL, "--root", str(missing)) == 2
    assert "not a directory" in capsys.readouterr().err


def test_a_repository_without_workflows_credits_nobody(tmp_path: Path) -> None:
    write_spec(tmp_path, "c-a", "cap-a", SPEC_A)
    assert _rows(tmp_path)["test"] == (1, 1, ())


def test_a_speckit_tree_is_read_through_the_same_discovery(tmp_path: Path) -> None:
    write_speckit_spec(tmp_path, "001-feature", GOOD_SPECKIT)
    count, _rows_list = sc.build_rows(tmp_path)
    assert count == 1


def test_the_text_summary_names_the_unrun_verification_stages(
    labelled: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_tool_main("stage_citations", TOOL, "--root", str(labelled), "--workflow", "ci.yml") == 0
    out = capsys.readouterr().out
    assert re.search(r"^docs\s+1\s+0\s+-$", out, re.MULTILINE), out
    assert out.rstrip().endswith(
        "2 spec(s); 3 stage(s) cited; 2 on a verification line; 1 of those invoked by no scanned workflow: lint"
    ), out


def test_json_is_versioned_sorted_and_byte_stable(labelled: Path, capsys: pytest.CaptureFixture[str]) -> None:
    renders = []
    for _ in range(2):
        assert run_tool_main("stage_citations", TOOL, "--root", str(labelled), "--format", "json") == 0
        renders.append(capsys.readouterr().out)
    # Bytes, not parsed equality: two renders that differ only in key order or
    # whitespace would parse equal and still break a diff-based consumer.
    assert renders[0] == renders[1]
    payload = json.loads(renders[0])
    assert payload["schema_version"] == sc.SCHEMA_VERSION
    assert payload["specs"] == 2
    assert payload["workflows_scanned"] == "all"
    assert [s["stage"] for s in payload["stages"]] == ["docs", "lint", "test"]
    assert payload["stages"][2] == {"stage": "test", "mentioned": 2, "verified": 2, "workflows": ["ci.yml"]}


def test_this_repository_report_holds_its_invariants(capsys: pytest.CaptureFixture[str]) -> None:
    """Regression against the live tree, by invariant rather than by snapshot:
    a count pinned here would break every time a change package lands."""
    assert run_tool_main("stage_citations", TOOL, "--root", str(REPO_ROOT), "--format", "json") == 0
    payload = json.loads(capsys.readouterr().out)
    # The package's own makefile parser, which is what G004 checks against --
    # a hand-written `^[a-z_-]+:` regex here once missed `e2e-live`.
    targets = set(detect.profile(REPO_ROOT).make_targets)
    assert payload["specs"] > 0
    for row in payload["stages"]:
        assert row["verified"] <= row["mentioned"], row
        assert row["stage"] in targets, f"{row['stage']} is cited but not a Makefile target"
    by_stage = {row["stage"]: row for row in payload["stages"]}
    assert "ci.yml" in by_stage["test"]["workflows"]


def test_an_unreadable_spec_exits_two_rather_than_a_traceback(
    labelled: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Non-success: the CLI refuses an unreadable spec with exit 2, and so does
    the report that counts specs; a directory in a spec's place is the
    portable way to make one unreadable."""
    blocker = labelled / "openspec" / "changes" / "c-dir" / "specs" / "cap" / "spec.md"
    blocker.mkdir(parents=True)
    assert run_tool_main("stage_citations", TOOL, "--root", str(labelled)) == 2
    err = capsys.readouterr().err
    assert "cannot read" in err and "spec.md" in err
