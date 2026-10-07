"""How the Agent Skill is distributed: its generated catalog, its manifests, its shipped CI asset, its packaging.

Moved from ``tests/test_skill_contract.py`` by ``shape-the-test-suite`` (R-TSS-2); the
skill's behavioural contract -- read-only verbs, exit codes, boundaries -- stays there.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from openspec_graph import __version__
from tests.support import load_tool

REPO_ROOT = Path(__file__).resolve().parent.parent

SKILL_DIR = REPO_ROOT / "skills" / "planlint-spec-governance"

PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"

MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"

CATALOG = SKILL_DIR / "references" / "rule-catalog.md"

RENDERER = REPO_ROOT / "tools" / "render_rule_catalog.py"

# --- AC-SD-2 / AC-SD-3: the generated catalog -------------------------------


# _load_tool lives in tests/support.py as load_tool: three verbatim copies
# is the definition of a helper that belongs there.
_load_tool = load_tool

def _run_renderer(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RENDERER), *args],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )

@pytest.mark.e2e
def test_rule_catalog_is_fresh() -> None:
    """AC-SD-2: the committed catalog matches the live rule registry."""
    result = _run_renderer("--check")
    assert result.returncode == 0, (
        f"{result.stdout}{result.stderr}\nrun `make skill-catalog` to regenerate"
    )

@pytest.mark.integration
def test_rule_catalog_check_fails_when_stale(tmp_path: Path, monkeypatch) -> None:
    """AC-SD-3 (non-success): --check reports staleness rather than hiding it.

    Runs against a redirected copy under tmp_path, never the tracked file. An
    earlier version mutated the real catalog and restored it in a ``finally``:
    a hard interrupt then left an invented rule row in the contributor's tree,
    it raced the two sibling tests that read the same file under xdist, and it
    failed outright on a read-only checkout.
    """
    module = _load_tool("rrc", "render_rule_catalog.py")
    staged = tmp_path / "rule-catalog.md"
    monkeypatch.setattr(module, "CATALOG_PATH", staged)

    # Missing entirely.
    assert module.main(["--check"]) == 1

    # Present but stale.
    staged.write_text(module.render() + "| Z999 | ERROR | any | invented |\n", encoding="utf-8")
    assert module.main(["--check"]) == 1

    # Written by the generator, then fresh -- proves --write and --check agree.
    assert module.main(["--write"]) == 0
    assert module.main(["--check"]) == 0
    assert CATALOG.read_text(encoding="utf-8"), "the tracked catalog must be untouched"

@pytest.mark.integration
def test_rule_catalog_render_is_deterministic() -> None:
    """The pure function's own contract, exercised in-process.

    Every other check here runs the tool as a subprocess, which measures no
    coverage of the module and cannot see this property at all.
    """
    module = _load_tool("rrc", "render_rule_catalog.py")
    assert module.render() == module.render()
    assert module.render().endswith("\n")

@pytest.mark.integration
def test_rule_catalog_lists_every_registered_rule() -> None:
    """The catalog is generated, so this asserts the generator's coverage."""
    from openspec_graph.rules import RULES

    text = CATALOG.read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| ([A-Z]\d{3}) \|", text, re.MULTILINE))
    assert listed == {rule.ident for rule in RULES}

@pytest.mark.integration
def test_rule_catalog_states_no_total_count() -> None:
    """DEC-SD-003: a count here would be the one number nothing guards."""
    text = CATALOG.read_text(encoding="utf-8")
    assert not re.search(r"\b\d+\s+(?:deterministic\s+)?rules\b", text), (
        "the generated catalog must not state a rule total -- "
        "tests/test_rule_registry_docs.py cannot see this file"
    )

# --- AC-SD-7: manifest agreement --------------------------------------------


@pytest.mark.integration
def test_plugin_manifests_agree() -> None:
    """AC-SD-7: manifests, skill directory, and package version are one story."""
    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))

    assert plugin["name"] == SKILL_DIR.name
    assert plugin["version"] == __version__, (
        f"plugin.json version {plugin['version']!r} != package {__version__!r}"
    )

    entries = [p for p in marketplace["plugins"] if p["name"] == plugin["name"]]
    assert len(entries) == 1, (
        f"marketplace.json must list {plugin['name']!r} exactly once"
    )
    assert entries[0]["source"] == "./", (
        "the plugin's source is the repo root, so skills/ ships with it"
    )
    assert entries[0]["version"] == __version__

# --- AC-SD-10 / AC-SD-11: the shipped CI asset ------------------------------


@pytest.mark.integration
def test_skill_asset_matches_template() -> None:
    """AC-SD-10: the bundled workflow is a byte-identical copy (DEC-SD-004)."""
    template = (REPO_ROOT / "templates" / "spec-gate.yml").read_bytes()
    asset = (SKILL_DIR / "assets" / "spec-gate.yml").read_bytes()
    assert asset == template, (
        "skills/planlint-spec-governance/assets/spec-gate.yml has drifted from "
        "templates/spec-gate.yml; copy the template over it"
    )

@pytest.mark.integration
def test_spec_gate_template_triggers_on_speckit_trees() -> None:
    """AC-SD-11: a SpecKit repo must trigger the gate it just installed."""
    text = (REPO_ROOT / "templates" / "spec-gate.yml").read_text(encoding="utf-8")
    paths_block = text.split("paths:", 1)[1].split("workflow_dispatch", 1)[0]
    assert '"specs/**"' in paths_block, (
        "the template triggers only on openspec/**, so a SpecKit repo would "
        "never run the gate"
    )
    assert '"openspec/**"' in paths_block

# --- AC-SD-12 / AC-SD-13 / AC-SD-14: packaging and gate coverage ------------


@pytest.mark.integration
def test_version_has_a_single_source() -> None:
    """AC-SD-12: pyproject reads the package attribute, never a second literal.

    Two literals with nothing binding them is the drift class
    tests/test_rule_registry_docs.py exists for, and a release is the worst
    place to find it (DEC-SD-009).
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in text
    assert 'version = { attr = "openspec_graph.__version__" }' in text
    assert not re.search(r'^version = "\d', text, re.MULTILINE), (
        "pyproject.toml carries its own version literal again"
    )

@pytest.mark.unit
def test_installed_distribution_version_matches_the_package_attribute() -> None:
    """The single source, proven end to end through the installed metadata."""
    import importlib.metadata

    try:
        installed = importlib.metadata.version("planlint")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        pytest.skip("planlint is not installed in this environment")
    assert installed == __version__

@pytest.mark.e2e
def test_cli_version_flag_reports_the_package_version() -> None:
    """`planlint --version` is the preflight step SKILL.md tells agents to run."""
    result = subprocess.run(
        [sys.executable, "-m", "openspec_graph.cli", "--version"],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    assert result.returncode == 0
    assert __version__ in result.stdout

@pytest.mark.integration
def test_threshold_guard_scans_every_workflow() -> None:
    """AC-SD-13 (non-success): a workflow other than ci.yml cannot escape it.

    The guard named ci.yml alone, so any workflow added later -- a release
    job, a scheduled scan -- went unscanned while the guard still printed
    PASS. Asserting on the resolved target list rather than on a temp file
    keeps this honest: the bug was in target selection, not in matching.
    """
    mod = _load_tool("nht", "check_no_hardcoded_thresholds.py")

    # Assert on the guard's OWN target selection. Re-globbing the directory
    # here instead would pass against the broken version too: the bug was
    # never in matching, it was in which files were handed to the matcher.
    selected = {p.name for p in mod.targets()}
    assert {"Makefile", "ci.yml", "release.yml"} <= selected, (
        f"the guard scans {sorted(selected)}; it must cover every workflow, "
        "not a named subset"
    )
    on_disk = {p.name for p in (REPO_ROOT / ".github" / "workflows").glob("*.y*ml")}
    assert on_disk <= selected, (
        f"workflow(s) {sorted(on_disk - selected)} exist but are not scanned"
    )
    for target in mod.targets():
        checker = mod.check_makefile if target.name == "Makefile" else mod.check_workflow
        assert checker(target) == [], f"{target.name} already trips the guard"

@pytest.mark.integration
def test_threshold_guard_flags_a_pinned_floor_in_a_non_ci_workflow(tmp_path: Path) -> None:
    """The matching half of AC-SD-13, on a file that is not ci.yml."""
    mod = _load_tool("nht", "check_no_hardcoded_thresholds.py")

    body = "jobs:\n  x:\n    steps:\n      - run: pytest --cov-fail-under=90\n"
    # Both spellings GitHub Actions accepts. A guard covering only one is the
    # same bug one rename away.
    for name in ("release.yml", "scheduled.yaml"):
        fake = tmp_path / name
        fake.write_text(body, encoding="utf-8")
        assert mod.check_workflow(fake), (
            f"a pinned coverage floor in {name} must be flagged"
        )

@pytest.mark.e2e
def test_required_docs_are_linked() -> None:
    """AC-SD-14: the skill is a required doc and the README links it."""
    check_docs = REPO_ROOT / "tools" / "check_docs.py"
    text = check_docs.read_text(encoding="utf-8")
    assert "skills/planlint-spec-governance/SKILL.md" in text, (
        "the skill must be listed in REQUIRED_DOCS"
    )
    result = subprocess.run(
        [sys.executable, str(check_docs)],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr

@pytest.mark.integration
def test_skill_quotes_no_credential_shaped_literals() -> None:
    """`make security` scans every tracked file; an example token would fail it.

    Cheaper to catch here, where the message says why, than in a gitleaks run
    whose output points at a documentation file with no explanation.
    """
    patterns = (r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{20,}",
                r"github_pat_[A-Za-z0-9_]{20,}", r"sk-[A-Za-z0-9]{20,}",
                r"xox[bpras]-[A-Za-z0-9-]{10,}")
    for path in sorted(SKILL_DIR.glob("**/*")):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            assert not re.search(pattern, body), (
                f"{path.relative_to(REPO_ROOT)} contains a credential-shaped "
                f"literal matching {pattern!r}; make security scans this file"
            )

# --- backwards compatibility: the distribution rename ------------------------


@pytest.mark.unit
def test_version_lookup_prefers_the_named_distribution_over_list_order(monkeypatch) -> None:
    """A stale `openspec-graph` install must not be able to report its version.

    Two distributions can provide the import name `openspec_graph` at once --
    exactly what an upgrade from before the rename leaves behind if the old
    editable install is not removed. `packages_distributions()` returns them in
    no defined order, so selecting by index could report the old code's version
    indefinitely. `--version` is the preflight step the Agent Skill tells every
    agent to run first, which makes a wrong answer here the worst one
    available.
    """
    import importlib.metadata as md

    from openspec_graph import cli

    monkeypatch.setattr(
        md, "packages_distributions",
        lambda: {"openspec_graph": ["openspec-graph", "planlint"]},
    )
    monkeypatch.setattr(
        md, "version",
        lambda dist: "0.0.1-stale" if dist == "openspec-graph" else __version__,
    )
    captured: list[str] = []
    monkeypatch.setattr(
        cli, "print",
        lambda *a, **k: captured.append(" ".join(str(x) for x in a)),
        raising=False,
    )

    result = cli._version_string()
    assert __version__ in result, f"reported {result!r} instead of the live version"
    assert "0.0.1-stale" not in result
    assert any("WARNING" in line for line in captured), (
        "an ambiguous environment must say so; silence hides a stale install"
    )

@pytest.mark.unit
def test_version_lookup_is_silent_when_one_distribution_is_listed_twice(monkeypatch) -> None:
    """Duplicate entries for one name are not ambiguity, and must not warn.

    A repeated editable install can leave several metadata directories for the
    same distribution. Warning there would fire on every invocation of every
    verb for an environment that is in fact fine -- noise that trains a reader
    to ignore the warning that matters.
    """
    import importlib.metadata as md

    from openspec_graph import cli

    monkeypatch.setattr(
        md, "packages_distributions",
        lambda: {"openspec_graph": ["planlint", "planlint"]},
    )
    monkeypatch.setattr(md, "version", lambda dist: __version__)
    captured: list[str] = []
    monkeypatch.setattr(
        cli, "print",
        lambda *a, **k: captured.append(" ".join(str(x) for x in a)),
        raising=False,
    )

    assert __version__ in cli._version_string()
    assert not captured, f"warned about a non-ambiguous environment: {captured}"

@pytest.mark.integration
def test_scaffolded_project_doc_names_the_current_distribution() -> None:
    """`planlint init` must not write a package name that no longer exists.

    The scaffold template named `openspec-graph` -- the distribution the 0.2.0
    notes tell users to uninstall -- so every repository scaffolded by this
    release would have carried a reference to a package that is gone, and
    contradicted itself two lines later where it says `planlint`.
    """
    source = (REPO_ROOT / "openspec_graph" / "scaffold.py").read_text(encoding="utf-8")
    assert "openspec-graph" not in source, (
        "scaffold.py still writes the pre-rename distribution name into "
        "scaffolded repositories"
    )
