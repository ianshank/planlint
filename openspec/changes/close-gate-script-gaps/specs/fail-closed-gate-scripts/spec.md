# Spec: Fail-Closed Gate Scripts

> **Change:** `close-gate-script-gaps`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Scripts under `tools/` gate this repository, and some of them answer "pass"
on an input they were added to catch, or could not read.

The threshold guard, `tools/check_no_hardcoded_thresholds.py`, enforces rule
G003 on this repository's own configuration, and it scans less than its
docstring claims. It reads the makefile and the workflow files, and nothing
else in the tree that carries a command line: not the composite action, the
adopter templates, the skill's template copy, the pre-commit files or the
`Dockerfile`. In the workflows it recognises only `fail-under`/`fail_under`
followed by `:` or `=`, and exact pins of `ruff`, `mypy` and `pytest`. A
single digit, a decimal, an upper-case variable, a space-separated flag, any
other named threshold flag, any other dev tool or operator, and a threshold
constant in `tools/` all pass. The docstring promises a "pinned path" check
that does not exist.

The shared reader, `tools/_common.py`'s `read_pyproject_int`, takes the
leading digits of whatever follows the key. A floor written as a fraction, or
with TOML's digit separator, is read as a smaller number, and the coverage
gates compare against that. The product's own reader of the same key is
anchored, reads the fraction, and refuses the rest.

The secret scan, `tools/check_secrets.py`, falls back to a Python scan over
`git ls-files` when gitleaks is absent, which is the case in the CI jobs that
run `make pre-pr`. When git cannot list the files, the list is empty and the
scan passes. A test locks that empty list in as the contract. A tracked file
whose name git quotes, or which cannot be read, is skipped, and a listing
whose every path is skipped passes as clean.

The coverage checkers, `check_coverage_floor.py` and
`check_branch_coverage.py`, read `pyproject.toml` from the working directory,
not from the tree whose report they judge. A directory with its own
`pyproject.toml` lends them its floor.

And a gate script that prints a non-ASCII path on an ASCII console raises
instead of printing it, so the verdict is a traceback.

The repository already has the rule these break. A report over nothing is not
a clean report (DEC-RDS-006), an empty tree is not a clean tree
(DEC-RDS-005), and a gate that cannot be shown to fail is a decoration
(`tests/AGENTS.md`). This spec makes each of them fail closed: a value a gate
cannot read exactly, or a set of files it cannot enumerate or scan, is exit
2, never a loosened pass. It widens the threshold guard to the files and
shapes its rule covers, in proportion and without a general parser.

**Evidence:** each finding was re-measured in session scratch at `bfbc124`
(`origin/dev`) on 2026-10-16, and the review's findings on 2026-10-17. The
commands and outputs are in `tasks.md` "Measured at `bfbc124`" and
"Re-checked at `bfbc124`, 2026-10-17 (the first review)"; the proposal
summarises them.

- **The guard's reach.** Planted roots, one shape each, were run through the
  current `main(argv, root)`. Only the control case failed. The first scratch
  prototype, whose word list was already the superset DEC-GSG-005 now
  adopts, failed every planted shape but a `coverage` pin, which no dev-extra
  name covers. The revised rules, rebuilt in scratch from R-GSG-3 and R-GSG-4
  with `coverage` declared, fail every planted shape, and over the real tree
  they report only the `Makefile`'s `NO_FLOOR := 0` sentinel.
- **The reader.** `read_pyproject_int` over planted values truncates a
  decimal, a digit-separated integer, a hexadecimal literal and a value with a
  trailing word to their leading digits. The line gate run against each
  truncated floor passes a report it should fail.
  `openspec_graph/thresholds.py`'s `_TOML_FAIL_UNDER` with
  `as_threshold_number` reads the decimal exactly and refuses the rest.
  `tomllib` returns the digit-separated, signed, hexadecimal and octal
  spellings and both quoted keys as a plain `int`.
- **The secret scan.** Each of these prints the fallback's PASS line over a
  planted AWS-shaped key:
  - git's "not a git repository" result, injected into the loaded script;
  - git's "dubious ownership" result, injected the same way;
  - git's octal-quoted spelling of a non-ASCII name;
  - a real repository whose only tracked path is under a skipped directory
    and absent from disk.

  The NUL-separated spelling names the file.
  `test_fallback_scan_returns_nothing_outside_a_git_repo` asserts the empty
  list, and no spec cites it.
- **The coverage checkers.** Each, run as a script from a directory whose own
  `pyproject.toml` declares a lower floor, passes a report that fails this
  repository's floor. A report written below its project root, as
  `out/coverage.json`, has no `pyproject.toml` in its own directory.
- **The console.** A FAIL line naming a non-ASCII path, from the guard and
  from the secret scan, is a `UnicodeEncodeError` traceback under
  `PYTHONIOENCODING=ascii`, with nothing on stdout.

---

## Requirements

- R-GSG-1: The threshold guard's `targets(root)` MUST select the makefile
  `resolve_makefile` finds, by GNU Make's search order, and every other file
  kind by pattern, never by a named file:
  - `.github/workflows/*.yml` and `*.yaml`;
  - `.github/actions/*/action.yml` and `action.yaml`;
  - `templates/*.yml` and `*.yaml`;
  - `skills/*/assets/*.yml` and `*.yaml`;
  - `.pre-commit-*.yaml` at the root;
  - `Dockerfile*` at the root.

  `targets(root)` MUST stay the one selection a test asserts on. The `tools/`
  modules R-GSG-5 reads are selected beside it, by `tools/*.py`.
- R-GSG-2: The guard's existing rules MUST be kept as they are, with their
  messages: the makefile's two-or-more-digit literal outside `$(...)`, the
  workflow's `fail-under`/`fail_under` floor, and the `ruff`, `mypy` and
  `pytest` exact pins. The floor and pin rules run over every target that is
  not the makefile, as `check_workflow` runs them over a workflow today.
  Every line the current guard reports on a tree MUST still be reported on
  that tree, before the whitelist. The makefile's whole-line comments and its
  `.PHONY` line stay unscanned by every rule. In every other target, comment
  lines stay scanned by R-GSG-2's rules, as the workflow rules scan them
  today.
- R-GSG-3: A named-threshold rule MUST run over every text target:
  - **The name.** A name token `[A-Za-z_][A-Za-z0-9_-]*` whose segments, split
    on `-` and `_`, include `min`, `max`, `minimum`, `maximum`, `floor`,
    `under`, `ratio` or `threshold`, or one of those words with a trailing
    `s`, compared case-insensitively and as whole segments.
  - **The excluded name.** `max-parallel`, the GitHub Actions `strategy` key,
    MUST NOT be reported. It is a runner-scheduling key, not a gate threshold
    (DEC-GSG-013).
  - **The separator.** `=`, `:`, `:=`, `::=`, `?=` or `+=`, each optionally
    spaced, with an optional closing quote before a `:` or an `=`
    (`["']?\s*[:=]`), as a quoted key writes it; whitespace alone; or the
    argument-list separator `["']?\s*,\s*`, which is an optional closing quote
    and a comma, optionally spaced, as a YAML flow list or a `Dockerfile` exec
    form writes an argv.
  - **The number.** An optional quote, then an integer or a decimal, not
    followed by a word character or a `.`.
  - **Comment lines.** The rule MUST skip whole-line comments in every
    target, as the makefile already skips them for every rule. It is the only
    rule that does so outside the makefile.

  In the makefile the rule MUST run on the line after the `$(...)` strip and
  the leading-`@` strip the literal rule uses. A number MUST be reported at
  most once per line, and where a rule of R-GSG-2 already reports it, with
  that rule's message and subject. Each finding MUST name the file, the line,
  the name and the number.
- R-GSG-4: A pin rule MUST run over every text target, the makefile
  included, on the lines R-GSG-2 scans: in the makefile after its comment,
  `.PHONY`, `$(...)` and leading-`@` handling, and in every other target on
  every line, comment lines included. Its names MUST be the distribution
  names of the `[project.optional-dependencies] dev` entries in the root's
  `pyproject.toml`, read at run time and normalised as PEP 503 normalises
  them (case-insensitive, runs of `-`, `_` and `.` equivalent). A name not
  preceded by a word character, `.` or `-`, optionally followed by an extras
  list in brackets, then optional whitespace, one of `===`, `==`, `!=`, `~=`,
  `<=`, `>=`, `<` or `>`, optional whitespace and a digit, MUST be reported.
  So MUST such a name followed, after any extras list, directly by `@`, with
  nothing required after it: the `uvx` and `pipx` version spelling
  `ruff@0.4.2` and a direct reference `ruff@git+https://...` (DEC-GSG-006).
  Whitespace around the `@` is allowed only when a URL scheme follows it
  (`git+`, `http://`, `https://` or `file:`), so the PEP 508 spelling
  `ruff @ git+https://...` is a pin too. In this `@` form a name directly
  after a `/` is not a pin, because `owner/name@ref` is an action or
  repository reference.
  A pin a rule of R-GSG-2 already reports MUST be reported once, with that
  rule's message and subject, so a `ruff==` pin is one finding. No name list
  beyond R-GSG-2's pattern MAY be written in the script. When the dev extra
  cannot be read — no `pyproject.toml`, no such table or key, or no entry —
  the guard MUST exit 2 naming what is missing.
- R-GSG-5: A constants rule MUST read every `tools/*.py` module with `ast`.
  It MUST report each module-level `Assign` or `AnnAssign`, tuple unpacking
  included, that binds a name whose `_`-separated segments include a word of
  R-GSG-3 to an `int` or `float` literal or its negation. A `bool` is not a
  number. A module that does not parse MUST be exit 2 naming it. Nothing below
  module level, and no file outside `tools/`, is read by this rule.
- R-GSG-6: Exemptions MUST live in `tools/threshold_whitelist.txt`, read
  only by the guard, and nowhere else: no inline marker, no `pyproject.toml`
  table.
  - **The file.** The guard MUST read `root / "tools/threshold_whitelist.txt"`
    under the root it scans, as `tools/dead_code.py` reads
    `root / WHITELIST`. A run over a planted tree reads that tree's
    whitelist, or none, and never this repository's.
  - **The format.** Blank lines and lines beginning `#` are skipped. Every
    other line is a root-relative POSIX path, whitespace, a subject, the
    separator `\s+#\s*` that `tools/dead_code.py`'s `_WHITELIST_LINE` uses,
    and a non-empty reason.
  - **The subject.** Every finding carries one, and its FAIL line MUST print
    it:
    - a named or constants finding: `NAME=VALUE`, the name and the number
      as written;
    - R-GSG-2's workflow floor: the `NAME=VALUE` the named rule gives the
      same number, the name without its leading dashes
      (`cov-fail-under=85`);
    - the makefile literal: the literal as written;
    - a pin, R-GSG-2's or R-GSG-4's: the name as written followed by the
      operator (`ruff==`, `ruff@`).
  - **Matching.** An entry suppresses every finding whose
    `path.relative_to(root).as_posix()` and subject equal its own, and no
    other. Every FAIL line MUST begin with that relative POSIX path, so an
    entry copied from a FAIL line printed on Windows matches.
  - **Workflows.** A finding in a file under `.github/workflows/` MUST NOT be
    whitelisted. It is moved, into a makefile recipe or a tool where the
    whitelist applies, or its line is reworded (R-GSG-9). The reason is a
    shipped test: `tests/test_release_surface.py`'s
    `test_every_workflow_is_scanned_by_the_threshold_guard` asserts that
    `check_workflow` returns nothing for each workflow before any whitelist,
    and `harden-release-pipeline`'s AC-HRP-23 requires it to pass unedited.
  - **Failures.** An entry that suppresses no finding MUST fail the guard as
    stale, naming the entry. A malformed line MUST be exit 2, naming the line.
  - **No file.** An absent whitelist is an empty one.
- R-GSG-7: The guard MUST exit 0 when nothing is reported, 1 on any finding
  or stale entry, and 2 when it cannot run. Cannot run means: a selected
  regular file that cannot be read or decoded as UTF-8, a `tools/` module that
  does not parse, an unreadable dev extra, or a malformed whitelist line. Each
  exit 2 MUST carry a message naming the file and never a traceback. A
  selected path that is not a regular file keeps today's reading: nothing to
  scan. `check_makefile(path)` and `check_workflow(path)` MUST keep their
  one-argument call shapes and return one file's findings before the
  whitelist, so the guards in other modules that call them keep working.
  Called with one argument, they MUST read the dev extra of the root
  `REPO_ROOT` names at call time, never a root bound into a signature
  default.
- R-GSG-8: The guard's docstring MUST state what it scans, by rule and by
  file kind, which rules read comment lines, and MUST name the whitelist. It
  MUST NOT claim a check the code does not make, and the "pinned path" claim
  MUST go. The PASS line MUST name the scanned kinds rather than "Makefile or
  workflow YAML".
- R-GSG-9: Every literal the widened guard reports on the tree when this
  lands MUST be resolved, and the guard MUST then exit 0 on the tree:
  - a threshold this repository enforces moves to `pyproject.toml`, read by
    a script;
  - any other literal outside `.github/workflows/` is whitelisted with its
    reason;
  - any other literal in a workflow moves into a makefile recipe or a tool,
    or its line is reworded to a spelling that states no bound by name, with
    the reason recorded in `tasks.md` (R-GSG-6).

  The same tree with the whitelist withheld MUST exit 1, so no entry is
  decorative. No threshold's name, flag or constant MAY be renamed so as to
  fall outside a rule.
- R-GSG-10: The dev extra MUST gain a bare `coverage` entry, under a comment
  saying that the coverage-run recipe invokes `python -m coverage` directly
  and that the pin rule takes its names from this list. `[project]
  dependencies` MUST stay empty, and no other dev-extra entry MAY change.
- R-GSG-11: `read_pyproject_int` MUST read the key written bare, followed by
  `=`, a value of ASCII digits only and an optional trailing `#` comment,
  matched to the end of the line. It MUST return `None` only when the file,
  the table or the key is absent, presence being decided as
  `has_pyproject_key` decides it, which also recognises a quoted spelling of
  the key. When the key is present in any other shape — quoted, or with a
  value not of that form — it MUST raise a `ReportError` subclass whose
  message names the file, the table, the key and the value as written. It
  MUST NOT return a truncated or partial integer. It MUST stay stdlib-only.
- R-GSG-12: Every caller of `read_pyproject_int` under `tools/` MUST turn
  that refusal into exit 2, with the reader's message on stderr, nothing on
  stdout that states a verdict, and no traceback:
  - `check_coverage_floor.py`, in its gate mode and its per-file mode;
  - `check_branch_coverage.py`;
  - `dead_code.py`;
  - `matcher_accuracy.py`.
- R-GSG-13: For every `fail_under` line whose value lies inside the
  product's range, `openspec_graph/thresholds.py`'s `THRESHOLD_MIN` to
  `THRESHOLD_MAX`, the tools reader MUST never disagree with the product's
  reader: either `read_pyproject_int` refuses it, or it returns the number
  that `_TOML_FAIL_UNDER` and `as_threshold_number` read from it. Outside
  that range the two differ, and the outcome is recorded rather than
  forbidden: the tools reader reads `101` as 101, a floor no coverage can
  meet, so the line checker fails closed with exit 1, while the product
  refuses the value. A test MUST hold both over a planted corpus that
  includes a decimal, a digit-separated integer, a sign, a hexadecimal
  literal, an octal literal, an exponent, a quoted value, a quoted key, a
  trailing word, and `101` with its recorded outcome.
- R-GSG-14: `read_pyproject_int`'s docstring, and the docstring of the
  dev-extra reader `dev_extra_names`, MUST each say:
  - that the scanner was chosen under the 3.10 floor, and that replacing it
    with `tomllib` is `docs/next-steps.md` item 7a's change;
  - that the reader's type refusals carry forward to item 7a's `tomllib`
    reader, which sees a float, an exponent or a string as a `float` or a
    `str` and still refuses it, so those tests are kept;
  - that the spellings `tomllib` normalises to a plain value are a decision
    item 7a records, and that item 7a replaces this package's tests of those
    spellings rather than keeping them. For `read_pyproject_int` these are
    `9_5`, `+97`, `0x61`, `0o141` and a quoted key, and with them `-1`,
    which `tomllib` returns as a negative integer (DEC-GSG-002).

  Neither docstring MAY claim that `tomllib` is missing on a supported
  interpreter. Each is then true before and after `prepare-release-0-4-0`'s
  R-RFR-7.
- R-GSG-15: The secret scan's fallback MUST enumerate files with `git
  ls-files -z`, reading bytes, decoding them as UTF-8 with no error handler,
  and splitting on NUL.
- R-GSG-16: When the fallback runs, it MUST exit 2, with a message on stderr
  naming the cause, no PASS line and no traceback, when:
  - git cannot be started;
  - git exits non-zero, the message carrying git's stderr;
  - git's output is not UTF-8;
  - no file is scanned: git lists none, or every listed path is absent from
    disk, not a regular file, or under a skipped directory. The count is of
    files read, never of files listed;
  - a listed path is a regular file that cannot be read.
- R-GSG-17: A listed path absent from disk, or not a regular file, MUST be
  skipped as today, with a DEBUG record, and counts as not scanned. File
  contents MUST still be read with undecodable bytes ignored. The token
  patterns, `_SKIP_DIRS`, `run_gitleaks` and the gitleaks branch of `main`
  MUST be unchanged.
- R-GSG-18: `tools/check_secrets.py`'s module docstring MUST describe the
  two skip lists as two, in place of its claim that the fallback honours
  `.gitleaks.toml`'s allowlist of `tests/` fixtures:
  - `_SKIP_DIRS`, which the fallback applies, and `.gitleaks.toml`'s
    allowlist, which gitleaks applies;
  - the fallback alone skips `venv`, `__pycache__`, `.ruff_cache` and
    `.mypy_cache`;
  - both skip only vendored and generated trees, and both scan `tests/` on
    purpose.

  It MUST also state R-GSG-16's refusals.
- R-GSG-19: `check_coverage_floor.py`, in both modes, and
  `check_branch_coverage.py` MUST first confirm that the coverage report
  exists, exiting 2 with their "coverage file not found" message when it
  does not, and only then look for the configuration. They MUST read the
  nearest `pyproject.toml` at or above the report's resolved directory: that
  directory, then each parent in turn, the first found winning, whether the
  report path is given or is the default. They MUST NOT take the working
  directory's `pyproject.toml` as such. Every message that names the
  configuration MUST name the file found. When the walk ends at the
  filesystem root with no `pyproject.toml`, they MUST exit 2 with a message
  naming the walk: the directory it started from, and that no
  `pyproject.toml` was found at or above it. Their argv MUST be unchanged.
- R-GSG-20: `test_fallback_scan_returns_nothing_outside_a_git_repo` MUST be
  deleted, not renamed and not inverted. Tests of R-GSG-16's refusals take
  its place. Every existing test a shipped spec cites MUST keep its name and
  every property it asserts. Where a cited test's planted tree must carry a
  `pyproject.toml` for R-GSG-4, the change MUST be made in the shared
  `_guard_tree` helper and nowhere else. `test_threshold_guard_scans_every_workflow`
  MUST judge each target after the whitelist and assert that no entry is
  stale. Its name and every other assertion are kept.
  `test_every_workflow_is_scanned_by_the_threshold_guard` MUST pass unedited.
- R-GSG-21: Every check this spec adds MUST be shown failing on a planted
  input, and its test MUST be written and run red against the unmodified
  scripts before the change that makes it pass. The red run is recorded in
  `tasks.md` and never committed. DEC-GSG-013 lists the planted inputs.
- R-GSG-22: Every new test MUST carry the tier `tests/shape_support.py`'s
  criterion computes, every edited test module MUST stay within
  `MAX_TEST_MODULE_LINES`, every new public function MUST carry a docstring,
  and a docstring ceiling in `tests/test_static_ratchets.py` MUST move only
  down, in the commit that lowers its count.
- R-GSG-23: The documents MUST say what the guard and the changed scripts now
  do. These are:
  - the thresholds target's help text in the `Makefile`, with its recipe
    unchanged and no number in the text;
  - `README.md`'s gates-table row for that target and its paragraph that
    says no numeric threshold lives in the Makefile or CI YAML;
  - `docs/hooks.md`'s commit-hook line for that target and its note on the
    workflows it scans;
  - `docs/aqa.md`'s paragraph on what is externalised, and its Gates-table
    row for the security target, which names exit 1 alone and gains the
    fallback's exit 2;
  - `tools/AGENTS.md`'s bullet on hard-coded thresholds, which MUST name
    `tools/threshold_whitelist.txt`, its reason rule, and that a workflow
    line is never whitelisted. The file MUST stay within `MAX_NESTED_LINES`,
    with its precedence clause and its links resolving;
  - `tools/_common.py`'s `resolve_makefile` docstring, whose sentence that
    `check_makefile` tolerates a path it cannot open becomes true only of a
    path that is not a regular file;
  - `tests/support.py`'s `run_tool_main` docstring, whose sentence "These
    scripts read `Path("pyproject.toml")` from the cwd" becomes R-GSG-19's
    walk;
  - `.claude/agents/planlint-verifier.md`'s sentence that the guard
    "allowlists comments", which becomes which rules skip whole-line
    comments and which read them. The rest of that line stays.

  `CHANGELOG.md`'s `[Unreleased]` section MUST gain a `### Fixed` entry led by
  this package's bold backticked name, naming each script this package
  changes and what each now refuses.
- R-GSG-24: Every script this package changes MUST print a non-ASCII path on
  an ASCII console without raising:
  - the guard, the secret scan, both coverage checkers, `dead_code.py` and
    `matcher_accuracy.py`.

  Each `main` MUST first reconfigure `sys.stdout` and `sys.stderr` to UTF-8
  with `errors="backslashreplace"`, each call under
  `contextlib.suppress(ValueError, OSError)`, through one shared helper in
  `tools/_common.py`. This is the mechanism `fix-stdout-encoding-crash` gave
  `openspec_graph/cli.py`'s `main` (R-SE-1, R-SE-3, DEC-SE-004). A FAIL line
  or an exit-2 message naming a non-ASCII path MUST then be written as
  UTF-8, whatever the console's encoding, with the script's own exit code and
  no traceback (DEC-GSG-015).
- C-GSG-1: No file under `openspec_graph/` MAY change, and neither MAY the
  `RULES` tuple, `README.md`'s rules table, `tests/baseline_rules.json`, any
  golden hash, the CLI's verbs or `[project] dependencies`.
- C-GSG-2: No file under `.github/` MAY change, no `make` target MAY be added
  or removed, and no recipe line MAY change. The `Makefile`'s only edit is
  R-GSG-23's help text.
- C-GSG-3: The change MUST add no parser library, no dependency beyond
  R-GSG-10's, and no `tomllib` or `tomli` import under `tools/`.
  `tools/_common.py` and every script this package changes MUST stay
  stdlib-only.
- C-GSG-4: This spec MUST NOT pin a count or a line number — of findings,
  entries, files, tests, specs or packages. Every measurement belongs in
  `tasks.md`, dated with its commit and naming its command.
- C-GSG-5: No file of another change package MAY change, its `Status` header
  included.
- C-GSG-6: Every coverage floor MUST stay where it is and hold at every
  milestone, `tools/`'s included. No per-file exemption, `noqa`, mypy ignore
  or waiver MAY be added. `make pre-pr` MUST be green at the end.
- C-GSG-7: This package MUST land in `dev` alone, in a pull request carrying
  no code, after the 0.3.0 promotion is done. The implementation MUST be a
  separate pull request from `dev`, opened as a GitHub draft and marked ready
  only after `tasks.md` Milestone 0's gate is recorded.

---

## Decisions

- **DEC-GSG-001:** a dev-side package, package-first, in 0.4.0, in this order.
  It changes no shipped behaviour, so its record and its code can land
  separately without an adopter seeing a half-state. Package-first is the
  shape `lean-production-tree` (#58) and `prepare-release-0-4-0` (#60) took:
  the plan is reviewable in `dev` before any code depends on it. The order:
  1. The 0.3.0 promotion completes: `v0.3.0` tagged and published, and its
     record merged into `dev`. Until then this package's pull request is held,
     so nothing new reaches the 0.3.0 tree.
  2. This package alone into `dev`.
  3. Its implementation, a new pull request from `dev`, a draft until
     Milestone 0's gate is recorded. It must merge before
     `prepare-release-0-4-0`'s pull request 2, the release prep, is cut, or
     it misses 0.4.0. It is expected to merge before that package's pull
     request 1, which waits on `lean-production-tree`'s implementation and
     rewords `read_pyproject_int`'s docstring. This package writes that
     docstring in the shape R-RFR-7 asks for (R-GSG-14), so that reword finds
     nothing to change at that site. If pull request 1 merges first, this
     implementation rebases onto it and keeps its wording. No order is
     required against the implementations of `lean-production-tree`,
     `harden-release-pipeline`, `tighten-release-surface` or
     `raise-coding-standards`. Whichever lands second re-reads the shared
     sites the proposal names, at its own head.
  4. Later, item 7a's `tomllib` package. It keeps this package's
     type-refusal tests, and it replaces the tests of the spellings `tomllib`
     normalises, recording its own decision on them (DEC-GSG-002).

  If this package is in `dev` when `lean-production-tree`'s Milestone 2 lists
  the packages added since `c0ff090`, that package classifies it by its own
  evidence. It has not shipped, so it is kept (R-LPT-2). This package edits
  nothing of that one's (C-GSG-5).
- **DEC-GSG-002:** anchor the regular expression now; do not wait for
  `tomllib`. The premise handed to this draft was that
  `prepare-release-0-4-0` replaces the hand-written readers with `tomllib`
  once 3.10 is dropped. Read in full, it does the opposite:
  - its C-RFR-1 says no hand-rolled TOML scanner may be replaced, the
    `tools/_common.py` readers named among them;
  - its DEC-RFR-004 rejects the swap as "item 7a's own package, with its own
    tests";
  - its R-RFR-7 only rewords the docstrings that claim `tomllib` is missing.

  So the swap has no package, no branch and no date. Meanwhile the
  truncation is live on every leg, 3.10 included, where `tomllib` does not
  exist. Waiting would tie a gate defect to an unscheduled change. Anchoring
  is one pattern and a refusal path, stdlib-only, and correct on every
  interpreter in the matrix today.

  What carries forward to item 7a is part of the contract, not the regular
  expression, and the docstrings say which part (R-GSG-14):
  - **The type refusals carry forward.** `tomllib` returns `97.5` and `97e0`
    as a `float` and `"97"` as a `str`. An integer reader over its result
    still refuses each, so those cases of R-GSG-11's test are kept as they
    are.
  - **The normalised spellings do not.** `tomllib` returns `9_5` as 95, and
    `+97`, `0x61`, `0o141` and both quoted keys as 97, a plain `int` no
    different from the bare spelling. No reader over `tomllib`'s result can
    refuse them. Which of them item 7a accepts is a decision that package
    records, and it replaces this package's tests of those spellings, in
    R-GSG-11's test and in R-GSG-13's corpus, rather than keeping them. The
    product's reader refuses each of them, so the decision item 7a records
    covers R-GSG-13's corpus too.
  - **`-1` goes with them.** `tomllib` returns it as the integer -1, where
    this package's reader refuses it as a sign. An integer reader that
    accepted it would set a floor every report meets, so item 7a records it
    beside the normalised spellings.

  Rejected:
  - depending on `prepare-release-0-4-0`, which does not do the swap;
  - doing the swap here, which C-GSG-3 forbids and which would break the
    3.10 leg until pull request 1 merges.
- **DEC-GSG-003:** the reader reads an exact decimal integer or refuses, by
  raising. The choices:
  - **Integers only.** Every caller under `tools/` takes an `int`. The
    coverage floors are compared and printed as whole numbers, vulture's
    `--min-confidence` takes an integer, and the matcher floors are integer
    percentages by their own comment. This repository writes every one as an
    integer. Reading a fraction would change the type in every caller and
    every message, for a value this tree does not hold. Refusing it is loud
    and costs nothing today. The product accepts a fraction because adopters
    write them; these scripts read only this repository. A later package may
    widen the reader to the product's grammar, and R-GSG-13 then still holds.
  - **The product's integer grammar.** ASCII digits only, so `9_5` is
    refused, as the product refuses `1_000`. TOML reads it as 95, but the two
    readers then cannot disagree.
  - **No range in the reader.** The product refuses a value outside
    `THRESHOLD_MIN` to `THRESHOLD_MAX`; this reader does not. A digits-only
    value cannot fall below the range. Above it, `101` is a floor no report
    can meet, so the line checker fails every report against it with exit 1,
    which is closed. A range in the reader would be a second copy of the
    product's. So R-GSG-13 forbids disagreement inside the range and records
    the outcome above it.
  - **Raise, not `None`.** `None` already means "absent", and every caller
    turns it into a message saying no floor is set. That message would be
    false for a floor that is set and unreadable, and a caller that forgot the
    distinction would fail closed only by luck. A `ReportError` subclass names
    the value. `dead_code.py` already maps `ReportError` to exit 2, and the
    other callers gain one branch each (R-GSG-12).

  A quoted spelling of the key is refused, not read, though
  `has_pyproject_key` counts it as present. The product's anchored pattern
  reads only the bare key, and reading a floor it does not would be the
  disagreement R-GSG-13 forbids. Today that spelling reads as absent and the
  gate says no floor is set. It will now say a floor is set in a shape the
  gate does not read.
- **DEC-GSG-004:** the guard's files. Each pattern added is a file kind that
  carries a command line or a configuration value, which a threshold or a
  pin can be written into:
  - `.github/actions/*/action.yml`: the composite action's `run:` steps;
  - `templates/*.yml` and the skill's `assets/*.yml`: the workflow adopters
    copy, so a floor pinned there ships to every adopter;
  - `.pre-commit-*.yaml`: `.pre-commit-config.yaml` and
    `.pre-commit-hooks.yaml` both carry `entry:` command lines, the second
    being the adopter-facing one;
  - `Dockerfile*`: `RUN` lines, of the root `Dockerfile` and of any variant
    added beside it.

  Each is selected by pattern because the guard's first bug was a named file
  (R-SD-10), and a lone `Dockerfile` would be the same bug one variant away.
  The makefile alone is found by name, in GNU Make's order, because that is
  the one file `make` reads (`fix-makefile-discovery-names`).
  `.github/dependabot.yml` is not added: it carries update policy, not
  commands or thresholds, and its numbers are Dependabot's own settings.
  Fixtures under `tests/` are not added: they are labelled input that plants
  violations on purpose. `release.yml` stays scanned and is not edited
  (C-GSG-2).
- **DEC-GSG-005:** the named-threshold rule, as R-GSG-3 states it. Its
  parts:
  - **A rule by name.** A number after a name that says it is a bound is the
    shape every missed case shares: `--cov-fail-under 90`, `COV_FAIL_UNDER:
    90`, `--per-file-min 85`, `fail_under: 97.5`, `NO_FLOOR := 0`.
  - **Every number after that name**, so single digits and decimals count.
    The makefile literal rule still catches bare numbers of two or more
    digits in recipes.
  - **Whole segments.** `timeout-minutes: 15` must stay quiet, and so must
    every `timeout-minutes` line in the workflows, which
    `test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency` holds.
    A substring match on `min` would flag all of them.
  - **The separators** include Make's assignment operators. The prototype
    without them missed `NO_FLOOR := 0`, the literal it then found on the
    tree. They include the argument-list separator, so that
    `args: [--cov-fail-under, "90"]` in a pre-commit file and
    `RUN ["pytest", "--cov-fail-under", "90"]` in a `Dockerfile` are caught.
    Neither is caught without it.
    They admit a closing quote before a `:` or an `=`, so a quoted key such
    as `"fail_under": 90` is caught. The legitimate keys stay quiet in their
    quoted spelling too: `timeout-minutes`, `fetch-depth`, `python-version`,
    `retention-days` and `open-pull-requests-limit` carry no word of the
    list as a whole segment, and `max-parallel` is excluded by name.
  - **Case-insensitive**, for environment variables.
  - **The word list.** `min`, `max`, `minimum`, `maximum`, `floor`, `under`,
    `ratio` and `threshold`, each also with a trailing `s`, so
    `--minimum 90`, `COVERAGE_FLOORS: 90` and `--thresholds=3` are caught.
    This is the superset the drafting prototype already used. The first
    draft's narrower list, which missed each of those, misdescribed it. Over
    the real tree the superset finds what the narrower list found. Adding a
    word is a one-line change with its own planted case.
  - **Comment lines.** The named rule skips whole-line comments in every
    target, as the makefile already skips them. A comment in a template or a
    workflow is prose, such as "finishes in under 5 minutes" or "the floor
    97", and the rule would flag it by name. R-GSG-2's rules and the pin rule
    still read comment lines outside the makefile, so R-GSG-2's superset
    holds, and a pin written in a comment is still a finding.
  - **`max-*` flags of other tools are flagged.** `--max-count=1`,
    `--max-time 30`, `--retry-max-time 60` and
    `--hypothesis-max-examples=200` each put a number after a `max` segment,
    and the rule cannot tell a tool's own bound from a gate's. None is on the
    tree. Outside the workflows such a flag is whitelisted with its reason.
    In a workflow it is moved or reworded (R-GSG-6, R-GSG-9).
  - **Accepted misses**, each beyond a line rule by name:
    - `${FLOOR:-90}`: the number is a shell default inside a parameter
      expansion. Attributing it to the name inside the braces is shell
      parsing, and `:-` introduces every other default as well.
    - `${{ inputs.floor || 90 }}`: the number is the fallback of a GitHub
      expression. Reading `||` as a separator is an expression parser.
    - A pre-commit `rev:` pin: a `rev:` names a git ref of a hook repository,
      not a PEP 440 pin of a dev-extra name. This repository's
      `.pre-commit-config.yaml` holds only `repo: local` hooks, which call
      the targets and carry no `rev:`.
    - A name with no word of the list, such as `COVERAGE: 90` or
      `COV ?= 9`: a rule by name cannot see a threshold behind a neutral
      name. It is the same class as the neutral-named anchor and `env:`
      value the review already called inherent to a rule by name. In the
      makefile the literal rule still catches such a number of two or more
      digits.
  - **An accepted false positive.** An address such as `pytest@example.org`
    in a comment is a pin finding, because the pin rule reads comment lines
    outside the makefile by design. The remedy is to reword the line; the
    rule is not narrowed for it, and no such line is on the tree.

  Rejected:
  - every number on every non-makefile line, which flags Python versions,
    timeouts, `fetch-depth: 0` and SHA pins, whose quiet the cited tests hold;
  - a YAML or shell parser, which this package was told not to build.
- **DEC-GSG-006:** the pin rule takes its names from the dev extra, with
  every PEP 440 operator, and `coverage` joins the extra. The extra is this
  repository's one statement of which development tools CI installs, with
  two exceptions that are outside it by their own mechanism:
  - `[build-system] requires`, the setuptools floor, which the build
    frontend installs in its own isolated environment;
  - `pip`, which each workflow's install step upgrades, unpinned.

  Neither is a dev-extra name, so the pin rule does not see a pin of either.
  A name list in the script would be a second copy of the extra, and
  dropping `tomli` from the extra, as `prepare-release-0-4-0` does, would
  leave it stale. `>=` and `~=` are pins for this rule's purpose: each is a
  version decision written outside the extra, which
  `test_dependabot_does_not_add_a_pip_ecosystem` says the repository
  declines to maintain. `coverage` is not in the extra, so a rule built from
  it cannot see `coverage==`. Yet the `coverage-run` recipe invokes
  `python -m coverage` directly, and `[tool.coverage.run]` depends on
  coverage's own subprocess hook. It is a direct dependency that the extra
  leaves to `pytest-cov`'s requirements. Declaring it, bare and unpinned like
  the rest, is a true statement that also brings it under the rule. It
  changes no install: `pytest-cov` already requires it. The digit after the
  operator keeps a shell redirection, such as `ruff check . > out.txt`, quiet.

  `@` after a dev-extra name is a pin too. `uvx ruff@0.4.2` and
  `pipx run ruff@0.4.2` choose a version outside the extra, and
  `ruff@git+https://...` chooses a source, which is the same decision. No
  digit is required after the `@`, because a direct reference begins with a
  scheme. PEP 508 allows whitespace around that `@`, so whitespace is
  allowed where a URL scheme follows it, and only there, which keeps prose
  such as `ruff @ noon` quiet. A name directly after a `/` is not a pin in
  this form: `owner/name@ref` is an action or repository reference, and a
  workflow's `uses:` line cannot be whitelisted (R-GSG-6). The rule keys on
  dev-extra names, so the `@` of every SHA-pinned `uses:` line, of the
  `Dockerfile`'s digest and of a makefile's recipe-echo prefix is quiet. On
  the tree no dev-extra name stands directly before an `@`, and no `uses:`
  line has a finding (`tasks.md`).

  Rejected:
  - a hand list in the script;
  - names harvested from the makefile's `python -m` invocations, a second
    derivation of the same fact;
  - leaving `coverage==` unseen;
  - a floor on `coverage`, which nothing measured here justifies (contrast
    DEC-RDS-001, which measured one).
- **DEC-GSG-007:** the constants rule reads `tools/*.py` with `ast`, at
  module level only. `tools/AGENTS.md` says a threshold belongs in
  `pyproject.toml` and the guard "fails the build over it". Until now that was
  true only of the makefile and the workflows. `ast` sees bindings and nothing
  else, so a docstring or a string literal that mentions `floor = 90` is not a
  binding. Module level is where a constant lives. A default argument or an
  inline comparison is code, which review reads. `tests/` is not read: its
  bounds — the test-module line bound, the nested-agents line bound — are the
  suite's own assertions about itself. `openspec_graph/` is not read: its
  percentage range is the product's definition of a percentage, not a gate
  threshold. On the drafting tree the rule reports nothing, with the widened
  word list too. Its value is the next constant, and its planted case shows
  it fires.
- **DEC-GSG-008:** the whitelist is `tools/threshold_whitelist.txt`, keyed
  by path and subject. The shape is `tools/dead_code_whitelist.txt`'s, which
  DEC-RDS-004 chose: a text file read by one script, one entry per line, each
  with its reason, and not a `.py` file that coverage, mypy and ruff would
  read.
  - **Read under the scanned root, with `dead_code.py`'s separator.** The
    path is `root / "tools/threshold_whitelist.txt"`, so the planted trees of
    the suite never read this repository's entries and fail for their own
    findings only. The separator is `\s+#\s*`, so one whitelist grammar
    serves both files.
  - **Not inline markers.** The `Dockerfile` cannot carry a trailing comment,
    as its own header says; a `#` after an instruction is an argument. A `#`
    on a makefile recipe line is handed to the shell. And a marker beside a
    number is a waiver at the site, where a reviewer reads past it.
  - **Not a `pyproject.toml` table.** It would need a hand-rolled reader of
    quoted keys, and it would put exemptions inside the file whose purpose
    is to hold the thresholds themselves.
  - **Keyed by path and subject, never by line number.** The path is the
    root-relative POSIX form, which the FAIL line also prints, so an entry
    reads the same on every platform. An unrelated edit above the line does
    not stale the entry, while a changed value or a copy into another file is
    a new finding that needs its own reason.
  - **A stale entry fails the guard.** The guard is deterministic, so unlike
    vulture's whitelist there is no release that could make staleness flaky.
    An exemption that exempts nothing would otherwise outlive its reason.
  - **Never for a workflow.** `check_workflow` is judged before the
    whitelist by `test_every_workflow_is_scanned_by_the_threshold_guard`,
    which `harden-release-pipeline` AC-HRP-23 holds unedited. An entry for a
    workflow line would leave that test red, so the rule is stated rather than
    discovered (R-GSG-6).
- **DEC-GSG-009:** the disposition of each literal the widened guard reports
  on the tree. At drafting it reports `Makefile NO_FLOOR=0` (`tasks.md`). It
  is whitelisted, with the reason the `Makefile`'s own comment gives. It
  turns pytest-cov's own floor off on the one `coverage-run`, because that
  floor would read the diluted total of both trees, and the scoped checkers
  then gate each tree against the real floors in `pyproject.toml`. It is not
  a threshold this repository enforces; it is the switch that hands
  enforcement to the gate that reads config.
  - Moving it to `pyproject.toml` would present a zero as a floor.
  - Renaming it to dodge the rule would make the finding disappear without
    changing the fact, which `AGENTS.md` forbids (R-GSG-9).

  Milestone 0 rebuilds the patterns from R-GSG-3 and R-GSG-4, since the
  drafting scratch scripts are not committed, and re-runs them at the
  implementation head, after any sibling has landed. Each further hit is
  decided by R-GSG-9's test. A hit in a workflow is never whitelisted. If
  the change that added it has not landed, that change moves or rewords it.
  If it has landed, this package cannot (C-GSG-2), so the implementation
  stops and the package is amended by a recorded decision before it goes on.
- **DEC-GSG-010:** the fallback enumerates with `git ls-files -z`, decoded
  as strict UTF-8, and refuses rather than passes.
  - **`-z`.** Git turns off path quoting under `-z`, so a non-ASCII name
    arrives as its UTF-8 bytes. NUL cannot occur in a path, so the split is
    exact. `core.quotePath=false` with a newline split was rejected: a name
    can contain a newline.
  - **Bytes, then UTF-8.** Git writes paths in UTF-8. `text=True` would
    decode with the locale's preferred encoding, which on Windows need not be
    UTF-8.
  - **No error handler.** A name that does not decode is a file the scan
    cannot be sure it opens, so it is exit 2 rather than a
    `surrogateescape` guess.
  - **No file scanned is exit 2**, for DEC-RDS-005's reason: a scan over
    nothing is not a clean scan. The count is of files read, after the
    absent, non-regular and skipped paths are dropped. A listing whose every
    path is skipped scans nothing, however long it is.
  - **An unreadable tracked file is exit 2**, where today it is skipped
    silently. A missing or non-regular path is still skipped, because there
    is nothing on disk to scan.

  The fallback is a CI gate on the release path: `make pre-pr` runs it in
  `release-tier` and in `release.yml`'s `gate`, where no gitleaks binary is
  installed. A false PASS there reaches a release.

  Rejected:
  - a filesystem walk when git fails, which scans untracked and ignored
    files, a different set from "committed";
  - warning and passing, which is the current behaviour with a message added.
- **DEC-GSG-011:** `test_fallback_scan_returns_nothing_outside_a_git_repo`
  is deleted and replaced, not renamed. It asserts the fail-open behaviour as
  the contract ("`_tracked_files` returns [] -- no crash"), and no spec cites
  it. A kept name asserting the opposite would mislead anyone reading the
  history of the test. Its replacements are named for what they hold:
  - a refusal test parametrised over the causes:
    - a real directory with no `.git`, with `GIT_CEILING_DIRECTORIES` set to
      its `tmp_path`'s parent, so git does not walk up into an enclosing
      repository, as it would under a `--basetemp` inside a checkout;
    - git's non-zero exit injected with the dubious-ownership message;
    - git absent from `PATH` injected as `FileNotFoundError`;
  - a test of undecodable output and of a listing with nothing to scan:
    empty, or every listed path absent or under a skipped directory;
  - a test of an unreadable tracked file, injected as `PermissionError`, as
    `tests/test_stage_citations.py` injects one, because as root a mode of
    000 still reads;
  - an e2e test that commits a non-ASCII name through `_git_repo` and finds
    its planted key.

  The first three run `main` in-process and are `integration`: the git
  process is started by the code under test, not by the test (DEC-TSS-017).
  `test_secret_scan_clean_repo_passes` stays as it is. On a checkout git can
  list it passes, and where git cannot list the checkout it now exits 2,
  which is the behaviour this package asks for.
- **DEC-GSG-012:** the coverage checkers read the nearest `pyproject.toml` at
  or above their report: the report's directory first, then each parent,
  the first found winning. Not the working directory's, and not
  `repo_root()`'s.
  - **Why the walk.** A report is written inside the tree it measures, at
    the tree's root or below it. `coverage-run` writes `coverage.json` at the
    root, and an adopter-shaped run may write `out/coverage.json`. The
    nearest configuration at or above the report is that tree's. `--scope`
    already matches the report's paths as relative to that tree's root.
  - **Nothing changes where the call is right.** For `make test` the report
    sits in the working directory beside the root `pyproject.toml`, which
    the walk finds at its first step. So does every planted tree in
    `tests/test_coverage_checkers.py`, which passes `coverage.json` with its
    tree as the working directory. `check_coverage_floor.py
    out/coverage.json` from a project root keeps working, as it does today.
  - **What changes.** A checker invoked from elsewhere with this repository's
    report now applies this repository's floors. A report with no
    `pyproject.toml` at or above it exits 2 with a message naming where the
    walk started, as a working directory without one exits 2 today.
  - **The report first.** The checkers confirm the report exists before they
    look for configuration, so a missing report is named as missing. Today a
    missing report in a directory with no `pyproject.toml` reports "no line
    floor set", which sends the reader to the wrong file.

  Rejected:
  - the report's own directory alone, which the first draft chose. It made
    `check_coverage_floor.py out/coverage.json` from the project root exit 2,
    a call that works today (measured).
  - `repo_root()`, which the review suggested. The tests in
    `tests/test_coverage_checkers.py` that plant a tree as their working
    directory would silently read the real floors, and some would pass for
    the wrong reason: a half-covered planted report fails the real floors as
    surely as the planted ones. The checkers would also lose the planted-tree
    testing that `read_pyproject_int`'s and `run_tool_main`'s docstrings
    describe.
  - The working directory, which is the defect.
  - A `--pyproject` or `--root` flag, which is a second way to say where the
    tree is, inside a hand-rolled argv parser that both scripts share.
- **DEC-GSG-013:** how each check is shown failing. Every planted input
  goes through the script's `main`, the path the thresholds target and
  `make pre-pr` run, and the test is red on the unmodified script first. The
  planted inputs:
  - **The guard, loud.** One case per widened shape, each with a
    `Makefile`, a `ci.yml` and a `pyproject.toml` holding a dev extra, exiting
    1 with its file and subject named:
    - a single digit and a decimal in the makefile;
    - in a workflow: an upper-case environment variable, a space-separated
      flag, `--per-file-min`, and a `max`, a `ratio` and a `threshold` flag;
    - `--minimum 90`, `COVERAGE_FLOORS: 90` and `--thresholds=3`;
    - `args: [--cov-fail-under, "90"]` in a pre-commit file and
      `RUN ["pytest", "--cov-fail-under", "90"]` in a `Dockerfile`;
    - a `coverage`, a `pytest-cov`, a `>=`, a `~=` and an extras-bracketed
      pin, and a `ruff==` pin reported once;
    - `"fail_under": 90`, a quoted key;
    - `uvx ruff@0.4.2 check .`, `pip install ruff@git+https://x` and
      `pip install 'ruff @ git+https://x'`, each an `@` pin;
    - a pin written in a workflow comment;
    - a floor in each added file kind;
    - a constant in `tools/`.

    A dev-extra name planted only in the fixture's `pyproject.toml` is caught
    when pinned, which shows the names are read, not written.
  - **The guard, flagged by design.** `--max-count=1` and
    `--hypothesis-max-examples=200` in a composite action each fail, and each
    passes once whitelisted with its reason.
  - **The guard, quiet.** One planted tree holding every shape the rule must
    not flag exits 0. Among them:
    - the GitHub schema keys `timeout-minutes: 15` and `max-parallel: 4`. The
      second is a runner-scheduling key, not a gate threshold, and is quiet
      only because R-GSG-3 excludes it;
    - comment prose naming a bound, such as `# the job finishes in under 5
      minutes`;
    - `pytest --maxfail=1`, whose segment is `maxfail`, not `max`;
    - `timeout-minutes`, `fetch-depth`, `python-version`, `retention-days`,
      `open-pull-requests-limit` and `max-parallel`, each also written as a
      quoted key;
    - `uses: someorg/build@v1`, an action reference whose repository is
      named after a dev-extra name;
    - Python version strings, `fetch-depth: 0`, a SHA-pinned `uses:` line, a
      `$(...)` expansion, a `run:` of the test target, `pip install -e
      ".[dev]"`, `python -m build`, a shell redirection after a tool name and
      the `Dockerfile`'s digest-pinned `FROM`.
  - **The guard, cannot run.** Each exit-2 input of R-GSG-7: no dev extra, a
    malformed whitelist line, an unreadable target (injected), an
    undecodable target, and an unparsable `tools/` module.
  - **The whitelist.** An entry suppresses its finding and no other; a stale
    entry fails; a planted tree does not read this repository's whitelist.
  - **The real tree.** It passes with its whitelist, and fails naming
    `NO_FLOOR` with the whitelist withheld.
  - **The reader.** Each malformed value or quoted key refused with key and
    value named; the agreement corpus of R-GSG-13, `101` and its outcome
    included; each caller of R-GSG-12 exiting 2 on a planted fractional floor
    where it passed before.
  - **The secret scan.** DEC-GSG-011's tests.
  - **The coverage checkers.** A report and a `pyproject.toml` in one tree,
    a `pyproject.toml` with a lower floor in the working directory: both
    checkers fail against the tree's floor. A report in the tree's `out/`
    finds the tree's `pyproject.toml` above it. A report with no
    `pyproject.toml` at or above it exits 2 naming the walk. A missing report
    is named as missing.
  - **The console.** A non-ASCII path in a FAIL line and in an exit-2
    message, under `PYTHONIOENCODING=ascii` (DEC-GSG-015).

  The scratch measurement of `tasks.md` is re-run at the implementation head
  in Milestone 0 and again after Milestone 4, so the before and after stand
  side by side.
- **DEC-GSG-014:** the documents that change, and those that do not.
  - **That change.** The help text, the README row and paragraph, the two
    `docs/hooks.md` lines and the `docs/aqa.md` paragraph each say "the
    Makefile or workflow YAML" and would be false the day this lands.
    `docs/aqa.md`'s security row says a committed secret is exit 1 and
    nothing else, and the fallback now also exits 2.
    `resolve_makefile`'s docstring says `check_makefile` tolerates a path it
    cannot open, which an unreadable regular file now contradicts.
    `run_tool_main`'s docstring says the scripts read `pyproject.toml` from
    the working directory, which is the defect this package removes.
    The verifier's line says the guard allowlists comments, which is now true
    of one rule. `tools/AGENTS.md` gains the whitelist rule because an agent
    that meets a finding needs to know the one exemption path, its reason
    rule and its one exclusion, or the shortest path to green is a rename. It
    is replaced text, not added: the file sits at the edge of its line
    budget, which `harden-release-pipeline` also spends from.
  - **That do not.** `docs/next-steps.md` item 7a, which
    `prepare-release-0-4-0`'s pull request 1 rewrites; the contract travels
    in the reader's docstring and tests. The `.claude/` hook reminders: a
    reminder is not the gate. The rest of the verifier's remediation line,
    whose advice to read the flagged line first stays right. `ci.yml`'s step
    name, which C-GSG-2 keeps.
- **DEC-GSG-015:** a gate script writes a non-ASCII path as UTF-8, never as
  a traceback.
  - **Why now.** `-z` makes the secret scan name a non-ASCII file it could
    not name before. The widened guard reads more files, and the coverage
    checkers name the configuration they found. Measured under
    `PYTHONIOENCODING=ascii`, a FAIL line naming such a path, from the guard
    or from the secret scan, raises `UnicodeEncodeError`. The process exits 1
    with nothing on stdout. For a finding that exit is right only by
    accident. For an exit-2 message it is the wrong code.
  - **The mechanism is the product's.** `fix-stdout-encoding-crash` fixed
    the same crash in the CLI by reconfiguring both streams to UTF-8 once,
    at the entry point, with each call guarded against a closed or
    unreconfigurable stream (R-SE-1, R-SE-3, DEC-SE-004). One shared helper
    in `tools/_common.py` does the same for these scripts, because a copy in
    each would drift. A path is then written as its UTF-8 bytes whatever the
    console's encoding. `errors="backslashreplace"` escapes only what UTF-8
    cannot encode, a lone surrogate, rather than raising on it.
  - **Where an ASCII console is real.** The Windows leg's console codepage is
    the case `openspec_graph/cli.py` names. CI's `encoding-stress` job sets
    `PYTHONIOENCODING: ascii` for the e2e-live target, which runs the
    product and not these scripts, so no job exercises them there today.

  Rejected:
  - `ascii()` of every path in every message, which changes each message on
    a UTF-8 console too;
  - `PYTHONIOENCODING` set in the `Makefile`, which is a recipe change
    C-GSG-2 forbids and which CI's direct invocations of the scripts would
    bypass.

---

## Acceptance Criteria

- [ ] **AC-GSG-1:** `targets(root)` on a planted root selects the makefile
  and each file of every pattern R-GSG-1 names, `Dockerfile*` included. A
  coverage floor planted in a composite action, an adopter template, the
  skill's template copy, each pre-commit file and the `Dockerfile` each fails
  `main` with its file named. The wiring tests over the real tree still find
  every workflow selected. (R-GSG-1, R-GSG-7, DEC-GSG-004)
  _Verified by:_ `pytest -k "test_every_workflow_is_scanned_by_the_threshold_guard or test_threshold_guard_scans_both_yaml_spellings"` · stage: `make test`

- [ ] **AC-GSG-2:** each widened shape of DEC-GSG-013's loud set fails
  `main` with exit 1, naming the file, the line, the name and the number:
  the widened word list, the argument-list separator, a quoted key and the
  flagged `max-*` flags among them. A makefile number today's literal rule
  reports is reported once, with today's message, and so is a `ruff==` pin in a
  workflow. (R-GSG-2, R-GSG-3, R-GSG-4, DEC-GSG-005, DEC-GSG-013)
  _Verified by:_ stage: `make test`

- [ ] **AC-GSG-3 (non-success):** the guard stays quiet on every shape
  DEC-GSG-013's quiet set plants, `max-parallel`, the legitimate keys in their
  quoted spelling, an `owner/name@ref` reference and comment prose among
  them, and the existing quiet and token-strip tests pass unedited. (R-GSG-2,
  R-GSG-3, R-GSG-4, DEC-GSG-005, DEC-GSG-013)
  _Verified by:_ `pytest -k "test_threshold_guard_stays_quiet_on_legitimate_lines or test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency or test_threshold_guard_stays_quiet_on_a_sha_pinned_uses_line or test_threshold_guard_ignores_comments_and_make_expansions"` · stage: `make test`

- [ ] **AC-GSG-4:** the pin rule reports each PEP 440 operator after each
  dev-extra name, `@` directly after one or spaced before a URL scheme, an
  extras-bracketed pin, a `coverage` pin and a pin in a workflow comment. A
  name planted only in a fixture's dev extra is caught when pinned. The
  script holds no name list beyond R-GSG-2's pattern, which
  is read in the diff. The dev extra lists `coverage` bare, and `[project]
  dependencies` is still empty. (R-GSG-4, R-GSG-10, DEC-GSG-006)
  _Verified by:_ `pytest -k "test_threshold_guard_fails_on_a_pinned_tool_version or test_runtime_dependencies_stay_empty or test_dependabot_does_not_add_a_pip_ecosystem"` · stage: `make test`

- [ ] **AC-GSG-5 (non-success):** the guard exits 2, naming the file and
  printing no traceback, for each input it cannot run on: no dev extra, a
  malformed whitelist line, an unreadable target (an injected
  `PermissionError`), an undecodable target and an unparsable `tools/`
  module. A directory where a makefile is expected is still nothing to scan.
  (R-GSG-4, R-GSG-5, R-GSG-6, R-GSG-7)
  _Verified by:_ `pytest -k "test_threshold_guard_survives_a_makefile_that_is_not_a_regular_file or test_threshold_guard_stops_at_an_unreadable_higher_precedence_candidate"` · stage: `make test`

- [ ] **AC-GSG-6:** a planted `tools/` module binding a threshold-named
  constant at module level — plain, annotated, tuple-unpacked, negated —
  fails the guard naming the module and the subject. A constant whose name
  carries no word of R-GSG-3, a `bool`, and a binding inside a function do
  not. (R-GSG-5, DEC-GSG-007)
  _Verified by:_ stage: `make test`

- [ ] **AC-GSG-7:** a whitelist entry suppresses exactly the finding with
  its relative POSIX path and subject, and a planted copy of the same
  literal in a second file is still reported. The FAIL line begins with that
  path and carries that subject. An entry that suppresses nothing fails the
  guard as stale, naming the entry, and an absent whitelist is an empty one.
  A planted tree is judged by its own whitelist and never by this
  repository's. (R-GSG-6, DEC-GSG-008)
  _Verified by:_ stage: `make test`

- [ ] **AC-GSG-8:** on the real tree the guard exits 0 with
  `tools/threshold_whitelist.txt`, every entry carrying a reason and none
  naming a workflow, and exits 1 naming `NO_FLOOR` with the whitelist
  withheld. `test_threshold_guard_scans_every_workflow` judges each real
  target after the whitelist and finds no stale entry, with its name and its
  other assertions kept, and
  `test_every_workflow_is_scanned_by_the_threshold_guard` passes unedited.
  (R-GSG-6, R-GSG-9, R-GSG-20, DEC-GSG-008, DEC-GSG-009)
  _Verified by:_ `pytest -k "test_no_hardcoded_passes_on_clean_repo or test_threshold_guard_scans_every_workflow or test_every_workflow_is_scanned_by_the_threshold_guard"` · stage: `make pre-pr`

- [ ] **AC-GSG-9:** the guard tests that shipped specs cite pass with their
  names and asserted properties kept. Those built on `_guard_tree` pass
  because that helper now plants a `pyproject.toml` with a dev extra, and no
  other edit is made to them. The docstring states what is scanned and which
  rules read comment lines, names the whitelist and no longer promises a
  "pinned path" check, and the PASS line names the scanned kinds. The
  docstring is read directly. (R-GSG-2, R-GSG-7, R-GSG-8, R-GSG-20)
  _Verified by:_ `pytest -k "test_threshold_guard_passes_on_a_clean_tree or test_threshold_guard_fails_on_a_hard_coded_coverage_floor or test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow or test_threshold_guard_flags_numbers_in_ordinary_recipe_idioms or test_threshold_guard_flags_a_pinned_floor_in_a_non_ci_workflow or test_threshold_guard_dispatches_a_gnumakefile_to_the_makefile_checker"` · stage: `make test`

- [ ] **AC-GSG-10:** `read_pyproject_int` returns the integer for a bare key
  with ASCII digits and an optional trailing comment. It returns `None` for
  an absent file, table or key. For a quoted key, a decimal, a
  digit-separated integer, a sign, a hexadecimal literal, an octal literal,
  an exponent, a quoted value or a trailing word it raises the `ReportError`
  subclass, naming the file, the table, the key and the value. The
  commented-header test passes unedited. (R-GSG-11, DEC-GSG-003)
  _Verified by:_ `pytest -k test_pyproject_readers_stop_at_a_commented_table_header` · stage: `make test`

- [ ] **AC-GSG-11 (non-success):** a planted fractional `fail_under`, whose
  integer part a planted report clears, no longer passes. The line checker in
  both modes, the branch checker on its own key, `dead_code.py` on its
  confidence and `matcher_accuracy.py` on a floor each exit 2, with the
  reader's message on stderr, nothing on stdout that states a verdict, and no
  traceback. (R-GSG-12, DEC-GSG-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-GSG-12:** over the planted corpus of R-GSG-13, every in-range
  value the tools reader returns is the number the product's reader returns,
  and every value the product reads as a fraction the tools reader refuses.
  For `101` the recorded outcome holds: the tools reader returns 101, the
  product's returns nothing, and the line checker exits 1 on a report at full
  coverage. Both readers' docstrings say that the type refusals carry
  forward to item 7a, that the spellings `tomllib` normalises are item 7a's
  decision and those tests its to replace, and nothing about `tomllib`'s
  availability. The docstrings are read directly. (R-GSG-13, R-GSG-14,
  DEC-GSG-002, DEC-GSG-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-GSG-13:** a key planted in a tracked non-ASCII file name,
  committed through `_git_repo`, is found by the fallback. The existing
  token-shape, skip-list and clean-repository tests pass unedited, and
  `_tracked_files` passes `-z` to git. (R-GSG-15, R-GSG-17, DEC-GSG-010)
  _Verified by:_ `pytest -k "test_fallback_scan_fires_on_each_token_shape or test_fallback_scan_skips_vendored_directories_but_not_tests or test_fallback_scan_is_clean_on_a_repo_without_secrets"` · stage: `make test`

- [ ] **AC-GSG-14 (non-success):** with gitleaks absent, `main` exits 2,
  naming the cause on stderr and printing no PASS line, in each case:
  - a directory with no `.git`, git's discovery bounded by
    `GIT_CEILING_DIRECTORIES`;
  - git's non-zero exit with the dubious-ownership message, git's stderr
    carried;
  - git absent from `PATH`;
  - output that is not UTF-8;
  - output listing no file;
  - a listing whose every path is absent or under a skipped directory;
  - an unreadable tracked file.

  `test_fallback_scan_returns_nothing_outside_a_git_repo` no longer exists,
  and no spec cited it. (R-GSG-16, R-GSG-17, R-GSG-20, DEC-GSG-010,
  DEC-GSG-011)
  _Verified by:_ stage: `make test`

- [ ] **AC-GSG-15:** the secret gate's `main` contracts hold unedited: 1 on
  a fallback finding, 0 on a clean fallback, gitleaks' verdict trusted either
  way, and the real checkout scanning clean. The module docstring describes
  `_SKIP_DIRS` and `.gitleaks.toml`'s allowlist as two lists, names what the
  fallback alone skips, and states the refusals. The docstring is read
  directly. (R-GSG-17, R-GSG-18)
  _Verified by:_ `pytest -k "test_secret_gate_main_returns_1_when_the_fallback_finds_a_key or test_secret_gate_main_returns_0_when_the_fallback_is_clean or test_secret_gate_main_trusts_a_clean_gitleaks_verdict or test_secret_gate_main_fails_when_gitleaks_reports_a_finding or test_secret_scan_clean_repo_passes"` · stage: `make test`

- [ ] **AC-GSG-16 (non-success):** a report and a `pyproject.toml` sit in
  one planted tree, and a `pyproject.toml` declaring lower floors sits in the
  working directory. Run from there, both checkers fail against the tree's
  floors, and their messages name the tree's `pyproject.toml`. A report in
  the tree's `out/` directory finds the same file above it. A report with no
  `pyproject.toml` at or above it exits 2, naming where the walk started. A
  missing report exits 2 as not found, before any configuration is sought.
  The planted-tree tests that run with the tree as their working directory
  pass unedited. (R-GSG-19, DEC-GSG-012)
  _Verified by:_ `pytest -k "test_cov_floor_threshold_is_read_from_pyproject_not_hardcoded or test_cov_floor_fails_below_threshold or test_branch_check_fails_below_floor or test_scoped_gate_fails_below_its_own_floor_and_passes_at_it or test_per_file_report_names_each_module_below_the_minimum or test_per_file_flag_leaves_the_argv_contract_alone"` · stage: `make test`

- [ ] **AC-GSG-17:** every new test was red before its change, and
  `tasks.md` records each red run. Every new test carries the tier the
  criterion computes. Every edited test module is within the line bound.
  Every docstring ceiling is matched exactly, any that moved having moved
  down. (R-GSG-21, R-GSG-22, DEC-GSG-013)
  _Verified by:_ `pytest -k "test_every_tier_marker_matches_its_mechanical_criterion or test_no_test_module_exceeds_the_line_bound or test_every_docstring_exemption_matches_its_ceiling"` · stage: `make test`

- [ ] **AC-GSG-18:** these documents describe the widened guard, the
  whitelist and the changed scripts; the prose is read directly:
  - the thresholds target's help text;
  - `README.md`'s row and paragraph;
  - `docs/hooks.md`'s two lines;
  - `docs/aqa.md`'s paragraph and its security row;
  - `tools/AGENTS.md`'s bullet;
  - `resolve_makefile`'s and `run_tool_main`'s docstrings;
  - the verifier's sentence on what the guard skips.

  `tools/AGENTS.md` names `tools/threshold_whitelist.txt`, its reason rule
  and the workflow exclusion, and stays within its line budget, with its
  precedence clause and links resolving. Every path and target the verifier
  names is real. Every required document is present and linked. (R-GSG-23,
  DEC-GSG-014)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve or test_path_like_backtick_references_resolve_to_real_files or test_make_target_references_are_real_makefile_targets"` · stage: `make docs-check`

- [ ] **AC-GSG-19:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `### Fixed` entry, led by its bold backticked name and naming each script
  and what it now refuses. Every versioned section still links to its tag.
  The entry is read directly. (R-GSG-23)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [ ] **AC-GSG-20 (non-success):** the product is untouched and the scripts
  stay what they were:
  - the rule inventory matches its baseline;
  - `_common` is stdlib-only;
  - every listed `tools/` script still runs as a script;
  - every `pytest -k` selector in every spec still resolves;
  - no file of another change package changed.

  The diff is read directly for the last item. (C-GSG-1, C-GSG-3, C-GSG-5)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_common_module_is_stdlib_only or test_gate_script_is_runnable_as_a_script or test_every_spec_test_citation_resolves_to_a_real_test"` · stage: `make test`

- [ ] **AC-GSG-21:** the whole ladder is green. It includes the thresholds
  and security stages over the widened set, and every coverage floor is where
  it was. No file under `.github/` changed, and the `Makefile` diff is
  R-GSG-23's help text alone. No exemption, `noqa`, mypy ignore or waiver was
  added. (C-GSG-2, C-GSG-6)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-GSG-22:** this package reached `dev` alone, with no code, after
  the 0.3.0 promotion. The implementation was a separate pull request opened
  as a draft and marked ready after Milestone 0's gate. `tasks.md` records
  each measurement dated, with its commit and command, and this spec pins no
  count or line number. This package validates clean, and the record is read
  directly. (C-GSG-4, C-GSG-7, DEC-GSG-001)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-GSG-23 (non-success):** under `PYTHONIOENCODING=ascii`, each
  script writes a non-ASCII path as its UTF-8 bytes, with its own exit code
  and no traceback:
  - the guard's FAIL line for a planted non-ASCII template name, exit 1;
  - the secret scan's FAIL line for a committed non-ASCII file, exit 1;
  - the line checker's refusal of a fractional floor in a tree under a
    non-ASCII directory, exit 2.

  Each script this package changes calls the shared helper first in its
  `main`, which is read in the diff. (R-GSG-24, DEC-GSG-015)
  _Verified by:_ stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-GSG-1..7, 9..17, 19, 20, 23 — every widened rule loud on its planted input and quiet on the quiet set, the whitelist exact, read under the scanned root and never stale, every exit-2 input refused, the reader exact or refusing in every caller and never disagreeing with the product inside its range, the secret scan enumerating NUL-separated names and refusing what it cannot list or scan, the coverage checkers reading the nearest configuration at or above their report, every non-ASCII path written as UTF-8, every cited test kept, every new test in its computed tier |
| Docs | `make docs-check` | AC-GSG-18 — the widened scope, the whitelist and the changed scripts described, `tools/AGENTS.md` within budget, every required document linked |
| Full | `make pre-pr` | AC-GSG-8, 21, 22 — the thresholds and security stages green over the real tree with its whitelist, no workflow line whitelisted, every floor where it was, no workflow or recipe changed, this package and the tree validating clean |
