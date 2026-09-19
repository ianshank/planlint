# Tasks: gate-tools-coverage

## Milestone 1 — Stop an ambient `COVERAGE_FILE` from ending the run  [DONE]

- `tests/support.py`: add `COVERAGE_ENV_VARS`, naming `COVERAGE_FILE`,
  `COVERAGE_PROCESS_START` and the `COV_CORE_*` family, with the comment
  recording why the set is stripped whole rather than probed — which names
  exist depends on the pytest-cov version and on whether the outer run used
  `--cov` at all (DEC-GTC-001).
- `tests/support.py`: add `env_without_coverage(**overrides)`, returning
  `os.environ` minus that family with the overrides applied on top. A
  denylist, not an allowlist (C-GTC-1). Its docstring states the failure it
  closes: the child writes statement-only data into this run's data file,
  `parallel = true` makes the outer run combine every sibling at teardown, and
  `combine` raises `DataError` from inside pytest's teardown hook —
  INTERNALERROR and exit 3, not a red test.
- `tests/test_ci_hardening.py`: switch
  `test_coverage_floor_fails_below_threshold_pytest` and
  `test_coverage_floor_passes_at_threshold` from `{**os.environ, ...}` to
  `env_without_coverage(PYTHONPATH=...)` (R-GTC-1, AC-GTC-3).
- `tests/test_ci_hardening.py`: add
  `test_suite_survives_an_ambient_coverage_file`, which runs a nested pytest
  under exactly the trap conditions — `COVERAGE_FILE` set, `--cov-branch` on
  the parent — and asserts a real verdict rather than a crash. The nested run
  pins its own `--cov-fail-under` to zero, because it measures `tools` while
  running one test that touches none of it (DEC-GTC-002, AC-GTC-2).
- `tests/test_ci_hardening.py`: add
  `test_env_without_coverage_strips_every_coverage_variable`, planting every
  name and asserting none survives, the override lands, and `PATH` is still
  there (AC-GTC-1).
- **Gate:** `make test`

## Milestone 2 — Make the four subprocess-only gate scripts measurable  [DONE]

- `tests/support.py`: add `working_directory(path)`, a context manager
  restoring the prior cwd in a `finally`. Spelled out rather than
  `contextlib.chdir`, which is 3.11+ while `requires-python` is 3.10.
- `tests/support.py`: add `run_tool_main(module_name, filename, *args, cwd,
  pass_argv0)`, calling a script's `main(argv)` in-process through the
  existing `load_tool` by-path import, optionally under a temporary cwd. Its
  docstring records why the configuration route does not reach: the coverage
  gates read `Path("pyproject.toml")` from the cwd, so their tests run from a
  throwaway directory, and coverage resolves a relative `source` entry against
  that same cwd (DEC-GTC-003, R-GTC-3).
- `tests/support.py`: `pass_argv0` as an explicit parameter, with the argv
  split named in the docstring — eight scripts take `sys.argv`, the two
  argparse ones take `sys.argv[1:]`, and the mismatch is loud in one direction
  and silent in the other (DEC-GTC-004, R-GTC-4, AC-GTC-5).
- `tests/test_ci_hardening.py`: convert the `check_branch_coverage`,
  `check_coverage_floor`, `diff_spec_graph` and `render_mermaid` tests from
  `subprocess.run` to `run_tool_main` (AC-GTC-4).
- `tests/test_ci_hardening.py`: add the parametrized
  `test_gate_script_is_runnable_as_a_script`, listing every script in
  `tools/`, run from a throwaway cwd with `env_without_coverage()`. Assert on
  the load-failure markers in stderr and on the set of documented exit codes,
  never on a specific code — exit 1 is also a valid gate verdict, and a failed
  import and a `SyntaxError` do not agree on either signal (DEC-GTC-005,
  DEC-GTC-006, AC-GTC-6).
- Record, do not act: the `sys.path.insert` bootstrap is redundant for script
  execution and load-bearing only for `load_tool`. Confirm by deleting it and
  observing the test still passes, then restore it and write the limit into
  the spec as C-GTC-2 / AC-GTC-7 rather than claiming coverage of it
  (DEC-GTC-008).
- **Gate:** `make test`

## Milestone 3 — Show the three unfired gates firing  [DONE]

- `tools/check_docs.py`: `check(root=None)` and `main(argv, root=None)`
  resolve `REPO_ROOT` at call time through the sentinel instead of binding it
  into the signature default (R-GTC-6, DEC-GTC-007). No verdict changes.
- `tools/check_secrets.py`: the same sentinel for `_tracked_files`,
  `_is_allowlisted`, `fallback_scan`, `run_gitleaks` and `main` (R-GTC-6).
- `tests/test_gate_scripts.py` (new module): `check_docs`' passing case, its
  missing-doc and present-but-unlinked verdicts, `main()` returning both codes
  in one run, and the missing-README case that must report every doc unlinked
  rather than crashing or passing (AC-GTC-8, AC-GTC-10, AC-GTC-11).
- `tests/test_gate_scripts.py`: `check_secrets`' fallback scan, one case per
  token family so a broken regex is attributable; the truncated-finding
  assertion, so the gate does not publish the secret further than the commit
  did; the vendored-but-not-`tests/` skip list; the outside-a-git-repo case;
  and all four of `main()`'s gitleaks/fallback branches, forced with
  `monkeypatch` so the gitleaks-absent path is asserted on CI too, where the
  binary is present (AC-GTC-10, AC-GTC-11). Token literals are assembled from
  fragments so this file does not itself trip `make security`.
- `tests/test_gate_scripts.py`: `render_plugin_manifests`' `--check`
  staleness, `--write` regeneration of both files, the required-mode
  enforcement, the empty-`SKILL.md` and unusable-description exits, and the
  `-v` logging case asserted through `caplog` rather than `capsys` — pytest's
  logging plugin intercepts the records before the stderr stream `capsys`
  reads (AC-GTC-10).
- `tests/test_gate_scripts.py`: `check_no_hardcoded_thresholds`' failing
  paths — a pinned floor in the Makefile, a pinned floor in a workflow, a
  pinned tool version, `GNUmakefile` dispatch, both YAML spellings, and the
  allowlist working by token rather than by vetoing whole lines (AC-GTC-12).
- **Gate:** `make test`

## Milestone 4 — Give `tools/` its own floors  [DONE]

- `tools/_common.py`: `coverage_totals` gains a `scope` parameter summing the
  per-file summaries under one directory prefix, separator-normalized so a
  coverage report written on Windows still matches; `scope=None` keeps reading
  the report's own totals unchanged (R-GTC-10).
- `tools/_common.py`: add `SCOPED_FLOOR_SECTION`, `scoped_floor_key(scope,
  kind)` and `parse_coverage_argv(argv)`, so the two checkers cannot disagree
  about where a scoped floor lives or how `--scope` is spelled, and a second
  measured tree is a config line rather than a code change (DEC-GTC-012,
  AC-GTC-16).
- `tools/check_coverage_floor.py`, `tools/check_branch_coverage.py`: accept
  `--scope NAME` and `--scope=NAME`, read the scoped floor from
  `[tool.specgraph]`, label the output with the scope, and return 2 for a
  usage error, an unconfigured floor, or a scope that matches no measured file
  (R-GTC-10, R-GTC-11, DEC-GTC-011).
- `pyproject.toml`: `[tool.specgraph] tools_line_fail_under` and
  `tools_branch_fail_under`, set to the same numbers as the package's own
  floors rather than to today's reading, with the comment saying why
  (DEC-GTC-010, R-GTC-8).
- `Makefile`: new `coverage-tools` target — `coverage erase`, then
  `pytest --cov=tools --cov-branch` with pytest-cov's own floor disabled via a
  named `NO_FLOOR` variable (a bare `0` in a recipe is indistinguishable, to
  `tools/check_no_hardcoded_thresholds.py`, from the pinned floor it exists to
  reject), then both checkers under `--scope tools`. Add it to `.PHONY` and to
  `pre-pr`, never to `ci` or `test` (R-GTC-9, C-GTC-4, DEC-GTC-013).
- `Makefile`: `clean` removes `coverage-tools.json`; `.gitignore` and
  `.dockerignore` gain it too.
- `tests/test_gate_scripts.py`: the scoped-coverage section — scoped totals
  sum only the named subtree, normalize separators, and are zero for an
  unmeasured subtree; a scope matching nothing exits 2 from both checkers; a
  report where the package is perfect and `tools/` is not fails the scoped
  gate while passing the unscoped one; a missing scoped floor exits 2; every
  accepted `--scope` spelling parses identically; `--scope` with no value is a
  usage error (AC-GTC-13, AC-GTC-14, AC-GTC-15, AC-GTC-16).
- `.github/workflows/ci.yml`: a `coverage-tools` job on one interpreter, not a
  matrix step — the scripts are stdlib-only and version-independent
  (DEC-GTC-013).
- `docs/hooks.md`: the `coverage-tools` row in the CI hooks table, plus the
  paragraph explaining why it is its own job while `typecheck` is a matrix
  step and why folding it into the test run would dilute both numbers
  (R-GTC-12, AC-GTC-17).
- **Gate:** `make coverage-tools`

## Milestone 5 — Confirm and record  [DONE]

- Read the scoped run's term-missing report and confirm the residual
  uncovered lines in the four converted scripts are their
  `if __name__ == "__main__":` guards and nothing else, so C-GTC-5 /
  AC-GTC-19 states a measured fact rather than an assumption.
- Confirm `make test`'s numbers are unchanged by this package — the package
  run still measures `--cov=openspec_graph` alone (C-GTC-4).
- Confirm this package validates clean under the repo's own rules, and that
  every `pytest -k` selector in the spec resolves to a real test function
  (`tests/test_spec_test_citations.py`).
- **Gate:** `make pre-pr`
