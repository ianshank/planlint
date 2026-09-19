"""Deterministic validation of the agent-facing artifacts this repo publishes.

`skills/`, `.claude-plugin/`, `evals/`, `context7.json` and `llms.txt` are
consumed by machines outside this repository: a plugin installer, a retrieval
index, an evaluation runner. None of them is exercised by the CLI, so nothing
else here would notice a malformed manifest, an eval case with no grader, or a
retrieval config scoping a folder that was renamed away.

That is the same argument `tests/test_agent_skill_docs.py` and
`tests/test_rule_registry_docs.py` already make for prose: an artifact only an
external consumer reads needs an internal check, or its first failure happens
in someone else's tool. These are structural checks (shape, required keys,
referential integrity), deliberately not judgements about content.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support import load_tool

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = REPO_ROOT / "evals"
SKILL_DIR = REPO_ROOT / "skills" / "planlint-spec-governance"
CONTEXT7 = REPO_ROOT / "context7.json"
LLMS_TXT = REPO_ROOT / "llms.txt"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
AGENTS_MD = REPO_ROOT / "AGENTS.md"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# Trees whose files are INPUT to planlint rather than documents of this
# repository. A corpus target may legitimately carry an `AGENTS.md`:
# `detect.INVARIANT_SOURCES` lists that filename, so any shape exercising
# invariant discovery needs one, and that file is a fixture rather than
# guidance for a contributor. Excluded by prefix, named here with the reason,
# so a future detection shape does not fail a gate about agent guidance.
FIXTURE_TREES = ("tests/corpus/", "tests/fixtures/")


def nested_agents_files(root: Path = REPO_ROOT) -> list[Path]:
    """Every `AGENTS.md` this repository ships *below* its root.

    Enumerated through git rather than `rglob` + a hand-maintained blocklist.
    The property wanted is "files this repository ships", and
    `--cached --others --exclude-standard` is literally that: tracked files
    plus untracked ones that are not ignored. A glob would descend into
    `build/` and `planlint.egg-info/` and would need a blocklist that drifts
    away from `.gitignore`; `--others` additionally means a nested file is
    seen on the run that *creates* it, before anyone stages it, which is the
    one run where a gate about orphaned files most needs to fire.
    """
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:  # pragma: no cover -- not a git checkout
        return []
    return sorted(
        root / line
        for line in result.stdout.splitlines()
        if line.endswith("AGENTS.md")
        and line != "AGENTS.md"
        and not line.startswith(FIXTURE_TREES)
    )

# A case is a directory carrying a prompt, not "any directory that is not one
# of these". The runner writes its own output beside the cases
# (``evals/results/<timestamp>/``, and ``mocks/`` when MCP stand-ins are
# recorded), so a name blacklist silently turns the first local eval run into
# a failing suite.
EVAL_CASES = sorted(p for p in EVALS_DIR.iterdir() if (p / "prompt.md").is_file())

# Grader kinds the plugin-eval format defines. A grader naming anything else is
# a typo that would silently never run.
_GRADER_TYPES = frozenset(
    {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}
)

# Fields each grader kind cannot work without. A ``regex`` grader with no
# ``pattern`` parses, runs, and grades nothing -- the same silent pass an
# ungraded case gives.
_GRADER_REQUIRED_FIELDS = {
    "regex": ("pattern", "match", "target"),
    "tool_used": ("tool", "should_use"),
    "llm": ("focus",),
}

# What a regex grader may be pointed at. A typo here ("command", "files")
# would match nothing forever while the case still reported PASS.
_GRADER_TARGETS = frozenset({"commands", "files_changed"})

# The tag vocabulary. Tags are how a runner selects a slice of the suite, so an
# invented tag is a case that silently drops out of every filtered run.
_TAGS = frozenset({
    # families
    "activation", "adversarial", "repair", "routing", "discovery",
    # qualifiers
    "authority", "destructive", "dialect", "exit-codes", "machinery",
    "negative", "preflight", "threshold", "waiver", "witness",
})


# See tests/support.py::load_tool -- the one shared copy.
_load_tool = load_tool


def _ids(paths: list[Path]) -> list[str]:
    return [p.name for p in paths]


def _frontmatter_block(text: str, path: Path) -> str:
    assert text.startswith("---\n"), f"{path}: must open with a '---' frontmatter line"
    return text[4:text.index("\n---\n", 4)]


def _frontmatter(text: str, path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in _frontmatter_block(text, path).splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def _frontmatter_list(raw: str) -> list[str]:
    """``[a, b]`` -> ``["a", "b"]``.

    The frontmatter parser above is deliberately flat (it predates any need for
    YAML here and adding a parser dependency for four keys would be worse), so
    list-valued fields arrive as their literal source text. Comparing that text
    with ``in`` makes ``[planlint-spec-governance-old]`` satisfy a check for
    ``planlint-spec-governance``, which is exactly the drift these tests exist
    to catch.
    """
    return [item.strip() for item in raw.strip().strip("[]").split(",") if item.strip()]


# --- evals ------------------------------------------------------------------


def test_eval_suite_is_not_empty() -> None:
    """A silently-empty glob would make every case-level test vacuous."""
    assert len(EVAL_CASES) >= 20, (
        f"expected the eval suite to be populated, found {len(EVAL_CASES)} case(s)"
    )


@pytest.mark.parametrize("case", EVAL_CASES, ids=_ids(EVAL_CASES))
def test_eval_case_has_a_prompt_with_required_frontmatter(case: Path) -> None:
    prompt = case / "prompt.md"
    assert prompt.exists(), f"{case.name}: no prompt.md"
    text = prompt.read_text(encoding="utf-8")
    fields = _frontmatter(text, prompt)
    for key in ("name", "tags", "plugins", "max_turns"):
        assert fields.get(key), f"{case.name}: prompt frontmatter missing {key!r}"
    assert fields["name"] == case.name, (
        f"{case.name}: frontmatter name {fields['name']!r} must match the directory"
    )
    body = text.split("\n---\n", 1)[1].strip()
    assert body, f"{case.name}: prompt has frontmatter but no actual prompt text"


@pytest.mark.parametrize("case", EVAL_CASES, ids=_ids(EVAL_CASES))
def test_eval_case_declares_the_plugin_under_test(case: Path) -> None:
    """A case that forgets the plugin tests the base agent, not this skill.

    Compared against the plugin manifest's own ``name``, not against the skill
    directory's: those two agree today, and nothing here asserted that they do,
    so this check passed for the wrong reason. It is the manifest name a runner
    resolves.
    """
    declared = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["name"]
    fields = _frontmatter((case / "prompt.md").read_text(encoding="utf-8"), case / "prompt.md")
    assert _frontmatter_list(fields["plugins"]) == [declared], (
        f"{case.name}: plugins {fields['plugins']!r} does not name exactly [{declared}]"
    )


@pytest.mark.parametrize("case", EVAL_CASES, ids=_ids(EVAL_CASES))
def test_eval_case_bounds_its_turns(case: Path) -> None:
    """``max_turns`` was only checked for truthiness, so ``banana`` passed."""
    fields = _frontmatter((case / "prompt.md").read_text(encoding="utf-8"), case / "prompt.md")
    raw = fields["max_turns"]
    assert raw.isdigit() and int(raw) > 0, (
        f"{case.name}: max_turns {raw!r} is not a positive integer"
    )


@pytest.mark.parametrize("case", EVAL_CASES, ids=_ids(EVAL_CASES))
def test_eval_case_tags_come_from_the_known_vocabulary(case: Path) -> None:
    """An invented tag drops the case out of every tag-filtered run, silently."""
    fields = _frontmatter((case / "prompt.md").read_text(encoding="utf-8"), case / "prompt.md")
    tags = set(_frontmatter_list(fields["tags"]))
    assert tags, f"{case.name}: no tags"
    unknown = sorted(tags - _TAGS)
    assert not unknown, (
        f"{case.name}: unknown tag(s) {unknown}; add them to _TAGS deliberately "
        "or fix the typo"
    )


@pytest.mark.parametrize("case", EVAL_CASES, ids=_ids(EVAL_CASES))
def test_eval_case_has_at_least_one_typed_grader(case: Path) -> None:
    """An ungraded case always passes, which is worse than not having it."""
    graders = sorted((case / "graders").glob("*.md"))
    assert graders, f"{case.name}: no graders; the case could never fail"
    for grader in graders:
        fields = _frontmatter(grader.read_text(encoding="utf-8"), grader)
        kind = fields.get("type")
        assert kind in _GRADER_TYPES, (
            f"{case.name}/{grader.name}: grader type {kind!r} is not one of "
            f"{sorted(_GRADER_TYPES)}"
        )
        for required in _GRADER_REQUIRED_FIELDS.get(kind, ()):
            assert fields.get(required), (
                f"{case.name}/{grader.name}: a {kind!r} grader needs {required!r}"
            )
        body = grader.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()
        assert body, (
            f"{case.name}/{grader.name}: grader has frontmatter but no rubric; "
            "an LLM grader with no rubric grades nothing"
        )
        if kind == "regex":
            try:
                re.compile(fields["pattern"])
            except re.error as exc:  # pragma: no cover - only on a bad pattern
                raise AssertionError(
                    f"{case.name}/{grader.name}: pattern {fields['pattern']!r} "
                    f"is not a valid regex: {exc}"
                ) from exc
            assert fields["match"] in {"true", "false"}, (
                f"{case.name}/{grader.name}: match {fields['match']!r} is not a boolean"
            )
            assert fields["target"] in _GRADER_TARGETS, (
                f"{case.name}/{grader.name}: target {fields['target']!r} is not one of "
                f"{sorted(_GRADER_TARGETS)}"
            )


# The README carries two tables now (activation/repair/routing, then
# adversarial). Matching table rows across the whole file conflates them, which
# would make the tagging test below demand `adversarial` on an activation case.
_ADVERSARIAL_HEADING = "**Adversarial.**"


def _readme_tables() -> tuple[set[str], set[str]]:
    """Case names listed in the README's first table, and in the adversarial one."""
    readme = (EVALS_DIR / "README.md").read_text(encoding="utf-8")
    assert _ADVERSARIAL_HEADING in readme, (
        f"evals/README.md no longer contains the {_ADVERSARIAL_HEADING!r} marker "
        "this split relies on"
    )
    head, _, tail = readme.partition(_ADVERSARIAL_HEADING)
    row = re.compile(r"^\| `([a-z0-9-]+)` \|", re.MULTILINE)
    return set(row.findall(head)), set(row.findall(tail))


def test_readme_tables_index_every_case_and_only_real_ones() -> None:
    """The README's tables are the suite's index; a stale row hides a gap.

    Asserted in both directions. Only the forward direction was checked before,
    so a case added without a README row was invisible -- and an unindexed case
    is one nobody reviews.
    """
    listed = set().union(*_readme_tables())
    actual = {c.name for c in EVAL_CASES}
    assert not sorted(listed - actual), (
        f"evals/README.md lists case(s) that do not exist: {sorted(listed - actual)}"
    )
    assert not sorted(actual - listed), (
        f"case(s) exist but are in no README table: {sorted(actual - listed)}"
    )


def test_adversarial_table_and_the_adversarial_tag_agree() -> None:
    """Tagging is how a runner selects the half that matters."""
    _, adversarial = _readme_tables()
    assert len(adversarial) >= 10, (
        f"the adversarial table lists {len(adversarial)} cases; they are the point "
        "of the suite"
    )
    tagged = set()
    for case in EVAL_CASES:
        fields = _frontmatter((case / "prompt.md").read_text(encoding="utf-8"), case / "prompt.md")
        if "adversarial" in _frontmatter_list(fields["tags"]):
            tagged.add(case.name)
    assert tagged == adversarial, (
        "the adversarial table and the adversarial tag disagree: "
        f"tabled-not-tagged={sorted(adversarial - tagged)} "
        f"tagged-not-tabled={sorted(tagged - adversarial)}"
    )


def test_eval_prompts_quote_no_credential_shaped_literals() -> None:
    """`make security` scans every tracked file, and these discuss secrets."""
    patterns = (r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{20,}",
                r"github_pat_[A-Za-z0-9_]{20,}", r"sk-[A-Za-z0-9]{20,}",
                r"xox[bpras]-[A-Za-z0-9-]{10,}")
    for path in sorted(EVALS_DIR.glob("**/*.md")):
        body = path.read_text(encoding="utf-8")
        for pattern in patterns:
            assert not re.search(pattern, body), (
                f"{path.relative_to(REPO_ROOT)} matches {pattern!r}; make security scans it"
            )


# --- context7.json ----------------------------------------------------------


def test_context7_config_is_valid_and_its_folders_exist() -> None:
    """A retrieval config scoping a renamed folder indexes nothing, silently."""
    config = json.loads(CONTEXT7.read_text(encoding="utf-8"))
    for key in ("projectTitle", "description", "folders", "excludeFolders"):
        assert key in config, f"context7.json missing {key!r}"
    assert 10 <= len(config["description"]) <= 200, (
        "context7.json description must be between ten and two hundred characters"
    )
    for folder in config["folders"]:
        assert (REPO_ROOT / folder).is_dir(), (
            f"context7.json indexes {folder!r}, which is not a directory"
        )
    for folder in config["excludeFolders"]:
        assert (REPO_ROOT / folder).is_dir(), (
            f"context7.json excludes {folder!r}, which no longer exists; "
            "a stale exclusion silently stops excluding"
        )
    for name in config.get("excludeFiles", []):
        assert (REPO_ROOT / name).exists(), f"context7.json excludes missing file {name!r}"


def test_context7_indexes_the_skill_and_excludes_the_evals() -> None:
    """The scoping decision itself, pinned: skill in, eval prompts out.

    The eval prompts are adversarial instructions ("waive all the findings").
    Indexing them for retrieval would surface those strings to an agent as if
    they were guidance.
    """
    config = json.loads(CONTEXT7.read_text(encoding="utf-8"))
    assert any("skills/" in f for f in config["folders"])
    assert "evals" in config["excludeFolders"]


# --- llms.txt ---------------------------------------------------------------


# Every index an agent reads on its own initiative, rather than because a human
# pointed at it. A dead link here is worse than a dead link in the README: no
# human opens these files, so nothing surfaces the breakage.
#
# Discovered rather than listed. As a fixed tuple this covered exactly the two
# root files, so a nested `AGENTS.md` -- which the nearest-file-wins convention
# makes *more* likely to be the one actually read -- would have had its links
# checked by nothing at all. That is the same argument the docstring above
# already makes, applied to the files it did not reach.
AGENT_INDEXES = (LLMS_TXT, AGENTS_MD, *nested_agents_files())


def _index_id(path: Path) -> str:
    """`tools/AGENTS.md` rather than three test cases all called `AGENTS.md`."""
    return path.relative_to(REPO_ROOT).as_posix()


@pytest.mark.parametrize("path", AGENT_INDEXES, ids=[_index_id(p) for p in AGENT_INDEXES])
def test_agent_index_links_resolve(path: Path) -> None:
    """Every path advertised must exist, or the index sends readers nowhere."""
    links = re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
    assert links, f"{path.name} advertises no documents at all"
    missing = [ref for ref in links if not (REPO_ROOT / ref).exists()]
    assert not missing, f"{path.name} links to missing path(s): {missing}"


def test_agents_md_declares_no_invariant_ids() -> None:
    """A self-referential trap this repository is uniquely able to walk into.

    ``AGENTS.md`` is the last candidate in ``detect.INVARIANT_SOURCES``: for a
    target repository with no dedicated contract file, it is where planlint
    looks for ``INV-n`` declarations. Discovery is content-gated, so an
    ``AGENTS.md`` carrying none is skipped and this repo's own
    ``invariant_source`` stays empty -- which is the state ``make validate``
    currently passes in.

    Write a single ``INV-1`` into this file, though, and planlint's self-run
    adopts it as the invariant source, at which point the bidirectional
    invariant rules start firing against a document that was never meant to
    declare anything. Cheaper to forbid the id here than to debug the gate
    later.

    **Root-scoped, and that is a property of ``detect``, not of this test.**
    ``_invariants()`` iterates ``root / rel`` over the fixed relative paths in
    ``INVARIANT_SOURCES``, so a nested ``tools/AGENTS.md`` is not a candidate
    and cannot spring this trap. ``test_nested_agents_file_declares_no_invariant_ids``
    forbids the id there anyway, because the cost of the habit is zero and the
    cost of relearning it is a debugging session -- and because adding a
    nested path to ``INVARIANT_SOURCES`` would otherwise reopen the trap
    silently.
    """
    from openspec_graph import detect

    assert "AGENTS.md" in detect.INVARIANT_SOURCES, (
        "this guard assumes AGENTS.md is an invariant-source candidate; if that "
        "changed, the trap is gone and so is the reason for this test"
    )
    found = re.findall(r"\bINV-\d+\b", AGENTS_MD.read_text(encoding="utf-8"))
    assert not found, (
        f"AGENTS.md declares invariant id(s) {found}, which makes planlint's own "
        "detect adopt it as this repository's invariant source"
    )


def test_llms_txt_states_the_exit_code_contract() -> None:
    """It is a summary for agents; omitting the contract makes it misleading."""
    text = LLMS_TXT.read_text(encoding="utf-8")
    for token in ("Exit 0", "Exit 1", "Exit 2"):
        assert token in text, f"llms.txt does not state {token}"


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
    AC-pinned check (``test_skill_contract.py::test_rule_catalog_is_fresh``,
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


# --- nested AGENTS.md: the contract, so nine files cannot land in no gate -----
#
# Proposed in docs/agent-directory-wiring-plan.md, milestone 1. These land
# BEFORE any nested file exists, because the plan's whole argument is that the
# guards must exist first: `test_every_root_markdown_file_is_wired_into_the_docs_gate`
# enumerates the repository root only, so without these a nested AGENTS.md is
# held by nothing. `test_nested_agents_discovery_finds_a_planted_file` keeps
# that from being a vacuous claim while the discovered set is still empty.


NESTED_AGENTS = nested_agents_files()
_NESTED_IDS = [p.relative_to(REPO_ROOT).as_posix() for p in NESTED_AGENTS]

# The precedence the root file already states, which every nested file inherits
# and extends by one level. Matched on the distinctive clause rather than the
# whole sentence, so wording can improve without the gate arguing about prose.
PRECEDENCE_CLAUSE = "SKILL.md` wins"

# A file an agent will not finish reading is worse than no file: it displaces
# the root pointer that would have been read instead. From the plan's §5.
MAX_NESTED_LINES = 60


def test_nested_agents_discovery_finds_a_planted_file(tmp_path: Path) -> None:
    """The discovery these contracts rest on actually discovers.

    Every test below is parametrized over `nested_agents_files()`, so while
    that returns nothing they are all zero-case passes -- a green gate that
    has never run. This one plants files in a throwaway git repository and
    asserts what comes back, so the mechanism is proven independently of
    whether this repository has adopted any nested file yet.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "AGENTS.md").write_text("root\n", encoding="utf-8")
    for rel in ("tools/AGENTS.md", "tests/AGENTS.md",
                "tests/corpus/targets/shape/AGENTS.md", "build/AGENTS.md"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")

    found = {p.relative_to(tmp_path).as_posix() for p in nested_agents_files(tmp_path)}
    assert found == {"tools/AGENTS.md", "tests/AGENTS.md"}, found
    # Untracked but not ignored: seen on the run that creates it, which is the
    # run where a gate about orphaned files most needs to fire.
    assert not any(
        subprocess.run(["git", "ls-files", "tools/AGENTS.md"], cwd=tmp_path,
                       capture_output=True, text=True, check=False).stdout.strip()
    ), "precondition: the planted file is untracked, and was still discovered"


@pytest.mark.parametrize("path", NESTED_AGENTS, ids=_NESTED_IDS)
def test_nested_agents_file_states_its_precedence(path: Path) -> None:
    """Nearest-file-wins makes a nested file the one an agent reads first.

    A file that does not say what outranks it is a file that reads as the last
    word on its directory, which is exactly backwards: `SKILL.md` outranks the
    root `AGENTS.md`, and the root file outranks this one.
    """
    assert PRECEDENCE_CLAUSE in path.read_text(encoding="utf-8"), (
        f"{_index_id(path)} does not state its precedence; every nested file "
        f"must say that SKILL.md wins, as the root AGENTS.md does"
    )


@pytest.mark.parametrize("path", NESTED_AGENTS, ids=_NESTED_IDS)
def test_nested_agents_file_declares_no_invariant_ids(path: Path) -> None:
    """Defence in depth against the trap the root guard describes.

    Not reachable today -- `detect.INVARIANT_SOURCES` iterates fixed
    root-relative paths -- but the whole point of that guard is that the trap
    is cheap to fall into and expensive to diagnose. Adding a nested path to
    that tuple later must not silently re-arm it.
    """
    found = re.findall(r"\bINV-\d+\b", path.read_text(encoding="utf-8"))
    assert not found, f"{_index_id(path)} declares invariant id(s) {found}"


@pytest.mark.parametrize("path", NESTED_AGENTS, ids=_NESTED_IDS)
def test_nested_agents_file_stays_short(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= MAX_NESTED_LINES, (
        f"{_index_id(path)} is {len(lines)} lines, over the {MAX_NESTED_LINES}-line "
        f"budget: an agent that does not finish it is worse off than one that "
        f"read the root pointer instead"
    )


@pytest.mark.parametrize("path", NESTED_AGENTS, ids=_NESTED_IDS)
def test_nested_agents_file_has_a_balanced_mermaid_block(path: Path) -> None:
    """Each file carries a diagram of what its directory is for, and the fence
    closes.

    An unclosed ```mermaid fence swallows the rest of the document into a code
    block, and GitHub renders a broken diagram as a small error box that no
    reviewer reads as a failure. This checks the fence, not the diagram's
    semantics -- rendering is a human step recorded in the plan.
    """
    text = path.read_text(encoding="utf-8")
    assert "```mermaid" in text, f"{_index_id(path)} carries no mermaid diagram"
    assert text.count("```") % 2 == 0, (
        f"{_index_id(path)} has an odd number of code fences: an unclosed "
        f"```mermaid block swallows everything after it"
    )
