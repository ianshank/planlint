# Milestones

> Nothing in this package is implemented yet. Every acceptance criterion
> starts unchecked, and every `_Verified by:` that names a test file rather
> than a `pytest -k` selector is naming a test that does not exist yet —
> deliberately, because `tests/test_spec_test_citations.py` fails the suite
> on a selector that resolves to nothing. Writing those tests is the gating
> work of Milestones 2 through 7, not a follow-up, and the citations are
> upgraded to `pytest -k` selectors as each test lands. Flip a criterion to
> `[x]` only when it is implemented *and* verified — never retroactively.

## Milestone 0 — Grounding pass (done in the drafting of this package)

- Facts established against the tree and the live index, not inferred, each
  cited in `proposal.md`'s Evidence: the install line resolves to nothing
  because `planlint` is not on PyPI and `v0.1.0` is the only tag; the action
  has no `outputs:` block and writes `planlint.sarif` into the consumer's
  checkout; a zero-spec run prints `PASS` and exits 0 (reproduced on an
  empty `openspec/changes/`); the SARIF upload has no fork guard;
  `sarif.to_sarif` takes the envelope's own `findings` list; the verb set is
  closed at nine and held equal to `SKILL.md`'s tables.
- Two assumptions from the external design brief did not survive contact and
  are corrected in the spec: helper subcommands that *write*
  `$GITHUB_OUTPUT`/`$GITHUB_STEP_SUMMARY` through flags contradict the
  stdout-only stance (`DEC-SA-012`), so `report` prints and the action
  redirects; and a `--exit-code` flag on the summary helper is redundant,
  because `blocking > 0` and exit 1 are one fact (`cli.py:449`, `cli.py:494`)
  — `status` is derived from the envelope alone (`DEC-GA-004`).
- Every non-obvious call recorded as `DEC-GA-001` through `DEC-GA-015`.
- **Gate:** `make validate`

## Milestone 1 — Change package

- `openspec/changes/add-github-action-contract/proposal.md`, this
  `tasks.md`, and `specs/github-action-contract/spec.md`, spec-first,
  before any implementation. Hand the draft to `spec-adversary` before
  Milestone 2 starts; fold its findings back into the spec, not into code.
- **Gate:** `make validate`

## Milestone 2 — `report.py` pure module

- New `openspec_graph/report.py` in the `sarif.py` shape: stdlib-only, no
  I/O, zero intra-package imports, taking the envelope as a plain dict
  (`R-GA-15`). Public surface: `status_of(envelope) -> str`,
  `to_annotations(envelope, *, limit=ANNOTATION_LIMIT) -> list[str]`,
  `to_step_summary(envelope) -> str`, `to_outputs(envelope) -> dict[str, str]`,
  plus the module constants `ANNOTATION_LIMIT` and `STATUSES`.
- Status derivation exactly as `R-GA-5`, from `blocking` and
  `specs_checked` only (`DEC-GA-004`).
- Workflow-command escaping as `R-GA-12`: a single `_escape_data` and a
  single `_escape_property`, each a module-level table, never inline
  replacements at a call site. `line=` only for `line >= 1`, mirroring
  `DEC-SA-003`'s reason.
- The cap is `ANNOTATION_LIMIT = 10` and its trailing `::notice::`
  (`DEC-GA-010`); the summary's findings table is capped identically with
  the same note, which is the guaranteed withheld-count surface. Table
  cells escape `|` (`R-GA-14`). `to_outputs` derives `errors` / `warnings`
  / `findings` counts as `R-GA-13`; it does not read those keys off the
  envelope.
- `tests/test_decomposition.py::_NEW_MODULES` gains `"report"`.
- New `tests/test_report.py`, unit half: the four statuses on constructed
  envelopes; the zero-spec envelope from a real `validate --format json`
  run (`AC-GA-4`); the escaping fixture whose message carries `%`, `\r`,
  `\n`, `:` and `,` (`AC-GA-5`); the cap boundary — exactly the cap plus one
  notice, and no notice below it (`AC-GA-6`); outputs key set and no
  embedded newline (`AC-GA-3`); summary determinism across two calls
  (`AC-GA-7`, `AC-GA-17`).
- Upgrade each `_Verified by:` in `AC-GA-3..7` and the `report` half of
  `AC-GA-17` to the real `pytest -k` selector as the test lands.
- **Gate:** `make test`

## Milestone 3 — CLI wiring and the guards that pin the surface

- `openspec_graph/cli.py`: `cmd_report` and the `report` subparser
  (`--findings FILE` required, `--format` with the four choices). Reads the
  file with `utf-8-sig` like `_load_card` does (extract a shared
  `_load_json_object` if that keeps the two readers identical); exit 2 with
  a stderr line and empty stdout on an unreadable file, a non-object, a
  foreign `schema_version`, or a JSON object missing envelope keys
  (`findings` list, integer `blocking`, integer `specs_checked`) — including
  a dialect card (`R-GA-10`); one stderr warning on a `tool_version`
  mismatch, never a refusal (`R-GA-16`). `--format sarif` calls
  `print(json.dumps(sarif.to_sarif(envelope["findings"], rules.rule_table(),
  tool_version=envelope["tool_version"]), indent=2))` — the producer's
  version and the same `indent=2` `print` as `cmd_validate`, so the driver
  block matches `validate --format sarif` byte-for-byte (`R-GA-11`). Ignores
  the global `--target` (`DEC-GA-014`). Update the module docstring's verb
  list.
- `tests/test_cli_surface.py::ALLOWED_VERBS` gains `"report"` and nothing
  else (`C-GA-2`).
- `tests/test_skill_contract.py::READ_ONLY_INVOCATIONS` gains
  `("report", "--findings", <placeholder>, "--format", "github-outputs")`,
  with the placeholder substituted at run time by an envelope written
  *outside* the target tree, the way `_BASELINE_PLACEHOLDER` already works
  for `delta`. Confirm the invocation exits 0 against the populated fixture
  — the test's own guard rejects a verb that exits 2.
- `SKILL.md`: the read-only verb table gains a `report` row (the parity
  test requires it); the structured-output paragraph names it.
  `references/exit-codes.md`: a `report` section quoting its exit-2
  messages. `llms.txt`: `report` in the read-only list.
- `tests/test_report.py`, end-to-end half: SARIF byte-identity on a
  multi-file failing fixture and on a clean one (`AC-GA-1`); the exit-2
  inputs of AC-GA-2 (missing file, non-JSON, JSON array, foreign
  `schema_version`, dialect card) and the no-exit-1 property; the
  version-mismatch warning (`AC-GA-18`).
- Confirm empirically that `_EXPECTED_HASHES` and `tests/baseline_rules.json`
  are untouched (`AC-GA-11`).
- Upgrade the `_Verified by:` lines of `AC-GA-1`, `AC-GA-2`, `AC-GA-18`.
- **Gate:** `make ci`

## Milestone 4 — Fixture targets

- New `tests/fixtures/action/` with five committed targets, each a minimal
  repository shape (`Makefile`, `pyproject.toml` where a floor is needed,
  and a spec tree): `passing/` (one harness change package that validates
  clean), `failing/` (two packages, findings in both, so `AC-GA-1`'s
  multi-file case has a home), `empty-tree/` (`openspec/changes/` with no
  package — the vacuous-pass shape), `no-tree/` (no `openspec/` and no
  `specs/`), `nested/` (the valid target one directory down, so a
  repository-root run and a subdirectory run differ). A `README.md` in the
  directory states each fixture's expected `status`, the way
  `tests/corpus/targets/README.md` labels its shapes.
- `tests/test_report.py`: one parametrized test per fixture asserting the
  exit code and the envelope facts its label promises (`AC-GA-16`).
- `.gitattributes`: pin the fixture tree `-text` if any specimen would be
  rewritten by a Windows checkout, as the detect corpus already does.
- Upgrade `AC-GA-16`'s `_Verified by:`.
- **Gate:** `make test`

## Milestone 5 — The action

- Rewrite `.github/actions/planlint/action.yml` to the contract in
  `R-GA-1..9`, `R-GA-17`, `R-GA-20`. Step order: paths (evidence dir under
  `RUNNER_TEMP`, outputs for `evidence-dir`/`json-path`/`sarif-path`);
  setup-python; install (from `$GITHUB_ACTION_PATH/../../..` when `version`
  is empty, else `pip install "planlint${INPUT_VERSION}"` — inputs passed
  through `env:`, never interpolated into `run:`); `detect --target
  "$INPUT_TARGET"` to `detect.txt` and `detect --target "$INPUT_TARGET"
  --format json` to `dialect-card.json`; `validate --target "$INPUT_TARGET"
  --format json --fail-on "$INPUT_FAIL_ON"` to `findings.json` under
  `set +e`, capturing the exit code and writing `run.json`; `report --format
  sarif` to `findings.sarif` when `findings.json` exists as a JSON object
  (including an empty `findings` list); `report --format
  github-annotations` to stdout; `report --format github-summary` appended
  to `$GITHUB_STEP_SUMMARY`; `report --format github-outputs` appended to
  `$GITHUB_OUTPUT`, with the action itself emitting `status=error` and the
  exit code when no envelope exists (`DEC-GA-004`); `dialect` read from the
  card; SARIF upload skipped unless `upload-sarif` is `true`, a
  path-based `[ -s "$SARIF_PATH" ]` (never `hashFiles`) says the file
  exists, and (`github.event_name != 'pull_request'` or
  `github.event.pull_request.head.repo.full_name == github.repository`)
  (`R-GA-20`, `DEC-GA-016`); artifact upload under `always()` and
  `upload-artifact`; the gate last, branching on `status` with the three
  distinct messages of `R-GA-6`. Composite `outputs.*.value` MUST map every
  declared output to a step that writes `$GITHUB_OUTPUT`.
- Keep the `target` input and its SARIF caveat text (`DEC-GA-007`).
- `tests/test_sarif.py::test_the_composite_action_declares_the_expected_steps`
  re-pinned to the new contract (`AC-GA-12`): exact input names, the
  thirteen output names, one `validate --format json` and no
  `validate --format sarif`, `report` invocations, `RUNNER_TEMP`,
  `always()`, the R-GA-20 fork-or-push condition, a path-based SARIF
  existence check and no `hashFiles` of the SARIF, `GITHUB_ACTION_PATH`,
  and the `pip install "planlint` override line. New
  `test_no_workflow_or_template_uses_pull_request_target` and
  `test_the_action_declares_no_token_input` (`AC-GA-13`).
- Upgrade `AC-GA-13`'s `_Verified by:`.
- **Gate:** `make ci`

## Milestone 6 — Consumer template and skill asset

- `templates/spec-gate.yml` rewritten as the consumer workflow: triggers
  `pull_request` (with the existing `openspec/**`/`specs/**`/`Makefile`/
  `pyproject.toml` path filters) and `push` to the default branch; job
  `permissions: contents: read` and `security-events: write`, the second
  annotated with the one line to delete when code scanning is off, plus
  `actions: read` annotated as required only on a private repository;
  `actions/checkout` with `persist-credentials: false`; the action pinned
  to `@v<__version__>` with a comment showing the full-SHA form.
- Copy byte-for-byte over `skills/planlint-spec-governance/assets/spec-gate.yml`
  (`test_skill_asset_matches_template`).
- `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`:
  the pin is now read from the `uses:` ref (`@v([0-9.]+)`) and compared with
  the skill's `planlint-min-version`; add the third leg — equality with
  `openspec_graph.__version__` (`DEC-GA-012`). Keep the assertion that the
  pin exists at all.
- `README.md` "Wiring it into CI": the action first, with the pinning rule
  and the permissions block; the raw-`pip` workflow second, with the note
  that it needs the published distribution.
- **Gate:** `make test`

## Milestone 7 — The hosted contract job

- `.github/workflows/ci.yml`: new `action-contract` job, `ubuntu-latest`,
  `permissions: contents: read`, matrix over the five fixture names.
  Steps: checkout; `uses: ./.github/actions/planlint` with `id: planlint`,
  `continue-on-error: true`, `target: tests/fixtures/action/<fixture>`
  (`nested/` points at its subdirectory), `upload-sarif: false`,
  `artifact-name: planlint-evidence-<fixture>`; an assertion step in bash
  comparing `steps.planlint.outcome` and every `steps.planlint.outputs.*`
  against the fixture's label, and checking the evidence files exist.
- `docs/hooks.md`: CI table row for `action-contract`
  (`test_hooks_ci_table_lists_every_ci_job` fails until it is there).
- `tests/test_ci_hardening.py`: `test_ci_workflow_has_an_action_contract_job`
  — the job exists, uses the local action, names every fixture directory
  that exists on disk (so a sixth fixture cannot be added without a leg),
  declares `contents: read`, and is referenced by no Makefile target
  (`AC-GA-15`, `C-GA-5`).
- Push, and read the job on the pull request. This is the first time the
  action has ever executed; expect at least one round of YAML-level fixes
  the local text tests cannot see, and make each one in the action or the
  fixtures, never by loosening an assertion (`AC-GA-20`).
- Upgrade `AC-GA-15`'s `_Verified by:`.
- **Gate:** `make ci` locally; the `action-contract` job green on the PR.

## Milestone 8 — Docs, versioning rule, roadmap, close-out

- `docs/architecture/c4.md`: component row for `report.py` and the
  container-diagram edge from `cli.py`. `CHANGELOG.md`: `### Added` entry
  under `[Unreleased]` naming the verb, the contract, and the supersession
  of the action-internal install line. `docs/differentiation-roadmap.md`:
  CP-6's status note amended with what this change corrected (the action
  never ran; the vacuous pass; the fork case). `docs/next-steps.md`: the
  deferred items with their reopen triggers — pull-request comments via a
  `workflow_run` reporter, `extra-args`, the floating major tag and
  Marketplace listing at 1.0, the SARIF subdirectory prefix, an
  `evidence-sha256` output, and widening `indeterminate` to "no machinery
  detected".
- Version sequencing: if `v0.2.0` has been tagged before this merges, set
  `openspec_graph.__version__` to `0.3.0`, run `make skill-manifests`,
  update `SKILL.md`'s `metadata.version` and `planlint-min-version`, and the
  template pin follows through `DEC-GA-012`'s test. If not, nothing moves
  and `0.2.0` is the release that carries `report`.
- Dogfood: run the action's exact command sequence by hand against this
  repository's own tree into a temp directory and confirm the evidence set
  of `R-GA-8`, then `planlint --target . validate --fail-on WARN` to show
  the graph-diff job cannot regress on this package.
- Flip each acceptance criterion to `[x]` only as it is verified;
  `AC-GA-20` flips only after the hosted job is observed green.
- **Gate:** `make pre-pr`

## Milestone 9 — Outside this repository (owner-executed, not a code change)

- `docs/distribution-plan.md` §3 in full: pending trusted publisher on PyPI,
  the `pypi` environment, the tag, the three release jobs, the fresh-venv
  install. Until this is done the action works from any ref of this
  repository (Milestone 5) but `pip install planlint`, the skill preflight
  and the pre-commit hook still do not resolve — the plan's own exit
  criterion.
- The measure that matters after release, in place of any traffic proxy:
  clones, unique visitors, package downloads, and — the only one that
  proves the action is workable — a repository this account does not own
  running it in CI and acting on a finding. The differentiation roadmap's
  next planlint decision waits on that signal, not on more rules.
- **Gate:** every install line this repository prints resolves in a clean
  virtual environment; one external repository shows a green or red
  `planlint` check produced by the action.
