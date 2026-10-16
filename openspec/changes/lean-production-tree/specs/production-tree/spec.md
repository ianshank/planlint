# Spec: Production Tree

> **Change:** `lean-production-tree`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

What an adopter fetches from this repository is the whole tree at a tag: the
composite Action installs from a copy of its own checkout, and the plugin
marketplace installs from the repository root. Most of that tree is the
development record — planning documents and peer reviews of work that has
shipped, a roadmap that calls itself a plan, an evaluation suite no job runs,
and a change package for every piece of shipped work. Conventions kept it
there. A `*-plan.md` is left ungated because it is "consumed and retired",
and nothing retires one. A shipped package is a record and is not edited, so
it is never removed either. And the evaluation suite is kept as evidence
although nothing runs it.

The cost is not only weight. A test pins this repository's own package name,
so no package can leave without a red suite. Agent prose sends every new
drafter to a package a sweep would delete. Living documents state facts about
the record — that the spec-status report stays red, how many nested
`AGENTS.md` files exist — that stop being true the day it goes. And packages
that stay open require edits to files this change deletes.

This spec moves the record out of the tree and keeps it reachable: an archive
tag pins the last `dev` tree that carried it, every pointer names that tag,
the content still needed moves before its file goes, a sweep rule keeps the
tree from refilling, and a test holds the tree to all of it.

**Evidence:** measured at `c0ff090`, 2026-10-15; each command and its figure
is in `tasks.md`, and none is repeated here (C-LPT-3).

- **What ships.** `.github/actions/planlint/action.yml` copies
  `$GITHUB_ACTION_PATH/../../..` with `shutil.copytree` before installing,
  and `.claude-plugin/marketplace.json` declares `"source": "./"`.
- **The conventions.** `docs/AGENTS.md` — its diagram and its closing
  paragraph — and the comment above `docs/policies.md` in
  `tools/check_docs.py` leave a plan ungated; DEC-MCO-006 and DEC-TSS-016
  treat a shipped package as a record that is not edited; `docs/next-steps.md`
  item 16 says no job runs `evals/`, and item 4's one real run is still open.
- **The coupling.** `tests/test_spec_status.py` pins `THIS_PACKAGE`;
  `.claude/agents/spec-drafter.md`, `.claude/agents/spec-adversary.md` and
  `.claude/skills/planlint-release/SKILL.md` name packages; `docs/hooks.md`'s
  reports section, `docs/aqa.md` and `docs/next-steps.md` item 24 say
  `make spec-status` stays red until `settle-package-status-headers` lands,
  which a scratch export with the deletions applied contradicts.
- **The kept packages.** `add-witness-ci-artifacts`, with no criterion
  ticked, requires moving `docs/differentiation-roadmap.md` and
  `docs/peer-review-2026-09.md` and keeping `evals/fabricate-witness/`
  byte-identical; `prepare-release-0-3-0` and `adopt-branch-promotion-model`
  place the release runbook in `docs/distribution-plan.md`.
- **What a lean tree keeps green.** The same scratch export validates clean
  at `--fail-on INFO`, graphs with no broken link and no new orphan
  requirement, and passes the docs gate. G006 and G009 cannot fire:
  `openspec/specgraph.json` declares no invariant source, and no candidate
  path in `openspec_graph/detect.py` exists.

---

## Requirements

### What leaves the tree

- R-LPT-1: No file the repository ships MAY be a planning or review document
  under `docs/`, and none MAY sit under `evals/`. The change MUST delete
  `docs/agent-directory-wiring-plan.md`, `docs/distribution-plan.md`,
  `docs/eval-corpus-plan.md`, `docs/reflection-plan-2026-10.md`,
  `docs/peer-review-2026-09.md`, `docs/peer-review-2026-10.md`,
  `docs/differentiation-roadmap.md`, the whole of `evals/`, and
  `.claude/skills/planlint-add-eval-case/`. A plan is a change package under
  `openspec/changes/`; a planning document that is not one is not tracked.
  `docs/AGENTS.md` — its closing paragraph and the diagram node that names
  ungated plans — and the comment above the `docs/policies.md` entry in
  `tools/check_docs.py` MUST state that convention in place of the one that
  left a `*-plan.md` ungated, and MUST say that the archive tag of R-LPT-3
  holds the last planning documents. `docs/AGENTS.md` MUST keep its link to
  `policies.md`, its precedence clause and a balanced mermaid fence, and MUST
  stay within `MAX_NESTED_LINES`. `REQUIRED_DOCS` MUST keep every entry.
- R-LPT-2: Under `openspec/changes/`, the change MUST delete every package
  directory present at the archive tag except `add-witness-ci-artifacts`,
  `widen-indeterminate-unchecked-citations`, `prepare-release-0-3-0` and
  `adopt-branch-promotion-model`, which stay open with this package beside
  them. `openspec/AGENTS.md`, `openspec/project.md` and
  `openspec/specgraph.json` MUST stay. Wherever the deleted package set is
  described — this spec, its proposal, `CHANGELOG.md` — it MUST be described
  by that rule and by the command that lists it from the merged tree,
  `git diff --name-only --diff-filter=D archive/dev-record-2026-10 <merge commit> -- openspec/changes | cut -d/ -f3 | sort -u`,
  and MUST NOT be described by a count.
- R-LPT-3: Every pointer from a file the repository ships to a path this
  change deletes MUST be a URL of the form
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/<path>`
  — or, where DEC-LPT-001's fallback is taken, the same form under the dated
  tag that replaces it — on the line that names the path. The tag's name MUST
  begin `archive/`, so it matches no `v*` pattern, and no workflow trigger,
  guard or tool in the tree MAY act on it.

### What moves before its file goes

- R-LPT-4: The release runbook MUST move into `docs/hooks.md` under its
  existing `## Releasing` heading, kept by that name, in the same change and
  before `docs/distribution-plan.md` is deleted. It MUST be one numbered
  sequence, in this order: the release-prep pull request into the integration
  branch, carrying the bump checklist the section already holds and the
  changelog cut; the pre-tag checks on its head; the promotion to the
  release-candidate branch and then to production, each a merge commit; the
  release workflow's `workflow_dispatch` dry run on the production merge
  commit, with `publish` skipped; the date rule — the `[X.Y.Z]` heading is
  dated the day the tag is pushed, and a slip means a new release-prep pull
  request and a re-promotion, never a commit on production;
  `tools/check_promotion.py tag-ancestry` on that commit, then the annotated
  tag, pushed by a person or an App token and never by `GITHUB_TOKEN`;
  watching the release workflow; verifying each published file's
  attestations through PyPI's Integrity API and `pypi-attestations verify`;
  installing the published version into a fresh venv and running
  `validate --fail-on ERROR` on this repository; the GitHub release cut from
  the `[X.Y.Z]` section; the back-merge into the integration branch;
  recording the production merge commit and the run ids in a later pull
  request into the integration branch; and the post-release sweep of
  R-LPT-13. It MUST state that a tag goes only on a merge commit on the
  production branch and that nothing is committed to production after it,
  and MUST carry one sentence saying that the PyPI trusted publisher is bound
  to `release.yml` and the GitHub environment `pypi`. The section MUST name
  no change package. `.claude/skills/planlint-release/SKILL.md` MUST cite
  `docs/hooks.md` "Releasing" wherever it cited the deleted runbook, MUST
  name the sweep as its last step, and MUST name no change package.
- R-LPT-5: `docs/next-steps.md` MUST carry the deferrals of
  `docs/distribution-plan.md` §5 into item 17, retiring with the suite the
  rows about the evaluation suite, and its §6 non-goals as one sentence under
  "Deferred / out of scope". On every line that names a deleted document it
  MUST drop the path or carry an archive pointer on the same line. It MUST
  retire items 4 and 16 to one line each saying the suite is withdrawn and
  where it is archived; MUST re-scope item 24 so that its worklist is
  recorded as having left with `report-dead-code-and-spec-status`, its
  condition (b) as moot because no shipped package remains in the tree, and
  only its condition (c) — whether the vocabulary gains a "shipped" value an
  agent may set at a package's closure — as surviving; MUST replace the "Near
  term" pointer at the reflection plan with an archive pointer; MUST make
  every sentence that counts nested `AGENTS.md` files true on the merged
  tree, naming the command that regenerates the count; and MUST gain a
  "Retired documents" list naming once each document R-LPT-1 deletes, each
  with its archive pointer. Its "the N rules" phrase MUST still match the
  rule registry.

### The prose and configuration that pointed at the record

- R-LPT-6: `README.md` MUST say that `tests/test_agent_artifacts.py`
  validates the retrieval config and the agent indexes, not an evaluation
  suite; MUST replace the evaluation-suite paragraph with one saying the
  suite lived in the tree through v0.3.0, is archived at its archive URL and
  was never a gate, and that `tests/test_skill_contract.py` holds the
  read-only verbs and the exit-code messages while the refusal itself is
  `SKILL.md`'s prose; MUST describe the gate under "Dogfooding" with no link
  to a change package and no count — `openspec/changes/` holds the packages
  still open, CI runs this repository's own `planlint --target . validate
  --fail-on ERROR` as a hard gate, a package leaves the tree in the release
  that ships it, and the CHANGELOG and the archive tag hold every package
  shipped through v0.3.0; and MUST drop the documentation-list rows of every
  document R-LPT-1 deletes and of the suite, keeping every `REQUIRED_DOCS`
  link. `llms.txt` MUST drop its roadmap line.
  `docs/agents-skills-harness.md` MUST drop the eval-case skill from its list,
  MUST state the nested `AGENTS.md` set true on the merged tree with the
  command that regenerates its count, and MUST point at the wiring plan by
  archive URL. `SECURITY.md` MUST say coverage limits are tracked as findings
  in `docs/next-steps.md`. `docs/aqa.md` MUST drop its evaluation-suite claim.
  `docs/architecture/c4.md` MUST drop `evals/` from its distribution row.
  `docs/hooks.md` MUST drop the bullet for edits under `evals/` and the
  eval-case skill from its skill list.
- R-LPT-7: `context7.json` MUST drop `evals` from `excludeFolders` and the
  deleted plan files from `excludeFiles`, and every folder and file it names
  MUST exist. Each line of `.gitignore`, `.dockerignore`, `.gitleaks.toml`,
  `pyproject.toml` and `.github/dependabot.yml` that names `evals/` or
  `docs/distribution-plan.md` MUST be removed or reworded so it states
  nothing about a deleted path, and `.dockerignore` MUST keep excluding
  `skills`, `.claude`, `.claude-plugin`, `context7.json` and `llms.txt`.
  `tests/test_adopter_urls.py` MUST drop `evals` from `_EXCLUDED_DIRS` in the
  same commit as the deletion.
- R-LPT-8: `.claude/` MUST be kept, with only references to deleted paths and
  names of change packages trimmed. `.claude/hooks/nudge_rule_registry.sh`
  MUST lose its `*/evals/*` arm. Agent and skill prose under `.claude/` MUST
  name no change package: `.claude/agents/spec-drafter.md`,
  `.claude/agents/spec-adversary.md` and
  `.claude/skills/planlint-change-package/SKILL.md` MUST say to read the open
  packages under `openspec/changes/` in full, and MUST put any worked example
  behind its archive URL as a backticked `https://` span;
  `.claude/skills/planlint-add-rule/SKILL.md` MUST drop the roadmap;
  `.claude/agents/planlint-verifier.md` MUST drop `evals/` and the
  `post-merge-quality-review` path. Area codes MUST stay unique across the
  record: `openspec/project.md` MUST gain one line listing every area code a
  deleted package declared, and the drafter's collision check MUST read that
  line as well as the open specs. Every backticked path in `.claude/` prose
  MUST resolve, every make target it names MUST exist, and both harness
  indexes MUST name every agent and skill that exists.

### The tests

- R-LPT-9: No test MAY name a change package as a value it asserts on.
  `tests/test_spec_status.py` MUST drop `THIS_PACKAGE` and every assertion on
  it; the header-agreement test MUST keep its assertion that it compared at
  least one spec, and the row test MUST assert that it found rows beside its
  row-per-package equality, so that neither can pass on an empty scope; their
  docstrings MUST follow. `tests/test_agent_artifacts.py` MUST drop
  `EVALS_DIR`, `EVAL_CASES` and its comment, the grader and tag constants and
  the evals section, and MUST rename
  `test_context7_indexes_the_skill_and_excludes_the_evals` to
  `test_context7_indexes_the_skill`, keeping its assertion that the skill is
  indexed; its module docstring MUST follow. `tests/test_release_surface.py`
  MUST drop `evals` from the Docker-context tuple and from the docstring of
  the root-scoped test. `tests/test_claude_hooks.py` MUST drop the evals
  entry from its nudge table. `tests/test_rule_registry_docs.py` MUST drop
  the roadmap's row. Each mypy ceiling `tests/test_static_ratchets.py` holds
  that the deletions lower MUST be lowered to its new exact count, and none
  MAY be raised.
- R-LPT-10: A new module `tests/test_tree_hygiene.py` MUST hold the shape of
  the tree: no file the repository ships — tracked, plus untracked and not
  ignored — MAY match `docs/**/*-plan.md`, `docs/**/peer-review-*.md` or
  `docs/**/reflection-*.md`, or sit under `evals/`. The check MUST read paths
  only, never a file's contents. The files MUST be enumerated through one git
  helper in `tests/support.py`, which `nested_agents_files` in
  `tests/test_agent_artifacts.py` MUST call as well.
- R-LPT-11: The module MUST hold every reference in the shipped prose:
  `README.md`, `llms.txt`, the root `AGENTS.md` and every nested one
  `nested_agents_files` returns, and every shipped `docs/**/*.md`,
  `skills/**/*.md` and `.claude/**/*.md` — no file under `openspec/changes/`,
  no other file under `tests/`, and never `CHANGELOG.md`. It MUST read as
  tokens every markdown link target that does not begin `http://`,
  `https://`, `mailto:` or `#`, its fragment removed, resolved against the
  directory of the file that carries it; and every backticked span that is
  wholly a path beginning `docs/`, `evals/`, `openspec/changes/`, `.claude/`
  or `skills/`, made of letters, digits, `_`, `.`, `/` and `-`, resolved
  against the repository root, a span carrying `<`, `*` or `://` being
  skipped. A token MUST be exempt when the line that carries it also carries
  a ref matching `archive/[\w.-]+`, whatever the tag's name. Every other
  token that resolves to nothing MUST be reported with its file, its line and
  the token.
- R-LPT-12: The reference scanner MUST be one function that takes a file's
  text, its repository-relative path and the root, reads no file, and returns
  the offenders; the real-tree test and the planted tests MUST both call it.
  Planted, the module MUST show: a dangling backticked path reported with
  file and line; a dangling relative link reported with file and line; a
  line that carries an archive ref, quiet; a path-shaped token inside an
  external URL, quiet; a span carrying `<` or `*`, quiet; and, in a repository
  made under `tmp_path` with `git init`, a tracked `docs/foo-plan.md`
  reported by the shape check. Every test in it MUST carry the tier
  `tests/shape_support.py`'s criterion computes, marked per function where
  the module mixes tiers. The module MUST stay flat under `tests/` and within
  `MAX_TEST_MODULE_LINES`, and MUST add no mypy error under `tests/`.

### Keeping the tree lean

- R-LPT-13: `docs/hooks.md` "Releasing", as its last step, and `README.md`
  "Dogfooding" MUST state the sweep rule: after a release is tagged, a
  post-release sweep deletes from `openspec/changes/` every package whose
  work that release shipped, once its `tasks.md` records the release, and
  appends the area codes the deleted packages declared to the
  `openspec/project.md` line of R-LPT-8; a package's shipped-ness is read
  from evidence — the surface in the tree and a CHANGELOG entry — never from
  its Status header; and the sweep MUST NOT delete the last package in
  `openspec/changes/` — if none would remain, the next package lands first.
- R-LPT-14: On the merged tree, `make spec-status` MUST list one row per
  package under `openspec/changes/` and none for a deleted one. Every living
  document's sentence about its exit — the spec-status row and the paragraph
  under the reports table in `docs/hooks.md`, the paragraph in `docs/aqa.md`
  and item 24 of `docs/next-steps.md` — MUST be true on the merged tree: the
  report exits 0 while no package closes under a `DRAFT` header, and a
  package that closes under one reads `draft-but-complete`, exiting 1, until
  `settle-package-status-headers` decides the vocabulary. A figure in such a
  sentence MUST name the commit it was measured at and `make spec-status`.
  `docs/hooks.md`'s reports section MUST keep the literal
  `settle-package-status-headers`.
- R-LPT-15: `CHANGELOG.md`'s `[Unreleased]` section MUST gain
  `### Removed — the development record`, with a bullet led by the bold
  backticked name of this package, naming by name each document R-LPT-1
  deletes, `evals/`, the eval-case skill, the deleted package set by R-LPT-2's
  rule and command, the archive tag, and the move of the release runbook to
  `docs/hooks.md` "Releasing".
- R-LPT-16: Where a package that stays open requires an edit to a path this
  change deletes, the clause MUST be reconciled in this change. In
  `add-witness-ci-artifacts`, which is open and unimplemented, every clause
  naming a deleted path — the documents its R-WCA-33 and AC-WCA-29 require to
  move, the byte-identical `evals/fabricate-witness/` of R-WCA-33 and
  AC-WCA-30, and the matching proposal and `tasks.md` lines — MUST be amended
  in place and marked "(amended by `lean-production-tree`)": the deleted
  documents leave its lists, and the evals clause becomes `SKILL.md`'s
  refusal kept verbatim. The clauses of `prepare-release-0-3-0` (R-REL-11,
  AC-REL-16, DEC-REL-008) and of `adopt-branch-promotion-model` (R-BPM-14)
  that place the runbook in `docs/distribution-plan.md` MUST be superseded in
  part by name, here (DEC-LPT-006), and MUST NOT be edited; the properties
  they protect MUST hold of `docs/hooks.md` "Releasing" (R-LPT-4).

### Constraints

- C-LPT-1: No file under `openspec_graph/` or `.github/workflows/` MAY
  change, and neither MAY the `Makefile`, the `RULES` tuple, `README.md`'s
  rules table, `tests/baseline_rules.json` or a golden hash.
  `[project] dependencies` MUST stay empty.
- C-LPT-2: A code comment or docstring that attributes a fact to a deleted
  document or package — that says where the fact came from — MUST stay as
  written. One that states a present fact about a deleted path MUST be
  corrected.
- C-LPT-3: This spec MUST NOT pin a count — of files, bytes, packages, specs,
  documents, tokens, nested files or tests. Every measurement belongs in
  `tasks.md`, dated with its commit and naming its command.
- C-LPT-4: `CHANGELOG.md`'s released sections MUST NOT be edited. This change
  MUST NOT edit the requirements, decisions or criteria of
  `prepare-release-0-3-0` or `adopt-branch-promotion-model`; the release
  record the runbook writes into their `tasks.md` belongs to the 0.3.0
  release and MAY ride in this change's pull request. R-LPT-16's amendment is
  the only edit to another package's text.
- C-LPT-5: `tests/test_spec_test_citations.py` MUST NOT change, and its
  absolute floor on selector tokens MUST hold over the specs that remain.

---

## Decisions

- **DEC-LPT-001:** the development record leaves the tree, and an annotated
  tag keeps it. What an adopter fetches is the tree at a tag — the Action
  copies its own checkout and the marketplace installs the root — and the
  record serves the people who change the tool, not the people who run it.
  Git history already holds every byte; an annotated tag,
  `archive/dev-record-2026-10`, makes the last tree that carried the record
  addressable by a name a reader can type, and carries its reason in the tag
  object. It points at the `dev` commit the implementation branch is cut
  from, so each deleted file is byte for byte what the tree held, and before
  the merge the branch is checked for a deleted path that changed on `dev`
  since the tag (`tasks.md` Milestone 2). The tag is never moved: the owner's
  tag ruleset refuses an update or a deletion under `archive/*`, and a moved
  tag would silently change what every pointer shows. So if that check
  fails, the merge base is tagged under a dated suffix, the pointers are
  rewritten to it, and the first tag stays. A pointer names the tag rather
  than a sha so a reader sees what it is, and uses `/tree/` because GitHub
  resolves files and directories alike under it. The name begins `archive/`,
  outside every `v*` pattern, and nothing in the tree reacts to such a tag:
  `release.yml` triggers on `v*`, the promotion guard's tag pattern requires
  `v` and a digit, and `tools/check_promotion.py` takes a sha. Rejected: an
  archive branch (a branch can be force-pushed or deleted, and the branch
  rulesets cover only `main`, `qa` and `dev`); a second repository (a second
  thing to own, for bytes history already keeps); an `archive/` directory in
  the tree (adopters would still fetch it, and `detect` would count
  `openspec/changes/archive/` as one package).
- **DEC-LPT-002:** what leaves, by kind. The planning documents and reviews
  were "written to be executed and then retired" (`docs/AGENTS.md`); they
  were executed, and the finding ids they produced stay in
  `docs/next-steps.md`. The roadmap is DEC-LPT-009's, the suite and its skill
  DEC-LPT-008's. The change packages whose work had shipped by v0.3.0 leave
  because the CHANGELOG records what each release did and the tag holds each
  package as it was (DEC-LPT-004). A package's shipped-ness is read from
  evidence — the surface it describes is in the tree and a CHANGELOG entry
  covers it — never from its Status header, which `make spec-status` exists
  to compare against that evidence precisely because header and evidence
  disagree. The set is described by its rule and by the command that lists
  it, never by a count: a count is true at one commit, and
  `docs/policies.md` writes a number no command regenerates as a description
  of the set.
- **DEC-LPT-003:** which packages stay, and why the 0.3.0 pair is not swept
  here. `add-witness-ci-artifacts` and
  `widen-indeterminate-unchecked-citations` are drafted and unimplemented, so
  they are open work, not record. `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` shipped in 0.3.0, but each still owes its
  release record — the production merge commit, the run ids, the pull
  requests — which the runbook writes after the tag and which may ride in
  this change's pull request (C-LPT-4). Deleting a package in the change that
  writes its record would leave that record only in history. They leave in
  the 0.4.0 post-release sweep, as this package does. This change is a
  one-time removal set by the kept list; the sweep rule of DEC-LPT-012 binds
  from that sweep on.
- **DEC-LPT-004 (supersedes the premise of DEC-MCO-006 and DEC-TSS-016):**
  restated, DEC-MCO-006
  (`https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/measure-coverage-once/specs/one-run-coverage/spec.md`)
  and DEC-TSS-016
  (`https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/shape-the-test-suite/specs/test-suite-shape/spec.md`)
  supersede shipped records by name and edit none of their packages, on the
  premise that a shipped package is a record of what shipped and is not
  edited. That premise made the tree the record, and it is superseded: the
  record is `CHANGELOG.md` — the dated record `docs/policies.md` exempts from
  tracking the tree — and the archive tag, which holds each package exactly
  as it shipped; the tree carries the packages still open. Deleting a shipped
  package is a different act from editing one. Deletion leaves every byte at
  the tag unaltered; an edit would make the tag and the tree disagree about
  what shipped. So the half that protected the record survives — no change
  edits a shipped package's text, and a change that supersedes a shipped
  decision names it with its archive URL — and this change applies it to the
  0.3.0 pair (C-LPT-4). Both packages are deleted here, so both are cited by
  archive URL. The cost is recorded, not hidden: a precedent grep over the
  open specs no longer finds an archived decision, and a kept package's
  cross-reference to one becomes an archive lookup; a package restates what
  it relies on, as this one does.
- **DEC-LPT-005 (supersedes the premise of DEC-POL-008):** restated, DEC-POL-008
  (`https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/write-down-policies/specs/project-policies/spec.md`)
  registered `docs/policies.md` in `REQUIRED_DOCS` because a policy document
  is permanent, against `docs/AGENTS.md`'s convention that leaves a
  `*-plan.md` ungated because it is consumed and retired. That convention
  assumed a plan lives in the tree, and it is superseded: a plan is a change
  package — gated by this repository's own validate, reviewed by
  `spec-adversary`, swept after its release — and a planning document that is
  not one stays out of the tree, where an issue, a pull-request description
  or a session's own plan already lives. DEC-POL-008's conclusion stands:
  `docs/policies.md` stays in `REQUIRED_DOCS`. Nothing ever retired a plan,
  so "retired" meant kept forever and ungated; the shape check of R-LPT-10
  turns the new convention into a test. Rejected: gating plans through
  `REQUIRED_DOCS` (a plan is not permanent, and each would need a README
  row); a `docs/plans/` directory (the same tree, fetched the same way).
- **DEC-LPT-006 (supersedes, in part, R-REL-11, AC-REL-16 and DEC-REL-008 of
  `prepare-release-0-3-0` and R-BPM-14 of `adopt-branch-promotion-model`):**
  content moves before its file goes. The runbook goes to `docs/hooks.md`
  "Releasing": that file is the gated contributor document that already holds
  the bump checklist and *Branching and promotion*, the release skill already
  points there, and `tests/test_agent_skill_docs.py` cites the heading, so it
  keeps its name. The steps keep their order, and the date rule moves in
  substance, because it is the line the release's own review found must
  survive the move: a slipped date is a new release-prep pull request, never
  a commit on production. Only the location those clauses name is
  superseded; what they protect — the order, a tag only on a merge commit on
  production, nothing committed to production after it — holds of the new
  section, and neither package is edited (DEC-LPT-004). The 0.3.0-only steps
  neither recur nor move: registering the pending publisher, the Context7
  submission, and the repository's description and topics. The one fact a
  later release needs from them is the binding, so one sentence states that
  the trusted publisher is bound to `release.yml` and the environment `pypi`.
  The deferral table (§5) goes to item 17 of `docs/next-steps.md`, the
  backlog of record, its evaluation-suite rows retired with the suite; the
  non-goals (§6) become one sentence there, because their substance already
  lives in that file and the README.
- **DEC-LPT-007:** the open, unimplemented package is amended in place.
  `add-witness-ci-artifacts` requires moving documents this change deletes
  and keeping `evals/fabricate-witness/` byte-identical; implemented on the
  lean tree as written, those clauses could not be met. It is not shipped, so
  there is no record to protect, and it already carries in-place amendments
  marked "(amended by `measure-coverage-once`)"; the same form here keeps the
  open spec true of the tree its implementer will meet. The evals clause
  becomes `SKILL.md`'s refusal kept verbatim, the property the eval case was
  evidence for. Rejected: superseding it by name only (its implementer would
  meet a requirement nobody can satisfy and would reconcile it without this
  reasoning); deleting it (it is open work).
- **DEC-LPT-008:** `evals/` is withdrawn, not moved. No job runs it,
  `claude plugin eval` needs a plugin runtime CI lacks, its adversarial half
  is non-deterministic, and item 4's one real run never happened; its only
  gate was the structural half of `tests/test_agent_artifacts.py`. Moving it
  — under `docs/`, to another repository — would keep a corpus nobody runs in
  a place someone must maintain. The cost is named: the cases were the only
  evidence that the skill refuses to make a finding disappear, and no test
  holds that refusal — `tests/test_skill_contract.py` holds the read-only
  verbs and the exit-code messages, and `SKILL.md`'s refusal is prose. The
  README says exactly that, rather than that the contract test holds "the
  boundary", so the claim does not outgrow the test. The reopen trigger is
  item 16's — a headless, deterministic runner — and the cases are restored
  from the archive tag then.
- **DEC-LPT-009:** the roadmap is retired as a plan by its own header,
  "Planning artifact. Not implementation.", not by the shape check. Its
  comparison already lives in the README's "Why this and not Spec-Kit /
  GitHub Spec / Kiro / Cursor", and the rule-count row
  `tests/test_rule_registry_docs.py` reads from it goes with the file.
- **DEC-LPT-010:** agent prose names no change package, and area codes stay
  unique across the record. Every package is transient now, so a package
  named as the worked example dangles at the next sweep, while "read the open
  packages under `openspec/changes/` in full" is true at every commit. An
  example worth keeping sits behind its archive URL as a backticked
  `https://` span, which the `.claude/` path test cannot read as a path (its
  pattern admits no `:`) and which the reference scanner skips (`://`) and
  exempts (the archive ref). Ids are history-wide: the kept packages cite
  archived decisions by id, so a new package reusing an archived area code
  would make those citations ambiguous. A drafter that may not run `git`
  cannot read the tag, so `openspec/project.md` — which declares itself
  authoritative and which `detect` reads only for its existence — carries one
  line listing the area codes the deleted packages declared, generated by the
  command `tasks.md` names and extended at each sweep. A docstring under
  `.claude/hooks/` that names a package is code, and C-LPT-2's. No mechanical
  guard checks package names: the reference scanner reads paths, a name check
  would need the package list at each commit and would fire on every
  archive-URL line, and `spec-adversary` reads agent prose.
- **DEC-LPT-011:** no test names a change package, and non-vacuity stays.
  `THIS_PACKAGE` made `report-dead-code-and-spec-status` impossible to
  remove. Dropping it leaves each real-tree test honest by its own floor: the
  header-agreement test already asserts it compared at least one spec, and
  the row test gains an assertion that it found rows, beside the
  row-per-package equality that already proves one row per package. Every
  real-tree gate assumes at least one open package — the spec-status report
  exits 2 on none, the agreement test refuses an empty scope, and the
  stage-citation test reads the `test` stage's row — which is why the sweep
  has a floor (DEC-LPT-012).
- **DEC-LPT-012:** the sweep rule. A package leaves `openspec/changes/` in the
  post-release sweep of the release that ships it, once its `tasks.md`
  records that release. After the tag and not before: the tagged tree carries
  the packages it shipped, so the release tag is their archive by
  DEC-LPT-001's reasoning, and the record the runbook writes lands only after
  the tag. The sweep never deletes the last package, and if none would
  remain the next package lands first, because the real-tree gates of
  DEC-LPT-011 would otherwise read nothing — and a planted empty tree shows
  they refuse it rather than pass. Shipped-ness is read from evidence
  (DEC-LPT-002), and the sweep appends the deleted packages' area codes to
  `openspec/project.md` (DEC-LPT-010). The rule is written where it is run,
  as the runbook's last step, and where a reader of the front page meets it,
  under "Dogfooding".
- **DEC-LPT-013:** the reference scanner's scope and tokens. The scope is the
  prose a reader or an agent opens first, where a path is a claim: the
  README, `llms.txt`, every `AGENTS.md` the nested-agent contracts hold (the
  fixture trees excluded, `tests/AGENTS.md` included) and the markdown under
  `docs/`, `skills/` and `.claude/`. It excludes `openspec/changes/`, where
  packages cite history freely and the kept ones cite archived packages by
  path until their own sweep; the rest of `tests/`, whose comments are
  C-LPT-2's; and `CHANGELOG.md`, a dated record. Link targets are resolved as
  `test_agent_index_links_resolve` resolves them, against the carrying file's
  directory, which is the renderer's rule. Backticked spans are read only
  when they are wholly a path under one of the trees this change deletes from
  or keeps prose in, resolved from the root: a bare pattern over running text
  would misread the external `docs/concepts.md` URL in the README, a span
  carrying `<` or `*` is a placeholder or a glob, and `://` marks a URL.
  Existence is read from disk under the root, as the link test reads it.
  Gaps are accepted and named: a bare directory span such as `evals/` names
  no path below its prefix and is not resolved, so the shape check holds
  `evals/` absent instead; a `path:line` span is not wholly a path and is not
  resolved (none sits in scope at `c0ff090`); a reference-style link is not
  read. The scanner's first run on a tree with the deletions applied is the
  authority on what the edit list missed, so it is run red before the edits
  (`tasks.md` Milestone 3).
- **DEC-LPT-014:** the archive exemption is generic — any `archive/[\w.-]+`
  ref on the same line, not the 2026-10 tag's name — so a dated-suffix tag
  (DEC-LPT-001) or a later archive needs no test edit. The same line, because
  a pointer and the path it stands in for belong in one sentence. The cost: a
  line naming any `archive/` path is exempt too; accepted, because the tree
  has no `archive/` directory and the spec-status report would list one as a
  package.
- **DEC-LPT-015:** the shape check reads paths only. The shapes are the names
  the deleted documents used; a content heuristic — a "Planning artifact"
  header, say — would misfire on documents that discuss plans, the README's
  opening paragraph among them. A plan under another name, as the roadmap
  was, is not caught by its shape: a link to it is caught by the reference
  check, and the rest by review.
- **DEC-LPT-016:** what `make spec-status` says after the merge, and the
  sentences about it. On a tree with the deletions applied the report has no
  finding, so "stays red until `settle-package-status-headers` lands" becomes
  false the day this merges. The sentences are rewritten to the conditional
  truth, which keeps the literal `tests/test_ci_makefile.py` requires in the
  reports section and names the one case that turns the report red: a package
  that closes under a `DRAFT` header, this one included once its boxes are
  ticked. A figure is allowed only dated with its commit and its command,
  because the package count moves at every sweep. Item 24 keeps only its
  condition (c). Condition (b), writing down an exception to the records
  convention before editing a shipped header, is moot with no shipped package
  in the tree; condition (a) concerned recording the status of shipped
  packages somewhere the report would have to learn to read, and a swept
  package's status is its absence and its CHANGELOG entry, which the report
  never reads; the worklist the report produced left with the package that
  recorded it.
- **DEC-LPT-017:** the preconditions are `tasks.md` gates, not criteria. No
  test can observe a remote tag or a published release, and a criterion
  citing a stage that cannot see its subject is a pass nobody observed.
  `tasks.md` Milestone 2 records them before any deletion: `v0.3.0` on PyPI
  and back-merged into `dev` — `docs/next-steps.md`'s "After the first public
  tag" starts nothing earlier, and the archive tag must hold the 0.3.0
  release's own record; `git ls-remote --tags origin 'archive/*'`, with the
  peeled line naming the branch's base; and the deleted-path diff from the tag
  to the merge base. The change lands on `dev` after those and before 0.4.0's
  release-prep pull request, and reaches production only through the 0.4.0
  promotion, so `main` never differs from `qa` in content.
- **DEC-LPT-018:** stages and selectors. Verification lines cite `make test`,
  `make docs-check` or `make pre-pr`. None cites this repository's validate
  target: the `self-validate` job runs the bare command, so on the lean tree
  no workflow invokes that target by name and `make stage-citations` would
  list it as unrun; `make pre-pr` composes it through `ci`. Existing tests
  whose names survive the change are cited by selector. The new module's
  tests are not named until they exist, because the citation test resolves
  every selector against the collected test functions; the implementation
  commit adds them to AC-LPT-1 to AC-LPT-5, keeping each stage. The citation
  floor needs no retune, and if the corpus ever falls under it the remedy is
  a parity guard — the token count equal to the citation count, and not zero
  — never a floor of one.
- **DEC-LPT-019:** edits move in couples, and every commit stays green. Each
  couple is red if one half lands alone: `evals/` with the evals section of
  `tests/test_agent_artifacts.py`, whose collection-time read of `evals/`
  hides further failures behind its error; `context7.json`'s `evals`
  exclusion with the renamed context7 test; `llms.txt`'s roadmap line with
  the roadmap; `.dockerignore`'s `evals` line with the Docker-context tuple;
  the hook's `evals/` arm with the nudge-table entry; the eval-case skill's
  directory with its name in both harness indexes; `evals/AGENTS.md` with
  every sentence that counts nested `AGENTS.md` files; `evals` in
  `_EXCLUDED_DIRS` with `evals/` itself; and the reports sentence with the
  literal its test reads. The edits a still-present record does not
  contradict land first; the deletion, the halves coupled to it and the
  hygiene module land together, because the shape check is red while any
  deleted document exists.
- **DEC-LPT-020:** history comments stay. A comment or docstring that says
  where a fact came from — G003's scope limit as a peer review measured it, a
  test as a plan proposed it — is history: the archive tag resolves its path,
  and rewriting it to satisfy a lint is how a project loses the ability to
  explain itself, as the comment above `_EXCLUDED_DIRS` in
  `tests/test_adopter_urls.py` says of the CHANGELOG. A comment that states a
  present fact about a deleted path — that `evals/` holds markdown, that a
  directory is excluded from a scan — would be false, and is corrected.

---

## Acceptance Criteria

- [ ] **AC-LPT-1:** On the merged tree no file the repository ships matches a
  planning, review or reflection shape under `docs/` or sits under `evals/`;
  none of the documents R-LPT-1 names, and not the eval-case skill's
  directory, is present; and the directories under `openspec/changes/` are
  the open packages R-LPT-2 names and this one, as the listing command
  recorded in `tasks.md` confirms. The test is written with this change and
  cited here once it exists; the stage holds the criterion until then.
  (R-LPT-1, R-LPT-2, R-LPT-10, DEC-LPT-002, DEC-LPT-015)
  _Verified by:_ stage: `make test`

- [ ] **AC-LPT-2 (non-success):** In a repository made under `tmp_path` with
  `git init`, a tracked `docs/foo-plan.md` fails the shape check with its
  path named, and so does a planted file under `evals/`; the check reads no
  file's contents to decide either. (R-LPT-10, R-LPT-12, DEC-LPT-015)
  _Verified by:_ stage: `make test`

- [ ] **AC-LPT-3:** Over the shipped prose R-LPT-11 scopes, on the merged
  tree, the reference scanner returns no offender: every link target and
  every in-scope backticked path resolves, or its line carries an archive
  ref; and every archive pointer the change writes has R-LPT-3's URL form,
  which is read directly. (R-LPT-3, R-LPT-11, DEC-LPT-001, DEC-LPT-013)
  _Verified by:_ stage: `make test`

- [ ] **AC-LPT-4 (non-success):** Through the same scanner the real-tree test
  calls, a planted backticked path under one of R-LPT-11's prefixes that
  resolves to nothing, and a planted relative link that resolves to nothing,
  are each reported with the planted file's path, the line and the token,
  and the scan is not clean. (R-LPT-11, R-LPT-12, DEC-LPT-013)
  _Verified by:_ stage: `make test`

- [ ] **AC-LPT-5:** Through the same scanner, each of these planted lines
  yields no offender: a dangling path on a line that also carries
  `archive/dev-record-2026-10`, and one on a line carrying a differently
  named `archive/` tag; a path-shaped token inside an external `https://`
  URL; a span carrying `<` or `*`; and a link that is a fragment only.
  (R-LPT-11, R-LPT-12, DEC-LPT-013, DEC-LPT-014)
  _Verified by:_ stage: `make test`

- [ ] **AC-LPT-6:** The shape check and `nested_agents_files` enumerate the
  shipped files through the one helper in `tests/support.py`, and the
  planted nested-agent discovery still finds its planted file; the scanner
  reads no file; every test in the new module carries the tier the criterion
  computes; the module is flat under `tests/` and within the line bound; and
  every mypy code under `tests/` matches its ceiling exactly, none raised.
  The helper's shared use and the scanner's purity are read directly.
  (R-LPT-9, R-LPT-10, R-LPT-12, DEC-LPT-013)
  _Verified by:_ `pytest -k "test_every_tier_marker_matches_its_mechanical_criterion or test_no_test_module_exceeds_the_line_bound or test_the_tests_directory_stays_flat or test_nested_agents_discovery_finds_a_planted_file or test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms"` · stage: `make test`

- [ ] **AC-LPT-7:** `docs/AGENTS.md`'s closing paragraph and its diagram, and
  the comment above `docs/policies.md` in `tools/check_docs.py`, say that a
  plan is a change package, that a planning document that is not one is not
  tracked, and that the archive tag holds the last ones; `docs/AGENTS.md` is
  within its line budget, states its precedence, carries a balanced mermaid
  fence and links that resolve; and every required document is present and
  linked from the README. The prose is read directly; the tests and the docs
  gate hold the rest. (R-LPT-1, DEC-LPT-005)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_nested_agents_file_has_a_balanced_mermaid_block or test_agent_index_links_resolve"` · stage: `make docs-check`

- [ ] **AC-LPT-8:** `docs/hooks.md` "Releasing" carries the numbered runbook
  in R-LPT-4's order — the date rule, the tag only on a merge commit on
  production after `tag-ancestry`, nothing committed to production after the
  tag, and the post-release sweep among its steps — with the
  trusted-publisher sentence, and names no change package;
  `.claude/skills/planlint-release/SKILL.md` cites that section where it
  cited the deleted runbook, names the sweep as its last step, names no
  change package, invokes only real promotion subcommands, and backticks
  only paths that exist. The runbook is read directly. (R-LPT-4, R-LPT-13,
  DEC-LPT-006, DEC-LPT-012)
  _Verified by:_ `pytest -k "test_release_skill_uses_only_real_promotion_subcommands or test_path_like_backtick_references_resolve_to_real_files or test_docs_check_passes"` · stage: `make docs-check`

- [ ] **AC-LPT-9:** `docs/next-steps.md` carries R-LPT-5's edits — item 17
  with the distribution plan's deferrals, the non-goals sentence, items 4 and
  16 retired to one line each, item 24 re-scoped to its surviving condition,
  the "Retired documents" list with one archive pointer per document, and a
  nested-file count that names its command — and its rule-count phrase still
  matches the registry. The edits are read directly. (R-LPT-5, DEC-LPT-006,
  DEC-LPT-016)
  _Verified by:_ `pytest -k "test_total_rule_count_matches_every_prose_claim or test_docs_check_passes"` · stage: `make docs-check`

- [ ] **AC-LPT-10:** `README.md` says what `tests/test_agent_artifacts.py`
  validates, describes the archived suite without claiming a test holds the
  skill's refusal, describes the gate under "Dogfooding" with no package
  link, no count and the sweep rule, and keeps every required document's
  link and none to a deleted one; `llms.txt`, `docs/agents-skills-harness.md`,
  `SECURITY.md`, `docs/aqa.md`, `docs/architecture/c4.md` and
  `docs/hooks.md` carry R-LPT-6's edits, each pointer in R-LPT-3's form;
  every root markdown file is still wired into the docs gate; and both
  harness indexes name every agent and skill. The prose is read directly.
  (R-LPT-3, R-LPT-6, R-LPT-13, DEC-LPT-008, DEC-LPT-012)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_agent_index_links_resolve or test_harness_docs_list_every_agent_and_skill or test_every_root_markdown_file_is_wired_into_the_docs_gate"` · stage: `make docs-check`

- [ ] **AC-LPT-11:** `context7.json` indexes the skill and excludes only
  folders and files that exist, `evals` not among them; `.dockerignore`
  still keeps every agent artifact out of the build context; the hook nudges
  each documented file class and has no arm for `evals/`, and `docs/hooks.md`
  mentions every remedy the hook points at; and each configuration line of
  R-LPT-7 states nothing about a deleted path, which is read directly.
  (R-LPT-7, R-LPT-8, DEC-LPT-019)
  _Verified by:_ `pytest -k "test_context7_config_is_valid_and_its_folders_exist or test_agent_artifacts_are_excluded_from_the_docker_context or test_each_documented_file_class_is_nudged or test_docs_list_every_hook_case_the_script_implements"` · stage: `make test`

- [ ] **AC-LPT-12:** No agent or skill file under `.claude/` names a change
  package; the drafter, the adversary and the change-package skill say to
  read the open packages in full and put worked examples behind archive
  URLs; `openspec/project.md` lists the area codes the deleted packages
  declared, and the drafter's collision check reads that line; every
  backticked path in `.claude/` prose resolves and every cited target is
  real. The names, the list and the collision check are read directly.
  (R-LPT-8, DEC-LPT-010)
  _Verified by:_ `pytest -k "test_path_like_backtick_references_resolve_to_real_files or test_make_target_references_are_real_makefile_targets or test_harness_docs_list_every_agent_and_skill"` · stage: `make test`

- [ ] **AC-LPT-13 (non-success):** With no test naming a change package, the
  real-tree spec-status tests pass on the merged tree and each refuses an
  empty scope — the header-agreement test fails when it compared no spec, and
  the row test fails when it found no row — and a planted
  `openspec/changes/` holding no package makes the report exit 2, so a sweep
  that emptied the directory is refused rather than passed on nothing.
  (R-LPT-9, R-LPT-13, DEC-LPT-011, DEC-LPT-012)
  _Verified by:_ `pytest -k "test_spec_status_runs_over_this_repository or test_the_header_reader_agrees_with_parse_spec_on_every_uncommented_real_header or test_spec_status_exits_two_when_it_cannot_run"` · stage: `make test`

- [ ] **AC-LPT-14:** `tests/test_agent_artifacts.py` collects on a tree
  without `evals/` and holds the retrieval config and the agent indexes;
  `tests/test_spec_test_citations.py` is byte-identical to the base, its
  floor holds over the specs that remain and every selector in them
  resolves; and the rule-count test passes without the roadmap's row. The
  unchanged bytes are read against the base. (R-LPT-9, C-LPT-5, DEC-LPT-018)
  _Verified by:_ `pytest -k "test_the_spec_corpus_actually_contains_citations or test_every_spec_test_citation_resolves_to_a_real_test or test_total_rule_count_matches_every_prose_claim or test_context7_config_is_valid_and_its_folders_exist"` · stage: `make test`

- [ ] **AC-LPT-15:** On the merged tree `make spec-status` prints one row per
  package under `openspec/changes/` and none for a deleted package; the
  reports table still has a row for every report target and its section
  still names `settle-package-status-headers`; and the sentences R-LPT-14
  names state the report's exit as it is on the merged tree, any figure in
  them dated with its commit. The sentences and the report's output are read
  directly, the output recorded in `tasks.md`. (R-LPT-14, DEC-LPT-016)
  _Verified by:_ `pytest -k "test_every_report_target_has_a_row_in_the_hooks_reports_table or test_spec_status_runs_over_this_repository"` · stage: `make test`

- [ ] **AC-LPT-16:** `CHANGELOG.md`'s `[Unreleased]` section carries
  `### Removed — the development record` with this package's bold backticked
  bullet naming what R-LPT-15 lists, the package set described by its rule
  and command and by no count; no released section changed; and every
  versioned section still links to its release tag. The entry is read
  directly. (R-LPT-2, R-LPT-15, C-LPT-4)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [ ] **AC-LPT-17:** `add-witness-ci-artifacts` names no deleted path, each of
  its amended clauses carries the "(amended by `lean-production-tree`)"
  marker, and its refusal clause keeps `SKILL.md`'s sentence verbatim; the
  requirements, decisions and criteria of `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` are unchanged against the base; every spec
  under `openspec/changes/` validates clean at `--fail-on INFO`; and the
  graph diff against the base reports no new broken link and no new orphan
  requirement. The amendment and the unchanged text are read against the
  base; the validation and the graph diff are recorded in `tasks.md`.
  (R-LPT-16, C-LPT-4, DEC-LPT-006, DEC-LPT-007)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-LPT-18:** The rule inventory, the golden validate, graph and rules
  hashes and the empty runtime-dependency list are unchanged, and the diff
  touches no file under `openspec_graph/` or `.github/workflows/` and not the
  `Makefile`; the paths are read against the base. (C-LPT-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [ ] **AC-LPT-19:** Every code comment and docstring that attributes a fact
  to a deleted document or package is unchanged, and every one that stated a
  present fact about a deleted path is corrected, each named by file in
  `tasks.md`. Read directly against the diff and the cross-check recorded in
  `tasks.md`. (C-LPT-2, DEC-LPT-020)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-LPT-20:** The whole ladder is green on the merged tree, this
  repository's own validate over every package included; this spec pins no
  count; and every measurement in `tasks.md` is dated with its commit and
  names its command. A review property, read directly; the ladder confirms
  the package validates clean. (C-LPT-3, DEC-LPT-018)
  _Verified by:_ stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Preconditions | none — owner actions recorded in `tasks.md` Milestone 2 | `v0.3.0` on PyPI and back-merged into `dev`; `archive/dev-record-2026-10` on origin at the implementation branch's base, recorded with `git ls-remote --tags origin 'archive/*'`; no deleted path changed on `dev` since the tag (DEC-LPT-017) |
| Focused | `make test` | AC-LPT-1..6, AC-LPT-11..16, AC-LPT-18 — the hygiene module green on the real tree and red on its planted cases, the retuned tests green with no package named, every guard this change leans on still green |
| Docs | `make docs-check` | AC-LPT-7..10 — the moved runbook, the rewritten conventions and pointers, every required document present and linked |
| Full | `make pre-pr` | AC-LPT-17, AC-LPT-19, AC-LPT-20 — the ladder, including this repository's own validate over every package and the typecheck ratchets |
