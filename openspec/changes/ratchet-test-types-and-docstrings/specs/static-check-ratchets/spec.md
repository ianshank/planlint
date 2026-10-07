# Spec: Static-Check Ratchets

> **Change:** `ratchet-test-types-and-docstrings`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Two static checks stop short of code this repository depends on. mypy runs
strict over `openspec_graph/` and `tools/` and never over `tests/`: the
`typecheck` recipe names the two trees on its command line and
`[tool.mypy] files` names the same two, so a helper in `tests/support.py`
whose signature drifts from its callers is found by whichever test trips on
it, if one does, and never before. And ruff selects no docstring rule, so a
public function, method or class of the package ships undocumented and
nothing says so. Both debts are measured, both are too large to clear in one
change, and both are therefore ratchets in the plan's D1 sense: configured at
today's state, green on the first commit, every unlisted case enforced from
that commit, and the listed state allowed only to shrink.

Neither ratchet can be configured the way the plan describes it. Adding
`tests` to `files` with `explicit_package_bases = true` turns today's clean
`tools/` run red, because explicit bases rename `tools/_common.py` to
`tools._common` while every gate script imports it as `_common`; and the
recipe would not read `files` anyway, because positional paths override it.
The plan's tally predates the suite's split and its tiers, and one of its
codes, `str`, is not a mypy error code at all. Disabling codes for `tests.*`
makes the inline ignores that suppress those codes redundant, which strict
mode reports. The tests' one TOML import is checked on its 3.10 branch on
every leg, so its verdict depends on whether the leg installed `tomli`. A
per-code count taken on Linux is not the count on Windows, and the
difference is debt that only the Windows leg's type gate could see, which
the override would then hide there too.

Nor does a count that only caps from above hold the line. An inline
`# type: ignore[<code>, unused-ignore]` beside a listed code, a bare
`# type: ignore` at the top of a module, or a `# mypy: disable-error-code=…`
comment lowers a count as surely as a code added to the override would. So,
with no comment at all, do a stub beside a module, `no_type_check`, a branch
that mypy judges unreachable from a version or platform check, a global
`exclude`, and an override that reaches a test module in a spelling a
pattern matcher misreads. A count taken with `tests` passed as a path moves
with a `follow_imports` override on the package and with an ambient
`MYPYPATH`. On the ruff side, a `noqa` comment, an `extend-per-file-ignores`
entry or an ignore file lowers a docstring count while the ratchet entries
stay as they are. A stray `mypy.ini` or `.mypy.ini` replaces the whole mypy
configuration for a run that does not name its file, `files` with it. A
count that falls below its ceiling leaves room for new debt until someone
remembers to lower it. And a ruff exemption, like a disabled mypy code, is
silent once it exempts nothing, so nothing would ever force either list to
shrink.

So this spec names the configuration file in the type gate's recipe, names
the trees once in `files`, holds `[tool.mypy]` to an exact key set, and gives
mypy the module bases the scripts and the suite actually run with. It fixes
in `tests/` every code that is cheaper to fix than to exempt, and every
error that only one platform reports. It lists the rest in at most one
`tests.*` override, asks mypy itself what every override does to every test
module, and holds every listed code to a recorded count, taken by the gate's
own run less that one entry, which the guard requires to match exactly and
on both platforms. It records every inline ignore as a shrink-only waiver
keyed by the line it waives, and refuses every comment, stub, name or
condition that would hide code from mypy. It selects `D100`–`D103` with one
exemption per offending file of the package and `tools/`, each held to an
exact recorded count that ruff takes with no configuration file, no ignore
file and no `noqa` honoured. It floors mypy at the release whose JSON output
the guard reads. It records rather than configures the docstring
convention. And it states what the guards defend against, and what they
leave to review (DEC-TDR-017).

**Evidence:** measured on 2026-10-07 at `e558eba` (`claude/m2-tests-under-mypy`,
based on `main` at `46ae1b3`, where #42 was squash-merged), and for the
round-3 points at `25c65de`, the round-2 revision's commit of this package on
that branch. The earlier drafts measured at `1c8917c` and `d2b3cc6`, neither
of which is an ancestor of the branch; the headline figures re-taken since
match theirs. Every figure here names its command, and the proposal gives
each one in full. `python -m mypy tests --explicit-package-bases` reports
185 errors in 32 files (61 checked). Counted by the trailing code of
`error:` lines only, those are sixteen codes, of which `no-untyped-def`,
`attr-defined`, `arg-type`, `type-arg`, `no-any-return`, `index` and
`union-attr` hold all but fifteen occurrences. The bracketed `str` and
`bytes` that a looser tally finds are the `PathLike[str]` of `note:` lines.
Without explicit bases, mypy stops at "Source file found twice under
different module names" for `tests/graft_support.py` and exits 2. `python -m
mypy openspec_graph tools --explicit-package-bases` reports 19 errors in 12
files where today's command reports none. With `tools` on the module search
path it reports none again, and the tests' count falls to 184. A
gate-shaped JSON run, with `files` naming the three trees and no path given,
reports 184 errors under `tests/` with `--platform linux` and 188 with
`--platform win32`, the four extra all `attr-defined` on `os.mkfifo` in
`tests/test_detect_thresholds.py`; both runs leave stderr empty and exit 1.
A run with nothing to report prints one newline and exits 0. A
`# mypy: disable-error-code="no-untyped-def"` line at the head of
`tests/test_graph.py`, stood in by `--shadow-file`, takes `no-untyped-def`
from 96 to 72, which reproduces the round-1 reviewer's figure. So do a
global `exclude` of that file and an override for it spelled
`tests/test_graph`, `openspec_graph.cli,tests.test_graph`, as a list, or as
`tests.*.test_graph`; mypy's own `clone_for_module` reports all four
spellings as applying, and mypy's `compile_glob` misses the first two. With
`tests` passed as a path, a `follow_imports = "skip"` override on two
package modules takes `attr-defined` from 19 to 7, and an ambient `MYPYPATH`
moves the count; with `files` kept and no path, the override does not, and
a stub on `MYPYPATH` still does. An untyped `def` under ten forms of version,
platform or name check passes `--strict --warn-unreachable`. In a probe
tree, a planted `.mypy.ini` or `mypy.ini` replaced `pyproject.toml` for a
bare `python -m mypy`, and `--config-file pyproject.toml` ignored it. With
the seven codes disabled for `tests.*`, the residue is 23 errors in 15
files: the fifteen occurrences, plus eight inline `# type: ignore[arg-type]`
or `[attr-defined]` comments that the override makes redundant. A
command-line `--enable-error-code` does not lift a per-module
`disable_error_code`. `python -m ruff check --select D100,D101,D102,D103
--statistics` reports 52 findings in 18 files of `openspec_graph/`, 25 in 12
files of `tools/` and 584 in `tests/`, 575 of them test functions. The
sorted finding set is identical under no `pydocstyle` convention and under
each of the three. A stale `per-file-ignores` entry draws no ruff warning.
With the repository's configuration and `per-file-ignores` cleared, a
file-level `# ruff: noqa: D103`, a line-level `# noqa: D103` and an
`extend-per-file-ignores` entry each lower `openspec_graph/cli.py`'s count;
under `--isolated --ignore-noqa` none of them does, but an `.ignore` file
still hides a module, which `--no-respect-gitignore` undoes.

---

## Requirements

- R-TDR-1: `[tool.mypy] files` MUST list `openspec_graph`, `tools` and
  `tests`, and `[tool.mypy]` MUST set `explicit_package_bases = true` and a
  `mypy_path` that names `tools` and nothing else, written `"tools"` or
  `["tools"]`, which mypy parses alike as exactly `["tools"]`. `strict =
  true`, `warn_unreachable = true` and `python_version = "3.10"` MUST be
  unchanged. Those six MUST be the table's only keys, with `overrides`
  beside them while any per-module override exists, so that no global
  option, `exclude` among them, narrows what is checked without an edit to
  the guard that holds the set (DEC-TDR-016). The `typecheck` recipe MUST be
  `python -m mypy --config-file pyproject.toml`, with no path argument. It
  names its configuration file because mypy reads a `mypy.ini` or
  `.mypy.ini` ahead of `pyproject.toml`, and a stray one would otherwise
  replace the whole configuration, `files` with it. It passes no path, so
  `files` is the one list of checked trees and a tree is added by a
  configuration line. The type gate, `make typecheck`, MUST exit 0 on the
  tree after this change and MUST still check `openspec_graph/` and `tools/`
  under strict, and this change MUST add no per-module option for either. A
  guard test MUST read the recipe and the table structurally and assert the
  recipe, the key set, the three trees, the two module-base options and the
  three unchanged options.
- R-TDR-2: What an override does to the tests MUST be decided by mypy
  itself, and by no matcher of the guard's own. A guard test MUST load
  `pyproject.toml` as mypy's command line does, through
  `mypy.main.process_options(["--config-file", "pyproject.toml"],
  require_targets=False)`, which calls mypy's `parse_config_file` with the
  callback that applies `strict`, and MUST name anything that call writes to
  stderr. For every module under `tests/`, named `tests.<stem>` for each
  `.py` file there (the directory is flat), it compares `Options.snapshot()`
  of the global options with that of `clone_for_module(<module>)`.
  - Only `disable_error_code` and `disabled_error_codes` MAY differ, and the
    codes in the module's `disabled_error_codes` and not in the global one
    MUST be exactly the listed codes. Every other differing field is named
    with its module, the field and both values: `follow_imports`,
    `ignore_errors`, `always_false`, a strict flag, an enabled code, an
    extra disabled code or any other. The one field the comparison ignores
    is `unused_configs`, the bookkeeping that mypy 1.11.0 exposes in the
    snapshot (DEC-TDR-015).
  - The listed codes MUST sit in at most one `[[tool.mypy.overrides]]`
    entry, spelled exactly `module = "tests.*"` or `module = ["tests.*"]`,
    whose only other key MUST be a `disable_error_code` holding at least one
    code. The commit that empties that list MUST remove the entry. With that
    entry removed, no module under `tests/` MAY have options that differ
    from the global options at all; R-TDR-5's derived configuration is
    where that is checked.
  - The list MUST be a subset of `no-untyped-def`, `attr-defined`,
    `arg-type`, `type-arg`, `no-any-return`, `index` and `union-attr`,
    holding exactly those of the seven that still occur when the entry
    lands, and no other code MAY ever be added to it. So every code the
    entry does not list is enforced in `tests/` under the global strict
    configuration from the commit that lands it.
  - An override that changes no test module's options, such as the `tomli`
    one of R-TDR-6 or one for a module of the package or of `tools/`, is
    outside this requirement (DEC-TDR-015).
- R-TDR-3: Every code outside R-TDR-2's seven that occurs in `tests/` at
  Milestone 0's re-measurement MUST be fixed in `tests/` before the
  override lands, and never listed. At drafting those codes are
  `assignment`, `call-overload`, `import-not-found`, `list-item`, `misc`,
  `operator`, `unreachable`, `unused-ignore` and `var-annotated`. So MUST
  every error that mypy reports under one of `--platform linux` and
  `--platform win32` and not under the other, whatever its code, so that
  every module type-checks the same under both. At drafting that is the
  `attr-defined` on `os.mkfifo` in `tests/test_detect_thresholds.py`,
  which only the Windows view reports. A fix MUST NOT be a new
  `# type: ignore`, a `# mypy:` comment, a stub, a `no_type_check`, a
  branch that mypy treats as unreachable, a `cast` to `Any`, a `# noqa` or
  a removed assertion: it is an annotation, a narrowing, a typed local or a
  corrected call. The `check_wheel_metadata` import of
  `tests/test_wheel_metadata.py` is resolved by R-TDR-1's `mypy_path`, not
  by an ignore.
- R-TDR-4: `tests/test_static_ratchets.py` MUST hold a module-level
  `MYPY_TESTS_CEILINGS` that maps each code the override lists to its
  occurrence count in `tests/`, as R-TDR-5's reader measures it at the
  commit that lands the override. A comment above it MUST state the rule.
  An entry is lowered or removed in the commit that changes its count, and
  is never added. It is raised only to follow a mypy release that changes
  the count of unchanged code, in the pull request where the guard first
  names that change, with the release named beside the entry
  (DEC-TDR-004). A guard test MUST assert that the override's list and the
  mapping's keys are the same set, an absent override listing nothing, and
  name a listed code without a ceiling and a ceiling without a listed code.
- R-TDR-5: A guard test MUST measure every code's occurrences with the
  gate's own run, less the tests entry.
  - It derives a configuration file under its own temporary directory that
    keeps every key of `[tool.mypy]`, `files` among them, and every other
    override, and drops only the entry R-TDR-2 allows. Before running, it
    loads that file with the same `process_options` call as R-TDR-2, and
    MUST find its global options equal to `pyproject.toml`'s but for
    `config_file` and `per_module_options`, its per-module options equal to
    `pyproject.toml`'s less the tests entry, and no module under `tests/`
    whose options differ from the global options in any field but
    `unused_configs`. It names each difference.
  - It runs mypy with `--config-file` naming that file and no path
    argument, so that `files` decides what is checked, as it does for the
    gate. It passes `-O json`, runs from the repository root, once with
    `--platform linux` and once with `--platform win32`, each with its own
    cache directory under that temporary directory, in an environment that
    is `env_without_coverage()` with `MYPYPATH` also removed.
  - Each run MUST leave stderr empty and exit 0 or 1, and the guard MUST
    name a run that does not. It MUST read stdout as one JSON object per
    non-blank line, skipping blank lines, because a run with nothing to
    report prints a single newline; and it MUST name a non-blank line that
    is not a JSON object. It MUST count, by their `code` field, only
    objects whose `severity` is `error` and whose `file`, with path
    separators normalised, is under `tests/`, and it MUST name an error
    without a code.
  - It MUST name every error that one platform reports and the other does
    not, with its file, line and code, as a platform-only error to fix
    under R-TDR-3 and never as a reason to list a code. It MUST fail
    whenever a code's count differs from its ceiling, in either direction:
    - a count above its ceiling is named with both numbers;
    - a count below its ceiling is named in the form `lower <code> from A
      to B`;
    - a listed code with no occurrence is named as stale, and the commit
      that fixed its last occurrence MUST remove it from the override and
      from the ceilings;
    - a code that occurs but is not listed is named.
- R-TDR-6: `tests/support.py`'s `pyproject.toml` reader MUST choose
  `tomllib` or `tomli` by `sys.version_info`, not by catching
  `ModuleNotFoundError`, and MUST return the parsed table through an
  annotated local. An override for `module = "tomli"` MUST set
  `ignore_missing_imports = true`, and that import MUST carry no inline
  ignore. mypy's verdict over `tests/` MUST then be the same on the leg that
  installs `tomli` and on the legs that do not.
- R-TDR-7: Every inline `# type: ignore` comment in a `.py` file under
  `tests/`, bracketed or bare, MUST be a recorded waiver.
  `tests/test_static_ratchets.py` MUST hold a module-level `MYPY_WAIVERS`
  of (path, code, waived line) entries, under a comment stating that an
  entry is removed and never added, and that a commit which edits a waived
  line's text updates that entry's text in the same commit. The waived line
  is the text of the physical line that holds the comment, with the comment
  token removed, every run of whitespace collapsed to one space, and both
  ends stripped. A guard test MUST assert that the waivers it reads from
  the tree and the recorded entries are equal as multisets. It MUST name
  each unrecorded comment with its path and line, and each recorded entry
  the tree no longer holds.
  - A waiver's brackets MUST hold exactly one code besides `unused-ignore`,
    and that code is the entry's code. While the code is listed,
    `unused-ignore` MUST sit beside it; once the code is enforced,
    `unused-ignore` MUST NOT. The guard names an ignore holding no code
    besides `unused-ignore`, a bare one among them; an ignore holding more
    than one; `unused-ignore` without a listed code; and a listed code
    without `unused-ignore`. A recorded ignore of exactly one enforced
    code, without `unused-ignore`, is a well-formed waiver.
  - Renaming the enclosing function, or moving the waived line within its
    file, leaves the key alone, so neither needs an edit to
    `MYPY_WAIVERS`. Moving the waived line to another file changes only the
    entry's path, in the same commit. Moving the comment to another line
    changes the key's text, so the guard names the comment as unrecorded
    and the entry as missing. The gaps this keying leaves are DEC-TDR-017's.
  - The inline ignores that the override makes redundant are the waivers.
    Each MUST keep its code and gain `unused-ignore`, and none MAY be
    deleted or have its code changed, because each records a review
    decision of the package that wrote it and is needed again when its code
    is re-enabled.
  - When a code leaves the override, the commit that removes it MUST strip
    `unused-ignore` from that code's waivers and keep their entries. Each
    then holds exactly its one enforced code, so strict mode reports it
    once it is unused.
  - An ignore that is unused even without the override is a defect rather
    than a decision, and is fixed under R-TDR-3.
  - The same guard MUST name every comment under `tests/` that configures
    mypy. That is every comment token, found with `tokenize`, whose text
    after the `#` and any whitespace begins with `mypy:`, and every
    physical line that begins with mypy's own inline-configuration prefix,
    `# mypy: `, because releases that R-TDR-16's floor admits honour such a
    line inside a string literal (DEC-TDR-006).
  - The guard MUST read comments with `tokenize`, not by a substring search
    over the source, and MUST find an ignore inside a comment token as
    mypy's own pattern finds it, so `#type:ignore[...]` is read
    (DEC-TDR-006).
  - The same guard, or a sibling in the same module, MUST name each of the
    following with its path and line, because each hides code from mypy
    with no comment and no override (DEC-TDR-016):
    - every `.pyi` file under `openspec_graph/`, `tools/` or `tests/`;
    - every `NAME` token of a `.py` file under `tests/`, found with
      `tokenize`, that is `no_type_check`, `no_type_check_decorator`,
      `TYPE_CHECKING`, `MYPY`, `PY2` or `PY3`;
    - every test of an `if` or `elif`, a `while`, a conditional expression
      or an `assert`, and every `match` case guard, in a `.py` file under
      `tests/`, read with `ast`, that refers to `sys.version_info` or
      `sys.platform`. The one exception is the version check R-TDR-6
      requires, recorded by path and function as `tests/support.py`'s
      `read_pyproject` and allowed there once.
- R-TDR-8: `[tool.ruff.lint] select` MUST include `D100`, `D101`, `D102` and
  `D103` and no other `D` rule. In `[tool.ruff.lint.per-file-ignores]` a `D`
  code MAY appear only in two places. One is under a key that is one
  concrete file path under `openspec_graph/` or `tools/`, listing exactly
  the codes among the four that the file violates when the entry is
  written: a ratchet entry. The other is the existing `tests/*` key, which
  MUST carry all four as a policy exemption. No glob key other than
  `tests/*` MAY carry a `D` code. Where a file already has an entry, its
  `D` codes join that entry. Every non-`D` code of every existing entry
  MUST be unchanged, so R-ZCG-1's two `T201` exemptions stand. No `D` code
  MAY appear in `[tool.ruff.lint.extend-per-file-ignores]`, and no comment
  token of a `.py` file under `openspec_graph/` or `tools/`, found with
  `tokenize`, MAY hold a `noqa` directive naming a `D` code. `make lint`
  MUST exit 0.
  - The guard reads `noqa` directives as ruff does (DEC-TDR-009). A line
    directive is `#`, optional whitespace and `noqa` in any case, then
    optional whitespace, a colon, optional whitespace and a list of codes,
    each upper-case letters followed by digits, separated by commas,
    whitespace or both. The list ends at the first token that is not a
    code, and the directive may follow other text in the same comment.
  - A file-level directive is a comment on its own line, anywhere in the
    file, reading `ruff: noqa` or `flake8: noqa`, matched in any case, with
    optional whitespace around each colon, then a colon and a code list.
    ruff treats the `flake8` form as blanket.
  - The guard names every directive whose code list holds a `D` code. A
    directive with no colon names no code, and is left to `--ignore-noqa`.
- R-TDR-9: `tests/test_static_ratchets.py` MUST hold a module-level
  `DOCSTRING_CEILINGS` that maps each ratchet entry's file to each of its
  `D` codes and that code's finding count in the file at the commit that
  lands the entries. It MUST sit under a comment stating R-TDR-4's rule,
  with a ruff release in place of a mypy release.
  - A guard test MUST assert that the ratchet entries' file-and-code pairs
    and the mapping's pairs are the same set, and that nothing breaks
    R-TDR-8's shape, whether a key, an `extend-per-file-ignores` entry or a
    `noqa` comment, naming each offender.
  - A guard test MUST run ruff over `openspec_graph` and `tools` with
    `--isolated`, so that no configuration file is read and no per-file
    table or configured exclusion can hide a finding; with
    `--no-respect-gitignore`, so that no `.gitignore`, `.ignore` or git
    exclude file can; with `--ignore-noqa`, so that no `noqa` comment can;
    and with `--select D100,D101,D102,D103`, JSON output and `--exit-zero`
    (DEC-TDR-009). It MUST fail unless ruff exits 0 with empty stderr, and
    it reads each finding's path relative to the repository root, in POSIX
    form.
  - It MUST fail whenever a pair's count differs from its ceiling, in
    either direction. A pair above its ceiling is named with both numbers.
    A pair below it is named in the form `lower <file> <code> from A to B`.
    A ratchet pair with no finding is named as stale, because its file no
    longer offends. A pair that offends but is not listed is named.
- R-TDR-10: No `pydocstyle` `convention` MAY be configured while no selected
  rule's verdict depends on it. The selected `D` rules' findings MUST be
  measured under no convention and under each of `google`, `numpy` and
  `pep257` and MUST be the identical set. That measurement MUST be recorded
  with its command in the `pyproject.toml` comment that explains the `D`
  selection. The same comment MUST record the convention that fits the
  existing docstrings best, meaning the one that leaves the fewest findings
  of the wider `D` family over the package and `tools/`, as a best fit and
  not as a convention the docstrings follow. The change that selects a
  convention-sensitive rule then sets the convention with it.
  - The comment that today declines `ANN/D` for tests MUST say instead that
    `D100`–`D103` are selected by per-file ratchet for the package and
    `tools/`, that `tests/` is exempt because a test's name is its
    documentation, and that `ANN` stays unselected because mypy's
    `no-untyped-def` is the annotation check.
  - The header comment above `select`, which says every family there was at
    or near zero violations when it was turned on, MUST be rewritten so that
    it stays true. It MUST name `D100`–`D103` as the one selection made with
    a backlog, held by per-file ratchet entries, as the "ratchet first" step
    of `select-zero-cost-guards`' DEC-ZCG-012.
- R-TDR-11: Every guard this spec adds MUST read the file it judges, and MUST
  be written and run red before the change it covers:
  - the recipe-and-files guard, red on the unchanged Makefile;
  - the override guard, red with the ceilings filled and no override, which
    it names as ceilings without a listed code. No override and no ceiling
    is R-TDR-2's clean end state, so the unchanged tree is green;
  - the mypy occurrence guard, red naming every occurring code as unlisted
    and the Windows-only `os.mkfifo` errors as platform-only;
  - the waiver guard, red naming every inline ignore of the unchanged tree as
    unrecorded;
  - the dev-extra guard, red on the unfloored `mypy` entry;
  - the docstring shape guard, red with `D` unselected, and its occurrence
    guard, red naming every offending pair as unlisted.

  The guard that names stubs, names and conditions covers no change of this
  package, so it has no red tree state and is shown red on planted inputs
  only. Each red run MUST be recorded in `tasks.md` and never committed as a
  tree state. Each guard MUST also be shown red on planted inputs:
  - a listed code with no occurrence; a code that occurs but is not listed;
    a listed code above its ceiling; and a listed code below its ceiling,
    named as one to lower;
  - a code listed without a ceiling, and a ceiling without a listed code;
  - a `typecheck` recipe without `--config-file pyproject.toml`, and one
    with a path argument; a `[tool.mypy]` table with an `exclude` key; and
    a `mypy_path` holding more than `tools`;
  - a second option on the tests entry, and a tests entry whose list is
    empty;
  - overrides that reach a test module spelled `tests/test_graph`,
    `openspec_graph.cli,tests.test_graph`, as a list, and as
    `tests.*.test_graph`; an override on a test module that sets only
    `follow_imports`; and one that sets `disallow_untyped_defs = false`;
  - a derived configuration that drops an option, keeps the tests entry, or
    keeps a second override that repeats a listed code for one test module;
  - an environment holding `MYPYPATH`, which the run's environment drops;
  - mypy JSON output with a `note` object, which MUST NOT be counted; an
    `error` object whose `file` has Windows separators, which MUST be; a
    stdout line that is not JSON; an error without a code; a nonempty
    stderr; and an exit code of 2;
  - two platforms' outputs that agree but for one error, named as
    platform-only;
  - a new `# type: ignore[no-untyped-def, unused-ignore]` absent from
    `MYPY_WAIVERS`; a recorded waiver the tree no longer holds; an ignore
    holding two codes besides `unused-ignore`; `unused-ignore` beside a code
    that is not listed; a listed code without `unused-ignore`; a bare
    `# type: ignore`; and a recorded waiver whose comment moves to another
    line;
  - a `# mypy: disable-error-code=…` comment, and a `# mypy: ` line inside a
    string literal;
  - a `.pyi` file under `openspec_graph/` and one under `tests/`; a
    `no_type_check` name; a `TYPE_CHECKING` name; a `MYPY` name; and, each
    outside the recorded site, `if sys.version_info >= (3, 11):`,
    `MYPY = False` followed by `if not MYPY:`, `if sys.platform ==
    "darwin":`, `if sys.version_info < (3, 10):`, a `match` case guard on
    `sys.platform`, and a module-level `assert` on it;
  - a dev extra whose `mypy` entry is bare, one pinned `mypy==1.11.0`, one
    floored lower at `mypy>=1.10`, and one `mypy~=1.11`;
  - a ratchet pair with no finding; a pair that offends but is not listed; a
    pair above its ceiling; a pair below its ceiling, named as one to lower;
    and a pair without a ceiling;
  - a `D` code under a glob key other than `tests/*`; a `D` code on a file
    under `tests/` by its own path; and a `D` code under
    `extend-per-file-ignores`;
  - the `noqa` spellings `#noqa:D103`, `# NOQA:D103`, `#  noqa  :  D103`,
    `# noqa: S607 D103` and `# see docs # noqa: D103`; a `# ruff: noqa:
    D103` in the middle of a file; and a `# flake8: noqa: D103`;
  - a planted tree under a temporary directory whose `.ignore` names its
    one module, which the docstring occurrence guard's command MUST still
    count.

  Each MUST be shown quiet on the matching well-formed input. Among those,
  these MUST be quiet:
  - a stdout that is one newline with an exit code of 0;
  - a recorded ignore of one enforced code without `unused-ignore`;
  - a bare `*` override, which mypy applies to no module;
  - a `follow_imports` override on the package;
  - R-TDR-6's version check in `read_pyproject`;
  - a `skipif(sys.platform == "win32", …)` argument, which is no test of a
    branch;
  - `# noqa: S607 -- D103 is documented elsewhere`;
  - a dev-extra marker `python_version == "3.10"`.
- R-TDR-12: Every new test MUST carry exactly one tier marker that agrees
  with `tests/shape_support.py`'s criterion (R-TSS-5, R-TSS-6). The guards
  that run mypy and ruff as processes are `e2e`. The guards that read
  `pyproject.toml`, the Makefile, or the modules under `tests/`,
  `openspec_graph/` or `tools/`, including through mypy's in-process
  `process_options`, are `integration`. The planted-input test, whose
  helpers take their input as arguments, is `unit`. The new module MUST
  mark per function, MUST stay within `MAX_TEST_MODULE_LINES`, and MUST
  contribute no occurrence of a listed code and no waiver.
- R-TDR-13: Every live document that describes the type-check's scope or the
  lint selection MUST describe the new state.
  - `docs/hooks.md`'s pre-commit list names `tests/` under `make typecheck`.
  - `tests/AGENTS.md` says in one sentence that `make typecheck` covers
    `tests/` and that a new occurrence of an exempted code, or a new inline
    ignore, fails `tests/test_static_ratchets.py`. It stays within
    `MAX_NESTED_LINES`, with its precedence clause and resolving links.
  - `.claude/agents/planlint-verifier.md`'s `ruff`/`mypy` bullet names the
    standing configuration: strict for the package and `tools/`, a per-code
    baseline for `tests/`, and per-file docstring exemptions. It also names
    the remediation norm: fix the code or lower a ceiling; never add a code,
    a file, a waiver, a `# mypy:` comment or a `noqa` for a `D` rule; and
    never raise a ceiling except to follow a tool release, as R-TDR-4 says.
  - Dated records MUST NOT be edited: `CHANGELOG.md`'s released sections,
    `docs/next-steps.md`, the peer reviews, the plan and
    `docs/distribution-plan.md`'s measured rows.
- R-TDR-14: This spec supersedes two passages of `select-zero-cost-guards`
  and MUST say so by name, here and in the CHANGELOG entry. The first is
  the clause of R-ZCG-3 that `[tool.mypy]` "MUST keep … `files =
  ["openspec_graph", "tools"]`". The second is the sentence of DEC-ZCG-004
  that lists what remains in `[tool.mypy]` ("The table that remains is
  `python_version`, `strict`, `warn_unreachable`, `files`").
  - The rest of R-ZCG-3 stands: strict, `warn_unreachable`, the 3.10
    floor, and the type gate exiting 0. So do R-ZCG-1, R-ZCG-2 and R-ZCG-4.
  - That package's C-ZCG-2 and DEC-ZCG-012, which name `D` as a backlog
    family to ratchet first and gate when the count is zero, are named
    here as followed, not reversed (DEC-TDR-008).
  - That package's files MUST NOT be edited.
  - `shape-the-test-suite`'s C-TSS-6, which forbids that package's own diff
    from widening the `tests/*` per-file-ignores, is named here as not
    reversed: R-TDR-8 adds to that key only rules that were never enforced
    in `tests/`.
- R-TDR-15: `CHANGELOG.md`'s `[Unreleased]` section MUST carry a `Changed`
  entry naming:
  - tests under mypy, with the override's codes and their ceilings;
  - the codes and the platform-only errors fixed instead of listed;
  - the waivers;
  - the mypy floor;
  - the `D100`–`D103` selection, with its per-file entries and the `tests/`
    policy exemption;
  - the guard module;
  - the two superseded passages of R-TDR-14.

  `tasks.md` MUST record each of the following, dated with the commit and
  naming the command:
  - the per-code counts under both platforms at Milestone 0 and at the
    commit that lands the override;
  - `MYPY_WAIVERS` at that commit;
  - the per-file docstring counts at the commit that lands the entries;
  - every red run;
  - the new guards' call durations;
  - the cold wall time of the type gate before and after;
  - the verdict on every leg of the CI run on the W6.5 commit and of the CI
    run on the W6.6 commit, each with its run id, the head SHA it ran for
    and the merge SHA it tested.
- R-TDR-16: The dev extra's `mypy` entry MUST carry a floor at the first
  mypy release that accepts `-O json`. A comment beside it MUST name that
  release and the guard that needs it. The floor MUST land in the commit
  that first runs mypy with `-O json`, as `migrate-license-metadata-pep639`'s
  R-LM-2 raised the setuptools floor in the commit that used the form that
  needed it. It MUST be a floor and not a pin: no dev-extra entry MAY carry
  `==` (DEC-TDR-014). A guard test MUST read the dev extra through
  `tests/support.py`'s `read_pyproject()`, and each entry with
  `packaging.requirements.Requirement`. It MUST assert that exactly one
  entry is named `mypy`, that its specifier is exactly that floor, and that
  no entry's specifier holds a clause whose operator is `==` or `===`. A
  marker is not a specifier, so `python_version == "3.10"` in a marker is
  no pin.
- C-TDR-1: No change under `openspec_graph/`, no rule, no golden hash, no
  runtime dependency and no new dev dependency. `pytest` and `hypothesis`
  ship their own types, so no stub package is added. `packaging`, which the
  dev-extra guard imports, is installed as pytest's own dependency and is
  not added to the extra (DEC-TDR-014). The one dev-extra edit is
  R-TDR-16's floor on the existing `mypy` entry. The `RULES` tuple,
  `README.md`'s rules table, `tests/baseline_rules.json`, the
  `validate`/`graph`/`rules` hashes and `[project] dependencies` are
  untouched.
- C-TDR-2: No workflow, composite-action or `.pre-commit-config.yaml` line MAY
  change. CI's `test` matrix, its Windows job and the pre-commit typecheck
  hook already run `make typecheck`, and the hook already fires on a staged
  test module. The only Makefile change is the `typecheck` target's help
  text and its recipe line, which becomes `python -m mypy --config-file
  pyproject.toml`. `make thresholds` MUST print PASS, and the four coverage
  floors MUST be unchanged in value and hold.
- C-TDR-3: No test function MAY be renamed or deleted, no assertion removed,
  and no `tests/<subdir>/` created; every test module stays within
  `MAX_TEST_MODULE_LINES`.
- C-TDR-4: This spec's requirements and criteria MUST NOT pin a count that
  another package changes: an error count, a finding count, a file count or
  a duration. Measurements belong in the proposal and in `tasks.md`, dated
  with their commit and naming their command. The ceilings and waivers live
  in the guard module, recorded there by the commit that lands each ratchet.
- C-TDR-5: The type gate and the mypy occurrence and waiver guards MUST give
  the same verdict on every CI leg, which is Linux on each supported
  interpreter, and Windows. So MUST the lint gate and the docstring guards.
  The CI run on the W6.5 commit MUST show the first, and the CI run on the
  W6.6 commit MUST show the second. Each is a pull-request run, which tests
  the merge of its commit into the base branch, so each is recorded with
  both SHAs.
- C-TDR-6: No `D` rule other than `D100`–`D103` MAY be selected, and this
  package MUST add no docstring under `openspec_graph/` or `tools/`. The
  ratchet entries shrink in the packages that already touch those files.

---

## Decisions

- **DEC-TDR-001:** `tests` joins `make typecheck` through `[tool.mypy]
  files`, and the recipe names its configuration file and no path.
  - Today the recipe is `python -m mypy openspec_graph tools`, and
    positional paths override `files`. So the plan's one-line change to
    `files` would have changed nothing the gate runs: the list would have
    lived in two places, and the one that mattered would have stayed short.
    A recipe with no path makes `files` the one list. That is the shape
    `coverage-run`'s bare `--cov` already gives the coverage sources
    (R-MCO-2: the trees are named in configuration, never in the recipe).
  - The recipe names `--config-file pyproject.toml`, because with no file
    named mypy searches for one, and in each directory it reads `mypy.ini`
    and `.mypy.ini` ahead of `pyproject.toml` (`mypy/defaults.py`,
    `CONFIG_NAMES`; `mypy/config_parser.py`, `_find_config_file`). A stray
    one would replace the whole configuration, `files` and `strict` with it,
    and the gate would pass on whatever it named. In a probe tree, a bare
    run checked only the tree that a planted `.mypy.ini` named, and a
    planted `mypy.ini` did the same, while `--config-file pyproject.toml`
    checked `pyproject.toml`'s tree under strict, on mypy 2.4.0 and 1.11.0
    (the proposal's evidence). A `setup.cfg` `[mypy]` section is read after
    `pyproject.toml`, and did not displace one that carries `[tool.mypy]`;
    the named file covers it anyway.
  - The gate keeps its name and its callers. CI's `test` matrix and its
    Windows job run `make typecheck` on every interpreter and on Windows.
    The pre-commit hook runs it with `types: [python]` and
    `pass_filenames: false`, so a staged test module already triggers it.
    Four other specs cite the stage on verification lines (`make
    stage-citations` at `e558eba`). Cold, the gate goes from 0.9 s to 3.7 s
    (the proposal's timing commands, at `e558eba`).

  Rejected: `python -m mypy openspec_graph tools tests` (a second list
  beside `files`); a recipe that names no configuration file (the round-1
  draft's, which a stray `mypy.ini` or `.mypy.ini` silently redirects); a
  `typecheck-tests` target (a second gate for one tool, which needs a
  workflow step and a hook entry this package otherwise does not touch); a
  mypy run inside pytest only (the type gate would then run under coverage,
  and only where the suite runs).
- **DEC-TDR-002:** `explicit_package_bases = true` with `mypy_path` holding
  `tools`. Explicit bases are needed because neither `tests/` nor `tools/`
  has an `__init__.py`. Without them, mypy names `tests/graft_support.py`
  both `graft_support` and `tests.graft_support`, and stops. With them
  alone, mypy roots every module at the repository and renames
  `tools/_common.py` to `tools._common`. Each gate script imports `_common`
  the way it runs: `python tools/<script>.py` puts the script's directory
  first on `sys.path`. So the scripts fail to resolve it (19 errors in 12
  files from `python -m mypy openspec_graph tools --explicit-package-bases`
  at `e558eba`). `mypy_path` holding `tools` makes that directory a base
  too. That is the static form of how the scripts run, and of
  `tests/test_wheel_metadata.py`'s own `sys.path` insert, so both resolve
  and `tools/` stays clean. Both options are global in mypy, which is why
  the measurement covers all three trees. `mypy_path` names `tools` and
  nothing else, because a second directory there is a second search root
  that the guards never measured. Rejected: a `tools/__init__.py` (mypy
  would then name the module `tools._common` with or without explicit
  bases, so the scripts' `from _common import` would still not resolve; and
  `INP001`'s exemption records that the scripts are not a package); a
  `tests/__init__.py` (it changes how pytest imports every test module,
  which is the suite's shape and not this package's business); a second
  mypy invocation with its own flags for `tests/` (two configurations for
  one checker).
- **DEC-TDR-003:** list seven codes, and fix the rest. Listing a code
  disables it across every test module, so a code with one or two
  occurrences buys one site's exemption at the price of the whole suite's
  protection: `unreachable` would go unchecked in all of `tests/` to excuse
  one assertion. The cut falls where the measured distribution says fixing
  is a few lines and listing is a standing exemption. The nine fixed codes
  hold fifteen occurrences on fourteen lines (the proposal's emulation, at
  `e558eba`). The seven listed codes hold the rest, and clearing them is
  the shrink's own work, commit by commit.

  An occurrence that depends on the configuration, the leg or the platform,
  rather than on the code, must be fixed whatever its count. A listed code
  whose count flips by leg would make R-TDR-5's comparison flip with it.
  - `import-not-found` on `tomllib` is produced by `python_version = "3.10"`
    on every leg.
  - The `unused-ignore` on the `tomli` import flips with whether the leg
    installed `tomli`.
  - The `attr-defined` on `os.mkfifo` occurs only in the Windows view. Its
    code is listed, but its occurrence is platform debt. Listing it would
    give `attr-defined` one count per platform and let the override hide,
    on the Windows leg, errors that the Linux leg never sees.

  The plan's five codes were a tally of a different tree, and they counted
  the `[str]` of note lines. `no-untyped-def`, `attr-defined` and
  `type-arg` join because this container now resolves `pytest` and
  `hypothesis`, which ship their own types. Rejected: listing all sixteen
  measured codes (green on day one, with nearly nothing enforced); fixing
  all occurrences at once (the plan's own alternative, at a size that is
  several packages' work, not one milestone's).
- **DEC-TDR-004:** each listed code is held to an exact count, its count at
  the landing commit, and not only to its presence in the list.
  - D1 configures a new limit "at today's maxima". For a disabled error
    code, the maximum is the count. A list of codes without counts would
    leave every listed code unenforced for every test written after it, so
    the debt could grow inside the list while the list shrank.
  - The guard fails in both directions. A count above its ceiling is new
    debt. A count below it is fixed debt the ceiling has not yet locked in:
    left alone, it is room for the next regression. So the guard says
    `lower <code> from A to B`, and the commit that fixed the occurrences
    lowers the ceiling.
  - The ceilings are a module-level constant beside the guard that reads
    them, in the form `MAX_TEST_MODULE_LINES` took (DEC-TSS-004): a number
    one test reads lives beside that test, not in `[tool.specgraph]`, whose
    keys gate a build.
  - The guard asserts that the override's list and the ceilings' keys are
    one set, so the two places cannot disagree silently. Growth is an edit
    to a constant whose comment forbids it: the visible diff a reviewer
    refuses, which is as far as a test that cannot read history can go.
  - The round-1 reviewer measured identical per-code counts on Python 3.11,
    3.12 and 3.13, and on mypy 2.1.0 and 2.4.0, by the guard-shaped run of
    the proposal's Evidence. The ceilings are therefore one number across
    the interpreters CI runs, at those releases.
  - The consequence, stated plainly: the dev extras are unpinned by
    decision, so a mypy release that changes a count makes the guard name
    it on the next run. The remedy is a ceiling edit in the pull request
    that meets it, to the count the release reports, with the release named
    beside the entry. It is never a widened list. A release that reports a
    new code is fixed under R-TDR-3, exactly as a release that finds a new
    error fails the type gate today.

  Rejected: codes without counts (above); a ceiling that only caps from
  above (it is never forced down); counts in a JSON baseline beside
  `tests/baseline_rules.json` (a file that invites regeneration, which is
  the one operation a ratchet must not have).
- **DEC-TDR-005:** the occurrence guard runs the gate's own mypy run, less
  the tests entry, twice: under `--platform linux` and `--platform win32`.
  It runs through a configuration it derives and re-checks, with `-O json`,
  each run with a cold cache under its own temporary directory, and it
  requires the two error sets to agree.
  - Derived, because a per-module `disable_error_code` beats a command-line
    `--enable-error-code` (measured), so the override cannot be lifted from
    the command line. It is written in mypy's INI form, which mypy reads
    with the same option names, because the standard library on the 3.10
    leg writes no TOML. It is named with `--config-file`, so, like the
    recipe, the guard reads no file that mypy would discover.
  - The gate's run, and not a run over `tests` alone. The round-2 draft
    dropped `files` and passed `tests` as a path. In that shape, a
    `follow_imports = "skip"` override on `openspec_graph.detect` and
    `openspec_graph.witness` took `attr-defined` from 19 to 7, and an
    ambient `MYPYPATH` naming a stub of `openspec_graph` took the tests'
    errors from 184 to 194 (the proposal's evidence, at `25c65de`). With
    `files` kept and no path, the same override leaves 19, as the gate
    sees it. So the derived configuration keeps every key, `files` among
    them, and every other override; the run passes no path; and the count
    is the tests' share of the gate's own errors, filtered by `file`.
  - `MYPYPATH` is removed from the run's environment, as
    `env_without_coverage()` removes the coverage variables. mypy puts it
    ahead of the configured `mypy_path` (`mypy/modulefinder.py`), and with
    `files` kept a `pytest` stub on it still took the tests' errors from 184
    to 928 (measured). `MYPY_CONFIG_FILE_DIR` is inert: mypy sets it itself
    from the configuration file's directory (`mypy/config_parser.py`), and a
    run with it set elsewhere counted the same 184.
  - Re-checked before it runs, by the same mypy loading as R-TDR-2. Its
    global options must equal `pyproject.toml`'s but for `config_file` and
    `per_module_options`; its per-module options must equal
    `pyproject.toml`'s less the tests entry; and no test module's options
    may differ from the global options in any field but `unused_configs`.
    A planned configuration and its derived INI met all three on 2.4.0 and
    1.11.0, and a slash-spelled override left in the derived
    configuration was named (the proposal's evidence). The check answers
    for the writer and for every override at once. So the run differs from
    the gate's by the one entry, the platform flag, the output format, the
    cache directory and an environment without `MYPYPATH` or the coverage
    variables, and by nothing else.
  - Both platforms, because CI runs a Windows leg. mypy's Windows view
    reported four errors the Linux view did not (`attr-defined` on
    `os.mkfifo`, by the proposal's two-platform command at `e558eba`, and
    the same four in the gate-shaped run at `25c65de`), and under the
    override the Windows leg's type gate would have hidden them. Requiring
    the two error sets to agree turns platform-only debt into a named error
    to fix, under DEC-TDR-003's own rule, and makes each ceiling one number
    on every leg. A mismatch is named as a platform-only error to fix. It
    is never listed and never given a ceiling per platform. No CI leg runs
    macOS, so these two platforms are every platform the gate runs on.
  - `-O json`, because a code read from a JSON field cannot be confused
    with the bracketed text of a note line. That confusion is where the
    plan's `str` came from. Only `severity == "error"` objects are counted.
  - Blank lines are skipped. A run with nothing to report prints one newline
    and exits 0, on mypy 2.4.0 and on 1.11.0 (the proposal's evidence).
    Without the skip, the clean tree that the ratchet ends at would be named
    as unreadable output.
  - Empty stderr and an exit code of 0 or 1, because mypy exits 2 on a
    usage error or a crash. A guard that counted the stdout of such a run
    would compare nothing and call it a match.
  - A cold cache under the test's temporary directory, so the test writes
    nothing into the tree and reads nothing stale. The two gate-shaped runs
    took 3.7 s and 3.9 s cold (the proposal's timing command, at
    `25c65de`).

  Rejected: reusing the repository's `.mypy_cache` (a test that writes into
  the tree, and a cache keyed on options the gate does not use); Linux only
  (the first draft's choice, which left Windows-only errors unmeasured and,
  under the override, unchecked on every leg); the leg's own platform
  (ceilings that differ by leg); per-platform ceilings (two numbers for one
  code, and the Windows-only debt kept rather than fixed); parsing the text
  output (a format for people, which the JSON output makes unnecessary); a
  run over `tests` with `files` dropped (the round-2 draft's, which a
  package override or an ambient `MYPYPATH` moves).
- **DEC-TDR-006:** every inline ignore under `tests/` is a recorded waiver,
  keyed by the line it waives, and every comment that configures mypy is
  refused.
  - The inline ignores that the override makes redundant (eight, by the
    proposal's emulation at `e558eba`) keep their codes and gain
    `unused-ignore`. Each was written by a package's author for a reason
    the line shows: `negation_matches(None, None)` passes `None` on
    purpose; the `**fields` splats build records that the dataclasses type
    more narrowly; the `witness.os` patches reach a module attribute mypy
    does not re-export. Each is needed again the day its code is
    re-enabled. Deleting them would erase those decisions from packages
    this one does not own, and add their sites to the ceilings.
  - `unused-ignore` in the brackets silences strict mode's report while the
    override makes the ignore redundant. But the same brackets beside any
    listed code, on any line, also silence that code there, so the round-1
    reviewer's `# type: ignore[no-untyped-def, unused-ignore]` lowered a
    count while the first draft's guard, which asked only that
    `unused-ignore` sit beside a listed code, passed it.
  - So every ignore is recorded in `MYPY_WAIVERS`, which only shrinks, and
    compared as a multiset, so a second ignore of the same code on a line
    of the same text in the same file is named.
  - It is keyed by path, code and the waived line's own text, comment
    removed and whitespace collapsed, and not by line number or enclosing
    function. A line number moves with every edit above it. A function key,
    the round-2 draft's, let a re-key re-point a waiver: the rule that
    allowed renames could not tell a rename from a move of the comment onto
    other code. A text key needs no re-key. A rename or a move within the
    file leaves it alone; a move to another file changes only the path; a
    comment moved onto other code changes the text, and the guard names it.
    An edit to the waived line itself changes the key too, so the commit
    that makes it updates the entry, and its diff shows the old and the new
    text side by side. At `25c65de`, the ten ignores under `tests/` have ten
    distinct keys, and no waived line's text recurs in its file (the
    proposal's evidence).
  - Each waiver holds exactly one code, so one comment cannot waive two.
    `unused-ignore` sits beside that code while it is listed, and not once
    it is enforced. The round-1 draft also named "an ignore holding no
    listed code", which would have named every waiver of a code in the
    commit that re-enables it: the very state its own next rule required.
    The two rules that replace it, `unused-ignore` without a listed code
    and a listed code without `unused-ignore`, name only the two ways to get
    the pairing wrong. When a code is re-enabled, its waivers keep their
    entries and lose `unused-ignore`, so strict mode polices them as
    ordinary ignores of an enforced code.
  - Two more forms lower a count with no override. A bare `# type: ignore`
    before a module's first statement silences the whole module: it passes
    clean an inline program whose body holds an untyped `def` and a
    mistyped assignment (`python -m mypy -O json --strict -c …`, run outside
    the worktree). It is named because it holds no code. A file-level
    `# mypy: disable-error-code=…` comment is an override in disguise: one
    at the head of `tests/test_graph.py` lowers `no-untyped-def` from 96 to
    72 (the round-1 reviewer's figure, reproduced by the proposal's
    `--shadow-file` command at `e558eba`). So every `# mypy:` comment is
    named.
  - The comment check reads tokens with `tokenize`, so a string that looks
    like a comment is not one. mypy, however, can read its inline
    configuration by physical line (`mypy/util.py`, `get_mypy_comments`: a
    line that starts with `# mypy: `), and then a line inside a docstring
    counts, though no comment token reveals it. Whether it counts depends on
    the release and the parser. With the line on a docstring's second line
    of a file read from disk, mypy 2.4.0's default parser does not honour
    it, while mypy 1.11.0 does, and so does 2.4.0 under
    `--no-native-parser`, under `-c` and under `--shadow-file` (the
    proposal's evidence). R-TDR-16's `>=1.11` floor admits 1.11.0, so a leg
    or a contributor may run a release that honours it. The guard therefore
    also names every physical line with that prefix, which is mypy's own
    rule and not a substring search. As a result, the guard module writes
    its planted inputs so that no line of its own begins with it.

  Rejected: deleting the ignores (above); disabling `unused-ignore` for
  `tests.*` (it would never be re-enabled, because no stale ignore would
  ever be reported to fix); a per-module `warn_unused_ignores = false` (the
  same, spelled as an option R-TDR-2 forbids); keying waivers by line (they
  would churn on every unrelated edit); keying them by enclosing function
  with a re-key rule (the round-2 draft's, which a re-key could use to
  re-point a waiver); naming every ignore that holds no listed code (the
  round-1 rule, which contradicts the re-enable step); a recorded list of
  permitted `# mypy:` comments (a second override list that R-TDR-2's one
  entry exists to prevent); a substring search over the source (it would
  name the guard's own planted strings); dropping the physical-line check
  because the current release ignores such a line in a file (the floor
  admits a release that honours it).
- **DEC-TDR-007:** the TOML reader picks its module by `sys.version_info`,
  and `tomli` is a `module = "tomli"` override with
  `ignore_missing_imports`. mypy understands version checks, and at
  `python_version = "3.10"` it analyses the `tomli` branch on every leg.
  `tomli` is installed only on the 3.10 leg, so the import resolves there
  and is missing elsewhere. The override makes both cases silent without an
  inline ignore whose use flips by leg. The annotated local makes the
  return typed in both, so `no-any-return` does not flip either. Measured:
  the version-check form with an annotated local is clean under the 3.10
  and the 3.11 view with `tomli` absent, while the current `try`/`except`
  form reports an unused ignore and a `no-any-return`. This check is the
  one version condition R-TDR-7's sibling guard allows, by path and
  function (DEC-TDR-016). Rejected: `# type: ignore[import-not-found,
  unused-ignore]` on the import (a waiver of a code the override does not
  list, which R-TDR-7 forbids); adding `tomli` to the dev extra for every
  interpreter (a dependency change for a type checker's benefit).
- **DEC-TDR-008:** docstrings are ratcheted for `openspec_graph/` and
  `tools/`, and `tests/` is exempt by policy.
  - `select-zero-cost-guards` already decided how `D` arrives. Its C-ZCG-2
    kept `D` out of that change as "a ratchet with a backlog". Its
    DEC-ZCG-012 set the sequence: "ratchet first — count, reduce, re-count
    — and gate when the count is zero". This package's per-file ratchet is
    that "ratchet first" step. The count is the ceilings, recorded per file
    and code. The reduction is each entry's removal in the W2 or W3 pull
    request that documents its file. The re-count is the guard of R-TDR-9,
    which fails until a fixed count is lowered. Selecting the four rules
    under per-file entries is not DEC-ZCG-012's gate, which "would turn a
    measurable debt into a red build". The build stays green, and only an
    unlisted file or a count above its ceiling turns it red. The gate in
    that decision's sense, `D100`–`D103` with no ratchet entry, is the end
    of those removals.
  - The plan counted the package only. `tools/` joins because its own
    floors comment in `pyproject.toml` says that holding the gate machinery
    to a lower bar than the code it guards is the argument this project
    exists to refuse.
  - `tests/` is exempt because 575 of its 584 findings (`python -m ruff
    check --isolated --select D100,D101,D102,D103 tests --statistics`, at
    `e558eba`) are test functions whose names are sentences, and whose
    docstrings would repeat them. That is what the existing comment means
    by "large, low-yield". Its support modules follow the key that covers
    them. The exemption is the existing `tests/*` key and not a ratchet,
    because nothing is meant to shrink it.
  - That key gains four codes, and `shape-the-test-suite`'s C-TSS-6 forbids
    widening it. But C-TSS-6 constrains that package's own diff, and the
    property it protects still holds: no rule once enforced in `tests/` is
    silenced, because `D` was never enforced there.

  Rejected: selecting `D` only through a second `ruff` invocation in the
  `lint` recipe (configuration on the command line, which editors and a
  bare `ruff check` would not see); exempting `tools/*` by glob (a lower
  bar for the gate scripts than for the package); waiting for a zero count
  before selecting anything (DEC-ZCG-012's gate with no ratchet before it,
  so nothing would stop the count growing in the meantime).
- **DEC-TDR-009:** one ratchet entry per offending file, with exactly its
  codes; an exact count per file and code, taken with no configuration, no
  ignore file and no `noqa`; and no docstring written here.
  - A glob would exempt files that do not offend, and every future file
    beside them. A per-file entry exempts what offends today and nothing
    else.
  - The count stops a listed file from gaining an undocumented function,
    which ruff's all-or-nothing exemption cannot. Its below-ceiling message
    forces the count down when one is documented, as DEC-TDR-004 does for
    mypy.
  - ruff reports nothing when an entry exempts nothing (measured), so
    R-TDR-9's stale check is what forces an entry out once its file is
    documented.
  - The guard counts with `--isolated` and `--ignore-noqa`, because three
    things lower ruff's count while the ratchet entries stay as they are: a
    file-level `# ruff: noqa: D103`, a line-level `# noqa: D103`, and an
    `extend-per-file-ignores` entry. Planted over `openspec_graph/cli.py`
    under the repository's configuration with `per-file-ignores` cleared,
    each lowered the file's count; under `--isolated --ignore-noqa`, none
    did (the proposal's evidence, at `e558eba`). Clearing the extend table
    inline does not work: ruff adds a command-line layer's extend entries to
    the configuration file's rather than replacing them, and a probe
    `pyproject.toml` whose extend table exempted the file kept it exempt
    with both tables cleared by `--config` (measured). `--isolated` reads no
    configuration file, so no per-file table and no configured exclusion
    reaches the count, and `--ignore-noqa` makes every `noqa` comment inert.
  - It also passes `--no-respect-gitignore`, because ignore files are not
    configuration: `--isolated` still honours them. In a probe tree, an
    `.ignore` naming a module hid all of its findings under `--isolated
    --ignore-noqa`, and `--no-respect-gitignore` restored them; the
    round-3 reviewer measured an `openspec_graph/.ignore` naming `cli.py`
    taking the tree from 77 findings to 69. Today's tree gives the same 77
    findings in 30 files with the flag as without it (the proposal's
    evidence, at `25c65de`). A `.gitignore` had no effect in a probe outside
    a git repository; inside one, the same flag covers it, so it was not
    planted into the worktree.
  - The count is then the four rules' findings as ruff reports them with
    defaults, and the shape guard ties the configuration to that count.
    ruff's built-in exclusion list still applies (DEC-TDR-017).
  - The shape guard also names a `D` code under `extend-per-file-ignores`
    and a `noqa` comment naming a `D` code, so that `make lint`'s view
    agrees with the guard's, and an offender is named where it is written
    rather than only as a count. Its reader follows ruff's own grammar, as
    measured against ruff over `openspec_graph/cli.py`:
    - `#noqa:D103`, `# NOQA:D103`, `# NoQa: D103`, `#  noqa  :  D103`,
      `# noqa: S607 D103`, `# noqa: S607, D103`, `# see docs # noqa: D103`
      and `# noqa: D103 # because` each exempted the line;
    - `# noqa: S607 -- D103 is documented elsewhere` did not, because the
      code list ends at `--`, and neither did a lower-case `d103` nor an
      empty `# noqa:`, which ruff warns about;
    - `# ruff: noqa: D103`, `#ruff:noqa:D103` and `# flake8: noqa: D103` on
      their own line in the middle of the file exempted the whole file, the
      last as a blanket;
    - `# RUFF: NOQA: D103` did not. The reader matches the file-level
      prefixes in any case, so it also names that spelling: naming a
      comment written to exempt a `D` rule costs nothing even where ruff
      ignores it.

    None names a `D` code at `25c65de`. `openspec_graph/report.py:59`'s
    `# ruff: noqa: S105 -- …` carries a reason after `--`, as the quiet
    case does. A bare `noqa` directive is left to `--ignore-noqa`: it
    cannot lower the guard's count, and forbidding it would reach past the
    `D` rules into a choice this package does not own.
  - The plan routes the shrinking to the W2 and W3 pull requests that
    already touch those files. Writing docstrings here would edit
    `openspec_graph/`, which C-TDR-1 keeps out of this package. A function
    that W2 moves into a new file is documented in that move, or is a new
    entry the guard names.
  - The ruff run asserts exit 0 and empty stderr for the reason DEC-TDR-005
    gives for mypy. A ruff release that changes a count is met as
    DEC-TDR-004 meets a mypy one.

  Rejected: one entry per directory (the glob above); fixing the files
  with a single finding first (an edit under `openspec_graph/` for a list
  that W2 rewrites anyway); the repository's configuration with
  `per-file-ignores` cleared (the round-1 command, under which an extend
  entry and every `noqa` still lower the count); clearing
  `extend-per-file-ignores` with `--config` as well (measured not to clear
  a configuration file's table); `--isolated` alone (an ignore file still
  hides a module).
- **DEC-TDR-010:** the convention is measured and recorded, not configured.
  - Under no `pydocstyle` convention and under each of `google`, `numpy`
    and `pep257`, ruff reports the identical `D100`–`D103` finding set. The
    sorted concise output of `python -m ruff check --isolated --select
    D100,D101,D102,D103 --config 'lint.pydocstyle.convention = "<c>"'
    openspec_graph tools tests` has one digest under all four, with 661
    findings each, at `e558eba`. So a `convention` key would change no
    selected rule's verdict while reading as a gate. That is the class of
    configuration this repository's own `pyproject.toml` comment refuses:
    "an ignore list for rules that were never on is config that looks like
    a gate and is not".
  - The measurement belongs in the comment. Over the package and `tools/`,
    with the presence rules set aside, Google is the best fit: it leaves
    the fewest findings of the wider family, 37 against 67 under `numpy`
    and under `pep257` (`python -m ruff check --isolated --select D
    --ignore D100,…,D107 --config 'lint.pydocstyle.convention = "<c>"'
    openspec_graph tools --statistics`, at `e558eba`). The difference is
    `D401`'s 29 non-imperative summaries and one `D400`, which Google does
    not require.
  - It is a fit, not a convention the docstrings follow. Under it, 37
    findings remain: a summary line not followed by a blank line, a closing
    quote on the last paragraph's line, and a backslash in a non-raw
    docstring. Those are formatting debt that every convention keeps.

  Rejected: `convention = "google"` now (it changes no selected rule's
  verdict, so it is inert configuration); claiming that the docstrings
  follow one convention, as the plan does (they fit Google better than the
  others on the rules that tell the conventions apart, and they still break
  three rules every convention keeps).
- **DEC-TDR-011:** two superseded passages, named, and three sibling
  decisions named and not reversed. `select-zero-cost-guards` shipped in
  0.3.0. So, in DEC-MCO-006's form, its R-ZCG-3 clause on `files` and the
  sentence of DEC-ZCG-004 that lists "the table that remains" are
  superseded by name here and in the CHANGELOG, and the package is not
  edited.
  - Its AC-ZCG-3 does not mention `files`, and stays true.
  - R-ZCG-4 holds unchanged: a bare generic in the package or `tools/`
    fails the gate. That is still shown by
    `test_a_bare_generic_in_tools_fails_typecheck`, under the new
    configuration.
  - Its C-ZCG-2 and DEC-ZCG-012 are followed, for the reason in
    DEC-TDR-008: this package is the ratchet those decisions put before a
    `D` gate.
  - `shape-the-test-suite` merged to `main` as `46ae1b3` (#42), and this
    branch is based on that commit. C-TSS-6 is named for the reason in
    DEC-TDR-008, and that package's files are not edited from here.

  Rejected: amending R-ZCG-3 or DEC-ZCG-004 in place (both are shipped);
  leaving them unnamed (a reader of either would find `[tool.mypy]`
  changed, and take it for a requirement this package broke); reading
  C-ZCG-2 as a ban on `D` (it constrains that change's own diff, and
  DEC-ZCG-012 says what comes next).
- **DEC-TDR-012:** the guards live in a new module,
  `tests/test_static_ratchets.py`.
  - `tests/test_ci_workflow.py` holds the mypy and ruff configuration
    claims of `select-zero-cost-guards`. But its subject is the CI
    configuration as the workflows state it. A module named for the
    ratchets is a subject that the W3 and W4 limits configured "at today's
    maxima" can join, and a module named for a subject refuses what does
    not belong (DEC-TSS-001).
  - `tests/test_suite_shape.py`, the other candidate, is the suite's shape,
    which the ratchets are not. It now has room under the bound (555 lines
    by `wc -l` at `e558eba`), so its size is no longer the reason.
  - The new module's budget is 600 lines by `wc -l
    tests/test_static_ratchets.py` at the W6.6 commit. That leaves a
    hundred lines under `MAX_TEST_MODULE_LINES` for the first limit that
    joins it. A draft over budget does not raise the budget. Instead, the
    planted-input test moves to a module of its own, and the helpers its
    two users then share move to an uncollected support module, as
    R-TSS-2 permits for a helper two collected modules need.

  Rejected: either existing module (above); an uncollected
  `ratchet_support.py` while the module is within budget (the helpers have
  one collected user, and R-TSS-2's rule moves a helper with its only
  user).
- **DEC-TDR-013:** one pull request, three commits, each `make pre-pr`
  green.
  - The W6.5 commit carries the mypy guards, the fixed codes and
    platform-only errors, the override, the ceilings, the waivers and the
    mypy floor.
  - The W6.6 commit carries the docstring guards, the selection, the
    entries and their ceilings.
  - The documents commit carries the live documents, the re-pointed
    verification lines and the records.

  Each guard lands in the commit whose change it covers. Its red run
  happens in the working tree before that commit, and is recorded, never
  committed. Each commit is pushed and its CI run recorded before the next
  is pushed, so AC-TDR-20 and AC-TDR-21 each have a run of their own. Each
  is a pull-request run, which tests the merge of the pushed commit into
  `main` (`ci.yml` runs on `pull_request`, and on `push` only to `main` and
  `master`), so each record names the head SHA and the merge SHA. Each
  ratchet's ceilings are recorded at the commit that lands it. The two
  ratchets touch different tables of one file, so a reviewer reads one kind
  of change per commit, and the per-code record and the per-file record
  each have a commit to be dated with. Rejected: a commit of red guards (a
  tree state that fails its own gate, which the plan's loop forbids); two
  pull requests (the plan's loop is one package, one pull request); one
  commit (the two records would share a date and a diff, and a red CI leg
  could not be attributed to one ratchet).
- **DEC-TDR-014:** the dev extra floors `mypy` at 1.11, the first release
  with `-O json`.
  - mypy's changelog lists "Add error format support and JSON output
    option via `--output json`" (PR 11396) under Mypy 1.11. Its
    `mypy/main.py` defines `-O`/`--output` at tag `v1.11.0` and not at
    `v1.10.0`. mypy 1.10.1 rejects `-O` as an unrecognized argument, and
    1.11.0 accepts it (measured). Each JSON object carries `file`, `line`,
    `column`, `message`, `hint`, `code` and `severity` from that release
    on.
  - No dev-extra entry is floored at `e558eba` (`pyproject.toml`'s `dev`
    list). The precedent followed is R-LM-2's setuptools floor: a floor at
    the release that understands the feature used, raised in the commit
    that uses it, under a comment naming why.
  - A floor is not a pin. `tools/check_no_hardcoded_thresholds.py` names
    `mypy==` in a workflow, and `test_dependabot_does_not_add_a_pip_ecosystem`
    names a pip ecosystem; neither is touched by a `>=` bound, and the
    decision that the extras float is kept.
  - The floor and the no-pin rule are held by a guard that reads the dev
    extra itself (R-TDR-16). `test_threshold_guard_fails_on_a_pinned_tool_version`
    plants `ruff==` in a workflow, and says nothing about the extras.
  - The guard reads each entry with `packaging.requirements.Requirement`,
    so a specifier and a marker are told apart: `tomli; python_version <
    "3.11"` has no specifier, and a marker `python_version == "3.10"` holds
    no `==` clause, while `mypy~=1.11`, `mypy>=1.10` and `mypy==1.11.0` each
    parse to the operator they spell (measured). `packaging` 26.3 is
    importable from the dev install because pytest requires `packaging>=22`
    (measured here and in the 1.11.0 environment). It is imported, not
    declared: if pytest ever dropped it, the guard would fail at import,
    by name.
  - Without the floor, nothing states that the guard needs the flag. A
    resolver free to choose an older mypy would make the guard's run a
    usage error, which DEC-TDR-005's exit-code check would name as a broken
    run, not as a requirement.

  Rejected: no floor (the requirement unstated); a pin (the extras float by
  decision); parsing text output to avoid the floor (DEC-TDR-005); a
  substring test for `==` (it would flag a marker); adding `packaging` to
  the extra (a dependency edit C-TDR-1 rules out, for a module the extra
  already installs).
- **DEC-TDR-015:** R-TDR-2 asks mypy what every override does to every test
  module.
  - The first draft allowed exactly one other override, the `tomli` one.
    That would have failed the first package to need an override for an
    untyped import in `openspec_graph/` or `tools/`, on a matter this
    package has no stake in. So only overrides that change a test module
    are judged.
  - The round-2 draft decided "applies" with `compile_glob`, mypy's pattern
    compiler. That is not mypy's whole resolution: `mypy/config_parser.py`
    splits a `module` value on commas and maps `os.sep` and `os.altsep` to
    dots before it compiles anything. `module = "tests/test_graph"` and
    `module = "openspec_graph.cli,tests.test_graph"` each lowered
    `no-untyped-def` from 96 to 72, as a list spelling and
    `tests.*.test_graph` did, and `compile_glob` says the first two do not
    apply; it also says a bare `*` applies, which mypy files as a concrete
    key (the proposal's evidence, at `25c65de`). A matcher short of mypy's
    resolution chases spellings one at a time.
  - So the guard asks mypy. It loads `pyproject.toml` through
    `mypy.main.process_options(["--config-file", "pyproject.toml"],
    require_targets=False)` and compares `Options.snapshot()` of the global
    options with that of `clone_for_module(<module>)` for each test module.
    It uses `process_options` and not a bare `parse_config_file`, because
    `parse_config_file` applies `strict` only through the callback it is
    given. With a no-op callback, the global `disallow_untyped_defs` stays
    false, and an override that sets it false for a test module compares
    equal; through `process_options` it is named, on 2.4.0 and 1.11.0
    alike (measured). The round-3 review's probe used the no-op callback;
    this draft does not.
  - The comparison ignores one field, `unused_configs`: mypy 1.11.0
    exposes it in `snapshot()` and fills it as `clone_for_module` runs,
    while 2.4.0 keeps it private. On a configuration whose only override is
    `tomli`, it was the only field that differed for any test module, and
    only on 1.11.0. On the planned configuration, all 61 test modules
    differed in `disable_error_code` and `disabled_error_codes` and nothing
    else, on both releases (the proposal's evidence). The raw
    `disable_error_code` list is not compared to the listed codes, because
    a concrete override inheriting from `tests.*` can show the effect in
    `disabled_error_codes` alone (measured); the effective set is what
    mypy reports against.
  - An override that repeats a listed code for one test module leaves the
    effective set unchanged, so R-TDR-2's comparison alone passes it.
    R-TDR-5's derived configuration drops only the exact `tests.*` entry
    and is re-checked, so any other override that changes a test module is
    named there. That closes the class rather than one spelling.
  - These are mypy internals. Their signatures, read from each release's
    shipped source, match: `parse_config_file(options, set_strict_flags,
    filename, stdout=None, stderr=None)`; `Options.clone_for_module(self,
    module)`; `Options.snapshot(self)`; and `process_options(args,
    stdout=None, stderr=None, require_targets=True, server_options=False,
    fscache=None, program="mypy", header=HEADER)`, to which 2.4.0 adds
    `mypyc=False`. A release that removes or renames one fails the guard
    with an import or attribute error, which is red. A release that keeps
    the names but stops reporting an override's effect fails the
    requirement that the listed codes appear as the difference, which is
    also red. The guard asserts what it expects to see, so it fails closed.
    `process_options` also sets `MYPY_CONFIG_FILE_DIR` in `os.environ`
    (`mypy/config_parser.py`), so the guard restores the environment after
    the call.
  - A bare `*` follows mypy's truth. mypy 2.4.0 and 1.11.0 file it as a
    concrete key, it changes no test module's options, and it is not named.
    A release that starts applying it would change them, and the
    comparison would name it.

  Rejected: the first draft's closed list of overrides (above); matching the
  literal `tests.*` only (it misses the per-module bypass); `compile_glob`
  (the round-2 draft's, which misses the comma and slash spellings); a
  matcher of the guard's own (the same risk); `parse_config_file` with a
  no-op callback (it hides a relaxed strict flag); comparing
  `per_module_options` keys as text (the spellings again).
- **DEC-TDR-016:** what hides code from mypy with no comment and no override
  is named, and a future legitimate use is a reviewed change to the guard.
  - A `.pyi` beside a module is what mypy reads for that module, in place
    of its source. That holds in all three trees `files` names: the round-3
    reviewer measured an `openspec_graph/graph.pyi` taking the tests'
    `attr-defined` from 19 to 17. None exists in any of them at `25c65de`
    (`find openspec_graph tools tests -name '*.pyi'`).
  - `@typing.no_type_check` stops mypy checking a function, and mypy skips
    a branch it judges unreachable. Its rules (`mypy/reachability.py`) are
    `not`, `and` and `or` over: the names `MYPY` and `TYPE_CHECKING`, which
    it takes as true; `PY2` and `PY3`; the configured `always_true` and
    `always_false`; and comparisons on `sys.version_info` and
    `sys.platform`, including an index, a slice and `.startswith`, where
    `sys` is the literal name. It applies them to `if` and `elif`, to
    `match` case guards and to a module-level `assert`. An untyped `def`
    passed `--strict --warn-unreachable` under each of `if
    sys.version_info >= (3, 11):`, `MYPY = False` then `if not MYPY:`, `if
    sys.platform == "darwin":`, `if sys.version_info < (3, 10):`,
    `.startswith("darwin")`, `sys.version_info[0] < 3`, `if PY2:`, `if not
    PY3:`, a `match` guard and a module-level `assert` on `sys.platform`, on
    2.4.0 and 1.11.0, and under `x and sys.version_info < (3, 10)` on 2.4.0
    only. A `while`, a conditional expression, an `assert` inside a
    function, `from sys import platform` and `if False:` hid nothing
    (the proposal's evidence).
  - The sibling guard names all of those forms, and `while` tests and
    conditional expressions too: they hide nothing on either release, cost
    nothing to name, and close the form if a release starts reading them.
    It reads tests with `ast` and names with `tokenize`, so text inside the
    guard's own planted strings is not one. None occurs at `25c65de`: the
    one `sys.platform` under `tests/` is a `skipif` argument in
    `tests/test_claude_hooks.py`, which is no branch test.
  - The one allowed site is R-TDR-6's version check in `tests/support.py`'s
    `read_pyproject`. It is recorded by path and function and allowed once,
    so a second version check in that function is named.
  - A global `exclude` drops a module from the run: one naming
    `tests/test_graph.py` lowered `no-untyped-def` from 96 to 72 (the
    proposal's in-memory configuration, at `e558eba`). R-TDR-1's exact key
    set closes it, with every other global option, which a key-by-key ban
    would chase one release at a time. Per-module `always_true` and
    `always_false` are closed by R-TDR-2's comparison.
  - All of this is deliberately broad. `if TYPE_CHECKING:` around an import
    used only in annotations hides nothing, and a stub can be legitimate. A
    future use of either, or a new global option, is a change to the guard
    in the pull request that needs it, with its reason beside it and read
    by a reviewer. It is never an addition the guard does not see.

  Rejected: naming only `if not TYPE_CHECKING:` (the `else:` of
  `if TYPE_CHECKING:` is the same branch, and an alias spells it again);
  naming only comparisons (`.startswith` is a call); stubs in `tests/` only
  (a package stub moved the tests' count); an allow-list of permitted names,
  stubs or conditions beyond R-TDR-6's one (a second waiver list beside
  `MYPY_WAIVERS`); a substring search (it would name the guard's own planted
  text).
- **DEC-TDR-017:** the threat model. The guards defend against accidental
  and casual loosening, and leave deliberate loosening to review.
  - Every configuration-level and code-level suppression this package knows
    of is made visible and named:
    - the configuration file mypy reads, and the global key set;
    - any override that changes a test module, however spelled;
    - inline ignores and `# mypy:` comments and lines;
    - stubs, unchecked names and unreachable branches;
    - per-file tables, `noqa` directives and ignore files on the ruff side;
    - an ambient `MYPYPATH`;
    - a count that moves in either direction.
  - A guard that reads one tree cannot stop a change that edits both the
    code and the guard's own constants, or the guard itself, in one commit.
    Such a change is visible in review: the constants sit under comments
    that state their rules, and every ratchet edit is a diff to them.
    Review is the control for it.
  - Known residual gaps, accepted rather than missed:
    - a coordinated edit of a waived line and its `MYPY_WAIVERS` entry, whose
      diff shows both texts;
    - a waiver moved between two lines of identical text in one file, which
      keeps its key (no waived line has a twin at `25c65de`);
    - a mypy or ruff suppression mechanism released after this package;
    - ruff's built-in exclusion list (`dist`, `venv`, `_build`,
      `node_modules` and the rest), which `--isolated` and
      `--no-respect-gitignore` leave in force, so a package subdirectory of
      that name would go unread;
    - mypy internals that keep their names but change their meaning in a
      way that still shows the listed codes, which the guard cannot tell
      from today's behaviour.
  - This bounds further review. A new finding that falls inside these gaps
    is accepted risk, recorded beside them, and not a defect of this
    package. A finding that names a suppression mechanism that exists today
    and is not named above is in scope.

  Rejected: reading git history in the guard to catch a coordinated edit
  (CI's checkout depth, and a test that judges commits rather than the
  tree); a second copy of the constants elsewhere (it moves the problem,
  since both copies sit in one commit's reach).

---

## Acceptance Criteria

- [ ] **AC-TDR-1:** `[tool.mypy]` keeps `strict = true`,
  `warn_unreachable = true` and `python_version = "3.10"`, and the type gate
  exits 0 on the finished tree with `openspec_graph/`, `tools/` and `tests/`
  checked from `files`, read from the configuration file the recipe names.
  (R-TDR-1, C-TDR-5, DEC-TDR-001, DEC-TDR-002)
  _Verified by:_ `pytest -k "test_typecheck_passes_on_clean_repo or test_mypy_is_strict_and_warns_on_unreachable_code"` · stage: `make typecheck`

- [ ] **AC-TDR-2 (non-success):** under a copy of the new configuration, a
  bare generic in a `tools/` module is still a `type-arg` error, and a type
  error in a module outside every package base still fails mypy and names its
  file. Neither explicit bases nor the new search path silences either.
  (R-TDR-1, R-TDR-14, DEC-TDR-002, DEC-TDR-011)
  _Verified by:_ `pytest -k "test_a_bare_generic_in_tools_fails_typecheck or test_mypy_fails_on_a_type_error"` · stage: `make typecheck`

- [ ] **AC-TDR-3:** read structurally from the Makefile and `pyproject.toml`:
  the `typecheck` recipe is `python -m mypy --config-file pyproject.toml`
  with no path argument; `[tool.mypy]`'s keys are exactly R-TDR-1's six and
  `overrides`; `files` holds the three trees, `explicit_package_bases` is
  true and `mypy_path` names `tools` and nothing else. The guard ran red on
  the unchanged Makefile, as `tasks.md` records. (R-TDR-1, R-TDR-11,
  DEC-TDR-001, DEC-TDR-002, DEC-TDR-016)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-4:** loaded through mypy's own `process_options`, every
  module under `tests/` has options that differ from the global options
  only in its disabled codes, and the codes it adds are exactly the listed
  codes. Those sit in at most one entry, spelled exactly `tests.*`, whose
  only option is a non-empty `disable_error_code`. They are a subset of
  R-TDR-2's seven and exactly the keys of `MYPY_TESTS_CEILINGS`; with no
  entry, the mapping is empty. An override that changes no test module is
  not judged. (R-TDR-2, R-TDR-4, DEC-TDR-003, DEC-TDR-004, DEC-TDR-015)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-5:** the derived configuration, loaded through mypy, matches
  `pyproject.toml` but for the tests entry, and leaves every test module's
  options equal to the global options. Run with `files` kept, no path and
  no `MYPYPATH`, mypy's JSON output gives the same errors under `--platform
  linux` and `--platform win32`, and each run exits 0 or 1 with empty
  stderr, its blank stdout lines skipped. Every listed code's count equals
  its ceiling, with none above, none below and none stale, and every code
  that occurs is listed. The guard's call duration is in `tasks.md`.
  (R-TDR-2, R-TDR-4, R-TDR-5, DEC-TDR-004, DEC-TDR-005, DEC-TDR-014,
  DEC-TDR-015)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-6:** none of the codes R-TDR-3 fixes occurs in `tests/` with
  the override lifted, no error occurs under one platform only, and the
  type gate passes with those codes unlisted. Read at review, the diff of
  every fixed site adds no ignore, no `# mypy:` comment, no stub, no
  `no_type_check`, no branch mypy treats as unreachable, no cast to `Any`
  and no `noqa`, and removes no assertion. (R-TDR-3, C-TDR-3, DEC-TDR-003)
  _Verified by:_ `pytest -k test_typecheck_passes_on_clean_repo` · stage: `make typecheck`

- [ ] **AC-TDR-7:** `tests/support.py`'s reader selects its TOML module by
  version and returns an annotated local, and the `tomli` override sets
  only `ignore_missing_imports`. The pyproject guards that read through the
  reader pass on the leg that installs `tomli` and on those that do not.
  (R-TDR-6, C-TDR-5, DEC-TDR-007)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_mypy_is_strict_and_warns_on_unreachable_code"` · stage: `make typecheck`

- [ ] **AC-TDR-8:** every inline ignore under `tests/` is a recorded
  `MYPY_WAIVERS` entry keyed by path, code and waived line, and every entry
  is in the tree, compared as multisets. Each waiver holds exactly one code,
  with `unused-ignore` beside it while the code is listed and without it
  once the code is enforced. None of the ignores that the override made
  redundant is deleted or has its code changed. No comment or line under
  `tests/` configures mypy, and no `.pyi` sits in any of the three trees.
  No test module holds a `no_type_check`, `TYPE_CHECKING`, `MYPY`, `PY2`
  or `PY3` name, or a branch test on `sys.version_info` or `sys.platform`
  outside R-TDR-6's one site. (R-TDR-7, DEC-TDR-006, DEC-TDR-016)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-9 (non-success):** on planted inputs, the mypy-side helpers
  name each of the following:
  - a stale code, a code occurring but unlisted, a code above its ceiling,
    and a code below its ceiling as one to lower;
  - a code without a ceiling, and a ceiling without a code;
  - a recipe without the named configuration file, a recipe with a path,
    a `[tool.mypy]` table with an `exclude` key, and a wider `mypy_path`;
  - a second option on the tests entry, and a tests entry with an empty
    list;
  - an override reaching a test module spelled with a slash, with a comma,
    as a list and as a mid-pattern glob; one that sets only
    `follow_imports`; and one that relaxes a strict flag;
  - a derived configuration that drops an option, keeps the tests entry or
    keeps a repeated listed code;
  - an environment holding `MYPYPATH`;
  - a platform-only error;
  - a non-JSON stdout line, an error without a code, a nonempty stderr and
    an exit code of 2;
  - a new `# type: ignore[no-untyped-def, unused-ignore]` absent from
    `MYPY_WAIVERS`, a recorded waiver the tree no longer holds, an ignore
    holding two codes besides `unused-ignore`, `unused-ignore` beside an
    unlisted code, a listed code without `unused-ignore`, a bare
    `# type: ignore`, and a waiver re-pointed to another line;
  - a `# mypy: disable-error-code=…` comment, and a `# mypy: ` line inside a
    string literal;
  - a `.pyi` under `openspec_graph/` and under `tests/`, the names
    R-TDR-7 lists, and each planted version or platform condition;
  - a dev extra with a bare `mypy`, a pinned one, a lowered floor and a
    `~=` bound.

  They count an `error` object whose `file` has Windows separators and do
  not count a `note` object. They stay quiet on the well-formed shape, and
  on each quiet case R-TDR-11 lists. (R-TDR-1, R-TDR-2, R-TDR-5, R-TDR-7,
  R-TDR-11, R-TDR-16)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-10:** `D100`–`D103` are selected, and no other `D` rule is.
  Every `D` code in `per-file-ignores` sits either on one concrete file
  under `openspec_graph/` or `tools/`, or on `tests/*`. No `D` code sits in
  `extend-per-file-ignores`, and no comment under `openspec_graph/` or
  `tools/` holds a `noqa` naming a `D` code, read as ruff reads it. The
  `T201` exemptions are exactly R-ZCG-1's two. `make lint` exits 0 and
  offers no escape. (R-TDR-8, R-TDR-14, DEC-TDR-008, DEC-TDR-009)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_lint_is_a_hard_gate"` · stage: `make lint`

- [ ] **AC-TDR-11 (non-success):** under a copy of the new ruff
  configuration, a `print` in a library module is still a finding and the
  same `print` at the two exempt paths is not. The new selection and
  entries disturb no existing exemption. (R-TDR-8)
  _Verified by:_ `pytest -k test_a_print_in_a_library_module_fails_lint` · stage: `make lint`

- [ ] **AC-TDR-12:** the ratchet entries' pairs equal `DOCSTRING_CEILINGS`'
  pairs. With `--isolated`, `--no-respect-gitignore` and `--ignore-noqa`,
  ruff exits 0 with empty stderr, every listed pair's count equals its
  ceiling, with none above, none below and none stale, and every offending
  pair is listed. (R-TDR-9, DEC-TDR-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-13 (non-success):** on planted inputs, the docstring helpers
  name a pair with no finding, a pair offending but unlisted, a pair above
  its ceiling, a pair below its ceiling as one to lower, a pair without a
  ceiling, a `D` code under a glob key other than `tests/*`, a `D` code on
  a file under `tests/` by its own path, and a `D` code under
  `extend-per-file-ignores`. They name each `noqa` spelling R-TDR-11
  lists, and stay quiet on a code list that ends before `D103`. The
  occurrence guard's command counts a planted module that an `.ignore`
  file names. They stay quiet on the well-formed shape. (R-TDR-8, R-TDR-9,
  R-TDR-11)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-14:** read directly:
  - `pyproject.toml` sets no `pydocstyle` convention;
  - its comment records, with their commands, that no selected rule's
    verdict changes under any convention, and that Google is the best fit;
  - the `ANN/D` comment says what R-TDR-10 requires;
  - the header comment above `select` no longer claims that every family
    was at or near zero when selected, and names the four rules as the
    ratchet;
  - no `D` rule beyond the four is selected;
  - no docstring is added under `openspec_graph/` or `tools/`.

  (R-TDR-10, C-TDR-6, DEC-TDR-008, DEC-TDR-010)
  _Verified by:_ stage: `make lint`

- [ ] **AC-TDR-15:** every collected test carries exactly one tier marker
  that agrees with the criterion, the new module marks per function and is
  within the line bound, and `tests/` stays flat. (R-TDR-12, C-TDR-3,
  DEC-TDR-012)
  _Verified by:_ `pytest -k "test_every_test_carries_exactly_one_tier_marker or test_every_tier_marker_matches_its_mechanical_criterion or test_no_test_module_exceeds_the_line_bound or test_the_tests_directory_stays_flat"` · stage: `make test`

- [ ] **AC-TDR-16:** the rule inventory, the golden hashes, the public
  imports and the empty runtime-dependency list are unchanged, and no tool
  version is pinned, in a workflow or in the dev extra. (C-TDR-1,
  R-TDR-16)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_public_import_compatibility or test_runtime_dependencies_stay_empty or test_threshold_guard_fails_on_a_pinned_tool_version"` · stage: `make test`

- [ ] **AC-TDR-17:** `make thresholds` prints PASS. No workflow, action or
  pre-commit line is in the diff, and the Windows job still runs the type
  gate. The only Makefile hunk is the `typecheck` target's help text and
  its recipe line, `python -m mypy --config-file pyproject.toml`. (C-TDR-2,
  DEC-TDR-001)
  _Verified by:_ `pytest -k "test_ci_workflow_has_a_windows_job or test_threshold_guard_passes_on_a_clean_tree"` · stage: `make thresholds`

- [ ] **AC-TDR-18:** `docs/hooks.md`, `tests/AGENTS.md` and
  `.claude/agents/planlint-verifier.md` say what R-TDR-13 requires, with
  `tests/AGENTS.md` within its budget and its precedence clause and links
  intact. No dated record is in the diff. (R-TDR-13)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve"` · stage: `make docs-check`

- [ ] **AC-TDR-19:** `CHANGELOG.md` `[Unreleased]` carries the entry that
  R-TDR-15 names, with the two superseded passages among it, and every
  versioned section still links to its release tag. `tasks.md` records
  every figure that R-TDR-15 names, with its commit and command. No
  requirement or criterion pins a count another package changes, every
  test this spec cites resolves, and the package validates clean.
  (R-TDR-14, R-TDR-15, C-TDR-4, DEC-TDR-011, DEC-TDR-013, DEC-TDR-017)
  _Verified by:_ `pytest -k "test_every_changelog_version_links_to_its_release_tag or test_every_spec_test_citation_resolves_to_a_real_test"` · stage: `make validate`

- [ ] **AC-TDR-20 (observed on the CI run on the W6.5 commit):** the type
  gate and the mypy occurrence and waiver guards are green on every Linux
  leg and on Windows. This is recorded in `tasks.md` with that run's id,
  the head SHA it ran for and the merge SHA it tested. (C-TDR-5,
  DEC-TDR-005, DEC-TDR-007, DEC-TDR-013)
  _Verified by:_ stage: `make typecheck`

- [ ] **AC-TDR-21 (observed on the CI run on the W6.6 commit):** the lint
  gate, and the docstring shape and occurrence guards that the `test` stage
  runs, are green on every Linux leg and on Windows. This is recorded in
  `tasks.md` with that run's id, the head SHA it ran for and the merge SHA
  it tested, separately from AC-TDR-20's run. (C-TDR-5, DEC-TDR-009,
  DEC-TDR-013)
  _Verified by:_ stage: `make lint`

- [ ] **AC-TDR-22:** read through `read_pyproject()` and
  `packaging.requirements.Requirement` by a guard: the dev extra's one
  `mypy` entry carries exactly a floor at the first release that accepts
  `-O json`, with a comment naming that release and the guard, and it
  landed in the W6.5 commit. No dev-extra entry's specifier holds `==`,
  and a marker is not read as one. On every leg the occurrence guard's
  `-O json` runs exit 0 or 1. (R-TDR-16, C-TDR-1, DEC-TDR-014)
  _Verified by:_ stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Typecheck | `make typecheck` | AC-TDR-1, 2, 6, 7, 20: the three trees checked from `files` under strict, read from the configuration file the recipe names; the nine codes and the platform-only errors fixed; the TOML reader leg-independent; every leg green on the W6.5 commit's CI run |
| Focused | `make test` | AC-TDR-3, 4, 5, 8, 9, 12, 13, 15, 16, 22: the recipe, key-set, override, occurrence, waiver, stub-name-and-condition, dev-extra and docstring guards green on the tree and red on their planted inputs. mypy itself says what each override does to each test module. The occurrence run is the gate's own, less the tests entry, re-checked before it runs, under both `--platform linux` and `--platform win32` with `-O json` and no `MYPYPATH`; the two error sets are equal and every count equals its ceiling. Every inline ignore is a waiver keyed by its line, and nothing hides code from mypy. ruff counts with `--isolated --no-respect-gitignore --ignore-noqa`. mypy is floored and nothing is pinned. Tiers and the line bound hold, and the invariants are unchanged |
| Lint | `make lint` | AC-TDR-10, 11, 14, 21: `D100`–`D103` selected, with per-file entries and the `tests/` policy key, and no `D` code in `extend-per-file-ignores` or a `noqa`; every existing exemption undisturbed; the convention recorded, not configured; every leg green on the W6.6 commit's CI run |
| Threshold guard | `make thresholds` | AC-TDR-17: PASS; no workflow, action or hook line changed; the Makefile changed only in the `typecheck` target's help text and recipe |
| Docs | `make docs-check` | AC-TDR-18: the scope stated where contributors and agents read it, the agent file within budget |
| Self-check | `make validate` | AC-TDR-19: this package, then the whole tree, validate clean; every cited test resolves |
| Full | `make pre-pr` | the whole ladder green at each of the package's three commits |
