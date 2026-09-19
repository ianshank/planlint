# Change: Cover the `tools/` Gate Scripts and Give Them Their Own Floors

## Why

The scripts under `tools/` are what `make pre-pr` and every CI job actually
run. Seven of them were, in coverage terms, unexamined: four read 0% while
being thoroughly tested, and three had never been shown to *fire* at all —
the untested region in each was its `main()`, which is the decision itself. A
gate that cannot be shown to fail is worse than no gate, because it reports
PASS on the thing it was added to catch.

Underneath that sat a second defect of a different kind: an inherited
`COVERAGE_FILE` did not fail a test, it destroyed the run.

**Evidence:**

- **The ambient-`COVERAGE_FILE` crash.** `tests/test_ci_hardening.py`'s
  `test_coverage_floor_fails_below_threshold_pytest` and
  `test_coverage_floor_passes_at_threshold` each spawn a nested `pytest --cov`
  to prove pytest-cov's own `--cov-fail-under` gate fires. Both built the
  child environment as `{**os.environ, ...}`, so the child inherited
  `COVERAGE_FILE` and wrote statement-only data (it has no `--cov-branch`)
  into this run's data file. `pyproject.toml` sets
  `[tool.coverage.run] parallel = true`, so the outer run combines every
  sibling data file at teardown and `combine` raises
  `DataError: Can't combine branch coverage data with statement data` from
  inside pytest's own teardown hook: INTERNALERROR, exit 3, the entire suite
  lost with no test marked red. Nothing in this repository sets
  `COVERAGE_FILE` — not the `Makefile`, not `.github/workflows/ci.yml`, not
  `pyproject.toml` — so the trap is entirely ambient. It springs for anyone
  whose CI names a per-leg coverage data file, which is the standard way to
  keep a build matrix's coverage separate.
- **Four scripts at 0%.** `tools/check_branch_coverage.py`,
  `tools/check_coverage_floor.py`, `tools/diff_spec_graph.py` and
  `tools/render_mermaid.py` were exercised only through `subprocess.run`, and
  a subprocess's execution is invisible to coverage. Handing the child the
  coverage config would not have fixed it: the two coverage gates read
  `Path("pyproject.toml")` from the cwd (see `check_coverage_floor.main`), so
  their tests run them from a throwaway directory — and coverage resolves a
  *relative* `source` entry against that same cwd, so `source = ["tools"]`
  would resolve to a `tools` directory inside the fixture that does not
  exist. In-process invocation moved the four to 89%, 82%, 95% and 89%.
- **Three scripts never shown to fire.** `tools/check_docs.py` (29%),
  `tools/check_secrets.py` (52%) and `tools/render_plugin_manifests.py` (57%)
  had their `main()` uncovered. Testability came first: `check_docs` and
  `check_secrets` bound `REPO_ROOT` into signature defaults, which Python
  evaluates at definition time, so a caller reassigning the module constant
  changed nothing and the gate logic could only ever be run against the
  directory the module was imported from. The three now read 95%, 92% and
  97%.
- **`tools/` had no floor of its own.** `pyproject.toml`'s
  `[tool.coverage.report] fail_under` and `[tool.specgraph] branch_fail_under`
  gate `make test`, which measures `--cov=openspec_graph` only. Nothing held
  the gate machinery to any bar at all.

## What Changes

- `tests/support.py`: new `COVERAGE_ENV_VARS` tuple and
  `env_without_coverage(**overrides)`, returning `os.environ` with the whole
  `COVERAGE_*` / `COV_CORE_*` family removed and the overrides applied on top.
  Stripped whole rather than probed: which names are present depends on the
  pytest-cov version and on whether the outer run used `--cov` at all, and
  removing an unset name is a no-op. A denylist, not an allowlist —
  everything unrelated survives.
- `tests/support.py`: new `run_tool_main(module_name, filename, *args, cwd,
  pass_argv0)`, which calls a `tools/` script's `main(argv)` in-process
  through the existing `load_tool` by-path import, optionally under a
  temporary cwd. `pass_argv0` is explicit rather than assumed because
  `tools/` is split on the argv convention: eight scripts index `argv[1]` and
  are invoked `main(sys.argv)`, while the two argparse ones
  (`render_plugin_manifests`, `render_rule_catalog`) are invoked
  `main(sys.argv[1:])`. Passing the wrong one is not quiet in either
  direction — argparse rejects the stray filename, and a hand-rolled script
  silently drops the first real argument.
- `tests/support.py`: new `working_directory(path)` context manager, spelled
  out rather than `contextlib.chdir` because that is 3.11+ and this project's
  `requires-python` is 3.10; it restores in a `finally` so a failing
  assertion cannot strand the session in a deleted temporary directory.
- `tests/test_ci_hardening.py`: the two nested-coverage tests build their
  child environment through `env_without_coverage(...)`; new
  `test_suite_survives_an_ambient_coverage_file` runs a nested pytest under
  exactly the conditions that spring the trap and asserts a real verdict
  rather than a crash; new
  `test_env_without_coverage_strips_every_coverage_variable`. The
  `check_branch_coverage`, `check_coverage_floor`, `diff_spec_graph` and
  `render_mermaid` tests move from `subprocess.run` to `run_tool_main`. One
  new parametrized `test_gate_script_is_runnable_as_a_script` covers the
  `python tools/<script>.py` invocation contract for all eleven scripts at
  once — it asserts on load-failure markers in stderr, not on exit code,
  because a failed import prints `Traceback (most recent call last)` while a
  `SyntaxError` does not, and both exit 1, which is also a documented code
  here meaning the gate found a violation.
- `tools/check_docs.py`, `tools/check_secrets.py`: every `root` parameter
  defaults through a `None` sentinel and resolves to `REPO_ROOT` at call
  time. Backwards compatible — a caller passing no root behaves exactly as
  before.
- `tests/test_gate_scripts.py` (new module): the gate scripts' own decision
  logic, in-process. `check_docs`'s missing-vs-unlinked verdicts and its
  missing-README case; `check_secrets`'s per-token-family scan, its
  vendored-but-not-`tests/` skip list, its truncated finding, and each of
  `main()`'s four gitleaks/fallback branches; `render_plugin_manifests`'s
  `--check` staleness, `--write` regeneration, required-mode enforcement and
  unusable-description rejections; `check_no_hardcoded_thresholds`'s failing
  paths; and the scoped-coverage behaviour below.
- `tools/_common.py`: `coverage_totals` gains a `scope` parameter that sums
  the per-file summaries under one directory prefix instead of reading the
  report's own totals, separator-normalized so a Windows-spelled path still
  matches; new `SCOPED_FLOOR_SECTION`, `scoped_floor_key` and
  `parse_coverage_argv`, so the two checkers cannot disagree about where a
  scoped floor lives or how `--scope` is spelled.
- `tools/check_coverage_floor.py`, `tools/check_branch_coverage.py`: both
  accept `--scope NAME` (and `--scope=NAME`), read the scoped floor from
  `[tool.specgraph]`, and label their output with the scope. A scope matching
  no measured file, and a scoped floor absent from config, are each exit 2 —
  misconfiguration, never a vacuous pass.
- `pyproject.toml`: `[tool.specgraph] tools_line_fail_under` and
  `tools_branch_fail_under`, set to the same numbers as the package's own
  floors rather than to today's reading.
- `Makefile`: new `coverage-tools` target — its own `coverage erase` +
  `pytest --cov=tools --cov-branch` run with pytest-cov's `--cov-fail-under`
  disabled via a named `NO_FLOOR` variable, then the two checkers under
  `--scope tools`. Composed into `pre-pr`, not into `ci`. `clean` removes
  `coverage-tools.json`.
- `.github/workflows/ci.yml`: a dedicated `coverage-tools` job on one
  interpreter rather than a step in the version matrix — the scripts are
  stdlib-only and version-independent, so one leg is the whole answer.
- `docs/hooks.md`: the `coverage-tools` row in the CI hooks table, plus the
  paragraph explaining why it is its own job while `typecheck` is a matrix
  step; `.gitignore` and `.dockerignore` gain `coverage-tools.json`.

## Non-Goals

- **No new rule.** The `RULES` tuple in `openspec_graph/rules.py` and
  `README.md`'s rules table are untouched; nothing here is a spec-quality
  finding. `tests/baseline_rules.json` is unchanged.
- **No change to what any gate script decides.** Every behaviour asserted by
  the new tests is the behaviour that was already there; the change is that
  it is now asserted. The one source edit to a decision path is the root
  sentinel, which is deliberately behaviour-preserving for every existing
  caller.
- **No folding of `tools/` into `make test`'s coverage run.** pytest-cov's
  `--cov-fail-under` applies to the combined total of everything measured, so
  adding `--cov=tools` there would replace two honest per-tree numbers with
  one diluted number — and the diluted one is what the gate would then
  enforce.
- **No removal of the `sys.path.insert` bootstrap** from the nine scripts
  that import `_common`. It is redundant for script execution (Python already
  puts the script's own directory on `sys.path[0]`) and load-bearing only for
  `load_tool`'s by-path import, and deleting it does *not* fail the
  runnable-as-a-script test. Removing it is a separate change with its own
  argument; this one records the limit rather than acting on it.
- **No coverage floor for the `tests/` tree itself**, and no third scope. The
  scoped-floor mechanism is derived (`scoped_floor_key`) rather than
  hard-listed so a second measured tree is a config line, but adding one is
  not this change.
- **No change to `run_cli()`** or to `COVERAGE_PROCESS_START`, which
  `fix-subprocess-coverage-blind-spot` established for the CLI subprocesses
  and which stays exactly as it was. `env_without_coverage` is for the
  opposite case: a child that runs its *own* coverage session.

## Affected Capabilities

- `gate-script-coverage`
