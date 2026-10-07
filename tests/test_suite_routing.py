"""The routing and loop guards of the test suite.

Split from ``tests/test_suite_shape.py`` by ``shape-the-test-suite`` (R-TSS-1)
when the review's planted spawn shapes took that module to its line bound:
here, R-TSS-8's two routing guards -- the CLI spawn and the spec writers go
through ``tests/support.py`` -- and R-TSS-9's guard on the four converted
loops, each with its planted counter-examples. ``tests/shape_support.py`` is
the AST engine behind both modules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.shape_support import (
    SUPPORT_MODULE,
    converted_loop_violations,
    hand_written_specs,
    inline_cli_spawns,
    plant,
    routed_shapes,
)

TESTS_DIR = Path(__file__).resolve().parent


# --- Milestone 5: the duplicated shapes route through tests/support.py (R-TSS-8) ---


@pytest.mark.integration
def test_no_test_module_spawns_the_cli_outside_support() -> None:
    """R-TSS-8: `run_cli` is the one place a test spawns the CLI against a
    target; the shape is read from `run_cli` itself, so a copy that drifts
    from it -- the UTF-8 decode, the coverage hand-off -- is named."""
    shapes = routed_shapes(TESTS_DIR / SUPPORT_MODULE)
    inline = inline_cli_spawns(TESTS_DIR, shapes)
    assert inline == [], f"spawn the CLI through tests.support.run_cli, not inline: {inline}"


@pytest.mark.integration
def test_no_test_module_writes_a_spec_path_by_hand() -> None:
    """R-TSS-8: `write_spec` and `write_speckit_spec` are the only writers of
    the harness and SpecKit spec paths; a FIFO, a directory or an assertion at
    such a path is not a write."""
    shapes = routed_shapes(TESTS_DIR / SUPPORT_MODULE)
    by_hand = hand_written_specs(TESTS_DIR, shapes)
    assert by_hand == [], f"write specs through the tests.support writers: {by_hand}"


_PLANTED_ROUTING = {
    "inline-cli-spawn": ("""
        import subprocess
        import sys


        def test_spawns(tmp_path):
            subprocess.run(
                [sys.executable, "-m", "openspec_graph.cli", "--target", str(tmp_path), "validate"],
                check=False,
            )
    """, "spawn", True),
    "spawn-through-a-module-alias": ("""
        import subprocess as sp
        import sys


        def test_spawns(tmp_path):
            sp.run([sys.executable, "-m", "openspec_graph.cli", "--target", str(tmp_path)], check=False)
    """, "spawn", True),
    "spawn-through-a-from-import": ("""
        import sys
        from subprocess import run


        def test_spawns(tmp_path):
            run([sys.executable, "-m", "openspec_graph.cli", "--target", str(tmp_path)], check=False)
    """, "spawn", True),
    "spawn-with-the-argv-built-in-a-local": ("""
        import subprocess
        import sys


        def test_spawns(tmp_path):
            argv = [sys.executable, "-m", "openspec_graph.cli", "--target", str(tmp_path)]
            subprocess.run(argv, check=False)
    """, "spawn", True),
    "version-spawn-without-target": ("""
        import subprocess
        import sys


        def test_version():
            subprocess.run([sys.executable, "-m", "openspec_graph.cli", "--version"], check=False)
    """, "spawn", False),
    "harness-write-through-a-local": ("""
        def test_writes(tmp_path):
            spec = tmp_path / "openspec" / "changes" / "c1" / "specs" / "cap" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("# Spec", encoding="utf-8")
    """, "write", True),
    "speckit-write-through-two-locals": ("""
        def test_writes(tmp_path):
            features = tmp_path / "specs"
            feature = features / "001-demo"
            (feature / "spec.md").write_text("# Spec", encoding="utf-8")
    """, "write", True),
    "fifo-at-a-spec-path": ("""
        import os


        def test_fifo(tmp_path):
            os.mkfifo(tmp_path / "specs" / "001-demo" / "spec.md")
    """, "write", False),
    "assertion-on-a-spec-path": ("""
        def test_exists(tmp_path):
            assert not (tmp_path / "specs" / "001-demo" / "spec.md").exists()
    """, "write", False),
    "main-spec-path-no-writer-routes": ("""
        def test_writes(tmp_path):
            (tmp_path / "openspec" / "specs" / "cap" / "spec.md").write_text("x")
    """, "write", False),
}


@pytest.mark.integration
@pytest.mark.parametrize("case", sorted(_PLANTED_ROUTING))
def test_a_planted_inline_spawn_or_hand_written_spec_is_named(tmp_path: Path, case: str) -> None:
    """R-TSS-8: each routing guard names its planted shape and stays quiet on
    a spawn without `--target`, a FIFO, an assertion and a path no routed
    writer owns."""
    text, guard, named = _PLANTED_ROUTING[case]
    root = tmp_path / TESTS_DIR.name
    plant(root, {"test_planted.py": text})
    shapes = routed_shapes(TESTS_DIR / SUPPORT_MODULE)
    found = inline_cli_spawns(root, shapes) if guard == "spawn" else hand_written_specs(root, shapes)
    assert bool(found) is named, f"{case}: {found}"


# --- Milestone 6: the converted loops keep one subprocess each (R-TSS-9) -----------

#: The four tests R-TSS-9 converts, by module: each loop runs through
#: `cli.main` in-process, and one `run_cli` stays as the entry-point check.
CONVERTED_LOOPS = {
    "test_report.py": (
        "test_projections_are_byte_stable_across_runs",
        "test_an_unprojectable_file_exits_two_with_an_empty_stdout",
    ),
    "test_sarif.py": ("test_sarif_returns_the_same_exit_code_as_the_text_run",),
    "test_e2e_corpus.py": ("test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict",),
}


@pytest.mark.integration
def test_the_converted_loops_keep_exactly_one_subprocess() -> None:
    """R-TSS-9: each converted body holds exactly one `run_cli`, outside any
    loop, and references `main`, so its verdicts run in-process and stay tied
    to one real process."""
    found = converted_loop_violations(TESTS_DIR, CONVERTED_LOOPS)
    assert found == [], "\n".join(found)


_PLANTED_LOOPS = {
    "two-run-cli-calls": ("""
        def test_loop(tmp_path):
            run_cli(tmp_path, "validate")
            run_cli(tmp_path, "rules")
            main(["--target", str(tmp_path), "validate"])
    """, True),
    "no-run-cli-call": ("""
        def test_loop(tmp_path):
            main(["--target", str(tmp_path), "validate"])
    """, True),
    "run-cli-inside-a-loop": ("""
        def test_loop(tmp_path):
            for fmt in ("a", "b"):
                run_cli(tmp_path, "report", "--format", fmt)
            main(["--target", str(tmp_path), "validate"])
    """, True),
    "no-reference-to-main": ("""
        def test_loop(tmp_path):
            run_cli(tmp_path, "validate")
    """, True),
    "one-entry-check-and-main": ("""
        def test_loop(tmp_path, capsys):
            for fmt in ("a", "b"):
                main(["--target", str(tmp_path), "report", "--format", fmt])
            assert run_cli(tmp_path, "validate").returncode == 0
    """, False),
}


@pytest.mark.integration
@pytest.mark.parametrize("case", sorted(_PLANTED_LOOPS))
def test_a_planted_loop_with_the_wrong_subprocess_count_is_named(tmp_path: Path, case: str) -> None:
    """R-TSS-9, R-TSS-12: the loop guard names a body with two `run_cli`
    calls, with none, with one inside a loop, or with no `main`, and stays
    quiet on the converted shape."""
    text, named = _PLANTED_LOOPS[case]
    root = tmp_path / TESTS_DIR.name
    plant(root, {"test_planted.py": text})
    found = converted_loop_violations(root, {"test_planted.py": ("test_loop",)})
    assert bool(found) is named, f"{case}: {found}"
