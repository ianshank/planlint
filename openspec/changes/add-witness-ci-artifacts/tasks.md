# Milestones

## Milestone 0 — Grounding pass

- Re-establish against the tree, each cited in `proposal.md`: the hard-coded
  store (`witness.py:37,104,176`; `detect.py:715`; `.gitignore:55`); the
  clone-fails / copy-passes reproduction; `DEC-WM-011`'s anticipated
  cross-job shape with no `--witness-dir` to realise it; `R-GA-8` and the
  `action-contract` job's `git diff --quiet` guard (`ci.yml:307`) that keep
  the scan action from ever downloading into the checkout; W001's `any`
  (`rules_witness.py:61`) against W002's `every` (`DEC-WM-019`).
- Re-measure the stage set W001 enforces with the package's own extraction
  (`parse_harness.py:55` — the Verified-by line only;
  `rules_witness.py:31-34`), not the whole-file regex the peer review used,
  over the 43 spec files excluding this package's own. Record both numbers:
  14 stages by whole-file regex, 12 on Verified-by lines, 11 once
  `fix-heading-regex-newline-span` AC-HNS-12's `matcher-accuracy` citation
  is re-pointed to `make test` (`DEC-PM-011`). `e2e-live` and
  `skill-catalog` are prose and matrix mentions only;
  `lint-empty-speckit-requirements/.../spec.md:132` sits inside `R-SER-10`,
  not a criterion, so W001 never reads it and that spec needs no edit.
- Confirm `v0.2.0` is still untagged on origin, so no version moves.
- **Gate:** `make validate`

## Milestone 1 — Change package

- `proposal.md`, `tasks.md`, `specs/witness-ci-artifacts/spec.md` written
  spec-first; every AC unchecked; `Status: DRAFT`. Reviewed by
  `spec-adversary` before any code; its four MEDIUM decisions recorded as
  `DEC-WCA-023` (rewritten), `DEC-WCA-024`, `DEC-WCA-025` and `R-WCA-35`.
- **Gate:** `make validate`

## Milestone 2 — Store and profile plumbing

- `openspec_graph/witness.py`: `load_witnesses(root, directory=None)` and
  `write_witness(root, witness, directory=None)`; `None` resolves to
  `root / WITNESS_DIR_NAME`. Docstrings say the default is unchanged and the
  explicit directory may lie outside the target. No schema, hash, or
  atomic-write change. `WITNESS_DIR_NAME` unchanged.
- `openspec_graph/detect.py`: `profile(root, witness_dir=None)` forwards to
  `load_witnesses`. `_current_sha(root)` still runs against the target root
  and still only when the loaded store is non-empty. Nothing added to
  `StackProfile`, `to_card()`, `as_dict()`, or `dialect_card._COMPARABLE_FIELDS`.
- `tests/test_graft_witness.py`:
  `test_load_witnesses_reads_an_explicit_directory_instead_of_the_default`,
  `test_two_stores_merge_by_directory_union`,
  `test_write_witness_under_an_explicit_directory_matches_the_default_bytes`,
  `test_profile_witness_dir_does_not_reach_the_card`,
  `test_current_sha_comes_from_the_target_not_the_witness_dir`,
  `test_current_sha_is_still_skipped_when_the_explicit_store_is_empty`.
- **Gate:** `make test`

## Milestone 3 — CLI flags

- `openspec_graph/cli.py`: `--witness-dir PATH` on `p_val` and `p_witness`.
  In `cmd_validate`, before `_profile`: `--witness-dir` without
  `--require-witness` → one stderr line naming both flags, exit 2 (the same
  boundary shape as the `--json`/`--format` conflict at `cli.py:414-420`);
  PATH missing or not a directory → one stderr line naming PATH, exit 2, no
  rule evaluated. `_profile(args)` passes `witness_dir` via `getattr`, so
  `detect`/`graph` are untouched. In `cmd_witness`: PATH resolved as given
  against the process cwd; a PATH that exists and is not a directory → exit
  2; `write_witness(..., directory=PATH)` creates it otherwise; `OSError`
  still maps to the existing "cannot write" exit 2.
- Message constants beside `_NOT_A_DIRECTORY`/`_JSON_FORMAT_CONFLICT`.
- `tests/test_graft_witness.py`:
  `test_validate_witness_dir_without_require_witness_exits_two`,
  `test_validate_witness_dir_that_does_not_exist_exits_two_and_evaluates_no_rule`,
  `test_validate_witness_dir_that_is_a_file_exits_two`,
  `test_validate_require_witness_reads_a_store_outside_the_target`,
  `test_validate_witness_dir_is_resolved_against_cwd_not_target`,
  `test_witness_verb_writes_under_an_explicit_witness_dir`,
  `test_witness_verb_creates_a_missing_explicit_witness_dir`,
  `test_witness_verb_rejects_a_witness_dir_that_is_a_file`.
- `tests/test_skill_contract.py`: `_WITNESS_DIR_PLACEHOLDER` substituted with
  an existing, empty directory created outside the tree (exit 1 from W001 is
  within `_ALLOWED_READ_ONLY_EXITS`; a missing directory would exit 2 and
  trip the vacuity guard); `READ_ONLY_INVOCATIONS` gains
  `("validate", "--require-witness", "--witness-dir", _WITNESS_DIR_PLACEHOLDER)`.
- `skills/planlint-spec-governance/references/exit-codes.md`: two rows —
  `--witness-dir` without `--require-witness`; `--witness-dir` not a
  directory — each with its message.
- **Gate:** `make test`

## Milestone 4 — W001 "every" semantics

- `openspec_graph/rules_witness.py::_missing_witness`: compute `passing` and
  `failing` over `at_commit`; proven only when `passing and not failing`;
  mixed → a fourth message naming a failing exit code; the existing three
  messages unchanged byte for byte; `Rule.description` unchanged. Module
  docstring and the `matching_witnesses` docstring in `witness.py` updated
  to say W001 is now "every" too.
- `tests/test_graft_witness.py`:
  `test_w001_fires_when_a_passing_and_a_failing_witness_share_the_current_sha`,
  `test_w001_mixed_message_names_the_failing_exit_code_and_is_distinct`,
  `test_w001_still_passes_when_every_witness_at_the_current_sha_exited_zero`.
- Confirm empirically that `tests/baseline_rules.json` and
  `tests/test_decomposition.py::_EXPECTED_HASHES["rules"]` do not move (the
  description is unchanged) and that `["validate"]`/`["graph"]` do not move
  (the golden fixture never passes `--require-witness`).
- `README.md` W001 table row reworded to add "and no failing witness at the
  current commit"; `openspec_graph/rules.py`'s module docstring likewise. The
  rule catalog is generated from `Rule.description`, which does not change,
  so `make skill-catalog` should produce no diff — confirm rather than
  assume.
- **Gate:** `make test`

## Milestone 5 — Scan action inputs

- `.github/actions/planlint/action.yml`: inputs `require-witness`
  (`default: "false"`) and `witness-dir` (`default: ""`), each with a
  description that says the consumer downloads the artifact under
  `runner.temp` and passes the path, and that the action never downloads.
  The `paths` step checks the combination first — non-empty `witness-dir`
  with `require-witness` not `"true"` → `::error` naming both inputs,
  `exit 1` — so the step id list `paths, install, scan, project, gate` is
  unchanged. The scan step's env gains `INPUT_REQUIRE_WITNESS` and
  `INPUT_WITNESS_DIR`; the argv array appends `--require-witness` when the
  value is exactly `true` and `--witness-dir "$INPUT_WITNESS_DIR"` when
  non-empty. Header comment: "download artifacts" joins the list of things
  it deliberately does not do.
- `tests/test_action_contract.py`: `EXPECTED_INPUTS` and `ActionRun` defaults
  gain `require-witness: "false"`, `witness-dir: ""`; delete
  `test_action_does_not_pass_require_witness`; add
  `test_action_inputs_include_require_witness_and_witness_dir`,
  `test_require_witness_flag_appears_only_inside_the_conditional_append`
  (keeps the `extra-args`/`args`/root-`action.yml` assertions),
  `test_false_require_witness_omits_the_flag`,
  `test_true_require_witness_passes_the_flag`,
  `test_nonempty_witness_dir_passes_the_flag_with_require_witness`,
  `test_witness_dir_without_require_witness_is_an_input_error`,
  `test_a_populated_witness_dir_outside_the_workspace_reports_pass`,
  `test_require_witness_with_no_store_reports_fail_with_w001`. Update
  `test_the_step_extractor_sees_the_whole_action`'s env set.
- `openspec/changes/add-finding-line-hits/specs/github-action-contract/spec.md`:
  `AC-GA-29` cites `test_action_does_not_pass_require_witness`, which this
  milestone deletes. In the same commit, re-point that verification citation
  at `test_require_witness_flag_appears_only_inside_the_conditional_append`
  and amend the AC's "no step passes `--require-witness`" clause to "no step
  passes it unconditionally", so `test_spec_test_citations.py` stays green
  and the older spec stops describing behaviour the action no longer has.
  One test, one name: the old name must not survive as an alias for an
  assertion it contradicts.
- `README.md`: the Action inputs table (lines 445-448) gains the two rows;
  the "no `extra-args`" paragraph (462-467) replaces "`--require-witness` is
  deliberately absent" with the recorder/gate shape and a pointer to the
  witness template.
- **Gate:** `make test`

## Milestone 6 — Recorder action

- New `.github/actions/planlint-witness/action.yml`: inputs `stage`,
  `exit-code`, `coverage`, `target`, `witness-dir`, `upload-artifact`,
  `artifact-name`, `python-version`, `version`. Steps: `paths` (resolve
  `witness-dir` to `${RUNNER_TEMP}/planlint-witnesses` when empty; resolve
  it and `RUNNER_TEMP` with symlinks followed and refuse with `::error`,
  exit 1, when the former is not under the latter — `R-WCA-36`,
  `DEC-WCA-026`; then `mkdir -p`; export `EVIDENCE` as a sibling directory under `RUNNER_TEMP`
  so the shared install body's `${EVIDENCE}/planlint-src` resolves; when
  `exit-code` is empty, emit `::notice` "stage <stage> did not run; nothing
  recorded" and set an output that skips every later step), then
  `actions/setup-python@v5`, `install` (body identical to the scan action's
  except the version probe, which runs `planlint witness --help` and refuses
  the install unless the output mentions `--witness-dir`), `sha`
  (`git -C "$INPUT_TARGET" rev-parse HEAD`; non-zero → `::error`, exit 1,
  nothing recorded), `record` (one `planlint --target "$INPUT_TARGET"
  witness --stage ... --exit ... [--coverage ...] --witness-dir "$DIR"`),
  upload under `always() && inputs.upload-artifact == 'true'`. Header
  comment states the consumer idiom, that recorder and gate must check out
  the same ref, and that an empty `exit-code` records nothing (`DEC-WCA-024`).
- `.github/dependabot.yml`: a second `github-actions` entry with
  `directory: "/.github/actions/planlint-witness"`, mirroring the existing
  `/.github/actions/planlint` block; the comment above the root entry
  mentions both composite actions. Guard:
  `test_every_composite_action_directory_is_watched_by_dependabot`
  (`tests/test_ci_hardening.py:707`) — run it first to watch it fail, then
  add the entry.
- New `tests/test_witness_action_contract.py` (flat under `tests/`, never a
  subdirectory):
  `test_the_recorder_declares_exactly_its_inputs`,
  `test_the_recorder_needs_no_token_and_no_privileged_permission`,
  `test_the_recorder_writes_only_under_runner_temp_and_the_command_files`,
  `test_the_recorder_refuses_a_witness_dir_outside_runner_temp`,
  `test_the_recorder_derives_the_sha_from_the_checkout_not_github_sha`,
  `test_the_recorder_never_invokes_make`,
  `test_the_recorder_uploads_under_always`,
  `test_the_recorder_install_step_matches_the_scan_action_minus_the_probe`,
  `test_the_recorder_probe_requires_witness_dir_support`,
  `test_the_recorder_records_a_witness_the_gate_then_accepts`,
  `test_the_recorder_records_a_failing_stage_as_a_failing_witness`,
  `test_the_recorder_refuses_a_target_that_is_not_a_git_repository`,
  `test_the_recorder_records_nothing_and_succeeds_when_exit_code_is_empty`.
  The execution half extracts and runs the shell steps the way
  `test_action_contract.py::ActionRun` does, against a `tmp_path` git
  repository, with `GITHUB_SHA` deliberately set to a different value so the
  derivation test cannot pass by accident; the empty-input test asserts no
  `planlint` invocation, an empty directory, a `::notice` line, and exit 0.
- `test_no_workflow_or_template_uses_pull_request_target` already globs
  `.github/**/*.yml`; confirm the new file appears in its parametrisation.
- **Gate:** `make test`

## Milestone 7 — Witness template and its twin

- New `templates/spec-gate-witness.yml`, copied byte for byte to
  `skills/planlint-spec-governance/assets/spec-gate-witness.yml`: header
  comment (why two jobs; `pull_request` never `_target`; recorder and gate
  check out the same ref; the artifact name must vary per stage); `on:`
  `pull_request` (no `paths:` filter — the stages are the repository's real
  gates), `push` to `main`, `workflow_dispatch`; the same `permissions`
  block as `templates/spec-gate.yml`; `stages` job (matrix `stage:` with one
  example entry and a comment "the stage names your specs cite"; checkout
  with `persist-credentials: false`; `id: run` step with
  `env: STAGE: ${{ matrix.stage }}` and the exit-capture idiom; recorder
  step `if: always()` with `exit-code: ${{ steps.run.outputs.exit-code }}`
  and `artifact-name: planlint-witness-${{ matrix.stage }}`); `gate` job
  (`needs: stages`, `if: always()`, checkout, `actions/download-artifact@v4`
  with `pattern`/`merge-multiple`/`path` under `runner.temp`; then a
  one-line step — `ls "$STORE"/*.json >/dev/null 2>&1 || { echo "::error
  title=planlint::no witness artifact was downloaded into $STORE"; exit 1; }`
  with the directory passed through `env:` — before the scan action with
  `require-witness: "true"` and `witness-dir`; then the SARIF upload step as
  in the existing template). Both `uses:` refs pin the same SHA the existing
  template pins.
- `tests/test_skill_contract.py`: `test_skill_witness_asset_matches_template`.
- `tests/test_adopter_urls.py`: extend
  `test_ci_template_pins_the_floor_the_skill_enforces` (or add
  `test_witness_template_pins_the_same_ref_on_both_actions`) to read every
  `uses: ianshank/planlint/.github/actions/...@` ref in both templates and
  require them equal.
- `tests/test_witness_action_contract.py`:
  `test_witness_template_passes_matrix_values_through_env`,
  `test_witness_template_gate_downloads_merged_artifacts_into_runner_temp`,
  `test_witness_template_gate_refuses_an_empty_store_before_scanning`,
  `test_witness_template_grants_the_same_permissions_as_the_plain_template`.
- `templates/spec-gate.yml` and its twin: untouched;
  `test_skill_asset_matches_template` still green.
- **Gate:** `make test`

## Milestone 8 — Dogfood in `ci.yml`

- `self-validate`: `make validate` replaces the bare
  `planlint --target . validate --fail-on ERROR` step; `security`:
  `make thresholds` replaces the bare
  `python tools/check_no_hardcoded_thresholds.py` step and a `make security`
  step is added (the gitleaks action step stays); `packaging`:
  `make wheel-check` replaces the `python -m build` +
  `check_wheel_metadata.py` pair.
- Every recording job (`test` legs, `self-validate`, `encoding-stress`,
  `docs`, `security`, `packaging`; `coverage-tools` has no job of its own —
  amended by `measure-coverage-once`): each stage step gets an
  `id`, `if: always()`, `set +e`, `code=$?`,
  `echo "exit-code=$code" >> "$GITHUB_OUTPUT"`, `exit $code`; each is
  followed by a recorder step `if: always()` using
  `./.github/actions/planlint-witness` with `stage`, `exit-code`, and an
  `artifact-name` of the form `planlint-witness-<job>[-<leg>]-<stage>`. The
  `if: always()` on the stage step is what keeps `typecheck` and `test`
  running and recorded when `lint` fails (`DEC-WCA-024`).
- New `ladder` job (3.12): `make ci` and `make pre-pr`, each a recorded step
  as above — the `make pre-pr` step's recorder also records `coverage-tools`,
  conditional on that step's exit 0 and recording nothing on red
  (DEC-WCA-006; amended by `measure-coverage-once`) — and nothing else; `make matcher-accuracy` is a report target
  (`DEC-PM-011`, `DEC-WCA-025`) and does not belong here.
- New `witness-gate` job: `needs:` lists every recording job and `ladder`;
  `if: always()`; `permissions: contents: read` (add `actions: read` only if
  the download step demonstrably needs it on the first hosted run);
  checkout with `persist-credentials: false`; `actions/download-artifact@v4`
  with `pattern: planlint-witness-*`, `merge-multiple: true`,
  `path: ${{ runner.temp }}/planlint-witnesses`; the same one-line
  empty-store check as the template, failing with a named `::error` before
  the scan; `./.github/actions/planlint` with `require-witness: "true"`,
  `witness-dir: ${{ runner.temp }}/planlint-witnesses`, `fail-on: ERROR`,
  `artifact-name: planlint-evidence-witness-gate`.
- `tests/test_ci_hardening.py`:
  `test_ci_workflow_has_a_witness_gate_job`,
  `test_every_recording_job_is_needed_by_the_witness_gate`,
  `test_ci_witness_recorders_use_unique_artifact_names`,
  `test_ci_recorded_stage_steps_carry_always`,
  `test_ci_witness_gate_refuses_an_empty_store_before_scanning`,
  `test_ci_ladder_runs_only_the_two_aggregates` (counting `run: make` steps,
  not recorder steps — amended by `measure-coverage-once`),
  `test_ci_runs_every_w001_enforced_stage_by_its_make_target_name` (parse
  every `openspec/changes/*/specs/*/spec.md` with the package's own parser,
  collect `MAKE_REF.findall(crit.verified_by)` over every criterion, and
  assert each stage appears as `make <stage>` in `ci.yml`, or is a
  prerequisite of an aggregate the `ladder` job runs and is recorded under
  DEC-WCA-006's one sanctioned inference — amended by `measure-coverage-once`),
  `test_no_ci_step_runs_the_witness_verb_outside_the_recorder`.
- `docs/hooks.md`: rows `| `ladder` | push + PR | `make ci` + `make pre-pr`,
  each recorded as a witness (hard) |` and `| `witness-gate` | push + PR |
  the scan action with `require-witness` over the merged witness artifacts
  of every recording job (hard) |`; the `self-validate`, `security`,
  `packaging` gate cells name their make targets.
- First hosted run: the `witness-gate` job's W001 findings, if any, name
  exactly the Verified-by citations CI does not back. Each is a citation to
  fix in that spec — never a witness to record by hand, never a Makefile
  target added or renamed to make one resolve (`SKILL.md`). Expected: zero,
  because Milestone 0's re-measurement found every W001-enforced stage is
  run by name after this milestone. If the run shows otherwise, the
  re-measurement was wrong and the finding is the correction.
- **Gate:** `make pre-pr`

## Milestone 9 — Docs and close-out

- `skills/planlint-spec-governance/SKILL.md`: Witness mode section describes
  the recorder/gate shape and `--witness-dir`; "Never run `witness` yourself
  to make the flag pass" stays verbatim; the "Do not expose it through the
  composite Action" sentence is replaced by "the Action's `require-witness`
  input is for a workflow that downloaded a witness artifact, not for an
  agent"; the writes-files row for `witness` mentions `--witness-dir`; the
  "Wiring it into CI" section names `assets/spec-gate-witness.yml`.
- `README.md`: the witness paragraph (199-206) describes record-in-the-job,
  upload, download-into-`runner.temp`, empty-store check, gate; the Action
  section links the witness template. `llms.txt` if it lists templates.
- `docs/next-steps.md`: item 3 (lines 34-37) struck through and pointed
  here; the deferral-table row at line 225 that says to leave the flag alone
  amended. `docs/differentiation-roadmap.md`: the v2 note rewritten from
  "does not yet reach CI" to the shipped shape, citing the `witness-gate`
  job (its `.gitignore` line number already reads 55, corrected on the
  planning branch; the dated 2026-09 review keeps its own 52, which was right
  at the commit it measured).
  `docs/peer-review-2026-09.md`: R7 row → "shipped —
  `add-witness-ci-artifacts`". `docs/architecture/c4.md`: the `witness.py`
  row mentions the explicit-directory reader/writer if its responsibility
  text changes. `CHANGELOG.md` under `[Unreleased]`: the two flags, the W001
  tightening, the two action inputs, the recorder and its empty-input rule,
  the dependabot entry, the template, the dogfood jobs; no version bump.
- `evals/fabricate-witness/` unchanged; confirm its graders still fail an
  agent that runs the verb.
- Flip this package's ACs to `[x]` only as each is actually verified; leave
  `AC-WCA-27` until the hosted job has run green.
- **Gate:** `make pre-pr`
