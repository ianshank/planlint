# Change: Measure Both Trees in One Suite Run, Read Both Floors Scoped, Report the Per-File Minimum

## Why

The ladder runs the whole test suite twice to produce two coverage numbers.
`make test` measures `openspec_graph/` under `--cov=openspec_graph` and gates
it with the two checkers unscoped, against `[tool.coverage.report] fail_under`
and `[tool.specgraph] branch_fail_under`; `make coverage-tools` erases that
data, runs the same suite again under `--cov=tools`, and gates `tools/` with
the same two checkers under `--scope tools`, against `tools_line_fail_under`
and `tools_branch_fail_under`. The Makefile's own comment gives the reason:
pytest-cov's `--cov-fail-under` applies to the total of everything measured,
so one run measuring both trees would replace two honest numbers with one
diluted one, and the diluted one is what the gate would enforce. That was
right when pytest-cov's total was the only floor. It stopped being the only
floor when `gate-tools-coverage` shipped the scoped checkers: `--scope` sums
the per-file entries under one subtree instead of reading the report's
`totals`, so one data file can be read honestly for each tree — provided the
package's floor is also read scoped, which today it is not. The unscoped call
reads `totals`, and `--scope openspec_graph` exits 2 because no
`openspec_graph_line_fail_under` key exists. One mapping rule closes that: a
scope that names an entry of `[tool.coverage.run] source` and has no scoped
key falls back to the unscoped locators, so the four floors stay exactly
where they are, planlint's own detected floor locator stays the package's
floor, and both trees are read scoped from one report.

The second run is paid on every ladder and on every pull request, where a
`coverage-tools` job on one interpreter re-runs the suite to learn a number
the matrix legs could produce themselves — and the ratchet needs them to:
floors set from the lowest CI leg rather than from one Linux container have
to be measured on every leg, Windows and 3.10 included. And coverage.py's
`fail_under` is a total, so no floor in this repository says anything about
one module; the per-file minimum is the next measurement, and by this
repository's own rule it is a report before it is a gate.

This package is the first of milestone M2 ("Measure cheaper") of
`docs/reflection-plan-2026-10.md` and implements its W7.2 (one suite run for
both trees), W7.3 (the per-file minimum as a report) and W7.1 (floors
ratcheted from the minimum CI leg — which can only be read after the first CI
run of W7.2, so it is this package's last milestone, with its rule written
now and its figures filled in then). It reverses five recorded requirements
of `gate-tools-coverage` and says so by name (DEC-MCO-006), and it amends the
stage list of the unimplemented `add-witness-ci-artifacts` draft rather than
waiting behind it (DEC-MCO-007).

**Evidence:** measured at `31d7275` on `claude/m2-measure-cheaper`,
2026-10-06, the tree that carries milestones M0 and M1. Every number names
its command; `tasks.md` Milestone 0 re-measures at the branch head before
the first edit.

- **Two runs per ladder, seven per pull request.**
  `make -n pre-pr | grep -c "python -m pytest"` prints 2 — `Makefile` line
  21 (`--cov=openspec_graph` in `test`) and line 34 (`--cov=tools
  --cov-fail-under=$(NO_FLOOR)` in `coverage-tools`), with `pre-pr` at line
  71 naming `coverage-tools`; `make -n coverage-tools | grep -c "python -m
  pytest"` prints 1. `grep -n "make test\|make coverage-tools"
  .github/workflows/ci.yml` finds `make test` at line 63 (the `test` matrix,
  whose `python-version` list at line 43 has five entries) and line 99
  (`test-windows`), and `make coverage-tools` at line 403 in the
  `coverage-tools` job (lines 384–403). The Appendix A durations command,
  `python -m pytest tests/ -p no:cacheprovider -q --durations=12 -o
  addopts=""`, reports 1578 passed in 212.5 s on this container (213.2 s
  wall; the plan measured 1498 in 235 s at `9c4b6e9`), slowest
  `test_read_only_verbs_leave_tree_byte_identical` at 10.0 s — W7.6's
  baseline, which this package does not move. The full ladder's wall time
  before the change is measured by `time make pre-pr` at the branch head in
  Milestone 0 and recorded in `tasks.md`; the suite's share of it is
  measured here. The `test` recipe's pytest line alone, timed with
  `TIMEFORMAT='%R s'; time …` with `COVERAGE_FILE` and its JSON report
  pointed into a scratch directory so the tree's own reports were untouched,
  took 234.3 s and wrote 2276/2292 lines and 744/762 branches; the
  `coverage-tools` recipe's pytest line alone took 236.7 s and wrote
  842/876 and 276/296 under `--scope tools` (its report holds 43 files — the
  30 of `openspec_graph/` plus the 13 of `tools/`, for the reason in the
  third bullet); the combined run in the fourth bullet took 232.9 s. One
  run costs what either run costs, and the ladder pays for two.
- **What the checkers do today, against the reports in the tree.**
  `coverage.json` and `coverage-tools.json` were written at 22:35:38 and
  22:40:14 UTC (`stat -c '%y'`), after the HEAD commit at 22:30:59 UTC
  (`.git/logs/HEAD`, epoch 1791325859) and before this branch was created,
  so they are HEAD's figures. `python tools/check_coverage_floor.py
  coverage.json --scope openspec_graph` exits 2 — "no line floor set in
  pyproject.toml [tool.specgraph] openspec_graph_line_fail_under";
  `python tools/check_branch_coverage.py coverage.json --scope openspec_graph`
  exits 2 — "no openspec_graph_branch_fail_under set". Unscoped,
  `python tools/check_coverage_floor.py coverage.json` exits 0 with "line
  coverage 99.3% (2276/2292)". `python tools/check_coverage_floor.py
  coverage-tools.json --scope tools` exits 0 at 96.1 % (842/876) and the
  branch checker at 93.2 % (276/296). `python
  tools/check_no_hardcoded_thresholds.py` prints PASS.
- **The tools run's own totals are already both trees.** Reading `totals`
  from `coverage-tools.json` gives 2850/3168 lines and 861/1058 branches
  against `tools/`'s 842/876 and 276/296: `tests/support.run_cli` sets
  `COVERAGE_PROCESS_START`, pytest-cov's `.pth` hook starts coverage in every
  CLI subprocess from the config's `source = ["openspec_graph"]`, and under
  `parallel = true` that data combines into the tools run's file. The only
  honest number on that file is the scoped one — the data file was never the
  protection; the scoped read was.
- **One run reproduces both numbers exactly.** The Appendix A verification
  pass at `31d7275` — `python -m pytest tests/ --cov=openspec_graph
  --cov=tools --cov-branch --cov-fail-under=0 --cov-report=json:combined.json
  -q` (run with `COVERAGE_FILE` and the report pointed into a scratch
  directory so the tree's own reports were untouched; exit 0; 232.9 s wall)
  — summed per scope through the checkers from the repository root:
  `--scope tools` 96.1 % (842/876) lines and 93.2 % (276/296) branches, both
  exit 0 — identical to the two-run `coverage-tools.json`; summing the
  per-file `summary` entries under `openspec_graph/` gives 2276/2292 lines
  and 744/762 branches — identical to the two-run `coverage.json`; 30 files
  under `openspec_graph/`, 13 under `tools/`, none outside either. Its
  unscoped `totals` are the diluted figure the Makefile warned about —
  `python tools/check_coverage_floor.py combined.json` reads 98.4 %
  (3118/3168) and the branch checker 96.4 % (1020/1058) — and
  `--scope openspec_graph` against it exits 2 with the same message. The
  equality also shows what the subprocess hook does not do: no `tools/` line
  is reached by a CLI subprocess, so the combined run adds nothing to
  `tools/` (DEC-MCO-008).
- **The mapping has one place to live.** `tools/_common.py`:
  `read_pyproject_int(pyproject, section, key)` (line 146) reads one integer
  under one table and nothing else — no list reader exists;
  `SCOPED_FLOOR_SECTION` (231) and `scoped_floor_key(scope, kind)` (234)
  derive `<scope>_<kind>_fail_under`; `coverage_totals` (239) sums per-file
  summaries under a scope and normalises separators; `parse_coverage_argv`
  (273) returns exactly `(path, scope)`, and
  `test_coverage_argv_parses_every_accepted_shape` unpacks that pair.
  `tools/check_coverage_floor.py::_read_floor` (lines 31–42) returns
  `[tool.coverage.report] fail_under` when `scope is None` and the scoped
  key otherwise; `tools/check_branch_coverage.py::_read_branch_floor`
  (36–43) does the same with `branch_fail_under`; both `main`s read
  `Path("pyproject.toml")` from the cwd (lines 57 and 58), which is why
  their tests run from a throwaway directory with a planted `pyproject.toml`
  (`tests/test_ci_hardening.py::_write_pyproject`,
  `tests/test_gate_scripts.py::_pyproject`). `pyproject.toml`:
  `[tool.coverage.run]` at 86 with `source = ["openspec_graph"]` (87),
  `branch = true` (88) and `parallel = true` (96); `[tool.coverage.report]
  fail_under = 90` (98–101); `[tool.specgraph] branch_fail_under = 80` (109),
  `tools_line_fail_under = 90` and `tools_branch_fail_under = 80` (126–127)
  under a comment (111–125) that says the tools floors are "separate …
  because they measure a different tree".
- **planlint's own locator is `fail_under`.** `planlint --target . detect`
  reports "coverage floor 90 from pyproject.toml:[tool.coverage.report].fail_under"
  (21 make targets, 48 change packages); `openspec_graph/thresholds.py`
  anchors on `COVERAGE_REPORT_TABLE = "tool.coverage.report"` and a
  whole-line `fail_under = <number>`. A duplicate
  `openspec_graph_line_fail_under` key would leave `fail_under` read by
  nothing but a disabled pytest-cov total; the fallback keeps the key this
  tool itself detects as the floor (DEC-MCO-002).
- **What the thresholds guard would say.**
  `tools/check_no_hardcoded_thresholds.py::_THRESHOLD_TOKEN` flags any
  literal of two or more digits outside a `$(...)` span on a recipe line, so
  `--cov-fail-under=$(NO_FLOOR)` passes — `NO_FLOOR := 0` at `Makefile:9`
  exists for exactly this — and a literal `--per-file-min 85` in a recipe
  would be FAIL; the per-file threshold therefore lives in `pyproject.toml`
  like every other number here.
- **The documents that describe two runs.** `grep -rn
  "coverage-tools\|--cov=tools\|separate runs" Makefile .github docs
  tests/AGENTS.md pyproject.toml`: `Makefile` 14–37 and 71; `ci.yml`
  384–403; `docs/hooks.md` 60 (the job's row) and 93–100 (the paragraph
  "`coverage-tools` is the reverse … re-runs the suite under `--cov=tools`");
  `docs/architecture/c4.md` 44–54 (§2 "Two trees, two coverage floors") and
  222–223, 229–230, 233–237 (§4b's `mktest`/`mkcov` nodes and "Why the two
  gates are separate runs"); `tests/AGENTS.md` 23 and 43–44 ("they are
  separate runs because one combined number would dilute both"; the file is
  50 lines by `wc -l` against `MAX_NESTED_LINES = 60` at
  `tests/test_agent_artifacts.py:702`); `pyproject.toml` 111–125. Dated
  records that describe it too and stay as written under the count policy:
  `CHANGELOG.md`'s `[0.3.0]` entries, `docs/next-steps.md` 286–291, both
  peer reviews and the plan.
- **The requirements this reverses, and what holds them.**
  `openspec/changes/gate-tools-coverage/specs/gate-script-coverage/spec.md`:
  R-GTC-9 ("`make coverage-tools` MUST be its own coverage run with
  pytest-cov's `--cov-fail-under` disabled"), C-GTC-4 ("`make test` MUST
  keep measuring the package alone. No `--cov=tools` may be added to it"),
  R-GTC-12 (`coverage-tools` "MUST run in continuous integration as its own
  single-interpreter job" with a `docs/hooks.md` row), DEC-GTC-009 (scoped
  floors "not merged into the package's run") and DEC-GTC-013 (a CI job on
  one interpreter). AC-GTC-17 cites `test_hooks_ci_table_lists_every_ci_job`
  (`tests/test_ci_hardening.py:733`), which asserts that every `ci.yml` job
  has a row and says nothing about a row whose job is gone; AC-GTC-18 cites
  the stage `make pre-pr`; AC-GTC-4, 13 and 19 cite `make coverage-tools`,
  a target this package keeps. The package is shipped and on `main`; its
  header still reads DRAFT. What stands: R-GTC-8 (floors in
  `[tool.specgraph]`, no literal in Makefile or workflow), R-GTC-10 and
  R-GTC-11 (a scope matching nothing, a missing floor and an empty `--scope`
  all exit 2), DEC-GTC-011 and DEC-GTC-012 (the derived key in `_common`,
  which the mapping rule extends), and DEC-GTC-010 as qualified by W7.1
  (DEC-MCO-010).
- **How a supersession of a package on `main` has been recorded before.**
  `select-zero-cost-guards`' DEC-ZCG-003 "supersedes DEC-PR-001 and
  `post-merge-quality-review`'s non-success criterion … named here so the
  reversal is on record, not discovered", and its R-ZCG-13 names
  `gate-tools-coverage` R-GTC-4's stale count as "a shipped package's record
  and is not edited here"; `pin-actions-by-sha`'s DEC-ASP-007 amended
  `harden-ci-workflows` in place only because that package was on the same
  unmerged branch. `gate-tools-coverage` is on `main`, so its record is
  named here and not edited.
- **The draft whose stage list names the job.**
  `openspec/changes/add-witness-ci-artifacts/` is `Status: DRAFT`;
  `grep -c "^- \[ \] \*\*AC-WCA" openspec/changes/add-witness-ci-artifacts/specs/witness-ci-artifacts/spec.md`
  prints 34 and the `[x]` form prints 0; `ls .github/actions/` shows only
  `planlint` (no `planlint-witness` recorder); `grep -n "witness_dir\|ladder:"
  .github/workflows/ci.yml openspec_graph/detect.py openspec_graph/cli.py`
  finds nothing. It names `coverage-tools` at
  `specs/witness-ci-artifacts/spec.md` lines 56 ("Five run in `ci.yml` under
  their make-target name"), 227 (R-WCA-27's `coverage-tools` →
  `coverage-tools` row), 468 and 470 (DEC-WCA-016's suite-run count) and at
  `tasks.md:249` (the recording-job list); its `proposal.md` lines 66 and 75
  are a dated measurement and stay.
- **Stage citations before.** `make stage-citations` at `31d7275`: 49 specs;
  `coverage-tools` mentioned in 2 specs and verified by 2
  (`gate-tools-coverage` and `select-zero-cost-guards`, by
  `grep -ln "Verified by.*coverage-tools" openspec/changes/*/specs/*/spec.md`),
  run directly by `ci.yml`; `test` mentioned in 46 and verified by 46;
  `pre-pr` 44 and 11; `ci` 14 and 7; 16 stages cited, 12 on a verification
  line, 5 invoked by no scanned workflow: `ci`, `security`, `thresholds`,
  `validate`, `wheel-check`. Removing the job moves `coverage-tools` into
  that set; `tasks.md` records the after figures.
- **The per-file list at the plan's threshold.** Summing each file's
  `summary` in the two HEAD reports under its scope prefix: `openspec_graph/`
  has 30 measured files and none below 85 % line coverage (lowest
  `openspec_graph/sarif.py`, 89.1 %, 41/46); `tools/` has 13 and one below —
  `tools/check_branch_coverage.py` at 84.2 % (32/38), a file this package
  edits; next is `tools/render_rule_catalog.py` at 90.3 % (28/31).
  pytest-cov 7.1.0 and coverage 7.16.2
  (`python -c "import pytest_cov, coverage; print(pytest_cov.__version__, coverage.__version__)"`);
  pytest-cov's own documentation: `--cov-fail-under` fails "if the total
  coverage is less than MIN", and `--cov=x` overrides the config's `source`
  — which is why the recipe passes a bare `--cov`.
- **Guards that hold the shapes this package changes.**
  `test_hooks_ci_table_lists_every_ci_job` (one direction, above);
  `test_makefile_has_matcher_accuracy_report_target`
  (`tests/test_ci_hardening.py:750`) is the model for a report target
  composed into neither `ci` nor `pre-pr`;
  `test_every_reference_to_one_action_agrees_on_one_ref` and
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  hold any new `uses:` line to the pin already at `ci.yml:156` and `:230`
  (`actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1`);
  `test_no_quoted_python_version_literal_outside_env_and_matrix` forbids a
  pasted version in an artifact name; `test_ci_workflow_has_a_windows_job`
  requires the Windows job to run `make test`;
  `test_runtime_dependencies_stay_empty` and `test_rule_set_matches_baseline`
  pin two constraints; `test_gate_script_is_runnable_as_a_script` covers
  both edited scripts' script path; `test_coverage_floor_fails_below_threshold_pytest`,
  `test_coverage_floor_passes_at_threshold` and
  `test_suite_survives_an_ambient_coverage_file` are the nested runs a wider
  `source` must not disturb (they pass `--cov=<x>`, which overrides it).

## What Changes

- `pyproject.toml`: `[tool.coverage.run] source = ["openspec_graph", "tools"]`;
  a new `[tool.specgraph] per_file_line_min = 85` with a comment saying it is
  a reporting threshold read by the per-file report and gates nothing; the
  comments above `source`, above `fail_under` and above the `tools_*` floors
  rewritten for one run read scoped — `fail_under` and `branch_fail_under`
  are the package's floors, read under `--scope openspec_graph` through the
  fallback, and the `tools_*` keys the `tools/` floors. The four floor values
  are untouched until Milestone 4 (C-MCO-3).
- `tools/_common.py`: `coverage_sources(pyproject) -> list[str]`, a
  stdlib reader for the `source` array under `[tool.coverage.run]` — an
  inline or multi-line array of quoted strings, nothing else — returning
  `[]` when the file, table or key is absent; and
  `scoped_floor(pyproject, scope, kind) -> int | None` implementing the
  mapping (DEC-MCO-002): the scoped key when present; else the unscoped
  locator for that kind — `[tool.coverage.report] fail_under` for `line`,
  `[tool.specgraph] branch_fail_under` for `branch` — when `scope` is an
  entry of `coverage_sources`; else `None`. `scoped_floor_key`,
  `coverage_totals` and `parse_coverage_argv` are unchanged.
- `tools/check_coverage_floor.py`: `_read_floor` delegates a scoped read to
  `scoped_floor`; the exit-2 message for a missing floor names both places
  looked — the scoped key and the `source` list the scope is not in; a
  `--per-file-min` flag, consumed in `main` before `parse_coverage_argv` so
  that function's contract stands, switches the script into report mode:
  `per_file_report(cov_path, minimum, scope)` lists every measured file
  under the scope (every file when unscoped) whose line coverage is below
  `[tool.specgraph] per_file_line_min`, sorted ascending by percentage then
  path, one line each with the percentage, the path and `covered/total`;
  exit 1 when the list is non-empty, 0 when it is empty with a line saying
  so, 2 when the key, the report or the scope's files are missing. The
  module docstring describes the one-run shape.
- `tools/check_branch_coverage.py`: `_read_branch_floor` delegates a scoped
  read to `scoped_floor`; the exit-2 message names both places; no per-file
  flag (branches are not in W7.3). The module docstring describes the
  one-run shape.
- `Makefile`: the `test` recipe keeps `coverage erase` and runs pytest once
  with a bare `--cov`, `--cov-branch`, `--cov-fail-under=$(NO_FLOOR)`,
  `--cov-report=term-missing` and `--cov-report=json:coverage.json`, then
  both checkers under `--scope openspec_graph` and both under `--scope
  tools`, four hard steps; its comment says why the total is disabled and
  where each floor is read. `coverage-tools: test` keeps its name and help
  text, runs no pytest of its own, and runs the two `--scope tools` checks
  against `coverage.json` so a standalone invocation is a complete gate;
  its comment says it reads the report `test` just produced. New
  `coverage-per-file: test` runs `check_coverage_floor.py coverage.json
  --per-file-min`, is in `.PHONY` and in the help, and is composed into
  neither `ci` nor `pre-pr`. `NO_FLOOR`'s comment moves its subject to the
  `test` recipe. `ci` and `pre-pr` are unchanged line for line. `clean`
  keeps removing `coverage-tools.json`, which stale checkouts still carry.
- `.github/workflows/ci.yml`: the `coverage-tools` job (lines 384–403) is
  removed; the `test` matrix job and `test-windows` each gain, after their
  `make test` step, an `actions/upload-artifact` step with `if: always()`,
  the pin and comment already on lines 156 and 230, `path: coverage.json`,
  and a name built from expressions — `coverage-${{ runner.os }}-${{
  matrix.python-version }}` and `coverage-${{ runner.os }}-${{
  env.PYTHON_DEFAULT }}`. Nothing else in the file changes.
- `docs/hooks.md`: the `coverage-tools` row is removed; the `test` and
  `test-windows` rows say `make test` gates both trees' floors and uploads
  the leg's report; the paragraph at 93–100 is rewritten: one run, both
  floors read scoped from one report, `coverage-tools` kept as a documented
  target that depends on `test`, the per-leg artifacts the ratchet reads.
- `docs/architecture/c4.md`: §2's "Two trees, two coverage floors" paragraph
  says one run and two scoped reads, with the fallback rule; §4b's
  `mktest`/`mkcov` nodes become one `make test` node naming both scopes and a
  `make coverage-tools` node that depends on it, and "Why the two gates are
  separate runs" becomes "Why one run and two scoped reads".
- `tests/AGENTS.md`: the diagram node at line 23 and the sentence at 43–44
  say one run with both floors read scoped, within `MAX_NESTED_LINES`.
- `tests/test_gate_scripts.py`: the mapping rule's tests on planted
  `pyproject.toml` fixtures (a declared source with no scoped key reads the
  unscoped locators; a scoped key wins when both exist; an undeclared scope
  with no key still exits 2 naming both places), the `source` reader's
  tests, the duplicate-key guard on the real `pyproject.toml` and on a
  planted one, and the per-file report's tests (a module below the minimum
  is named with percentage and path in ascending order; none below exits 0;
  a missing key exits 2; `--scope` narrows the list).
- `tests/test_ci_hardening.py`: Makefile-shape tests that read the Makefile
  (the `test` recipe's bare `--cov`, `$(NO_FLOOR)`, four scoped checker
  lines and no `--cov=`; `coverage-tools` listing `test` as a prerequisite
  and running no pytest; `pre-pr` still naming it; `ci` unchanged), a
  report-target test in the shape of
  `test_makefile_has_matcher_accuracy_report_target`, a workflow test that
  every job running `make test` uploads `coverage.json` under `if: always()`,
  and planted counter-examples through the same helpers.
- `openspec/changes/add-witness-ci-artifacts/specs/witness-ci-artifacts/spec.md`
  and `tasks.md`: the four sites amended (DEC-MCO-007) — line 56's count of
  stages `ci.yml` runs by make-target name drops `coverage-tools`; R-WCA-27
  loses its `coverage-tools` row and R-WCA-28's `ladder` job records
  `coverage-tools` beside `pre-pr` from the `make pre-pr` step that builds
  it; DEC-WCA-016's suite-run arithmetic becomes a description of the set
  with its regenerating command; `tasks.md:249`'s recording-job list drops
  `coverage-tools`. Nothing else in that package changes.
- `CHANGELOG.md` `[Unreleased]`: a `Changed` entry for this package naming
  the one run, the mapping rule, the removed job and the per-leg artifacts,
  the supersession of the five GTC ids, the per-file report and its key, and
  the R7 amendment; Milestone 4 appends the floor move with its per-leg
  figures and run id.
- `openspec/changes/measure-coverage-once/tasks.md`: the records — the red
  runs, the combined-versus-two-run equality at the branch head, the ladder
  wall time before and after, the per-file list, the per-leg table and the
  ratchet arithmetic.

## Non-Goals

- **No floor moves before Milestone 4, and none moves down ever.**
  Milestones 1–3 leave `fail_under`, `branch_fail_under`,
  `tools_line_fail_under` and `tools_branch_fail_under` at their current
  values; Milestone 4 raises whichever the ratchet rule raises, from the
  per-leg artifacts of the first CI run that uploads them, and records the
  figures. A floor whose candidate is at or below its current value stays.
- **No third floor on the combined total, and no duplicate key.** D2
  rejected both: the total is the diluted number the Makefile refused, and
  an `openspec_graph_line_fail_under` beside `fail_under` is two places for
  one threshold. `--cov-fail-under=$(NO_FLOOR)` disables pytest-cov's total
  on the one run, and a guard asserts the duplicate key is absent.
- **No gate on the per-file minimum.** The report target is composed into
  neither `ci` nor `pre-pr`, and its exit code is a signal for whoever runs
  it. Promotion to the ladder is a later package, once the list is empty on
  every leg, with its own reason (guardrail 7, DEC-PM-011).
- **No change to the checkers' command-line contract beyond one flag on one
  script.** `parse_coverage_argv` returns the same pair for the same argv;
  every `--scope` spelling, the usage-error exit, the nothing-measured exit
  and the separator normalisation are unchanged; `check_branch_coverage.py`
  gains no flag.
- **No rule, golden hash, dependency or dev extra change.** `RULES`, the
  README's rules table and `tests/baseline_rules.json` are untouched; the
  `validate`/`graph`/`rules` hashes are unmoved; `[project] dependencies`
  stays empty; `pytest-xdist` (W7.5) is not added; no test is converted to
  an in-process loop (W7.6); no marker is registered (W7.4).
- **No edit to `gate-tools-coverage`.** It is on `main`; the supersession
  is recorded here. No edit to `add-witness-ci-artifacts` beyond the four
  sites named, and no implementation of it.
- **No claim that the subprocess hook now measures `tools/`.** The combined
  run's `tools/` figures equal the tools run's to the line, so nothing new
  is reached; the plan's expectation to that effect is recorded as not borne
  out (DEC-MCO-008).
- **No change to `make ci`'s membership or `make pre-pr`'s.** `ci` stays
  `test lint validate`; `pre-pr` keeps naming `coverage-tools`, which Make
  now satisfies from the `test` it already built.
- **No change to what the Windows leg or the 3.10 leg runs or skips.** The
  floors are set from what each leg measures; a leg that skips
  capability-probe tests measures less and is allowed to be the minimum.
- **No archive, no spec-status report, no edit to the plan.** W8 items are
  their own packages; the plan is a dated document and records nothing from
  here until M2 closes.

## Affected Capabilities

- `one-run-coverage`
