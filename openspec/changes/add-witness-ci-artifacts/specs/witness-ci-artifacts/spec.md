# Spec: Witness CI Artifacts

> **Change:** `add-witness-ci-artifacts`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Witness mode proves a cited stage ran, but only on the machine that ran it.
The store is a constant path inside the target, it is gitignored, and the
composite Action may not write into the checkout — so the one directory
`validate --require-witness` reads is the one directory a CI job can never
fill from another job. `DEC-WM-011` said the two halves would be wired with
the CI system's own artifact mechanism; nothing in the CLI or the Action lets
a downloaded artifact be read. This is peer-review finding F7 and
recommendation R7: a v2 whose differentiating feature cannot run where its
claim means anything.

**Evidence:** `openspec_graph/witness.py:37` fixes
`WITNESS_DIR_NAME = ".planlint/witnesses"`; `write_witness` (`witness.py:104`)
and `load_witnesses` (`witness.py:176`) compute `root / WITNESS_DIR_NAME`
with no override; `detect.profile` (`detect.py:715`) calls
`witness.load_witnesses(root)` with the target alone; `.gitignore:55` is
`.planlint/`. A fresh clone of a repository whose specs cite `` `make test` ``
fails `validate --require-witness` with W001 "has never been witnessed" on
every criterion; copying the origin's `.planlint/witnesses/` into the clone
makes the same command print `PASS` (both reproduced), because the record is
path-free JSON content-addressed by filename (`witness.py:68-76`, `:107`,
`:127`) and two stores merge by directory union. The scan action's header
says "Evidence lives under RUNNER_TEMP, never in the workspace"
(`.github/actions/planlint/action.yml:147-150`), `R-GA-8` forbids writes
into `GITHUB_WORKSPACE`, and the `action-contract` job asserts
`git diff --quiet --exit-code` after the action (`ci.yml:307`) — so the
action cannot download a store into the checkout, which is why
`--require-witness` is "deliberately absent" (`README.md:464`;
`tests/test_action_contract.py:289-294`; `docs/next-steps.md:220`).

Two further facts shape the design. `rules_witness.py:61` passes W001 when
`any(w.exit_code == 0 for w in at_commit)`, while `DEC-WM-019` gave W002
"every" semantics so a bad retry is not out-voted by a lucky one; this
repository runs `make test` on four interpreters (`ci.yml:14`), and under
W001 as written a failing leg is out-voted by a passing one. And the
dogfood gap is measurable: `Criterion.verified_by` for the harness dialect is
the `_Verified by:_` line alone (`parse_harness.py:55`), W001 scans only that
(`rules_witness.py:31-34`), and across the 43 spec files under
`openspec/changes/*/specs/*/` those lines cite 12 distinct stages. Five run
in `ci.yml` under their make-target name (`test`, `lint`, `typecheck`,
`coverage-tools`, `docs-check`); three run as bare commands under another
name (`self-validate` at `ci.yml:115`, `security` at `:332`, `packaging` at
`:152-155`); four never run on a pull request at all (`ci`, `pre-pr`,
`matcher-accuracy`, `security`; `make pre-pr` runs only in `release.yml:42`
on a tag). The brief's whole-file regex counted 14 stages; `e2e-live` and
`skill-catalog` appear only in prose and matrix tables, never on a
`_Verified by:_` line, so W001 never asks for them and no spec needs editing
on their account.

---

## Requirements

### The CLI

- R-WCA-1: `validate` MUST accept `--witness-dir PATH`. Passed together with
  `--require-witness`, W001 and W002 MUST read witnesses from PATH instead of
  `<target>/.planlint/witnesses/`, and MUST NOT also read the default store.
  Without `--witness-dir`, `validate`'s behaviour MUST be unchanged.
- R-WCA-2: `validate --witness-dir` without `--require-witness` MUST exit 2
  with one stderr line naming both flags and nothing on stdout, before the
  target is profiled. It MUST NOT be silently ignored.
- R-WCA-3: `validate --require-witness --witness-dir PATH` where PATH does
  not exist or is not a directory MUST exit 2 with one stderr line naming
  PATH, before any rule is evaluated, with nothing on stdout. The default
  store's absence MUST continue to produce W001 "has never been witnessed" at
  exit 1 (`AC-WM-9` is untouched).
- R-WCA-4: PATH MUST be resolved as given, against the process working
  directory, never relative to `--target`, and MAY lie anywhere outside the
  target tree.
- R-WCA-5: `witness` MUST accept `--witness-dir PATH` and write the record
  under PATH instead of the default store, creating PATH when it does not
  exist (the same `mkdir(parents=True)` the default store already receives).
  A PATH that exists and is not a directory, or that cannot be written, MUST
  exit 2 with a clear, non-traceback message (`R-WM-15` applies).
- R-WCA-6: `witness.load_witnesses(root, directory=None)` and
  `witness.write_witness(root, witness, directory=None)` MUST be additive:
  `None` MUST mean `root / WITNESS_DIR_NAME`, and every existing call MUST
  keep working unchanged. `detect.profile(root, witness_dir=None)` MUST be
  additive the same way, and `cli._profile(args)` MUST forward the directory
  when the namespace carries one.
- R-WCA-7: The witness directory MUST NOT be added to `StackProfile`,
  `StackProfile.to_card()`, `as_dict()`, or `dialect_card._COMPARABLE_FIELDS`.
  `detect._current_sha` MUST still run against the target root — never
  against PATH — and MUST still run only when the loaded store is non-empty.

### W001

- R-WCA-8: W001 MUST treat a citation as proven only when at least one
  witness for that stage at the current sha has `exit_code == 0` AND no
  witness for that stage at the current sha has `exit_code != 0`.
- R-WCA-9: A set containing both MUST produce a message distinct from the
  three existing W001 messages and MUST name a failing exit code. The three
  existing messages and W001's `Rule.description` MUST be unchanged byte for
  byte.
- R-WCA-10: W002 MUST be unchanged.

### The scan action

- R-WCA-11: The scan action's inputs MUST be exactly the eight of `R-GA-28`
  plus `require-witness` and `witness-dir`. This supersedes `R-GA-28`'s
  closed list, and `R-GA-32`/`C-GA-7`'s "MUST NOT pass `--require-witness`",
  in part (`DEC-WCA-022`). The rest of `R-GA-3`/`R-GA-28` stands: no raw
  argument pass-through, no input whose name contains `token`.
- R-WCA-12: `require-witness` MUST default to the string `"false"`; exactly
  `"true"` MUST append `--require-witness` to the `validate` argv and any
  other value MUST omit it. `witness-dir` MUST default to `""`; a non-empty
  value MUST append `--witness-dir` and the value as two argv elements, and
  empty MUST omit both.
- R-WCA-13: A non-empty `witness-dir` with `require-witness` not `"true"`
  MUST fail the action with exit 1 and an `::error` naming both inputs,
  before `setup-python`, the install, and the scan run. `validate` MUST NOT
  run and no envelope MUST be written.
- R-WCA-14: The scan action MUST NOT download artifacts, MUST NOT declare a
  token input, and MUST write only under `RUNNER_TEMP` plus `$GITHUB_OUTPUT`
  and `$GITHUB_STEP_SUMMARY` (`R-GA-8` holds). `require-witness: "true"`
  without `witness-dir` MUST be accepted and MUST read the default store in
  the checkout (the same-job case `DEC-WM-011` already allows).
- R-WCA-15: `tests/test_action_contract.py::EXPECTED_INPUTS` and
  `ActionRun`'s default inputs MUST include both new names. The test that
  asserts `--require-witness` is absent from the action MUST be replaced by
  one asserting the flag appears only inside the conditional append, keeping
  the `extra-args`/`args`/root-`action.yml` assertions. Execution tests MUST
  cover a populated store under a temporary directory reporting `pass`, a
  `require-witness: "true"` run with no store reporting `fail` with a W001
  finding in the envelope, and the input error of R-WCA-13.

### The recorder action

- R-WCA-16: A composite action MUST exist at
  `.github/actions/planlint-witness/action.yml` with inputs exactly `stage`
  (required), `exit-code` (required), `coverage` (default `""`), `target`
  (default `"."`), `witness-dir` (default `""`, resolved in a step to
  `${RUNNER_TEMP}/planlint-witnesses` when empty), `upload-artifact`
  (default `"true"`), `artifact-name` (default `planlint-witness`),
  `python-version` (the scan action's default) and `version` (default `""`).
  It MUST NOT declare an input whose name contains `token`.
- R-WCA-17: The recorder MUST install the CLI as the scan action does: from a
  copy of its own checkout under `RUNNER_TEMP` by default, never in place,
  and `planlint==<version>` from the index when `version` is set. The install
  step body MUST be held in parity with the scan action's by a test.
- R-WCA-18: The recorder MUST derive the sha by running `git rev-parse HEAD`
  in `target`, MUST NOT read `GITHUB_SHA`, MUST pass the result to `--sha`
  unabbreviated, and MUST fail with exit 1 and a message — recording nothing —
  when that command fails.
- R-WCA-19: The recorder MUST run `planlint --target <target> witness --stage
  <stage> --exit <exit-code> [--coverage <coverage>] --witness-dir <dir>`
  exactly once per invocation, omitting `--coverage` when `coverage` is
  empty. It MUST NOT invoke `make`, any Makefile target, or any other command
  of the target repository.
- R-WCA-20: The recorder MUST upload `<dir>` as the artifact `artifact-name`
  under `always()` and `upload-artifact == 'true'` and on nothing else. Its
  documentation MUST state that the name must be unique per upload within a
  workflow run.
- R-WCA-21: Every file the recorder writes MUST live under `RUNNER_TEMP`,
  with `$GITHUB_OUTPUT` and `$GITHUB_STEP_SUMMARY` as the only exemptions. It
  MUST NOT create, modify or remove any file in `GITHUB_WORKSPACE`.
- R-WCA-22: The recorder's header comment, the README, SKILL.md and the
  witness template MUST state the consumer idiom: the stage step clears
  `errexit`, runs the stage, captures `$?` into a step output, and exits with
  that code; the recorder step carries `if: always()` so a failing stage is
  recorded as a failing witness rather than not at all; recorder and gate
  MUST check out the same ref.

### Templates

- R-WCA-23: `templates/spec-gate.yml` and
  `skills/planlint-spec-governance/assets/spec-gate.yml` MUST remain
  byte-identical to each other and unchanged by this change.
- R-WCA-24: A new `templates/spec-gate-witness.yml` and a byte-identical
  `skills/planlint-spec-governance/assets/spec-gate-witness.yml` MUST show
  two jobs: `stages` (a matrix `stage:` over the names the repository's specs
  cite; checkout with `persist-credentials: false`; a stage step that
  receives the matrix value through `env:` and never through an inline
  expression in `run:`; the recorder with `if: always()`, `exit-code` from
  that step's output, and `artifact-name: planlint-witness-<stage>`) and
  `gate` (`needs: stages`, `if: always()`, checkout,
  `actions/download-artifact@v4` with `pattern: planlint-witness-*`,
  `merge-multiple: true` and `path: ${{ runner.temp }}/planlint-witnesses`,
  the scan action with `require-witness: "true"` and `witness-dir`, then the
  SARIF upload as the existing template has it).
- R-WCA-25: The new template MUST declare the same `permissions` block as
  `templates/spec-gate.yml`, MUST trigger on `pull_request`, `push` to the
  default branch and `workflow_dispatch`, MUST NOT contain
  `pull_request_target`, and MUST pin both `uses:` refs to the exact ref the
  existing template pins. The pin-parity test MUST cover the new template
  and its twin.

### Dogfood in `.github/workflows/ci.yml`

- R-WCA-26: `self-validate` MUST run `make validate`; `security` MUST run
  `make thresholds` and `make security` (the gitleaks step unchanged);
  `packaging` MUST run `make wheel-check`. The commands behind those names
  MUST be the ones the jobs run today.
- R-WCA-27: Each job below MUST record, through the recorder with
  `if: always()` and an `artifact-name` unique per job, matrix leg and stage,
  exactly the stages it ran, by name: the `test` legs → `lint`, `typecheck`,
  `test`; `self-validate` → `validate`; `encoding-stress` → `e2e-live`;
  `coverage-tools` → `coverage-tools`; `docs` → `docs-check`; `security` →
  `thresholds` and `security`; `packaging` → `wheel-check`. Each recorded
  stage step MUST capture its exit code with the idiom of R-WCA-22 and exit
  with it.
- R-WCA-28: A new `ladder` job MUST run `make ci`, `make matcher-accuracy`
  and `make pre-pr`, each as its own recorded step.
- R-WCA-29: A new `witness-gate` job MUST list every recording job and
  `ladder` in `needs:`, carry `if: always()`, download every
  `planlint-witness-*` artifact merged into `${{ runner.temp }}/planlint-witnesses`,
  and run `./.github/actions/planlint` with `require-witness: "true"`,
  `witness-dir` set to that directory and `fail-on: ERROR`, under a read-only
  token with no secret.
- R-WCA-30: A test MUST derive the W001-enforced stage set from this
  repository's own specs — every criterion's `verified_by` through the
  package's parser and `MAKE_REF` — and assert that `ci.yml` runs each stage
  as `make <stage>`.
- R-WCA-31: `docs/hooks.md`'s CI table MUST gain rows for `ladder` and
  `witness-gate`, and the `self-validate`, `security` and `packaging` rows
  MUST name the make targets those jobs now run.
- R-WCA-32: No job in `ci.yml` MAY run `planlint witness` other than through
  the recorder. A W001 finding on the first hosted `witness-gate` run MUST be
  resolved by correcting the citing spec or by running the cited stage by
  name in CI — never by recording a witness by hand, and never by adding or
  renaming a Makefile target so a citation resolves.

### Documentation and the skill

- R-WCA-33: `README.md`, `skills/planlint-spec-governance/SKILL.md`,
  `skills/planlint-spec-governance/references/exit-codes.md`,
  `docs/next-steps.md`, `docs/differentiation-roadmap.md`,
  `docs/peer-review-2026-09.md`, `docs/hooks.md`, `docs/architecture/c4.md`
  (where `witness.py`'s responsibility text changes) and `CHANGELOG.md` MUST
  move in this change. SKILL.md MUST keep "Never run `witness` yourself to
  make the flag pass" verbatim, and `evals/fabricate-witness/` MUST be
  unchanged.
- R-WCA-34: `tests/test_skill_contract.py::READ_ONLY_INVOCATIONS` MUST gain
  `("validate", "--require-witness", "--witness-dir", <placeholder>)`, the
  placeholder substituted at run time with an existing directory outside the
  target tree, following the `delta --baseline` precedent.

### Constraints

- C-WCA-1: Every signature change MUST be additive and defaulted; no new
  `StackProfile` field; `WITNESS_SCHEMA_VERSION`, `WITNESS_DIR_NAME` and
  `.gitignore` MUST be unchanged.
- C-WCA-2: `tests/baseline_rules.json`, every entry of
  `tests/test_decomposition.py::_EXPECTED_HASHES`, and
  `rules.FINDINGS_SCHEMA_VERSION` MUST be unchanged.
- C-WCA-3: No new CLI verb and no `witness` sub-verb; `ALLOWED_VERBS` MUST
  be unchanged (`DEC-WM-002`).
- C-WCA-4: No runtime or test dependency; YAML is read by line scan.
- C-WCA-5: `openspec_graph.__version__` MUST NOT move.
- C-WCA-6: Neither action MAY write into `GITHUB_WORKSPACE`.
- C-WCA-7: `make ci` and `make pre-pr`'s composition MUST NOT change, and
  neither `ladder` nor `witness-gate` MAY be composed into a Makefile target.
- C-WCA-8: The scan action MUST NOT gain a download step, a token, or a raw
  argument pass-through.

---

## Decisions

- **DEC-WCA-001:** the override is a CLI flag, `--witness-dir`, not an
  environment variable, not a config key, and not a change to the default
  path. A flag is visible on the line of the workflow that uses it — the
  property `DEC-GA-008` paid for by moving the SARIF upload into the consumer
  workflow — whereas an environment variable is invisible inside a `uses:`
  block and a config key would make the store's location a fact about the
  repository rather than about the run. The default stays per-checkout and
  gitignored exactly as `DEC-WM-011` decided; this change adds a second way
  to point at a store, it does not move the first.
- **DEC-WCA-002:** `--witness-dir` on `validate` requires `--require-witness`;
  alone it is a usage error at exit 2. Alone, the flag would configure two
  rules that are then not evaluated — a flag that silently does nothing is
  the same contradiction `cli.py:414-420` already refuses when `--json` is
  paired with another `--format`, and the exit-code reference already lists
  that case under "precondition or usage error". Exit 2, never 1: a usage
  error must not be confusable with a spec failure (`DEC-SD-001`, through
  `_profile`'s own comment at `cli.py:165-172`).
- **DEC-WCA-003:** an explicitly named directory that does not exist is exit
  2; the default store's absence stays W001 at exit 1. The two look alike and
  mean opposite things. With no `--witness-dir`, "nothing has ever been
  witnessed" is a true statement about the specs and `AC-WM-9`'s fail-closed
  contract is the right answer. With `--witness-dir` naming a path, the
  common cause of its absence is that a `download-artifact` step failed or
  wrote somewhere else — a precondition the gate could not check, not a
  claim about the specs — and reporting it as "the specs are lying" would
  send a maintainer to fix citations that are fine. `R-GA-6` already makes
  the action say "precondition or usage error, not a spec failure" for exit
  2, so the message lands in the right place without new YAML.
- **DEC-WCA-004:** `witness --witness-dir` creates the directory;
  `validate --witness-dir` does not. A writer creating its own output
  directory is ordinary and is what `write_witness` already does for the
  default store (`witness.py:105`); a reader finding its input directory
  missing is the failed-download signal of `DEC-WCA-003`. Making the writer
  strict would force every recorder step to `mkdir` first; making the reader
  lenient would turn a failed download into a silent empty store and then
  into W001 "never witnessed" — exactly the misdiagnosis `DEC-WCA-003` exists
  to prevent.
- **DEC-WCA-005:** W001 becomes "every": proven only when some witness at
  the current sha exited 0 and none exited non-zero. This is `DEC-WM-019`'s
  own argument for W002 — "one bad run among several retries for the same
  commit still blocks, rather than being silently out-voted by a luckier
  one" — applied to the rule it was left off. The case that makes it
  concrete is a matrix: this repository runs `make test` on four
  interpreters, and once every leg records a witness, a failure on one of
  them must not be hidden by three passes. The change is strictly more
  fail-closed; a repository whose witnesses at the current sha all passed
  sees no difference. One gap is accepted and named: a leg that never ran a
  stage leaves no witness and is invisible to W001, because the store has
  no notion of how many legs were expected and inventing one would need
  configuration this tool refuses to carry; that leg's own job is red, and
  CI as a whole is red with it.
- **DEC-WCA-006:** W001 does not infer that a `pre-pr` witness proves `test`
  ran, even though `pre-pr` depends on `ci` which depends on `test` in this
  Makefile. `DEC-WM-016` already decided that every citation requires its own
  witness; the Makefile's dependency graph is parsed structurally
  (`machinery.py`) but a parsed prerequisite is a claim about what *would*
  run, not evidence that it did, and trusting it would reintroduce the
  "guess which mention is the real one" class of heuristic this project has
  already paid for once. The consequence is accepted directly: the aggregate
  targets specs cite must be run by name, which is what the `ladder` job
  does.
- **DEC-WCA-007:** the scan action downloads nothing; the consumer workflow
  downloads into `runner.temp` and passes the path. This is `DEC-GA-008`'s
  shape applied to the other direction of the same artifact store. A
  download step inside the action would have to be right about an
  expression over the event, the artifact pattern and a missing-artifact
  failure mode at once, would need `actions: read` the action currently does
  not hold, and would put a write — into `RUNNER_TEMP`, but still a write
  the adopter cannot see — behind an input. Three lines in a template the
  adopter copies anyway keep the action's inputs a pure translation of CLI
  flags (`R-GA-1`) and keep `R-GA-8` true by construction.
- **DEC-WCA-008:** `require-witness` is a string defaulting to `"false"`,
  `witness-dir` defaults to empty, and a non-empty `witness-dir` without
  `require-witness: "true"` is an input error the action fails on before
  installing anything — the action-layer twin of `DEC-WCA-002`, for the same
  reason: a path that configures nothing must not be accepted silently. The
  check lives in the existing `paths` step, so the step-id list the
  extractor test pins (`paths, install, scan, project, gate`) is unchanged.
  `require-witness: "true"` without `witness-dir` is allowed: it reads the
  default store in the checkout, which a step earlier in the same job may
  legitimately have populated (`DEC-WM-011`'s same-job case), and refusing it
  would forbid the simplest pipeline for no safety gain.
- **DEC-WCA-009:** the recorder is a second composite action, not a mode of
  the scan action. The scan action's contract is "run `validate` exactly
  once and project it" (`R-GA-2`), its outputs describe a scan, and its
  posture is read-only against the target; the recorder runs a *writer* verb
  and has no envelope to project. One action with a `mode:` input would have
  two personalities, a `status` output that is meaningless in one of them,
  and an `EXPECTED_INPUTS` set that mixes both. The honest cost is a copied
  install recipe — two actions, one shell body — and the mitigation is a
  parity test on the install step text (`R-WCA-17`), the same move
  `test_skill_asset_matches_template` makes for the template and its twin.
- **DEC-WCA-010:** the recorder derives the sha with `git rev-parse HEAD`
  executed in the target, not from `GITHUB_SHA`. The gate compares a
  witness's `sha` to `detect._current_sha`, which is `git rev-parse HEAD` in
  the checkout being validated. On `pull_request` the default checkout and
  `GITHUB_SHA` are both the merge commit and usually agree [Likely], but a
  consumer that checks out `pull_request.head.sha` — as this repository's
  `graph-diff` job does (`ci.yml:170`) — would record a witness under a sha
  the gate can never see. Deriving from the checkout makes recorder and gate
  agree by construction whenever they check out the same ref, and when they
  do not, the stale witness is the correct answer. `DEC-WM-003` holds: the
  *CLI* still never derives the sha; the shell around it does, and the two
  values the freshness check compares are still obtained independently.
- **DEC-WCA-011:** the recorder never runs the stage. planlint never runs
  `make` (`SECURITY.md`, `machinery.py`'s static guard), and an action that
  did would make the recorder the thing that decides what a stage is. The
  consumer's own step runs it and captures the code — `set +e`, run,
  `code=$?`, write the output, `exit $code` — and the recorder step carries
  `if: always()`. The idiom matters: without `set +e` the step dies before
  the code is written (the `errexit` lesson of `DEC-GA-013`), and without
  `always()` a failing stage records nothing, which W001 reports as "never
  witnessed" rather than "recorded a failing run" — true, but the less
  useful of the two true messages. `--exit` is the harness's own status
  (`DEC-WM-017`); the recorder passes it through unexamined because it has
  nothing to examine it against.
- **DEC-WCA-012:** one upload per recorder call, each under its own
  artifact name, rather than one upload per job. A job that records three
  stages uploads three small artifacts whose contents overlap; because
  filenames are content hashes and `merge-multiple: true` unions
  directories, the overlap is harmless. The alternative — `upload-artifact:
  "false"` on all but the last recorder — loses every earlier record when a
  later stage step is skipped after a failure, which is exactly the run
  whose evidence matters.
- **DEC-WCA-013:** a second template beside the first, not a rewrite of
  `templates/spec-gate.yml`. The plain gate remains the default an adopter
  copies; witness mode is opt-in at the CLI (`R-WM-3`) and stays opt-in at
  the template. `templates/AGENTS.md` is explicit that a copied default is
  harder to change than one in this repository. The witness template carries
  no `paths:` filter: the stages it records are the repository's real gates
  and the proof is per commit, so the "skip a spec-only lint on unrelated
  changes" rationale behind the plain template's filter does not apply.
- **DEC-WCA-014:** the template passes matrix values to the stage step
  through `env:`, never as `${{ matrix.stage }}` inline in `run:`. An inline
  expression in a script is GitHub's documented injection vector; matrix
  values are author-controlled here, but this file is copied and edited by
  strangers, and a template that models the safe form costs one line.
- **DEC-WCA-015:** the dogfood aligns `ci.yml`'s three bare-command steps to
  the make targets the specs cite rather than rewriting the citing specs.
  The commands are the same; the Makefile is the gate ladder the specs
  describe and `docs/hooks.md` documents; the citations are true statements
  about what the author ran. Making CI run the named target makes the fact
  behind each citation true in CI, which is the repair SKILL.md permits.
  Rewriting eleven specs to cite bare commands would make the specs match
  CI's accident rather than CI match the specs' intent.
- **DEC-WCA-016:** a `ladder` job runs `make ci`, `make matcher-accuracy`
  and `make pre-pr` by name, even though `pre-pr` re-runs the whole suite
  the matrix already ran. Seven specs cite `pre-pr` and five cite `ci` on
  `_Verified by:_` lines; under `DEC-WCA-006` no inference can stand in for
  running them, and the release workflow already runs `make pre-pr` on every
  tag, so this is the same gate moved earlier, not a new one. The cost is
  runner minutes on one Linux job; the alternative was leaving the aggregate
  citations permanently unproven.
- **DEC-WCA-017:** `test-windows`, `graph-diff` and `action-contract` do not
  record. `graph-diff` checks out the pull request's head sha, a different
  `HEAD` from every other job, so anything it recorded would be stale by
  construction (`DEC-WCA-010`). `action-contract` runs the scan action
  against labelled fixtures; it runs no stage this repository's specs cite.
  `test-windows` runs the same three stages the Linux matrix records and
  remains its own hard gate; the recorder's first hosted runs stay on one
  shell and platform, and a Windows-only defect the matrix misses is the
  recorded reopen trigger for adding it.
- **DEC-WCA-018:** a W001 finding on the first hosted `witness-gate` run is a
  citation to fix, never a witness to record by hand. The mechanical form of
  that expectation ships as a local test (`R-WCA-30`): derive the stage set
  from the specs with the package's own parser and assert `ci.yml` runs each
  by name — so the hosted job is expected to find nothing the local suite
  did not already enforce, and if it does, the test was wrong and the hosted
  finding is the correction.
- **DEC-WCA-019:** no CI recorder passes `--coverage` in this change, so
  W002 stays inert in the dogfood. Extracting a percentage from a coverage
  report and trusting it is `DEC-WM-020`'s named gap, and a step that reads
  the wrong unit would silently clear every floor; it deserves its own
  tested contract. The reopen trigger is a coverage-extraction step whose
  unit and source are asserted by a test.
- **DEC-WCA-020:** W001's `Rule.description` and its three existing messages
  do not change, so `tests/baseline_rules.json`, the `rules` golden hash and
  the generated rule catalog do not move, and `validate`/`graph` hashes do
  not move because the golden fixture never passes `--require-witness`. The
  cost is that the README's W001 row and `rules.py`'s docstring must be
  reworded by hand to say "and no failing witness at the current commit";
  the description string "every cited stage has a fresh, passing witness"
  remains true under the tightened semantics.
- **DEC-WCA-021:** `READ_ONLY_INVOCATIONS` gains the `--witness-dir` variant
  with a placeholder substituted by an *existing, empty* directory outside
  the tree. Exit 1 (W001) is inside `_ALLOWED_READ_ONLY_EXITS`
  (`test_skill_contract.py:88`), so the verb really runs and the read-only
  digest is a genuine measurement; a missing directory would exit 2 and the
  vacuity guard would correctly reject it. Outside the tree for the same
  reason `delta --baseline`'s placeholder is: a file inside the target would
  show up as created and mask what the verb itself did.
- **DEC-WCA-022 (supersedes `R-GA-28`, `R-GA-32`, `C-GA-7` and `DEC-GA-019`,
  each in part):** the closed input list grows to ten, and "the action never
  passes `--require-witness`" becomes "the action passes it only when
  `require-witness` is exactly `"true"`". `DEC-GA-019`'s reasoning was that
  the flag "fails closed on a fresh CI checkout (the store is gitignored)";
  that premise is the thing this change removes, so the decision resting on
  it is retired rather than contradicted. What `DEC-GA-019` protected
  survives intact: no `extra-args`, no `token`, and a wrapper flag only
  where it has a tested contract — which `R-WCA-15` now gives it.
  `add-finding-line-hits`'s `AC-GA-29` cites the test this change replaces;
  its `_Verified by:_` is re-pointed in the same commit so the citation gate
  stays green. `DEC-WM-011` is realised by this change, not altered.
- **DEC-WCA-023:** the GitHub Actions facts this design leans on are stated
  as [Likely], not [Certain], and each has a fail-closed consequence if
  wrong. If jobs in one run did not share `HEAD`, the gate would see stale
  witnesses and fail; if `merge-multiple` did not union, the gate would see
  a partial store and fail; if a fork pull request could not upload
  artifacts, the gate would see nothing and fail. The hosted `witness-gate`
  job (`AC-WCA-27`) is the only evidence that turns [Likely] into observed,
  which is why it is a criterion and not a note.

---

## Acceptance Criteria

- [ ] **AC-WCA-1:** `validate --require-witness --witness-dir D`, with D
  outside the target tree and holding a passing witness for the target's
  current sha, exits 0, while the same target's default store is absent and
  is not consulted. (R-WCA-1, R-WCA-4, R-WCA-6)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-2 (non-success):** `validate --witness-dir D` without
  `--require-witness` exits 2 with one stderr line naming both flags, empty
  stdout, and no profile run. (R-WCA-2, DEC-WCA-002)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-3 (non-success):** `validate --require-witness --witness-dir D`
  where D does not exist, and where D is a regular file, each exit 2 with
  one stderr line naming D, empty stdout, and no W001 or W002 finding
  evaluated. (R-WCA-3, DEC-WCA-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-4 (non-success):** without `--witness-dir`, a target with no
  witness store still fails closed at exit 1 with W001 — `AC-WM-9` is
  untouched. (R-WCA-3, DEC-WCA-003)
  _Verified by:_ `pytest -k test_validate_require_witness_fails_closed_on_a_repo_with_no_witness_store` · stage: `make test`

- [ ] **AC-WCA-5:** `witness --witness-dir D` writes the content-addressed
  record under D and nothing under `<target>/.planlint/witnesses/`, creates
  D when it is missing, and the file's bytes equal what the default store
  would hold for the same inputs. (R-WCA-5, R-WCA-6, DEC-WCA-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-6 (non-success):** `witness --witness-dir D` where D exists
  and is a regular file exits 2 with a clear message and writes nothing.
  (R-WCA-5)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-7 (non-success):** both verbs' default behaviour is
  unchanged: plain `validate` never evaluates W001; an unwritable default
  store still exits 2 cleanly; a record-then-validate round trip on the
  default store still exits 0. (R-WCA-1, R-WCA-5, R-WCA-6, C-WCA-1)
  _Verified by:_ `pytest -k "test_validate_without_require_witness_never_evaluates_w001 or test_cli_witness_reports_a_clean_error_when_the_witness_directory_is_unwritable or test_validate_require_witness_passes_once_a_matching_fresh_witness_is_recorded"` · stage: `make test`

- [ ] **AC-WCA-8:** `load_witnesses(root, directory=D)` returns the records
  under D and none from the default store, and the plain union of two
  stores' files in one directory loads every distinct record exactly once.
  (R-WCA-6)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-9 (non-success):** `witnesses`/`current_sha` remain absent
  from `to_card()` and `_COMPARABLE_FIELDS`, and the current sha is still
  not computed when the loaded store is empty. (R-WCA-7, C-WCA-1)
  _Verified by:_ `pytest -k "test_to_card_excludes_witnesses_and_current_sha or test_current_sha_is_not_invoked_when_no_witnesses_are_present"` · stage: `make test`

- [ ] **AC-WCA-10:** `profile(root, witness_dir=D)` with D holding a witness
  yields a `current_sha` equal to the target's `git rev-parse HEAD` — not
  anything derived from D — and a `to_card()` byte-identical to the call
  without `witness_dir`. (R-WCA-7, C-WCA-1)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-11 (non-success):** a passing and a failing witness for the
  same stage at the current sha make W001 fire with a message distinct from
  the three existing ones that names the failing exit code. (R-WCA-8,
  R-WCA-9, DEC-WCA-005)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-12 (non-success):** W001's existing causes are unchanged — a
  lone failing witness still reports "failing run", and only-passing
  witnesses at the current sha still do not fire. (R-WCA-9)
  _Verified by:_ `pytest -k "test_w001_fires_when_the_matching_witness_recorded_a_nonzero_exit_code or test_w001_does_not_fire_when_a_fresh_passing_witness_exists"` · stage: `make test`

- [ ] **AC-WCA-13 (non-success):** the rule set matches the committed
  baseline and the `validate`/`graph`/`rules` golden hashes are unchanged.
  (R-WCA-9, R-WCA-10, C-WCA-2, DEC-WCA-020)
  _Verified by:_ `pytest -k "test_output_byte_identical or test_rule_set_matches_baseline"` · stage: `make test`

- [ ] **AC-WCA-14:** the scan action declares exactly the ten inputs of
  R-WCA-11, `EXPECTED_INPUTS` and `ActionRun` defaults match, and no input
  name contains `token`. (R-WCA-11, R-WCA-15, DEC-WCA-022)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-15:** `require-witness: "true"` puts `--require-witness` on
  the `validate` argv; `"false"` and the shipped default omit it; a non-empty
  `witness-dir` with `require-witness: "true"` puts `--witness-dir <value>`
  on the argv; the flag string appears in `action.yml` only inside the
  conditional append. (R-WCA-12, R-WCA-15)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-16 (non-success):** a non-empty `witness-dir` with
  `require-witness` left at `"false"` fails the action with exit 1 and an
  `::error` naming both inputs before the scan step, with no envelope
  written. (R-WCA-13, DEC-WCA-008)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-17:** the scan action's extracted steps, run with
  `require-witness: "true"` and a `witness-dir` under a temporary directory
  holding a passing witness for the fixture's current sha, report `pass`;
  run with `require-witness: "true"` and an empty store, they report `fail`
  with a W001 finding in the envelope. (R-WCA-12, R-WCA-15)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-18 (non-success):** the scan action still redirects only to
  approved paths, still declares no token and no privileged permission, and
  still leaves the scanned tree byte-identical. (R-WCA-14, C-WCA-6, C-WCA-8)
  _Verified by:_ `pytest -k "test_the_action_writes_only_to_evidence_and_the_runner_command_files or test_the_action_needs_no_token_and_no_privileged_permission or test_the_evidence_directory_is_outside_the_scanned_tree"` · stage: `make test`

- [ ] **AC-WCA-19:** the recorder declares exactly its nine inputs and no
  token; its header comment states the consumer idiom; its install step body
  equals the scan action's; it runs `git rev-parse HEAD` in the target and
  never reads `GITHUB_SHA`; it never invokes `make`; its upload is
  conditioned on `always()` and `upload-artifact` and nothing else; every
  redirection targets `RUNNER_TEMP` or a runner command file — all read from
  the YAML by line scan, with no parser dependency added. (R-WCA-16,
  R-WCA-17, R-WCA-18, R-WCA-19, R-WCA-20, R-WCA-21, R-WCA-22, C-WCA-4,
  DEC-WCA-009, DEC-WCA-010)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-20:** the recorder's extracted steps, run against a temporary
  git repository with `GITHUB_SHA` set to a different value, write one
  witness whose `sha` is that repository's `HEAD`, and
  `validate --require-witness --witness-dir` over that directory exits 0;
  run with `exit-code: 1`, they write a failing witness that W001 then
  reports as a failing run. (R-WCA-18, R-WCA-19, DEC-WCA-010, DEC-WCA-011)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-21 (non-success):** the recorder run against a target that is
  not a git repository exits 1 with a message and writes no witness.
  (R-WCA-18)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-22:** `templates/spec-gate-witness.yml` and its skill twin
  are byte-identical; both `uses:` refs equal the ref `templates/spec-gate.yml`
  pins; the `permissions` block equals the plain template's; the stage step
  reads the matrix value from `env:` and exits with the captured code; the
  recorder step carries `if: always()`; the `gate` job downloads
  `planlint-witness-*` with `merge-multiple: true` into `runner.temp` and
  passes `require-witness: "true"` and `witness-dir` to the scan action.
  (R-WCA-22, R-WCA-24, R-WCA-25, DEC-WCA-013, DEC-WCA-014)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-23 (non-success):** `templates/spec-gate.yml` and its twin
  are still byte-identical, still pin the floor the skill enforces, and no
  file under `.github/`, `templates/` or `skills/` — the new action and
  template included — contains `pull_request_target`. (R-WCA-23, R-WCA-25)
  _Verified by:_ `pytest -k "test_skill_asset_matches_template or test_ci_template_pins_the_floor_the_skill_enforces or test_no_workflow_or_template_uses_pull_request_target"` · stage: `make test`

- [ ] **AC-WCA-24:** `ci.yml`'s `self-validate`, `security` and `packaging`
  jobs run `make validate`, `make thresholds` + `make security`, and
  `make wheel-check`; every recording job records its stages through the
  recorder with artifact names unique across the workflow; `ladder` runs its
  three recorded steps; `witness-gate` lists every recording job in `needs:`,
  carries `if: always()`, downloads the merged artifacts into `runner.temp`,
  runs the local scan action with `require-witness: "true"`, `witness-dir`
  and `fail-on: ERROR`, needs no secret, and is composed into no Makefile
  target. (R-WCA-26, R-WCA-27, R-WCA-28, R-WCA-29, R-WCA-32, C-WCA-7,
  DEC-WCA-015, DEC-WCA-016, DEC-WCA-017)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-25:** every stage any criterion in this repository's own
  specs cites on its verification line — collected from
  `Criterion.verified_by` through the package's parser, not from a hand-kept
  list — appears in `ci.yml` as `make <stage>`. (R-WCA-30, DEC-WCA-018)
  _Verified by:_ stage: `make test`

- [ ] **AC-WCA-26:** `docs/hooks.md`'s CI table has a row for every job in
  `ci.yml`, `ladder` and `witness-gate` included. (R-WCA-31)
  _Verified by:_ `pytest -k test_hooks_ci_table_lists_every_ci_job` · stage: `make test`

- [ ] **AC-WCA-27:** the hosted `witness-gate` job is green on the pull
  request that lands this change, with every recording job having uploaded
  its artifact and the merged store accepted by the scan action under
  `require-witness: "true"`. This is the first time `validate
  --require-witness` passes on a runner, and the only evidence for the
  [Likely] platform facts of DEC-WCA-023. Any W001 finding on the way there
  is resolved by a visible commit that fixes a citation or runs a stage by
  name — never by a hand-recorded witness. (R-WCA-29, R-WCA-32, DEC-WCA-018,
  DEC-WCA-023)
  _Verified by:_ the `witness-gate` job's own gate step on the pull request · stage: `make ci` must also be green on the same commit

- [ ] **AC-WCA-28 (non-success):** `validate --require-witness --witness-dir`
  over an existing directory outside the tree leaves the target
  byte-identical and is listed in `READ_ONLY_INVOCATIONS`, which still
  matches SKILL.md's read-only table. (R-WCA-34, DEC-WCA-021)
  _Verified by:_ `pytest -k "test_read_only_verbs_leave_tree_byte_identical or test_read_only_invocations_cover_every_verb_the_skill_calls_read_only"` · stage: `make test`

- [ ] **AC-WCA-29:** the README, SKILL.md, the exit-code reference,
  `docs/next-steps.md`, `docs/differentiation-roadmap.md`,
  `docs/peer-review-2026-09.md`, `docs/hooks.md`, `docs/architecture/c4.md`
  and `CHANGELOG.md` describe the recorder, the two inputs, `--witness-dir`,
  the consumer idiom and the tightened W001; no document still says
  `--require-witness` is deliberately absent from the action; the docs gate
  passes. (R-WCA-22, R-WCA-33)
  _Verified by:_ `pytest -k test_docs_check_passes` · stage: `make docs-check`

- [ ] **AC-WCA-30 (non-success):** the CLI verb surface is unchanged,
  `openspec_graph.__version__` is unchanged, `[project] dependencies` is
  still empty, SKILL.md still says never to run `witness` to make the flag
  pass, and `evals/fabricate-witness/` is byte-identical to HEAD. (R-WCA-33,
  C-WCA-3, C-WCA-4, C-WCA-5)
  _Verified by:_ `pytest -k test_cli_verbs_are_exactly_the_allow_list` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-WCA-1..26, AC-WCA-28, AC-WCA-30 |
| Core | `make ci` | the above, plus lint and this repo's own `planlint validate` over this package |
| Docs | `make docs-check` | AC-WCA-29 |
| Hosted | `witness-gate` job in `.github/workflows/ci.yml` | AC-WCA-27 |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, no-hardcoded-thresholds |
