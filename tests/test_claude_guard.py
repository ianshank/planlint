"""The PreToolUse promotion guard is wired, and decides what it claims to.

``.claude/hooks/guard_promotion.py`` (adopt-branch-promotion-model) runs before
a Bash command or a pull-request tool call and refuses the moves the promotion
model forbids while no branch ruleset exists to. Every decision is asserted
in-process against a topology planted with role names unlike this
repository's (``trunk``/``staging``/``live``), so a branch name hard-coded in
the guard would fail here; one ``e2e`` case drives the real script through
stdin the way Claude Code does.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.promotion_support import promotion_tool, write_promotion_pyproject

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / ".claude" / "hooks" / "guard_promotion.py"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
HOOKS_DOC = REPO_ROOT / "docs" / "hooks.md"

#: Command -> the decision the guard must make on the planted topology.
BASH_DECISIONS: dict[str, str] = {
    "git push origin live": "deny",
    "git push origin HEAD:staging": "deny",
    "git push origin refs/heads/live": "deny",
    "cd repo && git -C . push origin live": "deny",
    "git push --force origin trunk": "deny",
    "git push --force-with-lease=trunk origin trunk": "deny",
    "git push origin +trunk": "deny",
    "git push origin :staging": "deny",
    "git push --delete origin trunk": "deny",
    "git push origin v1.2.3": "ask",
    "git push origin refs/tags/v1.2.3": "ask",
    "git push --tags": "ask",
    "gh pr merge 7 --squash": "ask",
    "gh pr merge 7 -s": "ask",
    "git push --mirror origin": "deny",
    "git push --all origin": "deny",
    "GIT_TRACE=1 git push origin live": "deny",
    "env GIT_TRACE=1 git push origin live": "deny",
    "echo hi\ngit push origin live": "deny",
    "git push -o ci.skip origin live": "deny",
    "gh pr create --base live --head trunk": "deny",
    "gh pr create -B staging": "deny",
}
#: Pushes that name no destination: judged against the checked-out branch.
CURRENT_BRANCH_DECISIONS: dict[tuple[str, str], str] = {
    ("git push", "live"): "deny",
    ("git push origin HEAD", "staging"): "deny",
    ("git push --force", "trunk"): "deny",
    ("git push origin +HEAD", "trunk"): "deny",
    ("git push", "feature/x"): "allow",
    ("git push origin HEAD", ""): "allow",
}
#: GitHub MCP calls -> the decision on the planted topology.
GITHUB_DECISIONS: list[tuple[str, dict[str, str], str]] = [
    ("mcp__github__push_files", {"branch": "live"}, "deny"),
    ("mcp__github__create_or_update_file", {"branch": "staging"}, "deny"),
    ("mcp__github__delete_file", {"branch": "feature/x"}, "allow"),
    ("mcp__github__merge_pull_request", {"merge_method": "squash"}, "ask"),
    ("mcp__github__merge_pull_request", {"merge_method": "merge"}, "allow"),
    ("mcp__github__update_pull_request", {"base": "live"}, "ask"),
    ("mcp__github__update_pull_request", {"base": "trunk"}, "allow"),
]
#: Commands the guard must leave alone: a nag on every push gets disabled.
BASH_ALLOWED = (
    "git push -u origin claude/feature",
    "git push origin trunk",
    "git push origin feature/x:feature/x",
    "git status && git log --oneline -3",
    "echo 'git push origin live'",
    "gh pr merge 7 --merge",
    "git log --grep push origin live",
    "git push -o ci.skip origin feature/x",
    "gh pr create --base trunk --head feature/x",
    "git push 'unterminated",
)


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("guard_promotion", GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_guard()


@pytest.fixture
def planted(tmp_path: Path) -> tuple[ModuleType, Any]:
    """The promotion tool and an enforced topology with foreign branch names."""
    tool = promotion_tool()
    return tool, tool.load_topology(write_promotion_pyproject(tmp_path))


def _decide(
    guard: ModuleType, planted: tuple[ModuleType, Any], payload: dict[str, Any], branch: str = "feature/x"
) -> str:
    decided = guard.decide(payload, *planted, current_branch=lambda: branch)
    return decided["hookSpecificOutput"]["permissionDecision"] if decided else "allow"


@pytest.mark.integration
def test_settings_wires_the_guard_before_bash_and_pull_requests() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    entries = settings["hooks"]["PreToolUse"]
    commands = [hook["command"] for entry in entries for hook in entry["hooks"]]
    assert any(cmd.endswith('/.claude/hooks/guard_promotion.py"') for cmd in commands), commands
    matcher = " ".join(entry["matcher"] for entry in entries)
    for tool_name in ("Bash", "mcp__github__create_pull_request"):
        assert tool_name in matcher, f"the guard does not fire before {tool_name}"


@pytest.mark.integration
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX execute bit")
def test_the_guard_is_executable() -> None:
    assert os.access(GUARD, os.X_OK), f"{GUARD.name} is not executable"


@pytest.mark.integration
@pytest.mark.parametrize(("command", "expected"), sorted(BASH_DECISIONS.items()))
def test_the_guard_refuses_what_the_promotion_model_forbids(
    guard: ModuleType, planted: tuple[ModuleType, Any], command: str, expected: str
) -> None:
    assert _decide(guard, planted, {"tool_name": "Bash", "tool_input": {"command": command}}) == expected


@pytest.mark.integration
@pytest.mark.parametrize("command", BASH_ALLOWED)
def test_the_guard_stays_quiet_on_ordinary_commands(
    guard: ModuleType, planted: tuple[ModuleType, Any], command: str
) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    if command.endswith("'unterminated"):
        with pytest.raises(ValueError):
            guard.decide(payload, *planted, current_branch=lambda: "x")  # main() turns this into silence
        return
    assert _decide(guard, planted, payload) == "allow"


@pytest.mark.integration
@pytest.mark.parametrize(("command", "branch", "expected"),
                         [(c, b, e) for (c, b), e in sorted(CURRENT_BRANCH_DECISIONS.items())])
def test_a_push_without_a_destination_is_judged_on_the_checked_out_branch(
    guard: ModuleType, planted: tuple[ModuleType, Any], command: str, branch: str, expected: str
) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert _decide(guard, planted, payload, branch=branch) == expected


@pytest.mark.integration
@pytest.mark.parametrize(("name", "tool_input", "expected"), GITHUB_DECISIONS)
def test_the_guard_judges_the_github_tools_that_write_merge_or_retarget(
    guard: ModuleType, planted: tuple[ModuleType, Any], name: str, tool_input: dict[str, str], expected: str
) -> None:
    assert _decide(guard, planted, {"tool_name": name, "tool_input": tool_input}) == expected


@pytest.mark.integration
def test_settings_route_every_judged_github_tool_to_the_guard(guard: ModuleType) -> None:
    """A tool the guard knows how to judge but the matcher never sends is a silent gap."""
    matcher = " ".join(e["matcher"] for e in json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]["PreToolUse"])
    judged = guard.CREATE_PR_TOOLS | guard.BRANCH_WRITE_TOOLS | guard.MERGE_TOOLS | guard.RETARGET_TOOLS
    assert not sorted(name for name in judged if name not in matcher.split("|"))


@pytest.mark.integration
def test_the_current_branch_reader_answers(guard: ModuleType) -> None:
    """In this checkout it names a branch, or "" when detached -- never "HEAD"."""
    assert guard.git_current_branch() != "HEAD"


@pytest.mark.integration
@pytest.mark.parametrize(
    "base,head,expected",
    [("live", "trunk", "deny"), ("staging", "feature/x", "deny"), ("live", "staging", "allow"),
     ("trunk", "feature/x", "allow"), ("live", "", "allow")],
)
def test_the_guard_judges_a_pull_request_with_the_ci_route(
    guard: ModuleType, planted: tuple[ModuleType, Any], base: str, head: str, expected: str
) -> None:
    payload = {"tool_name": "mcp__github__create_pull_request", "tool_input": {"base": base, "head": head}}
    assert _decide(guard, planted, payload) == expected


@pytest.mark.integration
def test_a_refused_route_is_only_a_warning_while_enforcement_is_off(
    guard: ModuleType, tmp_path: Path
) -> None:
    """The guard agrees with CI's bootstrap switch rather than being stricter than it."""
    tool = promotion_tool()
    topology = tool.load_topology(write_promotion_pyproject(tmp_path, extra='enforce_routes = "false"\n'))
    payload = {"tool_name": "mcp__github__create_pull_request", "tool_input": {"base": "live", "head": "trunk"}}
    assert guard.decide(payload, tool, topology) is None


@pytest.mark.integration
@pytest.mark.parametrize("stdin", ["not json", "[]", '{"tool_name": "Bash", "tool_input": "x"}',
                                   '{"tool_name": "Read", "tool_input": {}}'])
def test_the_guard_never_blocks_on_input_it_cannot_judge(guard: ModuleType, stdin: str) -> None:
    assert guard.main(stdin) == ""


@pytest.mark.integration
def test_the_guard_reads_the_repository_topology(guard: ModuleType) -> None:
    """With this checkout's own table: a direct push to its production branch is denied."""
    production = promotion_tool().load_topology(REPO_ROOT / "pyproject.toml").production
    out = guard.main(json.dumps({"tool_name": "Bash", "tool_input": {"command": f"git push origin {production}"}}))
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.e2e
def test_the_guard_script_answers_on_stdout() -> None:
    production = promotion_tool().load_topology(REPO_ROOT / "pyproject.toml").production
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": f"git push --force origin {production}"}})
    result = subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True,
                            text=True, check=False, cwd=REPO_ROOT)
    assert result.returncode == 0, result.stderr
    decided = json.loads(result.stdout)["hookSpecificOutput"]
    assert (decided["hookEventName"], decided["permissionDecision"]) == ("PreToolUse", "deny")


@pytest.mark.integration
def test_docs_describe_the_guard() -> None:
    doc = HOOKS_DOC.read_text(encoding="utf-8")
    assert ".claude/hooks/guard_promotion.py" in doc and "PreToolUse" in doc
