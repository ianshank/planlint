# Spec: Coding Standards

> **Change:** `raise-coding-standards`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Several properties of this tree are true and unenforced.

- In the linted trees (the package, `tools/` and `tests/`), no module calls a
  debugger, swallows every exception, formats a log message eagerly or
  leaves a `TODO` comment where `docs/next-steps.md` belongs.
- The suite emits no warning and relies on no expected failure.
- No severity other than `ERROR`, `WARN` and `INFO` is ever built.

Each holds by habit. A reviewer re-checks it by hand on every pull request,
and the next change could break it with every gate green. The ruff selection
already carries the posture that answers this. A family is turned on when it
is at or near zero, so that it locks in a property the code has rather than
opening a backlog. The families still at zero, and a few just above it, have
not been asked.

Four further gaps sit beside them.

- pytest reads its configuration laxly. A misspelt ini key is a warning, an
  expected failure that starts passing is a reported curiosity, and a new
  warning is a line in a summary nobody reads.
- The shared CLI helper in `tests/support.py` starts the CLI with no bound,
  so a hung child holds its CI leg until the job's own timeout kills it.
  That failure names no test.
- `Finding.severity` and `Rule.severity` are typed as any string, so the
  type gate accepts a severity the CLI cannot order.
- The package ships no PEP 561 marker. A consumer's type checker reads none
  of the annotations strict mypy already holds, although the versioning
  policy counts a public import as a user-facing surface.

The review also asked for a Python 3.15 leg. Its availability on the runners
is established from here, and so is a Linux 3.15 run of the suite under this
change's configuration. A Windows 3.15 run, a run on a hosted runner, and the
way the aggregator reads a failed experimental leg are not. The leg would
also land on the lines `prepare-release-0-4-0` rewrites. So this spec decides
it and does not do it.

**Evidence:** measured at `bfbc124`, the base of
`claude/raise-coding-standards`, on 2026-10-16 and, for its revisions, on
2026-10-17, together with the adversarial reviews' runs on copies of that
commit, read from their logs and trees. Every figure, with the command that
produced it, is in `tasks.md`'s "Measured at `bfbc124`" section, and the
proposal's Evidence points at each site. No count is written here (C-RCS-3).

---

## Requirements

### Order

- R-RCS-1: This package MUST land alone in the integration branch, in a pull
  request held until `v0.3.0` is pushed to origin and `v0.3.0^{commit}` is an
  ancestor of the integration branch. The implementation MUST follow in its
  own pull request, opened as a draft, and each of its commits MUST be green
  under the full ladder. It MUST ship in one of two releases, and the
  maintainer MUST record which in `tasks.md`, with the reason (DEC-RCS-017):
  - **0.4.0.** The implementation merges before `prepare-release-0-4-0`'s
    release-prep pull request opens.
  - **The next minor.** If it has not merged by then, it is held until
    `v0.4.0` is pushed to origin and `v0.4.0^{commit}` is an ancestor of the
    integration branch, and ships in the minor release after 0.4.0.

  Each hold's two facts MUST be recorded in `tasks.md` with their output and
  the date, by `git ls-remote --tags origin 'v0.X.0'` and `git merge-base
  --is-ancestor 'v0.X.0^{commit}'` against the integration branch, the form
  `prepare-release-0-4-0`'s R-RFR-1 uses. In neither case MAY the
  implementation merge between that package's release-prep commit and its
  promotion. The merge facts MUST be recorded in `tasks.md`.

### Lint

- R-RCS-2: `[tool.ruff.lint] select` MUST include the families A, ASYNC,
  BLE, FIX, FLY, G, INT, LOG, PGH, PLE, SLOT, T10 and YTT. These are the
  zero-cost set, each at zero findings under `--isolated --ignore-noqa`
  when measured. It MUST also include FURB, PYI and the single rule PT011.
  - For every module under `openspec_graph`, `tools` and `tests`, nothing
    MAY hide a finding of any of them from the lint gate: no
    `per-file-ignores` or `extend-per-file-ignores` entry, no `noqa`
    comment, no `ignore` or `exclude` key, no rule setting, no target
    version below the `requires-python` floor, no ignore file, no nested
    configuration file, and no directory ruff excludes by default.
  - R-RCS-5's count guard enforces this ban. Whatever hides a finding from
    the lint gate leaves it in the count, or leaves the module out of
    ruff's file list, and either fails the count guard. A `noqa` that names
    one of their codes and hides nothing is reported by the lint gate
    itself, as an unused directive.
  - Every existing selection and exemption MUST be unchanged, so the `T201`
    exemptions and the docstring ratchet entries stand.
  - The lint gate MUST exit 0 on the tree after this change.
- R-RCS-3: Every finding the new selection reports MUST be fixed, and each
  fix MUST be behaviour-neutral.
  - The FURB and PYI findings take the fix ruff marks safe: an `or` for a
    conditional that repeats its own test, `re.DOTALL` for its alias,
    `str.removeprefix` for a hand-rolled prefix strip, `writelines` over the
    generator a loop wrote line by line, and `float` for `int | float`.
  - Each PT011 finding takes a `match=` naming the message the code under
    test raises today.
  - No assertion MAY be removed, no product output MAY change, and the
    existing tests that exercise each fixed site MUST pass unchanged.
- R-RCS-4: FA, TD, PTH, ERA, TRY003, EM, COM812, D401, D205, PLR, PLC, PLW and
  TC MUST NOT be selected by this change. Each MUST be recorded in
  `pyproject.toml`'s comment block of deliberately unselected rules, with its
  finding count, the command that produced it, the commit it was taken at,
  and its reason.
  - The block's existing lines MUST be re-measured and rewritten so every
    figure in them is true.
  - The PL line MUST say that PLE is now selected.
  - The PTH line MUST name the trigger that re-opens it (DEC-RCS-003).
  - The header sentence above `select` MUST stay true: every family selected
    here was at or near zero when it was turned on.
- R-RCS-5: The selection MUST be held by guards that read what ruff reports,
  as well as what the configuration says (DEC-RCS-016).
  - **Selected.** A structural guard MUST assert that every family and rule
    R-RCS-2 names is in `[tool.ruff.lint] select`. It MUST assert nothing
    else about `select` or any other key, so a later selection needs no edit
    to it.
  - **Counted.** A count guard MUST run ruff by this repository's counting
    method: the flags `tests/ratchet_support.py`'s `ruff_docstring_command`
    passes, under which ruff uses no cache and honours no configuration
    file, no ignore file and no `noqa` directive, with JSON output.
    - It MUST select exactly the families and rule R-RCS-2 names, over
      `openspec_graph`, `tools` and `tests`.
    - It MUST take its target version only from the lower bound of
      `[project] requires-python`, read with `packaging`'s specifier
      parser. A compound specifier gives its highest lower bound, and a
      compatible-release specifier its own version. When the floor cannot
      be read, the guard MUST fail naming what is missing, and never run at
      ruff's default.
    - It MUST fail with a named problem when `[tool.ruff]` sets a
      `target-version` other than that floor.
    - It MUST assert a zero exit, an empty stderr and no finding, naming each
      finding it sees by file, line and code.
    - **The file list.** It MUST also assert that ruff's `--show-files` list
      of Python modules under the three trees equals the tracked `*.py` and
      `*.pyi` under them, with the untracked ones git does not ignore. It
      MUST name each tracked module ruff skips and each module ruff reads
      that git does not list, and MUST fail closed when git cannot list the
      files.
    - Its command builder and its target-version reader MUST live beside
      `ruff_docstring_command`.
  - **Escapes.** A planted guard MUST show that each of these hides a planted
    finding from a ruff run under the planted tree's own configuration, and
    does not hide it from the count guard:
    - a comment that quotes a `noqa` directive inside prose;
    - a `per-file-ignores` entry naming a family or a code prefix: `PT`,
      `PT01`, `FURB1`, `PL` and `ALL`;
    - `[tool.ruff.lint]` `ignore`, `extend-ignore` and `exclude`;
    - `[tool.ruff]` `exclude` and `extend-exclude`;
    - a rule setting that disarms a rule: an empty `flake8-pytest-style`
      `raises-require-match-for`, and a `flake8-builtins` `ignorelist` naming
      the shadowed builtin;
    - `[tool.ruff] target-version` below the floor, and a
      `per-file-target-version` entry below it, each over a planted module
      whose findings depend on the version;
    - a ruff configuration file nested under the planted `tests/`;
    - an `.ignore` file naming the planted module;
    - a module under a directory ruff excludes by default, such as
      `openspec_graph/dist/`, which both runs skip and the file-list check
      names.

    Each case MUST also show, as its control, that the same run without the
    escape reports the finding.
  - **Fires.** A planted-violation guard MUST run ruff, under a copy of this
    repository's configuration, against a planted tree holding one violation
    of every family and rule R-RCS-2 names. Each is planted under a package
    path, a `tools/` path and a `tests/` path, PT011's under the `tests/`
    path only. The guard MUST assert that each is reported at each path where
    it is planted.

### pytest

- R-RCS-6: `[tool.pytest.ini_options]` MUST read as follows.
  - `addopts` MUST carry `--strict-markers`, `--strict-config` and `-ra`.
  - `xfail_strict` MUST be `true`.
  - `filterwarnings` MUST be a list whose first entry is exactly `error`.
  - `testpaths` and the three tier `markers` MUST be unchanged, so the
    existing registration guard stays green unedited.
- R-RCS-7: Any `filterwarnings` entry after `error` MUST be an `ignore` that
  names one warning category and one module, both non-empty, with a comment
  above it naming the warning, its source and why it cannot be fixed at its
  cause. A blanket `ignore`, or one that leaves the category or the module
  empty, MUST NOT be written. This change adds no such entry unless the
  implementation's measurement under R-RCS-9 finds a warning that cannot be
  fixed at its cause, and any entry added is recorded in `tasks.md` with
  that run.
- R-RCS-8: A guard test MUST read the pytest table structurally and assert
  R-RCS-6 and R-RCS-7. A helper it calls MUST also be shown red on a planted
  blanket `ignore`, and quiet on a narrowed one. Nested-run guards MUST each
  plant a module under a copy of this repository's `pyproject.toml`, run
  pytest on it in a child process, and assert pytest's exact exit code and a
  string that names the cause:
  - **A warning.** A planted test emits a warning whose message is
    distinctive. The exit MUST be pytest's tests-failed code, and the output
    MUST carry that message.
  - **An unexpected pass.** A planted expected failure passes. The exit MUST
    be the tests-failed code, and the output MUST carry `XPASS(strict)` with
    the planted reason.
  - **An unknown key.** The copied table gains an unknown key. The exit MUST
    be pytest's usage-error code, the output MUST carry `ERROR: Unknown config
    option` with the key, and no `INTERNALERROR` MAY appear. A second run of
    the same tree with `addopts` cleared, as the durations command clears
    it, MUST still stop with a non-zero exit naming the key.
- R-RCS-9: Before the configuration lands, the implementation MUST run the
  whole suite under it on its own head in each of these shapes, and record
  every failure with its warning and its fix:
  - each tier alone;
  - the coverage-measured run the test stage makes;
  - the nested pytest runs that read this repository's configuration.

  The CI run on the implementation's pull request MUST then show every leg
  green under it, Windows included.

### The CLI subprocess

- R-RCS-10: `tests/support.py` MUST define a module-level
  `RUN_CLI_TIMEOUT_SECONDS`, under a comment saying four things: what it
  bounds; that it is a test-harness constant and not configuration, as
  `detect.GIT_TIMEOUT_SECONDS` is; how its value was chosen; and its limit,
  below.
  - `run_cli` MUST pass it to `subprocess.run` as `timeout`. It MUST NOT
    take a per-call override.
  - When the child exceeds it, the `subprocess.TimeoutExpired` MUST
    propagate out of `run_cli`, never caught and never turned into a
    completed process, so the test that called it fails naming the command.
  - The value MUST be chosen above the slowest measured CLI child, measured
    under coverage as the test stage runs it, with a wide margin, and below
    the shorter of the `test` and `test-windows` jobs' timeouts.
  - **Its limit.** The bound names a hung child by the test that called it
    only while the hung calls fit inside the job's own timeout. Each hung
    call waits the full bound, so a hang that repeats across many calls
    still ends in the job's cancellation. `tasks.md` MUST record the
    measurement, the margin, both job timeouts and how many full-bound waits
    each job's budget holds.
  - The constant MUST NOT be a `[tool.specgraph]` key, and its name MUST NOT
    contain a word the threshold guard, as merged at the implementation's
    head, reads as a threshold.
- R-RCS-11: A guard test MUST intercept `subprocess.run` inside
  `tests/support.py`, as the existing `COVERAGE_PROCESS_START` contract
  tests do, and assert that `run_cli` passes the named constant as
  `timeout`. A second MUST assert that a `TimeoutExpired` raised by the
  intercepted call reaches the caller unchanged.

### The typed surface

- R-RCS-12: `openspec_graph/rule_types.py` MUST define `Severity` as a
  `Literal` of exactly `ERROR`, `WARN` and `INFO`, and list it in the
  module's `__all__`.
  - `ERROR`, `WARN` and `INFO` MUST each be declared `Final` with their own
    names as values.
  - `Finding.severity` and `Rule.severity` MUST be annotated `Severity`.
  - No run-time check MAY be added, and `report.py`'s `FindingRecord` MUST
    keep its `str` field and its zero intra-package imports.
  - A guard test MUST assert that `Severity`'s members are exactly the
    constants' values, and exactly each severity table the package keeps:
    the keys of `openspec_graph.cli`'s `SEVERITY_ORDER`, the members of
    `openspec_graph.report`'s `SEVERITIES`, the keys of its `_COMMANDS`, and
    the keys of `openspec_graph.sarif`'s `_LEVELS`. The guard compares them
    from the test side, so `report.py` gains no import.
- R-RCS-13: After R-RCS-12 the type gate MUST exit 0. `MYPY_TESTS_CEILINGS`,
  `MYPY_WAIVERS` and `DOCSTRING_CEILINGS` MUST be unchanged by this change,
  and their guards green. A guard test MUST run mypy, under a copy of this
  repository's configuration, on a planted module that builds a `Finding`
  with a severity outside the `Literal`, and assert an `arg-type` error
  naming that line. The module MUST sit at the root of a temporary
  directory, not under a `tests/` path, because the `tests.*` override of
  `[tool.mypy]` disables `arg-type` for modules there.
- R-RCS-14: `openspec_graph/py.typed` MUST exist and be empty, and the built
  sdist and wheel MUST each carry it beside the package's modules. The build
  system's setuptools floor already packages it by default, so no
  `[tool.setuptools]` key MAY be added for it.
  - A guard test MUST assert the file in the source tree.
  - A second MUST build the sdist and then the wheel from it, as the release
    paths build them, and find it in both archives' member lists.
  - That second guard MAY skip only when `build` cannot be imported, or when
    the build's output shows a network or requirement-resolution failure.
    It MUST fail on any other non-zero exit, naming the exit and the tail of
    the output (DEC-RCS-011).
  - The wheel MUST still pass its licence gate, as that gate stands at the
    implementation's head.
- R-RCS-15: `py.typed` and R-RCS-12 MUST land in the same release, so the
  first typed public surface any consumer reads is already the narrowed
  one. This holds in either release R-RCS-1 allows, because both land in
  the implementation's one pull request.

### Python 3.15

- R-RCS-16: This change MUST NOT add a 3.15 leg to any workflow, a 3.15
  classifier or a 3.15 bound to `docs/hooks.md`'s `test` row.
  `docs/next-steps.md` MUST gain one item recording four things:
  - the deferral;
  - what was established: the runners' download manifest and images, the
    dev extra's 3.15 wheels, and a Linux 3.15 run of the suite under this
    change's configuration, with its failures named as environmental;
  - what was not: a Windows 3.15 run, a run on a hosted runner, and how
    `ci-ok` reads a failed experimental leg;
  - the trigger DEC-RCS-012 names.

### Documents and records

- R-RCS-17: `.claude/agents/planlint-verifier.md`'s `ruff`/`mypy` bullet MUST
  name three things: the families this change selects, the pytest posture
  of R-RCS-6, and the `run_cli` bound. It MUST also state their remediation
  norm:
  - a finding of a selected family is fixed, never exempted by a per-file
    entry, a setting or a `noqa`;
  - a FIX finding on a comment that quotes a tag word in prose is fixed by
    rewording the prose, never by a `noqa`;
  - a warning is fixed at its cause, or narrowed by one `ignore` under
    R-RCS-7;
  - a `TimeoutExpired` from `run_cli` is a hung child to investigate, never
    a reason to raise the bound.
- R-RCS-18: `CHANGELOG.md`'s `[Unreleased]` section MUST gain a `### Changed`
  group and an `### Added` group, beside any group a sibling wrote, each
  entry led by this package's bold backticked name.
  - `Changed` holds the lint families with the declined list's location,
    the pytest options, and the `run_cli` bound.
  - `Added` holds the `Severity` type and `py.typed`, stating that a typed
    consumer now reads the package's annotations.
- R-RCS-19: `tasks.md` MUST record each of these, dated with its commit and
  naming its command:
  - Milestone 0's re-measurement at the implementation head;
  - every red run;
  - every fix with the test that holds its site;
  - the R-RCS-9 runs;
  - the measurement behind the `run_cli` bound, with its limit;
  - the built sdist's and wheel's `py.typed` entries;
  - the CI run on the implementation's pull request, with its run id, the
    head SHA it ran for, the merge SHA it tested and every leg's verdict;
  - each hold's facts of R-RCS-1, and the maintainer's record of the release
    it took, and why.

### Constraints

- C-RCS-1: No behaviour of `openspec_graph/` MAY change. The `RULES` tuple,
  `README.md`'s rules table, `tests/baseline_rules.json`, the `validate`,
  `graph` and `rules` golden hashes, every output shape and `[project]
  dependencies` MUST be unchanged. No runtime or dev dependency MAY be added
  or floored by this change.
- C-RCS-2: No workflow file, composite action, `Makefile` recipe or
  `.pre-commit-config.yaml` line MAY change, and the threshold guard MUST
  stay green.
- C-RCS-3: This spec MUST NOT pin a count that another package changes: no
  finding count, test count, call count, duration or line number.
  Measurements belong in `tasks.md`, dated with their commit and naming
  their command, and in the dated `pyproject.toml` comments R-RCS-4
  requires.
- C-RCS-4: No file of another change package MAY be edited. A shipped
  record this spec builds on is named, not amended, and is read at the
  archive tag once `lean-production-tree` removes it from the tree.
- C-RCS-5: Every new test MUST carry exactly one tier marker that agrees with
  `tests/shape_support.py`'s criterion, and every test module MUST stay
  within `MAX_TEST_MODULE_LINES`.

---

## Decisions

- **DEC-RCS-001: what is selected, and why each family earns its place.**
  The zero-cost set is the families that report nothing under `--isolated
  --ignore-noqa`, which no configuration file, ignore file or `noqa` can
  shade, and that guard a property a regression would actually break:
  - T10, a debugger call left in;
  - BLE, a bare `except Exception` that swallows;
  - G and LOG, a log call that formats eagerly or misuses the API, in a
    package that logs on every verb;
  - PGH, a blanket `type: ignore` or `noqa`, the shape the ratchets already
    refuse under `tests/`;
  - A, a shadowed builtin;
  - SLOT, a missing `__slots__` on a `str` or `tuple` subclass;
  - YTT, a `sys.version` comparison by string;
  - INT, a translated string formatted before translation;
  - ASYNC, a blocking call in a coroutine;
  - PLE, pylint's error class;
  - FLY, a `join` that is a literal;
  - FIX, a `TODO`, `FIXME`, `XXX` or `HACK` comment. The ruff comment and
    the E501 line already send owed work to `docs/next-steps.md`, and FIX
    makes that the only place it can go.

  Families the code does not exercise, such as INT and ASYNC, cost nothing
  and guard the first use. FURB and PYI are adopted because every finding
  each reports has a safe, behaviour-neutral fix (R-RCS-3), and PT011
  because each of its findings is a test assertion made stricter by a
  `match=`.

  The risk accepted, stated plainly. CI installs ruff unpinned through the
  dev extra, and a release that promotes a preview rule into a selected
  family turns lint red until the code is fixed. `tasks.md` measures the
  exposure: the new selection adds FURB preview findings, and today's
  selection already carries latent preview findings of its own, in S, RUF
  and UP. That is the posture this repository already takes for every
  family it selects, and `ratchet-test-types-and-docstrings` DEC-TDR-004
  states it for mypy: the release is met by a fix in the pull request that
  meets it, never by an exemption.

  Rejected:
  - selecting the whole `PT` family, which has a backlog of its own,
    chiefly composite assertions and parametrize-name types;
  - selecting FURB and PYI with per-file exemptions for their findings
    instead of fixing them, which would be a ratchet, not a zero-cost
    guard.
- **DEC-RCS-002: FA and TD are declined although they report nothing,
  departing from the brief's "adopted together".**
  - FA flags an annotation only when the target is Python 3.9 or older,
    by ruff's own rule text and a probe that fires at a 3.9 target and
    passes at 3.10.
  - This project's floor is 3.10, and 3.11 once `prepare-release-0-4-0`
    lands, so FA can never fire here. Selecting it would be a selection
    that reads as a gate and is not. That is the shape `pyproject.toml`'s
    own comment refuses for an ignore list, and DEC-TDR-010 refused for an
    inert `pydocstyle` convention.
  - TD checks the format of a `TODO`-style comment, and every line it can
    flag carries a FIX finding too: a probe of planted comments drew FIX on
    every line TD flagged.
  - With FIX selected, no such comment survives, so TD could only repeat
    FIX's verdict on the same line.

  Rejected: selecting them for symmetry with the zero-hit list, which would
  add selections that can never change a verdict.
- **DEC-RCS-003: PTH is deferred, because its fix is shown non-neutral on
  3.10.**
  - Its findings at `tools/check_promotion.py`'s `open()` and at a test's
    `glob.glob` have plainly neutral fixes. Its findings in
    `openspec_graph/witness.py`'s `write_witness` sit where the atomic-write
    tests intercept `witness.os.replace` and `witness.os.unlink`.
  - A probe that patches `os.replace` and `os.unlink`, then calls
    `Path.replace` and `Path.unlink`, sees neither call on 3.10. That
    interpreter's `pathlib` reaches them through an accessor class that
    bound `os.replace` and `os.unlink` when it was imported, before any
    patch. On 3.11 and every later interpreter measured, through 3.15, the
    probe sees both calls.
  - So on the 3.10 leg, live until `prepare-release-0-4-0` removes it, the
    PTH fix would take `write_witness`'s calls out of its tests' reach.
    R-RCS-3 admits only behaviour-neutral fixes.
  - The trigger is `prepare-release-0-4-0`'s removals merged into the
    integration branch. At that floor PTH is re-measured and selected in
    its own change, or declined again with its reason.

  Rejected:
  - a per-file exemption for `witness.py`, which would make a zero-cost
    selection carry an exemption;
  - holding this whole change for the floor.
- **DEC-RCS-004: ERA stays declined, its reason re-checked.** The comment says
  ERA flags prose that quotes markdown, and that this is most of its hits.
  Each of today's findings is prose: a parenthesised list of quoted phrases
  in a tier comment, and quoted markdown headings in a test comment. In a
  tool whose subject is markdown, quoting a heading in a comment is
  ordinary, and the rule's heuristic cannot tell it from code. The line is
  rewritten with the measured figure, and the reason stands.
- **DEC-RCS-005: the families with a backlog are recorded, not selected.**
  - TRY003 and EM would move every exception message into a variable or a
    subclass: churn without a defect found.
  - COM812 is trailing-comma style that ruff's own documentation recommends
    against beside its formatter.
  - D401 and D205 are formatting debt that DEC-TDR-010 leaves to the change
    that selects a convention.
  - PLR is refactor heuristics, PLC is mostly import placement, and TC
    moves imports for type-checking only.
  - PLW is near zero, but its findings were not read site by site here. It
    is named as a candidate for the next zero-cost pass, not adopted
    unread.
  - Each line carries its count, command and commit, so the next reader
    re-runs it rather than trusts it (`docs/policies.md`, "Count cites a
    command").

  Rejected:
  - recording the declined list only in this package, which leaves the
    configuration's reader without it;
  - a guard asserting each declined family stays unselected, which would
    turn a recorded judgement into a test a later package must edit to
    reverse.
- **DEC-RCS-006: PT011 is selected as one rule.** It is the rule of its
  family at near zero. Its findings sit in tests only, and each fix makes
  an assertion stricter without touching the code under test, which keeps
  it within R-RCS-3. Selecting a single rule is the form `T201` took
  (DEC-ZCG-001). Rejected: the family, as DEC-RCS-001 says.
- **DEC-RCS-007: pytest's options are spelled one by one, not through
  pytest 9's `strict`.**
  - `strict` would also turn on `strict_parametrization_ids`, under which
    collection stops today in `tests/test_adopter_urls.py` and
    `tests/test_detect_thresholds.py`, so it is not zero-cost.
  - It needs a pytest floor the dev extra does not carry.
  - It would move `--strict-markers` out of `addopts`, where
    `shape-the-test-suite`'s registration guard reads it.
  - `--strict-config` and `-ra` go in `addopts`. `xfail_strict` and
    `filterwarnings` are ini keys, so they also hold under the durations
    command, which clears `addopts` (R-TSS-5's reason for registering the
    markers as keys).
  - `xfail_strict` is the expected-failure counterpart of a stale waiver.
    An `xfail` that passes is a fix nobody recorded, and it fails the run
    so the mark is removed. No test carries `xfail` today, so it costs
    nothing.
  - `-ra` puts every skip, expected failure and error in a short summary.
    That matters on the Windows leg, where the platform guards skip on
    capability, because a skip that hides a gate is the silence this
    repository exists to refuse. It gates nothing.
  - **What `--strict-config` adds, measured.** The first draft said it turns
    a misspelt key from a warning into a stop. With `filterwarnings =
    ["error"]` in place, the key is already a stop without it: pytest's
    configuration warning becomes an error while the run configures itself,
    and the run ends as an internal error with a traceback. `--strict-config`
    turns the same key into a usage error, with one line naming the key and
    no traceback. Its gain is that clean stop, not the stop itself. Under the
    durations command, which clears `addopts` and so drops the flag, only the
    ini filter still stops the run. The unknown-key guard checks both
    (R-RCS-8).

  Rejected: `strict = true` (above), and `-rA` (it would print every pass).
- **DEC-RCS-008: warnings are errors, measured first, with one rule for any
  exception.**
  - Each tier passed under `-W error` here. The nested runs that read this
    repository's configuration passed with `PYTHONWARNINGS=error`
    inherited by the child. That is stricter than an ini filter, because it
    reaches every child interpreter.
  - The adversarial review ran the coverage-measured run of the test stage,
    on copies of the base carrying this change's pytest configuration, on
    Linux under 3.10, 3.11, 3.12, 3.13, 3.14 and 3.15. No failure on any of
    them was caused by a warning. Every failure it recorded is
    environmental, named in `tasks.md` with the evidence for each.
  - Windows was not measured. So R-RCS-9 makes the implementation's own
    runs, and its CI run, the measurement.
  - An exception is one `ignore` per warning, narrowed to its category and
    its module with its reason beside it (R-RCS-7), so a filter can never
    widen into silence.
  - A blanket `ignore::DeprecationWarning` would restore exactly the blind
    spot this closes.

  Rejected:
  - `-W error` in `addopts` only, which the durations command clears. A
    nested run that copies `pyproject.toml` does read `addopts`; the
    durations command is the one run that drops it, and an ini key holds
    there too;
  - `PYTHONWARNINGS` set in the workflows, which would also reach the CLI's
    own subprocesses and change what they print.
- **DEC-RCS-009: the `run_cli` bound is a harness constant, not
  configuration.**
  - The thresholds policy keeps a number that gates a build in
    `pyproject.toml` (G003), and its guard scans the Makefile and the
    workflows.
  - A subprocess bound is not a quality threshold. `detect.GIT_TIMEOUT_SECONDS`
    is the in-tree precedent: "Named rather than inlined … Not a quality
    threshold, so not configuration." `MAX_TEST_MODULE_LINES` sets the
    other: a number one test helper reads lives beside it (DEC-TSS-004).
  - A `[tool.specgraph]` key would make a harness detail look like a policy
    a build enforces. It would also give the threshold guard a number to
    judge.
  - The name avoids every word of the threshold guard `close-gate-script-gaps`
    drafts. Its named-threshold rule reads text targets, and its constants
    rule reads `tools/*.py` at module level. Neither holds `tests/support.py`,
    and no segment of the name is a word of its list or that word's plural.
  - The value is chosen from the slowest measured CLI child, under coverage
    as the test stage runs it, with a margin for a loaded Windows runner,
    and below both jobs' timeouts.
  - **Its limit, stated.** The bound turns one hung child into a failure
    naming its test. It cannot do that for a hang that repeats across many
    calls. Each waits the full bound, the waits add up past the job's
    budget, and the job is cancelled as it is today. A shorter bound would
    fit more hangs into the budget, but would sit closer to a loaded
    runner's real call times. The value kept trades that for no false
    timeout, and `tasks.md` records how many full-bound waits each job holds.
  - The `TimeoutExpired` propagates, because a helper that returned a fake
    completed process would let the calling test assert on output that
    never came.
  - No per-call override is added, because no caller needs one, and an
    unused knob is the next caller's way to unbound a hang.

  Rejected:
  - a `[tool.specgraph]` key (above);
  - a timeout at every `subprocess.run` call site under `tests/` at once,
    which mixes the shared helper with mypy, ruff, pytest, `build`, git and
    bash runs whose costs differ by orders of magnitude, each needing its
    own measurement;
  - `pytest-timeout`, a new dev dependency (C-RCS-1).
- **DEC-RCS-010: `Severity` is a `Literal`, the constants are `Final`, and
  every severity table is bound to both.**
  - A `Literal` makes the type gate refuse an unlisted severity at the call
    that builds it. `Final` makes mypy read each constant as its literal
    value, so every existing construction still type-checks, which the
    shadow-file run measured with no new error and no ceiling moved.
  - The package keeps its severity tables in the CLI's `SEVERITY_ORDER`,
    `report.py`'s `SEVERITIES` and `_COMMANDS`, and `sarif.py`'s `_LEVELS`.
    Each stays the plain value it is. The guard of R-RCS-12 holds every one
    of them equal to the `Literal`'s members, so a new severity cannot be
    typed without being ordered, counted, annotated and given a SARIF level.
  - The guard compares them from the test side. `report.py` reads an
    untrusted envelope with no intra-package import, and keeps none.
  - `report.py`'s `FindingRecord` stays a separate `str` field. Narrowing it
    would refuse envelopes `report` accepts today: a behaviour change for
    the envelope's schema policy, not a typing one.
  - Nothing is validated at run time, so a `Finding` built with a bad string
    by an untyped caller behaves as it does today.

  Rejected:
  - an `enum.Enum`, which would change every serialized severity and the
    golden hashes;
  - a `NewType` over `str`, which refuses nothing;
  - run-time validation in `__post_init__` (C-RCS-1);
  - importing `Severity` into `report.py` or `sarif.py` to type their tables,
    which would give `report.py` its first intra-package import.
- **DEC-RCS-011: `py.typed` ships with the `Literal`, and `TypedDict` does
  not.**
  - A PEP 561 marker makes the package's annotations a surface consumers
    type-check against. Once it ships, narrowing a field from `str` to a
    `Literal` would break a consumer's type check: a typing-level break of
    a public import, which the versioning policy counts as user-facing.
  - Landing both in one release (R-RCS-15) means no consumer ever type-checks
    against the wide field. A minor release, 0.4.0 or the one after it, is
    where this belongs.
  - setuptools has packaged `py.typed` by default since its v69.0.0, by its
    own changelog. The build floor is later than that, so no packaging key
    is added.
  - The guard builds the sdist and then the wheel from it, the way the
    release paths build, so the marker is shown in the archives a consumer
    installs from. The review's copy with the marker built both ways and
    found it in each archive, as `tasks.md` records.
  - **Its skip is narrower than its precedent's.**
    `test_the_real_wheel_passes_the_gate` in `tests/test_wheel_metadata.py`
    skips on any non-zero exit of the build, because its subject is the
    licence metadata, and a missing tool is not a licensing defect. This
    guard's subject is what the build puts in the archives. A build that
    fails for any reason but a missing `build` or an unreachable index is
    the packaging defect it exists to catch, and a skip there would be the
    silence this repository refuses. So it skips on those two causes only,
    read from the import and the build's own output, and fails on the rest.
  - A `TypedDict` for `Finding.as_dict`'s return would be a new exported
    name whose keys the envelope's schema version already pins. A
    `TypedDict` is not a `dict[str, object]` to mypy, so every caller that
    treats the result as one would change, and so would the per-code
    ceilings under `tests/`.

  Rejected: `py.typed` without the `Literal` (the break above, one release
  later); a `TypedDict` now (above); the precedent's skip on any failed
  build (above).
- **DEC-RCS-012: the 3.15 leg is deferred, with a named trigger.**

  **What is established.**
  - The manifest `setup-python` downloads from lists 3.15.0 as stable, with
    Linux 24.04 and Windows x64 builds.
  - The `ubuntu-latest` and `windows-latest` images pre-cache Python only
    through 3.14, so the leg would download 3.15.
  - The dev extra's compiled dependencies publish 3.15 wheels, and the rest
    are pure Python.
  - **A Linux 3.15 run.** The adversarial review ran the test stage's
    coverage-measured run on a CPython 3.15.0 build, on a copy of the base
    carrying this change's pytest configuration. Every coverage floor
    passed, and no failure was caused by a warning. Every failure was
    environmental:
    - the action-contract tests, whose shell starts an interpreter without
      the library path that build needs, fail identically on an unmodified
      copy;
    - the smoke-wheel test fails on every interpreter in the review's
      copies, and passed in this drafting's own run of its tier.

  **What is not established.**
  - A Windows 3.15 run. The `test-windows` job runs only the default
    interpreter, so no CI run would supply one either.
  - A run on a hosted runner, with what the pinned `setup-python` release
    resolves there.
  - How `needs.test.result` reads when a matrix leg fails under
    `continue-on-error`. GitHub documents the step-level behaviour, not
    this.

  **A correction to the brief.** The guards that forbid `continue-on-error`
  cover `promotion`, `release-tier`, `ci-ok` and the release ancestry step
  (R-BPM-11). The `test` job explicitly permits an experimental leg behind
  `continue-on-error: ${{ matrix.experimental || false }}` (R-HCW-10,
  DEC-HCW-005), and 3.14 entered that way. What is unknown is whether that
  route is still advisory now that `ci-ok` fails on any result other than
  `success`, because no run here has combined the two.

  **Why not now.**
  - The leg would sit on the matrix line, the classifier block and the
    `docs/hooks.md` row that `prepare-release-0-4-0` rewrites.
  - Windows 3.15 and a hosted runner are unmeasured, and a hard leg is
    proven only by a green run there, which this package cannot observe
    before its implementation.
  - The experimental route's advisory claim is unverified under the
    aggregator.

  The first draft also gave this change's warning policy as a reason. The
  Linux 3.15 run above found no warning-caused failure, so that reason is
  withdrawn.

  **The trigger.** A package of its own opens once both
  `prepare-release-0-4-0`'s removals and this change's implementation have
  merged into the integration branch.
  - It adds 3.15 as a hard leg, with its classifier, in one commit, and the
    `docs/hooks.md` row's upper bound follows.
  - It merges only after the leg is green on that package's own pull
    request.
  - It does not use the experimental route unless a run has first shown how
    `ci-ok` reads a failed experimental leg.

  `docs/next-steps.md` records this (R-RCS-16).

  Rejected:
  - a hard leg in this change (above);
  - an experimental leg in this change, whose advisory claim is unverified
    under the aggregator;
  - a deferral with no trigger, which is a decision nobody can find.
- **DEC-RCS-013: the merge hazards, named by file and symbol so they are
  resolved on purpose.**

  **This change's own sites.**
  - `pyproject.toml`: `[tool.ruff.lint]` (`select` and its comment block)
    and `[tool.pytest.ini_options]` only.
  - `tests/support.py`: `run_cli` and the new constant above it.
  - `tools/_common.py`: `_SOURCE_ARRAY` and `normalize_scope`.
  - `tools/check_promotion.py`: `write_github_output`.
  - `openspec_graph/`: `rules.py`'s FURB110 site, `delta.py`'s
    `_mentions_value`, `rule_types.py`, and the new `py.typed`.
  - The test modules of DEC-RCS-014, `.claude/agents/planlint-verifier.md`,
    `docs/next-steps.md` (one new item) and `CHANGELOG.md` (`[Unreleased]`).
    No workflow at all.

  For every site below, whichever change lands second re-reads it at its
  own head, and Milestone 0 records what landed first.
  - **`prepare-release-0-4-0`.**
    - `pyproject.toml`: `requires-python`, the classifiers,
      `[project.scripts]`, the dev extra and `[tool.mypy]`. The count guard
      reads its target version from `requires-python` alone, so it follows
      the new floor without an edit. Whichever lands second re-reads the
      count at the merged floor.
    - Its ruff `UP` findings at the new floor are its own. This change's
      families report the same counts at a 3.11 target, measured, and PTH's
      trigger is its removals.
    - `tests/support.py`: `read_pyproject` and `working_directory`'s
      docstring. Whichever lands second re-reads both beside `run_cli`.
    - `ci.yml`'s matrix line, which this change does not touch.
    - `tests/test_ci_workflow.py`: it edits
      `test_mypy_is_strict_and_warns_on_unreachable_code`, and this change
      adds guards beside other functions. Whichever lands second re-reads
      the module and its line count.
    - `tests/test_cli_surface.py`: it deletes the alias tests and the
      `repo_root` fixture, and this change adds its `run_cli` guards beside
      the `COVERAGE_PROCESS_START` contract. Whichever lands second re-reads
      that the new guards request no deleted fixture.
    - `docs/next-steps.md`: it edits the items titled "`scoped_fail_under`
      reads the common TOML forms, not all of them" and "Docker as primary
      delivery", and this change adds a new item. Whichever lands second
      re-reads the list.
    - `CHANGELOG.md`: both add groups to `[Unreleased]`, and the release
      prep moves every line of it under `[0.4.0]` (DEC-RCS-017).
  - **`tighten-release-surface`**, as narrowed.
    - It has no sdist reader and pins no file list of either archive, so
      `py.typed` joins no pin. The earlier hazard is moot.
    - It rewrites the `Makefile`'s wheel-check recipe to build the sdist,
      then the wheel from it, run the metadata check, and smoke that wheel.
      Milestone 4 runs that recipe as it stands at the head, and its
      `py.typed` guard builds the same way. Whichever lands second re-reads
      the recipe.
    - It hardens `tools/check_wheel_metadata.py` to read only the licence
      field in `METADATA`'s header. The licence gate R-RCS-14 names is that
      check once it lands. Whichever lands second re-reads it against the
      wheel that carries `py.typed`.
    - Its new tests go in `tests/test_wheel_metadata.py`,
      `tests/test_ci_makefile.py`, `tests/test_stage_citations.py` and
      `tests/test_skill_contract.py`, none of which this change edits. The
      new families judge them the moment both are in the tree.
  - **`harden-release-pipeline`.**
    - It adds tests to `tests/test_release_surface.py`'s release-workflow
      section, and this change adds its `py.typed` guards to the same
      module. Both are additions, kept both, and whichever lands second
      re-reads the module's line count.
    - It builds on `tools/check_promotion.py`'s `tag_ancestry`, on
      `tools/_common.py`'s `run_scripts`, `shell_invocations` and
      `read_text`, and on `tests/support.py`'s `workflow_job_blocks`, and
      its record cites them by line. This change edits
      `write_github_output`, `_SOURCE_ARRAY`, `normalize_scope` and
      `run_cli`, each above one of those, so the cited lines move.
      Whichever lands second re-reads the citations.
    - Its new `tools/release_notes.py` and `tests/test_release_notes.py`
      are judged by the new families.
  - **`add-witness-ci-artifacts`**, a draft whose implementation has not
    landed.
    - `openspec_graph/rules.py`: it rewords the module docstring, and this
      change applies FURB110 in the same module.
    - `openspec_graph/witness.py`: it changes `load_witnesses` and the
      `matching_witnesses` docstring, beside the `write_witness` sites PTH's
      deferral names. The new families judge its code.
    - `tests/test_decomposition.py`: it holds `_EXPECTED_HASHES` unmoved,
      and this change adds its severity guard to the module.
    - `docs/next-steps.md`: it edits the item titled "Named Action inputs
      for `--change` and `--dialect`" and the deferral table's
      `--require-witness` row.
    - `CHANGELOG.md`: both add to `[Unreleased]`.

    Whichever lands second re-reads each.
  - **`close-gate-script-gaps`**, as revised.
    - `pyproject.toml`: it adds a bare `coverage` entry to the dev extra.
      AC-RCS-15 cites `test_the_dev_extra_floors_mypy_and_pins_nothing`, and
      a bare entry pins nothing, so that test stays green. Whichever lands
      second re-reads the extra and the test, and confirms this change adds
      no entry of its own (C-RCS-1).
    - `tools/_common.py`: it adds `dev_extra_names` beside
      `coverage_sources`, near the `_SOURCE_ARRAY` and `normalize_scope`
      fixes. Whichever lands second re-applies its edit to the merged text.
    - It edits `tools/_common.py`, `tools/check_branch_coverage.py`,
      `tools/check_coverage_floor.py`, `tools/check_no_hardcoded_thresholds.py`,
      `tools/check_secrets.py`, `tools/dead_code.py` and
      `tools/matcher_accuracy.py`, and their tests. Its own hazard list
      names BLE, G, LOG, FURB and PT011 as families that will judge that
      code. The rest of this change's selection judges it too, and
      Milestone 0's re-measurement at the head covers every family.
    - `tests/test_static_ratchets.py`: it may lower a docstring ceiling
      there, and this change adds the count guard and its escapes to the
      same module. Both are kept, and whichever lands second re-reads the
      ceilings.
    - `tests/support.py`: it rewords `run_tool_main`'s docstring.
    - Its widened threshold guard is re-run over the merged tree with
      `RUN_CLI_TIMEOUT_SECONDS` in place (R-RCS-10).
  - **`lean-production-tree`.** It adds a helper to `tests/support.py`, and
    deletes the shipped packages this spec cites, which are then read at
    the archive tag (C-RCS-4).

  Rejected: sequencing this change behind every sibling, which would hold
  zero-cost guards for a release.
- **DEC-RCS-014: where the guards live.** Each guard sits beside the guard it
  extends, because a module named for a subject takes what belongs to it
  (DEC-TSS-001).
  - The lint presence guard, the planted-violation guard and the planted
    mypy guard go in `tests/test_ci_workflow.py`, beside `T201`'s and the
    bare-generic guard: DEC-ZCG-010's section for claims about the CI
    configuration.
  - The count guard and its planted escapes go in
    `tests/test_static_ratchets.py`, beside
    `test_every_docstring_exemption_matches_its_ceiling`, which counts by the
    same method. The command builder, the target-version reader and the
    file-list comparison go in `tests/ratchet_support.py`, beside
    `ruff_docstring_command`.
  - The pytest guards go in `tests/test_suite_shape.py`, beside the marker
    registration and its nested strict-markers run. Of the modules this
    change adds to, it is the nearest its line bound, and the guards
    planned for it could carry it past. So the structural guard and its
    helper go there. The nested runs go there too unless, measured after
    they are written, they would carry the module past
    `MAX_TEST_MODULE_LINES`. Then they move, names unchanged, to a module
    named for the pytest configuration, as Milestone 2 plans and
    DEC-TDR-012's split did.
  - The `run_cli` guards go in `tests/test_cli_surface.py`, beside its
    `COVERAGE_PROCESS_START` contract.
  - The severity binding goes in `tests/test_decomposition.py`, beside
    `test_public_import_compatibility`.
  - The `py.typed` guards go in `tests/test_release_surface.py`, the module
    for what the wheel and the sdist carry.

  The other modules keep room under the bound after their additions, by the
  sizes `tasks.md` records. C-RCS-5 holds each to the bound whatever a
  sibling adds first.

  The implementation is one draft pull request, in the milestones of
  `tasks.md`, each commit green under the full ladder. A guard is written
  and seen red in the working tree before the change it covers, and never
  committed red.

  Rejected: one new module named for this change, which would hold several
  unrelated subjects under a name that describes a change rather than a
  subject.
- **DEC-RCS-015: the shipped packages this builds on, followed and not
  edited.**
  - `select-zero-cost-guards`' posture is followed exactly: only
    zero-after-edit selections (C-ZCG-2, DEC-ZCG-012), each shown to fire
    on a planted violation (DEC-ZCG-011).
  - `ratchet-test-types-and-docstrings`' ceilings and waivers are
    unchanged, its counting method (DEC-TDR-009) is reused rather than
    copied, and its threat model's residual gaps are not widened.
  - `shape-the-test-suite`'s R-TSS-5 registration guard stays green
    unedited, because `--strict-markers` stays in `addopts`, and its tier
    criterion classes every new test.
  - `harden-ci-workflows`' experimental-leg rule is left as it is and not
    used (DEC-RCS-012).
  - Once `lean-production-tree` lands, each of these is read at
    `archive/dev-record-2026-10`, as `prepare-release-0-4-0` reads R-TDR-6,
    and none is amended here.
- **DEC-RCS-016: the lint selection is held by a count, not by reading its
  exemptions.**
  - The first draft's guard read `per-file-ignores` and
    `extend-per-file-ignores` structurally. The first adversarial review
    bypassed it:
    - a `noqa` quoted inside a prose comment still suppresses the line;
    - a per-file entry of a family or a code prefix, `PT`, `PT01`, `FURB1`,
      `PL` or `ALL`, hides codes a code-by-code read does not match;
    - `ignore`, `extend-ignore`, `exclude` and `extend-exclude` were never
      read.
  - The first revision measured more of the same kind: a rule setting that
    disarms one rule, a configuration file nested in a subdirectory, and an
    ignore file. Any list of devices a structural guard reads is a list the
    next device is not on.
  - The count asks ruff the question directly. `--isolated` reads no
    configuration file, `--no-respect-gitignore` reads no ignore file, and
    `--ignore-noqa` honours no directive. It is the method
    `ratchet-test-types-and-docstrings` already uses for the docstring
    ratchet (DEC-TDR-009), so the repository has one way to count ruff
    findings, not two.
  - **The count's own inputs.** The second review showed that the count is
    only as honest as what it is handed.
    - **The target version.** The first revision passed `[tool.ruff]
      target-version` when set. Setting it to a version below the floor hid
      version-dependent findings from the lint gate and the count alike. So
      the count now takes its version from the `requires-python` floor
      alone, and the guard names a `[tool.ruff] target-version` other than
      that floor. A target above it would make the gate recommend code the
      floor cannot run, which is wrong too.
    - **The file list.** Ruff skips directories it excludes by default,
      `dist`, `venv`, `.venv`, `node_modules`, `_build`, `site-packages`,
      `.tox`, `.eggs`, `__pypackages__` and `.git` among them, under
      `--isolated` too. So a module placed in one is hidden from both runs.
      The guard compares ruff's own file list with git's, and names the
      difference.
  - **Why these checks are not a structural ban.** Neither reads an
    exemption or forbids a key for what it might hide. Each checks an input
    of the count itself: the version it runs at, and the files it reads.
    The count stays the judge of findings, and these checks make sure it
    judges the modules the repository ships, at the version the project
    declares.
  - **What remains true, and how far.** For the modules under
    `openspec_graph`, `tools` and `tests` that git lists, the only way to
    bring the count to zero is to fix the finding, or to lower the
    project's own `requires-python`. That second way is a user-facing
    change to the supported versions, made in the open, and no test ties
    `requires-python` to the lowest hard matrix leg today
    (`test_classifiers_equal_the_hard_matrix_legs` ties the classifiers
    only). Anchoring it is out of scope here.
  - The presence guard stays, because a count over an unselected family is
    zero too. The count proves there is no finding, and the presence guard
    proves the lint gate would report the next one.
  - The planted escapes are the count guard's non-success cases. Each is
    shown, by its control, to hide a finding from the configured run, so
    the guard is proven against a device that works. One that ruff refuses
    is not an escape. `extend-exclude` under `[tool.ruff.lint]` is not a
    ruff key: ruff refuses it as an unknown field and exits 2, which turns
    the lint gate red by itself. The working spelling is `[tool.ruff]`'s.
  - An unused `noqa` naming a selected code is reported by the lint gate
    already, as RUF100. So the count and the gate together refuse every
    `noqa` R-RCS-2 bans in the three trees.

  Rejected:
  - extending the structural read to every key and setting (above);
  - a structural ban on `ignore` and `exclude`, which would also refuse a
    deliberate scope a later package records, and would still miss
    settings, nested files and prose directives;
  - letting the count read `[tool.ruff] target-version`, the hole above.
- **DEC-RCS-017: the order is conditional, with a recorded deferral.**
  - `close-gate-script-gaps`' DEC-GSG-001 takes this shape: its
    implementation merges before the release prep is cut, "or it misses
    0.4.0". This change follows it. If its implementation has not merged
    when `prepare-release-0-4-0`'s release-prep pull request is due, the
    release goes ahead without it, and it ships in the next minor. The
    maintainer records which in `tasks.md` (R-RCS-1).
  - **Each hold ends at a tag on origin, not at an event.** The 0.3.0 hold
    ends when `v0.3.0` is pushed to origin and `v0.3.0^{commit}` is an
    ancestor of the integration branch. The deferral's 0.4.0 hold ends the
    same way for `v0.4.0`. Each is recorded by `git ls-remote --tags origin`
    for the tag and `git merge-base --is-ancestor` for the ancestry, the
    form `prepare-release-0-4-0`'s R-RFR-1 already uses. "The promotion has
    left the integration branch" names no fact anyone can check after the
    day.
  - **Why this differs from DEC-TRS-012.** That decision holds the release
    prep for its change, or for a recorded deferral, through an amendment of
    `prepare-release-0-4-0`. `tighten-release-surface` rewrites
    `docs/aqa.md` lines that `prepare-release-0-4-0`'s own `docs/aqa.md`
    edit also changes, and a scratch merge of the two stops on a conflict.
    That order has to be held.
  - This change edits no line the release prep edits. The two share one
    file, `CHANGELOG.md`. The release prep moves every `[Unreleased]` line
    under `[0.4.0]` and leaves an empty `[Unreleased]`, and this change's
    groups go under whichever `[Unreleased]` is there when it merges. It
    adds no tag reference to the adopter corpus the release prep re-points.
  - Either release keeps R-RCS-15, because `Severity` and `py.typed` land
    in the implementation's one pull request.
  - C-RCS-4 stands. No other package is amended to hold this order, so the
    record is this package's alone.
  - Neither branch allows a merge between the release-prep commit and the
    promotion, which `prepare-release-0-4-0` forbids for every change.

  Rejected:
  - holding the release prep for this change, which would need an
    amendment of `prepare-release-0-4-0` (C-RCS-4) to protect an order no
    conflict needs;
  - an unconditional "before the release prep", which leaves no recorded
    outcome when it slips;
  - a hold that ends at "the promotion left the integration branch", which
    no command reads back.

---

## Acceptance Criteria

- [ ] **AC-RCS-1:** read structurally from `pyproject.toml`: every family and
  rule R-RCS-2 names is selected, and the `T201` exemptions and the
  docstring ratchet entries are unchanged. The count by this repository's
  counting method, at the `requires-python` floor, finds no finding of the
  new selection over the three trees. `[tool.ruff]` sets no target version
  other than that floor, and ruff's file list equals git's for those trees.
  So, for every module there that git lists, no exemption, setting, lowered
  target version, ignore file, nested configuration, default exclude or
  `noqa` comment can hide a finding from the count. The lint gate's recipe
  still has no escape of its own. The new guards are written with this
  change and added to this line when they exist. (R-RCS-2, R-RCS-5,
  DEC-RCS-001, DEC-RCS-006, DEC-RCS-016)
  _Verified by:_ `pytest -k "test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_lint_is_a_hard_gate or test_docstring_exemptions_are_file_entries_matching_their_ceilings or test_every_docstring_exemption_matches_its_ceiling"` · stage: `make pre-pr`

- [ ] **AC-RCS-2 (non-success):** under a copy of this repository's ruff
  configuration, a planted violation of every family and rule R-RCS-2
  names is reported at a package path, a `tools/` path and a `tests/` path,
  PT011's at the `tests/` path where it is planted. The existing planted
  `print` is still reported in a library module and not at the two exempt
  paths. (R-RCS-2, R-RCS-5, DEC-RCS-001)
  _Verified by:_ `pytest -k test_a_print_in_a_library_module_fails_lint` · stage: `make test`

- [ ] **AC-RCS-3:** each fixed site keeps its behaviour. The tests that
  exercise the GitHub step-output writer, the coverage-source reader, the
  property test the fixed conditional sits in, the delta's threshold
  matching, the guard's unterminated-quote case, the manifest generator's
  refusals, the witness write-failure paths and the golden hashes pass,
  each with its assertions intact. The PT011 sites now also match the
  message. (R-RCS-3, DEC-RCS-006)
  _Verified by:_ `pytest -k "test_route_writes_github_output or test_coverage_sources_reads_the_run_table_array_and_nothing_else or test_parse_makefile_never_raises_on_arbitrary_text or test_delta_threshold_matching_agrees_with_the_rule_engine or test_the_guard_stays_quiet_on_ordinary_commands or test_manifest_generator_rejects_a_folded_description or test_write_witness_removes_its_temp_file_when_the_replace_fails or test_write_witness_reraises_the_original_error_not_the_cleanup_one or test_output_byte_identical"` · stage: `make test`

- [ ] **AC-RCS-4 (non-success):** none of FA, TD, PTH, ERA, TRY003, EM,
  COM812, D401, D205, PLR, PLC, PLW or TC is selected. Each appears in the
  comment block of deliberately unselected rules with its count, command,
  commit and reason, and PTH's line names its trigger. Every figure already
  in that block is true at the commit it names, and the header sentence
  above `select` still holds. The comment is read directly; the full ladder
  confirms the tree. (R-RCS-4, DEC-RCS-002, DEC-RCS-003, DEC-RCS-004,
  DEC-RCS-005)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RCS-5:** read structurally from `pyproject.toml`:
  - `addopts` carries `--strict-markers`, `--strict-config` and `-ra`;
  - `xfail_strict` is true;
  - `filterwarnings` begins with `error`, and every later entry is an
    `ignore` naming one category and one module;
  - `testpaths` and the tier markers are unchanged.

  The new guard is written with this change and added to this line when it
  exists. (R-RCS-6, R-RCS-7, R-RCS-8, DEC-RCS-007)
  _Verified by:_ `pytest -k test_pytest_registers_exactly_the_three_tier_markers_strictly` · stage: `make test`

- [ ] **AC-RCS-6 (non-success):** under a copy of this repository's
  `pyproject.toml`, each nested pytest run stops with its exact exit code,
  naming the cause:
  - a planted test that emits a distinctive warning ends with the
    tests-failed code and that message;
  - a planted expected failure that passes ends with the tests-failed code
    and `XPASS(strict)` with its reason;
  - a planted unknown key ends with the usage-error code and `ERROR: Unknown
    config option` naming it, with no `INTERNALERROR`, and still stops,
    naming it, with `addopts` cleared.

  A planted unregistered marker still fails collection. A planted blanket
  `ignore` is named by the structural guard's helper, and a narrowed one is
  not. (R-RCS-7, R-RCS-8, DEC-RCS-007, DEC-RCS-008)
  _Verified by:_ `pytest -k test_an_unregistered_marker_fails_collection_under_strict_markers` · stage: `make test`

- [ ] **AC-RCS-7:** under the new configuration, each tier, the
  coverage-measured run and the nested runs that read the configuration
  pass on the implementation's head, as `tasks.md` records. The
  ambient-coverage nested run still reaches a real verdict, and no `ignore`
  entry was needed or each one added is recorded with its run. (R-RCS-9,
  DEC-RCS-008)
  _Verified by:_ `pytest -k "test_suite_survives_an_ambient_coverage_file or test_an_unregistered_marker_fails_collection_under_strict_markers or test_property_settings_are_derandomized_and_nothing_is_xfailed"` · stage: `make test`

- [ ] **AC-RCS-8:** `run_cli` passes `RUN_CLI_TIMEOUT_SECONDS` to
  `subprocess.run` as its timeout, takes no per-call override, and still
  injects `COVERAGE_PROCESS_START` without overriding a caller's value. The
  constant's comment states its limit. `tasks.md` records its value with
  the measurement under coverage, the margin, the job timeouts and the
  number of full-bound waits each job holds. The new guards are written
  with this change and added to this line when they exist. (R-RCS-10,
  R-RCS-11, DEC-RCS-009)
  _Verified by:_ `pytest -k "test_run_cli_injects_coverage_process_start_by_default or test_run_cli_never_overrides_a_caller_supplied_coverage_process_start"` · stage: `make test`

- [ ] **AC-RCS-9 (non-success):** a `TimeoutExpired` raised by the
  intercepted `subprocess.run` reaches `run_cli`'s caller unchanged, and is
  never caught or converted into a completed process. The threshold guard
  stays green with the constant in place. (R-RCS-10, R-RCS-11, C-RCS-2,
  DEC-RCS-009)
  _Verified by:_ `pytest -k test_threshold_guard_passes_on_a_clean_tree` · stage: `make test`

- [ ] **AC-RCS-10:** `Severity` is the `Literal` of the three severities and
  is in `rule_types`' `__all__`. Its members equal the `Final` constants'
  values, the keys of the CLI's `SEVERITY_ORDER`, the members of
  `report.SEVERITIES`, the keys of `report._COMMANDS` and the keys of
  `sarif._LEVELS`. `Finding` and `Rule` annotate their severity with it,
  and `report.py` still has no intra-package import. The type gate exits 0
  and the public imports are unchanged. The binding guard is written with
  this change and added to this line when it exists. (R-RCS-12, R-RCS-13,
  DEC-RCS-010)
  _Verified by:_ `pytest -k "test_typecheck_passes_on_clean_repo or test_public_import_compatibility or test_mypy_is_strict_and_warns_on_unreachable_code or test_severity_map_covers_every_severity or test_report_has_no_intra_package_imports"` · stage: `make test`

- [ ] **AC-RCS-11 (non-success):** under a copy of this repository's mypy
  configuration, a planted module at a temporary directory's root, outside
  any `tests/` path, that builds a `Finding` with a severity outside the
  `Literal` is reported with an `arg-type` error on that line. A bare
  generic in a `tools/` module is still reported. (R-RCS-13, DEC-RCS-010)
  _Verified by:_ `pytest -k test_a_bare_generic_in_tools_fails_typecheck` · stage: `make test`

- [ ] **AC-RCS-12:** the per-code baseline under `tests/` and the docstring
  ratchet are unchanged by the typed surface and by the fixes. Every listed
  code's count still equals its ceiling on both platforms, every inline
  ignore is still a recorded waiver, and every docstring pair still equals
  its ceiling. (R-RCS-3, R-RCS-13, DEC-RCS-010, DEC-RCS-015)
  _Verified by:_ `pytest -k "test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms or test_every_inline_ignore_is_a_recorded_waiver or test_every_docstring_exemption_matches_its_ceiling or test_the_tests_override_is_one_entry_listing_exactly_the_ceilinged_codes"` · stage: `make test`

- [ ] **AC-RCS-13:** `openspec_graph/py.typed` exists and is empty. The sdist
  built from the implementation's head, and the wheel built from that
  sdist, each list it beside the package's modules, with no
  `[tool.setuptools]` key added. The archive guard skips only for a missing
  `build` or an unreachable index, and fails on any other failed build.
  That wheel still passes its licence gate. The `Severity` type and
  `py.typed` land in the same release, read from the CHANGELOG entry. The
  `py.typed` guards are written with this change and added to this line
  when they exist. (R-RCS-14, R-RCS-15, DEC-RCS-011)
  _Verified by:_ `pytest -k test_the_real_wheel_passes_the_gate` · stage: `make pre-pr`

- [ ] **AC-RCS-14 (non-success):** no 3.15 leg, classifier or `docs/hooks.md`
  bound is added. The classifiers still equal the hard legs, the `test`
  row still names the matrix's bounds, and no experimental leg or
  job-level `continue-on-error` appears. `docs/next-steps.md` carries the
  item R-RCS-16 names, with the Linux 3.15 run among what was established,
  read directly. (R-RCS-16, DEC-RCS-012)
  _Verified by:_ `pytest -k "test_classifiers_equal_the_hard_matrix_legs or test_hooks_test_row_names_the_matrix_bounds or test_the_experimental_leg_is_an_expression_not_a_job_literal or test_the_default_python_is_a_hard_matrix_leg"` · stage: `make test`

- [ ] **AC-RCS-15 (non-success):** nothing the package does changes:
  - the rule inventory still matches `tests/baseline_rules.json`;
  - the golden hashes are unmoved;
  - the runtime-dependency list is still empty;
  - the dev extra still floors mypy and pins nothing, and this change adds
    no entry to it.

  (C-RCS-1, DEC-RCS-010, DEC-RCS-013)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty or test_the_dev_extra_floors_mypy_and_pins_nothing"` · stage: `make test`

- [ ] **AC-RCS-16:** no workflow, composite-action, `Makefile` or
  `.pre-commit-config.yaml` line is in the diff, which is read directly.
  The lint gate's recipe still has no escape, and the type gate passes on
  the repository. (C-RCS-2, DEC-RCS-013)
  _Verified by:_ `pytest -k "test_lint_is_a_hard_gate or test_typecheck_passes_on_clean_repo or test_threshold_guard_passes_on_a_clean_tree"` · stage: `make pre-pr`

- [ ] **AC-RCS-17:** every collected test, the new ones included, carries
  exactly one tier marker that agrees with the criterion, and no test
  module exceeds the line bound. (C-RCS-5, DEC-RCS-014)
  _Verified by:_ `pytest -k "test_every_test_carries_exactly_one_tier_marker or test_every_tier_marker_matches_its_mechanical_criterion or test_no_test_module_exceeds_the_line_bound"` · stage: `make test`

- [ ] **AC-RCS-18:** `.claude/agents/planlint-verifier.md`'s `ruff`/`mypy`
  bullet names the new families, the pytest posture, the `run_cli` bound
  and their remediation norm, the prose-rewording norm for FIX included,
  read directly. Every required document is still present and linked, and
  the nested agents file is still within its budget. (R-RCS-17, R-RCS-16)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_nested_agents_file_stays_short"` · stage: `make docs-check`

- [ ] **AC-RCS-19:** `CHANGELOG.md`'s `[Unreleased]` carries the two groups
  R-RCS-18 names, and every versioned section still links to its release
  tag. `tasks.md` records every figure R-RCS-19 names with its commit and
  command. No requirement or criterion of this spec pins a count, every
  test this spec cites resolves, and no other change package is in the
  diff. (R-RCS-18, R-RCS-19, C-RCS-3, C-RCS-4)
  _Verified by:_ `pytest -k "test_every_changelog_version_links_to_its_release_tag or test_every_spec_test_citation_resolves_to_a_real_test or test_the_spec_corpus_actually_contains_citations"` · stage: `make pre-pr`

- [ ] **AC-RCS-20 (observed on the implementation pull request's CI run):**
  every `test` leg and `test-windows` is green under the new lint
  selection, pytest options and typed surface, and so is `ci-ok`. This is
  recorded in `tasks.md` with the run id, the head SHA it ran for, the
  merge SHA it tested and every job's verdict. (R-RCS-9, R-RCS-19,
  DEC-RCS-008)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RCS-21:** `tasks.md` records the merge order, each hold's facts and
  the release the implementation took:
  - before this package's pull request merged, `git ls-remote --tags origin
    'v0.3.0'` printed the tag and `git merge-base --is-ancestor
    'v0.3.0^{commit}'` against the integration branch exited 0;
  - the implementation's merged after it, and either before
    `prepare-release-0-4-0`'s release-prep pull request opened, shipping in
    0.4.0, or, by the maintainer's recorded deferral, after the same two
    facts held for `v0.4.0`, shipping in the next minor with its groups
    under the `[Unreleased]` that follows `[0.4.0]`;
  - in neither case between that release-prep commit and its promotion.

  Each fact is recorded with its output and the date, each merge with its
  commit, the deferral with its reason, and each sibling's state is re-read
  at the implementation head. (R-RCS-1, R-RCS-15, R-RCS-19, DEC-RCS-013,
  DEC-RCS-017)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RCS-22 (non-success):** on planted trees, each escape R-RCS-5
  lists hides a planted finding from a ruff run under the tree's own
  configuration, which reports it without the escape, and the count guard
  still fails on it with the escape in place:
  - a prose comment quoting a `noqa` directive;
  - the per-file entries `PT`, `PT01`, `FURB1`, `PL` and `ALL`;
  - `[tool.ruff.lint]` `ignore`, `extend-ignore` and `exclude`, and
    `[tool.ruff]` `exclude` and `extend-exclude`;
  - the disarming rule settings;
  - `[tool.ruff] target-version` below the floor, which the count still
    reports at the floor and the guard names, and a
    `per-file-target-version` entry below it;
  - a nested configuration file and an `.ignore` file;
  - a module under a directory ruff excludes by default, which the
    file-list check names.

  The new guard is written with this change and added to this line when it
  exists; until then the existing count's own planted ignore file is the
  citation. (R-RCS-2, R-RCS-5, DEC-RCS-016)
  _Verified by:_ `pytest -k test_every_docstring_exemption_matches_its_ceiling` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-RCS-2, 3, 5 to 12, 14, 15, 17, 22: the lint presence, count, file-list, escape and planted-violation guards, the pytest, `run_cli`, severity and archive guards green on the tree and red on their planted inputs; the fixed sites' own tests intact; the ratchets unchanged; tiers and the line bound held; nothing the package does changed. The lint gate and the type gate run inside the full ladder below, and the `lint` and `typecheck` targets are not cited on a verification line here |
| Docs | `make docs-check` | AC-RCS-18: the verifier's bullet and the next-steps item, every required document present and linked |
| Full | `make pre-pr` | AC-RCS-1, 4, 13, 16, 19 to 21: the lint selection, its count at the floor and its comment block, the archives with `py.typed`, no workflow or recipe in the diff, the records, every leg of the implementation's CI run, each hold's facts, the merge order and the release taken |
| Self-check | `planlint --target . validate --fail-on INFO --change raise-coding-standards` | this package validates with no finding at any severity against the repository's own rules |
