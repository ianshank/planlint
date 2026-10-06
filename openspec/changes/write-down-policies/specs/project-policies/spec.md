# Spec: Project Policies

> **Change:** `write-down-policies`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Three rules this repository works by are not written where a reader would
find them. The five machine-readable outputs each carry an integer
`schema_version`, and the only statement of when one moves is a comment
beside one declaration; what a bump means for a consumer — `report` exits 2,
`witness` skips the record — is implemented and nowhere stated as policy, and
nothing says in which kind of release a bump may land. The `specgraph` alias
has warned since 0.2.0 that it "will be removed" with no version named, while
`detect --json`, deprecated in the same release, names 1.0. A number written
into a change package goes stale on its own branch, and the rule that
prevents it — a count names the command that regenerates it — is stated in
`docs/AGENTS.md` for `docs/` and in no file that governs `openspec/`. Two
coding agents fixed one review thread at once on this branch, and no document
says who owns a thread.

A rule that is stated once, where readers look, and pointed at from the
places they start, is the cheapest guard this repository has; a rule each
reader reconstructs from precedent is one that gets reconstructed
differently. This spec names one document of record, fixes the wording of
each policy, keeps every pointer to one sentence so the nearest `AGENTS.md`
stays inside its budget, and holds the document's structure with a test that
reads the document rather than a copy of it.

**Evidence:** measured at `5fe043e`; each command is in the proposal.
`grep -rn "SCHEMA_VERSION\s*=" openspec_graph tools` finds five
declarations, all `= 1`, with the bump rule stated only at
`openspec_graph/rule_types.py:32–36`; `openspec_graph/report.py:257–260` and
`:301–304` refuse a mismatched version and
`skills/planlint-spec-governance/references/exit-codes.md:107` documents the
exit 2; `openspec_graph/witness.py:194–198` skips; `openspec_graph/sarif.py:28`
carries SARIF's own version and no planlint schema integer.
`openspec_graph/cli.py:1010–1013` names no removal version for `specgraph`;
`cli.py:80–84` names 1.0 for `detect --json`; `CHANGELOG.md` has no
`Deprecated` entry for the alias and one, for Python 3.10, under
`[Unreleased]` (`:45–52`); the sibling draft `prepare-release-0-3-0`
(R-REL-6, R-REL-7) specifies the CHANGELOG line and the warning text that
will name the window, and agrees with this spec on what it is.
`docs/AGENTS.md:3–5` states the count rule; `openspec/AGENTS.md` does not;
`.claude/agents/spec-adversary.md:20` checks it in review;
`add-witness-ci-artifacts`'s DEC-WCA-016 recorded six specs verifying with
`ci` and seven with `pre-pr`, and `make stage-citations` at `5fe043e` reads
7 and 9. `openspec/changes/harden-ci-workflows/tasks.md` Milestone 9 is the
in-tree trace of a second agent on PR #38; no file in `docs/` or `openspec/`
names a convention for it. `openspec/AGENTS.md` is 49 lines against the
budget `tests/test_agent_artifacts.py` declares as `MAX_NESTED_LINES`.
`tools/check_docs.py` `REQUIRED_DOCS` is the exists-and-linked gate, run by
`make docs-check`, with a fixture test that reads the list rather than
copying it.

---

## Requirements

- R-POL-1: `docs/policies.md` MUST exist and MUST be the single document of
  record for three policies: versioning and deprecation, the
  count-cites-a-command rule, and the one-agent-per-thread convention. Each
  policy MUST be a level-two section whose heading is plain words — letters,
  digits, spaces and hyphens only, so its anchor is the heading lowercased
  with spaces as hyphens — and the document MUST open with an index that
  lists every level-two section as a link to its anchor. No other file MAY
  restate a policy's text; other files point.
- R-POL-2: The versioning section MUST state that the package follows
  Semantic Versioning with `openspec_graph.__version__` as its one source;
  that while the major is 0 a minor release is the only release in which a
  surface may be removed or an output shape broken, and a patch release
  never removes or breaks; that every machine-readable output carries its
  own integer `schema_version`, declared beside the type whose serialization
  it describes and independent of the package version; that a bump of that
  integer is a breaking change for every consumer of that output — a saved
  envelope the next `report` refuses with exit 2, a witness record the next
  run skips — and therefore lands only in a release that may break (a minor
  while the major is 0, a major from 1.0), never in a patch, with a
  `CHANGELOG.md` entry naming the output, the old and new integer and the
  keys that changed; that an additive key never bumps it; that
  `tool_version` is informational and a mismatch is a warning, never a
  refusal; and that the SARIF projection has no planlint schema version
  because its shape is SARIF 2.1.0's, so a change to what planlint writes
  into SARIF follows the package rule, not a schema integer.
- R-POL-3: The deprecation section MUST state the window: a deprecation of
  a user-facing surface — a command or alias, a flag, an output shape, a
  public import — is announced under `Deprecated` in `CHANGELOG.md` in the
  release that first deprecates it, naming the removal version; the surface
  keeps working and warns on stderr only, with its exit code unchanged,
  through the whole of the next minor series; it is removed no earlier than
  the minor after that. A longer window MAY be named; an unnamed window MUST
  NOT be written. The section MUST state that dropping an interpreter follows
  upstream end-of-life with notice in the release notes one minor ahead and
  is not this window (the Python 3.10 entry and DEC-HCW-006 stand unchanged).
  It MUST name `specgraph` as the first instance — deprecated in 0.2.0, warns
  through 0.3.x, removed in 0.4.0, the window `prepare-release-0-3-0` R-REL-6
  writes into the CHANGELOG — and `detect --json` as a second, with its
  named 1.0 removal as an example of a longer window.
- R-POL-4: The count section MUST state that a number written into a spec,
  a decision, a plan or a document of record names the command that produced
  it — a `make` report target or the exact command line — so a reader
  re-runs it rather than trusts it; that a number which no command
  regenerates is written as a description of the set, not a count; that a
  measurement is dated with the commit it was taken at; and that the
  CHANGELOG is a dated record and exempt. It MUST name `make stage-citations`
  as the regenerator for every count of cited stages, and MUST say that
  `spec-adversary` re-measures every count a draft states.
- R-POL-5: The one-agent section MUST state that one session owns a
  pull-request thread — the session that opened it, or on a review thread
  whoever first replies with a commit; that a second agent answers only when
  addressed in the thread and otherwise waits for the owner's push before
  touching the same files; and that when two pushes race anyway the result
  is merged and never force-pushed.
- R-POL-6: `openspec/AGENTS.md` MUST carry one sentence, after its list of
  traps, saying a number in a package names the command that regenerates it
  and linking the count policy's anchor through `../docs/policies.md`;
  `docs/agents-skills-harness.md` MUST carry one short closing section whose
  single sentence points at `policies.md` for the working conventions;
  `docs/AGENTS.md`'s existing count bullet MUST link the same anchor.
  None of the three MAY restate a policy. `openspec/AGENTS.md` MUST stay
  within `MAX_NESTED_LINES`, keep its precedence clause and balanced mermaid
  fence, declare no `INV-n`, and every link in it MUST resolve from
  `openspec/`.
- R-POL-7: `docs/policies.md` MUST be listed in `tools/check_docs.py`
  `REQUIRED_DOCS`, MUST be named in `README.md`'s "Documentation" section as
  a bullet in the shape of its neighbours, and MUST be linked from
  `llms.txt`.
- R-POL-8: A new module `tests/test_policies_doc.py` MUST assert that
  `docs/policies.md` is in `REQUIRED_DOCS` and named in `README.md`; MUST
  read the index entries and the level-two headings from the document and
  assert they agree in both directions — every heading indexed, every index
  anchor a heading; MUST read every link whose path resolves to
  `docs/policies.md` and carries a fragment, from `openspec/AGENTS.md`,
  `docs/AGENTS.md`, `docs/agents-skills-harness.md`, `llms.txt` and
  `README.md`, and assert each fragment is a heading's anchor; MUST assert
  that each of the three pointer files carries at least one such link; MUST
  run `parse_semantics.MAKE_REF` over the document and assert every cited
  stage is in `detect.profile(REPO_ROOT).make_targets`; MUST, on planted
  fixtures, show that a dead index anchor and an unindexed heading are each
  reported by name; and MUST collect every offender before asserting. The
  module MUST NOT carry a list of expected headings or anchors.
- R-POL-9: `CHANGELOG.md`'s `[Unreleased]` section MUST carry an `Added`
  entry for this package. This package MUST NOT write a `specgraph` line
  under `Deprecated`: that line is `prepare-release-0-3-0`'s (R-REL-6), the
  window it states and the one `docs/policies.md` states MUST be the same,
  and the two packages MUST be landable in either order.
- C-POL-1: No file under `openspec_graph/` MAY change. `_DEPRECATION_WARNING`
  and `main_deprecated` keep their text and contract; every `*SCHEMA_VERSION`
  keeps its value; the `RULES` tuple, `README.md`'s rules table and
  `tests/baseline_rules.json` are untouched; the `Makefile` is unedited and
  no target is added. `tools/check_docs.py` changes by one `REQUIRED_DOCS`
  entry and its comment and nothing else.
- C-POL-2: This spec's requirements and criteria MUST NOT pin a count that
  another package changes — a spec count, a stage count, a line budget's
  value, a test count. A measurement belongs in the proposal and in
  `tasks.md`, dated with its commit and naming its command: the policy,
  applied to the package that writes it.
- C-POL-3: The edit to `docs/agents-skills-harness.md` MUST NOT add a
  rule-count phrase and MUST NOT alter the one already there;
  `tests/test_rule_registry_docs.py` reads that file for it.
- C-POL-4: Every backticked `make` citation in `docs/policies.md`, in the
  three pointer files and in `llms.txt` MUST name a target the `Makefile`
  declares.

---

## Decisions

- **DEC-POL-001:** one new document, `docs/policies.md`, rather than
  sections inside `docs/agents-skills-harness.md`. That document is about
  what the tool *is* — its opening paragraph exists to separate three
  meanings of "skill" and its subject is the product architecture — and a
  reader asking "when does `schema_version` bump" or "who owns this review
  thread" would not open a file so titled. It is also already long and
  carries a rule-count sentence a test guards, so growing it by three
  policies makes a wrong-subject file harder to keep true. A document named
  for what it holds gets its own README bullet, its own `REQUIRED_DOCS`
  entry and its own `llms.txt` line, which is how a human and an agent each
  find it from where they start. Rejected: the root `AGENTS.md`, which its
  own text calls "a pointer, not a second skill"; `openspec/AGENTS.md`,
  which the nearest-file-wins convention shows only to readers inside
  `openspec/` and which has a line budget; and splitting the three across
  the files the plan named, which is three places for a reader to look and
  the drift R2 describes, one level up.
- **DEC-POL-002:** every pointer is one sentence carrying a link, and none
  restates the policy. `openspec/AGENTS.md` sits inside `MAX_NESTED_LINES`
  with little room, and the budget exists because an agent that does not
  finish a nested file is worse off than one that read the root pointer; a
  paragraph of policy there would spend the room and still be a second copy.
  The sentence goes after the four-trap list as its own paragraph — the
  list's heading says "four", and a fifth bullet would make it wrong — and
  links `../docs/policies.md#<anchor>` because `test_agent_index_links_resolve`
  resolves against the containing directory, which is also what a reader's
  renderer does. `docs/agents-skills-harness.md` gets a short closing section
  rather than a sentence buried in "Per-directory guidance", so a reader
  scanning headings finds it; its one sentence names the three conventions
  and the file, nothing more. `docs/AGENTS.md` already states the count rule
  for its own directory and keeps that sentence as the local reminder, gaining
  only the link; two statements with no link between them would be exactly
  two copies. The wrapped width of a sentence is formatting; "one sentence"
  is the rule, and the line budget is what the test measures.
- **DEC-POL-003:** the versioning text. The package already declares
  Semantic Versioning (`CHANGELOG.md:4`) and a single `__version__`
  (DEC-SD-009); what is missing is the pre-1.0 reading and the schema rule.
  While the major is 0, SemVer permits a minor to break, and this
  repository's practice makes the minor the *only* release that may: a patch
  is a fix and never removes anything. Each `schema_version` is an integer
  declared beside the type it describes — the pattern `rule_types.py`,
  `dialect_card.py`, `witness.py`, `delta.py` and `tools/stage_citations.py`
  already follow — and is independent of the package version, because
  DEC-FE-010 already rejected tying them: a bump on every release would make
  every consumer re-pin for nothing. A bump is defined by its effect on a
  consumer, not by the size of the diff: `report` refuses the old envelope
  with exit 2 and `witness` skips the old record, so a bump breaks every
  consumer of that output and may land only where the package rule allows a
  break — a minor while the major is 0, a major from 1.0 — never a patch,
  and always with a CHANGELOG entry naming the output, old and new integer,
  and the keys that changed. Additive keys never bump, as `rule_types.py`'s
  comment says and the `line` precedent (`CHANGELOG.md:423`) shows. One
  integer per output rather than one shared integer, because a change to
  the witness record must not force every envelope consumer to re-pin.
  `tool_version` stays informational — a mismatch warns and projects
  (`exit-codes.md:111–112`) — and the SARIF projection has no planlint
  integer: its shape is SARIF 2.1.0's (`sarif.py:28`), its `driver.version`
  is the tool version, and a change to what planlint writes into it follows
  the package rule. Rejected: one shared schema integer; a schema integer
  on the SARIF output, which would version a standard this tool does not own.
- **DEC-POL-004:** the deprecation window, as the plan's W1.5 states it for
  `specgraph` and generalised: announced under `Deprecated` in the release
  that first deprecates the surface, naming the removal version; the surface
  keeps working and warns on stderr only with its exit code unchanged —
  `main_deprecated`'s contract, pinned by the three alias tests — through
  the whole next minor series; removed no earlier than the minor after
  that. Announced in 0.Y, warning through 0.(Y+1).x, removed in 0.(Y+2).0.
  `specgraph` is the first instance and fits exactly: deprecated in 0.2.0,
  warns through 0.3.x, removed in 0.4.0. `detect --json` is the second and
  shows the other permitted shape: a longer window, named (1.0). What the
  policy forbids is the shape `specgraph` has today — "will be removed"
  with no version. The two edits that close that shape on the record — the
  CHANGELOG `Deprecated` line and a warning string that names 0.4.0 — are
  `prepare-release-0-3-0`'s R-REL-6 and R-REL-7 on this branch, drafted
  concurrently and stating the same window; this package names the window
  in the policy and does not write either edit a second time, so neither
  package depends on the other's landing order. Interpreter support is
  carved out explicitly: dropping Python 3.10 is announced in the 0.3.0
  notes and lands in 0.4.0 (R-HCW-12, DEC-HCW-006), one minor of notice
  rather than two, because an interpreter is not a surface this tool can
  warn from and the clock is upstream's end-of-life; writing the general
  window without this carve-out would contradict a sibling package's
  recorded decision on the same branch. One consequence is recorded rather
  than discovered: the plan's W5.1 and W5.2 sketch deprecating
  `Criterion.has_selector` and the section-reader names in 0.3.0 and
  removing them in 0.4.0; under this window a surface first deprecated in
  0.3.0 is removed no earlier than 0.5.0, and the W5 package follows the
  policy or amends it with a reason, by name. Rejected: a window counted in
  time rather than releases, which this repository cannot measure from the
  tree; a window of one minor, which the task of writing the first instance
  down showed is shorter than what `specgraph` already has.
- **DEC-POL-005:** the count rule's text. A number written into a spec, a
  decision, a plan or a document of record names the command that produced
  it — a `make` report target such as `make stage-citations`, or the exact
  command line — so a reader re-runs it rather than trusts it; a number no
  command regenerates is written as a description of the set ("every
  package present when this lands"), not as a count; a measurement is dated
  with the commit it was taken at; the CHANGELOG is a dated record and is
  exempt, for the reason `tests/test_rule_registry_docs.py`'s docstring
  already gives for rule counts. The rule exists because the alternative has
  failed in the tree twice — DEC-WCA-016's counts moved before the branch
  merged, and the E501 count was taken three times without the work being
  done — and because `spec-adversary` already re-measures every count
  (checklist item 8), so the rule is enforced in review and stated for the
  wrong directory. It is stated once in `docs/policies.md`; `docs/AGENTS.md`
  keeps its local sentence and links; `openspec/AGENTS.md` gains the
  sentence the plan's R2 asked for, as a pointer. Rejected: a matcher that
  flags bare numbers in specs — G003's own docstring records why widening a
  prose scan to running text reintroduces the false-positive class
  `fix-prose-matcher-precision` was spent lowering, and a dated measurement
  is legitimate prose a matcher cannot tell from a stale count.
- **DEC-POL-006:** the one-agent convention's text. One session owns a
  pull-request thread: the session that opened it, or on a review thread
  whoever first replies with a commit. A second agent — another Claude
  session, Copilot's coding agent, a bot a human drives — answers only when
  addressed in the thread, and otherwise waits for the owner's push before
  touching the same files. When two pushes race anyway, the result is merged
  and never force-pushed, which is the habit the plan's R6 says to keep. The
  convention is written because the race in R3 cost a merge commit, a re-run
  of a coverage leg and about fifteen minutes, and because nothing in
  `docs/` or `openspec/` says who owns a thread. It lives in
  `docs/policies.md` with a pointer from `docs/agents-skills-harness.md`
  rather than as that file's own sentence (the plan's R3 wording), by
  DEC-POL-001. It is a convention and not a guard: a hook cannot see another
  agent's intent, a `CODEOWNERS` file names reviewers and not sessions
  (W8.4), and the mechanism that makes a merge wait is branch protection,
  outside the tree (W8.7); the test holds only that the convention is written
  and pointed at.
- **DEC-POL-007:** the guard is a new module, `tests/test_policies_doc.py`,
  and it reads the document instead of a copy of it. The one place the set
  of policies is written is `docs/policies.md`; the index at its top is the
  document's own table of contents, so "every heading is indexed and every
  index anchor resolves" is a property between two parts of one file, and
  adding a policy is one heading plus one index bullet with no test edit.
  The pointers in the agent-facing files are the other side: each link to
  `policies.md#<anchor>` must land on a heading, and each pointer file must
  carry at least one, so a pointer cannot quietly vanish or dangle. Anchors
  are GitHub's — lowercase, spaces to hyphens, other punctuation dropped —
  which is why R-POL-1 confines headings to plain words: the helper stays
  three lines and cannot disagree with the renderer on a heading that has
  no punctuation to disagree about. The module also runs `MAKE_REF` over the
  document against `detect.profile().make_targets`, the same pairing
  `test_every_make_citation_in_an_agent_index_names_a_real_target` uses,
  because a policy document that says "run `make <x>`" for a target that
  does not exist is the defect this tool reports in a stranger's spec. The
  planted-fixture tests exist because a structural check that has never
  failed is a decoration: each plants a document with one defect and asserts
  the failure names the anchor or heading. A new module rather than a
  section of `tests/test_agent_artifacts.py`, which already holds the
  nested-AGENTS contracts, the eval checks, the release workflow and the
  Docker surface; the same locality argument as DEC-HCW-008. Rejected: a
  list of expected headings in the test, which is the second copy
  `tests/test_rule_registry_docs.py` exists to prevent; reading the set from
  `tools/check_docs.py`, which lists paths and is a gate script this package
  touches by one entry only.
- **DEC-POL-008:** `docs/policies.md` is registered in `REQUIRED_DOCS`.
  `docs/AGENTS.md` leaves a `*-plan.md` ungated because it is consumed and
  retired; a policy document is the opposite — permanent, and a front-page
  promise — and `test_every_root_markdown_file_is_wired_into_the_docs_gate`
  is root-scoped on purpose, so nothing would require the registration if
  this package did not. The cost is one list entry with a comment, and
  `tests/test_gate_scripts.py` builds its fixture from the list, so no test
  changes; `test_docs_check_passes` then proves present-and-linked on the
  real tree, which is why the new module asserts membership in the list and
  the README mention rather than re-implementing the check.
- **DEC-POL-009:** the CHANGELOG gets this package's `Added` entry and
  nothing about `specgraph`. The first draft of this spec wrote the window
  into the `Deprecated` group here, on the argument that the policy's first
  instance should not stay unnamed in the tree that writes the policy; the
  sibling draft `prepare-release-0-3-0` (R-REL-6, R-REL-7, DEC-REL-005)
  already owns exactly that line and the warning string, with the same
  window, and two packages on one branch writing one CHANGELOG line is a
  duplicate entry or a conflict at merge. So the record of the window is the
  release package's, the rule it instantiates is this one's, and the policy
  document names the window itself so a reader of either finds the same
  numbers whichever lands first. `tasks.md` carries the cross-check: when
  the second of the two lands, its author re-reads the other's line.
- **DEC-POL-010:** the document says what it does not hold. The operating
  contract — floors move up and never down, no agent-written waivers, no
  hand-run `witness` — is `SKILL.md`'s and outranks every `AGENTS.md`;
  disclosure is `SECURITY.md`'s; the gate ladder is `docs/hooks.md`'s. One
  closing sentence points at each. Copying any of them would make a second
  place for a rule that already has one, which is the condition the
  nested-AGENTS convention and this package both exist to end.

---

## Acceptance Criteria

- [ ] **AC-POL-1:** `docs/policies.md` exists, opens with an index, carries
  the three policy sections with plain-word headings and the wording
  DEC-POL-003 through DEC-POL-006 decide, is listed in
  `tools/check_docs.py` `REQUIRED_DOCS`, is named in `README.md`'s
  "Documentation" section and linked from `llms.txt`, and the docs gate
  passes on the real tree. (R-POL-1, R-POL-2, R-POL-3, R-POL-4, R-POL-5,
  R-POL-7, DEC-POL-001, DEC-POL-008)
  _Verified by:_ `pytest -k test_docs_check_passes` · stage: `make docs-check`

- [ ] **AC-POL-2 (non-success):** with `docs/policies.md` in the required
  set, a tree where it is missing, or present but not named in `README.md`,
  fails the docs gate with a message naming the document — the fixture is
  built from `REQUIRED_DOCS` itself, so the new entry is inside the
  property without a test edit. (R-POL-7, DEC-POL-008)
  _Verified by:_ `pytest -k "test_docs_check_reports_a_missing_doc or test_docs_check_reports_a_present_but_unlinked_doc"` · stage: `make test`

- [ ] **AC-POL-3:** every level-two heading in `docs/policies.md` has an
  index entry and every index anchor is a heading; every link to
  `policies.md#<anchor>` in `openspec/AGENTS.md`, `docs/AGENTS.md`,
  `docs/agents-skills-harness.md`, `llms.txt` and `README.md` lands on a
  heading; and each of the three pointer files carries at least one such
  link. (R-POL-1, R-POL-6, R-POL-8, DEC-POL-002, DEC-POL-007)
  _Verified by:_ stage: `make test`

- [ ] **AC-POL-4 (non-success):** a planted document whose index names an
  anchor with no heading fails naming the anchor; a planted document with a
  heading no index entry names fails naming the heading; a planted pointer
  whose fragment is not a heading fails naming the file and fragment.
  (R-POL-8, DEC-POL-007)
  _Verified by:_ stage: `make test`

- [ ] **AC-POL-5:** after its one-sentence pointer, `openspec/AGENTS.md` is
  within `MAX_NESTED_LINES`, still states its precedence, still carries a
  balanced mermaid fence, declares no `INV-n`, and every link in it — the
  new `../docs/policies.md` one included — resolves from `openspec/`; the
  same link check holds for `docs/AGENTS.md` and `llms.txt`. (R-POL-6,
  R-POL-7, DEC-POL-002)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_nested_agents_file_has_a_balanced_mermaid_block or test_nested_agents_file_declares_no_invariant_ids or test_agent_index_links_resolve"` · stage: `make test`

- [ ] **AC-POL-6:** every backticked `make` citation in the agent indexes
  (`openspec/AGENTS.md`, `docs/AGENTS.md`, `llms.txt`) names a target this
  repository declares, through G004's own matcher; the same check over
  `docs/policies.md` is the new module's. (C-POL-4, R-POL-4, R-POL-8,
  DEC-POL-007)
  _Verified by:_ `pytest -k test_every_make_citation_in_an_agent_index_names_a_real_target` · stage: `make test`

- [ ] **AC-POL-7:** the `specgraph` alias behaves exactly as before — warns
  to stderr, delegates, preserves a failing exit code, keeps stdout
  parseable — and `openspec_graph/cli.py` is absent from this package's
  diff. (C-POL-1, R-POL-3, DEC-POL-004)
  _Verified by:_ `pytest -k "test_deprecated_alias_warns_to_stderr_and_delegates or test_deprecated_alias_preserves_failure_exit_code or test_deprecated_alias_keeps_stdout_parseable"` · stage: `make test`

- [ ] **AC-POL-8:** the rule inventory is unchanged — the live rule table
  still matches `tests/baseline_rules.json`. (C-POL-1)
  _Verified by:_ `pytest -k test_rule_set_matches_baseline` · stage: `make test`

- [ ] **AC-POL-9:** `docs/agents-skills-harness.md`'s existing rule-count
  sentence still matches the registry and no second rule-count phrase was
  added by the new section. (C-POL-3, R-POL-6)
  _Verified by:_ `pytest -k test_total_rule_count_matches_every_prose_claim` · stage: `make test`

- [ ] **AC-POL-10:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `Added` entry and no `specgraph` line written by this package; the window
  `docs/policies.md` states — warns through 0.3.x, removed in 0.4.0 — is
  the one `prepare-release-0-3-0` R-REL-6 writes, read directly against
  that package's spec or, once it has landed, its CHANGELOG line; and every
  versioned section still links to its release tag. (R-POL-9, DEC-POL-009)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag`, plus the entry and the window read directly · stage: `make test`

- [ ] **AC-POL-11:** the consumer behaviour the versioning section describes
  is the behaviour the tree has — a dialect card whose `schema_version`
  changed is reported as its own kind of change, and a witness record with an
  unrecognized `schema_version` is skipped rather than read. (R-POL-2,
  DEC-POL-003)
  _Verified by:_ `pytest -k "test_diff_cards_reports_schema_version_changes_distinctly or test_load_witnesses_skips_a_file_with_an_unrecognized_schema_version"` · stage: `make test`

- [ ] **AC-POL-12:** this spec's requirements and criteria pin no count
  another package changes, and every measurement in the proposal and in
  `tasks.md` is dated with its commit and names its command — a review
  property, read directly; the gate confirms the package validates clean
  against the repository's own rules. (C-POL-2, DEC-POL-005)
  _Verified by:_ stage: `make validate`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Docs gate | `make docs-check` | AC-POL-1 — the document is present and named in the README on the real tree |
| Focused | `make test` | AC-POL-2..11 — the new module green on the real tree and red on its planted fixtures; every existing guard this change leans on still green |
| Self-check | `make validate` | AC-POL-12 — this package validates clean against the repo's own rules, then the whole tree |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
