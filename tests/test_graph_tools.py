"""``tools/diff_spec_graph.py`` and ``tools/render_mermaid.py``.

Moved from ``tests/test_ci_hardening.py`` by ``shape-the-test-suite`` (R-TSS-2).
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from openspec_graph import detect
from openspec_graph import graph as graph_module
from tests.support import (
    captured_logger,
    run_tool_main,
)
from tests.support import write_spec as _write_spec

pytestmark = pytest.mark.integration

# --- AC-CH-5 / AC-CH-6: graph-diff fails on regressions, passes on fixes ----


MAKEFILE = textwrap.dedent(
    """\
    .PHONY: test
    test:
    \tpytest
    """
)

PYPROJECT = textwrap.dedent(
    """\
    [project]
    name = "demo"
    [tool.coverage.report]
    fail_under = 90
    """
)

GOOD_HARNESS = textwrap.dedent(
    """\
    # Spec: Demo

    > **Status:** DRAFT

    ## Problem Statement

    **Evidence:** `mod.py::run` does X.

    ## Requirements

    - R-DMO-1: The system MUST do a thing.

    ## Acceptance Criteria

    - [ ] **AC-DMO-1:** The thing is done. (R-DMO-1)
      _Verified by:_ `pytest -k test_thing` · stage: `make test`

    - [ ] **AC-DMO-2 (non-success):** The thing is refused when invalid. (R-DMO-1)
      _Verified by:_ `pytest -k test_refused` · stage: `make test`

    ## Validation Matrix

    | Stage | Make Target | Pass Criteria |
    |---|---|---|
    | Focused | `make test` | AC-DMO-1..2 |
    """
)

@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    return tmp_path

def _graph_json(repo: Path) -> dict:
    return graph_module.build_graph(detect.profile(repo))

def _diff(base: dict, head: dict) -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        bp = Path(d) / "base.json"
        hp = Path(d) / "head.json"
        bp.write_text(json.dumps(base))
        hp.write_text(json.dumps(head))
        # Absolute paths, so no cwd is needed -- unlike the two coverage gates,
        # this script reads nothing relative to where it was started.
        return run_tool_main("diff_spec_graph", "diff_spec_graph.py", str(bp), str(hp))

def test_graph_diff_passes_when_clean(repo: Path) -> None:
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    head = json.loads(json.dumps(base))
    assert _diff(base, head) == 0

def test_graph_diff_fails_on_new_broken_edges(repo: Path) -> None:
    # base: clean spec
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    # head: same spec but the AC cites a stage the repo lacks -> broken edge
    bad = GOOD_HARNESS.replace("make test", "make nope")
    _write_spec(repo, "c1", "cap1", bad)
    head = _graph_json(repo)
    assert head["broken_links"] > base["broken_links"]
    assert _diff(base, head) == 1

def test_graph_diff_fails_on_new_orphan(repo: Path) -> None:
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    # head: add an orphan requirement nothing verifies
    orphan_body = GOOD_HARNESS.replace(
        "- R-DMO-1: The system MUST do a thing.",
        "- R-DMO-1: The system MUST do a thing.\n- R-DMO-9: MUST do an untested thing.",
    )
    _write_spec(repo, "c1", "cap1", orphan_body)
    head = _graph_json(repo)
    assert "R-DMO-9" in {n["id"] for n in head["nodes"] if n.get("orphan")}
    assert _diff(base, head) == 1

def test_graph_diff_passes_when_orphan_fixed(repo: Path) -> None:
    # base has an orphan; head fixes it by adding a criterion that traces to it
    orphan_body = GOOD_HARNESS.replace(
        "- R-DMO-1: The system MUST do a thing.",
        "- R-DMO-1: The system MUST do a thing.\n- R-DMO-9: MUST do an untested thing.",
    )
    _write_spec(repo, "c1", "cap1", orphan_body)
    base = _graph_json(repo)
    assert "R-DMO-9" in {n["id"] for n in base["nodes"] if n.get("orphan")}

    fixed = orphan_body.replace(
        "- [ ] **AC-DMO-2 (non-success):** The thing is refused when invalid. (R-DMO-1)",
        "- [ ] **AC-DMO-2 (non-success):** The thing is refused when invalid. (R-DMO-1)\n- [ ] **AC-DMO-3:** The untested thing is now tested. (R-DMO-9)\n  _Verified by:_ `pytest -k test_now` · stage: `make test`",
    )
    _write_spec(repo, "c1", "cap1", fixed)
    head = _graph_json(repo)
    assert "R-DMO-9" not in {n["id"] for n in head["nodes"] if n.get("orphan")}
    assert _diff(base, head) == 0  # fixing an orphan is an improvement, not a regression

def test_graph_diff_rejects_bad_args(capsys) -> None:
    """One positional where two are declared is argparse's own
    ``SystemExit(2)`` -- usage on stderr, nothing on stdout -- which the
    ``if __name__`` guard turns into the same exit 2 the script returned
    when it counted ``argv`` by hand (AC-ZCG-6)."""
    with pytest.raises(SystemExit) as excinfo:
        run_tool_main("diff_spec_graph", "diff_spec_graph.py", "only-one-arg")
    assert excinfo.value.code == 2
    out, err = capsys.readouterr()
    assert "usage:" in err
    assert out == ""

def test_graph_diff_help_exits_zero(capsys) -> None:
    """``--help`` is the one argument the argparse move adds (R-ZCG-5)."""
    with pytest.raises(SystemExit) as excinfo:
        run_tool_main("diff_spec_graph", "diff_spec_graph.py", "--help")
    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert "usage:" in out and "base" in out and "head" in out
    assert err == ""

def test_graph_diff_logs_its_decision_without_polluting_stdout(repo: Path, capsys, caplog) -> None:
    """At DEBUG the diff names each file it read and the inputs to its
    verdict; stdout is still the one ``PASS:`` line CI greps for (R-ZCG-8)."""
    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    base = _graph_json(repo)
    head = json.loads(json.dumps(base))
    with captured_logger(caplog, "planlint.tools"):
        assert _diff(base, head) == 0
    messages = [record.getMessage() for record in caplog.records]
    assert sum("read_json:" in m for m in messages) == 2, messages
    assert any("broken_links" in m and "orphan" in m for m in messages), messages
    out = capsys.readouterr().out
    assert out.startswith("PASS:") and out.count("\n") == 1, out
    assert not any(m in out for m in messages)

# --- render_mermaid.py: thin consumer of a saved graph.json (CP-GV) ---------


def test_render_mermaid_matches_to_mermaid_byte_for_byte(repo: Path, tmp_path: Path, capsys) -> None:
    from openspec_graph.mermaid import to_mermaid

    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    graph = _graph_json(repo)
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph))

    assert run_tool_main("render_mermaid", "render_mermaid.py", str(graph_path)) == 0
    # `print(..., end="")`, so stdout is the rendering with nothing appended.
    assert capsys.readouterr().out == to_mermaid(graph)

def test_render_mermaid_rejects_bad_args(capsys) -> None:
    """No positional where one is declared: argparse's ``SystemExit(2)``,
    usage on stderr, nothing on stdout (AC-ZCG-8)."""
    with pytest.raises(SystemExit) as excinfo:
        run_tool_main("render_mermaid", "render_mermaid.py")
    assert excinfo.value.code == 2
    out, err = capsys.readouterr()
    assert "usage:" in err
    assert out == ""

def test_render_mermaid_help_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        run_tool_main("render_mermaid", "render_mermaid.py", "--help")
    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert "usage:" in out and "graph" in out
    assert err == ""

def test_render_mermaid_logs_the_node_count_without_polluting_stdout(
    repo: Path, tmp_path: Path, capsys, caplog
) -> None:
    """With the logger at DEBUG, stdout is *still* byte-identical to
    ``to_mermaid(graph)``: the records go to stderr through ``_common``'s
    handler and never touch the rendering (R-ZCG-7, R-ZCG-8)."""
    from openspec_graph.mermaid import to_mermaid

    _write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    graph = _graph_json(repo)
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph))
    with captured_logger(caplog, "planlint.tools"):
        assert run_tool_main("render_mermaid", "render_mermaid.py", str(graph_path)) == 0
    messages = [record.getMessage() for record in caplog.records]
    assert any("read_json:" in m and graph_path.name in m for m in messages), messages
    nodes, edges = len(graph["nodes"]), len(graph["edges"])
    assert any(f"{nodes} node" in m and f"{edges} edge" in m for m in messages), messages
    assert capsys.readouterr().out == to_mermaid(graph)
