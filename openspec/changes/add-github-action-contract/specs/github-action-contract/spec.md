# Spec: GitHub Action Contract

> **Change:** `add-github-action-contract`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The composite action at `.github/actions/planlint/action.yml` is the one
artifact by which an outsider reproduces planlint in a clean environment, and
it cannot currently be reproduced by anyone: its install line names a
distribution that is not on the index, it exposes no outputs, it uploads no
evidence, it writes a file into the repository it lints, it breaks on the
fork pull requests it exists for, and it relays a run that checked zero specs
as a pass. The CLI underneath already holds every property the action lacks —
deterministic JSON, a read-only guarantee, a three-way exit-code contract, a
SARIF projection that is a pure function of the JSON — so the work is to make
the wrapper as honest as the tool.

**Evidence:** `.github/actions/planlint/action.yml:54` runs
`pip install "planlint${{ inputs.version }}"` with a default of `>=0.2.0,<1`
(`action.yml:27`); PyPI returns `404` for `planlint` and `pip index versions
planlint` finds no distribution (2026-09-11), and the only tag on `origin` is
`v0.1.0` under the old name. `action.yml:11-43` declares inputs and no
`outputs:` block. `action.yml:78` writes `planlint.sarif` into the consumer's
working directory. `action.yml:87-92` guards the SARIF upload on `hashFiles`
alone, so a fork's read-only `GITHUB_TOKEN` fails the upload before the gate
step at `action.yml:98-112` can explain anything. `cli.py::cmd_validate`
(`cli.py:404`, `cli.py:496-508`) prints `0 spec(s) checked` / `PASS` and exits
0 on an `openspec/changes/` directory with no packages; its `--format json`
envelope for that run is `{"specs_checked": 0, "findings": [], "blocking": 0}`.
`sarif.to_sarif` (`sarif.py:103-109`) takes serialized finding dicts and the
rule table — the envelope's own `findings` list — so SARIF is computable from
the envelope file. `tests/test_cli_surface.py::ALLOWED_VERBS` closes the verb
set at nine, and `tests/test_skill_contract.py::READ_ONLY_INVOCATIONS` is
held equal to `SKILL.md`'s read-only table.

---

## Requirements

### Layering and contract

- R-GA-1: The action MUST be a composite action whose only responsibilities
  are to install the CLI, invoke it, project its machine-readable output into
  GitHub surfaces, upload the evidence, and relay the gate. It MUST NOT parse
  the CLI's text output, evaluate a rule, or decide severity policy:
  `fail-on` is passed to `validate --fail-on` unchanged, and the gate is
  `validate`'s exit code as interpreted by R-GA-5.
- R-GA-2: The action MUST run `validate` exactly once per invocation, with
  `--format json`, and MUST derive every other surface — SARIF, annotations,
  the step summary, the outputs — from that one envelope file through
  `planlint report`. It MUST NOT run `validate` a second time for a second
  format.
- R-GA-3: The action's inputs MUST be exactly `target`, `version`, `fail-on`,
  `python-version`, `upload-sarif`, `upload-artifact` and `artifact-name`. It
  MUST NOT expose a raw argument pass-through input.
- R-GA-4: The action's outputs MUST include `status`, `exit-code`, `errors`,
  `warnings`, `findings`, `blocking`, `specs-checked`, `rules-triggered`,
  `dialect`, `version`, `evidence-dir`, `json-path` and `sarif-path`. Within a
  major version an output MAY be added and MUST NOT be renamed, removed, or
  given a different meaning.
- R-GA-5: `status` MUST be exactly one of `pass`, `fail`, `error`,
  `indeterminate`, derived as follows: `fail` when the envelope's `blocking`
  is greater than zero; `indeterminate` when `blocking` is zero and
  `specs_checked` is zero; `error` when no envelope was produced (the
  validate step exited 2, or died before writing one); `pass` otherwise. Only
  `pass` MAY leave the job green.
- R-GA-6: `indeterminate` and `error` MUST fail the job with messages distinct
  from `fail`'s. The `indeterminate` message MUST state that zero specs were
  checked and name what to add; the `error` message MUST quote the CLI's
  stderr and say it is a precondition or usage error, not a spec failure.

### Evidence

- R-GA-7: Every file the action writes MUST live under a directory beneath
  `$RUNNER_TEMP`, never under `GITHUB_WORKSPACE`. The action MUST leave the
  target tree unchanged.
- R-GA-8: The evidence directory MUST contain `findings.json` (the envelope,
  byte-for-byte as `validate` printed it), `findings.sarif`,
  `dialect-card.json` (from `detect --format json`), `detect.txt` (the text
  report), and `run.json` (the validate exit code, the tool version, the
  action ref, and timestamps). `findings.json`, `findings.sarif` and
  `dialect-card.json` MUST be byte-identical across two runs on an unchanged
  tree and build; every non-deterministic field MUST live only in `run.json`.
- R-GA-9: The artifact upload MUST run whenever the validate step ran,
  including on `fail` and on `error` — conditioned on `upload-artifact` and
  `always()`, on nothing else.

### The `report` verb

- R-GA-10: A read-only verb `report` MUST exist with the signature
  `report --findings FILE --format {sarif,github-annotations,github-summary,github-outputs}`.
  It MUST print its projection to stdout only, MUST NOT create, modify or
  remove any file, MUST exit 0 on success, MUST exit 2 with a stderr message
  and empty stdout when `FILE` is unreadable, is not a JSON object, or carries
  a `schema_version` other than `rules.FINDINGS_SCHEMA_VERSION`, and MUST
  NOT exit 1 under any input.
- R-GA-11: `report --format sarif` over the envelope `validate --format json`
  printed MUST produce stdout byte-identical to `validate --format sarif` for
  the same tree and the same build.
- R-GA-12: `report --format github-annotations` MUST emit one workflow
  command per finding, in envelope order: `::error` for `ERROR`, `::warning`
  for `WARN`, `::notice` for `INFO`; `file=<path>` when `path` is non-null;
  `line=<n>` only when `line` is at least 1 (never for 0, never clamped);
  `title=<rule>`; and message text escaped by the workflow-command rules
  (`%` to `%25`, carriage return to `%0D`, newline to `%0A`, and in property
  values additionally `:` to `%3A` and `,` to `%2C`). It MUST stop at a
  module-level cap and, when the cap is reached, emit exactly one trailing
  `::notice::` naming how many findings were withheld and that the full
  envelope is in the evidence artifact.
- R-GA-13: `report --format github-outputs` MUST emit one `key=value` line per
  envelope-derivable output — `status`, `errors`, `warnings`, `findings`,
  `blocking`, `specs-checked`, `rules-triggered`, `version` — with no newline
  inside any value. `rules-triggered` MUST be the sorted, de-duplicated,
  comma-joined rule ids of the findings.
- R-GA-14: `report --format github-summary` MUST emit Markdown carrying the
  status, the counts, and a findings table (rule, severity, path, message)
  subject to the same cap and trailing note as R-GA-12, derived only from the
  envelope.
- R-GA-15: `openspec_graph/report.py` MUST be pure and stdlib-only, MUST
  perform no I/O, MUST import no other module of this package, and MUST be
  registered in `tests/test_decomposition.py::_NEW_MODULES`.
- R-GA-16: `report` MUST print one stderr warning, and MUST NOT refuse, when
  the envelope's `tool_version` differs from the running build's version;
  stdout MUST be unaffected.

### Install source and versioning

- R-GA-17: With `version` empty, which MUST be the default, the action MUST
  install the CLI from its own checkout (`$GITHUB_ACTION_PATH` resolved to
  the repository root), so that the `uses:` reference pins the CLI and the
  action together. With `version` set to a PEP 440 specifier, the action
  MUST install `planlint<specifier>` from the package index instead, on a
  line that names the distribution so the existing install-line guard covers
  it.
- R-GA-18: The template and the README MUST pin the action to an exact
  release tag, and MUST document full-SHA pinning; the template's tag
  version MUST equal `openspec_graph.__version__` and the skill's
  `planlint-min-version`. No floating major tag MAY be created or documented
  by this change.

### Security posture

- R-GA-19: The string `pull_request_target` MUST NOT appear in any file
  under `.github/`, `templates/` or `skills/`. The template MUST declare job
  `permissions` explicitly — `contents: read`, plus `security-events: write`
  only for the SARIF upload — and MUST check out with
  `persist-credentials: false`. The action MUST require no secret and MUST
  declare no token input.
- R-GA-20: The SARIF upload step MUST be skipped, not failed, when
  `upload-sarif` is not `true`, when no SARIF file exists, or when the event
  is a pull request whose head repository is not the workflow's repository
  (a fork, whose token is read-only). A policy result MUST NOT be turned into
  an `error` by the upload.

### Contract tests

- R-GA-21: CI MUST run the local action (`uses: ./.github/actions/planlint`)
  against committed fixture targets under `tests/fixtures/action/` and
  assert, per fixture: `passing/` gives `status=pass`, `exit-code=0`, a
  succeeding step; `failing/` gives `status=fail`, `exit-code=1`, a failing
  step, a non-empty `findings.sarif`, and at least one annotation command in
  the log; `empty-tree/` gives `status=indeterminate` and a failing step;
  `no-tree/` gives `status=error`, `exit-code=2`, a failing step, and an
  uploaded artifact; `nested/` proves a `target` other than `.` works. The
  job MUST run with `permissions: contents: read` and MUST use no secret.
- R-GA-22: The contract job MUST appear in `docs/hooks.md`'s CI table and
  MUST carry no coverage-floor literal and no tool-version pin, so the two
  existing guards for those properties cover it.

### Constraints

- C-GA-1: This change MUST NOT alter `validate --json`'s envelope,
  `rules.FINDINGS_SCHEMA_VERSION`, any of
  `tests/test_decomposition.py::_EXPECTED_HASHES`, or
  `tests/baseline_rules.json`.
- C-GA-2: This change MUST NOT add a rule, a rule family, or a field on the
  `Rule` dataclass. `tests/test_cli_surface.py::ALLOWED_VERBS` MUST grow by
  exactly `report` and by nothing else, and no authoring verb MAY be added.
- C-GA-3: This change MUST NOT add a runtime or test dependency, including a
  YAML parser. YAML artifacts are checked as text.
- C-GA-4: `templates/spec-gate.yml` and
  `skills/planlint-spec-governance/assets/spec-gate.yml` MUST remain
  byte-identical, and `SKILL.md`'s read-only table,
  `tests/test_skill_contract.py::READ_ONLY_INVOCATIONS`, `llms.txt`, and
  `references/exit-codes.md` MUST all list `report`.
- C-GA-5: `make pre-pr`'s composition MUST NOT change. The contract job is
  CI-side only — it needs a runner — and MUST NOT be folded into any Makefile
  target.

---

## Decisions

- **DEC-GA-001:** three layers with a hard boundary — consumer workflow,
  composite action, CLI — and the action stays deliberately boring. Every
  reviewer of this portfolio said the same thing about planlint's wedge: it
  is a linter that reads a stranger's clone, not an authoring or policy
  framework. A wrapper that starts deciding severity, discovering machinery,
  or reshaping findings in YAML is a second implementation of the tool, in a
  language with no tests. The action translates inputs to flags, flags to
  files, and files to GitHub surfaces. Nothing else.
- **DEC-GA-002:** the `validate --format json` envelope is the canonical
  evidence and every other surface is a projection of that file. Two
  alternatives were rejected. Running `validate` twice — once for JSON, once
  for SARIF — spends double the work asking the same question, and the two
  runs can in principle disagree (the existing action's own comment,
  `action.yml:63-67`, already made this argument for one format). Adding
  `--sarif-out`/`--json-out` flags to `validate` would put file-writing
  inside the verb whose whole guarantee is that it only reads
  (`DEC-SA-012`, `AC-SA-12`). Projecting from the envelope needs neither:
  `sarif.to_sarif` already takes the envelope's `findings` list
  (`DEC-SA-007` chose serialized dicts precisely so the projection would not
  depend on live objects), and R-GA-11 turns "same findings, no divergence"
  from a property two code paths must keep into a byte-identity a test
  asserts.
- **DEC-GA-003:** the projections are a CLI verb, not a script inside the
  action directory. The script would keep `ALLOWED_VERBS` at nine and avoid
  the SKILL parity work, and it was rejected for three reasons. First, code
  inside `.github/actions/` sits outside `[tool.coverage.run] source`, so
  the escaping rules of R-GA-12 — the part `jq`-in-YAML implementations get
  wrong — would be enforced by nothing. Second, a script shipped with the
  action and a CLI installed from the index can be different builds; the
  verb is always the build that produced the envelope. Third, `report`
  reuses `sarif.py` instead of vendoring a copy of it. The cost is one
  reviewed addition to a closed verb set; the surface stays read-only and
  gains no authoring capability, which is the property `AC-RP-3` actually
  protects.
- **DEC-GA-004:** `status` is derived from the envelope alone; `report`
  takes no `--exit-code` flag. `cmd_validate` computes `blocking` and
  returns `1 if blocking else 0` from the same list (`cli.py:449`,
  `cli.py:494`), so "exit 1" and "`blocking > 0`" are the same fact stated
  twice, and passing the exit code back in would be a second input that
  could disagree with the first. The one status the envelope cannot express
  is `error`: an exit-2 run prints nothing on stdout, so there is no
  envelope to read. That mapping — no envelope, `status=error` — is the
  action's, and it is the only status logic the YAML holds, because it is
  the CLI's documented exit-code contract and nothing more.
- **DEC-GA-005:** `indeterminate` fails the job by default, and there is no
  input to change that. The failure this forbids is the one the proposal's
  third evidence item reproduces: a repository that gates nothing gets a
  green check. `DEC-SA-011` already settled the shape of the argument for
  exit codes — the gate is the product claim, and a caller who wants a
  softer result says so visibly in the workflow — and the same escape holds
  here: `continue-on-error: true` on the step plus a branch on
  `outputs.status`. An `allow-indeterminate` input was considered and
  rejected as a knob whose only purpose is to make a false green available
  by configuration.
- **DEC-GA-006:** the CLI is installed from the action's own checkout by
  default; the `version` input is an explicit package-index override. This
  supersedes the action-internal half of `DEC-SA-009`'s install line, and
  only that half: the README, the skill preflight and the pre-commit hook
  still say `pip install planlint`, and `docs/distribution-plan.md` §3 is
  still what makes those true. The reasons are two. The action is
  unrunnable today because nothing is published, and this makes it runnable
  the moment the branch merges, at any ref. And with `uses:` pinning the
  same commit that supplies the CLI, the "two consumption modes must not
  drift" requirement becomes structural: the ref *is* the version, the
  release workflow already refuses a tag whose version disagrees with the
  package (`release.yml:78-85`), and there is nothing left to keep in step.
  The cost is a wheel build in pip's isolated environment on every run,
  which fetches `setuptools>=77` from the index — the same network
  dependency the index install has, plus a few seconds. An adopter who wants
  the index path sets `version`.
- **DEC-GA-007:** the input keeps the name `target`, not `path`. It mirrors
  the CLI's global `--target` flag, which the skill, the exit-code reference
  and every error message use; two names for one thing is the drift this
  repository pays for elsewhere. The existing caveat stands: SARIF paths are
  relative to the target and code scanning resolves them against the
  repository root, so a subdirectory target places annotations wrongly, and
  the input's description says so. Rewriting the `uri` with the
  subdirectory prefix inside `report --format sarif` was considered; it is
  deferred until an adopter has a monorepo, because it changes the byte
  identity R-GA-11 guarantees.
- **DEC-GA-008:** the SARIF upload stays inside the action, on by default,
  guarded and skippable. Moving it to the consumer workflow is cleaner on
  paper — every permission then lives in the file the adopter reads — and
  it costs the adopter two more steps and a `sarif-path` lookup on the way
  to their first annotation, which is the number this action exists to
  move. The compromise is the current default plus the fork guard R-GA-20
  requires and the documented opt-out: `upload-sarif: false` and the
  `sarif-path` output give an adopter full control, and the template shows
  which permission line to delete.
- **DEC-GA-009:** evidence lives under `$RUNNER_TEMP`, never in the
  workspace, and non-determinism is quarantined in `run.json`. The current
  action writes `planlint.sarif` into the consumer's checkout, which a later
  step can commit and which contradicts the CLI's own read-only guarantee
  one directory up. Timestamps and the action ref are useful for audit and
  poison byte-stability, so they get their own file; `findings.json`,
  `findings.sarif` and `dialect-card.json` stay exactly what the CLI printed
  and stay comparable across runs.
- **DEC-GA-010:** the annotation cap is a module-level constant in
  `report.py`, not an action input. Annotations flood a pull request past a
  few dozen and GitHub itself stops rendering them; the cap is a property of
  the surface, not a policy an adopter tunes. It also keeps a bare number
  out of the action YAML, which is this repository's posture for every
  other threshold (`tools/check_no_hardcoded_thresholds.py`). The trailing
  notice exists so a capped run can never be mistaken for a complete one.
- **DEC-GA-011:** no floating major tag and no Marketplace listing until
  1.0. `add-sarif-and-actions` declined both, and DEC-GA-006 removes the
  last reason to want a floating tag early: an exact tag now pins the CLI
  too. Moving a `v0` tag on every release would also need `contents: write`
  in the release workflow, whose permissions are currently `contents: read`
  plus `id-token: write` on the publish job only, and widening that for a
  convenience is the wrong trade. A Marketplace listing needs a root
  `action.yml`; that is a one-commit move when the contract is declared
  stable and not before.
- **DEC-GA-012:** the template pins `@v<X.Y.Z>` where `X.Y.Z` equals
  `openspec_graph.__version__`, and the existing pin-parity test is
  re-pointed at that ref rather than deleted. Between releases the template
  therefore names the *next* tag — exactly the semantics the current
  `>=0.2.0` pin already has, and the semantics the release workflow's
  tag-equals-version check makes true at tag time. Naming the last released
  tag instead would need a machine-readable record of it in the tree, which
  does not exist, and would make the template lag the verb it depends on.
- **DEC-GA-013:** the contract tests are a `ci.yml` job over committed
  fixtures, with `continue-on-error: true` on the `uses:` step in the
  *workflow*, and the composite action itself uses no `continue-on-error`.
  Living in `ci.yml` puts the job under the hooks-table and threshold guards
  automatically. Committed fixtures rather than fixtures generated by
  `planlint init`/`new` at test time keep the job's inputs reviewable and
  byte-stable. `act` is not the proof and is not required: its event and
  permission model differs from hosted Actions, and the point of the job is
  the hosted behaviour.
- **DEC-GA-014:** `report` is the one verb that never reads the target. It
  takes the envelope path explicitly and ignores the global `--target`, so
  it can project an artifact downloaded on a different machine — the
  cross-machine case `add-findings-json-envelope` made the envelope portable
  for. It still joins `READ_ONLY_INVOCATIONS`, because the digest test's
  guarantee is "leaves the tree byte-identical", and a verb that never
  touches the tree should be held to that like every other.
- **DEC-GA-015:** `pull_request_target` is forbidden by a test, not by
  review. The event hands a workflow write permissions and secrets while
  checking out attacker-controlled content, and the failure mode is silent:
  a template that used it would look identical to one that did not. A
  text-level guard over the three directories adopters copy from costs one
  test and closes the door.

---

## Acceptance Criteria

- [ ] **AC-GA-1:** For a fixture with findings in more than one spec file
  and for a clean fixture, `report --format sarif` over the envelope
  `validate --format json` printed produces stdout byte-identical to
  `validate --format sarif` on the same tree — asserted on a non-empty
  results array first, so the equality cannot hold vacuously. (R-GA-11)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 3) · stage: `make test`

- [ ] **AC-GA-2 (non-success):** `report` exits 2, prints one line to
  stderr, and prints nothing to stdout for each of: a missing file, a file
  that is not JSON, a JSON array, and an envelope whose `schema_version` is
  not the current one. No input makes it exit 1. (R-GA-10)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 3) · stage: `make test`

- [ ] **AC-GA-3:** `report --format github-outputs` over a failing fixture's
  envelope yields `status=fail` with `errors`, `warnings`, `findings` and
  `blocking` equal to the envelope's own counts and `rules-triggered` sorted
  and de-duplicated; over a clean fixture it yields `status=pass`; every
  line is `key=value`, the key set is exactly the documented one, and no
  value contains a newline. (R-GA-5, R-GA-13)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 2) · stage: `make test`

- [ ] **AC-GA-4 (non-success):** The envelope a real `validate --format
  json` prints for an `openspec/changes/` directory with no packages —
  `specs_checked` zero, `blocking` zero — yields `status=indeterminate`,
  never `pass`. (R-GA-5, DEC-GA-005)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 2) · stage: `make test`

- [ ] **AC-GA-5:** `report --format github-annotations` emits one command
  per finding in envelope order, maps `ERROR`/`WARN`/`INFO` to
  `::error`/`::warning`/`::notice`, carries `file=` for a finding with a
  path and omits it for a pathless one, omits `line=` when `line` is zero
  and carries it for a real line, sets `title=` to the rule id, and escapes
  `%`, carriage return, newline, `:` and `,` as the workflow-command rules
  require — checked on a constructed finding whose message contains every
  one of those characters. (R-GA-12)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 2) · stage: `make test`

- [ ] **AC-GA-6 (non-success):** With more findings than the cap, the
  annotation output holds exactly the cap's count of finding commands plus
  one trailing `::notice::` naming the withheld count; with fewer, no notice
  is emitted. Constructed input, so the criterion cannot pass on an empty
  set. (R-GA-12, DEC-GA-010)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 2) · stage: `make test`

- [ ] **AC-GA-7:** `report --format github-summary` is a pure function of
  the envelope: two calls over one envelope are byte-identical, the output
  names the status and the counts, and it is capped with the same trailing
  note as the annotations. (R-GA-14)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 2) · stage: `make test`

- [ ] **AC-GA-8:** `openspec_graph/report.py` imports only the standard
  library, imports no module of this package, and is listed in
  `_NEW_MODULES`, so both properties are checked mechanically. (R-GA-15,
  C-GA-3)
  _Verified by:_ `pytest -k "test_new_modules_stdlib_only or test_import_boundary_discipline"` · stage: `make test`

- [ ] **AC-GA-9 (non-success):** `report` creates, modifies and removes no
  file in the target tree. Enforced by adding a `report` invocation to
  `READ_ONLY_INVOCATIONS`, whose whole-tree digest comparison then covers it
  and whose exit-code guard keeps the assertion from passing because the
  verb refused to run; the SKILL.md parity test then requires the read-only
  table to list `report`. (R-GA-10, C-GA-4, DEC-GA-014)
  _Verified by:_ `pytest -k "test_read_only_verbs_leave_tree_byte_identical or test_read_only_invocations_cover_every_verb_the_skill_calls_read_only"` · stage: `make test`

- [ ] **AC-GA-10:** The verb surface is exactly the previous nine verbs
  plus `report`, and no authoring verb was added. (C-GA-2)
  _Verified by:_ `pytest -k "test_cli_verbs_are_exactly_the_allow_list or test_cli_rejects_authoring_verbs"` · stage: `make test`

- [ ] **AC-GA-11 (non-success):** The golden hashes for `validate`, `graph`
  and `rules` are unchanged and the rule set matches the committed baseline:
  a new verb and a new module changed no existing output. (C-GA-1, C-GA-2)
  _Verified by:_ `pytest -k "test_output_byte_identical or test_rule_set_matches_baseline"` · stage: `make test`

- [ ] **AC-GA-12:** `.github/actions/planlint/action.yml` declares exactly
  the seven inputs and at least the thirteen outputs of the contract;
  contains one `validate --format json` invocation and no
  `validate --format sarif`; invokes `report` for the SARIF, annotation,
  summary and outputs surfaces; roots its evidence under `RUNNER_TEMP`;
  uploads the artifact under `always()`; guards the SARIF upload on the
  fork condition; installs from `GITHUB_ACTION_PATH` by default and from
  the index on a line naming the distribution when `version` is set;
  carries three distinct gate messages, one each for `fail`, `error` and
  `indeterminate`; and is discovered by the adopter corpus rather than
  exempt from it. Text-level, no YAML parser. (R-GA-1, R-GA-2, R-GA-3,
  R-GA-4, R-GA-6, R-GA-7, R-GA-8, R-GA-9, R-GA-17, R-GA-20)
  _Verified by:_ `pytest -k "test_the_composite_action_declares_the_expected_steps or test_the_adopter_corpus_includes_the_composite_action or test_install_lines_spell_this_project_the_way_it_is_published"` · stage: `make test`

- [ ] **AC-GA-13 (non-success):** The string `pull_request_target` appears
  in no file under `.github/`, `templates/` or `skills/`, and the action
  declares no input whose name contains `token`. (R-GA-19, DEC-GA-015)
  _Verified by:_ `tests/test_sarif.py` (to be written in Milestone 5) · stage: `make test`

- [ ] **AC-GA-14:** `templates/spec-gate.yml` and the skill asset are
  byte-identical; the template declares job `permissions` with
  `contents: read`, checks out with `persist-credentials: false`, and pins
  `uses: ianshank/planlint/.github/actions/planlint@v<X.Y.Z>` where `X.Y.Z`
  equals both `openspec_graph.__version__` and the skill's
  `planlint-min-version`. (R-GA-18, R-GA-19, C-GA-4, DEC-GA-012)
  _Verified by:_ `pytest -k "test_skill_asset_matches_template or test_ci_template_pins_the_floor_the_skill_enforces"` · stage: `make test`

- [ ] **AC-GA-15:** `.github/workflows/ci.yml` defines an `action-contract`
  job that checks out this repository, uses `./.github/actions/planlint`
  once per fixture directory under `tests/fixtures/action/`, runs under
  `permissions: contents: read`, reads no secret, and asserts the status
  each fixture is labelled with; the job is listed in `docs/hooks.md`'s CI
  table and carries no threshold literal or tool pin; the Makefile does not
  reference it. (R-GA-21, R-GA-22, C-GA-5)
  _Verified by:_ `pytest -k "test_hooks_ci_table_lists_every_ci_job or test_no_hardcoded_passes_on_clean_repo"` plus a structural job test in `tests/test_ci_hardening.py` (to be written in Milestone 7) · stage: `make test`

- [ ] **AC-GA-16:** Each fixture under `tests/fixtures/action/` produces,
  under the installed CLI, the result its name promises: `passing/` exits 0
  with at least one spec checked, `failing/` exits 1 with `blocking` above
  zero, `empty-tree/` exits 0 with `specs_checked` zero, `no-tree/` exits 2
  printing the no-spec-tree message, and `nested/` passes only when the
  target is its subdirectory. (R-GA-21)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 4) · stage: `make test`

- [ ] **AC-GA-17:** Two consecutive runs over an unchanged fixture produce
  byte-identical `validate --format json`, `validate --format sarif` and
  `detect --format json` output, and byte-identical `report` projections of
  the same envelope. (R-GA-8)
  _Verified by:_ `pytest -k "test_validate_json_is_deterministic or test_sarif_output_is_byte_stable_across_runs or test_detect_format_json_is_byte_identical_across_runs"` plus a `report` determinism test in `tests/test_report.py` (to be written in Milestone 2) · stage: `make test`

- [ ] **AC-GA-18:** When the envelope's `tool_version` differs from the
  running build's, `report` prints one warning to stderr and its stdout is
  byte-identical to the matching-version run; it never exits 2 for the
  mismatch alone. (R-GA-16)
  _Verified by:_ `tests/test_report.py` (to be written in Milestone 3) · stage: `make test`

- [ ] **AC-GA-19:** `README.md`, `SKILL.md`, `references/exit-codes.md`,
  `llms.txt`, `docs/hooks.md`, `docs/architecture/c4.md` and `CHANGELOG.md`
  describe `report`, the action's inputs, outputs and statuses, the
  evidence artifact, the exact-ref pinning rule, and the security posture;
  the docs gate passes and every required document is still linked from the
  README. (C-GA-4)
  _Verified by:_ `pytest -k test_docs_check_passes` and manual review · stage: `make docs-check`

- [ ] **AC-GA-20:** The hosted `action-contract` job is green on the pull
  request that lands this change, with each fixture's assertion step
  passing — including that the `empty-tree/` and `no-tree/` legs fail with
  their own messages rather than `fail`'s — the first execution of the
  action anywhere, and the evidence that a checkout of this repository at
  that commit is enough to run it. (R-GA-6, R-GA-21)
  _Verified by:_ the `action-contract` job's own assertion steps on the pull request · stage: `make ci` on the same commit must also be green

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-GA-1..18 |
| Core | `make ci` | AC-GA-1..18, plus lint and this repo's own `planlint validate` over this package |
| Docs | `make docs-check` | AC-GA-19 |
| Hosted | `action-contract` job in `.github/workflows/ci.yml` | AC-GA-20 — each fixture's status assertion, under read-only permissions and no secrets |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, no-hardcoded-thresholds |
