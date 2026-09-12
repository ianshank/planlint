# Spec: GitHub Action Contract

> **Change:** `add-github-action-contract`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The composite action is the one artifact by which an outsider reproduces
planlint in a clean environment, and it could not be reproduced by anyone: its
install line named a distribution that is not on the index, it exposed no
outputs, it uploaded no evidence, it wrote a file into the repository it
linted, and it relayed a run that checked zero specs as a pass. The CLI
underneath already held every property the wrapper lacked — deterministic JSON,
a read-only guarantee, a three-way exit-code contract, a SARIF projection that
is a pure function of the JSON — so the work was to make the wrapper as honest
as the tool.

**Evidence:** the pre-change `.github/actions/planlint/action.yml:54` ran
`pip install "planlint${{ inputs.version }}"` with a default of `>=0.2.0,<1`;
PyPI returns `404` for `planlint` and `pip index versions planlint` finds no
distribution, and the only tag on `origin` is `v0.1.0` under the pre-rename
name. That file declared inputs and no `outputs:` block, redirected
`validate --format sarif` to `planlint.sarif` in the consumer's working
directory, and guarded the upload on `hashFiles` alone — which cannot address a
path outside `GITHUB_WORKSPACE`, and which on a fork pull request fails before
the gate step can explain anything. `cli.py::cmd_validate` (`cli.py:404`,
`cli.py:496-508`) prints `0 spec(s) checked` / `PASS` and exits 0 on an
`openspec/changes/` directory with no packages. `sarif.to_sarif`
(`sarif.py:103-109`) takes serialized finding dicts and the rule table — the
envelope's own `findings` list — so SARIF is computable from the envelope file.

Two further defects were found while grounding the design, and both are fixed
here because leaving either would make a criterion below untrue rather than
merely incomplete:

- **The adopter install-line guard was hollow.**
  `tests/test_adopter_urls.py::_requirements` split a requirement token on
  `[<>=!~;` only, so `planlint${{ inputs.version }}` parsed as a package name
  nobody publishes and `_confusable()` skipped the line as somebody else's.
  The action's install line has been outside the rename guard since it landed.
- **Composite steps start under `errexit`.** GitHub runs a `shell: bash`
  composite step as `bash --noprofile --norc -eo pipefail {0}`, so a body that
  merely omits `set -e` still dies on the first non-zero command — before an
  exit code can be recorded. Observed directly, by executing the action's own
  steps (`tests/test_action_contract.py`).

---

## Requirements

### Layering

- R-GA-1: The action MUST be a composite action whose only responsibilities are
  to install the CLI, invoke it, project its machine-readable output into
  GitHub surfaces, upload the evidence, and relay the gate. It MUST NOT parse
  the CLI's text output, evaluate a rule, or decide severity policy: `fail-on`
  is passed to `validate --fail-on` unchanged.
- R-GA-2: The action MUST run `validate` exactly once per invocation, with
  `--format json`, and MUST derive every other surface — SARIF, annotations,
  the job summary, the outputs — from that one envelope through
  `planlint report`. It MUST NOT run `validate` a second time for a second
  format.
- R-GA-3: The action's inputs MUST be exactly `target`, `version`, `fail-on`,
  `python-version`, `upload-artifact` and `artifact-name`. It MUST NOT expose a
  raw argument pass-through, and MUST NOT declare an input whose name contains
  `token`.
- R-GA-4: The action MUST expose at least these outputs: `status`, `exit-code`,
  `errors`, `warnings`, `infos`, `findings`, `blocking`, `specs-checked`,
  `rules-triggered`, `dialect`, `make-targets`, `coverage-floor`,
  `discovery-warnings`, `version`, `evidence-dir`, `json-path`, `sarif-path`,
  `evidence-sha256`. Within a major version an output MAY be added and MUST NOT
  be renamed, removed, or given a different meaning.

### The gate

- R-GA-5: `status` MUST be exactly one of `pass`, `fail`, `error`,
  `indeterminate`. `fail` when the envelope's `blocking` exceeds zero;
  `indeterminate` when `blocking` is zero and `specs_checked` is zero; `pass`
  otherwise. `error` MUST be reported when no envelope exists or when `report`
  cannot project the one that does, and the gate MUST treat an absent or
  unrecognised `status` as `error`.
- R-GA-6: Only `pass` MAY leave the job green. `fail`, `indeterminate` and
  `error` MUST each fail the job with a message distinct from the other two:
  the `indeterminate` message MUST state that nothing was checked and name what
  to add, and the `error` message MUST say it is a precondition or usage error
  rather than a spec failure, and MUST quote the CLI's captured stderr.
- R-GA-7: Every step of the action that can observe a non-zero exit MUST
  disable `errexit` explicitly. Relying on the absence of `set -e` is
  insufficient, because a composite `shell: bash` step begins with it enabled.

### Evidence

- R-GA-8: Every file the action writes MUST live under a directory beneath
  `$RUNNER_TEMP`. The action MUST NOT create, modify or remove any file in
  `GITHUB_WORKSPACE`, including build artifacts from installing the CLI.
- R-GA-9: The evidence directory MUST contain `run.json` on every run, and —
  whenever `validate` exited 0 or 1 — the envelope byte-for-byte as `validate`
  printed it, its SARIF projection, the dialect card, the annotation stream and
  the job summary. `findings.json`, `findings.sarif` and the dialect card MUST
  be byte-identical across two runs on an unchanged tree and build; every
  non-deterministic value MUST live only in `run.json`.
- R-GA-10: The artifact upload MUST run whenever the action ran, including on
  `fail` and on `error`, conditioned on `upload-artifact` and `always()` and on
  nothing else.

### The `report` verb

- R-GA-11: A read-only verb `report` MUST exist, taking `--findings FILE`, an
  optional `--card FILE`, an optional `--path-prefix`, and a required
  `--format` of `sarif`, `github-annotations`, `github-summary` or
  `github-outputs`. It MUST print to stdout only, MUST NOT create, modify or
  remove any file, MUST ignore the global `--target`, and MUST NOT exit 1 under
  any input.
- R-GA-12: `report` MUST exit 2, with one message on stderr and nothing on
  stdout, when the findings file is unreadable, is not JSON, is not an object,
  carries a foreign `schema_version`, lacks any of `schema_version`,
  `tool_version`, `specs_checked`, `findings` or `blocking`, carries a
  `findings` that is not a list, carries a count that is not a non-negative
  integer, or carries a finding that is not an object or lacks `rule`,
  `severity`, `message`, `path` or `line` or types them wrongly. A card passed
  with `--card` MUST be held to the same standard.
- R-GA-13: `report --format sarif` over the envelope `validate --format json`
  printed MUST produce stdout byte-identical to `validate --format sarif` for
  the same tree and build, on a tree with findings and on a clean one.
- R-GA-14: `report --format github-annotations` MUST emit one workflow command
  per finding in envelope order: `::error` for `ERROR`, `::warning` for `WARN`,
  `::notice` for `INFO`, and `::error` for any unrecognised severity, never a
  lower level. It MUST carry `file=` only when the finding has a path,
  `line=` only when the line is at least 1, and `title=` set to the rule id.
  Message text MUST be escaped `%`→`%25`, CR→`%0D`, LF→`%0A`; property values
  additionally `:`→`%3A` and `,`→`%2C`, and only there.
- R-GA-15: The annotation cap MUST be applied per severity, at a module-level
  constant, so a run whose earliest findings by path are warnings cannot
  withhold the error that failed the gate. When anything is withheld, exactly
  one trailing notice MUST say how many.
- R-GA-16: `--path-prefix` MUST prepend the target's position inside the
  repository to each annotation's `file=`, so a subdirectory target's
  annotations resolve from the repository root. Absent the flag, output MUST be
  unchanged.
- R-GA-17: `report --format github-outputs` MUST emit one `key=value` line per
  envelope-derivable output, with no newline inside any value.
  `rules-triggered` MUST be sorted, de-duplicated and comma-joined.
- R-GA-18: `report --format github-summary` MUST emit Markdown carrying the
  status, the counts and a findings table, capped as R-GA-15 requires, with
  table-breaking characters escaped. It MUST be a pure function of its inputs.
- R-GA-19: `report` MUST print one stderr warning, and MUST NOT refuse, when
  the envelope's `tool_version` differs from the running build's. Stdout MUST
  be unaffected.
- R-GA-20: `openspec_graph/report.py` MUST be pure and stdlib-only, MUST
  perform no I/O, and MUST import no module of this package — the schema
  versions it validates against are parameters, not imports. That property MUST
  be checked mechanically rather than asserted.

### Discovery

- R-GA-21: Given `--card`, `report` MUST report the detected dialect, the
  make-target count and the coverage-floor locator, and MUST emit one warning
  per rule family that had nothing to check against: no make targets leaves the
  cited-stage rule with nothing to compare, and no coverage floor leaves the
  hard-coded-threshold rule unable to confirm a cited number. It MUST emit no
  such warning when both are present, and MUST NOT change `status` on account
  of either.

### Install source and versioning

- R-GA-22: With `version` empty, which MUST be the default, the action MUST
  install the CLI from its own checkout, so the `uses:` reference pins the CLI
  and the adapter together. The build MUST NOT write into the checkout. With
  `version` set to an exact version, the action MUST install
  `planlint==<version>` from the package index on a line the adopter
  install-line guard parses as this distribution.
- R-GA-23: The template and the README MUST pin the action to an exact release
  tag and MUST document full-sha pinning. The template's tag MUST equal both
  `openspec_graph.__version__` and the skill's `planlint-min-version`. No
  floating major tag MAY be created or documented by this change.

### Security posture

- R-GA-24: The string `pull_request_target` MUST NOT appear in any file under
  `.github/`, `templates/` or `skills/`, comments included. The action MUST
  require no secret, MUST declare no token input, and MUST contain no step
  needing a write permission.
- R-GA-25: SARIF upload MUST live in the consumer workflow, not the action, so
  the permission it needs is declared where an adopter can read it. The
  template MUST declare `permissions` explicitly, MUST check out with
  `persist-credentials: false`, MUST skip rather than fail the upload on a fork
  pull request and where code scanning is unavailable, and MUST trigger on
  `pull_request`, `push` to the default branch and `workflow_dispatch`, with
  its own path in the pull-request path filter.

### Verification

- R-GA-26: The action's own shell steps MUST be exercised locally against
  labelled fixture targets under `tests/fixtures/action/`, with GitHub's
  environment simulated, so the status derivation, the evidence bundle and the
  gate messages are covered by `make test`.
- R-GA-27: CI MUST additionally run the real action (`uses: ./...`) against
  every one of those fixtures under `permissions: contents: read` with no
  secret, asserting each fixture's labelled outcome, status and exit code, and
  MUST fail if a fixture exists with no matching leg. The job MUST appear in
  `docs/hooks.md`'s CI table and MUST NOT be composed into any Makefile target.

### Constraints

- C-GA-1: This change MUST NOT alter `validate --json`'s envelope,
  `rules.FINDINGS_SCHEMA_VERSION`, any of `_EXPECTED_HASHES`, or
  `tests/baseline_rules.json`.
- C-GA-2: This change MUST NOT add a rule, a rule family, or a field on the
  `Rule` dataclass. `ALLOWED_VERBS` MUST grow by exactly `report`.
- C-GA-3: This change MUST NOT add a runtime or test dependency, including a
  YAML parser. YAML artifacts are read by line scan.
- C-GA-4: `templates/spec-gate.yml` and the skill's copy of it MUST remain
  byte-identical, and SKILL.md's read-only table, `READ_ONLY_INVOCATIONS`,
  `llms.txt` and the exit-code reference MUST all list `report`.
- C-GA-5: `make pre-pr`'s composition MUST NOT change.

---

## Decisions

- **DEC-GA-001:** three layers with a hard boundary — consumer workflow,
  composite action, CLI — and the action stays deliberately boring. A wrapper
  that starts deciding severity, discovering machinery or reshaping findings in
  YAML is a second implementation of the tool in a language with no tests.
- **DEC-GA-002:** the envelope is the canonical evidence and every other
  surface is a projection of it. Running `validate` twice spends double the
  work asking one question and lets two runs disagree; adding write flags to
  `validate` would put file-writing inside the verb whose whole guarantee is
  that it only reads (`DEC-SA-012`). Projecting needs neither, and R-GA-13
  turns "no divergence" from a property two code paths must maintain into a
  byte-identity a test asserts. This supersedes `R-SA-16`, which had the action
  produce SARIF from its own `validate` run.
- **DEC-GA-003:** the projections are a CLI verb, not a script in the action
  directory. Code under `.github/` sits outside `[tool.coverage.run] source`,
  so the escaping rules of R-GA-14 — the part shell-and-jq implementations get
  wrong — would be enforced by nothing; a script shipped with the action and a
  CLI installed from the index can be different builds; and `report` reuses
  `sarif.py` rather than vendoring a copy. The cost is one reviewed addition to
  a closed verb set, and the surface stays read-only and non-authoring, which
  is what `AC-RP-3` actually protects.
- **DEC-GA-004:** `status` is derived from the envelope alone; `report` takes
  no `--exit-code`. `cmd_validate` computes `blocking` and returns
  `1 if blocking else 0` from the same list, so exit 1 and `blocking > 0` are
  one fact stated twice. The single status the envelope cannot express is
  `error` — an exit-2 run prints nothing on stdout — and that mapping is the
  only status logic the YAML holds.
- **DEC-GA-005:** `indeterminate` fails the job and there is no input to change
  that. The failure it forbids is a green check over an unmeasured repository.
  `DEC-SA-011` already settled the shape of this argument for exit codes, and
  the same escape applies: `continue-on-error` on the step plus a branch on
  `status`, both visible in the workflow. An `allow-indeterminate` input would
  be a knob whose only purpose is to make a false green available by
  configuration.
- **DEC-GA-006:** the CLI is installed from the action's own checkout by
  default. This supersedes the action-internal half of `DEC-SA-009`'s install
  line and only that half: the README, the skill preflight and the pre-commit
  hook still say `pip install planlint`, and `docs/distribution-plan.md` §3 is
  still what makes those true. The honest trade, stated rather than glossed: a
  published wheel is one hashable artifact that runs no build, while a checkout
  install fetches an unpinned `setuptools>=77` and executes it, so the `uses:`
  sha pins the source but not the toolchain. It is a stopgap that makes the
  action runnable at any ref today, and the reopen trigger is recorded in
  `docs/next-steps.md`: once the distribution is published, the default becomes
  an exact pinned install.
- **DEC-GA-007:** the build happens in a copy under `$RUNNER_TEMP`, not in
  place. `pip install <dir>` builds in that directory and leaves `build/` and
  `*.egg-info` behind — verified — and when the action is referenced as
  `./.github/actions/planlint` the action path *is* the workspace, so an
  in-place build writes into the repository being scanned. The copy is derived
  from an ignore list rather than an allow list, so a change to the package
  layout cannot silently stop shipping part of it.
- **DEC-GA-008:** SARIF upload moves to the consumer workflow, reversing the
  shape `add-sarif-and-actions` shipped. Keeping it inside the action meant an
  expression that had to be right about three things at once — a fork, a
  missing file under `$RUNNER_TEMP` that `hashFiles` cannot see, and a
  repository without code scanning — while the permission it needs stayed
  invisible to the person granting it. Three lines in a template an adopter
  copies anyway buys: no `security-events` anywhere in the action, no
  expression surface, and a failure mode that is skipped rather than fatal.
- **DEC-GA-009:** the annotation cap is per severity, at GitHub's own per-step
  limit. Envelope order is `(path, rule)`, not severity, so one shared budget
  lets a file full of warnings withhold the error that failed the gate — a red
  X with no annotation explaining it. Per severity, the error's budget is never
  spent by warnings. The number is a module constant, not an action input: it
  is a property of the surface, and a bare number in the action YAML is exactly
  the hard-coded threshold this project fails other repositories for.
- **DEC-GA-010:** discovery facts are reported, and `status` is untouched by
  them. Two rules relax when the fact they compare against is absent, which is
  correct for a rule — inventing a finding from missing evidence would be worse
  — and means a green run over such a repository proves less than it looks like
  it proves. Saying so is projection and ships here; changing what the rules do
  about it is policy, belongs in the rules, and gets its own design pass.
- **DEC-GA-011:** no floating major tag and no Marketplace listing before 1.0.
  `add-sarif-and-actions` declined both; DEC-GA-006 removes the last reason to
  want a floating tag early, since an exact tag now pins the CLI too. Moving a
  `v0` tag each release would also need `contents: write` in the release
  workflow, which holds `contents: read` plus `id-token: write` on the publish
  job alone.
- **DEC-GA-012:** the template pins `@v<X.Y.Z>` equal to
  `openspec_graph.__version__`, and the pin-parity test is re-pointed at that
  ref rather than deleted. Between releases the template therefore names the
  next tag — the same semantics the previous `>=0.2.0` pin had, and the
  semantics the release workflow's tag-equals-version check makes true at tag
  time.
- **DEC-GA-013:** the action's own steps are extracted and executed in
  `make test`. YAML's usual failure mode is that nobody finds out it is wrong
  until a runner says so, and everything this change fixes was well-formed YAML
  saying the wrong thing. The extractor is a line scan, matching
  `DEC-AQA-005`'s reasoning and `C-GA-3`. It found a real defect immediately:
  composite steps begin under `errexit`, so `set -uo pipefail` did not clear
  it and every fallible step would have died on its first non-zero command.
- **DEC-GA-014:** `report` is the one verb that never reads the target. It
  takes the envelope path explicitly and ignores `--target`, so it can project
  an artifact downloaded on another machine — the cross-machine case
  `add-findings-json-envelope` made the envelope portable for. It still joins
  `READ_ONLY_INVOCATIONS`, because "leaves the tree byte-identical" is the
  claim and a verb that should touch nothing is worth holding to it. The
  exit-code reference says `--target` does not apply, since `cli.py`'s
  "every verb's target check" comment stops being universal here.
- **DEC-GA-015:** `pull_request_target` is forbidden by a test, comments
  included. The event hands a workflow write permissions and secrets while
  checking out attacker-controlled content, the failure is silent, and a
  commented-out example is one paste from being real.
- **DEC-GA-016:** the install-line guard is fixed in this change rather than
  noted. `_requirements()` stopped at `[<>=!~;`, so a shell-interpolated
  install line parsed as a package nobody publishes and was skipped as
  somebody else's — meaning the guard `DEC-SA-009` created for the action's
  install line has never covered it. Adding a second such line while leaving
  the parser blind would reproduce the original bug in the test written to
  prevent it.

---

## Acceptance Criteria

- [x] **AC-GA-1:** `report --format sarif` over the envelope
  `validate --format json` printed is byte-identical to
  `validate --format sarif`, on a fixture with findings in more than one spec
  file — asserted non-empty first, so the equality cannot hold vacuously — and
  on a clean fixture. (R-GA-13)
  _Verified by:_ `pytest -k "test_report_sarif_is_byte_identical_to_validate_sarif or test_report_sarif_matches_on_a_clean_tree_too"` · stage: `make test`

- [x] **AC-GA-2 (non-success):** Every malformed envelope — absent, not JSON,
  an array, `null`, a foreign schema, a missing count, a wrong-typed count, a
  malformed finding — exits 2 with an empty stdout and one stderr line, in
  every format, and never exits 1. (R-GA-11, R-GA-12)
  _Verified by:_ `pytest -k "test_a_malformed_envelope_raises_rather_than_crashing_a_renderer or test_an_unprojectable_file_exits_two_with_an_empty_stdout or test_a_missing_findings_file_exits_two"` · stage: `make test`

- [x] **AC-GA-3:** `github-outputs` emits single-line `key=value` pairs whose
  counts match the envelope, with `rules-triggered` sorted and de-duplicated
  and every severity present even at zero. (R-GA-17)
  _Verified by:_ `pytest -k "test_outputs_are_single_line_key_value_pairs or test_rules_triggered_is_sorted_and_deduplicated or test_counts_cover_every_severity_even_at_zero"` · stage: `make test`

- [x] **AC-GA-4 (non-success):** A run that checked nothing is
  `indeterminate`, never `pass` — asserted both on a constructed envelope and
  on the envelope a real `validate` writes for an empty spec tree, so the unit
  test cannot be describing a state the CLI never emits. (R-GA-5, DEC-GA-005)
  _Verified by:_ `pytest -k "test_a_tree_with_nothing_to_check_is_indeterminate_not_pass or test_an_empty_spec_tree_really_produces_that_envelope or test_step_summary_names_the_indeterminate_case"` · stage: `make test`

- [x] **AC-GA-5:** Annotations map each severity to its command, carry `file=`
  only with a path and `line=` only for a real line, and escape `%`, CR, LF in
  message data and additionally `:` and `,` in property values — checked on one
  finding carrying every one of those characters. (R-GA-14)
  _Verified by:_ `pytest -k "test_annotation_escaping_covers_every_documented_character or test_a_line_of_zero_emits_no_line_property or test_a_real_line_emits_a_line_property or test_a_pathless_finding_is_annotated_without_a_file or test_an_unknown_severity_maps_up_to_error"` · stage: `make test`

- [x] **AC-GA-6 (non-success):** With more warnings than the cap and exactly
  one error, the error is still annotated — the property a single shared budget
  would break — the warnings are capped, one notice names the withheld count,
  and a run under the cap emits no notice. (R-GA-15, DEC-GA-009)
  _Verified by:_ `pytest -k "test_the_annotation_cap_is_per_severity_so_an_error_is_never_starved or test_a_capped_run_says_how_many_findings_were_withheld or test_an_uncapped_run_emits_no_withheld_notice or test_the_annotation_cap_is_a_named_constant"` · stage: `make test`

- [x] **AC-GA-7:** The job summary is byte-stable across calls, names the
  status and counts, and escapes characters that would break its table.
  (R-GA-18)
  _Verified by:_ `pytest -k "test_step_summary_is_deterministic or test_step_summary_escapes_table_breaking_characters or test_projections_are_byte_stable_across_runs"` · stage: `make test`

- [x] **AC-GA-8:** `report.py` imports no module of this package, checked by
  reading its imports rather than by resolving module roots — the existing
  stdlib-only guard deliberately drops relative imports, so several modules on
  its list have intra-package imports and pass it. It also imports in a fresh
  interpreter with nothing else from the package loaded. (R-GA-20, C-GA-3)
  _Verified by:_ `pytest -k "test_report_has_no_intra_package_imports or test_module_is_importable_without_the_rest_of_the_package or test_new_modules_stdlib_only"` · stage: `make test`

- [x] **AC-GA-9 (non-success):** `report` leaves the target tree
  byte-identical and ignores `--target` entirely, enforced by adding it to
  `READ_ONLY_INVOCATIONS` — whose digest comparison then covers it and whose
  exit-code guard stops the assertion passing because the verb refused to run —
  and by the SKILL.md parity test. (R-GA-11, C-GA-4, DEC-GA-014)
  _Verified by:_ `pytest -k "test_read_only_verbs_leave_tree_byte_identical or test_read_only_invocations_cover_every_verb_the_skill_calls_read_only or test_report_ignores_the_global_target or test_report_is_registered_as_a_read_only_verb"` · stage: `make test`

- [x] **AC-GA-10:** The verb surface is the previous nine verbs plus `report`,
  and no authoring verb was added. (C-GA-2)
  _Verified by:_ `pytest -k "test_cli_verbs_are_exactly_the_allow_list or test_cli_rejects_authoring_verbs or test_the_verb_appears_in_the_module_docstring"` · stage: `make test`

- [x] **AC-GA-11 (non-success):** The golden hashes for `validate`, `graph`
  and `rules` are unchanged and the rule set matches the committed baseline: a
  new verb and a new module changed no existing output. (C-GA-1, C-GA-2)
  _Verified by:_ `pytest -k "test_output_byte_identical or test_rule_set_matches_baseline"` · stage: `make test`

- [x] **AC-GA-12:** The action declares exactly the six inputs and every named
  output, runs `validate` once with no second SARIF run, projects each surface
  through `report`, roots its evidence outside the workspace, and uploads the
  artifact under `always()`. (R-GA-1, R-GA-2, R-GA-3, R-GA-4, R-GA-8, R-GA-10)
  _Verified by:_ `pytest -k "test_the_action_declares_exactly_the_v1_inputs or test_the_action_declares_every_v1_output or test_the_action_runs_validate_once_and_projects_the_rest or test_evidence_is_written_outside_the_workspace or test_the_artifact_upload_survives_a_failing_gate"` · stage: `make test`

- [x] **AC-GA-13 (non-success):** No file under `.github/`, `templates/` or
  `skills/` contains `pull_request_target`, comments included; the action
  declares no token input and no step needing a write permission; and the
  index-install line parses as this distribution under the adopter guard.
  (R-GA-22, R-GA-24, DEC-GA-015, DEC-GA-016)
  _Verified by:_ `pytest -k "test_no_workflow_or_template_uses_pull_request_target or test_the_action_needs_no_token_and_no_privileged_permission or test_the_install_override_names_the_published_distribution or test_install_lines_spell_this_project_the_way_it_is_published"` · stage: `make test`

- [x] **AC-GA-14:** The template and the skill's copy are byte-identical, the
  template declares its permissions, checks out without persisted credentials,
  and pins the action to a tag equal to both the package version and the
  skill's declared minimum. (R-GA-23, R-GA-25, C-GA-4, DEC-GA-012)
  _Verified by:_ `pytest -k "test_skill_asset_matches_template or test_ci_template_pins_the_floor_the_skill_enforces or test_spec_gate_template_triggers_on_speckit_trees"` · stage: `make test`

- [x] **AC-GA-15:** The action's own shell steps, extracted from the YAML and
  executed against each labelled fixture, produce that fixture's status and
  gate exit code, with the three failing statuses each explaining themselves
  differently. (R-GA-5, R-GA-6, R-GA-7, R-GA-26)
  _Verified by:_ `pytest -k "test_the_action_reports_each_fixtures_labelled_status or test_the_step_extractor_sees_the_whole_action"` · stage: `make test`

- [x] **AC-GA-16:** A failing run writes the whole evidence bundle and hashes
  the envelope; an unscannable target writes `run.json` and the captured
  stderr and no envelope at all; and the job summary reaches the summary file.
  (R-GA-9, R-GA-5)
  _Verified by:_ `pytest -k "test_a_failing_run_populates_the_whole_evidence_bundle or test_an_unscannable_target_produces_the_error_status_and_no_envelope or test_the_step_summary_reaches_the_job_summary_file"` · stage: `make test`

- [x] **AC-GA-17 (non-success):** The scanned fixture is byte-identical before
  and after a run, and the evidence lands outside it — the read-only guarantee
  held by the wrapper, not only by the CLI. (R-GA-8, DEC-GA-007)
  _Verified by:_ `pytest -k "test_the_evidence_directory_is_outside_the_scanned_tree"` · stage: `make test`

- [x] **AC-GA-18:** Annotation paths for a subdirectory target resolve from
  the repository root, and a nested target is scanned at its own root.
  (R-GA-16)
  _Verified by:_ `pytest -k "test_path_prefix_relocates_annotation_paths or test_annotation_paths_resolve_from_the_repository_root or test_a_nested_target_is_scanned_at_its_own_root"` · stage: `make test`

- [x] **AC-GA-19 (non-success):** A target with machinery produces no
  discovery warning; one with no make targets or no coverage floor produces
  exactly one each, reaching both the annotations and the summary; the
  discovery outputs are omitted entirely without a card, so "not measured" is
  distinguishable from "measured as zero"; and a malformed card is refused
  rather than degraded. (R-GA-21, DEC-GA-010)
  _Verified by:_ `pytest -k "test_a_target_with_machinery_produces_no_discovery_warning or test_a_target_with_no_make_targets_is_flagged or test_a_target_with_no_coverage_floor_is_flagged or test_discovery_warnings_reach_the_annotations_and_the_summary or test_discovery_outputs_are_omitted_without_a_card or test_a_malformed_card_is_refused or test_a_malformed_card_exits_two_without_projecting or test_a_card_from_detect_projects_without_a_warning"` · stage: `make test`

- [x] **AC-GA-20:** Each fixture produces, through the real CLI, the exit code
  and envelope its label promises, and the unscannable one writes no envelope.
  (R-GA-26)
  _Verified by:_ `pytest -k "test_each_fixture_produces_the_status_its_label_promises or test_the_no_tree_fixture_writes_no_envelope"` · stage: `make test`

- [x] **AC-GA-21:** An envelope from a different build warns on stderr, still
  renders, and renders identically to the matching-version run. (R-GA-19)
  _Verified by:_ `pytest -k "test_a_version_mismatch_warns_but_still_renders"` · stage: `make test`

- [x] **AC-GA-22:** `ci.yml` defines an `action-contract` job that runs the
  local action with `continue-on-error` under a read-only token and no secret,
  every fixture on disk has a leg, the job appears in `docs/hooks.md`'s CI
  table, and no Makefile target composes it. (R-GA-27, C-GA-5)
  _Verified by:_ `pytest -k "test_ci_workflow_has_an_action_contract_job or test_every_action_fixture_has_a_contract_leg or test_the_contract_job_is_not_wired_into_a_make_target or test_hooks_ci_table_lists_every_ci_job"` · stage: `make test`

- [ ] **AC-GA-23:** The hosted `action-contract` job is green on the pull
  request that lands this change, with every fixture's assertion step passing.
  This is the first execution of the action on a runner, and the only evidence
  that a checkout of this repository is enough to run it. The local simulation
  covers the shell; only a runner covers the `uses:` steps, the artifact upload
  and the action path. (R-GA-27)
  _Verified by:_ the `action-contract` job's own assertion steps on the pull request · stage: `make ci` must also be green on the same commit

- [x] **AC-GA-24:** The README, SKILL.md, the exit-code reference, `llms.txt`,
  `docs/hooks.md`, `docs/architecture/c4.md` and `CHANGELOG.md` describe the
  verb, the action's contract, the four statuses and the pinning rule; the docs
  gate passes. (C-GA-4)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_agent_index_links_resolve"` · stage: `make docs-check`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-GA-1..22, AC-GA-24 |
| Core | `make ci` | the above, plus lint and this repo's own `planlint validate` over this package |
| Docs | `make docs-check` | AC-GA-24 |
| Hosted | `action-contract` job in `.github/workflows/ci.yml` | AC-GA-23 |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, no-hardcoded-thresholds |
