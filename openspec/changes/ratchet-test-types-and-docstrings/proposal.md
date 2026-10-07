# Change: Type-Check the Tests by a Per-Code Baseline, Select Public Docstrings by a Per-File Ratchet

## Why

The type gate stops at the suite's edge. `make typecheck` runs `python -m mypy
openspec_graph tools`, and `[tool.mypy] files` names the same two trees. So
every module under `tests/`, including the helpers that every spec's
verification line depends on, is type-checked by nothing. A helper whose
signature drifts from its callers is found by the test run that trips on it,
if one does, and never before. The lint gate has the matching gap one level
up. No docstring rule is selected, and the comment that says so
(`pyproject.toml:297`, "`ANN/D` -- annotation and docstring coverage in
tests; large, low-yield") gives a reason about tests and none about the
package. The package's public functions, methods and classes ship
undocumented, with nothing to say so.

Both are debts too large to clear in one change, and the plan's D1 says how
to carry them: configure at today's state, so the first commit is green and
everything not yet listed is enforced from it, and let the listed state only
shrink. This package does that for both. It holds each list to an exact
recorded count, which a guard requires to match in both directions, so the
shrinking is forced rather than remembered. `select-zero-cost-guards` already
named `D` as a family to "ratchet first … and gate when the count is zero"
(DEC-ZCG-012), and this package is that ratchet.

This is milestone M2's W6.5 (tests under mypy) and W6.6 (public docstrings by
ratchet) of the October 2026 reflection plan (`docs/reflection-plan-2026-10.md`
§4 W6 items 5 and 6; §5's M2 row; §6 D1; §7's "Tests under mypy" and "Public
symbols without a docstring" rows). It is drafted on
`claude/m2-tests-under-mypy`, stacked on #42 (`shape-the-test-suite`), whose
tier criterion, line bound and suite layout it builds on. #42's head is merged
into this branch at `d2b3cc6`.

The plan's W6.5 mechanism does not survive the tree it would run on, and the
measurements below say where.
- Adding `tests` to `files` with `explicit_package_bases = true` turns
  today's clean `tools/` run red, because explicit bases rename
  `tools/_common.py`, which every gate script imports as `_common`. It also
  changes nothing the gate runs, because the recipe's positional paths
  override `files`.
- The plan's tally predates the test-suite split and the tier work, and its
  `str` code is not a mypy code: it is the `PathLike[str]` at the end of
  note lines.
- Disabling codes for `tests.*` makes the existing inline ignores of those
  codes redundant, which strict mode reports.
- The one TOML import in `tests/` is checked on its 3.10 branch on every
  leg, so its verdict flips with whether the leg installed `tomli`.
- A count taken on Linux is not the count on Windows.

The round-1 review found two more gaps in this package's own first draft.
First, an inline ignore or a file-level `# mypy:` comment lowered a count
that the draft's guards passed. Second, a ceiling that only capped from above
was never forced down. This package takes its own baseline and answers each
of those points. The decisions that depart from the plan are named in the
spec (DEC-TDR-001, 002, 003, 004, 005, 006, 008, 010, 014).

**Evidence:** every figure below was taken on 2026-10-07, by the command its
bullet names, at `d2b3cc6` (`claude/m2-tests-under-mypy`, the first draft
with #42's head merged), unless the bullet says it was taken at `1c8917c`
(the first draft's measurement commit) or by the round-1 reviewer. The
environment, read by `python --version`, `python -m mypy --version`, `python
-m ruff --version`, `python -c "import pytest, hypothesis;
print(pytest.__version__, hypothesis.__version__)"` and `nproc`, was Python
3.13.16, mypy 2.4.0, ruff 0.16.10, pytest 9.1.1, hypothesis 6.168.5 and four
cores. `python -c "import tomli"` raises `ModuleNotFoundError`. Every mypy run
used a cache directory outside the worktree, or `--cache-dir /dev/null` where
a cold time is stated. Every time is `TIMEFORMAT='%R s'; time <command>`, and
every command was read-only on the tree. `tasks.md` Milestone 0 re-measures at
the branch head before the first edit.

- **The gate's scope, and why `files` alone does not move it.**
  `Makefile:53–54` is the target `typecheck: ## mypy with config from
  pyproject.toml — a hard gate`, with the recipe `python -m mypy
  openspec_graph tools`. `pyproject.toml:309–322` is `[tool.mypy]`, with
  `python_version = "3.10"`, `strict = true`, `warn_unreachable = true` and
  `files = ["openspec_graph", "tools"]` (line 322). mypy reads `files` only
  when no path is given on the command line, so the recipe's two positional
  paths are what the gate checks. `.github/workflows/ci.yml` runs `make
  typecheck` in the `test` matrix (line 60) and in `test-windows` (line
  108). `grep -n "runs-on" .github/workflows/ci.yml` shows `test-windows` on
  `windows-latest` and every other job, the `test` matrix among them, on
  `ubuntu-latest`, so no job runs macOS. `.pre-commit-config.yaml:18–23`
  runs it as the `specgraph-typecheck` hook with `types: [python]` and
  `pass_filenames: false`, so a staged test module already fires it.
  `python -m mypy openspec_graph tools --cache-dir /dev/null` reports
  "Success: no issues found in 43 source files", in 0.9 s.
- **Today's tests, by code.** `python -m mypy tests
  --explicit-package-bases --cache-dir <scratch>` reports "Found 185 errors
  in 32 files (checked 61 source files)". They were counted by the trailing
  code of the `error:` lines (`grep ": error:" | grep -oE "\[[a-z-]+\]$" |
  sort | uniq -c`), across sixteen codes:

  | code | count | code | count |
  |---|---|---|---|
  | `no-untyped-def` | 96 | `operator` | 2 |
  | `attr-defined` | 19 | `misc` | 2 |
  | `arg-type` | 18 | `import-not-found` | 2 |
  | `type-arg` | 16 | `call-overload` | 2 |
  | `no-any-return` | 9 | `var-annotated` | 1 |
  | `index` | 7 | `unreachable` | 1 |
  | `union-attr` | 4 | `assignment` | 1 |
  | `list-item` | 3 | | |
  | `unused-ignore` | 2 | | |

  The figures are the same as at `1c8917c`, which checked 60 source files.
  The same grep without the `": error:"` filter also counts `[str]` 4 and
  `[bytes]` 1. Those come from the `PathLike[str]` and `PathLike[bytes]` that
  close the overload signatures mypy prints as notes under
  `tests/test_graft_witness.py:107`. That is where the plan's `str` came
  from, and the briefing this package was drafted from repeated it. Without
  `--explicit-package-bases`, `python -m mypy tests` stops at
  "tests/graft_support.py: error: Source file found twice under different
  module names" and exits 2. pytest and hypothesis resolve here and ship
  `py.typed` (`_pytest/py.typed`, `hypothesis/py.typed`). So the plan's
  unresolved imports are gone, and `no-untyped-def`, `attr-defined` and
  `type-arg` now show. `pip install -e ".[dev]"` installs both on every CI
  leg, and their `Requires-Python` is `>=3.10`, as mypy's is, so no leg's
  interpreter holds either to an older release.
- **The plan's mechanism, measured.** `python -m mypy openspec_graph tools
  --explicit-package-bases --cache-dir /dev/null` reports "Found 19 errors in
  12 files (checked 43 source files)". Every gate script's `from _common
  import …` is `import-not-found`, and the values read through it become
  `no-any-return`. With `MYPYPATH=tools` added, it reports "Success: no
  issues found in 43 source files" (at `1c8917c`).

  `MYPYPATH=tools python -m mypy tests --explicit-package-bases --platform
  linux` reports "Found 184 errors in 31 files (checked 61 source files)".
  `import-not-found` falls to 1, because
  `tests/test_wheel_metadata.py:26–29`'s `sys.path.insert(0, str(TOOLS))`,
  followed by `from check_wheel_metadata import …`, now resolves statically.
  The other occurrence is `tests/support.py:84`'s `import tomllib`, which
  `python_version = "3.10"` makes missing on every leg. With all three trees
  in one run (`MYPYPATH=tools python -m mypy openspec_graph tools tests
  --explicit-package-bases`), there are 184 errors, every one under `tests/`
  (at `1c8917c`).
- **What disabling seven codes leaves, and what it creates.** The
  configuration was emulated with no file written: an INI configuration
  passed through process substitution, `python -m mypy --config-file
  <(printf '[mypy]\n…\n[mypy-tests.*]\ndisable_error_code = no-untyped-def,
  attr-defined, arg-type, type-arg, no-any-return, index, union-attr\n')
  --cache-dir /dev/null`, with `explicit_package_bases`, `mypy_path = tools`
  and `files = openspec_graph, tools, tests`. It reports "Found 23 errors in
  15 files (checked 104 source files)", in 3.6 s. Those are the fifteen
  occurrences of the nine other codes, plus eight `unused-ignore` that did
  not exist before. Each of the eight sits on an inline ignore of a code
  that is now disabled:

  | site | enclosing function | code |
  |---|---|---|
  | `tests/test_witness.py:47` | `_witness` | `arg-type` |
  | `tests/test_witness.py:95` | `test_write_witness_is_atomic` | `attr-defined` |
  | `tests/test_witness.py:110` | `test_write_witness_cleans_up_the_temp_file_and_reraises_on_write_failure` | `attr-defined` |
  | `tests/test_suite_shape.py:115` | `_registration_problems` | `attr-defined` |
  | `tests/test_rules_speckit.py:149` | `_minimal_speckit_spec` | `arg-type` |
  | `tests/test_matcher_accuracy.py:329` | `test_annotation_tier_matches_the_whole_marker_only` | `arg-type` |
  | `tests/test_stage_citations.py:233` | `test_an_unreadable_workflow_exits_two_rather_than_a_traceback.refuse` | `arg-type` |
  | `tests/test_graft_witness.py:168` | `_witness` | `arg-type` |

  The enclosing functions were read by AST over each comment token that
  `tokenize` finds, with a one-off `python -` script that writes nothing.
  `grep -n "type: ignore" tests/*.py` lists ten comments: those eight, plus
  the two that Milestone 2 removes, at `tests/support.py:86` and
  `tests/test_graft_witness.py:107`.

  A command-line `--enable-error-code arg-type` beside a per-module
  `disable_error_code = arg-type` still reports no `arg-type`. Counted with
  `grep -c` over `tests/test_mermaid.py`'s run, both runs give 0 (at
  `1c8917c`). So a per-module disable cannot be lifted from the command
  line.
- **The nine codes this package fixes, by site.**

  | code | site | enclosing function |
  |---|---|---|
  | `assignment` | `tests/shape_support.py:590` | `_class_facts` |
  | `import-not-found` | `tests/support.py:84` | `read_pyproject` |
  | `import-not-found` | `tests/test_wheel_metadata.py:29` | module level, resolved by the search path |
  | `unused-ignore` | `tests/support.py:86` | `read_pyproject` (the `tomli` import) |
  | `unused-ignore` | `tests/test_graft_witness.py:107` | `spy` in `test_current_sha_is_not_invoked_when_no_witnesses_are_present` (an `arg-type` ignore on a `call-overload`) |
  | `call-overload` | `tests/test_graft_witness.py:107` | the same line |
  | `call-overload` | `tests/test_action_contract.py:250` | `test_the_step_extractor_sees_the_whole_action` |
  | `operator` | `tests/test_suite_shape.py:555` | `test_a_mismarked_or_unmarked_planted_module_is_named` |
  | `operator` | `tests/test_cli_surface.py:203` | `test_run_cli_injects_coverage_process_start_by_default` |
  | `misc` | `tests/conftest.py:19` | `_reset_version_cache` (a generator annotated `-> None`) |
  | `misc` | `tests/test_graph.py:119` | `test_graph_covers_every_parsed_spec_when_multiple` |
  | `list-item` | `tests/test_mermaid.py:31` | `test_node_ids_are_sanitized_to_synthetic_identifiers` |
  | `list-item` | `tests/test_mermaid.py:47` | `test_node_label_combines_ident_and_text_for_requirement_nodes` |
  | `list-item` | `tests/test_mermaid.py:53` | `test_node_label_escapes_embedded_quotes` |
  | `var-annotated` | `tests/test_dialect_card.py:49` | `test_diff_cards_detects_an_adr_source_change` |
  | `unreachable` | `tests/test_finding_line_hits.py:322` | `test_section_body_still_returns_only_the_span_text` (an `assert not isinstance(result, tuple)` after an `isinstance(result, str)` that the type already guarantees) |

  Every site is from the `--platform linux` run above, with each line's
  enclosing function read by AST. `tests/support.py:88`'s `no-any-return`
  is the same reader and goes with it, so `no-any-return` is listed at one
  fewer than measured.
- **The seven listed codes, by file.** Counted from the `code` and `file`
  fields of `MYPYPATH=tools python -m mypy tests --explicit-package-bases
  --platform linux -O json --cache-dir /dev/null`:
  - `no-untyped-def`: 96 in 15 files — `test_graph.py` 24,
    `test_gate_scripts.py` 12, `test_graft_cli.py` 10,
    `test_graft_witness.py` 10, `test_graft_detection.py` 9, and ten more;
  - `attr-defined`: 19 in 7 files — `test_detect_speckit.py` 7, most of them
    `detect.subprocess`, which mypy does not see as re-exported;
  - `arg-type`: 18 in 5 files — `test_mermaid.py` 10;
  - `type-arg`: 16 in 11 files;
  - `no-any-return`: 9 in 7 files;
  - `index`: 7 in 3 files — `test_sarif.py` 5;
  - `union-attr`: 4 in 1 file, all in `test_enterprise.py`'s two
    hand-rolled `spec_from_file_location` loads.
- **Windows sees more, and the fix is clean on both.** The same JSON
  command emits 184 error objects under `--platform linux` and 188 under
  `--platform win32`. Its error lines `diff` to exactly four, all `Module has
  no attribute "mkfifo" [attr-defined]`:
  - `tests/test_detect_thresholds.py:250` and `:251`, in
    `test_a_fifo_where_a_config_file_belongs_does_not_hang`;
  - `:406`, in `test_a_fifo_where_a_spec_file_belongs_does_not_hang`;
  - `:425`, in `test_a_fifo_spec_raises_spec_read_error_rather_than_blocking`.

  These tests skip at runtime where `os.mkfifo` is absent. Under the
  override, the Windows leg's type gate would not see them either.
  `openspec_graph tools` under `--platform win32` reports no issues (at
  `1c8917c`).

  The round-1 reviewer verified a fix, and it was re-checked here. The fix
  is a module-level `_MKFIFO: Callable[[Path], None] | None = getattr(os,
  "mkfifo", None)`, then `assert _MKFIFO is not None` before the calls.
  `python -m mypy --strict --warn-unreachable --python-version 3.10
  --platform <p> -c '<that form>'`, run outside the worktree, reports
  "Success" under `linux` and under `win32`. The current form, `os.mkfifo(p)`,
  reports `attr-defined` under `win32` only. `python -m ruff check
  --stdin-filename tests/test_detect_thresholds.py -` over the form prints
  "All checks passed!": B009 does not fire on a three-argument `getattr`,
  and S101 is exempt in `tests/`. `wc -l tests/test_detect_thresholds.py`
  reads 476.
- **Suppression comments lower a count.**
  - The round-1 reviewer showed that a file-level `# mypy:
    disable-error-code=...` comment lowers `no-untyped-def` from 96 to 72.
    That figure is reproduced here with no file written: `MYPYPATH=tools
    python -m mypy tests --explicit-package-bases --platform linux -O json
    --cache-dir /dev/null --shadow-file tests/test_graph.py <(printf '#
    mypy: disable-error-code="no-untyped-def"\n'; cat tests/test_graph.py)`
    reports `no-untyped-def` 72 and 160 errors in all, with empty stderr.
  - The reviewer also showed that a new `# type: ignore[no-untyped-def,
    unused-ignore]` passed the first draft's waiver guard.
  - Running `python -m mypy -O json --strict -c '<program>'` outside the
    worktree, over a program with an untyped `def`, gives the following.
    With `# mypy: disable-error-code="no-untyped-def"` as the program's
    first line, it exits 0. With the same text on the second line of the
    module docstring, it also exits 0: mypy reads its inline configuration
    by physical line (`mypy/util.py`, `get_mypy_comments`, a line that
    starts with `# mypy: `), and no comment token is involved. Indented
    inside a function body, the comment is not honoured (exit 1).
  - A bare `# type: ignore` as the first line silences the whole program:
    an untyped `def` and a `str` assigned to an `int` both pass, exit 0. A
    bracketed one there is itself an error, "Type ignore with error code is
    not supported for modules".
  - mypy takes its inline ignores from the standard library's
    `ast.parse(..., type_comments=True).type_ignores` (`mypy/fastparse.py`),
    so `#type:ignore[...]` with no spaces counts too.
- **The guard's run, hardened.**
  - `MYPYPATH=tools python -m mypy tests --explicit-package-bases --platform
    <p> -O json --cache-dir /dev/null` writes one JSON object per stdout
    line and no summary, leaves stderr empty, and exits 1. Each object
    carries `file`, `line`, `column`, `end_line`, `end_column`, `message`,
    `hint`, `code` and `severity`. Note text is folded into `hint`, so the
    `[str]` of a note's overload signature is never a `code`.
  - The two runs take 3.7 s under `linux` and 4.1 s under `win32`.
  - `-O`/`--output` first shipped in mypy 1.11.0. mypy's `CHANGELOG.md`
    lists "Add error format support and JSON output option via `--output
    json`" (PR 11396) under Mypy 1.11. `mypy/main.py` defines `"-O",
    "--output"` at tag `v1.11.0`, and `grep -c '"--output"'` reads 0 at
    `v1.10.0`; both were fetched from the mypy repository's raw files on
    2026-10-07.
  - `pyproject.toml:244–252`'s `dev` list floors nothing. The only floors in
    the file are `requires = ["setuptools>=77"]` and `requires-python`
    (`grep -n ">=" pyproject.toml`). `setuptools>=77` is R-LM-2's floor,
    raised with the form that needed it.
  - The round-1 reviewer measured the guard-shaped run's per-code counts as
    identical on Python 3.11, 3.12 and 3.13, and on mypy 2.1.0 and 2.4.0.
- **The TOML import.** `tests/support.py:83–88` tries `import tomllib`,
  falls back to `import tomli as toml_reader  # type:
  ignore[import-not-found,no-redef]`, and returns
  `toml_reader.load(handle)`. A one-file program in the `sys.version_info >=
  (3, 11)` form, with an annotated local, is clean under `python -m mypy
  --strict --warn-unreachable` at `--python-version 3.10` and at `3.11`. A
  one-file analogue of the current form at 3.10 reports three errors, among
  them an unused `no-redef` ignore and a `no-any-return`. A `[mypy-tomli]
  ignore_missing_imports = True` section makes the 3.10-branch import silent
  with `tomli` absent. A run whose configuration carried sections that
  matched no processed module printed no warning and exited 0 (all at
  `1c8917c`).
- **Docstrings, measured.** `python -m ruff check --no-cache --isolated
  --select D100,D101,D102,D103 <tree> --statistics` gives:
  - `openspec_graph/`: 52 findings in 18 files — `D103` 30, `D102` 15,
    `D101` 7, `D100` 0 — exactly the plan's figure;
  - `tools/`: 25 findings in 12 files — `D103` 21, `D102` 4;
  - `tests/`: 584 findings in 47 files — `D103` 575, `D102` 8, `D101` 1.

  Files were counted by `--output-format concise`, path field, `sort -u`.
  Per file (the same command with `--output-format concise`):
  - `openspec_graph/`:
    - `cli.py`: `D103` 8;
    - `parse_semantics.py`: `D103` 7;
    - `parse_model.py`: `D101` 2, `D102` 4;
    - `scaffold_templates.py`: `D103` 4;
    - `scaffold.py`: `D101` 1, `D102` 1, `D103` 3;
    - `detect.py`: `D101`, `D102` and `D103`, 1 each;
    - `rule_types.py`: `D101` 2, `D102` 2;
    - `ledger.py`: `D101` 1, `D102` 1;
    - `delta.py` and `report.py`: `D102` 2 each;
    - `witness.py`: `D102` 1, `D103` 1;
    - `thresholds.py`: `D102` 1;
    - `machinery.py`, `parse.py`, `parse_harness.py`, `parse_speckit.py`,
      `parse_upstream.py` and `rules.py`: `D103` 1 each.
  - `tools/`:
    - `check_no_hardcoded_thresholds.py` and `render_plugin_manifests.py`:
      `D103` 3 each;
    - `stage_citations.py`: `D102` 1, `D103` 3;
    - `matcher_accuracy.py`: `D102` 3, `D103` 1;
    - `check_branch_coverage.py`, `check_coverage_floor.py` and
      `diff_spec_graph.py`: `D103` 2 each;
    - `check_docs.py`, `check_secrets.py`, `check_wheel_metadata.py`,
      `render_mermaid.py` and `render_rule_catalog.py`: `D103` 1 each.

  The planned guard's command over the two trees, `python -m ruff check
  --no-cache --select D100,D101,D102,D103 --config "lint.per-file-ignores =
  {}" --output-format json --exit-zero openspec_graph tools`, prints 77
  findings in 30 files, exits 0 and leaves stderr empty. The proposed
  configuration was emulated with no file written: `--config
  'lint.extend-select = ["D100","D101","D102","D103"]'`, with the thirty
  entries plus `tests/*` passed as one inline `lint.per-file-ignores`
  table. Under it, `python -m ruff check openspec_graph tests tools` prints
  "All checks passed!" and exits 0 (at `1c8917c`).
- **The convention, measured.**
  - The sorted concise output of `python -m ruff check --no-cache --isolated
    --select D100,D101,D102,D103 [--config 'lint.pydocstyle.convention =
    "<c>"'] openspec_graph tools tests` has one SHA-256 digest under no
    convention and under each of `google`, `numpy` and `pep257`, with 661
    findings each. So the setting changes no selected rule's verdict.
  - Over the wider family, `python -m ruff check --no-cache --isolated
    --select D --ignore D100,…,D107 --config 'lint.pydocstyle.convention =
    "<c>"' openspec_graph tools --statistics` reads 37 findings under Google
    (`D205` 23, `D209` 10, `D301` 4), and 67 each under `numpy` and
    `pep257`. The difference is `D401` 29 (non-imperative summaries) and
    `D400` 1.
  - Google is therefore the best fit, not a convention the docstrings
    follow: 37 findings remain under it.
- **ruff's exemptions, measured.**
  - A file entry and a matching glob entry union. Under `python -m ruff
    check --no-cache --isolated --select D103 --config 'lint.per-file-ignores
    = {…}' tools/check_docs.py`, `tools/check_docs.py`'s `D103` is reported
    under `{"tools/*" = ["T201"]}`, and not under that plus
    `{"tools/check_docs.py" = ["D103"]}` ("All checks passed!").
  - An entry that exempts nothing draws no warning: `tools/_common.py` with a
    `D103` entry and no finding prints "All checks passed!".
  - `--config 'lint.per-file-ignores = {}'` replaces the table rather than
    merging. `python -m ruff check --no-cache --config 'lint.per-file-ignores
    = {}' --select T201 openspec_graph/cli.py --statistics` reports 80
    `T201` findings.
- **What reads this configuration today.**
  - `tests/test_ci_workflow.py:37–55` holds
    `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt` (the
    `T201` keys must be exactly `openspec_graph/cli.py` and `tools/*`) and
    `test_mypy_is_strict_and_warns_on_unreachable_code` (strict,
    `warn_unreachable`, `python_version`; not `files`).
  - `tests/test_ci_workflow.py:69–104` holds two planted-tree tests that copy
    the real `pyproject.toml` and run ruff and mypy on a path given on the
    command line, so `files` is not read.
  - `tests/test_enterprise.py:225` and `:241` hold
    `test_mypy_fails_on_a_type_error` (a module under `tmp_path`, outside
    every package base) and `test_typecheck_passes_on_clean_repo` (it runs
    `make typecheck` from the repository root, so it will check `tests/`
    too).
  - `tests/test_threshold_guard.py:168` holds
    `test_threshold_guard_fails_on_a_pinned_tool_version`, which names
    `ruff==`, `mypy==` and `pytest==` in a workflow and not a `>=` bound.
  - `select-zero-cost-guards` shipped in 0.3.0 (`CHANGELOG.md:134`), and
    `specs/zero-cost-guards/spec.md` says four things about this
    configuration:
    - R-ZCG-3 (line 67) requires `[tool.mypy]` to "keep … `files =
      ["openspec_graph", "tools"]`";
    - DEC-ZCG-004 (line 188) says "The table that remains is
      `python_version`, `strict`, `warn_unreachable`, `files`";
    - C-ZCG-2 (line 143) kept `D` out of that change as a ratchet "with a
      backlog";
    - DEC-ZCG-012 (line 309) says "The sequence is ratchet first — count,
      reduce, re-count — and gate when the count is zero".

    `pyproject.toml`'s own `[tool.mypy]` comment (lines 310–318) explains
    `strict` and `warn_unreachable`, lists no table contents, and stays
    true.
  - The first draft's claim that no shipped spec recorded a decision about
    `D` came from a `grep` for `pydocstyle\|D10[0-3]\|ANN`, which misses a
    bare `` `D` ``. It was wrong, and is corrected here.
  - `shape-the-test-suite`'s C-TSS-6 forbids that package's own diff from
    widening the `tests/*` per-file-ignores.
- **Where the scope is written down.**
  - `docs/hooks.md:19` reads "`make typecheck` (mypy) across
    `openspec_graph/`, `tools/`". `:111–112` says `typecheck` runs inside the
    `test` matrix on every interpreter, which stays true.
  - `wc -l tests/AGENTS.md` reads 59, against `MAX_NESTED_LINES = 60`
    (`tests/test_agent_artifacts.py:454`).
  - `.claude/agents/planlint-verifier.md:28` still calls the configuration
    "pragmatic strictness, not `--strict`". That has been stale since
    `select-zero-cost-guards` made mypy strict.
  - `README.md:375` and `docs/aqa.md:12` say "mypy (config in
    `pyproject.toml`)", which stays true. `docs/distribution-plan.md:34`'s
    "mypy clean over 43 files" is a dated measurement, and stays.
- **The neighbourhood this package writes into.**
  - `wc -l tests/test_*.py | sort -n | tail -4` reads `test_graph.py` 647,
    `test_graft_detection.py` 658, `test_graft_rules.py` 677 and
    `test_report.py` 692, against `MAX_TEST_MODULE_LINES = 700`
    (`tests/test_suite_shape.py:44`). `wc -l` reads
    `tests/test_suite_shape.py` 555 (689 at `1c8917c`, before #42's head
    was merged) and `tests/test_ci_workflow.py` 392.
  - `make thresholds` prints "PASS: no hard-coded thresholds in Makefile or
    workflow YAML".
  - `make stage-citations` reads 52 specs, this package's own among them.
    `typecheck` is mentioned in 8 and verified by 5, and is run directly by
    `ci.yml`; `lint` is mentioned in 8 and verified by 5; `test` is
    mentioned in 49 and verified by 49.
  - The gate before this revision's first write under `openspec/`,
    `planlint --target . validate --fail-on ERROR`, exits 0: 52 specs, 0
    error / 0 warn / 0 info.

## What Changes

- `pyproject.toml` `[tool.mypy]`:
  - `files = ["openspec_graph", "tools", "tests"]`;
  - `explicit_package_bases = true` and `mypy_path = "tools"`, each with a
    comment giving its measured reason (DEC-TDR-002);
  - `strict`, `warn_unreachable` and `python_version` unchanged;
  - a `module = "tests.*"` override whose `disable_error_code` lists the
    codes of R-TDR-2 that still occur when it lands. A comment above it
    names the ratchet and the guard module that holds its ceilings and
    waivers, and states that a code leaves in the commit that fixes its
    last occurrence;
  - a `module = "tomli"` override with `ignore_missing_imports = true`,
    under a comment saying why only the 3.10 leg has it.
- `pyproject.toml` `[project.optional-dependencies] dev`: `"mypy"` becomes
  `"mypy>=1.11"`, under a comment naming 1.11 as the first release with
  `-O json` and the guard that reads it (R-TDR-16, DEC-TDR-014). No other
  entry changes.
- `pyproject.toml` `[tool.ruff.lint]`:
  - `select` gains `"D100", "D101", "D102", "D103"`, with a comment that
    records the convention measurement and its command (R-TDR-10,
    DEC-TDR-010);
  - the header sentence "every family here was at or near zero violations
    when it was turned on" is rewritten to name the four as the one
    selection made with a backlog, under per-file ratchet;
  - the "Deliberately NOT selected" comment's `ANN/D` line is rewritten as
    R-TDR-10 requires.

  `[tool.ruff.lint.per-file-ignores]`:
  - `tests/*` gains the four codes;
  - each offending file under `openspec_graph/` and `tools/` gets one entry
    listing exactly its `D` codes. That is thirty entries by the planned
    guard's command above, at `d2b3cc6`. `openspec_graph/cli.py`'s entry
    joins its `T201` entry;
  - a comment above the entries names the ratchet and its guard.

  There is no `[tool.ruff.lint.pydocstyle]` table.
- `Makefile`: the `typecheck` recipe becomes `python -m mypy`, and its help
  text says it checks the trees that `[tool.mypy] files` names. Nothing else
  changes.
- `tests/support.py`: `read_pyproject` picks `tomllib` or `tomli` by
  `sys.version_info` and returns an annotated local, and the inline ignore
  goes. The nine codes are fixed at the sites this proposal lists, by
  annotation, narrowing or a typed local, with every assertion kept, in
  `tests/conftest.py`, `tests/shape_support.py`,
  `tests/test_action_contract.py`, `tests/test_cli_surface.py`,
  `tests/test_dialect_card.py`, `tests/test_finding_line_hits.py`,
  `tests/test_graft_witness.py`, `tests/test_graph.py`,
  `tests/test_mermaid.py` and `tests/test_suite_shape.py`.
- `tests/test_detect_thresholds.py`: the four `os.mkfifo` calls go through a
  module-level `_MKFIFO: Callable[[Path], None] | None = getattr(os,
  "mkfifo", None)`, narrowed by `assert _MKFIFO is not None` in each test.
  The skip condition reads the same name, so the file type-checks the same
  under `linux` and `win32` (R-TDR-3, DEC-TDR-003).
- `tests/test_witness.py`, `tests/test_suite_shape.py`,
  `tests/test_rules_speckit.py`, `tests/test_matcher_accuracy.py`,
  `tests/test_stage_citations.py` and `tests/test_graft_witness.py`: the
  inline ignores that the override makes redundant gain `unused-ignore`
  beside their code (DEC-TDR-006). There are eight, by the emulation above
  at `d2b3cc6`.
- `tests/test_static_ratchets.py` (new), within a budget of 600 lines by
  `wc -l` at the W6.6 commit (DEC-TDR-012):
  - `MYPY_TESTS_CEILINGS`, `MYPY_WAIVERS` and `DOCSTRING_CEILINGS`, each
    under the comment stating its rule;
  - the pure helpers, each taking its input as an argument: the derived mypy
    configuration, the mypy-JSON counter, the two-platform comparison, the
    ceiling comparison, the ignore-and-mypy-comment reader with its
    enclosing-function lookup, the waiver comparison, the override-scope
    matcher, the per-file-ignores shape check and the ruff-JSON counter;
  - the guards of R-TDR-1, 2, 4, 5, 7 and 9, and the planted-input test of
    R-TDR-11, each with one tier marker, the module marking per function.
- `docs/hooks.md:19`: "`make typecheck` (mypy) across `openspec_graph/`,
  `tools/`, `tests/`", with `tests/` under its per-code baseline.
  `tests/AGENTS.md`: one sentence, replacing rather than adding, within
  `MAX_NESTED_LINES`. `.claude/agents/planlint-verifier.md`: the
  `ruff`/`mypy` bullet states the standing configuration and the ratchet
  remediation norm (R-TDR-13).
- `CHANGELOG.md` `[Unreleased]`: `### Changed — tests under mypy, public
  docstrings by ratchet (M2)`, with the items R-TDR-15 names.
- `openspec/changes/ratchet-test-types-and-docstrings/tasks.md`: the records
  that R-TDR-15 names. The verification lines of AC-TDR-3, 4, 5, 8, 9, 10,
  12, 13 and 14 are re-pointed to the guards once they exist.

## Non-Goals

- **Clearing the baseline.** No listed code is re-enabled and no docstring is
  written here. Each code leaves the override in its own later commit, which
  fixes its last occurrence, removes its ceiling and strips `unused-ignore`
  from the waivers that named it. Each docstring entry leaves in the W2 or W3
  pull request that touches its file. The plan's §7 target ("checked,
  overrides tightened to strict"; "0, `D100`–`D103` selected") is the end of
  those commits, not of this package. It is also DEC-ZCG-012's gate.
- **Anything under `openspec_graph/`.** No docstring, no re-export for the
  `attr-defined` sites that patch `detect.subprocess` or `witness.os`, no
  rule and no golden hash. `test_rule_set_matches_baseline`,
  `test_output_byte_identical` and `test_public_import_compatibility` hold
  that.
- **A new dependency or a pin.** There is no stub package (pytest and
  hypothesis ship types), no `tomli` for every interpreter, and no `==` on
  any tool. The dev extras stay unpinned by decision, and
  `test_threshold_guard_fails_on_a_pinned_tool_version` holds that. The one
  bound added is a floor on `mypy`, at the release whose output format the
  guard reads (DEC-TDR-014).
- **A workflow, composite-action or `.pre-commit-config.yaml` change.** Every
  leg and the hook already run `make typecheck`, and the hook's `types:
  [python]` already includes a test module. The occurrence guard runs the
  Windows view itself, so no leg is added.
- **A `tests/__init__.py` or `tools/__init__.py`.** Either would change how
  pytest or mypy names modules, and the search path does the job
  (DEC-TDR-002).
- **Overrides for the package, `tools/` or a third-party import.** R-TDR-2
  judges only the overrides that apply to the tests (DEC-TDR-015).
- **`ANN`, any `D` rule beyond `D100`–`D103`, or a `pydocstyle`
  convention.** mypy's `no-untyped-def` is the annotation check. The
  remaining `D` findings are formatting debt that a later package can select
  with the convention it then needs (DEC-TDR-010).
- **Docstrings in `tests/`.** They are exempt by policy, not by ratchet
  (DEC-TDR-008).
- **The stale verifier sentence's wider claim.**
  `.claude/agents/planlint-verifier.md:28` is re-worded for the mypy and
  ruff configuration this package changes. The agent's other guidance is
  W9's.
- **Editing `select-zero-cost-guards` or `shape-the-test-suite`.** The
  R-ZCG-3 clause and DEC-ZCG-004's sentence are superseded by name, C-ZCG-2
  and DEC-ZCG-012 are named as followed, and C-TSS-6 is named as not
  reversed (DEC-TDR-011). Neither package's files change.
- **More than one pull request.** There are three commits in one: W6.5,
  W6.6 and the documents, each `make pre-pr` green (DEC-TDR-013).

## Affected Capabilities

- `static-check-ratchets`
