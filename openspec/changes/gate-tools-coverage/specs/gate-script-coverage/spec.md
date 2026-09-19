# Spec: Gate Script Coverage

> **Change:** `gate-tools-coverage`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The scripts under `tools/` are the gate machinery: `make pre-pr` and every CI
job run them, and their verdicts are what a green build means here. Seven of
them were unexamined in coverage terms. Four reported zero coverage while
being thoroughly tested, because they were exercised only through
`subprocess.run` and a subprocess's execution is invisible to coverage. Three
more had never been shown to *fire*: the uncovered region in each was its
`main()`, which is the decision itself, so "this gate fails when it should"
was assumed rather than demonstrated. A gate that cannot be shown to fail is
worse than no gate, because it reports PASS on exactly the thing it was added
to catch.

Underneath that sat a defect of a different kind. Two tests spawn a nested
`pytest --cov` to prove pytest-cov's own `--cov-fail-under` gate fires, and
both handed the child `{**os.environ, ...}`. The child therefore inherited
`COVERAGE_FILE` and wrote statement-only data — it has no `--cov-branch` —
into this run's data file. With `[tool.coverage.run] parallel = true` the
outer run combines every sibling data file at teardown, and `combine` raises
`DataError: Can't combine branch coverage data with statement data` from
inside pytest's own teardown hook. That is INTERNALERROR and exit 3: the
entire suite lost, with no test marked red, which is why an ordinary test of
those two functions could never have caught it.

**Evidence:** nothing in this repository sets `COVERAGE_FILE` — not the
`Makefile`, not `.github/workflows/ci.yml`, not `pyproject.toml` — so the
trap is entirely ambient and springs only for a caller whose environment
happens to name a per-leg coverage data file, which is the standard way to
keep a build matrix's coverage separate. For the coverage blind spot,
`tools/check_coverage_floor.py`'s `main()` reads `Path("pyproject.toml")`
from the process cwd, so its tests must run it from a throwaway directory;
coverage resolves a relative `source` entry against that same cwd, so handing
the child the coverage config would have pointed `source = ["tools"]` at a
`tools` directory inside the fixture that does not exist. The four scripts
went from zero to 89%, 82%, 95% and 89% on in-process invocation alone, with
no new assertions about their behaviour. `tools/check_docs.py`,
`tools/check_secrets.py` and `tools/render_plugin_manifests.py` measured 29%,
52% and 57% before their `main()` was tested, and 95%, 92% and 97% after.
Testability had to come first for two of them: `check_docs.check` and
`check_secrets.fallback_scan` bound `REPO_ROOT` into their signature
defaults, which Python evaluates at definition time, so a caller reassigning
the module constant changed nothing and the gate logic could only ever run
against the directory the module was imported from.

---

## Requirements

- R-GTC-1: A test that spawns a child running its **own** coverage session
  MUST NOT hand that child this run's coverage identity. `tests/support.py`
  MUST expose `env_without_coverage(**overrides)`, which removes every name
  in `COVERAGE_ENV_VARS` — the `COVERAGE_*` and `COV_CORE_*` families — and
  applies the overrides on top; every such test MUST build its child
  environment through it rather than through `{**os.environ, ...}`.
- R-GTC-2: An ambient `COVERAGE_FILE` MUST NOT be able to end the run. The
  suite MUST reach a per-test verdict under it: no INTERNALERROR, and never
  pytest's internal-error exit code from a `combine` raised in a teardown
  hook.
- C-GTC-1: `env_without_coverage` MUST be a denylist, not an allowlist. Every
  environment variable unrelated to coverage MUST survive into the child, and
  the family MUST be stripped whole rather than probed — which names are
  present depends on the pytest-cov version and on whether the outer run used
  `--cov` at all, and removing an unset name is a no-op.
- R-GTC-3: A `tools/` gate script's decision logic MUST be asserted by
  calling its `main(argv)` in-process, through a single shared
  `tests/support.run_tool_main()` helper, so that coverage measures it. No
  gate script's behaviour may be asserted only through a subprocess.
- R-GTC-4: `run_tool_main` MUST make the argv convention explicit per call
  rather than assuming one. `tools/` is split: eight scripts index `argv[1]`
  and are invoked `main(sys.argv)`, while the two argparse ones
  (`render_plugin_manifests`, `render_rule_catalog`) are invoked
  `main(sys.argv[1:])`. The mismatch is not quiet in either direction —
  argparse rejects the stray filename as an unrecognized argument, and a
  hand-rolled script silently drops the first real argument.
- R-GTC-5: The `python tools/<script>.py` invocation contract — the one the
  `Makefile` and the workflows actually use — MUST stay covered by exactly
  one parametrized subprocess test naming every script in `tools/`, so a new
  gate script is covered by adding one line. That test MUST assert on
  load-failure markers in the child's stderr, not on exit code alone: a
  failed import prints `Traceback (most recent call last)` while a
  `SyntaxError` is reported in a different format with no such line, and both
  exit 1 — which is also a documented code here meaning the gate found a
  violation.
- C-GTC-2: This spec MUST NOT claim that the invocation-contract test covers
  the `sys.path.insert` bootstrap line in the nine scripts that import
  `_common`. Deleting that line does not fail the test. Python already places
  a script's own directory on `sys.path[0]`, so the line is redundant for
  script execution and load-bearing only for `load_tool`'s by-path import.
  The limit is recorded, not acted on.
- R-GTC-6: A gate script whose decision depends on a repository root MUST
  resolve that root at call time, through a `None` sentinel. It MUST NOT bind
  `REPO_ROOT` into a signature default, which Python evaluates at definition
  time and which makes the function unrunnable against a fixture tree.
- C-GTC-3: The sentinel change MUST be backwards compatible. A caller passing
  no root MUST behave exactly as it did before, and this repository's own
  `docs-check` and `security` gates MUST be unaffected.
- R-GTC-7: `check_docs`, `check_secrets` and `render_plugin_manifests` MUST
  each be shown to FIRE — `main()` returning non-zero against a planted
  defect — and to pass against a clean tree. Demonstrating only the passing
  side leaves the failing side, which is the whole reason the gate exists,
  asserted by nothing.
- R-GTC-8: The `tools/` tree MUST carry its own line and branch coverage
  floors, declared in `pyproject.toml`'s `[tool.specgraph]` table as
  `tools_line_fail_under` and `tools_branch_fail_under` and read at run time.
  No floor literal may appear in the `Makefile` or in any workflow file
  (rule G003).
- R-GTC-9: Those floors MUST be enforced **scoped**, never combined into the
  package's number. `make coverage-tools` MUST be its own coverage run with
  pytest-cov's `--cov-fail-under` disabled, gated instead by the two existing
  checkers under `--scope tools`, because pytest-cov's own floor applies to
  the total of everything measured.
- C-GTC-4: `make test` MUST keep measuring the package alone. No `--cov=tools`
  may be added to it, and its reported numbers MUST be unchanged by this
  spec.
- R-GTC-10: A `--scope` that matches no measured file MUST exit 2. A prefix
  typo, a renamed directory, or a run that forgot `--cov=tools` all yield
  zero measured statements, and zero of zero is not full coverage — it is a
  gate pointed at nothing. Scope matching MUST normalize path separators, so
  a coverage report written on Windows still matches.
- R-GTC-11: A scoped floor absent from `[tool.specgraph]` MUST exit 2, and
  `--scope` given without a value MUST be a usage error rather than an empty
  scope whose prefix matches every file in the report. A missing floor is a
  misconfiguration, never a skip — the same posture the unscoped floors
  already take.
- R-GTC-12: `coverage-tools` MUST run in continuous integration as its own
  single-interpreter job rather than as a step in the version matrix — the
  scripts are stdlib-only and version-independent — and MUST carry its row in
  `docs/hooks.md`'s CI hooks table. Locally it MUST be part of `make pre-pr`
  and MUST NOT be folded into `make ci`, which stays the fast core gate.
- C-GTC-5: This spec MUST NOT claim full coverage of the converted scripts.
  The residual uncovered lines in the four moved to in-process invocation are
  their `if __name__ == "__main__":` guards, which in-process invocation
  structurally cannot reach.

---

## Decisions

- **DEC-GTC-001:** the coverage environment is stripped whole rather than
  probed for the variable that actually caused the crash. Only `COVERAGE_FILE`
  was implicated, but `COVERAGE_PROCESS_START` and the `COV_CORE_*` family are
  three more routes by which a child can be handed this run's coverage
  identity, and which of them exist depends on the pytest-cov version and on
  whether the outer run was invoked with `--cov` at all. A probe would have to
  be re-audited on every pytest-cov upgrade; removing an unset name costs
  nothing. The property worth stating is "a nested run must not share this
  repo's coverage identity by any route," and a family-wide strip states it
  directly.
- **DEC-GTC-002:** the crash gets its own regression test
  (`test_suite_survives_an_ambient_coverage_file`) that runs a nested pytest
  under the trap conditions, rather than a unit test of the helper alone. The
  failure mode is not a red test but a lost run, so the only assertion that
  proves it closed is "a real verdict came back." The nested run pins
  `--cov-fail-under` to zero for itself, because it measures `tools` while
  running one test that touches none of it; the real floor would fail it for
  reasons unrelated to the crash, and its exit code would stop meaning
  anything.
- **DEC-GTC-003:** the gate scripts are converted to in-process `main(argv)`
  calls rather than given a working subprocess-coverage configuration. The
  configuration route is not merely more work — it does not reach. The two
  coverage gates read `Path("pyproject.toml")` from the cwd, so their tests
  must run them from a throwaway directory, and coverage resolves a relative
  `source` entry against that same cwd. `source = ["tools"]` would point at a
  `tools` directory inside the fixture. Making it reach would mean rewriting
  the gates to take their config path as an argument, which changes the thing
  under test to make it measurable.
- **DEC-GTC-004:** `pass_argv0` is a parameter, not an inference from the
  script name or a probe of `main`'s signature. Both alternatives encode the
  split as a rule that a future script can silently violate, and the failure
  is asymmetric: argparse errors loudly on the stray filename, while a
  hand-rolled script quietly drops its first real argument and the test still
  passes, asserting the wrong invocation. An explicit flag at the call site
  makes the convention visible where the reader is.
- **DEC-GTC-005:** the script-execution contract is asserted once for the
  whole directory, parametrized over the eleven scripts, rather than once per
  script alongside each script's own tests. In-process testing cannot see
  whether a file still *runs* as a script — an import that only resolves
  because pytest put the repo root on `sys.path`, a bootstrap line deleted as
  dead code, a syntax error under the `__main__` guard. That is one property,
  not eleven, and it costs one list entry per new gate script instead of a new
  test each time.
- **DEC-GTC-006:** that test asserts on stderr markers and on the set of
  documented exit codes, not on a specific code. Exit 1 here means "the gate
  found a violation," and it is also what a script that failed to load exits
  with; exit code alone cannot separate "the gate ran and failed the repo"
  from "the file is not loadable at all." The two load failures do not even
  agree with each other — a failed import prints a traceback header, a
  `SyntaxError` is reported by the compiler in a different format with no such
  line — so both shapes are named.
- **DEC-GTC-007:** the roots default through `None` rather than being turned
  into required arguments. A required argument would be the cleaner signature
  and would break every existing call site, including the `main()` bodies the
  `Makefile` invokes with no arguments at all. The sentinel keeps the shipped
  contract exactly — no root means this repository — while making the default
  a call-time lookup, which is the only property the tests needed.
- **DEC-GTC-008:** the `sys.path.insert` bootstrap stays, and this spec
  records that it is not covered rather than claiming it is. Deleting it was
  tried against the invocation-contract test and the test still passed: Python
  puts the script's own directory on `sys.path[0]` for script execution, so
  the line only matters for `load_tool`'s by-path import, which is a test-side
  concern. Writing an acceptance criterion that implied otherwise would be the
  same class of claim this project exists to fail other repositories for.
- **DEC-GTC-009:** the `tools/` floors are scoped, not merged into the
  package's run. pytest-cov's `--cov-fail-under` applies to the total of
  everything measured, so `--cov=tools` on the existing run would replace two
  honest per-tree numbers with one diluted number — and the diluted one is
  what the gate would then enforce. The package and its gate machinery have
  genuinely different coverage, and a combined figure lets a regression in
  either hide behind the other's headroom.
- **DEC-GTC-010:** the scoped floors are set to the same numbers as the
  package's own, not to today's reading of `tools/`. Holding the gate
  machinery to a lower bar than the code it guards is the argument this
  project exists to refuse, and a floor pinned at the current measurement is a
  floor at the measurement rather than a bar to clear.
- **DEC-GTC-011:** a scope that matches nothing is exit 2, not exit 0. Zero
  covered of zero measured is arithmetically unconstrained, and every way of
  reaching it — a prefix typo, a renamed directory, a run missing its
  `--cov=` — is a gate pointed at nothing while looking green. This is the
  same call the unscoped gates already make for a missing floor and for zero
  measured branches, extended to the new failure mode that scoping
  introduces.
- **DEC-GTC-012:** the scoped-floor key is derived
  (`scoped_floor_key(scope, kind)`) and lives in `_common.py` rather than
  being listed per scope in each checker. Adding a second measured tree
  becomes a config line instead of a code change, and the two checkers cannot
  disagree about where a floor lives — which is the drift that would make one
  gate silently read a floor the other does not.
- **DEC-GTC-013:** `coverage-tools` is a CI job on one interpreter and a
  `pre-pr` step locally, not part of `ci` and not a matrix step. The scripts
  are stdlib-only and version-independent, so a matrix adds runtime and no
  information; and `make ci` stays the fast core gate, matching how
  `typecheck`, `security` and `docs-check` are already placed.

---

## Acceptance Criteria

- [x] **AC-GTC-1:** `env_without_coverage()` returns an environment with every
  name in `COVERAGE_ENV_VARS` removed and its overrides applied, while leaving
  unrelated variables intact. (R-GTC-1, C-GTC-1)
  _Verified by:_ `pytest -k test_env_without_coverage_strips_every_coverage_variable` · stage: `make test`

- [x] **AC-GTC-2 (non-success):** with `COVERAGE_FILE` set in the ambient
  environment and the parent run branch-typed, a nested pytest reaches a real
  verdict — no `INTERNALERROR` in its output and never pytest's internal-error
  exit code. (R-GTC-2)
  _Verified by:_ `pytest -k test_suite_survives_an_ambient_coverage_file` · stage: `make test`

- [x] **AC-GTC-3:** the two tests that spawn a nested `pytest --cov` build
  their child environment through `env_without_coverage(...)` and still assert
  the real outcome of pytest-cov's own floor in both directions. (R-GTC-1)
  _Verified by:_ `pytest -k "test_coverage_floor_fails_below_threshold_pytest or test_coverage_floor_passes_at_threshold"` · stage: `make test`

- [x] **AC-GTC-4:** the four scripts that previously read zero are exercised
  through `run_tool_main` and are measured by the scoped coverage run.
  (R-GTC-3)
  _Verified by:_ `pytest -k "test_branch_check_fails_below_floor or test_cov_floor_fails_below_threshold or test_graph_diff_fails_on_new_broken_edges or test_render_mermaid_matches_to_mermaid_byte_for_byte"` · stage: `make coverage-tools`

- [x] **AC-GTC-5:** `run_tool_main` passes `argv[0]` by default and omits it
  under `pass_argv0=False`; the argparse scripts are invoked without it and
  the hand-rolled ones with it, and both reach their own argument handling
  rather than an unrecognized-argument error or a dropped argument. (R-GTC-4)
  _Verified by:_ `pytest -k "test_plugin_manifests_check_passes_on_the_committed_repo or test_graph_diff_rejects_bad_args or test_render_mermaid_rejects_bad_args"` · stage: `make test`

- [x] **AC-GTC-6 (non-success):** every script under `tools/`, run as
  `python tools/<script>.py` from a throwaway cwd, emits none of the
  load-failure markers on stderr and exits one of the documented codes — so a
  script that no longer loads at all is caught even though exit 1 is a valid
  gate verdict. (R-GTC-5, DEC-GTC-006)
  _Verified by:_ `pytest -k test_gate_script_is_runnable_as_a_script` · stage: `make test`

- [x] **AC-GTC-7 (non-success):** the criterion above does **not** cover the
  `sys.path.insert` bootstrap: deleting that line leaves the test passing.
  This spec records the line as uncovered rather than claiming it. (C-GTC-2,
  DEC-GTC-008)
  _Verified by:_ manual deletion experiment against the parametrized script-execution test, re-run green · stage: `make test`

- [x] **AC-GTC-8:** `check_docs` and `check_secrets` run against a fixture
  tree passed as an argument, reaching verdicts about that tree rather than
  about this repository — the behaviour their definition-time defaults
  prevented. (R-GTC-6)
  _Verified by:_ `pytest -k "test_docs_check_treats_a_missing_readme_as_every_doc_unlinked or test_fallback_scan_skips_vendored_directories_but_not_tests"` · stage: `make test`

- [x] **AC-GTC-9:** calling those entry points with no root argument still
  resolves to this repository and still reports it clean, so no existing
  caller changes behaviour. (C-GTC-3, DEC-GTC-007)
  _Verified by:_ `pytest -k test_plugin_manifests_check_passes_on_the_committed_repo` · stage: `make pre-pr`

- [x] **AC-GTC-10 (non-success):** each of the three gate scripts returns
  non-zero from `main()` against a planted defect — a required doc that is
  present but unlinked, a committed credential, a manifest that no longer
  matches its generator — and zero against a clean tree. (R-GTC-7)
  _Verified by:_ `pytest -k "test_docs_check_reports_a_present_but_unlinked_doc or test_secret_gate_main_fails_when_gitleaks_reports_a_finding or test_plugin_manifests_check_fails_on_a_stale_manifest"` · stage: `make test`

- [x] **AC-GTC-11:** `check_secrets`' scanner is shown to fire on each token
  family it claims to detect, and `check_docs`' `main()` is shown to return
  both verdicts in one run. (R-GTC-7)
  _Verified by:_ `pytest -k "test_fallback_scan_fires_on_each_token_shape or test_docs_check_main_exits_1_on_a_defect_and_0_when_clean"` · stage: `make test`

- [x] **AC-GTC-12 (non-success):** no floor literal appears in the `Makefile`
  or in any workflow file; the guard that enforces this is itself shown to
  fail on a pinned floor in each place, so the `tools/` floors must be read
  from `pyproject.toml` at run time. (R-GTC-8)
  _Verified by:_ `pytest -k "test_threshold_guard_fails_on_a_hard_coded_coverage_floor or test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow"` · stage: `make thresholds`

- [x] **AC-GTC-13:** a scoped run sums only the named subtree, and a coverage
  report in which the package is perfect while the scoped tree is not fails
  the scoped gate while passing the unscoped one — which is exactly the
  dilution the split exists to prevent. (R-GTC-9, C-GTC-4, DEC-GTC-009)
  _Verified by:_ `pytest -k "test_scoped_gate_fails_below_its_own_floor_and_passes_at_it or test_scoped_totals_sum_only_the_named_subtree"` · stage: `make coverage-tools`

- [x] **AC-GTC-14 (non-success):** a `--scope` matching no measured file exits
  2 from both checkers rather than reporting a vacuous pass, and a
  backslash-spelled coverage path still matches the scope prefix. (R-GTC-10,
  DEC-GTC-011)
  _Verified by:_ `pytest -k "test_a_scope_matching_nothing_fails_the_gate_rather_than_passing or test_scoped_totals_normalize_windows_separators or test_scoped_totals_are_zero_for_a_subtree_nobody_measured"` · stage: `make test`

- [x] **AC-GTC-15 (non-success):** a scoped floor absent from
  `[tool.specgraph]` exits 2 from both checkers, and `--scope` with no value
  is a usage error on stderr with exit 2 rather than an empty scope matching
  every file. (R-GTC-11)
  _Verified by:_ `pytest -k "test_scoped_gate_fails_loudly_when_its_floor_is_not_configured or test_coverage_argv_rejects_a_scope_without_a_value or test_scoped_gate_reports_a_usage_error_as_exit_2"` · stage: `make test`

- [x] **AC-GTC-16:** every accepted `--scope` spelling parses to the same
  `(path, scope)` pair, in either argument order and with either separator, so
  the two checkers cannot be invoked differently by accident. (R-GTC-9)
  _Verified by:_ `pytest -k test_coverage_argv_parses_every_accepted_shape` · stage: `make test`

- [x] **AC-GTC-17:** the `coverage-tools` CI job carries its row in
  `docs/hooks.md`'s CI hooks table, enforced by the existing guard that fails
  when any `ci.yml` job is absent from that table. (R-GTC-12)
  _Verified by:_ `pytest -k test_hooks_ci_table_lists_every_ci_job` · stage: `make test`

- [x] **AC-GTC-18 (non-success):** `coverage-tools` runs as part of the
  pre-PR ladder and does **not** run as part of the core gate, so the fast
  local loop is unchanged by it. No automated guard asserts this composition;
  it is observed by running the two stages. (R-GTC-12, DEC-GTC-013)
  _Verified by:_ stage: `make pre-pr`

- [x] **AC-GTC-19 (non-success):** the residual uncovered lines under `tools/`
  in the four converted scripts are their `if __name__ == "__main__":`
  guards, which in-process invocation cannot reach; nothing else is claimed as
  covered by the conversion. (C-GTC-5)
  _Verified by:_ the term-missing report of the scoped run, read directly · stage: `make coverage-tools`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-GTC-1..3, 5..12, 14..17 |
| Scoped coverage | `make coverage-tools` | AC-GTC-4, 13, 19 — `tools/` meets both floors read from `pyproject.toml` |
| Threshold guard | `make thresholds` | AC-GTC-12 — no floor literal in the Makefile or any workflow |
| Self-check | `make validate` | this package validates clean against the repo's own rules |
| Full | `make pre-pr` | AC-GTC-9, 18 — full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
