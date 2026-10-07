# Spec: Branch Promotion

> **Change:** `adopt-branch-promotion-model`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The repository is trunk-only. Every pull request squashes into `main`, a
release tag is cut from `main`, and the 0.3.0 runbook pushes one more commit
to `main` after the tag. "Merged", "release candidate" and "released" are the
same branch, so the release ladder — `make pre-pr`, a wheel build, the
licence-metadata check and a clean-venv run of the installed console script —
runs together for the first time on the tag, against an immutable index. The
release workflow publishes whatever commit a `v*` tag points at, whether or
not that commit is on `main`. And no status check exists that a branch
ruleset could safely require: the conditional jobs report a skip as success.

This spec moves the project to `dev` (integration) → `qa` (release
candidate) → `main` (production only), declared once in `pyproject.toml` and
interpreted by one stdlib script; adds a CI release tier that runs the
release workflow's own checks on every pull request into `qa` or `main` and
every push to them; adds one aggregating check, `ci-ok`, as the single
required status; and refuses, in the release gate, a tag whose commit is not
on production. The branches, rulesets and environment rule are the owner's,
outside the tree, after this lands and after `v0.3.0` is tagged on trunk.

**Evidence:** `ci.yml`'s `on.push.branches` is `[main, master]` and no
`master` branch exists on `origin`. `release.yml` triggers on
`push: tags: "v*"`, its `gate` runs `make pre-pr` and nothing asks whether the
tagged commit is on `main`. `release.yml`'s `build` job is the only place the
console script is run from an installed wheel; `ci.yml`'s `packaging` job
builds and checks metadata but installs nothing, and `make stage-citations`
shows `pre-pr` run by `release.yml` alone. `ci.yml`'s `graph-diff` is
`if: github.event_name == 'pull_request'`. `docs/distribution-plan.md` §3
step 8 is a commit to `main` after the tag.
`tests/test_release_surface.py::test_every_workflow_is_scanned_by_the_threshold_guard`
pins the workflow set to `ci.yml` and `release.yml`;
`tests/test_workflow_posture.py::test_every_job_in_every_workflow_has_a_timeout_inside_the_range`
requires a timeout on every job;
`tests/test_workflow_pins.py::test_every_composite_action_directory_is_watched_by_dependabot`
requires a Dependabot directory per composite action;
`tests/test_release_surface.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
required, before this change, `python -m venv` in `build`. `release.yml`'s `publish` declares
`id-token: write` alone under a comment that assumes the top-level
`contents: read` still applies. `tools/_common.py::read_pyproject_int` reads
digits only.

---

## Requirements

- R-BPM-1: `pyproject.toml` MUST declare `[tool.specgraph.promotion]` with
  the string keys `integration_branch`, `candidate_branch`,
  `production_branch` and `hotfix_prefix`, valued `"dev"`, `"qa"`, `"main"`
  and `"hotfix/"`, and MAY declare `enforce_routes` (`"true"` or
  `"false"`, absent meaning `"true"`; DEC-BPM-013), declared `"false"` until
  Phase 2. It MUST be the single source of the topology: no script
  under `tools/` and no test MAY name a branch as a literal it then relies
  on; each reads the table.
- R-BPM-2: `tools/_common.py` MUST provide
  `read_pyproject_str(pyproject, section, key)`, stdlib-only and runnable on
  the oldest supported interpreter, on the same table-aware line scan as
  `read_pyproject_int`. It MUST return `None` when the file, the table or the
  key is absent or the value is empty.
- R-BPM-3: `tools/check_promotion.py` MUST be stdlib-only and MUST provide
  the subcommands `branches`, `route`, `tag-ancestry` and `aggregate`. Every
  subcommand MUST exit 0 on pass, 1 on a refusal and 2 when it cannot run —
  a missing or empty promotion key, unreadable input, a git error — naming
  the cause on stderr. It MUST log through the `planlint.tools` logger, so
  `PLANLINT_LOG_LEVEL=DEBUG` shows the values it read.
- R-BPM-4: `route`, given a pull request's base and head, MUST accept into
  the production branch only a head equal to the candidate branch or
  starting with the hotfix prefix; MUST accept into the candidate branch
  only a head equal to the integration branch; and MUST accept any head into
  any other base. A refusal MUST exit 1 naming the base, the head and the
  heads that base accepts -- unless `enforce_routes` is `"false"`, when it
  MUST instead print the same refusal as a `WARN` and exit 0, with the release
  tier computed exactly as when enforced. Any value other than `"true"` or
  `"false"` MUST exit 2.
- R-BPM-5: `route` MUST refuse a head from another repository into the
  candidate or production branch, whatever its name, because a fork's
  branch name is not the branch the rule means.
- R-BPM-6: `route` MUST compute a release tier, true when a pull request's
  base, or a push's ref, is the candidate or the production branch, and
  false otherwise; and when `$GITHUB_OUTPUT` is set it MUST append
  `release-tier=true` or `release-tier=false` to that file.
- R-BPM-7: `tag-ancestry` MUST exit 0 when the tagged commit is an ancestor
  of `origin/<production_branch>`, 1 when it is not, and 2 when git fails;
  with `--fetch` it MUST fetch the production branch first.
- R-BPM-8: `aggregate` MUST read the `needs` context as JSON on stdin and
  MUST fail on any job whose result is `failure` or `cancelled`, and on any
  `skipped` job not declared conditional. A job declared
  `--pull-request-only` MAY be skipped only when the event is not
  `pull_request`; a job declared `--release-tier-only` MAY be skipped only
  when the release tier is false. Any other skip MUST fail, naming the job.
- R-BPM-9: `tools/smoke_wheel.py` MUST be stdlib-only, MUST refuse with exit
  2 unless the dist directory holds exactly one wheel, MUST install it into
  a fresh venv and run that venv's `planlint` console script —
  `--version`, `--target . detect`, `--target . validate --fail-on ERROR` —
  and MUST run each repeatable `--expect PATH=EXITCODE` probe as
  `--target PATH validate --fail-on ERROR`, exiting 1 naming any probe whose
  exit code differs from the one declared.
- R-BPM-10: `ci.yml`'s `on.push.branches` MUST be exactly the three
  configured branches, and a test MUST hold that list equal to the
  promotion table; `master` is dropped.
- R-BPM-11: `ci.yml` MUST add a job `promotion` that runs `route` on every
  event and exposes the release tier as a job output; a job `release-tier`
  that needs `promotion`, runs only when that output is true, and runs
  `make pre-pr`, an sdist and wheel build, `tools/check_wheel_metadata.py`
  and `tools/smoke_wheel.py` with `tests/fixtures/action/passing` expected at
  0 and `tests/fixtures/action/failing` at 1; and a job `ci-ok` with
  `if: always()` that needs every other job in the workflow and runs
  `aggregate`, declaring each conditional job with the flag matching its
  condition. A test MUST fail when a job is missing from `ci-ok`'s needs or
  a conditional job is undeclared.
- R-BPM-12: `release.yml`'s `gate` MUST run
  `check_promotion.py tag-ancestry --fetch` in a step that runs only for a
  tag ref; `build`'s smoke step MUST call `tools/smoke_wheel.py`, the same
  tool `ci.yml`'s `release-tier` calls, with `--venv` naming the path the
  tag-versus-version step reads; `publish`'s job-level block MUST grant
  `contents: read` beside `id-token: write`, with a comment that is true of
  the block.
- R-BPM-13: `docs/hooks.md` MUST list `promotion`, `release-tier` and `ci-ok`
  in its CI table and MUST gain a "Branching and promotion" section stating
  the three roles and where they are declared; that feature pull requests
  squash into the integration branch; that integration → candidate,
  candidate → production and the back-merge from production into
  integration (on a `sync/` branch after each release) are merge commits;
  that a hotfix branch may target production and is back-merged; that
  `ci-ok` is the one required check; and the base-retarget limitation of
  DEC-BPM-008.
- R-BPM-14: `docs/distribution-plan.md`'s runbook MUST tag only a merge
  commit on the production branch and MUST commit nothing to production
  after the tag: the own-action ref flip moves into a release-prep pull
  request on the integration branch that promotes with the next release.
  `.github/pull_request_template.md` MUST carry a base-branch checkbox, and
  `CHANGELOG.md`'s `[Unreleased]` MUST carry an entry for this change.
- C-BPM-1: No new file under `.github/workflows/`, no reusable workflow and
  no composite action. No existing job MAY be renamed, removed or given a
  new condition. Every new job MUST carry a `timeout-minutes` inside the
  configured range and no permission beyond the workflow's read-only
  default.
- C-BPM-2: No rule, no `make` target and no dependency changes: the `RULES`
  tuple, `README.md`'s rules table, `tests/baseline_rules.json`, the
  `Makefile` and `[project] dependencies` are untouched, and both new scripts
  import the standard library and `tools/_common.py` only.
- C-BPM-3: The default branch stays `main`. Creating `dev` and `qa`, the
  branch and tag rulesets, the `pypi` environment's deployment rule and
  Dependabot's `target-branch` are the owner's, outside the tree, and no
  criterion below claims one before it is observed and recorded in
  `tasks.md`.
- C-BPM-4: This change MUST NOT merge before `v0.3.0` is tagged on trunk.

---

## Decisions

- **DEC-BPM-001:** three long-lived branches, with a QA tier that *is* the
  release tier. The candidate branch exists so that what the release
  workflow will run on the tag has already run, unchanged, on the commit the
  tag will sit on: a promotion pull request into `qa` or `main` runs
  `make pre-pr`, builds the wheel, checks its metadata and smokes the
  installed console script with the same tool `release.yml` calls
  (DEC-BPM-012). Rejected: `main` plus short-lived `release/*` branches. A
  release branch is cut, stabilised and merged back, which is the same
  promotion with a branch that is created and deleted each time and a ruleset
  pattern instead of a name; for a single-maintainer project with one
  release line, a standing `qa` is the simpler thing to protect, to point
  Dependabot past, and to read in a graph.
- **DEC-BPM-002:** feature pull requests squash; promotions and back-merges
  are merge commits. A squash keeps `dev`'s history one commit per change. A
  promotion squashed into `qa` or `main` would create a commit with no
  ancestry link to `dev`, so the next promotion would re-present every
  earlier change as new and the back-merge would conflict on every file a
  release touched. A merge commit keeps the production tip a descendant of
  the candidate tip, which is what makes `tag-ancestry` meaningful and what
  makes the merge-base of `dev` and `qa` the last promotion.
- **DEC-BPM-003:** one aggregating job, `ci-ok`, is the single required
  status check. GitHub reports a job skipped by its `if:` as success to a
  required check, so requiring `graph-diff` or `release-tier` by name would
  pass on a skip that should not have happened, and requiring every job by
  name makes each new job a settings change. `ci-ok` runs `if: always()` and
  needs every other job, so it runs after all of them whatever they
  concluded. The verdict lives in `aggregate` rather than in a
  `contains(needs.*.result, …)` expression because an expression cannot
  tell an expected skip from an unexpected one: `aggregate` is told which
  jobs are conditional and on what, and fails the rest.
- **DEC-BPM-004:** the topology lives in `pyproject.toml`, not in the
  workflow. The scripts that judge a route, an ancestry or a release tier
  read it there, so a rename is one table edit. The one copy GitHub forces is
  `on.push.branches`: triggers are evaluated before any job runs, so they
  cannot read a file. That literal is held equal to the table by a test
  (R-BPM-10), which is the pattern `PYTHON_DEFAULT` already follows.
- **DEC-BPM-005:** no reusable workflow and no composite action for the
  shared release-tier steps. The threshold guard's wiring test pins the
  workflow set to `ci.yml` and `release.yml`; GitHub does not accept
  `timeout-minutes` on a job that calls a reusable workflow, which the
  every-job timeout guard would then fail; and a composite action needs its
  own Dependabot directory and pins. The shared behaviour is the smoke run,
  and that is a stdlib script under `tools/` both workflows call, covered by
  the `tools/` floor and the runnable-script test like every other gate
  script.
- **DEC-BPM-006:** the tag-ancestry check runs in `release.yml`'s `gate`, in a
  step that runs only for a tag ref. In `gate` because it is the first job:
  a tag off production fails before the full ladder spends its timeout. Only
  for a tag because `workflow_dispatch` is the runbook's dry run on a
  candidate commit, which by design is not yet on production. A tag
  ruleset can restrict who may push `v*` but cannot express "this commit is
  on `main`", so the check has to be in the workflow.
- **DEC-BPM-007:** `graph-diff` on a promotion pull request diffs a whole
  release. DEC-CH-001 compares a pull request's head with its merge-base so
  the gate flags only the drift *that* pull request introduces. For a
  `dev` → `qa` or `qa` → `main` pull request, under merge-commit promotions,
  the merge-base is the previous promotion, so the diff is every change since
  the last release. That is a different meaning from DEC-CH-001's, and it is
  accepted: the promotion's change *is* the release, and a release-sized
  graph regression is exactly what a promotion should refuse. No change to
  `graph-diff` or `tools/diff_spec_graph.py`.
- **DEC-BPM-008:** no `edited` trigger. Retargeting a pull request's base is
  a `pull_request` event of type `edited`, which `ci.yml` does not listen
  for, so a pull request opened against `dev` and retargeted to `main` keeps
  the `ci-ok` verdict computed against `dev` until its next push or re-run.
  Adding `edited` reruns the whole matrix on every title or body edit; gating
  the heavy jobs off on `edited` instead produces a run in which those jobs
  are skipped and `ci-ok` has to judge the skip, where a wrong declaration
  reads as passing. The limitation is stated in `docs/hooks.md`, and the
  pull request template's base-branch checkbox asks for the base to be right
  before the first push.
- **DEC-BPM-009:** the default branch stays `main`. Dependabot, the README's
  links, the own-action references adopters copy and GitHub's landing page
  all read the default branch, and `main` remains the one branch whose tip
  is always a release. The cost is that a new pull request offers `main` as
  its base; the template checkbox, the `route` refusal and, from Phase 2,
  the `main` ruleset each catch a feature pull request aimed there.
- **DEC-BPM-010:** this change merges only after `v0.3.0` is tagged on
  trunk. The 0.3.0 runbook in `docs/distribution-plan.md` was written for
  trunk and ends with a post-tag commit on `main`; this change rewrites that
  step. Landing mid-release would leave the release half under one runbook
  and half under the other. After the tag, Phase 2 creates `dev` and `qa`
  from `main` and turns the rulesets on.
- **DEC-BPM-011:** Dependabot's `target-branch: dev` waits for Phase 2.
  Dependabot reads `.github/dependabot.yml` from the default branch, so a
  `target-branch` merged with this change would point at a branch that does
  not exist yet. The owner adds it in the same sitting that creates `dev`.
- **DEC-BPM-012:** one smoke tool for both workflows. `release.yml`'s inline
  smoke block and a second copy in `ci.yml` would drift, and the QA tier is
  only the release tier if it runs the same thing. `tools/smoke_wheel.py`
  owns the venv install and the probes; `release.yml` passes `--venv` so the
  tag-versus-version step still reads the installed script, and
  `test_release_workflow_is_gated_and_uses_trusted_publishing` now asserts
  that `build` calls the shared tool where it used to assert an inline
  `python -m venv` -- the property it pins, a clean-environment smoke of the
  wheel, is unchanged, and the venv creation itself is asserted in
  `tests/test_smoke_wheel.py`. The `passing`/`failing` fixture probes make
  the smoke prove the console script can fail a tree, not merely exit 0 on
  this one.
- **DEC-BPM-013:** the bootstrap window is handled by an enforcement switch
  in the promotion table, option (b) of the draft. Until Phase 2 creates `dev`
  and `qa`, every pull request -- this one included -- targets `main` from a
  branch that is neither `qa` nor `hotfix/*`; enforced, `route` would turn
  `promotion` and `ci-ok` red on every one of them, and a red check everyone
  learns to ignore is the habit this repository refuses. So
  `enforce_routes = "false"` ships with this change: `route` prints each
  refusal as `WARN` with its full reason and exits 0, and still computes the
  release tier, so every pull request into `main` runs `release-tier` from
  the day this merges. Phase 2 sets it to `"true"` in the change that creates
  the branches, visible in review. Absent means enforced, so a table that
  loses the key fails closed. Rejected: (a) accepting the red window, for the
  reason above; (c) `route` treating a protected base whose source branch is
  absent on `origin` as open -- it needs network access in `route`, and a
  deleted `qa` would silently open `main`.

---

## Acceptance Criteria

- [ ] **AC-BPM-1:** `check_promotion.py branches` prints the four roles read
  from `[tool.specgraph.promotion]` through `read_pyproject_str`, and a
  planted `pyproject.toml` with other values is honoured. Test: `test_promotion_config_reads_every_role_from_pyproject` in
  `tests/test_promotion.py`.
  (R-BPM-1, R-BPM-2, R-BPM-3)
  _Verified by:_ `pytest -k "test_promotion_config_reads_every_role_from_pyproject or test_read_pyproject_str_reads_exactly_the_shape_this_repo_writes"` · stage: `make test`

- [ ] **AC-BPM-2 (non-success):** a promotion table missing any one key, or
  holding an empty value, makes every subcommand exit 2 naming the key,
  never a silent default. Test: `test_promotion_config_missing_key_exits_two`. (R-BPM-2, R-BPM-3)
  _Verified by:_ `pytest -k "test_promotion_config_missing_key_exits_two or test_promotion_config_absent_file_exits_two"` · stage: `make test`

- [ ] **AC-BPM-3:** `route` accepts `qa` → `main`, `hotfix/x` → `main`,
  `dev` → `qa` and any head into `dev` or another base. Test: `test_route_allows_only_the_declared_sources_into_protected_branches`.
  (R-BPM-4)
  _Verified by:_ `pytest -k test_route_allows_only_the_declared_sources_into_protected_branches` · stage: `make test`

- [ ] **AC-BPM-4 (non-success):** `route` refuses `dev` → `main`, a feature
  branch into `main` and a feature branch into `qa`, each with exit 1 naming
  the base, the head and the accepted heads. Same test as AC-BPM-3.
  (R-BPM-4)
  _Verified by:_ `pytest -k test_route_allows_only_the_declared_sources_into_protected_branches` · stage: `make test`

- [ ] **AC-BPM-5 (non-success):** a head from another repository named `qa`
  into `main`, or named `dev` into `qa`, is refused with exit 1. Test: `test_route_rejects_a_cross_repository_head_into_a_protected_branch`.
  (R-BPM-5)
  _Verified by:_ `pytest -k test_route_rejects_a_cross_repository_head_into_a_protected_branch` · stage: `make test`

- [ ] **AC-BPM-6:** the release tier is true for a pull request based on
  `qa` or `main` and for a push to either, and false for a pull request into
  `dev` and a push to `dev`. Test: `test_route_selects_the_release_tier_for_candidate_and_production`.
  (R-BPM-6)
  _Verified by:_ `pytest -k test_route_selects_the_release_tier_for_candidate_and_production` · stage: `make test`

- [ ] **AC-BPM-7:** with `$GITHUB_OUTPUT` pointing at a file, `route`
  appends one `release-tier=` line carrying the computed value. Test: `test_route_writes_github_output`. (R-BPM-6)
  _Verified by:_ `pytest -k test_route_writes_github_output` · stage: `make test`

- [ ] **AC-BPM-8 (non-success):** `aggregate` exits 1 naming the job for a
  `failure`, a `cancelled`, and a `skipped` result on a job not declared
  conditional. Test: `test_aggregate_fails_on_failure_cancelled_and_unexpected_skip`. (R-BPM-8)
  _Verified by:_ `pytest -k "test_aggregate_fails_on_failure_cancelled_and_unexpected_skip or test_aggregate_cli_refuses_unusable_needs"` · stage: `make test`

- [ ] **AC-BPM-9:** `aggregate` exits 0 when a `--pull-request-only` job is
  skipped on a push and a `--release-tier-only` job is skipped with the
  release tier false. Test: `test_aggregate_accepts_a_conditional_job_skipped_when_its_condition_is_false`.
  (R-BPM-8, DEC-BPM-003)
  _Verified by:_ `pytest -k test_aggregate_accepts_a_conditional_job_skipped_when_its_condition_is_false` · stage: `make test`

- [ ] **AC-BPM-10 (non-success):** `aggregate` exits 1 when a
  `--pull-request-only` job is skipped on a `pull_request` event, and when a
  `--release-tier-only` job is skipped with the release tier true. Test: `test_aggregate_fails_a_conditional_job_skipped_when_its_condition_is_true`.
  (R-BPM-8, DEC-BPM-003)
  _Verified by:_ `pytest -k "test_aggregate_fails_a_conditional_job_skipped_when_its_condition_is_true or test_aggregate_names_a_declared_job_missing_from_needs"` · stage: `make test`

- [ ] **AC-BPM-11:** in a throwaway repository with an `origin` remote,
  `tag-ancestry` exits 0 for a commit on the production branch and 1 for a
  commit only on another branch, and exits 2 when git cannot resolve the
  ref. Test: `test_tag_ancestry_accepts_a_commit_on_production_and_rejects_one_off_it`.
  (R-BPM-7, DEC-BPM-006)
  _Verified by:_ `pytest -k "test_tag_ancestry_accepts_a_commit_on_production_and_rejects_one_off_it or test_tag_ancestry_fetch_failure_is_exit_two"` · stage: `make test`

- [ ] **AC-BPM-12:** `smoke_wheel.py` runs the three default invocations and
  every `--expect` probe with the venv's own `planlint` console script, not
  `python -m`. Test: `test_smoke_runs_every_probe_with_the_venv_console_script` in
  `tests/test_smoke_wheel.py`. (R-BPM-9)
  _Verified by:_ `pytest -k "test_smoke_runs_every_probe_with_the_venv_console_script or test_the_real_wheel_passes_the_shared_smoke_tool"` · stage: `make test`

- [ ] **AC-BPM-13 (non-success):** a probe whose exit code differs from its
  declared one makes `smoke_wheel.py` exit 1 naming the path, the expected
  and the observed code. Test: `test_smoke_fails_when_a_probe_exit_code_differs`. (R-BPM-9)
  _Verified by:_ `pytest -k test_smoke_fails_when_a_probe_exit_code_differs` · stage: `make test`

- [ ] **AC-BPM-14 (non-success):** a dist directory with no wheel, or with
  two, makes `smoke_wheel.py` exit 2 before creating a venv. Test: `test_smoke_requires_exactly_one_wheel`. (R-BPM-9)
  _Verified by:_ `pytest -k test_smoke_requires_exactly_one_wheel` · stage: `make test`

- [ ] **AC-BPM-15:** `ci.yml`'s push branches equal the three values of the
  promotion table, read at test time, and `master` is absent. Test: `test_ci_push_branches_match_the_promotion_config` in
  `tests/test_ci_workflow.py`. (R-BPM-10, DEC-BPM-004)
  _Verified by:_ `pytest -k test_ci_push_branches_match_the_promotion_config` · stage: `make test`

- [ ] **AC-BPM-16:** `ci-ok` runs `if: always()` and its `needs:` is every
  other job in `ci.yml`. Test: `test_ci_ok_needs_every_other_ci_job`. (R-BPM-11, DEC-BPM-003)
  _Verified by:_ `pytest -k "test_ci_ok_needs_every_other_ci_job or test_a_job_missing_from_the_aggregator_is_named"` · stage: `make test`

- [ ] **AC-BPM-17 (non-success):** a `ci.yml` job carrying an `if:` that is
  not declared to `aggregate` with the matching flag fails the suite naming
  the job. Test: `test_every_conditional_ci_job_is_declared_to_the_aggregator`.
  (R-BPM-11, R-BPM-8)
  _Verified by:_ `pytest -k test_every_conditional_ci_job_is_declared_to_the_aggregator` · stage: `make test`

- [ ] **AC-BPM-18:** `release.yml`'s `build` and `ci.yml`'s `release-tier`
  both call `tools/smoke_wheel.py`, and `release-tier` passes the `passing`
  and `failing` fixtures as probes expecting 0 and 1. Test: `test_release_and_ci_share_one_smoke_tool`. (R-BPM-11, R-BPM-12,
  DEC-BPM-012)
  _Verified by:_ `pytest -k test_release_and_ci_share_one_smoke_tool` · stage: `make test`

- [ ] **AC-BPM-19:** `release.yml`'s `gate` runs
  `check_promotion.py tag-ancestry --fetch` in a step conditioned on a tag
  ref, against the production branch read from the table. Test: `test_release_gate_checks_tag_ancestry_against_production` in
  `tests/test_release_surface.py`. (R-BPM-12, DEC-BPM-006)
  _Verified by:_ `pytest -k test_release_gate_checks_tag_ancestry_against_production` · stage: `make test`

- [ ] **AC-BPM-29:** with `enforce_routes = "false"`, a refused route --
  a feature branch into production, a fork into the candidate -- exits 0 with
  a `WARN` line carrying the full refusal and the release tier unchanged; a
  permitted route is not a warning; an absent key or `"true"` enforces; any
  other value exits 2. (R-BPM-1, R-BPM-4, DEC-BPM-013)
  _Verified by:_ `pytest -k "test_route_with_enforcement_off_warns_instead_of_failing or test_route_enforcement_defaults_on or test_route_enforcement_rejects_a_non_boolean"` · stage: `make test`

- [ ] **AC-BPM-20:** `release.yml` still chains `gate` → `build` →
  `publish`, `gate` still runs the full ladder, `build` still creates a
  venv, `publish` still holds `id-token: write` with no stored token, and the
  workflow default stays read-only; `publish`'s block now also grants
  `contents: read`, read directly. (R-BPM-12, C-BPM-1)
  _Verified by:_ `pytest -k test_release_workflow_is_gated_and_uses_trusted_publishing` · stage: `make test`

- [ ] **AC-BPM-21 (non-success):** the workflow directory still holds exactly
  `ci.yml` and `release.yml` and the threshold guard is quiet on both; every
  job, the three new ones included, carries a timeout inside the configured
  range; no `write` permission appears in `ci.yml`; and every composite
  action directory is still watched by Dependabot. That no composite action
  was added is a property of the diff, read directly. (C-BPM-1, DEC-BPM-005)
  _Verified by:_ `pytest -k "test_every_workflow_is_scanned_by_the_threshold_guard or test_every_job_in_every_workflow_has_a_timeout_inside_the_range or test_no_write_permission_anywhere_in_ci or test_every_composite_action_directory_is_watched_by_dependabot"` · stage: `make test`

- [ ] **AC-BPM-22:** `tools/check_promotion.py` and `tools/smoke_wheel.py`
  each start as `python tools/<script>.py` from a throwaway directory, and
  the `tools/` coverage floor is still met with both in the tree.
  (R-BPM-3, R-BPM-9, C-BPM-2)
  _Verified by:_ `pytest -k test_gate_script_is_runnable_as_a_script` · stage: `make test`

- [ ] **AC-BPM-23:** `docs/hooks.md`'s CI table lists every `ci.yml` job,
  `promotion`, `release-tier` and `ci-ok` included, and every row names a
  job or workflow. (R-BPM-13)
  _Verified by:_ `pytest -k "test_hooks_ci_table_lists_every_ci_job or test_every_hooks_ci_table_row_names_a_job_or_workflow"` · stage: `make test`

- [ ] **AC-BPM-24:** `docs/hooks.md`'s "Branching and promotion" section, the
  runbook in `docs/distribution-plan.md`, the pull request template's
  base-branch checkbox and the `CHANGELOG.md` entry read as R-BPM-13 and
  R-BPM-14 require — in particular, no runbook step commits to production
  after the tag. The prose is read directly; the stage proves the required
  documents are present and linked. (R-BPM-13, R-BPM-14, DEC-BPM-008)
  _Verified by:_ stage: `make docs-check`

- [ ] **AC-BPM-25 (non-success):** the rule inventory is unchanged — the live
  rule table still matches `tests/baseline_rules.json`. (C-BPM-2)
  _Verified by:_ `pytest -k test_rule_set_matches_baseline` · stage: `make test`

- [ ] **AC-BPM-26 (observed on this pull request):** the first CI run on
  this change's pull request shows `promotion`, `release-tier` and `ci-ok`
  each reaching a conclusion, with `release-tier` green, and its run number
  and each job's result recorded in `tasks.md`. `ci-ok`'s verdict on this
  run is `WARN` on `promotion` and green on `ci-ok`, per DEC-BPM-013. (R-BPM-11, DEC-BPM-003)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-BPM-27 (observed after Phase 2):** `v0.3.0` is tagged on trunk
  before this merges; `dev` and `qa` exist, created from `main`; rulesets on
  `main`, `qa` and `dev` require `ci-ok` and forbid force-push and deletion,
  with `main` and `qa` accepting merge commits and `dev` squash and merge
  commits; `enforce_routes` is `"true"`; a `v*` tag
  ruleset exists; the `pypi` environment admits `v*` tags only; and
  Dependabot targets `dev`. Each is recorded in `tasks.md` with its date.
  (C-BPM-3, C-BPM-4, DEC-BPM-010, DEC-BPM-011)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-BPM-28 (observed after Phase 2, non-success):** a feature pull
  request opened against `qa` shows `promotion` red and `ci-ok` red and
  cannot merge; a `dev` → `qa` pull request runs `release-tier` and shows
  `ci-ok` green. Both run numbers are recorded in `tasks.md`. (R-BPM-4,
  R-BPM-11, DEC-BPM-001)
  _Verified by:_ stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-BPM-1..23, 25, 29 — the topology is read, every route, tier, aggregate and ancestry verdict holds with its counter-example, the smoke tool is shared, the workflow shape guards stay green |
| Docs | `make docs-check` | AC-BPM-24 — the branching section, runbook, template and changelog are present and linked |
| Self-check | `make validate` | this package validates clean against the repo's own rules |
| Full | `make pre-pr` | AC-BPM-26..28 — the local equivalent of the release tier, which `ci.yml` now runs by name; the observations recorded in `tasks.md` |

## Open Questions

None open. DEC-BPM-013 (the bootstrap window) is resolved under Decisions.
