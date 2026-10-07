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
per-code count taken on Linux is not the count on Windows. And a ruff
exemption, like a disabled mypy code, is silent once it exempts nothing, so
nothing would ever force either list to shrink.

So this spec names the trees once in `files`, gives mypy the module bases the
scripts and the suite actually run with, fixes in `tests/` every code that is
cheaper to fix than to exempt, lists the rest in one `tests.*` override,
holds every listed code to a recorded ceiling and names a listed code that no
longer occurs, keeps the review decisions the inline ignores record, selects
`D100`–`D103` with one exemption per offending file of the package and
`tools/`, holds each to a recorded ceiling and names an entry whose file no
longer offends, and records rather than configures the docstring convention.

**Evidence:** measured at `1c8917c` (`claude/m2-tests-under-mypy`, stacked on
the unmerged #42, `shape-the-test-suite`), 2026-10-07; every command is in the
proposal. `python -m mypy tests --explicit-package-bases` reports 185 errors
in 32 files (60 checked); counted by the trailing code of `error:` lines
only, sixteen codes, of which `no-untyped-def`, `attr-defined`, `arg-type`,
`type-arg`, `no-any-return`, `index` and `union-attr` hold all but fifteen
occurrences; the bracketed `str` and `bytes` a looser tally finds are the
`PathLike[str]` of `note:` lines. Without explicit bases mypy stops at
"Source file found twice under different module names" for
`tests/graft_support.py`, exit 2. `python -m mypy openspec_graph tools
--explicit-package-bases` reports 19 errors in 12 files where today's command
reports none; with `tools` on the module search path it reports none again,
and the tests' count falls to 184 because `tests/test_wheel_metadata.py`'s
`check_wheel_metadata` import resolves. Under `--platform win32` the tests'
count is 188, the four extra all `attr-defined` on `os.mkfifo` in
`tests/test_detect_thresholds.py`. With the seven codes disabled for
`tests.*` the residue is 23 errors in 15 files: the fifteen occurrences plus
eight inline `# type: ignore[arg-type]` or `[attr-defined]` comments the
override makes redundant. A command-line `--enable-error-code` does not lift
a per-module `disable_error_code`. `python -m ruff check --select
D100,D101,D102,D103` reports 52 findings in 18 files of `openspec_graph/`,
25 in 12 files of `tools/` and 584 in `tests/`, 575 of them test functions;
the four counts are identical under every `pydocstyle` convention, while the
broader family fits the Google convention best. A stale `per-file-ignores`
entry draws no ruff warning.

---

## Requirements

- R-TDR-1: `[tool.mypy] files` MUST list `openspec_graph`, `tools` and
  `tests`, and `[tool.mypy]` MUST set `explicit_package_bases = true` and a
  `mypy_path` holding `tools`; `strict = true`, `warn_unreachable = true` and
  `python_version = "3.10"` MUST be unchanged. The `typecheck` recipe MUST be
  `python -m mypy` with no path argument, so `files` is the one list of
  checked trees and a tree is added by a configuration line. The type gate,
  `make typecheck`, MUST exit 0 on the tree after this change and MUST still
  check `openspec_graph/` and `tools/` under strict with no per-module
  relaxation of either. A guard test MUST read the recipe and the table
  structurally and assert each of these properties.
- R-TDR-2: Exactly one `[[tool.mypy.overrides]]` entry MUST match `tests.*`,
  and its only option MUST be `disable_error_code`. No other per-module
  option — `ignore_errors`, `disallow_untyped_defs`, `check_untyped_defs`,
  `follow_imports`, `ignore_missing_imports` or any other — MAY apply to
  `tests.*`, so every code the entry does not list is enforced in `tests/`
  under the global strict configuration from the commit that lands it. The
  entry's list MUST be a subset of `no-untyped-def`, `attr-defined`,
  `arg-type`, `type-arg`, `no-any-return`, `index` and `union-attr`, holding
  exactly those of the seven that still occur when the entry lands, and no
  other code MAY ever be added to it. The only other override MAY be one for
  `module = "tomli"` setting `ignore_missing_imports = true` (R-TDR-6).
- R-TDR-3: Every code outside R-TDR-2's seven that occurs in `tests/` at
  Milestone 0's re-measurement — at drafting `assignment`, `call-overload`,
  `import-not-found`, `list-item`, `misc`, `operator`, `unreachable`,
  `unused-ignore` and `var-annotated` — MUST be fixed in `tests/` before the
  override lands, and never listed. A fix MUST NOT be a new `# type: ignore`,
  a `cast` to `Any`, a `# noqa` or a removed assertion: it is an annotation,
  a narrowing, a typed local or a corrected call. The
  `check_wheel_metadata` import of `tests/test_wheel_metadata.py` is resolved
  by R-TDR-1's `mypy_path`, not by an ignore.
- R-TDR-4: `tests/test_static_ratchets.py` MUST hold a module-level
  `MYPY_TESTS_CEILINGS` mapping each code the override lists to its
  occurrence count in `tests/`, as R-TDR-5's reader measures it at the commit
  that lands the override, under a comment stating that an entry is lowered
  or removed and never raised or added. A guard test MUST assert that the
  override's list and the mapping's keys are the same set, naming a listed
  code without a ceiling and a ceiling without a listed code.
- R-TDR-5: A guard test MUST measure every code's occurrences by running mypy
  over `tests/` with the `tests.*` override removed and every other option
  of `[tool.mypy]` and of its other overrides kept, through a configuration
  file it derives under its own temporary directory, with `--platform
  linux`, a cache directory under that temporary directory and
  `env_without_coverage()`, from the repository root. It MUST count only
  `error:` lines whose path is under `tests/`, by the code in their trailing
  brackets, with path separators normalised, and MUST NOT count `note:`
  lines. It MUST name a listed code with no occurrence — a stale entry, which
  the commit that fixed its last occurrence MUST remove from the override and
  from the ceilings in that commit — a code that occurs but is not listed,
  and a listed code whose count exceeds its ceiling.
- R-TDR-6: `tests/support.py`'s `pyproject.toml` reader MUST choose
  `tomllib` or `tomli` by `sys.version_info`, not by catching
  `ModuleNotFoundError`, and MUST return the parsed table through an
  annotated local. An override for `module = "tomli"` MUST set
  `ignore_missing_imports = true`, and that import MUST carry no inline
  ignore. mypy's verdict over `tests/` MUST then be the same on the leg that
  installs `tomli` and on the legs that do not.
- R-TDR-7: An inline `# type: ignore[<code>]` in `tests/` that the override
  makes redundant MUST keep its code and gain `unused-ignore` in the same
  brackets; none MAY be deleted or have its code changed, because each
  records a review decision of the package that wrote it and is needed again
  when its code is re-enabled. An ignore that is unused even without the
  override is a defect rather than a decision, and is fixed under R-TDR-3. A
  guard test MUST read every `# type: ignore[...]` comment in the modules
  under `tests/` and name each one whose brackets hold `unused-ignore` and no
  code the override lists, so the commit that re-enables a code also strips
  `unused-ignore` from the comments that named it and strict mode's report of
  a stale ignore returns for them.
- R-TDR-8: `[tool.ruff.lint] select` MUST include `D100`, `D101`, `D102` and
  `D103` and no other `D` rule. In `[tool.ruff.lint.per-file-ignores]` a `D`
  code MAY appear only under a key that is one concrete file path under
  `openspec_graph/` or `tools/`, listing exactly the codes among the four
  that the file violates when the entry is written — a ratchet entry — or
  under the existing `tests/*` key, which MUST carry all four as a policy
  exemption. No glob key other than `tests/*` MAY carry a `D` code. Where a
  file already has an entry, its `D` codes join that entry. Every non-`D`
  code of every existing entry MUST be unchanged, so R-ZCG-1's two `T201`
  exemptions stand. `make lint` MUST exit 0.
- R-TDR-9: `tests/test_static_ratchets.py` MUST hold a module-level
  `DOCSTRING_CEILINGS` mapping each ratchet entry's file to each of its `D`
  codes and that code's finding count in the file at the commit that lands
  the entries, under the same never-raised, never-added comment. A guard test
  MUST assert that the ratchet entries' file-and-code pairs and the
  mapping's pairs are the same set and that no key breaks R-TDR-8's shape,
  naming each offender. A guard test MUST run ruff with the repository's
  configuration, `--select D100,D101,D102,D103`, the `per-file-ignores` table
  replaced by an empty one and JSON output, over `openspec_graph` and
  `tools`, reading each finding's path relative to the repository root in
  POSIX form, and MUST name a ratchet pair with no finding — its file no
  longer offends, so the entry is stale — a pair that offends but is not
  listed, and a pair whose count exceeds its ceiling.
- R-TDR-10: The `pydocstyle` convention MUST NOT be configured while no rule
  it governs is selected. The convention the existing docstrings follow MUST
  be recorded, with the measurement behind it, in the `pyproject.toml`
  comment that explains the `D` selection, so the change that broadens the
  family sets it together with the rules it governs. The comment that today
  declines `ANN/D` for tests MUST say instead that `D100`–`D103` are selected
  by per-file ratchet for the package and `tools/`, that `tests/` is exempt
  because a test's name is its documentation, and that `ANN` stays
  unselected because mypy's `no-untyped-def` is the annotation check.
- R-TDR-11: Every guard this spec adds MUST read the file it judges and MUST
  be written and run red before the change it covers — the recipe-and-files
  guard red on the unchanged Makefile; the override guard red with no
  override; the mypy occurrence guard red naming every occurring code as
  unlisted; the waiver guard, green on a tree whose comments carry no
  `unused-ignore` yet, red on the tree's own redundant ignores checked
  against a list from which their codes are removed; the docstring shape
  guard red with `D` unselected and its occurrence guard red naming every
  offending pair as unlisted — each red run recorded in `tasks.md` and never
  committed as a tree state. Each MUST be shown red on planted inputs: a
  listed code with no occurrence; a code that occurs but is not listed; a
  listed code above its ceiling; a code listed without a ceiling, and a
  ceiling without a listed code; a `tests.*` override carrying a second
  option; mypy output whose `note:` line ends in bracketed text, which MUST
  NOT be counted, and an `error:` line with Windows separators, which MUST
  be; a derived configuration that drops an option or keeps the `tests.*`
  override; an ignore comment holding `unused-ignore` beside only enforced
  codes; a ratchet pair with no finding; a pair that offends but is not
  listed; a pair above its ceiling; a pair without a ceiling; a `D` code
  under a glob key other than `tests/*`; and a `D` code on a file under
  `tests/` by its own path. Each MUST be shown quiet on the matching
  well-formed input.
- R-TDR-12: Every new test MUST carry exactly one tier marker that agrees
  with `tests/shape_support.py`'s criterion (R-TSS-5, R-TSS-6): the guards
  that run mypy and ruff are `e2e`; the guards that read `pyproject.toml`,
  the Makefile or the modules under `tests/` are `integration`; the
  planted-input test, whose helpers take their input as arguments, is
  `unit`. The new module MUST mark per function, MUST stay within
  `MAX_TEST_MODULE_LINES`, and MUST contribute no occurrence of a listed
  code.
- R-TDR-13: Every live document that describes the type-check's scope or the
  lint selection MUST describe the new state. `docs/hooks.md`'s pre-commit
  list names `tests/` under `make typecheck`. `tests/AGENTS.md` says in one
  sentence that `make typecheck` covers `tests/` and that a new occurrence of
  an exempted code fails `tests/test_static_ratchets.py`, staying within
  `MAX_NESTED_LINES` with its precedence clause and resolving links.
  `.claude/agents/planlint-verifier.md`'s `ruff`/`mypy` bullet names the
  standing configuration — strict for the package and `tools/`, a per-code
  baseline for `tests/`, per-file docstring exemptions — and the remediation
  norm: fix the code or lower a ceiling, never add a code or a file and never
  raise a ceiling. Dated records — `CHANGELOG.md`'s released sections,
  `docs/next-steps.md`, the peer reviews, the plan and
  `docs/distribution-plan.md`'s measured rows — MUST NOT be edited.
- R-TDR-14: This spec supersedes the clause of `select-zero-cost-guards`'
  R-ZCG-3 that `[tool.mypy]` "MUST keep … `files = ["openspec_graph",
  "tools"]`", and MUST say so by name here and in the CHANGELOG entry. The
  rest of R-ZCG-3 — strict, `warn_unreachable`, the 3.10 floor, and the type
  gate exiting 0 — stands, as do R-ZCG-1, R-ZCG-2 and R-ZCG-4. That
  package's files MUST NOT be edited. `shape-the-test-suite`'s C-TSS-6, which
  forbids that package's own diff from widening the `tests/*`
  per-file-ignores, is named here as not reversed: R-TDR-8 adds to that key
  only rules that were never enforced in `tests/`.
- R-TDR-15: `CHANGELOG.md`'s `[Unreleased]` section MUST carry a `Changed`
  entry naming tests under mypy with the override's codes and their
  ceilings, the codes fixed instead of listed, the `D100`–`D103` selection
  with its per-file entries and the `tests/` policy exemption, the guard
  module, and the superseded R-ZCG-3 clause. `tasks.md` MUST record, dated
  with the commit and naming the command: the per-code counts at Milestone 0
  and at the commit that lands the override, the per-file docstring counts at
  the commit that lands the entries, every red run, the new guards' call
  durations, the cold wall time of the type gate before and after, and the
  first CI run's verdict on every leg.
- C-TDR-1: No change under `openspec_graph/`, no rule, no golden hash, no
  runtime or dev dependency: `pytest` and `hypothesis` ship their own types,
  so no stub package is added. The `RULES` tuple, `README.md`'s rules table,
  `tests/baseline_rules.json`, the `validate`/`graph`/`rules` hashes and
  `[project] dependencies` are untouched.
- C-TDR-2: No workflow, composite-action or `.pre-commit-config.yaml` line MAY
  change: CI's `test` matrix and its Windows job and the pre-commit
  typecheck hook already run `make typecheck`, and the hook already fires on
  a staged test module. The only Makefile change is the `typecheck` recipe
  line. `make thresholds` MUST print PASS, and the four coverage floors MUST
  be unchanged in value and hold.
- C-TDR-3: No test function MAY be renamed or deleted, no assertion removed,
  and no `tests/<subdir>/` created; every test module stays within
  `MAX_TEST_MODULE_LINES`.
- C-TDR-4: This spec's requirements and criteria MUST NOT pin a count that
  another package changes — an error count, a finding count, a file count, a
  duration. Measurements belong in the proposal and in `tasks.md`, dated with
  their commit and naming their command; the ceilings live in the guard
  module, recorded there by the commit that lands each ratchet.
- C-TDR-5: The type gate and the two occurrence guards MUST give the same
  verdict on every CI leg — Linux on each supported interpreter, and
  Windows — and the pull request's first CI run MUST show it.
- C-TDR-6: No `D` rule other than `D100`–`D103` MAY be selected, and this
  package MUST add no docstring under `openspec_graph/` or `tools/`: the
  ratchet entries shrink in the packages that already touch those files.

---

## Decisions

- **DEC-TDR-001:** `tests` joins `make typecheck` through `[tool.mypy]
  files`, and the recipe names no path. The recipe today is `python -m mypy
  openspec_graph tools`, and positional paths override `files`, so the plan's
  one-line change to `files` would have changed nothing the gate runs: the
  list would have lived in two places and the one that mattered would have
  stayed short. A bare `python -m mypy` makes `files` the one list, which is
  the shape `coverage-run`'s bare `--cov` already gives the coverage sources
  (R-MCO-2: the trees are named in configuration, never in the recipe). The
  gate keeps its name and its callers: CI's `test` matrix and its Windows job
  run `make typecheck` on every interpreter and on Windows, the pre-commit
  hook runs it with `types: [python]` and `pass_filenames: false`, so a
  staged test module already triggers it, and four specs cite the stage on
  verification lines. Measured cold, the gate goes from 0.9 s to 3.7 s.
  Rejected: `python -m mypy openspec_graph tools tests` (a second list beside
  `files`); a `typecheck-tests` target (a second gate for one tool, which
  needs a workflow step and a hook entry this package otherwise does not
  touch); a mypy run inside pytest only (the type gate would then run under
  coverage and only where the suite runs).
- **DEC-TDR-002:** `explicit_package_bases = true` with `mypy_path` holding
  `tools`. Explicit bases are needed because neither `tests/` nor `tools/`
  has an `__init__.py`: without them mypy names `tests/graft_support.py` both
  `graft_support` and `tests.graft_support` and stops. With them alone, mypy
  roots every module at the repository and renames `tools/_common.py` to
  `tools._common`, while each gate script imports `_common` the way it runs —
  `python tools/<script>.py` puts the script's directory first on
  `sys.path` — so twelve scripts fail to resolve it. `mypy_path` holding
  `tools` makes that directory a base too, which is the static form of how
  the scripts run and of `tests/test_wheel_metadata.py`'s own `sys.path`
  insert, so both resolve and `tools/` stays clean. Both options are global
  in mypy, which is why the measurement covers all three trees. Rejected: a
  `tools/__init__.py` (mypy would then name the module `tools._common` with
  or without explicit bases, so the scripts' `from _common import` would
  still not resolve, and `INP001`'s exemption records that the scripts are
  not a package); a `tests/__init__.py` (changes how pytest imports every
  test module, which is the suite's shape and not this package's business);
  a second mypy invocation with its own flags for `tests/` (two
  configurations for one checker).
- **DEC-TDR-003:** list seven codes and fix the rest. Listing a code
  disables it across every test module, so a code with one or two
  occurrences buys one site's exemption at the price of the whole suite's
  protection: `unreachable` would go unchecked in all of `tests/` to excuse
  one assertion. The cut falls where the measured distribution says fixing
  is a few lines and listing is a standing exemption: at drafting the nine
  fixed codes hold fifteen occurrences on fourteen lines, and the seven
  listed codes hold the rest, which is the shrink's own work, commit by
  commit. Two of the nine must be fixed whatever their counts, because their
  occurrence depends on the configuration or the leg rather than on the
  code: `import-not-found` on `tomllib` is produced by `python_version =
  "3.10"` on every leg, and the `unused-ignore` on the `tomli` import flips
  with whether the leg installed `tomli`; a listed code whose occurrence
  flips by leg would make R-TDR-5's stale check flip with it. The plan's
  five codes were a tally of a different tree and counted the `[str]` of
  note lines; `no-untyped-def`, `attr-defined` and `type-arg` join because
  this container now resolves `pytest` and `hypothesis`, which ship their own
  types. Rejected: listing all sixteen measured codes (green on day one and
  nearly nothing enforced); fixing all occurrences at once (the plan's own
  alternative, at a size that is several packages' work, not one
  milestone's).
- **DEC-TDR-004:** each listed code is held to a ceiling — its count at the
  landing commit — and not only to its presence in the list. D1 configures a
  new limit "at today's maxima"; for a disabled error code the maximum is the
  count, and a list of codes without counts would leave every listed code
  unenforced for every test written after it, so the debt could grow inside
  the list while the list shrank. The ceilings are a module-level constant
  beside the guard that reads them, in the form `MAX_TEST_MODULE_LINES` took
  (DEC-TSS-004): a number one test reads lives beside that test, not in
  `[tool.specgraph]`, whose keys gate a build. The guard asserts that the
  override's list and the ceilings' keys are one set, so the two places
  cannot disagree silently, and growth is an edit to a constant whose comment
  forbids it — the visible diff a reviewer refuses, which is as far as a test
  that cannot read history can go. Exposure accepted: the dev extras are
  unpinned by decision, so a mypy release that finds more occurrences of a
  listed code turns the guard red until they are fixed, exactly as a release
  that finds a new code turns the type gate red today. Rejected: codes
  without counts (above); counts in a JSON baseline beside
  `tests/baseline_rules.json` (a file that invites regeneration, which is the
  one operation a ratchet must not have).
- **DEC-TDR-005:** the occurrence guard runs mypy with the `tests.*` override
  removed through a configuration it derives, on the Linux platform, with a
  cold cache under its own temporary directory, and counts `error:` lines
  only. Derived, because a per-module `disable_error_code` beats a
  command-line `--enable-error-code` (measured), so the override cannot be
  lifted from the command line; written as mypy's INI form, which mypy reads
  with the same option names, because the standard library on the 3.10 leg
  writes no TOML; every global option and every other override carried, so
  the measurement differs from the gate by the one entry and nothing else.
  Linux, because under `--platform win32` mypy reports four more
  `attr-defined` on `os.mkfifo`, which the module skips at runtime on
  Windows; a ceiling must mean one number on every leg, and the type gate on
  the Windows leg still checks the Windows view under the same override. A
  cold cache under the test's temporary directory, so the test writes
  nothing into the tree and reads nothing stale; measured cold, the run
  takes 3.6 s. `error:` lines only, because a tally of bracketed text found a
  `str` code in note lines, which is where the plan's `str` came from.
  Rejected: reusing the repository's `.mypy_cache` (a test that writes into
  the tree, and a cache keyed on options the gate does not use); the leg's
  own platform (ceilings that differ by leg).
- **DEC-TDR-006:** the eight inline ignores the override makes redundant keep
  their codes and gain `unused-ignore`, and a guard keeps that escape
  temporary. Each was written by a package's author for a reason the line
  shows — `negation_matches(None, None)` passes `None` on purpose, the
  `**fields` splats build records the dataclasses type more narrowly, the
  `witness.os` patches reach a module attribute mypy does not re-export — and
  each is needed again the day its code is re-enabled. Deleting them would
  erase those decisions from packages this one does not own and add their
  sites to the ceilings. `unused-ignore` in the brackets silences strict
  mode's report while the override makes the ignore redundant and stays
  silent after, which would also hide a genuinely stale ignore for good; the
  waiver guard prevents that by naming any comment whose `unused-ignore`
  sits beside no listed code, so re-enabling a code and stripping its
  waivers happen in one commit. Rejected: deleting the ignores (above);
  disabling `unused-ignore` for `tests.*` (it would never be re-enabled,
  because no stale ignore would ever be reported to fix); a per-module
  `warn_unused_ignores = false` (the same, spelled as an option R-TDR-2
  forbids).
- **DEC-TDR-007:** the TOML reader picks its module by `sys.version_info`,
  and `tomli` is a `module = "tomli"` override with `ignore_missing_imports`.
  mypy understands version checks and, at `python_version = "3.10"`, analyses
  the `tomli` branch on every leg; `tomli` is installed only on the 3.10 leg,
  so the import resolves there and is missing elsewhere. The override makes
  both cases silent without an inline ignore whose use flips by leg, and the
  annotated local makes the return typed in both, so `no-any-return` does
  not flip either. Measured: the version-check form with an annotated local
  is clean under the 3.10 and the 3.11 view with `tomli` absent, while the
  current `try`/`except` form reports an unused ignore and a
  `no-any-return`. Rejected: `# type: ignore[import-not-found,
  unused-ignore]` on the import (works, but is a permanent escape on a line
  the waiver guard would then have to special-case); adding `tomli` to the
  dev extra for every interpreter (a dependency change for a type checker's
  benefit).
- **DEC-TDR-008:** docstrings are ratcheted for `openspec_graph/` and
  `tools/`, and `tests/` is exempt by policy. The plan counted the package
  only; `tools/` joins because its own floors comment in `pyproject.toml`
  says holding the gate machinery to a lower bar than the code it guards is
  the argument this project exists to refuse. `tests/` is exempt because 575
  of its 584 findings at drafting are test functions whose names are
  sentences and whose docstring would repeat them, which is what the
  existing comment means by "large, low-yield"; its support modules follow
  the key that covers them. The exemption is the existing `tests/*` key and
  not a ratchet, because nothing is meant to shrink it. That key gains four
  codes, and `shape-the-test-suite`'s C-TSS-6 forbids widening it; C-TSS-6
  constrains that package's own diff, and the property it protects — no rule
  once enforced in `tests/` is silenced — holds, because `D` was never
  enforced there. Rejected: selecting `D` only through a second `ruff`
  invocation in the `lint` recipe (configuration on the command line, which
  editors and a bare `ruff check` would not see); exempting `tools/*` by
  glob (a lower bar for the gate scripts than for the package).
- **DEC-TDR-009:** one ratchet entry per offending file with exactly its
  codes, a ceiling per file and code, and no docstring written here. A glob
  would exempt files that do not offend and every future file beside them;
  a per-file entry exempts what offends today and nothing else, and the
  ceiling stops a listed file from gaining an undocumented function, which
  ruff's all-or-nothing exemption cannot. ruff reports nothing when an entry
  exempts nothing (measured), so R-TDR-9's stale check is what forces an
  entry out once its file is documented. The plan routes the shrinking to
  the W2 and W3 pull requests that already touch those files; writing
  docstrings here would edit `openspec_graph/`, which C-TDR-1 keeps out of
  this package, and a function moved by W2 into a new file is documented in
  that move or is a new entry the guard names. Rejected: one entry per
  directory (the glob above); fixing the files with a single finding first
  (an edit under `openspec_graph/` for a list that W2 rewrites anyway).
- **DEC-TDR-010:** the convention is measured and recorded, not configured.
  Under every `pydocstyle` convention, and under none, ruff reports the same
  `D100`–`D103` findings (measured), so a `convention` key would change no
  verdict while reading as a gate — the class of configuration this
  repository's own `pyproject.toml` comment refuses ("an ignore list for
  rules that were never on is config that looks like a gate and is not").
  The measurement belongs in the comment: over the package and `tools/`,
  with the presence rules set aside, the Google convention leaves the fewest
  findings, because the docstrings describe rather than command and Google
  does not require an imperative summary; the findings that remain under
  every convention — a summary line not followed by a blank line, a closing
  quote on the last paragraph's line, a backslash in a non-raw docstring —
  are formatting debt, not convention. Rejected: `convention = "google"` now
  (inert configuration); claiming the docstrings are consistent, as the plan
  does (they are consistent with Google on the two rules that tell the
  conventions apart, and not on three others).
- **DEC-TDR-011:** one superseded clause, named, and one sibling constraint,
  named and not reversed. `select-zero-cost-guards` shipped in 0.3.0, so in
  DEC-MCO-006's form its R-ZCG-3 clause on `files` is superseded by name
  here and in the CHANGELOG, and the package is not edited; its AC-ZCG-3
  does not mention `files` and stays true, and R-ZCG-4 — a bare generic in
  the package or `tools/` fails the gate — holds unchanged, still shown by
  `test_a_bare_generic_in_tools_fails_typecheck` under the new
  configuration. `shape-the-test-suite` is unmerged on the branch below this
  one; C-TSS-6 is named for the reason in DEC-TDR-008, and that package's
  files are not edited from here. Rejected: amending R-ZCG-3 in place (it is
  shipped); leaving it unnamed (a reader of R-ZCG-3 would find `files`
  changed and take it for a requirement this package broke).
- **DEC-TDR-012:** the guards live in a new module,
  `tests/test_static_ratchets.py`. `tests/test_ci_workflow.py` holds the
  mypy and ruff configuration claims of `select-zero-cost-guards` and has
  room under the bound, but its subject is the CI configuration as the
  workflows state it; a module named for the ratchets is a subject the W3
  and W4 limits configured "at today's maxima" can join, and a module named
  for a subject refuses what does not belong (DEC-TSS-001).
  `tests/test_suite_shape.py`, the other candidate, is the suite's shape and
  sits near the bound. Rejected: either existing module (above); an
  uncollected `ratchet_support.py` (the helpers are small and have one
  collected user, and R-TSS-2's rule moves a helper with its only user).
- **DEC-TDR-013:** one pull request, two commits after the guards: W6.5,
  then W6.6. Each ratchet's ceilings are recorded at the commit that lands
  it, and the two ratchets touch different tables of one file, so a reviewer
  reads one kind of change per commit and the per-code record and the
  per-file record each have a commit to be dated with. Rejected: two pull
  requests (the plan's loop is one package, one pull request); one commit
  (the two records would share a date and a diff, and a red CI leg could not
  be attributed to one ratchet).

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
  file — explicit bases and the new search path silence neither. (R-TDR-1,
  R-TDR-14, DEC-TDR-002, DEC-TDR-011)
  _Verified by:_ `pytest -k "test_a_bare_generic_in_tools_fails_typecheck or test_mypy_fails_on_a_type_error"` · stage: `make typecheck`

- [ ] **AC-TDR-3:** read structurally from the Makefile and `pyproject.toml`:
  the `typecheck` recipe is `python -m mypy` with no path argument, `files`
  holds the three trees, `explicit_package_bases` is true and `mypy_path`
  holds `tools`; the guard ran red on the unchanged Makefile, as `tasks.md`
  records. (R-TDR-1, R-TDR-11, DEC-TDR-001)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-4:** exactly one override matches `tests.*`, its only option
  is `disable_error_code`, its codes are a subset of R-TDR-2's seven, and they
  are exactly the keys of `MYPY_TESTS_CEILINGS`. (R-TDR-2, R-TDR-4,
  DEC-TDR-003, DEC-TDR-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-5:** with the override lifted on the Linux platform, every
  listed code still occurs in `tests/`, every code that occurs is listed, and
  none exceeds its ceiling; the guard's call duration is in `tasks.md`.
  (R-TDR-5, DEC-TDR-005)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-6:** none of the codes R-TDR-3 fixes occurs in `tests/` with
  the override lifted, and the type gate passes with them unlisted; the diff
  of every fixed site adds no ignore, no cast to `Any` and no `noqa`, and
  removes no assertion, read at review. (R-TDR-3, C-TDR-3, DEC-TDR-003)
  _Verified by:_ `pytest -k test_typecheck_passes_on_clean_repo` · stage: `make typecheck`

- [ ] **AC-TDR-7:** `tests/support.py`'s reader selects its TOML module by
  version and returns an annotated local, the `tomli` override is the only
  other override, and the pyproject guards that read through it pass on the
  leg that installs `tomli` and on those that do not. (R-TDR-6, C-TDR-5,
  DEC-TDR-007)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_mypy_is_strict_and_warns_on_unreachable_code"` · stage: `make typecheck`

- [ ] **AC-TDR-8:** each inline ignore the override made redundant keeps its
  code beside `unused-ignore`, none is deleted, and every comment carrying
  `unused-ignore` names a code the override lists. (R-TDR-7, DEC-TDR-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-9 (non-success):** on planted inputs the mypy-side helpers
  name a stale code, a code occurring but unlisted, a code above its
  ceiling, a code without a ceiling, a ceiling without a code, a second
  option on the `tests.*` override, a derived configuration that drops an
  option or keeps the override, and an `unused-ignore` beside only enforced
  codes; they count an `error:` line with Windows separators and do not
  count a `note:` line ending in bracketed text; and they stay quiet on the
  well-formed shape. (R-TDR-5, R-TDR-7, R-TDR-11)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-10:** `D100`–`D103` are selected and no other `D` rule; every
  `D` code in `per-file-ignores` sits on one concrete file under
  `openspec_graph/` or `tools/` or on `tests/*`; the `T201` exemptions are
  exactly R-ZCG-1's two; `make lint` exits 0 and offers no escape. (R-TDR-8,
  R-TDR-14, DEC-TDR-008)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_lint_is_a_hard_gate"` · stage: `make lint`

- [ ] **AC-TDR-11 (non-success):** under a copy of the new ruff
  configuration, a `print` in a library module is still a finding and the
  same `print` at the two exempt paths is not — the new selection and
  entries disturb no existing exemption. (R-TDR-8)
  _Verified by:_ `pytest -k test_a_print_in_a_library_module_fails_lint` · stage: `make lint`

- [ ] **AC-TDR-12:** the ratchet entries' pairs equal `DOCSTRING_CEILINGS`'
  pairs, and with the exemptions lifted every listed pair still has a
  finding, every offending pair is listed, and none exceeds its ceiling.
  (R-TDR-9, DEC-TDR-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-13 (non-success):** on planted inputs the docstring helpers
  name a pair with no finding, a pair offending but unlisted, a pair above
  its ceiling, a pair without a ceiling, a `D` code under a glob key other
  than `tests/*` and a `D` code on a file under `tests/` by its own path,
  and stay quiet on the well-formed shape. (R-TDR-9, R-TDR-11)
  _Verified by:_ stage: `make test`

- [ ] **AC-TDR-14:** `pyproject.toml` sets no `pydocstyle` convention, its
  comment records the measured convention with its command, and the `ANN/D`
  comment says what R-TDR-10 requires; no `D` rule beyond the four is
  selected and no docstring is added under `openspec_graph/` or `tools/`.
  Read directly. (R-TDR-10, C-TDR-6, DEC-TDR-010)
  _Verified by:_ stage: `make lint`

- [ ] **AC-TDR-15:** every collected test carries exactly one tier marker
  that agrees with the criterion, the new module marks per function and is
  within the line bound, and `tests/` stays flat. (R-TDR-12, C-TDR-3,
  DEC-TDR-012)
  _Verified by:_ `pytest -k "test_every_test_carries_exactly_one_tier_marker or test_every_tier_marker_matches_its_mechanical_criterion or test_no_test_module_exceeds_the_line_bound or test_the_tests_directory_stays_flat"` · stage: `make test`

- [ ] **AC-TDR-16:** the rule inventory, the golden hashes, the public imports
  and the empty runtime-dependency list are unchanged, and no tool version is
  pinned. (C-TDR-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_public_import_compatibility or test_runtime_dependencies_stay_empty or test_threshold_guard_fails_on_a_pinned_tool_version"` · stage: `make test`

- [ ] **AC-TDR-17:** `make thresholds` prints PASS; no workflow, action or
  pre-commit line is in the diff, and the Windows job still runs the type
  gate; the only Makefile hunk is the `typecheck` recipe line. (C-TDR-2)
  _Verified by:_ `pytest -k "test_ci_workflow_has_a_windows_job or test_threshold_guard_passes_on_a_clean_tree"` · stage: `make thresholds`

- [ ] **AC-TDR-18:** `docs/hooks.md`, `tests/AGENTS.md` and
  `.claude/agents/planlint-verifier.md` say what R-TDR-13 requires,
  `tests/AGENTS.md` within its budget with its precedence clause and links
  intact; no dated record is in the diff. (R-TDR-13)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve"` · stage: `make docs-check`

- [ ] **AC-TDR-19:** `CHANGELOG.md` `[Unreleased]` carries the entry R-TDR-15
  names, the superseded R-ZCG-3 clause among it, and every versioned section
  still links to its release tag; `tasks.md` records every figure R-TDR-15
  names with its commit and command; no requirement or criterion pins a count
  another package changes; every test this spec cites resolves; the package
  validates clean. (R-TDR-14, R-TDR-15, C-TDR-4, DEC-TDR-011, DEC-TDR-013)
  _Verified by:_ `pytest -k "test_every_changelog_version_links_to_its_release_tag or test_every_spec_test_citation_resolves_to_a_real_test"` · stage: `make validate`

- [ ] **AC-TDR-20 (observed on the first CI run):** the type gate and both
  occurrence guards are green on every Linux leg and on Windows, recorded in
  `tasks.md` with the run id. (C-TDR-5, DEC-TDR-005, DEC-TDR-007)
  _Verified by:_ stage: `make typecheck`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Typecheck | `make typecheck` | AC-TDR-1, 2, 6, 7, 20 — the three trees checked from `files` under strict, the nine codes fixed, the TOML reader leg-independent, every leg green |
| Focused | `make test` | AC-TDR-3, 4, 5, 8, 9, 12, 13, 15, 16 — the recipe, override, ceiling, occurrence, waiver and docstring guards green on the tree and red on their planted inputs; tiers and bound held; the invariants unchanged |
| Lint | `make lint` | AC-TDR-10, 11, 14 — `D100`–`D103` selected with per-file entries and the `tests/` policy key; every existing exemption undisturbed |
| Threshold guard | `make thresholds` | AC-TDR-17 — PASS; no workflow, action or hook line changed |
| Docs | `make docs-check` | AC-TDR-18 — the scope stated where contributors and agents read it, the agent file within budget |
| Self-check | `make validate` | AC-TDR-19 — this package, then the whole tree, validate clean; every cited test resolves |
| Full | `make pre-pr` | the whole ladder green at each of the package's commits |
