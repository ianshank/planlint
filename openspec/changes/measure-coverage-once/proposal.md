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
`openspec_graph_line_fail_under` key exists. One mapping rule closes that:
the first entry of `[tool.coverage.run] source` is the tree whose floors are
the unscoped locators, so a scoped read of it falls back to them and every
other tree keeps needing its own keys; the four floors stay exactly where
they are, planlint's own detected floor locator stays the package's floor,
and both trees are read scoped from one report.

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
now and its figures filled in then). It reverses six recorded requirements
and decisions of `gate-tools-coverage` and says so by name (DEC-MCO-006),
and it amends the stage list and one decision of the unimplemented
`add-witness-ci-artifacts` draft rather than waiting behind it
(DEC-MCO-007).

**Evidence:** measured at `31d7275` on `claude/m2-measure-cheaper`,
2026-10-06, the tree that carries milestones M0 and M1; where the
adversarial review re-measured a figure at the same commit on the same day,
both are given. Every number names its command; `tasks.md` Milestone 0
re-measures at the branch head before the first edit.

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
  wall) in the drafter's run and 1578 passed in 210.46 s in the reviewer's
  re-measurement at the same commit (the plan measured 1498 in 235 s at
  `9c4b6e9`); the slowest test is `test_read_only_verbs_leave_tree_byte_identical`
  at 10.0 s — W7.6's baseline, which this package does not move. The full
  ladder's wall time before the change is measured by `time make pre-pr` at
  the branch head in Milestone 0 and recorded in `tasks.md`; the suite's
  share of it is measured here. The `test` recipe's pytest line alone, timed
  with `TIMEFORMAT='%R s'; time …` with `COVERAGE_FILE` and its JSON report
  pointed into a scratch directory so the tree's own reports were untouched,
  took 234.3 s and wrote 2276/2292 lines and 744/762 branches; the
  `coverage-tools` recipe's pytest line alone took 236.7 s and wrote
  842/876 and 276/296 under `--scope tools` (its report holds 43 files — the
  30 of `openspec_graph/` plus the 13 of `tools/`, for the reason in the
  third bullet); the combined run in the fourth bullet took 232.9 s
  (230.9 s in the reviewer's run). One run costs what either run costs, and
  the ladder pays for two.
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
- **The tools run's own totals are already both trees — and why.** Reading
  `totals` from `coverage-tools.json` gives 2850/3168 lines and 861/1058
  branches against `tools/`'s 842/876 and 276/296. The mechanism, checked
  against the installed packages rather than remembered: the only
  subprocess hook in `site-packages` is coverage.py 7.16's own
  `a1_coverage.pth`, which calls `coverage.process_startup()` when
  `COVERAGE_PROCESS_START` or `COVERAGE_PROCESS_CONFIG` is set; pytest-cov
  7.1.0's METADATA says its own `.pth` support "was removed in pytest-cov 7".
  `tests/support.run_cli` sets `COVERAGE_PROCESS_START` and passes no
  `cwd`, so every CLI subprocess it launches runs from the repository root,
  resolves the config's `source` entries as directories, and under
  `parallel = true` writes data that combines into whichever run is in
  progress — today, `openspec_graph/` lines into the tools run's file. The
  only honest number on that file is the scoped one: the data file was never
  the protection; the scoped read was. `pyproject.toml` lines 89–96 credit
  the hook to "pytest-cov's own auto-installed subprocess-coverage hook",
  which was true of pytest-cov 6.3 and is stale; Milestone 2's comment
  rewrite corrects it.
- **One run reproduces both numbers exactly.** The Appendix A verification
  pass at `31d7275` — `python -m pytest tests/ --cov=openspec_graph
  --cov=tools --cov-branch --cov-fail-under=0 --cov-report=json:combined.json
  -q` (run with `COVERAGE_FILE` and the report pointed into a scratch
  directory so the tree's own reports were untouched; exit 0; 232.9 s wall,
  230.9 s in the reviewer's re-measurement) — summed per scope through the
  checkers from the repository root: `--scope tools` 96.1 % (842/876) lines
  and 93.2 % (276/296) branches, both exit 0 — identical to the two-run
  `coverage-tools.json`; summing the per-file `summary` entries under
  `openspec_graph/` gives 2276/2292 lines and 744/762 branches — identical
  to the two-run `coverage.json`; 30 files under `openspec_graph/`, 13 under
  `tools/`, none outside either. Its unscoped `totals` are the diluted
  figure the Makefile warned about — `python tools/check_coverage_floor.py
  combined.json` reads 98.4 % (3118/3168) and the branch checker 96.4 %
  (1020/1058) — and `--scope openspec_graph` against it exits 2 with the
  same message. The equality also says what the subprocess hook does with
  `tools/` in `source`: nothing is *exercised*, because the CLI imports
  nothing under `tools/`, and the one test that spawns gate scripts
  (`test_gate_script_is_runnable_as_a_script`, `tests/test_ci_hardening.py`,
  `cwd=tmp_path`, `env=env_without_coverage()`) strips the coverage
  environment by design (DEC-GTC-003). It does not say the measurement
  cannot be produced: a gate script run from the repository root under
  that environment would record `tools/` arcs (DEC-MCO-008).
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
  `branch = true` (88), the stale hook comment (89–95) and `parallel = true`
  (96); `[tool.coverage.report] fail_under = 90` (98–101); `[tool.specgraph]
  branch_fail_under = 80` (109), `tools_line_fail_under = 90` and
  `tools_branch_fail_under = 80` (126–127) under a comment (111–125) that
  says the tools floors are "separate … because they measure a different
  tree".
- **planlint's own locator is `fail_under`.** `planlint --target . detect`
  reports "coverage floor 90 from pyproject.toml:[tool.coverage.report].fail_under"
  and 21 make targets; it counted 48 change packages at `31d7275` before
  this package existed and 49 with this draft present (committed as
  `c172eef`, 2026-10-06). `openspec_graph/thresholds.py` anchors on
  `COVERAGE_REPORT_TABLE = "tool.coverage.report"` and a whole-line
  `fail_under = <number>`. A duplicate `openspec_graph_line_fail_under` key
  would leave `fail_under` read by nothing but a disabled pytest-cov total;
  the first-entry fallback keeps the key this tool itself detects as the
  floor, and a guard forbids the duplicate (DEC-MCO-002).
- **What the thresholds guard would say.**
  `tools/check_no_hardcoded_thresholds.py::_THRESHOLD_TOKEN` flags any
  literal of two or more digits outside a `$(...)` span on a recipe line, so
  `--cov-fail-under=$(NO_FLOOR)` passes — `NO_FLOOR := 0` at `Makefile:9`
  exists for exactly this — and a literal `--per-file-min 85` in a recipe
  would be FAIL; the per-file threshold therefore lives in `pyproject.toml`
  like every other number here. The guard scans recipe lines and carries no
  list of target names, so a new target needs no edit to it.
- **The documents that describe two runs.** `grep -rn
  "coverage-tools\|--cov=tools\|separate runs" Makefile .github .gitignore
  docs tests pyproject.toml`: `Makefile` 14–37 and 71; `ci.yml` 384–403;
  `docs/hooks.md` 60 (the job's row) and 93–100 (the paragraph
  "`coverage-tools` is the reverse … re-runs the suite under `--cov=tools`");
  `docs/architecture/c4.md` 44–54 (§2 "Two trees, two coverage floors",
  whose last sentence — "the floors are the same numbers (90/80) for both"
  — states DEC-GTC-010's first half) and 222–223, 229–230, 233–237 (§4b's
  `mktest`/`mkcov` nodes and "Why the two gates are separate runs");
  `tests/AGENTS.md` 23 and 43–44 ("they are separate runs because one
  combined number would dilute both"; the file is 50 lines by `wc -l`
  against `MAX_NESTED_LINES = 60` at `tests/test_agent_artifacts.py:702`);
  `pyproject.toml` 89–95 and 111–125; `.gitignore` 42–45 (`coverage.json`,
  then a two-line comment "`make coverage-tools` writes its own report so
  the tools/ floors can be gated without diluting the package's number",
  then `coverage-tools.json` — an entry that stays, because stale checkouts
  carry the file and `clean` still removes it); and the comment above the
  scoped-floor tests at `tests/test_gate_scripts.py:430–432` ("`make
  coverage-tools` gates tools/ against its own floors using the same two
  checkers under `--scope`"). `docs/hooks.md`'s `test` row carries a
  version-range cell, "(3.10–3.14)" at `31d7275`, that
  `tests/test_workflow_hardening.py::test_hooks_test_row_names_the_matrix_bounds`
  parses; the row's gate cell changes and that cell does not. Dated records
  that describe the two runs too and stay as written under the count
  policy: `CHANGELOG.md`'s `[0.3.0]` entries, `docs/next-steps.md` 286–291,
  both peer reviews and the plan.
- **The requirements this reverses, and what holds them.**
  `openspec/changes/gate-tools-coverage/specs/gate-script-coverage/spec.md`:
  R-GTC-9 ("`make coverage-tools` MUST be its own coverage run with
  pytest-cov's `--cov-fail-under` disabled"), C-GTC-4 ("`make test` MUST
  keep measuring the package alone. No `--cov=tools` may be added to it"),
  R-GTC-12 (`coverage-tools` "MUST run in continuous integration as its own
  single-interpreter job" with a `docs/hooks.md` row), DEC-GTC-009 (scoped
  floors "not merged into the package's run"), DEC-GTC-013 (a CI job on one
  interpreter) and the first half of DEC-GTC-010 ("the scoped floors are
  set to the same numbers as the package's own") — six. DEC-GTC-010's
  second half ("a floor pinned at the current measurement is a floor at the
  measurement rather than a bar to clear") carries forward through the
  two-under rule. AC-GTC-17 cites `test_hooks_ci_table_lists_every_ci_job`
  (`tests/test_ci_hardening.py:733`), which asserts that every `ci.yml` job
  has a row and says nothing about a row whose job is gone; AC-GTC-18 cites
  the stage `make pre-pr`; AC-GTC-4, 13 and 19 cite `make coverage-tools`,
  a target this package keeps as a gate on `tools/` alone. The package is
  shipped and on `main`; its header still reads DRAFT. What stands:
  R-GTC-8 (floors in `[tool.specgraph]`, no literal in Makefile or
  workflow), R-GTC-10 and R-GTC-11 (a scope matching nothing, a missing
  floor and an empty `--scope` all exit 2 — including `--scope tools` with
  its keys removed, which the first-entry rule leaves at exit 2),
  DEC-GTC-011 and DEC-GTC-012 (the derived key in `_common`, which the
  mapping rule extends).
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
  finds nothing. `grep -n coverage-tools` over its spec and tasks finds the
  job named in the stage list of jobs that run a make target by name
  (`specs/witness-ci-artifacts/spec.md:56`), in R-WCA-27's recording table
  (`:227`), in DEC-WCA-016's suite-run arithmetic (`:468–470`) and in the
  recording-job list of its `tasks.md` (`:249`); R-WCA-28 and the tasks'
  `ladder` bullet are where the recording moves to; DEC-WCA-006 (`:359`)
  is the decision that "W001 does not infer that a `pre-pr` witness proves
  `test` ran", which the amendment names and qualifies. Its Problem
  Statement's measurement at `:56` and its `proposal.md` lines 66 and 75
  are dated measurements and stay as written.
- **Stage citations and package counts, in both states.** At `31d7275`
  before this package existed, `make stage-citations`: 49 specs;
  `coverage-tools` mentioned in 2 specs and verified by 2
  (`gate-tools-coverage` and `select-zero-cost-guards`, by
  `grep -ln "Verified by.*coverage-tools" openspec/changes/*/specs/*/spec.md`),
  run directly by `ci.yml`; `test` mentioned in 46 and verified by 46;
  `pre-pr` 44 and 11; `ci` 14 and 7; 16 stages cited, 12 on a verification
  line, 5 invoked by no scanned workflow: `ci`, `security`, `thresholds`,
  `validate`, `wheel-check`. With this draft present (`c172eef`,
  2026-10-06): 50 specs; `coverage-tools` 3 and 2 (this spec mentions it in
  prose and verifies with nothing new); `test` 47 and 47; `pre-pr` 45 and
  12; `ci` 14 and 7; the same five unrun stages. Removing the job moves
  `coverage-tools` into that set; `tasks.md` records the after figures and
  says they include this spec.
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
  `test_hooks_test_row_names_the_matrix_bounds` (the `test` row's version
  cell); `test_makefile_has_matcher_accuracy_report_target`
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
  `make help` lists every target carrying a `##` comment through one
  `grep`, so a new target appears in it by carrying one; `docs/hooks.md`'s
  pre-commit list names the hook targets, not every target, and
  `tools/stage_citations.py` reads stages from specs and workflows, so
  neither needs an entry for a target no spec cites.

## What Changes

- `pyproject.toml`: `[tool.coverage.run] source = ["openspec_graph", "tools"]`
  — the package first, because the first entry is the tree the unscoped
  locators belong to; a new `[tool.specgraph] per_file_line_min = 85` with a
  comment saying it is a reporting threshold read by the per-file report and
  gates nothing; the comments above `source`, above `parallel` (the hook is
  coverage.py's own `a1_coverage.pth`, keyed on `COVERAGE_PROCESS_START`;
  pytest-cov 7 removed its own), above `fail_under` and above the `tools_*`
  floors rewritten for one run read scoped — `fail_under` and
  `branch_fail_under` are the first entry's floors, read under
  `--scope openspec_graph` through the fallback, and the `tools_*` keys the
  `tools/` floors, which may differ from the package's. The four floor
  values are untouched until Milestone 4 (C-MCO-3).
- `tools/_common.py`: `coverage_sources(pyproject) -> list[str]`, a
  stdlib reader for the `source` array under the literal
  `[tool.coverage.run]` header — an inline or multi-line array of quoted
  strings, each entry stripped of a leading `./` and a trailing `/`, nothing
  else; the dotted `[tool.coverage] run.source` form and `source_pkgs` are
  not read, and the docstring says so — returning `[]` when the file, table
  or key is absent; and `scoped_floor(pyproject, scope, kind) -> int | None`
  implementing the mapping (DEC-MCO-002): the scoped key when present; else
  the unscoped locator for that kind — `[tool.coverage.report] fail_under`
  for `line`, `[tool.specgraph] branch_fail_under` for `branch` — when
  `scope` equals the first entry of `coverage_sources`; else `None`.
  `scoped_floor_key`, `coverage_totals` and `parse_coverage_argv` are
  unchanged.
- `tools/check_coverage_floor.py`: `_read_floor` delegates a scoped read to
  `scoped_floor`; the exit-2 message for a missing floor names both places
  looked — the scoped key, and that the unscoped locators belong to the
  first `source` entry, named; a `--per-file-min` flag, consumed in `main`
  before `parse_coverage_argv` so that function's contract stands, switches
  the script into report mode: `per_file_report(cov_path, minimum, scope)`
  lists every measured file under the scope (every file when unscoped)
  whose line coverage is below `[tool.specgraph] per_file_line_min`, sorted
  ascending by percentage then path, one line each with the percentage, the
  path and `covered/total`; exit 1 when the list is non-empty, 0 when it is
  empty with a line saying so, 2 when the key, the report or the scope's
  files are missing. The module docstring describes the one-run shape.
- `tools/check_branch_coverage.py`: `_read_branch_floor` delegates a scoped
  read to `scoped_floor`; the exit-2 message names both places; no per-file
  flag (branches are not in W7.3). The module docstring describes the
  one-run shape.
- `Makefile`: a new `.PHONY`, help-documented `coverage-run` target holds
  `python -m coverage erase` (with its comment) and the one pytest line —
  bare `--cov`, `--cov-branch`, `--cov-fail-under=$(NO_FLOOR)`,
  `--cov-report=term-missing`, `--cov-report=json:coverage.json` — with the
  `NO_FLOOR` comment moved to it. `test: coverage-run` runs both checkers
  under `--scope openspec_graph` and both under `--scope tools`, four hard
  steps, and its help text says both trees' floors. `coverage-tools:
  coverage-run` keeps its name and help text, runs no pytest, and runs the
  two `--scope tools` checks against `coverage.json`, so a standalone
  invocation produces the report and gates `tools/` alone. New
  `coverage-per-file: coverage-run` runs `check_coverage_floor.py
  coverage.json --per-file-min`, is in `.PHONY` and in the help, is reachable
  while a floor is red because it depends on the run and not the gate, and
  is composed into neither `ci` nor `pre-pr`. `ci` and `pre-pr` are
  unchanged line for line; Make builds `coverage-run` once per invocation,
  so `make -n pre-pr` prints one pytest line. `clean` keeps removing
  `coverage-tools.json`, which stale checkouts still carry.
- `.github/workflows/ci.yml`: the `coverage-tools` job (lines 384–403) is
  removed; the `test` matrix job and `test-windows` each gain, after their
  `make test` step, an `actions/upload-artifact` step with `if: always()`,
  the pin and comment already on lines 156 and 230, `path: coverage.json`,
  and a name built from expressions — `coverage-${{ runner.os }}-${{
  matrix.python-version }}` and `coverage-${{ runner.os }}-${{
  env.PYTHON_DEFAULT }}`; the step's comment says a red leg's report is
  uploaded on purpose and excluded by the ratchet, and that a leg with no
  file contributes nothing under the action's `if-no-files-found` default.
  Nothing else in the file changes.
- `docs/hooks.md`: the `coverage-tools` row is removed; the `test` and
  `test-windows` rows say `make test` gates both trees' floors and uploads
  the leg's report, with the `test` row's version-range cell untouched; the
  paragraph at 93–100 is rewritten: one run, both floors read scoped from
  one report, `coverage-tools` kept as a documented target that depends on
  the run, the per-leg artifacts the ratchet reads.
- `docs/architecture/c4.md`: §2's "Two trees, two coverage floors" paragraph
  says one run and two scoped reads, with the first-entry rule, and
  replaces "the same numbers (90/80) for both" with two sets of keys that
  each ratchet from their own tree's minimum leg (DEC-GTC-010's first half,
  superseded); §4b's `mktest`/`mkcov` nodes become a `coverage-run` node
  feeding a `make test` node that names both scopes and a `make
  coverage-tools` node that names `tools/`, and "Why the two gates are
  separate runs" becomes "Why one run and two scoped reads". Milestone 4
  re-reads §2 when the numbers move.
- `tests/AGENTS.md`: the diagram node at line 23 and the sentence at 43–44
  say one run with both floors read scoped, within `MAX_NESTED_LINES`.
- `.gitignore`: unchanged — the `coverage-tools.json` entry and its comment
  stay for the checkouts that still carry the file.
- `tests/test_gate_scripts.py`: the comment above the scoped-floor tests
  (line 430) says `make test` gates both trees from one report and `make
  coverage-tools` re-reads `tools/`; new tests: the mapping rule on planted
  `pyproject.toml` fixtures (the first source with no scoped key reads the
  unscoped locators; a scoped key on the first source is honoured — the
  misconfiguration the guard rejects; `tools` declared second without its
  keys still exits 2 naming both places), the `source` reader's tests
  including the `./`/trailing-slash normalisation and the unread dotted
  form, the duplicate-key guard on the real `pyproject.toml` and on a
  planted one, and the per-file report's tests (a module below the minimum
  is named with percentage and path in ascending order; none below exits 0;
  a missing key exits 2; `--scope` narrows the list).
- `tests/test_ci_hardening.py`: Makefile-shape tests that read the Makefile
  (`coverage-run`'s erase and single bare-`--cov` pytest line with
  `$(NO_FLOOR)`; no `--cov=` anywhere; `test`, `coverage-tools` and the
  report target each depending on `coverage-run` and running no pytest;
  four scoped checker lines in `test`; `pre-pr` still naming
  `coverage-tools`; `ci` unchanged), a report-target test in the shape of
  `test_makefile_has_matcher_accuracy_report_target`, a workflow test that
  every job running `make test` uploads `coverage.json` under `if: always()`,
  a reverse hooks-table test that every CI-table row names a job in
  `ci.yml` or a workflow file under `.github/workflows/` (the `release` row
  names `release.yml`), and planted counter-examples through the same
  helpers.
- `openspec/changes/add-witness-ci-artifacts/specs/witness-ci-artifacts/spec.md`
  and `tasks.md`: amended at every site that names the `coverage-tools` job
  — the stage list at line 56's sentence of jobs that run a make target by
  name, R-WCA-27's table, DEC-WCA-016's arithmetic (which becomes a
  description of the set with its regenerating command) and the
  recording-job list at `tasks.md:249` — plus R-WCA-28 and the tasks'
  `ladder` bullet, which take over the recording of `coverage-tools` from
  the `make pre-pr` step on exit 0 only, and DEC-WCA-006, which gains the
  one sanctioned inference by name and why (DEC-MCO-007). Each edit names
  this package; the dated Problem-Statement measurement at `:56` and the
  proposal stay as written.
- `CHANGELOG.md` `[Unreleased]`: a `Changed` entry for this package naming
  the one run through `coverage-run`, the first-entry mapping rule, the
  removed job and the per-leg artifacts, the supersession of the six GTC
  ids, the per-file report and its key, and the R7 amendment; Milestone 4
  appends the floor move with its per-leg figures and run id.
- `openspec/changes/measure-coverage-once/tasks.md`: the records — the red
  runs, the combined-versus-two-run equality at the branch head, the ladder
  wall time before and after, the per-file list, the per-leg table and the
  ratchet arithmetic.

## Non-Goals

- **No floor moves before Milestone 4, and none moves down ever.**
  Milestones 1–3 leave `fail_under`, `branch_fail_under`,
  `tools_line_fail_under` and `tools_branch_fail_under` at their current
  values; Milestone 4 raises whichever the ratchet rule raises, from the
  per-leg artifacts of the first CI run that uploads them and was green on
  the legs it reads, and records the figures. A floor whose candidate is at
  or below its current value stays.
- **No third floor on the combined total, and no duplicate key.** D2
  rejected both: the total is the diluted number the Makefile refused, and
  an `openspec_graph_line_fail_under` beside `fail_under` is two places for
  one threshold. `--cov-fail-under=$(NO_FLOOR)` disables pytest-cov's total
  on the one run, and a guard asserts the first source entry carries no
  scoped key.
- **No fallback for any tree but the first `source` entry.** `tools` with
  its keys removed stays exit 2 (R-GTC-11); so does a scope `source` does
  not declare, and so does a package configured through the dotted
  `[tool.coverage] run.source` form, which the reader does not read — loud,
  never a silent pass.
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
  is recorded here. No edit to `add-witness-ci-artifacts` beyond the set of
  sites DEC-MCO-007 describes, and no implementation of it.
- **No claim that a CLI subprocess exercises `tools/`.** The combined run's
  `tools/` figures equal the tools run's to the line because the CLI
  imports nothing under `tools/` and the one test that spawns gate scripts
  strips the coverage environment by design; that is "not exercised", and
  the package does not say "cannot be produced" (DEC-MCO-008).
- **No change to `make ci`'s membership or `make pre-pr`'s.** `ci` stays
  `test lint validate`; `pre-pr` keeps naming `coverage-tools`, which Make
  now satisfies from the `coverage-run` it already built.
- **No change to what the Windows leg or the 3.10 leg runs or skips.** The
  floors are set from what each leg measures; a leg that skips
  capability-probe tests measures less and is allowed to be the minimum.
  The first time the `tools/` floors are enforced on those legs is
  Milestone 2's CI run; if a leg is red there, the remedy is coverage,
  never a lower floor.
- **No archive, no spec-status report, no edit to the plan.** W8 items are
  their own packages; the plan is a dated document and records nothing from
  here until M2 closes.

## Affected Capabilities

- `one-run-coverage`
