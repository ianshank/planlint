# Change: Write the Policies Down, Once — Versioning and Deprecation, Counts That Name Their Command, One Agent per Thread

## Why

Three rules this repository already lives by are written nowhere a reader
would look for them, or are written in one directory's `AGENTS.md` and not
the next. Every machine-readable output the tool emits announces an integer
`schema_version`, and the only statement of when that integer moves is a
code comment beside one of the five declarations; nothing says what a bump
means for a consumer, or in which kind of release it may happen. The
`specgraph` alias has been deprecated since 0.2.0 with a warning that says it
"will be removed" and names no version, while `detect --json`, deprecated in
the same release, names 1.0 — two deprecations, two conventions, one of them
open-ended. A number written into a spec goes stale inside its own branch
(`add-witness-ci-artifacts`'s DEC-WCA-016 recorded how many specs cite `ci`
and `pre-pr` on verification lines; today's report reads differently for
both), and the rule that fixes it — a count names the command that
regenerates it — is stated for `docs/` in `docs/AGENTS.md` and for nobody
else. And two coding agents fixed one review thread at once on this branch,
costing a merge commit and a re-run, with no convention anywhere about who
owns a thread.

This package writes the three policies down once, in a document of record,
with one-line pointers from the places an agent or a contributor actually
reads, and a test that holds the document's structure so a policy cannot be
added without being indexed or pointed at without resolving. It is item
W8.3 of milestone M1 of the October 2026 reflection plan; that plan sits on
`origin/claude/reflection-plan-2026-10` (`80708db`) and is not in this tree,
so its reflections R2 and R3 are restated here and every fact below is
re-measured against this checkout. Docs plus one test; no code behaviour
changes.

**Evidence:** measured at `5fe043e` (the head of `claude/m0-guard-the-green`,
read from `.git/refs/heads/`), 2026-10-06. Each number names the command that
produced it, which is the policy this package writes down, applied to itself.

- **Five schema versions, one comment.**
  `grep -rn "SCHEMA_VERSION\s*=" openspec_graph tools` finds five
  declarations, every one `= 1`: `openspec_graph/rule_types.py:37`
  (`FINDINGS_SCHEMA_VERSION`, the `validate --json` envelope),
  `openspec_graph/dialect_card.py:16` (the `detect --format json` card),
  `openspec_graph/witness.py:38` (`WITNESS_SCHEMA_VERSION`),
  `openspec_graph/delta.py:40` (`DELTA_SCHEMA_VERSION`) and
  `tools/stage_citations.py:67`. Only `rule_types.py:32–36` says when the
  integer moves: "Bump on any breaking change to the envelope or to a
  finding's own keys; additive keys do not bump it." The consumer side is
  implemented and undocumented as policy: `report.parse_envelope`
  (`openspec_graph/report.py:257–260`) and `parse_card` (`:301–304`) refuse
  a payload whose version is not this build's — exit 2, quoted at
  `skills/planlint-spec-governance/references/exit-codes.md:107` — while a
  `tool_version` mismatch is a WARNING that still projects (`:111–112`);
  `witness._load_one` skips a record whose version differs
  (`openspec_graph/witness.py:194–198`); `dialect_card.diff_cards` reports
  a card whose version changed as its own kind of change
  (`openspec_graph/dialect_card.py:58–61`). The SARIF projection carries no
  planlint schema version at all: `openspec_graph/sarif.py:28` pins
  `SARIF_VERSION = "2.1.0"` and `:172–173` puts the tool version in
  `driver.version`. Two precedents exist and neither is written as a rule:
  `add-findings-json-envelope`'s DEC-FE-010 started the envelope at 1 and
  kept it apart from the package version, and `add-finding-line-hits` left it
  at 1 because "the `line` key already existed" (`CHANGELOG.md:423`).
- **Two deprecations, two conventions.**
  `grep -n -i deprecat openspec_graph/cli.py`: `_DEPRECATION_WARNING`
  (`cli.py:1010–1013`) reads "`specgraph` is deprecated; use `planlint`
  instead. The `specgraph` command is a backwards-compatible alias and will
  be removed." — no version; `main_deprecated` (`:1016–1025`) prints it to
  stderr and delegates, never changing the exit code, which
  `tests/test_cli_surface.py:239,250,264` pin.
  `_DETECT_JSON_DEPRECATED` (`cli.py:80–84`) reads "will be removed in
  1.0". `pyproject.toml:67` still maps the `specgraph` console script to
  `main_deprecated`. `README.md:84–89` describes the alias with no window.
  `grep -n -i specgraph CHANGELOG.md` finds the rename entry inside the
  0.2.0 section (`CHANGELOG.md:1382–1391`) and no `Deprecated` entry for the
  alias anywhere; the only `Deprecated` entry under `[Unreleased]`
  (`CHANGELOG.md:45–52`) is Python 3.10's, which names 0.4.0
  (`harden-ci-workflows` R-HCW-12, DEC-HCW-006). The plan's §1.2 row
  "Release" records the same fact — "the `specgraph` alias is deprecated with
  no removal date" — and its W1.5 states the window to adopt: warns through
  0.3.x, removed in 0.4.0. A sibling draft on this branch,
  `openspec/changes/prepare-release-0-3-0/` (W1.5), already specifies both
  edits that close it: its R-REL-6 writes the `specgraph` window into the
  CHANGELOG's `Deprecated` group and its R-REL-7 makes the warning string
  name 0.4.0 (DEC-REL-005, "stated where each audience reads"). It states
  the same window this package writes down; what it does not do is state
  the general rule the window is an instance of.
- **The package version is SemVer by declaration.** `CHANGELOG.md:4`
  declares Semantic Versioning 2.0.0; `openspec_graph/__init__.py:16` is
  `__version__ = "0.2.0"`, the single source `pyproject.toml` reads
  (DEC-SD-009, in the comment above it); `grep -n "^## " CHANGELOG.md`
  shows `[Unreleased]`, `[0.2.0] — 2026-09-12` and `[0.1.0] — 2026-08-30`.
  No document says what a minor means while the major is 0.
- **The count rule is written for one directory.** `docs/AGENTS.md:3–5`:
  "a number in this directory should be one a reader can regenerate with a
  named command", restated in its first bullet.
  `grep -n -i -E "count|regenerat|command" openspec/AGENTS.md` finds only
  the gate command; the four-trap list there has no fifth about counts.
  `.claude/agents/spec-adversary.md:20` (checklist item 8) re-measures every
  count a draft states, so the rule is enforced by review and stated for the
  wrong directory. The drift it prevents is in the tree twice:
  `add-witness-ci-artifacts`'s DEC-WCA-016 says "Seven specs cite `pre-pr`
  and six cite `ci` on Verified-by lines" and names `make stage-citations`
  as the regenerator; at `5fe043e` `make stage-citations` reports `ci`
  mentioned in 14 specs and verified by 7, `pre-pr` mentioned in 41 and
  verified by 9 — the numbers moved, the command stayed true. And
  `docs/peer-review-2026-10.md:267` records the E501 count "re-counted three
  times (100, 122, 121) without being done", with `:447` asking that it not
  be counted a fourth time.
- **Two agents, one thread.** The plan's R3: Copilot's coding agent pushed
  its own fix while the session's ladder ran; the merge kept the lexer and
  adopted two details of theirs; cost one merge commit, one re-run of the
  tools coverage leg, about fifteen minutes. The in-tree trace is
  `openspec/changes/harden-ci-workflows/tasks.md`, Milestone 9: "Copilot's
  review of the first implementation (PR #38, head `b658242`)".
  `grep -n -i -E "thread|one agent|concurrent|owns" docs/agents-skills-harness.md openspec/AGENTS.md docs/AGENTS.md`
  finds nothing; `docs/hooks.md:113–186` describes the `.claude/` agents
  and the drafter's shell and says nothing about two agents on one thread.
- **Where a pointer can go, and how much room it has.**
  `wc -l openspec/AGENTS.md docs/AGENTS.md docs/agents-skills-harness.md`
  reads 49, 35 and 142. `tests/test_agent_artifacts.py` holds every nested
  `AGENTS.md` to `MAX_NESTED_LINES` (`test_nested_agents_file_stays_short`),
  to a stated precedence clause, a balanced mermaid fence, no `INV-n`, and
  links that resolve from the containing directory
  (`test_agent_index_links_resolve`, which also covers `llms.txt`); and
  `test_every_make_citation_in_an_agent_index_names_a_real_target` runs
  G004's own matcher over those files. `docs/agents-skills-harness.md` is
  read by `tests/test_rule_registry_docs.py:58–63` for the phrase
  `The (\d+) rules`, so an edit there must not add a second rule-count claim.
- **How a document becomes gated.** `tools/check_docs.py:17–40`
  `REQUIRED_DOCS` lists nine documents that must exist and be named in
  `README.md`; `make docs-check` (`Makefile:74–75`) runs it;
  `tests/test_gate_scripts.py:34–47` builds its fixture from `REQUIRED_DOCS`
  itself, so a new entry needs no test edit;
  `tests/test_enterprise.py:307` runs the real tree.
  `test_every_root_markdown_file_is_wired_into_the_docs_gate` is root-scoped
  by design, so a file under `docs/` is gated only if someone registers it.
  `docs/AGENTS.md` says a `*-plan.md` is deliberately ungated because it is
  consumed and retired; a policy document is the opposite kind of file.

## What Changes

- `docs/policies.md` (new): the document of record. An opening paragraph
  saying what it is and is not, an index with one bullet per policy linking
  its anchor, then three sections with plain-word headings — versioning and
  deprecation (semantic versioning for the package, what a `schema_version`
  bump means and where it may land, the deprecation window, with `specgraph`
  as the first instance and `detect --json` as the second); the
  count-cites-a-command rule; the one-agent-per-thread convention — each
  carrying the wording DEC-POL-003 through DEC-POL-006 decide, and a closing
  line pointing at `SKILL.md`, `SECURITY.md` and `docs/hooks.md` for the
  rules this document deliberately does not restate.
- `tools/check_docs.py`: one `REQUIRED_DOCS` entry, `docs/policies.md`,
  with a comment in the style of the entries above it saying why a policy
  document is gated where a plan is not.
- `README.md`, "Documentation" section: one bullet linking
  `docs/policies.md` with a one-line description, in the shape of the
  bullets around it.
- `llms.txt`, "Optional" list: one line linking `docs/policies.md`, so the
  agent index names the policy an envelope consumer needs.
- `openspec/AGENTS.md`: one sentence after the four-trap list — a number in
  a package names the command that regenerates it — linking the policy's
  anchor through `../docs/policies.md`. Nothing else in the file changes.
- `docs/agents-skills-harness.md`: one short closing section whose single
  sentence says that how this repository is worked on — one agent per
  thread, counts that name their command, the version and deprecation
  window — is policy, written once in `policies.md`. No rule count is added
  or changed.
- `docs/AGENTS.md`: the existing first bullet gains the link to the count
  policy's anchor, and the diagram's label for the gated documents gains
  `policies.md`, so the picture of what `check_docs.py` gates stays true.
- `tests/test_policies_doc.py` (new): the guard. It asserts
  `docs/policies.md` is in `REQUIRED_DOCS` and is named in `README.md`;
  reads the index and the `##` headings from the document and asserts they
  agree in both directions; reads every link to `policies.md#<anchor>` in
  the agent-facing files and asserts each anchor is a heading; asserts each
  pointer file carries at least one such link; runs G004's `MAKE_REF` over
  the document against `detect.profile().make_targets`; and, on planted
  fixtures, asserts a dead anchor and an unindexed heading are each named.
  Every check collects its offenders before asserting. The test carries no
  list of expected headings.
- `CHANGELOG.md` `[Unreleased]`: an `Added` entry for this package. The
  `specgraph` line under `Deprecated` is `prepare-release-0-3-0`'s R-REL-6
  and is not written a second time here; the policy document names the
  window itself, so the two packages may land in either order.

## Non-Goals

- **No code behaviour change.** Nothing under `openspec_graph/` is edited:
  `_DEPRECATION_WARNING` keeps its text, `main_deprecated` its contract,
  every `*SCHEMA_VERSION` its value. Making the alias warning name 0.4.0,
  and writing the window into the CHANGELOG's `Deprecated` group, are
  `prepare-release-0-3-0`'s R-REL-7 and R-REL-6 on this same branch; this
  package states the rule those two edits are the first instance of, and
  does not duplicate either.
- **No release, no removal, no bump.** 0.3.0 is `prepare-release-0-3-0`
  (W1.5); nothing is removed and no schema integer moves. This package
  states the rules a removal or a bump will follow.
- **No mechanical guard for the one-agent convention.** A hook cannot see
  another agent's intent, and the setting that would make merges wait for
  checks is branch protection — a repository setting outside the tree (the
  plan's W8.7). The test holds that the convention is written and pointed
  at, not that it is obeyed.
- **No new rule, no new `make` target, no new gate script.** The `RULES`
  tuple, `README.md`'s rules table and `tests/baseline_rules.json` are
  untouched; `make docs-check` is already the gate for "exists and is
  linked", and the heading check is a test in the shape of
  `tests/test_rule_registry_docs.py` — the cheapest form once drift has
  recurred (DEC-AD-006), not a tool.
- **No restating of the operating contract.** Floors move up and never
  down, waivers are not written, `witness` is not run by hand: those are
  `skills/planlint-spec-governance/SKILL.md`'s and stay there. Disclosure
  is `SECURITY.md`'s. The gate ladder is `docs/hooks.md`'s. The policy
  document points at each and copies none.
- **No archive, no spec-status report, no `CODEOWNERS`, no retiring of
  plans.** W8.2, W8.4, W8.5 and W8.6 are their own items.
- **No edit to the plan's W5 sketch**, which removes symbols deprecated in
  0.3.0 at 0.4.0. Under the window this package writes, a surface first
  deprecated in 0.3.0 is removed no earlier than 0.5.0; DEC-POL-004 records
  the consequence so the W5 package meets it rather than discovers it.

## Affected Capabilities

- `project-policies`
