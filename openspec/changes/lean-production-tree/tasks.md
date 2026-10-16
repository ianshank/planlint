# Tasks: lean-production-tree

Drafted at `c0ff090` — the merge of PR #57 into `dev`, the base of
`claude/lean-production-tree` — on 2026-10-15, as Phase 1 of the session plan
for a lean production branch, and revised at `04d1622` on 2026-10-16 to
resolve the first adversarial review (Milestone 1). That plan is not tracked
(DEC-LPT-005); every decision this package takes from it is restated in
`specs/production-tree/spec.md`. **This package must not merge before
`v0.3.0` is published and the 0.3.0 record is in `dev`** (Milestone 2,
DEC-LPT-017): pull request #58 stays a GitHub draft, and is marked ready for
review only after Milestone 2's gate is recorded here. Every line number
below is re-read at the implementation branch's head before the milestone
that uses it; a sibling landing first may move a line without moving the
fact. Every number names the command that produced it.

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
  `None`. Of the paths in `INVARIANT_SOURCES` and `ADR_SOURCES`
  (`openspec_graph/detect.py:64-86`), `for p in <each>; do [ -e "$p" ] && echo
  "$p"; done` prints only `AGENTS.md`, which `_invariants`
  (`detect.py:349-372`) skips because it carries no `INV-n` id
  (`test_agents_md_declares_no_invariant_ids`); so G006 and G009 cannot fire.
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
  implementing the first draft's R-LPT-11 tokens and scope over the files
  that survive the deletion, not committed): 28 files in scope, 31 dangling
  tokens in 10 files — `.claude/agents/planlint-verifier.md:28`,
  `.claude/agents/spec-drafter.md:7`,
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
  - `tests/test_ledger.py:53-59`, a spec path under
    `openspec/changes/add-waiver-ledger-and-inv-lints/` built in memory and
    an assertion on that package name — test data, not a reference to the
    tree, outside R-LPT-9 (DEC-LPT-011) — no edit;
  - the clauses of the kept packages that R-LPT-16 reconciles.
- **No test holds the skill's refusal.**
  `grep -rn "Never run .witness. yourself\|finding disappear\|without changing the fact" tests/`
  prints nothing (DEC-LPT-008).

## Re-checked at `04d1622`, 2026-10-16 (the review)

- **The gate before the revision.** `planlint --target . validate --fail-on
  ERROR`: `55 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`, exit 0.
- **Remote state.** `git ls-remote --tags origin` prints `refs/tags/v0.1.0`
  and its peeled line, nothing else; `curl -s -o /dev/null -w '%{http_code}\n'
  https://pypi.org/pypi/planlint/0.3.0/json` → `404`;
  `gh api repos/ianshank/planlint/rulesets` → `[]`;
  `gh api repos/ianshank/planlint/pulls/58 --jq '{draft,base:.base.ref,head:.head.ref}'`
  → `{"base":"dev","draft":true,"head":"claude/lean-production-tree"}`.
  `adopt-branch-promotion-model/tasks.md:183-188` plans the rulesets, the
  owner as the only bypass and a `v*` tag ruleset, unticked.
- **The widened reference scan** (the same read-only script, fed on stdin
  and not committed, over every root `*.md` but `CHANGELOG.md` and the
  markdown under `.github/` as well): 30 files in scope, 32 dangling tokens in
  11 files — the 31 above plus `SECURITY.md:48`, which backticks
  `docs/peer-review-2026-09.md`; `.github/pull_request_template.md` has none.
  No in-scope line carries a `path:line` span: a `grep -nE` over the scope
  for a backticked in-scope path followed by a colon and a digit prints
  nothing.
- **`openspec/AGENTS.md`'s budget.** `wc -l openspec/AGENTS.md` → 54;
  `grep -n '^MAX_NESTED_LINES' tests/test_agent_artifacts.py` →
  `454:MAX_NESTED_LINES = 60`, held as `len(lines) <= MAX_NESTED_LINES` by
  `test_nested_agents_file_stays_short`. The retired-codes entry, wrapped as
  the file's prose is, takes four lines
  (`printf '%s\n' "<entry>" | fold -s -w 78 | wc -l` → 4) and one blank line
  before it, leaving the file at 59 of 60.
- **The retired-codes generator** (Milestone 5's command), run here:
  `AA AC AD AQA ASP CF CH CP CT DC DEF DG DL EH FE GA GR GTC GV HCW HNS LH LM
  MCO MFD MP PB PM POL PR PS RDS RE RP SA SD SDI SE SER SK SNAP TC TDR TSS UB
  UG UMC VER WL WM ZCG`, `| wc -w` → 51. None of `WCA`, `IND`, `REL`, `BPM`
  or `LPT`, which `grep -ohE '^- (R|C)-[A-Z]{2,}-' openspec/changes/*/specs/*/spec.md`
  shows the open packages declare. The first draft's command, run with this
  package present, also listed `LPT`; reading only the packages, it missed
  `RP` and `AC`, which only `docs/differentiation-roadmap.md` declares
  (`AC-RP-1` to `AC-RP-3`, `AC-AC-1` to `AC-AC-3`) and which
  `CHANGELOG.md:1712` and three deleted packages cite (`AC-RP-3`).
- **`widen-indeterminate-unchecked-citations` is unimplemented.**
  `grep -rn 'unchecked-citations' openspec_graph/ .github/actions/` and
  `grep -rn '"waived"' openspec_graph/` print nothing; 0 of 20 criteria
  ticked, 0 of 6 milestones `[DONE]` (the commands above).
- **Where IND and WCA name a deleted path.**
  `grep -n 'peer-review\|differentiation-roadmap\|evals/\|openspec/changes/' <file>`
  over each package's three files. Requiring an edit or preservation:
  WCA spec `:270-277` (R-WCA-33), `:547-549` (DEC-WCA-022's AC-GA-29
  sentence), `:815-822` (AC-WCA-29), `:824-829` (AC-WCA-30); WCA proposal
  `:194-200`, `:212-213`, `:243-245`; WCA `tasks.md:135-143`, `:316-322`,
  `:327-328`; IND spec `:196-200` (C-IND-7); IND proposal `:208-215`; IND
  `tasks.md:249-260`. Evidence, which stays: WCA proposal `:13`, `:16`,
  `:37`; WCA spec `:20`; IND proposal `:16`, `:21`, `:62`, `:64`, `:66`,
  `:115`, `:117`, `:120`; IND spec `:22`, `:29`, `:46`, `:219`, `:248`.
  After the deletion only WCA's own `tasks.md` names
  `test_action_does_not_pass_require_witness`
  (`grep -ln test_action_does_not_pass_require_witness <kept packages>`), so
  the AC-GA-29 re-point is moot.
- **The couples' direction** (DEC-LPT-019), read in the tests:
  `test_agent_artifacts_are_excluded_from_the_docker_context`
  (`tests/test_release_surface.py:216-224`) asserts each tuple entry is in
  `.dockerignore`; `test_harness_docs_list_every_agent_and_skill` asserts
  each existing agent and skill is named, never that a named one exists;
  `test_each_documented_file_class_is_nudged` asserts each table entry is
  nudged. `tests/test_adopter_urls.py`'s argument-free tests, run in memory
  with `evals` removed from `_EXCLUDED_DIRS` and no file edited, all pass.
- **The helpers only the evals section calls.** `grep -n '_ids\b\|_frontmatter' tests/test_agent_artifacts.py`:
  `_ids` (`:114-115`), `_frontmatter_block`, `_frontmatter` and
  `_frontmatter_list` (`:117-140`) are defined there and called only inside
  the evals section (`:146-307`); `tests/test_agent_skill_docs.py` has its
  own `_frontmatter`.
- **More lines the inventory missed**, each added below:
  `docs/next-steps.md:391-392` ("Eight files exist and are gated");
  `tests/test_agent_artifacts.py:433` ("so nine files cannot land in no
  gate"); `pyproject.toml:162-166` ("is in measure-coverage-once's
  tasks.md"); `tests/test_ci_makefile.py:478-480` (the docstring saying the
  section says the report "stays red"). `.github/dependabot.yml:23-25`
  attributes a deferral and says an earlier attribution to the distribution
  plan was wrong — history (C-LPT-2), unchanged.

## Milestone 0 — Grounding at the implementation branch's head

- Run the gate and record its exit code before the first edit outside this
  package: `planlint --target . validate --fail-on ERROR`.
- Re-run every measurement above at the head and record the figures beside
  the `c0ff090` and `04d1622` ones, each with its commit.
- Re-run the cross-check `git grep` above and the package-name grep over the
  agent prose,
  `git grep -nwE "$(ls openspec/changes | grep -vE '\.(md|json)$' | paste -sd'|')" -- .claude skills AGENTS.md '*/AGENTS.md' llms.txt`;
  any hit outside Milestones 4 to 6 joins them, recorded here.
- Confirm `add-witness-ci-artifacts` is still unimplemented: no criterion
  ticked, and `grep -n "witness-dir" openspec_graph/cli.py` prints nothing.
- Confirm `widen-indeterminate-unchecked-citations` is still unimplemented:
  no criterion ticked, no milestone `[DONE]`, and
  `grep -rn 'unchecked-citations' openspec_graph/ .github/actions/` prints
  nothing.
- If either has been implemented, R-LPT-16's amendment of it changes shape:
  stop and re-read DEC-LPT-007.
- **Gate:** `make test`

## Milestone 1 — The change package

- `proposal.md`, `specs/production-tree/spec.md` and `tasks.md` written spec
  first; every criterion unticked; `Status: DRAFT`. Reviewed by
  `spec-adversary` before any edit outside this directory; each finding
  resolved by a decision and recorded here.
- Review 1 (`spec-adversary`, against `04d1622`), resolved in this revision,
  each finding by the clauses beside it:
  - IND's C-IND-7 requires edits to deleted documents — R-LPT-16,
    DEC-LPT-007, AC-LPT-17, Milestones 0 and 5, the proposal's "Kept
    packages" bullet;
  - the line-wide archive exemption hid broken links — R-LPT-3, R-LPT-5,
    R-LPT-11, R-LPT-12, DEC-LPT-014, AC-LPT-3 to AC-LPT-5, AC-LPT-9,
    Milestones 3 and 5;
  - AC-LPT-17 reached too far and not far enough — AC-LPT-17, R-LPT-16,
    DEC-LPT-007;
  - the 0.3.0 record riding in this change — C-LPT-4, DEC-LPT-003,
    DEC-LPT-017, Milestone 2;
  - the merge-order gate was unenforceable — DEC-LPT-017, AC-LPT-1,
    Milestone 2, this file's header;
  - the retired-codes line in `openspec/project.md` — R-LPT-8, R-LPT-13,
    DEC-LPT-010, DEC-LPT-012, AC-LPT-12, Milestones 5 and 7;
  - AC-LPT-1 claimed more than its test sees — AC-LPT-1;
  - the enumeration could pass vacuously — R-LPT-10, DEC-LPT-015, AC-LPT-6,
    Milestone 3;
  - lines missing from the edit inventory — R-LPT-7, R-LPT-9, R-LPT-14,
    Milestones 5 to 7;
  - `.github/dependabot.yml` and the couples' direction — R-LPT-7,
    DEC-LPT-019, DEC-LPT-020, AC-LPT-11;
  - the simulated scan's file figure — "Measured at `c0ff090`";
  - Milestone 4's gate — Milestone 4;
  - a tag ruleset that does not exist — DEC-LPT-001, Milestone 2;
  - in-memory package names — R-LPT-9, DEC-LPT-011;
  - AC-LPT-2's planted file and AC-LPT-13's empty scope — AC-LPT-2,
    AC-LPT-13, Milestone 3;
  - the scan's scope, widened — R-LPT-11, DEC-LPT-013.

  Found while resolving them: the roadmap declares area codes the CHANGELOG
  cites, so the retired-codes generator reads it (R-LPT-8, DEC-LPT-010); and
  the G006/G009 evidence said no candidate path exists, while the root
  `AGENTS.md` does and carries no `INV-n` (proposal and spec evidence). Hand
  the revision back to `spec-adversary` before any edit outside this
  directory.
- AC-LPT-1 to AC-LPT-5 cite their stage only, and AC-LPT-6 only its existing
  tests, because the new tests do not exist yet; Milestone 7 adds the
  selectors (DEC-LPT-018).
- Record the exit codes of `planlint --target . validate --fail-on INFO
  --change lean-production-tree`, of the unscoped run at `--fail-on ERROR`,
  and of `python -m pytest tests/test_spec_test_citations.py tests/test_spec_status.py tests/test_stage_citations.py -q -p no:cacheprovider`.
- **Gate:** `make pre-pr`

## Milestone 2 — Preconditions, recorded before any deletion (owner)

- Pull request #58 stays a GitHub draft through this milestone, and is
  marked ready for review only after this milestone's gate is recorded here.
  No criterion observes the release or a tag, so the draft state is what
  keeps the change from merging early (DEC-LPT-017).
- `v0.3.0` is tagged, published and back-merged:
  `git ls-remote --tags origin v0.3.0` prints the tag and its peeled line;
  `curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/0.3.0/json`
  prints `200`, and in a fresh venv `python -m pip install planlint==0.3.0`
  resolves and exits 0; `git fetch origin && git merge-base --is-ancestor
  'v0.3.0^{commit}' origin/dev` exits 0. Record all three with their output
  and the date.
- The 0.3.0 record is merged into `dev` before the archive tag is created:
  the `tasks.md` entries and the criteria ticks of `prepare-release-0-3-0`
  and `adopt-branch-promotion-model` that the release's record step writes,
  in their own pull request into `dev`, never in this change (C-LPT-4).
  Record that pull request's number and merge commit, and
  `git show origin/dev:<spec> | grep -c '^- \[x\] \*\*AC-'` for each of the
  two specs beside the `c0ff090` figures.
- Record `gh api repos/ianshank/planlint/rulesets` as the tag is pushed (`[]`
  at `04d1622`): whatever it prints is what protects the archive tag, and
  nothing in the tree depends on it (DEC-LPT-001).
- The archive tag, pushed by the owner on the `dev` tip that will be the
  implementation branch's base — after the 0.3.0 record above has merged:

  ```
  git fetch origin
  X=$(git rev-parse origin/dev)
  git tag -a archive/dev-record-2026-10 "$X" -m "Last dev tree carrying the development record before lean-production-tree"
  git push origin archive/dev-record-2026-10
  ```

  This branch was cut at `c0ff090`, before the release; bring it to `X` by
  merging `origin/dev` into it, never by force-pushing, so that
  `git merge-base origin/dev HEAD` prints `X`.
- With the deletion committed (Milestone 7, and again at the last push):
  `B=$(git merge-base origin/dev HEAD); git diff --quiet archive/dev-record-2026-10 "$B" -- $(git diff --name-only --diff-filter=D "$B" HEAD)`
  exits 0 — no deleted path changed on `dev` since the tag. Not before: with
  no deletion the path list is empty and the diff would compare whole trees.
  If it fails, the owner tags `$B` as
  `archive/dev-record-2026-10-<YYYYMMDD>`, every pointer is rewritten to the
  new name, and the first tag stays; a tag is never moved (DEC-LPT-001).
- **Gate:** every precondition recorded here, with both shas and the date —
  `git ls-remote --tags origin v0.3.0` prints the tag; the PyPI JSON query
  prints `200`; `git merge-base --is-ancestor 'v0.3.0^{commit}' origin/dev`
  exits 0; the 0.3.0 record's pull request is merged into `dev`; and
  `git ls-remote --tags origin 'archive/*'` prints
  `refs/tags/archive/dev-record-2026-10` and its peeled
  `refs/tags/archive/dev-record-2026-10^{}` naming `X`. Only then is pull
  request #58 marked ready, and no milestone below starts until this is
  recorded.

## Milestone 3 — The hygiene module, seen red first

- `tests/support.py`: `shipped_files(root: Path) -> list[str]`, the
  `git ls-files --cached --others --exclude-standard` call moved out of
  `nested_agents_files`, returning `[]` when git fails, as today, and
  keeping only paths present on disk (`(root / p).exists()`), so an index
  entry removed with plain `rm` is not shipped; `nested_agents_files` in
  `tests/test_agent_artifacts.py` keeps its filter and calls it (R-LPT-10,
  DEC-LPT-015).
- `tests/test_tree_hygiene.py` (new, flat under `tests/`): a module docstring
  giving the argument — the record lives at the archive tag, so a shipped
  path resolves or says where it went. `_SHAPES` for
  `docs/**/*-plan.md`, `docs/**/peer-review-*.md` and
  `docs/**/reflection-*.md`, plus the `evals/` prefix; `_LINK` over
  `](target)`; `_SPAN` exactly
  `` `((?:docs|evals|openspec/changes|\.claude|skills)/[A-Za-z0-9_./-]+)` ``;
  the span exemption
  `re.search(r"archive/[\w.-]+/" + re.escape(span) + r"(?![\w./-])", line)`,
  and no exemption for a link. Functions:
  `shape_offenders(paths) -> list[str]`;
  `reference_offenders(text: str, path: str, root: Path) -> list[str]`, each
  offender `"<path>:<line>: <token>"`, reading no file;
  `prose_files(paths) -> list[str]`, R-LPT-11's scope over `shipped_files` —
  every root `*.md` but `CHANGELOG.md`, `llms.txt`, the nested `AGENTS.md`
  set, and `*.md` under `docs/`, `skills/`, `.claude/` and `.github/`
  (R-LPT-11, R-LPT-12, DEC-LPT-013, DEC-LPT-014).
- Planned tests, named so Milestone 7 can cite them (DEC-LPT-018):
  - `test_no_shipped_file_is_a_plan_review_or_evaluation_document` (the real
    tree through `shipped_files`, asserting `README.md` is enumerated) —
    AC-LPT-1;
  - `test_a_tracked_plan_document_is_named` and
    `test_a_file_under_evals_is_named` (one `tmp_path` repository made with
    `git init`, `docs/foo-plan.md` and `evals/case/prompt.md` added with
    `git add`) — AC-LPT-2;
  - `test_every_path_in_shipped_prose_resolves_or_names_its_archive` (the
    real tree, asserting `README.md` is in scope) — AC-LPT-3;
  - `test_a_dangling_backticked_path_is_named_with_file_and_line`,
    `test_a_dangling_relative_link_is_named_with_file_and_line`,
    `test_a_dangling_path_beside_another_archive_ref_is_named` (parametrised
    over an archive URL for a different path and a bare
    `archive/does-not-exist`) and
    `test_a_dangling_relative_link_beside_its_own_archive_url_is_named`
    (planted text under `tmp_path`) — AC-LPT-4;
  - `test_a_path_beside_its_own_archive_url_is_quiet` (parametrised over
    `archive/dev-record-2026-10` and `archive/dev-record-2026-10-20261101`),
    `test_a_path_inside_an_external_url_is_quiet`,
    `test_a_placeholder_or_glob_span_is_quiet` and
    `test_a_fragment_only_link_is_quiet` — AC-LPT-5;
  - `test_a_tracked_file_removed_from_disk_is_not_enumerated` (the `git init`
    repository: a committed file removed with plain `rm` is absent from
    `shipped_files`) — AC-LPT-6.

  Each carries the tier `tests/shape_support.py` computes, marked per
  function, since the module mixes tiers (a git process is `e2e`).
- Red first, never committed: in a scratch worktree outside the repository
  (`git worktree add --detach <scratch>/lean HEAD`), apply Milestone 6's
  deletion list with `git rm -r` — never plain `rm`, so the index agrees with
  the disk — copy the module and the helper in, and run
  `python -m pytest tests/test_tree_hygiene.py -q -p no:cacheprovider` there.
  Record: the planted tests green; the shape test green there and red in the
  real checkout, where the planning documents still exist; the reference test
  red with its offender list. That list is the authority on what Milestones 4
  to 6 missed (DEC-LPT-013): compare it with the widened simulated list above
  and add any extra file to Milestone 5. Then `git worktree remove` the
  scratch tree.
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
  post-release sweep of R-LPT-13, appending the swept packages' area codes to
  the `openspec/AGENTS.md` entry. One sentence: the PyPI trusted publisher is
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
  each of R-LPT-1's documents once, each as a link whose target is its
  archive URL or as a backticked path beside its own archive URL, and one
  line for `evals/`.
- `.claude/skills/planlint-release/SKILL.md`: `:17-19` — the branches may not
  exist until routes are enforced (point at `docs/hooks.md`, *Branching and
  promotion*), and `docs/hooks.md` *Releasing* is this skill's checklist, in
  the same order; `:61` — "as `docs/hooks.md` *Releasing* says"; the
  back-merge section ends with the post-release sweep. No package named.
- **Gate:** `make pre-pr` (this milestone edits files `make test` checks)

## Milestone 5 — References, conventions, agent prose, the open packages and the retunes, with the record still present

- The pointer rule for every edit below (R-LPT-3, DEC-LPT-014): a markdown
  link to a deleted path takes the archive URL as its target — never left
  relative with the URL beside it — and a backticked deleted path is dropped
  or kept on the same line as its own archive URL.
- `docs/next-steps.md`: on `:13`, `:28`, `:39`, `:52-53`, `:120`, `:163`,
  `:230`, `:234`, `:322` and `:338`, drop the path token or point at it by
  that rule, keeping finding ids such as F4, D3 and N8a — `:53`'s link
  `(reflection-plan-2026-10.md)` becomes the archive URL; `:384`, the
  wiring-plan link, takes its archive URL as target; items 4 (`:41-43`) and
  16 (`:437-442`) become one line each; item 24 (`:350-379`) is re-scoped as
  R-LPT-5 says and its exit sentence rewritten as R-LPT-14 says. The
  nested-file sentences at `:385` and `:391-392` move with the deletion
  (Milestone 6).
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
- `docs/agents-skills-harness.md:140`, the wiring-plan link's target → its
  archive URL (`:6` and `:127-130` move with the deletion, Milestone 6).
- `SECURITY.md:47-48` (the widened scan's addition); `docs/aqa.md:113-114`
  (the evaluation-suite claim) and `:221-222` (R-LPT-14);
  `docs/architecture/c4.md:84`.
- `docs/hooks.md`: the spec-status row (`:163`) and the paragraph
  (`:171-173`) as R-LPT-14 says, keeping `settle-package-status-headers` —
  for example: "`make spec-status` reads the packages still open under
  `openspec/changes/`; at `<sha>` it reported `<n>` packages and no finding
  (`make spec-status`, exit 0). A package that closes under a `DRAFT` header
  reads `draft-but-complete`, exiting 1, until
  `settle-package-status-headers` decides the vocabulary
  ([`next-steps.md`](next-steps.md) item 24)." — with
  `tests/test_ci_makefile.py:478-480`, the docstring, saying the section
  names the follow-up that settles the vocabulary; the bullet at `:214-218`,
  together with the hook arm and the nudge-table entry below.
- `docs/AGENTS.md:13` (the diagram node) and `:31-33` (the paragraph): "a
  plan is a change package; a planning document that is not one is not
  tracked; `archive/dev-record-2026-10` holds the last ones", keeping the
  `policies.md#count-cites-a-command` link and the file under
  `MAX_NESTED_LINES`; `tools/check_docs.py:24-28`, the comment, the same.
- Configuration: `.gitignore:60-65`; `.dockerignore:52` with
  `tests/test_release_surface.py:223`; `.gitleaks.toml:4-6`;
  `pyproject.toml:77-79` and `:162-166` (the per-file list "is in
  measure-coverage-once's tasks.md" → at that file's archive URL).
  `.github/dependabot.yml:23-25` is not edited (R-LPT-7, C-LPT-2).
- `.claude/hooks/nudge_rule_registry.sh:58-61` with
  `tests/test_claude_hooks.py:49` and `docs/hooks.md:214-218`.
  `tests/test_claude_hooks.py:52` and `:201` need no edit: the hook matches
  path strings and never stats them.
- `.claude/agents/spec-drafter.md:7` — the worked example behind
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/add-witness-mode/proposal.md`;
  its "read existing packages" step says to read the open packages under
  `openspec/changes/` in full; its area-code step also reads
  `openspec/AGENTS.md`'s retired-codes entry.
  `.claude/agents/spec-adversary.md:7,24` — the same example by archive URL.
  `.claude/skills/planlint-change-package/SKILL.md:11` — the reviewed
  packages by the archive URL of `docs/peer-review-2026-10.md`.
  `.claude/skills/planlint-add-rule/SKILL.md:18` — drop the roadmap.
  `.claude/agents/planlint-verifier.md:22,28` — drop `evals/` and the
  `post-merge-quality-review` path.
- `openspec/AGENTS.md`: one entry, after the paragraph naming the drafter
  and the adversary and before the precedence paragraph — "Retired area
  codes, declared by packages and documents the `archive/dev-record-2026-10`
  tag holds; never reuse one:" and the codes, wrapped as the file's prose
  is — generated before the deletion by

  ```
  KEEP='add-witness-ci-artifacts|widen-indeterminate-unchecked-citations|prepare-release-0-3-0|adopt-branch-promotion-model|lean-production-tree'
  { for p in $(ls openspec/changes | grep -vE '\.(md|json)$' | grep -vxE "$KEEP"); do cat openspec/changes/"$p"/specs/*/spec.md; done; cat docs/differentiation-roadmap.md; } | grep -oE '^- (\*\*)?(R|C|AC)-[A-Z]{2,}-[0-9]' | sed -E 's/^- (\*\*)?(R|C|AC)-//; s/-[0-9]$//' | sort -u | paste -sd' ' -
  ```

  — declarations only, from files this change deletes, so no code an open
  package declares is listed, this package's `LPT` included. The precedence
  paragraph and the mermaid block are not touched, and `wc -l
  openspec/AGENTS.md` stays at or under `MAX_NESTED_LINES` (60).
  `openspec/project.md` is not edited (R-LPT-8, DEC-LPT-010).
- `openspec/changes/add-witness-ci-artifacts/`, each edit marked "(amended
  by `lean-production-tree`)" (R-LPT-16, DEC-LPT-007): R-WCA-33 (spec
  `:270-277`) and AC-WCA-29 (`:815-822`) drop the roadmap and the 2026-09
  review from their lists; R-WCA-33 and AC-WCA-30 (`:824-829`) drop the
  `evals/fabricate-witness/` clause, keeping SKILL.md's "Never run `witness`
  yourself to make the flag pass" verbatim; DEC-WCA-022's AC-GA-29 sentence
  (`:547-549`) reads as moot — `add-finding-line-hits` left the tree, so no
  open spec cites the test this change replaces. Proposal: the "Docs that
  move together" entries for the roadmap and the 2026-09 review (`:212-213`);
  the `add-finding-line-hits` bullet (`:194-200`), as moot; the evals clause
  of "No agent permission to record a witness" (`:243-245`), becoming
  SKILL.md's refusal. `tasks.md`: the AC-GA-29 bullet (`:135-143`), as moot;
  the roadmap and 2026-09 review lines (`:316-322`); the
  `evals/fabricate-witness/` line (`:327-328`). Not edited: the evidence at
  proposal `:13`, `:16`, `:37` and spec `:20`.
- `openspec/changes/widen-indeterminate-unchecked-citations/`, each edit
  marked the same way: C-IND-7 (spec `:196-200`) drops
  `docs/peer-review-2026-09.md`, `docs/peer-review-2026-10.md` and
  `docs/differentiation-roadmap.md`; `tasks.md:249-260`, the three bullets
  editing those documents, become one line saying they left the tree at the
  archive tag and need no edit; the proposal's "Docs and contracts that move
  together" bullet drops its clauses for the three (`:208-215`). Not edited:
  AC-IND-18, which names no deleted path, and the evidence listed under
  "Re-checked at `04d1622`".
- Then `planlint --target . validate --fail-on ERROR --change add-witness-ci-artifacts`
  and `--change widen-indeterminate-unchecked-citations`, each exit 0, and
  `python -m pytest tests/test_spec_test_citations.py -q` green.
- Retunes: `tests/test_spec_status.py` — `:40`, `:289`, and `:494-502`
  (`assert rows`, docstring); `tests/test_agent_artifacts.py` — the docstring
  at `:3`, `:27`, `:78-307` (`EVAL_CASES` and its comment, the grader and tag
  constants, `_ids`, `_frontmatter_block`, `_frontmatter`,
  `_frontmatter_list` and the evals section), and `:333-343` with
  `context7.json` above; `tests/test_release_surface.py:223` with
  `.dockerignore`, and the docstring at `:252`;
  `tests/test_rule_registry_docs.py:69`. Then `make typecheck`, and lower
  each ceiling in `MYPY_TESTS_CEILINGS` the guard names to its new exact
  count; raise none (R-LPT-9).
- **Gate:** `make pre-pr`

## Milestone 6 — The deletion, its coupled halves, the hygiene module and the CHANGELOG entry

- `git rm -r docs/agent-directory-wiring-plan.md docs/distribution-plan.md docs/eval-corpus-plan.md docs/reflection-plan-2026-10.md docs/peer-review-2026-09.md docs/peer-review-2026-10.md docs/differentiation-roadmap.md evals .claude/skills/planlint-add-eval-case`,
  and `git rm -r openspec/changes/<name>` for each directory R-LPT-2's
  listing prints.
- In the same commit (DEC-LPT-019): `docs/agents-skills-harness.md:6` and
  `docs/hooks.md:277` drop `planlint-add-eval-case`;
  `docs/agents-skills-harness.md:127-130`, `docs/next-steps.md:385` and
  `:391-392` state the nested set true, naming `git ls-files '*/AGENTS.md'`
  as the regenerator; the section comment at
  `tests/test_agent_artifacts.py:433` drops "nine files";
  `tests/test_adopter_urls.py:59` drops `"evals"`; `tests/support.py`,
  `nested_agents_files` and `tests/test_tree_hygiene.py` from Milestone 3.
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
- AC-LPT-1's listing, at the head before the merge, so no criterion waits on
  the merge: `git diff --name-only --diff-filter=D archive/dev-record-2026-10 HEAD -- openspec/changes | cut -d/ -f3 | sort -u`
  — every package at the tag but the four kept; `ls -d openspec/changes/*/`
  — the four and this one; and `ls docs/differentiation-roadmap.md
  .claude/skills/planlint-add-eval-case` fails on each.
- Milestone 2's deleted-path diff, now that the deletion is committed; record
  its exit.
- The retired codes, re-derived from the tag:
  `T=archive/dev-record-2026-10; git diff --name-only --diff-filter=D "$T" HEAD -- 'openspec/changes/*/specs/*/spec.md' docs/differentiation-roadmap.md | while read -r f; do git show "$T:$f"; done | grep -oE '^- (\*\*)?(R|C|AC)-[A-Z]{2,}-[0-9]' | sed -E 's/^- (\*\*)?(R|C|AC)-//; s/-[0-9]$//' | sort -u | paste -sd' ' -`
  prints the codes the `openspec/AGENTS.md` entry lists, and none of them is
  in `grep -ohE '^- (R|C)-[A-Z]{2,}-' openspec/changes/*/specs/*/spec.md`;
  `wc -l openspec/AGENTS.md` is at or under 60.
- Re-point AC-LPT-1 to AC-LPT-5 from stage-only to the Milestone 3 test
  names, and add `test_a_tracked_file_removed_from_disk_is_not_enumerated` to
  AC-LPT-6, keeping each stage; run `python -m pytest
  tests/test_spec_test_citations.py -q` and record.
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
  `.claude/hooks/guard_promotion.py:2`, `.github/dependabot.yml:23-25`;
  corrected — `tests/test_release_surface.py:252`,
  `tests/test_ci_makefile.py:478-480`, `tests/test_agent_artifacts.py:433`,
  `pyproject.toml:162-166`.
- Tick each criterion only as it is verified. This package's header stays
  `DRAFT`; the pull request, into `dev`, asks the maintainer to settle it at
  merge. This package leaves the tree in the 0.4.0 post-release sweep, with
  the 0.3.0 pair.
- **Gate:** `make pre-pr`
