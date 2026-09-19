"""Behavioural tests for the ``tools/`` gate scripts' own decision logic.

These scripts are what ``make pre-pr`` and the workflows run, so a gate that
cannot fail is worse than no gate: it reports PASS on the thing it was added
to catch. Three of them had never been shown to fire.

Each script's ``main()`` is called in-process (see ``run_tool_main``), because
a subprocess's execution is invisible to coverage and these had therefore all
read 0% while looking tested. The ``python tools/<script>.py`` invocation path
is covered once for the whole directory by
``test_ci_hardening.test_gate_script_is_runnable_as_a_script``.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.support import load_tool, run_tool_main

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"


# --- check_docs.py: the required-doc set is present AND linked ---------------


def _docs_fixture(root: Path, *, omit: str | None = None, unlinked: str | None = None) -> Path:
    """Build a tree that satisfies check_docs, minus one deliberate defect."""
    check_docs = load_tool("check_docs_fixture", "check_docs.py")
    linked = []
    for doc in check_docs.REQUIRED_DOCS:
        if doc == omit:
            continue
        path = root / doc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {doc}\n", encoding="utf-8")
        if doc != unlinked:
            linked.append(doc)
    body = "# README\n\n" + "\n".join(f"- [{d}]({d})" for d in linked) + "\n"
    (root / "README.md").write_text(body, encoding="utf-8")
    return root


def test_docs_check_passes_when_every_doc_is_present_and_linked(tmp_path: Path) -> None:
    check_docs = load_tool("check_docs_pass", "check_docs.py")
    assert check_docs.check(_docs_fixture(tmp_path)) == []


def test_docs_check_reports_a_missing_doc(tmp_path: Path) -> None:
    check_docs = load_tool("check_docs_missing", "check_docs.py")
    problems = check_docs.check(_docs_fixture(tmp_path, omit="SECURITY.md"))
    assert problems == ["MISSING: SECURITY.md"]


def test_docs_check_reports_a_present_but_unlinked_doc(tmp_path: Path) -> None:
    """Present-but-unlinked is the whole point of the gate: a doc a new
    contributor cannot reach from the front page is effectively absent, and
    an existence-only check would report PASS on it."""
    check_docs = load_tool("check_docs_unlinked", "check_docs.py")
    problems = check_docs.check(_docs_fixture(tmp_path, unlinked="docs/aqa.md"))
    assert problems == ["UNLINKED: docs/aqa.md not referenced in README.md"]


def test_docs_check_main_exits_1_on_a_defect_and_0_when_clean(tmp_path: Path, capsys) -> None:
    check_docs = load_tool("check_docs_main", "check_docs.py")
    assert check_docs.main(["check_docs.py"], _docs_fixture(tmp_path, omit="AGENTS.md")) == 1
    assert "FAIL: MISSING: AGENTS.md" in capsys.readouterr().out

    clean = tmp_path / "clean"
    clean.mkdir()
    assert check_docs.main(["check_docs.py"], _docs_fixture(clean)) == 0
    assert "all required docs present and linked" in capsys.readouterr().out


def test_docs_check_treats_a_missing_readme_as_every_doc_unlinked(tmp_path: Path) -> None:
    """No README at all must not crash or silently pass.

    ``read_text`` returns "" for an absent file, so the substring test fails
    for every doc -- the loud answer, and the one a repo without a README
    deserves from a gate about README links.
    """
    check_docs = load_tool("check_docs_noreadme", "check_docs.py")
    _docs_fixture(tmp_path)
    (tmp_path / "README.md").unlink()
    problems = check_docs.check(tmp_path)
    assert len(problems) == len(check_docs.REQUIRED_DOCS)
    assert all(p.startswith("UNLINKED:") for p in problems)


# --- check_secrets.py: the gate must be shown to FIRE, not just to pass ------


def _git_repo(root: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
    }
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, env=env, check=True)
    return root


# Split so this file does not itself carry a scannable token: the repo's own
# `make security` gate scans tests/ on purpose (_is_allowlisted skips only
# vendored and generated directories), and a test proving the scanner fires
# must not trip the scanner it is testing.
AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
GH_TOKEN = "ghp_" + "b" * 36
SLACK_TOKEN = "xoxb-" + "1234567890-abcdefghij"


@pytest.mark.parametrize(
    ("label", "secret"),
    [("aws", AWS_KEY), ("github", GH_TOKEN), ("slack", SLACK_TOKEN)],
)
def test_fallback_scan_fires_on_each_token_shape(tmp_path: Path, label: str, secret: str) -> None:
    """One case per pattern family, so a broken regex is attributable.

    A single AWS-key case would leave the other four patterns asserted only by
    the fact that they compile.
    """
    secrets = load_tool(f"check_secrets_{label}", "check_secrets.py")
    repo = _git_repo(tmp_path, {"leaked.py": f'TOKEN = "{secret}"\n'})
    findings = secrets.fallback_scan(repo)
    assert findings, f"{label} token not detected"
    assert "leaked.py" in findings[0]
    # The finding is truncated: a gate that echoes the whole secret into CI
    # logs has published it further than the commit did.
    assert secret not in findings[0]


def test_fallback_scan_is_clean_on_a_repo_without_secrets(tmp_path: Path) -> None:
    secrets = load_tool("check_secrets_clean", "check_secrets.py")
    repo = _git_repo(tmp_path, {"ok.py": "VERSION = '1.2.3'\nSHA = 'a' * 40\n"})
    assert secrets.fallback_scan(repo) == []


def test_fallback_scan_skips_vendored_directories_but_not_tests(tmp_path: Path) -> None:
    """The skip list is vendored/generated only. A secret under ``tests/``
    must still fail the gate -- the comment in ``_is_allowlisted`` says so,
    and nothing asserted it."""
    secrets = load_tool("check_secrets_skip", "check_secrets.py")
    repo = _git_repo(tmp_path, {
        "node_modules/dep.js": f'const k = "{AWS_KEY}";\n',
        "tests/fixture.py": f'KEY = "{AWS_KEY}"\n',
    })
    findings = secrets.fallback_scan(repo)
    assert len(findings) == 1, findings
    assert "tests" in findings[0] and "node_modules" not in findings[0]


def test_fallback_scan_returns_nothing_outside_a_git_repo(tmp_path: Path) -> None:
    """``git ls-files`` fails, ``_tracked_files`` returns [] -- no crash."""
    secrets = load_tool("check_secrets_nogit", "check_secrets.py")
    assert secrets.fallback_scan(tmp_path) == []


def test_secret_gate_main_returns_1_when_the_fallback_finds_a_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """main()'s gitleaks-absent branch: the local safety net must fail non-zero.

    Forced rather than waiting for a machine without gitleaks, so the branch
    is asserted on every host including CI, where the binary IS installed and
    this path would otherwise never run.
    """
    secrets = load_tool("check_secrets_main_fail", "check_secrets.py")
    repo = _git_repo(tmp_path, {"leaked.py": f'TOKEN = "{AWS_KEY}"\n'})
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (-1, "absent"))
    assert secrets.main(["check_secrets.py"], repo) == 1
    assert "FAIL:" in capsys.readouterr().out


def test_secret_gate_main_returns_0_when_the_fallback_is_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    secrets = load_tool("check_secrets_main_pass", "check_secrets.py")
    repo = _git_repo(tmp_path, {"ok.py": "X = 1\n"})
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (-1, "absent"))
    assert secrets.main(["check_secrets.py"], repo) == 0
    assert "fallback scan clean" in capsys.readouterr().out


def test_secret_gate_main_trusts_a_clean_gitleaks_verdict(monkeypatch, capsys) -> None:
    secrets = load_tool("check_secrets_gl_ok", "check_secrets.py")
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (0, ""))
    assert secrets.main(["check_secrets.py"]) == 0
    assert "gitleaks found no secrets" in capsys.readouterr().out


def test_secret_gate_main_fails_when_gitleaks_reports_a_finding(monkeypatch, capsys) -> None:
    """The CI path. Any non-zero, non-(-1) code is a finding, and the gate
    must surface gitleaks' own output rather than swallowing it."""
    secrets = load_tool("check_secrets_gl_fail", "check_secrets.py")
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (1, "leak: api.py:3"))
    assert secrets.main(["check_secrets.py"]) == 1
    out = capsys.readouterr().out
    assert "FAIL: gitleaks detected secrets" in out
    assert "leak: api.py:3" in out


def test_run_gitleaks_reports_minus_one_when_the_binary_is_absent(monkeypatch) -> None:
    secrets = load_tool("check_secrets_which", "check_secrets.py")
    monkeypatch.setattr(secrets.shutil, "which", lambda _name: None)
    code, message = secrets.run_gitleaks()
    assert code == -1
    assert "not installed" in message


# --- render_plugin_manifests.py: --check must detect staleness --------------


def test_plugin_manifests_check_passes_on_the_committed_repo() -> None:
    """``make skill-manifests`` output is committed; --check must agree."""
    # argparse-based: no argv[0]. See run_tool_main's note on the split.
    assert run_tool_main(
        "rpm_check", "render_plugin_manifests.py", "--check", pass_argv0=False
    ) == 0


def test_plugin_manifests_check_fails_on_a_stale_manifest(tmp_path: Path, monkeypatch) -> None:
    rpm = load_tool("rpm_stale", "render_plugin_manifests.py")
    stale = tmp_path / "plugin.json"
    stale.write_text('{"name": "wrong"}\n', encoding="utf-8")
    monkeypatch.setattr(rpm, "PLUGIN_PATH", stale)
    assert rpm.main(["--check"]) == 1


def test_plugin_manifests_write_regenerates_both_files(tmp_path: Path, monkeypatch) -> None:
    rpm = load_tool("rpm_write", "render_plugin_manifests.py")
    plugin, marketplace = tmp_path / "plugin.json", tmp_path / "marketplace.json"
    monkeypatch.setattr(rpm, "PLUGIN_PATH", plugin)
    monkeypatch.setattr(rpm, "MARKETPLACE_PATH", marketplace)
    assert rpm.main(["--write"]) == 0
    # Both, not just the first: --write regenerates unconditionally so it is
    # not order-dependent on which file happened to be stale.
    assert json.loads(plugin.read_text(encoding="utf-8"))["name"] == rpm.SKILL_NAME
    assert json.loads(marketplace.read_text(encoding="utf-8"))["plugins"][0]["version"]


def test_plugin_manifests_require_a_mode(capsys) -> None:
    """--write and --check are mutually exclusive AND required: a bare
    invocation must not silently do nothing."""
    rpm = load_tool("rpm_nomode", "render_plugin_manifests.py")
    with pytest.raises(SystemExit) as excinfo:
        rpm.main([])
    assert excinfo.value.code == 2


def test_plugin_manifests_reject_an_empty_skill_file(tmp_path: Path, monkeypatch, capsys) -> None:
    rpm = load_tool("rpm_empty", "render_plugin_manifests.py")
    empty = tmp_path / "SKILL.md"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(rpm, "SKILL_MD", empty)
    assert rpm.main(["--check"]) == 2
    assert "missing or empty" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("no frontmatter", "# Skill\n\nNo frontmatter here.\n"),
        ("no description", "---\nname: x\n---\n\nbody\n"),
        ("block scalar", "---\nname: x\ndescription: >-\n  wrapped\n---\n\nbody\n"),
        ("empty description", "---\nname: x\ndescription:\n---\n\nbody\n"),
    ],
)
def test_plugin_manifests_reject_an_unusable_description(
    tmp_path: Path, monkeypatch, capsys, label: str, body: str
) -> None:
    """A description that cannot be read as a single-line scalar is exit 2,
    not a manifest carrying ``">-"`` as its published description."""
    rpm = load_tool(f"rpm_desc_{label.replace(' ', '_')}", "render_plugin_manifests.py")
    skill = tmp_path / "SKILL.md"
    skill.write_text(body, encoding="utf-8")
    monkeypatch.setattr(rpm, "SKILL_MD", skill)
    assert rpm.main(["--check"]) == 2, label
    assert "ERROR" in capsys.readouterr().err


def test_plugin_manifests_verbose_logs_without_polluting_stdout(
    tmp_path: Path, monkeypatch, capsys, caplog
) -> None:
    """-v is a debugging affordance, so its output must not land on stdout.

    Asserted through ``caplog`` rather than ``capsys.readouterr().err``:
    pytest's logging plugin installs its own handler and intercepts the
    records before the stderr stream capsys reads, so a stderr assertion here
    fails even when the message does reach stderr in a real run. Verified by
    running it both ways -- the capsys form reported ``err=''`` while
    pytest's own "Captured stderr call" section showed the line present.
    """
    rpm = load_tool("rpm_verbose", "render_plugin_manifests.py")
    monkeypatch.setattr(rpm, "PLUGIN_PATH", tmp_path / "p.json")
    monkeypatch.setattr(rpm, "MARKETPLACE_PATH", tmp_path / "m.json")
    with caplog.at_level("DEBUG", logger="planlint.tools"):
        rpm.main(["--write", "-v"])
    assert any("manifests:" in record.message for record in caplog.records)
    # The real invariant: stdout stays the machine-readable channel.
    assert "manifests:" not in capsys.readouterr().out


# --- check_no_hardcoded_thresholds.py: this project's flagship rule ---------
#
# G003 says a threshold belongs in config, and this guard enforces it on the
# repo's own Makefile and workflows. Its failing path had no test: main() was
# exercised only against the repository itself, which passes, so "the guard
# reports FAIL when a threshold is hard-coded" was assumed rather than shown.


def _guard_tree(root: Path, makefile: str = "", workflow: str | None = None,
                makefile_name: str = "Makefile") -> Path:
    (root / makefile_name).write_text(makefile, encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text(workflow or "name: ci\n", encoding="utf-8")
    return root


def test_threshold_guard_passes_on_a_clean_tree(tmp_path: Path, capsys) -> None:
    guard = load_tool("hct_clean", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, makefile="test:\n\tpytest -q\n")
    assert guard.main(["x"], tree) == 0
    assert "PASS" in capsys.readouterr().out


def test_threshold_guard_fails_on_a_hard_coded_coverage_floor(tmp_path: Path, capsys) -> None:
    guard = load_tool("hct_makefile", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, makefile="test:\n\tpytest --cov-fail-under=90\n")
    assert guard.main(["x"], tree) == 1
    assert "hard-coded numeric literal '90'" in capsys.readouterr().out


def test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow(tmp_path: Path, capsys) -> None:
    guard = load_tool("hct_workflow", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, workflow="jobs:\n  t:\n    run: pytest --cov-fail-under=85\n")
    assert guard.main(["x"], tree) == 1
    assert "pinned in workflow, not pyproject" in capsys.readouterr().out


def test_threshold_guard_fails_on_a_pinned_tool_version(tmp_path: Path, capsys) -> None:
    """A pinned ruff/mypy/pytest is the other half of the rule: dev extras are
    deliberately unpinned so contributors and CI resolve the same versions."""
    guard = load_tool("hct_pin", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, workflow="jobs:\n  t:\n    run: pip install ruff==0.4.2\n")
    assert guard.main(["x"], tree) == 1
    assert "tool version pinned in workflow" in capsys.readouterr().out


def test_threshold_guard_dispatches_a_gnumakefile_to_the_makefile_checker(
    tmp_path: Path, capsys
) -> None:
    """Dispatch is by which list the path came from, never by basename.

    A repo using GNUmakefile would otherwise be handed to the *workflow*
    checker, which scans for entirely different shapes and would report PASS
    on a hard-coded floor. The source says so; nothing asserted it.
    """
    guard = load_tool("hct_gnu", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(
        tmp_path, makefile="test:\n\tpytest --cov-fail-under=90\n", makefile_name="GNUmakefile"
    )
    assert guard.main(["x"], tree) == 1
    assert "hard-coded numeric literal '90'" in capsys.readouterr().out


def test_threshold_guard_scans_both_yaml_spellings(tmp_path: Path) -> None:
    """`.yaml` is as valid to GitHub Actions as `.yml`."""
    guard = load_tool("hct_yaml", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path)
    (tree / ".github" / "workflows" / "extra.yaml").write_text(
        "run: pytest --cov-fail-under=70\n", encoding="utf-8"
    )
    assert {p.name for p in guard.targets(tree)} >= {"ci.yml", "extra.yaml"}
    assert guard.main(["x"], tree) == 1


def test_threshold_guard_ignores_comments_and_make_expansions(tmp_path: Path) -> None:
    """The allowlist works by token, not by vetoing whole lines.

    `$(shell ...)` and a leading `@` are stripped before scanning, so a recipe
    that echoes a number computed elsewhere is fine -- but a literal outside
    an expansion on that same line must still be caught, which a line-level
    veto would have missed.
    """
    guard = load_tool("hct_allow", "check_no_hardcoded_thresholds.py")
    tree = _guard_tree(tmp_path, makefile=(
        "# fail_under = 90 in a comment is documentation, not a pin\n"
        "check:\n"
        "\t@echo $(shell python -c 'print(90)')\n"
    ))
    assert guard.main(["x"], tree) == 0


def test_threshold_guard_survives_a_makefile_that_is_not_a_regular_file(tmp_path: Path) -> None:
    """A directory carrying the name: nothing to scan, and no fall-through to
    a lower-precedence file -- `make` stops there too."""
    guard = load_tool("hct_notfile", "check_no_hardcoded_thresholds.py")
    (tmp_path / "Makefile").mkdir()
    assert guard.check_makefile(tmp_path / "Makefile") == []


def test_threshold_guard_survives_a_missing_workflow(tmp_path: Path) -> None:
    guard = load_tool("hct_nowf", "check_no_hardcoded_thresholds.py")
    assert guard.check_workflow(tmp_path / "nope.yml") == []


# --- scoped coverage floors: the gate that guards the gate scripts ----------
#
# `make coverage-tools` gates tools/ against its own floors using the same two
# checkers under `--scope`. That scoping is now gate-critical logic: get it
# wrong and the gate silently measures the wrong tree, or nothing at all.


def _cov_json(path: Path, files: dict[str, tuple[int, int, int, int]]) -> Path:
    """Write a coverage.json. Values are (statements, covered, branches, covered)."""
    payload = {
        "files": {
            name: {"summary": {
                "num_statements": stm, "covered_lines": cov,
                "num_branches": br, "covered_branches": bcov,
            }}
            for name, (stm, cov, br, bcov) in files.items()
        },
        "totals": {
            "num_statements": sum(v[0] for v in files.values()),
            "covered_lines": sum(v[1] for v in files.values()),
            "num_branches": sum(v[2] for v in files.values()),
            "covered_branches": sum(v[3] for v in files.values()),
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _pyproject(path: Path, **keys: int) -> Path:
    specgraph = "\n".join(f"{k} = {v}" for k, v in keys.items())
    path.write_text(
        f"[tool.coverage.report]\nfail_under = 90\n[tool.specgraph]\n{specgraph}\n",
        encoding="utf-8",
    )
    return path


def test_scoped_totals_sum_only_the_named_subtree(tmp_path: Path) -> None:
    common = load_tool("common_scope", "_common.py")
    cov = _cov_json(tmp_path / "c.json", {
        "openspec_graph/cli.py": (100, 100, 40, 40),   # perfect, and irrelevant
        "tools/a.py": (10, 5, 4, 2),
        "tools/b.py": (10, 5, 4, 2),
    })
    assert common.coverage_totals(cov, "covered_lines", "num_statements", "tools") == (10, 20)
    # Unscoped still reads the report's own totals, unchanged.
    assert common.coverage_totals(cov, "covered_lines", "num_statements") == (110, 120)


def test_scoped_totals_normalize_windows_separators(tmp_path: Path) -> None:
    """coverage.py writes paths as the platform spells them.

    A backslash-separated path would never match a ``tools/`` prefix, and the
    failure mode is not a crash but a scope that matches nothing -- which on a
    green run looks exactly like a passing gate until the next assertion below
    turns it into exit 2.
    """
    common = load_tool("common_win", "_common.py")
    cov = _cov_json(tmp_path / "c.json", {"tools\\check_docs.py": (10, 9, 2, 2)})
    assert common.coverage_totals(cov, "covered_lines", "num_statements", "tools") == (9, 10)


def test_scoped_totals_are_zero_for_a_subtree_nobody_measured(tmp_path: Path) -> None:
    common = load_tool("common_none", "_common.py")
    cov = _cov_json(tmp_path / "c.json", {"openspec_graph/cli.py": (10, 10, 2, 2)})
    assert common.coverage_totals(cov, "covered_lines", "num_statements", "tools") == (0, 0)


def test_a_scope_matching_nothing_fails_the_gate_rather_than_passing(tmp_path: Path) -> None:
    """The load-bearing case. A prefix typo, a renamed directory, or a run
    that forgot `--cov=tools` all produce 0 measured statements, and 0/0 is
    not 100% -- it is a gate pointed at nothing. It must exit 2."""
    _cov_json(tmp_path / "coverage.json", {"openspec_graph/cli.py": (10, 10, 2, 2)})
    _pyproject(tmp_path / "pyproject.toml", tools_line_fail_under=90, tools_branch_fail_under=80)
    assert run_tool_main(
        "cf_empty", "check_coverage_floor.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2
    assert run_tool_main(
        "bc_empty", "check_branch_coverage.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2


def test_scoped_gate_fails_below_its_own_floor_and_passes_at_it(tmp_path: Path) -> None:
    _pyproject(tmp_path / "pyproject.toml", tools_line_fail_under=90, tools_branch_fail_under=80)
    _cov_json(tmp_path / "coverage.json", {
        # The package is perfect; tools/ is not. A combined number would pass.
        "openspec_graph/cli.py": (900, 900, 200, 200),
        "tools/thin.py": (100, 50, 20, 4),
    })
    assert run_tool_main(
        "cf_below", "check_coverage_floor.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 1
    assert run_tool_main(
        "bc_below", "check_branch_coverage.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 1
    # And the unscoped gate on the same file passes, which is exactly the
    # dilution the scoped floors exist to prevent: 95% overall, 50% in tools/.
    assert run_tool_main(
        "cf_whole", "check_coverage_floor.py", "coverage.json", cwd=tmp_path
    ) == 0


def test_scoped_gate_fails_loudly_when_its_floor_is_not_configured(tmp_path: Path) -> None:
    """A missing scoped floor is a misconfiguration, not a skip -- the same
    rule the unscoped floors already follow."""
    _cov_json(tmp_path / "coverage.json", {"tools/a.py": (10, 10, 2, 2)})
    _pyproject(tmp_path / "pyproject.toml", branch_fail_under=80)  # no tools_* keys
    assert run_tool_main(
        "cf_nofloor", "check_coverage_floor.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2
    assert run_tool_main(
        "bc_nofloor", "check_branch_coverage.py", "coverage.json", "--scope", "tools", cwd=tmp_path
    ) == 2


@pytest.mark.parametrize(
    ("argv", "expected_path", "expected_scope"),
    [
        (["prog"], "coverage.json", None),
        (["prog", "c.json"], "c.json", None),
        (["prog", "--scope", "tools"], "coverage.json", "tools"),
        (["prog", "--scope=tools"], "coverage.json", "tools"),
        (["prog", "c.json", "--scope", "tools"], "c.json", "tools"),
        (["prog", "--scope", "tools", "c.json"], "c.json", "tools"),
    ],
)
def test_coverage_argv_parses_every_accepted_shape(
    argv: list[str], expected_path: str, expected_scope: str | None
) -> None:
    common = load_tool("common_argv", "_common.py")
    path, scope = common.parse_coverage_argv(argv)
    assert (path.name, scope) == (expected_path, expected_scope)


@pytest.mark.parametrize("argv", [["prog", "--scope"], ["prog", "--scope="], ["prog", "--scope", ""]])
def test_coverage_argv_rejects_a_scope_without_a_value(argv: list[str]) -> None:
    """`--scope` with nothing after it must not be read as scope="" , which
    would build the prefix "/" and match every file in the report."""
    common = load_tool("common_argv_bad", "_common.py")
    with pytest.raises(ValueError, match="requires a directory name"):
        common.parse_coverage_argv(argv)


def test_scoped_gate_reports_a_usage_error_as_exit_2(tmp_path: Path, capsys) -> None:
    _pyproject(tmp_path / "pyproject.toml", tools_line_fail_under=90)
    assert run_tool_main(
        "cf_usage", "check_coverage_floor.py", "--scope", cwd=tmp_path
    ) == 2
    assert "usage error" in capsys.readouterr().err
