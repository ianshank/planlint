"""The release surface: the publish workflow, the generated artifacts, the packaging surface.

Moved from ``tests/test_agent_artifacts.py`` by ``shape-the-test-suite`` (R-TSS-2): the
release workflow's per-job safety properties, the freshness of every generated
agent-facing artifact, and what the wheel and sdist carry.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support import load_tool

REPO_ROOT = Path(__file__).resolve().parent.parent

WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# See tests/support.py::load_tool -- the one shared copy.
_load_tool = load_tool

# --- release workflow -------------------------------------------------------


def _workflow_jobs(text: str) -> dict[str, str]:
    """Split a workflow's ``jobs:`` mapping into one text block per job.

    A crude split, but scoped: a top-level ``jobs:`` key, then each two-space
    indented ``<name>:`` starts a block that runs to the next one. That is
    enough to ask "does *this* job declare that dependency" instead of "does
    this string appear anywhere in the file", which a comment or an unrelated
    job would satisfy just as well.

    No YAML parser is used because this project declares no runtime
    dependencies and none is available to the test suite either.
    """
    body = text.split("\njobs:\n", 1)[1] if "\njobs:\n" in text else ""
    assert body, "release.yml has no top-level jobs: mapping"
    jobs: dict[str, str] = {}
    current: str | None = None
    for line in body.splitlines():
        header = re.match(r"^  ([A-Za-z_][\w-]*):\s*$", line)
        if header:
            current = header.group(1)
            jobs[current] = ""
            continue
        if line and not line.startswith("  ") and not line.startswith("\t"):
            break  # dedented out of jobs: entirely
        if current:
            jobs[current] += line + "\n"
    return jobs

def _uncommented(block: str) -> str:
    """Strip comment-only lines and trailing comments before matching.

    Without this, every assertion below is satisfiable by a comment that
    merely mentions the token it is looking for.
    """
    kept = []
    for line in block.splitlines():
        stripped = line.split("#", 1)[0]
        if stripped.strip():
            kept.append(stripped)
    return "\n".join(kept)

def test_release_workflow_is_gated_and_uses_trusted_publishing() -> None:
    """The publish path's own safety properties, pinned per job.

    Scoped to the job blocks rather than the whole file: asserting that
    ``needs: gate`` appears *somewhere* does not pin the wiring at all, since
    a comment or an unrelated job satisfies it identically. The question worth
    asking is whether the publish job depends on the build job, and this asks
    exactly that.
    """
    text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
    jobs = _workflow_jobs(text)
    assert {"gate", "build", "publish"} <= set(jobs), (
        f"release.yml defines jobs {sorted(jobs)}; the gate/build/publish chain is "
        "what makes publishing safe"
    )

    gate, build, publish = (_uncommented(jobs[n]) for n in ("gate", "build", "publish"))

    assert "make pre-pr" in gate, "the gate job must run the full ladder"
    assert re.search(r"^\s*needs:\s*gate\s*$", build, re.MULTILINE), (
        "the build job must depend on the gate job, not run beside it"
    )
    assert "python -m venv" in build, (
        "the clean-environment console-script smoke test is the wheel's only check"
    )
    assert re.search(r"^\s*needs:\s*build\s*$", publish, re.MULTILINE), (
        "the publish job must depend on the build job"
    )
    assert re.search(r"^\s*id-token:\s*write\s*$", publish, re.MULTILINE), (
        "trusted publishing needs an OIDC token, declared on the publish job"
    )
    assert "pypa/gh-action-pypi-publish" in publish

    # No stored secret anywhere: trusted publishing exists so none is needed.
    assert "secrets.PYPI" not in text, "a stored token defeats trusted publishing"
    # Least privilege at the top level.
    assert re.search(r"^permissions:\n\s+contents:\s*read\s*$", text, re.MULTILINE), (
        "the workflow's default permissions must be read-only"
    )

def test_every_workflow_is_scanned_by_the_threshold_guard() -> None:
    """Wiring check: the guard's target list must cover what actually exists."""
    mod = _load_tool("nht", "check_no_hardcoded_thresholds.py")
    # Both spellings GitHub Actions accepts. Globbing only *.yml here would let
    # a workflow added as .yaml escape this wiring check entirely -- the same
    # single-spelling assumption the guard itself was just fixed for.
    on_disk = {p.name for p in WORKFLOWS.glob("*.yml")} | {
        p.name for p in WORKFLOWS.glob("*.yaml")
    }
    scanned = {p.name for p in mod.targets()}
    assert on_disk <= scanned, (
        f"workflow(s) {sorted(on_disk - scanned)} exist but the guard does not "
        "scan them"
    )
    assert on_disk == {"ci.yml", "release.yml"}, (
        f"a workflow was added or renamed ({sorted(on_disk)}); confirm the guard "
        "still globs the directory rather than naming files"
    )
    for name in on_disk:
        assert mod.check_workflow(WORKFLOWS / name) == []

# --- generated artifacts ----------------------------------------------------


@pytest.mark.parametrize(
    "script,target",
    [("render_plugin_manifests.py", "make skill-manifests")],
)
def test_generated_artifacts_are_fresh(script: str, target: str) -> None:
    """Every generated artifact matches its generator on the committed tree.

    The rule catalog is deliberately absent from this list: it has its own
    AC-pinned check (``test_skill_distribution.py::test_rule_catalog_is_fresh``,
    verifying AC-SD-2) and running it twice would be duplication, not defence.
    This is parametrized so a future generator is added by one list entry.
    """
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / script), "--check"],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"{result.stdout}{result.stderr}\nrun `{target}` to regenerate"
    )

def test_manifest_generator_rejects_a_folded_description(tmp_path: Path) -> None:
    """A folded scalar must stop the generator, not become the description.

    Written as `description: >-`, a naive parser yields the fold marker itself.
    A published manifest whose description reads ">-" is worse than a build
    failure, so the generator raises instead of defaulting.
    """
    mod = _load_tool("rpm", "render_plugin_manifests.py")

    with pytest.raises(ValueError):
        mod.skill_description("---\nname: x\ndescription: >-\n  folded text\n---\n\nbody\n")
    with pytest.raises(ValueError):
        mod.skill_description("---\nname: x\n---\n\nbody\n")
    with pytest.raises(ValueError):
        mod.skill_description("no frontmatter at all\n")

def test_manifest_version_tracks_the_package_not_a_literal() -> None:
    """The generator must read the version, never restate it."""
    source = (REPO_ROOT / "tools" / "render_plugin_manifests.py").read_text(encoding="utf-8")
    assert "from openspec_graph import __version__" in source
    assert not re.search(r'"version":\s*"\d+\.\d+', source), (
        "the manifest generator hard-codes a version literal"
    )

# --- packaging surface ------------------------------------------------------


def test_docker_build_context_is_sufficient_for_the_dynamic_version() -> None:
    """The Dockerfile copies a subset; `attr:` needs the package in it.

    `pyproject.toml` reads the version from `openspec_graph.__version__`, so a
    build context missing the package (or the README that `readme =` names)
    fails at install time rather than at review time.
    """
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    copied = re.findall(r"^COPY\s+(.+?)\s+\S+$", dockerfile, re.MULTILINE)
    copied_tokens = {tok for line in copied for tok in line.split()}
    for required in ("pyproject.toml", "openspec_graph"):
        assert required in copied_tokens, (
            f"Dockerfile does not COPY {required!r}, which the build needs"
        )
    readme_declared = 'readme = "README.md"' in (
        REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if readme_declared:
        assert "README.md" in copied_tokens, (
            "pyproject declares readme = README.md but the Dockerfile never copies it"
        )

def test_agent_artifacts_are_excluded_from_the_docker_context() -> None:
    """Prose for external agents has no place in a runtime image."""
    ignored = {
        line.strip()
        for line in (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    for entry in ("skills", "evals", ".claude", ".claude-plugin", "context7.json", "llms.txt"):
        assert entry in ignored, f".dockerignore does not exclude {entry!r}"

    # Root-level markdown is excluded by pattern rather than by name, so a
    # name-by-name check above can never see it. The realistic mistake is a
    # helpful re-inclusion: `!AGENTS.md` alongside `!README.md` is a one-line
    # diff that silently ships agent prose into the runtime image.
    assert "*.md" in ignored, ".dockerignore no longer excludes markdown by pattern"
    negations = {entry for entry in ignored if entry.startswith("!")}
    assert negations == {"!README.md"}, (
        f".dockerignore re-includes {sorted(negations)}; only README.md belongs in "
        "the build context, and every other root markdown file is agent-facing prose"
    )

def test_every_root_markdown_file_is_wired_into_the_docs_gate() -> None:
    """The check that would have caught AGENTS.md landing as an orphan.

    A markdown file at the repository root is, by position, something a reader
    or an agent finds without being told. Adding one is therefore a promise to
    keep it current, and the mechanism for that here is
    ``tools/check_docs.py``: required to exist, and required to be linked from
    the README. `AGENTS.md` shipped wired into neither, and every gate stayed
    green, because nothing enumerated this directory.

    README.md is the target of the linking rather than a subject of it.

    **Root-scoped on purpose.** ``glob`` here is deliberate, not an oversight
    that ``rglob`` would fix: a markdown file is a front-page promise *because
    of its position*, and `docs/`, `skills/` and `evals/` hold plenty of
    markdown that is reached by a link rather than by being at the top. Nested
    ``AGENTS.md`` files are the one nested kind an agent opens on its own
    initiative, and they are held by the contract tests below instead --
    stated here so neither gate can be read as covering the other's ground.
    """
    module = _load_tool("check_docs", "check_docs.py")
    required = set(module.REQUIRED_DOCS)
    on_disk = {p.name for p in REPO_ROOT.glob("*.md")}
    unwired = sorted(on_disk - required - {"README.md"})
    assert not unwired, (
        f"root markdown file(s) {unwired} are in no gate: add them to "
        "tools/check_docs.py REQUIRED_DOCS (and link them from README.md), or "
        "move them under docs/ where they are not a front-page promise"
    )
