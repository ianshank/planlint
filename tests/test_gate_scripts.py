"""Behavioural tests for the ``tools/`` gate scripts' own decision logic.

These scripts are what ``make pre-pr`` and the workflows run, so a gate that
cannot fail is worse than no gate: it reports PASS on the thing it was added
to catch. Three of them had never been shown to fire.

Each script's ``main()`` is called in-process (see ``run_tool_main``), because
a subprocess's execution is invisible to coverage and these had therefore all
read 0% while looking tested. The ``python tools/<script>.py`` invocation path
is covered once for the whole directory by
``test_gate_script_is_runnable_as_a_script`` at the end of this module.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support import captured_logger, env_without_coverage, load_tool, run_tool_main

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

@pytest.mark.integration
def test_docs_check_passes_when_every_doc_is_present_and_linked(tmp_path: Path) -> None:
    check_docs = load_tool("check_docs_pass", "check_docs.py")
    assert check_docs.check(_docs_fixture(tmp_path)) == []

@pytest.mark.integration
def test_docs_check_reports_a_missing_doc(tmp_path: Path) -> None:
    check_docs = load_tool("check_docs_missing", "check_docs.py")
    problems = check_docs.check(_docs_fixture(tmp_path, omit="SECURITY.md"))
    assert problems == ["MISSING: SECURITY.md"]

@pytest.mark.integration
def test_docs_check_reports_a_present_but_unlinked_doc(tmp_path: Path) -> None:
    """Present-but-unlinked is the whole point of the gate: a doc a new
    contributor cannot reach from the front page is effectively absent, and
    an existence-only check would report PASS on it."""
    check_docs = load_tool("check_docs_unlinked", "check_docs.py")
    problems = check_docs.check(_docs_fixture(tmp_path, unlinked="docs/aqa.md"))
    assert problems == ["UNLINKED: docs/aqa.md not referenced in README.md"]

@pytest.mark.integration
def test_docs_check_main_exits_1_on_a_defect_and_0_when_clean(tmp_path: Path, capsys) -> None:
    check_docs = load_tool("check_docs_main", "check_docs.py")
    assert check_docs.main(["check_docs.py"], _docs_fixture(tmp_path, omit="AGENTS.md")) == 1
    assert "FAIL: MISSING: AGENTS.md" in capsys.readouterr().out

    clean = tmp_path / "clean"
    clean.mkdir()
    assert check_docs.main(["check_docs.py"], _docs_fixture(clean)) == 0
    assert "all required docs present and linked" in capsys.readouterr().out

@pytest.mark.integration
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

@pytest.mark.e2e
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

@pytest.mark.e2e
def test_fallback_scan_is_clean_on_a_repo_without_secrets(tmp_path: Path) -> None:
    secrets = load_tool("check_secrets_clean", "check_secrets.py")
    repo = _git_repo(tmp_path, {"ok.py": "VERSION = '1.2.3'\nSHA = 'a' * 40\n"})
    assert secrets.fallback_scan(repo) == []

@pytest.mark.e2e
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

@pytest.mark.integration
def test_fallback_scan_returns_nothing_outside_a_git_repo(tmp_path: Path) -> None:
    """``git ls-files`` fails, ``_tracked_files`` returns [] -- no crash."""
    secrets = load_tool("check_secrets_nogit", "check_secrets.py")
    assert secrets.fallback_scan(tmp_path) == []

@pytest.mark.e2e
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

@pytest.mark.e2e
def test_secret_gate_main_returns_0_when_the_fallback_is_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    secrets = load_tool("check_secrets_main_pass", "check_secrets.py")
    repo = _git_repo(tmp_path, {"ok.py": "X = 1\n"})
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (-1, "absent"))
    assert secrets.main(["check_secrets.py"], repo) == 0
    assert "fallback scan clean" in capsys.readouterr().out

@pytest.mark.integration
def test_secret_gate_main_trusts_a_clean_gitleaks_verdict(monkeypatch, capsys) -> None:
    secrets = load_tool("check_secrets_gl_ok", "check_secrets.py")
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (0, ""))
    assert secrets.main(["check_secrets.py"]) == 0
    assert "gitleaks found no secrets" in capsys.readouterr().out

@pytest.mark.integration
def test_secret_gate_main_fails_when_gitleaks_reports_a_finding(monkeypatch, capsys) -> None:
    """The CI path. Any non-zero, non-(-1) code is a finding, and the gate
    must surface gitleaks' own output rather than swallowing it."""
    secrets = load_tool("check_secrets_gl_fail", "check_secrets.py")
    monkeypatch.setattr(secrets, "run_gitleaks", lambda root=None: (1, "leak: api.py:3"))
    assert secrets.main(["check_secrets.py"]) == 1
    out = capsys.readouterr().out
    assert "FAIL: gitleaks detected secrets" in out
    assert "leak: api.py:3" in out

@pytest.mark.integration
def test_run_gitleaks_reports_minus_one_when_the_binary_is_absent(monkeypatch) -> None:
    secrets = load_tool("check_secrets_which", "check_secrets.py")
    monkeypatch.setattr(secrets.shutil, "which", lambda _name: None)
    code, message = secrets.run_gitleaks()
    assert code == -1
    assert "not installed" in message

# --- render_plugin_manifests.py: --check must detect staleness --------------


@pytest.mark.integration
def test_plugin_manifests_check_passes_on_the_committed_repo() -> None:
    """``make skill-manifests`` output is committed; --check must agree."""
    # argparse-based: no argv[0]. See run_tool_main's note on the split.
    assert run_tool_main(
        "rpm_check", "render_plugin_manifests.py", "--check", pass_argv0=False
    ) == 0

@pytest.mark.integration
def test_plugin_manifests_check_fails_on_a_stale_manifest(tmp_path: Path, monkeypatch) -> None:
    rpm = load_tool("rpm_stale", "render_plugin_manifests.py")
    stale = tmp_path / "plugin.json"
    stale.write_text('{"name": "wrong"}\n', encoding="utf-8")
    monkeypatch.setattr(rpm, "PLUGIN_PATH", stale)
    assert rpm.main(["--check"]) == 1

@pytest.mark.integration
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

@pytest.mark.integration
def test_plugin_manifests_require_a_mode(capsys) -> None:
    """--write and --check are mutually exclusive AND required: a bare
    invocation must not silently do nothing."""
    rpm = load_tool("rpm_nomode", "render_plugin_manifests.py")
    with pytest.raises(SystemExit) as excinfo:
        rpm.main([])
    assert excinfo.value.code == 2

@pytest.mark.integration
def test_plugin_manifests_reject_an_empty_skill_file(tmp_path: Path, monkeypatch, capsys) -> None:
    rpm = load_tool("rpm_empty", "render_plugin_manifests.py")
    empty = tmp_path / "SKILL.md"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(rpm, "SKILL_MD", empty)
    assert rpm.main(["--check"]) == 2
    assert "missing or empty" in capsys.readouterr().err

@pytest.mark.integration
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

@pytest.mark.integration
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

    And captured through ``captured_logger`` rather than a bare
    ``caplog.at_level``: ``_common`` sets ``propagate = False`` on
    ``planlint.tools`` at import, and pytest attaches its handler only to
    loggers that are already non-propagating when the test starts. With
    ``_common`` first loaded *inside* this test, the records never reached
    ``caplog`` -- red under ``-k``, green in the full run, where an earlier
    test had done the import. Order dependence hiding behind a green suite.
    """
    rpm = load_tool("rpm_verbose", "render_plugin_manifests.py")
    monkeypatch.setattr(rpm, "PLUGIN_PATH", tmp_path / "p.json")
    monkeypatch.setattr(rpm, "MARKETPLACE_PATH", tmp_path / "m.json")
    with captured_logger(caplog, "planlint.tools"):
        rpm.main(["--write", "-v"])
    assert any("manifests:" in record.message for record in caplog.records)
    # The real invariant: stdout stays the machine-readable channel.
    assert "manifests:" not in capsys.readouterr().out

# --- _common.read_json: the typed reader the artifact consumers share --------


@pytest.mark.integration
def test_read_json_rejects_a_non_mapping_document(tmp_path: Path) -> None:
    """A top-level list is refused here, naming the file, rather than
    surfacing later as a ``TypeError`` from the first ``graph["nodes"]``."""
    common = load_tool("common_read_json_list", "_common.py")
    doc = tmp_path / "graph.json"
    doc.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match=re.escape(str(doc))):
        common.read_json(doc)

@pytest.mark.integration
def test_read_json_reports_a_missing_file_by_name(tmp_path: Path) -> None:
    """Read directly, not through ``read_text``: its missing-file ``""`` would
    turn an absent artifact into a ``JSONDecodeError`` with no path in it."""
    common = load_tool("common_read_json_missing", "_common.py")
    missing = tmp_path / "absent.json"
    with pytest.raises(FileNotFoundError) as excinfo:
        common.read_json(missing)
    assert missing.name in str(excinfo.value)

@pytest.mark.integration
@pytest.mark.parametrize(
    "line,expected",
    [
        ('key = "dev"', "dev"),
        ('key="hotfix/"   # trailing comment', "hotfix/"),
        ('key = ""', None),
        ("key = 'single'", None),
        ('key = "esc\\aped"', None),
        ("key = 7", None),
        ('keyed = "other"', None),
    ],
)
def test_read_pyproject_str_reads_exactly_the_shape_this_repo_writes(
    tmp_path: Path, line: str, expected: str | None
) -> None:
    """adopt-branch-promotion-model: the string reader behind the promotion table.

    Section-aware like ``read_pyproject_int``: the same key under another table
    is not read, and a value outside the one supported shape is ``None`` -- the
    caller's misconfiguration path -- never a mangled string.
    """
    common = load_tool("common_read_pyproject_str", "_common.py")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'[tool.a]\nkey = "decoy"\n\n[tool.b]\n{line}\n', encoding="utf-8")
    assert common.read_pyproject_str(pyproject, "[tool.b]", "key") == expected
    assert common.read_pyproject_str(pyproject, "[tool.a]", "key") == "decoy"
    assert common.read_pyproject_str(pyproject, "[tool.c]", "key") is None
    assert common.read_pyproject_str(tmp_path / "absent.toml", "[tool.b]", "key") is None

@pytest.mark.integration
def test_pyproject_readers_stop_at_a_commented_table_header(tmp_path: Path) -> None:
    """adopt-branch-promotion-model review LOW-2: ``[tool.x]  # why`` still ends the table.

    Judged by its last character, that header read as a key line, the scan
    stayed in the previous table, and the next table's keys leaked into it --
    for both readers, since they share the loop.
    """
    common = load_tool("common_commented_header", "_common.py")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.a]\nkept = 1\n\n[tool.b]  # a comment\nleak = 2\nname = "leak"\n', encoding="utf-8"
    )
    assert common.table_header("[tool.b]  # a comment") == "[tool.b]"
    assert common.table_header('name = "[not a header]"') is None
    assert common.read_pyproject_int(pyproject, "[tool.a]", "leak") is None
    assert common.read_pyproject_str(pyproject, "[tool.a]", "name") is None
    assert common.read_pyproject_int(pyproject, "[tool.b]", "leak") == 2
    assert common.has_pyproject_key(pyproject, "[tool.b]", "name")
    assert not common.has_pyproject_key(pyproject, "[tool.a]", "name")
    assert common.table_lines(tmp_path / "absent.toml", "[tool.a]") == []

# --- the executable contract, once rather than per script --------------------


@pytest.mark.e2e
@pytest.mark.parametrize(
    "script",
    [
        "check_branch_coverage.py",
        "check_coverage_floor.py",
        "diff_spec_graph.py",
        "render_mermaid.py",
        "check_docs.py",
        "check_no_hardcoded_thresholds.py",
        "check_promotion.py",
        "check_secrets.py",
        "check_wheel_metadata.py",
        "matcher_accuracy.py",
        "render_plugin_manifests.py",
        "render_rule_catalog.py",
        "smoke_wheel.py",
        "stage_citations.py",
    ],
)
def test_gate_script_is_runnable_as_a_script(script: str, tmp_path: Path) -> None:
    """``python tools/<script>.py`` starts and returns an exit code.

    Every behaviour of these scripts is asserted in-process, against
    ``main(argv)``, because a subprocess's execution is invisible to coverage
    (see ``run_tool_main``). That leaves exactly one thing in-process testing
    cannot see: whether the file still *runs* as a script -- an import that
    only resolves because pytest put the repo root on ``sys.path``, a
    ``sys.path`` bootstrap line deleted as dead code, a syntax error under the
    ``if __name__ == "__main__"`` guard. The Makefile and the workflows invoke
    every one of these this way, so that path is a real contract.

    Asserted here once for the whole directory rather than once per script, so
    a new gate script is covered by adding one line. Run from a throwaway cwd
    with no arguments: what matters is that the interpreter got far enough to
    reach the script's own argument handling, not which verdict it reached.
    """
    result = subprocess.run(
        [sys.executable, str(TOOLS / script)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
        env=env_without_coverage(),
    )
    # Checked by marker rather than by exit code alone, because the two ways a
    # script fails to load do not agree on either signal. A failed import
    # raises and prints "Traceback (most recent call last)"; a SyntaxError is
    # reported by the compiler in a different format with no such line -- and
    # both exit 1, which is a documented code here (a gate that found a
    # violation). Exit code alone therefore cannot tell "the gate ran and
    # failed the repo" from "the file is not loadable at all".
    for marker in ("Traceback (most recent call last)", "SyntaxError",
                   "ModuleNotFoundError", "ImportError", "IndentationError"):
        assert marker not in result.stderr, f"{script}: {marker}\n{result.stderr}"
    # 0/1/2 are the documented codes. Anything else (a negative code for a
    # fatal signal, or an unhandled SystemExit payload) says the script did
    # not reach its own exit path.
    assert result.returncode in (0, 1, 2), (
        f"{script} exited {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
