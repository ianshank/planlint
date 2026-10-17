# Change: Close the Gate-Script Gaps — the Threshold Guard Sees What It Claims, and Every Gate Script Fails Closed

## Why

`tools/AGENTS.md` opens with the rule this package applies: a gate whose
failing path is untested "is worse than no gate: it reports PASS on the thing
it was added to catch." A review of `dev` on 2026-10-16 found four gate
scripts that do exactly that, on inputs a contributor can produce by accident:

- **The threshold guard sees a fraction of what its docstring claims.**
  `tools/check_no_hardcoded_thresholds.py` is the thresholds target's recipe,
  which `make pre-pr` composes. CI's `security` job runs the same command
  inline, not through the target. It scans the `Makefile` for integers of two
  or more digits outside `$(...)`, and the files under `.github/workflows/`
  for `fail-under`/`fail_under` followed by `:` or `=` and a digit, and for
  `ruff==`, `mypy==` and `pytest==`. Everything else passes. It misses a
  single digit, a decimal, an upper-case `COV_FAIL_UNDER`, a space-separated
  `--cov-fail-under 90`, any other named threshold flag such as
  `--per-file-min 85`, every other dev tool and every other PEP 440 operator,
  the composite action, the adopter templates, the skill's copy of the
  template, the pre-commit files, the `Dockerfile`, and threshold constants in
  `tools/` itself. Its docstring also promises to catch a "pinned path", which
  no line of code checks.
- **The pyproject reader truncates.** `tools/_common.py`'s
  `read_pyproject_int` matches `rf"{key}\s*=\s*(\d+)"` without an end anchor,
  so `fail_under = 97.5` reads as `97`, `9_5` as `9`, `0x61` as `0` and
  `97abc` as `97`. The coverage gates then compare against the truncated
  number, so a floor written as a fraction silently loosens. The product's own
  reader, `openspec_graph/thresholds.py`'s `_TOML_FAIL_UNDER`, is anchored,
  reads the fraction exactly (`tests/test_detect_thresholds.py` expects
  `85.5`), and refuses the other three.
- **The secret scan's fallback fails open.** `tools/check_secrets.py` runs
  gitleaks when the binary is on `PATH` and otherwise a Python fallback over
  `git ls-files`. When `git ls-files` fails (no `.git`, or git's "dubious
  ownership" refusal), `_tracked_files` returns `[]`, and `main` prints "PASS:
  no secrets found (gitleaks absent, fallback scan clean)" and exits 0 over a
  tree holding a planted AWS-shaped key. `tests/test_gate_scripts.py`'s
  `test_fallback_scan_returns_nothing_outside_a_git_repo` asserts that empty
  list as the contract. A tracked file with a non-ASCII name is skipped,
  because git quotes it (`"cl\303\251.py"`) and the quoted string names no
  file. A tracked file that exists but cannot be read is skipped too
  (`except OSError: continue`). A listing whose every path is skipped passes
  as clean, and git missing from `PATH` is a traceback. The fallback is not
  only a local safety net. `make pre-pr` runs in `ci.yml`'s `release-tier`
  job and in `release.yml`'s `gate` job, and neither installs a gitleaks
  binary. The only gitleaks in the workflows is the `security` job's action.
- **Both coverage checkers take their floor from the working directory.**
  `tools/check_coverage_floor.py` reads `Path("pyproject.toml")` in both of its
  modes, and so does `tools/check_branch_coverage.py`, which the review did not
  name. Run from a directory whose own `pyproject.toml` declares a lower floor,
  either one gates this repository's report against that floor and passes.

Each is a gate that answers "pass" when it could not read what it was asked to
judge. The repository already decided what such a gate must say instead: "a
report over no package is not a clean report" (DEC-RDS-006), and "an empty
tree is not a clean tree" (DEC-RDS-005). This package applies that rule to the
gates that predate it. Once the secret scan can name a non-ASCII file, it and
the guard must also print that name on an ASCII console, where today the
FAIL line is a traceback.

**This is a dev-side tooling package.** It changes no shipped CLI behaviour.
`openspec_graph/`, the rules, the golden hashes, the workflows and every
`make` recipe are untouched. It lands in 0.4.0, package-first, the shape
`lean-production-tree` (#58) and `prepare-release-0-4-0` (#60) took. One pull
request carries this package alone into `dev`, held until the 0.3.0 promotion
is done. The implementation is a new pull request from `dev`, opened as a
GitHub draft (`tasks.md`, header, and DEC-GSG-001).

**Evidence:** every finding re-measured in session scratch at `bfbc124`
(`origin/dev`), 2026-10-16, and the first review's findings on 2026-10-17.
`tasks.md` "Measured at `bfbc124`" and "Re-checked at `bfbc124`, 2026-10-17
(the first review)" record each command and its output. Each scratch script
loaded the real script from the worktree by path and wrote only under the
session's scratch directory.

- **The threshold guard.** One planted root per shape, each holding a clean
  `Makefile`, a clean `ci.yml` and a copy of this repository's
  `pyproject.toml`, was handed to the current guard's `main(argv, root)`.
  Among the shapes listed above, the current guard caught only the control
  case, `--cov-fail-under=90` in a workflow. The drafting prototype caught
  every planted shape except `coverage==`. Its word list was not the one the
  first draft of DEC-GSG-005 stated: it also matched `minimum`, `maximum` and
  trailing-s plurals. DEC-GSG-005 now adopts that superset. `coverage` is not
  a dev-extra name, which is why DEC-GSG-006 declares it. Rebuilt from the
  revised R-GSG-3 and R-GSG-4 with `coverage` declared, the rules catch every
  planted shape. On the real tree they report one literal, the `Makefile`'s
  `NO_FLOOR := 0` (DEC-GSG-009), as the drafting prototype did. The rules in
  `tools/check_no_hardcoded_thresholds.py` are `_THRESHOLD_TOKEN` and the two
  `re.search` calls in `check_workflow`. `targets()` globs
  `.github/workflows/*.yml` and `*.yaml` and resolves the makefile, and nothing
  else.
- **The reader.** Planted `pyproject.toml` files read through the real
  `_common.read_pyproject_int` give the truncations above. Read through
  `check_coverage_floor.main` from a planted tree, a report below
  `fail_under = 97.5` but above 97 exits 0 with "meets floor 97%", and the same
  report against `fail_under = 9_5` exits 0 with "meets floor 9%". The
  product's `as_threshold_number` over `_TOML_FAIL_UNDER`'s capture returns
  `97.5` for the first and `None` for every other malformed value, and `None`
  for `101`, which the tools reader reads as 101. `tomllib` returns `9_5`,
  `+97`, `0x61`, `0o141` and both quoted keys as a plain `int`, and `97.5`,
  `97e0` and `"97"` as a `float` or a `str` (DEC-GSG-002).
- **The secret scan**, reproduced with **no git process started**: the loaded
  script's `subprocess.run` was replaced by a stub returning git's own result
  in each case. These cases print the PASS line and exit 0 over a planted key:
  - exit 128 with "not a git repository";
  - exit 128 with "detected dubious ownership";
  - exit 0 with the quoted `"cl\303\251.py"`.

  The same name reported NUL-separated, as `git ls-files -z` reports it, names
  the file on disk. No path in this worktree is non-ASCII, so the tree is clean
  today by luck rather than by guard. A real repository whose only tracked
  path sits under `node_modules/` and is absent from disk also prints the PASS
  line. `tasks.md` Milestone 0 repeats the no-`.git` and non-ASCII cases
  against a real `git init` fixture, the test suite's `_git_repo` helper.
- **The coverage checkers.** Both run as `python tools/<script>.py
  <report>` against a planted report. From a directory holding no
  `pyproject.toml`, each exits 2. From a directory whose `pyproject.toml`
  declares a lower floor, each exits 0. From the worktree root, each exits 1
  against this repository's floors. From a project root,
  `check_coverage_floor.py out/coverage.json` exits 0 today, and `out/` holds
  no `pyproject.toml`, which is why the floor is found by a walk up from the
  report (DEC-GSG-012).
- **The console.** Under `PYTHONIOENCODING=ascii`, the current guard over a
  planted root with a non-ASCII path, and the secret scan given the
  NUL-split `clé.py`, each raise `UnicodeEncodeError` on their FAIL line and
  exit 1 with nothing on stdout (DEC-GSG-015).
- **The tests this package touches.** No spec cites
  `test_fallback_scan_returns_nothing_outside_a_git_repo`. The guard tests that
  shipped specs cite are `test_threshold_guard_passes_on_a_clean_tree`,
  `test_threshold_guard_fails_on_a_hard_coded_coverage_floor`,
  `test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow`,
  `test_threshold_guard_fails_on_a_pinned_tool_version`,
  `test_threshold_guard_scans_every_workflow`,
  `test_every_workflow_is_scanned_by_the_threshold_guard` and
  `test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency`. The
  first four build their tree through `tests/test_threshold_guard.py`'s
  `_guard_tree`, which writes no `pyproject.toml`.
  `test_every_workflow_is_scanned_by_the_threshold_guard` asserts that
  `check_workflow` returns nothing for each workflow before any whitelist,
  and `harden-release-pipeline`'s AC-HRP-23 requires it to pass unedited, so
  a workflow line can never be whitelisted (R-GSG-6).
  `tests/test_static_ratchets.py` holds each of the four scripts' missing
  docstrings at an exact ceiling. `tools/AGENTS.md` is one line under
  `MAX_NESTED_LINES` (`tests/test_agent_artifacts.py`).
- **The neighbours.** `prepare-release-0-4-0` does **not** plan the `tomllib`
  swap: its C-RFR-1 forbids replacing any hand-rolled TOML scanner, and it
  leaves the swap to `docs/next-steps.md` item 7a's own package. Its pull
  request 1 rewords the 3.10 sentences of `tools/_common.py`'s scanner
  docstrings (R-RFR-7), `read_pyproject_int`'s among them, and drops `tomli`
  from the dev extra. `lean-production-tree` keeps every package added to
  `dev` after `c0ff090` that has not shipped (R-LPT-2).
  `harden-release-pipeline` adds `tools/release_notes.py` and lines to
  `release.yml`, which it pins whole against a golden copy.
  `tighten-release-surface` and `raise-coding-standards` are drafts not yet on
  `dev`, read in their own worktrees at `bfbc124`; their edit sites are under
  "Shared edit sites" below. At `bfbc124` none of these is implemented.

## What Changes

**One pull request carries this package alone into `dev`, after the 0.3.0
promotion is done. The implementation follows in a new pull request from
`dev`, opened as a draft (DEC-GSG-001).**

- **`tools/check_no_hardcoded_thresholds.py`** (DEC-GSG-004 to DEC-GSG-009):
  - `targets(root)` adds, by pattern, `.github/actions/*/action.y{a,}ml`,
    `templates/*.y{a,}ml`, `skills/*/assets/*.y{a,}ml`, the root's
    `.pre-commit-*.yaml` and the root's `Dockerfile*` to the makefile and the
    workflows it selects today.
  - Today's three rules stay as they are, and the floor and pin rules run
    over every target that is not the makefile. Two line rules are added for
    every text target:
    - a named-threshold rule: a flag, key or variable whose `-`/`_`-separated
      name has a segment `min`, `max`, `minimum`, `maximum`, `floor`,
      `under`, `ratio` or `threshold`, or one of those with a trailing `s`,
      in any case, followed by `=` or `:` (a closing quote allowed before
      either, as a quoted key writes it), a Make assignment operator,
      whitespace or an argument-list comma, then an integer or a decimal. It
      skips whole-line comments in every target and never reports
      `max-parallel`;
    - a pin rule built from the dev extra's names with every PEP 440
      operator, and `@` after a name (`uvx ruff@0.4.2`,
      `ruff @ git+https://...`) but never after a `/`, as in an action's
      `owner/name@ref`; it reads comment lines outside the makefile.

    A number or a pin today's rules already report is reported once, with
    today's message.
  - One AST rule is added for `tools/*.py`: a module-level numeric constant
    whose name has one of those segments.
  - `tools/threshold_whitelist.txt`, read under the scanned root, exempts a
    finding by its root-relative POSIX path and subject, with a reason. An
    entry that suppresses nothing fails the guard. No workflow line is ever
    whitelisted.
  - A target it cannot read or decode, a `tools/` module it cannot parse, a
    dev extra it cannot read, and a malformed whitelist line each exit 2.
  - The docstring states what is scanned and drops "pinned path". The PASS
    line names the scanned set by kind. Each FAIL line begins with the
    root-relative POSIX path and carries the finding's subject.
- **`tools/threshold_whitelist.txt`** (new): a two-line header, then one
  entry, `Makefile NO_FLOOR=0`, with its reason (DEC-GSG-008, DEC-GSG-009).
- **`tools/_common.py`** (DEC-GSG-002, DEC-GSG-003, DEC-GSG-015):
  - `read_pyproject_int` matches the bare key, then `=`, ASCII digits only and
    an optional trailing comment, anchored at both ends. It returns `None`
    only when the file, table or key is absent, presence being
    `has_pyproject_key`'s. A key present in any other shape — quoted, or with
    any other value — raises `PyprojectValueError`, a new `ReportError`
    subclass naming the file, the table, the key and the value as written.
  - Its docstring says the scanner was chosen under the 3.10 floor and that
    replacing it with `tomllib` is item 7a's change. The type refusals carry
    forward to that change. The spellings `tomllib` normalises are item 7a's
    decision, and it replaces those tests rather than keeping them. It claims
    nothing about `tomllib`'s availability.
  - `dev_extra_names`, a stdlib reader of the `[project.optional-dependencies]
    dev` names, on the same table-tracking loop as `coverage_sources`, with
    the same docstring wording on 3.10, item 7a and `tomllib`.
  - One helper that reconfigures `sys.stdout` and `sys.stderr` to UTF-8 with
    `errors="backslashreplace"`, as `openspec_graph/cli.py`'s `main` does,
    called first by every script this package changes.
  - `resolve_makefile`'s docstring stops saying `check_makefile` tolerates
    a path it cannot open.
- **`tools/check_secrets.py`** (DEC-GSG-010, DEC-GSG-011):
  - `_tracked_files` runs `git ls-files -z`, reads bytes, decodes them as
    strict UTF-8 and splits on NUL.
  - The fallback exits 2, naming the cause and printing no PASS line, in five
    cases: git cannot be started; it exits non-zero (its stderr is carried);
    its output is not UTF-8; no listed file is scanned, counted after the
    absent, non-regular and skipped paths are dropped; a listed regular file
    cannot be read.
  - The module docstring's claim that the fallback honours `.gitleaks.toml`'s
    allowlist of `tests/` fixtures is replaced by the two skip lists as they
    are: `_SKIP_DIRS` for the fallback and `.gitleaks.toml` for gitleaks.
    The fallback alone skips `venv`, `__pycache__`, `.ruff_cache` and
    `.mypy_cache`. The token patterns and the gitleaks path are unchanged.
- **`tools/check_coverage_floor.py`** and **`tools/check_branch_coverage.py`**
  (DEC-GSG-012):
  - Each confirms the report exists first, then reads the nearest
    `pyproject.toml` at or above the report's directory, the first found
    winning, in every mode.
  - None found is exit 2, naming where the walk started.
  - Each maps `PyprojectValueError` to exit 2. The argv is unchanged.
- **`tools/dead_code.py`** and **`tools/matcher_accuracy.py`**: a floor the
  reader refuses is exit 2 with the reader's message, never a traceback
  (R-GSG-12). Each calls the console helper first.
- **`pyproject.toml`**: the dev extra gains a bare `"coverage"`, under a
  comment. The `coverage-run` recipe invokes `python -m coverage` directly,
  and `[tool.coverage.run]` relies on coverage's own subprocess hook, so it is
  a direct dependency the extra did not declare. Declaring it puts it under the
  pin rule. `[project] dependencies` stays `[]`, and no other line changes
  (DEC-GSG-006).
- **Tests**, every new one written and run red first (DEC-GSG-013):
  - `tests/test_threshold_guard.py`: the widened targets, each widened
    shape, the quiet set, the pin rule, the constants rule, the whitelist, the
    exit-2 inputs and the real tree. `_guard_tree` gains a planted
    `pyproject.toml` with a dev extra, so the cited tests built on it keep
    their names and every asserted property.
  - `tests/test_pyproject_reader.py` (new, flat): the reader's exact-or-refuse
    contract, its agreement with the product's reader inside the product's
    range and its recorded outcome at `101`, and each caller's exit 2.
  - `tests/test_gate_scripts.py`: `test_fallback_scan_returns_nothing_outside_a_git_repo`
    is deleted and replaced by tests of each refusal and of the `-z`
    enumeration (DEC-GSG-011), and a test of non-ASCII paths on an ASCII
    console (DEC-GSG-015).
  - `tests/test_coverage_checkers.py`: the walk up from the report, from a
    foreign working directory and from below the project root.
  - `tests/test_skill_distribution.py`: `test_threshold_guard_scans_every_workflow`'s
    loop judges each target through the whitelist, with its name and every
    other assertion kept.
  - `tests/test_static_ratchets.py`: a docstring ceiling moves only down,
    and only where a rewritten function's count falls.
- **Documents**: these each describe the widened scope, the whitelist or the
  changed scripts:
  - the thresholds target's `##` help text in the `Makefile`, with its
    recipe unchanged;
  - `README.md`'s gates row and its "No numeric threshold" paragraph;
  - `docs/hooks.md`'s commit-hook line and its every-workflow note;
  - `docs/aqa.md`'s externalisation paragraph, and its Gates-table security
    row, which names exit 1 only;
  - `tests/support.py`'s `run_tool_main` docstring, whose sentence "These
    scripts read `Path("pyproject.toml")` from the cwd" becomes the walk;
  - `.claude/agents/planlint-verifier.md`'s sentence that the guard
    "allowlists comments".

  `tools/AGENTS.md`'s "Never hard-code a threshold" bullet names the
  whitelist, its reason rule and that no workflow line is whitelisted,
  replacing text so the file stays within its line budget.
- **`CHANGELOG.md`** `[Unreleased]`: a `### Fixed` entry led by
  ``- **`close-gate-script-gaps`.**``.
- **Shared edit sites**, named so each merge is prepared rather than found.
  For each sibling, whichever lands second re-reads the sites at its own head:
  - with `prepare-release-0-4-0`'s pull request 1: `read_pyproject_int`'s
    docstring in `tools/_common.py`, which its R-RFR-7 rewords, and the dev
    extra in `pyproject.toml`, from which it drops `tomli`;
  - with `lean-production-tree`'s implementation: `README.md`,
    `docs/hooks.md` and `tools/AGENTS.md`, each at other lines;
  - with `harden-release-pipeline`'s implementation: `tools/AGENTS.md`'s
    line budget, which both spend from, and its new `tools/release_notes.py`
    and `release.yml` lines, which the widened guard must find quiet. A
    `release.yml` line cannot be whitelisted (`tasks.md` Milestone 0);
  - with `tighten-release-surface`'s implementation, a draft not yet on
    `dev`:
    - `README.md`'s gates table, which gains its `wheel-check` row beside
      this package's thresholds row;
    - `docs/hooks.md`'s opening and pre-commit paragraphs and its CI table's
      `security` cell, beside this package's commit-hook line and
      every-workflow note;
    - `docs/aqa.md`'s "Reproducing CI locally" and a sentence after its
      Gates table, beside this package's security row and externalisation
      paragraph;
    - `.pre-commit-config.yaml`'s header comment, which it rewords and which
      the widened guard now reads, comments included for the pin rule;
    - the `Makefile`'s `wheel-check` recipe, which the widened guard scans;
    - `ci.yml`'s `security` step, which it turns into a call of the
      thresholds target. The line must be quiet, and no workflow line is
      whitelisted;
  - with `raise-coding-standards`' implementation, a draft not yet on `dev`:
    - `tools/_common.py`, where it applies ruff's safe FURB fixes to
      `_SOURCE_ARRAY` and `normalize_scope`, beside `coverage_sources`, where
      this package adds `dev_extra_names`;
    - the ruff families BLE, G, LOG and FURB and the single rule PT011, and
      the pytest posture `filterwarnings = ["error"]`, `xfail_strict` and
      `--strict-config`. These will judge this package's new code and tests:
      no blind `except Exception`, lazy arguments in the DEBUG records, a
      `match=` on any broad `pytest.raises`, and no warning raised by a new
      test;
    - `tests/support.py`, where it adds `RUN_CLI_TIMEOUT_SECONDS` above
      `run_cli` and this package rewords `run_tool_main`'s docstring. The
      constant lives in `tests/`, which the constants rule does not read,
      and its name carries no word of R-GSG-3.

## Non-Goals

- **No product change.** No file under `openspec_graph/`, no rule, no rule
  message, no golden hash, no `README.md` rules-table row, no
  `tests/baseline_rules.json` entry. G003 keeps its matcher. This package
  governs this repository's own gate scripts, which no adopter runs.
- **No general parser.** No YAML, shell, Make or TOML parser is added, and no
  runtime dependency; the dev extra gains `coverage` alone (R-GSG-10). The
  guard stays a line scanner with one small `ast` pass over `tools/`, as the
  decision this package was handed requires. Its accepted misses, the ones
  only a parser could catch and the neutral names no rule by name can see,
  are recorded in DEC-GSG-005.
- **No `tomllib`.** Replacing the hand-rolled readers is
  `docs/next-steps.md` item 7a's own package, which `prepare-release-0-4-0`'s
  C-RFR-1 leaves to it. This package anchors the reader now. It leaves, in
  the reader's docstring and tests, what carries forward to that package,
  the type refusals, and what that package decides, the spellings `tomllib`
  normalises. It does not leave them in `docs/next-steps.md`, whose item 7a
  `prepare-release-0-4-0`'s pull request 1 rewrites (DEC-GSG-002,
  DEC-GSG-014).
- **No fractional floors and no quoted keys.** The gates refuse
  `fail_under = 97.5` and `"fail_under" = 97` loudly rather than reading
  them. A later package may widen the reader to the product's grammar
  (DEC-GSG-003).
- **No constants scan of `tests/` or `openspec_graph/`.** The suite's own
  shape bounds and the product's percentage range are out of scope (DEC-GSG-007).
- **No change to the secret patterns, the gitleaks path, `_SKIP_DIRS` or
  `.gitleaks.toml`**, and no filesystem walk in place of `git ls-files`
  (DEC-GSG-010). The two skip lists stay two; the docstring says so.
- **No workflow edit.** `release.yml` is pinned whole against a golden copy,
  and `ci.yml`'s step name for the guard, "No hard-coded thresholds in
  Makefile / workflow", stays true as far as it goes.
- **No `--root` or `--pyproject` argument on the coverage checkers**
  (DEC-GSG-012).
- **No hook change.** `.claude/hooks/nudge_rule_registry.sh`'s reminder globs
  stay as they are: the reminder is not the gate, and `make pre-pr` runs the
  guard over the widened set whatever file was edited. Of
  `.claude/agents/planlint-verifier.md`, only the sentence on what the guard
  skips changes, because it would otherwise be false (DEC-GSG-014).
- **Not before the 0.3.0 promotion, and not in this pull request.** This pull
  request carries the package and no code.

## Affected Capabilities

- `fail-closed-gate-scripts`
