# Spec: Hygiene Reports

> **Change:** `report-dead-code-and-spec-status`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Two kinds of drift have no command that shows them. Unreferenced code under
`openspec_graph/` and `tools/` was found once, by hand, for the October plan,
and nothing will find the next instance. And every change package carries a
`Status` header that nothing compares with the package's own record of what it
did. `openspec/AGENTS.md` says the spec has to match what shipped, and the
plan's own example, `gate-tools-coverage`, is exercised by every `make test`
while its header reads `DRAFT`. The plan asks for one report target for each
(W5.5, W8.5). Both are reports under guardrail 7 and DEC-PM-011: composed into
neither `ci` nor `pre-pr`, with a gate considered only after a quarter of quiet
and only by a package of its own.

The measurement changes three of the plan's premises. First, vulture at the
plan's confidence of 80 reports nothing over the two trees at this commit.
Vulture rates every unused function, method, class, property, attribute and
variable at 60, imports at 90, and only unreachable code and unused arguments
at 100, and ruff's `F` family already gates imports and locals. So a report at
80 could never list the unreferenced symbols the plan's end-state row holds it
to. At 60, with `tests/` counted as a user of the code, it lists exactly the
genuinely unreferenced symbols plus two shlex attribute assignments, which are
what a whitelist is for.

Second, a package's evidence is not uniform across its era. Shipped `APPROVED`
packages have every criterion unticked; a package with a CHANGELOG section of
its own has no milestone done; and only one package in five has a CHANGELOG
entry that names it. A mechanical report can therefore flag only the cases
where the header and the evidence both speak and disagree, and has to list
the rest for a reader.

Third, setting headers "to what shipped" is a decision this repository
reserves to a human. It also edits the record of packages that are on `main`,
and it needs a header value that means "shipped", which today's two values —
`DRAFT` and `APPROVED`, the latter meaning approved after review — do not
provide.

**Evidence:** measured at `1c8917c` (the head of `claude/m2-report-targets`,
stacked on PR #42), 2026-10-07; each command is in the proposal.

- **vulture's output.** `python -m vulture openspec_graph tools
  --min-confidence 80` prints nothing (exit 0). At 60 it prints 12 findings
  (exit 3). Over `openspec_graph tools tests` at 60 it prints 9, of which
  the 7 under the two trees are `has_selector`, `speckit_section_body`,
  `speckit_subsection_body`, `precision_pct`, `recall_pct`,
  `whitespace_split` and `commenters`.
- **The version facts.** vulture 2.16 is installed and is the latest on the
  index. Its changelog dates exit code 3 for dead code to 2.9 and Python 3.14
  support to 2.15.
- **The headers.** 25 of 51 `spec.md` headers read `DRAFT` and 26
  `APPROVED`, in one shape. Four proposals carry a status line of their own
  in another shape.
- **The comparison.** A one-off reading of this spec's definitions finds 9
  all-`DRAFT` packages with every milestone `[DONE]` and every criterion
  ticked, none all-`APPROVED` with neither, one whose proposal and spec
  headers disagree, and none unrecognised.
- **The guards.** The two report-target guards check direct prerequisites
  only and repeat one another. docs/hooks.md documents no report target, and
  its one table is read by a helper that would read any second table as CI
  rows.

---

## Requirements

- R-RDS-1: `pyproject.toml`'s `dev` extra MUST gain `vulture` with a lower
  bound and no upper bound or exact pin, at the release DEC-RDS-001 names,
  under a comment giving the floor's reasons. `[project] dependencies` MUST
  stay `[]`, and no other extra MAY be added. No workflow, Makefile recipe or
  Dependabot entry MAY pin or install vulture on its own.
- R-RDS-2: `pyproject.toml` MUST carry a `[tool.vulture]` table holding
  `min_confidence`, set to the confidence vulture assigns an unused function,
  method, class, property, attribute or variable (DEC-RDS-002). Its comment
  MUST say that it is a reporting threshold read by `tools/dead_code.py` and
  by vulture itself when run from the repository root, and that it gates
  nothing. No key vulture applies to a run's findings on its own — `exclude`,
  `ignore_names`, `ignore_decorators`, or a whitelist among `paths` — MAY be
  added there. No recipe line, workflow line or script MAY carry the number.
- R-RDS-3: `tools/dead_code.py` MUST import no third-party module and not
  `openspec_graph`, and MUST follow `tools/_common.py`'s conventions: its
  `logger`; a root resolved at call time; `read_pyproject_int`;
  `coverage_sources`; and argparse with the program name first in `argv`, as
  `stage_citations.py` takes it. It MUST accept `--root` (default: the
  repository root). It MUST produce its report from exactly one vulture
  process: `sys.executable -m vulture`, with the root as working directory,
  over every tree `[tool.coverage.run] source` declares (the reported trees)
  and over `tests/` when that directory exists, at `min_confidence` passed on
  the command line, and without the whitelist. `tests/` MUST count as a user
  of the code and MUST NOT be reported.
- R-RDS-4: Each line of that process's output MUST be read in vulture's
  shape — a path, a line number, a message, and a parenthesised confidence —
  with the path's separators normalised to `/`. The script MUST:
  - keep only findings under a reported tree;
  - take a symbol name only from a message of the form `unused <kind>
    '<name>'`;
  - suppress a finding whose name is a whitelist entry;
  - list every remaining finding, sorted by path then line, in vulture's own
    line form;
  - list as stale every whitelist entry that suppressed no finding.

  A finding whose message names no symbol — unreachable code, an
  unsatisfiable condition — MUST be listed and MUST NOT be suppressed by any
  entry. The first line of the report MUST name the reported trees, the
  confidence, the installed vulture version (read through
  `importlib.metadata`, without importing vulture) and how many whitelist
  entries were read.
- R-RDS-5: `tools/dead_code.py` MUST exit 1 when either list is non-empty,
  and 0, with one line saying both are empty, when neither is. It MUST exit 2,
  with a message naming the cause and never a traceback, when it cannot run:
  - vulture is not installed, decided by `importlib.util.find_spec` before
    any process starts, so no import-error text reaches stderr;
  - vulture exits with anything other than 0 or 3;
  - a line of vulture's output has neither shape;
  - `min_confidence` is absent, or `source` declares no tree;
  - a whitelist line is malformed.

  Vulture's own exit code 3 MUST be read as "findings" and MUST NOT reach the
  caller.
- R-RDS-6: The whitelist MUST be `tools/dead_code_whitelist.txt`. Each line
  that is neither blank nor a comment is one Python identifier, whitespace,
  `#`, and a non-empty reason. It is read only by `tools/dead_code.py` and
  never passed to vulture, and an absent file is an empty whitelist. An entry
  MAY be added only for a reported name that is used by code vulture does not
  read — at drafting, the shlex lexer attributes `tools/stage_citations.py`
  assigns for the standard library to read. It MUST NOT be added for a symbol
  that nothing uses.
- R-RDS-7: `tools/dead_code.py` MUST expose a function that returns every
  whitelist entry no reported tree binds. A binding is a function, class or
  method name, an assignment target (a name, or an attribute's name), an
  import alias or a parameter, read with `ast` and without vulture. A test in
  `make test` MUST assert that the function returns nothing on the real tree,
  and MUST show on a planted tree that an entry naming nothing is named. The
  other half of staleness — an entry that is bound but suppresses no finding
  — MUST be the report's (R-RDS-4) and MUST NOT be a test, so `make test`
  does not change its verdict with a vulture release.
- R-RDS-8: The `Makefile` MUST gain a `dead-code` target that is `.PHONY`,
  has no prerequisites, has help text that begins `Report` and says it is a
  report and not a gate, and has the recipe `python tools/dead_code.py` and
  nothing else.
- R-RDS-9: `tools/spec_status.py` MUST import no third-party module. It MUST
  read each spec's `Status` header and verification lines through
  `openspec_graph`'s own parse (`parse_spec`, under the dialect
  `detect.profile` reports, with `MAKE_REF` over each criterion's
  `verified_by`), and the stages each workflow runs through
  `stage_citations.workflow_stages`. Criterion checkboxes, milestone headings,
  task checkboxes, a proposal's status line and CHANGELOG entries, which no
  parser in the package reads, MUST be read with the standard library's `re`.
  It MUST accept `--root` (default: the repository root), with the program
  name first in `argv`.
- R-RDS-10: For every directory under `openspec/changes/` — each one a
  package, as `detect` counts them — the script MUST print one row, sorted by
  package name, giving:
  - the package name;
  - the `Status` header of each `spec.md`, and the proposal's status line when
    one is present;
  - criteria ticked of declared, counting `- [x] **AC-` against every
    `- [ ] **AC-` and `- [x] **AC-` line over the package's specs;
  - `## Milestone` headings in `tasks.md` carrying `[DONE]` of all such
    headings — or, when there are none, task checkboxes ticked of all —
    or "none recorded";
  - the `CHANGELOG.md` sections holding an entry naming the package, where an
    entry is a heading ending in the backticked package name in parentheses
    or a bullet led by the bold backticked package name, and any other
    mention is not an entry;
  - the stages cited on the package's verification lines that no scanned
    workflow invokes directly;
  - the package's finding, or none.

  A last line MUST count the packages and the findings by kind. The output
  MUST be text only.
- R-RDS-11: The header vocabulary MUST be:
  - spec `DRAFT` is draft, and spec `APPROVED` is settled;
  - proposal `proposed` is draft, and proposal `implemented` is settled.

  A package MUST carry at most one finding, chosen in this order:
  - `header-unrecognised`: a `spec.md` with no status header or a word outside
    the vocabulary, a proposal status line with such a word, or no `spec.md`
    at all;
  - `headers-disagree`: the package's headers map to both draft and settled;
  - `draft-but-complete`: every header is draft, the tasks are complete (at
    least one milestone heading and every one `[DONE]`, or no milestone
    heading and at least one task checkbox with every one ticked), and the
    criteria are complete (at least one declared and every one ticked);
  - `settled-but-empty`: every header is settled, no milestone heading carries
    `[DONE]` and no task checkbox is ticked, and no criterion is ticked.

  The CHANGELOG and workflow columns MUST NOT enter any finding. A package
  whose evidence is partial MUST be listed with its columns and MUST NOT be a
  finding.
- R-RDS-12: `tools/spec_status.py` MUST exit 1 when any package carries a
  finding, and 0, with a line saying none does, otherwise. It MUST exit 2,
  with a message naming the cause and never a traceback, when the root has no
  `openspec/changes/` directory, or when a `spec.md`, `proposal.md`,
  `tasks.md`, `CHANGELOG.md` or workflow file exists but cannot be read. An
  absent `CHANGELOG.md`, `proposal.md`, `tasks.md` or workflow directory is
  not a failure: its column reads as empty.
- R-RDS-13: The `Makefile` MUST gain a `spec-status` target with the shape
  R-RDS-8 gives `dead-code`, and the recipe `python tools/spec_status.py` and
  nothing else.
- R-RDS-14: The report-target guard MUST be extended, not duplicated. One
  helper in `tests/test_ci_makefile.py` MUST define a report target: a
  documented target whose help text begins `Report`, which is in `.PHONY` and
  is not reachable from `ci` or `pre-pr` through prerequisites, followed
  transitively. The two existing report-target tests MUST delegate to the
  helper and keep their names and assertions, because shipped specs cite
  them. A new test MUST run the helper over every report target in the real
  `Makefile`, requiring the `dead-code` and `spec-status` targets among them.
- R-RDS-15: `docs/hooks.md` MUST gain a reports section with one table row
  per report target. Each row's first cell is the backticked command, followed
  by what the report reads and its exit contract, and the section MUST say
  that none is composed into `ci`, `pre-pr` or a CI job. A test MUST hold that
  every report target has a row and every row names a report target. The
  CI-table reader in `tests/test_ci_workflow.py` MUST read only the table
  under the CI hooks heading, so that a second table in the file is never
  read as CI rows.
- R-RDS-16: `docs/architecture/c4.md`'s §4 `tools/*` row and `tools/AGENTS.md`
  MUST name both scripts in their groups and give their argv convention:
  - `spec_status` among the reports that import `openspec_graph`;
  - `dead_code` as a report that imports neither `openspec_graph` nor vulture,
    and runs vulture as a process.

  `tools/AGENTS.md` MUST stay within `MAX_NESTED_LINES`, with its precedence
  clause and resolving links. `docs/aqa.md` MUST describe both reports beside
  the stage-citation paragraph. Dated records — `CHANGELOG.md`'s released
  sections, the peer reviews, the plan — MUST NOT be edited.
- R-RDS-17: `CHANGELOG.md`'s `[Unreleased]` section MUST carry an `Added`
  entry led by the bold backticked name of this package, in the shape
  R-RDS-10 reads. It MUST name:
  - both targets;
  - the floored dev extra;
  - the confidence key and why it is not the plan's D4 figure;
  - the whitelist and its two stale checks;
  - the four finding kinds;
  - that no header was edited.
- R-RDS-18: Every new test MUST carry exactly one of the registered tiers,
  the one `tests/shape_support.py`'s criterion computes. An in-process test of
  either script loads a `tools/` script and is therefore at least
  `integration`, and a process the script itself starts does not count
  (DEC-TSS-017). Every new or edited test module MUST stay within
  `MAX_TEST_MODULE_LINES`. Both scripts MUST join
  `test_gate_script_is_runnable_as_a_script`'s list. Every `spec.md` a test
  plants MUST be written through `tests/support.py`'s `write_spec`.
- R-RDS-19: Every guard this spec adds MUST read the file it judges, and MUST
  be written and run red against the tree before the change it covers, with
  the red run recorded in `tasks.md` and never committed as a tree state. Each
  MUST also be shown red on a planted counter-example:
  - a `Makefile` text whose `pre-pr` composes a report target directly;
  - one that composes it through an intermediate target;
  - one whose report target is missing from `.PHONY`;
  - a docs/hooks.md text with a report target that has no row;
  - one with a row naming no report target;
  - one whose second table would be read as CI rows;
  - a whitelist entry naming no binding;
  - a `pyproject.toml` whose dev extra pins vulture exactly, or lists it
    under `[project] dependencies`.
- R-RDS-20: `tasks.md` MUST record, each dated with its commit and naming
  its command:
  - both reports' complete output at the branch head after the change;
  - the installed vulture version;
  - vulture's output at the plan's figure and at the configured one, before
    the change;
  - the stage-citation report after the change.

  The record MUST say that its figures include this package's own spec. The
  spec-status output so recorded is the worklist for the header follow-up
  DEC-RDS-008 describes.
- R-RDS-21: The dead-code report MUST NOT delete, rename, deprecate or
  privatise any symbol, and this package MUST NOT either. Every symbol the
  report lists at landing stays for M4's W5.1–3, and is recorded there as
  this package's measurement.
- C-RDS-1: No change to any rule, golden hash, `openspec_graph/` module or
  runtime dependency: the `RULES` tuple, `README.md`'s rules table and
  `tests/baseline_rules.json` are untouched, the `validate`/`graph`/`rules`
  hashes are unmoved, and `[project] dependencies` stays empty.
- C-RDS-2: `make thresholds` MUST print PASS at every milestone. The
  confidence lives only in `pyproject.toml`, and no recipe or workflow line
  carries a numeric literal for it.
- C-RDS-3: Neither target MAY be composed into `ci`, `pre-pr` or any CI
  workflow job. The `ci:` and `pre-pr:` lines MUST be byte-identical, and no
  file under `.github/` MAY change.
- C-RDS-4: This spec's requirements and criteria MUST NOT pin a count that
  another package changes — of specs, packages, findings, report targets,
  whitelist entries or scripts. Measurements belong in the proposal and in
  `tasks.md`, dated with their commit and naming their command.
- C-RDS-5: Every coverage floor MUST stay where it is and MUST hold at every
  milestone, the two new `tools/` scripts included. `make lint` and
  `make typecheck` (mypy `strict`, over `tools/`) MUST stay clean with no new
  per-file exemption.
- C-RDS-6: No file of any other change package MAY change — no `Status`
  header, no criterion tick, no milestone marker. That includes the packages
  the spec-status report lists, and the packages on this branch's own unmerged
  base.
- C-RDS-7: Neither script MAY emit JSON or declare a `schema_version`. Their
  text output is a report read by a person or an agent, not a stored output
  under `docs/policies.md`'s schema-integer rule.
- C-RDS-8: `tools/dead_code.py` MUST NOT import vulture or `openspec_graph`,
  and `tools/spec_status.py` MUST NOT import any module outside the standard
  library, `openspec_graph` and `tools/`. `tools/_common.py` stays
  stdlib-only.

---

## Decisions

- **DEC-RDS-001:** vulture is a floored dev extra — `vulture>=2.15` — not a
  bare one and not a pin. The repository's rule is that dev extras are
  unpinned "so contributors and CI resolve the same versions", held by the
  threshold guard's `==` check, by
  `test_dependabot_does_not_add_a_pip_ecosystem` and by a test docstring. A
  lower bound keeps that property: every fresh install resolves the latest
  release, and no update bot is needed, because a floor never goes stale the
  way a pin does. A bare requirement loses something this design needs:
  `pip install -e ".[dev]"` leaves an installed package that satisfies a bare
  requirement alone. Before 2.9, vulture exits 1 both for "dead code found"
  and for invalid input, so on an old install the report would read every
  finding as "could not run". The floor is 2.15 rather than 2.9 because
  vulture's changelog names 2.15 as the release that adds Python 3.14, which
  is in the support window and on the `test` matrix, where the dev extra is
  installed and the planted-tree test runs the installed vulture. This
  package does not claim what an older release does on 3.14; none was run.
  Rejected: bare (the silent misread above); an exact pin (it contradicts the
  written decision and would need the pip ecosystem a test forbids); a
  separate extra (the plan names the dev extra, and the planted-tree test
  needs vulture on every leg that installs `dev`).
- **DEC-RDS-002:** the confidence is vulture's unused-definition level, 60,
  read from `[tool.vulture] min_confidence`. This supersedes the plan's D4
  figure of 80, by measurement.
  - At 80, vulture reports nothing over `openspec_graph` and `tools` at
    `1c8917c`. Vulture's own table rates every unused function, method,
    class, property, attribute and variable at 60, imports at 90, and
    unreachable code and unused arguments at 100.
  - Imports and unused locals are already gated by ruff's `F` family, so a
    report at 80 would duplicate a gate and could never list
    `has_selector`, `precision_pct` or `recall_pct` — the three the plan's
    §7 row holds this target to, all rated 60.
  - D4's worry was that a *gate* at 60 would fail on shlex attribute
    assignments vulture cannot see. That is answered by the whitelist D4
    itself prescribes, and by this being a report.
  - The key sits in `[tool.vulture]` rather than `[tool.specgraph]` because
    vulture reads that table itself, so a contributor's bare vulture run from
    the root agrees with the report without being told. The script passes
    the same number explicitly, so its run does not depend on the working
    directory.
  - The table carries nothing vulture would apply on its own (R-RDS-2),
    because the report's one run must see every finding to compute staleness
    (DEC-RDS-004).

  Rejected: 80 (blind to the target's purpose, as measured); 100
  (unreachable code only); a number on the recipe line (the threshold guard
  would fail it, rightly).
- **DEC-RDS-003:** `tests/` counts as a user of the code and is never a
  reported tree, and the reported trees are `[tool.coverage.run] source`'s
  entries.
  - A symbol a test calls is referenced. That is the measure behind the
    plan's §1.2 "0 refs" (repository-wide), and the plan treats test-only
    public API as a separate question with its own decision (W5.2).
  - Without `tests/`, the 60 run lists five live symbols a test calls —
    `main_deprecated`, `filter_speckit_by_feature`, `section_body`,
    `suppressions` and `duplicate_scoped_floor_keys` — which would have to be
    whitelisted, hiding them from every later reading.
  - Reporting `tests/` would list pytest fixtures, which pytest injects by
    name and vulture cannot see.
  - The reported trees come from `source` because that list is this
    repository's one declaration of the trees it measures; a third tree
    added there is reported without a second edit.

  Rejected: a list of trees in the script (two places for one fact); the two
  trees alone (the five live symbols above).
- **DEC-RDS-004:** the whitelist is `tools/dead_code_whitelist.txt`. The
  script applies it by name to one run made without it, and its staleness is
  caught in two halves.
  - **By name, after the run.** Vulture's own whitelist works by name: a
    whitelisted name is added to the set of used names, so a name suppresses
    every finding that carries it. Applying the list by name after the run is
    therefore what vulture would have done. It also lets the one run show
    both what the whitelist hides and which entry hides nothing.
  - **A text file.** It is not a `.py` file under `tools/`: there it would be
    measured as a never-executed file by `[tool.coverage.run] source`,
    type-checked by `[tool.mypy] files`, and linted by `make lint`, where
    vulture's `_.name` idiom is an undefined name and a useless expression.
  - **Not at the root.** That would be a new kind of root file that nothing
    lints and nobody looks at.
  - **Not `[tool.vulture] ignore_names`.** Vulture would apply it to the
    report's own run, and its glob patterns can hide more than the name they
    were added for.
  - **Two halves of staleness.**
    - An entry that names no binding — the symbol was deleted or renamed —
      is caught deterministically in `make test` by `ast`, without vulture.
    - An entry that is bound but suppresses nothing — the code became
      referenced, or a vulture release stopped the false positive — is listed
      by the report.

    The split keeps `make test`'s verdict independent of vulture's releases,
    which the floor of DEC-RDS-001 leaves free to arrive, while no stale
    entry survives a run of the report.
- **DEC-RDS-005:** `tools/dead_code.py` runs vulture as a process rather than
  importing it, and translates its exit code.
  - `tools/AGENTS.md`: "No third-party dependencies, ever". A script that
    imports nothing third-party and reports an absent tool follows
    `tools/check_secrets.py`'s handling of `gitleaks`.
  - `importlib.util.find_spec` decides absence before any process starts, so
    the report exits 2 with its own message and no import-error text — which
    `test_gate_script_is_runnable_as_a_script` would read as a load failure.
  - Vulture's exit 3 becomes the report's 1, because that test, the report
    contract, and planlint's own contract all speak 0, 1 and 2.
  - `sys.executable -m vulture`, never a bare `vulture` on `PATH`, so the
    report reads the vulture installed beside the interpreter that runs it.
  - The planted-tree test runs the real process. It is `integration` and not
    `e2e`, because the process is started by the code under test, not by the
    test (DEC-TSS-017).
- **DEC-RDS-006:** one exit contract for both reports — 0 for nothing to
  report, 1 for a non-empty report, 2 for could not run. That is planlint's
  own contract and `coverage-per-file`'s (DEC-MCO-009): the friendly path and
  a later gating path cannot diverge, because promoting the report is
  composing the target into a gate aggregate and nothing else.
  `stage-citations` exits 0 whatever it finds, and that is right for it,
  since it counts things that are neither good nor bad. These two list things
  the plan wants at zero and names a gate for after a quiet quarter. Neither
  is composed into `ci` or `pre-pr` (DEC-PM-011, guardrail 7); a report that
  exits 1 makes `make` print an error line, which `matcher-accuracy` and
  `coverage-per-file` already accept.
- **DEC-RDS-007:** "disagrees with its evidence" is defined mechanically as
  the four findings of R-RDS-11, and only tasks and criteria enter them.
  - The measurement shows each signal is era-dependent: `APPROVED` packages
    on `main` with every criterion unticked, a package with a CHANGELOG
    section and no milestone done, an owner-executed milestone no in-tree
    commit can tick.
  - A finding is therefore raised only where the header and *both* in-tree
    signals point the same way and contradict it, and every other package is
    listed with its columns for a reader.
  - The CHANGELOG column is shown and not used. Measured, one package in
    five has an entry naming it in either shape, and the 0.2.0 entries name
    features, not packages. Requiring an entry would excuse
    `gate-tools-coverage`, the plan's own example, whose entry names no
    package.
  - The workflow column is shown and not used. A stage no workflow runs by
    name is a fact about the workflows, which `make stage-citations` reports
    per stage, not about whether a package shipped.
  - The plan's W8.2 makes "tasks complete and a CHANGELOG entry" the archive
    criterion, and that package may require both. This one only reports.
  - `header-unrecognised` exists so that a new header word, or a spec
    without a header, is a finding rather than a silent pass.
- **DEC-RDS-008:** the headers are not set in this package. The report's
  output is the worklist, recorded in `tasks.md`, and the follow-up is a
  maintainer's. Four reasons:
  1. **Promotion is a human decision.** `.claude/agents/spec-drafter.md`
     says `APPROVED` is "a human decision after review", and
     `lint-empty-speckit-requirements`' `tasks.md` says the same.
  2. **The records are not edited.** The packages the report flags are on
     `main` or on this branch's unmerged base. This repository's convention
     is that a later package names a shipped package's record and does not
     edit it (DEC-MCO-006, DEC-ZCG-003 and R-ZCG-13, DEC-TSS-016). The one
     in-place amendment, DEC-ASP-007, was of a sibling on the same unmerged
     branch, and that was a plan, not a header.
  3. **No value means shipped.** The header has two values, `DRAFT` and
     `APPROVED`, and `APPROVED` means approved after review — rule H005 reads
     it as "not `DRAFT`". Writing "what shipped" needs either `APPROVED` to
     change meaning or a third value, which is a convention change for the
     scaffold template, the drafter and the rule. It is not a hygiene edit.
  4. **The number is not mechanical.** The plan's "18" was a count of
     `DRAFT` headers, and it is not recoverable mechanically. 25 of 51 read
     `DRAFT` at `1c8917c`, and the evidence is unanimous for only some.

  This package squares with the convention by editing no other package
  (C-RDS-6). The follow-up has to decide, in writing, the vocabulary and the
  exception for one `Status` line of a shipped record, or a supersession-style
  record of status. It closes the plan's end-state row. This package makes
  the row measurable.
- **DEC-RDS-009:** `tools/spec_status.py` imports `openspec_graph` and its
  sibling `stage_citations`. The plan's direction that the script be
  stdlib-only is read as `tools/AGENTS.md`'s actual rule — no third-party
  dependency — and is followed in its other half: whatever no parser in the
  package reads is read with `re` alone.
  - The status header and verification lines are read by the same parse the
    rules use, because a second reader would count something else — the
    reason `stage_citations.py`'s docstring gives for importing the package.
  - The workflow invocations come from the one lexer that already answers
    "which stages does CI run by name", with its quoting and comment handling.
  - The import is through `tools/` on `sys.path`, as `_common` is imported.

  Rejected: a stdlib-only reimplementation of both (two answers to one
  question); dropping the workflow column (the plan names it as evidence).
- **DEC-RDS-010:** the reports table lives in docs/hooks.md, and the CI-table
  reader is scoped to its section. `_hooks_ci_table_cells` reads every
  backticked first cell of every table row in the file, while its docstring
  says "the CI hooks table". That is latent today, because the file has one
  table. A reports table would turn
  `test_every_hooks_ci_table_row_names_a_job_or_workflow` red on its first
  row. Scoping the reader makes it read what it says, and a planted second
  table proves it. The reports table's first cell is the backticked command,
  which reads as a command and which the old reader would not have matched
  either. docs/hooks.md is where the ladder — what runs at commit, in CI and
  before a pull request — is documented, so it is where "what is
  deliberately outside the ladder" belongs.
- **DEC-RDS-011:** the report-target guard is extended through one helper,
  and reachability is transitive. Today two tests repeat the same three
  assertions, and both check only `ci`'s and `pre-pr`'s direct
  prerequisites, so a report composed into `test` would slip into the ladder
  unseen. One helper defines a report target, and reachability follows
  prerequisites to a fixed point. The definition is a documented target whose
  help text begins "Report", in `.PHONY` and unreachable from the aggregates —
  the shape every existing report target already has. The two existing tests
  keep their names and assertions, because AC-PM-14 and AC-MCO-17 cite them,
  and delegate. The new test requires `dead-code` and `spec-status` by name,
  so that it is red before they exist.
- **DEC-RDS-012:** the report lists and does not act, and what it found
  beyond the plan is recorded for M4. `has_selector`, `precision_pct` and
  `recall_pct` stay for W5.1, under guardrail 1's deprecation window.
  `speckit_section_body` and `speckit_subsection_body`, which the plan called
  test-only and which nothing calls at this commit, are listed by the report
  and left to W5.2's decision on public names. The three `report.__all__`
  names are used inside their module and imported by no other. Vulture cannot
  see that, by construction, and this package does not add a second analyser
  for one row of the plan.
- **DEC-RDS-013:** the tests are split by subject, and tiered by the
  criterion, not by intent.
  - `tests/test_dead_code.py` and `tests/test_spec_status.py` are new
    modules, one subject each. The report-target and reports-table guards
    join `tests/test_ci_makefile.py` beside the tests they extend, and the
    scoped CI reader's planted test joins `tests/test_ci_workflow.py`.
  - Every in-process test of a script loads a `tools/` script and is
    `integration`. A test that only calls a helper on a planted string is
    whatever the criterion computes for it. The only `e2e` path is the
    existing runnable-as-a-script test.
  - The planted-tree test runs the installed vulture with no skip, as the
    property tests import `hypothesis` with no skip: both are dev extras, and
    `make test` already requires the dev extra.
  - Planted packages are written through `write_spec`; their `proposal.md`,
    `tasks.md` and `CHANGELOG.md` are not spec paths and are written
    directly.

---

## Acceptance Criteria

- [ ] **AC-RDS-1:** `pyproject.toml`'s dev extra lists vulture with a lower
  bound and no exact pin or upper bound, `[project] dependencies` is still
  empty, and Dependabot has no pip ecosystem. The planned dev-extra test also
  names a planted file with an exact pin or a runtime entry; until it exists
  the stage covers it. (R-RDS-1, R-RDS-19, C-RDS-1, DEC-RDS-001)
  _Verified by:_ `pytest -k "test_runtime_dependencies_stay_empty or test_dependabot_does_not_add_a_pip_ecosystem or test_threshold_guard_fails_on_a_pinned_tool_version"` · stage: `make test`

- [ ] **AC-RDS-2:** `[tool.vulture] min_confidence` is set at vulture's
  unused-definition level and is the only key in that table. The threshold
  guard prints PASS on the finished tree at every milestone and still fails
  on a planted literal in a recipe. (R-RDS-2, C-RDS-2, DEC-RDS-002)
  _Verified by:_ `pytest -k "test_threshold_guard_passes_on_a_clean_tree or test_threshold_guard_fails_on_a_hard_coded_coverage_floor"` · stage: `make thresholds`

- [ ] **AC-RDS-3:** against canned vulture output on a planted root:
  - a finding under a reported tree is listed in vulture's line form, and
    one under `tests/` is not;
  - a finding whose name is a whitelist entry is suppressed, and an entry
    that suppressed nothing is listed as stale;
  - an unreachable-code finding is listed and never suppressed;
  - a path written with Windows separators names the same tree;
  - the first line names the trees, the confidence, the vulture version and
    the entry count;
  - the script imports neither vulture nor `openspec_graph`.

  The tests are planned in `tasks.md`; until they exist the stage is the
  citation. (R-RDS-3, R-RDS-4, C-RDS-8, DEC-RDS-003, DEC-RDS-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-4 (non-success):** the dead-code script exits 2, with a
  message and no traceback, when:
  - vulture is not installed (with no process started and no import-error
    text on stderr);
  - `min_confidence` is absent, or `source` declares no tree;
  - vulture exits 1 or 2;
  - its output carries a line in neither shape;
  - a whitelist line is malformed.

  It exits 1, never 3, on findings, and 0 with the saying-so line on none.
  The tests are planned; until they exist the stage is the citation.
  (R-RDS-5, DEC-RDS-005, DEC-RDS-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-5 (non-success):** every entry of the real whitelist names a
  binding in a reported tree, and a planted whitelist entry naming no binding
  is named by the binding function — with no vulture process started.
  Neither test asserts that an entry suppresses a finding. The tests are
  planned; until they exist the stage is the citation. (R-RDS-6, R-RDS-7,
  R-RDS-19, DEC-RDS-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-6:** run through `main` with the real process, the installed
  vulture on a planted tree reports a planted unused function under a
  reported tree and the script exits 1. The same tree with that function
  called from a planted `tests/` module exits 0. The test is planned; until
  it exists the stage is the citation. (R-RDS-3, R-RDS-5, R-RDS-18,
  DEC-RDS-001, DEC-RDS-005)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-7:** on planted packages, the spec-status script raises each
  finding of R-RDS-11 on exactly its case:
  - `draft-but-complete` — milestones all `[DONE]` and criteria all ticked
    under a `DRAFT` header — including the task-checkbox form for a package
    with no milestone heading;
  - `settled-but-empty`;
  - `headers-disagree` — a proposal's `proposed` against a spec's `APPROVED`;
  - `header-unrecognised` — a missing header, an unknown word, a package
    with no `spec.md`.

  It prints one text row per package with every column, and exits 1. The
  tests are planned; until they exist the stage is the citation. (R-RDS-9,
  R-RDS-10, R-RDS-11, R-RDS-12, C-RDS-7, DEC-RDS-007, DEC-RDS-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-8 (non-success):** none of these raises a finding:
  - a `DRAFT` package with every criterion ticked but a milestone not `[DONE]`;
  - an `APPROVED` package with its milestones done and no criterion ticked;
  - a package named in a CHANGELOG sentence that is not an entry.

  Each is listed with its columns, and the script exits 0 when nothing else
  is found. The script exits 2, with no traceback, when the root has no
  `openspec/changes/` or a package file exists but cannot be read; an absent
  `CHANGELOG.md` or workflow directory does not change the exit code. The
  tests are planned; until they exist the stage is the citation. (R-RDS-11,
  R-RDS-12, DEC-RDS-006, DEC-RDS-007)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-9:** the workflow column lists a verification-line stage that
  no planted workflow runs, and omits one a planted workflow runs in command
  position. The reused reader's own behaviour — `run:` scripts read, other
  YAML fields ignored, a filter honoured — stays green unedited. The
  column's own test is planned; until it exists the stage covers it.
  (R-RDS-9, R-RDS-10, DEC-RDS-009)
  _Verified by:_ `pytest -k "test_run_block_commands_are_scanned_but_yaml_fields_are_not or test_the_workflow_filter_restricts_who_is_credited or test_a_repository_without_workflows_credits_nobody"` · stage: `make test`

- [ ] **AC-RDS-10:** read from the `Makefile`:
  - the `dead-code` and `spec-status` targets are `.PHONY`, documented with
    help text beginning "Report", have no prerequisites, and run exactly
    their script;
  - every report target is unreachable from `ci` and `pre-pr` through
    prerequisites;
  - the two existing report-target tests pass unedited in name and
    assertion;
  - no recipe but `coverage-run`'s invokes pytest;
  - the `ci:` and `pre-pr:` lines are unchanged.

  The new test is planned; until it exists the existing tests and the stage
  are the citation. (R-RDS-8, R-RDS-13, R-RDS-14, C-RDS-3, DEC-RDS-006,
  DEC-RDS-011)
  _Verified by:_ `pytest -k "test_makefile_has_matcher_accuracy_report_target or test_makefile_has_coverage_per_file_report_target or test_the_suite_runs_once_through_coverage_run"` · stage: `make test`

- [ ] **AC-RDS-11 (non-success):** through the same helper, each of these
  planted `Makefile` texts is named, with the target and the path by which
  it is reached:
  - a report target composed into `pre-pr` directly;
  - one composed through an intermediate target of `ci`;
  - one missing from `.PHONY`.

  The tests are planned; until they exist the stage is the citation.
  (R-RDS-14, R-RDS-19, DEC-RDS-011)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-12:** docs/hooks.md's reports section has a row for every
  report target and no row for anything else. A planted text missing a row,
  and one with a row naming no report target, are each named. The CI-table
  guards still pass on the real file, and a planted second table is not read
  as CI rows. The new tests are planned; until they exist the existing
  CI-table tests and the stage are the citation. (R-RDS-15, R-RDS-19,
  DEC-RDS-010)
  _Verified by:_ `pytest -k "test_every_hooks_ci_table_row_names_a_job_or_workflow or test_hooks_ci_table_lists_every_ci_job or test_hooks_test_row_names_the_matrix_bounds"` · stage: `make test`

- [ ] **AC-RDS-13:** `docs/architecture/c4.md` §4, `tools/AGENTS.md` and
  `docs/aqa.md` describe both scripts in their groups with their argv
  convention. `tools/AGENTS.md` stays within its line budget with its
  precedence clause and resolving links, every required document is present
  and linked, and no dated record is edited. The prose is read directly; the
  agent-file budget and the docs gate are the tests. (R-RDS-16)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve"` · stage: `make docs-check`

- [ ] **AC-RDS-14:** `python tools/dead_code.py` and `python
  tools/spec_status.py`, run from a throwaway cwd with no arguments, reach
  their own exit path with 0, 1 or 2 and no load-failure marker on stderr.
  (R-RDS-5, R-RDS-12, R-RDS-18, DEC-RDS-005)
  _Verified by:_ `pytest -k test_gate_script_is_runnable_as_a_script` · stage: `make test`

- [ ] **AC-RDS-15:** every new test carries exactly the tier the criterion
  computes for it, every new or edited test module is within the line bound,
  and no new test writes a planted spec path by hand. The suite-shape guards
  that hold this are `test_every_test_carries_exactly_one_tier_marker`,
  `test_every_tier_marker_matches_its_mechanical_criterion`,
  `test_no_test_module_exceeds_the_line_bound` and
  `test_no_test_module_writes_a_spec_path_by_hand`, on this package's base
  branch. They are cited by the stage, because they do not exist on `main`.
  (R-RDS-18, DEC-RDS-013)
  _Verified by:_ stage: `make test`

- [ ] **AC-RDS-16:** the rule inventory, the golden `validate`/`graph`/`rules`
  hashes and the empty runtime-dependency list are unchanged. (C-RDS-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [ ] **AC-RDS-17 (non-success):** the diff deletes, renames, deprecates or
  privatises no symbol; it changes no file of another change package, its
  `Status` header included; and every `pytest -k` selector in every spec under
  `openspec/changes/` still resolves to a test function. (R-RDS-21, C-RDS-6,
  DEC-RDS-008, DEC-RDS-012)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make test`

- [ ] **AC-RDS-18:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `Added` entry with the items R-RDS-17 names, in the bullet shape the
  spec-status report reads as an entry, and every versioned section still
  links to its release tag. The entry is read directly; the test holds the
  link shape. (R-RDS-17)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [ ] **AC-RDS-19:** `tasks.md` records, each dated with its commit and naming
  its command:
  - the red run of every guard;
  - vulture's output before the change at the plan's figure and at the
    configured one;
  - both reports' complete output at the branch head after the change;
  - the installed vulture version;
  - the stage-citation report after, noting that its figures include this
    spec.

  No requirement or criterion here pins a count another package changes,
  and the package validates clean under the repository's own rules. A review
  property, read directly; the gate confirms the package. (R-RDS-19,
  R-RDS-20, C-RDS-4, DEC-RDS-008)
  _Verified by:_ stage: `make validate`

- [ ] **AC-RDS-20:** the whole ladder is green with every floor where it was,
  ruff and strict mypy clean over both new scripts with no new exemption,
  and neither report target run by any step of the ladder or of CI. (C-RDS-3,
  C-RDS-5)
  _Verified by:_ stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-RDS-1, 3..12, 14..18 — both scripts' behaviour on planted roots and on the installed vulture, the whitelist binding guard, the report-target and reports-table guards green on the real tree and red on their planted counter-examples, every new test in its computed tier |
| Threshold guard | `make thresholds` | AC-RDS-2 — PASS at every milestone; the confidence only in `pyproject.toml` |
| Docs | `make docs-check` | AC-RDS-13 — both scripts described, the agent file within budget, every required document linked |
| Self-check | `make validate` | AC-RDS-19 — this package, then the whole tree, validate clean |
| Full | `make pre-pr` | AC-RDS-20 — the ladder green with no floor moved and neither report in it |
