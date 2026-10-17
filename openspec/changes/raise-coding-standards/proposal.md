# Change: Raise the Coding Standards — Lock In the Lint Families Already at Zero, Run pytest Strict, Bound the CLI Subprocess, Type the Severity

## Why

A review of `dev` on 2026-10-16 found the same shape `select-zero-cost-guards`
found a milestone earlier. Several properties of this tree hold today and are
enforced by nothing. In the linted trees (the package, `tools/` and `tests/`):

- No module calls a debugger.
- No `except` swallows everything.
- No logging call formats eagerly.
- No `TODO` comment stands in for `docs/next-steps.md`.

And across the suite and the package:

- The suite emits no warning.
- No test relies on an expected failure.
- No severity outside `ERROR`, `WARN` and `INFO` is ever built.

Each is a fact a reviewer re-checks by hand on every pull request, because
the gates as configured would let it drift without a red build. The posture
is the one `pyproject.toml`'s ruff comment already states: a family is
turned on when it is at or near zero, so that it locks in a property the
code already has rather than starting a cleanup backlog. This package
applies that posture to the families measured at zero, and to the three
measured near zero whose few findings each have a behaviour-neutral fix. It
also records, with its count and reason, every family it measured and
declined.

The same review named four further gaps.

- **pytest runs lax.** A misspelt ini key is a warning, an `xfail` that
  starts passing is reported and forgotten, and a new warning is a line in
  a summary nobody reads.
- **The shared CLI helper waits forever.** `tests/support.py`'s `run_cli`
  starts the CLI with no timeout, so a hung child holds a CI leg until the
  job's own `timeout-minutes` kills it, and the job's failure names no test.
- **The severity is typed as any string.** `Finding.severity` and
  `Rule.severity` are typed `str`, so mypy accepts a finding with a severity
  the CLI's `SEVERITY_ORDER` cannot order.
- **The package ships no PEP 561 marker.** A consumer's type checker
  therefore reads none of the annotations `mypy --strict` already holds, even
  though `docs/policies.md` counts a public import as a user-facing surface.

Python 3.15 is the review's fifth point, and this package decides it rather
than doing it: no 3.15 leg is added here (DEC-RCS-012).

Two revisions answer the package's first and second adversarial reviews,
and their decisions are written into the spec:
- the lint guard became a count, which takes its target version from the
  `requires-python` floor alone and checks ruff's file list against git's
  (DEC-RCS-016);
- the order became conditional, each hold ending at a tag on origin
  (DEC-RCS-017);
- DEC-RCS-003, 004, 007, 008, 009, 010, 011, 012, 013 and 014 were
  corrected against what was measured.

**Evidence:** measured at `bfbc124` (`origin/dev`, the base of
`claude/raise-coding-standards`) on 2026-10-16, with Python 3.13.16, ruff
0.17.0, mypy 2.4.0, pytest 9.1.1 and hypothesis 6.169.2 on four cores, and on
2026-10-17 for the revisions. The adversarial reviews' runs on copies of
`bfbc124` are read from their logs and trees and named as theirs. `tasks.md`'s
"Measured at `bfbc124`" section holds every figure with the command that
produced it, and this list points at where each fact lives.

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR` printed `57 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`,
  exit 0. The same command run on the worktree's own package (`PYTHONPATH`
  set to it) printed the same: the installed `planlint` imports
  `/home/user/planlint/openspec_graph`, a checkout on another branch.
- **Fifteen families report nothing.** `python -m ruff check --no-cache
  --select <family> --statistics openspec_graph tools tests` prints no finding
  and exits 0 for each of A, BLE, FA, FLY, G, LOG, PGH, SLOT, T10, YTT, INT,
  ASYNC, FIX, TD and PLE. So does the same run with `--isolated
  --ignore-noqa`, so no per-file entry or `noqa` comment hides a hit.
- **The count the guard will run.** The repository's counting method
  (`tests/ratchet_support.py`'s `ruff_docstring_command` flags: `--no-cache
  --isolated --no-respect-gitignore --ignore-noqa`), with `--target-version
  py310` read from `requires-python` and `--select` the proposed set, reports
  the same 12 findings the configured run does, with an empty stderr. Its
  `--show-files` list holds the same 119 Python modules `find` does.
- **Every selection fires, planted.** One violation of each of the sixteen
  selections, planted at `openspec_graph/`, `tools/` and `tests/` paths of the
  first review's probe tree, is reported at each path (PT011 at `tests/`,
  where it is planted).
- **The structural guard could be escaped.** Over the same probe tree,
  each of these hid a planted finding from the configured run and not from
  the count:
  - a prose comment quoting `# noqa: BLE001`;
  - per-file entries `PT`, `PT01`, `FURB1`, `PL` and `ALL`;
  - `[tool.ruff.lint]` `ignore`, `extend-ignore` and `exclude`, and
    `[tool.ruff]` `exclude` and `extend-exclude`;
  - an empty `raises-require-match-for`, which disarms PT011, and a
    builtins `ignorelist`, which disarms A001;
  - a nested `tests/ruff.toml`;
  - an `.ignore` file.

  `extend-exclude` under `[tool.ruff.lint]` is not a ruff key, and ruff
  exits 2 on it.
- **The count's own inputs could be bent.** The second review showed two
  ways past the first revision's count:
  - `[tool.ruff] target-version = "py38"`, which that count read, hid
    version-dependent findings from the lint gate and the count alike. Over
    the review's `tv/tree-py38/` the configured run passes and the count at
    `py38` reads nothing, while at the `py310` floor it reads FURB188 and
    FURB161. Over its `tv2/p.py` the floor adds A001 three times.
  - A module under a directory ruff excludes by default, such as
    `openspec_graph/dist/planted.py`, is hidden from both runs and absent
    from ruff's `--show-files` list.

  The rule as now written fails `tv/tree-py38/` twice over: the reader names
  `py38` against the `py310` floor, and the count at the floor reports both
  findings.
- **Two of the fifteen lock in nothing.**
  - `python -m ruff rule FA100` and `FA102` each say the rule will "flag
    such usages if your project targets Python 3.9 or below". A PEP 604
    annotation probe fires FA102 at `--target-version py39` and passes at
    `py310`, and this project's floor is 3.10 now and 3.11 after
    `prepare-release-0-4-0`.
  - Nine planted TODO-style comments, run through `--select FIX,TD` on
    stdin, drew TD findings on eight lines and FIX findings on all nine:
    every line TD flagged, FIX flagged too.
- **The near-zero families, by site.**
  - FURB has five findings, all marked safe-fixable:
    `openspec_graph/rules.py` and `tests/test_properties.py` (FURB110, a
    conditional repeating its own test), `tools/_common.py` (FURB167
    `re.S`, FURB188 a hand-rolled prefix strip) and
    `tools/check_promotion.py` `write_github_output` (FURB122).
  - PYI has one, `openspec_graph/delta.py` `_mentions_value`'s `int | float`
    (PYI041).
  - PT011 has six, a broad `pytest.raises` in
    `test_the_guard_stays_quiet_on_ordinary_commands`,
    `test_manifest_generator_rejects_a_folded_description` (three) and the
    two witness write-failure tests. The `PT` family as a whole has more
    than a hundred findings.
  - PTH has four: `open()` in `write_github_output`, `glob.glob` in
    `test_gate_scripts_have_no_duplicated_repo_root_literal`, and
    `os.replace` and `os.unlink` in `openspec_graph/witness.py`'s
    `write_witness`, which `test_write_witness_is_atomic` and its siblings
    intercept by patching `witness.os.replace`. A probe patching `os.replace`
    and `os.unlink` sees `Path.replace` and `Path.unlink` call neither on
    3.10.20, and both on 3.11.17, 3.12.3, 3.13.16, 3.14.6 and 3.15.0.
  - ERA has two, both prose: a parenthesised list of quoted phrases in
    `openspec_graph/parse_semantics.py`'s tier comment, and the two
    markdown headings quoted in
    `test_parse_speckit_extracts_fr_and_sc_from_canonically_annotated_headings`.
    The documented reason for leaving ERA off, that most of its hits are
    prose quoting markdown, still holds: both are.
- **Preview exposure.** `--preview` adds FURB142 twice in
  `tests/test_decomposition.py` to the new selection on ruff 0.17.0 and
  0.17.1. Today's selection already carries 44 latent preview findings
  (S404 30, RUF105 8, RUF069 4, UP052 2). CI installs `ruff` unpinned, through
  the dev extra.
- **The declined families have backlogs.** By the same `--statistics`
  command:
  - TRY003 and EM: 138 together, 118 of them under `openspec_graph/` and
    `tools/` (the review's 118 counted those two trees);
  - COM812 458, D401 104, D205 354, PLR 213 and TC 86;
  - PLC 86 and PLW 6, which PL's existing line covers.

  The existing E501 line says "~100 places", and E501 now reads 457.
- **Outside the linted trees.** `.claude/hooks/guard_promotion.py` holds an
  `except Exception` on purpose ("a seat belt never blocks on its own
  fault"). It is outside the lint gate's trees and `[tool.mypy] files`, so
  the new families do not judge it, and this package does not widen either
  gate.
- **pytest.**
  - `[tool.pytest.ini_options] addopts` is `-q --strict-markers`. `python -m
    pytest --collect-only -q -p no:cacheprovider --strict-config` exits 0.
    No test carries `xfail`, and no test uses `pytest.warns` or a warnings
    filter.
  - Each tier passed under `-W error`: unit 867, integration 871, e2e 332.
    The two nested pytest runs that read this repository's configuration
    passed under `PYTHONWARNINGS=error`.
  - The first review ran the coverage-measured run of the test stage under
    this change's pytest configuration on copies of `bfbc124`. On 3.10.20,
    3.11.17, 3.12.3, 3.13.16 and 3.14.6 it read 2069 passed and 1 failed, the
    smoke-wheel test that fails in every one of the review's copies. On
    3.15.0 it read 2057 passed and 13 failed: the same smoke-wheel test, and
    12 action-contract tests that fail identically on an unmodified copy,
    because the action's shell starts an interpreter without the library
    path that build needs. No failure was caused by a warning, and every
    coverage floor passed.
  - Nested, on pytest 9.1.1:
    - an unknown key under `--strict-config` and `filterwarnings =
      ["error"]` exits 4 with `ERROR: Unknown config option`;
    - under the filter alone it exits 3, `INTERNALERROR`, as it also does
      with `addopts` cleared;
    - a planted warning exits 1 naming its message;
    - a passing `xfail` exits 1 with `[XPASS(strict)]`.
  - pytest 9's umbrella `strict` option would also turn on
    `strict_parametrization_ids`, under which collection stops in
    `tests/test_adopter_urls.py` and `tests/test_detect_thresholds.py`
    (duplicate parameter ids).
- **The subprocess calls.**
  - An AST pass over `tests/*.py` finds 45 `subprocess.run` calls in 21
    files, and none passes `timeout=`. The review's "one with a timeout"
    most likely counted the assertion in `test_graft_witness.py` that
    `detect`'s own call passes `detect.GIT_TIMEOUT_SECONDS`.
  - That constant is the in-tree precedent: "Named rather than inlined …
    Not a quality threshold, so not configuration."
  - The slowest of 269 CLI children in the e2e tier took 0.68 s here, and
    0.77 s under coverage in the first review's run.
  - `tools/check_no_hardcoded_thresholds.py` scans the Makefile and the
    workflow YAML only. `close-gate-script-gaps`, as revised, widens it to
    text targets and to `tools/*.py` constants, and never to `tests/`.
- **Typing.**
  - `rule_types.py` binds `ERROR, WARN, INFO = "ERROR", "WARN", "INFO"` as
    plain `str`, and `Finding` is constructed in `rules.py` alone.
    `report.py` reads a severity from JSON into its own `FindingRecord`,
    keeps its own `SEVERITIES` and `_COMMANDS` tables, and keeps zero
    intra-package imports (`test_report_has_no_intra_package_imports`).
    `sarif.py` keeps `_LEVELS`.
  - A scratch copy of `rule_types.py`, with `Severity = Literal["ERROR",
    "WARN", "INFO"]`, `Final` constants and both fields annotated, was
    substituted with mypy's `--shadow-file`. The type gate printed
    "Success" under `--platform linux` and `win32`, and at
    `--python-version 3.11`.
  - With the `tests.*` override lifted, the per-code counts under `tests/`
    equalled `MYPY_TESTS_CEILINGS` with and without the change, on both
    platforms. Ruff's docstring counts for that file still equal
    `DOCSTRING_CEILINGS`. The override disables `arg-type` for `tests.*`, so
    a planted module there would hide the error the planted guard looks for.
- **`py.typed`.** No `py.typed` exists, and `[tool.setuptools]` declares no
  package data. No test or gate script pins either archive's file list, and
  `tools/check_wheel_metadata.py` reads `METADATA` and the licence
  directory. setuptools' own `NEWS.rst` lists, under v69.0.0, "Include type
  information (py.typed, *.pyi) by default (#3136)", and the build system
  requires a setuptools from 77 on. The first review's copy with the marker
  added built a wheel alone, and an sdist then the wheel from it. Both wheels
  and the sdist list it. `test_the_real_wheel_passes_the_gate` skips on any
  failed build; the archive guard skips only for a missing `build` or an
  unreachable index.
- **Python 3.15.**
  - The `actions/python-versions` manifest `setup-python` downloads from
    lists `3.15.0` with `stable: true`, with `linux-24.04-x64` and
    `win32-x64` builds. The `ubuntu-24.04` (`ubuntu-latest`) and
    `windows-2025-vs2026` (`windows-latest`) image readmes pre-cache Python
    up to 3.14.8.
  - coverage 7.16.2, mypy 2.4.0 (with `librt`) and hypothesis 6.170.1
    publish `cp315` wheels. The rest of the dev extra is pure Python.
  - `ci.yml`'s matrix is 3.10 to 3.14. `prepare-release-0-4-0` rewrites
    that line, the classifier block and `docs/hooks.md`'s `test` row.
  - The workflow guards forbid soft-fail tokens on `promotion`,
    `release-tier`, `ci-ok` and the release ancestry step:
    `tests/workflow_support.py`'s `SOFT_FAIL`, applied in
    `tests/test_ci_promotion.py` and `tests/test_release_surface.py`. The
    `test` job, by contrast, explicitly permits an experimental leg behind
    `continue-on-error: ${{ matrix.experimental || false }}` (R-HCW-10,
    `test_the_experimental_leg_is_an_expression_not_a_job_literal`).
  - `ci-ok` fails on any `needs` result other than `success`. GitHub's
    contexts reference documents `outcome` and `conclusion` for a step
    under `continue-on-error`, and documents nothing about how
    `needs.<job>.result` reads after a matrix leg fails under it.

## What Changes

**The package goes alone into `dev` in one pull request, held until `v0.3.0`
is pushed to origin and `v0.3.0^{commit}` is an ancestor of `dev`. The
implementation follows in a draft pull request, and ships in 0.4.0 if it
merges before that release's release-prep pull request opens. Otherwise it
is held until the same two facts hold for `v0.4.0`, and ships in the next
minor, as the maintainer records (DEC-RCS-017).**

- **`pyproject.toml` `[tool.ruff.lint]`.**
  - `select` gains the zero-cost families A, ASYNC, BLE, FIX, FLY, G, INT,
    LOG, PGH, PLE, SLOT, T10 and YTT. It also gains FURB, PYI and the single
    rule PT011, each under a one-line reason.
  - For the modules under the three trees, nothing hides a finding of any
    of them. That rules out a per-file entry, a `noqa`, an `ignore` or
    `exclude` key, a setting, a target version below the floor, an ignore
    file, a nested configuration and a default-excluded directory. The
    count guard below enforces that.
  - The "Deliberately NOT selected" block is rewritten. Every family this
    package measured and declined gets a line with its count, the command
    and `bfbc124`, and its reason: FA, TD, PTH (with its trigger), ERA
    (re-checked), TRY003/EM, COM812, TC, and the PL subfamilies (PLE now
    selected; PLR, PLC and PLW declined). The existing E501, D and ANN
    lines are re-measured so their figures are true.
- **The hits, fixed and behaviour-neutral.**
  - `openspec_graph/rules.py`, `tests/test_properties.py`,
    `tools/_common.py` and `tools/check_promotion.py`: ruff's safe FURB
    fixes.
  - `openspec_graph/delta.py`: `value: float`.
  - `tests/test_claude_guard.py`, `tests/test_release_surface.py` and
    `tests/test_witness.py`: a `match=` on each broad `pytest.raises`,
    naming the message the code raises today.
- **`pyproject.toml` `[tool.pytest.ini_options]`.**
  - `addopts = "-q --strict-markers --strict-config -ra"`,
    `xfail_strict = true` and `filterwarnings = ["error"]`, under a comment
    naming the measurement and the rule for any later `ignore` entry.
  - `testpaths` and `markers` are unchanged.
- **`tests/support.py`.** A module-level `RUN_CLI_TIMEOUT_SECONDS`, under a
  comment saying what it bounds, why it is a harness constant and not
  configuration, and its limit: a hang that repeats across many calls still
  ends in the job's cancellation. `run_cli` passes it to `subprocess.run`,
  and a `TimeoutExpired` propagates.
- **`openspec_graph/rule_types.py`.** `Severity = Literal["ERROR", "WARN",
  "INFO"]`, added to the module's `__all__`. `ERROR`, `WARN` and `INFO` are
  each `Final`, and `Finding.severity` and `Rule.severity` are annotated
  `Severity`. Nothing changes at run time, and `report.py` and `sarif.py` are
  not edited.
- **`openspec_graph/py.typed`** (new, empty). setuptools packages it by
  default, so no `[tool.setuptools]` key is added.
- **Tests**, each with one tier marker, red before the change it covers:
  - `tests/ratchet_support.py`, beside `ruff_docstring_command`:
    - the zero-cost selection;
    - the target-version reader, which takes the `requires-python` floor
      alone and names a `[tool.ruff] target-version` other than it;
    - the count's command builder;
    - the file-list comparison;
  - `tests/test_static_ratchets.py`: the reader's unit test, the count guard
    with its file-list check, and its planted escapes, beside the docstring
    count that uses the same method;
  - `tests/test_ci_workflow.py`: the selection's presence guard, its planted
    violation of every selection and the planted unknown-severity type
    check, beside the `T201` and bare-generic guards;
  - `tests/test_suite_shape.py`: the pytest-strictness guards and their
    planted nested runs with their exact exit codes, beside the marker
    registration guard;
  - `tests/test_cli_surface.py`: the `run_cli` timeout guards, beside the
    `COVERAGE_PROCESS_START` contract;
  - `tests/test_decomposition.py`: the severity binding to every severity
    table, beside the public-import guard;
  - `tests/test_release_surface.py`: the `py.typed` guards. The archive
    guard builds the sdist and then the wheel from it, and skips only for a
    missing `build` or an unreachable index.

  Their names are fixed in `tasks.md`.
- **`.claude/agents/planlint-verifier.md`.** The `ruff`/`mypy` bullet names
  the new families and the pytest posture, with their remediation norm,
  including that a FIX hit on prose is fixed by rewording the prose.
- **`docs/next-steps.md`.** A new item records the 3.15 leg's deferral,
  what was established (the Linux 3.15 run included) and what was not, and
  its trigger.
- **`CHANGELOG.md` `[Unreleased]`.** A `### Changed` group for the lint and
  pytest standards and the `run_cli` bound, and an `### Added` group for
  the typed public surface, each entry led by **`raise-coding-standards`**.

## Non-Goals

- **No Python 3.15 leg, classifier or `docs/hooks.md` change.** It is
  deferred to its own package, with the trigger DEC-RCS-012 names. No line
  of `.github/workflows/` changes in this package.
- **No PTH, ERA, FA or TD, and no family with a backlog.** PTH waits for
  the 3.11 floor, because its fix is not neutral on 3.10 (DEC-RCS-003).
  ERA's reason still holds. FA cannot fire at this floor, and TD repeats
  FIX. TRY003/EM, COM812, D401/D205, PLR, PLC, PLW and TC start a cleanup
  rather than lock in a property (DEC-RCS-005), so they are recorded and
  not selected.
- **No widening of the lint or type gates.** `.claude/hooks/guard_promotion.py`
  stays outside both, with its deliberate `except Exception`. Bringing the
  hooks under the gates is its own change.
- **No anchor between `requires-python` and the matrix.** The count trusts
  the declared floor. No existing test ties it to the lowest hard leg, and
  adding one is out of scope (DEC-RCS-016).
- **No `pytest` floor and no dev-extra edit.** The individual pytest keys
  work on the unfloored `pytest` the extra installs, and pytest 9's `strict`
  umbrella would not be zero-cost (DEC-RCS-007).
  `test_the_dev_extra_floors_mypy_and_pins_nothing` stays as it is.
- **No timeout at the other `subprocess.run` sites under `tests/`.** They
  start mypy, ruff, pytest, `build`, git and bash, each with its own cost.
  `run_cli` is the one shared helper and the most frequent caller. The rest
  are counted in `tasks.md` and left to a later package.
- **No run-time severity validation, no `TypedDict`, no change to
  `report.py` or `sarif.py`.** A `Literal` changes nothing at run time.
  `FindingRecord` reads an untrusted envelope, and narrowing it there would
  refuse envelopes `report` accepts today. Their severity tables are bound
  to `Severity` from the test side. A `TypedDict` for `Finding.as_dict`
  would widen the typed surface and move the ratchet ceilings
  (DEC-RCS-010, DEC-RCS-011).
- **No change to `openspec_graph/`'s behaviour.** The rules, the `RULES`
  tuple, `README.md`'s rules table, `tests/baseline_rules.json`, the golden
  hashes and `[project] dependencies` are untouched.
- **No Makefile, workflow, composite-action or `.pre-commit-config.yaml`
  edit.**
- **No edit to another package, shipped or not, or to the ratchets.**
  `MYPY_TESTS_CEILINGS`, `MYPY_WAIVERS` and `DOCSTRING_CEILINGS` are
  unchanged by this change, which the measurement above predicts.
  `select-zero-cost-guards`, `ratchet-test-types-and-docstrings` and
  `shape-the-test-suite` are followed, not edited (DEC-RCS-015).
  `prepare-release-0-4-0` is not amended to hold this change's order
  (DEC-RCS-017).
- **No `tests/AGENTS.md` edit.** It sits one line under its
  `MAX_NESTED_LINES` budget, nothing in it becomes false, and a test that
  warns fails naming the warning itself.
- **No ruff formatter.** The repository runs `ruff check` and not
  `ruff format`, and COM812's documented conflict is with that formatter.

## Affected Capabilities

- `coding-standards`
