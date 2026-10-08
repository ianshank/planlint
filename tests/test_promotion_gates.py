"""``tools/check_promotion.py``: ``aggregate`` and ``tag-ancestry`` (adopt-branch-promotion-model).

Split from ``tests/test_promotion.py`` by concern. ``aggregate`` is the
single required check, asserted against every way a run goes red;
``tag-ancestry`` against a real repository in the promotion shape and against
an injected git runner for the paths real git cannot be made to take.
"""

from __future__ import annotations

import io
import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType

import pytest

from tests.promotion_support import TOOL, git, promotion_tool, write_promotion_pyproject
from tests.promotion_support import needs as needs_of
from tests.support import captured_logger, run_tool_main


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return promotion_tool()


# --- aggregate ----------------------------------------------------------------


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
    results: dict[str, str], expected: list[str], tool: ModuleType
) -> None:
    needs = needs_of(build="success", **results)
    assert tool.aggregate(needs, event="push", release_tier=False) == expected


@pytest.mark.integration
def test_aggregate_accepts_a_conditional_job_skipped_when_its_condition_is_false(tool: ModuleType) -> None:
    needs = needs_of(build="success", graph_diff="skipped", release_tier="skipped")
    problems = tool.aggregate(
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
    event: str, tier: bool, job: str, tool: ModuleType
) -> None:
    needs = needs_of(build="success", graph_diff="success", release_tier="success")
    needs[job]["result"] = "skipped"
    problems = tool.aggregate(
        needs, event=event, release_tier=tier,
        pull_request_only=["graph-diff"], release_tier_only=["release-tier"],
    )
    assert problems == [f"{job}: skipped, but its condition held on this run"]


@pytest.mark.integration
def test_aggregate_names_a_declared_job_missing_from_needs(tool: ModuleType) -> None:
    problems = tool.aggregate(
        needs_of(build="success"), event="push", release_tier=False, release_tier_only=["gone"]
    )
    assert problems == ["gone: declared conditional but not in needs"]


@pytest.mark.integration
def test_aggregate_cli_reads_needs_and_logs_every_job(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The CLI path: a file of ``toJSON(needs)``, a verdict line, a DEBUG trail."""
    path = tmp_path / "needs.json"
    needs = needs_of(build="success", release_tier="skipped", promotion="success")
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
    needs = needs_of(promotion="success", release_tier="skipped")
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
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(needs_of(build="failure"))))
    code = run_tool_main("check_promotion", TOOL, "aggregate", "--needs", "-", "--event", "push",
                         pass_argv0=False)
    assert code == 1
    assert "FAIL build: failure" in capsys.readouterr().out


# --- tag-ancestry -------------------------------------------------------------


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
        git(repo, *identity, "commit", "--quiet", "--allow-empty", "-m", message)
        return git(repo, "rev-parse", "HEAD")

    git(repo, "init", "--quiet", "--initial-branch=live")
    trunk = commit("pre-model trunk release")
    git(repo, "checkout", "--quiet", "-b", "trunk")
    commit("feature a")
    feature_b = commit("feature b")
    git(repo, "checkout", "--quiet", "-b", "staging", trunk)
    git(repo, *identity, "merge", "--quiet", "--no-ff", "-m", "promote to staging", "trunk")
    git(repo, "checkout", "--quiet", "live")
    git(repo, *identity, "merge", "--quiet", "--no-ff", "-m", "promote to live", "staging")
    promoted = git(repo, "rev-parse", "HEAD")
    git(repo, *identity, "tag", "-a", "v9.9.9", "-m", "annotated", promoted)
    git(repo, "update-ref", "refs/remotes/origin/live", promoted)
    git(repo, "checkout", "--quiet", "trunk")
    never = commit("never promoted")
    pyproject = write_promotion_pyproject(tmp_path)
    monkeypatch.chdir(repo)

    def check(sha: str) -> int:
        return run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject),
                             "tag-ancestry", "--sha", sha, "--expect-production", "live",
                             pass_argv0=False)

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
def test_tag_ancestry_fetch_failure_is_exit_two(tool: ModuleType) -> None:
    """A fetch that fails answers nothing: exit 2, and nothing else is asked."""
    calls: list[list[str]] = []

    def runner(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        return subprocess.CompletedProcess(args, 128, "", "fatal: no remote")

    code, message = tool.tag_ancestry("abc", "live", remote="origin", fetch=True, runner=runner)
    assert (code, calls) == (
        2, [["git", "fetch", "--no-tags", "origin", "+refs/heads/live:refs/remotes/origin/live"]]
    )
    assert message == "could not fetch origin/live: fatal: no remote"


@pytest.mark.integration
def test_tag_ancestry_fetches_with_an_explicit_refspec_before_checking(tool: ModuleType) -> None:
    """The remote-tracking ref is updated whatever ``remote.<name>.fetch`` says."""
    calls: list[list[str]] = []

    def runner(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        stdout = "c0ffee\n" if args[1] in ("rev-parse", "rev-list") else ""
        return subprocess.CompletedProcess(args, 0, stdout, "")

    code, _ = tool.tag_ancestry("v1", "live", remote="upstream", fetch=True, runner=runner)
    assert code == 0
    assert calls == [
        ["git", "fetch", "--no-tags", "upstream", "+refs/heads/live:refs/remotes/upstream/live"],
        ["git", "rev-parse", "--verify", "--quiet", "v1^{commit}"],
        ["git", "rev-list", "--first-parent", "upstream/live"],
    ]


@pytest.mark.integration
def test_tag_ancestry_git_errors_are_exit_two(tool: ModuleType) -> None:
    """A rev-list or merge-base that errors is "could not answer", never a verdict."""
    def failing_at(step: str) -> Callable[[Sequence[str]], subprocess.CompletedProcess[str]]:
        def runner(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
            if args[1] == step:
                return subprocess.CompletedProcess(args, 128, "", "fatal: boom")
            stdout = "c0ffee\n" if args[1] == "rev-parse" else "other\n"
            return subprocess.CompletedProcess(args, 0, stdout, "")
        return runner

    code, message = tool.tag_ancestry("v1", "live", remote="o", fetch=False, runner=failing_at("rev-list"))
    assert (code, message) == (2, "cannot list o/live: fatal: boom")
    code, message = tool.tag_ancestry("v1", "live", remote="o", fetch=False, runner=failing_at("merge-base"))
    assert (code, message) == (2, "git merge-base failed: fatal: boom")


@pytest.mark.integration
def test_aggregate_names_a_malformed_needs_entry(tool: ModuleType) -> None:
    problems = tool.aggregate({"build": {"result": "success"}, "odd": ["not", "a", "mapping"]},
                              event="push", release_tier=False)
    assert problems == ["odd: malformed needs entry (list)"]


@pytest.mark.integration
def test_an_undecided_tier_still_names_every_failed_job(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The promotion job died before writing its output: say so AND name the rest."""
    data = needs_of(promotion="failure", test="failure", release_tier="skipped")
    path = tmp_path / "needs.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    code = run_tool_main(
        "check_promotion", TOOL, "aggregate", "--needs", str(path), "--event", "pull_request",
        "--release-tier-from", "promotion", "--release-tier-only", "release-tier", pass_argv0=False,
    )
    captured = capsys.readouterr()
    assert code == 2
    for line in ("FAIL promotion: failure", "FAIL test: failure", "FAIL release-tier: skipped"):
        assert line in captured.out
    assert "promotion.outputs.release-tier must be" in captured.err


@pytest.mark.integration
@pytest.mark.parametrize("sha", ["-x", "--all", " "])
def test_tag_ancestry_refuses_an_option_shaped_sha(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], sha: str
) -> None:
    code = run_tool_main("check_promotion", TOOL, "--pyproject", str(write_promotion_pyproject(tmp_path)),
                         "tag-ancestry", f"--sha={sha}", pass_argv0=False)
    assert code == 2
    assert "--sha must name a commit" in capsys.readouterr().err


@pytest.mark.integration
def test_tag_ancestry_refuses_a_production_branch_that_is_not_the_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Configuration from a tree the tag's author controls must agree with the repository."""
    code = run_tool_main("check_promotion", TOOL, "--pyproject", str(write_promotion_pyproject(tmp_path)),
                         "tag-ancestry", "--sha", "abc", "--expect-production", "main", pass_argv0=False)
    assert code == 2
    assert "configured production branch 'live' is not the expected 'main'" in capsys.readouterr().err
