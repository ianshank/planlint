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
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

EVALS_DIR = REPO_ROOT / "evals"

SKILL_DIR = REPO_ROOT / "skills" / "planlint-spec-governance"

CONTEXT7 = REPO_ROOT / "context7.json"

LLMS_TXT = REPO_ROOT / "llms.txt"

PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"

AGENTS_MD = REPO_ROOT / "AGENTS.md"

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
        # Split on "/" rather than `endswith("AGENTS.md")`: that substring test
        # also matches a path ending in the filename, so a future
        # `docs/NOTAGENTS.md` would be held to the nested-agent contracts it
        # was never meant to satisfy. A path segment comparison is what the
        # docstring above claims and what the caller expects.
        if line.rpartition("/")[2] == "AGENTS.md"
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


@pytest.mark.integration
def test_eval_suite_is_not_empty() -> None:
    """A silently-empty glob would make every case-level test vacuous."""
    assert len(EVAL_CASES) >= 20, (
        f"expected the eval suite to be populated, found {len(EVAL_CASES)} case(s)"
    )

@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.integration
@pytest.mark.parametrize("case", EVAL_CASES, ids=_ids(EVAL_CASES))
def test_eval_case_bounds_its_turns(case: Path) -> None:
    """``max_turns`` was only checked for truthiness, so ``banana`` passed."""
    fields = _frontmatter((case / "prompt.md").read_text(encoding="utf-8"), case / "prompt.md")
    raw = fields["max_turns"]
    assert raw.isdigit() and int(raw) > 0, (
        f"{case.name}: max_turns {raw!r} is not a positive integer"
    )

@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.integration
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


@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.e2e
@pytest.mark.parametrize("path", AGENT_INDEXES, ids=[_index_id(p) for p in AGENT_INDEXES])
def test_agent_index_links_resolve(path: Path) -> None:
    """Every path advertised must exist, or the index sends readers nowhere.

    Resolved against the *containing directory*, which is what every markdown
    renderer does, GitHub included. Against ``REPO_ROOT`` this was right only
    because both original indexes sat at the root: the first nested file would
    have had a correct sibling link (``[x](_common.py)`` from ``tools/``)
    reported as missing, and the way to satisfy the gate would have been to
    write a repo-root-relative path that then breaks when a reader clicks it.
    A gate that can only be satisfied by breaking the thing it checks is worse
    than no gate. Verified in both directions before changing it.
    """
    links = re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
    assert links, f"{path.name} advertises no documents at all"
    missing = [
        ref for ref in links
        # An external URL is not this repository's to resolve, and a bare
        # anchor addresses the current document.
        if not ref.startswith(("http://", "https://", "mailto:", "#"))
        and not (path.parent / ref.split("#", 1)[0]).exists()
    ]
    assert not missing, f"{_index_id(path)} links to missing path(s): {missing}"

@pytest.mark.integration
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

@pytest.mark.integration
def test_llms_txt_states_the_exit_code_contract() -> None:
    """It is a summary for agents; omitting the contract makes it misleading."""
    text = LLMS_TXT.read_text(encoding="utf-8")
    for token in ("Exit 0", "Exit 1", "Exit 2"):
        assert token in text, f"llms.txt does not state {token}"

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

@pytest.mark.e2e
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
                "tests/corpus/targets/shape/AGENTS.md", "build/AGENTS.md",
                # Matched by a naive endswith("AGENTS.md") and by nothing a
                # reader would call a nested agent file.
                "docs/NOTAGENTS.md"):
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

@pytest.mark.e2e
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

@pytest.mark.e2e
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

@pytest.mark.e2e
@pytest.mark.parametrize("path", NESTED_AGENTS, ids=_NESTED_IDS)
def test_nested_agents_file_stays_short(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= MAX_NESTED_LINES, (
        f"{_index_id(path)} is {len(lines)} lines, over the {MAX_NESTED_LINES}-line "
        f"budget: an agent that does not finish it is worse off than one that "
        f"read the root pointer instead"
    )

@pytest.mark.e2e
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

# --- M5: a cited command that does not exist ---------------------------------


@pytest.mark.e2e
def test_every_make_citation_in_an_agent_index_names_a_real_target() -> None:
    """G004, turned on this repository's own agent-facing prose.

    Milestone 5 of docs/agent-directory-wiring-plan.md, and the reason it was
    worth building after all: a nested `AGENTS.md` naming a stale command is
    worse than no file, because an agent runs it and gets an error it cannot
    attribute. The plan proposed reusing `resolve_makefile` and parsing
    targets by hand; the shipped code already does both better.

    `MAKE_REF` is the matcher G004 uses to find stage citations in a
    stranger's spec, and `detect.profile().make_targets` is the target set it
    checks them against. Pointing the pair at this repository is the same
    check, on the same code path, with this repo as the target — so the guard
    cannot drift from the rule, and a change to either is caught here too.

    What was **dropped** rather than deferred, per the plan's instruction to
    decide explicitly: the general "every fenced command names a real
    executable" check. It needs a shell-command parser to survive pipelines,
    flags and redirections, it false-positives on anything it half-parses, and
    it would cover exactly one command today (`planlint ... validate`, whose
    console script `test_console_script_is_declared` already pins). The
    complexity is real and the coverage is one line.
    """
    from openspec_graph import detect
    from openspec_graph.parse_semantics import MAKE_REF

    targets = set(detect.profile(REPO_ROOT).make_targets)
    assert targets, (
        "detect found no make targets in this repository, so this guard would "
        "pass vacuously -- the detector, not the citations, is what broke"
    )

    unknown: dict[str, list[str]] = {}
    for path in AGENT_INDEXES:
        cited = sorted(set(MAKE_REF.findall(path.read_text(encoding="utf-8"))))
        missing = [stage for stage in cited if stage not in targets]
        if missing:
            unknown[_index_id(path)] = missing
    assert not unknown, (
        f"agent-facing file(s) cite `make <stage>` targets this repository does "
        f"not declare: {unknown}. This is the same defect G004 reports in a "
        f"stranger's spec; fix the citation or add the target."
    )
