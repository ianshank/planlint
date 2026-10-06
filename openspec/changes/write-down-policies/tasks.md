# Tasks: write-down-policies

Measured at `5fe043e` (head of `claude/m0-guard-the-green`), 2026-10-06,
before the two sibling M1 packages — `pin-actions-by-sha` and
`prepare-release-0-3-0` — landed on `claude/m1-pin-and-release`. Every line
number below is re-checked against the tree before the milestone that uses
it; a sibling package landing first may move a line without moving the fact.
Every count here names the command that produced it, and Milestone 4
re-measures at the branch head: at `ea40bc2` `make stage-citations` reads 49
specs, `pre-pr` mentioned in 44 and verified by 11, `validate` mentioned in
19 and verified by 8, `ci` mentioned in 14 and verified by 7. Landing order
(R-POL-9): `pin-actions-by-sha`, then this package, then
`prepare-release-0-3-0`.

## Milestone 1 — The document of record

- `docs/policies.md` (new): title `# Policies`; one opening paragraph saying
  this is the document of record for how the repository is versioned and
  worked on, that each policy is stated here once and pointed at from
  elsewhere, and that the operating contract, disclosure and the gate ladder
  live in `skills/planlint-spec-governance/SKILL.md`, `SECURITY.md` and
  `docs/hooks.md` respectively (DEC-POL-010). Then an index — one bullet per
  level-two section, `- [Heading](#anchor) — one line` — followed by the
  sections. Headings are plain words so the anchor is the heading lowercased
  with spaces as hyphens (R-POL-1). Any CHANGELOG heading shown as an
  example goes inside a fenced code block, which the guard skips.
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
  planlint integer; state the refusal as exit 2 and do not quote the
  message, DEC-POL-011), and the deprecation window as a minimum (announced
  under `Deprecated` in the notes of a minor 0.Y.0 naming the removal
  version; keeps working through the whole 0.Y.x series, warning on stderr
  with the exit code unchanged where the tool runs it; removable from
  0.(Y+1).0; a longer named window allowed, an unnamed one not). Name the
  three instances honestly: `specgraph` — a bare "will be removed" warning
  since 0.2.0, whose notes had no `Deprecated` group and filed the rename
  under `Changed`; announced with its removal version in the 0.3.0 release
  notes; warns through 0.3.x; removed in 0.4.0 — exceeds the minimum;
  `detect --json` (deprecated 0.2.0, removal named as 1.0) exceeds it;
  Python 3.10 (announced in the 0.3.0 notes, dropped in 0.4.0) meets it
  exactly. Phrase the `specgraph` window as what the 0.3.0 release notes
  state, not as a citation of a change package (R-POL-2, R-POL-3,
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
  consumer needs (R-POL-7). The literal `docs/policies.md` is what the new
  module's registration test looks for (R-POL-8).
- `CHANGELOG.md`, `[Unreleased]`: an `Added` entry for this package in the
  shape of the siblings' (what the document holds, where the pointers are,
  the test), and under `### Deprecated`, beside the Python 3.10 entry, the
  `specgraph` line — **the `specgraph` alias is removed in 0.4.0.** It warns
  to stderr through every 0.3.x release and delegates with the exit code
  preserved; in 0.4.0 the entry point goes; the waiver syntax, the config
  file name and the `[tool.specgraph]` section are stable identifiers and
  are not affected; the general rule is in `docs/policies.md`. Written here
  because this package lands before `prepare-release-0-3-0` cuts
  `[Unreleased]` into `[0.3.0]`; if the cut has already happened when this
  lands, put both lines under `[0.3.0]` instead. Run
  `grep -n -i specgraph CHANGELOG.md` first and confirm no sibling has
  written the line already — the release package's tasks say it writes the
  line only if this package has not (R-POL-9, DEC-POL-009).
- Confirm `python tools/check_docs.py` prints its all-present line, and
  that `docs/policies.md` cites no `make` target the `Makefile` does not
  declare — compare every backticked `make` word in it against
  `grep -E "^[a-zA-Z0-9_.-]+:" Makefile` (C-POL-4).
- Follow-ups found while writing the document, not fixed here (C-POL-1
  closes both files to this package): `openspec_graph/rule_types.py:32–36`
  restates the bump rule without a link and says "all three machine-readable
  outputs" where `grep -rn "SCHEMA_VERSION\s*=" openspec_graph tools` finds
  five; and `skills/planlint-spec-governance/references/exit-codes.md:107`
  quotes "unsupported schema_version <got> (expected <n>)" where
  `openspec_graph/report.py:259–261` emits "findings schema_version <got> is
  not the <n> this build reads; regenerate the envelope with this version of
  planlint" (the card refusal at `:303–305` differs the same way). The first
  belongs to whichever package next touches `rule_types.py`; the second to
  a skill release under `docs/hooks.md`'s "Releasing a skill change"
  (DEC-POL-002, DEC-POL-011).
- **Gate:** `make docs-check`

## Milestone 2 — The pointers

- `openspec/AGENTS.md`: after the four-bullet list of ways a package fails
  and before the paragraph beginning "The `spec.md` — not just the
  `proposal.md`", one sentence as its own paragraph: a number written into
  a package names the command that regenerates it — the count-cites-a-command
  policy, with the link
  `[docs/policies.md](../docs/policies.md#count-cites-a-command)` on a line
  of its own so it cannot wrap. Nothing else changes; the list's "Four ways"
  stays true (R-POL-6, DEC-POL-002). `wc -l openspec/AGENTS.md` read 49 at
  `5fe043e`; a paragraph of one wrapped sentence plus the link line and two
  blank lines simulates to 53, within the 60 `tests/test_agent_artifacts.py`
  declares as `MAX_NESTED_LINES` — confirm with `wc -l` after the edit. No
  test holds a markdown line width.
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
  the bullet's existing sentence stays as the local reminder and gains no
  detail the document lacks (R-POL-1). In the mermaid diagram, add
  `policies.md` to the node that lists
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
  `llms.txt` and `README.md`; `HEADING_FORM = re.compile(r"^[A-Za-z0-9 -]+$")`.
  Helpers: `_anchor(heading)` — lowercase, spaces to hyphens, nothing else,
  correct by construction once every heading matches `HEADING_FORM`;
  `_headings(text)` — every `^## ` line outside a fenced code block, tracked
  by toggling on lines that start with three backticks; `_index_anchors(text)`
  — every `](#anchor)` in the bullets between the opening paragraph and the
  first level-two heading; `_policy_links(text)` — every markdown link whose
  path part ends in `policies.md` and carries a fragment, as
  `(path, fragment)` pairs (R-POL-8, DEC-POL-007).
- The two offender functions both kinds of test call (R-POL-8, DEC-POL-007):
  `_index_offenders(text: str) -> list[str]` — returns, in order, `"no
  level-two heading"` if `_headings` is empty, `"no index entry"` if
  `_index_anchors` is empty, one entry per heading that fails `HEADING_FORM`
  (`"heading not plain words: <heading>"`), one per repeated heading, one
  per index anchor with no heading (`"index anchor with no heading:
  #<anchor>"`), one per heading with no index entry (`"heading not indexed:
  <heading>"`); `_pointer_offenders(pointer_text: str, policies_text: str)
  -> list[str]` — one entry per `_policy_links(pointer_text)` fragment that
  is not in `{_anchor(h) for h in _headings(policies_text)}`, as
  `"#<fragment>"`. Both return `[]` on a clean input. The real-tree tests
  prefix each offender with the file it came from; the planted tests assert
  on the bare strings.
- Planned test functions, named here so the spec's stage-only citations can
  be re-pointed when they exist (AC-POL-1, AC-POL-3, AC-POL-4, AC-POL-6):
  `test_policies_doc_is_registered_in_the_docs_gate_and_named_in_the_readme_and_llms`
  (membership in `REQUIRED_DOCS` through `load_tool("check_docs",
  "check_docs.py")`, the literal `docs/policies.md` in `README.md`, and the
  same literal in `llms.txt` — the clause nothing else guards);
  `test_every_policy_heading_is_indexed_and_every_index_anchor_resolves`
  (`_index_offenders(POLICIES.read_text())` is empty);
  `test_every_policy_pointer_resolves_to_a_heading_and_each_pointer_file_has_one`
  (for each of `LINKING_FILES`: `_pointer_offenders` is empty, and each
  link's path resolves from the file's parent to `POLICIES`; for each of
  `POINTER_FILES`: at least one policy link);
  `test_every_make_citation_in_the_policy_doc_names_a_real_target`
  (`parse_semantics.MAKE_REF` over the document against
  `detect.profile(REPO_ROOT).make_targets`, asserting the target set is
  non-empty first, as the agent-index guard does);
  `test_a_dead_index_anchor_is_named`,
  `test_an_unindexed_policy_heading_is_named` and
  `test_an_empty_policy_document_is_an_offender_not_a_pass` (each builds a
  short planted text — no `tmp_path` needed — calls `_index_offenders`, and
  asserts the anchor, the heading, or the two floor strings appear);
  `test_a_pointer_to_a_missing_fragment_is_named` (a planted pointer text
  with `../docs/policies.md#no-such-heading` against a planted policies
  text; the offender names the fragment). Write each real-tree test so its
  green state is seen once with the document in place, then confirm the
  planted tests go red when their offender function is stubbed to return
  `[]` and green when it is restored.
- Confirm the module carries no list of expected headings or anchors
  (R-POL-8), imports nothing beyond the standard library, `pytest`,
  `tests.support.load_tool` and the two `openspec_graph` names it needs, and
  passes under `make lint` and `make typecheck` (the `tests/` tree is in the
  lint scan; the strict mypy scope is `openspec_graph` and `tools`).
- **Gate:** `make test`

## Milestone 4 — Confirm and record

- Re-point AC-POL-3 and AC-POL-4 from stage-only verification to the test
  names in Milestone 3, keeping the stage; add the registration test to
  AC-POL-1's citation beside `test_docs_check_passes`; add
  `test_every_make_citation_in_the_policy_doc_names_a_real_target` to
  AC-POL-6's. Run `python -m pytest tests/test_spec_test_citations.py -q`
  and confirm every selector resolves.
- Run `make stage-citations` at the branch head and record the output's
  spec count and the `pre-pr`, `validate` and `ci` rows here beside the
  `ea40bc2` figures in the header; confirm this package added no stage to
  the set no workflow invokes by name — its criteria cite `test`,
  `docs-check` and `validate`, all of which were already cited on
  verification lines at `5fe043e` and at `ea40bc2`.
- Re-read `docs/policies.md` against the tree once more: the five
  `SCHEMA_VERSION` declarations and their values
  (`grep -rn "SCHEMA_VERSION\s*=" openspec_graph tools`), the two deprecation
  strings in `openspec_graph/cli.py`, the `Deprecated` entries in
  `CHANGELOG.md` (`grep -n -A3 "^### Deprecated" CHANGELOG.md`). A policy
  that misdescribes the tree on the day it lands is the drift this package
  exists to end. One known gap is accepted, not hidden: until
  `prepare-release-0-3-0` lands, `_DEPRECATION_WARNING` names no version
  while the CHANGELOG line does (DEC-POL-009).
- Confirm `openspec_graph/`, `skills/`, the `Makefile`,
  `tests/baseline_rules.json` and `README.md`'s rules table are absent from
  this package's diff, and that `tools/check_docs.py`'s diff is one list
  entry and its comment (C-POL-1, AC-POL-7, AC-POL-8).
- Cross-check with `prepare-release-0-3-0`, which lands after this package
  (R-POL-9, DEC-POL-009): its CHANGELOG cut carries this package's `Added`
  entry and `specgraph` `Deprecated` line under `[0.3.0]` and writes no
  second `specgraph` line (its proposal records this; its Milestone 1
  CHANGELOG bullet greps for the line first); its warning string (R-REL-7)
  states the window `docs/policies.md` states — warns through 0.3.x,
  removed in 0.4.0; and its `tasks.md` header is dated at a commit and
  names the command behind its line count — at `ea40bc2` it is dated and
  names `grep -n '^## ' CHANGELOG.md`; if a later revision drops either,
  tell its author. Tell its author also that `docs/policies.md` is where the
  general rule lives, so its `[0.3.0]` preamble or `Deprecated` group can
  name it.
- Confirm this package validates clean under the repo's own rules
  (`planlint --target . validate --fail-on ERROR --change
  write-down-policies`), then the whole tree, reporting both exit codes.
- Record for the plan's M1 row, when `docs/reflection-plan-2026-10.md`
  merges: the policies live in `docs/policies.md`, not in
  `docs/agents-skills-harness.md` and `openspec/AGENTS.md` as W8.3 names
  them; those two files carry one-sentence pointers (DEC-POL-001,
  DEC-POL-002); the deprecation window is the one-minor minimum W1.5 and W5
  already assume, so neither needs amending (DEC-POL-004).
- **Gate:** `make pre-pr`
