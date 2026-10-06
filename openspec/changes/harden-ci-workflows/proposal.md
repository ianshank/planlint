# Change: Harden the CI Workflows — Node 24 Actions, Least Privilege, Timeouts, One Python Default

## Why

`.github/workflows/ci.yml` is the gate every change package in this repository
is held to, and the workflow itself has none of the hygiene the gates inside
it enforce on everything else. Every third-party action it runs is on a
floating major that targets a Node runtime GitHub has already removed from
its hosted runners; the workflow grants its jobs the repository's default
token permissions rather than stating any; no job has a timeout, so a hung
step holds a runner for GitHub's six-hour default; no `concurrency` group
exists, so every push to a pull request queues a full matrix behind the last
one; and the single-interpreter Python version is a string literal repeated
in every job, in the release workflow, in the composite action and in the
Dockerfile, with nothing holding the copies equal. Python 3.14 has been final
for a year and appears in neither the matrix nor the classifiers. The
Dockerfile runs as root from a tag-pinned base that no update bot watches.

Seven Dependabot pull requests have proposed the action bumps since
2026-09-19, against a base two merges behind `main`, and none has been
merged. This package lands the whole posture at once — the bumps, the
permissions, the timeouts, the concurrency group, the single Python default,
the 3.14 leg and the Dockerfile — with dynamic guard tests so none of it can
drift back silently. It is milestone M0, items W1.1, W1.3, W1.4, W1.6 and
W1.7, of the October 2026 reflection plan; that plan is not yet committed to
this tree, so every number below is re-measured here rather than cited from
it.

**Evidence:** (measured at `main` `9c4b6e9`, CI run #171)

- **Node 20 actions, forced onto Node 24.** Run #171's own annotations, on
  every job: "Node.js 20 is deprecated. The following actions target Node.js
  20 but are being forced to run on Node.js 24: actions/checkout@v4,
  actions/setup-python@v5, actions/upload-artifact@v4" — and
  `gitleaks/gitleaks-action@v2` on `security`. The run is green, so the
  exposure today is an untested runtime remap plus a warning per job, not an
  observed failure; the bumps close it before it becomes one. The refs:
  `actions/checkout@v4` at `ci.yml` lines 16, 48, 80, 100, 140, 168, 247, 318,
  352, 363 and `release.yml` lines 28, 49; `actions/setup-python@v5` at
  `ci.yml` lines 18, 50, 82, 102, 142, 173, 322, 353, 364, `release.yml` lines
  32, 51 and `.github/actions/planlint/action.yml` line 163;
  `actions/upload-artifact@v4` at `ci.yml` lines 124, 196, `release.yml` line
  87 and `action.yml` line 337; `actions/download-artifact@v4` at
  `release.yml` line 101; `gitleaks/gitleaks-action@v2` at `ci.yml` line 335.
  `templates/spec-gate.yml` line 52 and `README.md` line 400 ship
  `actions/checkout@v4` to adopters; `templates/spec-gate.yml` line 65 and
  `README.md` line 403 pin this repository's own action to a 40-hex SHA,
  which `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
  requires until the first public tag exists.
  The open Dependabot pull requests #28–#34 (all created 2026-09-19T13:16Z,
  base `main@c0540c4`) propose checkout 4→7, setup-python 5→7,
  upload-artifact 4→7, download-artifact 4→8 and gitleaks-action 2→3; the
  composite action's two bumps (#28, #29) are separate pull requests from the
  workflow root's, because `.github/dependabot.yml` lines 25 and 51 declare
  them as separate directories. gitleaks-action's v3 README: "v3 migrates the
  GitHub Actions runtime from Node 20 to Node 24. There are no changes to
  inputs, outputs, or behavior", and "September 16, 2026: Node 20 is removed
  from GitHub-hosted runners entirely." Its `src/index.js` and
  `src/gitleaks.js` are byte-identical between v2 and v3.
- **No stated permissions in `ci.yml`.** The file has no top-level
  `permissions:` block; the only one is job-level `contents: read` on
  `action-contract` (`ci.yml` lines 215–216), and
  `tests/test_ci_hardening.py::test_ci_workflow_has_an_action_contract_job`
  asserts that block inside that job, so it must stay. `release.yml` already
  states `contents: read` at the top (lines 20–21) and `id-token: write` on
  `publish` only (lines 98–99), pinned by
  `tests/test_agent_artifacts.py::test_release_workflow_is_gated_and_uses_trusted_publishing`.
  Three consumers of the token are known from source: gitleaks-action calls
  `GET /users/{owner}` on every event (`src/index.js`; not a repository
  permission, so a read-only token satisfies it, but the action exits 1 if
  the call fails); on a `pull_request` event it calls
  `GET /repos/{owner}/{repo}/pulls/{pull_number}/commits` with `GITHUB_TOKEN`
  (`src/gitleaks.js`), which needs `pull-requests: read`; and it lists and
  posts review comments unless `GITLEAKS_ENABLE_COMMENTS` is `"false"`,
  which would need `pull-requests: write`. `actions/upload-artifact`
  authenticates with the runner's `ACTIONS_RUNTIME_TOKEN`, not
  `GITHUB_TOKEN`, and run #171 already shows it: `action-contract` runs the
  composite action's upload step under that job's `contents: read`, green on
  all five legs. `ci.yml` line 214, immediately above `action-contract`'s
  `permissions:`, is `runs-on:` — the job's comment is lines 205–213 — and
  `release.yml`'s `publish` has no comment at all.
- **No timeouts, no concurrency.** `grep -n timeout-minutes` and
  `grep -n concurrency` over `.github/workflows/*.yml` both return nothing.
  Run #171's job durations: `test (3.10)` 2m16s, `test (3.11)` 2m14s,
  `test (3.12)` 3m41s, `test (3.13)` 2m56s, `test-windows` 5m42s,
  `coverage-tools` 2m09s, every other job between 9s and 23s, `graph-diff`
  skipped on a push. Nothing here needs more than a few minutes, and today a
  hang gets six hours.
- **The default Python is a repeated literal.** `python-version: "3.12"`
  appears as a single value on `ci.yml` lines 52, 84, 104, 144, 175, 324, 355
  and 366 — every non-matrix `setup-python` step — on `release.yml` lines 34
  and 53, as the composite action's `python-version` input default
  (`action.yml` line 46), and as the Dockerfile base `python:3.12-slim`
  (`Dockerfile` line 9). The matrix is
  `["3.10", "3.11", "3.12", "3.13"]` (`ci.yml` line 14); `pyproject.toml`
  classifies 3.10–3.13 (lines 47–50). Python 3.10 reaches end-of-life in
  October 2026 (PEP 619); 3.14 has been final since October 2025 (PEP 745)
  and is in neither. `docs/hooks.md` line 52 and `docs/aqa.md` lines 138–139
  and 257 state the 3.10–3.13 range in prose.
- **The thresholds guard is not in the way.**
  `tools/check_no_hardcoded_thresholds.py::check_workflow` (lines 92–104)
  flags exactly two shapes in a workflow: a coverage floor
  (`--cov-fail-under` or `fail[-_]under` followed by `:`/`=` and a digit, line
  99) and a tool pin (`ruff==`, `mypy==`, `pytest==` followed by a digit, line
  102). Its own comment on line 101 reads "A python-version pin is allowed
  (matrix)". Bare integers are flagged only in the Makefile
  (`_THRESHOLD_TOKEN`, line 50, via `check_makefile`). So `timeout-minutes: N`
  and an `env: PYTHON_DEFAULT: "3.12"` line pass the guard as written; it has
  nothing to learn.
- **The Dockerfile.** `Dockerfile` has no `USER` instruction, so the image
  runs as root; line 9 pins the base by tag, not digest; its own header (lines
  3–4) says the image "is not built in CI, so a pyproject change can break it
  silently"; `.dockerignore` is present. `.github/dependabot.yml` has two
  `github-actions` entries and no `docker` ecosystem, so the base would never
  be bumped even if it were pinned.
- **Where the guards go.** `tests/test_ci_hardening.py` is already 859 lines
  and holds the job-block parser `_ci_job_blocks` (line 505) that the
  existing workflow tests use; `tests/test_agent_artifacts.py` carries a
  second copy of the same parser (`_workflow_jobs`). `tests/support.py`'s
  docstring says a genuinely duplicated helper belongs there.

## What Changes

- `.github/workflows/ci.yml`: every third-party `uses:` moves to the major
  Dependabot proposes, in one batch; a top-level `permissions: contents: read`;
  a `concurrency` group keyed on the workflow and, for pull requests, the
  ref — every other event keys on its SHA — whose `cancel-in-progress` is
  the expression `${{ github.event_name == 'pull_request' }}`; a
  `timeout-minutes` literal on every job; a workflow-level
  `env: PYTHON_DEFAULT` read by every single-version `setup-python` step; the
  `security` job gains job-level `contents: read` + `pull-requests: read` with
  a comment naming the gitleaks commit listing that needs it, and
  `GITLEAKS_ENABLE_COMMENTS: "false"`; the `test` matrix gains a 3.14 leg
  through `include:` with an `experimental: true` flag and a job-level
  `continue-on-error: ${{ matrix.experimental || false }}`, flipped to a hard
  leg after one green run. `action-contract` keeps its job-level block. No
  job is renamed.
- `.github/workflows/release.yml`: the same action bumps (the
  `upload-artifact`/`download-artifact` pair moving together), a
  `timeout-minutes` on each of `gate`, `build` and `publish`, and the same
  `env: PYTHON_DEFAULT`. Its existing top-level permissions and
  `id-token: write` on `publish` grant exactly what they did; `publish`'s
  block gains the comment R-HCW-4 asks of every job-level block. No
  `concurrency` group: a tag
  push must never be cancelled, and two tags are two refs anyway.
- `.github/actions/planlint/action.yml`: `actions/setup-python` and
  `actions/upload-artifact` move to the same majors as the workflows. Inputs,
  outputs and the `python-version` default are unchanged.
- `templates/spec-gate.yml`, its byte-identical copy
  `skills/planlint-spec-governance/assets/spec-gate.yml`, and the copyable
  workflow block in `README.md`: `actions/checkout` moves with the workflows,
  so adopters are not handed the pin this package retires. Their
  `ianshank/planlint/...@<sha>` ref stays: it is owned by
  `tests/test_adopter_urls.py` and `docs/distribution-plan.md`.
- `pyproject.toml`: `[tool.specgraph] ci_job_timeout_minutes_min` and
  `ci_job_timeout_minutes_max`, the bounded range every `timeout-minutes`
  literal must fall in, read by the guard through `_common.read_pyproject_int`;
  the `Programming Language :: Python :: 3.14` classifier when the leg flips
  to hard.
- `Dockerfile`: a non-root `USER` after the install step; `FROM` pinned by
  digest with the tag kept inside the reference
  (`python:3.12-slim@sha256:…`), not in a trailing comment, which the
  Dockerfile grammar does not have.
- `.github/dependabot.yml`: a `docker` ecosystem entry for `/`, so the digest
  is maintained rather than instantly stale.
- `tests/support.py`: `workflow_job_blocks(text)`, the job-block parser moved
  out of `tests/test_ci_hardening.py`, which keeps `_ci_job_blocks` as an
  alias so its own tests and call sites are untouched.
- `tests/test_workflow_hardening.py` (new module): the dynamic guards — every
  reference to one action agrees on one ref across workflows, the composite
  action, the templates and the README snippet; `ci.yml` has top-level
  read-only permissions and no write permission under any block; every
  job-level `permissions:` block carries a comment within its job; every job in every workflow has a `timeout-minutes`
  inside the configured range; `ci.yml`'s `concurrency` never cancels a push;
  no single-value `python-version` literal outside `env:` and the matrix; the
  two workflow envs, the action default and the Dockerfile tag agree and name
  a hard matrix leg; classifiers equal the hard matrix legs; `docs/hooks.md`'s
  `test` row names the matrix's first and last versions; the Dockerfile is
  digest-pinned and non-root and Dependabot watches `docker`; and the
  thresholds guard stays quiet on `timeout-minutes:` and `PYTHON_DEFAULT:`
  lines. Every assertion message names the offending file, line and job.
- `docs/hooks.md`: the `test` row's version range; the `test-windows` and
  `coverage-tools` rows say `PYTHON_DEFAULT` rather than a literal; a short
  paragraph after the CI table on permissions, timeouts, concurrency and
  where the default Python lives.
- `docs/aqa.md`: the two prose ranges (lines 138–139, 257) when the 3.14 leg
  flips to hard, and the `actions/checkout@v4` example on line 41 with the
  bumps.
- `CHANGELOG.md` `[Unreleased]`: this change, and a `Deprecated` note that
  0.4.0 drops Python 3.10, moves `requires-python` to `>=3.11` and removes
  the `tomli` extra.

## Non-Goals

- **No SHA pinning of actions (W1.2).** Every third-party ref stays a major
  tag; `pypa/gh-action-pypi-publish@release/v1` stays a branch ref; this
  repository's own action ref in the templates and the README stays the SHA
  `test_ci_template_pins_the_floor_the_skill_enforces` requires until the
  first tag exists. Pinning to
  commit SHAs is its own package: it needs the pins resolved and verified and
  it changes how Dependabot's `groups` behave. `.github/dependabot.yml`'s
  header already records the deferral; this package does not close it.
- **No release (W1.5).** No version bump, no tag, no `requires-python`
  change. The 0.4.0 removal of Python 3.10 — with `requires-python` moving
  to `>=3.11` and the `tomli` extra going — is *announced* in the CHANGELOG's
  `[Unreleased]` section and nothing else; `requires-python = ">=3.10"`,
  `[tool.mypy] python_version = "3.10"` and the 3.10 matrix leg are untouched.
- **No change to any rule.** `openspec_graph/rules.py`'s `RULES` tuple,
  `README.md`'s rules table and `tests/baseline_rules.json` are unchanged.
  Nothing here is a spec-quality finding.
- **No change to what any `make` target does**, and no new target. The
  Makefile is not edited; `make ci` and `make pre-pr` compose exactly as
  before.
- **No job rename and no job removed**, so `docs/hooks.md`'s CI table test
  (`test_hooks_ci_table_lists_every_ci_job`) and every job-scoped assertion
  in `tests/test_ci_hardening.py` and `tests/test_agent_artifacts.py` pass
  unchanged.
- **No behaviour change for consumers of the composite action.** Its inputs,
  outputs, defaults and the no-token/no-permissions contract
  (`test_the_action_needs_no_token_and_no_privileged_permission`) are
  unchanged; only two `uses:` refs move. The new majors require a Node 24
  runner, which GitHub-hosted runners have; a self-hosted runner too old for
  Node 24 is the one consumer this could affect, and it is already receiving
  the deprecation warning today.
- **No teaching the thresholds guard new shapes.** It already passes
  `timeout-minutes:` and `PYTHON_DEFAULT:` lines; the single-literal
  `python-version` rule is a new test, not a new guard pattern.
- **No Docker build in CI.** The Dockerfile's "not built in CI" header stays
  true; the `docker build` check is a manual step at implementation,
  recorded in `tasks.md`. Wiring an image build into CI is a separate
  decision with its own runtime cost.
- **No runner-label pinning.** Run #171 also carries the notice that
  `ubuntu-latest` migrates to Ubuntu 26 from 2026-10-19; whether to pin
  `ubuntu-24.04` is a separate question this package records and does not
  answer.
- **No Dependabot `pip` ecosystem**, for the reasons
  `test_dependabot_does_not_add_a_pip_ecosystem` already pins.

## Affected Capabilities

- `ci-workflow-hardening`
