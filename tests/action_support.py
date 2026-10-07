"""The GitHub-runner simulator the action-contract tests drive -- runs, never asserts.

The pattern of ``tests/workflow_support.py``: an uncollected module holding
``ActionRun`` (one simulated invocation of the composite action's ``shell: bash``
steps), the step extractor and the expression resolver, so that
``tests/test_action_contract.py`` keeps its tests and its ``EXPECTED_INPUTS`` and
stays within the suite's line bound once every test carries its tier mark.
Moved by ``shape-the-test-suite`` (R-TSS-1, R-TSS-2), bodies unchanged.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ACTION = REPO_ROOT / ".github" / "actions" / "planlint" / "action.yml"

_EXPRESSION = re.compile(r"\$\{\{\s*([^}]+?)\s*\}\}")

def _github_bash() -> str | None:
    """The interpreter GitHub uses for a ``shell: bash`` step on this platform.

    On Linux and macOS that is plain ``bash``. On Windows it is the bash that
    ships with Git for Windows -- deliberately *not* whatever ``bash`` resolves
    to on PATH, which is System32's WSL launcher. A hosted Windows runner has
    no WSL distribution installed, so that launcher answers every invocation
    with a UTF-16 error and exit 1, and this simulation would be reporting the
    absence of WSL rather than anything about the action.

    Mirroring the runner's own choice keeps the simulation faithful on both
    platforms instead of running on only one. Returns ``None`` when no such
    interpreter exists, so the caller can skip with a reason rather than fail
    with a confusing one.
    """
    if os.name != "nt":
        return "bash"
    roots = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
    ]
    for root in roots:
        candidate = Path(root) / "Git" / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return None

_BASH = _github_bash()

# The executable half only. The declarative assertions above read the YAML and
# run everywhere, including the Windows leg -- it is the contract that has to
# hold on every platform, while the shell body is POSIX and runs where GitHub
# runs it.
_needs_bash = pytest.mark.skipif(
    _BASH is None,
    reason="no Git for Windows bash on this machine; GitHub uses it for `shell: bash` "
    "on Windows runners, and PATH's `bash` there is the WSL launcher",
)

def _posix(path: Path | str) -> str:
    """A path spelled the way the interpreter above expects to read it.

    Git Bash accepts ``D:/a/_temp/x`` and mangles ``D:\\a\\_temp\\x``, whose
    backslashes it reads as escapes. No-op on POSIX.
    """
    return Path(path).as_posix()

def _action_text() -> str:
    return ACTION.read_text(encoding="utf-8")

# --- the executable half -----------------------------------------------------


def _steps(text: str) -> list[dict[str, object]]:
    """Every step under ``runs.steps``, as ``{id, uses, run, env}``.

    Scans the six-space-indented ``- `` items and their keys, and lifts a
    ``run: |`` block scalar by dedenting its body. Narrow on purpose: it
    understands exactly the shapes this action uses, and raises rather than
    guessing at anything else.
    """
    lines = text.splitlines()
    start = lines.index("  steps:") + 1
    steps: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    block_key: str | None = None
    block: list[str] = []
    in_env = False

    def flush() -> None:
        nonlocal block_key, block
        if current is not None and block_key:
            current[block_key] = "\n".join(block).rstrip() + "\n"
        block_key, block = None, []

    for raw in lines[start:]:
        if block_key:
            if raw.strip() and not raw.startswith(" " * 8):
                flush()
            else:
                block.append(raw[8:] if len(raw) > 8 else "")
                continue
        if raw.startswith("    - "):
            flush()
            current = {"env": {}}
            steps.append(current)
            in_env = False
            raw = "      " + raw[6:]
        if current is None:
            continue
        if re.match(r"^      env:\s*$", raw):
            in_env = True
            continue
        if in_env:
            pair = re.match(r"^        ([A-Za-z_][\w-]*):\s*(.+?)\s*$", raw)
            if pair:
                envs = current["env"]
                assert isinstance(envs, dict)
                envs[pair.group(1)] = pair.group(2)
                continue
            in_env = False
        entry = re.match(r"^      (id|uses|shell|if):\s*(.+?)\s*$", raw)
        if entry:
            current[entry.group(1)] = entry.group(2)
            continue
        if re.match(r"^      run:\s*\|\s*$", raw):
            block_key, block = "run", []
    flush()
    return steps

def _resolve(expression: str, context: dict[str, object]) -> str:
    """Evaluate the ``${{ ... }}`` forms this action uses, and only those."""
    def substitute(match: re.Match[str]) -> str:
        parts = match.group(1).split(".")
        if parts[0] == "inputs":
            inputs = context["inputs"]
            assert isinstance(inputs, dict)
            return str(inputs.get(parts[1], ""))
        if parts[0] == "steps":
            steps = context["steps"]
            assert isinstance(steps, dict)
            return str(steps.get(parts[1], {}).get(parts[3], ""))
        raise AssertionError(f"unsupported action expression: {match.group(1)}")

    return _EXPRESSION.sub(substitute, expression)

class ActionRun:
    """One simulated invocation of the composite action's shell steps."""

    def __init__(self, workspace: Path, runner_temp: Path, **inputs: str) -> None:
        self.context: dict[str, object] = {
            "inputs": {
                "target": ".", "version": "", "fail-on": "ERROR",
                "python-version": "3.12", "upload-artifact": "true",
                "artifact-name": "planlint-evidence",
                "change": "", "dialect": "", **inputs,
            },
            # The install step is a `uses:`-adjacent concern (it installs the
            # CLI that is already installed here), so its one output is seeded
            # from the real command rather than by running pip again.
            "steps": {"install": {"version": _installed_version()}},
        }
        self.workspace = workspace
        self.runner_temp = runner_temp
        self.summary = runner_temp / "step-summary.md"
        self.summary.write_text("", encoding="utf-8")
        self.logs: dict[str, str] = {}

    def run_step(self, step_id: str) -> int:
        step = next(s for s in _steps(_action_text()) if s.get("id") == step_id)
        outputs_file = self.runner_temp / f"{step_id}-outputs.txt"
        outputs_file.write_text("", encoding="utf-8")

        env = {
            "PATH": os.environ["PATH"],
            "HOME": _posix(self.runner_temp),
            "RUNNER_TEMP": _posix(self.runner_temp),
            "GITHUB_OUTPUT": _posix(outputs_file),
            "GITHUB_STEP_SUMMARY": _posix(self.summary),
            "GITHUB_ACTION_PATH": _posix(ACTION.parent),
            # Isolated HOME hides a `--user` install. The hosted job installs
            # into the runner's Python; pointing at this checkout is the local
            # equivalent so the scan exercises the adapter, not site.USER_SITE.
            "PYTHONPATH": os.pathsep.join(
                p for p in (str(REPO_ROOT), os.environ.get("PYTHONPATH", "")) if p
            ),
        }
        # Git Bash needs SYSTEMROOT to resolve its own helpers; harmless
        # elsewhere and absent from the minimal env above without it.
        for passthrough in ("SYSTEMROOT", "SystemRoot", "TEMP", "TMP", "COMSPEC"):
            if passthrough in os.environ:
                env.setdefault(passthrough, os.environ[passthrough])
        raw_env = step["env"]
        assert isinstance(raw_env, dict)
        for key, value in raw_env.items():
            env[key] = _resolve(value, self.context)

        assert _BASH is not None, "run_step needs the interpreter the skip guard checks for"
        # `-e` is not decoration: GitHub runs a composite `shell: bash` step as
        # `bash --noprofile --norc -eo pipefail {0}`, so a body that merely
        # omits `set -e` still starts under errexit. Simulating that is what
        # caught the action's fallible steps dying on their first non-zero
        # command before an exit code could be recorded.
        result = subprocess.run(
            [_BASH, "--noprofile", "--norc", "-eo", "pipefail", "-c", str(step["run"])],
            cwd=self.workspace, env=env, capture_output=True, text=True, check=False,
        )
        self.logs[step_id] = result.stdout + result.stderr
        parsed: dict[str, str] = {}
        for line in outputs_file.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                parsed[key] = value
        steps = self.context["steps"]
        assert isinstance(steps, dict)
        steps[step_id] = parsed
        return result.returncode

    def outputs(self, step_id: str) -> dict[str, str]:
        steps = self.context["steps"]
        assert isinstance(steps, dict)
        return dict(steps.get(step_id, {}))

def _installed_version() -> str:
    result = subprocess.run(["planlint", "--version"], capture_output=True, text=True, check=True)
    return result.stdout.split()[-1]

def _drive(tmp_path: Path, target: str) -> ActionRun:
    """Run paths -> scan -> project and return the simulation, gate not yet applied."""
    run = ActionRun(REPO_ROOT, tmp_path, target=target)
    assert run.run_step("paths") == 0, run.logs["paths"]
    assert run.run_step("scan") == 0, run.logs["scan"]
    assert run.run_step("project") == 0, run.logs["project"]
    return run
