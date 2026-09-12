# Spec: GitHub Action Contract

> **Change:** `add-finding-line-hits`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The composite Action is a thin scan adapter (`R-GA-1`) and today it cannot
pass the two `validate` flags a consumer already has on the CLI:
`--change` and `--dialect`. The scan step always validates the whole
target at the detect-derived dialect.

**Evidence:** `.github/actions/planlint/action.yml:222-224` runs
`planlint --target "$INPUT_TARGET" validate --fail-on "$INPUT_FAIL_ON"
--format json` — no `--change`, no `--dialect`. The scan-step env
(`action.yml:199-203`) exports `INPUT_TARGET` and `INPUT_FAIL_ON` only.
`openspec_graph/cli.py:879-880` (`p_val`) already declares both flags.
`R-GA-3` in `openspec/changes/add-github-action-contract/specs/github-action-contract/spec.md`
requires the Action's inputs to be *exactly* `target`, `version`,
`fail-on`, `python-version`, `upload-artifact`, and `artifact-name`, and
forbids a raw argument pass-through. `docs/next-steps.md` item 3 records
the reopen trigger this package takes: named inputs for `--change` and
`--dialect`, no `extra-args`, `--require-witness` left off the Action
because `.planlint/` is gitignored and a fresh CI checkout always fails
W001 closed.

`tests/test_action_contract.py:40-42` pins `EXPECTED_INPUTS` to those six
names; `ActionRun` (`test_action_contract.py:368-371`) defaults the same
six. `AC-GA-12` asserts "exactly the six inputs". This delta supersedes
that closed list; it does not reopen `extra-args`, `--require-witness`,
Marketplace listing, or a floating `v1` tag.

Templates need not start passing the new inputs: empty defaults omit the
CLI flags, so `templates/spec-gate.yml` and the skill twin stay valid
without an edit.

---

## Requirements

- R-GA-28: The action's inputs MUST be exactly `target`, `version`,
  `fail-on`, `python-version`, `upload-artifact`, `artifact-name`,
  `change`, and `dialect`. This supersedes `R-GA-3`'s closed list of six
  names. The rest of `R-GA-3` stands: the action MUST NOT expose a raw
  argument pass-through, and MUST NOT declare an input whose name
  contains `token`. (`DEC-GA-017`)
- R-GA-29: Inputs `change` and `dialect` MUST be `required: false` with
  default `""`.
- R-GA-30: An empty `change` input MUST omit `--change` from the
  `validate` argv. An empty `dialect` input MUST omit `--dialect` from
  the argv and MUST NOT pass `--dialect auto`. Detect-derived dialect
  for the run MUST remain unchanged when `dialect` is empty.
  (`DEC-GA-018`)
- R-GA-31: The scan step MUST export `INPUT_CHANGE` and `INPUT_DIALECT`
  from the new inputs, MUST build the `validate` command as an argv
  array, and MUST append `--change "$INPUT_CHANGE"` / `--dialect
  "$INPUT_DIALECT"` only when the corresponding value is non-empty.
  (`DEC-GA-021`)
- R-GA-32: The action MUST NOT declare an `extra-args` (or `args`)
  input, and MUST NOT pass `--require-witness` on any `planlint`
  invocation it runs. (`DEC-GA-019`)
- R-GA-33: `tests/test_action_contract.py`'s `EXPECTED_INPUTS` MUST
  include `change` and `dialect`. `ActionRun`'s default `inputs` MUST
  include `change: ""` and `dialect: ""` so a test that does not pass
  them still simulates the shipped defaults.
- R-GA-34: `templates/spec-gate.yml` and the skill's byte-identical copy
  NEED NOT start passing `change` or `dialect`. The two files MUST remain
  byte-identical to each other. (`DEC-GA-020`)
- C-GA-6: This change MUST NOT add a raw `extra-args` or `args` input.
- C-GA-7: This change MUST NOT expose `--require-witness` through the
  composite action.
- C-GA-8: This change MUST NOT increment `FINDINGS_SCHEMA_VERSION` and
  MUST NOT bump the package version.
- C-GA-9: This change MUST NOT require the consumer templates to declare
  the new inputs.
- C-GA-10: This change MUST NOT create a Marketplace listing, a floating
  `v1` tag, a root `action.yml`, or a CP-8 corpus.

---

## Decisions

- **DEC-GA-017 (supersedes `R-GA-3`, in part):** the input set grows from
  six names to eight by adding `change` and `dialect`. `R-GA-3` closed the
  list on purpose — so a raw pass-through and a token input could not
  land as "just another input" — and `docs/next-steps.md` item 3 named
  the two flags as the reopen trigger rather than inventing `extra-args`.
  This decision takes that trigger and leaves the rest of `R-GA-3`
  standing: no pass-through, no `token`. `AC-GA-12`'s "exactly the six
  inputs" wording is therefore stale as of this package; `R-GA-28` is
  the list going forward. Adding an output remains allowed within a
  major version (`R-GA-4`); adding an input is the stronger change, which
  is why it is specified here rather than waved through as compatible.
- **DEC-GA-018:** empty means omit the flag, not pass a sentinel.
  `--dialect auto` is a real CLI choice (`cli.py:880`) that *overrides*
  detection. Passing it when the Action input is empty would change
  behaviour for every current consumer: detect-derived dialect would
  become an explicit `auto` at the CLI boundary, which is a different
  code path than "flag absent". `--change` has no empty-string meaning
  either; an empty value must not become `--change ""`. The default `""`
  on both inputs is what makes templates that do not mention them keep
  working (`R-GA-34`).
- **DEC-GA-019:** no `extra-args`, no `--require-witness` on the Action.
  A raw pass-through is how `--require-witness`, `--json` aliases, and
  future flags leak onto a wrapper that has no test for them.
  `--require-witness` fails closed on a fresh CI checkout (the store is
  gitignored); exposing it here would turn every adopter's first Action
  run red for a reason that is not their specs. The skill already tells
  agents not to pass the flag in CI unless the store is present. That
  advice applies to the wrapper too.
- **DEC-GA-020:** templates need not start using the new inputs. Requiring
  `templates/spec-gate.yml` to pass `change` / `dialect` would force a
  lockstep edit of the skill twin (`C-GA-4` in the live package, still in
  force) for a feature the default workflow does not need: it already
  validates the whole repository. Empty defaults plus `DEC-GA-018` make
  "no mention" equivalent to "not passed".
- **DEC-GA-021:** the scan step builds `validate`'s argv as an array and
  appends optional flags, rather than interpolating them into a single
  string. An empty value must not leave a dangling `--change` or become
  a word-split. The existing `planlint --target "$INPUT_TARGET" validate
  --fail-on "$INPUT_FAIL_ON" --format json` line is the thing that
  grows; `validate` still runs exactly once (`R-GA-2`). Tests that
  currently match that literal (`test_the_action_runs_validate_once_and_projects_the_rest`,
  `test_the_step_extractor_sees_the_whole_action`) MUST be updated to
  keep asserting "once" against the array form rather than frozen to the
  two-flag spelling.

---

## Acceptance Criteria

- [ ] **AC-GA-25:** The action declares `change` and `dialect` in addition
  to the previous six inputs, both optional, both defaulting to empty;
  `EXPECTED_INPUTS` and `ActionRun`'s defaults include them. No `token`
  input appears. (R-GA-28, R-GA-29, R-GA-33, DEC-GA-017)
  _Verified by:_ `pytest -k test_action_inputs_include_change_and_dialect` · stage: `make test`

- [ ] **AC-GA-26 (non-success):** With `change` and `dialect` left empty
  (the shipped default), the scan step's `validate` argv does not contain
  `--change`, does not contain `--dialect`, and does not contain
  `--dialect auto`. Detect-derived dialect is unchanged.
  (R-GA-30, R-GA-31, DEC-GA-018, DEC-GA-021)
  _Verified by:_ `pytest -k test_empty_change_and_dialect_inputs_omit_cli_flags` · stage: `make test`

- [ ] **AC-GA-27:** A non-empty `change` input appears as `--change
  <value>` on the scan step's `validate` argv, and `validate` still runs
  exactly once. (R-GA-31, DEC-GA-021)
  _Verified by:_ `pytest -k test_nonempty_change_input_passes_change_flag` · stage: `make test`

- [ ] **AC-GA-28:** A non-empty `dialect` input appears as `--dialect
  <value>` on the scan step's `validate` argv, and an empty `change` on
  the same run still omits `--change`. (R-GA-31, R-GA-30, DEC-GA-021)
  _Verified by:_ `pytest -k test_nonempty_dialect_input_passes_dialect_flag` · stage: `make test`

- [ ] **AC-GA-29 (non-success):** The action YAML does not declare
  `extra-args` or `args`, and no step passes `--require-witness`. No
  Marketplace listing, floating `v1` tag, root `action.yml`, or CP-8
  corpus is added. (R-GA-32, C-GA-6, C-GA-7, C-GA-10, DEC-GA-019)
  _Verified by:_ `pytest -k test_action_does_not_pass_require_witness` · stage: `make test`

- [ ] **AC-GA-30 (non-success):** The consumer templates still do not have
  to pass `change` or `dialect`; `templates/spec-gate.yml` and the skill
  copy remain byte-identical; `FINDINGS_SCHEMA_VERSION` stays `1` and the
  package version is not bumped by this delta. The failing Action fixture
  is not used as proof of annotation `line=`, because its ERROR is G004
  (unknown make target in the labelled failing fixture) which this change
  leaves at line 0.
  (R-GA-34, C-GA-8, C-GA-9, DEC-GA-020)
  _Verified by:_ `pytest -k "test_skill_asset_matches_template or test_envelope_carries_a_schema_version or test_a_line_of_zero_emits_no_line_property"` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-GA-25..30 |
| Core | `make ci` | AC-GA-25..30, plus lint and this repo's own `planlint validate` |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, no-hardcoded-thresholds |
