# Change: Two Hygiene Reports — Unreferenced Code, and Each Package's Status Header Beside Its Evidence

## Why

Two kinds of drift in this repository have no command that shows them.

**Unreferenced code.** The October plan measured three symbols nothing calls —
`parse_model.Criterion.has_selector`, `matcher_accuracy.precision_pct` and
`recall_pct` — and three names `report.__all__` exports that nothing imports,
found by hand with `grep` and one vulture run. Nothing re-finds the next one.
The plan's W5.5 asks for a `make` report target over `openspec_graph` and
`tools` with a checked-in whitelist, and its D4 sets the confidence at 80.
Measured at this branch's head, vulture at 80 reports **nothing** over those
two trees. Vulture rates every unused function, method, class, property,
attribute and variable at 60, imports at 90, and only unreachable code and
unused arguments at 100. Imports and locals are already gated by ruff's `F`
family. So a report at 80 can never list the three symbols the plan's §7 row
"Unreferenced symbols: 3 → 0, with `make dead-code` reporting" holds it to.
At 60 it lists them, along with the two shlex attribute assignments D4 was
worried about — which is exactly what the plan's whitelist is for — and,
once `tests/` counts as a user of the code, nothing else that is alive.

**Status headers that disagree with what shipped.** Every `spec.md` carries a
`Status` header, and `openspec/AGENTS.md` says the spec has to match what
shipped, but nothing compares the header with the package's own record. The
plan counted 18 of 44 `spec.md` headers saying `DRAFT`, shipped packages among
them — `gate-tools-coverage` runs as part of every `make test` while its header
reads `DRAFT`. W8.5 asks for a report target listing each package's header
beside its evidence (tasks complete, a CHANGELOG entry, CI running its guards),
followed by one commit that sets the stale headers to what shipped. Measured
here, the evidence is not uniform across eras. Shipped `APPROVED` packages
have every criterion unticked (`add-graph-export`, `enterprise-hardening`,
`harden-ci-gates`, `rename-cli-and-positioning`). A package with a CHANGELOG
section of its own has no milestone done (`add-finding-line-hits`). Only one
package in five has a CHANGELOG entry that names it. A report can say
mechanically where the header and the evidence *both* speak and disagree; it
cannot say what "shipped" means for the rest. And promoting a header is the
one edit this repository reserves to a human (`.claude/agents/spec-drafter.md`:
"never `APPROVED`; that's a human decision after review"). The two packages
that promoted their own header in their implementing pull request did it in
the maintainer's own commits (`3bc3321`, `parse-repo-machinery-structurally`;
`49cb9ed`, `harden-ci-gates`).

This package is the third of milestone M2 ("Measure cheaper") of
`docs/reflection-plan-2026-10.md`, after `measure-coverage-once` and
`shape-the-test-suite`. It implements W5.5 (`make dead-code`) and the report
half of W8.5 (`make spec-status`). Both are reports under guardrail 7 and
`DEC-PM-011`: composed into neither `ci` nor `pre-pr`, a gate only in a later
package once a quarter passes quiet. It departs from the plan in three places,
each recorded with its measurement:

- the confidence is vulture's unused-definition level, not D4's 80, and lives
  in `[tool.specgraph]` beside the other reporting threshold (DEC-RDS-002);
- `tests/` counts as a user of the code but is never reported, because the
  plan's §7 metric counts references repository-wide (DEC-RDS-003);
- the header-setting commit is not in this package. It is the maintainer's,
  in a named follow-up package, `settle-package-status-headers`, which
  `docs/next-steps.md` carries (DEC-RDS-008, R-RDS-22).

It deletes nothing and edits no other package: removing the reported symbols
is M4's W5.1–3, and setting headers is the maintainer's decision in the
follow-up, for which this package produces the worklist. Until that follow-up
lands, `make spec-status` exits non-zero, and the quiet quarter before any
gate on it starts only then. This package's own header stays `DRAFT`; the
report lists it as `draft-but-complete` once its milestones close, and the
pull request asks the maintainer to settle it at merge.

**Evidence:** measured at `1c8917c`, 2026-10-07. That is the head of
`claude/m2-report-targets` at drafting, which was stacked on the unmerged PR
#42 (`shape-the-test-suite`, branch `claude/m2-shape-the-test-suite`).
`openspec_graph/`, the `Makefile` and every `tools/` script but one docstring
line of `tools/_common.py` are byte-identical to `f7118a0` (`main`, the squash
of #41), by `diff -rq` over the two checkouts at `1c8917c`. The round-1
corrections were measured at `114754c` (this package's first draft), and the
round-2 corrections at `1c6b8b8`, the same day. The only changes since
`1c8917c` are this package's own two commits and the merge of #42's head,
`92077b5`, which is `1c6b8b8`. That merge moved the suite's routing and loop
guards into `tests/test_suite_routing.py` and moved
`MAX_TEST_MODULE_LINES`'s line; every line number below in `tools/`,
`openspec_graph/`, the `Makefile`, `pyproject.toml`, docs/hooks.md and the
guarded test modules was re-read at `1c6b8b8` and holds. Every number names
its command. `tasks.md` Milestone 0 re-measures each one at the branch head
before the first edit.

- **The gate and the tree.** `planlint --target . validate --fail-on ERROR`
  at `1c8917c`: 51 specs, 0 error / 0 warn / 0 info, exit 0 (50 specs at
  `f7118a0`, before `shape-the-test-suite`'s package; 52 at `114754c` and at
  `1c6b8b8`, with this draft). `planlint --target . detect`: 50 change
  packages at `1c8917c` and 51 at `1c6b8b8`, 23 make targets, coverage floor
  97 from `pyproject.toml:[tool.coverage.report].fail_under`.
  `python tools/stage_citations.py`: 51 specs at `1c8917c` and 52 at
  `1c6b8b8`, 16 stages cited, 12 on a verification line. Six of those 12 are
  invoked by no scanned workflow: `ci`, `coverage-tools`, `security`,
  `thresholds`, `validate`, `wheel-check`.
- **vulture, as installed and as published.** `python -m vulture --version`
  prints `vulture 2.16` under Python 3.13.16 in this container.
  `python -m pip index versions vulture` reaches the index through the proxy
  and lists 2.16 as the latest release. `importlib.metadata` gives
  `Requires-Python: >=3.9` and one dependency, `tomli>=1.1.0; python_version <
  "3.11"`. Vulture's own `CHANGELOG.md` (fetched from the project's
  repository on 2026-10-07) dates the features this package rests on:
  - 2.1 (2020-08-19): options read from `pyproject.toml`'s `[tool.vulture]`;
  - 2.9 (2023-08-20): "Use exit code 3 when dead code is found" — before it,
    dead code and invalid input both exit 1;
  - 2.13 (2024-10-02): Python 3.13 support;
  - 2.15 (2026-03-04): "Add support for Python 3.14";
  - 2.16 (2026-03-25): the current release.

  The README's confidence table: function/method/class argument and
  unreachable code 100, import 90, "attribute, class, function, method,
  property, variable" 60. Exit codes: 0 no dead code, 1 invalid input, 2
  invalid arguments, 3 dead code found.
- **What vulture reports here.** All at `1c8917c`, from the repository root:
  - `python -m vulture openspec_graph tools --min-confidence 80`: no output,
    exit 0. At `--min-confidence 100`: no output, exit 0.
  - The same two trees at `--min-confidence 60`: 12 lines, exit 3.
    `cli.py:1017` `main_deprecated`, `detect.py:596`
    `filter_speckit_by_feature`, `parse_model.py:58` `has_selector`
    (property), `parse_semantics.py:501` `section_body`, `:510`
    `speckit_section_body`, `:546` `speckit_subsection_body`, `:735`
    `suppressions`, `tools/_common.py:353` `duplicate_scoped_floor_keys`,
    `tools/matcher_accuracy.py:119` `precision_pct` and `:123` `recall_pct`
    (methods), `tools/stage_citations.py:160` `whitespace_split` and `:161`
    `commenters` (attributes).
  - `python -m vulture openspec_graph tools tests --min-confidence 60`: 9
    lines, exit 3. Two are under `tests/`; seven are under the two reported
    trees — `has_selector`, `speckit_section_body`, `speckit_subsection_body`,
    `precision_pct`, `recall_pct`, `whitespace_split`, `commenters`. The five
    that leave the list are each called by a test.
  - Timed through `subprocess` in this container, the three-tree run took
    0.82 s and the two-tree run at 80 took 0.29 s.
- **vulture at its edges** (`114754c`, from the root, read-only):
  - `python -m vulture` with no path prints "Please pass at least one file or
    directory" and exits 2. Vulture takes paths from the command line or a
    `[tool.vulture] paths` key; with neither it raises `InputError`
    (`vulture/config.py:57–58`), which `main` turns into exit 2
    (`vulture/core.py:664–669`). It does read a `[tool.vulture]` table from
    the working directory's `pyproject.toml` and merges the command line
    over it (`vulture/config.py:183–226`).
  - `python -m vulture docs --min-confidence 60` — a directory holding no
    `.py` file (`find docs -name "*.py" | wc -l` prints 0) — prints nothing
    and exits 0. `python -m vulture no_such_tree --min-confidence 60` prints
    "Error: …/no_such_tree could not be found." and exits 1
    (`vulture/utils.py:101`).
  - Vulture writes findings to stdout, and a file it could not parse or read
    to stderr with exit 1 (`vulture/core.py:233–255`, `:290–295`). It parses
    with `ast.parse`; `python -c 'import ast; ast.parse("x = \"\\d\"\n",
    filename="planted.py")'` prints `planted.py:1: SyntaxWarning: invalid
    escape sequence '\d'` to stderr and exits 0.
- **The named symbols, re-measured.**
  `grep -rnw <name> --include=*.py openspec_graph tools tests` at `1c8917c`:
  - `has_selector`: 1 hit, its definition (`openspec_graph/parse_model.py:59`,
    under the `@property` at `:58`). `precision_pct` and `recall_pct`: 1 hit
    each, their definitions (`tools/matcher_accuracy.py:119`, `:123`). The
    `pyproject.toml` keys `g002_min_precision_pct` and the like are other
    names.
  - `STATUSES` (2 hits), `STATUS_ERROR` (4) and `FindingRecord` (6) are all
    in `openspec_graph/report.py`. They appear in `__all__` at lines 33, 34
    and 41 and are used inside the module (`STATUSES` is built from
    `STATUS_ERROR` at line 65; `FindingRecord` is constructed at line 225),
    and no other module imports them. That is "exported and unimported", which
    vulture cannot see by construction: a name in `__all__` counts as used.
  - `speckit_section_body` (`parse_semantics.py:510`) and
    `speckit_subsection_body` (`:546`) are found only in comments and
    docstrings outside their definitions (`parse_semantics.py:106`, `:547`,
    `:556`, `:649`; `parse_speckit.py:33`; `tests/test_parse_speckit.py:92`).
    The plan's §1.2 listed the first as "called only by tests"; at this
    commit nothing calls either.
  - Neither of the latter two kinds is acted on here.
- **What "unreferenced" means in the plan** (`114754c`). The §7 row
  (`docs/reflection-plan-2026-10.md:713`) is "Unreferenced symbols | 3 | 0,
  with `make dead-code` reporting". Its three are §1.2's "0 refs" symbols
  (`:46`), counted repository-wide like the "0 of 405 top-level symbols …
  unreferenced repository-wide" figure (`:30`). The test-only helpers are a
  separate row, "Test-only public API" (`:47`), decided by W5.2 (`:382`).
  Of the five symbols the three-tree run drops, `filter_speckit_by_feature`
  (`tests/test_detect_speckit.py:97`), `section_body`
  (`tests/test_finding_line_hits.py:319`) and `suppressions`
  (`tests/test_graft_cli.py:374`) are in that row, and
  `duplicate_scoped_floor_keys` is called only from
  `tests/test_coverage_checkers.py`. `main_deprecated` is called by
  `tests/test_cli_surface.py:261` and is the `specgraph` console script
  (`pyproject.toml:69`).
- **Status headers, as written.** At `1c6b8b8`, anchored on the header's own
  shape: `grep -l "^> \*\*Status:\*\* DRAFT"
  openspec/changes/*/specs/*/spec.md | wc -l` prints 26 and the `APPROVED`
  form prints 26, over 52 `spec.md` files in 51 packages
  (`add-finding-line-hits` has two specs, both `DRAFT`; this package's own
  spec is one of the 26 `DRAFT`). The grep has to be anchored: unanchored, it
  prints 27 for `APPROVED`, because this package's spec quotes the phrase in
  prose. At `1c8917c`, before this package's spec existed, the unanchored
  form printed 25 and 26 over 51. Every spec header has the one shape
  `> **Status:** <WORD>`, and the words are `DRAFT` and `APPROVED`.
  `grep -n "^> \*\*Status:" openspec/changes/*/proposal.md` finds four
  proposals with a status line of their own, in a different shape
  (`> **Status: proposed.**`, `> **Status: implemented.**`), each on line 3,
  before the proposal's first `## ` heading:
  `fix-heading-regex-newline-span`, `fix-u003-mandatory-given` and
  `lint-empty-speckit-requirements` say `proposed`, and
  `parse-repo-machinery-structurally` says `implemented`. Rule H005
  (`rules_harness.py:58`) warns when a spec containing `(BLOCKING)` is not
  `DRAFT`. `grep -l "(BLOCKING)" openspec/changes/*/specs/*/spec.md` prints
  nothing, so promoting a header fires nothing today.
- **How planlint reads a header** (`114754c`; re-read at `1c6b8b8`).
  `STATUS = re.compile(r"\*\*Status:\*\*\s*([A-Za-z-]+)")`
  (`openspec_graph/parse_semantics.py:16`) carries no anchor, and
  `parse_spec` runs `STATUS.search(text)` over the raw text
  (`openspec_graph/parse.py:156`) and upper-cases the match (`:168`). So
  the first `**Status:**` anywhere decides — in a waiver comment above the
  header, in prose, in a code example — and `> **Status:** draft` reads as
  `DRAFT`. H005 reads that same `spec.status`. More, at `1c6b8b8`:
  - `parse_spec` reads the file as `utf-8-sig` with `errors="replace"`
    (`openspec_graph/parse.py:119`), so `validate` accepts a spec with an
    undecodable byte; only an `OSError` becomes `SpecReadError`.
  - The waiver pattern `SUPPRESS` (`openspec_graph/parse_semantics.py:51`)
    is `re.DOTALL`, so a waiver's reason can run over several lines, and a
    line of it can begin `> **Status:**` inside a spec's header block.
  - `blank_html_comments` (`openspec_graph/parse_semantics.py:599`) blanks
    every HTML comment across lines, keeping length and newlines, and the
    speckit rules read through it (`openspec_graph/rules_speckit.py:111`).
    Its pattern, `<!--.*?-->` with `re.DOTALL` (`:575`), blanks a comment
    only where it closes.
  - A one-off read-only script, not committed, read every `spec.md` with the
    reader R-RDS-23 defines — comments blanked, header block cut at the first
    `## ` heading, the anchored header matched. No spec's header block holds
    an HTML comment, and the anchored word, upper-cased, equals
    `parse_spec(...).status` on all 52.
- **How planlint counts packages** (`114754c`; re-read at `1c6b8b8`).
  `detect.profile(root)` builds `change_dirs` from `openspec/changes/*`
  directories through `_dedupe_by_identity`
  (`openspec_graph/detect.py:707–715`): a symlinked alias is one package, and
  a package with no `spec.md` is still one. Because the glob is one level
  deep, an `archive/` directory there would be one more package, and the
  packages archived inside it would be none; an empty `openspec/changes/`
  gives no package. `ls openspec/changes` holds no `archive/` today.
  `tests/support.py:48` has the `supports_symlinks()` probe.
- **The evidence, as recorded.** `grep -h "^## Milestone"
  openspec/changes/*/tasks.md | grep -c "\[DONE\]"` prints 136 at `1c8917c`.
  `[DONE]` on a `## Milestone` heading is the only completion marker. Two
  older packages (`decompose-god-files`, `post-merge-quality-review`) record
  tasks as `- [x]` checkboxes and have no milestone headings. Criteria are
  ticked as `- [x] **AC-…**`. The parsed `Criterion` carries no checkbox state
  (`openspec_graph/parse_model.py:26–60`), so ticks are read from the text.
  CHANGELOG entries name their package in two shapes: a heading ending
  ``(`<package>`)`` (the 0.2.0 sections) and a bullet led by
  ``- **`<package>`.**`` (0.3.0 onwards). Read that way, 10 of the 50
  packages have an entry naming them. `gate-tools-coverage`'s own entry is
  headed "coverage floors for the `tools/` gate scripts" and names no package.
  A mention of a package elsewhere is not an entry: 0.3.0's "Three OpenSpec
  change packages, `Status: DRAFT`, none implemented" names three.
- **What a mechanical comparison finds.** These figures come from a one-off
  read-only script at drafting, not committed, implementing R-RDS-11's
  definitions over the `1c8917c` checkout; the figure of record is
  `make spec-status`'s first output, recorded in `tasks.md` Milestone 3.
  - **9 packages** are all-`DRAFT` with every milestone `[DONE]` and every
    criterion ticked: `add-parser-property-tests`, `add-speckit-dialect`,
    `fix-detect-corpus-defects`, `fix-prose-matcher-precision`,
    `gate-tools-coverage`, `pin-actions-by-sha`, `select-zero-cost-guards`,
    `shape-the-test-suite` and `write-down-policies`.
  - **None** is all-`APPROVED` with no milestone done and no criterion ticked.
  - **1** has headers that disagree with each other:
    `fix-u003-mandatory-given`, spec `APPROVED`, proposal `proposed`.
  - **No** header is unrecognised.
  - The other 40 have evidence that is partial or that agrees with the
    header. Examples of partial evidence: `measure-coverage-once` (23 of 23
    criteria, 5 of 6 milestones), `harden-ci-workflows` (29/29, 8/9),
    `add-github-action-contract` (24/24, 9/10, with a Milestone 9 "Outside
    this repository (owner-executed)"), `add-agent-skill-distribution` (17/17,
    0/7), `add-findings-json-envelope` (`APPROVED`, 12/12, 0/6),
    `add-graph-export` (`APPROVED`, 0/7, 2/2).
  - The plan's "18 headers to set" is therefore not recoverable
    mechanically: of 24 all-`DRAFT` packages, 9 have unanimous evidence
    against their header and the rest need a reader.
- **Where the numbers may live, and what guards them.** The dev extra is
  `pyproject.toml:244–252`: `pytest`, `pytest-cov`, `ruff`, `mypy`, `build`,
  `hypothesis`, and `tomli` behind a marker, all unpinned. `dependencies = []`
  is at `:38`, held by `test_runtime_dependencies_stay_empty`. The unpinned
  decision is held three ways:
  - `test_threshold_guard_fails_on_a_pinned_tool_version` and
    `tools/check_no_hardcoded_thresholds.py:103` flag `ruff==`, `mypy==` and
    `pytest==` in a workflow;
  - `test_dependabot_does_not_add_a_pip_ecosystem` ("the dev extras are
    unpinned on purpose");
  - a test docstring: "so contributors and CI resolve the same versions".

  `pip install -e ".[dev]"` (every `ci.yml` job that runs the suite, and
  `release.yml`) leaves an already-installed package that satisfies a bare
  requirement alone, so a bare `vulture` lets an old install stay old. The
  threshold guard flags any two-or-more-digit literal on a recipe line outside
  `$(...)`, so a `--min-confidence` number on the recipe would be FAIL.
  `openspec_graph/thresholds.py:51` anchors detection on a whole-line
  `fail_under` only, so a new `[tool.specgraph]` key changes no detected
  floor. `[tool.specgraph]` (`pyproject.toml:130`) holds this repository's
  other reporting threshold, `per_file_line_min` (`:167`), placed there by
  DEC-MCO-009 and read through
  `read_pyproject_int(pyproject, "[tool.specgraph]", key)`
  (`tools/_common.py:146`). That reader leaves the table at the next table
  header of any kind (`tools/_common.py:171`), such as the
  `[tool.specgraph.action_major_floors]` subtable at `pyproject.toml:226`.
- **Where a whitelist file could live.** `[tool.coverage.run] source` is
  `["openspec_graph", "tools"]`, so a never-executed `.py` under `tools/`
  would be measured. `[tool.mypy] files` is `["openspec_graph", "tools"]`, and
  `make lint` runs `ruff check openspec_graph tests tools`, with `F` and `B`
  selected. Vulture's own whitelist idiom (`_.whitespace_split`) is an
  undefined name and a useless expression to those two. The wheel packages
  `openspec_graph*` only. The repository root holds no `.py` file.
- **The tools' conventions.** `tools/AGENTS.md:32–33`: "No third-party
  dependencies, ever. Shared helpers go in `_common.py`." The seven gate
  scripts are stdlib-only, and the five generators and reports import
  `openspec_graph` "to avoid a second copy of logic that would drift".
  `grep -n "^from [a-z_]* import" tools/*.py` at `114754c`: every script
  imports `_common` and no other sibling. `tools/_common.py` is held
  stdlib-only by `test_common_module_is_stdlib_only`
  (`tests/test_enterprise.py:482`). `tools/stage_citations.py` (lines 62–63)
  imports `openspec_graph.detect` and `parse_spec` and owns the one workflow
  lexer: `WORKFLOW_DIR` (`:69`), the `run:` reader and shell-token patterns
  (`:79–88`), `ReportError` (`:109`), `run_scripts` (`:126`), `_shell_tokens`
  (`:158`, setting `whitespace_split` and `commenters`), `shell_invocations`
  (`:165`, which decides what a stage is with `MAKE_REF.fullmatch` at `:194`),
  `workflow_invocations` (`:201`) and `workflow_stages` (`:209`, raising
  `ReportError` at `:224` and `:233`). Re-read at `1c6b8b8`:
  - `re` and `shlex` (lines 50 and 51) are used only by the lexer's patterns
    and `_shell_tokens`, so the move leaves both unused;
  - `ReportError` is also raised by `spec_files` (`:122`) and `build_rows`
    (`:251`), which stay;
  - `workflow_stages` logs `"stage-citations: %s invokes %s"` (`:235`);
  - `shell_invocations` (`:165`) is a public name of the module, though no
    test reaches it.

  `tests/test_stage_citations.py` calls `sc.run_scripts(text)`,
  `sc.workflow_invocations(text)` and `sc.workflow_stages(root)`. The script
  exits 0 whatever it finds.
  `tools/check_secrets.py:87–97` (`run_gitleaks`) runs an external tool as a
  process and reports its absence. `read_pyproject_int` (`tools/_common.py:146`)
  and `coverage_sources` (`:262`) call `pyproject.read_text(encoding="utf-8")`
  directly (`:169`, `:281`), so an undecodable or unreadable `pyproject.toml`
  raises out of them. `tools/AGENTS.md` is 59 lines (`wc -l`) against
  `MAX_NESTED_LINES = 60` (`tests/test_agent_artifacts.py:454`), so its edit
  replaces text and adds none. `test_gate_script_is_runnable_as_a_script`
  (`tests/test_gate_scripts.py:348–404`, `TOOLS` at `:29`) runs every listed
  script from a throwaway cwd and accepts exit codes 0, 1 and 2 only, with no
  `ModuleNotFoundError` on stderr. `python tools/missing.py` exits 2 with
  "can't open file", which that test accepts, so today a listed script that
  does not exist passes it.
- **The report-target guards, and the reader a new table would trip.**
  `test_makefile_has_matcher_accuracy_report_target`
  (`tests/test_ci_makefile.py:44–57`, cited by AC-PM-14 and AC-MCO-17) and
  `test_makefile_has_coverage_per_file_report_target` (`:275–293`, cited by
  AC-MCO-17) each re-implement one check: documented, `.PHONY`, and absent
  from `ci`'s and `pre-pr`'s *direct* prerequisites. `_one_run_violations`
  (`:138–164`) carries a third copy of the aggregate half (`:161–163`), which
  `test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named`
  exercises with the planted case "pre-pr composing the report" (`:257–262`)
  on `_ONE_RUN_MAKEFILE` (`:217–236`), whose `coverage-per-file` help text is
  "a report" (`:229`). The three report targets today all have help text
  beginning "Report": `coverage-per-file` (`Makefile` line 45),
  `matcher-accuracy` (91) and `stage-citations` (94). docs/hooks.md documents
  none of them and has one table, the CI table (lines 71–82).
  `_hooks_ci_table_cells` (`tests/test_ci_workflow.py:293–295`) reads every
  table row in the file whose first cell is a backticked word — not only the
  CI table its docstring names. A second table with a `dead-code` row would
  turn `test_every_hooks_ci_table_row_names_a_job_or_workflow` red.
- **The suite's shape (PR #42, merged into this branch at `1c6b8b8`).**
  `pyproject.toml` registers `unit`, `integration` and `e2e` under
  `--strict-markers`. `tests/shape_support.py` decides each test's tier by
  what its own code under `tests/` uses: a process start is `e2e`; a read of
  this repository's files, or a `tools/` script run in-process, is
  `integration`. "The criterion stops at `tests/`" (DEC-TSS-017): a process
  the code under test starts does not count. `MAX_TEST_MODULE_LINES` (700)
  is defined in `tests/test_suite_shape.py`, beside the tier and line-bound
  guards. The routing and loop guards — among them
  `test_no_test_module_writes_a_spec_path_by_hand` — live in
  `tests/test_suite_routing.py`, split from the shape module by the merge.
  `wc -l` reads `tests/test_ci_makefile.py` 300, `tests/test_ci_workflow.py`
  392 and `tests/test_gate_scripts.py` 404. A planted spec must be written
  through `support.write_spec`, or the routing guard names it. An unreadable
  file is planted by injecting `PermissionError` into `Path.read_text`
  (`tests/test_stage_citations.py:223–239`, `tests/test_repo_io.py:23`),
  because as root a `chmod 000` file still reads.
- **Coverage headroom for two new `tools/` scripts.** The `coverage.json` in
  the `1c8917c` checkout (written 2026-10-07 03:08 UTC, after the branch's
  last commit) reads, through the checkers, `tools/` 96.4 % (946/981) lines
  and 93.9 % (323/344) branches against floors 94 and 91, and
  `openspec_graph/` 99.3 % (2276/2292) and 97.6 % (744/762) against 97 and 95.

## What Changes

- `pyproject.toml`:
  - The `dev` extra gains `"vulture>=2.15"`, under a comment giving the
    floor's two reasons: exit code 3 means "dead code found" only from 2.9,
    and Python 3.14, in the support window, is supported from 2.15. The
    comment adds that pip leaves a satisfied bare requirement alone, and that
    a floor needs no update bot where a pin would (DEC-RDS-001).
  - `[tool.specgraph]` gains `dead_code_min_confidence = 60`, after
    `per_file_line_min`, under a comment: a reporting threshold read by
    `tools/dead_code.py`, which passes it to vulture on the command line, and
    gating nothing (DEC-RDS-002). No `[tool.vulture]` table is added.
  - `[project] dependencies` stays `[]`.
- `tools/_common.py`: gains the workflow lexer, moved from
  `tools/stage_citations.py` unchanged in behaviour. The moved names are
  `WORKFLOW_DIR`, `ReportError`, the `run:` and shell-token patterns,
  `run_scripts`, `_shell_tokens`, `shell_invocations`, `workflow_invocations`
  and `workflow_stages`. The functions that decide what a stage is take the
  grammar as a keyword parameter, `stage_ref`, in place of the
  `openspec_graph` import, so the module stays stdlib-only. The debug line in
  `workflow_stages` takes a neutral label in place of `stage-citations:`,
  because the spec-status report logs through it too (R-RDS-24,
  DEC-RDS-009).
- `tools/stage_citations.py`: imports from `_common` only the names it uses.
  - It re-exports `run_scripts` explicitly,
    `from _common import run_scripts as run_scripts`, because its tests reach
    it as `sc.run_scripts`.
  - It keeps its public names and call shapes as documented wrappers that
    pass `stage_ref=MAKE_REF`: `shell_invocations(script)` (a public name,
    `:165`, raised by Copilot on PR #43), `workflow_invocations(text)` and
    `workflow_stages(root, only=())`.
  - It drops the `re` and `shlex` imports the move leaves unused, so
    `ruff check tools` stays clean.
  - Its output is byte-identical, shown by a recorded diff; its tests are not
    edited.
- `tools/dead_code.py` (new), a report that imports neither `openspec_graph`
  nor any third-party module, and nothing from `tools/` but `_common`.
  - It reads `[tool.specgraph] dead_code_min_confidence` through
    `read_pyproject_int` and the reported trees through `coverage_sources`.
  - It checks each reported tree is a directory holding a `.py` file, checks
    `importlib.util.find_spec("vulture")`, then runs one
    `sys.executable -m vulture` process from the root over the reported
    trees, plus `tests/` when present, at that confidence, without the
    whitelist.
  - It parses vulture's stdout only, line by line, normalising path
    separators, and keeps findings under a reported tree. Vulture's stderr
    goes to the logger at DEBUG and reaches the message only when vulture
    exits 1 or 2.
  - A finding whose `unused <kind> '<name>'` name is a whitelist entry is
    suppressed. The rest are listed in vulture's own line form, sorted. Every
    entry that suppressed nothing is listed as stale.
  - Exit 1 if either list is non-empty, 0 with a saying-so line, and 2 when
    it cannot run (R-RDS-5). An `OSError` or `UnicodeDecodeError` from
    reading `pyproject.toml` or the whitelist is turned into exit 2, naming
    the file.
  - It also exposes `unbound_whitelist_entries(root)` for the deterministic
    half of the stale check (R-RDS-7).
- `tools/dead_code_whitelist.txt` (new): one `name  # reason` per line,
  read only by `tools/dead_code.py`. At landing it holds `whitespace_split`
  and `commenters`, the shlex lexer attributes `tools/_common.py` sets, after
  the move, for the standard library's `shlex` module to read.
- `tools/spec_status.py` (new), a report that imports the stdlib,
  `openspec_graph` (`detect.profile`, `parse_spec`, `MAKE_REF`,
  `blank_html_comments`) and `_common` (`workflow_stages`, `ReportError`,
  `logger`), and no sibling script and no third-party module.
  - Its packages are `detect.profile(root).change_dirs`, so a symlinked alias
    is one row and a spec-less package is listed. An `openspec/changes/`
    holding no package exits 2, as an empty tree does in the dead-code
    report.
  - It reads each spec's `Status` header with `re`, anchored at a line that
    begins `> **Status:** `, matched case-sensitively, before the first `## `
    heading, after blanking every HTML comment with `blank_html_comments`,
    which keeps the newlines. So neither a waiver's multi-line reason nor a
    commented-out old header can set it. A proposal's status line is read the
    same way. It does not use `parse_spec(...).status`, which a waiver
    comment, prose or a code example can set (R-RDS-23, DEC-RDS-014).
  - It reads a `spec.md` as `parse_spec` does, `utf-8-sig` with undecodable
    bytes replaced, so it never refuses a spec the gate accepts.
  - For each package it prints one row: the package, its headers, criteria
    ticked of declared, milestones `[DONE]` of declared (else task boxes), the
    CHANGELOG sections holding an entry naming it, the verification-line
    stages no scanned workflow runs, and its finding, if any.
  - The findings are `draft-but-complete`, `settled-but-empty`,
    `headers-disagree` and `header-unrecognised`, as R-RDS-11 defines them.
    `VOCABULARY` is the one place the spec words are written.
  - Exit 1 on any finding, 0 with a saying-so line, and 2 when it cannot run.
    That includes an unreadable package file, or an undecodable
    `proposal.md`, `tasks.md` or `CHANGELOG.md`, with the file named. Text
    only.
- `Makefile`: `.PHONY` gains `dead-code` and `spec-status`. `dead-code: ##
  Report unreferenced code under the coverage source trees (vulture) — a
  report, not a gate` runs `python tools/dead_code.py`. `spec-status: ##
  Report each change package's Status header beside its evidence — a report,
  not a gate` runs `python tools/spec_status.py`. Neither has prerequisites.
  The `ci:` and `pre-pr:` lines are byte-identical. Both names fit `make
  help`'s fourteen-character column.
- `tests/test_dead_code.py` and `tests/test_spec_status.py` (new): the
  behaviour of both scripts, in-process through `load_tool`/`run_tool_main`
  against planted roots, plus one run of the installed vulture on a planted
  tree. They also hold the dev-extra guard, the `.github/`-and-recipe guard,
  the confidence-literal guard, the whitelist-binding guard and the
  header-reader agreement test. That test compares the two readers only
  where they must agree — a header found and no comment in the header block
  — and case-insensitively, so it guards the reader and never gates header
  form. Every test is tiered by `shape_support`'s criterion, and both modules
  stay under the line bound (R-RDS-18).
- `tests/test_ci_makefile.py`: one helper, `_report_target_violations`,
  defines a report target. It is a documented target whose help text begins
  "Report", in `.PHONY`, and not reachable from `ci` or `pre-pr` through
  prerequisites *transitively*. The two existing report-target tests and
  `_one_run_violations`' aggregate check delegate to it. The two tests keep
  their names and every asserted property; `_ONE_RUN_MAKEFILE`'s report
  target gets help text beginning "Report". New tests run it over every
  report target, with `dead-code` and `spec-status` required among them, and
  over planted counter-examples. A test holds every report target to a row in
  docs/hooks.md's reports table and every row to a report target.
- `tests/test_ci_workflow.py`: `_hooks_ci_table_cells` reads only the table
  under the `## CI hooks` heading. A planted second table is shown not to be
  read as CI rows. Both CI-table tests are otherwise unchanged.
- `tests/test_gate_scripts.py`: `dead_code.py` and `spec_status.py` join
  `test_gate_script_is_runnable_as_a_script`'s list, and the test gains
  `assert (TOOLS / script).is_file()` before it starts the process, so each
  entry is red before its script exists.
- `docs/hooks.md`: a new `## Reports, not gates` section before
  `## Claude Code hooks`. It has one table row per report target — first cell
  the backticked command (`make dead-code`), then what it reads and its exit
  contract. A paragraph under it says none is composed into `ci`, `pre-pr` or
  a CI job, that each becomes a gate only through its own package after a
  quiet quarter, and that `make spec-status` stays red until
  `settle-package-status-headers` lands (R-RDS-15).
- `docs/aqa.md`: one paragraph after the `make stage-citations` paragraph
  (line 193) describing both reports and their exit contract.
- `docs/architecture/c4.md` §4, the `tools/*` row (line 80): both scripts
  named. `spec_status` joins the generators and reports that import
  `openspec_graph`. `dead_code` is described as the one report that imports
  neither `openspec_graph` nor vulture and runs vulture as a process.
- `tools/AGENTS.md`: the same two facts and the argv convention (program name
  first), replacing text so the file stays within `MAX_NESTED_LINES`.
- `docs/next-steps.md`: one numbered item, after item 23, for
  `settle-package-status-headers` (R-RDS-22). The text is in `tasks.md`
  Milestone 4. It says:
  - the item is the maintainer's;
  - its scope: settle each listed header, decide whether the vocabulary
    gains a "shipped" value, and amend `VOCABULARY` in
    `tools/spec_status.py`;
  - `make spec-status` stays non-zero until it lands, and the quiet quarter
    starts only then;
  - a status recorded anywhere but the `Status` header — a
    supersession-style record — must be taught to `tools/spec_status.py`, or
    the report stays red for good;
  - before any shipped package's header is edited, the exception to the
    records convention (DEC-MCO-006, DEC-ZCG-003, DEC-TSS-016) is written
    down;
  - it decides whether a "shipped" value exists that an agent may set at a
    package's closure, since the drafter is barred only from `APPROVED`;
    without one every correctly closed package branch reads
    `draft-but-complete`, and any future gate would be red on every closing
    pull request;
  - H005's header leak, beside it.
- `CHANGELOG.md` `[Unreleased]`: `### Added — two hygiene reports: dead code
  and spec status (M2)` with a bullet led by
  ``- **`report-dead-code-and-spec-status`.**`` — the entry shape the new
  report reads. It names both targets, the floored dev extra, the confidence
  key and why it is not D4's 80, the whitelist and its two stale checks, the
  four findings, that no header was edited, the follow-up that owns them, and
  that `make spec-status` stays red until that follow-up lands (R-RDS-17).
- `openspec/changes/report-dead-code-and-spec-status/tasks.md`: the records.
  These are the red runs, the lexer-move diff, both reports' first output at
  the branch head (the header worklist among them), the vulture version, and
  the stage-citation report after.

## Non-Goals

- **No symbol is removed, renamed, deprecated or privatised.** The report
  lists; M4's W5.1–3 acts, under guardrail 1 — `has_selector` is on a
  re-exported dataclass and keeps a deprecation window. The two
  `speckit_*_body` readers this measurement adds to the list, and the three
  `report.__all__` names vulture cannot see, are recorded for M4, not
  decided here.
- **No Status header is changed, in any package, and the header vocabulary
  is not changed.** DEC-RDS-008 gives the reasons. The worklist is recorded
  in `tasks.md`. Settling the headers, writing down the exception to the
  records convention first, deciding whether a "shipped" value an agent may
  set joins the vocabulary, and teaching the report any other status record
  belong to `settle-package-status-headers`, which is the maintainer's. This
  package's own header stays `DRAFT` too, for the maintainer to settle at
  merge.
- **No fix to H005's header reading.** It reads the same unanchored `STATUS`
  the report refuses to use (DEC-RDS-014), but changing it is an
  `openspec_graph/` change (C-RDS-1). It is recorded beside the follow-up.
- **No gate.** Neither target is composed into `ci` or `pre-pr`, and no
  workflow file changes. Gating either is a later package, after a quarter
  of quiet, with its own reason (D4; W8.5; guardrail 7). For the spec-status
  report that quarter cannot start before the follow-up lands.
- **No JSON output.** Neither report is a machine-readable output a
  consumer keeps, so neither declares a `schema_version` under
  `docs/policies.md`'s schema-integer rule. A later consumer adds one with its
  integer.
- **No archive support (W8.2) and no change to package discovery.** The
  packages are the ones `detect` counts: every directory directly under
  `openspec/changes/`. So an `archive/` directory there counts as one package
  and, holding no `specs/*/spec.md` of its own, reports as
  `header-unrecognised`; the archived packages inside it are not seen.
  Reading archives belongs to W8.2.
- **No harness change beyond the documents named.** `planlint-verifier`
  running the report (W9.2), `spec-adversary`'s wider remit (W5.6) and a
  pre-commit hook for vulture are not in this package.
- **No rule, golden hash, `openspec_graph/` module or runtime dependency
  change.** No coverage floor moves. No marker is added beyond the three that
  exist.
- **No report of exported-but-unimported names.** Vulture cannot see them,
  and a second analyser for one row of the plan is not worth its keep. The
  three are recorded above with their command.
- **No report of test-only symbols.** They count as referenced, as in the
  plan's §7 metric; the plan's "Test-only public API" row and W5.2 own them.

## Affected Capabilities

- `hygiene-reports`
