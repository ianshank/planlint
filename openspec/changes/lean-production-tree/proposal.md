# Change: A Lean Production Tree — the Development Record Leaves the Tree, an Archive Tag Keeps It

## Why

`main` is the production branch of the `dev → qa → main` model
(`docs/hooks.md`, "Branching and promotion"), and what an adopter fetches from
it is the whole tree at a tag. The composite Action installs the CLI from a
copy of its own checkout — a `shutil.copytree` of
`$GITHUB_ACTION_PATH/../../..` (`.github/actions/planlint/action.yml:195-205`)
— and the plugin marketplace installs from the repository root
(`.claude-plugin/marketplace.json`, `"source": "./"`). Most of that tree is the
development record rather than the product: planning documents and peer
reviews of work that has shipped, a roadmap that calls itself a plan, an
evaluation suite nothing runs, and a change package for every piece of
shipped work. Each was kept for a reason that no longer holds.

- **Plans are "retired" by being kept.** `docs/AGENTS.md:31-33` leaves a
  `*-plan.md` ungated because it "is written to be executed and then
  retired", its diagram (`:13`) says the same of `peer-review-*.md`, and the
  comment above `docs/policies.md` in `tools/check_docs.py:24-28` repeats the
  reason (`write-down-policies`' DEC-POL-008). Nothing retires one.
- **The roadmap says what it is.** `docs/differentiation-roadmap.md:1-4`:
  "Planning artifact. Not implementation." Its comparison already lives in
  `README.md`, "Why this and not Spec-Kit / GitHub Spec / Kiro / Cursor".
- **The evaluation suite has no runner.** `docs/next-steps.md` item 16: no job
  runs the cases under `evals/`, `claude plugin eval` needs a plugin runtime
  CI does not have, and the suite "stays a manual pre-release check"; item
  4's one real run never happened. Its only gate is the structural half of
  `tests/test_agent_artifacts.py`, and `.claude/skills/planlint-add-eval-case/`
  only edits it.
- **Shipped packages are kept as the record.** DEC-MCO-006
  (`measure-coverage-once`) and DEC-TSS-016 (`shape-the-test-suite`)
  supersede shipped records by name and edit none, on the premise that a
  shipped package is a record of what shipped and is not edited. The record
  they protect already lives outside the tree's working set: in
  `CHANGELOG.md`, the dated record `docs/policies.md` ("Count cites a
  command") exempts for that reason, and in git history.
- **A test pins a transient package.** `tests/test_spec_status.py:40` sets
  `THIS_PACKAGE = "report-dead-code-and-spec-status"` and asserts on it at
  `:289` and `:502`, so that package cannot leave the tree without a red
  suite.
- **Agent prose names packages.** `.claude/agents/spec-drafter.md:7` and
  `.claude/agents/spec-adversary.md:7,24` point at `add-witness-mode` as the
  worked example, and `.claude/skills/planlint-release/SKILL.md:18` sends the
  release agent to `adopt-branch-promotion-model`. A sweep would leave each
  pointing at nothing.

This change deletes the record from the tree and keeps it one name away: an
annotated tag, `archive/dev-record-2026-10`, pins the last `dev` tree that
carried it, and every pointer to a deleted path is a URL under that tag. What
is still needed moves before its file goes — the release runbook into
`docs/hooks.md` "Releasing", the distribution plan's deferrals into
`docs/next-steps.md` — a cumulative sweep rule keeps the tree from refilling,
and a new test holds the tree to both.

**Evidence:** measured at `c0ff090` (the merge of PR #57 into `dev`, the base
of `claude/lean-production-tree`), 2026-10-15, and re-checked at `04d1622`
and `122fa09` (this package's first and second drafts), 2026-10-16, for the
adversarial reviews' findings. Every figure, with the command that produced
it, is in `tasks.md`; the one this proposal repeats names its commit and its
command where it appears (`docs/policies.md`, "Count cites a command").

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR`: exit 0, no finding at any severity.
- **The deleted package set, by its rule.** Every package whose work had
  shipped by v0.3.0 — read from its surface in the tree and a CHANGELOG
  entry, never from its Status header — except the packages that carry the
  0.3.0 release's own record (R-LPT-2). Once the deletion exists,
  `git diff --name-only --diff-filter=D archive/dev-record-2026-10 HEAD -- openspec/changes | cut -d/ -f3 | sort -u`
  lists it. At `c0ff090`, before the tag and before this package existed,
  the same set was `ls openspec/changes | grep -v -e
  '^add-witness-ci-artifacts$' -e '^widen-indeterminate-unchecked-citations$'
  -e '^prepare-release-0-3-0$' -e '^adopt-branch-promotion-model$'`.
  Of the packages that stay, `add-witness-ci-artifacts` and
  `widen-indeterminate-unchecked-citations` are drafted and unimplemented —
  no criterion ticked, no milestone `[DONE]`, `openspec_graph/cli.py` has no
  `--witness-dir`, and no file under `openspec_graph/` or
  `.github/actions/` names the `unchecked-citations` cause — while
  `prepare-release-0-3-0` and `adopt-branch-promotion-model` carry the 0.3.0
  release's own record, which the runbook writes after the tag.
- **`dev` keeps moving.** This change waits on a release while `dev` takes
  other work, so the kept set is a rule rather than the four names it held
  at `c0ff090`: a package added since is listed by
  `git diff --name-only --diff-filter=A c0ff090 <X> -- openspec/changes`
  and classified by the same evidence before anything is deleted (`tasks.md`
  Milestones 0 and 2).
- **A simulated lean tree passes every gate it can run.** A scratch export of
  `HEAD` with the deletions applied validates clean at `--fail-on INFO`,
  graphs with no broken link, passes `tools/diff_spec_graph.py` against the
  real tree's graph with no new orphan requirement, gives
  `tools/spec_status.py` no finding, and passes `tools/check_docs.py`.
- **The citation floor needs no retune.** The kept specs alone carry more
  selector tokens than the absolute floor of
  `test_the_spec_corpus_actually_contains_citations`
  (`tests/test_spec_test_citations.py:77-84`) requires.
- **G006 and G009 cannot fire.** `openspec/specgraph.json` has
  `"invariant_source": null`; of the paths in `INVARIANT_SOURCES` and
  `ADR_SOURCES` (`openspec_graph/detect.py:64-86`) only the root `AGENTS.md`
  exists, and it carries no `INV-n` id
  (`test_agents_md_declares_no_invariant_ids`), so detection selects none.
- **What breaks before the retunes.** On the lean tree
  `tests/test_agent_artifacts.py` errors at collection on `EVAL_CASES`
  (`:83`, an `iterdir` of `evals/`), and that error hides further failures in
  the module: `test_context7_config_is_valid_and_its_folders_exist`
  (`:313-331`, every `excludeFolders` and `excludeFiles` entry must exist)
  and `test_agent_index_links_resolve` over `llms.txt` (its roadmap link,
  `llms.txt:38`). Beside them: `tests/test_spec_status.py` at each
  `THIS_PACKAGE` site; `tests/test_rule_registry_docs.py:69`, the roadmap's
  rule-count row; and `test_path_like_backtick_references_resolve_to_real_files`
  over the `.claude/` files that backtick a deleted path
  (`spec-drafter.md`, `planlint-add-rule`, `planlint-change-package`,
  `planlint-release`).
- **Under `.claude/` and `skills/` only a URL can point at a deleted path.**
  `_PATH_LIKE` (`tests/test_agent_skill_docs.py:78`) reads every backticked
  repository path in `.claude/agents`, `.claude/skills` and `skills/`
  (`ALL_FILES`, `:42-46`) and fails on one that does not resolve, whatever
  stands beside it; a backticked `https://` span carries a `:` its pattern
  does not admit.
- **The precedent check would go blind.** `.claude/agents/spec-adversary.md:13`
  greps only `openspec/changes/*/specs/*/spec.md` for prior decisions, and
  its own examples, `DEC-AD-008` and `DEC-WM-004`, are declared in
  `add-architecture-drift-lint` and `add-witness-mode`, which this change
  deletes. The adversary has `Bash` (`:4`), so it can read the tag.
- **Edits that must land together.** Each couple goes red in one direction
  only — one half landing alone fails a test, the other alone does not — so
  the failing half sets the order: `.dockerignore:52` losing `evals` before
  `tests/test_release_surface.py:223` does; the hook's `*/evals/*` arm
  (`.claude/hooks/nudge_rule_registry.sh:58-61`) leaving before the
  `tests/test_claude_hooks.py:49` entry; the literal
  `settle-package-status-headers` leaving `docs/hooks.md`'s reports section,
  which `tests/test_ci_makefile.py:456-484` reads; the eval-case skill's name
  leaving `docs/hooks.md:277` or `docs/agents-skills-harness.md:6`, which
  `test_harness_docs_list_every_agent_and_skill`
  (`tests/test_agent_skill_docs.py:557-570`) reads, while its directory
  exists. `evals` in `tests/test_adopter_urls.py`'s `_EXCLUDED_DIRS` is green
  in either order, and `evals/AGENTS.md` with every sentence that counts
  nested `AGENTS.md` files is a couple for truth, not for a test.
- **Dangling references, cross-checked.** The session's scratch list of
  references the deletion leaves dangling, the session plan's edit list, a
  `git grep` of the surviving files and a one-off read-only simulation of
  R-LPT-11's scanner agree, except for the files the plan does not name;
  `tasks.md` lists them and adds each to a milestone. Re-run over the
  scanner's widened scope — every root markdown file but `CHANGELOG.md`, and
  the markdown under `.github/` — the simulation adds `SECURITY.md:48`, which
  backticks the 2026-09 review, and finds `.github/pull_request_template.md`
  clean. No archive URL appears in the shipped prose yet, so none is wrapped
  across lines.
- **Kept packages that require a deleted file.** `add-witness-ci-artifacts`'
  R-WCA-33 and AC-WCA-29 list `docs/differentiation-roadmap.md` and
  `docs/peer-review-2026-09.md` among the documents that "MUST move", its
  R-WCA-33 and AC-WCA-30 require `evals/fabricate-witness/` byte-identical,
  and its proposal (`:194-200`), `tasks.md` (`:135-143`) and DEC-WCA-022
  re-point `add-finding-line-hits`' AC-GA-29, a package this change deletes.
  `widen-indeterminate-unchecked-citations`' C-IND-7 says
  `docs/peer-review-2026-09.md`, `docs/peer-review-2026-10.md` and
  `docs/differentiation-roadmap.md` "MUST move in the same change", its
  `tasks.md:249-260` edits lines in all three, and its proposal's "Docs and
  contracts that move together" bullet (`:208-215`) matches.
  `prepare-release-0-3-0`'s R-REL-11, AC-REL-16 and DEC-REL-008 place the
  runbook in `docs/distribution-plan.md` §3, and its record step re-runs that
  file's §0 rows; `adopt-branch-promotion-model`'s R-BPM-14 requires that
  runbook to tag only a merge commit on production.
- **A shipped package still carries open owner actions.**
  `adopt-branch-promotion-model/tasks.md:164-190` leaves the first
  promotion's record, the rulesets with the `v*` tag ruleset, and the first
  refused pull request unticked. A sweep that deleted the package without
  moving them would leave them only at a tag, and a rule keyed to "the
  release that ships it" would never remove the package at all, since its
  release's sweep is already past.
- **The skill's refusal is held by prose.** A `grep` of `tests/` for
  `SKILL.md`'s "make a finding disappear" and "Never run `witness` yourself"
  finds nothing; `tests/test_skill_contract.py` holds the read-only verbs and
  the exit-code messages. The eval cases were the only evidence that the
  skill refuses, and no CI job ran them.
- **`make spec-status` is green on the lean tree only while no kept package
  is complete.** `docs/hooks.md`'s reports row and paragraph (`:163`,
  `:171-173`), `docs/aqa.md:221-222`, `docs/next-steps.md:374` and the
  docstring of `test_every_report_target_has_a_row_in_the_hooks_reports_table`
  (`tests/test_ci_makefile.py:478-480`) say it stays red until
  `settle-package-status-headers` lands. On the tree simulated at `c0ff090`
  it had no finding — with `prepare-release-0-3-0` at 19 of 24 criteria and
  2 of 3 milestones (`python tools/spec_status.py`, the same at `122fa09`).
  The 0.3.0 record ticks the rest (`prepare-release-0-3-0/tasks.md:357-361`),
  after which the report reads that package `draft-but-complete` and exits
  1, as the second review executed. Neither "stays red" nor "exits 0" holds
  in both states; R-LPT-14's conditional sentence does, and item 24's
  conditions (a) and (b) still bind on the shipped packages in the tree.
- **`openspec/project.md` is regenerated, `openspec/AGENTS.md` is not.**
  `planlint init --force` rewrites `openspec/project.md` from
  `scaffold.plan_init` (`openspec_graph/scaffold.py:99-150`), whose text since
  `fix-init-snapshot-wording` calls the file a snapshot; the copy in this tree
  still says it "is authoritative". `openspec/AGENTS.md` is hand-written and
  held by the nested-file contracts in `tests/test_agent_artifacts.py`,
  within `MAX_NESTED_LINES`.
- **Nothing reacts to a non-`v*` tag, and no ruleset protects one.**
  `release.yml` triggers on tags matching `v*` (`:16-17`); the promotion
  guard's `TAG_REF` matches `v` and a digit
  (`.claude/hooks/guard_promotion.py:63`); `tools/check_promotion.py
  tag-ancestry` takes a sha. `gh api repos/ianshank/planlint/rulesets`
  returns no ruleset, and the tag ruleset `adopt-branch-promotion-model`'s
  owner actions plan covers `v*` with the owner as its bypass.
- **Sequencing.** `docs/next-steps.md`, "After the first public tag (0.3.0)":
  nothing on that list starts before `v0.3.0` is tagged and `pip install
  planlint` resolves. At `04d1622` origin carries no `v0.3.0` tag and PyPI's
  JSON API has no 0.3.0 release; pull request #58, which carries this
  package into `dev`, is a GitHub draft. `tasks.md` Milestone 2 gates on all
  of it before any deletion.

## What Changes

- **Deleted** (`git rm -r`, Milestone 6): `docs/agent-directory-wiring-plan.md`,
  `docs/distribution-plan.md`, `docs/eval-corpus-plan.md`,
  `docs/reflection-plan-2026-10.md`, `docs/peer-review-2026-09.md`,
  `docs/peer-review-2026-10.md` and `docs/differentiation-roadmap.md`; the
  whole of `evals/`; `.claude/skills/planlint-add-eval-case/`; and every
  package directory under `openspec/changes/` at the archive tag whose work
  had shipped by v0.3.0, except the 0.3.0 release's own record packages —
  so every package but `add-witness-ci-artifacts`,
  `widen-indeterminate-unchecked-citations`, `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` at `c0ff090`, and no package added since
  that has not shipped. `openspec/AGENTS.md`, `openspec/project.md` and
  `openspec/specgraph.json` stay.
- **The archive tag** `archive/dev-record-2026-10`, annotated, pushed by the
  owner on X, the `dev` tip once the 0.3.0 record has merged, which then
  becomes the implementation branch's merge base when the branch merges
  `origin/dev` — before any deletion (Milestone 2). Every pointer to a
  deleted path is
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/<path>`:
  a link's target, or the URL on the same line as a backticked path, and
  under `.claude/` and `skills/` the backticked URL alone.
- **`docs/hooks.md`** — "Releasing", heading kept, gains the numbered release
  runbook from `docs/distribution-plan.md` §3 with the date rule carried in
  substance, the cumulative post-release sweep as its last step — every
  package shipped by that release or an earlier one leaves once its
  `tasks.md` records the release, its open owner actions moving to
  `docs/next-steps.md` — and one sentence binding the trusted publisher to
  `release.yml` and the environment `pypi`; its checklist paragraph names no
  package. The reports row and the paragraph under the table state what
  `make spec-status` does on the lean tree — the outcome measured at X, and
  the condition that turns it red — and keep the literal
  `settle-package-status-headers`. The hook bullet for edits under `evals/`
  and the eval-case skill in the skill list go.
- **`docs/next-steps.md`** — item 17 absorbs the distribution plan's
  deferrals (§5) less the suite's rows; one sentence under "Deferred / out of
  scope" carries its non-goals (§6); every line naming a deleted document
  drops the path or carries the archive pointer, a link's target replaced
  rather than annotated; items 4 and 16 are retired to one line each; item 24
  keeps conditions (a) and (b) for the shipped packages still in the tree
  and condition (c) outright, with its exit sentence corrected; each
  nested-file count names its command; a "Retired documents" list names each
  deleted document once.
- **`docs/AGENTS.md`** (prose and diagram) and the comment above
  `docs/policies.md` in **`tools/check_docs.py`** — a plan is a change
  package; a planning document that is not one is not tracked; the archive
  tag holds the last ones.
- **`README.md`** — what `tests/test_agent_artifacts.py` validates; the
  evaluation paragraph becomes an archived-suite sentence that claims only
  what `tests/test_skill_contract.py` holds; "Dogfooding" with no package
  link, no count and the cumulative sweep rule; the documentation list loses
  the deleted documents' rows and the suite's and keeps every
  `REQUIRED_DOCS` link.
- **`llms.txt`**, **`context7.json`**, **`docs/agents-skills-harness.md`**,
  **`SECURITY.md`**, **`docs/aqa.md`**, **`docs/architecture/c4.md`** — each
  line that names a deleted path, counts nested `AGENTS.md` files, or claims
  something about the suite or the spec-status exit.
- **Configuration comments and lists** — `.gitignore`, `.dockerignore`,
  `.gitleaks.toml` and `pyproject.toml`, where a line states a present fact
  about a deleted path or package. `.github/dependabot.yml`'s comment that an
  earlier attribution to the distribution plan was wrong is history, and
  stays (C-LPT-2).
- **`.claude/`** — kept. The `*/evals/*` hook arm goes; the drafter, the
  adversary and the change-package skill say to read the open packages under
  `openspec/changes/` in full, with worked examples behind archive URLs as
  backticked `https://` spans; the adversary's precedent step also greps the
  archive tag's specs with `git grep` and cites its examples by archive URL;
  the drafter's area-code check also reads a new retired-codes entry in
  **`openspec/AGENTS.md`** — the codes the deleted packages and the deleted
  roadmap declared, never one an open package declares — kept within that
  file's line bound with its precedence line and diagram intact;
  `openspec/project.md` is not edited. The release skill cites `docs/hooks.md`
  "Releasing" and names the sweep; the add-rule skill and the verifier drop
  their deleted paths.
- **Tests** — `tests/test_spec_status.py` drops `THIS_PACKAGE` and keeps its
  non-vacuity floors; `tests/test_agent_artifacts.py` drops the evals section
  with the helpers only it calls, renames its context7 test and drops its
  nested-file count; `tests/test_release_surface.py`,
  `tests/test_claude_hooks.py`, `tests/test_rule_registry_docs.py` and
  `tests/test_adopter_urls.py` drop their `evals` or roadmap entries;
  `tests/test_ci_makefile.py`'s reports docstring follows the rewritten
  section; the git enumeration moves into `tests/support.py`, drops paths
  not on disk, and is held to contain `README.md`; the mypy ceilings follow
  the deletions down. New **`tests/test_tree_hygiene.py`**: a shape check; a
  reference check over the shipped prose — every root markdown file but
  `CHANGELOG.md`, the agent indexes, and the markdown under `docs/`,
  `skills/`, `.claude/` and `.github/` — in which a link is never exempt and
  a backticked path is exempt only beside its own archive URL, read outside
  HTML comments, a trailing `/` ignored and a sentence's full stop allowed
  after it; and planted cases for both directions.
- **`openspec/changes/add-witness-ci-artifacts/`** and
  **`openspec/changes/widen-indeterminate-unchecked-citations/`** — every
  clause that requires an edit to, or the preservation of, a deleted path,
  amended in place and marked "(amended by `lean-production-tree`)"; the
  evidence that cites one stays as written (DEC-LPT-007).
- **`CHANGELOG.md`** `[Unreleased]` — `### Removed — the development record`,
  led by this package's bold backticked name.
- **No version bump and no code change.** The change lands on `dev` after
  `v0.3.0` is published and reaches `main` in 0.4.0. Its own header stays
  `DRAFT`; once its boxes are ticked `make spec-status` reads it as
  `draft-but-complete`, by design, until the maintainer settles it.

## Non-Goals

- **Not before `v0.3.0` is published and its record is in `dev`.** Milestone
  2's gate records the tag, the PyPI release, the back-merge, the merged
  0.3.0 record, the packages added to `dev` since `c0ff090`, the
  spec-status report at X and the archive tag before any deletion. Pull
  request #58 carried this package alone into `dev`. The implementation is
  a new pull request branched from X, and it stays a draft until the gate
  is recorded (DEC-LPT-017).
- **No release hardening and no 0.4.0 removals.** Build provenance, the
  automated GitHub release, `persist-credentials: false` on the release
  checkouts and `CODEOWNERS` are a later hardening package; dropping Python
  3.10, the `specgraph` alias and the Dockerfile is the 0.4.0 release
  package's. Neither is drafted here.
- **No owner settings.** Rulesets — none exists at drafting — and the `pypi`
  environment are repository settings outside the tree; the archive tag is
  the owner's push, and the rulesets' state when it is pushed is recorded in
  `tasks.md`, not a commit of this change.
- **No 0.3.0 record in this change.** The release's record step writes the
  `tasks.md` entries and criteria ticks of `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` in its own pull request, merged before the
  archive tag (C-LPT-4).
- **No sweep here.** `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` leave by the cumulative sweep rule at the
  first post-release sweep after their record is in, their open owner
  actions moving to `docs/next-steps.md` then; this change schedules no
  sweep (DEC-LPT-003, DEC-LPT-012).
- **No green promise for `make spec-status`.** The report turns red whenever
  a package closes under a `DRAFT` header, the 0.3.0 packages included; this
  change states that condition and the outcome measured at X, and settling
  the headers stays `settle-package-status-headers`' work (DEC-LPT-016).
- **No edit to a shipped record.** `CHANGELOG.md`'s released sections and the
  text of the 0.3.0 packages are unchanged; their runbook clauses are
  superseded by name (DEC-LPT-006).
- **No rewritten evidence in the open packages.** The amendments touch only
  clauses that require an edit to or the preservation of a deleted path; a
  dated citation of one stays (DEC-LPT-007).
- **No rewritten history comments.** A comment or docstring that says where a
  fact came from stays as written (C-LPT-2).
- **No code, rule, target or workflow change** (C-LPT-1), and **no retune of
  `tests/test_spec_test_citations.py`** (C-LPT-5).
- **No move of `evals/`.** It is withdrawn and archived at the tag, and is
  restored only when a headless, deterministic runner exists (DEC-LPT-008).
- **No archive support in the tool.** The archive is a tag, not a directory;
  `detect` and `tools/spec_status.py` read only the open packages.
- **No check that an archive tag exists, and no wrapped URLs.** The scanner
  reads no file and runs no `git`, so a pointer's tag name is read in review,
  and a URL split across lines is out of its scope (DEC-LPT-014).
- **No mechanical guard on package names in agent prose.** The hygiene module
  reads paths; names are read in review (DEC-LPT-010).
- **No test for the skill's refusal.** Its absence is the suite's named cost
  (DEC-LPT-008), not repaired here.

## Affected Capabilities

- `production-tree`
