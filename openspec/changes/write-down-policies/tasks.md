# Tasks: write-down-policies

Measured at `5fe043e` (head of `claude/m0-guard-the-green`), 2026-10-06.
Every line number below is re-checked against the tree before the milestone
that uses it; a sibling package landing first may move a line without moving
the fact. Every count here names the command that produced it.

## Milestone 1 — The document of record

- `docs/policies.md` (new): title `# Policies`; one opening paragraph saying
  this is the document of record for how the repository is versioned and
  worked on, that each policy is stated here once and pointed at from
  elsewhere, and that the operating contract, disclosure and the gate ladder
  live in `skills/planlint-spec-governance/SKILL.md`, `SECURITY.md` and
  `docs/hooks.md` respectively (DEC-POL-010). Then an index — one bullet per
  level-two section, `- [Heading](#anchor) — one line` — followed by the
  sections. Headings are plain words so the anchor is the heading lowercased
  with spaces as hyphens (R-POL-1).
- `docs/policies.md`, section "Versioning and deprecation": the package
  rule (Semantic Versioning; `openspec_graph.__version__` the one source; a
  minor is the only release that may remove or break while the major is 0;
  a patch never does), the schema rule (one integer per machine-readable
  output, declared beside its type — name the five: `rule_types.py`,
  `dialect_card.py`, `witness.py`, `delta.py`, `tools/stage_citations.py`;
  a bump breaks every consumer of that output — `report` exits 2, `witness`
  skips — so it lands only in a release that may break, never a patch, with
  a CHANGELOG entry naming output, old and new integer and changed keys;
  additive keys never bump; `tool_version` is informational; SARIF has no
  planlint integer), and the deprecation window (announced under
  `Deprecated` naming the removal version; warns on stderr only, exit code
  unchanged, through the whole next minor series; removed no earlier than
  the minor after; a longer named window allowed, an unnamed one not;
  interpreter drops follow upstream end-of-life with notice one minor ahead
  and are not this window). Name `specgraph` — deprecated 0.2.0, warns
  through 0.3.x, removed 0.4.0, the window `prepare-release-0-3-0` records
  in the CHANGELOG — and `detect --json` (removal named as 1.0) as the two
  instances. Record the W5 consequence in one sentence: a surface first
  deprecated in 0.3.0 is removed no earlier than 0.5.0 (R-POL-2, R-POL-3,
  DEC-POL-003, DEC-POL-004).
- `docs/policies.md`, section "Count cites a command": the rule as
  DEC-POL-005 words it; `make stage-citations` named as the regenerator for
  every count of cited stages; the dated-measurement form shown with one
  example taken from this package's proposal; `spec-adversary` named as the
  reviewer that re-measures; the CHANGELOG exemption (R-POL-4).
- `docs/policies.md`, section "One agent per thread": the convention as
  DEC-POL-006 words it — owner, when a second agent speaks, wait for the
  push, merge never force-push — and one sentence that this is a convention
  the test holds as written, not as obeyed (R-POL-5).
- `tools/check_docs.py`: add `"docs/policies.md"` to `REQUIRED_DOCS` after
  the `docs/next-steps.md` entry, with a comment in the shape of the
  entries below it: a policy document is permanent where a plan is retired,
  so it is gated where `docs/AGENTS.md` leaves plans ungated (R-POL-7,
  DEC-POL-008). Nothing else in the file changes (C-POL-1).
- `README.md`, "Documentation" section (heading at `README.md:546` at
  `5fe043e`): one bullet after the "Distribution plan" bullet —
  `[Policies](docs/policies.md)` — versioning and the deprecation window,
  `schema_version` bumps, counts that name their command, one agent per
  review thread (R-POL-7). No install command is added; the hook that
  nudges on a README edit asks for `pytest tests/test_adopter_urls.py`, run
  it.
- `llms.txt`, "Optional" list: one line, `[Policies](docs/policies.md)`,
  with a clause naming the `schema_version` rule — the policy an envelope
  consumer needs (R-POL-7).
- `CHANGELOG.md`, `[Unreleased]`: an `Added` entry for this package in the
  shape of the siblings' (what the document holds, where the pointers are,
  the test). Do not add a `specgraph` line under `Deprecated`:
  `prepare-release-0-3-0` R-REL-6 owns it. If that package has already
  landed, read its line and confirm it and `docs/policies.md` state the same
  window — warns through 0.3.x, removed in 0.4.0 (R-POL-9, DEC-POL-009).
- Confirm `python tools/check_docs.py` prints its all-present line, and
  that `docs/policies.md` cites no `make` target the `Makefile` does not
  declare — compare every backticked `make` word in it against
  `grep -E "^[a-zA-Z0-9_.-]+:" Makefile` (C-POL-4).
- **Gate:** `make docs-check`

## Milestone 2 — The pointers

- `openspec/AGENTS.md`: after the four-bullet list of ways a package fails
  and before the paragraph beginning "The `spec.md` — not just the
  `proposal.md`", one sentence as its own paragraph: a number written into
  a package names the command that regenerates it — the count-cites-a-command
  policy in `[docs/policies.md](../docs/policies.md#count-cites-a-command)`.
  Nothing else changes; the list's "Four ways" stays true (R-POL-6,
  DEC-POL-002). `wc -l openspec/AGENTS.md` read 49 at `5fe043e`; confirm the
  result is within `MAX_NESTED_LINES` as `tests/test_agent_artifacts.py`
  declares it.
- `docs/agents-skills-harness.md`: a short closing section after
  "Per-directory guidance" — heading "Where the working policies live", one
  sentence: how this repository is worked on — one agent per review thread,
  counts that name the command that produced them, the version and
  deprecation window — is policy, written once in
  `[policies.md](policies.md#one-agent-per-thread)` and pointed at from
  here. Do not add or alter any sentence of the form "The N rules"
  (`tests/test_rule_registry_docs.py:58–63`) (R-POL-6, C-POL-3,
  DEC-POL-002).
- `docs/AGENTS.md`: in the first bullet, after "catch** in other people's
  repositories", add the link `([policies.md](policies.md#count-cites-a-command))`;
  in the mermaid diagram, add `policies.md` to the node that lists
  `aqa.md · next-steps.md · agents-skills-harness.md`, so the picture of what
  `tools/check_docs.py` gates stays true (R-POL-6, DEC-POL-002). The file
  read 35 lines at `5fe043e`.
- Run `python -m pytest tests/test_agent_artifacts.py -q -k "nested_agents or
  agent_index_links or make_citation_in_an_agent_index"` and confirm every
  nested-file contract and link check is green with the new links in place
  (AC-POL-5, AC-POL-6).
- **Gate:** `make test`

## Milestone 3 — The guard

- `tests/test_policies_doc.py` (new module): module docstring naming this
  package and the argument — the document is the one place the policy set
  is written, so the test reads it rather than a copy. Constants `REPO_ROOT`,
  `POLICIES = REPO_ROOT / "docs" / "policies.md"`, and `POINTER_FILES`
  naming `openspec/AGENTS.md`, `docs/AGENTS.md` and
  `docs/agents-skills-harness.md`; `LINKING_FILES` is `POINTER_FILES` plus
  `llms.txt` and `README.md`. Helpers: `_anchor(heading)` — lowercase,
  spaces to hyphens, drop every character that is not a letter, digit or
  hyphen; `_headings(text)` — every `^## ` line; `_index_anchors(text)` —
  every `](#anchor)` in the index block, read as the bullets between the
  opening paragraph and the first level-two heading;
  `_policy_links(path)` — every markdown link in the file whose path part
  resolves, against the containing directory, to `POLICIES` and which
  carries a fragment. Every check collects a list of offenders and asserts
  `not offenders` with the joined list as the message (R-POL-8,
  DEC-POL-007).
- Planned test functions, named here so the spec's stage-only citations can
  be re-pointed when they exist (AC-POL-1, AC-POL-3, AC-POL-4, AC-POL-6):
  `test_policies_doc_is_registered_in_the_docs_gate_and_named_in_the_readme`
  (membership in `REQUIRED_DOCS` through `load_tool("check_docs",
  "check_docs.py")`, and the literal `docs/policies.md` in `README.md`);
  `test_every_policy_heading_is_indexed_and_every_index_anchor_resolves`;
  `test_every_policy_pointer_resolves_to_a_heading_and_each_pointer_file_has_one`;
  `test_every_make_citation_in_the_policy_doc_names_a_real_target`
  (`parse_semantics.MAKE_REF` over the document against
  `detect.profile(REPO_ROOT).make_targets`, asserting the target set is
  non-empty first, as the agent-index guard does);
  `test_a_dead_index_anchor_is_named` and
  `test_an_unindexed_policy_heading_is_named` (each writes a planted
  document under `tmp_path` and calls the same helpers the real-tree tests
  use, asserting the failure message carries the anchor or heading);
  `test_a_pointer_to_a_missing_fragment_is_named` (a planted pointer file
  under `tmp_path` beside a planted document). Write each against the real
  tree first so its green state is seen once with the document in place,
  then plant the defect and watch it go red.
- Confirm the module carries no list of expected headings or anchors
  (R-POL-8), imports nothing beyond the standard library, `pytest`,
  `tests.support.load_tool` and the two `openspec_graph` names it needs, and
  passes under `make lint` and `make typecheck` (the `tests/` tree is in the
  lint scan; the strict mypy scope is `openspec_graph` and `tools`).
- **Gate:** `make test`

## Milestone 4 — Confirm and record

- Re-point AC-POL-3, AC-POL-4 and the document half of AC-POL-6 from
  stage-only verification to the test names in Milestone 3, keeping the
  stage; add the registration test to AC-POL-1's citation beside
  `test_docs_check_passes`. Run
  `python -m pytest tests/test_spec_test_citations.py -q` and confirm every
  selector resolves.
- Run `make stage-citations` and confirm this package added no stage to the
  set no workflow invokes by name: its criteria cite `test`, `docs-check`
  and `validate`, all of which were already cited on verification lines at
  `5fe043e`.
- Re-read `docs/policies.md` against the tree once more: the five
  `SCHEMA_VERSION` declarations and their values
  (`grep -rn "SCHEMA_VERSION\s*=" openspec_graph tools`), the two deprecation
  strings in `openspec_graph/cli.py`, the `Deprecated` entries in
  `CHANGELOG.md`. A policy that misdescribes the tree on the day it lands is
  the drift this package exists to end.
- Confirm `openspec_graph/`, the `Makefile`, `tests/baseline_rules.json`
  and `README.md`'s rules table are absent from this package's diff, and
  that `tools/check_docs.py`'s diff is one list entry and its comment
  (C-POL-1, AC-POL-7, AC-POL-8).
- Cross-check with `prepare-release-0-3-0`, whichever of the two lands
  second: its CHANGELOG `Deprecated` line (R-REL-6) and warning string
  (R-REL-7) state the window `docs/policies.md` states — warns through
  0.3.x, removed in 0.4.0 — and, if that package is still a draft, its
  author is told `docs/policies.md` is where the general rule lives so its
  CHANGELOG line can name it (DEC-POL-009).
- Confirm this package validates clean under the repo's own rules
  (`planlint --target . validate --fail-on ERROR --change
  write-down-policies`), then the whole tree, reporting both exit codes.
- Record for W5 (dead and drifting code), when it is drafted: a surface
  first deprecated in 0.3.0 is removed no earlier than 0.5.0 under
  DEC-POL-004; the plan's W5.1 and W5.2 say 0.4.0 and will follow the
  policy or amend it by name.
- Record for the plan's M1 row, when `docs/reflection-plan-2026-10.md`
  merges: the policies live in `docs/policies.md`, not in
  `docs/agents-skills-harness.md` and `openspec/AGENTS.md` as W8.3 names
  them; those two files carry one-sentence pointers (DEC-POL-001,
  DEC-POL-002).
- **Gate:** `make pre-pr`
