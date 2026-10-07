"""``tools/check_promotion.py``: the branch promotion model, as a gate.

adopt-branch-promotion-model. Each subcommand is asserted in-process against
``main(argv)`` or its pure function, both directions: a permitted route and a
refused one, a green aggregate and every way one goes red. The topology is
always read from a ``pyproject.toml`` the test writes, with role names that
are deliberately *not* this repository's, so a branch name hard-coded in the
tool would fail here rather than pass by coincidence.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.support import captured_logger, load_tool, run_tool_main

TOOL = "check_promotion.py"

#: Role names unlike this repository's, so a literal in the tool cannot pass.
ROLES = {
    "integration_branch": "trunk",
    "candidate_branch": "staging",
    "production_branch": "live",
    "hotfix_prefix": "urgent/",
}


def _tool():  # type: ignore[no-untyped-def]
    return load_tool("check_promotion", TOOL)


def _pyproject(tmp_path: Path, roles: dict[str, str] | None = None, *, extra: str = "") -> Path:
    body = "\n".join(f'{key} = "{value}"  # role' for key, value in (roles or ROLES).items())
    path = tmp_path / "pyproject.toml"
    path.write_text(
        f'[tool.other]\nproduction_branch = "decoy"\n\n[tool.specgraph.promotion]\n{body}\n{extra}',
        encoding="utf-8",
    )
    return path


def _topology(tmp_path: Path):  # type: ignore[no-untyped-def]
    return _tool().load_topology(_pyproject(tmp_path))


# --- configuration ------------------------------------------------------------


@pytest.mark.integration
def test_promotion_config_reads_every_role_from_pyproject(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every role comes from its own table; a same-named key elsewhere is ignored."""
    pyproject = _pyproject(tmp_path)
    assert run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "branches",
                         pass_argv0=False) == 0
    printed = capsys.readouterr().out.splitlines()
    assert printed == [
        "integration=trunk", "candidate=staging", "production=live", "hotfix_prefix=urgent/"
    ]
    assert run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "branches",
                         "--role", "production", pass_argv0=False) == 0
    assert capsys.readouterr().out.strip() == "live"


@pytest.mark.integration
@pytest.mark.parametrize(
    "roles,needle",
    [
        ({k: v for k, v in ROLES.items() if k != "candidate_branch"}, "candidate_branch"),
        ({**ROLES, "production_branch": ""}, "production_branch"),
        ({**ROLES, "candidate_branch": "trunk"}, "must differ"),
        ({**ROLES, "candidate_branch": "urgent/qa"}, "hotfix_prefix"),
    ],
    ids=["missing", "empty", "duplicate", "under-hotfix-prefix"],
)
def test_promotion_config_missing_key_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], roles: dict[str, str], needle: str
) -> None:
    """An unreadable topology is exit 2 naming the problem -- never a pass."""
    pyproject = _pyproject(tmp_path, roles)
    for command in (["branches"], ["route", "--event", "push", "--ref", "refs/heads/live"]):
        code = run_tool_main(
            "check_promotion", TOOL, "--pyproject", str(pyproject), *command, pass_argv0=False
        )
        assert code == 2, command
        assert needle in capsys.readouterr().err


@pytest.mark.integration
def test_promotion_config_absent_file_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run_tool_main("check_promotion", TOOL, "--pyproject", str(tmp_path / "nope.toml"),
                         "branches", pass_argv0=False)
    assert code == 2
    assert "[tool.specgraph.promotion]" in capsys.readouterr().err


@pytest.mark.integration
def test_this_repository_declares_a_readable_topology() -> None:
    """The committed table parses: CI's route job reads it on every run."""
    tool = _tool()
    topology = tool.load_topology(Path(tool.__file__).resolve().parent.parent / "pyproject.toml")
    assert len({topology.integration, topology.candidate, topology.production}) == 3


# --- route --------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize(
    "base,head,allowed",
    [
        ("staging", "trunk", True),
        ("staging", "feature/x", False),
        ("staging", "live", False),
        ("live", "staging", True),
        ("live", "urgent/cve-fix", True),
        ("live", "trunk", False),
        ("live", "dependabot/pip/x", False),
        ("trunk", "feature/x", True),
        ("trunk", "sync/live-into-trunk", True),
        ("some-other-base", "anything", True),
    ],
)
def test_route_allows_only_the_declared_sources_into_protected_branches(
    tmp_path: Path, base: str, head: str, allowed: bool
) -> None:
    verdict = _tool().route(_topology(tmp_path), event="pull_request", base=base, head=head)
    assert verdict.allowed is allowed, verdict.reason
    if not allowed:
        assert repr(head) in verdict.reason and repr(base) in verdict.reason


@pytest.mark.integration
@pytest.mark.parametrize("base,expected", [("staging", False), ("live", False), ("trunk", True)])
def test_route_rejects_a_cross_repository_head_into_a_protected_branch(
    tmp_path: Path, base: str, expected: bool
) -> None:
    """A fork's branch named like the candidate is still a fork's branch."""
    head = {"staging": "trunk", "live": "staging", "trunk": "feature/x"}[base]
    verdict = _tool().route(
        _topology(tmp_path), event="pull_request", base=base, head=head,
        head_repo="someone/fork", base_repo="owner/repo",
    )
    assert verdict.allowed is expected, verdict.reason
    same_repo = _tool().route(
        _topology(tmp_path), event="pull_request", base=base, head=head,
        head_repo="owner/repo", base_repo="owner/repo",
    )
    assert same_repo.allowed


@pytest.mark.integration
@pytest.mark.parametrize("base", ["staging", "live"])
def test_route_treats_an_unknown_head_repository_as_foreign(tmp_path: Path, base: str) -> None:
    """GitHub reports a deleted fork's head repository as null: that is not "this repository"."""
    head = {"staging": "trunk", "live": "staging"}[base]
    verdict = _tool().route(_topology(tmp_path), event="pull_request", base=base, head=head,
                            head_repo="", base_repo="owner/repo")
    assert not verdict.allowed
    assert "an unknown repository" in verdict.reason and repr(head) in verdict.reason
    # A base outside the protected pair is still open to anyone.
    assert _tool().route(_topology(tmp_path), event="pull_request", base="trunk", head="x",
                         head_repo="", base_repo="owner/repo").allowed


@pytest.mark.integration
@pytest.mark.parametrize("value", ["false", "'false'", "true", "False"])
def test_route_enforcement_refuses_an_unreadable_switch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], value: str
) -> None:
    """Valid TOML the reader does not read must not silently mean "enforced"."""
    pyproject = _pyproject(tmp_path, extra=f"enforce_routes = {value}\n")
    assert run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "branches",
                         pass_argv0=False) == 2
    assert "enforce_routes must be written" in capsys.readouterr().err


@pytest.mark.integration
def test_promotion_config_does_not_read_past_a_commented_table_header(tmp_path: Path) -> None:
    """A ``[table]  # comment`` header ends the promotion table: its keys do not leak in."""
    pyproject = _pyproject(tmp_path, extra='[tool.after]  # a comment\nenforce_routes = "false"\n')
    assert _tool().load_topology(pyproject).enforce_routes is True


@pytest.mark.integration
@pytest.mark.parametrize(
    "kwargs,tier",
    [
        ({"event": "pull_request", "base": "staging", "head": "trunk"}, True),
        ({"event": "pull_request", "base": "live", "head": "staging"}, True),
        ({"event": "pull_request", "base": "trunk", "head": "feature/x"}, False),
        ({"event": "pull_request_target", "base": "live", "head": "staging"}, True),
        ({"event": "push", "ref": "refs/heads/staging"}, True),
        ({"event": "push", "ref": "refs/heads/live"}, True),
        ({"event": "push", "ref": "refs/heads/trunk"}, False),
        ({"event": "push", "ref": "refs/tags/v9.9.9"}, False),
        ({"event": "workflow_dispatch", "ref": "refs/heads/live"}, True),
        ({"event": "schedule", "ref": ""}, False),
    ],
)
def test_route_selects_the_release_tier_for_candidate_and_production(
    tmp_path: Path, kwargs: dict[str, str], tier: bool
) -> None:
    verdict = _tool().route(_topology(tmp_path), **kwargs)
    assert verdict.release_tier is tier
    assert verdict.allowed


@pytest.mark.integration
def test_route_writes_github_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tier reaches later jobs through the step-output file, refused or not."""
    pyproject = _pyproject(tmp_path)
    output = tmp_path / "out.txt"
    output.write_text("earlier=kept\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    code = run_tool_main(
        "check_promotion", TOOL, "--pyproject", str(pyproject), "route", "--event", "pull_request",
        "--base", "live", "--head", "trunk", pass_argv0=False,
    )
    assert code == 1
    assert output.read_text(encoding="utf-8") == "earlier=kept\nrelease-tier=true\n"
    out = capsys.readouterr().out
    assert out.startswith("FAIL 'trunk' may not target 'live'")

    explicit = tmp_path / "explicit.txt"
    code = run_tool_main(
        "check_promotion", TOOL, "--pyproject", str(pyproject), "route", "--event", "push",
        "--ref", "refs/heads/trunk", "--github-output", str(explicit), pass_argv0=False,
    )
    assert code == 0
    assert explicit.read_text(encoding="utf-8") == "release-tier=false\n"
    assert "PASS" in capsys.readouterr().out


@pytest.mark.integration
def test_route_without_github_output_only_prints(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    code = run_tool_main(
        "check_promotion", TOOL, "--pyproject", str(_pyproject(tmp_path)), "route",
        "--event", "pull_request", "--base", "staging", "--head", "trunk", pass_argv0=False,
    )
    assert code == 0
    assert capsys.readouterr().out.splitlines()[-1] == "release-tier=true"


@pytest.mark.integration
def test_route_with_enforcement_off_warns_instead_of_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The bootstrap switch (DEC-BPM-013): a refused route is reported, not failed.

    The tier is decided exactly as when enforced, and a permitted route is not
    marked as a warning.
    """
    pyproject = _pyproject(tmp_path, extra='enforce_routes = "false"\n')
    topology = _tool().load_topology(pyproject)
    assert topology.enforce_routes is False
    refused = _tool().route(topology, event="pull_request", base="live", head="feature/x")
    assert (refused.allowed, refused.warned, refused.release_tier) == (True, True, True)
    assert "not enforced" in refused.reason and "'feature/x' may not target 'live'" in refused.reason
    fork = _tool().route(topology, event="pull_request", base="staging", head="trunk",
                         head_repo="someone/fork", base_repo="owner/repo")
    assert (fork.allowed, fork.warned) == (True, True)
    permitted = _tool().route(topology, event="pull_request", base="live", head="staging")
    assert (permitted.allowed, permitted.warned) == (True, False)

    code = run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "route",
                         "--event", "pull_request", "--base", "live", "--head", "feature/x",
                         "--github-output", str(tmp_path / "o"), pass_argv0=False)
    assert code == 0
    assert capsys.readouterr().out.startswith("WARN 'feature/x' may not target 'live'")


@pytest.mark.integration
@pytest.mark.parametrize("value,enforced", [('"true"', True), (None, True)], ids=["true", "absent"])
def test_route_enforcement_defaults_on(tmp_path: Path, value: str | None, enforced: bool) -> None:
    """Absent means enforced: a table that forgets the key fails closed."""
    extra = f"enforce_routes = {value}\n" if value else ""
    topology = _tool().load_topology(_pyproject(tmp_path, extra=extra))
    assert topology.enforce_routes is enforced
    assert not _tool().route(topology, event="pull_request", base="live", head="trunk").allowed


@pytest.mark.integration
def test_route_enforcement_rejects_a_non_boolean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pyproject = _pyproject(tmp_path, extra='enforce_routes = "yes"\n')
    assert run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "branches",
                         pass_argv0=False) == 2
    assert 'enforce_routes must be "true" or "false"' in capsys.readouterr().err


# --- aggregate ----------------------------------------------------------------


def _needs(**results: str) -> dict[str, dict[str, object]]:
    return {job.replace("_", "-"): {"result": result, "outputs": {}} for job, result in results.items()}


@pytest.mark.integration
@pytest.mark.parametrize(
    "results,expected",
    [
        ({"lint": "failure"}, ["lint: failure"]),
        ({"lint": "cancelled"}, ["lint: cancelled"]),
        ({"lint": "skipped"}, ["lint: skipped, but its condition held on this run"]),
        ({"lint": "weird"}, ["lint: weird"]),
    ],
)
def test_aggregate_fails_on_failure_cancelled_and_unexpected_skip(
    results: dict[str, str], expected: list[str]
) -> None:
    needs = _needs(build="success", **results)
    assert _tool().aggregate(needs, event="push", release_tier=False) == expected


@pytest.mark.integration
def test_aggregate_accepts_a_conditional_job_skipped_when_its_condition_is_false() -> None:
    needs = _needs(build="success", graph_diff="skipped", release_tier="skipped")
    problems = _tool().aggregate(
        needs, event="push", release_tier=False,
        pull_request_only=["graph-diff"], release_tier_only=["release-tier"],
    )
    assert problems == []


@pytest.mark.integration
@pytest.mark.parametrize(
    "event,tier,job",
    [("pull_request", False, "graph-diff"), ("push", True, "release-tier")],
)
def test_aggregate_fails_a_conditional_job_skipped_when_its_condition_is_true(
    event: str, tier: bool, job: str
) -> None:
    needs = _needs(build="success", graph_diff="success", release_tier="success")
    needs[job]["result"] = "skipped"
    problems = _tool().aggregate(
        needs, event=event, release_tier=tier,
        pull_request_only=["graph-diff"], release_tier_only=["release-tier"],
    )
    assert problems == [f"{job}: skipped, but its condition held on this run"]


@pytest.mark.integration
def test_aggregate_names_a_declared_job_missing_from_needs() -> None:
    problems = _tool().aggregate(
        _needs(build="success"), event="push", release_tier=False, release_tier_only=["gone"]
    )
    assert problems == ["gone: declared conditional but not in needs"]


@pytest.mark.integration
def test_aggregate_cli_reads_needs_and_logs_every_job(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The CLI path: a file of ``toJSON(needs)``, a verdict line, a DEBUG trail."""
    path = tmp_path / "needs.json"
    needs = _needs(build="success", release_tier="skipped", promotion="success")
    needs["promotion"]["outputs"] = {"release-tier": "false"}
    path.write_text(json.dumps(needs), encoding="utf-8")
    args = ("aggregate", "--needs", str(path), "--event", "pull_request",
            "--release-tier-from", "promotion", "--release-tier-only", "release-tier")
    with captured_logger(caplog, "planlint.tools"):
        code = run_tool_main("check_promotion", TOOL, *args, pass_argv0=False)
    assert code == 0
    assert capsys.readouterr().out.startswith("PASS all 3 required job(s)")
    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "build -> success" in logged and "release-tier -> skipped" in logged

    needs["promotion"]["outputs"] = {"release-tier": "true"}
    path.write_text(json.dumps(needs), encoding="utf-8")
    assert run_tool_main("check_promotion", TOOL, *args, pass_argv0=False) == 1
    assert "FAIL release-tier: skipped" in capsys.readouterr().out


@pytest.mark.integration
@pytest.mark.parametrize(
    "outputs,extra",
    [
        ({"release-tier": ""}, ()),
        ({}, ()),
        ({"release-tier": "TRUE"}, ()),
        ({"release-tier": ["true"]}, ()),
        ({"release-tier": "false"}, ("--release-tier-from", "absent-job")),
        ({"release-tier": "false"}, ("--no-source",)),
    ],
    ids=["empty", "missing", "wrong-case", "not-a-string", "unknown-job", "no-source"],
)
def test_aggregate_refuses_an_undecided_release_tier(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    outputs: dict[str, object], extra: tuple[str, ...],
) -> None:
    """An empty tier output (a renamed step id) is exit 2, never "no release tier".

    Read as false, it would excuse the skipped release-tier job it failed to start
    and turn ci-ok green.
    """
    needs = _needs(promotion="success", release_tier="skipped")
    needs["promotion"]["outputs"] = outputs
    path = tmp_path / "needs.json"
    path.write_text(json.dumps(needs), encoding="utf-8")
    source = () if extra == ("--no-source",) else (extra or ("--release-tier-from", "promotion"))
    code = run_tool_main(
        "check_promotion", TOOL, "aggregate", "--needs", str(path), "--event", "push",
        *source, "--release-tier-only", "release-tier", pass_argv0=False,
    )
    assert code == 2
    assert "ERROR" in capsys.readouterr().err


@pytest.mark.integration
@pytest.mark.parametrize("content", ["", "[]", "{}", "not json"], ids=["blank", "list", "empty", "garbage"])
def test_aggregate_cli_refuses_unusable_needs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: str
) -> None:
    """Nothing to aggregate is exit 2, never a pass over zero jobs."""
    path = tmp_path / "needs.json"
    path.write_text(content, encoding="utf-8")
    code = run_tool_main("check_promotion", TOOL, "aggregate", "--needs", str(path),
                         "--event", "push", pass_argv0=False)
    assert code == 2
    assert capsys.readouterr().err.startswith("ERROR")


@pytest.mark.integration
def test_aggregate_cli_reads_stdin(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_needs(build="failure"))))
    code = run_tool_main("check_promotion", TOOL, "aggregate", "--needs", "-", "--event", "push",
                         pass_argv0=False)
    assert code == 1
    assert "FAIL build: failure" in capsys.readouterr().out


# --- tag-ancestry -------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout.strip()


@pytest.mark.e2e
def test_tag_ancestry_accepts_a_commit_on_production_and_rejects_one_off_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real git, the real promotion shape: only production's own commits pass.

    trunk ``R`` (from before the model) -> integration commits ``A``, ``B``
    -> ``--no-ff`` merge into the candidate -> ``--no-ff`` merge ``M`` into
    production. ``M`` and ``R`` are first-parent commits of production and pass;
    ``B`` is an *ancestor* of production but reached it only through a merge's
    second parent -- it never ran the release tier -- and is refused; a commit
    never promoted is refused; an annotated tag on ``M`` is peeled and passes.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    identity = ("-c", "user.name=t", "-c", "user.email=t@example.invalid",
                "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false")

    def commit(message: str) -> str:
        _git(repo, *identity, "commit", "--quiet", "--allow-empty", "-m", message)
        return _git(repo, "rev-parse", "HEAD")

    _git(repo, "init", "--quiet", "--initial-branch=live")
    trunk = commit("pre-model trunk release")
    _git(repo, "checkout", "--quiet", "-b", "trunk")
    commit("feature a")
    feature_b = commit("feature b")
    _git(repo, "checkout", "--quiet", "-b", "staging", trunk)
    _git(repo, *identity, "merge", "--quiet", "--no-ff", "-m", "promote to staging", "trunk")
    _git(repo, "checkout", "--quiet", "live")
    _git(repo, *identity, "merge", "--quiet", "--no-ff", "-m", "promote to live", "staging")
    promoted = _git(repo, "rev-parse", "HEAD")
    _git(repo, *identity, "tag", "-a", "v9.9.9", "-m", "annotated", promoted)
    _git(repo, "update-ref", "refs/remotes/origin/live", promoted)
    _git(repo, "checkout", "--quiet", "trunk")
    never = commit("never promoted")
    pyproject = _pyproject(tmp_path)
    monkeypatch.chdir(repo)

    def check(sha: str) -> int:
        return run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject),
                             "tag-ancestry", "--sha", sha, pass_argv0=False)

    for sha in (promoted, trunk, "v9.9.9"):
        assert check(sha) == 0, sha
        assert "is a commit origin/live itself held" in capsys.readouterr().out
    assert check(feature_b) == 1
    assert "only through a promotion merge's second parent" in capsys.readouterr().out
    assert check(never) == 1
    assert "release tags belong on 'live' only" in capsys.readouterr().out
    assert check("0" * 40) == 2
    assert "cannot resolve" in capsys.readouterr().err


@pytest.mark.integration
def test_tag_ancestry_fetch_failure_is_exit_two() -> None:
    """A fetch that fails answers nothing: exit 2, and nothing else is asked."""
    calls: list[list[str]] = []

    def runner(args):  # type: ignore[no-untyped-def]
        calls.append(list(args))
        return subprocess.CompletedProcess(args, 128, "", "fatal: no remote")

    code, message = _tool().tag_ancestry("abc", "live", remote="origin", fetch=True, runner=runner)
    assert (code, calls) == (
        2, [["git", "fetch", "--no-tags", "origin", "+refs/heads/live:refs/remotes/origin/live"]]
    )
    assert message == "could not fetch origin/live: fatal: no remote"


@pytest.mark.integration
def test_tag_ancestry_fetches_with_an_explicit_refspec_before_checking() -> None:
    """The remote-tracking ref is updated whatever ``remote.<name>.fetch`` says."""
    calls: list[list[str]] = []

    def runner(args):  # type: ignore[no-untyped-def]
        calls.append(list(args))
        stdout = "c0ffee\n" if args[1] in ("rev-parse", "rev-list") else ""
        return subprocess.CompletedProcess(args, 0, stdout, "")

    code, _ = _tool().tag_ancestry("v1", "live", remote="upstream", fetch=True, runner=runner)
    assert code == 0
    assert calls == [
        ["git", "fetch", "--no-tags", "upstream", "+refs/heads/live:refs/remotes/upstream/live"],
        ["git", "rev-parse", "--verify", "--quiet", "v1^{commit}"],
        ["git", "rev-list", "--first-parent", "upstream/live"],
    ]


@pytest.mark.integration
def test_tag_ancestry_git_errors_are_exit_two() -> None:
    """A rev-list or merge-base that errors is "could not answer", never a verdict."""
    def failing_at(step: str):  # type: ignore[no-untyped-def]
        def runner(args):  # type: ignore[no-untyped-def]
            if args[1] == step:
                return subprocess.CompletedProcess(args, 128, "", "fatal: boom")
            stdout = "c0ffee\n" if args[1] == "rev-parse" else "other\n"
            return subprocess.CompletedProcess(args, 0, stdout, "")
        return runner

    code, message = _tool().tag_ancestry("v1", "live", remote="o", fetch=False, runner=failing_at("rev-list"))
    assert (code, message) == (2, "cannot list o/live: fatal: boom")
    code, message = _tool().tag_ancestry("v1", "live", remote="o", fetch=False, runner=failing_at("merge-base"))
    assert (code, message) == (2, "git merge-base failed: fatal: boom")
