# Tasks: harden-ci-workflows

Measured at `main` `9c4b6e9`, CI run #171 (`databaseId` 37505111947). Every
number below is re-checked against the tree before the milestone that uses
it; a sibling package landing first may move a line number without moving
the fact.

## Milestone 1 — Guard scaffolding, before any workflow edit  [DONE]

- `tests/support.py`: add `workflow_job_blocks(text) -> dict[str, str]`,
  moved verbatim from `tests/test_ci_hardening.py::_ci_job_blocks` (line 505
  at `9c4b6e9`) with its docstring, including the DEC-AQA-005 note on why it
  is a line scan rather than PyYAML (R-HCW-16, DEC-HCW-009).
- `tests/test_ci_hardening.py`: add `workflow_job_blocks` to the existing
  `from tests.support import …` line at the top of the module (a mid-module
  import is `E402` under the `E4` family `make lint` selects) and replace the
  function with `_ci_job_blocks = workflow_job_blocks` where it stood.
  Nothing else in the module changes;
  `test_ci_job_blocks_returns_empty_when_jobs_key_is_absent` and
  `test_ci_job_blocks_ignores_comments_mentioning_jobs` keep exercising the
  alias (AC-HCW-23).
- `pyproject.toml`: under `[tool.specgraph]`, add `ci_job_timeout_minutes_min
  = 5` and `ci_job_timeout_minutes_max = 45` with a comment recording the
  run #171 durations they bound (`test-windows` 5m42s is the slowest measured
  job; `release.yml`'s `gate` at 30 is the one unmeasured value and sits
  under the ceiling with room) and
  why two keys rather than an inline table: `_common.read_pyproject_int`
  reads one integer per key (DEC-HCW-010).
- `tests/test_workflow_hardening.py` (new module): module docstring naming
  this package; `REPO_ROOT`, `WORKFLOWS`, `ACTION_YML`, `DOCKERFILE`,
  `DEPENDABOT`, `TEMPLATES`, `README` constants; a `_uses_refs(paths) ->
  list[(path, lineno, owner_repo, ref)]` helper that strips comment lines
  first and skips `./` local actions and this repository's own
  `ianshank/planlint/` action (its SHA ref is `tests/test_adopter_urls.py`'s
  to police); a `_quoted_version_literals(path)` helper returning
  `(lineno, value)` for every `python-version:` on a non-comment line whose
  value is a quoted `\d+\.\d+` outside `strategy.matrix` — the list and its
  `include:` entries; `_matrix_versions(ci_text) -> (hard: set,
  experimental: set)` reading both the list and `include:` entries; a
  `_job_level_keys(block)` reader that looks only at keys at job indentation,
  so `action-contract`'s step-level `continue-on-error: true` never trips
  the experimental-leg guard; `_timeout_range()` reading
  the two keys through `load_tool("_common", "_common.py").read_pyproject_int`
  and failing (not skipping) when either is `None`. Every guard collects a
  list of offenders and asserts `not offenders` with the joined list as the
  message (R-HCW-15).
- Planned test functions, named here so the spec's stage-only citations can
  be re-pointed when they exist (AC-HCW-1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13,
  14, 15, 16, 18, 19, 24, 27):
  `test_every_reference_to_one_action_agrees_on_one_ref`,
  `test_a_leftover_retired_major_is_reported_with_file_and_line`,
  `test_no_third_party_action_ref_is_a_commit_sha`,
  `test_ci_declares_read_only_permissions_at_the_top`,
  `test_no_write_permission_anywhere_in_ci`,
  `test_every_job_level_permissions_block_carries_a_comment`,
  `test_every_job_in_every_workflow_has_a_timeout_inside_the_range`,
  `test_a_job_without_a_timeout_is_named`,
  `test_a_timeout_above_the_ceiling_is_named`,
  `test_a_missing_timeout_range_key_fails_rather_than_skips`,
  `test_ci_concurrency_never_cancels_a_push`,
  `test_release_has_no_concurrency_group`,
  `test_no_quoted_python_version_literal_outside_env_and_matrix`,
  `test_a_pasted_python_literal_is_named_with_file_and_line`,
  `test_the_default_python_agrees_across_workflows_action_and_dockerfile`,
  `test_the_default_python_is_a_hard_matrix_leg`,
  `test_the_experimental_leg_is_an_expression_not_a_job_literal`,
  `test_classifiers_equal_the_hard_matrix_legs`,
  `test_hooks_test_row_names_the_matrix_bounds`,
  `test_dockerfile_from_is_digest_pinned_with_the_tag_in_the_reference`,
  `test_dockerfile_switches_to_a_non_root_user_after_install`,
  `test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry`,
  `test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency`.
  Write each guard first against the current tree so its red state is seen
  once (the current `ci.yml` has no timeouts, no top-level permissions, no
  concurrency and eight literals), then land the milestones below and watch
  each go green.
- **Gate:** `make test`

## Milestone 2 — The action bumps, as one batch  [DONE]

- `.github/workflows/ci.yml`: `actions/checkout@v4` → `@v7` at lines 16, 48,
  80, 100, 140, 168, 247, 318, 352, 363; `actions/setup-python@v5` → `@v7` at
  lines 18, 50, 82, 102, 142, 173, 322, 353, 364; `actions/upload-artifact@v4`
  → `@v7` at lines 124, 196; `gitleaks/gitleaks-action@v2` → `@v3` at line 335
  (R-HCW-1).
- `.github/workflows/release.yml`: `actions/checkout@v4` → `@v7` (lines 28,
  49); `actions/setup-python@v5` → `@v7` (lines 32, 51);
  `actions/upload-artifact@v4` → `@v7` (line 87) **and**
  `actions/download-artifact@v4` → `@v8` (line 101) in the same commit
  (R-HCW-3). `pypa/gh-action-pypi-publish@release/v1` (line 106) untouched
  (C-HCW-3).
- `.github/actions/planlint/action.yml`: `actions/setup-python@v5` → `@v7`
  (line 163); `actions/upload-artifact@v4` → `@v7` (line 337). Nothing else in
  the file changes (C-HCW-1, AC-HCW-22).
- `templates/spec-gate.yml`: `actions/checkout@v4` → `@v7` (line 52); line
  65's `ianshank/planlint/...@a1b686…` stays; copy the file over
  `skills/planlint-spec-governance/assets/spec-gate.yml` so
  `test_skill_asset_matches_template` stays green (DEC-HCW-012, AC-HCW-3).
- `README.md`: the copyable workflow block's `actions/checkout@v4` (line 400)
  → `@v7`; its `ianshank/planlint/...@a1b686…` line (403) stays, owned by
  `test_ci_template_pins_the_floor_the_skill_enforces`. `docs/aqa.md` line
  41's `actions/checkout@v4` example → `@v7` (prose, not scanned)
  (DEC-HCW-012, C-HCW-3).
  `github/codeql-action/upload-sarif@v3` (line 82) is already the current
  major and is not in any Dependabot pull request; leave it.
- Before committing, confirm each target major exists and is the one
  Dependabot proposed by reading the seven pull requests' diffs (#28–#34);
  do not merge them. Confirmed at implementation from the pull requests'
  titles and head branches: checkout 4→7 (#31), setup-python 5→7 (#32, #28
  for the composite action), upload-artifact 4→7 (#34, #29), download-artifact
  4→8 (#33), gitleaks-action 2→3 (#30). After this lands on `main`, confirm Dependabot closes
  all seven as superseded; close any it does not, with a comment naming this
  package (DEC-HCW-001).
- **Gate:** `make test`

## Milestone 3 — Permissions, timeouts, concurrency  [DONE]

- `.github/workflows/ci.yml`: after `on:`, add top-level
  `permissions:` with `contents: read` only, then `concurrency:` with
  `group: ${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}`
  and `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`, each
  with a short comment saying why — for the group, that a pending `main` run
  would otherwise be superseded by the next push (R-HCW-4, R-HCW-7,
  DEC-HCW-002, DEC-HCW-003).
- `.github/workflows/ci.yml`: `timeout-minutes:` on every job, placed
  directly under `runs-on:` — `test` 15, `test-windows` 20, `coverage-tools`
  10, and 10 on `encoding-stress`, `self-validate`, `packaging`, `graph-diff`,
  `action-contract`, `security`, `docs` (R-HCW-6, DEC-HCW-010).
- `.github/workflows/ci.yml`, `security` job: a job-level `permissions:` block
  with `contents: read` and `pull-requests: read`, preceded by the comment
  "gitleaks-action looks the repository owner up and, on `pull_request`
  events, lists the pull request's commits through the API; nothing else
  here needs more than contents: read";
  on the gitleaks step's `env:`, add `GITLEAKS_ENABLE_COMMENTS: "false"` with
  a comment that the build failing is the report and a write permission is
  not worth a comment (R-HCW-5). `GITHUB_TOKEN` stays.
- `.github/workflows/ci.yml`, `action-contract`: leave its `permissions:`
  block and the comment that heads the job exactly as they are (`ci.yml`
  lines 205–216); `test_ci_workflow_has_an_action_contract_job` asserts
  `contents: read` inside the job block (AC-HCW-6).
- `.github/workflows/release.yml`: `timeout-minutes:` — `gate` 30, `build`
  15, `publish` 10. No `concurrency:` block. Top-level `permissions:` and
  `publish`'s `id-token: write` grant what they did; above `publish`'s
  `permissions:` add the comment R-HCW-4 requires — trusted publishing mints
  the OIDC token through `id-token: write`, and nothing else in the job
  needs more than the top-level `contents: read` (AC-HCW-7).
- Confirm `python tools/check_no_hardcoded_thresholds.py` still prints PASS;
  the guard's workflow scan flags only a coverage-floor literal and a tool
  pin, so nothing above should register (C-HCW-2, AC-HCW-20).
- **Gate:** `make thresholds`, then `make test`

## Milestone 4 — One Python default per workflow  [DONE]

- `.github/workflows/ci.yml`: a workflow-level `env:` block with
  `PYTHON_DEFAULT: "3.12"` and a comment: the single-interpreter version
  lives here and nowhere else in this file; the matrix list is the other
  place a version is written on purpose. Replace `python-version: "3.12"` with
  `python-version: ${{ env.PYTHON_DEFAULT }}` at lines 52, 84, 104, 144, 175,
  324, 355, 366 (R-HCW-8, DEC-HCW-004).
- `.github/workflows/release.yml`: the same `env:` block; replace the literal
  at lines 34 and 53.
- `.github/actions/planlint/action.yml`: no change — the `python-version`
  input default (line 46) is the action's own contract and is one of the four
  values the agreement guard reads (R-HCW-9).
- `docs/hooks.md`: the `test-windows` and `coverage-tools` rows read
  `(PYTHON_DEFAULT)` in place of `(3.12)`; add the posture paragraph after
  the table: top-level read-only permissions and where a job widens them,
  the per-job timeouts and the range in `pyproject.toml`, the concurrency
  group — pull requests by ref so a re-push supersedes its predecessor,
  everything else by SHA so a `main` run is neither cancelled nor left
  pending — that an `include:` leg marked experimental is advisory and not
  listed in the `test` row until it is hard, and that a new single-version
  job reads `env.PYTHON_DEFAULT` (DEC-HCW-011).
- Confirm the `encoding-stress` job's own `env:` (`PYTHONIOENCODING`,
  `PYTHONUTF8`) does not shadow the workflow-level value — a job-level `env`
  adds keys, it does not replace the map.
- **Gate:** `make test`

## Milestone 5 — Python 3.14 as an experimental leg  [DONE]

- `.github/workflows/ci.yml`, `test` job: under `strategy.matrix`, add
  `include:` with one entry `python-version: "3.14"` and `experimental:
  true`; add `continue-on-error: ${{ matrix.experimental || false }}` at job
  level with a comment naming guardrail 4 — a config change never turns CI
  red — and that the flag is removed after one green run (R-HCW-10,
  DEC-HCW-005). The list stays `["3.10", "3.11", "3.12", "3.13"]` for now.
- `docs/hooks.md`: the `test` row stays `(3.10–3.13)`. The hooks-row guard
  reads the lowest and highest *hard* legs, and an advisory leg is not a
  promise; the posture paragraph from Milestone 4 already says so (R-HCW-11,
  DEC-HCW-005).
- Push, and record the run number of the first run showing the 3.14 leg in
  this file (recorded under Milestone 8 with the rest of the run evidence). If the leg is red, the failure is the information: fix it in a
  follow-up before Milestone 7; the job stays green either way.
- **Gate:** `make test`

## Milestone 6 — Dockerfile and its update bot  [DONE]

- `Dockerfile`: line 9 becomes `FROM python:3.12-slim@sha256:<digest>`, tag
  kept inside the reference (DEC-HCW-007). The digest resolved from the
  drafting environment on 2026-10-06 for the multi-arch index is
  `sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f`;
  re-resolve at implementation (`docker buildx imagetools inspect
  python:3.12-slim`, or the registry manifest HEAD) because the image
  rebuilds often, and use whatever is current. Add a comment above the line:
  the digest is the pin, the tag is for readers and for Dependabot, which
  moves both together.
- `Dockerfile`: after `RUN pip install --no-cache-dir .` and before
  `WORKDIR /repo`, add `RUN useradd --system --uid 10001 --no-create-home
  planlint` and `USER planlint`, with a comment: the CLI only reads the tree
  it is pointed at, so the entrypoint has no reason to be root; the install
  above still runs as root (R-HCW-13). `COPY` lines unchanged
  (`test_docker_build_context_is_sufficient_for_the_dynamic_version`).
- `Dockerfile`: update the header comment's "This image pins a Python
  version" sentence to say the version is `PYTHON_DEFAULT`'s and the
  agreement guard holds them equal.
- `.github/dependabot.yml`: a third entry, `package-ecosystem: "docker"`,
  `directory: "/"`, weekly, labels `dependencies` and `docker` in the shape
  of the two existing entries, `commit-message.prefix: "build"`, with a
  comment that a digest nobody bumps is a pin that only gets staler
  (R-HCW-14). Dependabot ignores a label the repository has not created —
  #28–#34 carry none of the labels the file already asks for — so the labels
  are a request recorded for the maintainer in Milestone 8, not a guarantee. Update the header's "Scope is
  deliberately narrow: GitHub Actions only" sentence.
- Manually: `docker build -t planlint .` then `docker run --rm -v
  "$PWD":/repo planlint --target /repo validate --fail-on ERROR`, and
  `docker run --rm --entrypoint id planlint` showing uid 10001. Record the
  result here; this is the only check the image gets (C-HCW-5).
- Recorded at implementation (2026-10-06): the digest re-resolved from the
  registry index for `python:3.12-slim` is unchanged from drafting,
  `sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f`.
  The manual build was **not run**: the implementation environment has a
  `docker` binary but no reachable daemon. The Dockerfile's shape (digest
  pin, tag in the reference, `USER` after the install, `COPY` set) is held
  by the guards; the build and the uid check remain the maintainer's to run
  once, and this bullet is updated with the result.
- `CHANGELOG.md`, `[Unreleased]` (moved here from Milestone 7 so the entry
  describes what this pull request ships): a `Changed` entry for this
  package and the `Deprecated` entry R-HCW-12 requires; Milestone 7 amends
  the 3.14 line when the leg flips.
- **Gate:** `make test`

## Milestone 7 — Flip 3.14 to a hard leg, after one green run  [DONE]

- Precondition: the run recorded in Milestone 5 shows the 3.14 leg green. If
  not, stop here; the package ships with the leg advisory and this milestone
  is re-opened when it is.
- `.github/workflows/ci.yml`, `test` job: move `"3.14"` into the matrix list,
  delete the `include:` block and the `continue-on-error` line (R-HCW-10).
- `pyproject.toml`: add `"Programming Language :: Python :: 3.14"` after the
  3.13 classifier (line 50). `requires-python`, `[tool.mypy] python_version`
  and the `UP` ruff floor unchanged (C-HCW-4, AC-HCW-15).
- `docs/hooks.md`: the `test` row becomes `(3.10–3.14)`; `docs/aqa.md` lines
  138–139 and 257 become `3.10–3.14` (R-HCW-11).
- `CHANGELOG.md`, `[Unreleased]`: an entry for this package under `Changed`
  (actions on Node 24 majors, read-only permissions, timeouts, concurrency,
  `PYTHON_DEFAULT`, the 3.14 leg, the Dockerfile) and a `Deprecated` entry:
  0.4.0 drops Python 3.10, moves `requires-python` to `>=3.11` and removes
  the `tomli` extra; PEP 619 ends upstream support in October 2026; nothing
  changes until that release (R-HCW-12, DEC-HCW-006). `CHANGELOG.md` line 1427's historical `(3.10–3.13)` is a
  dated record and stays.
- **Gate:** `make pre-pr`

## Milestone 8 — Confirm and record

- Re-point every stage-only citation in
  `specs/ci-workflow-hardening/spec.md` to the test function that now
  verifies it, keeping the stage; run
  `python -m pytest tests/test_spec_test_citations.py -q` and confirm every
  selector resolves.
- Recorded: the first full run on the branch with every Milestone 1–6
  change in place is run #37522794352 (head `b658242`, a pull request). Every job
  green; the `docs` job's full log shows `GITHUB_TOKEN Permissions:
  Contents: read, Metadata: read`, both actions downloaded on their new
  majors, and no "Node.js 20 is deprecated" line anywhere; `security` ran
  gitleaks-action v3 on the pull request under `pull-requests: read`,
  scanned six commits, found no leaks, uploaded its SARIF and logged
  "skipping comments"; `self-validate`, `graph-diff` and all five
  `action-contract` legs uploaded their artifacts under `contents: read`.
  Durations, every one inside its timeout: `test` legs 1m42s–3m44s,
  `test (3.14, true)` 2m26s (job 112472177646, success — the full suite with
  both coverage floors met), `test-windows` 6m00s, `coverage-tools`
  3m34s, every other job under 25s. The push-to-`main` half of AC-HCW-25
  and the two-pushes observation of AC-HCW-26 are recorded after merge.
- Recorded: after the 3.14 flip and the review-round fixes, run
  #37526162132 (head `50ac12a`, the final head of the pull request) is
  green on every job, with `test (3.14)` a hard leg. Pushing `50ac12a` while
  run #37525890760 (head `109ca5b`) was in progress cancelled that run
  within a minute (conclusion `cancelled` at 20:24:53Z) and started the new
  one — the pull-request half of AC-HCW-26, observed. The `main` half (each
  push to `main` keeping its own run) is recorded after merge.
- Record in this file the run number of the first full run on the branch
  and, from its annotations, that no job carries "Node.js 20 is deprecated"
  (AC-HCW-25), and the `security` job's result on the first push to `main`
  as well as on the pull request (AC-HCW-25); record the two consecutive
  pushes that showed a pull-request run cancelled and the two pushes to
  `main` that each kept their own run (AC-HCW-26).
- Repository settings, for the maintainer and not in this tree: create the
  `dependencies`, `github-actions` and `docker` labels `dependabot.yml` asks
  for — Dependabot ignores labels that do not exist, which is why #28–#34
  carry none.
- Record for the plan's M0 row, when `docs/reflection-plan-2026-10.md`
  merges: the guards live in `tests/test_workflow_hardening.py`, not
  `test_ci_hardening` (DEC-HCW-008), and gitleaks-action moved in the batch
  rather than last and alone (DEC-HCW-001).
- Run `make stage-citations` and confirm this package added no stage to the
  set no workflow invokes by name (DEC-HCW-013).
- Confirm this package validates clean under the repo's own rules
  (`planlint --target . validate --fail-on ERROR --change
  harden-ci-workflows`), then the whole tree.
- **Gate:** `make pre-pr`

## Milestone 9 — Review round 1  [DONE]

Copilot's review of the first implementation (PR #38, head `b658242`) found
three things worth fixing and one nit; all landed in one commit.

- `pyproject.toml`: `[tool.specgraph.action_major_floors]`, a per-action
  floor set to the majors this package landed plus `github/codeql-action` at
  the template's current major; `tests/test_workflow_hardening.py` gains
  `test_every_third_party_action_meets_its_major_floor`,
  `test_a_uniformly_retired_major_is_named_with_file_and_line` and
  `test_an_action_without_a_floor_is_named` (R-HCW-17, DEC-HCW-014,
  AC-HCW-28, AC-HCW-29). The agreement guard passed a tree in which every
  copy regressed together; the floor is the invariant it lacked.
- `Dockerfile`: the header names `init`, `new` and `witness` as the verbs
  that write into the mounted tree and gives the `--user "$(id -u):$(id -g)"`
  override; the `USER` comment no longer claims the CLI only reads.
  `test_dockerfile_documents_the_user_override_for_writing_verbs` and its
  planted counterpart hold it (R-HCW-13, DEC-HCW-007, AC-HCW-18, AC-HCW-19).
- The 3.14 leg was already flipped in the same push (Milestone 7).
- `tools/_common.read_json`'s DEBUG record now measures UTF-8 bytes, not
  code points (`select-zero-cost-guards`, recorded there).
- **Gate:** `make pre-pr`

