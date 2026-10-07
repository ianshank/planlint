# Tasks: ratchet-test-types-and-docstrings

## Header measurements

First measured at `1c8917c`, re-measured at `d2b3cc6` for the round-1
revision, and re-measured on 2026-10-07 at `e558eba` for the round-2
revision. `e558eba` is the head of `claude/m2-tests-under-mypy`, whose base
is `main` at `46ae1b3`, where #42 (`shape-the-test-suite`) was
squash-merged. Neither `1c8917c` nor `d2b3cc6` is an ancestor of the branch.
`git diff d2b3cc6 HEAD -- ':!openspec/changes/ratchet-test-types-and-docstrings'`
was empty at `e558eba` when the round-2 revision was handed over, and every
headline figure below was re-taken at `e558eba` and equals its `d2b3cc6`
value. The container had four cores (`nproc`) and ran Python 3.13.16, mypy
2.4.0, ruff 0.16.10, pytest 9.1.1 and hypothesis 6.168.5, with no `tomli`.
Every line number below is re-checked against the branch head before the
milestone that uses it, because a sibling package landing first may move a
line without moving the fact. Every number here names the command that
produced it. Every mypy run used `--cache-dir /dev/null` or a cache
directory outside the worktree. Times are `TIMEFORMAT='%R s'; time
<command>`.

At `e558eba`:
- **The gate.** `planlint --target . validate --fail-on ERROR` exits 0
  before the round-2 revision's first write under `openspec/`, with 52 specs
  and 0 error / 0 warn / 0 info.
- **Today's tests.** `python -m mypy tests --explicit-package-bases
  --cache-dir /dev/null` reports "Found 185 errors in 32 files (checked 61
  source files)". Counting only the trailing code of its `error:` lines
  (`grep ": error:" | grep -oE "\[[a-z-]+\]$" | sort | uniq -c`) gives:
  `no-untyped-def` 96, `attr-defined` 19, `arg-type` 18, `type-arg` 16,
  `no-any-return` 9, `index` 7, `union-attr` 4, `list-item` 3,
  `unused-ignore` 2, `operator` 2, `misc` 2, `import-not-found` 2,
  `call-overload` 2, `var-annotated` 1, `unreachable` 1 and `assignment` 1.
  The `str` 4 and `bytes` 1 of an unfiltered grep are note-line text, not
  codes.
- **Without explicit bases.** The run stops at "Source file found twice under
  different module names" for `tests/graft_support.py`, and exits 2.
- **The package and `tools/`.** `python -m mypy openspec_graph tools
  --explicit-package-bases --cache-dir /dev/null` reports 19 errors in 12
  files, from twelve `_common` imports. With `MYPYPATH=tools` it reports none
  in 43, under the default platform and under `--platform win32`.
- **Both platforms.** `MYPYPATH=tools python -m mypy tests
  --explicit-package-bases -O json --cache-dir /dev/null` emits 184 error
  objects under `--platform linux`, in 3.6 s, and 188 under `--platform
  win32`, in 3.5 s. Both runs leave stderr empty and exit 1. The four extra
  objects are `attr-defined` on `os.mkfifo` in
  `tests/test_detect_thresholds.py`, lines 250, 251, 406 and 425; no error
  is Linux-only.
- **A clean JSON run.** `python -m mypy --strict -O json --cache-dir
  /dev/null -c 'x: int = 1' | od -c` reads a lone `\n`, exit 0, under mypy
  2.4.0 and 1.11.0.
- **The suppression bypass.** The same Linux command, with `--shadow-file
  tests/test_graph.py <(printf '# mypy:
  disable-error-code="no-untyped-def"\n'; cat tests/test_graph.py)`, reports
  `no-untyped-def` 72, against 96.
- **The override, emulated.** With the seven codes of R-TDR-2 disabled for
  `tests.*` through an in-memory INI configuration, the three trees report
  23 errors in 15 files (104 checked) in 3.7 s cold. That is fifteen
  occurrences of nine codes on fourteen lines, plus eight `unused-ignore` on
  the inline ignores the override makes redundant.
- **Today's recipe.** `python -m mypy openspec_graph tools --cache-dir
  /dev/null` takes 0.9 s. The planned form, `python -m mypy --config-file
  pyproject.toml --cache-dir /dev/null`, reports "Success: no issues found
  in 43 source files" in 1.0 s, exit 0.
- **Docstrings.** `python -m ruff check --no-cache --isolated --select
  D100,D101,D102,D103 <tree> --statistics` reads 52 findings in 18 files of
  `openspec_graph/`, 25 in 12 files of `tools/`, and 584 in 47 files of
  `tests/`. The planned guard's command, `python -m ruff check --no-cache
  --isolated --ignore-noqa --select D100,D101,D102,D103 --output-format json
  --exit-zero openspec_graph tools`, prints 77 findings in 30 files (40
  file-and-code pairs), exits 0 and leaves stderr empty.
- **The convention.** The sorted `D100`–`D103` finding set has one digest
  under no convention and under `google`, `numpy` and `pep257` (661 each).
  Google is the best fit of the wider family, with 37 findings against 67.
- **Make targets.** `make thresholds` prints PASS. `make stage-citations`
  reads 52 specs, this package's own among them, with `typecheck` mentioned
  in 8, verified by 5 and run directly by `ci.yml`.
- **Line counts.** `wc -l tests/AGENTS.md` reads 59, against
  `MAX_NESTED_LINES = 60`. `wc -l` reads `tests/test_suite_shape.py` 555 and
  `tests/test_detect_thresholds.py` 476. `wc -l tests/test_*.py | sort -n |
  tail -1` reads `tests/test_report.py` 692, against `MAX_TEST_MODULE_LINES
  = 700`.

## Order and commits

The order follows DEC-TDR-013:
1. Measure.
2. Write the mypy guards and see them red in the working tree.
3. Fix the nine codes and the platform-only errors, and land the override
   with its ceilings, its waivers and the mypy floor. This is the W6.5
   commit.
4. Write the docstring guards, see them red, and land the entries with their
   ceilings. This is the W6.6 commit.
5. Land the documents, the re-pointed verification lines and the records.
   This is the documents commit.

One pull request carries the package. There are three commits, each `make
pre-pr` green, and each is pushed and its CI run recorded before the next is
pushed. `ci.yml` runs on `pull_request`, which tests the merge of the pushed
head into `main`, so each CI record names the run id, the head SHA it ran
for and the merge SHA it tested. No guard is committed red. The red runs are
recorded here, and never committed.

## Recorded (round-1 corrections, 2026-10-07)

Measured at `d2b3cc6`, before the revision's first write. `planlint --target
. validate --fail-on ERROR` exits 0, with 52 specs. Each finding is followed
by its resolution.

1. **HIGH: suppression comments bypass the ceilings** (round-1 adversarial
   review). A new `# type: ignore[no-untyped-def, unused-ignore]` passed the
   first draft's waiver guard, and a file-level `# mypy:
   disable-error-code=...` comment lowered `no-untyped-def` from 96 to 72.
   The second is reproduced in the header by `--shadow-file`.
   - Resolved in R-TDR-7, DEC-TDR-006, R-TDR-11, AC-TDR-8 and AC-TDR-9.
     Every inline `# type: ignore` under `tests/` must be a recorded
     `MYPY_WAIVERS` entry of (path, enclosing function or `<module>`, code).
     The entries only shrink and are compared as a multiset. Each waiver
     holds exactly one listed code plus `unused-ignore`. Every `# mypy:`
     comment token found with `tokenize` is named. Both bypasses are planted
     cases.
   - Two more forms were found while re-measuring, by `python -m mypy -O
     json --strict -c …` outside the worktree, and are named the same way.
     A bare `# type: ignore` before a module's first statement silences the
     whole module (exit 0 on an untyped `def` and a mistyped assignment). A
     `# mypy: ` line inside a docstring is honoured under `-c` (exit 0) but
     is no comment token. Round 2 found that mypy 2.4.0's default parser
     does not honour it in a file read from disk, while mypy 1.11.0, which
     the `>=1.11` floor admits, does; that floor is why the guard also names
     every physical line that begins with mypy's own prefix (`mypy/util.py`,
     `get_mypy_comments`). See round-2 item 8.
   - One completion of the decision is needed when a code is later
     re-enabled. Its waivers keep their entries and lose `unused-ignore`,
     so strict mode polices them as ordinary ignores of an enforced code.
2. **MEDIUM: measuring only on Linux hides Windows-only debt** (round-1
   adversarial review, and Copilot's first review of #44).
   - Resolved in R-TDR-3, R-TDR-5, DEC-TDR-003, DEC-TDR-005, AC-TDR-5,
     AC-TDR-6 and the Validation Matrix.
   - The four `os.mkfifo` sites in `tests/test_detect_thresholds.py` are
     fixed with `_MKFIFO: Callable[[Path], None] | None = getattr(os,
     "mkfifo", None)` and `assert _MKFIFO is not None`. That form was
     verified clean by the reviewer, and re-checked here under `--platform
     linux`, under `--platform win32` and under ruff.
   - The occurrence guard runs mypy under both platforms and requires the
     two error sets to agree. A mismatch is named as a platform-only error
     to fix, and is never listed.
3. **MEDIUM: nothing forces a ceiling down** (round-1 adversarial review).
   - Resolved in R-TDR-4, R-TDR-5, R-TDR-9, DEC-TDR-004, DEC-TDR-009,
     AC-TDR-5, AC-TDR-12 and AC-TDR-13.
   - Both guards fail when a count differs from its ceiling in either
     direction, and below the ceiling they say `lower <code> from A to B`,
     or `lower <file> <code> from A to B`.
   - DEC-TDR-004 records the reviewer's identical counts on Python 3.11,
     3.12 and 3.13, and on mypy 2.1.0 and 2.4.0. It also states the
     consequence of unpinned extras: a release that changes a count is met
     by a ceiling edit in that pull request, never by a widened list.
4. **MEDIUM: a shipped decision on `D` is not addressed** (round-1
   adversarial review).
   - Resolved in DEC-TDR-008 and DEC-TDR-011, which cite C-ZCG-2 and
     DEC-ZCG-012 and call this package's per-file ratchet their "ratchet
     first" step.
   - R-TDR-10 now requires the `pyproject.toml` ruff header sentence ("every
     family here was at or near zero violations when it was turned on") to
     be rewritten to stay true.
   - R-TDR-14 names DEC-ZCG-004's "table that remains" sentence as
     superseded, beside R-ZCG-3's `files` clause, without editing that
     package.
   - The first draft's evidence claimed that no shipped spec decided
     anything about `D`. That claim was false, and the proposal corrects it.
5. **LOW: harden the guard's mypy run** (round-1 adversarial review).
   - Resolved in R-TDR-5, R-TDR-16, DEC-TDR-005, DEC-TDR-014 and AC-TDR-22.
     The run uses `-O json` and counts the `code` field of `severity ==
     "error"` objects. It asserts empty stderr and an exit code of 0 or 1.
   - The dev extra floored nothing (`pyproject.toml:244–252`), so `mypy`
     gains a floor at 1.11, the release that added `-O`/`--output`. That is
     mypy's `CHANGELOG.md`, PR 11396, and `mypy/main.py` at `v1.11.0`
     against `v1.10.0`.
   - No floored dev extra existed to follow, so the precedent followed is
     R-LM-2's setuptools build floor. That is a floor at the release that
     understands the feature, raised in the commit that uses it.
6. **LOW: stale numbers after the merge of #42's head** (round-1 adversarial
   review).
   - Every figure in the proposal and this header is re-taken at
     `d2b3cc6`. `tests/shape_support.py:571` is now `:590`, and
     `tests/test_suite_shape.py:536` is now `:555`.
   - The waiver at `tests/test_suite_shape.py:111` is now `:115`, inside
     `_registration_problems` rather than the test the first draft named.
   - `tests/test_suite_shape.py` is 555 lines, so DEC-TDR-012 no longer
     calls it near the bound. DEC-TDR-012 sets a 600-line budget for
     `tests/test_static_ratchets.py`.
7. **LOW: the commit plan is inconsistent** (round-1 adversarial review).
   Resolved in DEC-TDR-013, Milestones 1 to 4 and the Validation Matrix. The
   guards land inside the W6.5 and W6.6 commits and never as red commits.
   Milestone 4 is the named documents commit. Every commit is `make pre-pr`
   green.
8. **LOW: R-TDR-2 over-reaches** (round-1 adversarial review).
   - Resolved in R-TDR-2, the new DEC-TDR-015, AC-TDR-4 and AC-TDR-7.
     R-TDR-2 judges only overrides whose `module` patterns, matched as mypy
     matches them, apply to a module under `tests/`.
   - Overrides for the package, `tools/` or a third-party import are
     outside it, and the closed "only `tomli`" list is gone.
   - An override for a single test module is named, because it would lower
     a count outside the one entry.
9. **C-TDR-2 and AC-TDR-17 permitted only the recipe line** (Copilot, first
   review of #44). Resolved: both now allow the `typecheck` target's help
   text and its recipe line.
10. **AC-TDR-20 cannot be met as written** (Copilot, first review of #44).
    Resolved: AC-TDR-20 is now the CI run on the W6.5 commit, covering the
    type gate and the mypy guards. The new AC-TDR-21 is the CI run on the
    W6.6 commit, covering the lint gate and the docstring guards. Each is
    recorded separately, with its run id.
11. **C1: numbers without a producing command** (Copilot, second review of
    #44).
    - `openspec/AGENTS.md:38–41` and `docs/policies.md`'s "Count cites a
      command" were the rule. Resolved: the "Why" section's line count of
      `tests/` is removed as non-essential.
    - Every other figure in the proposal names its command and is dated
      with its commit, either `d2b3cc6` or `1c8917c`, on 2026-10-07. The
      reviewer's figures are attributed as the reviewer's.
    - The spec's evidence and decisions name their commands the same way.
12. **C2: the convention wording was false** (Copilot, second review of
    #44). "While no rule it governs is selected" was untrue, because
    `D100`–`D103` are pydocstyle rules.
    - Resolved in R-TDR-10, DEC-TDR-010 and AC-TDR-14. No convention may be
      configured while no selected rule's verdict depends on it, and that is
      measured and recorded. The sorted `D100`–`D103` finding set has one
      digest under no convention and under each of the three.
    - Google is described as the best fit, with the fewest wider-family
      findings (37 against 67), and not as a convention the docstrings
      follow.
13. **C3: AC-TDR-10's re-pointing was missing** (Copilot, second review of
    #44). Resolved in Milestone 4's table. AC-TDR-10 gains
    `test_docstring_exemptions_are_file_entries_matching_their_ceilings`,
    which asserts that exactly `D100`–`D103` are selected among `D` rules,
    and that `D` codes sit only on concrete package and tool files plus
    `tests/*`. AC-TDR-14 gains the same guard, for the absent `pydocstyle`
    table and the four-rule limit.

## Recorded (round-2 corrections, 2026-10-07)

Measured at `e558eba`, before the round-2 revision's first write.
`planlint --target . validate --fail-on ERROR` exits 0, with 52 specs and 0
error / 0 warn / 0 info. Each finding of the round-2 adversarial review is
followed by its resolution and the measurements behind it. The probes that
needed a file on disk wrote it to a scratch directory outside the worktree;
every other run wrote nothing.

1. **HIGH-1: the docstring ratchet is bypassable three ways** (round-2
   adversarial review). A file-level `# ruff: noqa: D10x`, a line-level
   `# noqa: D10x` and a `[tool.ruff.lint.extend-per-file-ignores]` entry
   each lower the guard's count with the ratchet entries unchanged, and
   clearing `per-file-ignores` on the command line does not clear the
   extend table.
   - Measured by passing `openspec_graph/cli.py` on stdin to `python -m ruff
     check --no-cache --select D100,D101,D102,D103 --output-format json
     --exit-zero --stdin-filename openspec_graph/cli.py -`, counting
     findings. With `--config "lint.per-file-ignores = {}"`: the file as
     it is, 8; with a first line `# ruff: noqa: D103`, 0; with `  # noqa:
     D103` on line 206, 7. With `--ignore-noqa` added, 8 and 8.
   - The review proposed `--config "lint.extend-per-file-ignores = {}"`.
     That was measured and does not work. Run from a probe directory whose
     `pyproject.toml` holds the repository's `[tool.ruff]` tables plus
     `[tool.ruff.lint.extend-per-file-ignores] "openspec_graph/cli.py" =
     ["D103"]`, the file reads 0 with nothing cleared, 0 with
     `per-file-ignores` cleared, 0 with both tables cleared by `--config`,
     and 0 with `--ignore-noqa` added as well. With `--isolated` it reads 8.
     ruff adds a command-line layer's extend entries to the file's.
   - Resolved in R-TDR-8, R-TDR-9, R-TDR-11, DEC-TDR-009, AC-TDR-10,
     AC-TDR-12 and AC-TDR-13. The occurrence guard runs ruff with
     `--isolated --ignore-noqa` in place of the repository's configuration
     with `per-file-ignores` cleared. Under those flags each of the three
     planted variants reads 8, and the tree reads 77 findings in 30 files
     (40 pairs), exit 0, empty stderr: the same as the round-1 command on
     today's tree.
   - The shape guard names a `D` code under `extend-per-file-ignores` and
     any comment token, read with `tokenize`, holding a `noqa` directive
     that names a `D` code, under `openspec_graph/` or `tools/`. Today there
     are two `noqa` comment tokens there, `openspec_graph/detect.py:668`
     (`S607`) and `openspec_graph/report.py:59` (file-level `S105`); none
     names a `D` code, and `[tool.ruff.lint]` has no
     `extend-per-file-ignores` key.
   - Planted cases: a file-level `# ruff: noqa: D103`, a line-level
     `# noqa: D103`, and an `extend-per-file-ignores` entry carrying `D103`.
2. **HIGH-2: mypy's module-pattern matching was described wrongly**
   (round-2 adversarial review). The round-1 tasks text said a `*` inside a
   pattern matches one or more components.
   - Measured: `mypy.options.Options().compile_glob(<p>).match(<m>)`, under
     mypy 1.10.1, 1.11.0 and 2.4.0 alike, matches `tests.*.test_graph`,
     `*`, `*.test_graph` and `tests.*` against `tests.test_graph`, and
     `tests.*` against `tests`. As overrides with `disable_error_code =
     no-untyped-def` in an in-memory INI configuration,
     `[mypy-tests.*.test_graph]` and `[mypy-*.test_graph]` each take the
     Linux run from 184 errors to 160 and `no-untyped-def` from 96 to 72.
     `[mypy-*]` leaves 184, because mypy files a bare `*` as a concrete key
     that names no module.
   - Resolved in R-TDR-2, DEC-TDR-015, AC-TDR-4 and Milestone 1's matcher.
     The applicability test is `compile_glob` itself, so `.*` matches zero
     or more components and a leading `*` matches any module. `*` is judged
     as applying to the tests, which errs toward naming it.
   - Planted cases: overrides for `tests.test_graph`, `tests.*.test_graph`
     and `*`, each named.
3. **MEDIUM-3: counts can be lowered with no comment** (round-2 adversarial
   review), by a `tests/**/*.pyi` stub, `@typing.no_type_check`, code under
   `if not TYPE_CHECKING:` and a global `exclude`.
   - Measured: `python -m mypy --strict --warn-unreachable --python-version
     3.10 --cache-dir /dev/null -c …`, outside the worktree, exits 1 on an
     untyped `def`, and 0 with the same `def` under `@typing.no_type_check`
     or under `if not TYPE_CHECKING:`. An in-memory INI `exclude =
     tests/test_graph\.py` takes the Linux JSON run from 184 errors to 153
     and `no-untyped-def` from 96 to 72. The stub case was not measured,
     because it needs a file written into `tests/`.
   - None exists today: `find tests -name '*.pyi'` finds none; a `tokenize`
     pass over `tests/**/*.py` finds no `NAME` token `no_type_check`,
     `no_type_check_decorator` or `TYPE_CHECKING`; `grep -rn
     "no_type_check\|TYPE_CHECKING" tests/` finds no line; `[tool.mypy]`'s
     keys, read with `tomllib`, are `files`, `python_version`, `strict` and
     `warn_unreachable`.
   - Resolved in R-TDR-1, R-TDR-3, R-TDR-7, R-TDR-11, the new DEC-TDR-016,
     AC-TDR-3, AC-TDR-6, AC-TDR-8 and AC-TDR-9. The recipe-and-files guard
     asserts `[tool.mypy]`'s exact key set, which covers `exclude` and every
     other global key. A sibling of the waiver guard,
     `test_no_stub_or_unchecked_name_under_tests`, names any `.pyi` under
     `tests/` and any such `NAME` token. DEC-TDR-016 records that a future
     legitimate use is a reviewed change to the guard, not a silent
     addition.
   - Planted cases: a `.pyi` path under `tests/`, a `no_type_check` name, a
     `TYPE_CHECKING` name, and a `[tool.mypy]` table with `exclude`.
4. **MEDIUM-4: a stray mypy configuration silently narrows the gate**
   (round-2 adversarial review).
   - Measured in three probe directories outside the worktree, each with a
     `pyproject.toml` whose `[tool.mypy]` is strict over a tree holding one
     untyped `def`, beside a second file naming a clean tree. Under mypy
     2.4.0 and 1.11.0, a bare `python -m mypy --cache-dir /dev/null` read a
     planted `.mypy.ini` ("Success: no issues found in 1 source file"), and
     likewise a planted `mypy.ini`; `python -m mypy --config-file
     pyproject.toml --cache-dir /dev/null` reported the `no-untyped-def`
     error in both. A `setup.cfg` `[mypy]` section did not take precedence:
     both commands reported the error, because mypy reads `setup.cfg` after
     a `pyproject.toml` that carries `[tool.mypy]` (`mypy/defaults.py`,
     `mypy/config_parser.py`). That part of the finding does not hold for
     this tree, and the resolution covers it anyway.
   - Resolved in R-TDR-1, C-TDR-2, DEC-TDR-001, AC-TDR-1, AC-TDR-3,
     AC-TDR-17, the proposal's What Changes and Milestones 1, 2 and 4. The
     recipe is `python -m mypy --config-file pyproject.toml`, still with no
     path, so `files` stays the one list. On today's tree that form reports
     "Success: no issues found in 43 source files" in 1.0 s.
5. **MEDIUM-5: R-TDR-7 contradicted itself** (round-2 adversarial review).
   "An ignore holding no listed code" would go red when a code leaves the
   override, and "removed and never added" collided with a rename or move
   of a function that holds a waiver.
   - Resolved in R-TDR-7, R-TDR-11, DEC-TDR-006, AC-TDR-8 and AC-TDR-9. The
     guard names an ignore holding no code besides `unused-ignore`, an
     ignore holding more than one, `unused-ignore` without a listed code,
     and a listed code without `unused-ignore`. A recorded ignore of exactly
     one enforced code, without `unused-ignore`, is allowed and is a
     planted quiet case.
   - An entry may be re-keyed only in the commit that renames its enclosing
     function or moves the ignore's line into another function of the same
     file. A re-key changes that one entry's function and nothing else; the
     path and code stay, and `MYPY_WAIVERS` read as (path, code) pairs is
     the same multiset before and after. A move to another file is a new
     waiver.
6. **MEDIUM-6: a clean `-O json` run prints a lone newline** (round-2
   adversarial review).
   - Measured: `python -m mypy --strict -O json --cache-dir /dev/null -c
     'x: int = 1' | od -c` reads `\n` alone, exit 0, under mypy 2.4.0 and
     1.11.0. The failing run over `tests/` has no blank line.
   - Resolved in R-TDR-5, R-TDR-11, DEC-TDR-005, AC-TDR-5, AC-TDR-9 and
     Milestone 1's JSON counter: blank lines are skipped. Planted quiet
     case: stdout `"\n"` with exit 0.
7. **MEDIUM-7: nothing tests the mypy floor or the no-pin rule** (round-2
   adversarial review). AC-TDR-22 and AC-TDR-16 cited
   `test_threshold_guard_fails_on_a_pinned_tool_version`, which plants
   `pip install ruff==0.4.2` in a workflow (`tests/test_threshold_guard.py:168–174`)
   and reads no dev extra.
   - Resolved in R-TDR-16, R-TDR-11, DEC-TDR-014, AC-TDR-9, AC-TDR-16,
     AC-TDR-22 and Milestones 1 and 4. The planned
     `test_the_dev_extra_floors_mypy_and_pins_nothing` reads
     `[project.optional-dependencies] dev` through `tests/support.py`'s
     `read_pyproject()`, and asserts one entry for `mypy` whose specifier is
     `>=1.11` and no `==` in any entry.
   - Its tier is `integration` by `tests/shape_support.py`'s criterion: it
     starts no process, and it reaches `read_pyproject()`, whose path is
     built from `__file__` with no labelled segment (`tests/support.py:25`,
     `LABELLED_INPUT_SEGMENTS` at `tests/shape_support.py:95`). The two
     existing tests that read through it,
     `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt` and
     `test_mypy_is_strict_and_warns_on_unreachable_code`, are marked
     `integration`. Milestone 1 confirms the tier against the criterion
     once the test exists.
   - AC-TDR-22's verification line now cites the stage only, as the
     package's other not-yet-written guards do, and Milestone 4's table
     adds the new test to AC-TDR-16 and AC-TDR-22. AC-TDR-16 keeps the
     threshold-guard selector for the workflow half of "no tool version is
     pinned".
8. **LOW-8: the docstring-line evidence over-generalised** (round-2
   adversarial review).
   - Measured with a probe module outside the worktree whose docstring's
     second line is `# mypy: disable-error-code="no-untyped-def"`, by
     `python -m mypy --strict --cache-dir /dev/null <file>`. mypy 2.4.0's
     default parser reports the untyped `def`; 2.4.0 with
     `--no-native-parser`, with `-c`, and with `--shadow-file` all report
     "Success", and so does mypy 1.11.0. Over the tree, the line inserted by
     `--shadow-file` into `tests/test_graph.py`'s docstring takes
     `no-untyped-def` from 96 to 72 under 2.4.0 and 1.11.0.
   - Resolved in the proposal's suppression bullet, DEC-TDR-006, R-TDR-7
     and round-1 item 1 above: the physical-line check is needed because
     the `>=1.11` floor admits releases that honour such a line.
9. **LOW-9: stale dates and a stale stacking claim** (round-2 adversarial
   review). `d2b3cc6` and `1c8917c` are not ancestors of the branch, and #42
   merged as `46ae1b3`.
   - The headline figures were re-run at `e558eba` and each equals its
     `d2b3cc6` value: 185 errors in 32 files; 184 and 188 JSON error
     objects; 19 errors in 12 files without the search path; 23 errors in
     15 files under the emulated override; 52, 25 and 584 docstring
     findings; 77 findings in 30 files by the guard's command; 661 findings
     with one digest under each convention.
   - Re-dated to `e558eba` in the proposal, the spec's evidence and
     decisions, and this file's header. The proposal's "Why" and
     DEC-TDR-011 now say the branch is based on `46ae1b3`, and Milestone 0
     no longer asks whether #42 has merged.
10. **LOW-10: "exactly one override" had no clean end state** (round-2
    adversarial review). Resolved in R-TDR-2, R-TDR-4, R-TDR-11 and
    AC-TDR-4: at most one override may apply to the tests, its list is
    never empty, and the commit that empties it removes the override. With
    none, `MYPY_TESTS_CEILINGS` is empty. Planted case: a tests override
    with an empty list. One consequence: with no override and no ceiling,
    the override guard is green, so the unchanged tree cannot show its red.
    R-TDR-11 now takes that red with the ceilings filled and no override,
    which Milestone 2 does before the override lands.
11. **LOW-11: a PR run tests the merge ref** (round-2 adversarial review).
    `ci.yml` runs on `pull_request`, and on `push` only to `main` and
    `master`. Resolved in R-TDR-15, C-TDR-5, DEC-TDR-013, AC-TDR-20,
    AC-TDR-21 and Milestones 2 and 3: each CI record names the run id, the
    head SHA it ran for and the merge SHA it tested.

## Milestone 0 — Grounding pass at the branch head

- Re-run the gate and record its exit code before the first edit:
  `planlint --target . validate --fail-on ERROR`.
- Re-take the header's measurements and record what moved, with the commit:
  - `python -m mypy tests --explicit-package-bases --cache-dir /dev/null`,
    counted by the code of `error:` lines only;
  - `MYPYPATH=tools python -m mypy tests --explicit-package-bases -O json
    --cache-dir /dev/null` under `--platform linux` and under `--platform
    win32`, each counted by `code` over `severity == "error"` objects, blank
    lines skipped, with the two error sets compared and their stderr and
    exit codes recorded;
  - `python -m mypy openspec_graph tools --explicit-package-bases`, with and
    without `MYPYPATH=tools`;
  - `python -m mypy --config-file pyproject.toml --cache-dir /dev/null`;
  - the per-file distribution of the seven listed codes;
  - the ruff statistics per tree, and the per-file list over
    `openspec_graph` and `tools` (`--isolated --output-format concise`);
  - the guard's command, `python -m ruff check --no-cache --isolated
    --ignore-noqa --select D100,D101,D102,D103 --output-format json
    --exit-zero openspec_graph tools`;
  - the convention digest;
  - `make thresholds` and `make stage-citations`;
  - `wc -l tests/AGENTS.md`, `wc -l tests/test_*.py | sort -n | tail -4`
    and `wc -l tests/test_detect_thresholds.py`;
  - `grep -n "type: ignore" tests/*.py`, with each comment's enclosing
    function read by AST;
  - `grep -rn "mypy:" tests/`, where none is expected;
  - `find tests -name '*.pyi'` and a `tokenize` pass for `no_type_check`,
    `no_type_check_decorator` and `TYPE_CHECKING` names under `tests/`,
    where none is expected;
  - a `tokenize` pass for `noqa` comment tokens under `openspec_graph/` and
    `tools/`, where none naming a `D` code is expected;
  - `[tool.mypy]`'s key set, read with `tomllib`.

  Use a scratch cache directory or `/dev/null` for every mypy run, never the
  tree's `.mypy_cache`.
- Re-derive the code split from the re-measurement, not from this file. The
  override lists exactly those of R-TDR-2's seven that still occur. Every
  other code that occurs, and every error that only one platform reports, is
  fixed in Milestone 2 (R-TDR-3). If a sibling has added a code outside the
  sixteen, or a platform-only error, it joins the fixed set and is recorded
  here by site. If one of the seven is gone, it is not listed. If a stub, a
  `no_type_check` or a `TYPE_CHECKING` name has appeared, it is recorded
  here and raised with its author before Milestone 1, because the sibling
  guard would name it (DEC-TDR-016).
- Record the cold wall time of the type gate before the change, by the
  recipe's own command with a throwaway cache: `TIMEFORMAT='%R s'; time
  python -m mypy openspec_graph tools --cache-dir /dev/null`. It took 0.9 s
  at `e558eba`.
- Confirm the facts the decisions rest on:
  - the `Makefile` `typecheck` recipe still names two paths and no
    configuration file (DEC-TDR-001);
  - `.pre-commit-config.yaml`'s typecheck hook still has `types: [python]`
    and `pass_filenames: false`;
  - `ci.yml` still runs `make typecheck` in the `test` matrix and in
    `test-windows`, no job runs macOS, and it still runs on `pull_request`
    (DEC-TDR-005, DEC-TDR-013);
  - `python -c "import tomli"` fails here, and `tomli` is still the dev
    extra's 3.10-only entry (DEC-TDR-007);
  - `_pytest/py.typed` and `hypothesis/py.typed` exist (C-TDR-1);
  - the installed mypy accepts `-O json`, its `mypy.options.Options` still
    has `compile_glob`, and the dev extra's `mypy` entry is still unfloored
    (DEC-TDR-014, DEC-TDR-015);
  - the eight inline ignores of the proposal still carry `arg-type` or
    `attr-defined`;
  - `select-zero-cost-guards`' R-ZCG-3, DEC-ZCG-004, C-ZCG-2 and DEC-ZCG-012
    still read as quoted, and so does `shape-the-test-suite`'s C-TSS-6.
- **Gate:** `make validate`

## Milestone 1 — The mypy guards, seen red in the working tree (they land in the W6.5 commit)

- Write `tests/test_static_ratchets.py` (new) before any configuration
  change, and run it red (R-TDR-1, R-TDR-2, R-TDR-4, R-TDR-5, R-TDR-7,
  R-TDR-11, R-TDR-12, R-TDR-16, DEC-TDR-004, DEC-TDR-005, DEC-TDR-006,
  DEC-TDR-012, DEC-TDR-014, DEC-TDR-015, DEC-TDR-016). It holds:
  - a module docstring naming what the module holds, and that it verifies
    this package's criteria;
  - `MYPY_TESTS_CEILINGS: dict[str, int] = {}` and `MYPY_WAIVERS:
    tuple[tuple[str, str, str], ...] = ()`, each under the comment that
    R-TDR-4 or R-TDR-7 requires. `MYPY_WAIVERS`' comment states that an
    entry is removed, or re-keyed as R-TDR-7 defines, and never added.

  The pure helpers each take their input as an argument, so the planted
  test is `unit`:
  - **The recipe and key-set check.** The `typecheck` recipe's lines and a
    parsed `[tool.mypy]` table go in. Out come the offenders: a recipe that
    is not exactly `python -m mypy --config-file pyproject.toml`, a path
    argument, a missing or extra key, and a `files`, `mypy_path`,
    `explicit_package_bases`, `strict`, `warn_unreachable` or
    `python_version` that differs from R-TDR-1.
  - **The derived configuration.** A parsed `[tool.mypy]` table goes in,
    and mypy INI text comes out. Every global key but `files` is kept.
    Every override that does not apply to the tests becomes a
    `[mypy-<module>]` section. Booleans are written `True`/`False`, and
    lists are comma-joined.
  - **The JSON counter.** stdout, stderr and the return code go in. Out
    come the error objects, or the named failures: a nonempty stderr, an
    exit code other than 0 or 1, a non-blank stdout line that is not a JSON
    object, and an error without a code. Blank lines are skipped, so a
    clean run's lone newline reads as no errors. Only `severity == "error"`
    objects count, and only when their `file`, after `\` is normalised to
    `/`, is under `tests/`.
  - **The platform comparison.** Two runs' error objects go in, and every
    (file, line, code) that one has and the other lacks comes out, named as
    platform-only.
  - **The ceiling comparison.** The listed codes, the ceilings and the
    counts go in. Out come the named offenders: above the ceiling with both
    numbers; below it as `lower <code> from A to B`; stale; occurring but
    unlisted; listed without a ceiling; and a ceiling without a listed
    code. An absent override lists nothing.
  - **The comment reader.** A module's text goes in, read with `tokenize`.
    Out come four lists:
    - each `type: ignore` found inside a comment token by mypy's own
      pattern (`#\s*type:\s*ignore`), with its line and its bracketed codes,
      or none for a bare one;
    - each comment token whose text after `#` and whitespace begins with
      `mypy:`;
    - each physical line that begins with `# mypy: `;
    - each `NAME` token that is `no_type_check`, `no_type_check_decorator`
      or `TYPE_CHECKING`, with its line.
  - **The enclosing-function lookup.** A parsed module and a line go in, and
    the dotted name of the innermost `def` comes out, or `<module>`.
  - **The waiver comparison.** The ignores with their (path, function), the
    listed codes and `MYPY_WAIVERS` go in. Out come the unrecorded ignores,
    the recorded entries the tree lacks, and the malformed brackets: no
    code besides `unused-ignore` (a bare ignore among them), more than one,
    `unused-ignore` without a listed code, and a listed code without
    `unused-ignore`. One enforced code without `unused-ignore` is well
    formed.
  - **The override-scope matcher.** A `module` pattern and the dotted names
    of the modules under `tests/` go in. Out comes whether the pattern
    applies, decided by `mypy.options.Options().compile_glob(pattern)`
    matched against each name. Under it, `.*` matches zero or more
    components and a leading `*` matches any module, so
    `tests.*.test_graph` and `*` both apply.
  - **The dev-extra check.** The parsed `dev` list goes in. Out come the
    offenders: no `mypy` entry, a `mypy` entry whose specifier is not
    `>=1.11`, and any entry holding `==`.

  The module's own text must pass its own guard. Planted ignore and `# mypy:`
  text lives in single-line strings with `\n` escapes, so no line of the
  module begins with `# mypy: `, and no planted comment is a real one. The
  names `no_type_check`, `no_type_check_decorator` and `TYPE_CHECKING`
  appear only inside strings, never as `NAME` tokens.
- The planned tests are named here, so AC-TDR-3, 4, 5, 8, 9, 16 and 22 can
  be re-pointed when they exist.
  - `test_typecheck_reads_its_trees_from_the_mypy_files_list`
    (`integration`): the `typecheck` recipe's lines hold exactly `python -m
    mypy --config-file pyproject.toml` and no path argument; `[tool.mypy]`'s
    keys are exactly `files`, `explicit_package_bases`, `mypy_path`,
    `strict`, `warn_unreachable`, `python_version` and, while any override
    exists, `overrides`; `files` holds `openspec_graph`, `tools` and
    `tests`; `explicit_package_bases` is true; `mypy_path` holds `tools`;
    and `strict`, `warn_unreachable` and `python_version` are as R-TDR-1
    requires.
  - `test_the_tests_override_is_one_entry_listing_exactly_the_ceilinged_codes`
    (`integration`): at most one `[[tool.mypy.overrides]]` entry applies to
    a module under `tests/`, by the matcher above. While one does, its
    `module` is `tests.*`, its keys are exactly `module` and
    `disable_error_code`, its list is not empty, and its codes are a subset
    of R-TDR-2's seven and equal to `MYPY_TESTS_CEILINGS`' keys. With none,
    `MYPY_TESTS_CEILINGS` is empty. An override that applies to no test
    module is not judged.
  - `test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms`
    (`e2e`): the derived configuration is written under `tmp_path`. For
    each platform it runs `[sys.executable, "-m", "mypy", "--config-file",
    <it>, "--cache-dir", <tmp_path>/cache-<platform>, "--platform",
    <platform>, "-O", "json", "tests"]` from the repository root, under
    `env_without_coverage()`. Each run's stderr and exit code are checked,
    its output counted with blank lines skipped, the two platforms
    compared, and the counts compared to the ceilings.
  - `test_every_inline_ignore_is_a_recorded_waiver` (`integration`): every
    `.py` file under `tests/`. Its ignores are compared with `MYPY_WAIVERS`
    as multisets, and their brackets checked against the listed codes.
    Every `# mypy:` comment token or line is named, with its path and line.
  - `test_no_stub_or_unchecked_name_under_tests` (`integration`): every
    `.pyi` file under `tests/`, and every `no_type_check`,
    `no_type_check_decorator` or `TYPE_CHECKING` `NAME` token in a `.py`
    file under `tests/`, is named with its path and line (DEC-TDR-016).
  - `test_the_dev_extra_floors_mypy_and_pins_nothing` (`integration`):
    `read_pyproject()["project"]["optional-dependencies"]["dev"]` holds one
    entry for `mypy`, whose specifier is `>=1.11`, and no entry holding `==`
    (R-TDR-16).
  - `test_a_planted_ratchet_violation_is_named` (`unit`), one parameter
    per case of R-TDR-11's mypy half:
    - a stale code; a code occurring but unlisted; a code above its
      ceiling; a code below its ceiling, named `lower …`;
    - a code listed without a ceiling; a ceiling without a code;
    - a recipe of `python -m mypy` with no configuration file named; a
      recipe with a path argument; a `[tool.mypy]` table with `exclude`;
    - a second option on the tests override; a tests override with an
      empty list; overrides for `tests.test_graph`, `tests.*.test_graph`
      and `*`, each judged as applying to the tests;
    - a `note` object not counted, and an `error` object with `tests\`
      counted;
    - a non-JSON stdout line; an error without a code; a nonempty stderr;
      an exit code of 2;
    - two platforms' outputs that differ by one error;
    - a derived configuration from a planted table that keeps every option
      and drops the tests override;
    - a new `# type: ignore[no-untyped-def, unused-ignore]` that is not
      recorded; a recorded waiver that is gone; an ignore holding two codes
      besides `unused-ignore`; `unused-ignore` beside `index` with `index`
      unlisted; a listed code without `unused-ignore`; a bare
      `# type: ignore`; and `#type:ignore[...]` with no spaces, read;
    - a `# mypy: disable-error-code=...` comment, and a docstring line that
      begins with `# mypy: `;
    - a `.pyi` path under `tests/`; a `no_type_check` name; a
      `TYPE_CHECKING` name;
    - a `dev` list with a bare `mypy`; a `dev` list with `ruff==0.4.2`;
    - and the well-formed shape of each, quiet: among them, stdout `"\n"`
      with exit 0, and a recorded `# type: ignore[index]` with `index`
      unlisted.
- Run `python -m pytest tests/test_static_ratchets.py -q -o addopts=""` and
  record the red:
  - the recipe guard names the recipe's two paths, its missing
    `--config-file pyproject.toml`, the missing keys, and a `files` without
    `tests`;
  - the occurrence guard names every occurring code as unlisted, and the
    `os.mkfifo` errors as platform-only;
  - the waiver guard names every inline ignore of the tree as unrecorded.
    There are ten at `e558eba`, by `grep -n "type: ignore" tests/*.py`;
  - the dev-extra guard names the unfloored `mypy` entry.

  Record that the override guard passes here, because no override and no
  ceiling is R-TDR-2's clean end state; its red run is taken in Milestone 2
  (R-TDR-11). Record that the stub-and-name guard passes from its first
  run, as Milestone 0's measurement predicts. Record whether the planted
  test passes from its first run, since its helpers are written with it.
- Run `python -m pytest tests/test_suite_shape.py -q -o addopts=""`, and
  record that the new module's tiers agree with the criterion, the dev-extra
  guard's `integration` among them. Record `wc -l
  tests/test_static_ratchets.py` against DEC-TDR-012's budget.
- Nothing is committed at the end of this milestone. Its work lands in the
  W6.5 commit, with the change it covers.
- **Gate:** `make test`. Exactly this milestone's red guards fail; that is
  recorded here, and the tree is not committed in that state.

## Milestone 2 — The nine codes and the platform-only errors fixed, the override landed with its ceilings and waivers (the W6.5 commit)

- Fix the nine codes in `tests/`, each by annotation, narrowing, a typed
  local or a corrected call. A fix is never a new ignore, a `# mypy:`
  comment, a stub, a `no_type_check`, a `TYPE_CHECKING` branch, a cast to
  `Any`, a `noqa` or a removed assertion (R-TDR-3, C-TDR-3). The sites, at
  `e558eba`:
  - `tests/support.py` `read_pyproject`: `if sys.version_info >= (3, 11):
    import tomllib as toml_reader` / `else: import tomli as toml_reader`,
    with no inline ignore, then `parsed: dict[str, Any] =
    toml_reader.load(handle)` and `return parsed` (R-TDR-6). This clears
    `import-not-found`, the `unused-ignore` and one `no-any-return`.
  - `tests/conftest.py` `_reset_version_cache` becomes `-> Iterator[None]`.
  - `tests/shape_support.py:590` `_class_facts`: the `nodes` list is typed
    so that `cls.bases` and `cls.decorator_list` (`list[expr]`) fit.
  - `tests/test_mermaid.py`: the three single-node lists and `_graph`'s
    parameters are typed so a `dict[str, str]` node is accepted, either as
    a `Sequence` of `Mapping[str, object]` or with the node annotated where
    it is built.
  - `tests/test_dialect_card.py` `test_diff_cards_detects_an_adr_source_change`:
    `old` and `new` are annotated as the `dict[str, object]` that
    `diff_cards` takes.
  - `tests/test_suite_shape.py:555`
    `test_a_mismarked_or_unmarked_planted_module_is_named`: the `str | None`
    is narrowed before the `in`.
  - `tests/test_cli_surface.py`
    `test_run_cli_injects_coverage_process_start_by_default`: the captured
    `env` is narrowed to a mapping before the `in`.
  - `tests/test_graph.py` `test_graph_covers_every_parsed_spec_when_multiple`:
    `graph["nodes"]` is narrowed to a list of mappings before the generator.
  - `tests/test_finding_line_hits.py`
    `test_section_body_still_returns_only_the_span_text`: the `not
    isinstance(result, tuple)` assertion is kept, written so mypy does not
    judge it unreachable, with the result widened to `object` for that
    check.
  - `tests/test_action_contract.py`
    `test_the_step_extractor_sees_the_whole_action`: `scan["env"]` is
    narrowed to a mapping before `set(...)`.
  - `tests/test_graft_witness.py` `spy` in
    `test_current_sha_is_not_invoked_when_no_witnesses_are_present`: the
    spy's parameters and return are typed so that `original_run(*args,
    **kwargs)` matches an overload, and its stale `arg-type` ignore is
    removed, since it was unused before any override.

  Every edited test keeps its assertions. A fix that narrows with `assert
  isinstance(...)` adds an assertion and removes none.
- Fix the platform-only errors (R-TDR-3, DEC-TDR-003). At `e558eba` they are
  in `tests/test_detect_thresholds.py`:
  - add a module-level `_MKFIFO: Callable[[Path], None] | None =
    getattr(os, "mkfifo", None)`, importing `Callable` from
    `collections.abc`;
  - give each of the three tests `assert _MKFIFO is not None` before its
    `_MKFIFO(...)` calls, which were the four `os.mkfifo` sites;
  - make the `skipif` condition `_MKFIFO is None`, with its reason
    unchanged.

  Record `wc -l` after.
- Re-run the guard's measurement by hand with nothing listed: `MYPYPATH=tools
  python -m mypy tests --explicit-package-bases -O json --cache-dir
  /dev/null`, under `--platform linux` and under `--platform win32`. Record
  that none of the nine codes occurs, that the two error sets are equal,
  that stderr is empty, and the seven's per-code counts. These are the
  counts the commit records: the plan's "per-code counts so the list only
  shrinks".
- Fill `MYPY_TESTS_CEILINGS` from the occurrence guard's own failure
  messages on this tree: with the constant empty, they name each code's
  count. Then run the override guard and record its red: with the ceilings
  filled and no override yet, it names each ceiling as one without a listed
  code (R-TDR-11).
- `pyproject.toml`:
  - `[tool.mypy]`: `files`, `explicit_package_bases`, `mypy_path` and the
    two overrides of the proposal's What Changes, each with its comment, and
    no other key;
  - the dev extra's `"mypy"` becomes `"mypy>=1.11"`, under a comment naming
    1.11 as the release that added `-O json` and
    `tests/test_static_ratchets.py` as the reader (R-TDR-16,
    DEC-TDR-014).

  `Makefile`: the `typecheck` recipe becomes `python -m mypy --config-file
  pyproject.toml`, with help text naming `[tool.mypy] files`.

  Run `make typecheck`, and record the eight `unused-ignore` it then
  reports, which is the expected red of R-TDR-7. Then give each of the
  eight comments `unused-ignore` beside its code (DEC-TDR-006), and re-run:
  exit 0.
- Fill `MYPY_WAIVERS` from the waiver guard's own failure messages on this
  tree, which name each unrecorded waiver. Record both constants here with
  the commit. At `e558eba` the waivers are the proposal's eight (path,
  function, code) triples.
- Run `python -m pytest tests/test_static_ratchets.py
  tests/test_ci_workflow.py tests/test_enterprise.py
  tests/test_threshold_guard.py -q -o addopts=""` and record it green. Among
  the tests it runs:
  - `test_a_bare_generic_in_tools_fails_typecheck` and
    `test_mypy_fails_on_a_type_error`, the planted-tree tests, now under a
    copy of the new configuration (AC-TDR-2);
  - `test_typecheck_passes_on_clean_repo`, which now checks `tests/` too
    (AC-TDR-1);
  - `test_the_dev_extra_floors_mypy_and_pins_nothing`, with the floor in
    place (AC-TDR-22);
  - `test_threshold_guard_fails_on_a_pinned_tool_version`, unchanged.

  Record the call durations of the occurrence guard and of
  `test_typecheck_passes_on_clean_repo` from `--durations=0` over that
  selection. Record the type gate's cold wall time after the change,
  `TIMEFORMAT='%R s'; time python -m mypy --config-file pyproject.toml
  --cache-dir /dev/null`; the emulation at `e558eba` took 3.7 s.
- `CHANGELOG.md` `[Unreleased]`: add `### Changed — tests under mypy,
  public docstrings by ratchet (M2)`, the W6.5 half. It names:
  - the three trees, read from `files` in the configuration file the recipe
    names;
  - the search path, and why it is needed;
  - the override's codes, with their ceilings;
  - the nine codes and the platform-only errors, fixed instead of listed;
  - the `tomli` override;
  - the waivers;
  - the mypy floor;
  - the guard module;
  - R-ZCG-3's `files` clause and DEC-ZCG-004's "table that remains"
    sentence, superseded by name (R-TDR-14, R-TDR-15).
- Run `make pre-pr`, and record the exit code. Commit: this is the W6.5
  commit, with the ceilings and the waivers named in the message.
- Push this commit alone. Record its CI run: the type gate and the mypy
  occurrence and waiver guards are green on every `test` leg and on
  `test-windows`, with the run id, the head SHA it ran for and the merge
  SHA it tested (AC-TDR-20, C-TDR-5). A leg that differs is a fact about
  the leg, and is recorded here. It is fixed in a follow-up commit, which is
  also `make pre-pr` green, before Milestone 3, and never by raising a
  ceiling. The exception is DEC-TDR-004's case of a mypy release that
  changes a count, and that edit names the release.
- **Gate:** `make pre-pr`

## Milestone 3 — Docstrings by ratchet, guards seen red first (the W6.6 commit)

- Extend `tests/test_static_ratchets.py` before the configuration, and run
  it red (R-TDR-8, R-TDR-9, R-TDR-11, DEC-TDR-008, DEC-TDR-009):
  - a `DOCSTRING_CEILINGS: dict[str, dict[str, int]] = {}`, under R-TDR-9's
    comment;
  - a pure helper for the configuration's shape: a parsed `[tool.ruff.lint]`
    table goes in, and the offenders come out, from `select`,
    `per-file-ignores` and `extend-per-file-ignores`;
  - a pure helper for `noqa` comments: a module's text goes in, read with
    `tokenize`, and out comes each comment token holding a `noqa`
    directive, at file level (`# ruff: noqa: …`, `# flake8: noqa: …`) or on
    a line, that names a `D` code, with its line;
  - a pure helper for ruff's JSON: the findings, a root, stderr and the
    return code go in. Out comes a file-to-code-to-count mapping, with
    paths relative and in POSIX form, or a named failure for a nonempty
    stderr or a nonzero exit.

  The planned tests are named here, so AC-TDR-10, 12, 13 and 14 can be
  re-pointed:
  - `test_docstring_exemptions_are_file_entries_matching_their_ceilings`
    (`integration`). Among the `D` rules, `select` holds exactly `D100`,
    `D101`, `D102` and `D103`. Every `D` code sits under a concrete file
    key under `openspec_graph/` or `tools/`, or under `tests/*`, which
    carries all four. No `D` code sits in `extend-per-file-ignores`. No
    comment token of a `.py` file under `openspec_graph/` or `tools/` holds
    a `noqa` naming a `D` code. The ratchet pairs equal
    `DOCSTRING_CEILINGS`' pairs. There is no `[tool.ruff.lint.pydocstyle]`
    table.
  - `test_every_docstring_exemption_matches_its_ceiling` (`e2e`). It runs
    `[sys.executable, "-m", "ruff", "check", "--no-cache", "--isolated",
    "--ignore-noqa", "--select", "D100,D101,D102,D103", "--output-format",
    "json", "--exit-zero", "openspec_graph", "tools"]` from the repository
    root, under `env_without_coverage()`. It checks exit 0 and empty
    stderr, counts the findings, and compares them exactly: stale, above
    the ceiling, below it as `lower …`, and offending but unlisted.
  - The docstring half of `test_a_planted_ratchet_violation_is_named`:
    - a pair with no finding; a pair offending but unlisted; a pair above
      its ceiling; a pair below its ceiling; a pair without a ceiling;
    - a `D` code under `openspec_graph/*`; a `D` code under
      `tests/test_x.py`; a `D` code under `extend-per-file-ignores`;
    - a module whose first line is `# ruff: noqa: D103`; a `def` line
      ending `# noqa: D103`;
    - a Windows path in ruff's JSON, normalised; a nonempty ruff stderr;
    - and the well-formed shape of each, quiet, among them a `# noqa: S607`
      comment, which names no `D` code.

  Record the red: the shape guard finds `D` unselected, and the occurrence
  guard names every offending pair as unlisted.
- `pyproject.toml`:
  - the `select` entries, under their comment. The comment records that the
    `D100`–`D103` finding set is identical under no convention and under
    each of the three, and that Google is the best fit of the wider family.
    Both are given with their commands, and the comment does not call
    Google the convention the docstrings follow (R-TDR-10, DEC-TDR-010);
  - the header sentence about zero-violation families, rewritten to name
    the four as the ratchet;
  - the `ANN/D` comment, rewritten;
  - `tests/*` gains the four codes;
  - one entry per offending file of Milestone 0's list, with exactly its
    codes, and `cli.py`'s joining its `T201` entry;
  - a comment above the entries, naming the ratchet and the guard, and
    stating that an entry leaves in the pull request that documents its
    file.

  No convention key and no `extend-per-file-ignores` table is added.
- Fill `DOCSTRING_CEILINGS` from the occurrence guard's measurement, and
  record it here with the commit. Run `make lint` (exit 0). Run `python -m
  pytest tests/test_static_ratchets.py tests/test_ci_workflow.py -q -o
  addopts=""` and record it green, with
  `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt` and
  `test_a_print_in_a_library_module_fails_lint` among the tests run
  (AC-TDR-10, AC-TDR-11). Record the docstring guard's call duration, and
  `wc -l tests/test_static_ratchets.py` against the 600-line budget. If the
  module is over budget, split it as DEC-TDR-012 says before committing.
- `CHANGELOG.md`, the W6.6 half: the four codes; the per-file entries, with
  their count; the `tests/` policy exemption and why; the count taken with
  no configuration and no `noqa`; the convention measured, recorded and not
  configured; and the "ratchet first" step of DEC-ZCG-012.
- Run `make pre-pr`, and record the exit code. Commit: this is the W6.6
  commit. Push it alone, and record its CI run: the lint gate and the
  docstring guards are green on every `test` leg and on `test-windows`,
  with the run id, the head SHA it ran for and the merge SHA it tested
  (AC-TDR-21, C-TDR-5). This is recorded separately from Milestone 2's run.
- **Gate:** `make pre-pr`

## Milestone 4 — Documents, records and the verification lines (the documents commit)

- `docs/hooks.md:19` becomes: `make typecheck` (mypy) across
  `openspec_graph/`, `tools/`, `tests/`, with `tests/` under a per-code
  baseline in `[[tool.mypy.overrides]]`.
- `tests/AGENTS.md` gets one sentence: `make typecheck` covers this
  directory, and a new occurrence of an exempted code, or a new inline
  ignore, fails `test_static_ratchets.py`. Write it by replacing, not
  adding. The closing run paragraph's five lines can carry it in five, for
  example by folding "`make coverage-tools` re-reads `tools/` from the same
  report. The `planlint-verifier` subagent runs the whole ladder." into one
  line. Record `wc -l` after, against `MAX_NESTED_LINES`.
- `.claude/agents/planlint-verifier.md:28`: the `ruff`/`mypy` bullet names
  the standing configuration and the remediation norm of R-TDR-13, in the
  shape of the coverage and matcher-floor bullets beside it.
- Run `python -m pytest tests/test_agent_artifacts.py -q -k "nested_agents
  or agent_index_links"` and `make docs-check`, and record both green.
- Re-point the stage-only verification lines in
  `specs/static-check-ratchets/spec.md` to the guards, now that they exist.
  Each line keeps its stage, and AC-TDR-10, AC-TDR-14 and AC-TDR-16 keep
  the selectors they already have:

  | Criterion | Selector added |
  |---|---|
  | AC-TDR-3 | `test_typecheck_reads_its_trees_from_the_mypy_files_list` |
  | AC-TDR-4 | `test_the_tests_override_is_one_entry_listing_exactly_the_ceilinged_codes` |
  | AC-TDR-5 | `test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms` |
  | AC-TDR-8 | `test_every_inline_ignore_is_a_recorded_waiver` and `test_no_stub_or_unchecked_name_under_tests` |
  | AC-TDR-9 | `test_a_planted_ratchet_violation_is_named` |
  | AC-TDR-10 | `test_docstring_exemptions_are_file_entries_matching_their_ceilings`, beside its two existing selectors (exactly `D100`–`D103` among `D` rules; `D` codes only on concrete package and tool files plus `tests/*`; none in `extend-per-file-ignores` or a `noqa`) |
  | AC-TDR-12 | `test_docstring_exemptions_are_file_entries_matching_their_ceilings` and `test_every_docstring_exemption_matches_its_ceiling` |
  | AC-TDR-13 | `test_a_planted_ratchet_violation_is_named` |
  | AC-TDR-14 | `test_docstring_exemptions_are_file_entries_matching_their_ceilings` (no `pydocstyle` table; no `D` rule beyond the four) |
  | AC-TDR-16 | `test_the_dev_extra_floors_mypy_and_pins_nothing`, beside its five existing selectors (the dev-extra half of "no tool version is pinned") |
  | AC-TDR-22 | `test_the_dev_extra_floors_mypy_and_pins_nothing` |

  Run `python -m pytest tests/test_spec_test_citations.py -q -p
  no:cacheprovider`, and record that every selector in every spec resolves.
- Confirm that this package validates clean, `planlint --target . validate
  --fail-on ERROR --change ratchet-test-types-and-docstrings`. Then run it
  with `--change select-zero-cost-guards` and with `--change
  shape-the-test-suite`, which are unedited and must still be clean. Then
  validate the whole tree. Record each exit code.
- Confirm the boundaries in the diff against the branch base:
  - no file under `openspec_graph/`, `.github/` or another change package;
  - no `.pre-commit-config.yaml` hunk;
  - the only `Makefile` hunk is the `typecheck` target's help text and
    recipe;
  - the only dev-extra hunk is the `mypy` floor, and no `[project]
    dependencies` line changes (C-TDR-1, C-TDR-2).

  `make thresholds` prints PASS. Record `make stage-citations` after,
  noting that its figures include this package's spec.
- Re-take the header's measurements on the finished tree, with the commit:
  - the per-code counts under both platforms, with the override lifted.
    These are equal to each other and to the ceilings;
  - `MYPY_WAIVERS` against `grep -n "type: ignore" tests/*.py`;
  - the per-file docstring counts, equal to their ceilings;
  - `wc -l tests/AGENTS.md`, and the new module's line count;
  - the guards' durations.
- Tick each criterion only against its recorded evidence. Tick AC-TDR-20
  only with the CI run id, head SHA and merge SHA of Milestone 2, and
  AC-TDR-21 only with those of Milestone 3.
- Record for the plan's §7 rows, when they are next updated:
  - tests under mypy, with the override's codes and ceilings as recorded
    here, in place of the plan's own §7 tally;
  - public symbols without a docstring, as the package's and `tools/`'s
    ceilings, with `tests/` exempt by policy.
- Run `make pre-pr`, and record the exit code. Commit: this is the
  documents commit.
- **Gate:** `make pre-pr`
