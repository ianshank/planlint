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
comment lowers a count as surely as a code added to the override would. A
count that falls below its ceiling leaves room for new debt until someone
remembers to lower it. And a ruff exemption, like a disabled mypy code, is
silent once it exempts nothing, so nothing would ever force either list to
shrink.

So this spec names the trees once in `files` and gives mypy the module
bases the scripts and the suite actually run with. It fixes in `tests/`
every code that is cheaper to fix than to exempt, and every error that only
one platform reports. It lists the rest in one `tests.*` override and holds
every listed code to a recorded count, which the guard requires to match
exactly and on both platforms. It records every inline ignore as a
shrink-only waiver and refuses every comment that configures mypy. It
selects `D100`–`D103` with one exemption per offending file of the package
and `tools/`, each held to an exact recorded count. It floors mypy at the
release whose JSON output the guard reads. And it records rather than
configures the docstring convention.

**Evidence:** measured at `1c8917c` and re-measured on 2026-10-07 at
`d2b3cc6` (`claude/m2-tests-under-mypy` with #42's head merged). Every figure
here names its command, and the proposal gives each one in full. At
`d2b3cc6`, `python -m mypy tests --explicit-package-bases` reports 185
errors in 32 files (61 checked). Counted by the trailing code of `error:`
lines only, those are sixteen codes, of which `no-untyped-def`,
`attr-defined`, `arg-type`, `type-arg`, `no-any-return`, `index` and
`union-attr` hold all but fifteen occurrences. The bracketed `str` and
`bytes` that a looser tally finds are the `PathLike[str]` of `note:` lines.
Without explicit bases, mypy stops at "Source file found twice under
different module names" for `tests/graft_support.py` and exits 2. `python
-m mypy openspec_graph tools --explicit-package-bases` reports 19 errors in
12 files where today's command reports none. With `tools` on the module
search path it reports none again, and the tests' count falls to 184.
`MYPYPATH=tools python -m mypy tests --explicit-package-bases -O json`
emits 184 error objects under `--platform linux` and 188 under `--platform
win32`, the four extra all `attr-defined` on `os.mkfifo` in
`tests/test_detect_thresholds.py`; both runs leave stderr empty and exit 1.
The Linux run with `--shadow-file` standing a copy of `tests/test_graph.py`
headed by `# mypy: disable-error-code="no-untyped-def"` in for that file
reports `no-untyped-def` 72 against the unshadowed 96. That reproduces the
round-1 reviewer's figure. With the seven codes disabled for `tests.*`, the
residue is 23 errors in 15 files: the fifteen occurrences, plus eight inline
`# type: ignore[arg-type]` or `[attr-defined]` comments that the override
makes redundant. A command-line `--enable-error-code` does not lift a
per-module `disable_error_code`. `python -m ruff check --select
D100,D101,D102,D103 --statistics` reports 52 findings in 18 files of
`openspec_graph/`, 25 in 12 files of `tools/` and 584 in `tests/`, 575 of
them test functions. The sorted finding set is identical under no
`pydocstyle` convention and under each of the three. A stale
`per-file-ignores` entry draws no ruff warning.

---

## Requirements

- R-TDR-1: `[tool.mypy] files` MUST list `openspec_graph`, `tools` and
  `tests`, and `[tool.mypy]` MUST set `explicit_package_bases = true` and a
  `mypy_path` holding `tools`. `strict = true`, `warn_unreachable = true`
  and `python_version = "3.10"` MUST be unchanged. The `typecheck` recipe
  MUST be `python -m mypy` with no path argument, so `files` is the one
  list of checked trees and a tree is added by a configuration line. The
  type gate, `make typecheck`, MUST exit 0 on the tree after this change
  and MUST still check `openspec_graph/` and `tools/` under strict, and
  this change MUST add no per-module option for either. A guard test MUST
  read the recipe and the table structurally and assert the bare recipe,
  the three trees, the two module-base options and the three unchanged
  options.
- R-TDR-2: An override applies to the tests when any of its `module`
  patterns, matched as mypy matches them, names a module under `tests/`.
  Exactly one override MUST apply to the tests. Its `module` MUST be
  `"tests.*"` and its only option MUST be `disable_error_code`. No other
  per-module option — `ignore_errors`, `disallow_untyped_defs`,
  `check_untyped_defs`, `follow_imports`, `ignore_missing_imports` or any
  other — MAY apply to a module under `tests/`, so every code the entry
  does not list is enforced in `tests/` under the global strict
  configuration from the commit that lands it. The entry's list MUST be a
  subset of `no-untyped-def`, `attr-defined`, `arg-type`, `type-arg`,
  `no-any-return`, `index` and `union-attr`, holding exactly those of the
  seven that still occur when the entry lands, and no other code MAY ever
  be added to it. This requirement constrains only overrides that apply to
  the tests. An override for a module of the package, of `tools/` or of a
  third-party import, the `tomli` one of R-TDR-6 among them, is outside it
  (DEC-TDR-015).
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
  `# type: ignore`, a `# mypy:` comment, a `cast` to `Any`, a `# noqa` or a
  removed assertion: it is an annotation, a narrowing, a typed local or a
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
  mapping's keys are the same set, naming a listed code without a ceiling
  and a ceiling without a listed code.
- R-TDR-5: A guard test MUST measure every code's occurrences by running
  mypy over `tests/` with the tests override removed and every other option
  of `[tool.mypy]` and of its other overrides kept. It runs through a
  configuration file it derives under its own temporary directory, with
  `-O json`, under `env_without_coverage()` and from the repository root,
  once with `--platform linux` and once with `--platform win32`, each with
  its own cache directory under that temporary directory. Each run MUST
  leave stderr empty and exit 0 or 1, and the guard MUST name a run that
  does not. It MUST read stdout as one JSON object per line and name a line
  that is not one. It MUST count, by their `code` field, only objects whose
  `severity` is `error` and whose `file`, with path separators normalised,
  is under `tests/`, and it MUST name an error without a code. It MUST name
  every error that one platform reports and the other does not, with its
  file, line and code, as a platform-only error to fix under R-TDR-3 and
  never as a reason to list a code. It MUST fail whenever a code's count
  differs from its ceiling, in either direction:
  - a count above its ceiling is named with both numbers;
  - a count below its ceiling is named in the form `lower <code> from A to
    B`;
  - a listed code with no occurrence is named as stale, and the commit that
    fixed its last occurrence MUST remove it from the override and from
    the ceilings;
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
  of (path, enclosing function or `<module>`, code) entries, under a
  comment stating that an entry is removed and never added. The enclosing
  function is the dotted name of the innermost `def` around the comment,
  through any enclosing functions and classes. A guard test MUST assert
  that the waivers it reads from the tree and the recorded entries are
  equal as multisets. It MUST name each unrecorded comment with its path
  and line, and each recorded entry the tree no longer holds.
  - While its code is listed, a waiver's brackets MUST hold exactly that
    one listed code and `unused-ignore`. The guard names a bare ignore, an
    ignore holding no listed code, an ignore holding more than one code
    beside `unused-ignore`, and a listed code without `unused-ignore`.
  - The inline ignores that the override makes redundant are the waivers.
    Each MUST keep its code and gain `unused-ignore`, and none MAY be
    deleted or have its code changed, because each records a review
    decision of the package that wrote it and is needed again when its code
    is re-enabled.
  - When a code leaves the override, the commit that removes it MUST strip
    `unused-ignore` from that code's waivers and keep their entries. An
    entry whose code is enforced holds exactly that code, so strict mode
    reports it once it is unused.
  - An ignore that is unused even without the override is a defect rather
    than a decision, and is fixed under R-TDR-3.
  - The same guard MUST name every comment under `tests/` that configures
    mypy. That is every comment token, found with `tokenize`, whose text
    after the `#` and any whitespace begins with `mypy:`, and every
    physical line that begins with mypy's own inline-configuration prefix,
    `# mypy: `, which mypy honours on a line inside a string literal too.
  - The guard MUST read comments with `tokenize`, not by a substring search
    over the source, and MUST find an ignore inside a comment token as
    mypy's own pattern finds it, so `#type:ignore[...]` is read
    (DEC-TDR-006).
- R-TDR-8: `[tool.ruff.lint] select` MUST include `D100`, `D101`, `D102` and
  `D103` and no other `D` rule. In `[tool.ruff.lint.per-file-ignores]` a `D`
  code MAY appear only in two places. One is under a key that is one
  concrete file path under `openspec_graph/` or `tools/`, listing exactly
  the codes among the four that the file violates when the entry is
  written: a ratchet entry. The other is the existing `tests/*` key, which
  MUST carry all four as a policy exemption. No glob key other than
  `tests/*` MAY carry a `D` code. Where a file already has an entry, its
  `D` codes join that entry. Every non-`D` code of every existing entry
  MUST be unchanged, so R-ZCG-1's two `T201` exemptions stand. `make lint`
  MUST exit 0.
- R-TDR-9: `tests/test_static_ratchets.py` MUST hold a module-level
  `DOCSTRING_CEILINGS` that maps each ratchet entry's file to each of its
  `D` codes and that code's finding count in the file at the commit that
  lands the entries. It MUST sit under a comment stating R-TDR-4's rule,
  with a ruff release in place of a mypy release.
  - A guard test MUST assert that the ratchet entries' file-and-code pairs
    and the mapping's pairs are the same set, and that no key breaks
    R-TDR-8's shape, naming each offender.
  - A guard test MUST run ruff over `openspec_graph` and `tools` with the
    repository's configuration, `--select D100,D101,D102,D103`, the
    `per-file-ignores` table replaced by an empty one, JSON output and
    `--exit-zero`. It MUST fail unless ruff exits 0 with empty stderr, and
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
  - the override guard, red with no override;
  - the mypy occurrence guard, red naming every occurring code as unlisted
    and the Windows-only `os.mkfifo` errors as platform-only;
  - the waiver guard, red naming every inline ignore of the unchanged tree as
    unrecorded;
  - the docstring shape guard, red with `D` unselected, and its occurrence
    guard, red naming every offending pair as unlisted.

  Each red run MUST be recorded in `tasks.md` and never committed as a tree
  state. Each guard MUST also be shown red on planted inputs:
  - a listed code with no occurrence; a code that occurs but is not listed;
    a listed code above its ceiling; and a listed code below its ceiling,
    named as one to lower;
  - a code listed without a ceiling, and a ceiling without a listed code;
  - a second option on the tests override, and a second override that
    applies to a test module;
  - mypy JSON output with a `note` object, which MUST NOT be counted; an
    `error` object whose `file` has Windows separators, which MUST be; a
    stdout line that is not JSON; an error without a code; a nonempty
    stderr; and an exit code of 2;
  - two platforms' outputs that agree but for one error, named as
    platform-only;
  - a derived configuration that drops an option or keeps the tests
    override;
  - a new `# type: ignore[no-untyped-def, unused-ignore]` absent from
    `MYPY_WAIVERS`; a recorded waiver the tree no longer holds; a waiver
    holding two listed codes; an `unused-ignore` beside only enforced codes;
    and a bare `# type: ignore`;
  - a `# mypy: disable-error-code=…` comment, and a `# mypy: ` line inside a
    string literal;
  - a ratchet pair with no finding; a pair that offends but is not listed; a
    pair above its ceiling; a pair below its ceiling, named as one to lower;
    and a pair without a ceiling;
  - a `D` code under a glob key other than `tests/*`, and a `D` code on a
    file under `tests/` by its own path.

  Each MUST be shown quiet on the matching well-formed input.
- R-TDR-12: Every new test MUST carry exactly one tier marker that agrees
  with `tests/shape_support.py`'s criterion (R-TSS-5, R-TSS-6). The guards
  that run mypy and ruff are `e2e`. The guards that read `pyproject.toml`,
  the Makefile or the modules under `tests/` are `integration`. The
  planted-input test, whose helpers take their input as arguments, is
  `unit`. The new module MUST mark per function, MUST stay within
  `MAX_TEST_MODULE_LINES`, and MUST contribute no occurrence of a listed
  code and no waiver.
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
    a file, a waiver or a `# mypy:` comment; and never raise a ceiling
    except to follow a tool release, as R-TDR-4 says.
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
    run on the W6.6 commit, each with its run id.
- R-TDR-16: The dev extra's `mypy` entry MUST carry a floor at the first
  mypy release that accepts `-O json`. A comment beside it MUST name that
  release and the guard that needs it. The floor MUST land in the commit
  that first runs mypy with `-O json`, as `migrate-license-metadata-pep639`'s
  R-LM-2 raised the setuptools floor in the commit that used the form that
  needed it. It MUST be a floor and not a pin: no dev-extra entry MAY carry
  `==` (DEC-TDR-014).
- C-TDR-1: No change under `openspec_graph/`, no rule, no golden hash, no
  runtime dependency and no new dev dependency. `pytest` and `hypothesis`
  ship their own types, so no stub package is added. The one dev-extra edit
  is R-TDR-16's floor on the existing `mypy` entry. The `RULES` tuple,
  `README.md`'s rules table, `tests/baseline_rules.json`, the
  `validate`/`graph`/`rules` hashes and `[project] dependencies` are
  untouched.
- C-TDR-2: No workflow, composite-action or `.pre-commit-config.yaml` line MAY
  change. CI's `test` matrix, its Windows job and the pre-commit typecheck
  hook already run `make typecheck`, and the hook already fires on a staged
  test module. The only Makefile change is the `typecheck` target's help
  text and its recipe line. `make thresholds` MUST print PASS, and the four
  coverage floors MUST be unchanged in value and hold.
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
  W6.6 commit MUST show the second.
- C-TDR-6: No `D` rule other than `D100`–`D103` MAY be selected, and this
  package MUST add no docstring under `openspec_graph/` or `tools/`. The
  ratchet entries shrink in the packages that already touch those files.

---

## Decisions

- **DEC-TDR-001:** `tests` joins `make typecheck` through `[tool.mypy]
  files`, and the recipe names no path. Today the recipe is `python -m mypy
  openspec_graph tools`, and positional paths override `files`. So the
  plan's one-line change to `files` would have changed nothing the gate
  runs: the list would have lived in two places, and the one that mattered
  would have stayed short. A bare `python -m mypy` makes `files` the one
  list. That is the shape `coverage-run`'s bare `--cov` already gives the
  coverage sources (R-MCO-2: the trees are named in configuration, never in
  the recipe). The gate keeps its name and its callers. CI's `test` matrix
  and its Windows job run `make typecheck` on every interpreter and on
  Windows. The pre-commit hook runs it with `types: [python]` and
  `pass_filenames: false`, so a staged test module already triggers it.
  Four other specs cite the stage on verification lines (`make
  stage-citations` at `d2b3cc6`). Cold, the gate goes from 0.9 s to 3.6 s
  (the proposal's timing commands, at `d2b3cc6`). Rejected:
  `python -m mypy openspec_graph tools tests` (a second list beside
  `files`); a `typecheck-tests` target (a second gate for one tool, which
  needs a workflow step and a hook entry this package otherwise does not
  touch); a mypy run inside pytest only (the type gate would then run under
  coverage, and only where the suite runs).
- **DEC-TDR-002:** `explicit_package_bases = true` with `mypy_path` holding
  `tools`. Explicit bases are needed because neither `tests/` nor `tools/`
  has an `__init__.py`. Without them, mypy names `tests/graft_support.py`
  both `graft_support` and `tests.graft_support`, and stops. With them
  alone, mypy roots every module at the repository and renames
  `tools/_common.py` to `tools._common`. Each gate script imports `_common`
  the way it runs: `python tools/<script>.py` puts the script's directory
  first on `sys.path`. So the scripts fail to resolve it (19 errors in 12
  files from `python -m mypy openspec_graph tools --explicit-package-bases`
  at `d2b3cc6`). `mypy_path` holding `tools` makes that directory a base
  too. That is the static form of how the scripts run, and of
  `tests/test_wheel_metadata.py`'s own `sys.path` insert, so both resolve
  and `tools/` stays clean. Both options are global in mypy, which is why
  the measurement covers all three trees. Rejected: a `tools/__init__.py`
  (mypy would then name the module `tools._common` with or without explicit
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
  `d2b3cc6`). The seven listed codes hold the rest, and clearing them is
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
- **DEC-TDR-005:** the occurrence guard runs mypy twice, under `--platform
  linux` and `--platform win32`, with the tests override removed. It runs
  through a configuration it derives, with `-O json`, each run with a cold
  cache under its own temporary directory, and it requires the two error
  sets to agree.
  - Derived, because a per-module `disable_error_code` beats a command-line
    `--enable-error-code` (measured), so the override cannot be lifted from
    the command line. It is written in mypy's INI form, which mypy reads
    with the same option names, because the standard library on the 3.10
    leg writes no TOML. Every global option and every other override is
    carried, so the measurement differs from the gate by the one entry and
    nothing else.
  - Both platforms, because CI runs a Windows leg. mypy's Windows view
    reported four errors the Linux view did not (`attr-defined` on
    `os.mkfifo`, by the proposal's two-platform command at `d2b3cc6`), and
    under the override the Windows leg's type gate would have hidden them.
    Requiring the two error sets to agree turns platform-only debt into a
    named error to fix, under DEC-TDR-003's own rule, and makes each ceiling
    one number on every leg. A mismatch is named as a platform-only error to
    fix. It is never listed and never given a ceiling per platform. No CI
    leg runs macOS, so these two platforms are every platform the gate runs
    on.
  - `-O json`, because a code read from a JSON field cannot be confused
    with the bracketed text of a note line. That confusion is where the
    plan's `str` came from. Only `severity == "error"` objects are counted.
  - Empty stderr and an exit code of 0 or 1, because mypy exits 2 on a
    usage error or a crash. A guard that counted the stdout of such a run
    would compare nothing and call it a match.
  - A cold cache under the test's temporary directory, so the test writes
    nothing into the tree and reads nothing stale. The two runs took 3.7 s
    and 4.1 s cold (the proposal's timing command, at `d2b3cc6`).

  Rejected: reusing the repository's `.mypy_cache` (a test that writes into
  the tree, and a cache keyed on options the gate does not use); Linux only
  (the first draft's choice, which left Windows-only errors unmeasured and,
  under the override, unchecked on every leg); the leg's own platform
  (ceilings that differ by leg); per-platform ceilings (two numbers for one
  code, and the Windows-only debt kept rather than fixed); parsing the text
  output (a format for people, which the JSON output makes unnecessary).
- **DEC-TDR-006:** every inline ignore under `tests/` is a recorded waiver,
  and every comment that configures mypy is refused.
  - The inline ignores that the override makes redundant (eight, by the
    proposal's emulation at `d2b3cc6`) keep their codes and gain
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
  - So every ignore is recorded in `MYPY_WAIVERS`, which only shrinks. It is
    keyed by path, enclosing function and code rather than by line, because
    a line number moves with every edit above it while a function name is
    what a reviewer reads. It is compared as a multiset, so a second ignore
    of the same code in the same function is named. Each waiver holds
    exactly one listed code with `unused-ignore`, so one comment cannot
    waive two codes, or an enforced one.
  - When a code is re-enabled, its waivers keep their entries and lose
    `unused-ignore`, so strict mode polices them as ordinary ignores of an
    enforced code.
  - Two more forms lower a count with no override. A bare `# type: ignore`
    before a module's first statement silences the whole module: it passes
    clean an inline program whose body holds an untyped `def` and a
    mistyped assignment (`python -m mypy -O json --strict -c …`, run outside
    the worktree, at `d2b3cc6`). It is named because it holds no code. A
    file-level `# mypy: disable-error-code=…` comment is an override in
    disguise: one at the head of `tests/test_graph.py` lowers
    `no-untyped-def` from 96 to 72 (the round-1 reviewer's figure,
    reproduced by the proposal's `--shadow-file` command at `d2b3cc6`). So
    every `# mypy:` comment is named.
  - The comment check reads tokens with `tokenize`, so a string that looks
    like a comment is not one. mypy, however, reads its inline
    configuration by physical line (`mypy/util.py`, `get_mypy_comments`: a
    line that starts with `# mypy: `). It honours such a line inside a
    docstring, which no comment token reveals (the same `-c` measurement
    with the comment on a docstring's second line: exit 0). So the guard
    also names every physical line with that prefix, which is mypy's own
    rule and not a substring search. As a result, the guard module writes
    its planted inputs so that no line of its own begins with it.

  Rejected: deleting the ignores (above); disabling `unused-ignore` for
  `tests.*` (it would never be re-enabled, because no stale ignore would
  ever be reported to fix); a per-module `warn_unused_ignores = false` (the
  same, spelled as an option R-TDR-2 forbids); keying waivers by line (they
  would churn on every unrelated edit); a recorded list of permitted
  `# mypy:` comments (a second override list that R-TDR-2's one entry
  exists to prevent); a substring search over the source (it would name the
  guard's own planted strings).
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
  form reports an unused ignore and a `no-any-return`. Rejected:
  `# type: ignore[import-not-found, unused-ignore]` on the import (a waiver
  of a code the override does not list, which R-TDR-7 forbids); adding
  `tomli` to the dev extra for every interpreter (a dependency change for a
  type checker's benefit).
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
    `d2b3cc6`) are test functions whose names are sentences, and whose
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
  codes; an exact count per file and code; and no docstring written here.
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
  that W2 rewrites anyway).
- **DEC-TDR-010:** the convention is measured and recorded, not configured.
  - Under no `pydocstyle` convention and under each of `google`, `numpy`
    and `pep257`, ruff reports the identical `D100`–`D103` finding set. The
    sorted concise output of `python -m ruff check --isolated --select
    D100,D101,D102,D103 --config 'lint.pydocstyle.convention = "<c>"'
    openspec_graph tools tests` has one digest under all four, with 661
    findings each, at `d2b3cc6`. So a `convention` key would change no
    selected rule's verdict while reading as a gate. That is the class of
    configuration this repository's own `pyproject.toml` comment refuses:
    "an ignore list for rules that were never on is config that looks like
    a gate and is not".
  - The measurement belongs in the comment. Over the package and `tools/`,
    with the presence rules set aside, Google is the best fit: it leaves
    the fewest findings of the wider family, 37 against 67 under `numpy`
    and under `pep257` (`python -m ruff check --isolated --select D
    --ignore D100,…,D107 --config 'lint.pydocstyle.convention = "<c>"'
    openspec_graph tools --statistics`, at `d2b3cc6`). The difference is
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
  - `shape-the-test-suite` was unmerged below this branch when the package
    was drafted, and its head is merged into the branch at `d2b3cc6`.
    C-TSS-6 is named for the reason in DEC-TDR-008, and that package's
    files are not edited from here.

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
    by `wc -l` at `d2b3cc6`), so its size is no longer the reason.
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
    `v1.10.0`. Each JSON object carries `file`, `line`, `column`,
    `message`, `hint`, `code` and `severity` from that release on.
  - No dev-extra entry is floored at `d2b3cc6` (`pyproject.toml`'s `dev`
    list). The precedent followed is R-LM-2's setuptools floor: a floor at
    the release that understands the feature used, raised in the commit
    that uses it, under a comment naming why.
  - A floor is not a pin. `tools/check_no_hardcoded_thresholds.py` names
    `mypy==` in a workflow, and `test_dependabot_does_not_add_a_pip_ecosystem`
    names a pip ecosystem; neither is touched by a `>=` bound, and the
    decision that the extras float is kept.
  - Without the floor, nothing states that the guard needs the flag. A
    resolver free to choose an older mypy would make the guard's run a
    usage error, which DEC-TDR-005's exit-code check would name as a broken
    run, not as a requirement.

  Rejected: no floor (the requirement unstated); a pin (the extras float by
  decision); parsing text output to avoid the floor (DEC-TDR-005).
- **DEC-TDR-015:** R-TDR-2 judges only the overrides that apply to the
  tests. The first draft also allowed exactly one other override, the
  `tomli` one. That would have failed the first package to need an
  override for an untyped import in `openspec_graph/` or `tools/`, on a
  matter this package has no stake in. The boundary is drawn by mypy's own
  matching of `module` patterns, not by the string `tests.*`. An override
  for one test module, such as `module = "tests.test_graph"` with
  `disable_error_code`, applies to the tests and would lower a count
  outside the one entry, so it is named. Rejected: the first draft's
  closed list of overrides (above); matching the literal `tests.*` only
  (it misses the per-module bypass).

---

## Acceptance Criteria

- [ ] **AC-TDR-1:** `[tool.mypy]` keeps `strict = true`,
  `warn_unreachable = true` and `python_version = "3.10"`, and the type gate
  exits 0 on the finished tree with `openspec_graph/`, `tools/` and `tests/`
  checked from `files`. (R-TDR-1, C-TDR-5, DEC-TDR-001, DEC-TDR-002)
  _Verified by:_ `pytest -k "test_typecheck_passes_on_clean_repo or test_mypy_is_strict_and_warns_on_unreachable_code"` · stage: `make typecheck`

- [ ] **AC-TDR-2 (non-success):** under a copy of the new configuration, a
  bare generic in a `tools/` module is still a `type-arg` error, and a type
  error in a module outside every package base still fails mypy and names its
  file. Neither explicit bases nor the new search path silences either.
  (R-TDR-1, R-TDR-14, DEC-TDR-002, DEC-TDR-011)
  _Verified by:_ `pytest -k "test_a_bare_generic_in_tools_fails_typecheck or test_mypy_fails_on_a_type_error"` · stage: `make typecheck`

- [ ] **AC-TDR-3:** read structurally from the Makefile and `pyproject.toml`:
  the `typecheck` recipe is `python -m mypy` with no path argument, `files`
  holds the three trees, `explicit_package_bases` is true and `mypy_path`
  holds `tools`. The guard ran red on the unchanged Makefile, as `tasks.md`
  records. (R-TDR-1, R-TDR-11, DEC-TDR-001)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-4:** exactly one override applies to a module under
  `tests/`. Its `module` is `tests.*`, its only option is
  `disable_error_code`, its codes are a subset of R-TDR-2's seven, and they
  are exactly the keys of `MYPY_TESTS_CEILINGS`. No override for another
  module is judged. (R-TDR-2, R-TDR-4, DEC-TDR-003, DEC-TDR-004,
  DEC-TDR-015)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-5:** with the override lifted, mypy's JSON output gives the
  same errors under `--platform linux` and `--platform win32`, and each run
  exits 0 or 1 with empty stderr. Every listed code's count equals its
  ceiling, with none above, none below and none stale, and every code that
  occurs is listed. The guard's call duration is in `tasks.md`. (R-TDR-4,
  R-TDR-5, DEC-TDR-004, DEC-TDR-005, DEC-TDR-014)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-6:** none of the codes R-TDR-3 fixes occurs in `tests/` with
  the override lifted, no error occurs under one platform only, and the
  type gate passes with those codes unlisted. Read at review, the diff of
  every fixed site adds no ignore, no `# mypy:` comment, no cast to `Any`
  and no `noqa`, and removes no assertion. (R-TDR-3, C-TDR-3, DEC-TDR-003)
  _Verified by:_ `pytest -k test_typecheck_passes_on_clean_repo` · stage: `make typecheck`

- [ ] **AC-TDR-7:** `tests/support.py`'s reader selects its TOML module by
  version and returns an annotated local, and the `tomli` override sets
  only `ignore_missing_imports`. The pyproject guards that read through the
  reader pass on the leg that installs `tomli` and on those that do not.
  (R-TDR-6, C-TDR-5, DEC-TDR-007)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_mypy_is_strict_and_warns_on_unreachable_code"` · stage: `make typecheck`

- [ ] **AC-TDR-8:** every inline ignore under `tests/` is a recorded
  `MYPY_WAIVERS` entry, and every entry is in the tree, compared as
  multisets. Each waiver of a listed code holds that code and
  `unused-ignore` and nothing else. None of the ignores that the override
  made redundant is deleted or has its code changed. No comment or line
  under `tests/` configures mypy. (R-TDR-7, DEC-TDR-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-9 (non-success):** on planted inputs, the mypy-side helpers
  name each of the following:
  - a stale code, a code occurring but unlisted, a code above its ceiling,
    and a code below its ceiling as one to lower;
  - a code without a ceiling, and a ceiling without a code;
  - a second option on the tests override, and a second override that
    applies to a test module;
  - a derived configuration that drops an option or keeps the override;
  - a platform-only error;
  - a non-JSON stdout line, an error without a code, a nonempty stderr and
    an exit code of 2;
  - a new `# type: ignore[no-untyped-def, unused-ignore]` absent from
    `MYPY_WAIVERS`, a recorded waiver the tree no longer holds, a waiver
    holding two listed codes, an `unused-ignore` beside only enforced codes,
    and a bare `# type: ignore`;
  - a `# mypy: disable-error-code=…` comment, and a `# mypy: ` line inside a
    string literal.

  They count an `error` object whose `file` has Windows separators and do
  not count a `note` object, and they stay quiet on the well-formed shape.
  (R-TDR-2, R-TDR-5, R-TDR-7, R-TDR-11)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-10:** `D100`–`D103` are selected, and no other `D` rule is.
  Every `D` code in `per-file-ignores` sits either on one concrete file
  under `openspec_graph/` or `tools/`, or on `tests/*`. The `T201`
  exemptions are exactly R-ZCG-1's two. `make lint` exits 0 and offers no
  escape. (R-TDR-8, R-TDR-14, DEC-TDR-008)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_lint_is_a_hard_gate"` · stage: `make lint`

- [ ] **AC-TDR-11 (non-success):** under a copy of the new ruff
  configuration, a `print` in a library module is still a finding and the
  same `print` at the two exempt paths is not. The new selection and
  entries disturb no existing exemption. (R-TDR-8)
  _Verified by:_ `pytest -k test_a_print_in_a_library_module_fails_lint` · stage: `make lint`

- [ ] **AC-TDR-12:** the ratchet entries' pairs equal `DOCSTRING_CEILINGS`'
  pairs. With the exemptions lifted, ruff exits 0 with empty stderr, every
  listed pair's count equals its ceiling, with none above, none below and
  none stale, and every offending pair is listed. (R-TDR-9, DEC-TDR-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-13 (non-success):** on planted inputs, the docstring helpers
  name a pair with no finding, a pair offending but unlisted, a pair above
  its ceiling, a pair below its ceiling as one to lower, a pair without a
  ceiling, a `D` code under a glob key other than `tests/*`, and a `D` code
  on a file under `tests/` by its own path. They stay quiet on the
  well-formed shape. (R-TDR-9, R-TDR-11)
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
  version is pinned. (C-TDR-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_public_import_compatibility or test_runtime_dependencies_stay_empty or test_threshold_guard_fails_on_a_pinned_tool_version"` · stage: `make test`

- [ ] **AC-TDR-17:** `make thresholds` prints PASS. No workflow, action or
  pre-commit line is in the diff, and the Windows job still runs the type
  gate. The only Makefile hunk is the `typecheck` target's help text and
  recipe line. (C-TDR-2)
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
  (R-TDR-14, R-TDR-15, C-TDR-4, DEC-TDR-011, DEC-TDR-013)
  _Verified by:_ `pytest -k "test_every_changelog_version_links_to_its_release_tag or test_every_spec_test_citation_resolves_to_a_real_test"` · stage: `make validate`

- [ ] **AC-TDR-20 (observed on the CI run on the W6.5 commit):** the type
  gate and the mypy occurrence and waiver guards are green on every Linux
  leg and on Windows. This is recorded in `tasks.md` with that run's id.
  (C-TDR-5, DEC-TDR-005, DEC-TDR-007, DEC-TDR-013)
  _Verified by:_ stage: `make typecheck`

- [ ] **AC-TDR-21 (observed on the CI run on the W6.6 commit):** the lint
  gate, and the docstring shape and occurrence guards that the `test` stage
  runs, are green on every Linux leg and on Windows. This is recorded in
  `tasks.md` with that run's id, separately from AC-TDR-20's run.
  (C-TDR-5, DEC-TDR-009, DEC-TDR-013)
  _Verified by:_ stage: `make lint`

- [ ] **AC-TDR-22:** read directly: the dev extra's `mypy` entry carries a
  floor at the first release that accepts `-O json`, with a comment naming
  that release and the guard, and it landed in the W6.5 commit. No
  dev-extra entry carries `==`. On every leg the occurrence guard's
  `-O json` runs exit 0 or 1. (R-TDR-16, C-TDR-1, DEC-TDR-014)
  _Verified by:_ `pytest -k test_threshold_guard_fails_on_a_pinned_tool_version` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Typecheck | `make typecheck` | AC-TDR-1, 2, 6, 7, 20: the three trees checked from `files` under strict; the nine codes and the platform-only errors fixed; the TOML reader leg-independent; every leg green on the W6.5 commit's CI run |
| Focused | `make test` | AC-TDR-3, 4, 5, 8, 9, 12, 13, 15, 16, 22: the recipe, override, occurrence, waiver and docstring guards green on the tree and red on their planted inputs. mypy is run under both `--platform linux` and `--platform win32` with `-O json`, the two error sets are equal, and every count equals its ceiling. Every inline ignore is a recorded waiver and no comment configures mypy. mypy is floored and nothing is pinned. Tiers and the line bound hold, and the invariants are unchanged |
| Lint | `make lint` | AC-TDR-10, 11, 14, 21: `D100`–`D103` selected, with per-file entries and the `tests/` policy key; every existing exemption undisturbed; the convention recorded, not configured; every leg green on the W6.6 commit's CI run |
| Threshold guard | `make thresholds` | AC-TDR-17: PASS; no workflow, action or hook line changed; the Makefile changed only in the `typecheck` target's help text and recipe |
| Docs | `make docs-check` | AC-TDR-18: the scope stated where contributors and agents read it, the agent file within budget |
| Self-check | `make validate` | AC-TDR-19: this package, then the whole tree, validate clean; every cited test resolves |
| Full | `make pre-pr` | the whole ladder green at each of the package's three commits |
