"""The branch promotion model, as a gate (adopt-branch-promotion-model).

Feature work squashes into the *integration* branch; the integration branch
promotes by merge commit to the *candidate* branch; the candidate branch
promotes by merge commit to the *production* branch, the only branch a
release tag may sit on. The three names and the hotfix prefix live in
``pyproject.toml`` under ``[tool.specgraph.promotion]`` and nowhere in this
file: the topology is configuration, and this script is the one place it is
interpreted.

Four subcommands, each a separate CI question:

``branches``
    Print the configured roles (``role=value`` per line), or one value with
    ``--role``. For a workflow step that needs a branch name without
    restating it.
``route``
    Is this pull request allowed to target this base, and does this run need
    the release tier? A pull request into the candidate branch must come from
    the integration branch; one into the production branch must come from the
    candidate branch or a hotfix branch; a head from another repository may
    not target either. Any other base accepts any head. The release tier runs
    whenever the target -- the pull request's base, or the pushed branch -- is
    the candidate or the production branch. The verdict is printed; the tier
    is appended to ``$GITHUB_OUTPUT`` as ``release-tier=true|false``.
``tag-ancestry``
    Is the tagged commit reachable from the production branch? A release tag
    on a commit that never reached production would publish code that skipped
    the candidate tier.
``aggregate``
    The single required status check. Reads ``${{ toJSON(needs) }}`` and fails
    unless every job succeeded, except a job declared conditional whose
    condition was false for this run -- so a skipped job can never read as a
    pass, which is what GitHub does with a skipped *required* check.

Exit codes, every subcommand: 0 pass, 1 the gate fired, 2 the question could
not be answered (missing configuration, unreadable input, a git failure that
is not a verdict). Exit 2 is never a pass. Stdout carries the verdict;
debugging detail goes to the ``planlint.tools`` logger (stderr, silent unless
``PLANLINT_LOG_LEVEL=DEBUG``).

Stdlib only: it runs in a bare CI runner before anything is installed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import logger, read_pyproject_str, repo_root

#: The table every key below is read from.
PROMOTION_SECTION = "[tool.specgraph.promotion]"

#: role -> pyproject key. A role is how this script and its callers refer to a
#: branch; the key is where the name lives.
ROLE_KEYS: dict[str, str] = {
    "integration": "integration_branch",
    "candidate": "candidate_branch",
    "production": "production_branch",
    "hotfix_prefix": "hotfix_prefix",
}

#: The switch that turns a refused route from a warning into a failure. A
#: string, not a bool, because the reader is the string reader; absent means
#: enforced, so a table that forgets the key fails closed. It exists for the
#: bootstrap window only: until the integration and candidate branches exist,
#: every pull request targets production from some other branch, and an
#: enforced route would turn every one of them red (DEC-BPM-013).
ENFORCE_KEY = "enforce_routes"
_BOOLEAN = {"true": True, "false": False}

#: Events whose run is about a pull request's base, not the pushed ref.
PULL_REQUEST_EVENTS = frozenset({"pull_request", "pull_request_target"})

#: What GitHub reports for a job that ran to completion and passed.
SUCCESS = "success"
SKIPPED = "skipped"

_BRANCH_REF_PREFIX = "refs/heads/"

#: ``git merge-base --is-ancestor``'s own contract: 0 yes, 1 no, else an error.
_GIT_IS_ANCESTOR, _GIT_NOT_ANCESTOR = 0, 1

Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]


class ConfigError(ValueError):
    """The promotion table is missing, incomplete or self-contradictory."""


@dataclass(frozen=True)
class Topology:
    """The configured branch roles."""

    integration: str
    candidate: str
    production: str
    hotfix_prefix: str
    enforce_routes: bool = True

    @property
    def release_tier_branches(self) -> frozenset[str]:
        """Branches whose pull requests and pushes run the release tier."""
        return frozenset({self.candidate, self.production})

    def allowed_heads(self, base: str) -> str | None:
        """A human description of who may target ``base``, or ``None`` for anyone."""
        if base == self.production:
            return f"{self.candidate!r} or a {self.hotfix_prefix!r}* branch"
        if base == self.candidate:
            return repr(self.integration)
        return None

    def head_may_target(self, base: str, head: str) -> bool:
        if base == self.production:
            return head == self.candidate or head.startswith(self.hotfix_prefix)
        if base == self.candidate:
            return head == self.integration
        return True

    def as_roles(self) -> dict[str, str]:
        return {role: getattr(self, role) for role in ROLE_KEYS}


def load_topology(pyproject: Path) -> Topology:
    """Read every role out of ``pyproject``, or raise :class:`ConfigError` naming what is wrong."""
    values: dict[str, str] = {}
    missing: list[str] = []
    for role, key in ROLE_KEYS.items():
        value = read_pyproject_str(pyproject, PROMOTION_SECTION, key)
        if value is None:
            missing.append(key)
        else:
            values[role] = value
    if missing:
        raise ConfigError(
            f"{pyproject}: {PROMOTION_SECTION} is missing {', '.join(missing)} "
            "(each a non-empty double-quoted string)"
        )
    branches = [values["integration"], values["candidate"], values["production"]]
    if len(set(branches)) != len(branches):
        raise ConfigError(f"{pyproject}: the three promotion branches must differ, got {branches}")
    for name in branches:
        if name.startswith(values["hotfix_prefix"]):
            raise ConfigError(
                f"{pyproject}: branch {name!r} falls under hotfix_prefix "
                f"{values['hotfix_prefix']!r}, so the route rules would be ambiguous"
            )
    raw_enforce = read_pyproject_str(pyproject, PROMOTION_SECTION, ENFORCE_KEY)
    if raw_enforce is not None and raw_enforce not in _BOOLEAN:
        raise ConfigError(
            f'{pyproject}: {ENFORCE_KEY} must be "true" or "false", got {raw_enforce!r}'
        )
    topology = Topology(
        **values, enforce_routes=_BOOLEAN[raw_enforce] if raw_enforce is not None else True
    )
    logger.debug(
        "check_promotion: topology %s, enforce_routes=%s", topology.as_roles(), topology.enforce_routes
    )
    return topology


# --- route ------------------------------------------------------------------


@dataclass(frozen=True)
class RouteVerdict:
    allowed: bool
    release_tier: bool
    target: str
    reason: str
    #: A refused route let through because enforcement is off: reported, not failed.
    warned: bool = False


def branch_of(ref: str) -> str:
    """``refs/heads/x`` -> ``x``; any other ref (a tag, a pull ref) -> ``""``."""
    return ref[len(_BRANCH_REF_PREFIX):] if ref.startswith(_BRANCH_REF_PREFIX) else ""


def route(
    topology: Topology,
    *,
    event: str,
    base: str = "",
    head: str = "",
    ref: str = "",
    head_repo: str = "",
    base_repo: str = "",
) -> RouteVerdict:
    """Decide one run's route; pure, so every branch of it is unit-testable.

    With ``enforce_routes`` off, a refused route comes back allowed and
    ``warned``, its reason intact, so the run still says what will fail once
    enforcement is switched on. The release tier is unaffected either way.
    """
    verdict = _route(topology, event=event, base=base, head=head, ref=ref,
                     head_repo=head_repo, base_repo=base_repo)
    if verdict.allowed or topology.enforce_routes:
        return verdict
    return RouteVerdict(
        True, verdict.release_tier, verdict.target,
        f"{verdict.reason} (not enforced: {ENFORCE_KEY} is off)", warned=True,
    )


def _route(
    topology: Topology,
    *,
    event: str,
    base: str,
    head: str,
    ref: str,
    head_repo: str,
    base_repo: str,
) -> RouteVerdict:
    if event in PULL_REQUEST_EVENTS:
        target = base
        protected = target in topology.release_tier_branches
        cross_repo = bool(head_repo and base_repo and head_repo != base_repo)
        if protected and cross_repo:
            return RouteVerdict(
                False, True, target,
                f"a head from {head_repo!r} may not target {target!r}; "
                f"promotions into {target!r} come from {base_repo!r} itself",
            )
        if not topology.head_may_target(target, head):
            return RouteVerdict(
                False, protected, target,
                f"{head!r} may not target {target!r}; "
                f"only {topology.allowed_heads(target)} may",
            )
        return RouteVerdict(True, protected, target, f"{head!r} -> {target!r} is a permitted route")
    target = branch_of(ref)
    tier = target in topology.release_tier_branches
    return RouteVerdict(True, tier, target, f"{event} on {ref or 'no ref'}: no route to check")


def write_github_output(path: str, values: Mapping[str, str]) -> None:
    """Append ``key=value`` lines to the step-output file GitHub hands a step."""
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")
    logger.debug("check_promotion: wrote %s to %s", dict(values), path)


# --- aggregate --------------------------------------------------------------


def aggregate(
    needs: Mapping[str, Any],
    *,
    event: str,
    release_tier: bool,
    pull_request_only: Iterable[str] = (),
    release_tier_only: Iterable[str] = (),
) -> list[str]:
    """Every reason the run is not green, in job order; empty means green.

    A conditional job declared here but absent from ``needs`` is itself a
    problem: the declaration would otherwise exempt nothing and hide the
    misconfiguration that lost the job.
    """
    pr_only = set(pull_request_only)
    tier_only = set(release_tier_only)
    problems = [
        f"{job}: declared conditional but not in needs"
        for job in sorted((pr_only | tier_only) - set(needs))
    ]
    is_pull_request = event in PULL_REQUEST_EVENTS
    for job in sorted(needs):
        entry = needs[job]
        result = entry.get("result") if isinstance(entry, Mapping) else None
        logger.debug("check_promotion: %s -> %s", job, result)
        if result == SUCCESS:
            continue
        if result == SKIPPED:
            if job in pr_only and not is_pull_request:
                continue
            if job in tier_only and not release_tier:
                continue
            problems.append(f"{job}: skipped, but its condition held on this run")
            continue
        problems.append(f"{job}: {result}")
    return problems


def _read_needs(source: str) -> dict[str, Any]:
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"needs must be a JSON object, got {type(data).__name__}")
    return data


# --- tag-ancestry -----------------------------------------------------------


def _run_git(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), capture_output=True, text=True, check=False, encoding="utf-8"
    )


def tag_ancestry(
    sha: str,
    production: str,
    *,
    remote: str,
    fetch: bool,
    runner: Runner | None = None,
) -> tuple[int, str]:
    """``(exit code, message)``: is ``sha`` an ancestor of ``remote/production``?"""
    run = runner or _run_git
    tracking = f"{remote}/{production}"
    if fetch:
        fetched = run(["git", "fetch", "--no-tags", remote, production])
        if fetched.returncode != 0:
            return 2, f"could not fetch {tracking}: {fetched.stderr.strip()}"
    checked = run(["git", "merge-base", "--is-ancestor", sha, tracking])
    logger.debug("check_promotion: merge-base --is-ancestor %s %s -> %s", sha, tracking, checked.returncode)
    if checked.returncode == _GIT_IS_ANCESTOR:
        return 0, f"{sha} is on {tracking}"
    if checked.returncode == _GIT_NOT_ANCESTOR:
        return 1, f"{sha} is not on {tracking}; release tags belong on {production!r} only"
    return 2, f"git merge-base failed: {checked.stderr.strip()}"


# --- CLI --------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_promotion.py",
        description="Gate the dev -> qa -> main branch promotion model.",
    )
    parser.add_argument(
        "--pyproject", type=Path, default=None,
        help="the pyproject.toml holding [tool.specgraph.promotion] (default: this repository's)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    branches = sub.add_parser("branches", help="print the configured roles")
    branches.add_argument("--role", choices=sorted(ROLE_KEYS))

    rte = sub.add_parser("route", help="check a pull request's route; emit the release tier")
    rte.add_argument("--event", required=True)
    rte.add_argument("--base", default="")
    rte.add_argument("--head", default="")
    rte.add_argument("--ref", default="")
    rte.add_argument("--head-repo", default="")
    rte.add_argument("--base-repo", default="")
    rte.add_argument(
        "--github-output", default=None,
        help="step-output file to append release-tier to (default: $GITHUB_OUTPUT, if set)",
    )

    tag = sub.add_parser("tag-ancestry", help="require a tagged commit to be on production")
    tag.add_argument("--sha", required=True)
    tag.add_argument("--remote", default="origin")
    tag.add_argument("--fetch", action="store_true", help="fetch the production branch first")

    agg = sub.add_parser("aggregate", help="the single required check over toJSON(needs)")
    agg.add_argument("--needs", required=True, help="a JSON file, or - for stdin")
    agg.add_argument("--event", required=True)
    agg.add_argument("--release-tier", default="false", help="the route job's release-tier output")
    agg.add_argument("--pull-request-only", action="append", default=[], metavar="JOB")
    agg.add_argument("--release-tier-only", action="append", default=[], metavar="JOB")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    pyproject = args.pyproject or repo_root() / "pyproject.toml"

    if args.command == "aggregate":
        # The one subcommand that needs no topology: the condition values
        # arrive already decided by the route job.
        try:
            needs = _read_needs(args.needs)
        except (OSError, ValueError) as exc:
            print(f"ERROR cannot read needs: {exc}", file=sys.stderr)
            return 2
        if not needs:
            print("ERROR needs is empty; an aggregate over nothing gates nothing", file=sys.stderr)
            return 2
        problems = aggregate(
            needs,
            event=args.event,
            release_tier=args.release_tier.strip().lower() == "true",
            pull_request_only=args.pull_request_only,
            release_tier_only=args.release_tier_only,
        )
        for problem in problems:
            print(f"FAIL {problem}")
        if problems:
            return 1
        print(f"PASS all {len(needs)} required job(s) green or legitimately skipped")
        return 0

    try:
        topology = load_topology(pyproject)
    except ConfigError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    if args.command == "branches":
        roles = topology.as_roles()
        if args.role:
            print(roles[args.role])
        else:
            for role, value in roles.items():
                print(f"{role}={value}")
        return 0

    if args.command == "route":
        verdict = route(
            topology,
            event=args.event,
            base=args.base,
            head=args.head,
            ref=args.ref,
            head_repo=args.head_repo,
            base_repo=args.base_repo,
        )
        output = args.github_output or os.environ.get("GITHUB_OUTPUT")
        if output:
            write_github_output(output, {"release-tier": str(verdict.release_tier).lower()})
        label = "WARN" if verdict.warned else ("PASS" if verdict.allowed else "FAIL")
        print(f"{label} {verdict.reason}")
        print(f"release-tier={str(verdict.release_tier).lower()}")
        return 0 if verdict.allowed else 1

    # tag-ancestry, the only command left.
    code, message = tag_ancestry(
        args.sha, topology.production, remote=args.remote, fetch=args.fetch
    )
    print(f"{('PASS', 'FAIL', 'ERROR')[code]} {message}", file=sys.stdout if code < 2 else sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
