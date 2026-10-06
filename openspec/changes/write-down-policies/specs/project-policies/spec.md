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
`openspec_graph/rule_types.py:32–36` — a comment that also counts "all three
machine-readable outputs"; `openspec_graph/report.py:257–261` and
`:301–305` refuse a mismatched version with exit 2, emitting "findings
schema_version <got> is not the <n> this build reads; regenerate the
envelope with this version of planlint", which is not the message
`skills/planlint-spec-governance/references/exit-codes.md:107` quotes;
`openspec_graph/witness.py:194–198` skips; `openspec_graph/sarif.py:28`
carries SARIF's own version and no planlint schema integer.
`openspec_graph/cli.py:1010–1013` names no removal version for `specgraph`;
`cli.py:80–84` names 1.0 for `detect --json`; the 0.2.0 section of
`CHANGELOG.md` has no `Deprecated` group and files the rename under
`Changed` (`:1381`), and the file's one `Deprecated` entry, for Python 3.10,
is under `[Unreleased]` (`:45–52`). The sibling draft
`prepare-release-0-3-0` specifies the warning text that will name the window
(R-REL-7) and asks that the `[0.3.0]` notes state it (R-REL-6); it lands
after this package and moves the `[Unreleased]` body under `[0.3.0]`.
`docs/AGENTS.md:3–5` states the count rule; `openspec/AGENTS.md` does not;
`.claude/agents/spec-adversary.md:20` checks it in review;
`add-witness-ci-artifacts`'s DEC-WCA-016 recorded six specs verifying with
`ci` and seven with `pre-pr`, and `make stage-citations` at `5fe043e` reads
7 and 9. `openspec/changes/harden-ci-workflows/tasks.md` Milestone 9 is the
in-tree trace of a second agent on PR #38; no file in `docs/` or `openspec/`
names a convention for it. `openspec/AGENTS.md` is 49 lines against the
budget `tests/test_agent_artifacts.py` declares as `MAX_NESTED_LINES`, and
no test holds a markdown line width. `tools/check_docs.py` `REQUIRED_DOCS`
is the exists-and-linked gate, run by `make docs-check`, with a fixture test
that reads the list rather than copying it; nothing ties `llms.txt` to that
list.

---

## Requirements

- R-POL-1: `docs/policies.md` MUST exist and MUST be the single document of
  record for three policies: versioning and deprecation, the
  count-cites-a-command rule, and the one-agent-per-thread convention. Each
  policy MUST be a level-two section whose heading is plain words — letters,
  digits, spaces and hyphens only, so its anchor is the heading lowercased
  with spaces as hyphens — and the document MUST open with an index that
  lists every level-two section as a link to its anchor. No other file is
  the document of record for a policy. A file MAY carry a one-line local
  reminder of a policy; the reminder MUST link the policy's anchor and MUST
  NOT state a detail the document does not. A statement of a policy's
  instance — a particular deprecation's window where its audience reads it,
  a particular measurement with its command — is not a restatement and is
  what the policies themselves require.
- R-POL-2: The versioning section MUST state that the package follows
  Semantic Versioning with `openspec_graph.__version__` as its one source;
  that while the major is 0 a minor release is the only release in which a
  surface may be removed or an output shape broken, and a patch release
  never removes or breaks; that every machine-readable output a consumer
  keeps — the five versioned envelopes, not the read-only listings — carries
  its own integer `schema_version`, declared beside the type whose serialization
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
  into SARIF follows the package rule, not a schema integer. The section
  MUST state the refusal as its exit code and MUST NOT quote the refusal
  message.
- R-POL-3: The deprecation section MUST state the window as a minimum: a
  deprecation of a user-facing surface — a command or alias, a flag, an
  output shape, a public import, an interpreter version — is announced under
  `Deprecated` in the notes of a minor release 0.Y.0, naming the removal
  version; the surface keeps working through the whole 0.Y.x series, and
  where it is something the tool runs it warns on stderr with its exit code
  unchanged; it is removable from 0.(Y+1).0. A longer window MAY be named;
  an unnamed window MUST NOT be written. The section MUST name three
  instances: `specgraph` — a bare "will be removed" warning since 0.2.0,
  whose notes had no `Deprecated` group and filed the rename under
  `Changed`; announced with its removal version in the 0.3.0 release notes;
  warns through 0.3.x; removed in 0.4.0 — which exceeds the minimum, having
  warned for two minor series; `detect --json` — deprecated in 0.2.0,
  removal named as 1.0 — which also exceeds it; and Python 3.10 — announced
  in the 0.3.0 notes, nothing changes through 0.3.x, dropped in 0.4.0 —
  which meets it exactly (the entry and DEC-HCW-006 stand unchanged). The
  `specgraph` instance MUST be phrased as the window the 0.3.0 release notes
  state, not as a citation of another package's requirement.
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
  and linking the count policy's anchor through `../docs/policies.md`, with
  the link on its own line; `docs/agents-skills-harness.md` MUST carry one
  short closing section whose single sentence points at `policies.md` for
  the working conventions; `docs/AGENTS.md`'s existing count bullet MUST
  link the same anchor. Each of the three is a local reminder under R-POL-1:
  it links the anchor and states no detail the document does not.
  `openspec/AGENTS.md` MUST stay within `MAX_NESTED_LINES`, keep its
  precedence clause and balanced mermaid fence, declare no `INV-n`, and
  every link in it MUST resolve from `openspec/`.
- R-POL-7: `docs/policies.md` MUST be listed in `tools/check_docs.py`
  `REQUIRED_DOCS`, MUST be named in `README.md`'s "Documentation" section as
  a bullet in the shape of its neighbours, and MUST be linked from
  `llms.txt`. The `llms.txt` clause is held by the new test module
  (R-POL-8), because the docs gate reads `README.md` only.
- R-POL-8: A new module `tests/test_policies_doc.py` MUST assert that
  `docs/policies.md` is in `REQUIRED_DOCS`, that the literal
  `docs/policies.md` appears in `README.md`, and that the same literal
  appears in `llms.txt`. It MUST read the level-two headings from the
  document from `## ` lines outside fenced code blocks only, and the index
  anchors from the bullets before the first level-two heading, and MUST
  assert each list is non-empty before comparing them; MUST assert every
  heading matches `^[A-Za-z0-9 -]+$` and that no heading repeats; and MUST
  assert the two lists agree in both directions — every heading indexed,
  every index anchor a heading. It MUST read every markdown link whose path
  names `policies.md` and carries a fragment, from `openspec/AGENTS.md`,
  `docs/AGENTS.md`, `docs/agents-skills-harness.md`, `llms.txt` and
  `README.md`, assert each fragment is a heading's anchor, assert each
  link's path resolves from its file's directory to `docs/policies.md`, and
  assert that each of the three pointer files carries at least one such
  link. It MUST run `parse_semantics.MAKE_REF` over the document and assert
  every cited stage is in `detect.profile(REPO_ROOT).make_targets`, after
  asserting that set is non-empty. The offender collection MUST live in two
  named functions that the real-tree tests and the planted tests both call:
  `_index_offenders(text) -> list[str]`, which reports an empty heading
  list, an empty index, each heading outside the plain-word form, each
  repeated heading, each index anchor with no heading and each heading with
  no index entry, every one by name; and
  `_pointer_offenders(pointer_text, policies_text) -> list[str]`, which
  reports each fragment in a `policies.md` link that is not a heading's
  anchor, by name. Every test MUST collect every offender before asserting,
  with the offenders joined into the message. On planted texts the module
  MUST show that a dead index anchor, an unindexed heading, a dangling
  pointer fragment and a document with no heading or no index are each
  reported rather than passed. The module MUST NOT carry a list of expected
  headings or anchors.
- R-POL-9: The three M1 packages land in the order `pin-actions-by-sha`,
  then this package, then `prepare-release-0-3-0`, which moves the
  `[Unreleased]` body under `[0.3.0]` and lands last. `CHANGELOG.md`'s
  `[Unreleased]` section MUST carry this package's `Added` entry and, under
  `Deprecated`, the `specgraph` line — the alias warns through 0.3.x and is
  removed in 0.4.0 — written once, by this package, so that the cut carries
  both into the 0.3.0 notes; if this package lands after the cut and before
  the tag, both lines go under `[0.3.0]` instead. The window the line states
  and the one `docs/policies.md` states MUST be the same. The warning string
  that names the version is `prepare-release-0-3-0`'s R-REL-7 and this
  package MUST NOT edit it.
- C-POL-1: No file under `openspec_graph/` or `skills/` MAY change.
  `_DEPRECATION_WARNING` and `main_deprecated` keep their text and contract;
  every `*SCHEMA_VERSION` keeps its value; the `RULES` tuple, `README.md`'s
  rules table and `tests/baseline_rules.json` are untouched; the `Makefile`
  is unedited and no target is added. `tools/check_docs.py` changes by one
  `REQUIRED_DOCS` entry and its comment and nothing else.
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
- **DEC-POL-002:** every pointer is one sentence carrying a link, and the
  rule it obeys is "document of record", not "no restatement". The first
  draft said no other file may restate a policy's text; review showed that
  reading would outlaw `docs/AGENTS.md`'s existing count sentence, the
  README's alias paragraph and the `[project.scripts]` comment — three
  things the policies themselves want in place. The rule is now R-POL-1's:
  one document of record; a local reminder is allowed if it links the
  anchor and adds no detail the document lacks; a statement of an instance
  where its audience reads it is not a restatement. Under that rule
  `openspec_graph/rule_types.py:32–36` is a reminder that links nothing and
  carries a stale detail ("all three machine-readable outputs"); C-POL-1
  closes that file to this package, so `tasks.md` records it as a follow-up
  rather than fixing it. `openspec/AGENTS.md` sits inside `MAX_NESTED_LINES`
  with little room, and the budget exists because an agent that does not
  finish a nested file is worse off than one that read the root pointer; a
  paragraph of policy there would spend the room and still be a second copy.
  The sentence goes after the four-trap list as its own paragraph — the
  list's heading says "four", and a fifth bullet would make it wrong — and
  links `../docs/policies.md#<anchor>` because `test_agent_index_links_resolve`
  resolves against the containing directory, which is also what a reader's
  renderer does. The link sits on its own line: a markdown link wrapped
  across two lines breaks, no test holds a line width, and the file stays
  within the budget with the extra line (`tasks.md` names the simulated
  count and its command). `docs/agents-skills-harness.md` gets a short
  closing section rather than a sentence buried in "Per-directory guidance",
  so a reader scanning headings finds it; its one sentence names the three
  conventions and the file, nothing more. `docs/AGENTS.md` already states
  the count rule for its own directory and keeps that sentence as the local
  reminder, gaining only the link; two statements with no link between them
  would be exactly two copies.
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
  Amended after review (Copilot on PR #39): the rule is scoped to the
  outputs a consumer keeps — the five envelopes named — because `rules
  --json`, `graph --format json`, `waivers --format json` and the
  deprecated `detect --json` emit JSON with no planlint integer, as
  projections of the tree at the moment of the call; the document says so
  and files their shape under the package rule, so the claim matches the
  CLI. The same review found "nothing restates it" false of the version —
  SKILL.md's three fields and the generated manifests are copies held
  equal by tests and `make skill-manifests` — and the document now says
  that instead.

- **DEC-POL-004:** the deprecation window is a minimum of one minor series,
  as the plan's W1.5 and W5 both assume and as `prepare-release-0-3-0`'s
  DEC-REL-005 states it — "a full minor version is the notice". Announced
  under `Deprecated` in the notes of 0.Y.0 naming the removal version; the
  surface keeps working, and where the tool runs it, warns on stderr with
  the exit code unchanged — `main_deprecated`'s contract, pinned by the
  three alias tests — through the whole 0.Y.x series; removable from
  0.(Y+1).0. A longer window may be named; an unnamed one may not be
  written, because that is the shape `specgraph` has today and the shape
  this policy exists to end. The first draft wrote a two-minor window
  (announced in 0.Y, warning through 0.(Y+1).x, removed in 0.(Y+2).0) and
  rejected the one-minor window as "shorter than what `specgraph` already
  has"; that mistook a minimum for a target. `specgraph` has warned since
  0.2.0 because nobody wrote its removal version down, not because a
  two-series window was chosen, and a policy that takes the accident as its
  floor would have forced the plan's W5.1 and W5.2 — deprecate in 0.3.0,
  remove in 0.4.0 — to be amended for no reason the tree records. The
  two-minor window also needed an interpreter carve-out to avoid
  contradicting the Python 3.10 entry; under the one-minor minimum that
  entry — announced in the 0.3.0 notes naming 0.4.0, nothing changes
  through 0.3.x — fits as written, and the carve-out is deleted. An
  interpreter has no warning to print, so the window's substance for it is
  the named version and the full series of notice. Three instances are
  named honestly: `specgraph` first warned in 0.2.0 with a bare "will be
  removed" — the 0.2.0 notes have no `Deprecated` group and file the rename
  under `Changed` — is announced with its version in the 0.3.0 notes, warns
  through 0.3.x and goes in 0.4.0, which exceeds the minimum; `detect --json`
  was deprecated in 0.2.0 with its removal named as 1.0, which also exceeds
  it; Python 3.10 meets it exactly. The policy phrases the `specgraph`
  window as what the 0.3.0 release notes state, not as a citation of
  R-REL-6, because a reader of `docs/policies.md` has the CHANGELOG and not
  a change package in front of them. Rejected: a window counted in time
  rather than releases, which this repository cannot measure from the tree;
  the two-minor floor, for the reason above.
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
  Review found three ways that property could pass on nothing. A document
  with no level-two heading and no index agrees with itself in both
  directions, so each list is asserted non-empty first — a floor of one,
  which C-POL-2 permits because it is not a count another package moves.
  The anchor helper — lowercase, spaces to hyphens — agrees with GitHub's
  renderer only on headings with nothing else in them, so every heading is
  asserted against `^[A-Za-z0-9 -]+$` and asserted unique; with that
  assertion in place the three-line helper is correct by construction
  rather than by hope, and a duplicate heading cannot make two anchors
  collide into one. And a `## ` line inside a fenced code block — the
  document will show CHANGELOG headings as examples — is not a heading, so
  the reader skips fences. The pointers in the agent-facing files are the
  other side: each link to `policies.md#<anchor>` must land on a heading,
  each link's path must resolve from its own directory to the document, and
  each pointer file must carry at least one, so a pointer cannot quietly
  vanish or dangle. The offender collection lives in two named functions,
  `_index_offenders(text)` and `_pointer_offenders(pointer_text,
  policies_text)`, each returning a list of strings — the shape
  `tools/check_docs.py`'s `check(root)` has, and for the same reason: the
  real-tree test calls them on the tree and the planted tests call them on
  a text with one defect, so the planted tests exercise the collection and
  the message the real test would print, not a parallel implementation.
  The module also runs `MAKE_REF` over the document against
  `detect.profile().make_targets`, the same pairing
  `test_every_make_citation_in_an_agent_index_names_a_real_target` uses,
  because a policy document that says "run `make <x>`" for a target that
  does not exist is the defect this tool reports in a stranger's spec. The
  module also holds the `llms.txt` link — the literal `docs/policies.md` in
  that file, the same shape as its `README.md` assertion — because
  `check_docs.py` reads the README only and nothing else ties `llms.txt` to
  `REQUIRED_DOCS`. The planted-fixture tests exist because a structural
  check that has never failed is a decoration: each plants a text with one
  defect and asserts the failure names the anchor, heading or fragment, and
  one plants an empty document and asserts the floor fires. A new module
  rather than a section of `tests/test_agent_artifacts.py`, which already
  holds the nested-AGENTS contracts, the eval checks, the release workflow
  and the Docker surface; the same locality argument as DEC-HCW-008.
  Rejected: a list of expected headings in the test, which is the second
  copy `tests/test_rule_registry_docs.py` exists to prevent; reading the set
  from `tools/check_docs.py`, which lists paths and is a gate script this
  package touches by one entry only; a slug helper that handles punctuation,
  which would be a second renderer to keep in agreement with the first.
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
- **DEC-POL-009:** the landing order is named and the CHANGELOG lines follow
  it. The first draft wrote the `specgraph` window into the `Deprecated`
  group here; the second removed it in favour of `prepare-release-0-3-0`'s
  R-REL-6 and said the two packages could land in either order. Review
  showed that "either order" was false: the release package moves every
  line under `[Unreleased]` into `[0.3.0]` verbatim, so a package landing
  after that cut would file its entry under an `[Unreleased]` that means
  "after 0.3.0" while its work ships in 0.3.0, and a line both packages
  wrote would be a duplicate or a merge conflict in a section one of them
  had just moved. The order is `pin-actions-by-sha`, then this package,
  then the release package, which lands last because the cut is the last
  edit before the tag. Given that order, the package that lands first
  writes the line: this package puts its `Added` entry and the `specgraph`
  `Deprecated` line under `[Unreleased]`, the cut carries both into the
  0.3.0 notes, and R-REL-6 — the `[0.3.0]` group states the window — is met
  by the move rather than by a second line; the release package's proposal
  now records exactly this and keeps a fallback for the case where this
  package has not landed. If this package must land after the cut and
  before the tag, both lines go under `[0.3.0]` directly. The warning
  string stays the release package's (R-REL-7): C-POL-1 closes
  `openspec_graph/` to this package. That leaves a gap between the two
  landings in which the CHANGELOG names 0.4.0 and the alias warning on
  stderr still does not; it is acceptable because both packages land in one
  stack on one branch, the policy document describes the release, not the
  commit, and the alternative — editing `cli.py` here — would put one line
  of code behaviour into a docs package. `tasks.md` carries the cross-check
  the release package's author runs when it lands.
- **DEC-POL-010:** the document says what it does not hold. The operating
  contract — floors move up and never down, no agent-written waivers, no
  hand-run `witness` — is `SKILL.md`'s and outranks every `AGENTS.md`;
  disclosure is `SECURITY.md`'s; the gate ladder is `docs/hooks.md`'s. One
  closing sentence points at each. Copying any of them would make a second
  place for a rule that already has one, which is the condition the
  nested-AGENTS convention and this package both exist to end.
- **DEC-POL-011:** the versioning section states the refusal as an exit
  code and never quotes the message. Review found that the message the
  skill documents at `exit-codes.md:107` — "unsupported schema_version
  <got> (expected <n>)" — is not what `report.py:259–261` emits, which is
  "findings schema_version <got> is not the <n> this build reads;
  regenerate the envelope with this version of planlint". A policy document
  that quoted either would be a third copy of a string two files already
  disagree on, and the string is `report`'s to change. The exit code is the
  contract — `exit-codes.md` and the code agree on 2 — so the policy states
  that and stops. The stale quote is recorded in `tasks.md` as a follow-up
  for the skill, which C-POL-1 closes to this package and which ships in a
  package release under `docs/hooks.md`'s "Releasing a skill change".

---

## Acceptance Criteria

- [x] **AC-POL-1:** `docs/policies.md` exists, opens with an index, carries
  the three policy sections with plain-word headings and the wording
  DEC-POL-003 through DEC-POL-006 decide, is listed in
  `tools/check_docs.py` `REQUIRED_DOCS`, is named in `README.md`'s
  "Documentation" section and linked from `llms.txt`, and the docs gate
  passes on the real tree. The `llms.txt` clause is the new module's
  registration test, which is cited here once it exists; the stage holds
  the rest until then. (R-POL-1, R-POL-2, R-POL-3, R-POL-4, R-POL-5,
  R-POL-7, DEC-POL-001, DEC-POL-008)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_policies_doc_is_registered_in_the_docs_gate_and_named_in_the_readme_and_llms"` · stage: `make docs-check`

- [x] **AC-POL-2 (non-success):** with `docs/policies.md` in the required
  set, a tree where it is missing, or present but not named in `README.md`,
  fails the docs gate with a message naming the document — the fixture is
  built from `REQUIRED_DOCS` itself, so the new entry is inside the
  property without a test edit. (R-POL-7, DEC-POL-008)
  _Verified by:_ `pytest -k "test_docs_check_reports_a_missing_doc or test_docs_check_reports_a_present_but_unlinked_doc"` · stage: `make test`

- [x] **AC-POL-3:** `docs/policies.md` has at least one level-two heading
  and at least one index entry, read outside fenced code blocks; every
  heading is plain words and no heading repeats; every heading has an index
  entry and every index anchor is a heading; every link to
  `policies.md#<anchor>` in `openspec/AGENTS.md`, `docs/AGENTS.md`,
  `docs/agents-skills-harness.md`, `llms.txt` and `README.md` lands on a
  heading and resolves from its file's directory; and each of the three
  pointer files carries at least one such link. The tests are written with
  this change; until they exist the stage is the citation. (R-POL-1,
  R-POL-6, R-POL-8, DEC-POL-002, DEC-POL-007)
  _Verified by:_ `pytest -k "test_every_policy_heading_is_indexed_and_every_index_anchor_resolves or test_every_policy_pointer_resolves_to_a_heading_and_each_pointer_file_has_one"` · stage: `make test`

- [x] **AC-POL-4 (non-success):** through the same two offender functions
  the real-tree tests call, a planted document whose index names an anchor
  with no heading yields an offender naming the anchor; a planted document
  with a heading no index entry names yields one naming the heading; a
  planted document with no level-two heading, or no index, yields an
  offender rather than an empty list; and a planted pointer text whose
  fragment is not a heading yields an offender naming the fragment. The
  tests are written with this change; until they exist the stage is the
  citation. (R-POL-8, DEC-POL-007)
  _Verified by:_ `pytest -k "test_a_dead_index_anchor_is_named or test_an_unindexed_policy_heading_is_named or test_an_empty_policy_document_is_an_offender_not_a_pass or test_a_pointer_to_a_missing_fragment_is_named"` · stage: `make test`

- [x] **AC-POL-5:** after its one-sentence pointer, `openspec/AGENTS.md` is
  within `MAX_NESTED_LINES`, still states its precedence, still carries a
  balanced mermaid fence, declares no `INV-n`, and every link in it — the
  new `../docs/policies.md` one included — resolves from `openspec/`; the
  same link check holds for `docs/AGENTS.md` and `llms.txt`. (R-POL-6,
  R-POL-7, DEC-POL-002)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_nested_agents_file_has_a_balanced_mermaid_block or test_nested_agents_file_declares_no_invariant_ids or test_agent_index_links_resolve"` · stage: `make test`

- [x] **AC-POL-6:** every backticked `make` citation in the agent indexes
  (`openspec/AGENTS.md`, `docs/AGENTS.md`, `llms.txt`) names a target this
  repository declares, through G004's own matcher; the same check over
  `docs/policies.md` is the new module's and is cited here once it exists.
  (C-POL-4, R-POL-4, R-POL-8, DEC-POL-007)
  _Verified by:_ `pytest -k "test_every_make_citation_in_an_agent_index_names_a_real_target or test_every_make_citation_in_the_policy_doc_names_a_real_target"` · stage: `make test`

- [x] **AC-POL-7:** the `specgraph` alias behaves exactly as before — warns
  to stderr, delegates, preserves a failing exit code, keeps stdout
  parseable — and `openspec_graph/cli.py` is absent from this package's
  diff. (C-POL-1, R-POL-3, DEC-POL-004)
  _Verified by:_ `pytest -k "test_deprecated_alias_warns_to_stderr_and_delegates or test_deprecated_alias_preserves_failure_exit_code or test_deprecated_alias_keeps_stdout_parseable"` · stage: `make test`

- [x] **AC-POL-8:** the rule inventory is unchanged — the live rule table
  still matches `tests/baseline_rules.json`. (C-POL-1)
  _Verified by:_ `pytest -k test_rule_set_matches_baseline` · stage: `make test`

- [x] **AC-POL-9:** `docs/agents-skills-harness.md`'s existing rule-count
  sentence still matches the registry and no second rule-count phrase was
  added by the new section. (C-POL-3, R-POL-6)
  _Verified by:_ `pytest -k test_total_rule_count_matches_every_prose_claim` · stage: `make test`

- [x] **AC-POL-10:** `CHANGELOG.md` `[Unreleased]` — or `[0.3.0]`, if this
  package lands after the cut — carries this package's `Added` entry and
  the `specgraph` line under `Deprecated`, the window that line states is
  the one `docs/policies.md` states, the `Deprecated` group carries that
  line once, and every versioned section still links to its release tag.
  The entries are read directly; the test holds the link shape. (R-POL-9,
  DEC-POL-009)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [x] **AC-POL-11:** the consumer behaviour the versioning section describes
  is the behaviour the tree has — a dialect card whose `schema_version`
  changed is reported as its own kind of change, and a witness record with an
  unrecognized `schema_version` is skipped rather than read. (R-POL-2,
  DEC-POL-003)
  _Verified by:_ `pytest -k "test_diff_cards_reports_schema_version_changes_distinctly or test_load_witnesses_skips_a_file_with_an_unrecognized_schema_version"` · stage: `make test`

- [x] **AC-POL-12:** this spec's requirements and criteria pin no count
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
| Focused | `make test` | AC-POL-2..11 — the new module green on the real tree and red on its planted texts; every existing guard this change leans on still green |
| Self-check | `make validate` | AC-POL-12 — this package validates clean against the repo's own rules, then the whole tree |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
