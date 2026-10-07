# Tasks: measure-coverage-once

Measured at `5246931` (`main`, the squash of M1; the measured files are
byte-identical to `31d7275` on `claude/m1-pin-and-release`, where the figures
were first taken), 2026-10-06; figures taken with this draft present are
dated at `92acd04` on `claude/m2-measure-cheaper` and say so.
Every line number below is re-checked against the branch head before the
milestone that uses it; a sibling package landing first may move a line
without moving the fact. Every number here names the command that produced
it, and where the adversarial review re-measured one at the same commit
both figures stand. At `5246931`: `make -n pre-pr | grep -c "python -m
pytest"` prints 2 and `make -n coverage-tools | grep -c "python -m pytest"`
prints 1; the Appendix A durations command (`python -m pytest tests/ -p
no:cacheprovider -q --durations=12 -o addopts=""`) reports 1578 passed in
212.5 s (213.2 s wall) in the drafter's run and 1578 passed in 210.46 s in
the reviewer's; the Appendix A combined run (`python -m pytest tests/
--cov=openspec_graph --cov=tools --cov-branch --cov-fail-under=0
--cov-report=json:combined.json -q`, run with `COVERAGE_FILE` and the report
in a scratch directory; 232.9 s wall in the drafter's run, 230.9 s in the
reviewer's) sums per scope to `openspec_graph/` 2276/2292 lines and 744/762
branches and `tools/` 842/876 and 276/296 — exactly the figures in the
drafting-time `coverage.json` and `coverage-tools.json` — with unscoped totals
3118/3168 and 1020/1058; the `test` recipe's pytest line alone, timed the
same way into the scratch directory, took 234.3 s and wrote 2276/2292 and
744/762, and the `coverage-tools` recipe's pytest line alone took 236.7 s
and wrote 842/876 and 276/296 under `--scope tools` (its report holding 43
files, the 30 of `openspec_graph/` and the 13 of `tools/`);
`planlint --target . detect` counted 48 change packages. With this draft
present (`92acd04`, re-verified by the review): `detect` counts 49 change packages, and
`make stage-citations` reads 50 specs, `coverage-tools` mentioned in 3 and
verified by 2 and run directly by `ci.yml`, `test` 47 and 47, `pre-pr` 45
and 12, `ci` 14 and 7, 5 stages invoked by no scanned workflow (`ci`,
`security`, `thresholds`, `validate`, `wheel-check`) — at `5246931` without
the draft the same report read 49 specs, `coverage-tools` 2 and 2, `test`
46 and 46, `pre-pr` 44 and 11. Order (DEC-MCO-011, DEC-MCO-012): measure,
then the mapping rule with its guards seen red, then the one run with its
guards seen red and the records, then the per-file report, then — only
after the first CI run that uploads the per-leg reports — the floors.
Milestones 1 to 3 land in one pull request; Milestone 4 is a second, after
that pull request's first CI run; the red runs are recorded here and never
committed.

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
  package read does not exist yet). Drafting values at `5246931`: 234.3 s
  and 236.7 s, with the figures in the header. Re-run the combined command
  at the branch head and confirm the per-scope sums still equal the two-run
  figures; record both sets side by side (AC-MCO-9's before half,
  DEC-MCO-001's premise).
- Record today's checker behaviour against the two-run reports:
  `python tools/check_coverage_floor.py coverage.json --scope openspec_graph`
  and the branch checker both exit 2 naming `openspec_graph_line_fail_under`
  / `openspec_graph_branch_fail_under`; the unscoped line checker on the
  combined report reads its diluted total (98.4 % at `5246931`). Record
  `python tools/check_no_hardcoded_thresholds.py` → PASS.
- Record the per-file list at the branch head at the plan's 85, by summing
  each file's `summary` under its scope prefix in the two reports: at
  `5246931`, `openspec_graph/` none below (lowest `openspec_graph/sarif.py`
  89.1 %, 41/46); `tools/` one below, `tools/check_branch_coverage.py`
  84.2 % (32/38).
- Confirm the subprocess-hook facts DEC-MCO-008 rests on, against the
  installed packages: `ls` the `site-packages` directory for `*.pth` files
  (at `5246931`: only coverage.py's `a1_coverage.pth`, keyed on
  `COVERAGE_PROCESS_START` / `COVERAGE_PROCESS_CONFIG`);
  `python -c "import importlib.metadata as m; print(m.metadata('pytest-cov'))"`
  for the sentence that `.pth` support "was removed in pytest-cov 7";
  `tests/support.run_cli` passes no `cwd`; `test_gate_script_is_runnable_as_a_script`
  uses `cwd=tmp_path` and `env=env_without_coverage()`. Record what each
  says.
- Re-check `add-witness-ci-artifacts`' status: `Status: DRAFT`;
  `grep -c "^- \[ \] \*\*AC-WCA"` over its spec (34 at `5246931`) and the
  `[x]` form (0); `ls .github/actions/` (only `planlint`);
  `grep -n "witness_dir\|ladder:" .github/workflows/ci.yml openspec_graph/detect.py openspec_graph/cli.py`
  (nothing). If any of these has changed, stop and re-read DEC-MCO-007
  before Milestone 2: a partly implemented R7 changes which of its sites
  are a plan and which are a record. Run `grep -n coverage-tools` over its
  spec and tasks and record every site, so Milestone 2 amends the set it
  finds and not a remembered list.
- Re-check the line numbers the proposal cites: `Makefile` 9, 14–37, 71;
  `pyproject.toml` 86–127; `ci.yml` 43, 63, 99, 156, 230, 384–403;
  `docs/hooks.md` 52–53, 60, 93–100; `docs/architecture/c4.md` 44–54,
  222–237; `tests/AGENTS.md` 23, 43–44; `.gitignore` 42–45;
  `tests/test_gate_scripts.py` 430–432; `tools/_common.py` 146, 231–273;
  `tools/check_coverage_floor.py` 31–66; `tools/check_branch_coverage.py`
  36–58; `add-witness-ci-artifacts` spec 56, 227, 359, 468–470 and tasks
  249. Note here any that moved.
- **Gate:** `make validate`

## Milestone 1 — The mapping rule, its guards seen red first

- `tests/test_gate_scripts.py`, written before the code and run red
  (R-MCO-13, DEC-MCO-011): extend the module's `_pyproject(path, **keys)`
  helper — or add a sibling `_pyproject_with_sources(path, sources, **keys)`
  — to write `[tool.coverage.run]\nsource = [...]` above the existing
  tables, so every planted fixture states which trees are measured and in
  what order. Planned tests, named here so AC-MCO-1, 2, 3 and 4 can be
  re-pointed when they exist:
  `test_the_first_source_without_a_scoped_key_reads_the_unscoped_floors`
  (source `["openspec_graph", "tools"]`, `fail_under = 90`,
  `branch_fail_under = 80`, `tools_*` keys, no `openspec_graph_*` key; a
  report whose `openspec_graph/` entries sum below 90 fails both checkers
  under `--scope openspec_graph` with exit 1 and one at or above passes with
  exit 0, while `--scope tools` still reads the `tools_*` keys);
  `test_a_scoped_key_on_the_first_source_is_honoured_and_is_the_misconfiguration_the_guard_rejects`
  (a planted `openspec_graph_line_fail_under = 95` beside `fail_under = 90`
  with `openspec_graph` first in `source`: a package sum of 92 fails — the
  checker reads the scoped key first — and the same planted file is named
  by the duplicate-key helper below; R-MCO-5);
  `test_a_declared_scope_that_is_not_first_still_exits_2_without_its_key`
  (`--scope tools` with `tools` second in `source` and no `tools_*` key
  exits 2 from both checkers, and stderr names `tools_line_fail_under` and
  that the unscoped locators belong to the first entry, `openspec_graph`;
  a scope absent from `source` behaves the same — the existing
  `test_scoped_gate_fails_loudly_when_its_floor_is_not_configured` keeps
  proving the exit code on a fixture with no `source` at all; R-MCO-4);
  `test_the_first_source_without_its_unscoped_floor_is_named_as_absent`
  (`--scope openspec_graph` with `openspec_graph` first in `source` and no
  `fail_under` / `branch_fail_under`: both checkers exit 2 and stderr names
  the scoped key and says the first entry's unscoped floor is absent too —
  the other branch of R-MCO-4's message);
  `test_coverage_sources_reads_the_run_table_array_and_nothing_else`
  (inline `["a", "b"]`, a multi-line array, `["./tools/", "openspec_graph/"]`
  normalised to `["tools", "openspec_graph"]`, a `source` key under
  `[tool.other]` ignored, the dotted `[tool.coverage]\nrun.source = [...]`
  form and a `source_pkgs` key not read, absent file/table/key → `[]`;
  R-MCO-3, DEC-MCO-003);
  `test_the_first_source_declares_no_duplicate_scoped_floor_key` (on the
  real `pyproject.toml`: for the first entry of `coverage_sources`, neither
  `<entry>_line_fail_under` nor `<entry>_branch_fail_under` is present; on
  the planted file above the helper names the key). Run the module and
  record here which of these are red and with what message; the
  duplicate-key test is green on the real tree from the start and red only
  on its planted half, which is the expected shape.
- `tools/_common.py`: add `normalize_scope(name: str) -> str` — strip a
  leading `./` and a trailing `/`, the one spelling `--scope` and `source`
  compare in — and `coverage_sources(pyproject: Path) -> list[str]`
  beside `read_pyproject_int`, hand-rolled on the same table-tracking loop
  — enter the literal `[tool.coverage.run]` header, find `source = [`,
  collect quoted strings until the closing `]`, which may be on a later
  line, pass each through `normalize_scope` — with a docstring
  saying why it is not `tomllib`, what shape it accepts, and that the dotted
  `[tool.coverage] run.source` form and `source_pkgs` are not read and
  surface as the exit-2 message (DEC-MCO-003). Add `scoped_floor(pyproject:
  Path, scope: str, kind: str) -> int | None` implementing R-MCO-3 on the
  normalised scope, in that order — the scoped key, built from the
  normalised name (`tools_line_fail_under`, never `tools/_line_fail_under`),
  then the unscoped locator when `normalize_scope(scope) in
  coverage_sources(pyproject)[:1]` (an empty list needs no special case),
  then `None` — with the unscoped
  locators as one module-level mapping `{"line": ("[tool.coverage.report]",
  "fail_under"), "branch": (SCOPED_FLOOR_SECTION, "branch_fail_under")}` so
  both checkers read the same pair, and a docstring stating the rule, why
  only the first entry falls back, and D2's two reasons for the fallback
  (DEC-MCO-002). `scoped_floor_key`, `coverage_totals` and
  `parse_coverage_argv` unchanged.
- `tools/check_coverage_floor.py`: `_read_floor(pyproject, scope)` returns
  the unscoped read when `scope is None` and `scoped_floor(pyproject, scope,
  "line")` otherwise; the `floor is None` branch's `where` for a scope is
  branched (R-MCO-4): for a scope that is not the first entry,
  "`[tool.specgraph] <scope>_line_fail_under`; the unscoped `fail_under`
  applies only to the first `[tool.coverage.run] source` entry (`<first or
  'none declared'>`)"; for the first entry itself with `fail_under` absent,
  "`[tool.specgraph] <scope>_line_fail_under`, and `[tool.coverage.report]
  fail_under` — the first source entry's floor — is absent too", so a
  reader of the first entry is not sent to the scoped key. Update the
  module docstring:
  one run writes `coverage.json`; this script reads it under `--scope` for
  each measured tree; the floor is the scoped key or, for the first source
  entry without one, `[tool.coverage.report] fail_under`.
- `tools/check_branch_coverage.py`: `_read_branch_floor` likewise through
  `scoped_floor(pyproject, scope, "branch")`; the message is branched the
  same way, naming `[tool.specgraph] branch_fail_under` in the first-entry
  case; docstring updated the same way.
- Re-run `python -m pytest tests/test_gate_scripts.py tests/test_ci_hardening.py -q`
  and record: the new tests green, every pre-existing checker test green
  without an edit (C-MCO-5, AC-MCO-5). Run
  `python tools/check_coverage_floor.py coverage.json --scope openspec_graph`
  against the tree's two-run report with the still-unchanged `pyproject.toml`
  (its `source` has one entry, which is therefore the first) and record that
  it reads `fail_under` and passes — the fallback working on today's config
  before the run changes.
- **Gate:** `make test`

## Milestone 2 — One run, its guards seen red first, and the records

- `tests/test_ci_hardening.py`, written before the Makefile and workflow
  move and run red (R-MCO-13, DEC-MCO-011). Helpers, in the shape of the
  module's existing Makefile readers: `_recipe_lines(makefile_text, target)
  -> list[str]` (the tab-indented lines under `target:` up to the next
  rule, comments dropped, continuation lines joined),
  `_prerequisites(makefile_text, target) -> list[str]`,
  `_suite_jobs_without_coverage_upload(workflow_text) -> list[str]` over
  `workflow_job_blocks` — every job whose block contains `make test` and
  lacks an `upload-artifact` step naming `coverage.json` under
  `if: always()` — and `_hooks_rows_naming_no_job(hooks_text, job_names,
  workflow_names) -> list[str]` — every backticked first cell of the CI
  table that is neither a job id in any workflow under
  `.github/workflows/` nor a workflow file's stem (which is how the
  `release` row, naming `release.yml`, is allowed). Planned tests, named
  here so AC-MCO-6, 7, 10, 11 and 17 can be re-pointed when they exist:
  `test_the_suite_runs_once_through_coverage_run` (`coverage-run` is in
  `.PHONY` and documented; its recipe is the erase and exactly one
  `python -m pytest` line, carrying `--cov` as a bare token,
  `--cov-fail-under=$(NO_FLOOR)` and `--cov-report=json:coverage.json`; no
  `--cov=` anywhere in the Makefile; no other target's recipe contains
  `pytest`);
  `test_test_and_coverage_tools_read_the_one_report_scoped` (`coverage-run`
  in `_prerequisites("test")` and in `_prerequisites("coverage-tools")`;
  `test`'s recipe runs `check_coverage_floor.py` and
  `check_branch_coverage.py` each under `--scope openspec_graph` and under
  `--scope tools`; `coverage-tools`'s recipe runs both under `--scope tools`
  only; `coverage-tools` in `pre-pr`'s prerequisites; `ci`'s prerequisites
  exactly `test lint validate`);
  `test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named`
  (planted texts: `--cov=openspec_graph` on the pytest line; a literal
  `--cov-fail-under=90`; two pytest lines; `coverage-tools:` or `test:`
  with no `coverage-run` prerequisite; `pre-pr` naming `coverage-per-file`);
  `test_every_job_running_the_suite_uploads_its_coverage_report`
  (`_suite_jobs_without_coverage_upload(ci.yml) == []` after asserting at
  least one job runs `make test`);
  `test_a_suite_job_without_a_coverage_upload_is_named` (a planted job
  running `make test` with no upload step is named by job id; a planted job
  with the upload step but without `if: always()` is named too);
  `test_every_hooks_ci_table_row_names_a_job_or_workflow`
  (`_hooks_rows_naming_no_job(docs/hooks.md, …) == []` on the real tree
  after asserting the table has rows — the reverse of
  `test_hooks_ci_table_lists_every_ci_job`, red on the unchanged tree only
  once the job is gone and the row is not, so write it before the job is
  removed and watch it go red at that step);
  `test_a_hooks_row_naming_no_job_is_named` (a planted table with a
  `| \`gone-job\` |` row against the real job and workflow names is named;
  a planted `| \`release\` |` row is not);
  `test_makefile_has_coverage_per_file_report_target` (in the shape of
  `test_makefile_has_matcher_accuracy_report_target`: documented, `.PHONY`,
  `coverage-run` among its prerequisites, in neither `ci` nor `pre-pr`).
  Record the red run here: the first two Makefile tests and the upload
  test red on the unchanged tree with their messages, the planted tests red
  until the helpers exist, the reverse hooks test red between the job's
  removal and the row's.
- `pyproject.toml`: `source = ["openspec_graph", "tools"]` at line 87 with
  the comment above it saying the one run measures both trees, each is
  read scoped, and the first entry is the tree whose floors are
  `fail_under` and `branch_fail_under`; the comment at 89–95 above
  `parallel = true` rewritten — the hook is coverage.py's own
  `a1_coverage.pth`, which calls `process_startup()` whenever
  `COVERAGE_PROCESS_START` is set (`run_cli` sets it); pytest-cov 7 removed
  its own `.pth` support, so the old attribution to pytest-cov was stale
  (DEC-MCO-008) — keeping the sentence on why subprocess measurement
  matters; the `fail_under` comment (99–100) saying it is the package's line
  floor, read under `--scope openspec_graph` by the first-entry fallback of
  `scoped_floor`, and the locator planlint itself detects; the `tools_*`
  comment (111–125) rewritten — the same run, read under `--scope tools`;
  separate keys because `tools/` is a different tree with a different
  reading and one combined number would let either hide behind the other;
  the two sets of floors each ratchet from their own tree's minimum leg and
  need not be equal — keeping its sentence on why the gate machinery is
  held to a bar. Floor values untouched (C-MCO-3). `make thresholds` is not
  affected by comments; run it anyway and record PASS.
- `Makefile`: add `coverage-run: ## Run the suite once, measuring both
  trees into coverage.json (no floor of its own; test and coverage-tools
  read it scoped)` whose recipe is `python -m coverage erase` with the
  existing erase comment and `python -m pytest tests/ --cov --cov-branch
  --cov-fail-under=$(NO_FLOOR) --cov-report=term-missing
  --cov-report=json:coverage.json -q`; move the `NO_FLOOR` comment (3–8) to
  say pytest-cov's total is disabled on the one run because it is a diluted
  total and the scoped checks are the gate. `test: coverage-run` with the
  help text saying both trees' floors, its recipe the four checker lines
  (`check_coverage_floor.py coverage.json --scope openspec_graph`,
  `check_branch_coverage.py coverage.json --scope openspec_graph`, the two
  `--scope tools` lines). `coverage-tools: coverage-run` keeps its help
  text, its recipe is the two `--scope tools` checks against
  `coverage.json`, and its comment says it depends on the run so a
  standalone call produces the report, gates `tools/` alone, and that Make
  builds `coverage-run` once inside `pre-pr`. Add `coverage-run` to
  `.PHONY`. `pre-pr` and `ci` lines unchanged byte for byte (C-MCO-6).
  Confirm `make -n pre-pr | grep -c "python -m pytest"` prints 1 and record
  it; confirm `make help` lists `coverage-run` (the `##` grep picks it up)
  (R-MCO-6, R-MCO-15).
- Run `make test` once on the branch head and record the four scoped lines
  the checkers print beside Milestone 0's two-run figures; they must be
  equal to the line and branch (AC-MCO-9). Then `TIMEFORMAT='%R s'; time
  make pre-pr` and record the wall time beside Milestone 0's before figure
  (R-MCO-15, DEC-MCO-012).
- `.github/workflows/ci.yml`: delete the `coverage-tools` job (lines
  384–403 at `5246931`, comment included). In the `test` job, after the
  `make test` step, add `- uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1`
  with `if: always()`, `name: coverage-${{ runner.os }}-${{ matrix.python-version }}`
  and `path: coverage.json`, under a comment saying the per-leg report is
  what the floor ratchet reads (R-MCO-12), that a red leg's report is
  uploaded on purpose and excluded by the ratchet, and that a leg with no
  report — one that died before `make test`, or whose pytest ended at
  collection with exit 2 and wrote none — contributes nothing under the
  action's `if-no-files-found` default of `warn`. In `test-windows`, the
  same step with
  `name: coverage-${{ runner.os }}-${{ env.PYTHON_DEFAULT }}`. Nothing else
  changes (R-MCO-7). Run
  `python -m pytest tests/test_workflow_hardening.py tests/test_ci_hardening.py -q`
  and record green — the pin-agreement, floor, timeout, permission and
  Python-literal guards all read the new lines, and the reverse hooks test
  is red until the next bullet.
- `docs/hooks.md`: delete the `coverage-tools` row (line 60); the `test`
  row's gate cell becomes "`make lint` + `make typecheck` + `make test`
  (both trees' floors, read scoped from one report; the leg's
  `coverage.json` is uploaded)" with its first cell — the job name and the
  version range — byte-for-byte unchanged, because
  `test_hooks_test_row_names_the_matrix_bounds` parses it; the
  `test-windows` row "same three gates … and the same upload"; rewrite the
  paragraph at 93–100: one run measures both trees, both floors are read
  scoped, pytest-cov's total gates nothing, `coverage-tools` remains a
  documented target that depends on the run, and the per-leg artifacts are
  what the floors are set from. Keep the `typecheck` paragraph above it. Run
  `make docs-check` and `python -m pytest tests/test_ci_hardening.py
  tests/test_workflow_hardening.py -k "hooks" -q`; the reverse hooks test is
  green from here.
- `docs/architecture/c4.md`: §2's paragraph at 44–54 becomes "Two trees,
  two sets of floors, one run" — the first-entry rule in one sentence, the
  reason the floors stay separate keys, and in place of "the same numbers
  (90/80) for both" that each tree's floors ratchet from its own minimum CI
  leg and need not be equal (DEC-GTC-010's first half, superseded —
  DEC-MCO-006); §4b: a `coverage-run` node ("the one run<br/>--cov, both
  trees<br/>coverage.json"), the `mktest` node reading "make
  test<br/>--scope openspec_graph · --scope tools", the `mkcov` node "make
  coverage-tools<br/>--scope tools only", both fed by the run node and
  feeding their trees; the paragraph at 233–237 becomes "Why one run and
  two scoped reads". The §4b sentence on 0/0 and the in-process paragraph
  stay. Run `python -m pytest tests/test_rule_registry_docs.py -q` (it reads
  §4's module map, which this does not touch) and record green. Milestone 4
  re-reads §2 once the numbers move.
- `tests/AGENTS.md`: the node at line 23 becomes "make test — both trees'
  floors, read scoped<br/>make coverage-tools — tools/ only, same report";
  lines 43–44 become "Run `make test`; it measures both trees in one run and
  reads each floor scoped, so one tree's headroom never hides the other's
  regression. `make coverage-tools` re-reads `tools/` from the same report."
  Replace, do not add; `wc -l tests/AGENTS.md` read 50 at `5246931` against
  `MAX_NESTED_LINES = 60`. Run `python -m pytest tests/test_agent_artifacts.py -q -k "nested_agents or agent_index_links"`.
- `tests/test_gate_scripts.py`: the comment at 430–432 above the
  scoped-floor tests becomes "`make test` gates both trees from one report
  through the same two checkers under `--scope`, and `make coverage-tools`
  re-reads `tools/` from it" — the rest of the comment stays (R-MCO-8).
  `.gitignore` is not edited: lines 42–45 keep `coverage-tools.json` and its
  comment for the checkouts that still carry the file (DEC-MCO-013).
- `openspec/changes/add-witness-ci-artifacts/specs/witness-ci-artifacts/spec.md`
  (R-MCO-10, DEC-MCO-007), each edit ending "(amended by
  `measure-coverage-once`)", at every site Milestone 0's `grep -n
  coverage-tools` found, the recording sites, the run-by-name sites (which
  a grep for the job does not find) and DEC-WCA-006; at
  `5246931` those are: the stage-list sentence at line 56 — "Four run in
  `ci.yml` under their make-target name (`test`, `lint`, `typecheck`,
  `docs-check`); `coverage-tools` is built by `make pre-pr` and runs in no
  job of its own" — leaving the dated count at `:51–52` in the same
  paragraph as it is (the count is a measurement, the list at `:56` is a
  plan); R-WCA-27 at 227 — delete the `coverage-tools` → `coverage-tools`
  row; R-WCA-28 — add "the `ladder` job's `make pre-pr` step also records
  `coverage-tools`, which that invocation builds as a prerequisite of
  `pre-pr`, and records it only when the invocation exited 0 — a red
  `pre-pr` proves nothing about whether `coverage-tools` was reached, so
  nothing is recorded for it and W001 reports the stage with no witness at
  the current commit, not as a failing run (DEC-WCA-006)"; DEC-WCA-006 at 359 — append "One inference is sanctioned,
  and only this one: `coverage-tools` is a prerequisite of the very `make
  pre-pr` invocation the `ladder` job runs, so the two share one exit code,
  and Make reaches `pre-pr`'s own recipe only after every prerequisite
  succeeded — an exit 0 is evidence from that process that `coverage-tools`
  ran and passed, not a reading of the Makefile's graph. A red `pre-pr` is
  not evidence either way, so the step records `coverage-tools` on exit 0
  only and otherwise records nothing for it"; DEC-WCA-016's sentence at
  467–470 — "`ci.yml` already runs the suite once per `test` matrix leg and
  once on `test-windows` — the leg count regenerated by `grep -c "run: make
  test" .github/workflows/ci.yml` — and one `make pre-pr` invocation issues
  one pytest run (`make -n pre-pr | grep -c "python -m pytest"` prints 1
  since `measure-coverage-once`); `ladder` adds two — `make ci` runs
  `test`, and `make pre-pr`, a separate Make invocation, runs it again";
  AC-WCA-24 at 744–756 — "`ladder` runs exactly two recorded steps" becomes
  "two stage steps and three recorder steps, the third conditional on the
  `pre-pr` step's exit 0", and its planned
  `test_ci_ladder_runs_only_the_two_aggregates` (`tasks.md:276`) counts
  `run: make` steps, not recorder steps; R-WCA-22 at 185–190 and R-WCA-27
  at 223–225 — the `if: always()` recorder idiom gains its one exception by
  name, the `coverage-tools` recorder, conditional on exit 0 and recording
  nothing on red; R-WCA-30 at 242–245, AC-WCA-25 at 758–762, DEC-WCA-018 at
  481–487 and the planned
  `test_ci_runs_every_w001_enforced_stage_by_its_make_target_name`
  (`tasks.md:277–280`) — each gains the carve-out "each stage appears as
  `make <stage>` in `ci.yml`, or is a prerequisite of an aggregate the
  `ladder` job runs and is recorded under DEC-WCA-006's one sanctioned
  inference", because after this package `make coverage-tools` appears in
  no workflow while two shipped specs cite it on verification lines.
  `tasks.md:249`: drop `coverage-tools` from the recording-job list and add
  the exit-0-only recording of `coverage-tools` to its `ladder` bullet.
  Nothing else in that package — not its Problem Statement's dated count at
  `:51–52`, not its proposal. Run
  `planlint --target . validate --fail-on ERROR --change add-witness-ci-artifacts`
  and record exit 0.
- `CHANGELOG.md`, under `## [Unreleased]`: `### Changed — one suite run
  measures both trees (M2)` with a `measure-coverage-once` entry naming: the
  one run through `coverage-run` with the total disabled and four scoped
  checks; `scoped_floor`'s fallback for the first `source` entry; the
  removed `coverage-tools` job and the per-leg `coverage.json` artifacts;
  that this supersedes `gate-tools-coverage`'s R-GTC-9, C-GTC-4, R-GTC-12,
  DEC-GTC-009, DEC-GTC-013 and the first half of DEC-GTC-010 (recorded
  here, that package being on `main`); the `--per-file-min` report, its
  `per_file_line_min` key and target (added in Milestone 3 — write the
  entry once, after Milestone 3, or amend it then); and the amendment of
  `add-witness-ci-artifacts`. Milestone 4 appends the floor move (R-MCO-14).
- Run `make stage-citations` and record the output here, saying that the
  figures include this package's own spec: `coverage-tools` must now appear
  in the set invoked by no scanned workflow with its mentioned and verified
  counts as the header's with-draft figures read, and no other stage must
  have moved (R-MCO-15).
- **Gate:** `make pre-pr` — the ladder runs the suite once (one pytest line
  in `make -n pre-pr`), all four scoped checks pass with the floors
  unchanged, `make thresholds` PASS; then the pull request's first CI run,
  which is the first time the `tools/` floors are enforced on the Windows
  leg and on 3.10. If a leg is red on a `tools/` floor there, the remedy is
  coverage — a test for the uncovered path — never a lower floor (the
  operating contract: floors move up and never down); record the leg, the
  figure and the fix here.

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
  `check_branch_coverage.main` given a trailing `--per-file-min` ignores it
  and gates normally, as `parse_coverage_argv` already makes it — it keeps
  the first positional as the path and drops the rest — and given the flag
  first takes it as the path and exits 2, file not found; both recorded,
  neither changed). Record the red run.
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
- `Makefile`: `coverage-per-file: coverage-run ## Report every module below
  [tool.specgraph] per_file_line_min line coverage — a report, not a gate`
  with the recipe `python tools/check_coverage_floor.py coverage.json
  --per-file-min`; add it to `.PHONY`; `ci` and `pre-pr` unchanged. It
  depends on the run and not on `test`, so it can be read while a floor is
  red (DEC-MCO-009). Confirm `make thresholds` prints PASS (no literal on
  the line) and that `make help` lists it; its seventeen-character name
  overruns the help's `%-14s` column by three — accepted rather than
  widening the column and moving every row.
- Run `make coverage-per-file` at the branch head and record its output
  here beside Milestone 0's list; at `5246931` the expected list is the one
  module `tools/check_branch_coverage.py` (84.2 %, 32/38), which Milestone
  1's edit to that file may have moved — record what it prints, not what
  was expected.
- **Gate:** `make test` — the per-file tests green on their planted
  reports; then `make thresholds` PASS.

## Milestone 4 — Floors from the minimum leg, after the first CI run

- Precondition: the pull request carrying Milestones 1–3 has had one CI
  run with the upload steps of Milestone 2, and that run's `make test` step
  was green on every leg — if it was not, fix the leg first (Milestone 2's
  gate line) and use the run on which every leg is green, because a red
  leg's uploaded report describes a failure, not the tree, and is excluded
  by R-MCO-12. Record the run id and the artifact names here
  (`coverage-Linux-3.10` … `coverage-Linux-3.14`, `coverage-Windows-3.12` —
  whatever the expressions produced), and any leg whose artifact is absent
  (a leg with no report — died before `make test`, or pytest ended at
  collection — uploads nothing under the action's
  `if-no-files-found` default of `warn`).
- Download every `coverage.json` artifact into a scratch directory and,
  for each leg, sum `covered_lines`/`num_statements` and
  `covered_branches`/`num_branches` from the per-file `summary` entries
  under `openspec_graph/` and under `tools/` — the counts in the JSON,
  never the one-decimal percentage the checkers print, because
  `int()` of a rounded figure is a different number (2850/3168 prints 90.0
  and is 89.96). Run the checkers against each leg too, as the
  cross-check that the sums match what the gate saw. Record the table
  here: one row per leg, four cells of `covered/total (exact pct)`. Note
  which leg is the minimum for each of the four and whether it is the
  Windows leg (capability-probe skips) or 3.10 (the oldest interpreter) —
  recorded, not assumed (R-MCO-12, DEC-MCO-010).
- Apply the rule, writing the arithmetic here before editing: for each of
  `fail_under` (package line), `branch_fail_under` (package branch),
  `tools_line_fail_under`, `tools_branch_fail_under`: `candidate =
  int(min_exact_pct) - 2`; `new = max(current, candidate)`. The plan's
  expectation was near 97/95 and 94/91 from this container's 99.3/97.6 and
  96.1/93.2; write what the legs gave. A floor whose candidate is at or
  below its current value does not move, and that is recorded as such.
- `pyproject.toml`: set the four values (only those that rise), and amend
  the comment above each with "set two points under the minimum green CI
  leg (run <id>, <leg>: <covered/total>, <exact pct>) by
  `measure-coverage-once`; floors move up and never down". No other file
  carries a floor (R-MCO-12). Run `python tools/check_no_hardcoded_thresholds.py`
  and record PASS.
- `docs/architecture/c4.md` §2: re-read the paragraph Milestone 2 rewrote
  and confirm it describes two sets of floors that ratchet from their own
  minimum leg without pinning either number; if the Milestone 2 text names
  a value, replace it with the description (R-MCO-8, DEC-MCO-006).
- `CHANGELOG.md`: append to this package's entry the four floors' old and
  new values, the run id and the minimum leg for each (R-MCO-14).
- Push, and record here the next CI run's id and that every `test` leg and
  `test-windows` is green with the new floors — the leg that was the
  minimum included. Check AC-MCO-19 only once both runs are recorded.
- **Gate:** `make pre-pr`

## Milestone 5 — Confirm, re-point, and record for the plan

- Re-point the stage-only verification lines in
  `specs/one-run-coverage/spec.md` to the tests Milestones 1–3 named, now
  that they exist, keeping each stage: AC-MCO-1 →
  `test_the_first_source_without_a_scoped_key_reads_the_unscoped_floors`
  and `test_a_scoped_key_on_the_first_source_is_honoured_and_is_the_misconfiguration_the_guard_rejects`;
  AC-MCO-2 adds `test_a_declared_scope_that_is_not_first_still_exits_2_without_its_key`;
  AC-MCO-3 → `test_the_first_source_declares_no_duplicate_scoped_floor_key`;
  AC-MCO-4 → `test_coverage_sources_reads_the_run_table_array_and_nothing_else`;
  AC-MCO-6 → `test_the_suite_runs_once_through_coverage_run` and
  `test_test_and_coverage_tools_read_the_one_report_scoped`;
  AC-MCO-7 → `test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named`;
  AC-MCO-10 adds `test_every_hooks_ci_table_row_names_a_job_or_workflow`;
  AC-MCO-11 → `test_every_job_running_the_suite_uploads_its_coverage_report`,
  `test_a_suite_job_without_a_coverage_upload_is_named` and
  `test_a_hooks_row_naming_no_job_is_named`; AC-MCO-16 → the four per-file
  tests; AC-MCO-17 adds `test_makefile_has_coverage_per_file_report_target`;
  AC-MCO-18 adds `test_per_file_flag_leaves_the_argv_contract_alone`. Run
  `python -m pytest tests/test_spec_test_citations.py -q` and confirm every
  selector in every spec resolves.
- Confirm this package validates clean under the repository's own rules
  (`planlint --target . validate --fail-on ERROR --change measure-coverage-once`),
  then `--change add-witness-ci-artifacts`, then `--change gate-tools-coverage`
  (unedited, must still be clean), then the whole tree; record each exit
  code here.
- Confirm `gate-tools-coverage`'s directory is absent from the diff
  (`git diff --stat <base>..HEAD -- openspec/changes/gate-tools-coverage`
  prints nothing) and that `add-witness-ci-artifacts`' diff is the set of
  sites Milestone 2 recorded and nothing else (C-MCO-7).
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
  lines by two packages and run by no workflow by name; no CLI subprocess
  exercises `tools/`, and the hook that would measure one is coverage.py's
  own (DEC-MCO-008); the per-file list at 85 held one module when the
  report landed.
- **Gate:** `make pre-pr`
