# Spec: One-Run Coverage

> **Change:** `measure-coverage-once`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The suite runs twice per ladder to produce two coverage numbers — once under
`--cov=openspec_graph` for the package, gated unscoped against
`[tool.coverage.report] fail_under` and `[tool.specgraph] branch_fail_under`,
and once under `--cov=tools` for the gate scripts, gated under `--scope tools`
against the `tools_*` floors — and a `coverage-tools` job on one interpreter
pays the second run again on every pull request. The reason the Makefile
gives, that pytest-cov's `--cov-fail-under` is a total and a combined run
would enforce a diluted number, was true until `gate-tools-coverage` shipped
the scoped checkers. With `--scope` summing per-file entries, one report can
be read honestly for each tree — except that the package's floor is not read
scoped today: the unscoped call reads `totals`, and `--scope openspec_graph`
exits 2 because no scoped key exists for the package. A duplicate key would
be two places for one threshold; a floor on the combined total would be the
diluted number. The missing piece is one mapping rule: the first entry of
`[tool.coverage.run] source` is the tree whose floors are the unscoped
locators, so a scoped read of it falls back to them, and every other tree
keeps needing its own keys. With it, one run writes one report, both trees
are read scoped from it, the four floors stay where they are, the matrix
legs produce the `tools/` figures on every interpreter and on Windows —
which is what a floor ratcheted from the minimum leg needs — and a per-file
minimum, which coverage.py's total cannot express, becomes a report in the
same checker.

This reverses six recorded requirements and decisions of
`gate-tools-coverage`, which is on `main`, and amends the stage list, the
recording idiom and two decisions of the unimplemented
`add-witness-ci-artifacts` draft, which is on `main` too; both are recorded
here by name.

**Evidence:** measured at `5246931` (`main`, the squash of M1; the measured
files are byte-identical to `31d7275` on `claude/m1-pin-and-release`, where
the figures were first taken), 2026-10-06; each command is in the proposal.
`make -n pre-pr | grep -c "python -m pytest"` prints 2; `ci.yml` runs
`make test` on five matrix legs and `test-windows` and `make coverage-tools`
in a job of its own. Against the drafting-time reports, `--scope
openspec_graph` exits 2 from both checkers ("no line floor set in
pyproject.toml [tool.specgraph] openspec_graph_line_fail_under"), the
unscoped line checker reads 99.3 % (2276/2292), and `--scope tools` reads
96.1 % (842/876) and 93.2 % (276/296). The Appendix A combined run at the
same commit — 232.9 s wall in the drafter's run, 230.9 s in the reviewer's
re-measurement, both dated 2026-10-06 — reproduces those four pairs exactly
per scope while its unscoped totals read 98.4 % (3118/3168) and 96.4 %
(1020/1058); the two-run `coverage-tools.json`'s own totals are already
2850/3168, because the CLI subprocesses `run_cli` launches from the
repository root are measured by coverage.py's own `a1_coverage.pth` hook
(keyed on `COVERAGE_PROCESS_START`, which `run_cli` sets; pytest-cov 7
removed its own) against the config's `source`. `tools/_common.py` has
`read_pyproject_int`, `scoped_floor_key`, `coverage_totals` and
`parse_coverage_argv` and no list reader; `_read_floor` and
`_read_branch_floor` map a scope to `[tool.specgraph]
<scope>_<kind>_fail_under` and nothing else, and today `--scope tools/`
exits 2 asking for `tools/_line_fail_under`. `planlint --target . detect`
reports the floor locator as `pyproject.toml:[tool.coverage.report].fail_under`.
`tools/check_no_hardcoded_thresholds.py` would flag a literal threshold in a
recipe and passes `$(NO_FLOOR)`. The two-run design is described in
`Makefile`, `ci.yml`, `docs/hooks.md`, `docs/architecture/c4.md` §2 and
§4b, `tests/AGENTS.md`, a `pyproject.toml` comment, `.gitignore` and a
comment in `tests/test_gate_scripts.py`. `test_hooks_ci_table_lists_every_ci_job`
holds every `ci.yml` job to a `docs/hooks.md` row and not the reverse.
`add-witness-ci-artifacts` is DRAFT with every criterion unchecked and no
code in the tree; it names `coverage-tools` in its stage list, its
recording table, its suite-run arithmetic and its recording-job list, and
its R-WCA-30, AC-WCA-25 and DEC-WCA-018 require every stage cited on a
verification line to appear in `ci.yml` as `make <stage>`, which
`coverage-tools` does today and will not after this change. `make
stage-citations` at that commit reports `coverage-tools` verified by two
specs and run directly by `ci.yml`. At the plan's threshold of 85, one
module is below: `tools/check_branch_coverage.py` at 84.2 %.

---

## Requirements

- R-MCO-1: `pyproject.toml`'s `[tool.coverage.run] source` MUST list both
  measured trees, `openspec_graph` first and `tools` second; `branch =
  true` and `parallel = true` MUST be unchanged. The `[tool.coverage.report]
  fail_under` and `[tool.specgraph] branch_fail_under` keys MUST remain the
  floors of the first entry — the package — and the `tools_line_fail_under`
  / `tools_branch_fail_under` keys the `tools/` floors; no other floor key
  MAY be added. The comment above `parallel = true` MUST attribute the
  subprocess hook to coverage.py's own `.pth`, not to pytest-cov.
- R-MCO-2: The suite MUST run exactly once per Make invocation, through a
  `.PHONY`, help-documented `coverage-run` target whose recipe is
  `python -m coverage erase` followed by one pytest line with a bare `--cov`
  carrying no source — no `--cov=<source>` MAY appear anywhere in the
  Makefile — together with `--cov-branch`, `--cov-fail-under=$(NO_FLOOR)`,
  `--cov-report=term-missing` and `--cov-report=json:coverage.json`.
  `test` MUST list `coverage-run` as a prerequisite and its recipe MUST be
  `tools/check_coverage_floor.py` and `tools/check_branch_coverage.py`
  against `coverage.json` under `--scope openspec_graph` and under
  `--scope tools` — four invocations, each a hard step. pytest-cov's own
  total MUST gate nothing.
- R-MCO-3: `tools/_common.py` MUST expose `normalize_scope(name) -> str`,
  which strips a leading `./` and a trailing `/`; `coverage_sources(pyproject)
  -> list[str]`, a stdlib-only reader of the `source` array under the
  literal `[tool.coverage.run]` table — an inline or multi-line array of
  quoted strings, each entry passed through `normalize_scope`, table-aware
  so a `source` key under another table is not read — returning `[]` when
  the file, table or key is absent; and `scoped_floor(pyproject, scope,
  kind) -> int | None` with `kind` in `line`/`branch`. The dotted
  `[tool.coverage] run.source` form and `source_pkgs` MUST NOT be read; a
  configuration in either form has, for this reader, no first entry, and
  surfaces as R-MCO-4's exit 2 naming both places, never as a silent pass.
  `scoped_floor` MUST normalise `scope` the same way before anything else,
  so `--scope openspec_graph/` and `--scope ./tools` behave exactly as the
  bare names do, and MUST build the scoped key from the normalised name
  (`tools_line_fail_under`, never `tools/_line_fail_under`); it returns the
  scoped key `<scope>_<kind>_fail_under` under `[tool.specgraph]` when it is
  present; otherwise, when `scope in coverage_sources(pyproject)[:1]` — the
  first entry, with an empty list needing no special case — the unscoped
  locator for that kind: `[tool.coverage.report] fail_under` for `line`,
  `[tool.specgraph] branch_fail_under` for `branch`; otherwise `None`. No
  other entry of `source` falls back. `check_coverage_floor._read_floor`
  and `check_branch_coverage._read_branch_floor` MUST read every scoped
  floor through it; their unscoped behaviour MUST be unchanged.
- R-MCO-4: A scoped read that finds no floor MUST exit 2 from both checkers
  with a message that names both places looked, branched on which case it
  is: for a scope that is not the first `source` entry — `tools` with its
  `tools_*` keys removed, or a scope absent from `source` altogether — the
  message names the scoped key and says the unscoped locator applies only
  to the first `source` entry, naming it (or saying none is declared); for
  the first entry itself with the unscoped key absent, the message names
  the scoped key and says `[tool.coverage.report] fail_under` (for `line`)
  or `[tool.specgraph] branch_fail_under` (for `branch`), the first entry's
  floor, is absent too. R-GTC-11 therefore stands as written: a missing
  floor is a misconfiguration, never a skip. The nothing-measured exit, the
  usage-error exit, every accepted `--scope` spelling and the separator
  normalisation MUST be unchanged (R-GTC-10 stands).
- R-MCO-5: The first entry of `source` MUST carry no scoped key — no
  `openspec_graph_line_fail_under` or `openspec_graph_branch_fail_under` in
  `pyproject.toml`. Because R-MCO-3 reads the scoped key first, the checkers
  would honour such a key if it were present; its presence is therefore a
  misconfiguration the checkers cannot see, and a guard test MUST read the
  real `pyproject.toml` and assert it absent, and MUST show on a planted
  `pyproject.toml` that the duplicate is named. The guard and the fallback
  are complements: one rule says who falls back, the other forbids the key
  that would make the fallback dead.
- R-MCO-6: `coverage-tools` MUST remain a `.PHONY`, help-documented target
  whose prerequisites include `coverage-run`; its recipe MUST invoke no
  pytest and MUST run both checkers under `--scope tools` against
  `coverage.json`, so a standalone invocation on a clean checkout produces
  the report and gates `tools/` — and only `tools/` — on it, never reading
  a missing or stale one. `pre-pr` MUST still name `coverage-tools`, `ci`
  MUST remain `test lint validate`, and `make -n pre-pr` MUST print exactly
  one pytest invocation, because Make builds `coverage-run` once per
  invocation.
- R-MCO-7: `.github/workflows/ci.yml` MUST no longer carry a
  `coverage-tools` job. Every job that runs `make test` — the `test` matrix
  and `test-windows` — MUST upload `coverage.json` as an artifact with
  `if: always()`, using the `actions/upload-artifact` SHA and release-tag
  comment already in the file, under a name built from `runner.os` and the
  leg's interpreter expression and carrying no version literal. pytest-cov
  writes the JSON report on a run with failing tests and `if: always()`
  uploads it; a leg with no report — one that died before `make test`, or
  whose pytest ended at collection with exit 2 — has nothing to upload, and
  the action's `if-no-files-found` default of `warn` covers both cases
  without failing the leg a second time. No other job MAY change.
- R-MCO-8: `docs/hooks.md`'s CI table MUST lose the `coverage-tools` row,
  its `test` and `test-windows` rows MUST say both trees' floors are gated
  and the leg's report uploaded, and the `test` row's version-range cell
  MUST stay intact, because `test_hooks_test_row_names_the_matrix_bounds`
  parses it. The two-run paragraph in `docs/hooks.md`,
  `docs/architecture/c4.md` §2 — whose sentence that both trees' floors
  "are the same numbers" states DEC-GTC-010's first half and MUST become a
  description of two sets of keys that may differ — and §4b,
  `tests/AGENTS.md`'s diagram node and sentence, the `pyproject.toml`
  comments above `source`, `parallel`, `fail_under` and the `tools_*`
  floors, the `Makefile`'s recipe comments and the comment above the
  scoped-floor tests in `tests/test_gate_scripts.py` MUST describe one run
  read scoped. `.gitignore`'s entry and comment for `coverage-tools.json`
  stay, because stale checkouts still carry the file. `tests/AGENTS.md`
  MUST stay within `MAX_NESTED_LINES` with its links resolving. Dated
  records — `CHANGELOG.md`'s released sections, `docs/next-steps.md`, the
  peer reviews, the plan — MUST NOT be edited.
- R-MCO-9: This spec supersedes `gate-tools-coverage`'s R-GTC-9, C-GTC-4,
  R-GTC-12, DEC-GTC-009, DEC-GTC-013 and the first half of DEC-GTC-010 —
  that the `tools/` floors are set to the same numbers as the package's —
  and MUST say so by name here and in the CHANGELOG entry; DEC-GTC-010's
  second half, that a floor is not set at the measurement, carries forward
  through R-MCO-12's two-under rule. That package's files MUST NOT be
  edited. R-GTC-8, R-GTC-10, R-GTC-11, DEC-GTC-011 and DEC-GTC-012 stand.
- R-MCO-10: `add-witness-ci-artifacts`' record MUST be amended in this
  package at every site in its spec and tasks that names the
  `coverage-tools` job or requires every cited stage to run by name, each
  edit naming this package. The sites that name the job: the stage-list
  sentence of jobs that run a make target by name (its Problem Statement's
  dated count of cited stages, two sentences earlier, stays as written —
  the count is a measurement, the list is a plan), R-WCA-27's recording
  table, DEC-WCA-016's suite-run arithmetic and the recording-job list in
  its tasks. The sites that take over the recording: R-WCA-28 and the
  `ladder` bullet of its tasks, which gain the recording of
  `coverage-tools` from the `make pre-pr` step; AC-WCA-24, whose "exactly
  two recorded steps" becomes "two stage steps and three recorder steps,
  the third conditional on the `pre-pr` step's exit 0", with its planned
  `test_ci_ladder_runs_only_the_two_aggregates` counting `run: make` steps
  and not recorder steps; R-WCA-22 and R-WCA-27, whose recorder idiom —
  `if: always()`, so a failing stage is recorded as failing rather than not
  at all — gains its one exception, the `coverage-tools` recorder, which is
  conditional on exit 0 and records nothing on red; and DEC-WCA-006, which
  gains the one sanctioned inference by name and why: `coverage-tools` is a
  prerequisite of the very `make pre-pr` invocation the `ladder` job runs,
  so the two share one exit code, and an exit 0 proves the prerequisite
  was built and passed; a red `pre-pr` proves less — Make may have stopped
  before `coverage-tools` was built — so the step MUST record
  `coverage-tools` only when the invocation exited 0 and otherwise record
  nothing for it, leaving W001 to report the stage with no witness at the
  current commit, not as a failing run. The sites that require every cited
  stage to run by name: R-WCA-30, AC-WCA-25 and DEC-WCA-018, and the
  planned `test_ci_runs_every_w001_enforced_stage_by_its_make_target_name`
  in its tasks, each of which gains the carve-out "each stage appears as
  `make <stage>` in `ci.yml`, or is a prerequisite of an aggregate the
  `ladder` job runs and is recorded under DEC-WCA-006's one sanctioned
  inference" — because after R-MCO-7 `make coverage-tools` appears in no
  workflow while two specs still cite it on verification lines, and
  without the carve-out that test would be red and AC-WCA-25 unsatisfiable.
  DEC-WCA-016's count becomes a description of the set, each figure with
  its own regenerator: `grep -c "run: make test" .github/workflows/ci.yml`
  for the legs that run the suite, `make -n pre-pr | grep -c "python -m
  pytest"` for the runs one `make pre-pr` invocation issues. That package's
  dated Problem-Statement count and its proposal MUST NOT be edited, and
  its `--change` validation MUST stay clean.
- R-MCO-11: `tools/check_coverage_floor.py` MUST accept a `--per-file-min`
  flag, consumed in `main` before `parse_coverage_argv` so that function's
  `(path, scope)` contract is unchanged. Under the flag the script MUST read
  the minimum from `[tool.specgraph] per_file_line_min` — never from the
  command line — and list every measured file under the scope (every file
  when unscoped) whose line coverage is below it, sorted ascending by
  percentage then path, one line each with the percentage, the path and
  `covered/total`; exit 1 when the list is non-empty, 0 with a line saying
  so when it is empty, and 2 when the key, the report or the scope's files
  are missing. A `coverage-per-file` target MUST run it against
  `coverage.json`, MUST list `coverage-run` — not `test` — as its
  prerequisite, so the report is reachable while a floor is red, MUST be
  `.PHONY` and help-documented, and MUST be composed into neither `ci` nor
  `pre-pr`. `check_branch_coverage.py` MUST NOT gain the flag and
  `parse_coverage_argv` MUST NOT change: the branch checker keeps ignoring
  a trailing `--per-file-min` and gating normally, as it does today.
- R-MCO-12: After the first CI run that uploads the per-leg reports of
  R-MCO-7, the four floors MUST be set by this rule and no other: over the
  legs whose `make test` step was green on that run — a red leg's report
  is uploaded too and MUST be excluded — for each tree and kind, read
  `covered` and `total` from the uploaded JSON's per-file summaries under
  the scope prefix, compute the exact ratio, take the minimum over the
  legs, truncate to an integer, subtract two, and set the floor to the
  larger of that candidate and the current floor — floors move up and never
  down. The printed one-decimal percentage MUST NOT be the input: 2850/3168
  prints 90.0 and is 89.96. The per-leg table — run id, artifact name,
  `covered/total` and the exact percentage for each of the four pairs on
  each leg, and which legs were excluded — and the arithmetic MUST be
  recorded in `tasks.md` before the values move; the values MUST live only
  in `pyproject.toml`; `make thresholds` MUST print PASS afterwards; and the
  next CI run MUST be green on every leg with the new floors.
- R-MCO-13: Every guard this spec adds MUST read the file it judges, MUST be
  written and run red against the tree before the change it covers, with
  the red run recorded in `tasks.md` and never committed as a tree state,
  and MUST be shown red on a planted counter-example: a `pyproject.toml`
  whose first source has no scoped key and is read under the fallback, one
  whose first source carries a scoped key (the misconfiguration), one whose
  second source lacks its keys, one whose first source lacks the unscoped
  key too; a Makefile text with `--cov=openspec_graph` on the pytest line,
  with a literal floor, with `coverage-tools` or `test` lacking the
  `coverage-run` prerequisite, with two pytest lines, and with the report
  target composed into `pre-pr`; a workflow text with a job that runs
  `make test` and uploads nothing; a `docs/hooks.md` text whose CI table
  carries a row naming no job in any workflow; a coverage report with one
  module below the minimum.
- R-MCO-14: `CHANGELOG.md`'s `[Unreleased]` section MUST carry a `Changed`
  entry for this package naming the one run through `coverage-run`, the
  mapping rule, the removed job and the per-leg artifacts, the six
  superseded GTC ids, the per-file report and its key, and the R7
  amendment; Milestone 4 MUST append the floor move with its figures and
  run id.
- R-MCO-15: `tasks.md` MUST record, dated with the commit and naming the
  command: `make -n pre-pr | grep -c "python -m pytest"` before and after;
  `time make pre-pr` before and after; the combined report's per-scope
  figures against the two-run figures at the branch head; the per-file list
  at the branch head; and `make stage-citations` after, with
  `coverage-tools` in the set no workflow invokes by name, the record
  saying that its figures include this package's own spec.
- C-MCO-1: No change to any rule, golden hash or runtime dependency: the
  `RULES` tuple, `README.md`'s rules table and `tests/baseline_rules.json`
  are untouched; the `validate`/`graph`/`rules` hashes are unmoved;
  `[project] dependencies` stays empty and no dev extra is added.
- C-MCO-2: `make thresholds` MUST print PASS at every milestone; no recipe
  line and no workflow line MAY carry a numeric threshold literal — the
  total is disabled through `$(NO_FLOOR)` and the per-file minimum is read
  from `pyproject.toml`.
- C-MCO-3: Milestones 1–3 MUST NOT change the value of any of the four
  floors; Milestone 4 is the only milestone that does, upward only, with
  the figures of R-MCO-12 recorded first.
- C-MCO-4: This spec's requirements and criteria MUST NOT pin a count that
  another package changes — a spec count, a stage count, a test count, a
  leg count. Measurements belong in the proposal and in `tasks.md`, dated
  with their commit and naming their command.
- C-MCO-5: Every existing test that exercises the two checkers or the
  shared helpers MUST stay green without edits — the planted
  `pyproject.toml` fixtures those tests write declare no `source`, so no
  scope of theirs is a first entry and their exit codes are unchanged — and
  the nested `pytest --cov` tests and the ambient-`COVERAGE_FILE` test MUST
  stay green, because they pass `--cov=<x>`, which overrides the wider
  `source`.
- C-MCO-6: `ci`'s prerequisites, `pre-pr`'s prerequisites, every workflow
  job name other than the removed one, the composite action and the
  Windows job's three gates MUST be unchanged.
- C-MCO-7: No file of `gate-tools-coverage` MAY change, and no file of
  `add-witness-ci-artifacts` beyond the sites R-MCO-10 describes.
- C-MCO-8: Nothing in this package MAY claim that a CLI subprocess
  exercises `tools/`. The fact is stated as "not exercised" — the CLI
  imports nothing under `tools/`, and the one test that spawns a gate
  script strips the coverage environment by design — never as "cannot be
  produced": a script run from the repository root under that environment
  does record `tools/` arcs. The claim is checked by the per-scope equality
  of R-MCO-15.

---

## Decisions

- **DEC-MCO-001:** one run, two scoped reads per tree, pytest-cov's total
  disabled with `$(NO_FLOOR)`, and no floor on the combined number. The
  Makefile's two-run comment protected two honest numbers from one diluted
  total; the scoped checkers protect them from one data file, which is what
  the plan's D2 says and what the Appendix A run shows: at the measurement
  commit the combined report sums per scope to exactly the two-run figures
  for both trees and both kinds, while its totals read 98.4 % and 96.4 %.
  The total is disabled rather than floored because a floor on it would be
  the diluted number the Makefile refused, and because it would be a third
  floor with no tree of its own to describe. `NO_FLOOR` already exists for
  the tools run and keeps the thresholds guard quiet; it moves to the
  `coverage-run` recipe with its comment. Rejected: a floor on the total
  "as a backstop" (it backs up nothing the scoped reads do not already
  check, and lowers the bar to the better tree's headroom); keeping
  `--cov=openspec_graph --cov=tools` on the command line rather than in
  `source` (pytest-cov's documentation prefers the config form for several
  sources, and a `--cov=x` on the line overrides it — the recipe states both
  facts once).
- **DEC-MCO-002:** one mapping rule — the scoped key if present, else the
  unscoped locators for the first entry of `[tool.coverage.run] source`
  only, else `None` — with a guard that forbids the first entry a scoped
  key, and with the scope normalised before the comparison. The first entry
  and not every declared source, because `tools` is a declared source too,
  and a fallback for every entry would turn "`tools` with its `tools_*`
  keys deleted" from the exit-2 misconfiguration R-GTC-11 made it into a
  silent inheritance of the package's floors; with the rule scoped to the
  first entry, R-GTC-11 stands as written for every other tree and the
  fallback means exactly one thing: the tree whose floors have always been
  `fail_under` and `branch_fail_under`. The comparison is `scope in
  sources[:1]`, so an empty list — no `source`, or a form the reader does
  not read — is simply "no first entry" rather than an index error. The
  scoped key is read first so a future tree gets its own floors by adding
  keys and nothing else — DEC-GTC-012's property, extended — which has a
  consequence the guard exists for: a scoped key on the first entry would
  be honoured by the checkers and would silently make `fail_under` dead
  config, so R-MCO-5's test over the real `pyproject.toml` forbids it, and
  names it on a planted file. The fallback targets `fail_under` and
  `branch_fail_under` because D2 rejects the duplicate key for two reasons
  that both hold against the tree: two places for one threshold is how
  `make thresholds` came to exist, and `planlint --target . detect` reports
  this repository's floor as `[tool.coverage.report].fail_under` — the key a
  duplicate would leave read by nothing but a disabled total. One function
  for both kinds, so the two checkers cannot disagree about where a floor
  lives (the drift DEC-GTC-012 named). The missing-floor message names both
  places looked and is branched on the case, because a reader who sees only
  "no `tools_line_fail_under`" might add a key for the wrong tree, and a
  reader of the first entry whose `fail_under` is simply missing must be
  told that and not sent to the scoped key. Rejected: a `[tool.specgraph]
  default_scope` key (a second place to say what the order of `source`
  already says); a fallback for every declared source (the R-GTC-11
  regression above); reading `source` with `tomllib` (absent on the 3.10
  leg; the gates are stdlib-only and run before anything is installed,
  which is why `read_pyproject_int` is hand-rolled too).
- **DEC-MCO-003:** `coverage_sources` is a hand-rolled reader that accepts
  exactly the shape this file uses — an array of quoted strings, inline or
  spread over lines, under the literal `[tool.coverage.run]` header — and
  the same `normalize_scope` that strips a leading `./` and a trailing `/`
  is applied to each entry and to the `--scope` value, because coverage.py
  treats the two spellings as one directory and today the checkers do not:
  `--scope tools/` exits 2 asking for `tools/_line_fail_under`, which is not
  a regression but would make `--scope openspec_graph/` exit 2 where the
  bare name falls back. The scoped key is built from the normalised name.
  It is table-aware for the reason `read_pyproject_int` is: a bare search
  for `source` would match another table or a comment. It does not read the
  dotted `[tool.coverage] run.source` form or `source_pkgs`, and says so in
  its docstring; a repository configured that way has, for this reader, no
  first entry, so a scoped read of its package falls through to R-MCO-4's
  exit 2 naming both places — a loud mismatch, never a pass on a floor
  nobody read. It returns `[]` rather than `None` for an absent key, and the
  comparison is written `scope in sources[:1]` so the empty list is handled
  by the slice and not by a branch. Rejected: a general TOML array parser
  (a second parser to keep correct for one key); comparing the raw scope
  (the slash case above).
- **DEC-MCO-004:** the pytest line moves into its own `coverage-run`
  target, and `test`, `coverage-tools` and the per-file report all depend
  on it. Four properties follow and each is stated because a guard reads
  it: Make builds `coverage-run` once per invocation, so `make -n pre-pr`
  prints one pytest line and the ladder runs the suite once; a standalone
  `make coverage-tools` on a clean checkout produces the report before
  reading it, never a missing or stale one — the thing the `erase` comment
  warns about; a standalone `make coverage-tools` gates `tools/` and only
  `tools/`, so the stage AC-GTC-4, 13 and 19 cite keeps its meaning instead
  of becoming an alias for `test`; and the per-file report is reachable
  while a floor is red, because it depends on the run and not on the gate.
  `coverage-tools` keeps its name because it is a documented stage cited on
  verification lines by two shipped packages and named by `pre-pr`,
  `docs/hooks.md` and three agent files, and because the thing it names —
  a gate on `tools/`'s floors — still exists. Rejected: `coverage-tools:
  test`, the first draft's shape, under which a standalone call re-ran the
  package's four checks too and the per-file report could not run while a
  floor was red; a file rule `coverage.json:` with the sources as
  prerequisites, which would let a fresh report be reused across
  invocations but would stop `make test` from running when nothing changed
  — a behaviour change for every developer — and would depend on GNU
  Make's directory cache noticing a file another recipe wrote; deleting the
  target and re-pointing the citing criteria, which edits two shipped
  packages' records to remove a stage that still runs.
- **DEC-MCO-005:** the `coverage-tools` CI job is removed rather than kept.
  Its reason for existing — the suite under a different `--cov` — is gone;
  after R-MCO-2 every `make test` leg gates `tools/` too, which is the
  measurement W7.1 needs from every interpreter and from Windows, where a
  one-interpreter job could never have told us the minimum. Keeping the job
  would re-run the suite to confirm what six legs already confirmed.
  `docs/hooks.md`'s row goes with it. `test_hooks_ci_table_lists_every_ci_job`
  holds the table in one direction only — every job has a row — so the
  row's removal would be guarded by nothing; this package adds the reverse
  assertion as a planned guard: every row of the CI table names a job in
  `ci.yml` or a workflow under `.github/workflows/`, with the `release` row
  allowed because it names `release.yml` rather than one of its jobs. Until
  that test exists the stage is the citation. The stage moves into
  `make stage-citations`' set that no workflow invokes by name — recorded,
  not hidden (R-MCO-15) — and that is exactly why R7's "every cited stage
  runs by name" sites need the carve-out of DEC-MCO-007. The per-leg upload
  is placed on the same jobs so the artifacts the ratchet reads come from
  the runs that gate, not from a job of their own.
- **DEC-MCO-006:** six records of `gate-tools-coverage` are superseded and
  named — R-GTC-9 (its own coverage run), C-GTC-4 (`make test` measures the
  package alone), R-GTC-12 (its own CI job with a `docs/hooks.md` row),
  DEC-GTC-009 and DEC-GTC-013 (the reasoning behind both), and the first
  half of DEC-GTC-010 (the `tools/` floors set to the same numbers as the
  package's) — and that package is not edited, because it is shipped and on
  `main`. DEC-GTC-010's second half — a floor pinned at the current reading
  is a floor at the measurement, not a bar to clear — is kept and carried
  forward: R-MCO-12 sets each tree's floors two points under its own
  minimum leg, so the two trees may end on different numbers and neither
  is pinned at the reading; `docs/architecture/c4.md` §2, which states the
  first half as "the same numbers (90/80) for both", is rewritten in
  Milestone 2 to describe two sets of keys and re-read in Milestone 4 when
  the numbers move. The form follows the two precedents for a main-merged
  package: `select-zero-cost-guards`' DEC-ZCG-003 named
  `post-merge-quality-review`'s reversed criterion "so the reversal is on
  record, not discovered", and its R-ZCG-13 left `gate-tools-coverage`'s own
  stale count as "a shipped package's record"; `pin-actions-by-sha` amended
  `harden-ci-workflows` in place only because that sibling sat on the same
  unmerged branch. The six were right when pytest-cov's total was the only
  floor; the scoped checkers that package itself shipped are what make them
  unnecessary, so the reversal is a consequence of its own work. What that
  package still holds is listed in R-MCO-9, and its criteria stay true:
  AC-GTC-4, 13 and 19 cite `make coverage-tools`, which still exists and
  still gates `tools/` alone; AC-GTC-17's test still passes, because it
  never asserted the row's presence for a job that is gone.
- **DEC-MCO-007:** `add-witness-ci-artifacts`' record is amended in this
  package rather than this package landing after it. The plan prefers
  amending when R7 is still unimplemented, and it is: `Status: DRAFT`,
  every criterion unchecked, no recorder action and no `witness_dir` in the
  code. A draft is a plan, not a record of what shipped, so amending it is
  not the rewriting of history the precedents refuse; and leaving it would
  leave a plan that requires a job this package removes. R7 is on `main`,
  so — as with `gate-tools-coverage` and the `select-zero-cost-guards`
  precedent — the amendment is recorded in this package and applied to
  R7's files by Milestone 2 as this package's edit, with each edit naming
  this package. The set of sites is described, not counted, and widened at
  review from "every site that names the job" to "every site that names
  the job or requires every cited stage to run by name", because the
  second kind does not contain the string `coverage-tools` and a grep for
  the job would miss it: R-WCA-30, AC-WCA-25 and DEC-WCA-018 require that
  every stage cited on a verification line appears in `ci.yml` as `make
  <stage>`, and after this package `make coverage-tools` appears in no
  workflow while two shipped specs still cite it — without a carve-out R7's
  own guard would be red on the amended tree and AC-WCA-25 unsatisfiable.
  The carve-out is the sanctioned inference's other face: a stage appears
  as `make <stage>` in `ci.yml`, or is a prerequisite of an aggregate the
  `ladder` job runs and is recorded under DEC-WCA-006's one inference.
  That inference is decided here rather than left to be found: DEC-WCA-006
  refuses to infer `test` from a `pre-pr` witness because a parsed
  prerequisite is a claim about what would run; this amendment sanctions
  exactly one inference and names why it is different in kind: the
  `ladder` job's `make pre-pr` step is the invocation that builds
  `coverage-tools`, so the two share one exit code, and Make reaches
  `pre-pr`'s own recipe only after every prerequisite succeeded — an exit 0
  is evidence that `coverage-tools` ran and passed in that very process, not
  a reading of the Makefile. A red `pre-pr` is not evidence either way:
  Make may have stopped at `ci` before `coverage-tools` was built. So the
  step records `coverage-tools` only on exit 0 and otherwise records
  nothing for it, and W001 then reports the stage with no witness at the
  current commit, not as a failing run — the honest state, in the message
  shapes DEC-WCA-020 pins. That is a deliberate departure from R-WCA-22's
  and R-WCA-27's recorder idiom (`if: always()`, so a failing stage is
  recorded as failing rather than not at all), and the one recorder in the
  workflow that is not `if: always()`; both requirements gain the exception
  by name, and AC-WCA-24's "exactly two recorded steps" becomes two stage
  steps and three recorder steps, with its planned
  `test_ci_ladder_runs_only_the_two_aggregates` counting `run: make` steps
  rather than recorder steps. DEC-WCA-016's count of suite runs is replaced
  by a description of the set, each figure with its own regenerating
  command — the leg count by `grep -c "run: make test"` over `ci.yml`, the
  per-invocation count by `make -n pre-pr | grep -c "python -m pytest"` —
  the count policy applied to the text being amended. Rejected: landing
  after R7 (its schedule is not this package's to wait on, and the drift
  would be R7's to find); amending R7's proposal or its dated
  Problem-Statement count (measurements); recording `coverage-tools` as
  failed on a red `pre-pr` (an attribution the exit code cannot make).
- **DEC-MCO-008:** the subprocess hook is not claimed to exercise `tools/`,
  and the plan's expectation that it would is recorded as not borne out —
  with the mechanism stated correctly, because the first draft had it wrong
  on three counts. The hook is coverage.py 7.16's own `a1_coverage.pth`,
  which calls `process_startup()` when `COVERAGE_PROCESS_START` or
  `COVERAGE_PROCESS_CONFIG` is set; pytest-cov 7 removed its own `.pth`
  support, and its METADATA says so, so the `pyproject.toml` comment that
  credits "pytest-cov's own auto-installed subprocess-coverage hook" is
  stale and is rewritten in Milestone 2. `run_cli` passes no `cwd`, so the
  CLI subprocesses it launches run from the repository root and resolve
  both `source` entries as directories — nothing about the cwd keeps
  `tools/` out of the measurement. What keeps it out is that the CLI
  imports nothing under `tools/`: no line there is exercised by a CLI
  subprocess, which is why the combined run's `tools/` figures equal the
  tools run's to the line. The one test that does spawn gate scripts,
  `test_gate_script_is_runnable_as_a_script`, runs them from a throwaway
  cwd under `env_without_coverage()` by design (DEC-GTC-003), so it
  contributes nothing either. The honest statement is therefore "not
  exercised", never "cannot be produced": a gate script run from the
  repository root with `COVERAGE_PROCESS_START` set does record `tools/`
  arcs, and a future test that did so would move the number. What the
  wider `source` changes is nothing for the nested-pytest tests, which pass
  `--cov=<x>`, and nothing for `make test` run from the repository root.
  Recorded so the next reader neither expects a number the suite's shape
  does not produce nor believes the mechanism forbids it.
- **DEC-MCO-009:** the per-file minimum is a report, in the shape
  DEC-PM-011 gave `matcher-accuracy` and guardrail 7 requires: a flag on the
  checker that already reads the report, a threshold in `[tool.specgraph]`
  (`per_file_line_min`), a `make` target composed into neither `ci` nor
  `pre-pr`, and a non-zero exit when the list is non-empty so the friendly
  path and a future gating path cannot diverge. The threshold is in
  `pyproject.toml` and not on the command line because `_THRESHOLD_TOKEN`
  would flag `--per-file-min 85` in a recipe and because every other number
  here lives there; it is a reporting threshold and gates nothing, which its
  comment says. The flag is consumed before `parse_coverage_argv` so that
  function's `(path, scope)` contract — pinned by
  `test_coverage_argv_parses_every_accepted_shape` — stands, and so
  `check_branch_coverage.py`, which shares the parser, is untouched: that
  parser keeps the first positional as the path and drops the rest, so the
  branch checker given a trailing `--per-file-min` ignores it and gates
  normally today, and keeps doing so. The target depends on
  `coverage-run`, not on `test`, for DEC-MCO-004's reason: a report over a
  stale file misleads, Make makes the fresh one free when the run was
  already built in the same invocation, and a report that depended on the
  gate could not be read while a floor was red — exactly when it is wanted.
  Lines, not branches: W7.3 asks for modules below a line minimum, and a
  branch minimum per file would need its own data (a module with two
  branches and one covered is 50 %). Gating is a later package with its own
  reason, once the list is empty on every leg; at the measurement commit
  the list at 85 holds one module, `tools/check_branch_coverage.py`, which
  this package edits. Rejected: `coverage.py`'s own per-file `fail_under`
  (there is none — its `fail_under` is a total, Appendix B); a new script
  under `tools/` (a second reader of the same report and one more line in
  the runnable-script parametrize list for no new logic); teaching
  `parse_coverage_argv` the flag (R-MCO-11 and the Non-Goals forbid
  changing it).
- **DEC-MCO-010:** floors move to two points under the minimum green CI
  leg, per tree and per kind, computed from counts, after the first run
  that uploads the reports, and never down — D7 and the operating contract.
  From the minimum leg rather than this container because, after R-MCO-2,
  every leg enforces every floor, and the Windows leg skips
  capability-probe tests while the 3.10 leg is the oldest interpreter; a
  floor set from a Linux container's reading would turn red on the first
  Windows run. From legs whose `make test` was green only: pytest-cov
  writes the JSON report on a run with failing tests and `if: always()`
  uploads it on purpose, so a red leg's file exists and would otherwise
  pull the minimum down to a number that describes a failure rather than
  the tree; a leg with no report — one that died before `make test`, or
  whose pytest ended at collection with exit 2 and wrote none — uploads
  nothing, and `upload-artifact`'s `if-no-files-found` default of `warn`
  lets both cases contribute nothing without failing the leg a second time.
  From `covered` and `total` in the JSON, never from the checker's printed
  one-decimal percentage, because truncation of a rounded figure is a
  different number — 2850/3168 prints 90.0 and is 89.96, and `int(90.0) -
  2` is not `int(89.96) - 2`. Two under rather than at the reading because
  a floor at the measurement fails on the first honest deletion of a tested
  branch; two points is a refactor's room without hiding a regression of
  real size. Truncated to an integer because the floors are integers
  (`read_pyproject_int`). `max(current, candidate)` because a leg that
  measures below the current floor minus two is a red run to fix, never a
  reason to lower a floor. The rule is written now and the numbers later,
  because the numbers do not exist until CI produces them; a milestone
  whose figures are "expected near 97/95 and 94/91" writes the expectation
  in `tasks.md` as what the plan predicted and records what the legs said.
  Artifact names come from `runner.os` and the leg's interpreter expression
  so no literal version enters the file. Rejected: a floor per leg (five
  more keys for a property one minimum expresses); setting the floors from
  this container now (the reason above); reading the printed percentages
  (the rounding above).
- **DEC-MCO-011:** every property this package changes is read from the
  file by a test, not asserted by hand, and each guard is seen red first.
  The Makefile's shape — `coverage-run` holding the erase and the one bare
  `--cov` pytest line with `$(NO_FLOOR)`, no `--cov=` anywhere, `test`,
  `coverage-tools` and the report target each listing `coverage-run` as a
  prerequisite and running no pytest of their own, four scoped checker
  lines in `test`, the report target in neither `ci` nor `pre-pr` — is read
  from the Makefile the way `test_makefile_has_matcher_accuracy_report_target`
  reads it, through helpers the planted counter-examples call too; the
  workflow property — every job running `make test` uploads `coverage.json`
  under `if: always()` — is read through `workflow_job_blocks`; the hooks
  table's reverse property — every row names a job or a workflow — is read
  from `docs/hooks.md` and the workflow files; the mapping rule is
  exercised on planted `pyproject.toml` fixtures in the shape
  `tests/test_gate_scripts.py::_pyproject` already writes. The red runs are
  recorded in `tasks.md` with the message each guard printed and are never
  committed as a tree state (DEC-ASP-011's reason: a red commit is one the
  ladder cannot bisect past). The existing checker tests are not edited
  (C-MCO-5): their fixtures declare no `source`, so under the new rule no
  scope of theirs is a first entry and every exit code they assert is
  unchanged — which is itself the proof that the fallback is narrow.
- **DEC-MCO-012:** the saving is recorded as a measurement, before and
  after, dated with its commit — `make -n pre-pr | grep -c "python -m
  pytest"` for the count of runs and `time make pre-pr` for the wall time —
  rather than claimed from the plan's figures, and where two sessions
  measured the same commit both figures are kept: at `5246931` (the files
  of `31d7275`) the drafter's combined run took 232.9 s and the reviewer's
  230.9 s; the Appendix A durations command gave 1578 passed in 212.5 s and
  210.46 s. The durations command is recorded as W7.6's baseline and is not
  expected to move here: this package changes how often the suite runs, not
  how long one run takes. The combined-versus-two-run equality is recorded
  at the branch head in Milestone 0, because it is the premise of
  DEC-MCO-001 and a premise is re-measured where it is relied on; the
  reports in the working tree at drafting were a drafting-time reading, and
  Milestone 0's regeneration, dated at its commit, is the figure of record.
- **DEC-MCO-013:** documents that describe the design are updated; dated
  records are left. `docs/hooks.md`, `docs/architecture/c4.md`,
  `tests/AGENTS.md`, the `pyproject.toml` and `Makefile` comments and the
  comment above the scoped-floor tests in `tests/test_gate_scripts.py` say
  what the tree does and must say what it does after this change;
  `.gitignore`'s entry for `coverage-tools.json` stays with its comment
  because the file lingers in every checkout older than this change and
  `clean` still removes it; the CHANGELOG's released sections,
  `docs/next-steps.md`'s closed item, both peer reviews and the plan record
  what was true on a date and stay, under the count policy's exemption.
  `tests/AGENTS.md` is edited by replacing sentences, not adding them,
  because it sits ten lines under its budget and the budget is the point of
  the file; `docs/hooks.md`'s `test` row keeps its version-range cell
  byte-for-byte because a test parses it.

---

## Acceptance Criteria

- [x] **AC-MCO-1:** against a planted `pyproject.toml` declaring `source =
  ["openspec_graph", "tools"]` with `fail_under`, `branch_fail_under` and the
  `tools_*` keys and no `openspec_graph_*` key, both checkers under
  `--scope openspec_graph` — and under `--scope openspec_graph/`, which
  normalises to the same name — read the unscoped locators and gate the
  summed `openspec_graph/` entries against them — failing below and passing
  at the floor — while `--scope tools` reads the `tools_*` keys as before;
  and on a planted file whose first entry does carry a scoped key, the
  checkers honour that key (the misconfiguration the guard of AC-MCO-3
  exists to forbid). The tests are written with this change; until they
  exist the stage is the citation. (R-MCO-3, R-MCO-5, DEC-MCO-002,
  DEC-MCO-003)
  _Verified by:_ `pytest -k "test_the_first_source_without_a_scoped_key_reads_the_unscoped_floors or test_a_scoped_key_on_the_first_source_is_honoured_and_is_the_misconfiguration_the_guard_rejects"` · stage: `make test`

- [x] **AC-MCO-2 (non-success):** `--scope tools` on a planted file that
  declares `tools` second in `source` and carries no `tools_*` key exits 2
  from both checkers, as does a scope absent from `source`, with a message
  naming the scoped key and the first entry the unscoped locators belong
  to; `--scope openspec_graph` on a planted file whose first entry lacks
  `fail_under` (or `branch_fail_under`) exits 2 with a message naming the
  scoped key and saying the first entry's unscoped floor is absent too;
  the existing fixture, which declares no `source`, proves the exit code
  unchanged; the nothing-measured exit, every `--scope` spelling, the usage
  error and the Windows separators behave as before. The message assertions
  are new tests; until they exist the stage covers them. (R-MCO-4,
  C-MCO-5)
  _Verified by:_ `pytest -k "test_a_declared_scope_that_is_not_first_still_exits_2_without_its_key or test_the_first_source_without_its_unscoped_floor_is_named_as_absent or test_scoped_gate_fails_loudly_when_its_floor_is_not_configured or test_a_scope_matching_nothing_fails_the_gate_rather_than_passing or test_scoped_totals_normalize_windows_separators or test_coverage_argv_parses_every_accepted_shape or test_coverage_argv_rejects_a_scope_without_a_value or test_scoped_gate_reports_a_usage_error_as_exit_2"` · stage: `make test`

- [x] **AC-MCO-3 (non-success):** the real `pyproject.toml`'s first `source`
  entry carries no scoped key, and a planted `pyproject.toml` carrying one
  for its first entry is named by the guard's helper. The test is written
  with this change; until it exists the stage is the citation. (R-MCO-1,
  R-MCO-5, DEC-MCO-002)
  _Verified by:_ `pytest -k test_the_first_source_declares_no_duplicate_scoped_floor_key` · stage: `make test`

- [x] **AC-MCO-4:** `coverage_sources` reads an inline array and a
  multi-line array under `[tool.coverage.run]`, normalises `./tools/` and
  `tools/` to `tools`, ignores a `source` key under another table, does not
  read the dotted `[tool.coverage] run.source` form or `source_pkgs`, and
  returns an empty list when the file, table or key is absent; and
  `normalize_scope` maps `openspec_graph/`, `./openspec_graph` and
  `openspec_graph` to one name. The test is written with this change; until
  it exists the stage is the citation. (R-MCO-3, DEC-MCO-003)
  _Verified by:_ `pytest -k test_coverage_sources_reads_the_run_table_array_and_nothing_else` · stage: `make test`

- [x] **AC-MCO-5:** the scoped sum, the unscoped totals read, the
  scoped-versus-unscoped dilution case and the unscoped checkers' own
  floors, misconfiguration and nothing-measured exits are unchanged — every
  existing checker test passes without an edit. (R-MCO-3, R-MCO-4, C-MCO-5)
  _Verified by:_ `pytest -k "test_scoped_totals_sum_only_the_named_subtree or test_scoped_gate_fails_below_its_own_floor_and_passes_at_it or test_cov_floor_fails_below_threshold or test_cov_floor_passes_at_or_above or test_cov_floor_fails_loud_when_floor_not_configured or test_cov_floor_threshold_is_read_from_pyproject_not_hardcoded or test_branch_check_fails_below_floor or test_branch_check_passes_at_or_above_floor or test_branch_check_fails_when_no_branches_measured or test_branch_check_fails_when_floor_not_configured"` · stage: `make test`

- [x] **AC-MCO-6:** read from the Makefile: `coverage-run` is `.PHONY` and
  documented and holds the erase and the single pytest line with a bare
  `--cov`, `--cov-branch`, `--cov-fail-under=$(NO_FLOOR)` and the JSON
  report, with no `--cov=` anywhere in the file; `test`, `coverage-tools`
  and the report target each list `coverage-run` as a prerequisite and run
  no pytest; `test` runs both checkers under both scopes and
  `coverage-tools` the two `--scope tools` checks; `pre-pr` still names
  `coverage-tools`; `ci` is `test lint validate`; and `make -n pre-pr`
  prints one pytest invocation, recorded in `tasks.md`. The tests are
  written with this change; until they exist the stage is the citation.
  (R-MCO-2, R-MCO-6, C-MCO-6, DEC-MCO-001, DEC-MCO-004)
  _Verified by:_ `pytest -k "test_the_suite_runs_once_through_coverage_run or test_test_and_coverage_tools_read_the_one_report_scoped"` · stage: `make test`

- [x] **AC-MCO-7 (non-success):** through the same helpers, a planted
  Makefile text with `--cov=openspec_graph` on the pytest line, one with a
  literal floor on it, one with two pytest lines, one whose `coverage-tools`
  or `test` lacks the `coverage-run` prerequisite, and one whose `pre-pr`
  composes the report target are each named. The tests are written with
  this change; until they exist the stage is the citation. (R-MCO-13,
  DEC-MCO-011)
  _Verified by:_ `pytest -k test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named` · stage: `make test`

- [x] **AC-MCO-8:** `tools/check_no_hardcoded_thresholds.py` prints PASS on
  the finished tree at every milestone, and still fails on a planted floor
  literal in a recipe and in a workflow while ignoring `$(...)` spans and
  comments. (C-MCO-2)
  _Verified by:_ `pytest -k "test_threshold_guard_passes_on_a_clean_tree or test_threshold_guard_fails_on_a_hard_coded_coverage_floor or test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow or test_threshold_guard_ignores_comments_and_make_expansions"` · stage: `make thresholds`

- [x] **AC-MCO-9:** on the first run of the new `test` target at the branch
  head, the four scoped figures the checkers print equal the two-run figures
  measured in Milestone 0 to the line and branch, and all four checks exit
  0 with the floors unchanged; the comparison is recorded in `tasks.md`
  beside both sets of numbers. Read from the recorded output; no test can
  compare a run with a run that no longer happens. (R-MCO-2, R-MCO-15,
  C-MCO-3, DEC-MCO-001, DEC-MCO-012)
  _Verified by:_ stage: `make test`

- [x] **AC-MCO-10:** `ci.yml` has no `coverage-tools` job, `docs/hooks.md`'s
  table still lists every job that remains and — once the planned reverse
  guard exists — every row of it names a job in `ci.yml` or a workflow under
  `.github/workflows/`; every third-party `uses:` in the file — the new
  upload steps included — agrees on one pinned SHA and comment per action,
  every job keeps a timeout inside the range, no job gains a write
  permission, and no artifact name carries a pasted version literal. The
  reverse guard is cited by stage until it exists. (R-MCO-7, R-MCO-8,
  R-MCO-13, DEC-MCO-005)
  _Verified by:_ `pytest -k "test_every_hooks_ci_table_row_names_a_job_or_workflow or test_hooks_ci_table_lists_every_ci_job or test_every_reference_to_one_action_agrees_on_one_ref or test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag or test_every_job_in_every_workflow_has_a_timeout_inside_the_range or test_no_write_permission_anywhere_in_ci or test_no_quoted_python_version_literal_outside_env_and_matrix"` · stage: `make test`

- [x] **AC-MCO-11 (non-success):** every job block that runs `make test`
  uploads `coverage.json` under `if: always()`, and a planted job block that
  runs `make test` and uploads nothing is named with the job id; a planted
  `docs/hooks.md` table row naming no job in any workflow is named by the
  reverse guard's helper. The tests are written with this change; until
  they exist the stage is the citation. (R-MCO-7, R-MCO-13, DEC-MCO-005,
  DEC-MCO-010)
  _Verified by:_ `pytest -k "test_every_job_running_the_suite_uploads_its_coverage_report or test_a_suite_job_without_a_coverage_upload_is_named or test_a_hooks_row_naming_no_job_is_named"` · stage: `make test`

- [x] **AC-MCO-12:** the Windows job still runs `make lint`, `make
  typecheck` and `make test` — the same three gates as the matrix — so its
  leg gates both trees and uploads its report like every other. (R-MCO-7,
  C-MCO-6)
  _Verified by:_ `pytest -k test_ci_workflow_has_a_windows_job` · stage: `make test`

- [x] **AC-MCO-13:** `docs/hooks.md` (its `test` row's version-range cell
  intact), `docs/architecture/c4.md` §2 and §4b, the `pyproject.toml`
  comments — the hook attributed to coverage.py's own `.pth` — the
  `Makefile` comments and the `tests/test_gate_scripts.py` comment describe
  one run read scoped; `tests/AGENTS.md` does too and stays within
  `MAX_NESTED_LINES` with its precedence clause and resolving links;
  `.gitignore`'s `coverage-tools.json` entry stays; every required document
  is present and linked. The prose is read directly; the agent-file budget,
  the row-bounds parser and the docs gate are the tests. (R-MCO-1, R-MCO-8,
  DEC-MCO-008, DEC-MCO-013)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve or test_hooks_test_row_names_the_matrix_bounds"` · stage: `make docs-check`

- [x] **AC-MCO-14:** the six superseded GTC ids are named in this spec and
  in the CHANGELOG entry, `gate-tools-coverage`'s files are absent from the
  diff, and every `pytest -k` selector in every spec under
  `openspec/changes/` — that package's included — still resolves to a test
  function. (R-MCO-9, C-MCO-7, DEC-MCO-006)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make test`

- [x] **AC-MCO-15:** `add-witness-ci-artifacts`' spec and tasks carry the
  amendments R-MCO-10 describes — every site naming the job, the recording
  sites (R-WCA-28, the `ladder` bullet, AC-WCA-24, R-WCA-22, R-WCA-27), the
  run-by-name sites (R-WCA-30, AC-WCA-25, DEC-WCA-018 and the planned test)
  with their carve-out, and DEC-WCA-006 — each naming this package, with
  its dated Problem-Statement count and its proposal untouched and nothing
  else in that package changed, and that package validates clean under the
  repository's own rules after the edit, as does this one. The edits are
  read directly; the gate holds both packages. (R-MCO-10, C-MCO-7,
  DEC-MCO-007)
  _Verified by:_ stage: `make validate`

- [x] **AC-MCO-16 (non-success):** `check_coverage_floor.py --per-file-min`
  against a planted report with one module below `per_file_line_min` prints
  that module with its percentage and `covered/total`, in ascending order
  when there are two, and exits 1; with none below it prints the saying-so
  line and exits 0; with the key absent it exits 2; and under `--scope` it
  lists only that subtree. The tests are written with this change; until
  they exist the stage is the citation. (R-MCO-11, R-MCO-13, DEC-MCO-009)
  _Verified by:_ `pytest -k "test_per_file_report_names_each_module_below_the_minimum or test_per_file_report_exits_zero_when_no_module_is_below or test_per_file_report_fails_loudly_without_its_key or test_per_file_report_respects_the_scope"` · stage: `make test`

- [x] **AC-MCO-17:** the per-file report target is `.PHONY`, help-documented,
  lists `coverage-run` as its prerequisite and is composed into neither `ci`
  nor `pre-pr`, read from the Makefile in the shape of the existing
  report-target test; its output at the branch head is recorded in
  `tasks.md`. The new test is written with this change; until it exists the
  existing report-target test and the stage are the citation. (R-MCO-11,
  DEC-MCO-009)
  _Verified by:_ `pytest -k "test_makefile_has_coverage_per_file_report_target or test_makefile_has_matcher_accuracy_report_target"` · stage: `make test`

- [x] **AC-MCO-18:** `parse_coverage_argv` returns the same `(path, scope)`
  pair for every accepted shape it accepted before, the per-file flag is
  consumed by `check_coverage_floor.main` before it, and
  `check_branch_coverage.py` given a trailing `--per-file-min` ignores it
  and gates normally, exactly as it does today. The last clause is a new
  test; until it exists the existing argv test and the stage are the
  citation. (R-MCO-11, DEC-MCO-009)
  _Verified by:_ `pytest -k "test_per_file_flag_leaves_the_argv_contract_alone or test_coverage_argv_parses_every_accepted_shape"` · stage: `make test`

- [x] **AC-MCO-19 (observed after the first CI run):** the source run's
  `make test` step was green on every leg, so no leg is excluded; the
  per-leg table — run id, artifact names, `covered/total` and the exact
  percentage for both trees and both kinds on every leg — is recorded in
  `tasks.md`; each floor equals the larger of its current value and the
  minimum leg's truncated exact percentage minus two, computed from the
  counts; no floor moved down; `make thresholds` prints PASS; and the next
  CI run is green on every leg. This criterion stays unchecked until both
  runs are recorded. (R-MCO-12, C-MCO-2, C-MCO-3, DEC-MCO-010)
  _Verified by:_ stage: `make pre-pr`

- [x] **AC-MCO-20:** the rule inventory, the golden `validate`/`graph`/`rules`
  hashes and the empty runtime-dependency list are unchanged. (C-MCO-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [x] **AC-MCO-21:** both edited scripts still run as `python tools/<script>.py`
  from a throwaway cwd without a load-failure marker, and the nested
  `pytest --cov` tests and the ambient-`COVERAGE_FILE` test still reach
  their verdicts with the wider `source` in place. (R-MCO-1, C-MCO-5)
  _Verified by:_ `pytest -k "test_gate_script_is_runnable_as_a_script or test_coverage_floor_fails_below_threshold_pytest or test_coverage_floor_passes_at_threshold or test_suite_survives_an_ambient_coverage_file"` · stage: `make test`

- [x] **AC-MCO-22:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `Changed` entry with the items R-MCO-14 names, and every versioned section
  still links to its release tag. The entry is read directly; the test holds
  the link shape. (R-MCO-14)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [x] **AC-MCO-23:** `tasks.md` records, dated with the commit and naming
  the command, the before and after of `make -n pre-pr`'s pytest count and
  of `time make pre-pr`, the Appendix A durations figure as W7.6's baseline
  with both sessions' measurements, and the stage-citation report after the
  change with `coverage-tools` in the set no workflow invokes by name and
  the note that the figures include this package's own spec; no
  requirement or criterion of this spec pins a count another package
  changes; and nothing in the package claims a CLI subprocess exercises
  `tools/`. A review property, read directly; the gate confirms the package
  validates clean. (R-MCO-15, C-MCO-4, C-MCO-8, DEC-MCO-008, DEC-MCO-012)
  _Verified by:_ stage: `make validate`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-MCO-1..7, 9..12, 14, 16..18, 20..22 — the mapping rule, the Makefile, workflow and hooks-table shapes and the per-file report green on the real tree and red on their planted counter-examples; every existing checker test green unedited |
| Threshold guard | `make thresholds` | AC-MCO-8 — PASS on the finished tree at every milestone |
| Docs | `make docs-check` | AC-MCO-13 — the two-run prose replaced, the agent file within budget, every required document linked |
| Self-check | `make validate` | AC-MCO-15, 23 — this package, `add-witness-ci-artifacts` after its amendment, then the whole tree validate clean |
| Full | `make pre-pr` | AC-MCO-19 — the ladder runs the suite once and both trees' floors hold on every leg; after the first green CI run, the floors from the minimum leg |
