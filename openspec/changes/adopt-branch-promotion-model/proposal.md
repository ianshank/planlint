# Change: Adopt a Branch Promotion Model — dev → qa → main, One Required Check, Tags Only on Production

## Why

This repository runs trunk-only: every pull request squashes into `main`,
`main` is what a release tag is cut from, and the 0.3.0 runbook ends with a
commit pushed to `main` *after* the tag. Nothing separates "merged" from
"release candidate" from "released", so the full release ladder — the one
`release.yml`'s `gate` and `build` jobs run — is exercised for the first time
on the tag itself, against an index whose versions are immutable. And nothing
in the tree stops a `v*` tag from being pushed on a commit that never reached
`main` at all: the release workflow would gate, build and publish it.

This package moves the project to three long-lived branches — `dev`
(integration), `qa` (release candidate) and `main` (production only) — with
the topology declared once in `pyproject.toml`, a stdlib gate script that
interprets it, a CI release tier that runs exactly what the release workflow
runs whenever a pull request targets `qa` or `main`, one aggregating status
check that rulesets can require, and a tag-ancestry check in the release
gate. Creating the branches, the rulesets and the environment rule are the
owner's actions outside the tree, after this lands and after `v0.3.0` is
tagged on trunk.

**Evidence:** measured on `claude/branch-promotion-model`, 2026-10-07; a
sibling package landing first may move a line without moving the fact.

- **The push trigger names a branch that does not exist.** `ci.yml`'s
  `on.push.branches` is `[main, master]`; this clone's
  `.git/refs/remotes/origin/` holds `main` and topic namespaces and no
  `master`, and no other file in the tree names one.
- **A tag on any commit publishes.** `.github/workflows/release.yml` triggers
  on `push: tags: "v*"`; `gate` checks out with `fetch-depth: 0` and runs
  `make pre-pr`, and no step asks whether the tagged commit is on `main`.
  `publish` is `if: github.ref_type == 'tag'` and nothing else.
- **The release ladder first runs on the tag.** `release.yml`'s `build` job is
  the only place the installed `planlint` console script is exercised from a
  wheel (its own header says so), as an inline shell block. `ci.yml`'s
  `packaging` job builds the wheel and runs `tools/check_wheel_metadata.py`
  but installs nothing; `make pre-pr` is run by `release.yml` and by no job in
  `ci.yml` (`make stage-citations`, "run directly by" column).
- **Nothing a ruleset could require is safe to require.** `ci.yml`'s
  `graph-diff` job is `if: github.event_name == 'pull_request'`, so it is
  skipped on every push. GitHub reports a job skipped by its `if:` as
  success to a required status check, so requiring jobs by name either
  breaks on the conditional ones or passes a skip that should not have
  happened.
- **The runbook commits to `main` after the tag.**
  `docs/distribution-plan.md` §3 step 8, "The post-tag commit", flips every
  own-action ref to `@v0.3.0` in a commit on `main` after the tag is pushed.
  Under a production-only `main` that commit has nowhere to go.
- **The workflow set and its shape are pinned.**
  `tests/test_release_surface.py::test_every_workflow_is_scanned_by_the_threshold_guard`
  asserts the workflow directory holds exactly `ci.yml` and `release.yml`;
  `tests/test_workflow_posture.py::test_every_job_in_every_workflow_has_a_timeout_inside_the_range`
  requires a `timeout-minutes` on every job, which GitHub does not allow on
  a job that calls a reusable workflow;
  `tests/test_workflow_pins.py::test_every_composite_action_directory_is_watched_by_dependabot`
  requires a Dependabot directory for every composite action.
- **The release workflow's smoke venv is load-bearing.**
  `tests/test_release_surface.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
  asserts `python -m venv` inside `build`, and the "Confirm the tag matches
  the packaged version" step reads `/tmp/smoke/bin/planlint --version`.
- **`publish`'s comment describes a permission it does not hold.** Its
  job-level `permissions:` block is `id-token: write` alone, under a comment
  saying nothing else in the job "needs more than the top-level contents:
  read". A job-level block replaces the workflow's map rather than adding to
  it, so the job holds no `contents` permission at all.
- **The config reader reads integers only.** `tools/_common.py`'s
  `read_pyproject_int` matches `key = <digits>`; a branch name needs a string
  sibling on the same stdlib, 3.10-safe, table-aware loop.
- **Branches and tag at drafting.** This clone's refs carry no `dev` or `qa`
  branch and no `v0.3.0` tag (`.git/refs/tags/` holds `v0.1.0` only).

## What Changes

- `pyproject.toml`: a `[tool.specgraph.promotion]` table with four string keys
  — `integration_branch = "dev"`, `candidate_branch = "qa"`,
  `production_branch = "main"`, `hotfix_prefix = "hotfix/"` — and a comment
  naming this package and the one literal copy (`ci.yml`'s push branches).
- `tools/_common.py`: `read_pyproject_str(pyproject, section, key)`, the
  string sibling of `read_pyproject_int` on the same loop; `None` when the
  file, table, key or value is absent.
- `tools/check_promotion.py` (new, stdlib-only): subcommands `branches`
  (print the roles), `route` (judge a pull request's base and head, compute
  the release tier, write it to `$GITHUB_OUTPUT`), `tag-ancestry` (is the
  tagged commit an ancestor of `origin/<production>`, optionally fetching
  first) and `aggregate` (judge `toJSON(needs)` read on stdin). Exit 0 pass,
  1 refusal, 2 could-not-run; logging through the `planlint.tools` logger, so
  `PLANLINT_LOG_LEVEL=DEBUG` shows what was read.
- `tools/smoke_wheel.py` (new, stdlib-only): install the single wheel in a
  dist directory into a clean venv and run its console script — `--version`,
  `--target . detect`, `--target . validate --fail-on ERROR` — plus any
  repeatable `--expect PATH=EXITCODE` probes.
- `.github/workflows/ci.yml`: push branches become `[main, qa, dev]`;
  three new jobs — `promotion` (runs `route`, always), `release-tier` (needs
  `promotion`, runs when its output says so: `make pre-pr`, sdist and wheel
  build, `tools/check_wheel_metadata.py`, `tools/smoke_wheel.py` with the
  `passing`/`failing` action fixtures as probes) and `ci-ok` (`if: always()`,
  needs every other job, runs `aggregate`). Every new job has a timeout in the
  configured range and no permission beyond the workflow's read-only default.
- `.github/workflows/release.yml`: `gate` gains a tag-only step running
  `check_promotion.py tag-ancestry --fetch`; `build`'s smoke step calls
  `tools/smoke_wheel.py`, keeping the venv the tag-versus-version step reads;
  `publish`'s block gains `contents: read` and its comment is corrected. No
  new workflow file.
- `tests/test_promotion.py`, `tests/test_smoke_wheel.py` (new) and new tests
  in `tests/test_ci_workflow.py` and `tests/test_release_surface.py`; the two
  new scripts join `test_gate_script_is_runnable_as_a_script`'s list.
- `docs/hooks.md`: CI table rows for `promotion`, `release-tier` and `ci-ok`,
  and a "Branching and promotion" section stating the model, the merge
  methods, the required check and the base-retarget limitation.
- `docs/distribution-plan.md`: the §3 runbook stays the 0.3.0 trunk release
  it was written for; a paragraph after it states that from the next release
  the tag goes only on a `main` merge commit and the post-tag ref flip moves
  into a release-prep pull request on `dev`.
- `[tool.specgraph.promotion] enforce_routes = "false"` for the bootstrap
  window: until `dev` and `qa` exist, `route` reports a refused route as a
  `WARN` rather than failing every pull request into `main`; Phase 2 sets it
  to `"true"` (DEC-BPM-013).
- `.github/pull_request_template.md`: a checkbox for the base branch.
- `CHANGELOG.md` `[Unreleased]`: an entry for this change.

## Non-Goals

- **No branch, ruleset or environment change from inside the tree.** Creating
  `dev` and `qa`, the rulesets for `main`, `qa` and `dev` (required check
  `ci-ok`, merge methods, no force-push or deletion), the `v*` tag ruleset,
  and the `pypi` environment's deployment rule for `v*` tags are the owner's
  actions in repository settings. They are listed in `tasks.md` as Phase 2,
  after this merges and after `v0.3.0` ships.
- **No Dependabot `target-branch` yet.** Dependabot reads its configuration
  from the default branch, so `target-branch: dev` would take effect the
  moment this merges, before `dev` exists. It moves in Phase 2 with the
  branches.
- **No change of default branch.** `main` stays the default (DEC-BPM-009).
- **No reusable workflow, composite action or third workflow file.** The
  shared step is a stdlib script both workflows call (DEC-BPM-005).
- **No change to any rule, `make` target or existing job.** The `RULES`
  tuple, `README.md`'s rules table, `tests/baseline_rules.json` and the
  `Makefile` are untouched; no existing job is renamed, removed or given a
  new condition.
- **No `edited` trigger.** A pull request whose base is retargeted is not
  re-judged until its next push or re-run; documented, not fixed
  (DEC-BPM-008).
- **No merge before `v0.3.0`.** The 0.3.0 release finishes on trunk under the
  runbook it was written against (DEC-BPM-010).

## Affected Capabilities

- `branch-promotion`
