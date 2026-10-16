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
`docs/next-steps.md` — a sweep rule keeps the tree from refilling, and a new
test holds the tree to both.

**Evidence:** measured at `c0ff090` (the merge of PR #57 into `dev`, the base
of `claude/lean-production-tree`), 2026-10-15. Every figure, with the command
that produced it, is in `tasks.md`; this proposal states none
(`docs/policies.md`, "Count cites a command").

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR`: exit 0, no finding at any severity.
- **The deleted package set, by its rule.** `ls openspec/changes | grep -v -e
  '^add-witness-ci-artifacts$' -e '^widen-indeterminate-unchecked-citations$'
  -e '^prepare-release-0-3-0$' -e '^adopt-branch-promotion-model$'` lists it.
  Of the packages that stay, `add-witness-ci-artifacts` and
  `widen-indeterminate-unchecked-citations` are drafted and unimplemented —
  no criterion ticked, no milestone `[DONE]`, and `openspec_graph/cli.py` has
  no `--witness-dir` — while `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` carry the 0.3.0 release's own record, which
  the runbook writes after the tag.
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
  `"invariant_source": null`, and no path in `INVARIANT_SOURCES` or
  `ADR_SOURCES` (`openspec_graph/detect.py:64-86`) exists.
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
- **Edits that must land together.** Each pair is red if one half lands
  alone: `.dockerignore:52` and `tests/test_release_surface.py:223`; the
  hook's `*/evals/*` arm (`.claude/hooks/nudge_rule_registry.sh:58-61`) and
  `tests/test_claude_hooks.py:49`; the literal `settle-package-status-headers`
  in `docs/hooks.md`'s reports section and `tests/test_ci_makefile.py:456-484`;
  the eval-case skill's directory and its name in `docs/hooks.md:277` and
  `docs/agents-skills-harness.md:6`, which
  `test_harness_docs_list_every_agent_and_skill`
  (`tests/test_agent_skill_docs.py:557-570`) reads; `evals/AGENTS.md` and every
  sentence that counts nested `AGENTS.md` files.
- **Dangling references, cross-checked.** The session's scratch list of
  references the deletion leaves dangling, the session plan's edit list, a
  `git grep` of the surviving files and a one-off read-only simulation of
  R-LPT-11's scanner agree, except for the files the plan does not name;
  `tasks.md` lists them and adds each to a milestone.
- **Kept packages that require a deleted file.** `add-witness-ci-artifacts`'
  R-WCA-33 and AC-WCA-29 list `docs/differentiation-roadmap.md` and
  `docs/peer-review-2026-09.md` among the documents that "MUST move", and
  R-WCA-33 and AC-WCA-30 require `evals/fabricate-witness/` byte-identical;
  `prepare-release-0-3-0`'s R-REL-11, AC-REL-16 and DEC-REL-008 place the
  runbook in `docs/distribution-plan.md` §3; `adopt-branch-promotion-model`'s
  R-BPM-14 requires that runbook to tag only a merge commit on production.
- **The skill's refusal is held by prose.** A `grep` of `tests/` for
  `SKILL.md`'s "make a finding disappear" and "Never run `witness` yourself"
  finds nothing; `tests/test_skill_contract.py` holds the read-only verbs and
  the exit-code messages. The eval cases were the only evidence that the
  skill refuses, and no CI job ran them.
- **`make spec-status` goes green on the lean tree.** `docs/hooks.md`'s
  reports row and paragraph (`:163`, `:171-173`), `docs/aqa.md:221-222` and
  `docs/next-steps.md:374` say it stays red until
  `settle-package-status-headers` lands; on the simulated tree it has no
  finding.
- **Nothing reacts to a non-`v*` tag.** `release.yml` triggers on tags
  matching `v*` (`:16-17`); the promotion guard's `TAG_REF` matches `v` and a
  digit (`.claude/hooks/guard_promotion.py:63`); `tools/check_promotion.py
  tag-ancestry` takes a sha.
- **Sequencing.** `docs/next-steps.md`, "After the first public tag (0.3.0)":
  nothing on that list starts before `v0.3.0` is tagged and `pip install
  planlint` resolves. At drafting the tag had not been pushed (the session
  plan's progress table, 2026-10-15); `tasks.md` Milestone 2 checks it before
  any deletion.

## What Changes

- **Deleted** (`git rm -r`, Milestone 6): `docs/agent-directory-wiring-plan.md`,
  `docs/distribution-plan.md`, `docs/eval-corpus-plan.md`,
  `docs/reflection-plan-2026-10.md`, `docs/peer-review-2026-09.md`,
  `docs/peer-review-2026-10.md` and `docs/differentiation-roadmap.md`; the
  whole of `evals/`; `.claude/skills/planlint-add-eval-case/`; and every
  directory under `openspec/changes/` at the archive tag except
  `add-witness-ci-artifacts`, `widen-indeterminate-unchecked-citations`,
  `prepare-release-0-3-0` and `adopt-branch-promotion-model`.
  `openspec/AGENTS.md`, `openspec/project.md` and `openspec/specgraph.json`
  stay.
- **The archive tag** `archive/dev-record-2026-10`, annotated, pushed by the
  owner on the `dev` commit the implementation branch is cut from, before any
  deletion (Milestone 2). Every pointer to a deleted path is
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/<path>`.
- **`docs/hooks.md`** — "Releasing", heading kept, gains the numbered release
  runbook from `docs/distribution-plan.md` §3 with the date rule carried in
  substance, the post-release sweep as its last step, and one sentence
  binding the trusted publisher to `release.yml` and the environment `pypi`;
  its checklist paragraph names no package. The reports row and the
  paragraph under the table state what `make spec-status` does on the lean
  tree and keep the literal `settle-package-status-headers`. The hook bullet
  for edits under `evals/` and the eval-case skill in the skill list go.
- **`docs/next-steps.md`** — item 17 absorbs the distribution plan's
  deferrals (§5) less the suite's rows; one sentence under "Deferred / out of
  scope" carries its non-goals (§6); every line naming a deleted document
  drops the path or carries the archive pointer; items 4 and 16 are retired
  to one line each; item 24 is re-scoped to its surviving condition and its
  exit sentence corrected; the nested-file count names its command; a
  "Retired documents" list names each deleted document once.
- **`docs/AGENTS.md`** (prose and diagram) and the comment above
  `docs/policies.md` in **`tools/check_docs.py`** — a plan is a change
  package; a planning document that is not one is not tracked; the archive
  tag holds the last ones.
- **`README.md`** — what `tests/test_agent_artifacts.py` validates; the
  evaluation paragraph becomes an archived-suite sentence that claims only
  what `tests/test_skill_contract.py` holds; "Dogfooding" with no package
  link, no count and the sweep rule; the documentation list loses the deleted
  documents' rows and the suite's and keeps every `REQUIRED_DOCS` link.
- **`llms.txt`**, **`context7.json`**, **`docs/agents-skills-harness.md`**,
  **`SECURITY.md`**, **`docs/aqa.md`**, **`docs/architecture/c4.md`** — each
  line that names a deleted path, counts nested `AGENTS.md` files, or claims
  something about the suite or the spec-status exit.
- **Configuration comments and lists** — `.gitignore`, `.dockerignore`,
  `.gitleaks.toml`, `pyproject.toml`, `.github/dependabot.yml`.
- **`.claude/`** — kept. The `*/evals/*` hook arm goes; the drafter, the
  adversary and the change-package skill say to read the open packages under
  `openspec/changes/` in full, with worked examples behind archive URLs; the
  drafter's area-code check also reads a new retired-codes line in
  **`openspec/project.md`**; the release skill cites `docs/hooks.md`
  "Releasing" and names the sweep; the add-rule skill and the verifier drop
  their deleted paths.
- **Tests** — `tests/test_spec_status.py` drops `THIS_PACKAGE` and keeps its
  non-vacuity floors; `tests/test_agent_artifacts.py` drops the evals section
  and renames its context7 test; `tests/test_release_surface.py`,
  `tests/test_claude_hooks.py`, `tests/test_rule_registry_docs.py` and
  `tests/test_adopter_urls.py` drop their `evals` or roadmap entries; the git
  enumeration moves into `tests/support.py`; the mypy ceilings follow the
  deletions down. New **`tests/test_tree_hygiene.py`**: a shape check, a
  reference check over the shipped prose with a generic archive exemption,
  and planted cases.
- **`openspec/changes/add-witness-ci-artifacts/`** — the clauses that name a
  deleted path, amended in place and marked "(amended by
  `lean-production-tree`)".
- **`CHANGELOG.md`** `[Unreleased]` — `### Removed — the development record`,
  led by this package's bold backticked name.
- **No version bump and no code change.** The change lands on `dev` after
  `v0.3.0` is published and reaches `main` in 0.4.0. Its own header stays
  `DRAFT`; once its boxes are ticked `make spec-status` reads it as
  `draft-but-complete`, by design, until the maintainer settles it.

## Non-Goals

- **Not before `v0.3.0` is published.** Milestone 2 records the release, the
  back-merge and the archive tag before any deletion (DEC-LPT-017).
- **No release hardening and no 0.4.0 removals.** Build provenance, the
  automated GitHub release, `persist-credentials: false` on the release
  checkouts and `CODEOWNERS` are a later hardening package; dropping Python
  3.10, the `specgraph` alias and the Dockerfile is the 0.4.0 release
  package's. Neither is drafted here.
- **No owner settings.** Rulesets, the tag ruleset and the `pypi` environment
  are repository settings outside the tree; the archive tag is the owner's
  push, recorded in `tasks.md`, not a commit of this change.
- **No sweep of the 0.3.0 packages.** `prepare-release-0-3-0` and
  `adopt-branch-promotion-model` leave in the 0.4.0 post-release sweep, with
  this package (DEC-LPT-003).
- **No edit to a shipped record.** `CHANGELOG.md`'s released sections and the
  requirements, decisions and criteria of the 0.3.0 packages are unchanged;
  their runbook clauses are superseded by name (DEC-LPT-006).
- **No rewritten history comments.** A comment or docstring that says where a
  fact came from stays as written (C-LPT-2).
- **No code, rule, target or workflow change** (C-LPT-1), and **no retune of
  `tests/test_spec_test_citations.py`** (C-LPT-5).
- **No move of `evals/`.** It is withdrawn and archived at the tag, and is
  restored only when a headless, deterministic runner exists (DEC-LPT-008).
- **No archive support in the tool.** The archive is a tag, not a directory;
  `detect` and `tools/spec_status.py` read only the open packages.
- **No mechanical guard on package names in agent prose.** The hygiene module
  reads paths; names are read in review (DEC-LPT-010).
- **No test for the skill's refusal.** Its absence is the suite's named cost
  (DEC-LPT-008), not repaired here.

## Affected Capabilities

- `production-tree`
