# Tasks: report-dead-code-and-spec-status

Measured at `1c8917c` (the head of `claude/m2-report-targets` at drafting,
stacked on the unmerged PR #42, `shape-the-test-suite`), 2026-10-07.
`openspec_graph/`, the `Makefile` and every `tools/` script except one
docstring line of `tools/_common.py` are byte-identical to `f7118a0` (`main`,
the squash of #41), by `diff -rq` over the two checkouts at `1c8917c`. The
round-1 corrections were measured at `114754c`, this package's first draft,
and the round-2 corrections at `1c6b8b8`, the same day. The only changes
since `1c8917c` are this package's own two commits and the merge of #42's
head, `92077b5`, which is `1c6b8b8`; that merge moved the suite's routing and
loop guards into `tests/test_suite_routing.py`. Every line number below is
re-checked against the branch head before the milestone that uses it; a
sibling package landing first may move a line without moving the fact. Every
number here names the command that produced it.

At `1c8917c`:

- **The gate.** `planlint --target . validate --fail-on ERROR` exits 0 over
  51 specs, 0 error / 0 warn / 0 info. On `f7118a0`, before this draft, it read
  50 specs and exited 0. With this draft written it read 51 there and exited 0,
  as did `--change report-dead-code-and-spec-status`, and
  `python -m pytest tests/test_spec_test_citations.py -q` passed.
- **detect.** `planlint --target . detect` reads 50 change packages, 23 make
  targets, and the floor 97 from `[tool.coverage.report].fail_under`.
- **stage-citations.** `python tools/stage_citations.py` reads 51 specs, 16
  stages cited, 12 on a verification line. Six of those are invoked by no
  scanned workflow: `ci`, `coverage-tools`, `security`, `thresholds`,
  `validate`, `wheel-check`.
- **vulture.** `python -m vulture --version` prints `vulture 2.16` (Python
  3.13.16), and `python -m pip index versions vulture` lists 2.16 as the
  latest. Over the trees:
  - `python -m vulture openspec_graph tools --min-confidence 80` prints
    nothing (exit 0), as does `--min-confidence 100`;
  - at `--min-confidence 60` it prints 12 lines (exit 3);
  - `python -m vulture openspec_graph tools tests --min-confidence 60` prints
    9 lines (exit 3), 7 of them under the two reported trees, in 0.82 s
    timed through `subprocess`.
- **Milestones.** `grep -h "^## Milestone" openspec/changes/*/tasks.md | grep
  -c "\[DONE\]"` prints 136. The header counts are re-measured, anchored, at
  `1c6b8b8` below.
- **The comparison.** A one-off, read-only reading of R-RDS-11's definitions
  (not committed) found:
  - `draft-but-complete`: 9;
  - `settled-but-empty`: 0;
  - `headers-disagree`: 1;
  - `header-unrecognised`: 0;
  - packages with a CHANGELOG entry naming them in either shape: 10 of 50.
- **Coverage.** The checkout's `coverage.json` reads `tools/` 946/981 lines
  and 323/344 branches, and `openspec_graph/` 2276/2292 and 744/762, against
  floors 94/91 and 97/95.

At `1c6b8b8`:

- **The gate.** `planlint --target . validate --fail-on ERROR` exits 0 over
  52 specs, 0 error / 0 warn / 0 info. `planlint --target . detect` reads 51
  change packages and 23 make targets. `python tools/stage_citations.py`
  reads 52 specs, 16 stages cited, 12 on a verification line, and the same
  six invoked by no scanned workflow.
- **Status headers.** `grep -l "^> \*\*Status:\*\* DRAFT"
  openspec/changes/*/specs/*/spec.md | wc -l` prints 26 and the `APPROVED`
  form 26, over 52 specs (`ls openspec/changes/*/specs/*/spec.md | wc -l`),
  this package's own `DRAFT` spec among them. The grep is anchored on the
  header's shape: unanchored, the `APPROVED` form prints 27, because this
  package's spec quotes the phrase in prose. (At `1c8917c` the unanchored
  form printed 25 and 26 over 51, before this spec existed.)

The order is DEC-RDS-011 and R-RDS-19's: measure; extend the report-target
guard and scope the CI-table reader; move the workflow lexer into `_common`
with its output proved unchanged; then each report with its guards seen red
before its code; then the documents, the reports-table guard and the records.
The red runs are recorded here and never committed. Milestones 1 to 4 land in
one pull request on `claude/m2-report-targets`, one commit per milestone.

**Recorded (round-1 corrections, 2026-10-07):**

- *Before the edit.* `planlint --target . validate --fail-on ERROR` at
  `114754c`: exit 0, 52 specs, 0 error / 0 warn / 0 info.
- *Round-1 adversarial review.* The spec-adversary's first pass reviewed
  `114754c` and found one high, three medium and five low findings. All are
  folded in here and in the proposal and spec, before any implementation.
  Ids are kept where the meaning survived. New ids are at the end of each
  range: R-RDS-22 to R-RDS-24, AC-RDS-21 and AC-RDS-22, DEC-RDS-014.
  - *HIGH — W8.5's end state had no owner.* The draft left the header
    follow-up to "a maintainer" with no package, no record and no end. Fixed:
    - The follow-up is named, `settle-package-status-headers`, and is the
      maintainer's: settle each listed header, decide whether the vocabulary
      gains a "shipped" value, and amend `VOCABULARY` in
      `tools/spec_status.py`, the named edit point (DEC-RDS-008, R-RDS-22).
    - `make spec-status` stays non-zero until that package lands, and the
      quiet quarter before any gate starts only then.
    - This package's own header stays `DRAFT` at closure. The report lists it
      as `draft-but-complete` once its milestones close, which is the report
      working as designed, and the pull request asks the maintainer to
      settle it at merge.
    - DEC-RDS-008 cites both precedents, the maintainer's own commits
      `3bc3321` (`parse-repo-machinery-structurally`) and `49cb9ed`
      (`harden-ci-gates`). Its reason 3 now agrees with R-RDS-11: within
      today's two-value vocabulary `APPROVED` is the only settled value, so a
      `draft-but-complete` fix is the maintainer's choice between `APPROVED`
      and the follow-up's new value. The planted `IMPLEMENTED` case stays
      `header-unrecognised` until the follow-up amends `VOCABULARY`.
    - Milestone 3's claim that this package's own row "carries no finding"
      now says that holds only until its own milestones close.
    - Milestone 5 no longer records anything for the plan's M2 row, since
      the plan is a dated record. That record is here and in the
      `docs/next-steps.md` item.
    - One item for the follow-up goes into `docs/next-steps.md`, a living
      document that R-RDS-16 does not forbid. Writing it is outside the
      drafter's write scope, which is this package's directory only. Its text
      is in Milestone 4: the session lead applies it with these corrections,
      or Milestone 4 adds it.
  - *MEDIUM — DEC-RDS-003's reason was wrong.* Restated: tests count as a
    user because §7's "Unreferenced symbols" metric counts references
    repository-wide. A test-only symbol is therefore invisible to this
    report. `filter_speckit_by_feature`, `section_body` and `suppressions`
    are the plan's "Test-only public API" row, tracked by W5.2, and
    `duplicate_scoped_floor_keys` is called only from tests. `main_deprecated`
    is live as the `specgraph` console script. The claim that they "would
    have to be whitelisted", which contradicted R-RDS-6, is gone.
  - *MEDIUM — a waiver comment or prose could set the header.* `STATUS` is
    unanchored and searched over raw text (`openspec_graph/parse.py:156`).
    `tools/spec_status.py` now reads the header with `re` anchored at
    `^> \*\*Status:\*\*`, before the first `## ` heading (R-RDS-23,
    DEC-RDS-014). A planned test asserts that it agrees with
    `parse_spec(...).status` on every real spec. AC-RDS-7 gains the two
    planted cases: a waiver comment carrying `**Status:** APPROVED` above a
    `DRAFT` header reads `DRAFT`, and no header with the phrase in prose is
    `header-unrecognised`. H005 has the same leak and stays out of scope
    under C-RDS-1, recorded beside the follow-up.
  - *MEDIUM — vulture's stderr.* `tools/dead_code.py` parses stdout only.
    Stderr goes to the logger at DEBUG and matters only on vulture exit 1
    or 2, when it is carried in the exit-2 message (R-RDS-4, R-RDS-5,
    DEC-RDS-005). A `SyntaxWarning` on stderr beside exit 0 or 3 is not a
    failure; this is a parametrised planted case in Milestone 2.
  - *LOW — AC-RDS-10 contradicted the tasks.* It now reads "names and every
    asserted property kept". The third copy of the aggregate check, in
    `_one_run_violations`, delegates to the same helper, with
    `_ONE_RUN_MAKEFILE`'s report target given "Report" help text and the
    helper's message keeping `pre-pr composes`. So "extended, not
    duplicated" is true and the existing planted case is unedited (R-RDS-14,
    DEC-RDS-011).
  - *LOW — DEC-RDS-002's placement rationale was false.* A bare `vulture`
    reads no paths from a table that holds none; measured,
    `python -m vulture` from the root exits 2. The key is now
    `[tool.specgraph] dead_code_min_confidence`, following DEC-MCO-009's
    `per_file_line_min`. R-RDS-2, R-RDS-3, R-RDS-5, C-RDS-2, AC-RDS-2,
    DEC-RDS-002, DEC-RDS-004 and the proposal match. Because vulture reads
    `[tool.vulture]` from its working directory, R-RDS-2 now forbids that
    table outright. The value 60 and its reasoning are kept.
  - *LOW — DEC-RDS-009 cited a plan direction that does not exist.* It now
    cites `tools/AGENTS.md:32–33`: no third-party dependencies, and shared
    helpers go in `_common.py`. `workflow_stages` and its lexer move into
    `_common.py`, and `stage_citations.py` imports them. `spec_status.py`
    imports only `_common` and `openspec_graph`, with no sibling. The
    whitelist entries follow the code to `_common.py`. R-RDS-24 requires
    `stage_citations`' output to be byte-identical across the move, by a
    recorded diff.
    - *Found while applying it.* The lexer is not stdlib-only as it stands:
      `shell_invocations` decides what a stage is with
      `openspec_graph`'s `MAKE_REF` (`tools/stage_citations.py:194`), and
      `_common.py` must stay stdlib-only (`test_common_module_is_stdlib_only`).
      The move therefore makes the stage grammar a parameter, `stage_ref`.
      Both callers pass `MAKE_REF`, so there is one grammar and no
      `openspec_graph` import in `_common`. `ReportError` moves with the
      code, because `workflow_stages` raises it.
  - *LOW — R-RDS-19 versus the runnable-list entry.*
    `test_gate_script_is_runnable_as_a_script` (`tests/test_gate_scripts.py`)
    gains `assert (TOOLS / script).is_file()` before it starts the process.
    The change is additive and the name is kept. Each entry is shown red
    before its script exists, so R-RDS-19 needs no exception (R-RDS-18,
    AC-RDS-14).
  - *LOW — untested clauses.* Three tests are planned in Milestone 2:
    - `test_the_confidence_lives_only_in_the_specgraph_table`: the real
      `[tool.specgraph]` holds `dead_code_min_confidence`, there is no
      `[tool.vulture]`, and neither script carries the literal;
    - `test_no_github_file_or_recipe_line_names_vulture`;
    - `test_a_declared_tree_that_is_absent_or_holds_no_python_exits_two`,
      whose empty-tree case would otherwise read "clean" (vulture exits 0
      there).
- *Copilot review on PR #43* (three findings, verified by the session lead):
  - *A — case and body examples.* `parse_spec` upper-cases its match. The
    anchored read matches the header line case-sensitively, within the
    header block, and `parse_spec` is kept for verification lines only
    (R-RDS-9, R-RDS-11, R-RDS-23). Planted cases: a lower-case `draft`
    header, and no header with `**Status:** DRAFT` only in a body code
    example. Both are `header-unrecognised`.
  - *B — package enumeration.* R-RDS-10's packages are
    `detect.profile(root).change_dirs`, which dedupes symlink aliases by
    real path and keeps spec-less packages
    (`openspec_graph/detect.py:707–715`), never a raw glob or `iterdir`. A
    planted symlinked alias gives one row. It is skipped under
    `support.supports_symlinks()`.
  - *C — read failures.* R-RDS-5 and R-RDS-12 now cover an unreadable or
    undecodable `pyproject.toml`, which `read_pyproject_int` and
    `coverage_sources` read directly, and the whitelist and package files.
    Each script translates `OSError` and `UnicodeDecodeError` from its own
    reads into exit 2, naming the file. Planted cases:
    - an undecodable `pyproject.toml` and an undecodable whitelist;
    - the optional unreadable case, for `pyproject.toml`, a `spec.md` and a
      `tasks.md`.

    The unreadable case uses this repository's existing pattern, an injected
    `PermissionError` (`tests/test_stage_citations.py:223–239`). It does not
    use a chmod capability probe, because `tests/support.py` has none, and
    the injection behaves the same on Windows and as root. A planted
    `spec.md` stays decodable: `write_spec` encodes UTF-8, and R-RDS-18 routes
    every planted spec through it (DEC-RDS-013).
- *Also found while applying them.* AC-RDS-3 promised an import check that no
  planned test named. One is now named for each script. A planned test name
  that said `vulture_table` now says `specgraph_table`.
- *After the edit*, with the spec and proposal revised, at 2026-10-07:
  - `planlint --target . validate --fail-on ERROR`: exit 0, 52 specs, 0 / 0
    / 0;
  - the same with `--change report-dead-code-and-spec-status`: exit 0, 1
    spec, 0 / 0 / 0;
  - `python -m pytest tests/test_spec_test_citations.py -q -p
    no:cacheprovider`: exit 0.

**Recorded (round-2 corrections, 2026-10-07):**

- *Before the edit.* `planlint --target . validate --fail-on ERROR` at
  `1c6b8b8`, the merge of #42's head `92077b5` into this branch: exit 0, 52
  specs, 0 error / 0 warn / 0 info.
- *Round-2 adversarial review.* The spec-adversary's second pass reviewed the
  round-1 revision and found three medium and five low findings; one low
  finding is joined by a Copilot finding on PR #43. The session lead decided
  each resolution, and all are applied here and in the proposal and spec,
  before any implementation. Ids are kept where the meaning survived. No id
  is added: every resolution amends an existing requirement, decision or
  criterion.
  - *MEDIUM — a comment could still set the anchored header.* `SUPPRESS`
    matches across lines, so a waiver's reason, or a commented-out old
    header, could put a line beginning `> **Status:**` inside the header
    block. Resolved:
    - Before matching, the reader blanks every HTML comment, across lines and
      keeping the newlines so line structure survives. Only then does it find
      the header block and match. A proposal's status line is read the same
      way (R-RDS-9, R-RDS-23, DEC-RDS-014).
    - AC-RDS-7 gains both planted cases, and both read `DRAFT`: a `DRAFT`
      header under a waiver whose reason carries such a line, and a
      commented-out old `APPROVED` header above a `DRAFT` one.
    - Milestone 3 plans them as
      `test_a_status_line_inside_a_comment_is_never_the_header`, with a third
      case for the proposal line.
  - *MEDIUM — the agreement test was an undeclared gate on header form.* It
    is kept on the real tree and scoped:
    - It compares case-insensitively, the anchored word upper-cased against
      `parse_spec(...).status`.
    - It compares only the specs where the anchored reader found a header
      and the header block holds no comment, which is where the two readers
      must agree.
    - R-RDS-23 says the test guards against drift in the anchored reader,
      and that header form stays a report finding (R-RDS-11), never a test
      failure. DEC-RDS-014 and AC-RDS-7 match.
    - The planned test is renamed
      `test_the_header_reader_agrees_with_parse_spec_on_every_uncommented_real_header`.
      It asserts that it compared at least one spec, so an empty scope cannot
      pass it.
  - *MEDIUM — the hand-off could not turn the report green as written.*
    R-RDS-22's list, the `docs/next-steps.md` item text in Milestone 4,
    DEC-RDS-008's consequences and AC-RDS-22 gain three items:
    - (a) a status recorded anywhere but the `Status` header, such as a
      supersession-style record, must be taught to `tools/spec_status.py`,
      or the report stays red for good;
    - (b) before any shipped package's header is edited, the exception to the
      records convention (DEC-MCO-006, DEC-ZCG-003, DEC-TSS-016) is written
      down first;
    - (c) the follow-up decides whether the vocabulary gains a "shipped"
      value an agent may set at a package's closure, since the drafter is
      barred only from `APPROVED`. Otherwise every correctly closed package
      branch reads `draft-but-complete`, and any future gate would be red on
      every closing pull request.

    The proposal's What Changes and Non-Goals match, and so does Milestone
    5's hand-off.
  - *LOW — "stays red" was missing from two documents.* R-RDS-15 (the
    docs/hooks.md reports section) and R-RDS-17 (the CHANGELOG entry) now
    require the sentence that the spec-status report stays red until
    `settle-package-status-headers` lands. AC-RDS-12 and AC-RDS-18 match.
    Milestone 4 puts the sentence in the spec-status row, in the paragraph
    under the table and in the CHANGELOG bullet.
  - *LOW — the lexer move's imports, joined by Copilot on PR #43.* R-RDS-24,
    DEC-RDS-009, AC-RDS-21 and Milestone 2 now say:
    - `tools/stage_citations.py` imports from `_common` only the names it
      uses. It re-exports `run_scripts` as
      `from _common import run_scripts as run_scripts`, because its tests
      reach it as `sc.run_scripts`. It drops the now-unused `re` import, so
      `ruff check tools` stays clean.
    - The moved debug line takes a neutral label, `workflow-stages:`, not
      `stage-citations:`, because `spec_status` logs through it too.
    - *Copilot finding on #43 (verified by the session lead):*
      `shell_invocations` is a public name of `stage_citations`
      (`tools/stage_citations.py:165`). The promise to keep public names and
      call shapes therefore also covers a `shell_invocations(script)`
      wrapper that passes `MAKE_REF`. It is documented beside the
      `workflow_invocations(text)` and `workflow_stages(root, only=())`
      wrappers.
  - *LOW — stale references since the merge of `92077b5`.* Resolved:
    - `MAX_TEST_MODULE_LINES` is named without a line number.
    - The "only change since" sentence, in the proposal and above, names the
      merge.
    - Milestone 1's suite-shape command also runs
      `tests/test_suite_routing.py`, and Milestones 2 and 3, which plant
      roots and specs, run both modules. AC-RDS-15 names each guard's module.
    - The header-count grep is anchored on `^> \*\*Status:\*\*` everywhere
      it appears, with the figure at `1c6b8b8`. The spec's evidence and
      DEC-RDS-008's reason 4 use it.
  - *LOW — edge cases of `detect.profile(root).change_dirs`.* The Non-Goals
    say that an `archive/` directory under `openspec/changes/` counts as one
    package and reports as `header-unrecognised`. They say the packages
    archived inside it are not seen, and that reading archives belongs to
    W8.2. An `openspec/changes/` holding no package exits 2 with a message,
    consistent with DEC-RDS-005's refusal to read emptiness as clean
    (R-RDS-12, DEC-RDS-006, AC-RDS-8). It is planted in
    `test_spec_status_exits_two_when_it_cannot_run`.
  - *LOW — reading `spec.md`.* A `spec.md` is read as `parse_spec` reads it,
    `utf-8-sig` with undecodable bytes replaced, so the report never refuses
    a spec that `validate` accepts. R-RDS-12's undecodable clause no longer
    names `spec.md`; an `OSError` on it still exits 2. DEC-RDS-013 and
    AC-RDS-8 match.
- *Found while applying them.*
  - `openspec_graph.parse_semantics.blank_html_comments` (`:599`) already
    blanks every HTML comment with newlines kept, and the speckit rules read
    through it (`openspec_graph/rules_speckit.py:111`). R-RDS-23 names it as
    the blanking, so there is one comment grammar and no second copy in
    `tools/`. Like it, the reader blanks a comment only where the comment
    closes; DEC-RDS-014 records that limit.
  - The blanking runs before the end of the header block is found, so a
    `## ` line inside a comment cannot end the block early.
  - `shlex`, like `re`, is used in `tools/stage_citations.py` only by the
    moved lexer (lines 50 and 51 at `1c6b8b8`). R-RDS-24 drops both, since
    either left behind fails `ruff check tools` alike.
  - `stage_citations.py` no longer imports `WORKFLOW_DIR`: only the moved
    `workflow_stages` uses it, and no test reaches `sc.WORKFLOW_DIR`.
  - In the proposal, `:226` after `tools/_common.py:146` read as a line of
    `_common`. It is `pyproject.toml`'s `[tool.specgraph.action_major_floors]`
    header. The reader's own stop is `tools/_common.py:171`, now cited so.
  - A one-off read-only script at `1c6b8b8`, not committed, read every
    `spec.md` with R-RDS-23's reader. No header block holds a comment, and
    the scoped comparison agrees on all 52.
  - AC-RDS-22 lists what the item says, so it gains (a)–(c) with R-RDS-22.
- *After the edit*, with all three files revised, at 2026-10-07:
  - `planlint --target . validate --fail-on ERROR`: exit 0, 52 specs, 0 / 0
    / 0;
  - the same with `--change report-dead-code-and-spec-status`: exit 0, 1
    spec, 0 / 0 / 0;
  - `python -m pytest tests/test_spec_test_citations.py -q -p
    no:cacheprovider`: exit 0;
  - the anchored header grep still prints 26 `DRAFT` and 26 `APPROVED` over
    52 specs.

## Milestone 0 — Grounding pass at the branch head [DONE]

- Re-run the gate and record its exit code before the first edit under
  `openspec/`: `planlint --target . validate --fail-on ERROR`. The drafting
  value is exit 0 over 51 specs at `1c8917c` before this draft, and 52 at
  `114754c` and at `1c6b8b8` with it. Re-read the count here; it moves with
  every sibling.
- Re-measure vulture at the branch head, from the repository root, and record
  each command, exit code and full output:
  - `python -m vulture --version` and `python -m pip index versions
    vulture`. If the index is unreachable, record the refusal and continue
    with the installed version; the floor of DEC-RDS-001 stands on vulture's
    changelog, not on the index.
  - `python -m vulture openspec_graph tools --min-confidence 80`.
  - The same at 60.
  - `python -m vulture openspec_graph tools tests --min-confidence 60`.
  - The edges DEC-RDS-002 and DEC-RDS-005 rest on: `python -m vulture` with
    no path (exit 2 at drafting), over a directory with no `.py` file (exit 0,
    no output) and over an absent path (exit 1).

  The drafting lists are in the proposal. If the three-tree list under the
  two reported trees differs from the drafting seven, stop and re-read
  DEC-RDS-002, DEC-RDS-003 and R-RDS-6 before Milestone 2, and record what
  changed. These are the "before" figures of R-RDS-20.
- Re-measure the named symbols:
  `grep -rnw "has_selector\|precision_pct\|recall_pct\|STATUSES\|STATUS_ERROR\|FindingRecord\|speckit_section_body\|speckit_subsection_body"
  --include=*.py openspec_graph tools tests`. Record each hit, and whether any
  hit outside a definition is code rather than a comment or docstring. A
  reference that appeared since drafting moves that symbol off the dead-code
  list and is recorded, not argued with.
- Re-measure the status evidence:
  - the two anchored header counts,
    `grep -l "^> \*\*Status:\*\* <WORD>" openspec/changes/*/specs/*/spec.md | wc -l`
    for `DRAFT` and `APPROVED`. The anchor matters: an unanchored grep also
    counts this package's own spec, whose prose quotes the phrase;
  - `grep -n "^> \*\*Status:" openspec/changes/*/proposal.md`;
  - the `[DONE]` count;
  - the CHANGELOG entries in the two shapes, by
    `grep -nE '^### .*\(`[a-z0-9-]+`\)$|^- \*\*`[a-z0-9-]+`\.?\*\*' CHANGELOG.md`;
  - `grep -l "(BLOCKING)" openspec/changes/*/specs/*/spec.md`, which printed
    nothing at drafting;
  - whether any spec's header block holds an HTML comment, and whether
    `openspec/changes/` holds an `archive/` directory. Neither did at
    `1c6b8b8`.
- Re-read the sites the guards and the move touch, and note any line that
  moved:
  - `tests/test_ci_makefile.py` 44–57 and 275–293 (the two report-target
    tests), 138–164 (`_one_run_violations`), 217–236 (`_ONE_RUN_MAKEFILE`)
    and 257–262 (its "pre-pr composing the report" case), and the
    `_prerequisites` / `_MAKE_RULE` helpers;
  - `tests/test_ci_workflow.py` 193–207 and 293–330 (the CI-table tests and
    `_hooks_ci_table_cells`);
  - `tests/test_gate_scripts.py` 348–404 and `TOOLS` at 29;
  - `tests/test_stage_citations.py` (the calls into `sc.*`, and the injected
    `PermissionError` at 223–239);
  - `tests/test_enterprise.py:482`, `test_common_module_is_stdlib_only`;
  - `tests/support.py:48`, `supports_symlinks`;
  - `MAX_TEST_MODULE_LINES` in `tests/test_suite_shape.py`, and the routing
    and loop guards in `tests/test_suite_routing.py`;
  - `tests/test_agent_artifacts.py:454`, `MAX_NESTED_LINES`;
  - `tools/stage_citations.py` 46–63 (its imports), 56–88 and 109–236 (the
    lexer and its patterns) and 235 (the debug line's label), and
    `tools/_common.py` 146–181 and 262–300;
  - `openspec_graph/parse.py:119`, `:156` and `:168`; `parse_semantics.py:16`,
    `:51`, `:575` and `:599`; `rules_speckit.py:111`; `detect.py:707–715`;
  - `Makefile` 1 (`.PHONY`), 13–14 (`help`), 45, 79, 82, 91 and 94;
  - `pyproject.toml` 38, 69, 130, 167, 226 and 235–252;
  - `docs/hooks.md` 48, 69–82 and 142;
  - `docs/aqa.md` 193–199;
  - `docs/architecture/c4.md:80`;
  - `docs/next-steps.md` 320–338 (items 21–23, and whether item 24 is
    present);
  - `tools/AGENTS.md` 29–45.

  Then `wc -l tools/AGENTS.md tests/test_ci_makefile.py tests/test_ci_workflow.py
  tests/test_gate_scripts.py`; the drafting values are 59, 300, 392 and 404.
- Record the coverage before the change, from one `make test`: the four
  scoped lines the checkers print.
- Record `make help` and `make stage-citations` before the change.
- **Gate:** `make validate`
  **Recorded (Milestone 0, 2026-10-07, on `6679c2a`):**
  - *The gate, before the first edit under `openspec/`.*
    `planlint --target . validate --fail-on ERROR`: exit 0, 52 specs, 0 error
    / 0 warn / 0 info. `planlint --target . detect`: 51 change packages, 23
    make targets, coverage floor 97 from
    `pyproject.toml:[tool.coverage.report].fail_under`. `make validate`: exit
    0, the same 52 / 0 / 0 / 0.
  - *vulture, before the change* (the "before" figures of R-RDS-20), from the
    root:
    - `python -m vulture --version`: `vulture 2.16`, exit 0.
      `python -m pip index versions vulture` reached the index:
      `INSTALLED: 2.16`, `LATEST: 2.16`.
    - `python -m vulture openspec_graph tools --min-confidence 80`: no
      output, exit 0. The same at `--min-confidence 100`: no output, exit 0.
    - `python -m vulture openspec_graph tools --min-confidence 60`: 12
      lines, exit 3 — `cli.py:1017` `main_deprecated`, `detect.py:596`
      `filter_speckit_by_feature`, `parse_model.py:58` `has_selector`,
      `parse_semantics.py:501` `section_body`, `:510`
      `speckit_section_body`, `:546` `speckit_subsection_body`, `:735`
      `suppressions`, `tools/_common.py:353` `duplicate_scoped_floor_keys`,
      `tools/matcher_accuracy.py:119` `precision_pct`, `:123` `recall_pct`,
      `tools/stage_citations.py:160` `whitespace_split`, `:161`
      `commenters`. The drafting list, unchanged.
    - `python -m vulture openspec_graph tools tests --min-confidence 60`: 9
      lines, exit 3. Under the two reported trees, the drafting seven:
      `has_selector`, `speckit_section_body`, `speckit_subsection_body`,
      `precision_pct`, `recall_pct`, `whitespace_split`, `commenters`. Under
      `tests/`: `tests/conftest.py:18` `_reset_version_cache` (60 %) and
      `tests/test_graft_detection.py:43` `target_is_directory` (100 %).
      DEC-RDS-002, DEC-RDS-003 and R-RDS-6 stand as written.
    - The edges: `python -m vulture` prints "Please pass at least one file or
      directory", exit 2; `python -m vulture docs --min-confidence 60` prints
      nothing, exit 0 (`find docs -name "*.py" | wc -l` prints 0);
      `python -m vulture no_such_tree --min-confidence 60` prints "Error:
      /home/user/planlint/no_such_tree could not be found.", exit 1.
  - *The named symbols.* `grep -rnw
    "has_selector\|precision_pct\|recall_pct\|STATUSES\|STATUS_ERROR\|FindingRecord\|speckit_section_body\|speckit_subsection_body"
    --include=*.py openspec_graph tools tests`: 21 hits, the drafting set.
    `has_selector`, `precision_pct` and `recall_pct` hit their definitions
    only. `STATUSES`, `STATUS_ERROR` and `FindingRecord` hit
    `openspec_graph/report.py` only. The two `speckit_*_body` readers hit
    their definitions and comments or docstrings (`parse_semantics.py:106`,
    `:547`, `:556`, `:649`; `parse_speckit.py:33`;
    `tests/test_parse_speckit.py:92`). No reference in code appeared since
    drafting.
  - *The status evidence.* The anchored header grep prints 26 for `DRAFT`
    and 26 for `APPROVED`, over 52 specs (`ls
    openspec/changes/*/specs/*/spec.md | wc -l`) in 51 packages, this
    package's own `DRAFT` spec among them. `grep -n "^> \*\*Status:"
    openspec/changes/*/proposal.md`: the four drafting proposals, each on
    line 3. The `[DONE]` count: 136. The CHANGELOG grep: 10 entries, five
    bullets (`shape-the-test-suite`, `measure-coverage-once`,
    `harden-ci-workflows`, `select-zero-cost-guards`, `pin-actions-by-sha`)
    and five headings (`add-finding-line-hits`, `add-github-action-contract`,
    `fix-detect-corpus-defects`, `fix-prose-matcher-precision`,
    `add-parser-property-tests`). `grep -l "(BLOCKING)"
    openspec/changes/*/specs/*/spec.md` prints nothing. No spec's or
    proposal's header block holds an HTML comment (a one-off read-only
    script, not committed, reading the lines before the first `## `), and
    `openspec/changes/` holds no `archive/` directory.
  - *The sites.* Every line named above holds at `6679c2a`, `MAX_NESTED_LINES
    = 60` at `tests/test_agent_artifacts.py:454` and `MAX_TEST_MODULE_LINES =
    700` at `tests/test_suite_shape.py:44` among them. `docs/next-steps.md`
    has items 20–23 at lines 309–336 and no item 24; `## Skills / agents` is
    line 338. `wc -l tools/AGENTS.md tests/test_ci_makefile.py
    tests/test_ci_workflow.py tests/test_gate_scripts.py`: 59, 300, 392, 404.
    One fact found here that the plan does not name: besides the two CI-table
    tests, `test_a_hooks_row_naming_no_job_is_named`
    (`tests/test_ci_workflow.py:326–337`, cited by AC-MCO) runs
    `_hooks_ci_table_cells` over a planted table that has no `## CI hooks`
    heading; Milestone 1 records what scoping the reader does to it.
  - *Coverage before the change,* from one `make test` (exit 0, 2 min 55 s):
    `openspec_graph/ line coverage 99.3% (2276/2292) meets floor 97%`,
    `openspec_graph/ branch coverage 97.6% (744/762) meets floor 95%`,
    `tools/ line coverage 96.4% (946/981) meets floor 94%`,
    `tools/ branch coverage 93.9% (323/344) meets floor 91%`.
  - *`make help`*, exit 0: 22 documented targets (`e2e-live` is a target
    the help pattern does not match), with `coverage-per-file`,
    `matcher-accuracy`, `stage-citations`, `skill-manifests` and
    `skill-artifacts` overflowing the fourteen-character column. *`make stage-citations`*, exit 0: `52
    spec(s); 16 stage(s) cited; 12 on a verification line; 6 of those
    invoked by no scanned workflow: ci, coverage-tools, security, thresholds,
    validate, wheel-check`.

## Milestone 1 — The report-target guard extended and the CI-table reader scoped, seen red first [DONE]

- `tests/test_ci_makefile.py`, written before the refactor and run red
  (R-RDS-14, R-RDS-19, DEC-RDS-011). Add three helpers beside
  `_prerequisites`:
  - `_report_targets(makefile_text) -> list[str]`: every documented target
    whose `##` help text begins "Report";
  - `_reachable(makefile_text, start) -> dict[str, list[str]]`: every target
    reachable from `start` through prerequisites, followed to a fixed point,
    each with the path that reaches it;
  - `_report_target_violations(makefile_text, target) -> list[str]`, naming
    each way the target is not a report: no "Report" help text, missing from
    `.PHONY`, or reachable from `ci` or `pre-pr`. The last is worded
    `"<gate> composes the <target> report via <path>"`, so the words
    `pre-pr composes` survive.

  Three call sites delegate:
  - `test_makefile_has_matcher_accuracy_report_target` and
    `test_makefile_has_coverage_per_file_report_target` assert
    `_report_target_violations(...) == []` in place of their repeated
    `.PHONY` and aggregate checks. Their names, docstrings and every other
    assertion are kept, because AC-PM-14 and AC-MCO-17 cite them; the
    per-file test keeps its prerequisite and recipe assertions.
  - `_one_run_violations` replaces its aggregate loop (`:161–163`) with
    `found += _report_target_violations(makefile_text, _REPORT_TARGET)`.
  - `_ONE_RUN_MAKEFILE`'s `coverage-per-file: coverage-run ## a report`
    becomes `## Report the per-file minimum`, so the planted baseline stays
    clean. The parametrised case "pre-pr composing the report" stays
    unedited and is still named.

  Planned tests:
  - `test_every_report_target_stays_out_of_the_ladder`: on the real
    `Makefile`, `_report_targets` includes `matcher-accuracy`,
    `coverage-per-file` and `stage-citations`, and every report target has no
    violation. Milestones 2 and 3 add `dead-code` and `spec-status` to the
    required set.
  - `test_a_report_target_composed_into_the_ladder_is_named`, over planted
    texts: a report target in `pre-pr`'s prerequisites; one reached through
    an intermediate target that `ci` names; one absent from `.PHONY`. Each is
    named with the target and, where reached, the path.

  Record the red run: the planted test red until the helpers exist, and the
  real-tree test red on a deliberately planted ladder edit run locally and
  never committed. Record that
  `test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named`
  is green, unedited, after the delegation.
- `tests/test_ci_workflow.py` (R-RDS-15, DEC-RDS-010): planned
  `test_a_second_table_in_hooks_is_not_read_as_ci_rows`. A planted
  docs/hooks.md text has the CI hooks section and its table, then a later
  `##` section with a table whose first cell is `` `dead-code` ``;
  `_hooks_ci_table_cells` must not return `dead-code`. Run it red against
  today's reader, then scope the reader to the lines between the heading that
  begins `## CI hooks` and the next `## ` heading. Its docstring says so.
  `test_hooks_ci_table_lists_every_ci_job` and
  `test_every_hooks_ci_table_row_names_a_job_or_workflow` stay green unedited.
- Tiers: mark each new test with the tier `tests/shape_support.py` computes —
  `integration` for a test that reads the real `Makefile` or docs, and
  whatever the criterion says for a test that only calls a helper on a
  planted string. Run
  `python -m pytest tests/test_suite_shape.py tests/test_suite_routing.py tests/test_ci_makefile.py tests/test_ci_workflow.py -q`
  and record. If the criterion disagrees with a mark, the mark moves, never
  the criterion.
- **Gate:** `make test`
  **Recorded (Milestone 1, 2026-10-07, on `18b902f` + the Milestone 1 tree):**
  - *Red first: the report-target guard.* The two planned tests were written
    before any helper. `python -m pytest tests/test_ci_makefile.py -q -p
    no:cacheprovider -o addopts="" -k "report_target_stays_out or
    composed_into_the_ladder"`: 5 failed —
    `test_every_report_target_stays_out_of_the_ladder` with `NameError: name
    '_report_targets' is not defined`, and each of the four planted cases of
    `test_a_report_target_composed_into_the_ladder_is_named` with `NameError:
    name '_report_target_violations' is not defined`. The planted cases are
    the plan's three — `pre-pr` composing the report directly, `ci`
    reaching it through `test`, and the target missing from `.PHONY` — and a
    fourth, help text that does not begin "Report". The intermediate case is
    named twice, once per aggregate: `ci composes the audit report via ci ->
    test -> audit` and `pre-pr composes the audit report via pre-pr -> ci ->
    test -> audit`.
  - *The helpers.* `_phony_targets`, `_report_targets`, `_reachable`
    (breadth-first to a fixed point, so each path is the shortest) and
    `_report_target_violations`, beside `_prerequisites`. With them both new
    tests pass.
  - *The real-tree test red on a planted ladder edit,* run locally on a copy
    of the `Makefile` and restored by copying it back (`git diff --stat
    Makefile` then printed nothing; never committed):
    `coverage-tools: coverage-run matcher-accuracy`. The new test failed with
    `pre-pr composes the matcher-accuracy report via pre-pr -> coverage-tools
    -> matcher-accuracy`. `test_makefile_has_matcher_accuracy_report_target`,
    still reading direct prerequisites only at that point, passed on the same
    plant — the gap DEC-RDS-011 names.
  - *The delegation.* `test_makefile_has_matcher_accuracy_report_target` and
    `test_makefile_has_coverage_per_file_report_target` assert
    `_report_target_violations(...) == []` in place of their `.PHONY` and
    aggregate checks, with names, docstrings and every other assertion kept.
    `_one_run_violations` ends `found += _report_target_violations(makefile_text,
    _REPORT_TARGET)`, and `_ONE_RUN_MAKEFILE`'s report target reads `##
    Report the per-file minimum`.
    `test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named`:
    6 passed, unedited; its "pre-pr composing the report" case is named by
    the helper's `pre-pr composes the coverage-per-file report via pre-pr ->
    coverage-per-file`.
  - *Red first: the CI-table reader.* `python -m pytest
    tests/test_ci_workflow.py -q -p no:cacheprovider -o addopts="" -k
    second_table` against the unscoped reader: 1 failed, `assert ['fast',
    'test', 'release', 'dead-code'] == ['test', 'release']`. The planted text
    holds a table before the CI hooks section and one after it. The reader now
    reads only the section under the heading that begins `## CI hooks`, up to
    the next `## ` heading, through `tests.support.markdown_section`. That
    helper is shared because Milestone 4's reports-table reader needs the
    same cut. The reader's docstring says so.
    `test_hooks_ci_table_lists_every_ci_job` and
    `test_every_hooks_ci_table_row_names_a_job_or_workflow` stay green
    unedited.
  - *Found while applying it.* Scoping turned
    `test_a_hooks_row_naming_no_job_is_named` (AC-MCO's citation, not named by
    this plan) red: `assert [] == ['gone-job']`. Its planted table had no
    heading, so under a reader that reads the CI hooks section only it is no
    CI table at all. Its planted text gains the line `## CI hooks
    (`.github/workflows/`)` above the table. Its name, docstring and
    assertion are unchanged, and it is green.
  - *Tiers and bounds.* `python -m pytest tests/test_suite_shape.py
    tests/test_suite_routing.py tests/test_ci_makefile.py
    tests/test_ci_workflow.py -q -p no:cacheprovider`: 87 passed. The
    real-tree test is `integration`; the two planted tests are `unit`, which
    the criterion computes, since they reach no tree path. `wc -l`:
    `tests/test_ci_makefile.py` 423, `tests/test_ci_workflow.py` 431,
    `tests/support.py` 373.
  - *Lint.* The first write tripped ruff's `SIM102` (a nested `if` in
    `_report_targets`); the helper was restructured, not waived. `make lint`:
    exit 0. `make thresholds`: PASS.
  - *Gate.* `make test`: exit 0, with the four scoped lines unchanged from
    Milestone 0 (`openspec_graph/` 2276/2292 and 744/762, `tools/` 946/981
    and 323/344).

## Milestone 2 — The workflow lexer moved into `_common`, then the dead-code report, its guards seen red first [DONE]

- The lexer move (R-RDS-24, DEC-RDS-009), first and on its own:
  - Capture before, outside the tree (the session's scratch directory):
    `python tools/stage_citations.py > before.txt` and
    `python tools/stage_citations.py --format json > before.json`.
  - Move `WORKFLOW_DIR`, `ReportError`, `_RUN_KEY`, `_BLOCK_INDICATOR`,
    `_YAML_QUOTED`, `_SHELL_SEPARATORS`, `_SHELL_ASSIGNMENT`, `run_scripts`,
    `_shell_tokens`, `shell_invocations`, `workflow_invocations` and
    `workflow_stages` into `tools/_common.py`, with their comments.
    `shell_invocations`, `workflow_invocations` and `workflow_stages` gain a
    keyword-only `stage_ref: re.Pattern[str]`, the compiled pattern that
    fullmatches `` `make <word>` `` with the stage in group 1. It replaces
    the `MAKE_REF` import, and `_common` imports `shlex` and nothing outside
    the standard library. The debug line in `workflow_stages` takes the
    neutral label `workflow-stages:` in place of `stage-citations:`, because
    `spec_status` logs through it too. That is the move's one change of
    text, and it is on the logger, not in the output the diff compares.
  - `tools/stage_citations.py` imports from `_common` only the names it uses:
    - `logger` and `repo_root`, as today, and `ReportError`, which
      `spec_files`, `build_rows` and `main` still raise or catch;
    - `run_scripts`, re-exported in the redundant alias form,
      `from _common import run_scripts as run_scripts`, because
      `tests/test_stage_citations.py` reaches it as `sc.run_scripts`;
    - the three lexer functions it wraps, under private aliases, so its own
      names stay the wrappers.

    It keeps `shell_invocations(script)`, `workflow_invocations(text)` and
    `workflow_stages(root, only=())` as one-line wrappers that pass
    `stage_ref=MAKE_REF`, documented together in one comment or docstring
    that says where the lexer now lives. It does not import `WORKFLOW_DIR`,
    which only the moved code uses. It drops `import re` and `import shlex`,
    which only the moved lexer used.
  - Run `python -m pytest tests/test_stage_citations.py -q` unedited and
    `python -m pytest tests/test_enterprise.py -q -k
    test_common_module_is_stdlib_only`, and record both green.
  - Record that the wrapper nobody's test reaches still answers:
    `python -c "import sys; sys.path.insert(0, 'tools'); import stage_citations as sc; print(sorted(sc.shell_invocations('make test && echo make lint')))"`
    prints `['test']`.
  - Capture after, as before, then `diff before.txt after.txt` and
    `diff before.json after.json`. Record both exit codes and that both
    diffs are empty; a non-empty diff is a regression, fixed before
    anything else lands.
  - Run `ruff check tools` and `mypy tools`, and record both clean. An
    unused-import finding in `tools/stage_citations.py` is the move left
    half-done, not a warning to waive.
- `tests/test_dead_code.py` (new), written before the script and run red
  (R-RDS-1 to R-RDS-7, R-RDS-19). In-process through `load_tool` /
  `run_tool_main`, against roots planted under `tmp_path` — a
  `pyproject.toml` with `[tool.coverage.run] source` and `[tool.specgraph]
  dead_code_min_confidence`, a `tools/dead_code_whitelist.txt`, and the
  trees — with the vulture runner injected where the test is about parsing.
  Planned tests, named here so the verification lines can be re-pointed:
  - `test_vulture_is_a_floored_dev_extra_and_never_a_runtime_dependency`:
    the real `pyproject.toml` through `read_pyproject()` — the `dev` extra
    holds `vulture>=` and no `==` or upper bound, and `dependencies` holds no
    vulture.
  - `test_an_exact_vulture_pin_or_a_runtime_vulture_is_named`: the same
    helper on planted texts.
  - `test_no_github_file_or_recipe_line_names_vulture` (R-RDS-1): every file
    under the real `.github/`, and every tab-indented line of the real
    `Makefile`, is free of the word `vulture`. A planted workflow text with
    `pip install vulture` and a planted recipe line
    `\tpython -m vulture tools` are each named.
  - `test_the_confidence_lives_only_in_the_specgraph_table` (R-RDS-2,
    C-RDS-2): checked against the real tree.
    - `read_pyproject_int(pyproject, "[tool.specgraph]",
      "dead_code_min_confidence")` returns an integer.
    - The real `pyproject.toml` has no `[tool.vulture]` header line.
    - No `ast.Constant` in `tools/dead_code.py` equals that integer.
      Milestone 3 adds `tools/spec_status.py`.
    - A planted script text carrying it is named.
  - `test_dead_code_imports_only_the_standard_library_and_common` (C-RDS-8):
    every import root in `tools/dead_code.py` is in
    `sys.stdlib_module_names`, or is `_common`.
  - `test_the_confidence_is_read_from_the_specgraph_table_and_passed_to_vulture`:
    the argv the runner receives carries `--min-confidence` with the planted
    value and the planted `source` trees, plus `tests` when it exists.
  - `test_findings_outside_the_reported_trees_are_dropped_and_tests_count_as_users`.
  - `test_a_whitelisted_name_is_suppressed_and_an_entry_suppressing_nothing_is_stale`.
  - `test_unreachable_code_is_reported_and_never_whitelisted`.
  - `test_windows_separators_in_vulture_output_name_the_same_tree`.
  - `test_the_header_names_the_trees_the_confidence_the_version_and_the_entries`.
  - `test_dead_code_exits_zero_when_nothing_is_listed`.
  - `test_vulture_stderr_is_logged_and_never_decides_the_exit` (R-RDS-5),
    parametrised over the injected runner's result:
    - exit 0, empty stdout, stderr `x.py:1: SyntaxWarning: invalid escape
      sequence '\d'`: exit 0, with the saying-so line;
    - exit 3, one finding on stdout and the same stderr: exit 1, listing
      exactly that finding;
    - exit 1, stderr `x.py:3: invalid syntax`: exit 2, with `1` and that
      text in the message.

    In the first two cases the stderr text is in the DEBUG log, read through
    `support.captured_logger`, and on neither of the script's own streams.
  - `test_dead_code_exits_two_when_it_cannot_run`, parametrised over:
    - vulture absent (`find_spec` patched to `None`, and the runner asserted
      never called);
    - `dead_code_min_confidence` absent;
    - no `source` tree;
    - vulture exit 1, and vulture exit 2;
    - a stdout line in neither shape;
    - a whitelist line with no reason;
    - an undecodable `pyproject.toml` (bytes `b"\xff"` in it);
    - an undecodable whitelist;
    - an unreadable `pyproject.toml` (a `PermissionError` injected into
      `Path.read_text`, as `tests/test_stage_citations.py:223–239` does).

    Each asserts exit 2, no `Traceback` on stderr, and, where a file is the
    cause, its name in the message.
  - `test_a_declared_tree_that_is_absent_or_holds_no_python_exits_two`
    (R-RDS-5), parametrised: the tree absent; the tree present and holding
    only a `README.md`. Each exits 2 naming the tree, with the runner
    asserted never called.
  - `test_every_dead_code_whitelist_entry_names_a_binding_in_a_reported_tree`:
    the real tree, through `unbound_whitelist_entries`, with no vulture
    process.
  - `test_a_whitelist_entry_naming_no_binding_is_named`: planted.
  - `test_the_installed_vulture_reports_a_planted_unused_function`: the real
    process on a planted tree. It exits 1 naming the function, then exits 0
    once a planted `tests/test_x.py` calls it. There is no skip, for
    DEC-RDS-013's reason.

  All of these load a `tools/` script or read this repository and are
  `integration` by the criterion, except any that only exercise a helper on
  planted text, which take what the criterion computes. Record the red run:
  `FileNotFoundError` from `load_tool` before the script exists. Then
  `wc -l tests/test_dead_code.py` against `MAX_TEST_MODULE_LINES`, and run
  `python -m pytest tests/test_suite_shape.py tests/test_suite_routing.py -q`
  and record it green: the tier, line-bound and routing guards over the new
  module.
- `tests/test_ci_makefile.py`: add `dead-code` to
  `test_every_report_target_stays_out_of_the_ladder`'s required set and run
  it red ("dead-code is not a report target") before the target exists.
- `tests/test_gate_scripts.py` (R-RDS-18, R-RDS-19): in
  `test_gate_script_is_runnable_as_a_script`, add
  `assert (TOOLS / script).is_file(), f"{script} is listed but absent"` as
  the first statement, before the process starts. Keep the name, docstring
  and every other assertion. Add `"dead_code.py"` to the list. Run it and
  record the red run: `dead_code.py` fails the presence assertion, and every
  other entry is green.
- `pyproject.toml` (R-RDS-1, R-RDS-2, DEC-RDS-001, DEC-RDS-002):
  - In the `dev` extra, `"vulture>=2.15",` after `"hypothesis",`, with the
    extra's comment gaining a paragraph: dev-only like `hypothesis`; floored,
    not pinned — exit code 3 means "dead code found" from 2.9, Python 3.14 is
    supported from 2.15, pip leaves a satisfied bare requirement alone, and a
    floor needs no update bot.
  - In `[tool.specgraph]`, after `per_file_line_min`,
    `dead_code_min_confidence = 60` under a comment. The comment says:
    - it is vulture's level for an unused function, method, class, property,
      attribute or variable;
    - it is read by `tools/dead_code.py`, which passes it to vulture on the
      command line, and it is a reporting threshold that gates nothing;
    - it is not the plan's 80, which reports nothing over the two trees;
    - there is deliberately no `[tool.vulture]` table, because vulture would
      apply one to the report's own run.

  Run `python tools/check_no_hardcoded_thresholds.py` and record PASS. Run
  `planlint --target . detect` and record that the floor locator is
  unchanged.
- `tools/dead_code.py` (R-RDS-3 to R-RDS-7, DEC-RDS-003 to DEC-RDS-005):
  stdlib only, with `sys.path` bootstrapped for `_common` as its siblings do.
  `logger`, `repo_root`, `read_pyproject_int`, `coverage_sources`,
  `SCOPED_FLOOR_SECTION` (the `[tool.specgraph]` header) and `ReportError`
  come from `_common`.
  - `CONFIDENCE_KEY = "dead_code_min_confidence"`, `USAGE_ONLY = ("tests",)`
    and `WHITELIST = Path("tools") / "dead_code_whitelist.txt"`.
  - `Finding(path, line, message, name)`, with `name` set only for
    `unused <kind> '<name>'` messages.
  - `parse_line(text) -> Finding | None`, where `None` means neither shape.
  - `read_config(root) -> tuple[int, list[str]]`, the confidence and the
    trees. It raises `ReportError` naming `pyproject.toml` on an `OSError`
    or `UnicodeDecodeError` from `_common`'s readers, and on an absent key or
    no tree.
  - `check_trees(root, trees)`, raising `ReportError` naming the first tree
    that is not a directory holding a `*.py` file.
  - `read_whitelist(path) -> dict[str, str]`, name to reason, raising
    `ReportError` on a malformed line, and naming the file on an `OSError`
    or `UnicodeDecodeError`.
  - `unbound_whitelist_entries(root) -> list[str]`, the `ast` walk over every
    reported tree's `*.py` for bound names.
  - `run_vulture(root, trees, confidence) -> tuple[int, str, str]`, running
    `subprocess.run([sys.executable, "-m", "vulture", *trees, *usage,
    "--min-confidence", str(confidence)], cwd=root, capture_output=True,
    text=True, check=False)`.
  - `build_report(...) -> tuple[list[Finding], list[str]]`, giving the listed
    findings and the stale entries, from stdout alone.
  - `main(argv, run=run_vulture) -> int`, with argparse over `argv[1:]` and
    `--root`. It logs vulture's stderr at DEBUG. On exit 1 or 2 it raises
    `ReportError` carrying the code and the stderr. Then it prints the header
    line, the findings in vulture's form and a `stale whitelist entries:`
    block, and applies the exit contract of R-RDS-5, with `ReportError`
    mapped to 2 and its message on stderr.

  The docstring states the report's contract, the two halves of staleness,
  why vulture runs as a process, why stderr is a log, and why an empty tree
  is not clean. Run `ruff check tools/dead_code.py` and `mypy tools` and
  record both clean.
- `tools/dead_code_whitelist.txt` (R-RDS-6): a two-line header comment
  saying what an entry is and is not for, then `whitespace_split  # set on a
  shlex.shlex lexer in tools/_common.py (the workflow lexer) and read by the
  standard library` and `commenters  # likewise`. Nothing that is unused goes
  here.
- `Makefile`: add `dead-code` to `.PHONY`, and `dead-code: ## Report
  unreferenced code under the coverage source trees (vulture) — a report, not
  a gate` with the recipe `python tools/dead_code.py`. The `ci:` and `pre-pr:`
  lines are unchanged. Confirm `make thresholds` PASS and that `make help`
  lists the target.
- Run `make dead-code` at the branch head and record its complete output and
  exit code here. At drafting the list was expected to be `has_selector`,
  `speckit_section_body`, `speckit_subsection_body`, `precision_pct` and
  `recall_pct`, with no stale entry, exit 1. Record what it prints, not what
  was expected.
- Run `make test` and `make coverage-per-file`. Record the four scoped
  figures and whether `tools/dead_code.py` or `tools/_common.py` is on the
  per-file list. A floor that would fail is answered with a test, never a
  lower floor (C-RDS-5).
- **Gate:** `make test`
  **Recorded (Milestone 2, 2026-10-07, on `b40f9f1` + the Milestone 2 tree):**
  - *The lexer move, first and alone.* Before, outside the tree:
    `python tools/stage_citations.py > before.txt` (exit 0) and `python
    tools/stage_citations.py --format json > before.json` (exit 0). The moved
    names went to `tools/_common.py` with their comments: `WORKFLOW_DIR`,
    `ReportError`, `_RUN_KEY`, `_BLOCK_INDICATOR`, `_YAML_QUOTED`,
    `_SHELL_SEPARATORS`, `_SHELL_ASSIGNMENT`, `run_scripts`,
    `_shell_tokens`, `shell_invocations`, `workflow_invocations` and
    `workflow_stages`. The last three take a keyword-only `stage_ref:
    re.Pattern[str]`, and `_common` gains `import shlex` and `from
    collections.abc import Sequence`, both stdlib. The debug line reads
    `workflow-stages: %s invokes %s`. `tools/stage_citations.py` imports
    `ReportError`, `logger` and `repo_root`, re-exports `run_scripts as
    run_scripts`, and imports the three lexer functions under private
    aliases. Its `shell_invocations(script)`, `workflow_invocations(text)`
    and `workflow_stages(root, only=())` are one-line wrappers passing
    `stage_ref=MAKE_REF`, documented in one comment above them. It no longer
    imports `re`, `shlex` or `WORKFLOW_DIR`.
    - `python -m pytest tests/test_stage_citations.py -q -o addopts=""`
      unedited: 51 passed. `python -m pytest tests/test_enterprise.py -q -o
      addopts="" -k test_common_module_is_stdlib_only`: 1 passed.
    - `python -c "import sys; sys.path.insert(0, 'tools'); import
      stage_citations as sc; print(sorted(sc.shell_invocations('make test
      && echo make lint')))"` prints `['test']`.
    - After, captured the same way (both exit 0): `diff before.txt
      after.txt` exit 0 and `diff before.json after.json` exit 0, both
      empty. `PLANLINT_LOG_LEVEL=DEBUG python tools/stage_citations.py`
      logs `DEBUG planlint.tools: workflow-stages: ci.yml invokes
      ['docs-check', 'e2e-live', 'lint', 'test', 'typecheck']`.
    - `ruff check tools`: all checks passed. `mypy tools`: no issues in 13
      source files.
  - *Red first: `tests/test_dead_code.py`,* written before the script and
    before the `pyproject.toml` edit. `python -m pytest
    tests/test_dead_code.py -q -p no:cacheprovider -o addopts="" -rA`: 30
    failed, 7 passed. 26 failed with `FileNotFoundError: [Errno 2] No such
    file or directory: '/home/user/planlint/tools/dead_code.py'` from
    `load_tool` (or the import test's read). The dev-extra guard failed
    with `the dev extra lists vulture 0 times, not once: []`. Two failed with
    `[tool.specgraph] dead_code_min_confidence is not an integer`: the
    confidence guard, and the installed-vulture test, which reads the
    configured value. The 7 that passed are the six planted cases of the
    dev-extra guard and `test_no_github_file_or_recipe_line_names_vulture`,
    whose planted workflow and recipe are named inside it. That guard was
    shown red on the real tree with a local plant, reverted with `git
    checkout .github/workflows/ci.yml` and never committed: a line `# pip
    install vulture` appended to `ci.yml` gave `assert ['ci.yml:419'] ==
    []`.
  - *Red first: the two list entries.*
    `test_every_report_target_stays_out_of_the_ladder` with `dead-code`
    required: `Left contains one more item: 'dead-code is not a report
    target'`. `test_gate_script_is_runnable_as_a_script` with the presence
    assertion first and `"dead_code.py"` listed: 1 failed, `AssertionError:
    dead_code.py is listed but absent`, and the other 12 entries passed.
  - *`pyproject.toml`.* `"vulture>=2.15",` after `"hypothesis",` under the
    extra's comment paragraph, and `dead_code_min_confidence = 60` after
    `per_file_line_min` under its comment. `python
    tools/check_no_hardcoded_thresholds.py`: `PASS: no hard-coded thresholds
    in Makefile or workflow YAML`. `planlint --target . detect`: `coverage
    floor 97 from pyproject.toml:[tool.coverage.report].fail_under`,
    unchanged. `python -m pip install "vulture>=2.15"`: `Requirement already
    satisfied: vulture>=2.15 … (2.16)`.
  - *The script, the whitelist and the target.* `tools/dead_code.py` as
    planned, with one change of shape, recorded as a deviation. The
    command is built by `vulture_argv(root, trees, confidence)` and run by
    `run_vulture(root, argv)`; `main(argv, run=run_vulture)` hands the
    injected runner that argv. So
    `test_the_confidence_is_read_from_the_specgraph_table_and_passed_to_vulture`
    asserts the argv the runner receives, `tests` included only when it
    exists, as the plan words it. The plan's `run_vulture(root, trees,
    confidence)` would have built `tests` inside the real runner, out of the
    injected one's sight. The body of `main` is `report(root, run)`, with
    `ReportError` mapped to 2. `tools/dead_code_whitelist.txt` has its
    two-line header and the two entries. The `Makefile` gains `dead-code` in
    `.PHONY` and the target with the planned help text and recipe; the
    `ci:` and `pre-pr:` lines are unchanged. `make thresholds`: PASS. `make
    help` lists `dead-code      Report unreferenced code under the coverage
    source trees (vulture) — a report, not a gate`.
    `ruff check tools tests`: all checks passed. `mypy tools`: no issues in
    14 source files.
  - *Beyond the plan's list.* `test_findings_are_sorted_by_path_then_line`
    holds R-RDS-4's sort clause, which no planned test named, and a blank
    stdout line. The plan's unreadable-`pyproject.toml` and vulture-absent
    cases are parametrised cases of `test_dead_code_exits_two_when_it_cannot_run`
    (10 cases), through a spoiler that takes `monkeypatch`.
  - *Green.* `python -m pytest tests/test_dead_code.py tests/test_ci_makefile.py
    tests/test_gate_scripts.py tests/test_stage_citations.py -q -o
    addopts=""`: 146 passed. `python -m pytest tests/test_suite_shape.py
    tests/test_suite_routing.py -q -p no:cacheprovider`: 52 passed — every
    new test carries the tier the criterion computes. The six planted
    dev-extra cases are `unit`; every other new test loads the script or
    reads the tree and is `integration`. The installed-vulture test is
    `integration` too, because the vulture process is started by the script
    under test (DEC-TSS-017). `wc -l`: `tests/test_dead_code.py` 582,
    `tests/test_gate_scripts.py` 409, `tests/test_ci_makefile.py` 428.
  - *`make dead-code` at the branch head* (`b40f9f1` + this tree; `python
    tools/dead_code.py` exits 1, which `make` reports as `make: ***
    [Makefile:98: dead-code] Error 1` and exit 2; 0.67 s by `time`):

    ```
    python tools/dead_code.py
    dead-code: openspec_graph, tools at confidence 60 (vulture 2.16; tests/ read as a user); 2 whitelist entries read
    openspec_graph/parse_model.py:58: unused property 'has_selector' (60% confidence)
    openspec_graph/parse_semantics.py:510: unused function 'speckit_section_body' (60% confidence)
    openspec_graph/parse_semantics.py:546: unused function 'speckit_subsection_body' (60% confidence)
    tools/matcher_accuracy.py:119: unused method 'precision_pct' (60% confidence)
    tools/matcher_accuracy.py:123: unused method 'recall_pct' (60% confidence)
    5 unreferenced symbols; 0 stale whitelist entries
    ```

    The drafting expectation, exactly: the five symbols, no stale entry,
    exit 1. Both whitelist entries suppressed a finding, now at
    `tools/_common.py`, where the lexer moved.
  - *Coverage.* `make test`, on the tree this record closes: exit 0.
    `openspec_graph/ line coverage 99.3% (2276/2292) meets floor 97%`,
    `openspec_graph/ branch coverage 97.6% (744/762) meets floor 95%`,
    `tools/ line coverage 96.5% (1128/1169) meets floor 94%`, `tools/ branch
    coverage 94.4% (385/408) meets floor 91%` (1127/1169 and 384/408 before
    the sort test gained its blank line). Per file: `tools/dead_code.py` 97 % (`vulture_version`'s
    missing-metadata branch, the not-a-directory root and the `__main__`
    line are unrun), `tools/_common.py` 98 % and
    `tools/stage_citations.py` 97 %. The one new miss there is the
    `shell_invocations` wrapper, which no test reaches, as before the move;
    the recorded `python -c` above runs it. `make coverage-per-file`: exit
    0, `no module below 85% line coverage`, so neither script is on the
    list.

## Milestone 3 — The spec-status report, its guards seen red first

- `tests/test_spec_status.py` (new), written before the script and run red
  (R-RDS-9 to R-RDS-12, R-RDS-19, R-RDS-23). In-process through
  `load_tool` / `run_tool_main` with `--root` at a planted tree:
  - packages under `openspec/changes/` whose `spec.md` files are written
    through `support.write_spec`;
  - their `proposal.md` and `tasks.md`, written directly;
  - a planted `CHANGELOG.md`;
  - `.github/workflows/*.yml` where the workflow column is under test.

  Planned tests:
  - `test_a_draft_package_whose_tasks_and_criteria_are_complete_is_a_finding`.
  - `test_task_checkboxes_count_when_a_package_has_no_milestone_headings`.
  - `test_a_settled_package_with_no_task_done_and_no_criterion_ticked_is_a_finding`.
  - `test_a_proposal_status_that_disagrees_with_its_spec_header_is_a_finding`.
  - `test_a_missing_or_unrecognised_status_header_is_a_finding`,
    parametrised:
    - no header line;
    - the word `IMPLEMENTED`, unrecognised until the follow-up amends
      `VOCABULARY` (DEC-RDS-008);
    - a lower-case `> **Status:** draft`;
    - a proposal word outside the vocabulary;
    - no `spec.md` at all.
  - `test_a_status_line_outside_the_header_block_is_never_the_header`
    (R-RDS-23, DEC-RDS-014), parametrised:
    - a single-line waiver comment carrying `**Status:** APPROVED` above a
      `DRAFT` header: the header column reads `DRAFT`;
    - no header, `**Status:** APPROVED` in prose: `header-unrecognised`;
    - no header, `**Status:** DRAFT` only inside a fenced code example
      after the first `## ` heading: `header-unrecognised`.
  - `test_a_status_line_inside_a_comment_is_never_the_header` (R-RDS-23,
    DEC-RDS-014), parametrised:
    - a waiver whose reason spans lines, one of them
      `> **Status:** APPROVED`, above a `DRAFT` header: reads `DRAFT`;
    - a commented-out old header — the comment's opening, the line
      `> **Status:** APPROVED`, and its close, each on a line of its own —
      above a `DRAFT` header: reads `DRAFT`;
    - in a planted `proposal.md`, a commented-out `> **Status: implemented.**`
      above `> **Status: proposed.**`: the proposal column reads `proposed`.

    Each planted spec goes through `write_spec`; the comment is part of the
    text it is given.
  - `test_the_header_reader_agrees_with_parse_spec_on_every_uncommented_real_header`
    (R-RDS-23): for every `spec.md` under the real `openspec/changes/` whose
    header block holds no HTML comment and in which the script's
    `read_header` finds a header, `read_header(text).upper()` equals
    `parse_spec(path, dialect).status`. A spec outside that scope is skipped,
    never failed: a header in an unexpected form is the report's finding
    (R-RDS-11), not this test's. The test asserts that it compared at least
    one spec, so an empty scope cannot pass it.
  - `test_a_symlinked_alias_of_a_package_is_one_row` (R-RDS-10): a planted
    package and a directory symlink to it under `openspec/changes/` give one
    row. Decorated `pytest.mark.skipif(not supports_symlinks(), …)`.
  - `test_partial_evidence_is_listed_and_is_not_a_finding`: a `DRAFT` package
    with every criterion ticked and one milestone open, and an `APPROVED`
    package with milestones done and no criterion ticked — both rows printed,
    exit 0.
  - `test_a_changelog_entry_is_read_in_both_shapes_and_a_mention_is_not_an_entry`.
  - `test_the_workflow_column_names_verification_stages_no_workflow_runs`.
  - `test_spec_status_exits_two_when_it_cannot_run`, parametrised (R-RDS-12):
    - no `openspec/changes/`;
    - an `openspec/changes/` that holds no package;
    - an undecodable `proposal.md`, `tasks.md` or `CHANGELOG.md`;
    - an unreadable `spec.md` or `tasks.md` (an injected `PermissionError`).

    Each asserts exit 2, no `Traceback`, and the file or directory named. No
    `spec.md` decode case is planted: a `spec.md` is read with undecodable
    bytes replaced, as `parse_spec` reads it (DEC-RDS-013).
  - `test_absent_changelog_and_workflows_are_empty_columns_not_failures`.
  - `test_spec_status_imports_only_the_standard_library_common_and_openspec_graph`
    (C-RDS-8): every import root in `tools/spec_status.py` is in
    `sys.stdlib_module_names`, `_common` or `openspec_graph`.
  - `test_spec_status_runs_over_this_repository`: the real tree; exit 0 or 1,
    one row per entry of `detect.profile(REPO_ROOT).change_dirs`, and this
    package's own row present. It pins no count.

  Add `tools/spec_status.py` to
  `test_the_confidence_lives_only_in_the_specgraph_table`'s scripts. All
  `integration` by the criterion. Record the red run, then `wc -l
  tests/test_spec_status.py` against `MAX_TEST_MODULE_LINES`. This module
  plants specs, so run
  `python -m pytest tests/test_suite_shape.py tests/test_suite_routing.py -q`
  and record it green: the routing guard names any planted spec path written
  by hand.
- `tests/test_ci_makefile.py`: add `spec-status` to the required report
  targets, and run it red before the target exists.
  `tests/test_gate_scripts.py`: add `"spec_status.py"`, and record it red on
  the presence assertion before the script exists.
- `tools/spec_status.py` (R-RDS-9 to R-RDS-12, R-RDS-23, DEC-RDS-007,
  DEC-RDS-009, DEC-RDS-014):
  - Bootstrap `sys.path` for `_common` and the repository root as
    `stage_citations.py` does. Import `detect`, `parse_spec`, `MAKE_REF` and
    `SpecReadError` from `openspec_graph`, `blank_html_comments` from
    `openspec_graph.parse_semantics`, and `logger`, `repo_root`,
    `ReportError` and `workflow_stages` from `_common`. Import no sibling.
  - `VOCABULARY = {"DRAFT": "draft", "APPROVED": "settled"}`, commented as
    the one place the spec words are written and the follow-up's edit point.
    `PROPOSAL_VOCABULARY = {"proposed": "draft", "implemented": "settled"}`.
  - `HEADER_STATUS = re.compile(r"^> \*\*Status:\*\* ([A-Za-z-]+)",
    re.MULTILINE)` and `PROPOSAL_STATUS = re.compile(r"^> \*\*Status:
    (\w+)\.?\*\*", re.MULTILINE)`, both case-sensitive.
  - `header_block(text) -> str`: `blank_html_comments(text)` first, then the
    lines before the first line that begins `## `. Blanking first keeps the
    line structure and stops a `## ` line inside a comment from ending the
    block.
  - `read_header(text) -> str | None` and `read_proposal_status(text) -> str
    | None`, each applying its pattern to `header_block(text)`.
  - `PackageRow` (a dataclass with every column of R-RDS-10).
  - `packages(root) -> tuple[Path, ...]`, which is
    `detect.profile(root).change_dirs`, after checking that
    `openspec/changes/` is a directory. An empty result raises `ReportError`
    naming the directory.
  - `read_package(path, dialect, runs) -> PackageRow`. It reads each
    `spec.md` with `encoding="utf-8-sig", errors="replace"`, as `parse_spec`
    does, and `proposal.md` and `tasks.md` with `encoding="utf-8"`.
  - `changelog_entries(text) -> dict[str, list[str]]`, holding the two entry
    shapes and the section each sits under.
  - `finding(row) -> str | None`, in R-RDS-11's order.
  - `main(argv) -> int`, with argparse over `argv[1:]` and `--root`, the
    rows, the summary line, and the exit contract of R-RDS-12. The workflow
    column comes from `workflow_stages(root, stage_ref=MAKE_REF)`.
    `ReportError`, `SpecReadError`, `OSError` and `UnicodeDecodeError` map to
    2, with the file named.

  The docstring states the vocabulary, the four findings, why the CHANGELOG
  and workflow columns enter none of them, why the header is read anchored,
  comment-blind and not through `parse_spec`, and that it never edits a
  header. Run `ruff check` and `mypy tools` and record both clean.
- `Makefile`: add `spec-status` to `.PHONY`, and `spec-status: ## Report each
  change package's Status header beside its evidence — a report, not a gate`
  with the recipe `python tools/spec_status.py`. Confirm `make thresholds`
  PASS and `make help`.
- Run `make spec-status` at the branch head and record its complete output
  and exit code here. This is the worklist for `settle-package-status-headers`
  (DEC-RDS-008, R-RDS-22). Set beside it the drafting reading — 9
  `draft-but-complete`, 0 `settled-but-empty`, 1 `headers-disagree`
  (`fix-u003-mandatory-given`), 0 `header-unrecognised` — and note every
  difference. This package's own row, `DRAFT` with milestones still open,
  carries no finding at this point. That holds only until its own milestones
  close: once Milestone 5 is `[DONE]` and every criterion is ticked, the row
  is `draft-but-complete` (Milestone 5 records it).
- **Gate:** `make test`

## Milestone 4 — Documents, the reports table and the records

- `tests/test_ci_makefile.py`, written before the table and run red
  (R-RDS-15). Planned tests:
  - `test_every_report_target_has_a_row_in_the_hooks_reports_table`: the
    rows read from the section that begins `## Reports, not gates` up to the
    next `## ` heading, matched by the backticked command in the first cell,
    equal as a set to `_report_targets(Makefile)`.
  - `test_a_report_target_without_a_hooks_row_is_named`: planted; a missing
    row and a row naming no target are each named.

  Red until the section exists.
- `docs/hooks.md`: a `## Reports, not gates` section before `## Claude Code
  hooks`, with a table `| Target | Reads | Exit |` and one row per report
  target — at drafting `make coverage-per-file`, `make matcher-accuracy`,
  `make stage-citations`, `make dead-code` and `make spec-status`, each first
  cell the backticked command. The `make spec-status` row's exit cell says
  that it stays red until `settle-package-status-headers` lands (R-RDS-15).
  Under the table, one paragraph:
  - none is composed into `ci`, `pre-pr` or a CI job;
  - each becomes a gate only through its own package after a quarter of an
    empty report;
  - `make dead-code` needs the dev extra, exiting 2 without it;
  - `make spec-status` stays red until `settle-package-status-headers` lands,
    and its quiet quarter starts only then.

  The `## CI hooks` table is untouched. Run `make docs-check`.
- `docs/aqa.md`: after the `make stage-citations` paragraph (line 193), one
  paragraph on both reports — what each reads, its exit contract (0, 1, 2),
  that `tests/` counts as a user of the code, the whitelist's two stale
  checks, and that `make spec-status` never edits a header.
- `docs/architecture/c4.md` §4, the `tools/*` row (line 80): name
  `dead_code.py` (`make dead-code`) and `spec_status.py`
  (`make spec-status`). In the groups sentence, `spec_status` joins the
  generators and reports that import `openspec_graph`, and `dead_code` is
  described as a report that imports neither `openspec_graph` nor vulture and
  runs vulture as a process. Counts in that sentence are replaced by the
  lists they summarise, so the next script does not make them stale.
- `tools/AGENTS.md`: the same two facts in the "No third-party dependencies"
  bullet, and both scripts in the program-name-first group of the argv
  paragraph. Replace sentences, do not add: `wc -l` read 59 at drafting
  against `MAX_NESTED_LINES = 60`. Run
  `python -m pytest tests/test_agent_artifacts.py -q -k "nested_agents or agent_index_links"`.
- `docs/next-steps.md` (R-RDS-22): item 24, after item 23 and before
  `## Skills / agents`, in the file's numbered-item shape. If the session
  lead applied it with the round-1 or round-2 corrections, confirm the text
  below and leave it; otherwise add it here. At `1c6b8b8` it is not present.
  Its text:

  ```
  24. **Settle the change packages' `Status` headers**
      (`settle-package-status-headers`, the rest of the reflection plan's
      W8.5). `report-dead-code-and-spec-status` adds `make spec-status`, a
      report that lists each change package's `Status` header beside its
      evidence and edits none; its first output, recorded in that package's
      `tasks.md`, is this item's worklist. Setting a header is a human
      decision after review (`.claude/agents/spec-drafter.md`), so this
      package is the maintainer's: settle each listed header; decide whether
      the vocabulary gains a value meaning "shipped" — an `IMPLEMENTED`-style
      third value beside `DRAFT` and `APPROVED`, which touches the scaffold
      template, the drafter and H005 — and amend `VOCABULARY` in
      `tools/spec_status.py`, the one place the report's words are written,
      to match. Three conditions decide whether it can turn the report
      green. (a) If it records status anywhere other than the `Status`
      header, such as a supersession-style record, it must teach
      `tools/spec_status.py` to read that record too; otherwise the report
      stays red for good. (b) Before it edits any shipped package's header,
      it must first write down the exception to the records convention
      (DEC-MCO-006, DEC-ZCG-003, DEC-TSS-016), which otherwise forbids
      exactly that edit. (c) It decides whether the vocabulary gains a
      "shipped" value that an agent may set at a package's closure, since
      the drafter is barred only from `APPROVED`; otherwise every correctly
      closed package branch reads `draft-but-complete`, and any future gate
      would be red on every closing pull request. Until this lands
      `make spec-status` exits non-zero by design, and the quiet quarter
      before any package may make it a gate starts only then. Beside it:
      H005 reads the header through `parse_spec`'s unanchored `STATUS`,
      which a waiver comment or prose above the header can set; the report
      reads the header anchored and with comments blanked, and fixing the
      rule is an `openspec_graph/` change of its own.
  ```

  Run `make docs-check`, and
  `python -m pytest tests/test_rule_registry_docs.py -q`, since that module
  reads `docs/next-steps.md` for a rule-count claim the item must not
  disturb.
- `CHANGELOG.md`, under `## [Unreleased]`: `### Added — two hygiene reports:
  dead code and spec status (M2)`, with one bullet led by
  ``- **`report-dead-code-and-spec-status`.**`` naming the items of
  R-RDS-17. Among them are the follow-up `settle-package-status-headers` and
  the sentence that `make spec-status` stays red until it lands. The figures
  in it are dated and name their commands; the CHANGELOG is exempt from
  tracking the tree afterwards.
- Records, each dated with the commit (R-RDS-20):
  - `make stage-citations` after the change, saying the figures include this
    package's own spec;
  - `make help`;
  - the final `make dead-code` and `make spec-status` output at the commit
    that closes this milestone;
  - `python -m vulture --version`.
- **Gate:** `make docs-check`, then `make pre-pr`.

## Milestone 5 — Confirm, re-point and hand off

- Re-point the stage-only verification lines in
  `specs/hygiene-reports/spec.md` to the tests Milestones 1–4 named, now that
  they exist, keeping each stage. Then run
  `python -m pytest tests/test_spec_test_citations.py -q`. The mapping:

  | AC | Tests |
  |---|---|
  | AC-RDS-1 | adds `test_vulture_is_a_floored_dev_extra_and_never_a_runtime_dependency`, `test_an_exact_vulture_pin_or_a_runtime_vulture_is_named`, `test_no_github_file_or_recipe_line_names_vulture` |
  | AC-RDS-2 | adds `test_the_confidence_lives_only_in_the_specgraph_table` |
  | AC-RDS-3 | the confidence, trees, whitelist, unreachable, separator and header tests, and `test_dead_code_imports_only_the_standard_library_and_common` |
  | AC-RDS-4 | `test_dead_code_exits_two_when_it_cannot_run`, `test_a_declared_tree_that_is_absent_or_holds_no_python_exits_two`, `test_vulture_stderr_is_logged_and_never_decides_the_exit`, `test_dead_code_exits_zero_when_nothing_is_listed` |
  | AC-RDS-5 | the two binding tests |
  | AC-RDS-6 | `test_the_installed_vulture_reports_a_planted_unused_function` |
  | AC-RDS-7 | the four finding tests, the checkbox test, `test_a_status_line_outside_the_header_block_is_never_the_header`, `test_a_status_line_inside_a_comment_is_never_the_header`, `test_the_header_reader_agrees_with_parse_spec_on_every_uncommented_real_header`, `test_a_symlinked_alias_of_a_package_is_one_row` and the spec-status import test |
  | AC-RDS-8 | the partial-evidence, changelog-shape, exit-2 and absent-file tests |
  | AC-RDS-9 | adds `test_the_workflow_column_names_verification_stages_no_workflow_runs` |
  | AC-RDS-10 | adds `test_every_report_target_stays_out_of_the_ladder` |
  | AC-RDS-11 | `test_a_report_target_composed_into_the_ladder_is_named` |
  | AC-RDS-12 | adds the two reports-table tests and `test_a_second_table_in_hooks_is_not_read_as_ci_rows` |
  | AC-RDS-15 | the three guards in `tests/test_suite_shape.py` and the routing guard in `tests/test_suite_routing.py`, by name, which resolve on this branch |
- Confirm this package validates clean
  (`planlint --target . validate --fail-on ERROR --change report-dead-code-and-spec-status`),
  then the whole tree, and record each exit code.
- Confirm C-RDS-6: `git diff --stat <base>..HEAD -- openspec/changes` lists
  only this package's directory. Confirm C-RDS-1: `openspec_graph/`,
  `README.md`'s rules table, `tests/baseline_rules.json` and `[project]
  dependencies` are absent from the diff, and `python -m pytest
  tests/test_decomposition.py -k byte_identical -q` is green.
- Close the milestones and tick the criteria, leaving the spec's `Status`
  header `DRAFT` (R-RDS-22). Then run `make spec-status` once more and record
  that this package's own row now reads `draft-but-complete`, with exit 1.
  That is the report working as designed (DEC-RDS-008), not a defect to
  clear.
- Hand off, recorded here:
  - The pull request description asks the maintainer to settle this
    package's own header at merge. The two precedents are the maintainer's
    own commits `3bc3321` (`parse-repo-machinery-structurally`) and
    `49cb9ed` (`harden-ci-gates`). Within today's vocabulary the settled
    value is `APPROVED`. The description also names
    `settle-package-status-headers` as the owner of every other header on
    Milestone 3's worklist, and H005's header leak beside it.
  - Milestone 3's `make spec-status` output is that follow-up's worklist. It
    decides the vocabulary, including whether a "shipped" value exists that
    an agent may set at closure. It writes down the exception to the records
    convention before it edits any shipped header. If it records status
    anywhere but the header, it teaches `tools/spec_status.py` to read that
    record (DEC-RDS-008).
  - Milestone 2's `make dead-code` list goes to the M4 package for W5.1–3,
    with `speckit_section_body`, `speckit_subsection_body` and the three
    `report.__all__` names marked as this measurement's additions to the
    plan's list (DEC-RDS-012).
- Record here, and not in the plan, which is a dated record (R-RDS-16): both
  reports exist, neither is in the ladder, and the plan's D4 figure was
  superseded by measurement (DEC-RDS-002). The open remainder of W8.5 is
  `docs/next-steps.md` item 24.
- **Gate:** `make pre-pr`
