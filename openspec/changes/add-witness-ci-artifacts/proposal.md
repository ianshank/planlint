# Change: Witness Artifacts as a CI Upload/Download, Not a Local Store (CP-WCA / peer review R7)

## Why

`add-witness-mode` shipped the proof half of "verified by": `planlint witness`
records that a stage ran, and `validate --require-witness` fails unless every
cited stage has a fresh, passing record. It also anticipated, in `DEC-WM-011`,
that recording and validating would usually happen in different CI jobs,
wired together by "the CI system's own artifact-passing mechanism". What it
did not ship is any way to point `validate` at a store that arrived that way.
The store path is a constant, the store is gitignored, and the composite
Action is forbidden from writing into the checkout — so the only place a
witness can be read is the one place CI can never put it. `docs/peer-review-2026-09.md`
records this as finding **F7** and recommendation **R7**: "the differentiating
feature of v2 is currently unusable in continuous integration, which is the
only place its claim means anything." A 2026-10 re-measurement against this
tree reproduced every fact below.

**Evidence:**

1. **The store path is hard-coded and the store never leaves the machine.**
   `openspec_graph/witness.py:37` sets `WITNESS_DIR_NAME = ".planlint/witnesses"`;
   `write_witness` (`witness.py:104`) and `load_witnesses` (`witness.py:176`)
   both compute `root / WITNESS_DIR_NAME` with no override, and
   `detect.profile` (`detect.py:715`) calls `witness.load_witnesses(root)`
   with the target root alone. `.gitignore:55` is `.planlint/`. A fresh
   `git clone` of a repository whose specs cite `` `make test` `` therefore
   fails `validate --require-witness` with `ERROR W001 ... has never been
   witnessed` on every criterion (reproduced). Copying the origin checkout's
   `.planlint/witnesses/` directory into the clone makes the same command
   print `PASS` (reproduced): the record is portable JSON — `schema_version`,
   `stage`, `exit_code`, `coverage`, `sha`, `recorded_at`
   (`witness.py:68-76`) — with no path in it, content-addressed by filename
   (`witness.py:107`, `witness.py:127`). Two stores merge by plain directory
   union, because two files with the same content have the same name.
2. **The design was anticipated; the plumbing was not built.** `DEC-WM-011`
   (`openspec/changes/add-witness-mode/specs/witness-mode/spec.md`) says the
   two halves may run in different jobs via `upload-artifact`/`download-artifact`.
   But the scan action's first comment block says "Evidence lives under
   RUNNER_TEMP, never in the workspace" (`.github/actions/planlint/action.yml:147-150`),
   `R-GA-8` forbids any write into `GITHUB_WORKSPACE`, and the `action-contract`
   CI job asserts `git diff --quiet --exit-code` after the action runs
   (`.github/workflows/ci.yml:307`). The action cannot download a witness
   artifact into the one directory `validate` reads. That is why
   `--require-witness` is "deliberately absent" (`README.md:464`), why
   `tests/test_action_contract.py:289-294` asserts the string is absent from
   `action.yml`, and why `docs/next-steps.md:220` says it "is the one to
   leave alone".
3. **W001 is "any", W002 is "every".** `rules_witness.py:61` passes a
   citation when `any(w.exit_code == 0 for w in at_commit)`. `DEC-WM-019`
   chose "every" for W002 so that "one bad run among several retries for the
   same commit still blocks, rather than being silently out-voted by a
   luckier one" — and left W001 on "any". This repository runs `make test`
   on four interpreters (`ci.yml:14`); under W001 as written, a leg that
   fails is out-voted by a leg that passes.
4. **This repository's own gate would fail W001 today, and the failures are
   about the citations.** Across the 43 `spec.md` files under
   `openspec/changes/*/specs/*/` at HEAD, the whole-file regex
   `` `make\s+([a-z][a-z0-9_-]*)` `` finds 14 distinct stages (the brief's
   measurement). W001 reads a narrower set: for the harness dialect
   `Criterion.verified_by` is the Verified-by line alone
   (`parse_harness.py:55`), and `rules_witness._stage_citations` scans only
   that (`rules_witness.py:31-34`). Re-measured on Verified-by lines only,
   W001 enforces 12 stages: `test` (40 files), `docs-check` (10), `pre-pr`
   (7), `validate` (7), `ci` (5), `typecheck` (3), `lint` (2), and one file
   each for `security`, `coverage-tools`, `thresholds`, `wheel-check`,
   `matcher-accuracy`. `e2e-live` and `skill-catalog` appear only in prose
   and matrix tables, never on a Verified-by line, so W001 never asks for
   them. Of the 12, `.github/workflows/ci.yml` runs five by their
   make-target name (`test`, `lint`, `typecheck`, `coverage-tools`,
   `docs-check`). Three run as bare commands under a different name:
   `self-validate` runs `planlint --target . validate --fail-on ERROR`
   (`ci.yml:115`) rather than `make validate`; `security` runs
   `python tools/check_no_hardcoded_thresholds.py` (`ci.yml:332`) rather
   than `make thresholds`, and never runs `make security` at all;
   `packaging` runs `python -m build` + `tools/check_wheel_metadata.py`
   (`ci.yml:152-155`) rather than `make wheel-check`. Four are never run on a
   pull request: `ci`, `pre-pr`, `matcher-accuracy` and `security`;
   `make pre-pr` runs only in `release.yml:42`, on a tag. Every one of those
   is a true statement about what the author ran locally and a false
   statement about what CI proves — a finding about the citations, not about
   the tool.
5. **The GitHub facts this design leans on** — stated as [Likely], not
   [Certain], because they are properties of a hosted platform rather than
   of this tree: within one workflow run, every job using the default
   `actions/checkout` sees the same `HEAD` (on `pull_request`, the merge
   commit), so a witness recorded in one job matches the gate in another job
   of the same run, and a witness from a previous run is correctly stale
   because its sha differs. `actions/download-artifact@v4` with `pattern:`
   and `merge-multiple: true` unions several uploaded directories into one.
   The `graph-diff` job is the counter-example that proves the rule: it
   checks out `github.event.pull_request.head.sha` (`ci.yml:170`), so its
   `HEAD` differs from every other job's and nothing it recorded could ever
   match.

## What Changes

- **`openspec_graph/witness.py`** — `load_witnesses(root, directory=None)`
  and `write_witness(root, witness, directory=None)` gain an additive,
  defaulted `directory`; `None` keeps `root / WITNESS_DIR_NAME`. No change to
  the schema, the hash, the atomic write, or the fail-closed load.
- **`openspec_graph/detect.py`** — `profile(root, witness_dir=None)` passes
  the directory to `load_witnesses`. `_current_sha(root)` is still computed
  from the *target's* `HEAD`, and still only when the loaded store is
  non-empty (`DEC-WM-008`). Nothing new reaches `StackProfile.to_card()`
  (`DEC-WM-014`).
- **`openspec_graph/cli.py`** — `validate --witness-dir PATH` (accepted only
  with `--require-witness`; alone it is a usage error, exit 2; a PATH that
  does not exist or is not a directory is a precondition error, exit 2, named
  in the message, before any rule evaluates) and `witness --witness-dir PATH`
  (writes under PATH, creating it if absent). `_profile(args)` forwards the
  directory when present. The default behaviour of both verbs is unchanged.
- **`openspec_graph/rules_witness.py`** — W001 is proven only when at least
  one witness at the current sha exited 0 *and* none at the current sha
  exited non-zero. A mixed set yields a fourth, distinct message naming the
  failing exit code. The three existing messages and `Rule.description` are
  byte-for-byte unchanged, so `tests/baseline_rules.json` and the `rules`
  golden hash do not move.
- **`.github/actions/planlint/action.yml`** — two inputs: `require-witness`
  (string, default `"false"`; `"true"` appends `--require-witness`) and
  `witness-dir` (default empty; non-empty appends `--witness-dir <value>`).
  A non-empty `witness-dir` without `require-witness: "true"` is an input
  error the action reports and exits 1 on before installing or scanning. The
  action downloads nothing: the consumer workflow downloads the artifact
  under `${{ runner.temp }}` and passes the path, exactly as `DEC-GA-008`
  moved the SARIF upload into the workflow. `R-GA-8` holds.
- **New `.github/actions/planlint-witness/action.yml`** — a recorder
  composite action. Inputs `stage`, `exit-code` (required), `coverage`,
  `target`, `witness-dir`, `upload-artifact`, `artifact-name`,
  `python-version`, `version`. It installs the CLI from a copy of its own
  checkout under `RUNNER_TEMP` (or from the index when `version` is set),
  derives the sha with `git rev-parse HEAD` in the target — never
  `GITHUB_SHA` — runs `planlint witness` once, and uploads the directory
  under `always()`. It never runs the stage: the consumer's own step runs it
  and captures the exit code.
- **New `templates/spec-gate-witness.yml`** and its byte-identical twin
  **`skills/planlint-spec-governance/assets/spec-gate-witness.yml`** — the
  two-job shape: a `stages` matrix job (run the stage with the exit-capture
  idiom, then the recorder with a per-stage artifact name) and a `gate` job
  (`needs: stages`, `if: always()`) that downloads `planlint-witness-*` with
  `merge-multiple: true` into `${{ runner.temp }}/planlint-witnesses` and
  runs the scan action with `require-witness: "true"` and `witness-dir`.
  Same permissions, `persist-credentials: false`, exact-ref pinning and
  `pull_request`-never-`_target` posture as the existing template.
  `templates/spec-gate.yml` and its twin are unchanged.
- **`.github/workflows/ci.yml`** — dogfood, the proof that v2 reaches CI:
  `self-validate` runs `make validate`, `security` runs `make thresholds` and
  `make security`, `packaging` runs `make wheel-check` (same commands, by the
  names the specs cite); every job that runs a cited stage records it through
  the recorder with a unique `artifact-name`; a new `ladder` job runs
  `make ci`, `make matcher-accuracy` and `make pre-pr` as three recorded
  steps; a new `witness-gate` job (`needs:` every recording job,
  `if: always()`) downloads every `planlint-witness-*` artifact merged into
  one temp directory and runs the scan action with `require-witness: "true"`,
  `witness-dir`, `fail-on: ERROR`.
- **`tests/test_action_contract.py`** — `EXPECTED_INPUTS` and `ActionRun`
  defaults grow by two; `test_action_does_not_pass_require_witness` is
  replaced by a test that the flag appears only inside the conditional
  append (the `extra-args`/`args`/root-`action.yml` assertions stay); new
  execution tests for a populated store that reports `pass`, an empty
  `require-witness: "true"` run that reports `fail` with W001, and the input
  error. **New `tests/test_witness_action_contract.py`** for the recorder.
  **`tests/test_skill_contract.py`** — `READ_ONLY_INVOCATIONS` gains
  `("validate", "--require-witness", "--witness-dir", <placeholder>)` with an
  existing directory outside the tree. **`tests/test_adopter_urls.py`** —
  pin-parity extended to the new template and both of its `uses:` refs.
  **`tests/test_ci_hardening.py`** — the `witness-gate` job, the `needs:`
  closure, unique artifact names, and a test deriving the W001-enforced stage
  set from the specs' own Verified-by lines and asserting `ci.yml` runs each
  by its make-target name. **`tests/test_graft_witness.py`** — the CLI and
  W001 cases named in `tasks.md`.
- **`docs/hooks.md`** — CI table rows for `ladder` and `witness-gate`;
  amended gate cells for `self-validate`, `security`, `packaging`.
- **Docs that move together** — `README.md` (the witness paragraph at
  199-206 and the "no `extra-args`" paragraph at 462-467 stop saying the flag
  is deliberately absent; the Action inputs table gains two rows);
  `skills/planlint-spec-governance/SKILL.md` (the Witness mode section
  describes the recorder/gate shape; "Never run `witness` yourself" stays;
  the writes-files row mentions `--witness-dir`);
  `skills/planlint-spec-governance/references/exit-codes.md` (the two
  `--witness-dir` precondition rows); `docs/next-steps.md` (item 3 and the
  two deferral rows that say to leave `--require-witness` alone);
  `docs/differentiation-roadmap.md` (the v2 note); `docs/peer-review-2026-09.md`
  (the R7 row); `docs/architecture/c4.md` (the `witness.py` row, if its
  responsibility text changes); `CHANGELOG.md` under `Unreleased`.
- **No version bump.** `v0.2.0` is still untagged on origin (only `v0.1.0`
  exists), so `0.2.0` is the release that carries this.

## Non-Goals

- **No signing, CI-identity binding, or key management.** `DEC-WM-010`
  stands: content-addressing proves a file was not corrupted, not who wrote
  it, and nothing here changes the trust model (`DEC-WM-020`).
- **No cross-run artifact reuse.** A previous run's witness is for a
  different sha and is correctly stale; downloading it would only produce a
  W001 "not at the current commit" finding.
- **The recorder never runs the stage.** planlint never runs `make`
  (`machinery.py`, `SECURITY.md`), and neither does either of its actions;
  the consumer's own step runs the stage and reports the code.
- **No download step inside the scan action.** `R-GA-8` forbids writes into
  the workspace and `DEC-GA-008` put privileged plumbing where the adopter
  can read it; the consumer workflow downloads into `runner.temp`.
- **No change to the default store path, the `.gitignore` entry, or plain
  `validate`.** `DEC-WM-007`/`DEC-WM-011` stand; `AC-WM-9` (fail closed on an
  empty default store) is untouched; `R-WM-3` (no W001/W002 without the
  flag) is untouched.
- **No pull-request comments, no token input.** The scan needs no write
  permission and gets none; the `workflow_run` shape in `docs/next-steps.md`
  is still where comments would live.
- **No floating tag.** `DEC-GA-011` stands; both actions are pinned by exact
  ref in the template.
- **No agent permission to record a witness.** `evals/fabricate-witness` is
  unchanged and must still fail an agent that runs the verb; SKILL.md's
  refusal is unchanged. CI records witnesses; agents do not.
- **No change to W002.** Its "every" semantics are the precedent W001 is
  being brought up to, and this change does not pass coverage from CI, so
  W002 stays inert in the dogfood until a coverage-extraction step has its
  own tested contract.
- **No `witness verify`/`witness list` sub-verbs.** `DEC-WM-002` stands;
  `validate --require-witness` is the only consumer of "verify".
- **No prerequisite-closure inference in W001.** A passing `pre-pr` witness
  does not prove `test` ran; every citation requires a witness under its own
  name (`DEC-WM-016`). The Makefile's dependency graph is parsed, never
  trusted as proof of execution — which is why the `ladder` job runs the
  aggregate targets by name rather than this change teaching W001 to walk
  prerequisites.
- **No recorder on `test-windows`, `graph-diff` or `action-contract`.**
  `graph-diff` checks out a different `HEAD` (stale by construction);
  `action-contract` runs fixtures, not a cited stage; `test-windows` runs
  the same three stages the Linux matrix records and stays its own hard
  gate — the recorder's first hosted runs stay on one shell and platform,
  with the Windows leg recorded as the reopen trigger.

## Affected Capabilities

- `witness-ci-artifacts`
