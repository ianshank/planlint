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
provide. So this package builds the report and names the owner of the rest: a
follow-up package, `settle-package-status-headers`, in which the maintainer
settles the headers the report lists and decides the vocabulary.

**Evidence:** measured at `1c8917c` (the head of `claude/m2-report-targets`,
stacked on PR #42), 2026-10-07; for the round-1 corrections at `114754c`; and
for the round-2 corrections at `1c6b8b8`, the merge of #42's head `92077b5`
into this branch — all the same day. Each command is in the proposal.

- **vulture's output.** `python -m vulture openspec_graph tools
  --min-confidence 80` prints nothing (exit 0). At 60 it prints 12 findings
  (exit 3). Over `openspec_graph tools tests` at 60 it prints 9, of which
  the 7 under the two trees are `has_selector`, `speckit_section_body`,
  `speckit_subsection_body`, `precision_pct`, `recall_pct`,
  `whitespace_split` and `commenters`.
- **vulture at its edges.** From the root at `114754c`: `python -m vulture`
  with no path prints "Please pass at least one file or directory" and exits
  2; over a directory with no `.py` file it prints nothing and exits 0; over
  an absent path it exits 1. `ast.parse`, which vulture parses with, writes a
  `SyntaxWarning` for an invalid escape to stderr and still succeeds.
- **The version facts.** vulture 2.16 is installed and is the latest on the
  index. Its changelog dates exit code 3 for dead code to 2.9 and Python 3.14
  support to 2.15.
- **The headers.** At `1c6b8b8`, the grep anchored on a line that begins
  `> **Status:** ` counts 26 `spec.md` headers reading `DRAFT` and 26
  `APPROVED`, of 52, in one shape, this package's own `DRAFT` spec among
  them. The grep is anchored because this spec quotes the phrase in prose,
  which an unanchored grep counts as a second header. Four proposals carry a
  status line of their own in another shape, each in its header block.
- **The header reader.** `parse_spec` reads a spec as `utf-8-sig` with
  undecodable bytes replaced (`openspec_graph/parse.py:119`), and takes the
  status from `STATUS` (`openspec_graph/parse_semantics.py:16`), searched
  unanchored over the raw text and upper-cased (`openspec_graph/parse.py:156`,
  `:168`). Rule H005 reads that value. The waiver pattern `SUPPRESS`
  (`openspec_graph/parse_semantics.py:51`) matches across lines, so a
  waiver's reason can put a line of any shape inside a header block.
  `blank_html_comments` (`openspec_graph/parse_semantics.py:599`) blanks every
  HTML comment, across lines, keeping length and newlines, and the speckit
  rules already read through it (`openspec_graph/rules_speckit.py:111`). At
  `1c6b8b8` no spec's header block holds an HTML comment, and a one-off
  read-only reading with the anchored reader of R-RDS-23 agrees with
  `parse_spec(...).status` on every spec once upper-cased.
- **The packages.** `detect.profile(root).change_dirs`
  (`openspec_graph/detect.py:707–715`) counts a symlinked alias of a package
  once, by real-path identity, and keeps a package with no `spec.md`. It is
  every directory directly under `openspec/changes/`, so an empty directory
  gives no package at all.
- **The comparison.** A one-off reading of this spec's definitions finds 9
  all-`DRAFT` packages with every milestone `[DONE]` and every criterion
  ticked, none all-`APPROVED` with neither, one whose proposal and spec
  headers disagree, and none unrecognised.
- **The guards.** The two report-target tests and `_one_run_violations` each
  check direct prerequisites only, and repeat one another. docs/hooks.md
  documents no report target, and its one table is read by a helper that
  would read any second table as CI rows.

---

## Requirements

- R-RDS-1: `pyproject.toml`'s `dev` extra MUST gain `vulture` with a lower
  bound and no upper bound or exact pin, at the release DEC-RDS-001 names,
  under a comment giving the floor's reasons. `[project] dependencies` MUST
  stay `[]`, and no other extra MAY be added. No file under `.github/` —
  workflow or Dependabot configuration — and no `Makefile` recipe line MAY
  name vulture: the dev extra installs it, and `tools/dead_code.py` runs it.
- R-RDS-2: `pyproject.toml`'s `[tool.specgraph]` table MUST gain
  `dead_code_min_confidence`, set to the confidence vulture assigns an unused
  function, method, class, property, attribute or variable (DEC-RDS-002),
  beside `per_file_line_min`, the reporting threshold DEC-MCO-009 put there.
  Its comment MUST say that it is a reporting threshold read by
  `tools/dead_code.py`, which passes it to vulture on the command line, and
  that it gates nothing. `pyproject.toml` MUST NOT carry a `[tool.vulture]`
  table: vulture reads one from its working directory and would apply its
  keys to the report's own run. No recipe line, workflow line or script MAY
  carry the number.
- R-RDS-3: `tools/dead_code.py` MUST import no third-party module and not
  `openspec_graph`, and MUST follow `tools/_common.py`'s conventions: its
  `logger`; a root resolved at call time; `read_pyproject_int` over
  `[tool.specgraph]`; `coverage_sources`; and argparse with the program name
  first in `argv`, as `stage_citations.py` takes it. It MUST accept `--root`
  (default: the repository root). It MUST produce its report from exactly one
  vulture process: `sys.executable -m vulture`, with the root as working
  directory, over every tree `[tool.coverage.run] source` declares (the
  reported trees) and over `tests/` when that directory exists, at
  `dead_code_min_confidence` passed on the command line, and without the
  whitelist. `tests/` MUST count as a user of the code and MUST NOT be
  reported.
- R-RDS-4: The script MUST read findings from vulture's stdout and from
  nothing else. Each stdout line MUST be read in vulture's shape — a path, a
  line number, a message, and a parenthesised confidence — with the path's
  separators normalised to `/`. The script MUST:
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
  - `dead_code_min_confidence` is absent, or `source` declares no tree;
  - a tree `source` declares is not a directory holding at least one `.py`
    file, decided before any process starts, because vulture reads an empty
    tree as clean;
  - `pyproject.toml` or the whitelist exists but cannot be read (`OSError`)
    or decoded (`UnicodeDecodeError`), with the message naming the file. The
    script MUST translate these from its own reads, including the ones it
    makes through `_common`'s readers, which raise them unchanged;
  - vulture exits with anything other than 0 or 3;
  - a line of vulture's stdout has neither shape;
  - a whitelist line is malformed.

  Vulture's own exit code 3 MUST be read as "findings" and MUST NOT reach the
  caller. Vulture's stderr MUST go to the script's logger at DEBUG, and MUST
  decide nothing when vulture exits 0 or 3: a `SyntaxWarning` there is not a
  failure. When vulture exits 1 or 2, the exit-2 message MUST carry that exit
  code and vulture's stderr.
- R-RDS-6: The whitelist MUST be `tools/dead_code_whitelist.txt`. Each line
  that is neither blank nor a comment is one Python identifier, whitespace,
  `#`, and a non-empty reason. It is read only by `tools/dead_code.py` and
  never passed to vulture, and an absent file is an empty whitelist. An entry
  MAY be added only for a reported name that is used by code vulture does not
  read — at drafting, the shlex lexer attributes the workflow lexer assigns
  for the standard library to read, which R-RDS-24 moves into
  `tools/_common.py`. It MUST NOT be added for a symbol that nothing uses.
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
- R-RDS-9: `tools/spec_status.py` MUST import no third-party module, and from
  `tools/` only `_common`. It MUST read verification lines through
  `openspec_graph`'s own parse — `parse_spec`, under the dialect
  `detect.profile` reports, with `MAKE_REF` over each criterion's
  `verified_by` — and MUST use `parse_spec` for nothing else. It MUST read the
  `Status` header and a proposal's status line as R-RDS-23 requires, and the
  stages each workflow runs through `_common.workflow_stages`, passing
  `MAKE_REF` as the stage grammar (R-RDS-24). Criterion checkboxes, milestone
  headings, task checkboxes, a proposal's status line and CHANGELOG entries,
  which no parser in the package reads, MUST be read with the standard
  library's `re`. It MUST accept `--root` (default: the repository root), with
  the program name first in `argv`.
- R-RDS-10: The packages MUST be `detect.profile(root).change_dirs` — every
  directory under `openspec/changes/`, a symlinked alias counted once by
  real-path identity, and a package with no `spec.md` kept — and never a
  separate glob or listing of that directory. For each, the script MUST print
  one row, sorted by package name, giving:
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

  `VOCABULARY` in `tools/spec_status.py` MUST be the one place the spec
  vocabulary is written; it is where the follow-up of R-RDS-22 amends it.
  Words are matched case-sensitively, so any other word — a lower-case
  `draft`, or `IMPLEMENTED` — is unrecognised until the vocabulary names it.

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
  with a message naming the cause — the file or directory, where there is
  one — and never a traceback, when:
  - the root has no `openspec/changes/` directory;
  - that directory holds no package. A report over no package is not a clean
    report, for the reason DEC-RDS-005 gives for an empty tree;
  - a `spec.md`, `proposal.md`, `tasks.md`, `CHANGELOG.md` or workflow file
    exists but cannot be read (`OSError`);
  - a `proposal.md`, `tasks.md` or `CHANGELOG.md` cannot be decoded
    (`UnicodeDecodeError`).

  A `spec.md` MUST be read as `parse_spec` reads it — `utf-8-sig`, with
  undecodable bytes replaced — so the report never refuses a spec that the
  gate accepts. A workflow file is read as `stage_citations` reads it, with
  undecodable bytes replaced. The script MUST translate these from its own
  reads, or catch them in `main`. An absent `CHANGELOG.md`, `proposal.md`,
  `tasks.md` or workflow directory is not a failure: its column reads as
  empty.
- R-RDS-13: The `Makefile` MUST gain a `spec-status` target with the shape
  R-RDS-8 gives `dead-code`, and the recipe `python tools/spec_status.py` and
  nothing else.
- R-RDS-14: The report-target guard MUST be extended, not duplicated. One
  helper in `tests/test_ci_makefile.py` MUST define a report target: a
  documented target whose help text begins `Report`, which is in `.PHONY` and
  is not reachable from `ci` or `pre-pr` through prerequisites, followed
  transitively. Every check of that property in the module MUST go through
  the helper:
  - `test_makefile_has_matcher_accuracy_report_target` and
    `test_makefile_has_coverage_per_file_report_target` MUST delegate to it
    and keep their names and every property they assert, because shipped
    specs cite them;
  - `_one_run_violations` MUST delegate its aggregate check to it. Its planted
    Makefile's report target MUST have help text that begins `Report`, so the
    planted baseline stays clean. The helper's message for a reachable report
    target MUST keep the words `pre-pr composes`, so the existing planted case
    is named unedited.

  A new test MUST run the helper over every report target in the real
  `Makefile`, requiring the `dead-code` and `spec-status` targets among them.
- R-RDS-15: `docs/hooks.md` MUST gain a reports section with one table row
  per report target. Each row's first cell is the backticked command, followed
  by what the report reads and its exit contract, and the section MUST say
  that none is composed into `ci`, `pre-pr` or a CI job. The section — the
  spec-status row or the text under the table — MUST also say that the
  spec-status report stays red, exiting non-zero, until
  `settle-package-status-headers` lands. A test MUST hold that every report
  target has a row and every row names a report target. The CI-table reader
  in `tests/test_ci_workflow.py` MUST read only the table under the CI hooks
  heading, so that a second table in the file is never read as CI rows.
- R-RDS-16: `docs/architecture/c4.md`'s §4 `tools/*` row and `tools/AGENTS.md`
  MUST name both scripts in their groups and give their argv convention:
  - `spec_status` among the reports that import `openspec_graph`;
  - `dead_code` as a report that imports neither `openspec_graph` nor vulture,
    and runs vulture as a process.

  `tools/AGENTS.md` MUST stay within `MAX_NESTED_LINES`, with its precedence
  clause and resolving links. `docs/aqa.md` MUST describe both reports beside
  the stage-citation paragraph. Dated records — `CHANGELOG.md`'s released
  sections, the peer reviews, the plan — MUST NOT be edited.
  `docs/next-steps.md` is a living document, not a dated record, and gains the
  one item R-RDS-22 names.
- R-RDS-17: `CHANGELOG.md`'s `[Unreleased]` section MUST carry an `Added`
  entry led by the bold backticked name of this package, in the shape
  R-RDS-10 reads. It MUST name:
  - both targets;
  - the floored dev extra;
  - the confidence key and why it is not the plan's D4 figure;
  - the whitelist and its two stale checks;
  - the four finding kinds;
  - that no header was edited, and the follow-up that owns them;
  - that the spec-status report stays red until
    `settle-package-status-headers` lands.
- R-RDS-18: Every new test MUST carry exactly one of the registered tiers,
  the one `tests/shape_support.py`'s criterion computes. An in-process test of
  either script loads a `tools/` script and is therefore at least
  `integration`, and a process the script itself starts does not count
  (DEC-TSS-017). Every new or edited test module MUST stay within
  `MAX_TEST_MODULE_LINES`. Both scripts MUST join
  `test_gate_script_is_runnable_as_a_script`'s list, and that test MUST gain
  `assert (TOOLS / script).is_file()` before it starts the process — an
  addition, with its name and every other assertion kept — so a listed script
  that does not exist is red, not an accepted exit 2. Every `spec.md` a test
  plants MUST be written through `tests/support.py`'s `write_spec`.
- R-RDS-19: Every guard this spec adds MUST read the file it judges, and MUST
  be written and run red against the tree before the change it covers, with
  the red run recorded in `tasks.md` and never committed as a tree state. Each
  script's entry in the runnable-as-a-script list MUST be run red before that
  script exists, by the presence assertion of R-RDS-18. Each guard MUST also
  be shown red on a planted counter-example:
  - a `Makefile` text whose `pre-pr` composes a report target directly;
  - one that composes it through an intermediate target;
  - one whose report target is missing from `.PHONY`;
  - a docs/hooks.md text with a report target that has no row;
  - one with a row naming no report target;
  - one whose second table would be read as CI rows;
  - a whitelist entry naming no binding;
  - a `pyproject.toml` whose dev extra pins vulture exactly, or lists it
    under `[project] dependencies`;
  - a script text carrying the configured confidence as a numeric literal;
  - a workflow text, and a `Makefile` recipe line, naming vulture.
- R-RDS-20: `tasks.md` MUST record, each dated with its commit and naming
  its command:
  - both reports' complete output at the branch head after the change;
  - the installed vulture version;
  - vulture's output at the plan's figure and at the configured one, before
    the change;
  - the stage-citation report after the change;
  - the stage-citation output before and after the lexer move of R-RDS-24,
    and their diff.

  The record MUST say that its figures include this package's own spec. The
  spec-status output so recorded is the worklist for the follow-up of
  R-RDS-22.
- R-RDS-21: The dead-code report MUST NOT delete, rename, deprecate or
  privatise any symbol, and this package MUST NOT either. Every symbol the
  report lists at landing stays for M4's W5.1–3, and is recorded there as
  this package's measurement.
- R-RDS-22: The rest of W8.5 MUST have a named owner: the follow-up package
  `settle-package-status-headers`, which is the maintainer's.
  `docs/next-steps.md` MUST carry one item for it, in that file's numbered
  item shape. The item MUST say:
  - that in it the maintainer settles each header the spec-status report
    lists;
  - that the maintainer decides whether the vocabulary gains a value meaning
    "shipped";
  - that the maintainer amends `VOCABULARY` in `tools/spec_status.py`, the
    one place the vocabulary is written;
  - that the spec-status report stays non-zero until the follow-up lands,
    and the quiet quarter before any package may make it a gate starts only
    then;
  - that if the follow-up records status anywhere other than the `Status`
    header — a supersession-style record, say — it must teach
    `tools/spec_status.py` to read that record too, or the report stays red
    for good;
  - that before it edits any shipped package's header it must first write
    down the exception to the records convention that DEC-MCO-006,
    DEC-ZCG-003 and DEC-TSS-016 hold;
  - that it decides whether the vocabulary gains a "shipped" value that an
    agent may set at a package's closure, since the drafter is barred only
    from `APPROVED`. Without one, every correctly closed package branch reads
    `draft-but-complete`, and any future gate on the report would be red on
    every closing pull request.

  This package's own `Status` header MUST stay `DRAFT` when its milestones
  close. The pull request MUST ask the maintainer to settle it at merge.
- R-RDS-23: `tools/spec_status.py` MUST read each spec's `Status` header with
  `re`, anchored at the start of a line that begins `> **Status:** `, matched
  case-sensitively, within the header block — the lines before the first `## `
  heading — with the word kept as written. Before it finds the end of the
  header block, and before it matches, it MUST blank every HTML comment
  (`<!-- … -->`), matching across lines and keeping the newlines so line
  structure survives. It MUST do that through `openspec_graph`'s
  `blank_html_comments`, so the report and the speckit rules share one
  comment grammar. A proposal's status line MUST be read the same way:
  anchored at a line that begins `> **Status: `, within the proposal's header
  block, after the same blanking. The script MUST NOT take the header from
  `parse_spec`, whose `STATUS` pattern is unanchored, searched over the raw
  text, and upper-cased. Each of these MUST NOT be read as the header:
  - any line inside an HTML comment, however it is shaped — a single-line
    waiver above the header carrying the phrase, a waiver whose reason spans
    lines and carries a line that begins `> **Status:**`, or a commented-out
    old header above the current one;
  - a lower-case header word, which is read as written and is outside the
    vocabulary;
  - a `**Status:**` phrase anywhere after the header block, in prose or in a
    code example.

  A test in `make test` MUST compare the two readers on the real tree,
  case-insensitively — the anchored word upper-cased against
  `parse_spec(...).status` — and only for the specs where the anchored reader
  finds a header and whose header block holds no HTML comment. Those are the
  specs on which the two readers must agree. The test guards against drift in
  the anchored reader. The form of a header stays a report finding
  (R-RDS-11) and MUST NOT become a test failure. Rule H005 reads the
  unanchored value and has the same leak. Fixing it changes an
  `openspec_graph/` module, which C-RDS-1 excludes, so it MUST be recorded for
  the follow-up and MUST NOT be fixed here.
- R-RDS-24: `workflow_stages` and the stdlib lexer it uses MUST move from
  `tools/stage_citations.py` into `tools/_common.py`, which MUST stay
  stdlib-only. The lexer is the `run:` reader, the shell tokeniser, the
  invocation readers, `WORKFLOW_DIR` and `ReportError`.
  - The lexer MUST take the grammar of a stage as a parameter — a compiled
    pattern in `MAKE_REF`'s shape — rather than import it. Each caller MUST
    pass `openspec_graph`'s `MAKE_REF`, so the grammar has one copy.
  - The moved debug log line MUST carry a neutral label, not
    `stage-citations:`, because the spec-status report logs through it too.
  - `tools/stage_citations.py` MUST import from `_common` only the names it
    uses, and MUST keep its public names with their call shapes, so
    `tests/test_stage_citations.py` passes unedited:
    - `run_scripts(text)`, re-exported explicitly as
      `from _common import run_scripts as run_scripts`, because its tests
      reach it on the module;
    - wrappers that pass `MAKE_REF`, documented together:
      `shell_invocations(script)`, `workflow_invocations(text)` and
      `workflow_stages(root, only=())`.
  - Every import the move leaves unused in `tools/stage_citations.py` — `re`,
    and `shlex` with it — MUST be dropped, so `ruff check tools` stays clean.
  - Its output MUST be byte-identical before and after the move. That MUST
    be shown by a recorded diff of `python tools/stage_citations.py` output,
    as text and as JSON, captured on one tree immediately before and after.
- C-RDS-1: No change to any rule, golden hash, `openspec_graph/` module or
  runtime dependency: the `RULES` tuple, `README.md`'s rules table and
  `tests/baseline_rules.json` are untouched, the `validate`/`graph`/`rules`
  hashes are unmoved, and `[project] dependencies` stays empty.
- C-RDS-2: `make thresholds` MUST print PASS at every milestone. The
  confidence lives only in `pyproject.toml`'s `[tool.specgraph]`, and no
  recipe line, workflow line or new script carries a numeric literal equal to
  it.
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
- C-RDS-8: `tools/dead_code.py` MUST NOT import vulture, `openspec_graph` or
  any `tools/` module but `_common`. `tools/spec_status.py` MUST NOT import
  any module outside the standard library, `openspec_graph` and `_common`.
  `tools/_common.py` stays stdlib-only, with the moved lexer in it.

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
  read from `[tool.specgraph] dead_code_min_confidence`. This supersedes the
  plan's D4 figure of 80, by measurement.
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
  - The key sits in `[tool.specgraph]`, beside `per_file_line_min`, following
    DEC-MCO-009: that table holds this repository's reporting thresholds,
    each read by the script that reports and gating nothing. The first draft
    put it in `[tool.vulture]`, so that a bare vulture run from the root would
    agree with the report. That was false. Vulture takes its trees from the
    command line or from a `paths` key the table did not hold, and
    `python -m vulture` from the root with no path exits 2 asking for one. A
    contributor who names the trees and `tests/` names the confidence too.
  - No `[tool.vulture]` table is added at all (R-RDS-2). Vulture reads that
    table from its working directory, which is the root for the report's one
    run. Any key there — `exclude`, `ignore_names`, `paths` — would act on
    the run that must see every finding to compute staleness (DEC-RDS-004).
    The script passes the confidence on the command line.

  Rejected: 80 (blind to the target's purpose, as measured); 100
  (unreachable code only); a number on the recipe line (the threshold guard
  would fail it, rightly); `[tool.vulture] min_confidence` (the first draft:
  its rationale was false, and the table would sit one key away from
  filtering the report's own run).
- **DEC-RDS-003:** `tests/` counts as a user of the code and is never a
  reported tree, and the reported trees are `[tool.coverage.run] source`'s
  entries.
  - Tests count as a user because the plan's §7 metric this target answers
    to, "Unreferenced symbols", counts references repository-wide. Its three
    are the symbols with "0 refs" anywhere, tests included (§1.2), and its
    companion count — "0 of 405 top-level symbols … unreferenced" — is
    repository-wide too.
  - A symbol only a test uses is therefore invisible to this report, by
    design. At drafting those are:
    - `filter_speckit_by_feature`, `section_body` and `suppressions`, which
      are the plan's separate "Test-only public API" row, decided by W5.2;
    - `duplicate_scoped_floor_keys`, which only tests call.

    They are W5.2's question, not this report's.
  - `main_deprecated` leaves the list because a test calls it
    (`tests/test_cli_surface.py`), and it is live in any case: it is the
    `specgraph` console script (`pyproject.toml:69`), an entry point vulture
    cannot see.
  - Reporting `tests/` would list pytest fixtures, which pytest injects by
    name and vulture cannot see.
  - The reported trees come from `source` because that list is this
    repository's one declaration of the trees it measures; a third tree
    added there is reported without a second edit.

  Rejected: a list of trees in the script (two places for one fact); the two
  trees alone (a report that reads test-only symbols as unreferenced would
  count by a different measure from the §7 row it answers to).
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
  - **Not `ignore_names` in a `[tool.vulture]` table.** Vulture would apply
    it to the report's own run, and its glob patterns can hide more than the
    name they were added for.
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
  - **stdout is the report, stderr is a log.** Vulture writes findings to
    stdout and its complaints to stderr. `ast.parse`, which vulture parses
    with, writes a `SyntaxWarning` for an invalid escape to stderr and still
    succeeds. So stderr beside exit 0 or 3 is a warning about a file vulture
    read, not a failure. It goes to the logger at DEBUG, where
    `PLANLINT_LOG_LEVEL` shows it, and it reaches the message only when the
    exit code says vulture could not run.
  - **An empty tree is not a clean tree.** Measured from the root, vulture
    over a directory with no `.py` file prints nothing and exits 0, and over
    an absent path it exits 1. The first would read as "nothing to report"
    for a tree the report never read. So the script checks each declared tree
    before the process starts, and the second case gets its own message
    rather than vulture's.
  - **A read failure is "could not run".** `read_pyproject_int` and
    `coverage_sources` call `Path.read_text` and raise `OSError` or
    `UnicodeDecodeError` unchanged, which the seven gates sharing them rely
    on. So this script, not `_common`, turns those into its exit 2, naming the
    file, as it does for the whitelist.
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
  `coverage-per-file` already accept. Nothing read is never clean: the
  spec-status report over an `openspec/changes/` that holds no package exits
  2, for the reason DEC-RDS-005 gives for a declared tree with no `.py` file.
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
- **DEC-RDS-008:** this package sets no other package's header, and names the
  owner of the rest of W8.5: the follow-up package
  `settle-package-status-headers`, which is the maintainer's. The report's
  output is its worklist, recorded in `tasks.md`. Four reasons:
  1. **Promotion is a human decision.** `.claude/agents/spec-drafter.md`
     says `APPROVED` is "a human decision after review", and
     `lint-empty-speckit-requirements`' `tasks.md` says the same. The two
     packages that promoted their own header in their implementing pull
     request did it in the maintainer's own commits: `3bc3321`
     (`parse-repo-machinery-structurally`) and `49cb9ed` (`harden-ci-gates`).
     So an agent implementing this package leaves its own header `DRAFT`, and
     the pull request asks the maintainer to settle it at merge, as those two
     show the maintainer doing.
  2. **The records are not edited.** The packages the report flags are on
     `main` or on this branch's unmerged base. This repository's convention
     is that a later package names a shipped package's record and does not
     edit it (DEC-MCO-006, DEC-ZCG-003 and R-ZCG-13, DEC-TSS-016). The one
     in-place amendment, DEC-ASP-007, was of a sibling on the same unmerged
     branch, and that was a plan, not a header.
  3. **No value means shipped.** Within today's two-value vocabulary,
     `APPROVED` is the only settled value, and it means approved after review
     — rule H005 reads it as "not `DRAFT`". So a `draft-but-complete`
     finding is fixed by the maintainer's choice between `APPROVED` and the
     value the follow-up may add. Adding one is a convention change, not a
     hygiene edit: it touches the scaffold template, the drafter, H005, and
     `VOCABULARY` in `tools/spec_status.py`, the named edit point. Until the
     follow-up amends `VOCABULARY`, a header carrying such a word — the
     planted `IMPLEMENTED` case included — is `header-unrecognised`.
  4. **The number is not mechanical.** The plan's "18" was a count of
     `DRAFT` headers, and it is not recoverable mechanically. By the anchored
     grep, 26 of 52 read `DRAFT` at `1c6b8b8`, this package's own among them,
     and the evidence is unanimous for only some.

  Consequences, stated so nobody reads a red report as a defect:
  - The spec-status report exits non-zero until the follow-up lands, and the
    quiet quarter before any package may make it a gate starts only then
    (guardrail 7).
  - This package's own row becomes a finding once its milestones close:
    `DRAFT`, every milestone `[DONE]` and every criterion ticked is
    `draft-but-complete`. That is the report working as designed, and
    settling it is the maintainer's call at merge.
  - The follow-up can turn the report green only on three conditions, which
    `docs/next-steps.md` carries (R-RDS-22):
    - **Where status lives.** If it records status anywhere but the `Status`
      header — a supersession-style record, say — it teaches
      `tools/spec_status.py` to read that record. Otherwise the header the
      report reads never changes, and the report stays red for good.
    - **The written exception first.** Before it edits any shipped package's
      header, it writes down the exception to the records convention of
      reason 2 (DEC-MCO-006, DEC-ZCG-003, DEC-TSS-016). Settling a header is
      otherwise exactly the edit that convention forbids.
    - **A value an agent may set.** It decides whether the vocabulary gains
      a "shipped" value that an agent may set at a package's closure; the
      drafter is barred only from `APPROVED`. Without one, every correctly
      closed package branch reads `draft-but-complete` until a human edits
      it, and any future gate on the report would be red on every closing
      pull request.
  - It is named in `docs/next-steps.md` (R-RDS-22), and not in the plan,
    which is a dated record. It closes the plan's end-state row; this
    package makes the row measurable.
- **DEC-RDS-009:** `tools/spec_status.py` imports `openspec_graph` and
  `_common`, and no sibling script. `tools/AGENTS.md`'s rule is "No
  third-party dependencies, ever. Shared helpers go in `_common.py`", and
  every script in `tools/` today imports only `_common` among its siblings.
  - The workflow lexer becomes a helper two scripts share, so it moves into
    `_common.py` (R-RDS-24). That is the one lexer answering "which stages
    does CI run by name", with its quoting and comment handling, now in the
    place the rule names.
  - `_common` stays stdlib-only, because the seven gate scripts import it in
    a bare runner (`test_common_module_is_stdlib_only`). The lexer decides
    what a stage is through `MAKE_REF`, which lives in `openspec_graph`. So
    the grammar becomes a parameter, and both callers pass `MAKE_REF`: one
    grammar, and no `openspec_graph` import in `_common`.
  - `stage_citations.py` imports the lexer and binds `MAKE_REF` under its
    existing names and call shapes, so its tests run unedited and its output
    is byte-identical, which the recorded diff shows. Its public names are
    every name the module exposes, not only those its tests reach today:
    `shell_invocations` (`tools/stage_citations.py:165`) is one, so it keeps
    a wrapper beside `workflow_invocations` and `workflow_stages`.
    `run_scripts` needs no `MAKE_REF`, so it is re-exported in the redundant
    alias form, which ruff and mypy read as an intended re-export rather than
    an unused import. The module imports nothing else it does not use, and
    the `re` and `shlex` imports that served only the lexer go with it.
  - The moved debug log line takes a neutral label, because two reports log
    through it and a `stage-citations:` line in the spec-status report's log
    would name the wrong report. The label is on the logger only, never in
    the output the recorded diff compares.
  - Verification lines are read by the same parse the rules use, because a
    second reader would count something else — the reason
    `stage_citations.py`'s docstring gives for importing the package. The
    status header is the exception, for DEC-RDS-014's reason.

  Rejected: importing `stage_citations` (the first draft — no script in
  `tools/` imports a sibling, and the rule names `_common.py` as the place for
  shared helpers); a copy of `MAKE_REF`'s pattern in `_common` (two grammars
  that would drift); a stdlib-only reimplementation of both (two answers to
  one question); dropping the workflow column (the plan names it as
  evidence).
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
  and reachability is transitive. Today the module checks the property three
  times: the two report-target tests and `_one_run_violations`' aggregate
  check. All three check only `ci`'s and `pre-pr`'s direct prerequisites, so
  a report composed into `test` would slip into the ladder unseen.
  - One helper defines a report target, and reachability follows
    prerequisites to a fixed point. The definition is a documented target
    whose help text begins "Report", in `.PHONY` and unreachable from the
    aggregates — the shape every existing report target already has. All
    three checks delegate to it.
  - The two tests keep their names and every property they assert, because
    AC-PM-14 and AC-MCO-17 cite them: documented, `.PHONY` and not composed
    by `ci` or `pre-pr`, plus, for the per-file target, its prerequisite and
    recipe. What changes is that "not composed" now means "not reachable".
  - `_one_run_violations` keeps its contract of naming each way back to two
    runs. Its planted Makefile gives its report target help text that begins
    "Report", and the helper's message for a reachable target keeps the
    words `pre-pr composes`, so the existing planted case is unedited.
  - The new test requires `dead-code` and `spec-status` by name, so that it
    is red before they exist.
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
  - An unreadable file is produced by injecting `PermissionError` into
    `Path.read_text`, as `tests/test_stage_citations.py` and
    `tests/test_repo_io.py` already do, never by `chmod`: as root, a mode of
    000 still reads. A planted symlink is skipped under
    `support.supports_symlinks()`.
  - A `spec.md` has no undecodable case. It is read as `parse_spec` reads it,
    with undecodable bytes replaced (R-RDS-12), so the report accepts every
    spec the gate accepts, and `write_spec` encodes UTF-8 in any case. The
    undecodable case is planted in the files written directly, and a
    `spec.md` read failure by the injected `PermissionError`.
- **DEC-RDS-014:** the `Status` header is read anchored, case-sensitively and
  comment-blind, not through `parse_spec`.
  - `STATUS` (`openspec_graph/parse_semantics.py:16`) is unanchored, and
    `parse_spec` searches it over the raw text and upper-cases the match
    (`openspec_graph/parse.py:156`, `:168`). So the first `**Status:**`
    anywhere decides:
    - a waiver comment above the header carrying `**Status:** APPROVED`
      turns a `DRAFT` spec into an `APPROVED` one;
    - a spec with no header, but the phrase in its prose or in a code
      example, reads as having one;
    - `> **Status:** draft` reads as `DRAFT`.

    A report whose purpose is to compare headers cannot use a reader a
    comment can set.
  - Anchoring alone does not close that. `SUPPRESS` matches across lines, so
    a waiver's reason can carry a line that begins `> **Status:**` inside the
    header block. And a maintainer who keeps the old header in a comment
    above the new one leaves a whole header line there. So every HTML comment
    is blanked first, keeping its newlines so line structure survives, and
    the header block is found and matched in what is left. The blanking is
    `blank_html_comments`, which `openspec_graph` already uses for the
    speckit rules: one comment grammar, not a second copy. Like it, the
    reader blanks a comment only where it closes; an unclosed comment is
    malformed Markdown, read the same way by every reader in the repository.
  - The fix then reads only the header block — the lines before the first
    `## ` heading — and only a line that begins `> **Status:** `, keeping the
    word as written. Each case above then gets its honest reading: `DRAFT`,
    `header-unrecognised`, `header-unrecognised`. A proposal's status line is
    read the same way, in its own header block.
  - A test compares the two readers on the real tree, but only where they
    must agree: the anchored reader found a header and the header block holds
    no comment. There the comparison is case-insensitive, because
    `parse_spec` upper-cases. The test guards against drift in the anchored
    reader. It does not judge the headers themselves: a header in an
    unexpected form is the report's finding (R-RDS-11), and making it a test
    failure would be an undeclared gate on header form. Verification lines
    stay with `parse_spec`, because they are what the rules read.
  - H005 has the same leak, through the same value. Fixing it changes an
    `openspec_graph/` module and a rule's behaviour, which C-RDS-1 excludes,
    so it is recorded for the follow-up and not fixed here.

  Rejected: `parse_spec(...).status` (the leak above); stripping waiver
  comments and then searching the raw text (prose, code examples and lower
  case would still read as a header); anchoring without blanking comments (a
  multi-line waiver or a commented-out header still sets it); a comment
  pattern of the script's own (a second grammar beside
  `blank_html_comments`); comparing the two readers on every real spec (a
  gate on header form that no requirement declares).

---

## Acceptance Criteria

- [x] **AC-RDS-1:** `pyproject.toml`'s dev extra lists vulture with a lower
  bound and no exact pin or upper bound, `[project] dependencies` is still
  empty, and Dependabot has no pip ecosystem. No file under `.github/` and no
  `Makefile` recipe line names vulture. Two tests show these red on planted
  files:
  - the dev-extra test names a planted file with an exact pin or a runtime
    entry;
  - the `.github/`-and-recipe test names a planted workflow and a planted
    recipe line that name vulture.

  (R-RDS-1, R-RDS-19, C-RDS-1, DEC-RDS-001)
  _Verified by:_ `pytest -k "test_runtime_dependencies_stay_empty or test_dependabot_does_not_add_a_pip_ecosystem or test_threshold_guard_fails_on_a_pinned_tool_version or test_vulture_is_a_floored_dev_extra_and_never_a_runtime_dependency or test_an_exact_vulture_pin_or_a_runtime_vulture_is_named or test_no_github_file_or_recipe_line_names_vulture"` · stage: `make test`

- [x] **AC-RDS-2:** `[tool.specgraph] dead_code_min_confidence` is set at
  vulture's unused-definition level, and `pyproject.toml` has no
  `[tool.vulture]` table. Neither new script carries a numeric literal equal
  to the configured value; a test holds that and names a planted
  script text that does. The threshold guard prints PASS on the finished tree
  at every milestone and still fails on a planted literal in a recipe.
  (R-RDS-2, R-RDS-19, C-RDS-2, DEC-RDS-002)
  _Verified by:_ `pytest -k "test_threshold_guard_passes_on_a_clean_tree or test_threshold_guard_fails_on_a_hard_coded_coverage_floor or test_the_confidence_lives_only_in_the_specgraph_table"` · stage: `make thresholds`

- [x] **AC-RDS-3:** against canned vulture output on a planted root:
  - a finding under a reported tree is listed in vulture's line form, and
    one under `tests/` is not;
  - a finding whose name is a whitelist entry is suppressed, and an entry
    that suppressed nothing is listed as stale;
  - an unreachable-code finding is listed and never suppressed;
  - a path written with Windows separators names the same tree;
  - the first line names the trees, the confidence, the vulture version and
    the entry count;
  - the script imports nothing from `tools/` but `_common`, and neither
    vulture nor `openspec_graph`.

  Findings are listed sorted by path, then line. (R-RDS-3, R-RDS-4, C-RDS-8,
  DEC-RDS-003, DEC-RDS-004)
  _Verified by:_ `pytest -k "test_the_confidence_is_read_from_the_specgraph_table_and_passed_to_vulture or test_findings_outside_the_reported_trees_are_dropped_and_tests_count_as_users or test_a_whitelisted_name_is_suppressed_and_an_entry_suppressing_nothing_is_stale or test_unreachable_code_is_reported_and_never_whitelisted or test_windows_separators_in_vulture_output_name_the_same_tree or test_findings_are_sorted_by_path_then_line or test_the_header_names_the_trees_the_confidence_the_version_and_the_entries or test_dead_code_imports_only_the_standard_library_and_common"` · stage: `make test`

- [x] **AC-RDS-4 (non-success):** the dead-code script exits 2, with a
  message and no traceback, when:
  - vulture is not installed (with no process started and no import-error
    text on stderr);
  - `dead_code_min_confidence` is absent, or `source` declares no tree;
  - a declared tree is absent, or holds no `.py` file (with no process
    started);
  - `pyproject.toml` or the whitelist cannot be decoded, or `pyproject.toml`
    cannot be read (an injected `PermissionError`), with the file named;
  - vulture exits 1 or 2, with its exit code and stderr in the message;
  - its stdout carries a line in neither shape;
  - a whitelist line is malformed.

  Vulture's stderr carrying a `SyntaxWarning` beside exit 0 or 3 changes
  neither the list nor the exit code. The script exits 1, never 3, on
  findings, and 0 with the saying-so line on none. (R-RDS-3, R-RDS-5,
  DEC-RDS-005, DEC-RDS-006)
  _Verified by:_ `pytest -k "test_dead_code_exits_two_when_it_cannot_run or test_a_declared_tree_that_is_absent_or_holds_no_python_exits_two or test_vulture_stderr_is_logged_and_never_decides_the_exit or test_dead_code_exits_zero_when_nothing_is_listed"` · stage: `make test`

- [x] **AC-RDS-5 (non-success):** every entry of the real whitelist names a
  binding in a reported tree, and a planted whitelist entry naming no binding
  is named by the binding function — with no vulture process started.
  Neither test asserts that an entry suppresses a finding. (R-RDS-6,
  R-RDS-7, R-RDS-19, DEC-RDS-004)
  _Verified by:_ `pytest -k "test_every_dead_code_whitelist_entry_names_a_binding_in_a_reported_tree or test_a_whitelist_entry_naming_no_binding_is_named"` · stage: `make test`

- [x] **AC-RDS-6:** run through `main` with the real process, the installed
  vulture on a planted tree reports a planted unused function under a
  reported tree and the script exits 1. The same tree with that function
  called from a planted `tests/` module exits 0. (R-RDS-3, R-RDS-5,
  R-RDS-18, DEC-RDS-001, DEC-RDS-005)
  _Verified by:_ `pytest -k test_the_installed_vulture_reports_a_planted_unused_function` · stage: `make test`

- [x] **AC-RDS-7:** on planted packages, the spec-status script raises each
  finding of R-RDS-11 on exactly its case:
  - `draft-but-complete` — milestones all `[DONE]` and criteria all ticked
    under a `DRAFT` header — including the task-checkbox form for a package
    with no milestone heading;
  - `settled-but-empty`;
  - `headers-disagree` — a proposal's `proposed` against a spec's `APPROVED`;
  - `header-unrecognised`, in each of these cases:
    - a missing header;
    - an unknown word, `IMPLEMENTED` among them;
    - a lower-case `draft`;
    - a package with no `spec.md`;
    - no header, but `**Status:** APPROVED` in prose;
    - no header, but `**Status:** DRAFT` in a body code example.

  A `DRAFT` header reads `DRAFT` in each of these planted cases:
  - beneath a single-line waiver comment carrying `**Status:** APPROVED`;
  - beneath a waiver whose reason spans lines and carries a line that begins
    `> **Status:** APPROVED`;
  - beneath a commented-out old `APPROVED` header, the comment opening and
    closing on lines of their own.

  On every real spec where the anchored reader finds a header and the header
  block holds no HTML comment, the anchored word, upper-cased, equals
  `parse_spec(...).status`; a spec outside that scope is not compared. A
  symlinked alias of a planted package gives one row, where the filesystem
  supports symlinks. The script prints one text row per package with every
  column, exits 1, and imports nothing from `tools/` but `_common`.
  (R-RDS-9, R-RDS-10, R-RDS-11, R-RDS-12, R-RDS-23, C-RDS-7, C-RDS-8,
  DEC-RDS-007, DEC-RDS-009, DEC-RDS-014)
  _Verified by:_ `pytest -k "test_a_draft_package_whose_tasks_and_criteria_are_complete_is_a_finding or test_task_checkboxes_count_when_a_package_has_no_milestone_headings or test_a_settled_package_with_no_task_done_and_no_criterion_ticked_is_a_finding or test_a_proposal_status_that_disagrees_with_its_spec_header_is_a_finding or test_a_missing_or_unrecognised_status_header_is_a_finding or test_a_status_line_outside_the_header_block_is_never_the_header or test_a_status_line_inside_a_comment_is_never_the_header or test_the_header_reader_agrees_with_parse_spec_on_every_uncommented_real_header or test_a_symlinked_alias_of_a_package_is_one_row or test_spec_status_runs_over_this_repository or test_spec_status_imports_only_the_standard_library_common_and_openspec_graph"` · stage: `make test`

- [x] **AC-RDS-8 (non-success):** none of these raises a finding:
  - a `DRAFT` package with every criterion ticked but a milestone not `[DONE]`;
  - an `APPROVED` package with its milestones done and no criterion ticked;
  - a package named in a CHANGELOG sentence that is not an entry.

  Each is listed with its columns, and the script exits 0 when nothing else
  is found. The script exits 2, with the cause named and no traceback, when:
  - the root has no `openspec/changes/`;
  - `openspec/changes/` holds no package;
  - a `proposal.md`, `tasks.md` or `CHANGELOG.md` cannot be decoded;
  - a `spec.md` or a `tasks.md` cannot be read (an injected
    `PermissionError`).

  A `spec.md` is read as `parse_spec` reads it, with undecodable bytes
  replaced, so no `spec.md` decode failure exits 2; that is read directly. An
  absent `CHANGELOG.md` or workflow directory does not change the exit code.
  (R-RDS-11, R-RDS-12, DEC-RDS-006, DEC-RDS-007, DEC-RDS-013)
  _Verified by:_ `pytest -k "test_partial_evidence_is_listed_and_is_not_a_finding or test_a_changelog_entry_is_read_in_both_shapes_and_a_mention_is_not_an_entry or test_spec_status_exits_two_when_it_cannot_run or test_absent_changelog_and_workflows_are_empty_columns_not_failures"` · stage: `make test`

- [x] **AC-RDS-9:** the workflow column lists a verification-line stage that
  no planted workflow runs, and omits one a planted workflow runs in command
  position. The reused reader's own behaviour — `run:` scripts read, other
  YAML fields ignored, a filter honoured — stays green unedited after the
  reader moves into `_common`. (R-RDS-9, R-RDS-10, R-RDS-24, DEC-RDS-009)
  _Verified by:_ `pytest -k "test_run_block_commands_are_scanned_but_yaml_fields_are_not or test_the_workflow_filter_restricts_who_is_credited or test_a_repository_without_workflows_credits_nobody or test_the_workflow_column_names_verification_stages_no_workflow_runs"` · stage: `make test`

- [x] **AC-RDS-10:** read from the `Makefile`:
  - the `dead-code` and `spec-status` targets are `.PHONY`, documented with
    help text beginning "Report", have no prerequisites, and run exactly
    their script;
  - every report target is unreachable from `ci` and `pre-pr` through
    prerequisites;
  - the two existing report-target tests pass, with their names and every
    property they assert kept, delegating to the one helper;
  - `_one_run_violations` delegates its aggregate check to the same helper,
    and its planted case that composes the report into `pre-pr` is still
    named, unedited;
  - no recipe but `coverage-run`'s invokes pytest;
  - the `ci:` and `pre-pr:` lines are unchanged.

  The `ci:` and `pre-pr:` lines are read directly, against the base.
  (R-RDS-8, R-RDS-13, R-RDS-14, C-RDS-3, DEC-RDS-006, DEC-RDS-011)
  _Verified by:_ `pytest -k "test_makefile_has_matcher_accuracy_report_target or test_makefile_has_coverage_per_file_report_target or test_the_suite_runs_once_through_coverage_run or test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named or test_every_report_target_stays_out_of_the_ladder or test_the_hygiene_report_targets_run_exactly_their_script"` · stage: `make test`

- [x] **AC-RDS-11 (non-success):** through the same helper, each of these
  planted `Makefile` texts is named, with the target and the path by which
  it is reached:
  - a report target composed into `pre-pr` directly;
  - one composed through an intermediate target of `ci`;
  - one missing from `.PHONY`.

  (R-RDS-14, R-RDS-19, DEC-RDS-011)
  _Verified by:_ `pytest -k test_a_report_target_composed_into_the_ladder_is_named` · stage: `make test`

- [x] **AC-RDS-12:** docs/hooks.md's reports section has a row for every
  report target and no row for anything else, and says — in the spec-status
  row or the text under the table — that the spec-status report stays red
  until `settle-package-status-headers` lands. A planted text missing a row,
  and one with a row naming no report target, are each named. The CI-table
  guards still pass on the real file, and a planted second table is not read
  as CI rows. The stays-red sentence is also read directly. (R-RDS-15,
  R-RDS-19, DEC-RDS-008, DEC-RDS-010)
  _Verified by:_ `pytest -k "test_every_hooks_ci_table_row_names_a_job_or_workflow or test_hooks_ci_table_lists_every_ci_job or test_hooks_test_row_names_the_matrix_bounds or test_every_report_target_has_a_row_in_the_hooks_reports_table or test_a_report_target_without_a_hooks_row_is_named or test_a_second_table_in_hooks_is_not_read_as_ci_rows"` · stage: `make test`

- [x] **AC-RDS-13:** `docs/architecture/c4.md` §4, `tools/AGENTS.md` and
  `docs/aqa.md` describe both scripts in their groups with their argv
  convention. `tools/AGENTS.md` stays within its line budget with its
  precedence clause and resolving links, every required document is present
  and linked, and no dated record is edited. The prose is read directly; the
  agent-file budget and the docs gate are the tests. (R-RDS-16)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_agent_index_links_resolve"` · stage: `make docs-check`

- [x] **AC-RDS-14:** `python tools/dead_code.py` and `python
  tools/spec_status.py`, run from a throwaway cwd with no arguments, reach
  their own exit path with 0, 1 or 2 and no load-failure marker on stderr.
  The test first asserts that each listed script is a file, so each entry was
  red before its script existed, and the red runs are recorded. (R-RDS-5,
  R-RDS-12, R-RDS-18, R-RDS-19, DEC-RDS-005)
  _Verified by:_ `pytest -k test_gate_script_is_runnable_as_a_script` · stage: `make test`

- [x] **AC-RDS-15:** every new test carries exactly the tier the criterion
  computes for it, every new or edited test module is within the line bound,
  and no new test writes a planted spec path by hand. The guards that hold
  this are, in `tests/test_suite_shape.py`,
  `test_every_test_carries_exactly_one_tier_marker`,
  `test_every_tier_marker_matches_its_mechanical_criterion` and
  `test_no_test_module_exceeds_the_line_bound`, and, in
  `tests/test_suite_routing.py`,
  `test_no_test_module_writes_a_spec_path_by_hand`, which exist on this
  package's base branch and are cited by name. (R-RDS-18, DEC-RDS-013)
  _Verified by:_ `pytest -k "test_every_test_carries_exactly_one_tier_marker or test_every_tier_marker_matches_its_mechanical_criterion or test_no_test_module_exceeds_the_line_bound or test_no_test_module_writes_a_spec_path_by_hand"` · stage: `make test`

- [x] **AC-RDS-16:** the rule inventory, the golden `validate`/`graph`/`rules`
  hashes and the empty runtime-dependency list are unchanged. (C-RDS-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [x] **AC-RDS-17 (non-success):** the diff deletes, renames, deprecates or
  privatises no symbol; it changes no file of another change package, its
  `Status` header included; and every `pytest -k` selector in every spec under
  `openspec/changes/` still resolves to a test function. (R-RDS-21, C-RDS-6,
  DEC-RDS-008, DEC-RDS-012)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make test`

- [x] **AC-RDS-18:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `Added` entry with the items R-RDS-17 names — among them that the
  spec-status report stays red until `settle-package-status-headers` lands —
  in the bullet shape the spec-status report reads as an entry, and every
  versioned section still links to its release tag. The entry is read
  directly; the test holds the link shape. (R-RDS-17)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [x] **AC-RDS-19:** `tasks.md` records, each dated with its commit and naming
  its command:
  - the red run of every guard;
  - vulture's output before the change at the plan's figure and at the
    configured one;
  - both reports' complete output at the branch head after the change;
  - the installed vulture version;
  - the stage-citation output before and after the lexer move, and their
    empty diff;
  - the stage-citation report after, noting that its figures include this
    spec.

  No requirement or criterion here pins a count another package changes,
  and the package validates clean under the repository's own rules. A review
  property, read directly; the gate confirms the package. (R-RDS-19,
  R-RDS-20, C-RDS-4, DEC-RDS-008)
  _Verified by:_ stage: `make validate`

- [x] **AC-RDS-20:** the whole ladder is green with every floor where it was,
  ruff and strict mypy clean over both new scripts with no new exemption,
  and neither report target run by any step of the ladder or of CI. (C-RDS-3,
  C-RDS-5)
  _Verified by:_ stage: `make pre-pr`

- [x] **AC-RDS-21:** `tools/_common.py` holds `workflow_stages` and its
  lexer, takes the stage grammar as a parameter, and stays stdlib-only; the
  moved debug log line carries a neutral label, not `stage-citations:`.
  `tools/stage_citations.py` imports from `_common` only the names it uses,
  re-exports `run_scripts` in the redundant alias form, keeps
  `shell_invocations(script)`, `workflow_invocations(text)` and
  `workflow_stages(root, only=())` as documented wrappers that pass
  `MAKE_REF`, and no longer imports `re` or `shlex`, so `ruff check tools` is
  clean. Its tests pass unedited. Its text and JSON output are byte-identical
  across the move, by the recorded diff. The imports, the wrappers and the
  label are read directly; ruff runs in the ladder of AC-RDS-20. (R-RDS-24,
  C-RDS-8, DEC-RDS-009)
  _Verified by:_ `pytest -k "test_make_in_command_position_is_an_invocation or test_an_unreadable_workflow_exits_two_rather_than_a_traceback or test_an_unknown_workflow_filter_exits_two or test_common_module_is_stdlib_only"` · stage: `make test`

- [ ] **AC-RDS-22:** `docs/next-steps.md` carries one numbered item for
  `settle-package-status-headers`, which:
  - names the maintainer as its owner;
  - gives its scope — settle each listed header, decide whether the
    vocabulary gains a "shipped" value, amend `VOCABULARY`;
  - says the spec-status report stays non-zero until it lands, and the quiet
    quarter starts only then;
  - says that a status recorded anywhere but the `Status` header must be
    taught to `tools/spec_status.py`, or the report stays red for good;
  - says that the exception to the records convention is written down
    before any shipped package's header is edited;
  - says that the follow-up decides whether a "shipped" value exists that an
    agent may set at a package's closure, and why: without one every closing
    pull request reads `draft-but-complete`.

  This package's own header is `DRAFT` when its milestones close, and the
  pull request asks the maintainer to settle it at merge. No dated record is
  edited. The item and the header are read directly; the docs gate confirms
  the file is present and linked. (R-RDS-16, R-RDS-22, DEC-RDS-008)
  _Verified by:_ stage: `make docs-check`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-RDS-1, 3..12, 14..18, 21 — both scripts' behaviour on planted roots and on the installed vulture, the whitelist binding guard, the report-target and reports-table guards green on the real tree and red on their planted counter-examples, the lexer in `_common` with `stage_citations`' tests unedited, every new test in its computed tier |
| Threshold guard | `make thresholds` | AC-RDS-2 — PASS at every milestone; the confidence only in `[tool.specgraph]` |
| Docs | `make docs-check` | AC-RDS-13, AC-RDS-22 — both scripts described, the agent file within budget, the follow-up's item in the living backlog, every required document linked |
| Self-check | `make validate` | AC-RDS-19 — this package, then the whole tree, validate clean |
| Full | `make pre-pr` | AC-RDS-20 — the ladder green with no floor moved and neither report in it |
