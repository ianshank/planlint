#!/usr/bin/env python3
"""PreToolUse guard for the branch promotion model (adopt-branch-promotion-model).

Fires BEFORE a Bash command or a GitHub pull-request tool call runs, and
refuses the moves the promotion model forbids before anything leaves the
machine -- the window where no branch ruleset exists yet and nothing else
would stop them:

* ``git push`` whose destination is the candidate or production branch (they
  change only through pull requests) -> deny;
* a force-push (``-f``, ``--force``, ``--force-with-lease``, ``+refspec``) or a
  delete of any of the three long-lived branches -> deny;
* a push of a ``v*`` tag, or ``--tags`` -> ask: a pushed release tag publishes
  to PyPI, whose versions are immutable;
* ``gh pr merge --squash`` -> ask: promotions and back-merges are merge commits;
* a pull request whose head may not target its base (the GitHub tool, or
  ``gh pr create``) -> deny, judged by ``tools/check_promotion.py``'s own
  ``route`` so this hook holds no copy of the topology. While
  ``enforce_routes`` is ``"false"`` a refused route proceeds, as it does in CI;
* a GitHub tool writing a file straight to the candidate or production branch
  -> deny; a squash merge or a retarget onto one of them -> ask.

A push with no refspec (or a bare ``HEAD``) is judged against the checked-out
branch; ``--all`` and ``--mirror`` are refused outright.

Branch names come from ``pyproject.toml`` ``[tool.specgraph.promotion]``
through that tool. Anything this guard cannot parse it lets through, silently:
it is a seat belt, not the gate -- CI and the rulesets are. Stdlib only; one
JSON object on stdout when it decides, nothing otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

#: GitHub MCP tools, by what the guard reads from their input.
CREATE_PR_TOOLS = frozenset({"mcp__github__create_pull_request"})
BRANCH_WRITE_TOOLS = frozenset({
    "mcp__github__push_files", "mcp__github__create_or_update_file", "mcp__github__delete_file",
})
MERGE_TOOLS = frozenset({"mcp__github__merge_pull_request"})
RETARGET_TOOLS = frozenset({"mcp__github__update_pull_request"})
FORCE_FLAGS = frozenset({"-f", "--force", "--force-with-lease", "--force-if-includes"})
DELETE_FLAGS = frozenset({"-d", "--delete"})
#: Push options that take the next word as their value (unless written `--x=value`).
PUSH_VALUE_OPTIONS = frozenset({"-o", "--push-option", "--repo", "--receive-pack", "--exec"})
#: git's own options that take the next word as their value.
GIT_VALUE_OPTIONS = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})
#: Wrappers that run the rest of the line as the command.
WRAPPERS = frozenset({"env", "command", "exec", "nohup", "time"})
TAG_REF = re.compile(r"^(?:refs/tags/)?v\d")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SEPARATORS = frozenset({"&&", "||", ";", "|", "&"})

CurrentBranch = Callable[[], str]


def load_promotion_tool(repo_root: Path | None = None) -> ModuleType:
    """``tools/check_promotion.py`` of this checkout, imported by path."""
    root = repo_root or REPO_ROOT
    path = root / "tools" / "check_promotion.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("check_promotion_for_guard", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Registered before it runs: its dataclasses resolve their module there.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git_current_branch() -> str:
    """The checked-out branch, or ``""`` (detached, or git unavailable)."""
    git = shutil.which("git")
    if git is None:
        return ""
    done = subprocess.run(  # noqa: S603 - fixed argv, resolved git, no shell
        [git, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
        text=True, check=False, cwd=REPO_ROOT,
    )
    branch = done.stdout.strip() if done.returncode == 0 else ""
    return "" if branch == "HEAD" else branch


def _decision(kind: str, reason: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": kind, "permissionDecisionReason": reason,
    }}


def _commands(command: str) -> list[list[str]]:
    """The simple commands in a shell script: split on newlines and ``&&``, ``;``, ``|``,
    with leading ``VAR=value`` assignments and ``env``-style wrappers removed."""
    commands: list[list[str]] = []
    for line in command.splitlines():
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        current: list[str] = []
        for token in lexer:
            if token in _SEPARATORS:
                commands.append(current)
                current = []
            else:
                current.append(token)
        commands.append(current)
    stripped: list[list[str]] = []
    for words in commands:
        while words and (ASSIGNMENT.match(words[0]) or words[0] in WRAPPERS):
            words = words[1:]
        if words:
            stripped.append(words)
    return stripped


def _git_subcommand(words: list[str]) -> tuple[str, list[str]]:
    """``(subcommand, its arguments)`` of a ``git`` command, past git's own options."""
    index = 1
    while index < len(words) and words[index].startswith("-"):
        index += 2 if words[index] in GIT_VALUE_OPTIONS else 1
    if index >= len(words):
        return "", []
    return words[index], words[index + 1:]


def _branch(ref: str) -> str:
    return ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref


def judge_push(
    args: list[str], protected: frozenset[str], long_lived: frozenset[str], current_branch: CurrentBranch
) -> dict[str, Any] | None:
    """The decision for the words after ``git push``, or ``None`` to allow."""
    flags: set[str] = set()
    positional: list[str] = []
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg.startswith("-"):
            flags.add(arg.split("=", 1)[0])
            skip = arg in PUSH_VALUE_OPTIONS
        else:
            positional.append(arg)
    if "--mirror" in flags or "--all" in flags or "--branches" in flags:
        return _decision("deny", "Refusing a push of every branch (--mirror/--all): it would move the "
                         "long-lived branches outside a pull request.")
    forced = bool(flags & FORCE_FLAGS)
    deleting = bool(flags & DELETE_FLAGS)
    refspecs = positional[1:]  # positional[0] is the remote
    # No refspec, or a bare HEAD/@, pushes the checked-out branch.
    if not refspecs or all(spec.lstrip("+") in ("HEAD", "@") for spec in refspecs):
        branch = current_branch()
        refspecs = [("+" if any(s.startswith("+") for s in refspecs) else "") + branch] if branch else []
    for refspec in refspecs:
        plus = refspec.startswith("+")
        source, _, destination = refspec.lstrip("+").partition(":")
        target = _branch(destination or source)
        delete_refspec = source == "" and destination != ""  # `:branch` deletes it
        if (forced or plus or deleting or delete_refspec) and target in long_lived:
            return _decision("deny", f"Refusing to force-push or delete the long-lived branch {target!r}: "
                             "it changes only by pull request, and history on it is never rewritten.")
        if target in protected:
            return _decision("deny", f"Refusing a direct push to {target!r}: it changes only through a "
                             "promotion pull request (docs/hooks.md, Branching and promotion).")
        if TAG_REF.match(target):
            return _decision("ask", f"Pushing tag {target!r} runs the release workflow and publishes to "
                             "PyPI, whose versions are immutable. Tags are made by a person.")
    if "--tags" in flags or "--follow-tags" in flags:
        return _decision("ask", "Pushing tags can publish a release to PyPI, whose versions are immutable.")
    return None


def _option(words: list[str], *names: str) -> str:
    """The value of the first of ``names`` in ``words`` (``--x v`` or ``--x=v``), or ``""``."""
    for index, word in enumerate(words):
        for name in names:
            if word == name and index + 1 < len(words):
                return words[index + 1]
            if word.startswith(name + "="):
                return word.split("=", 1)[1]
    return ""


def _route_decision(base: str, head: str, tool: ModuleType, topology: Any) -> dict[str, Any] | None:
    if not (base.strip() and head.strip()):
        return None
    verdict = tool.route(topology, event="pull_request", base=base, head=head)
    if verdict.allowed:
        return None
    return _decision("deny", f"{verdict.reason}. Retarget the pull request; never relax "
                     "[tool.specgraph.promotion] to make a route pass.")


_SQUASH = "Promotions and back-merges are merge commits; squash only a feature pull request into the integration branch."


def judge_bash(
    command: str, tool: ModuleType, topology: Any, current_branch: CurrentBranch
) -> dict[str, Any] | None:
    protected = frozenset({topology.candidate, topology.production})
    long_lived = protected | {topology.integration}
    for words in _commands(command):
        if words[0] == "git":
            subcommand, rest = _git_subcommand(words)
            if subcommand == "push":
                decided = judge_push(rest, protected, long_lived, current_branch)
                if decided:
                    return decided
        if words[:3] == ["gh", "pr", "merge"] and ("--squash" in words or "-s" in words):
            return _decision("ask", _SQUASH)
        if words[:3] == ["gh", "pr", "create"]:
            base = _option(words, "--base", "-B")
            head = _option(words, "--head", "-H") or current_branch()
            decided = _route_decision(base, head, tool, topology)
            if decided:
                return decided
    return None


def judge_github_tool(
    name: str, tool_input: dict[str, Any], tool: ModuleType, topology: Any
) -> dict[str, Any] | None:
    protected = frozenset({topology.candidate, topology.production})
    if name in CREATE_PR_TOOLS:
        return _route_decision(str(tool_input.get("base") or ""), str(tool_input.get("head") or ""),
                               tool, topology)
    if name in BRANCH_WRITE_TOOLS and str(tool_input.get("branch") or "") in protected:
        return _decision("deny", f"Refusing a direct write to {tool_input['branch']!r}: it changes only "
                         "through a promotion pull request.")
    if name in MERGE_TOOLS and str(tool_input.get("merge_method") or "") == "squash":
        return _decision("ask", _SQUASH)
    if name in RETARGET_TOOLS and str(tool_input.get("base") or "") in protected:
        return _decision("ask", f"Retargeting onto {tool_input['base']!r} does not re-run CI, so the "
                         "route check is stale until the next push or re-run.")
    return None


def decide(
    payload: dict[str, Any], tool: ModuleType, topology: Any, current_branch: CurrentBranch | None = None
) -> dict[str, Any] | None:
    """The guard's decision for one PreToolUse payload, or ``None`` to stay quiet.

    A refused route while ``enforce_routes`` is off is ``None`` here: CI
    prints it as a WARN, and the guard is no stricter than CI.
    """
    name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    if name == "Bash":
        return judge_bash(str(tool_input.get("command") or ""), tool, topology,
                          current_branch or git_current_branch)
    return judge_github_tool(name, tool_input, tool, topology)


def main(stdin: str, repo_root: Path | None = None) -> str:
    """Stdout for one hook invocation: a decision object, or ``""``."""
    try:
        payload = json.loads(stdin)
        tool = load_promotion_tool(repo_root)
        topology = tool.load_topology((repo_root or REPO_ROOT) / "pyproject.toml")
        decided = decide(payload, tool, topology) if isinstance(payload, dict) else None
    except Exception as exc:  # a seat belt never blocks on its own fault
        sys.stderr.write(f"guard_promotion: not judged ({type(exc).__name__}: {exc})\n")
        return ""
    return json.dumps(decided) if decided else ""


if __name__ == "__main__":
    out = main(sys.stdin.read())
    if out:
        sys.stdout.write(out + "\n")
    sys.exit(0)
