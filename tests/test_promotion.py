"""``tools/check_promotion.py``: configuration and the route (adopt-branch-promotion-model).

Each case is asserted in-process against ``main(argv)`` or the pure function,
both directions: a permitted route and a refused one. The topology is read
from a ``pyproject.toml`` the test writes with role names unlike this
repository's (``tests/promotion_support.py``). ``aggregate`` and
``tag-ancestry`` live in ``tests/test_promotion_gates.py``.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest

from tests.promotion_support import ROLES, TOOL, promotion_tool, write_promotion_pyproject
from tests.support import run_tool_main


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    """Loaded once per module rather than re-executed in every call."""
    return promotion_tool()


def _pyproject(tmp_path: Path, roles: dict[str, str] | None = None, *, extra: str = "") -> Path:
    return write_promotion_pyproject(tmp_path, roles, extra=extra)


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
def test_this_repository_declares_a_readable_topology(tool: ModuleType) -> None:
    """The committed table parses: CI's route job reads it on every run."""
    topology = tool.load_topology(Path(__file__).resolve().parent.parent / "pyproject.toml")
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
    tmp_path: Path, base: str, head: str, allowed: bool, tool: ModuleType
) -> None:
    verdict = tool.route(tool.load_topology(_pyproject(tmp_path)), event="pull_request", base=base, head=head)
    assert verdict.allowed is allowed, verdict.reason
    if not allowed:
        assert repr(head) in verdict.reason and repr(base) in verdict.reason


@pytest.mark.integration
@pytest.mark.parametrize("base,expected", [("staging", False), ("live", False), ("trunk", True)])
def test_route_rejects_a_cross_repository_head_into_a_protected_branch(
    tmp_path: Path, base: str, expected: bool, tool: ModuleType
) -> None:
    """A fork's branch named like the candidate is still a fork's branch."""
    head = {"staging": "trunk", "live": "staging", "trunk": "feature/x"}[base]
    verdict = tool.route(
        tool.load_topology(_pyproject(tmp_path)), event="pull_request", base=base, head=head,
        head_repo="someone/fork", base_repo="owner/repo",
    )
    assert verdict.allowed is expected, verdict.reason
    same_repo = tool.route(
        tool.load_topology(_pyproject(tmp_path)), event="pull_request", base=base, head=head,
        head_repo="owner/repo", base_repo="owner/repo",
    )
    assert same_repo.allowed


@pytest.mark.integration
@pytest.mark.parametrize("base", ["staging", "live"])
def test_route_treats_an_unknown_head_repository_as_foreign(tmp_path: Path, base: str, tool: ModuleType) -> None:
    """GitHub reports a deleted fork's head repository as null: that is not "this repository"."""
    head = {"staging": "trunk", "live": "staging"}[base]
    verdict = tool.route(tool.load_topology(_pyproject(tmp_path)), event="pull_request", base=base, head=head,
                            head_repo="", base_repo="owner/repo")
    assert not verdict.allowed
    assert "an unknown repository" in verdict.reason and repr(head) in verdict.reason
    # A base outside the protected pair is still open to anyone.
    assert tool.route(tool.load_topology(_pyproject(tmp_path)), event="pull_request", base="trunk", head="x",
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
def test_promotion_config_does_not_read_past_a_commented_table_header(tmp_path: Path, tool: ModuleType) -> None:
    """A ``[table]  # comment`` header ends the promotion table: its keys do not leak in."""
    pyproject = _pyproject(tmp_path, extra='[tool.after]  # a comment\nenforce_routes = "false"\n')
    assert tool.load_topology(pyproject).enforce_routes is True


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
        ({"event": "schedule", "ref": "refs/heads/trunk"}, False),
    ],
)
def test_route_selects_the_release_tier_for_candidate_and_production(
    tmp_path: Path, kwargs: dict[str, str], tier: bool, tool: ModuleType
) -> None:
    verdict = tool.route(tool.load_topology(_pyproject(tmp_path)), **kwargs)
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
        "check_promotion", TOOL, "--pyproject", str(pyproject), "route", "--event", "pull_request", "--base-repo", "o/r", "--head-repo", "o/r",
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
        "--event", "pull_request", "--base-repo", "o/r", "--head-repo", "o/r", "--base", "staging", "--head", "trunk", pass_argv0=False,
    )
    assert code == 0
    assert capsys.readouterr().out.splitlines()[-1] == "release-tier=true"


@pytest.mark.integration
def test_route_with_enforcement_off_warns_instead_of_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], tool: ModuleType
) -> None:
    """The bootstrap switch (DEC-BPM-013): a refused route is reported, not failed.

    The tier is decided exactly as when enforced, and a permitted route is not
    marked as a warning.
    """
    pyproject = _pyproject(tmp_path, extra='enforce_routes = "false"\n')
    topology = tool.load_topology(pyproject)
    assert topology.enforce_routes is False
    refused = tool.route(topology, event="pull_request", base="live", head="feature/x")
    assert (refused.allowed, refused.warned, refused.release_tier) == (True, True, True)
    assert "not enforced" in refused.reason and "'feature/x' may not target 'live'" in refused.reason
    fork = tool.route(topology, event="pull_request", base="staging", head="trunk",
                         head_repo="someone/fork", base_repo="owner/repo")
    assert (fork.allowed, fork.warned) == (True, True)
    permitted = tool.route(topology, event="pull_request", base="live", head="staging")
    assert (permitted.allowed, permitted.warned) == (True, False)

    code = run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "route",
                         "--event", "pull_request", "--base-repo", "o/r", "--head-repo", "o/r", "--base", "live", "--head", "feature/x",
                         "--github-output", str(tmp_path / "o"), pass_argv0=False)
    assert code == 0
    assert capsys.readouterr().out.startswith("WARN 'feature/x' may not target 'live'")


@pytest.mark.integration
@pytest.mark.parametrize("value,enforced", [('"true"', True), (None, True)], ids=["true", "absent"])
def test_route_enforcement_defaults_on(tmp_path: Path, value: str | None, enforced: bool, tool: ModuleType) -> None:
    """Absent means enforced: a table that forgets the key fails closed."""
    extra = f"enforce_routes = {value}\n" if value else ""
    topology = tool.load_topology(_pyproject(tmp_path, extra=extra))
    assert topology.enforce_routes is enforced
    assert not tool.route(topology, event="pull_request", base="live", head="trunk").allowed


@pytest.mark.integration
def test_route_enforcement_rejects_a_non_boolean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pyproject = _pyproject(tmp_path, extra='enforce_routes = "yes"\n')
    assert run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "branches",
                         pass_argv0=False) == 2
    assert 'enforce_routes must be "true" or "false"' in capsys.readouterr().err




@pytest.mark.integration
@pytest.mark.parametrize(
    "args",
    [
        ("--base", "", "--head", "trunk", "--base-repo", "o/r"),
        ("--base", "staging", "--head", "", "--base-repo", "o/r"),
        ("--base", "staging", "--head", "trunk"),
    ],
    ids=["empty-base", "empty-head", "no-base-repo"],
)
def test_route_refuses_an_incomplete_pull_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], args: tuple[str, ...]
) -> None:
    """An empty base would read as "no protected base": pass the route, skip the tier.

    That is the one way the route could fail open, so it is exit 2, never a pass.
    """
    code = run_tool_main("check_promotion", TOOL, "--pyproject", str(_pyproject(tmp_path)), "route",
                         "--event", "pull_request", *args, "--github-output", str(tmp_path / "o"),
                         pass_argv0=False)
    assert code == 2
    assert capsys.readouterr().err.startswith("ERROR")
    assert not (tmp_path / "o").exists(), "no tier may be emitted for a route that was not judged"


@pytest.mark.integration
def test_route_rejects_an_empty_base_in_process(tmp_path: Path, tool: ModuleType) -> None:
    topology = tool.load_topology(_pyproject(tmp_path))
    with pytest.raises(ValueError, match="needs both --base and --head"):
        tool.route(topology, event="pull_request", base="", head="x")
    with pytest.raises(ValueError, match="needs both --base and --head"):
        tool.route(topology, event="pull_request", base="  ", head="x")
    for event in ("push", "workflow_dispatch", "schedule"):
        with pytest.raises(ValueError, match="needs --ref"):
            tool.route(topology, event=event, ref="")


@pytest.mark.integration
def test_a_bare_hotfix_prefix_is_not_a_hotfix(tmp_path: Path, tool: ModuleType) -> None:
    topology = tool.load_topology(_pyproject(tmp_path))
    assert not tool.route(topology, event="pull_request", base="live", head="urgent/").allowed
    assert tool.route(topology, event="pull_request", base="live", head="urgent/x").allowed


@pytest.mark.integration
@pytest.mark.parametrize("line", ['"enforce_routes" = "false"', "'enforce_routes' = \"false\"", 'enforce_routes = ""'])
def test_route_enforcement_refuses_a_quoted_key_or_empty_value(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], line: str
) -> None:
    """The same TOML key written another way must not silently read as absent."""
    pyproject = _pyproject(tmp_path, extra=f"{line}\n")
    assert run_tool_main("check_promotion", TOOL, "--pyproject", str(pyproject), "branches",
                         pass_argv0=False) == 2
    assert "enforce_routes" in capsys.readouterr().err


@pytest.mark.integration
def test_route_logs_its_inputs_at_debug(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, tool: ModuleType
) -> None:
    from tests.support import captured_logger

    with captured_logger(caplog, "planlint.tools"):
        tool.route(tool.load_topology(_pyproject(tmp_path)), event="pull_request",
                   base="staging", head="trunk", base_repo="o/r", head_repo="o/r")
    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "base='staging'" in logged and "head='trunk'" in logged
