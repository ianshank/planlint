"""``tools/smoke_wheel.py``: the clean-venv smoke test both workflows share.

adopt-branch-promotion-model. The probe logic is asserted in-process against an
injected runner that records every command, so ordering, the venv's own
interpreter and console script, and each exit-code mismatch are visible
without building anything. One ``e2e`` test builds this project's real wheel
and runs the real tool against the labelled action fixtures -- the same
invocation ci.yml's ``release-tier`` job makes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from tests.support import captured_logger, load_tool, run_tool_main

TOOL = "smoke_wheel.py"


def _tool():  # type: ignore[no-untyped-def]
    return load_tool("smoke_wheel", TOOL)


class FakeRunner:
    """Records each command; answers from ``codes`` keyed by the command's tail."""

    def __init__(self, codes: dict[tuple[str, ...], int] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.codes = codes or {}

    def __call__(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(args))
        for tail, code in self.codes.items():
            if tuple(args[-len(tail):]) == tail:
                return subprocess.CompletedProcess(args, code, "probe stdout", "probe stderr")
        return subprocess.CompletedProcess(args, 0, "", "")


def _dist(tmp_path: Path, *names: str) -> Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    for name in names:
        (dist / name).write_bytes(b"")
    return dist


@pytest.mark.integration
def test_smoke_runs_every_probe_with_the_venv_console_script(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    tool = _tool()
    dist = _dist(tmp_path, "planlint-1.0-py3-none-any.whl", "planlint-1.0.tar.gz")
    venv = tmp_path / "venv"
    runner = FakeRunner()
    probes = tool.build_probes("repo", "WARN", [("fixtures/failing", 1)])
    runner.codes = {("--target", "fixtures/failing", "validate", "--fail-on", "WARN"): 1}

    with captured_logger(caplog, "planlint.tools"):
        code = tool.smoke(dist, venv, probes, python="py-for-venv", runner=runner)

    assert code == 0, capsys.readouterr()
    script = str(tool.venv_bin(venv, "planlint"))
    assert runner.calls == [
        ["py-for-venv", "-m", "venv", str(venv)],
        [str(tool.venv_bin(venv, "python")), "-m", "pip", "install", "--quiet",
         str(dist / "planlint-1.0-py3-none-any.whl")],
        [script, "--version"],
        [script, "--target", "repo", "detect"],
        [script, "--target", "repo", "validate", "--fail-on", "WARN"],
        [script, "--target", "fixtures/failing", "validate", "--fail-on", "WARN"],
    ]
    out = capsys.readouterr().out
    assert "PASS validate fixtures/failing (exit 1)" in out
    assert any("smoke_wheel: install wheel -> 0" in r.getMessage() for r in caplog.records)


@pytest.mark.integration
def test_smoke_fails_when_a_probe_exit_code_differs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failing tree that validates clean is a broken artifact, and every probe still runs."""
    tool = _tool()
    dist = _dist(tmp_path, "planlint-1.0-py3-none-any.whl")
    runner = FakeRunner({("--version",): 1})
    probes = tool.build_probes(".", "ERROR", [("fixtures/failing", 1)])
    code = tool.smoke(dist, tmp_path / "v", probes, python="py", runner=runner)
    assert code == 1
    out = capsys.readouterr().out
    assert "FAIL version: expected exit 0, got 1" in out
    assert "FAIL validate fixtures/failing: expected exit 1, got 0" in out
    assert "probe stderr" in out
    assert len(runner.calls) == 2 + len(probes)


@pytest.mark.integration
def test_smoke_fails_a_probe_that_crashed_with_the_expected_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An uncaught exception exits 1 too: a failing verdict must not be a crash."""
    tool = _tool()
    dist = _dist(tmp_path, "planlint-1.0-py3-none-any.whl")

    def runner(args):  # type: ignore[no-untyped-def]
        if args[-3:] == ["validate", "--fail-on", "ERROR"] and "fixtures/failing" in args:
            return subprocess.CompletedProcess(
                args, 1, "", "Traceback (most recent call last):\n  ...\nRuntimeError: boom"
            )
        return subprocess.CompletedProcess(args, 0, "", "")

    probes = tool.build_probes(".", "ERROR", [("fixtures/failing", 1)])
    assert tool.smoke(dist, tmp_path / "v", probes, python="py", runner=runner) == 1
    out = capsys.readouterr().out
    assert "FAIL validate fixtures/failing: the console script crashed (exit 1)" in out
    assert "RuntimeError: boom" in out


@pytest.mark.integration
@pytest.mark.parametrize("wheels", [(), ("a-1-py3-none-any.whl", "b-1-py3-none-any.whl")],
                         ids=["none", "two"])
def test_smoke_requires_exactly_one_wheel(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], wheels: tuple[str, ...]
) -> None:
    tool = _tool()
    runner = FakeRunner()
    code = tool.smoke(_dist(tmp_path, *wheels), tmp_path / "v", [], python="py", runner=runner)
    assert code == 2
    assert runner.calls == []
    assert f"found {len(wheels)}" in capsys.readouterr().err


@pytest.mark.integration
def test_smoke_missing_dist_directory_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _tool().smoke(tmp_path / "absent", tmp_path / "v", [], python="py", runner=FakeRunner())
    assert code == 2
    assert "found 0" in capsys.readouterr().err


@pytest.mark.integration
@pytest.mark.parametrize("failing_step", ["venv", "install"])
def test_smoke_setup_failure_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], failing_step: str
) -> None:
    """A venv or install that fails is "could not run", never a probe verdict."""
    tool = _tool()
    dist = _dist(tmp_path, "planlint-1.0-py3-none-any.whl")
    venv = tmp_path / "v"
    tail = (str(venv),) if failing_step == "venv" else (str(dist / "planlint-1.0-py3-none-any.whl"),)
    runner = FakeRunner({tail: 3})
    code = tool.smoke(dist, venv, tool.build_probes(".", "ERROR", []), python="py", runner=runner)
    assert code == 2
    assert "failed (3)" in capsys.readouterr().err
    assert len(runner.calls) == (1 if failing_step == "venv" else 2)


@pytest.mark.integration
@pytest.mark.parametrize("raw", ["no-equals", "=1", "path=", "path=x"])
def test_smoke_rejects_a_malformed_expect(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], raw: str
) -> None:
    code = run_tool_main("smoke_wheel", TOOL, str(tmp_path), "--expect", raw, pass_argv0=False)
    assert code == 2
    assert "PATH=EXITCODE" in capsys.readouterr().err


@pytest.mark.integration
def test_smoke_expect_keeps_an_equals_sign_in_the_path() -> None:
    assert _tool().parse_expect("a=b/c=2") == ("a=b/c", 2)


@pytest.mark.integration
def test_smoke_venv_layout_follows_the_platform() -> None:
    tool = _tool()
    assert tool.venv_bin(Path("v"), "planlint", windows=True) == Path("v") / "Scripts" / "planlint.exe"
    assert tool.venv_bin(Path("v"), "planlint", windows=False) == Path("v") / "bin" / "planlint"
    native = tool.venv_bin(Path("v"), "planlint")
    assert native == tool.venv_bin(Path("v"), "planlint", windows=os.name == "nt")


@pytest.mark.e2e
def test_the_real_wheel_passes_the_shared_smoke_tool(tmp_path: Path) -> None:
    """This project's real wheel, the real venv, the labelled fixtures.

    Skips rather than fails when ``build`` cannot run here (no network for the
    build requirements): a missing tool is not a broken wheel, and CI's
    ``release-tier`` job runs this path unconditionally.
    """
    repo = Path(__file__).resolve().parent.parent
    dist = tmp_path / "dist"
    built = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist), str(repo)],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    if built.returncode != 0:
        pytest.skip(f"`python -m build` unavailable in this environment:\n{built.stderr[-400:]}")
    fixtures = repo / "tests" / "fixtures" / "action"
    smoke = subprocess.run(
        [sys.executable, str(repo / "tools" / TOOL), str(dist), "--venv", str(tmp_path / "venv"),
         "--target", str(repo),
         "--expect", f"{fixtures / 'passing'}=0", "--expect", f"{fixtures / 'failing'}=1"],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    assert smoke.returncode == 0, smoke.stdout + smoke.stderr
    assert smoke.stdout.count("PASS ") == 5, smoke.stdout


@pytest.mark.integration
@pytest.mark.parametrize("explicit_venv", [False, True], ids=["temporary", "explicit"])
def test_smoke_main_wires_its_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit_venv: bool
) -> None:
    """The CLI hands ``smoke`` its probes and a venv: a given one, or a fresh temporary one."""
    tool = _tool()
    seen: dict[str, object] = {}

    def fake_smoke(dist, venv, probes, *, python):  # type: ignore[no-untyped-def]
        seen.update(dist=dist, venv=venv, probes=probes, python=python, existed=venv.parent.is_dir())
        return 0

    monkeypatch.setattr(tool, "smoke", fake_smoke)
    args = [str(tmp_path / "d"), "--target", "t", "--fail-on", "WARN", "--expect", "f=1",
            "--python", "py"]
    if explicit_venv:
        args += ["--venv", str(tmp_path / "v")]
    assert tool.main(args) == 0
    assert seen["dist"] == tmp_path / "d" and seen["python"] == "py"
    assert [p.args for p in seen["probes"]][-1] == ("--target", "f", "validate", "--fail-on", "WARN")
    if explicit_venv:
        assert seen["venv"] == tmp_path / "v"
    else:
        venv = seen["venv"]
        assert isinstance(venv, Path) and venv.name == "venv" and seen["existed"]
        assert not venv.parent.exists(), "the temporary directory must be removed afterwards"
