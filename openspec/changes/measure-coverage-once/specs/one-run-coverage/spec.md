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
diluted number. The missing piece is a mapping rule: a scope that names an
entry of `[tool.coverage.run] source` and has no scoped key reads the
unscoped locators. With it, one run writes one report, both trees are read
scoped from it, the four floors stay where they are, the matrix legs produce
the `tools/` figures on every interpreter and on Windows — which is what a
floor ratcheted from the minimum leg needs — and a per-file minimum, which
coverage.py's total cannot express, becomes a report in the same checker.

This reverses five recorded requirements of `gate-tools-coverage`, which is
on `main`, and touches the stage list of the unimplemented
`add-witness-ci-artifacts` draft; both are recorded here by name.

**Evidence:** measured at `31d7275` on `claude/m2-measure-cheaper`,
2026-10-06; each command is in the proposal. `make -n pre-pr | grep -c
"python -m pytest"` prints 2; `ci.yml` runs `make test` on five matrix legs
and `test-windows` and `make coverage-tools` in a job of its own. Against
the HEAD reports, `--scope openspec_graph` exits 2 from both checkers ("no
line floor set in pyproject.toml [tool.specgraph]
openspec_graph_line_fail_under"), the unscoped line checker reads 99.3 %
(2276/2292), and `--scope tools` reads 96.1 % (842/876) and 93.2 %
(276/296). The Appendix A combined run at the same commit reproduces those
four pairs exactly per scope while its unscoped totals read 98.4 %
(3118/3168) and 96.4 % (1020/1058); the two-run `coverage-tools.json`'s own
totals are already 2850/3168, because `run_cli`'s subprocesses measure the
config's `source`. `tools/_common.py` has `read_pyproject_int`,
`scoped_floor_key`, `coverage_totals` and `parse_coverage_argv` and no list
reader; `_read_floor` and `_read_branch_floor` map a scope to
`[tool.specgraph] <scope>_<kind>_fail_under` and nothing else.
`planlint --target . detect` reports the floor locator as
`pyproject.toml:[tool.coverage.report].fail_under`. `tools/check_no_hardcoded_thresholds.py`
would flag a literal threshold in a recipe and passes `$(NO_FLOOR)`. The
two-run design is described in `Makefile`, `ci.yml`, `docs/hooks.md`,
`docs/architecture/c4.md` §2 and §4b, `tests/AGENTS.md` and a
`pyproject.toml` comment. `test_hooks_ci_table_lists_every_ci_job` holds
every `ci.yml` job to a `docs/hooks.md` row and not the reverse.
`add-witness-ci-artifacts` is DRAFT with every criterion unchecked and no
code in the tree, and names `coverage-tools` at four sites in its spec and
tasks. `make stage-citations` reports `coverage-tools` verified by two specs
and run directly by `ci.yml`. At the plan's threshold of 85, one module is
below: `tools/check_branch_coverage.py` at 84.2 %.

---

## Requirements

- R-MCO-1: `pyproject.toml`'s `[tool.coverage.run] source` MUST list both
  measured trees, `openspec_graph` and `tools`, in that order; `branch =
  true` and `parallel = true` MUST be unchanged. The `[tool.coverage.report]
  fail_under` and `[tool.specgraph] branch_fail_under` keys MUST remain the
  package's floors and the `tools_line_fail_under` / `tools_branch_fail_under`
  keys the `tools/` floors; no other floor key MAY be added.
- R-MCO-2: The `test` recipe MUST run pytest exactly once, with a bare
  `--cov` carrying no source — no `--cov=<source>` MAY appear anywhere in the
  recipe — together with `--cov-branch`, `--cov-fail-under=$(NO_FLOOR)`,
  `--cov-report=term-missing` and `--cov-report=json:coverage.json`, after
  `python -m coverage erase`; and MUST then run `tools/check_coverage_floor.py`
  and `tools/check_branch_coverage.py` against `coverage.json` under
  `--scope openspec_graph` and under `--scope tools` — four invocations,
  each a hard step. pytest-cov's own total MUST gate nothing on this run.
- R-MCO-3: `tools/_common.py` MUST expose `coverage_sources(pyproject) ->
  list[str]`, a stdlib-only reader of the `source` array under
  `[tool.coverage.run]` — an inline or multi-line array of quoted strings,
  table-aware so a `source` key under another table is not read — returning
  `[]` when the file, table or key is absent; and `scoped_floor(pyproject,
  scope, kind) -> int | None` with `kind` in `line`/`branch`, returning the
  scoped key `<scope>_<kind>_fail_under` under `[tool.specgraph]` when it is
  present; otherwise, when `scope` is an entry of `coverage_sources`, the
  unscoped locator for that kind — `[tool.coverage.report] fail_under` for
  `line`, `[tool.specgraph] branch_fail_under` for `branch`; otherwise
  `None`. `check_coverage_floor._read_floor` and
  `check_branch_coverage._read_branch_floor` MUST read every scoped floor
  through it; their unscoped behaviour MUST be unchanged.
- R-MCO-4: A scope that is not a declared source and has no scoped key MUST
  still exit 2 from both checkers, and the message MUST name both places
  that were looked in — the scoped key and the `source` list the scope is
  absent from. The nothing-measured exit, the usage-error exit, every
  accepted `--scope` spelling and the separator normalisation MUST be
  unchanged (R-GTC-10 and R-GTC-11 stand).
- R-MCO-5: No `openspec_graph_line_fail_under` or
  `openspec_graph_branch_fail_under` key MAY exist in `pyproject.toml`. A
  guard test MUST read the real `pyproject.toml` and assert that the tree
  whose floors are the unscoped locators — the first entry of `source` —
  carries no scoped key, and MUST show on a planted `pyproject.toml` that a
  duplicate is named.
- R-MCO-6: `coverage-tools` MUST remain a `.PHONY`, help-documented target
  whose prerequisites include `test`; its recipe MUST invoke no pytest and
  MUST run both checkers under `--scope tools` against `coverage.json`, so a
  standalone invocation on a clean checkout produces the report and gates on
  it, never reading a missing or stale one. `pre-pr` MUST still name
  `coverage-tools`, `ci` MUST remain `test lint validate`, and
  `make -n pre-pr` MUST print exactly one pytest invocation.
- R-MCO-7: `.github/workflows/ci.yml` MUST no longer carry a
  `coverage-tools` job. Every job that runs `make test` — the `test` matrix
  and `test-windows` — MUST upload `coverage.json` as an artifact with
  `if: always()`, using the `actions/upload-artifact` SHA and release-tag
  comment already in the file, under a name built from `runner.os` and the
  leg's interpreter expression and carrying no version literal. No other job
  MAY change.
- R-MCO-8: `docs/hooks.md`'s CI table MUST lose the `coverage-tools` row and
  its `test` and `test-windows` rows MUST say both trees' floors are gated
  and the leg's report uploaded; its two-run paragraph, `docs/architecture/c4.md`
  §2 and §4b, `tests/AGENTS.md`'s diagram node and sentence, the
  `pyproject.toml` comments above `source`, `fail_under` and the `tools_*`
  floors, and the `Makefile`'s recipe comments MUST describe one run read
  scoped. `tests/AGENTS.md` MUST stay within `MAX_NESTED_LINES` with its
  links resolving. Dated records — `CHANGELOG.md`'s released sections,
  `docs/next-steps.md`, the peer reviews, the plan — MUST NOT be edited.
- R-MCO-9: This spec supersedes `gate-tools-coverage`'s R-GTC-9, C-GTC-4,
  R-GTC-12, DEC-GTC-009 and DEC-GTC-013, and MUST say so by name here and
  in the CHANGELOG entry; that package's files MUST NOT be edited. R-GTC-8,
  R-GTC-10, R-GTC-11, DEC-GTC-011 and DEC-GTC-012 stand; DEC-GTC-010 is
  qualified by R-MCO-12 and not reversed.
- R-MCO-10: `add-witness-ci-artifacts`' record MUST be amended at exactly
  four sites, in this package: the sentence counting the stages `ci.yml`
  runs by make-target name drops `coverage-tools`; R-WCA-27 loses its
  `coverage-tools` row and R-WCA-28's `ladder` job records `coverage-tools`
  beside `pre-pr` from the `make pre-pr` step that builds it, with the same
  exit code; DEC-WCA-016's suite-run arithmetic becomes a description of the
  set with `make -n pre-pr | grep -c "python -m pytest"` as its regenerator;
  and `tasks.md`'s recording-job list drops `coverage-tools`. Each edit MUST
  name this package. Nothing else in that package MAY change, and that
  package's `--change` validation MUST stay clean.
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
  `coverage.json`, MUST list `test` as a prerequisite, MUST be `.PHONY` and
  help-documented, and MUST be composed into neither `ci` nor `pre-pr`.
  `check_branch_coverage.py` MUST NOT gain the flag.
- R-MCO-12: After the first CI run that uploads the per-leg reports of
  R-MCO-7, the four floors MUST be set by this rule and no other: for each
  tree and kind, take the minimum over every uploaded leg of the percentage
  the scoped checker prints, truncate to an integer, subtract two, and set
  the floor to the larger of that candidate and the current floor — floors
  move up and never down. The per-leg table — run id, artifact name,
  `covered/total` and percentage for each of the four pairs on each leg —
  and the arithmetic MUST be recorded in `tasks.md` before the values move;
  the values MUST live only in `pyproject.toml`; `make thresholds` MUST
  print PASS afterwards; and the next CI run MUST be green on every leg with
  the new floors.
- R-MCO-13: Every guard this spec adds MUST read the file it judges, MUST be
  written and run red against the tree before the change it covers, with
  the red run recorded in `tasks.md` and never committed as a tree state,
  and MUST be shown red on a planted counter-example: a `pyproject.toml`
  whose declared source has no scoped key, one where a scoped key wins, one
  with a duplicate package key; a Makefile text with `--cov=openspec_graph`
  in `test`, with a literal floor, with `coverage-tools` lacking the `test`
  prerequisite, and with the report target composed into `pre-pr`; a
  workflow text with a job that runs `make test` and uploads nothing; a
  coverage report with one module below the minimum.
- R-MCO-14: `CHANGELOG.md`'s `[Unreleased]` section MUST carry a `Changed`
  entry for this package naming the one run, the mapping rule, the removed
  job and the per-leg artifacts, the five superseded GTC ids, the per-file
  report and its key, and the R7 amendment; Milestone 4 MUST append the
  floor move with its figures and run id.
- R-MCO-15: `tasks.md` MUST record, dated with the commit and naming the
  command: `make -n pre-pr | grep -c "python -m pytest"` before and after;
  `time make pre-pr` before and after; the combined report's per-scope
  figures against the two-run figures at the branch head; the per-file list
  at the branch head; and `make stage-citations` after, with
  `coverage-tools` in the set no workflow invokes by name.
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
  `pyproject.toml` fixtures those tests write declare no `source`, so their
  scopes remain undeclared and their exit codes unchanged — and the nested
  `pytest --cov` tests and the ambient-`COVERAGE_FILE` test MUST stay green,
  because they pass `--cov=<x>`, which overrides the wider `source`.
- C-MCO-6: `ci`'s prerequisites, `pre-pr`'s prerequisites, every workflow
  job name other than the removed one, the composite action and the
  Windows job's three gates MUST be unchanged.
- C-MCO-7: No file of `gate-tools-coverage` MAY change, and no file of
  `add-witness-ci-artifacts` beyond the four sites R-MCO-10 names.
- C-MCO-8: Nothing in this package MAY claim that a CLI subprocess measures
  `tools/`. The claim is checked by the per-scope equality of R-MCO-15 and
  stated as not borne out.

---

## Decisions

- **DEC-MCO-001:** one run, two scoped reads per tree, pytest-cov's total
  disabled with `$(NO_FLOOR)`, and no floor on the combined number. The
  Makefile's two-run comment protected two honest numbers from one diluted
  total; the scoped checkers protect them from one data file, which is what
  the plan's D2 says and what the Appendix A run shows: at `31d7275` the
  combined report sums per scope to exactly the two-run figures for both
  trees and both kinds, while its totals read 98.4 % and 96.4 %. The total
  is disabled rather than floored because a floor on it would be the diluted
  number the Makefile refused, and because it would be a third floor with no
  tree of its own to describe. `NO_FLOOR` already exists for the tools run
  and keeps the thresholds guard quiet; it moves to the `test` recipe with
  its comment. Rejected: a floor on the total "as a backstop" (it backs up
  nothing the scoped reads do not already check, and lowers the bar to the
  better tree's headroom); keeping `--cov=openspec_graph --cov=tools` on the
  command line rather than in `source` (pytest-cov's documentation prefers
  the config form for several sources, and a `--cov=x` on the line
  overrides it — the recipe states both facts once).
- **DEC-MCO-002:** the mapping rule is `scoped_floor` in `_common.py`, keyed
  on membership of `[tool.coverage.run] source`, with the scoped key winning
  when both exist. The scoped key first, so a future tree can be given its
  own floors by adding keys and nothing else — DEC-GTC-012's property,
  extended. The fallback only for a declared source, so a scope nobody
  measures stays the exit-2 misconfiguration R-GTC-11 made it rather than
  silently inheriting the package's floor: `source` is the one list of what
  the run measures, and a scope that is in it and has no key of its own can
  mean only one thing. The fallback targets `fail_under` and
  `branch_fail_under` because D2 rejects the duplicate key for two reasons
  that both hold against the tree: two places for one threshold is how
  `make thresholds` came to exist, and `planlint --target . detect` reports
  this repository's floor as `[tool.coverage.report].fail_under` — the key a
  duplicate would leave read by nothing but a disabled total. One function
  for both kinds, so the two checkers cannot disagree about where a floor
  lives (the drift DEC-GTC-012 named). The missing-floor message names both
  places looked, because a reader who sees only "no `x_line_fail_under`"
  would add the duplicate key this decision rejects. Rejected: a
  `[tool.specgraph] default_scope` key naming the tree that owns the
  unscoped floors (a second place to say what `source` already says);
  reading `source` with `tomllib` (absent on the 3.10 leg; the gates are
  stdlib-only and run before anything is installed, which is why
  `read_pyproject_int` is hand-rolled too).
- **DEC-MCO-003:** `coverage_sources` is a hand-rolled reader that accepts
  exactly the shape this file uses — an array of quoted strings, inline or
  spread over lines, under `[tool.coverage.run]` — and nothing else. It is
  table-aware for the reason `read_pyproject_int` is: a bare search for
  `source` would match `[tool.setuptools.dynamic]`'s `version = { attr = …
  }` neighbourhood or a comment. It returns `[]` rather than `None` for an
  absent key so the mapping rule's membership test needs no special case,
  and a `source` with one entry — today's file, and every adopter's — makes
  that entry the only tree the fallback applies to. Rejected: a general TOML
  array parser (a second parser to keep correct for one key).
- **DEC-MCO-004:** `coverage-tools` keeps its name, becomes a target that
  depends on `test`, and re-runs the two `--scope tools` checks against the
  report `test` produced. The name stays because it is a documented stage
  cited on verification lines by two shipped packages and named by `pre-pr`,
  `docs/hooks.md` and three agent files, and because the thing it names — a
  gate on `tools/`'s floors — still exists. The dependency rather than a
  bare recipe reading `coverage.json`, because a standalone `make
  coverage-tools` on a clean checkout must produce the report and a stale
  report is the thing the `erase` comment warns about; the two checks are
  re-run in its own recipe, cheaply, so the target is a complete gate on its
  own and not an alias for `test`. Inside one Make invocation `test` is
  built once, so `pre-pr` runs the suite once — measured by `make -n pre-pr`
  printing one pytest line. Rejected: a file rule `coverage.json:` with the
  sources as prerequisites, which would let `make coverage-tools` reuse a
  fresh report across invocations and stop `make test` from running when
  nothing changed — a behaviour change for every developer and a dependence
  on GNU Make's directory cache noticing a file another recipe wrote;
  deleting the target and re-pointing the citing criteria, which edits two
  shipped packages' records to remove a stage that still runs.
- **DEC-MCO-005:** the `coverage-tools` CI job is removed rather than kept.
  Its reason for existing — the suite under a different `--cov` — is gone;
  after R-MCO-2 every `make test` leg gates `tools/` too, which is the
  measurement W7.1 needs from every interpreter and from Windows, where a
  one-interpreter job could never have told us the minimum. Keeping the job
  would re-run the suite to confirm what six legs already confirmed.
  `docs/hooks.md`'s row goes with it; `test_hooks_ci_table_lists_every_ci_job`
  holds the table in one direction only, so the row's removal is a
  requirement read directly (R-MCO-8), and the stage moves into
  `make stage-citations`' set that no workflow invokes by name — recorded,
  not hidden (R-MCO-15). The per-leg upload is placed on the same jobs so
  the artifacts the ratchet reads come from the runs that gate, not from a
  job of their own.
- **DEC-MCO-006:** five records of `gate-tools-coverage` are superseded and
  named — R-GTC-9 (its own coverage run), C-GTC-4 (`make test` measures the
  package alone), R-GTC-12 (its own CI job with a `docs/hooks.md` row),
  DEC-GTC-009 and DEC-GTC-013 (the reasoning behind both) — and that
  package is not edited, because it is shipped and on `main`. The form
  follows the two precedents for a main-merged package:
  `select-zero-cost-guards`' DEC-ZCG-003 named `post-merge-quality-review`'s
  reversed criterion "so the reversal is on record, not discovered", and its
  R-ZCG-13 left `gate-tools-coverage`'s own stale count as "a shipped
  package's record"; `pin-actions-by-sha` amended `harden-ci-workflows` in
  place only because that sibling sat on the same unmerged branch. Those
  five were right when pytest-cov's total was the only floor; the scoped
  checkers that package itself shipped are what make them unnecessary, so
  the reversal is a consequence of its own work, not a disagreement with it.
  What that package still holds is listed in R-MCO-9, and its criteria stay
  true: AC-GTC-4, 13 and 19 cite `make coverage-tools`, which still exists
  and still gates `tools/`; AC-GTC-17's test still passes, because it never
  asserted the row's presence for a job that is gone. DEC-GTC-010 — floors
  set to the package's numbers rather than to today's reading — is
  qualified, not reversed: R-MCO-12 sets each tree's floors two points under
  its own minimum leg, so the two trees may end on different numbers, and
  neither is pinned at the measurement.
- **DEC-MCO-007:** `add-witness-ci-artifacts`' stage list is amended in this
  package, at four named sites, rather than this package landing after it.
  The plan prefers amending when R7 is still unimplemented, and it is:
  `Status: DRAFT`, every criterion unchecked, no recorder action and no
  `witness_dir` in the code. A draft is a plan, not a record of what
  shipped, so amending it is not the rewriting of history the precedents
  refuse; and leaving it would leave a plan that requires a job this package
  removes. The amendment is written here because this package's writes are
  confined to its own directory at drafting; the implementer applies it in
  Milestone 2 and re-validates that package. The consequence for W001 is
  stated rather than left to be found: `coverage-tools` stays cited on
  verification lines, and with no job running it by name its witness must
  come from the `ladder` job, whose `make pre-pr` builds it — so R-WCA-28
  gains the recording of `coverage-tools` from that step with the same exit
  code, and R-WCA-27 loses the row. DEC-WCA-016's count of suite runs is
  replaced by a description of the set and its regenerating command, which
  is the count policy applied to the text being amended. Rejected: landing
  after R7 (its schedule is not this package's to wait on, and the drift
  would be R7's to find); amending R7's proposal (a dated measurement).
- **DEC-MCO-008:** the subprocess hook is not claimed to measure `tools/`,
  and the plan's expectation that it would is recorded as not borne out.
  coverage.py resolves each `source` entry per process against that
  process's cwd — a directory if one exists there, a package name otherwise
  — and a CLI subprocess launched from a temporary directory has no
  `tools/` under it and imports no `tools` package (there is no
  `tools/__init__.py`; a gate script runs as `__main__`), so it measures
  `openspec_graph` by import and nothing of `tools/`; coverage's
  `process_startup` suppresses the unimported-source warning, so nothing is
  printed either. The measurement agrees: the combined run's `tools/`
  figures equal the tools run's to the line. What the wider `source` does
  change is nothing for the nested-pytest tests, which pass `--cov=<x>`, and
  nothing for `make test` run from the repository root, where both entries
  are directories. Recorded so the next reader does not expect a number the
  mechanism cannot produce.
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
  `check_branch_coverage.py`, which shares the parser, is untouched. The
  target depends on `test` for DEC-MCO-004's reason: a report over a stale
  file misleads, and Make makes the fresh one free when `test` was already
  built in the same invocation. Lines, not branches: W7.3 asks for modules
  below a line minimum, and a branch minimum per file would need its own
  data (a module with two branches and one covered is 50 %). Gating is a
  later package with its own reason, once the list is empty on every leg;
  at `31d7275` the list at 85 holds one module, `tools/check_branch_coverage.py`,
  which this package edits. Rejected: `coverage.py`'s own per-file `fail_under`
  (there is none — its `fail_under` is a total, Appendix B); a new script
  under `tools/` (a second reader of the same report and one more line in
  the runnable-script parametrize list for no new logic).
- **DEC-MCO-010:** floors move to two points under the minimum CI leg, per
  tree and per kind, after the first run that uploads the reports, and never
  down — D7 and the operating contract. From the minimum leg rather than
  this container because, after R-MCO-2, every leg enforces every floor, and
  the Windows leg skips capability-probe tests while the 3.10 leg is the
  oldest interpreter; a floor set from a Linux container's reading would
  turn red on the first Windows run. Two under rather than at the reading
  because a floor at the measurement fails on the first honest deletion of a
  tested branch; two points is a refactor's room without hiding a regression
  of real size. Truncated to an integer because the floors are integers
  (`read_pyproject_int`). `max(current, candidate)` because a leg that
  measures below the current floor minus two is a red run to fix, never a
  reason to lower a floor. The rule is written now and the numbers later,
  because the numbers do not exist until CI produces them; a milestone whose
  figures are "expected near 97/95 and 94/91" writes the expectation in
  `tasks.md` as what the plan predicted and records what the legs said.
  The uploads are `if: always()` so a red leg still yields its report, and
  named from `runner.os` and the leg's interpreter expression so no literal
  version enters the file. Rejected: a floor per leg (five more keys for a
  property one minimum expresses); setting the floors from this container
  now (the reason above).
- **DEC-MCO-011:** every property this package changes is read from the
  file by a test, not asserted by hand, and each guard is seen red first.
  The Makefile's shape — a bare `--cov`, `$(NO_FLOOR)`, four scoped checker
  lines, no `--cov=`, `coverage-tools` depending on `test` and running no
  pytest, the report target in neither `ci` nor `pre-pr` — is read from the
  Makefile the way `test_makefile_has_matcher_accuracy_report_target` reads
  it, through helpers the planted counter-examples call too; the workflow
  property — every job running `make test` uploads `coverage.json` under
  `if: always()` — is read through `workflow_job_blocks`; the mapping rule is
  exercised on planted `pyproject.toml` fixtures in the shape
  `tests/test_gate_scripts.py::_pyproject` already writes. The red runs are
  recorded in `tasks.md` with the message each guard printed and are never
  committed as a tree state (DEC-ASP-011's reason: a red commit is one the
  ladder cannot bisect past). The existing checker tests are not edited
  (C-MCO-5): their fixtures declare no `source`, so under the new rule their
  scopes are undeclared and every exit code they assert is unchanged — which
  is itself the proof that the fallback is narrow.
- **DEC-MCO-012:** the saving is recorded as a measurement, before and
  after, dated with its commit — `make -n pre-pr | grep -c "python -m
  pytest"` for the count of runs and `time make pre-pr` for the wall time —
  rather than claimed from the plan's figures. The Appendix A durations
  command is recorded too, as W7.6's baseline, and is not expected to move
  here: this package changes how often the suite runs, not how long one run
  takes. The combined-versus-two-run equality is recorded at the branch head
  in Milestone 0, because it is the premise of DEC-MCO-001 and a premise is
  re-measured where it is relied on.
- **DEC-MCO-013:** documents that describe the design are updated; dated
  records are left. `docs/hooks.md`, `docs/architecture/c4.md`,
  `tests/AGENTS.md`, the `pyproject.toml` and `Makefile` comments say what
  the tree does and must say what it does after this change; the CHANGELOG's
  released sections, `docs/next-steps.md`'s closed item, both peer reviews
  and the plan record what was true on a date and stay, under the count
  policy's exemption. `tests/AGENTS.md` is edited by replacing sentences, not
  adding them, because it sits ten lines under its budget and the budget is
  the point of the file.

---

## Acceptance Criteria

- [ ] **AC-MCO-1:** against a planted `pyproject.toml` declaring `source =
  ["openspec_graph", "tools"]` with `fail_under`, `branch_fail_under` and the
  `tools_*` keys and no `openspec_graph_*` key, both checkers under
  `--scope openspec_graph` read the unscoped locators and gate the summed
  `openspec_graph/` entries against them — failing below and passing at the
  floor — while `--scope tools` reads the `tools_*` keys as before; and when
  a scoped key and the fallback both apply, the scoped key wins. The tests
  are written with this change; until they exist the stage is the citation.
  (R-MCO-3, DEC-MCO-002)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-2 (non-success):** a scope that is not a declared source and
  has no scoped key still exits 2 from both checkers — the existing fixture,
  which declares no `source`, proves the exit code unchanged — and the
  message names the scoped key and the `source` list; the nothing-measured
  exit, every `--scope` spelling, the usage error and the Windows separators
  behave as before. The message assertion is a new test; until it exists the
  stage covers it. (R-MCO-4, C-MCO-5)
  _Verified by:_ `pytest -k "test_scoped_gate_fails_loudly_when_its_floor_is_not_configured or test_a_scope_matching_nothing_fails_the_gate_rather_than_passing or test_scoped_totals_normalize_windows_separators or test_coverage_argv_parses_every_accepted_shape or test_coverage_argv_rejects_a_scope_without_a_value or test_scoped_gate_reports_a_usage_error_as_exit_2"` · stage: `make test`

- [ ] **AC-MCO-3 (non-success):** the real `pyproject.toml` carries no
  `openspec_graph_line_fail_under` or `openspec_graph_branch_fail_under`
  key, and a planted `pyproject.toml` carrying one is named by the guard's
  helper. The test is written with this change; until it exists the stage
  is the citation. (R-MCO-1, R-MCO-5, DEC-MCO-002)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-4:** `coverage_sources` reads an inline array and a
  multi-line array under `[tool.coverage.run]`, ignores a `source` key under
  another table, and returns an empty list when the file, table or key is
  absent. The test is written with this change; until it exists the stage
  is the citation. (R-MCO-3, DEC-MCO-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-5:** the scoped sum, the unscoped totals read, the
  scoped-versus-unscoped dilution case and the unscoped checkers' own
  floors, misconfiguration and nothing-measured exits are unchanged — every
  existing checker test passes without an edit. (R-MCO-3, R-MCO-4, C-MCO-5)
  _Verified by:_ `pytest -k "test_scoped_totals_sum_only_the_named_subtree or test_scoped_gate_fails_below_its_own_floor_and_passes_at_it or test_cov_floor_fails_below_threshold or test_cov_floor_passes_at_or_above or test_cov_floor_fails_loud_when_floor_not_configured or test_cov_floor_threshold_is_read_from_pyproject_not_hardcoded or test_branch_check_fails_below_floor or test_branch_check_passes_at_or_above_floor or test_branch_check_fails_when_no_branches_measured or test_branch_check_fails_when_floor_not_configured"` · stage: `make test`

- [ ] **AC-MCO-6:** read from the Makefile: the `test` recipe runs pytest
  once with a bare `--cov`, `--cov-branch`, `--cov-fail-under=$(NO_FLOOR)`
  and the JSON report, carries no `--cov=`, and runs both checkers under
  both scopes; `coverage-tools` lists `test` as a prerequisite, runs no
  pytest and runs the two `--scope tools` checks; `pre-pr` still names
  `coverage-tools`; `ci` is `test lint validate`; and `make -n pre-pr`
  prints one pytest invocation, recorded in `tasks.md`. The tests are
  written with this change; until they exist the stage is the citation.
  (R-MCO-2, R-MCO-6, C-MCO-6, DEC-MCO-001, DEC-MCO-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-7 (non-success):** through the same helpers, a planted
  Makefile text with `--cov=openspec_graph` in `test`, one with a literal
  floor on the pytest line, one whose `coverage-tools` lacks the `test`
  prerequisite, and one whose `pre-pr` composes the report target are each
  named. The tests are written with this change; until they exist the stage
  is the citation. (R-MCO-13, DEC-MCO-011)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-8:** `tools/check_no_hardcoded_thresholds.py` prints PASS on
  the finished tree at every milestone, and still fails on a planted floor
  literal in a recipe and in a workflow while ignoring `$(...)` spans and
  comments. (C-MCO-2)
  _Verified by:_ `pytest -k "test_threshold_guard_passes_on_a_clean_tree or test_threshold_guard_fails_on_a_hard_coded_coverage_floor or test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow or test_threshold_guard_ignores_comments_and_make_expansions"` · stage: `make thresholds`

- [ ] **AC-MCO-9:** on the first run of the new `test` recipe at the branch
  head, the four scoped figures the checkers print equal the two-run figures
  measured in Milestone 0 to the line and branch, and all four checks exit
  0 with the floors unchanged; the comparison is recorded in `tasks.md`
  beside both sets of numbers. Read from the recorded output; no test can
  compare a run with a run that no longer happens. (R-MCO-2, R-MCO-15,
  C-MCO-3, DEC-MCO-001, DEC-MCO-012)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-10:** `ci.yml` has no `coverage-tools` job, `docs/hooks.md`'s
  table still lists every job that remains, every third-party `uses:` in
  the file — the new upload steps included — agrees on one pinned SHA and
  comment per action, every job keeps a timeout inside the range, no job
  gains a write permission, and no artifact name carries a pasted version
  literal. (R-MCO-7, R-MCO-8, DEC-MCO-005)
  _Verified by:_ `pytest -k "test_hooks_ci_table_lists_every_ci_job or test_every_reference_to_one_action_agrees_on_one_ref or test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag or test_every_job_in_every_workflow_has_a_timeout_inside_the_range or test_no_write_permission_anywhere_in_ci or test_no_quoted_python_version_literal_outside_env_and_matrix"` · stage: `make test`

- [ ] **AC-MCO-11 (non-success):** every job block that runs `make test`
  uploads `coverage.json` under `if: always()`, and a planted job block that
  runs `make test` and uploads nothing is named with the job id. The test is
  written with this change; until it exists the stage is the citation.
  (R-MCO-7, R-MCO-13, DEC-MCO-010)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-12:** the Windows job still runs `make lint`, `make
  typecheck` and `make test` — the same three gates as the matrix — so its
  leg gates both trees and uploads its report like every other. (R-MCO-7,
  C-MCO-6)
  _Verified by:_ `pytest -k test_ci_workflow_has_a_windows_job` · stage: `make test`

- [ ] **AC-MCO-13:** `docs/hooks.md`, `docs/architecture/c4.md` §2 and §4b,
  the `pyproject.toml` and `Makefile` comments describe one run read
  scoped; `tests/AGENTS.md` does too and stays within `MAX_NESTED_LINES`
  with its precedence clause and resolving links; every required document
  is present and linked. The prose is read directly; the agent-file budget
  and the docs gate are the tests. (R-MCO-8, DEC-MCO-013)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve"` · stage: `make docs-check`

- [ ] **AC-MCO-14:** the five superseded GTC ids are named in this spec
  and in the CHANGELOG entry, `gate-tools-coverage`'s files are absent from
  the diff, and every `pytest -k` selector in every spec under
  `openspec/changes/` — that package's included — still resolves to a test
  function. (R-MCO-9, C-MCO-7, DEC-MCO-006)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make test`

- [ ] **AC-MCO-15:** `add-witness-ci-artifacts`' spec and tasks carry the
  four amendments R-MCO-10 names, each naming this package, nothing else in
  that package changed, and that package validates clean under the
  repository's own rules after the edit, as does this one. The edits are
  read directly; the gate holds both packages. (R-MCO-10, C-MCO-7,
  DEC-MCO-007)
  _Verified by:_ stage: `make validate`

- [ ] **AC-MCO-16 (non-success):** `check_coverage_floor.py --per-file-min`
  against a planted report with one module below `per_file_line_min` prints
  that module with its percentage and `covered/total`, in ascending order
  when there are two, and exits 1; with none below it prints the saying-so
  line and exits 0; with the key absent it exits 2; and under `--scope` it
  lists only that subtree. The tests are written with this change; until
  they exist the stage is the citation. (R-MCO-11, R-MCO-13, DEC-MCO-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-MCO-17:** the per-file report target is `.PHONY`, help-documented,
  lists `test` as a prerequisite and is composed into neither `ci` nor
  `pre-pr`, read from the Makefile in the shape of the existing
  report-target test; its output at the branch head is recorded in
  `tasks.md`. The new test is written with this change; until it exists the
  existing report-target test and the stage are the citation. (R-MCO-11,
  DEC-MCO-009)
  _Verified by:_ `pytest -k test_makefile_has_matcher_accuracy_report_target` · stage: `make test`

- [ ] **AC-MCO-18:** `parse_coverage_argv` returns the same `(path, scope)`
  pair for every accepted shape it accepted before, and the per-file flag
  is consumed by `check_coverage_floor.main` before it — so
  `check_branch_coverage.py` is unchanged in its argument handling.
  (R-MCO-11, DEC-MCO-009)
  _Verified by:_ `pytest -k test_coverage_argv_parses_every_accepted_shape` · stage: `make test`

- [ ] **AC-MCO-19 (observed after the first CI run):** the per-leg table —
  run id, artifact names, `covered/total` and percentage for both trees and
  both kinds on every leg — is recorded in `tasks.md`; each floor equals the
  larger of its current value and the minimum leg's truncated percentage
  minus two; no floor moved down; `make thresholds` prints PASS; and the
  next CI run is green on every leg. This criterion stays unchecked until
  the run is recorded. (R-MCO-12, C-MCO-2, C-MCO-3, DEC-MCO-010)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-MCO-20:** the rule inventory, the golden `validate`/`graph`/`rules`
  hashes and the empty runtime-dependency list are unchanged. (C-MCO-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [ ] **AC-MCO-21:** both edited scripts still run as `python tools/<script>.py`
  from a throwaway cwd without a load-failure marker, and the nested
  `pytest --cov` tests and the ambient-`COVERAGE_FILE` test still reach
  their verdicts with the wider `source` in place. (R-MCO-1, C-MCO-5)
  _Verified by:_ `pytest -k "test_gate_script_is_runnable_as_a_script or test_coverage_floor_fails_below_threshold_pytest or test_coverage_floor_passes_at_threshold or test_suite_survives_an_ambient_coverage_file"` · stage: `make test`

- [ ] **AC-MCO-22:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `Changed` entry with the items R-MCO-14 names, and every versioned section
  still links to its release tag. The entry is read directly; the test holds
  the link shape. (R-MCO-14)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [ ] **AC-MCO-23:** `tasks.md` records, dated with the commit and naming
  the command, the before and after of `make -n pre-pr`'s pytest count and
  of `time make pre-pr`, the Appendix A durations figure as W7.6's baseline,
  and the stage-citation report after the change with `coverage-tools` in
  the set no workflow invokes by name; no requirement or criterion of this
  spec pins a count another package changes. A review property, read
  directly; the gate confirms the package validates clean. (R-MCO-15,
  C-MCO-4, C-MCO-8, DEC-MCO-008, DEC-MCO-012)
  _Verified by:_ stage: `make validate`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-MCO-1..7, 9..12, 14, 16..18, 20..22 — the mapping rule, the Makefile and workflow shapes and the per-file report green on the real tree and red on their planted counter-examples; every existing checker test green unedited |
| Threshold guard | `make thresholds` | AC-MCO-8 — PASS on the finished tree at every milestone |
| Docs | `make docs-check` | AC-MCO-13 — the two-run prose replaced, the agent file within budget, every required document linked |
| Self-check | `make validate` | AC-MCO-15, 23 — this package, `add-witness-ci-artifacts` after its amendment, then the whole tree validate clean |
| Full | `make pre-pr` | AC-MCO-19 — the ladder runs the suite once and both trees' floors hold; after the first CI run, the floors from the minimum leg |
