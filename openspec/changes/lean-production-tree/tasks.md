# Tasks: lean-production-tree

Drafted at `c0ff090` — the merge of PR #57 into `dev`, the base of
`claude/lean-production-tree` — on 2026-10-15, as Phase 1 of the session plan
for a lean production branch. That plan is not tracked (DEC-LPT-005); every
decision this package takes from it is restated in
`specs/production-tree/spec.md`. **This package must not merge before
`v0.3.0` is published** (Milestone 2, DEC-LPT-017). Every line number below
is re-read at the implementation branch's head before the milestone that uses
it; a sibling landing first may move a line without moving the fact. Every
number names the command that produced it.

## Measured at `c0ff090`

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR`: `54 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`, exit 0 —
  the session lead's run and the drafter's, before any file of this package
  existed.
- **The tree.** `git ls-files | wc -l` → 480;
  `git ls-files -z | xargs -0 cat | wc -c` → 4799963;
  `git ls-files '*/AGENTS.md' | wc -l` → 8; `ls -d openspec/changes/*/ | wc -l`
  → 53; R-LPT-2's listing before the deletion,
  `ls openspec/changes | grep -v -e '^add-witness-ci-artifacts$' -e '^widen-indeterminate-unchecked-citations$' -e '^prepare-release-0-3-0$' -e '^adopt-branch-promotion-model$' | wc -l`
  → 49.
- **Stage citations.** `python tools/stage_citations.py` (what
  `make stage-citations` runs): `54 spec(s); 16 stage(s) cited; 12 on a
  verification line; 6 of those invoked by no scanned workflow: ci,
  coverage-tools, security, thresholds, validate, wheel-check`.
- **The kept packages.** `grep -c '^- \[x\] \*\*AC-'` and
  `grep -c '^- \[ \] \*\*AC-'` over each spec, `grep -c '^## Milestone.*\[DONE\]'`
  and `grep -c '^## Milestone'` over each `tasks.md`:
  `add-witness-ci-artifacts` 0 ticked, 34 open, 0 of 10 milestones done;
  `widen-indeterminate-unchecked-citations` 0, 20, 0 of 6;
  `prepare-release-0-3-0` 19, 5, 2 of 3; `adopt-branch-promotion-model` 0, 36,
  0 of 8. Every header reads `DRAFT`. `grep -n "witness-dir"
  openspec_graph/cli.py` prints nothing.
- **Citation selectors in the kept specs.** `grep -c 'pytest -k'` per spec,
  in the order above: 12, 9, 15, 32. Tokens as
  `tests/test_spec_test_citations.py`'s `_PYTEST_CITATION` reads them, the
  boolean operators skipped (a one-off read-only count, not committed): 22,
  14, 31, 78 — 145 in all, against the absolute floor at
  `tests/test_spec_test_citations.py:77-84`. No retune (C-LPT-5).
- **Invariant and ADR sources.** `python -c "import json;
  print(json.load(open('openspec/specgraph.json'))['invariant_source'])"` →
  `None`; no path in `INVARIANT_SOURCES` or `ADR_SOURCES`
  (`openspec_graph/detect.py:64-86`) exists, so G006 and G009 cannot fire.
- **A simulated lean tree** (the session lead's, this session):
  `git archive HEAD | tar -x` into a scratch directory with the deletions
  applied — 266 files, 2459866 bytes; `planlint --target <sim> validate
  --fail-on INFO` → 4 spec(s), 0 / 0 / 0, exit 0; `planlint --target <sim>
  graph --format json` → 233 nodes, 319 edges, `broken_links` 0;
  `python tools/diff_spec_graph.py base.json head.json` → `PASS: broken_links
  0 -> 0, no new orphan requirements`, exit 0; `python tools/spec_status.py
  --root <sim>` → 4 packages, 0 findings, exit 0; `tools/check_docs.py` over
  the sim → exit 0. Re-derived read-only by the drafter: 254 files outside
  `openspec/changes/` survive the deletion set
  (`git ls-files | grep -vE '<deletion pattern>' | grep -vE '^openspec/changes/' | wc -l`),
  plus the kept packages' 12 files, is 266.
- **Tests that fail on the lean tree before the retunes** (the review,
  cross-checked here). `tests/test_agent_artifacts.py` errors at collection on
  `EVAL_CASES` (`:83`); behind that error, and not in the review's list,
  `test_context7_config_is_valid_and_its_folders_exist` (`:313-331`: `evals`,
  `docs/distribution-plan.md` and `docs/eval-corpus-plan.md` in
  `context7.json`) and `test_agent_index_links_resolve[llms.txt]`
  (`llms.txt:38`) fail too. `tests/test_spec_status.py` at `:40`, `:289` and
  `:502`; `tests/test_rule_registry_docs.py:69`;
  `test_path_like_backtick_references_resolve_to_real_files` over
  `.claude/agents/spec-drafter.md:7`,
  `.claude/skills/planlint-add-rule/SKILL.md:18`,
  `.claude/skills/planlint-change-package/SKILL.md:11` and
  `.claude/skills/planlint-release/SKILL.md:19,61`. Edit-order couples
  (DEC-LPT-019): `tests/test_release_surface.py:223` with `.dockerignore:52`;
  `tests/test_claude_hooks.py:49` with
  `.claude/hooks/nudge_rule_registry.sh:58-61`;
  `tests/test_ci_makefile.py:456-484` with `docs/hooks.md`'s reports section;
  and, not in the review's list, `test_harness_docs_list_every_agent_and_skill`
  (`tests/test_agent_skill_docs.py:557-570`) with
  `.claude/skills/planlint-add-eval-case/` against `docs/hooks.md:277` and
  `docs/agents-skills-harness.md:6`.
- **The reference scanner, simulated** (a one-off read-only script
  implementing R-LPT-11's tokens over the files that survive the deletion, not
  committed): 28 files in scope, 31 dangling tokens in 9 files —
  `.claude/agents/planlint-verifier.md:28`, `.claude/agents/spec-drafter.md:7`,
  `.claude/skills/planlint-add-rule/SKILL.md:18`,
  `.claude/skills/planlint-change-package/SKILL.md:11`,
  `.claude/skills/planlint-release/SKILL.md:19,61`,
  `README.md:500,516,521,558,560,563,565,573,576,579`,
  `docs/agents-skills-harness.md:140`, `docs/hooks.md:434`,
  `docs/next-steps.md:13,28,39,53,120,163,230,234,322,338,384` (`:53` twice:
  link and span), `llms.txt:38`. Each is in Milestone 4's or 5's list.
- **Dangling references, cross-checked.** The session lead's scratch list —
  68 lines across 30 files, by `wc -l` over it and
  `cut -d: -f1 | sort -u | wc -l` — against the session plan's edit list and
  against
  `git grep -nE "agent-directory-wiring-plan|distribution-plan|eval-corpus-plan|reflection-plan-2026-10|peer-review-2026-(09|10)|differentiation-roadmap|evals|planlint-add-eval-case|openspec/changes/[a-z0-9-]+"`
  over the surviving files. The scratch list misses `docs/next-steps.md:52-53`
  (a relative link), `.dockerignore:52`, `context7.json:14` and
  `README.md:579`, which the plan names. The plan misses these, added to the
  milestones below:
  - `.claude/skills/planlint-release/SKILL.md:18` names
    `adopt-branch-promotion-model` (R-LPT-8), and its second runbook citation
    is at `:61`, not `:55`;
  - `docs/hooks.md:421` names `prepare-release-0-3-0`, and `:434` cites
    `docs/distribution-plan.md` §3, inside the paragraph the runbook move
    rewrites;
  - `docs/aqa.md:221-222`, a second "stays red" sentence (R-LPT-14);
  - `docs/AGENTS.md:13`, the diagram node stating the ungated-plan
    convention, beside `:31-33`;
  - `docs/next-steps.md:385`, "Eight nested files", beside the link at `:384`;
  - `tests/test_release_surface.py:252`, a docstring saying `evals/` holds
    markdown (C-LPT-2: corrected);
  - `tests/test_adopter_urls.py:59`, `"evals"` in `_EXCLUDED_DIRS` (R-LPT-7);
  - `tests/test_graph.py:1-4` and `.claude/hooks/guard_promotion.py:2`,
    docstrings naming `add-graph-export` and `adopt-branch-promotion-model`
    (C-LPT-2: history, unchanged);
  - `tests/test_ledger.py:55`, a fixture path under
    `openspec/changes/add-waiver-ledger-and-inv-lints/` that is test data, not
    a reference — no edit;
  - the clauses of the kept packages that R-LPT-16 reconciles.
- **No test holds the skill's refusal.**
  `grep -rn "Never run .witness. yourself\|finding disappear\|without changing the fact" tests/`
  prints nothing (DEC-LPT-008).

## Milestone 0 — Grounding at the implementation branch's head

- Run the gate and record its exit code before the first edit outside this
  package: `planlint --target . validate --fail-on ERROR`.
- Re-run every measurement above at the head and record the figures beside
  the `c0ff090` ones, each with its commit.
- Re-run the cross-check `git grep` above and the package-name grep over the
  agent prose,
  `git grep -nwE "$(ls openspec/changes | grep -vE '\.(md|json)$' | paste -sd'|')" -- .claude skills AGENTS.md '*/AGENTS.md' llms.txt`;
  any hit outside Milestones 4 to 6 joins them, recorded here.
- Confirm `add-witness-ci-artifacts` is still unimplemented: no criterion
  ticked, and `grep -n "witness-dir" openspec_graph/cli.py` prints nothing.
  If it has been implemented, R-LPT-16's amendment changes shape: stop and
  re-read DEC-LPT-007.
- **Gate:** `make test`

## Milestone 1 — The change package

- `proposal.md`, `specs/production-tree/spec.md` and `tasks.md` written spec
  first; every criterion unticked; `Status: DRAFT`. Reviewed by
  `spec-adversary` before any edit outside this directory; each finding
  resolved by a decision and recorded here.
- AC-LPT-1 to AC-LPT-5 cite their stage only, because their tests do not
  exist yet; Milestone 7 adds the selectors (DEC-LPT-018).
- Record the exit codes of `planlint --target . validate --fail-on ERROR
  --change lean-production-tree`, of the unscoped run, and of
  `python -m pytest tests/test_spec_test_citations.py -q -p no:cacheprovider`.
- **Gate:** `make pre-pr`

## Milestone 2 — Preconditions, recorded before any deletion (owner)

- `v0.3.0` is published and back-merged: `git ls-remote --tags origin v0.3.0`
  prints the tag; `python -m pip index versions planlint` lists `0.3.0`;
  `git merge-base --is-ancestor 'v0.3.0^{commit}' origin/dev` exits 0. Record
  all three. Nothing below starts until all three hold (DEC-LPT-017).
- The archive tag, pushed by the owner on the `dev` tip that will be the
  implementation branch's base:

  ```
  X=$(git rev-parse origin/dev)
  git tag -a archive/dev-record-2026-10 "$X" -m "Last dev tree carrying the development record before lean-production-tree"
  git push origin archive/dev-record-2026-10
  ```

  This branch was cut at `c0ff090`, before the release; bring it to `X` by
  merging `origin/dev` into it, never by force-pushing, so that
  `git merge-base origin/dev HEAD` prints `X`.
- Before merging, and again at the last push:
  `B=$(git merge-base origin/dev HEAD); git diff --quiet archive/dev-record-2026-10 "$B" -- $(git diff --name-only --diff-filter=D "$B" HEAD)`
  exits 0 — no deleted path changed on `dev` since the tag. If it fails, the
  owner tags `$B` as `archive/dev-record-2026-10-<YYYYMMDD>`, every pointer is
  rewritten to the new name, and the first tag stays; a tag is never moved
  (DEC-LPT-001).
- **Gate:** `git ls-remote --tags origin 'archive/*'` prints
  `refs/tags/archive/dev-record-2026-10` and its peeled
  `refs/tags/archive/dev-record-2026-10^{}` naming `X`, recorded here with
  both shas and the date. No milestone below starts until it is recorded.

## Milestone 3 — The hygiene module, seen red first

- `tests/support.py`: `shipped_files(root: Path) -> list[str]`, the
  `git ls-files --cached --others --exclude-standard` call moved out of
  `nested_agents_files`, returning `[]` when git fails, as today;
  `nested_agents_files` in `tests/test_agent_artifacts.py` keeps its filter
  and calls it (R-LPT-10).
- `tests/test_tree_hygiene.py` (new, flat under `tests/`): a module docstring
  giving the argument — the record lives at the archive tag, so a shipped
  path resolves or says where it went. `_SHAPES` for
  `docs/**/*-plan.md`, `docs/**/peer-review-*.md` and
  `docs/**/reflection-*.md`, plus the `evals/` prefix; `_LINK` over
  `](target)`; `_SPAN` exactly
  `` `((?:docs|evals|openspec/changes|\.claude|skills)/[A-Za-z0-9_./-]+)` ``;
  `_ARCHIVE = re.compile(r"archive/[\w.-]+")`. Functions:
  `shape_offenders(paths) -> list[str]`;
  `reference_offenders(text: str, path: str, root: Path) -> list[str]`, each
  offender `"<path>:<line>: <token>"`, reading no file;
  `prose_files(paths) -> list[str]`, R-LPT-11's scope over `shipped_files`
  (R-LPT-11, R-LPT-12, DEC-LPT-013, DEC-LPT-014).
- Planned tests, named so Milestone 7 can cite them (DEC-LPT-018):
  - `test_no_shipped_file_is_a_plan_review_or_evaluation_document` (the real
    tree through `shipped_files`) — AC-LPT-1;
  - `test_a_tracked_plan_document_is_named` (a `tmp_path` repository with
    `git init` and `git add docs/foo-plan.md`) and
    `test_a_file_under_evals_is_named` (a planted path list) — AC-LPT-2;
  - `test_every_path_in_shipped_prose_resolves_or_names_an_archive` (the real
    tree) — AC-LPT-3;
  - `test_a_dangling_backticked_path_is_named_with_file_and_line` and
    `test_a_dangling_relative_link_is_named_with_file_and_line` (planted text
    under `tmp_path`) — AC-LPT-4;
  - `test_a_line_naming_an_archive_ref_is_quiet` (parametrised over
    `archive/dev-record-2026-10` and `archive/dev-record-2026-10-20261101`),
    `test_a_path_inside_an_external_url_is_quiet`,
    `test_a_placeholder_or_glob_span_is_quiet` and
    `test_a_fragment_only_link_is_quiet` — AC-LPT-5.

  Each carries the tier `tests/shape_support.py` computes, marked per
  function, since the module mixes tiers (a git process is `e2e`).
- Red first, never committed: in a scratch worktree outside the repository
  (`git worktree add --detach <scratch>/lean HEAD`), apply Milestone 6's
  deletion list only, copy the module and the helper in, and run
  `python -m pytest tests/test_tree_hygiene.py -q -p no:cacheprovider` there.
  Record: the planted tests green; the shape test green there and red in the
  real checkout, where the planning documents still exist; the reference test
  red with its offender list. That list is the authority on what Milestones 4
  to 6 missed (DEC-LPT-013): compare it with the simulated list above and add
  any extra file to Milestone 5. Then `git worktree remove` the scratch tree.
- The module is committed in Milestone 6, with the deletion that turns its
  shape check green.
- **Gate:** `make test` (the committed tree, the module held back)

## Milestone 4 — Content that moves before its file goes

- `docs/hooks.md`, "Releasing" (heading kept): after the skill-version
  paragraphs, replace the checklist paragraph (`:421-438` at `c0ff090`; it
  names `prepare-release-0-3-0` and cites `docs/distribution-plan.md` §3)
  with the numbered runbook of R-LPT-4, taken from
  `docs/distribution-plan.md:96-198`: (1) the release-prep pull request into
  `dev`, squash — the bump checklist as the paragraph lists it today, the
  hand edits no test names, and the changelog cut with the heading dated the
  day the tag will be pushed; (2) the pre-tag checks on its head —
  `make pre-pr`, both generator `--check` modes, `make e2e-live`, a local
  wheel installed into a fresh venv printing the version; (3) `dev → qa`, a
  merge commit, waiting for `ci-ok` on the `pull_request` run; (4)
  `qa → main`, a merge commit, M; (5) the dry run — `workflow_dispatch` of
  `release.yml` on M, `gate` and `build` green, `publish` skipped; (6) the
  date rule — the `[X.Y.Z]` heading reads the day the tag is pushed, and a
  slip means a new release-prep pull request and a re-promotion, never a
  commit on `main`; (7) `python tools/check_promotion.py tag-ancestry --sha
  <M> --fetch` exit 0, then `git tag -a vX.Y.Z <M>`, pushed by a person or an
  App token, never `GITHUB_TOKEN`; (8) watch `gate`, `build` and `publish`;
  (9) verify both files —
  `https://pypi.org/integrity/planlint/<X.Y.Z>/<file>/provenance` returns 200
  with a bundle whose publisher is GitHub, then
  `pipx run pypi-attestations verify pypi --repository https://github.com/ianshank/planlint pypi:<file>`;
  (10) in a fresh venv, `pip install planlint==X.Y.Z`, `planlint --version`,
  and `planlint --target <clone at M> validate --fail-on ERROR` exit 0; (11)
  the GitHub release from the `[X.Y.Z]` section; (12) the back-merge,
  `sync/main-into-dev → dev`, a merge commit (`qa` is never back-merged);
  (13) M, the run ids and the pull requests recorded in a later pull request
  into `dev` — nothing is committed to `main` after the tag; (14) the
  post-release sweep of R-LPT-13. One sentence: the PyPI trusted publisher is
  bound to `release.yml` and the environment `pypi`, so renaming either
  breaks the publish. Keep the interim-window sentence (run M to the publish
  in one sitting). Do not carry the 0.3.0-only steps — the pending-publisher
  registration, the Context7 submission, the repository surface
  (DEC-LPT-006). Name no package.
- `docs/next-steps.md` item 17 (`:444-450`): absorb the rows of
  `docs/distribution-plan.md` §5 that are not about the suite — a wrapper
  script inside the skill; version output as JSON with a ruleset
  fingerprint; copies of the skill under other agents' directories;
  declaring allowed tools in the skill frontmatter; a freshness-check target
  in the pre-PR ladder — each with its reopen trigger. Drop "a hosted
  evaluation dataset (the suite under `evals/` is the source, an export is
  mechanical)"; the rows "Exporting the evaluation suite as a dataset" and
  "Running the evaluation suite in continuous integration" leave with the
  suite.
- `docs/next-steps.md`, "Deferred / out of scope": one sentence for §6 — no
  spec authoring, no MCP server, no rename of the import package or the
  waiver prefix, no container as the primary delivery path, no second copy
  of the skill in this repository, and no README claim about an agent load
  path this project has not tested.
- `docs/next-steps.md`: a "Retired documents" list, near the end, naming
  each of R-LPT-1's documents once, each with its archive URL on the same
  line, and one line for `evals/`.
- `.claude/skills/planlint-release/SKILL.md`: `:17-19` — the branches may not
  exist until routes are enforced (point at `docs/hooks.md`, *Branching and
  promotion*), and `docs/hooks.md` *Releasing* is this skill's checklist, in
  the same order; `:61` — "as `docs/hooks.md` *Releasing* says"; the
  back-merge section ends with the post-release sweep. No package named.
- **Gate:** `make docs-check`

## Milestone 5 — References, conventions, agent prose, the open package and the retunes, with the record still present

- `docs/next-steps.md`: on `:13`, `:28`, `:39`, `:52-53`, `:120`, `:163`,
  `:230`, `:234`, `:322` and `:338`, drop the path token or add the archive
  URL on the same line, keeping finding ids such as F4, D3 and N8a; `:384`,
  the wiring-plan link, becomes its archive URL; items 4 (`:41-43`) and 16
  (`:437-442`) become one line each; item 24 (`:350-379`) is re-scoped as
  R-LPT-5 says and its exit sentence rewritten as R-LPT-14 says. The
  nested-file sentence at `:385` moves with the deletion (Milestone 6).
- `README.md`: `:344-345` ("validates the retrieval config and the agent
  indexes"); `:500-504` (the archived-suite paragraph, DEC-LPT-008: "An
  agent-skill evaluation suite lived in this tree through v0.3.0 and is
  archived at
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/evals`.
  It was never a gate; `tests/test_skill_contract.py` holds the read-only
  verbs and the exit-code messages, and the refusal itself is the skill's
  own prose."); `:511-527` ("Dogfooding": "`openspec/changes/` holds the
  change packages still open; CI runs `planlint --target . validate
  --fail-on ERROR` as a hard gate (`self-validate`). A package leaves the
  tree in the release that ships it; the CHANGELOG records what shipped and
  `archive/dev-record-2026-10` holds every package shipped through v0.3.0.",
  plus the Mermaid paragraph without its package link); `:558-580`, the rows
  of each deleted document and of the suite. Every `REQUIRED_DOCS` link stays
  (`tools/check_docs.py:17-44`).
- `llms.txt:38`; `context7.json:14,20-21`, with
  `test_context7_indexes_the_skill_and_excludes_the_evals` renamed
  `test_context7_indexes_the_skill` and its `evals` assertion dropped in the
  same commit.
- `docs/agents-skills-harness.md:140`, the wiring-plan link → archive URL
  (`:6` and `:127-130` move with the deletion, Milestone 6).
- `SECURITY.md:47-48`; `docs/aqa.md:113-114` (the evaluation-suite claim)
  and `:221-222` (R-LPT-14); `docs/architecture/c4.md:84`.
- `docs/hooks.md`: the spec-status row (`:163`) and the paragraph
  (`:171-173`) as R-LPT-14 says, keeping `settle-package-status-headers` —
  for example: "`make spec-status` reads the packages still open under
  `openspec/changes/`; at `<sha>` it reported `<n>` packages and no finding
  (`make spec-status`, exit 0). A package that closes under a `DRAFT` header
  reads `draft-but-complete`, exiting 1, until
  `settle-package-status-headers` decides the vocabulary
  ([`next-steps.md`](next-steps.md) item 24)."; the bullet at `:214-218`,
  together with the hook arm and the nudge-table entry below.
- `docs/AGENTS.md:13` (the diagram node) and `:31-33` (the paragraph): "a
  plan is a change package; a planning document that is not one is not
  tracked; `archive/dev-record-2026-10` holds the last ones", keeping the
  `policies.md#count-cites-a-command` link and the file under
  `MAX_NESTED_LINES`; `tools/check_docs.py:24-28`, the comment, the same.
- Configuration: `.gitignore:60-65`; `.dockerignore:52` with
  `tests/test_release_surface.py:223`; `.gitleaks.toml:4-6`;
  `pyproject.toml:77-79`; `.github/dependabot.yml:24-25`.
- `.claude/hooks/nudge_rule_registry.sh:58-61` with
  `tests/test_claude_hooks.py:49` and `docs/hooks.md:214-218`.
  `tests/test_claude_hooks.py:52` and `:201` need no edit: the hook matches
  path strings and never stats them.
- `.claude/agents/spec-drafter.md:7` — the worked example behind
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/add-witness-mode/proposal.md`;
  its "read existing packages" step says to read the open packages under
  `openspec/changes/` in full; its area-code step also reads
  `openspec/project.md`'s retired-codes line.
  `.claude/agents/spec-adversary.md:7,24` — the same example by archive URL.
  `.claude/skills/planlint-change-package/SKILL.md:11` — the reviewed
  packages by the archive URL of `docs/peer-review-2026-10.md`.
  `.claude/skills/planlint-add-rule/SKILL.md:18` — drop the roadmap.
  `.claude/agents/planlint-verifier.md:22,28` — drop `evals/` and the
  `post-merge-quality-review` path.
- `openspec/project.md`: one line, "- Retired area codes (archived; never
  reuse): …", generated before the deletion by
  `ls openspec/changes | grep -v -e '^add-witness-ci-artifacts$' -e '^widen-indeterminate-unchecked-citations$' -e '^prepare-release-0-3-0$' -e '^adopt-branch-promotion-model$' | grep -vE '\.(md|json)$' | while read -r p; do cat openspec/changes/"$p"/specs/*/spec.md; done | grep -oE '^- (R|C)-[A-Z]{2,}-' | sed -E 's/^- (R|C)-//; s/-$//' | sort -u | paste -sd' ' -`
  — declarations only, so a code a kept package owns is never listed
  (R-LPT-8, DEC-LPT-010).
- `openspec/changes/add-witness-ci-artifacts/`: R-WCA-33 (spec `:270-277`),
  AC-WCA-29 (`:815-822`), AC-WCA-30 (`:824-829`), the proposal's "Docs that
  move together" and "No agent permission to record a witness" bullets, and
  Milestone 9's lines in its `tasks.md` naming a deleted document or
  `evals/fabricate-witness/` — each amended and marked "(amended by
  `lean-production-tree`)" (R-LPT-16, DEC-LPT-007). Then
  `planlint --target . validate --fail-on ERROR --change add-witness-ci-artifacts`
  exit 0, and `python -m pytest tests/test_spec_test_citations.py -q` green.
- Retunes: `tests/test_spec_status.py` — `:40`, `:289`, and `:494-502`
  (`assert rows`, docstring); `tests/test_agent_artifacts.py` — the docstring
  at `:3`, `:27`, `:78-115`, `:142-307`, and `:333-343` with `context7.json`
  above; `tests/test_release_surface.py:223` with `.dockerignore`, and the
  docstring at `:252`; `tests/test_rule_registry_docs.py:69`. Then
  `make typecheck`, and lower each ceiling in `MYPY_TESTS_CEILINGS` the guard
  names to its new exact count; raise none (R-LPT-9).
- **Gate:** `make pre-pr`

## Milestone 6 — The deletion, its coupled halves, the hygiene module and the CHANGELOG entry

- `git rm -r docs/agent-directory-wiring-plan.md docs/distribution-plan.md docs/eval-corpus-plan.md docs/reflection-plan-2026-10.md docs/peer-review-2026-09.md docs/peer-review-2026-10.md docs/differentiation-roadmap.md evals .claude/skills/planlint-add-eval-case`,
  and `git rm -r openspec/changes/<name>` for each directory R-LPT-2's
  listing prints.
- In the same commit (DEC-LPT-019): `docs/agents-skills-harness.md:6` and
  `docs/hooks.md:277` drop `planlint-add-eval-case`;
  `docs/agents-skills-harness.md:127-130` and `docs/next-steps.md:385` state
  the nested set true, naming `git ls-files '*/AGENTS.md'` as the
  regenerator; `tests/test_adopter_urls.py:59` drops `"evals"`;
  `tests/support.py`, `nested_agents_files` and `tests/test_tree_hygiene.py`
  from Milestone 3.
- `CHANGELOG.md` `[Unreleased]`: `### Removed — the development record`, one
  bullet led by ``- **`lean-production-tree`.**`` naming each of R-LPT-1's
  documents by name, `evals/`, `.claude/skills/planlint-add-eval-case/`,
  "every change package whose work had shipped by v0.3.0 — all but
  `add-witness-ci-artifacts`, `widen-indeterminate-unchecked-citations`,
  `prepare-release-0-3-0` and `adopt-branch-promotion-model`;
  `git diff --name-only --diff-filter=D archive/dev-record-2026-10 <merge commit> -- openspec/changes | cut -d/ -f3 | sort -u`
  lists them", the archive tag and its URL form, and "the release runbook
  moved to `docs/hooks.md` *Releasing*". No released section is edited
  (R-LPT-15, C-LPT-4).
- **Gate:** `make pre-pr`

## Milestone 7 — Verification, records and the selectors

- Record each command with the commit and its exit code:

  ```
  planlint --target . validate --fail-on INFO; echo $?
  git worktree add --detach <scratch>/base "$(git merge-base origin/dev HEAD)"
  planlint --target <scratch>/base graph --format json > <scratch>/base.json
  planlint --target . graph --format json > <scratch>/head.json
  python tools/diff_spec_graph.py <scratch>/base.json <scratch>/head.json; echo $?
  make pre-pr; echo $?
  python -m pytest tests/test_tree_hygiene.py tests/test_agent_artifacts.py tests/test_claude_hooks.py tests/test_spec_status.py tests/test_spec_test_citations.py tests/test_stage_citations.py tests/test_rule_registry_docs.py tests/test_agent_skill_docs.py tests/test_adopter_urls.py tests/test_release_surface.py tests/test_ci_makefile.py tests/test_static_ratchets.py -q; echo $?
  make spec-status; echo $?
  git ls-files | grep -E '^(evals/|docs/.*-plan\.md|docs/peer-review-)' | wc -l
  git ls-files | wc -l; git ls-files -z | xargs -0 cat | wc -c
  make stage-citations
  ```

  Expected: validate clean over the open packages and this one; the graph
  diff `PASS`; the ladder 0; the selection 0; `make spec-status` one row per
  package, this one partial until its boxes are ticked and
  `draft-but-complete` afterwards, by design (R-LPT-14); the grep 0. Record
  the file and byte counts beside the `c0ff090` figures above.
- Re-point AC-LPT-1 to AC-LPT-5 from stage-only to the Milestone 3 test names,
  keeping each stage; run `python -m pytest tests/test_spec_test_citations.py
  -q` and record.
- Confirm `make stage-citations` lists no stage this package added to the
  unrun set: its verification lines cite `test`, `docs-check` and `pre-pr`
  only (DEC-LPT-018).
- C-LPT-1: `git diff --stat "$(git merge-base origin/dev HEAD)" HEAD --
  openspec_graph .github/workflows Makefile tests/baseline_rules.json` prints
  nothing.
- C-LPT-2: unchanged — `openspec_graph/rule_types.py:47`,
  `tests/test_graft_rules.py:478`, `tests/test_rules_speckit.py:330`,
  `tests/test_detect_thresholds.py:382`, `tests/test_stage_citations.py:5`,
  `tools/stage_citations.py:13`, `tests/workflow_support.py:54`,
  `tests/test_agent_artifacts.py:435,549`, `tests/test_graph.py:1-4`,
  `.claude/hooks/guard_promotion.py:2`; corrected —
  `tests/test_release_surface.py:252`.
- Tick each criterion only as it is verified. This package's header stays
  `DRAFT`; the pull request, into `dev`, asks the maintainer to settle it at
  merge. This package leaves the tree in the 0.4.0 post-release sweep, with
  the 0.3.0 pair.
- **Gate:** `make pre-pr`
