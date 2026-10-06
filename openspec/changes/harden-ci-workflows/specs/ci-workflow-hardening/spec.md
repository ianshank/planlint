# Spec: CI Workflow Hardening

> **Change:** `harden-ci-workflows`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

`.github/workflows/ci.yml` holds every change package in this repository to
a set of hard gates and holds itself to none of the equivalent hygiene. Its
third-party actions are on floating majors that target Node 20, which GitHub
removed from its hosted runners on 2026-09-16; run #171 at `9c4b6e9` is
green only because the runner forces those actions onto Node 24, and it says
so in a warning on every job. The workflow states no permissions, so each job
holds whatever the repository default grants. No job has a timeout, so a hung
step keeps a runner for the six-hour default when the slowest measured job
takes under six minutes. No `concurrency` group exists, so each push to a
pull request queues a full matrix behind the last one. The single-interpreter
Python version is the literal `"3.12"` in eight `ci.yml` steps, two
`release.yml` steps, the composite action's input default and the Dockerfile
base, with nothing holding the twelve copies equal. Python 3.14, final since
October 2025, is in neither the matrix nor the classifiers, and Python 3.10
reaches end-of-life this month. The Dockerfile runs as root from a
tag-pinned base no update bot watches.

Seven Dependabot pull requests (#28–#34) have proposed the action bumps
since 2026-09-19 against a base two merges behind `main`. Merging them one by
one would land the `upload-artifact`/`download-artifact` pair in two separate
merges and the composite action's bumps apart from the workflows', each
against a stale base.

**Evidence:** the annotations on run #171 name `actions/checkout@v4`,
`actions/setup-python@v5`, `actions/upload-artifact@v4` and
`gitleaks/gitleaks-action@v2` as "target[ing] Node.js 20 but … being forced
to run on Node.js 24". `ci.yml` has no top-level `permissions:`; its only
block is job-level `contents: read` on `action-contract` (lines 215–216),
asserted inside that job by
`tests/test_ci_hardening.py::test_ci_workflow_has_an_action_contract_job`.
`grep timeout-minutes` and `grep concurrency` over `.github/workflows/` find
nothing. Run #171's durations: the four `test` legs between 2m14s and 3m41s,
`test-windows` 5m42s, `coverage-tools` 2m09s, every other job 9s–23s.
`python-version: "3.12"` sits on `ci.yml` lines 52, 84, 104, 144, 175, 324,
355, 366, `release.yml` lines 34, 53, `action.yml` line 46; the Dockerfile
base is `python:3.12-slim` (line 9); the matrix is `ci.yml` line 14. gitleaks-
action's source calls `GET /users/{owner}` with `GITHUB_TOKEN` on every
event (`src/index.js`, exiting 1 if the call fails); on a `pull_request`
event it also calls `GET /repos/{owner}/{repo}/pulls/{pull_number}/commits`
(`src/gitleaks.js`) and, when it finds a leak, lists and posts review
comments unless `GITLEAKS_ENABLE_COMMENTS` is `"false"`. Its v3 differs from
v2 in runtime only: `src/index.js` and `src/gitleaks.js` are byte-identical
across the two majors. `templates/spec-gate.yml` line 65 and `README.md`
line 403 pin this repository's own action to a 40-hex SHA, which
`tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
requires until the first public tag exists; `README.md` line 400 ships
`actions/checkout@v4` in the same copyable block. `ci.yml` line 214,
immediately above `action-contract`'s `permissions:`, is `runs-on:`; that
job's comment is lines 205–213. `release.yml`'s `publish` (lines 92–99) has
no comment anywhere in the job.
`tools/check_no_hardcoded_thresholds.py::check_workflow` flags only a
coverage-floor literal (line 99) and a `ruff==`/`mypy==`/`pytest==` pin (line
102) in a workflow; bare integers are flagged in the Makefile alone (line 50).
`tests/test_ci_hardening.py` is 859 lines and holds `_ci_job_blocks` (line
505); `tests/test_agent_artifacts.py` holds a second copy, `_workflow_jobs`.

---

## Requirements

- R-HCW-1: Every third-party action referenced from `.github/workflows/*.yml`,
  `.github/actions/*/action.yml`, `templates/*.yml` and the workflow snippet
  in `README.md` MUST be on a release whose runtime is Node 24. A third-party
  action is any `uses:` whose ref is neither a `./` local path nor this
  repository's own `ianshank/planlint/` action. At drafting that is the major each open Dependabot
  pull request proposes: `actions/checkout` 7, `actions/setup-python` 7,
  `actions/upload-artifact` 7, `actions/download-artifact` 8,
  `gitleaks/gitleaks-action` 3. The bumps MUST land in-tree as one reviewed
  batch, not by merging the seven pull requests.
- R-HCW-2: All references to one action MUST agree on one ref across every
  file R-HCW-1 names. A leftover reference on a retired major anywhere in
  that set MUST fail the suite, naming the file and line.
- R-HCW-3: `actions/upload-artifact` and `actions/download-artifact` MUST
  move in the same commit. Both have shared one artifact backend since their
  v4 majors, and `release.yml`'s `build` uploads what `publish` downloads on
  the one path — a `v*` tag — that no CI run exercises before W1.5; moving
  them together keeps that path off a split nobody would see.
- R-HCW-4: `ci.yml` MUST declare a top-level `permissions:` block whose only
  entry is `contents: read`. No `write` permission MAY appear under any
  `permissions:` block in `ci.yml`. A job MAY widen with a job-level block
  only where a named step needs it, and every job-level `permissions:` block
  in any workflow MUST have at least one comment line above it within the
  same job block; that comment names the step or the reason, a review
  property the guard does not parse. `action-contract`'s existing job-level
  `contents: read`, and the comment that already heads that job, stay as
  they are; `release.yml`'s `publish` gains the comment its `id-token: write`
  has never had.
- R-HCW-5: The `security` job MUST carry `contents: read` and
  `pull-requests: read` at job level, for gitleaks-action's pull-request
  commit listing, and MUST set `GITLEAKS_ENABLE_COMMENTS: "false"` so no
  write permission is needed. The step keeps `GITHUB_TOKEN` in its `env:`.
- R-HCW-6: Every job in every file under `.github/workflows/` MUST declare a
  `timeout-minutes` literal, and every such literal MUST fall inside the
  range `[tool.specgraph] ci_job_timeout_minutes_min ..
  ci_job_timeout_minutes_max` in `pyproject.toml`, read at test time through
  `_common.read_pyproject_int`. A job without a timeout, or with one outside
  the range, MUST fail the suite naming the file and job.
- R-HCW-7: `ci.yml` MUST declare a top-level `concurrency:` group keyed on
  `github.workflow` and, for a `pull_request` event, `github.ref`; for every
  other event the key MUST be `github.sha`, so no two pushes to `main` ever
  share a group. Its `cancel-in-progress` MUST be an expression that is
  false for a `push` event. A literal `cancel-in-progress: true`, or a group
  that names `github.ref` without the event switch, MUST fail the suite: a
  run for a push to `main` is neither cancelled in progress nor superseded
  while pending.
- R-HCW-8: Each workflow file MUST declare a workflow-level
  `env: PYTHON_DEFAULT`, and every single-version `setup-python` step in it
  MUST read `${{ env.PYTHON_DEFAULT }}`. A `python-version:` whose value is a
  quoted version literal anywhere in a workflow outside `strategy.matrix` —
  the list and its `include:` entries — MUST fail the suite, naming the file
  and line; comment lines are not scanned. The matrix stays literal.
- R-HCW-9: The `PYTHON_DEFAULT` values of `ci.yml` and `release.yml`, the
  composite action's `python-version` input default, and the Dockerfile's
  base-image tag MUST agree, and the agreed value MUST be a hard (not
  experimental) leg of the `test` matrix. Any disagreement MUST fail the
  suite naming each source and its value.
- R-HCW-10: Python 3.14 MUST join the `test` matrix first as a leg marked
  `experimental: true` through `include:`, with `continue-on-error:
  ${{ matrix.experimental || false }}` at job level, so a config change
  cannot turn CI red. A job-level literal `continue-on-error: true` on `test`
  MUST fail the suite; the guard reads job-level keys only, so
  `action-contract`'s step-level `continue-on-error: true` is not its
  business. After one green run the flag is removed and the
  version moves into the matrix list.
- R-HCW-11: The set of `Programming Language :: Python :: 3.x` classifiers in
  `pyproject.toml` MUST equal the set of hard matrix legs, and `docs/hooks.md`'s
  `test` row MUST name the lowest and highest hard legs of the matrix; an
  `include:` leg marked experimental counts for neither. Both are read from
  the files at test time, never hard-coded.
- R-HCW-12: The 0.4.0 removal of Python 3.10 — `requires-python` moving to
  `>=3.11` and the `tomli` extra going with it — MUST be announced under a
  `Deprecated` heading in `CHANGELOG.md`'s `[Unreleased]` section and nowhere
  else in this change.
- R-HCW-13: The Dockerfile MUST switch to a non-root `USER` after its install
  step, and its `FROM` MUST pin the base by digest with the tag kept inside
  the reference (`python:3.12-slim@sha256:…`). A `FROM` without a 64-hex
  digest, or a Dockerfile with no `USER` or with `USER root`, MUST fail the
  suite.
- R-HCW-14: `.github/dependabot.yml` MUST gain a `docker` ecosystem entry for
  `/`. A digest-pinned `FROM` with no `docker` entry MUST fail the suite,
  because an unwatched digest is a pin that only gets staler.
- R-HCW-15: Every guard this spec adds MUST live in the new module
  `tests/test_workflow_hardening.py`, MUST read the files it judges rather
  than compare to a hard-coded version string, MUST strip comment lines
  before matching (as `tests/test_agent_artifacts.py`'s `_uncommented`
  does), and MUST collect every offender before asserting so one failure message lists them all, each
  with file, line and job where applicable.
- R-HCW-16: The job-block parser MUST move to `tests/support.py` as
  `workflow_job_blocks(text)`. `tests/test_ci_hardening.py` MUST keep
  `_ci_job_blocks` as an alias so its own parser tests and every existing
  call site are unchanged.
- C-HCW-1: No job in any workflow MAY be renamed or removed, no `make` target
  MAY change what it does, and the composite action's inputs, outputs and
  defaults MUST be unchanged apart from its two `uses:` refs. Every existing
  job-scoped and action-scoped test MUST pass without edit.
- C-HCW-2: `tools/check_no_hardcoded_thresholds.py` MUST NOT be edited, and
  it MUST stay quiet on every line this change adds to a workflow. No integer
  literal MAY be added to the Makefile.
- C-HCW-3: No third-party action ref MAY become a commit SHA, and
  `pypa/gh-action-pypi-publish@release/v1` MUST be untouched. SHA pinning is
  a separate package. This repository's own
  `ianshank/planlint/.github/actions/planlint@<sha>` ref in the templates and
  the README is owned by
  `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
  and `docs/distribution-plan.md`, and is not this package's to move.
- C-HCW-4: No version bump, tag, or `requires-python` change. The 3.10 leg
  stays in the matrix and `[tool.mypy] python_version` stays `"3.10"`.
- C-HCW-5: The Dockerfile stays unbuilt in CI. The `docker build` check is a
  manual step at implementation, recorded in `tasks.md`, and this spec does
  not claim the image is exercised by any gate.

---

## Decisions

- **DEC-HCW-001:** the action bumps land in-tree as one reviewed batch;
  Dependabot's seven pull requests are superseded. The alternative — merging
  #28–#34 one at a time — was rejected because their base is two merges
  behind `main`, the `upload-artifact`/`download-artifact` pair would land in
  two merges and leave `release.yml`'s tag-only path on a split no CI run
  would show (the two share a backend from v4 on, so the risk is an unseen
  state rather than a known incompatibility), and the composite action's
  bumps (#28, #29) would land apart from the workflows' because Dependabot
  treats the two directories as separate entries. Dependabot closes a
  superseded pull request itself once the ref it proposed is on `main`. The
  plan's W1.1 had gitleaks-action move last and alone so a red `security`
  job would be attributable; the batch keeps the attribution, because v3 is
  byte-identical to v2 in source apart from the runtime and its three token
  calls are enumerated in DEC-HCW-002 — a red `security` on the first run
  names itself.
- **DEC-HCW-002:** permissions start at a top-level `contents: read` and
  widen per job only on evidence. The one pre-identified widening is
  `security`. gitleaks-action's source makes three calls with `GITHUB_TOKEN`:
  `GET /users/{owner}` on every event, which is not a repository permission
  and needs no grant but exits 1 if it fails — the reason AC-HCW-25 proves
  the push to `main` as well as the pull request; a pull request's commit
  listing, which `contents: read` alone does not allow — `pull-requests`
  defaults to `none` once any block is stated — so the job declares
  `pull-requests: read` from the start rather than failing the first PR run
  to prove it; and, when it finds a leak with comments enabled, the
  review-comment listing and post. Comments are turned off with `GITLEAKS_ENABLE_COMMENTS:
  "false"` rather than granting `pull-requests: write`: the job already
  fails the build and the log carries the finding, and a fork pull request's
  token is read-only regardless. `actions/upload-artifact` needs nothing,
  and the tree already proves it: `action-contract` runs the composite
  action, whose upload step executes under that job's `contents: read`, and
  all five legs succeeded on run #171. If the first
  run proves another need, the widening is added at job level with the
  comment R-HCW-4 requires, never at the top.
- **DEC-HCW-003:** `concurrency.cancel-in-progress` is the expression
  `${{ github.event_name == 'pull_request' }}`, not `true`, and the group is
  `${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}`.
  A superseded push to a pull request should free its runner, so pull
  requests group by ref and never share one. A push to `main` is the record
  and must finish — and `cancel-in-progress: false` alone does not promise
  that: GitHub keeps the in-progress run but cancels a *pending* run in the
  group when a newer one queues, so three quick pushes to `main` would leave
  the middle commit with no run at all. Keying every non-pull-request event
  by `github.sha` gives each push to `main` its own group, which is what the
  workflow has today with no group. `release.yml` gets no group: a tag is
  its own ref and must never be cancelled.
- **DEC-HCW-004:** the default Python lives in each workflow file as
  `env: PYTHON_DEFAULT`, not as a repository variable. `vars.*` is not in the
  tree, so it cannot be grepped, diffed, or reviewed, and an unset variable
  expands to the empty string and `setup-python` then installs its own
  default silently. The `env` context is available in a step's `with:`, so
  every single-version step reads it. The matrix list stays literal because
  a matrix is a list of versions, and the one thing that must agree with it
  is the default — which R-HCW-9's test checks.
- **DEC-HCW-005:** 3.14 enters as an `include:` leg carrying
  `experimental: true`, with `continue-on-error` as a job-level expression on
  that flag, rather than as a list member with a version comparison in the
  expression. The flag names the intent, the other legs see `matrix.experimental`
  as undefined and therefore false, and the flip is one deleted key plus
  moving the version into the list. A literal `continue-on-error: true` on
  the job is forbidden because it would soften every leg at once, which is
  the opposite of a gate. Classifiers and the docs follow the flip, not the
  soft leg: a classifier is a promise, and a leg allowed to fail is not one.
  The leg's check is displayed as `test (3.14, true)` — GitHub names a
  matrix leg by its keys, and the job's `name:` is left unset because
  setting one would rename every leg's check.
- **DEC-HCW-006:** the removal of 3.10 is announced in the CHANGELOG only,
  together with what the plan's W1.6 ties to it — `requires-python` moving
  to `>=3.11` and the `tomli` extra going with it.
  PEP 619 ends upstream support this month, but the leg stays and
  `requires-python` stays because the removal is a release decision (0.4.0),
  and the release is W1.5. Announcing it now gives adopters a full minor
  version of notice.
- **DEC-HCW-007:** the Dockerfile keeps its tag inside the pinned reference —
  `python:3.12-slim@sha256:…` — rather than in a trailing comment. The
  Dockerfile grammar has no trailing comments: a `#` after an instruction is
  an argument, and `FROM image@digest # tag` fails to parse. Docker ignores
  the tag when a digest is present and Dependabot's `docker` ecosystem
  updates tag and digest as a unit, which is what makes the pin maintainable.
  The non-root user is a system user with a fixed uid and no home directory,
  created after `pip install` runs as root, so the install path is unchanged
  and only the entrypoint is unprivileged.
- **DEC-HCW-008:** the guards go in a new module,
  `tests/test_workflow_hardening.py`, not in `tests/test_ci_hardening.py`.
  That module is 859 lines across five change packages' concerns already,
  and a reader looking for "why did CI's shape fail" should find one file
  named for it. Every guard is dynamic — it reads the files and asserts a
  consistency property — because a test that says `@v7` is a second copy of
  the pin, and the next Dependabot bump would have to edit the test to pass
  it. This amends the plan's W1.3 and its M0 row, which place the guards in
  `test_ci_hardening`; the plan's text follows this decision.
- **DEC-HCW-009:** the job-block parser moves to `tests/support.py` rather
  than being imported from `tests/test_ci_hardening.py` or copied a third
  time. There is no `tests/__init__.py`; importing one test module from
  another depends on pytest's import mode and risks executing the module
  twice under two names. `tests/test_agent_artifacts.py` already holds a
  second copy, which is exactly the duplication `support.py`'s docstring
  says it exists to absorb. The alias in `test_ci_hardening.py` keeps its two
  parser tests and every call site byte-identical; `test_agent_artifacts.py`'s
  copy is left alone, because consolidating it is W7.4's business.
- **DEC-HCW-010:** `timeout-minutes` is a per-job literal bounded by a range
  in `pyproject.toml`, not a workflow-level `env`. `timeout-minutes` does not
  evaluate the `env` context, and `vars` is rejected for the reasons in
  DEC-HCW-004, so a literal is the only form that works. The values are
  about three times each job's measured duration on run #171, rounded up to a
  multiple of five — `test` 15, `test-windows` 20, `coverage-tools` 10, every
  sub-minute job 10, and in `release.yml` `gate` 30 (it runs the whole
  pre-PR ladder), `build` 15, `publish` 10. The range is two integer keys in
  `[tool.specgraph]` — `ci_job_timeout_minutes_min` and
  `ci_job_timeout_minutes_max` — because `_common.read_pyproject_int` reads
  one integer per key and that is the reader every other floor in this
  repository uses. The range is 5..45: a floor because a timeout below a
  measured duration is a flaky red, and a ceiling because it catches the
  silent mistake (a `300` typed for `30`). The ceiling sits well above the
  one unmeasured value — `release.yml`'s `gate` has never run — so the first
  time the pre-PR ladder grows, the timeout can follow without a config
  change in the same pull request. The thresholds guard is unaffected: it
  flags bare integers in the Makefile only.
- **DEC-HCW-011:** `docs/hooks.md` gets one paragraph on the workflow's
  posture — permissions, timeouts, concurrency, and where `PYTHON_DEFAULT`
  lives. The root `AGENTS.md` names that file as the contributor gate ladder;
  a contributor whose run was cancelled by the concurrency group or killed by
  a timeout needs to find the reason there, and the next person adding a
  single-version job needs to be told to read `env.PYTHON_DEFAULT` rather
  than paste a literal. The table's `test-windows` and `coverage-tools` rows
  say `PYTHON_DEFAULT` instead of a literal so the docs cannot drift from the
  workflow; only the `test` row keeps versions, and R-HCW-11 reads them from
  the matrix.
- **DEC-HCW-012:** `templates/spec-gate.yml` and the workflow snippet in
  `README.md` are inside the consistency scan. Both ship `actions/checkout@v4`
  to adopters — the README's block is the most-copied snippet in the
  repository — and fixing the pin in our workflows while handing it out
  there is the drift this package exists to close. The cost is accepted:
  Dependabot watches neither file, so a future bump of `.github/` alone will
  fail R-HCW-2 until the template (and its byte copy under `skills/`) and
  the README move too — which is the intended effect, not a false positive.
  The no-SHA assertion exempts this repository's own action: both files pin
  `ianshank/planlint/.github/actions/planlint` to a 40-hex SHA because the
  first public tag does not exist yet,
  `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
  requires exactly that, and `docs/distribution-plan.md` owns the switch to
  the tag.
- **DEC-HCW-013:** criteria that can only be observed in a GitHub Actions run
  — no Node 20 warning, a pull-request re-push cancelling its predecessor, an
  artifact upload succeeding under read-only permissions — cite `make pre-pr`
  as their stage. It is the local equivalent of what the run executes and the
  one stage a workflow (`release.yml`) invokes by name, so the citation adds
  nothing to the set of stages no workflow runs. The observation itself is
  named in the criterion and recorded in `tasks.md` with the run number.

---

## Acceptance Criteria

- [ ] **AC-HCW-1:** every third-party `uses:` under `.github/workflows/`,
  `.github/actions/`, `templates/` and in `README.md`'s workflow snippet is
  on the major its Dependabot pull request proposes, and all references to one action agree on one ref.
  (R-HCW-1, R-HCW-2)
  _Verified by:_ the action-ref consistency guard in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-2 (non-success):** a single reference left on a retired major
  — one `actions/checkout@v4` in `templates/spec-gate.yml` while the
  workflows are on a later ref — fails the suite with a message naming the
  file and line of every disagreeing reference. (R-HCW-2, R-HCW-15)
  _Verified by:_ the same guard run against a planted tree under `tmp_path` · stage: `make test`

- [ ] **AC-HCW-3:** `actions/upload-artifact` and `actions/download-artifact`
  are on their proposed majors in the same tree, in `ci.yml`, `release.yml`
  and the composite action — landed in one commit, a review property of the
  diff — and the template under `skills/` is byte-identical to
  `templates/spec-gate.yml` after the bump. (R-HCW-3, DEC-HCW-012)
  _Verified by:_ the action-ref consistency guard in `tests/test_workflow_hardening.py` for the pair, and `pytest -k test_skill_asset_matches_template` for the byte copy · stage: `make test`

- [ ] **AC-HCW-4:** `ci.yml` declares top-level `permissions:` with
  `contents: read` as its only entry, and no `write` appears under any
  `permissions:` in the file. (R-HCW-4)
  _Verified by:_ the permissions guard in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-5 (non-success):** a `ci.yml` with no top-level block, or with
  a `pull-requests: write` under any job, fails the suite naming the job; a
  job-level `permissions:` block in a job with no comment line above it
  fails naming the job. (R-HCW-4, R-HCW-15)
  _Verified by:_ the permissions guard against planted trees · stage: `make test`

- [ ] **AC-HCW-6:** `security` carries `contents: read` and
  `pull-requests: read` with the comment naming gitleaks-action's commit
  listing, and sets `GITLEAKS_ENABLE_COMMENTS: "false"`; `action-contract`
  still carries its own `contents: read` block, so the existing contract
  test is unchanged. (R-HCW-5, R-HCW-4, C-HCW-1)
  _Verified by:_ `pytest -k test_ci_workflow_has_an_action_contract_job` · stage: `make test`

- [ ] **AC-HCW-7:** `release.yml`'s top-level `contents: read` and `publish`'s
  `id-token: write` grant exactly what they did before, `publish`'s block now
  carries the comment R-HCW-4 requires, and its `gate → build → publish`
  chain is unchanged. (C-HCW-1, R-HCW-4)
  _Verified by:_ `pytest -k test_release_workflow_is_gated_and_uses_trusted_publishing` · stage: `make test`

- [ ] **AC-HCW-8:** every job in every workflow file has a `timeout-minutes`
  literal, and every value lies within
  `[tool.specgraph] ci_job_timeout_minutes_min..max` read from
  `pyproject.toml`. (R-HCW-6, DEC-HCW-010)
  _Verified by:_ the timeout guard in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-9 (non-success):** a job with no `timeout-minutes`, and a job
  with one above the ceiling, each fail the suite with a message naming the
  file and the job; a `pyproject.toml` missing either key is exit-2-style
  misconfiguration — the guard fails rather than skipping. (R-HCW-6, R-HCW-15)
  _Verified by:_ the timeout guard against planted trees · stage: `make test`

- [ ] **AC-HCW-10:** `ci.yml` has a top-level `concurrency:` whose group names
  `github.workflow`, switches on `github.event_name == 'pull_request'`
  between `github.ref` and `github.sha`, and whose `cancel-in-progress` is
  the pull-request expression; a literal `cancel-in-progress: true`, or a
  group keyed on `github.ref` with no event switch, fails the suite.
  `release.yml` has no `concurrency:`. (R-HCW-7, DEC-HCW-003)
  _Verified by:_ the concurrency guard in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-11:** `ci.yml` and `release.yml` each declare
  `env: PYTHON_DEFAULT`, every single-version `setup-python` step reads
  `${{ env.PYTHON_DEFAULT }}`, and the only quoted version literals left in
  either file are inside `strategy.matrix` — the list and the `include:`
  leg. (R-HCW-8, DEC-HCW-004)
  _Verified by:_ the Python-literal guard in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-12 (non-success):** one `python-version: "3.12"` pasted into a
  step outside `strategy.matrix` fails the suite naming the file and line;
  the same text on a comment line is not reported. (R-HCW-8, R-HCW-15)
  _Verified by:_ the Python-literal guard against a planted workflow · stage: `make test`

- [ ] **AC-HCW-13:** the two `PYTHON_DEFAULT` values, `action.yml`'s
  `python-version` default and the Dockerfile's base tag agree, and the value
  is a hard leg of the matrix; a disagreement in any one of the four fails
  naming each source and its value. (R-HCW-9)
  _Verified by:_ the Python-agreement guard in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-14:** the `test` matrix carries a 3.14 leg through `include:`
  with `experimental: true` and the job-level `continue-on-error` expression;
  a job-level literal `continue-on-error: true` on `test` fails the suite;
  the first CI run on the branch shows the leg's own result, under the check
  name `test (3.14, true)`, without turning the workflow run red. (R-HCW-10,
  C-HCW-4, DEC-HCW-005)
  _Verified by:_ the experimental-leg guard in `tests/test_workflow_hardening.py`, plus the first run on the branch read in the Actions log · stage: `make test`

- [ ] **AC-HCW-15:** after one green run the flag is removed, 3.14 is in the
  matrix list, the `3.14` classifier is present, and the classifier set
  equals the hard-leg set; `docs/hooks.md`'s `test` row names the lowest and
  highest hard legs. (R-HCW-10, R-HCW-11)
  _Verified by:_ the classifier and hooks-row guards in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-16 (non-success):** a classifier with no matrix leg, or a hard
  matrix leg with no classifier, fails the suite naming the version; a
  `docs/hooks.md` `test` row that names a range the matrix does not have
  fails naming both. (R-HCW-11, R-HCW-15)
  _Verified by:_ the classifier and hooks-row guards against planted files · stage: `make test`

- [ ] **AC-HCW-17:** `CHANGELOG.md`'s `[Unreleased]` section carries a
  `Deprecated` entry announcing that 0.4.0 drops Python 3.10, moves
  `requires-python` to `>=3.11` and removes the `tomli` extra, while
  `requires-python`, `[tool.mypy] python_version` and the 3.10 leg are
  unchanged in this change. (R-HCW-12, C-HCW-4, DEC-HCW-006)
  _Verified by:_ `pytest -k test_ci_workflow_has_a_windows_job` for the unchanged job shape, and the CHANGELOG entry read directly · stage: `make test`

- [ ] **AC-HCW-18:** the Dockerfile's `FROM` is `python:3.12-slim@sha256:`
  followed by a 64-hex digest, a non-root `USER` follows the install step,
  the `COPY` set is unchanged, and `.github/dependabot.yml` has a `docker`
  entry for `/`. The image is still built by no CI job — its header says so
  — and the manual `docker build` and uid check are recorded in `tasks.md`
  as the only exercise it gets. (R-HCW-13, R-HCW-14, C-HCW-5, DEC-HCW-007)
  _Verified by:_ `pytest -k "test_docker_build_context_is_sufficient_for_the_dynamic_version or test_every_composite_action_directory_is_watched_by_dependabot"` for the unchanged parts, and the Dockerfile and Dependabot guards in `tests/test_workflow_hardening.py` · stage: `make test`

- [ ] **AC-HCW-19 (non-success):** a `FROM` without a digest, a Dockerfile
  with no `USER` or with `USER root`, and a digest-pinned `FROM` with no
  `docker` Dependabot entry each fail the suite with a message naming the
  line. (R-HCW-13, R-HCW-14, R-HCW-15)
  _Verified by:_ the Dockerfile and Dependabot guards against planted files · stage: `make test`

- [ ] **AC-HCW-20:** `tools/check_no_hardcoded_thresholds.py` is unedited and
  reports PASS on the real tree with the new lines in place. (C-HCW-2)
  _Verified by:_ the guard's own PASS line on the finished tree, with the script absent from the diff · stage: `make thresholds`

- [ ] **AC-HCW-21:** no job is renamed or removed: `docs/hooks.md`'s CI table
  still lists every `ci.yml` job, and the Windows, encoding-stress and
  action-contract jobs are still found by the tests that look for them.
  (C-HCW-1)
  _Verified by:_ `pytest -k "test_hooks_ci_table_lists_every_ci_job or test_ci_workflow_has_a_windows_job or test_ci_workflow_has_an_encoding_stress_job or test_every_action_fixture_has_a_contract_leg"` · stage: `make test`

- [ ] **AC-HCW-22:** the composite action's inputs, outputs and defaults are
  unchanged and it still declares no token input and no `permissions:`; its
  only diff is two `uses:` refs. (C-HCW-1)
  _Verified by:_ `pytest -k "test_the_action_needs_no_token_and_no_privileged_permission or test_no_workflow_or_template_uses_pull_request_target"` · stage: `make test`

- [ ] **AC-HCW-23:** `tests/support.py` exposes `workflow_job_blocks(text)`,
  `tests/test_ci_hardening.py` keeps `_ci_job_blocks` as an alias, and its
  two parser tests pass unchanged. (R-HCW-16, DEC-HCW-009)
  _Verified by:_ `pytest -k "test_ci_job_blocks_returns_empty_when_jobs_key_is_absent or test_ci_job_blocks_ignores_comments_mentioning_jobs"` · stage: `make test`

- [ ] **AC-HCW-24:** the rule set is unchanged, the Makefile is unedited, and
  no third-party action ref is a commit SHA — this repository's own action
  ref in the templates and the README stays the SHA `tests/test_adopter_urls.py`
  requires; `pypa/gh-action-pypi-publish@release/v1` is untouched. (C-HCW-3,
  DEC-HCW-001, DEC-HCW-012)
  _Verified by:_ `pytest -k test_rule_set_matches_baseline`, and the no-SHA assertion inside the action-ref guard · stage: `make test`

- [ ] **AC-HCW-25:** the first CI run on the branch carries no "Node.js 20 is
  deprecated" annotation on any job, every job finishes inside its
  `timeout-minutes`, the artifact uploads in `self-validate`, `graph-diff`
  and `action-contract` succeed under `contents: read`, and the `security`
  job's gitleaks step succeeds both on a pull request with
  `pull-requests: read` and on the push to `main` after merge, where
  gitleaks-action's owner lookup runs with the same token. (R-HCW-1,
  R-HCW-4, R-HCW-5, R-HCW-6, DEC-HCW-002, DEC-HCW-013)
  _Verified by:_ the run's annotations and job log, with the run number recorded in `tasks.md` · stage: `make pre-pr`

- [ ] **AC-HCW-26:** a second push to the same pull request cancels the first
  run's in-progress jobs, and a run for a push to `main` is neither cancelled
  nor left pending and superseded by a later push — each `main` push has its
  own group. (R-HCW-7, DEC-HCW-003, DEC-HCW-013)
  _Verified by:_ two consecutive pushes on the branch, and two consecutive pushes to `main`, read in the Actions log · stage: `make pre-pr`

- [ ] **AC-HCW-27 (non-success):** a planted workflow containing
  `timeout-minutes: 15`, `PYTHON_DEFAULT: "3.12"` and a `concurrency:` block
  yields no finding from `check_workflow`, while a planted
  `--cov-fail-under=90` in the same file still does, and every workflow file
  is in the guard's scan. (C-HCW-2, R-HCW-15)
  _Verified by:_ `pytest -k test_every_workflow_is_scanned_by_the_threshold_guard`, and the thresholds-quiet guard in `tests/test_workflow_hardening.py` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-HCW-1..19, 21..24, 27 — every new guard green on the real tree and red on its planted counter-example |
| Threshold guard | `make thresholds` | AC-HCW-20 — the guard is unedited and prints PASS on the finished tree |
| Self-check | `make validate` | this package validates clean against the repo's own rules (Milestone 8) |
| Full | `make pre-pr` | AC-HCW-25, 26 as the local equivalent of the observed run; full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
