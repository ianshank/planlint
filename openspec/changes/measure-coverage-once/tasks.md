# Tasks: measure-coverage-once

Measured at `31d7275` on `claude/m2-measure-cheaper`, 2026-10-06 — the tree
that carries milestones M0 and M1. Every line number below is re-checked
against the branch head before the milestone that uses it; a sibling
package landing first may move a line without moving the fact. Every number
here names the command that produced it. At `31d7275`:
`make -n pre-pr | grep -c "python -m pytest"` prints 2 and
`make -n coverage-tools | grep -c "python -m pytest"` prints 1; the Appendix
A durations command (`python -m pytest tests/ -p no:cacheprovider -q
--durations=12 -o addopts=""`) reports 1578 passed in 212.5 s (213.2 s
wall); the Appendix A combined run (`python -m pytest tests/
--cov=openspec_graph --cov=tools --cov-branch --cov-fail-under=0
--cov-report=json:combined.json -q`, 232.9 s wall, run with `COVERAGE_FILE`
and the report in a scratch directory) sums per scope to `openspec_graph/`
2276/2292 lines and 744/762 branches and `tools/` 842/876 and 276/296 —
exactly the figures in the tree's HEAD `coverage.json` and
`coverage-tools.json` — with unscoped totals 3118/3168 and 1020/1058; the
`test` recipe's pytest line alone, timed the same way into the scratch
directory, took 234.3 s and wrote 2276/2292 and 744/762, and the
`coverage-tools` recipe's pytest line alone took 236.7 s and wrote 842/876
and 276/296 under `--scope tools` (its report holding 43 files, the 30 of
`openspec_graph/` and the 13 of `tools/`); `make stage-citations` reads 49
specs, `coverage-tools` mentioned in 2 and verified by 2 and run directly
by `ci.yml`, `test` 46 and 46, `pre-pr` 44 and 11, 5 stages invoked by no
scanned workflow (`ci`, `security`, `thresholds`, `validate`,
`wheel-check`). Order (DEC-MCO-011, DEC-MCO-012): measure, then the mapping
rule with its guards seen red, then the one run with its guards seen red
and the records, then the per-file report, then — only after the first CI
run that uploads the per-leg reports — the floors. Milestones 1 to 3 land
in one pull request; Milestone 4 is a second, after that pull request's
first CI run; the red runs are recorded here and never committed.

## Milestone 0 — Grounding pass at the branch head

- Re-run the gate and record its exit code before the first edit under
  `openspec/`: `planlint --target . validate --fail-on ERROR`.
- Re-measure the two-run figures and the ladder before anything moves,
  into a scratch directory so the tree's own reports are untouched:
  `TIMEFORMAT='%R s'; time make pre-pr` for the ladder's wall time (the
  before figure of R-MCO-15; record exit code and seconds — not measured at
  drafting, because that target writes its reports into the tree); then the
  `test` recipe's pytest line and the `coverage-tools` recipe's pytest line
  each timed on their own with `COVERAGE_FILE` and `--cov-report=json:` in
  the scratch directory, recording seconds and the four scoped figures the
  checkers print against each report (`python tools/check_coverage_floor.py
  <report> --scope tools`, the branch checker likewise; the package figures
  by summing `summary` entries under `openspec_graph/`, since the scoped
  package read does not exist yet). Drafting values at `31d7275`: 234.3 s
  and 236.7 s, with the figures in the header. Re-run the combined command
  at the branch head and confirm the per-scope sums still equal the two-run
  figures; record both sets side by side (AC-MCO-9's before half,
  DEC-MCO-001's premise).
- Record today's checker behaviour against the two-run reports:
  `python tools/check_coverage_floor.py coverage.json --scope openspec_graph`
  and the branch checker both exit 2 naming `openspec_graph_line_fail_under`
  / `openspec_graph_branch_fail_under`; the unscoped line checker on the
  combined report reads its diluted total (98.4 % at `31d7275`). Record
  `python tools/check_no_hardcoded_thresholds.py` → PASS.
- Record the per-file list at the branch head at the plan's 85, by summing
  each file's `summary` under its scope prefix in the two reports: at
  `31d7275`, `openspec_graph/` none below (lowest `openspec_graph/sarif.py`
  89.1 %, 41/46); `tools/` one below, `tools/check_branch_coverage.py`
  84.2 % (32/38).
- Re-check `add-witness-ci-artifacts`' status: `Status: DRAFT`;
  `grep -c "^- \[ \] \*\*AC-WCA"` over its spec (34 at `31d7275`) and the
  `[x]` form (0); `ls .github/actions/` (only `planlint`);
  `grep -n "witness_dir\|ladder:" .github/workflows/ci.yml openspec_graph/detect.py openspec_graph/cli.py`
  (nothing). If any of these has changed, stop and re-read DEC-MCO-007
  before Milestone 2: a partly implemented R7 changes which of its sites
  are a plan and which are a record.
- Re-check the line numbers the proposal cites: `Makefile` 9, 14–37, 71;
  `pyproject.toml` 86–127; `ci.yml` 43, 63, 99, 156, 230, 384–403;
  `docs/hooks.md` 52–53, 60, 93–100; `docs/architecture/c4.md` 44–54,
  222–237; `tests/AGENTS.md` 23, 43–44; `tools/_common.py` 146, 231–273;
  `tools/check_coverage_floor.py` 31–66; `tools/check_branch_coverage.py`
  36–58; `add-witness-ci-artifacts` spec 56, 227, 468–470 and tasks 249.
  Note here any that moved.
- **Gate:** `make validate`

## Milestone 1 — The mapping rule, its guards seen red first

- `tests/test_gate_scripts.py`, written before the code and run red
  (R-MCO-13, DEC-MCO-011): extend the module's `_pyproject(path, **keys)`
  helper — or add a sibling `_pyproject_with_sources(path, sources, **keys)`
  — to write `[tool.coverage.run]\nsource = [...]` above the existing
  tables, so every planted fixture states which trees are measured. Planned
  tests, named here so AC-MCO-1, 2, 3 and 4 can be re-pointed when they
  exist: `test_a_declared_source_without_a_scoped_key_reads_the_unscoped_floors`
  (source `["openspec_graph", "tools"]`, `fail_under = 90`,
  `branch_fail_under = 80`, `tools_*` keys, no `openspec_graph_*` key; a
  report whose `openspec_graph/` entries sum below 90 fails both checkers
  under `--scope openspec_graph` with exit 1 and one at or above passes with
  exit 0, while `--scope tools` still reads the `tools_*` keys);
  `test_a_scoped_key_wins_over_the_fallback_when_both_exist` (a planted
  `tools_line_fail_under = 95` beside `fail_under = 90` with `tools` in
  `source`: a `tools/` sum of 92 fails);
  `test_an_undeclared_scope_without_a_key_names_both_places_it_looked`
  (`--scope tools` with no `tools_*` key and `tools` absent from `source`
  exits 2, and stderr names `tools_line_fail_under` and the `source` list —
  the existing `test_scoped_gate_fails_loudly_when_its_floor_is_not_configured`
  keeps proving the exit code);
  `test_coverage_sources_reads_the_run_table_array_and_nothing_else`
  (inline `["a", "b"]`, a multi-line array, a `source` key under
  `[tool.other]` ignored, absent file/table/key → `[]`);
  `test_the_package_tree_declares_no_duplicate_scoped_floor_key` (on the
  real `pyproject.toml`: for the first entry of `coverage_sources`, neither
  `<entry>_line_fail_under` nor `<entry>_branch_fail_under` is present; on a
  planted file carrying `openspec_graph_line_fail_under = 90` the helper
  names the key). Run the module and record here which of these are red and
  with what message; the duplicate-key test is green on the real tree from
  the start and red only on its planted half, which is the expected shape.
- `tools/_common.py`: add `coverage_sources(pyproject: Path) -> list[str]`
  beside `read_pyproject_int`, hand-rolled on the same table-tracking loop
  — enter `[tool.coverage.run]`, find `source = [`, collect quoted strings
  until the closing `]`, which may be on a later line — with a docstring
  saying why it is not `tomllib` and what shape it accepts (DEC-MCO-003).
  Add `scoped_floor(pyproject: Path, scope: str, kind: str) -> int | None`
  implementing R-MCO-3 in that order — scoped key, then fallback for a
  declared source, then `None` — with the unscoped locators as one
  module-level mapping `{"line": ("[tool.coverage.report]", "fail_under"),
  "branch": (SCOPED_FLOOR_SECTION, "branch_fail_under")}` so both checkers
  read the same pair, and a docstring stating the rule and D2's two reasons
  for the fallback (DEC-MCO-002). `scoped_floor_key`, `coverage_totals` and
  `parse_coverage_argv` unchanged.
- `tools/check_coverage_floor.py`: `_read_floor(pyproject, scope)` returns
  the unscoped read when `scope is None` and `scoped_floor(pyproject, scope,
  "line")` otherwise; the `floor is None` branch's `where` for a scope
  becomes "`[tool.specgraph] <scope>_line_fail_under`, and `<scope>` is not
  in `[tool.coverage.run] source`" (R-MCO-4). Update the module docstring:
  one run writes `coverage.json`; this script reads it under `--scope` for
  each measured tree; the floor is the scoped key or, for a declared source
  without one, `[tool.coverage.report] fail_under`.
- `tools/check_branch_coverage.py`: `_read_branch_floor` likewise through
  `scoped_floor(pyproject, scope, "branch")`; the message names both places;
  docstring updated the same way.
- Re-run `python -m pytest tests/test_gate_scripts.py tests/test_ci_hardening.py -q`
  and record: the new tests green, every pre-existing checker test green
  without an edit (C-MCO-5, AC-MCO-5). Run
  `python tools/check_coverage_floor.py coverage.json --scope openspec_graph`
  against the tree's two-run report with the still-unchanged `pyproject.toml`
  (its `source` has one entry) and record that it reads `fail_under` and
  passes — the fallback working on today's config before the run changes.
- **Gate:** `make test`

## Milestone 2 — One run, its guards seen red first, and the records

- `tests/test_ci_hardening.py`, written before the Makefile and workflow
  move and run red (R-MCO-13, DEC-MCO-011). Helpers, in the shape of the
  module's existing Makefile readers: `_recipe_lines(makefile_text, target)
  -> list[str]` (the tab-indented lines under `target:` up to the next
  rule, comments dropped, continuation lines joined) and
  `_prerequisites(makefile_text, target) -> list[str]`; and
  `_suite_jobs_without_coverage_upload(workflow_text) -> list[str]` over
  `workflow_job_blocks` — every job whose block contains `make test` and
  lacks an `upload-artifact` step naming `coverage.json` under
  `if: always()`. Planned tests, named here so AC-MCO-6, 7, 11 and 17 can
  be re-pointed when they exist:
  `test_the_test_recipe_measures_both_trees_in_one_run` (exactly one
  `python -m pytest` line in `test`; it carries `--cov` as a bare token and
  no `--cov=`; it carries `--cov-fail-under=$(NO_FLOOR)` and
  `--cov-report=json:coverage.json`; the recipe runs
  `check_coverage_floor.py` and `check_branch_coverage.py` each under
  `--scope openspec_graph` and under `--scope tools`);
  `test_coverage_tools_depends_on_the_run_that_produces_the_report`
  (`test` in `_prerequisites("coverage-tools")`; no `pytest` in its recipe;
  both `--scope tools` checks present; `coverage-tools` in `pre-pr`'s
  prerequisites; `ci`'s prerequisites exactly `test lint validate`);
  `test_a_recipe_that_pins_a_cov_source_or_skips_the_dependency_is_named`
  (planted texts: `--cov=openspec_graph` in `test`; a literal
  `--cov-fail-under=90`; `coverage-tools:` with no `test` prerequisite;
  `pre-pr` naming `coverage-per-file`);
  `test_every_job_running_the_suite_uploads_its_coverage_report`
  (`_suite_jobs_without_coverage_upload(ci.yml) == []` after asserting at
  least one job runs `make test`);
  `test_a_suite_job_without_a_coverage_upload_is_named` (a planted job
  running `make test` with no upload step is named by job id; a planted job
  with the upload step but without `if: always()` is named too);
  `test_makefile_has_coverage_per_file_report_target` (in the shape of
  `test_makefile_has_matcher_accuracy_report_target`: documented, `.PHONY`,
  `test` among its prerequisites, in neither `ci` nor `pre-pr`). Record the
  red run here: the first two and the upload test red on the unchanged tree
  with their messages, the planted tests red until the helpers exist.
- `pyproject.toml`: `source = ["openspec_graph", "tools"]` at line 87 with
  the comment above it saying the one run measures both trees and each is
  read scoped; the `fail_under` comment (99–100) saying it is the package's
  line floor, read under `--scope openspec_graph` by the fallback of
  `scoped_floor`, and the locator planlint itself detects; the `tools_*`
  comment (111–125) rewritten — the same run, read under `--scope tools`;
  separate keys because `tools/` is a different tree with a different
  reading and one combined number would let either hide behind the other
  — keeping its sentence on why the gate machinery is held to a bar. Floor
  values untouched (C-MCO-3). `make thresholds` is not affected by comments;
  run it anyway and record PASS.
- `Makefile`: `test` recipe — keep `python -m coverage erase` and its
  comment; the pytest line becomes `python -m pytest tests/ --cov
  --cov-branch --cov-fail-under=$(NO_FLOOR) --cov-report=term-missing
  --cov-report=json:coverage.json -q`; then the four checker lines
  (`check_coverage_floor.py coverage.json --scope openspec_graph`,
  `check_branch_coverage.py coverage.json --scope openspec_graph`, the two
  `--scope tools` lines); the help text says both trees' floors. The
  `NO_FLOOR` comment (3–8) moves its subject to `test`: pytest-cov's total
  is disabled on the one run because it is a diluted total and the four
  scoped checks are the gate. `coverage-tools: test` keeps its help text,
  its recipe is the two `--scope tools` checks against `coverage.json`, and
  its comment says it depends on `test` so a standalone call produces the
  report, that Make builds `test` once inside `pre-pr`, and that the two
  checks are re-run so the target is a complete gate on its own. `pre-pr`
  and `ci` lines unchanged byte for byte (C-MCO-6). Confirm
  `make -n pre-pr | grep -c "python -m pytest"` prints 1 and record it
  (R-MCO-6, R-MCO-15).
- Run `make test` once on the branch head and record the four scoped lines
  the checkers print beside Milestone 0's two-run figures; they must be
  equal to the line and branch (AC-MCO-9). Then `TIMEFORMAT='%R s'; time
  make pre-pr` and record the wall time beside Milestone 0's before figure
  (R-MCO-15, DEC-MCO-012).
- `.github/workflows/ci.yml`: delete the `coverage-tools` job (lines
  384–403 at `31d7275`, comment included). In the `test` job, after the
  `make test` step, add `- uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1`
  with `if: always()`, `name: coverage-${{ runner.os }}-${{ matrix.python-version }}`
  and `path: coverage.json`, under a comment saying the per-leg report is
  what the floor ratchet reads (R-MCO-12) and why `if: always()`. In
  `test-windows`, the same step with `name: coverage-${{ runner.os }}-${{ env.PYTHON_DEFAULT }}`.
  Nothing else changes (R-MCO-7). Run
  `python -m pytest tests/test_workflow_hardening.py tests/test_ci_hardening.py -q`
  and record green — the pin-agreement, floor, timeout, permission and
  Python-literal guards all read the new lines.
- `docs/hooks.md`: delete the `coverage-tools` row (line 60); the `test`
  row's gate cell becomes "`make lint` + `make typecheck` + `make test`
  (both trees' floors, read scoped from one report; the leg's
  `coverage.json` is uploaded)", the `test-windows` row "same three gates
  … and the same upload"; rewrite the paragraph at 93–100: one run measures
  both trees, both floors are read scoped, pytest-cov's total gates
  nothing, `coverage-tools` remains a documented target that depends on
  `test`, and the per-leg artifacts are what the floors are set from. Keep
  the `typecheck` paragraph above it. Run `make docs-check` and
  `python -m pytest tests/test_ci_hardening.py -k hooks_ci_table -q`.
- `docs/architecture/c4.md`: §2's paragraph at 44–54 becomes "Two trees,
  two floors, one run" — the fallback rule in one sentence and the reason
  the floors stay separate keys; §4b: the `mktest` node reads
  "make test<br/>--cov (both trees)<br/>--scope openspec_graph · --scope
  tools", the `mkcov` node "make coverage-tools<br/>depends on test<br/>
  --scope tools re-read", with the edges from `gatetests & support` going to
  `mktest` and `mkcov --> mktest` added; the paragraph at 233–237 becomes
  "Why one run and two scoped reads". The §4b sentence on 0/0 and the
  in-process paragraph stay. Run `python -m pytest tests/test_rule_registry_docs.py -q`
  (it reads §4's module map, which this does not touch) and record green.
- `tests/AGENTS.md`: the node at line 23 becomes "make test — both trees'
  floors, read scoped<br/>make coverage-tools — depends on test"; lines
  43–44 become "Run `make test`; it measures both trees in one run and reads
  each floor scoped, so one tree's headroom never hides the other's
  regression. `make coverage-tools` depends on it." Replace, do not add;
  `wc -l tests/AGENTS.md` read 50 at `31d7275` against `MAX_NESTED_LINES =
  60`. Run `python -m pytest tests/test_agent_artifacts.py -q -k "nested_agents or agent_index_links"`.
- `openspec/changes/add-witness-ci-artifacts/specs/witness-ci-artifacts/spec.md`
  (R-MCO-10, DEC-MCO-007), each edit ending "(amended by
  `measure-coverage-once`)": line 56 — "Four run in `ci.yml` under their
  make-target name (`test`, `lint`, `typecheck`, `docs-check`);
  `coverage-tools` is built by `make pre-pr` and runs in no job of its own";
  R-WCA-27 — delete the `coverage-tools` → `coverage-tools` row; R-WCA-28 —
  add "the `ladder` job's `make pre-pr` step also records `coverage-tools`,
  which that invocation builds, with the same exit code"; DEC-WCA-016's
  sentence at 467–470 — "`ci.yml` already runs the suite once per `test`
  matrix leg and once on `test-windows` (`make -n pre-pr | grep -c "python
  -m pytest"` prints 1 since `measure-coverage-once`); `ladder` adds two —
  `make ci` runs `test`, and `make pre-pr`, a separate Make invocation, runs
  it again". `tasks.md:249`: drop `coverage-tools` from the recording-job
  list and add the `ladder` recording of `coverage-tools` to its `ladder`
  bullet. Nothing else in that package. Run
  `planlint --target . validate --fail-on ERROR --change add-witness-ci-artifacts`
  and record exit 0.
- `CHANGELOG.md`, under `## [Unreleased]`: `### Changed — one suite run
  measures both trees (M2)` with a `measure-coverage-once` entry naming: the
  one run with the total disabled and four scoped checks; `scoped_floor`'s
  fallback for a declared source; the removed `coverage-tools` job and the
  per-leg `coverage.json` artifacts; that this supersedes
  `gate-tools-coverage`'s R-GTC-9, C-GTC-4, R-GTC-12, DEC-GTC-009 and
  DEC-GTC-013 (recorded here, that package being on `main`); the
  `--per-file-min` report, its `per_file_line_min` key and target (added in
  Milestone 3 — write the entry once, after Milestone 3, or amend it then);
  and the four-site amendment of `add-witness-ci-artifacts`. Milestone 4
  appends the floor move (R-MCO-14).
- Run `make stage-citations` and record the output here: `coverage-tools`
  must now appear in the set invoked by no scanned workflow, with its
  mentioned and verified counts unchanged from the header, and no other
  stage must have moved (R-MCO-15).
- **Gate:** `make pre-pr` — the ladder runs the suite once (one pytest line
  in `make -n pre-pr`), all four scoped checks pass with the floors
  unchanged, `make thresholds` PASS.

## Milestone 3 — The per-file minimum, as a report

- `tests/test_gate_scripts.py`, written first and run red (R-MCO-13,
  DEC-MCO-009): planned tests, named here so AC-MCO-16 can be re-pointed —
  `test_per_file_report_names_each_module_below_the_minimum` (a planted
  report with `tools/a.py` at 50 % and `tools/b.py` at 80 % against
  `per_file_line_min = 85`: both lines printed, ascending, each with its
  percentage, path and `covered/total`, exit 1);
  `test_per_file_report_exits_zero_when_no_module_is_below` (every file at
  or above the minimum: the saying-so line, exit 0);
  `test_per_file_report_fails_loudly_without_its_key` (no
  `per_file_line_min`: exit 2 naming the key);
  `test_per_file_report_respects_the_scope` (`--scope tools` lists the
  `tools/` module below and not the `openspec_graph/` one);
  `test_per_file_flag_leaves_the_argv_contract_alone` (`main` with the flag
  and `--scope tools` and a path still reaches the same `(path, scope)`;
  `check_branch_coverage.main` given the flag reports a usage error rather
  than silently accepting it — or, if `parse_coverage_argv` treats it as a
  positional, name that here and keep the branch script's behaviour what it
  was). Record the red run.
- `pyproject.toml`, `[tool.specgraph]`: `per_file_line_min = 85` under a
  comment — the reporting threshold for `check_coverage_floor.py
  --per-file-min`, read by the `coverage-per-file` target; it gates nothing
  and is composed into neither `ci` nor `pre-pr` (DEC-PM-011's posture);
  the list it printed when it landed is in this package's `tasks.md`, and a
  gate on it is a later package once the list is empty on every leg.
- `tools/check_coverage_floor.py`: in `main`, before `parse_coverage_argv`,
  `report_mode = "--per-file-min" in argv` and the flag removed from the
  argv passed on (R-MCO-11, AC-MCO-18); `per_file_report(cov_path, minimum,
  scope) -> list[tuple[float, str, int, int]]` returning `(pct, path,
  covered, total)` for every file under the scope prefix (every file when
  `scope is None`, separators normalised as `coverage_totals` does) with
  `pct < minimum`, sorted by `(pct, path)`; in report mode read the minimum
  through `read_pyproject_int(Path("pyproject.toml"), SCOPED_FLOOR_SECTION,
  "per_file_line_min")` (`None` → exit 2 naming the key), check the report
  exists (else exit 2 as today), compute the list, print a header naming
  the scope or "every measured tree" and the minimum, then one line per
  entry as `f"{pct:5.1f}%  {path}  ({covered}/{total})"`, and exit 1 if any,
  else print "no module below N% line coverage" and exit 0; a scope whose
  prefix matches no file exits 2 (R-GTC-10's posture). The docstring gains
  the report mode.
- `Makefile`: `coverage-per-file: test ## Report every module below
  [tool.specgraph] per_file_line_min line coverage — a report, not a gate`
  with the recipe `python tools/check_coverage_floor.py coverage.json
  --per-file-min`; add it to `.PHONY`; `ci` and `pre-pr` unchanged. Confirm
  `make thresholds` prints PASS (no literal on the line).
- Run `make coverage-per-file` at the branch head and record its output
  here beside Milestone 0's list; at `31d7275` the expected list is the one
  module `tools/check_branch_coverage.py` (84.2 %, 32/38), which Milestone
  1's edit to that file may have moved — record what it prints, not what
  was expected.
- **Gate:** `make test` — the per-file tests green on their planted
  reports; then `make thresholds` PASS.

## Milestone 4 — Floors from the minimum leg, after the first CI run

- Precondition: the pull request carrying Milestones 1–3 has had one CI
  run with the upload steps of Milestone 2. Record the run id and the
  artifact names here (`coverage-Linux-3.10` … `coverage-Linux-3.14`,
  `coverage-Windows-3.12` — whatever the expressions produced).
- Download every `coverage.json` artifact into a scratch directory and,
  from the repository root, run `python tools/check_coverage_floor.py
  <leg>.json --scope openspec_graph`, the same under `--scope tools`, and
  `python tools/check_branch_coverage.py` under both scopes, on each leg.
  Record the table here: one row per leg, four cells of
  `covered/total (pct)`. Note which leg is the minimum for each of the four
  and whether it is the Windows leg (capability-probe skips) or 3.10 (the
  oldest interpreter) — recorded, not assumed (R-MCO-12, DEC-MCO-010).
- Apply the rule, writing the arithmetic here before editing: for each of
  `fail_under` (package line), `branch_fail_under` (package branch),
  `tools_line_fail_under`, `tools_branch_fail_under`: `candidate =
  int(min_pct) - 2`; `new = max(current, candidate)`. The plan's
  expectation was near 97/95 and 94/91 from this container's 99.3/97.6 and
  96.1/93.2; write what the legs gave. A floor whose candidate is at or
  below its current value does not move, and that is recorded as such.
- `pyproject.toml`: set the four values (only those that rise), and amend
  the comment above each with "set two points under the minimum CI leg
  (run <id>, <leg>: <pct>) by `measure-coverage-once`; floors move up and
  never down". No other file carries a floor (R-MCO-12). Run
  `python tools/check_no_hardcoded_thresholds.py` and record PASS.
- `CHANGELOG.md`: append to this package's entry the four floors' old and
  new values, the run id and the minimum leg for each (R-MCO-14).
- Push, and record here the next CI run's id and that every `test` leg and
  `test-windows` is green with the new floors — the leg that was the
  minimum included. Check AC-MCO-19 only once that is recorded.
- **Gate:** `make pre-pr`

## Milestone 5 — Confirm, re-point, and record for the plan

- Re-point the stage-only verification lines in
  `specs/one-run-coverage/spec.md` to the tests Milestones 1–3 named, now
  that they exist, keeping each stage: AC-MCO-1 →
  `test_a_declared_source_without_a_scoped_key_reads_the_unscoped_floors`
  and `test_a_scoped_key_wins_over_the_fallback_when_both_exist`; AC-MCO-2
  adds `test_an_undeclared_scope_without_a_key_names_both_places_it_looked`;
  AC-MCO-3 → `test_the_package_tree_declares_no_duplicate_scoped_floor_key`;
  AC-MCO-4 → `test_coverage_sources_reads_the_run_table_array_and_nothing_else`;
  AC-MCO-6 → `test_the_test_recipe_measures_both_trees_in_one_run` and
  `test_coverage_tools_depends_on_the_run_that_produces_the_report`;
  AC-MCO-7 → `test_a_recipe_that_pins_a_cov_source_or_skips_the_dependency_is_named`;
  AC-MCO-11 → `test_every_job_running_the_suite_uploads_its_coverage_report`
  and `test_a_suite_job_without_a_coverage_upload_is_named`; AC-MCO-16 →
  the four per-file tests; AC-MCO-17 adds
  `test_makefile_has_coverage_per_file_report_target`; AC-MCO-18 adds
  `test_per_file_flag_leaves_the_argv_contract_alone`. Run
  `python -m pytest tests/test_spec_test_citations.py -q` and confirm every
  selector in every spec resolves.
- Confirm this package validates clean under the repository's own rules
  (`planlint --target . validate --fail-on ERROR --change measure-coverage-once`),
  then `--change add-witness-ci-artifacts`, then `--change gate-tools-coverage`
  (unedited, must still be clean), then the whole tree; record each exit
  code here.
- Confirm `gate-tools-coverage`'s directory is absent from the diff
  (`git diff --stat <base>..HEAD -- openspec/changes/gate-tools-coverage`
  prints nothing) and that `add-witness-ci-artifacts`' diff is the four
  sites and nothing else (C-MCO-7).
- Confirm C-MCO-1 on the finished tree: `openspec_graph/rules.py`,
  `README.md`'s rules table, `tests/baseline_rules.json` and `[project]
  dependencies` absent from the diff; `python -m pytest
  tests/test_decomposition.py -k byte_identical -q` green.
- Record for the plan's M2 row, when it is next updated: the ladder runs
  the suite once (`make -n pre-pr` count and `time make pre-pr` before and
  after, from Milestones 0 and 2); the scoped numbers equalled the two-run
  numbers on the first run (Milestone 2's record); the floors hold on every
  leg at the values Milestone 4 set, from the leg that was the minimum; the
  `coverage-tools` CI job is gone and the stage is cited on verification
  lines by two packages and run by no workflow by name; the subprocess hook
  measures nothing of `tools/` (DEC-MCO-008); the per-file list at 85 held
  one module when the report landed.
- **Gate:** `make pre-pr`
