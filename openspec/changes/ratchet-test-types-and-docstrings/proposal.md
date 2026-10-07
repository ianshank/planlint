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
`claude/m2-tests-under-mypy`, whose base is `main` at `46ae1b3`, where #42
(`shape-the-test-suite`) was squash-merged. It builds on that package's tier
criterion, line bound and suite layout.

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
was never forced down. The round-2 review found more ways to lower a count
unseen: a ruff `noqa` comment or an `extend-per-file-ignores` entry; an
override pattern the draft's matcher would have misjudged; a stub,
`no_type_check`, a `TYPE_CHECKING` branch or a global `exclude`; and a stray
`mypy.ini` or `.mypy.ini`, which mypy reads ahead of `pyproject.toml`. The
round-3 review found that a pattern matcher still misreads override
spellings mypy applies, that a run over `tests` alone is not the gate's run,
that version and platform checks hide code, that an ignore file hides a
module from ruff, and that a function-keyed waiver can be re-pointed. This
package takes its own baseline and answers each of those points, and
DEC-TDR-017 says what the guards defend against and what they leave to
review. The decisions that depart from the plan are named in the spec
(DEC-TDR-001, 002, 003, 004, 005, 006, 008, 010, 014, 016).

**Evidence:** every figure below was taken on 2026-10-07 at `e558eba`, the
head of `claude/m2-tests-under-mypy`, whose base is `main` at `46ae1b3`, by
the command its bullet names, unless the bullet says otherwise. A bullet
marked "at `25c65de`" was taken for the round-3 revision at that commit,
which is the round-2 revision of this package committed on `e558eba`; the
headline counts re-taken there (184 test errors in a gate-shaped Linux run,
188 under win32, 77 docstring findings in 30 files) are unchanged. The first
draft was measured at `1c8917c` and the round-1 revision at `d2b3cc6`.
Neither is an ancestor of the branch, which was rebuilt on `46ae1b3` after
#42 merged. `git diff d2b3cc6 HEAD --
':!openspec/changes/ratchet-test-types-and-docstrings'` was empty at
`e558eba` when the round-2 revision was handed over, and every headline mypy
and ruff figure re-taken then equals its `d2b3cc6` value. A figure kept from
an earlier commit says so, and why. The environment, read by `python
--version`, `python -m mypy --version`, `python -m ruff --version`, `python
-c "import pytest, hypothesis; print(pytest.__version__,
hypothesis.__version__)"` and `nproc`, was Python 3.13.16, mypy 2.4.0, ruff
0.16.10, pytest 9.1.1, hypothesis 6.168.5 and four cores. `python -c "import
tomli"` raises `ModuleNotFoundError`. Where a bullet names mypy 1.11.0 or
1.10.1, the run used the round-2 reviewer's scratch environments; the
round-3 reviewer's probe configurations are cited by file name. Every mypy
run used `--cache-dir /dev/null` or a cache directory outside the worktree.
Every time is `TIMEFORMAT='%R s'; time <command>` or Python's
`time.monotonic()` around the run. Every command was read-only on the tree;
the probes that needed a file on disk wrote it to a scratch directory
outside the worktree. `tasks.md` Milestone 0 re-measures at the branch head
before the first edit.

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
  `ubuntu-latest`, so no job runs macOS. `ci.yml` runs on `pull_request`,
  and on `push` only to `main` and `master`. `.pre-commit-config.yaml:18–23`
  runs it as the `specgraph-typecheck` hook with `types: [python]` and
  `pass_filenames: false`, so a staged test module already fires it.
  `python -m mypy openspec_graph tools --cache-dir /dev/null` reports
  "Success: no issues found in 43 source files", in 0.9 s. `python -m mypy
  --config-file pyproject.toml --cache-dir /dev/null`, the planned recipe's
  form, reads `files` and reports the same, in 1.0 s, exit 0.
- **Today's tests, by code.** `python -m mypy tests
  --explicit-package-bases --cache-dir /dev/null` reports "Found 185 errors
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
  issues found in 43 source files", and so it does with `--platform win32`.

  `MYPYPATH=tools python -m mypy tests --explicit-package-bases --platform
  linux --cache-dir /dev/null` reports "Found 184 errors in 31 files
  (checked 61 source files)". `import-not-found` falls to 1, because
  `tests/test_wheel_metadata.py:26–29`'s `sys.path.insert(0, str(TOOLS))`,
  followed by `from check_wheel_metadata import …`, now resolves statically.
  The other occurrence is `tests/support.py:84`'s `import tomllib`, which
  `python_version = "3.10"` makes missing on every leg. With all three trees
  in one run (`MYPYPATH=tools python -m mypy openspec_graph tools tests
  --explicit-package-bases --platform linux`), it reports "Found 184 errors
  in 31 files (checked 104 source files)", every one under `tests/`.
- **What disabling seven codes leaves, and what it creates.** The
  configuration was emulated with no file written: an INI configuration
  passed through process substitution, `python -m mypy --config-file
  <(printf '[mypy]\n…\n[mypy-tests.*]\ndisable_error_code = no-untyped-def,
  attr-defined, arg-type, type-arg, no-any-return, index, union-attr\n')
  --cache-dir /dev/null`, with `explicit_package_bases`, `mypy_path = tools`,
  a `[mypy-tomli]` section and `files = openspec_graph, tools, tests`. It
  reports "Found 23 errors in 15 files (checked 104 source files)", in 3.7
  s. Those are the fifteen occurrences of the nine other codes, plus eight
  `unused-ignore` that did not exist before. Each of the eight sits on an
  inline ignore of a code that is now disabled. Their waiver keys, the
  waived line's text with the comment removed and whitespace collapsed,
  were read at `25c65de` by `tokenize` with a one-off `python -I -c` script
  that writes nothing:

  | site | enclosing function | waived line, as keyed | code |
  |---|---|---|---|
  | `tests/test_witness.py:47` | `_witness` | `return Witness(**fields)` | `arg-type` |
  | `tests/test_witness.py:95` | `test_write_witness_is_atomic` | `monkeypatch.setattr(witness.os, "replace", spy_replace)` | `attr-defined` |
  | `tests/test_witness.py:110` | `test_write_witness_cleans_up_the_temp_file_and_reraises_on_write_failure` | `monkeypatch.setattr(witness.os, "replace", boom)` | `attr-defined` |
  | `tests/test_suite_shape.py:115` | `_registration_problems` | `entries = [str(entry) for entry in options.get("markers", [])]` | `attr-defined` |
  | `tests/test_rules_speckit.py:149` | `_minimal_speckit_spec` | `return parse_model.ParsedSpec(**defaults)` | `arg-type` |
  | `tests/test_matcher_accuracy.py:329` | `test_annotation_tier_matches_the_whole_marker_only` | `assert negation_matches(None, None) == ()` | `arg-type` |
  | `tests/test_stage_citations.py:233` | `test_an_unreadable_workflow_exits_two_rather_than_a_traceback.refuse` | `return original(self, *args, **kwargs)` | `arg-type` |
  | `tests/test_graft_witness.py:168` | `_witness` | `return witness.Witness(**fields)` | `arg-type` |

  The enclosing functions were read at `d2b3cc6` by AST, and the tree
  outside this package is unchanged since. `grep -n "type: ignore"
  tests/*.py` lists ten comments: those eight, plus the two that Milestone 2
  removes, at `tests/support.py:86` and `tests/test_graft_witness.py:107`.
  All ten keys are distinct, and no waived line's text occurs twice in its
  file.

  A command-line `--enable-error-code arg-type` beside a per-module
  `disable_error_code = arg-type` still reports no `arg-type`. Counted with
  `grep -c` over `tests/test_mermaid.py`'s run, both runs give 0, against 10
  with no override. So a per-module disable cannot be lifted from the
  command line.
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
  `--platform win32`. Compared by (file, line, code, message), the error
  sets differ by exactly four, all `Module has no attribute "mkfifo"
  [attr-defined]` and all Windows-only:
  - `tests/test_detect_thresholds.py:250` and `:251`, in
    `test_a_fifo_where_a_config_file_belongs_does_not_hang`;
  - `:406`, in `test_a_fifo_where_a_spec_file_belongs_does_not_hang`;
  - `:425`, in `test_a_fifo_spec_raises_spec_read_error_rather_than_blocking`.

  These tests skip at runtime where `os.mkfifo` is absent. Under the
  override, the Windows leg's type gate would not see them either.

  The round-1 reviewer verified a fix, and it was re-checked in the round-1
  revision by programs run outside the worktree. The fix is a module-level
  `_MKFIFO: Callable[[Path], None] | None = getattr(os, "mkfifo", None)`,
  then `assert _MKFIFO is not None` before the calls. `python -m mypy
  --strict --warn-unreachable --python-version 3.10 --platform <p> -c '<that
  form>'` reports "Success" under `linux` and under `win32`. The current
  form, `os.mkfifo(p)`, reports `attr-defined` under `win32` only. `python
  -m ruff check --stdin-filename tests/test_detect_thresholds.py -` over the
  form prints "All checks passed!": B009 does not fire on a three-argument
  `getattr`, and S101 is exempt in `tests/`. `wc -l
  tests/test_detect_thresholds.py` reads 476.
- **Suppression comments lower a count.**
  - The round-1 reviewer showed that a file-level `# mypy:
    disable-error-code=...` comment lowers `no-untyped-def` from 96 to 72.
    That figure is reproduced here with no file written: `MYPYPATH=tools
    python -m mypy tests --explicit-package-bases --platform linux -O json
    --cache-dir /dev/null --shadow-file tests/test_graph.py <(printf '#
    mypy: disable-error-code="no-untyped-def"\n'; cat tests/test_graph.py)`
    reports `no-untyped-def` 72 and 160 errors in all.
  - The reviewer also showed that a new `# type: ignore[no-untyped-def,
    unused-ignore]` passed the first draft's waiver guard.
  - A `# mypy: ` line inside a docstring is honoured by some releases and
    parsers, and not by others. Over a probe module whose docstring's second
    line is `# mypy: disable-error-code="no-untyped-def"` and whose only
    error is an untyped `def`, `python -m mypy --strict --cache-dir
    /dev/null <file>`, from a scratch directory outside the worktree,
    reports the error under mypy 2.4.0's default parser, and reports
    "Success" under 2.4.0 with `--no-native-parser`, under 2.4.0 with the
    module passed by `-c` or by `--shadow-file`, and under mypy 1.11.0; a
    control module without the line reports the error under all of them.
    The same line, inserted by `--shadow-file` as `tests/test_graph.py`'s
    docstring's second line, lowers `no-untyped-def` from 96 to 72 under
    2.4.0 and under 1.11.0. mypy reads its inline configuration by physical
    line where the source reaches it whole (`mypy/util.py`,
    `get_mypy_comments`, a line that starts with `# mypy: `). So whether
    such a line counts depends on the release, and the `>=1.11` floor this
    package adds admits 1.11.0, which honours it. Indented inside a
    function body, the comment is not honoured (round-1 revision, `-c`,
    exit 1).
  - A bare `# type: ignore` as the first line silences the whole program:
    an untyped `def` and a `str` assigned to an `int` both pass, exit 0,
    against `no-untyped-def` and `assignment` and exit 1 without it
    (`python -m mypy -O json --strict --cache-dir /dev/null -c …`, outside
    the worktree). A bracketed one there is itself an error, "Type ignore
    with error code is not supported for modules".
  - mypy takes its inline ignores from the standard library's
    `ast.parse(..., type_comments=True).type_ignores` (`mypy/fastparse.py`),
    so `#type:ignore[...]` with no spaces counts too.
- **Counts lowered with no comment.**
  - `python -m mypy --strict --warn-unreachable --python-version 3.10
    --platform linux --cache-dir /dev/null -c …`, outside the worktree,
    reports `no-untyped-def` for a program holding one untyped `def` (exit
    1). The same `def` under `@typing.no_type_check` passes (exit 0).
  - At `25c65de`, the same command, run under mypy 2.4.0 and 1.11.0, passes
    ("Success") for an untyped `def` under each of `if sys.version_info >=
    (3, 11):`, `MYPY = False` then `if not MYPY:`, `if sys.platform ==
    "darwin":`, `if sys.version_info < (3, 10):`, `if
    sys.platform.startswith("darwin"):`, `if sys.version_info[0] < 3:`,
    `if PY2:`, `if not PY3:`, a `match` case guard `if sys.platform ==
    "darwin"` and a module-level `assert sys.platform == "darwin"`. Under
    `x = True` then `if x and sys.version_info < (3, 10):` it passes on
    2.4.0 and reports the error on 1.11.0. It reports the error, on both,
    for a `while sys.version_info < (3, 10):` loop, a `str` assigned to an
    `int` through a conditional expression on `sys.version_info`, an
    `assert sys.platform == "darwin"` inside a function, `from sys import
    platform` then `if platform == "darwin":`, and `if False:`. The rules
    are in `mypy/reachability.py` (`infer_condition_value`,
    `consider_sys_version_info`, `consider_sys_platform`, `is_sys_attr`,
    which matches the literal name `sys`), applied to `if`, `match` and a
    module-level `assert` (`mypy/semanal_pass1.py`).
  - A global `exclude` of `tests/test_graph\.py` in an in-memory INI
    configuration (the derived configuration's options, via
    `--config-file <(printf …)`) lowers the Linux JSON run's errors from 184
    to 153 and `no-untyped-def` from 96 to 72, with `tests` passed as a path
    and with `files` naming the three trees alike.
  - A `.pyi` beside a module is what mypy reads for that module. It was not
    measured here, because it needs a file written into the tree; the
    round-3 reviewer measured an `openspec_graph/graph.pyi` taking the
    tests' `attr-defined` from 19 to 17.
  - None occurs today. At `25c65de`, `find openspec_graph tools tests -name
    '*.pyi'` finds none. A `tokenize` pass over every `.py` under `tests/`
    finds no `NAME` token that is `no_type_check`, `no_type_check_decorator`,
    `TYPE_CHECKING`, `MYPY`, `PY2` or `PY3`. An `ast` pass finds no test of
    an `if`, `elif`, `while`, conditional expression, `assert` or `match`
    guard that refers to `sys.version_info` or `sys.platform`; the one such
    reference is `tests/test_claude_hooks.py:100`, `@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX execute bit")`. `[tool.mypy]`,
    read with `tomllib`, has exactly the keys `files`, `python_version`,
    `strict` and `warn_unreachable`. `tests/` holds 61 `.py` files and no
    subdirectory with one.
- **What mypy applies to a test module, measured** (at `25c65de`).
  - `mypy/config_parser.py:382–387` splits a section's module list on
    commas and replaces `os.sep` and `os.altsep` with dots before it
    compiles a pattern. With the round-3 reviewer's probe configurations,
    `python -m mypy --config-file <cfg> --cache-dir /dev/null --platform
    linux -O json tests`, `MYPYPATH` unset, reports 184 test errors and
    `no-untyped-def` 96 for `base.toml`, and 160 and 72 for each of
    `slash.toml` (`module = "tests/test_graph"`), `comma.toml` (`module =
    "openspec_graph.cli,tests.test_graph"`) and `list.toml` (`module =
    ["openspec_graph.cli", "tests.test_graph"]`). An in-memory
    `[mypy-tests.*.test_graph]` and `[mypy-*.test_graph]` each give 160 and
    72 too, and `[mypy-*]` leaves 184.
  - `mypy.options.Options().compile_glob(p).match("tests.test_graph")` is
    false for `tests/test_graph` and for `openspec_graph.cli,tests.test_graph`,
    and true for `tests.*.test_graph` and for `*`.
  - Loaded through `mypy.main.process_options(["--config-file", <cfg>],
    require_targets=False)`, `Options.snapshot()` of
    `clone_for_module("tests.test_graph")` differs from the global
    snapshot in `disable_error_code` and `disabled_error_codes` for the
    slash, comma, list and mid-pattern spellings, on mypy 2.4.0 and 1.11.0.
    It differs in nothing for `base.toml`, `parent.toml` (`module =
    "tests"`), `ws.toml` (`module = " tests.test_graph"`), `fi_pkg.toml`
    (`follow_imports` on `openspec_graph.*`) and a bare `*`, apart from the
    bookkeeping set `unused_configs` that 1.11.0's snapshot carries and
    2.4.0's does not.
  - Over in-memory INI configurations built on the planned table, an
    override on `tests.test_graph` setting `follow_imports = skip` shows
    `follow_imports` `normal` → `skip`; `ignore_errors = True` shows
    `ignore_errors`; `always_false = FOO` shows `always_false`; and
    `enable_error_code = explicit-override` shows `enable_error_code` and
    `enabled_error_codes`, each on both releases. `disallow_untyped_defs =
    False` shows `disallow_untyped_defs` `True` → `False` through
    `process_options`, and shows nothing through `parse_config_file(o,
    lambda: None, …)`, where the global value was never made strict.
  - A planned `pyproject.toml`, written outside the worktree with the
    tests entry and the `tomli` entry, and its derived INI without the
    tests entry, loaded the same way, differ globally only in `config_file`
    and `per_module_options`, and the planned per-module options less
    `tests.*` equal the derived ones. Under the planned table, all 61 test
    modules differ from the global options in `disable_error_code` and
    `disabled_error_codes` and nothing else; under the derived one, in
    nothing (ignoring 1.11.0's `unused_configs`); both on 2.4.0 and
    1.11.0, with empty stderr. Loading and cloning take 0.1 s.
  - The signatures, read from each release's shipped source because
    1.11.0's compiled functions carry no signature metadata:
    `parse_config_file(options, set_strict_flags, filename, stdout=None,
    stderr=None)` (2.4.0 `config_parser.py:317`, 1.11.0 `:232`);
    `Options.snapshot(self)` (`options.py:448`, `:404`);
    `Options.clone_for_module(self, module)` (`:597`, `:499`); and
    `process_options(args, stdout=None, stderr=None, require_targets=True,
    server_options=False, fscache=None, program="mypy", header=HEADER)`
    (`main.py:1429`, `:441`), with a trailing `mypyc=False` at 2.4.0.
    `process_options` builds the strict callback from `define_options`;
    `parse_config_file` sets `MYPY_CONFIG_FILE_DIR` in `os.environ`
    (`config_parser.py:343`).
- **The occurrence run's shape, measured** (at `25c65de`, through a
  `python -I -c` runner that strips `MYPYPATH` and the coverage variables
  and counts the JSON).
  - With `tests` passed as a path, `fi_narrow.toml` (`follow_imports =
    "skip"` on `openspec_graph.detect` and `openspec_graph.witness`) gives
    176 test errors and `attr-defined` 7, against `base.toml`'s 184 and 19.
    With `files` kept and no path, `fi_narrow_gate.toml` gives 184 and 19,
    the same as `gate.toml`.
  - `MYPYPATH` set to the reviewer's `envstubs` (an `openspec_graph` stub
    whose `__getattr__` returns `Any`) gives 194 test errors and
    `attr-defined` 28 with `tests` as a path, and 184 and 19 in the
    `files` shape. `MYPYPATH` set to a scratch directory holding a
    `pytest/__init__.pyi` of the same form gives 928 in the `files` shape,
    744 of them `untyped-decorator`. mypy puts `MYPYPATH` ahead of the
    configured `mypy_path` (`mypy/modulefinder.py`).
  - `MYPY_CONFIG_FILE_DIR=/nonexistent` leaves `gate.toml`'s run at 184.
  - `gate.toml` in the `files` shape: 184 test errors under `--platform
    linux` in 3.7 s and 188 under `--platform win32` in 3.9 s, no error
    outside `tests/`, stderr empty, exit 1.
- **Configuration discovery, measured.** In each directory it searches,
  mypy reads `mypy.ini`, `.mypy.ini`, `pyproject.toml` and `setup.cfg`, in
  that order, and stops at the first that holds a mypy section
  (`mypy/defaults.py` `CONFIG_NAMES` and `SHARED_CONFIG_NAMES`,
  `mypy/config_parser.py` `_find_config_file`; 1.11.0 and 1.10.1 list the
  same order). Three probe directories were written outside the worktree,
  each with a `pyproject.toml` whose `[tool.mypy]` sets `strict = true` and
  names a tree holding one untyped `def`, beside a second file naming a
  clean tree:
  - with a `.mypy.ini`, `python -m mypy --cache-dir /dev/null` reports
    "Success: no issues found in 1 source file", the clean tree, under
    mypy 2.4.0 and 1.11.0, and `python -m mypy --config-file pyproject.toml
    --cache-dir /dev/null` reports the `no-untyped-def` error in the
    strict tree;
  - with a `mypy.ini`, the same two results;
  - with a `setup.cfg` `[mypy]` section, both commands report the error:
    `pyproject.toml`'s `[tool.mypy]` wins.

  `process_options` on `pyproject.toml` with `mypy_path = "tools"` parses
  it to `["tools"]` on 2.4.0 and 1.11.0.
- **The guard's run, hardened.**
  - `MYPYPATH=tools python -m mypy tests --explicit-package-bases --platform
    <p> -O json --cache-dir /dev/null` writes one JSON object per stdout
    line and no summary, leaves stderr empty, and exits 1. Each object
    carries `file`, `line`, `column`, `end_line`, `end_column`, `message`,
    `hint`, `code` and `severity`. Note text is folded into `hint`, so the
    `[str]` of a note's overload signature is never a `code`. That failing
    run's stdout has no blank line.
  - A run with nothing to report prints a single newline: `python -m mypy
    --strict -O json --cache-dir /dev/null -c 'x: int = 1' | od -c` reads
    `\n` alone, exit 0, under mypy 2.4.0 and 1.11.0.
  - The two runs over `tests` take 3.6 s under `linux` and 3.5 s under
    `win32`; the gate-shaped runs above take 3.7 s and 3.9 s.
  - `-O`/`--output` first shipped in mypy 1.11.0. mypy's `CHANGELOG.md`
    lists "Add error format support and JSON output option via `--output
    json`" (PR 11396) under Mypy 1.11. `mypy/main.py` defines `"-O",
    "--output"` at tag `v1.11.0`, and `grep -c '"--output"'` reads 0 at
    `v1.10.0`; both were fetched from the mypy repository's raw files on
    2026-10-07. The same `-c` run under mypy 1.10.1 prints "mypy: error:
    unrecognized arguments: -O".
  - `pyproject.toml:244–252`'s `dev` list floors nothing. The only floors in
    the file are `requires = ["setuptools>=77"]` and `requires-python`
    (`grep -n ">=" pyproject.toml`). `setuptools>=77` is R-LM-2's floor,
    raised with the form that needed it.
  - At `25c65de`, `packaging` 26.3 imports in this environment and in the
    1.11.0 environment, and `importlib.metadata.requires("pytest")` holds
    `packaging>=22`. `packaging.requirements.Requirement` parses each `dev`
    entry to its name, specifier and marker: `tomli; python_version <
    "3.11"` has an empty specifier and the marker apart; `mypy>=1.11`,
    `mypy==1.11.0`, `mypy>=1.10` and `mypy~=1.11` give the operators `>=`,
    `==`, `>=` and `~=`; a planted `tomli; python_version == "3.10"` gives
    no operator at all.
  - The round-1 reviewer measured the guard-shaped run's per-code counts as
    identical on Python 3.11, 3.12 and 3.13, and on mypy 2.1.0 and 2.4.0.
- **The TOML import.** `tests/support.py:83–88` tries `import tomllib`,
  falls back to `import tomli as toml_reader  # type:
  ignore[import-not-found,no-redef]`, and returns
  `toml_reader.load(handle)`. The rest of this bullet is kept from
  `1c8917c`: each figure is a one-file program run outside the tree, which
  no tree change since bears on. A one-file program in the
  `sys.version_info >= (3, 11)` form, with an annotated local, is clean
  under `python -m mypy --strict --warn-unreachable` at `--python-version
  3.10` and at `3.11`. A one-file analogue of the current form at 3.10
  reports three errors, among them an unused `no-redef` ignore and a
  `no-any-return`. A `[mypy-tomli] ignore_missing_imports = True` section
  makes the 3.10-branch import silent with `tomli` absent. A run whose
  configuration carried sections that matched no processed module printed
  no warning and exited 0.
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
  --no-cache --isolated --no-respect-gitignore --ignore-noqa --select
  D100,D101,D102,D103 --output-format json --exit-zero openspec_graph
  tools`, prints 77 findings in 30 files, 40 file-and-code pairs, exits 0
  and leaves stderr empty (at `25c65de`); without
  `--no-respect-gitignore` it prints the same. The round-1 draft's command,
  with the repository's configuration and `--config "lint.per-file-ignores
  = {}"` in place of `--isolated --ignore-noqa`, prints the same on today's
  tree. The proposed configuration was emulated with no file written:
  `--config 'lint.extend-select = ["D100","D101","D102","D103"]'`, with the
  thirty entries plus `tests/*` passed as one inline `lint.per-file-ignores`
  table built from that JSON. Under it, `python -m ruff check openspec_graph
  tests tools` prints "All checks passed!" and exits 0.
- **ruff's suppressions, measured.** Each case passes a variant of
  `openspec_graph/cli.py` on stdin, with `--stdin-filename
  openspec_graph/cli.py`, to `python -m ruff check --no-cache --select
  D100,D101,D102,D103 --output-format json --exit-zero`, and counts the
  findings. With the repository's configuration and `--config
  "lint.per-file-ignores = {}"`, the unmodified file has 8 (`D103`, at
  lines 206, 258, 282, 413, 534, 545, 674 and 830).
  - A first line `# ruff: noqa: D103` takes it to 0. With `--ignore-noqa`
    added, it is 8 again.
  - `  # noqa: D103` appended to line 206, `def cmd_detect(args:
    argparse.Namespace) -> int:`, takes it to 7. With `--ignore-noqa`, 8.
  - A probe `pyproject.toml`, written outside the worktree, holds the
    repository's `[tool.ruff]` tables plus `[tool.ruff.lint.extend-per-file-ignores]
    "openspec_graph/cli.py" = ["D103"]`. Run from its directory, the file
    has 0 findings; still 0 with `--config "lint.per-file-ignores = {}"`;
    still 0 with `--config "lint.extend-per-file-ignores = {}"` added; and
    still 0 with `--ignore-noqa` added too. ruff adds a command-line
    layer's extend entries to the configuration file's, so an empty inline
    table clears nothing. With `--isolated`, it has 8.
  - Under the planned guard's flags each of the three variants has 8.
  - The `noqa` grammar, at `25c65de`, by the same stdin command without
    `--ignore-noqa`. Appended to line 206, these each take the file to 7:
    `#noqa:D103`, `# NOQA:D103`, `# NoQa: D103`, `#  noqa  :  D103`,
    `# noqa: S607 D103`, `# noqa: S607, D103`, `# noqa:D103,S607`, `# see
    docs # noqa: D103`, `# noqa: D103 # because`, and a bare `# noqa`.
    These leave it at 8: `# noqa: S607 -- D103 is documented elsewhere`;
    `# noqa: d103` and `# noqa:`, each with a stderr warning "Invalid `#
    noqa` directive … expected a comma-separated list of codes". On their
    own line inserted at line 301, `# ruff: noqa: D103`, `#ruff:noqa:D103`,
    `# ruff: noqa`, `# flake8: noqa` and `# flake8: noqa: D103` each take it
    to 0, and `# RUFF: NOQA: D103` leaves 8.
  - Ignore files, at `25c65de`, in probe trees outside the worktree whose
    `pkg/m.py` holds two undocumented functions. With `pkg/.ignore` naming
    `m.py`, the guard's flags without `--no-respect-gitignore` find nothing
    and print "warning: No Python files found under the given path(s)";
    with it, 3 findings. A `pkg/.gitignore` naming `m.py`, outside any git
    repository, hid nothing either way. The round-3 reviewer measured an
    `openspec_graph/.ignore` naming `cli.py` taking the tree's 77 findings
    to 69 under `--isolated`. `python -m ruff check --isolated
    --no-respect-gitignore --show-settings` lists the built-in
    `file_resolver.exclude`, which the flags leave in force: `.bzr`,
    `.direnv`, `.eggs`, `.git`, `.git-rewrite`, `.hg`, `.ipynb_checkpoints`,
    `.mypy_cache`, `.nox`, `.pants.d`, `.pyenv`, `.pytest_cache`, `.pytype`,
    `.ruff_cache`, `.svn`, `.tox`, `.venv`, `.vscode`, `__pypackages__`,
    `_build`, `buck-out`, `dist`, `node_modules`, `site-packages` and
    `venv`.
  - Today, a `tokenize` pass over every `.py` under `openspec_graph/` and
    `tools/` finds two comment tokens holding `noqa`:
    `openspec_graph/detect.py:668` (`# noqa: S607`) and
    `openspec_graph/report.py:59` (`# ruff: noqa: S105 -- …`, file-level).
    None names a `D` code, and none is bare. No `.ignore` file exists in
    the worktree outside `.git` (`find . -name .ignore -not -path
    './.git/*'`). `python -m ruff check --no-cache --isolated --show-files
    openspec_graph tools` lists the same 43 files with and without
    `--no-respect-gitignore`, every `.py` file that `find openspec_graph
    tools -name '*.py'` counts, so no ignore file hides one there today.
    `[tool.ruff.lint]` has no `extend-per-file-ignores` key.
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
    `warn_unreachable`, `python_version`; not `files`). Both are marked
    `integration`, and both read through `tests/support.py`'s
    `read_pyproject()`, whose path is built from `__file__` with no
    labelled segment (`tests/support.py:25`), which is what
    `tests/shape_support.py`'s criterion calls `integration`.
  - `tests/test_ci_workflow.py:69–104` holds two planted-tree tests that copy
    the real `pyproject.toml` and run ruff and mypy on a path given on the
    command line, so `files` is not read.
  - `tests/test_enterprise.py:225` and `:241` hold
    `test_mypy_fails_on_a_type_error` (a module under `tmp_path`, outside
    every package base) and `test_typecheck_passes_on_clean_repo` (it runs
    `make typecheck` from the repository root, so it will check `tests/`
    too).
  - `tests/test_threshold_guard.py:168` holds
    `test_threshold_guard_fails_on_a_pinned_tool_version`, which plants
    `pip install ruff==0.4.2` in a workflow and asserts the threshold guard
    names it. It reads no dev extra, so nothing today asserts the extras'
    floor or their lack of a pin.
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
    `tests/test_suite_shape.py` 555 (689 at `1c8917c`, before #42 was in
    the branch) and `tests/test_ci_workflow.py` 392.
  - `make thresholds` prints "PASS: no hard-coded thresholds in Makefile or
    workflow YAML".
  - `make stage-citations` reads 52 specs, this package's own among them.
    `typecheck` is mentioned in 8 and verified by 5, and is run directly by
    `ci.yml`; `lint` is mentioned in 8 and verified by 5; `test` is
    mentioned in 49 and verified by 49.
  - The gate before each revision's first write under `openspec/`,
    `planlint --target . validate --fail-on ERROR`, exits 0: 52 specs, 0
    error / 0 warn / 0 info, at `e558eba` and at `25c65de`.

## What Changes

- `pyproject.toml` `[tool.mypy]`:
  - `files = ["openspec_graph", "tools", "tests"]`;
  - `explicit_package_bases = true` and `mypy_path = "tools"`, each with a
    comment giving its measured reason (DEC-TDR-002);
  - `strict`, `warn_unreachable` and `python_version` unchanged, and no
    other global key, so the table holds exactly those six and its
    overrides (R-TDR-1, DEC-TDR-016);
  - a `module = "tests.*"` override whose `disable_error_code` lists the
    codes of R-TDR-2 that still occur when it lands. A comment above it
    names the ratchet and the guard module that holds its ceilings and
    waivers, and states that a code leaves in the commit that fixes its
    last occurrence, and the override in the commit that empties its list;
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
    guard's command above, at `e558eba`. `openspec_graph/cli.py`'s entry
    joins its `T201` entry;
  - a comment above the entries names the ratchet and its guard.

  There is no `[tool.ruff.lint.pydocstyle]` table and no
  `[tool.ruff.lint.extend-per-file-ignores]` table.
- `Makefile`: the `typecheck` recipe becomes `python -m mypy --config-file
  pyproject.toml`, and its help text says it checks the trees that
  `[tool.mypy] files` names. Nothing else changes.
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
  at `e558eba`.
- `tests/test_static_ratchets.py` (new), within a budget of 600 lines by
  `wc -l` at the W6.6 commit (DEC-TDR-012). As shipped, the mypy half alone
  was over that budget, so DEC-TDR-012's split was taken at the W6.5 commit
  (`tasks.md`, Milestone 1's record): the pure helpers below are in the
  uncollected `tests/ratchet_support.py`, and the planted-input test is in
  `tests/test_static_ratchets_planted.py`.
  - `MYPY_TESTS_CEILINGS`, `MYPY_WAIVERS` and `DOCSTRING_CEILINGS`, each
    under the comment stating its rule;
  - the pure helpers, each taking its input as an argument: the recipe and
    key-set check, the mypy option comparison over `process_options` and
    `clone_for_module`, the derived mypy configuration and its re-check, the
    run's environment, the mypy-JSON counter, the two-platform comparison,
    the ceiling comparison, the ignore-and-mypy-comment reader with its
    waived-line key, the stub, name and condition reader, the waiver
    comparison, the dev-extra check over `packaging`, the per-file-ignores
    shape check with its `noqa` reader, and the ruff-JSON counter;
  - the guards of R-TDR-1, 2, 4, 5, 7, 9 and 16, and the planted-input test
    of R-TDR-11, each with one tier marker, the module marking per function.
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
  12, 13, 14, 16 and 22 are re-pointed to the guards once they exist.

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
  hypothesis ship types), no `tomli` for every interpreter, no declared
  `packaging` (pytest installs it), and no `==` on any tool. The dev extras
  stay unpinned by decision, and the dev-extra guard of R-TDR-16 holds that.
  The one bound added is a floor on `mypy`, at the release whose output
  format the guard reads (DEC-TDR-014).
- **A workflow, composite-action or `.pre-commit-config.yaml` change.** Every
  leg and the hook already run `make typecheck`, and the hook's `types:
  [python]` already includes a test module. The occurrence guard runs the
  Windows view itself, so no leg is added.
- **A `tests/__init__.py` or `tools/__init__.py`.** Either would change how
  pytest or mypy names modules, and the search path does the job
  (DEC-TDR-002).
- **Overrides for the package, `tools/` or a third-party import.** R-TDR-2
  judges only the overrides that change a test module (DEC-TDR-015).
- **A ban on a bare `noqa`, or on a `noqa` for another rule.** The docstring
  count ignores every `noqa` (DEC-TDR-009). What other rules a `noqa` may
  silence is not this package's choice.
- **Stopping a deliberate, coordinated loosening.** A change that edits the
  code and the guard's constants together is review's to catch, and the
  known residual gaps are listed rather than chased (DEC-TDR-017).
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
