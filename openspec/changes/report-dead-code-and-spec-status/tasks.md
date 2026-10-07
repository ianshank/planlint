# Tasks: report-dead-code-and-spec-status

Measured at `1c8917c` (the head of `claude/m2-report-targets`, stacked on the
unmerged PR #42, `shape-the-test-suite`), 2026-10-07. `openspec_graph/`, the
`Makefile` and every `tools/` script except one docstring line of
`tools/_common.py` are byte-identical to `f7118a0` (`main`, the squash of #41),
by `diff -rq` over the two checkouts. Every line number below is re-checked
against the branch head before the milestone that uses it; a sibling package
landing first may move a line without moving the fact. Every number here names
the command that produced it.

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
- **Status headers.** `grep -l "Status:\*\* DRAFT"
  openspec/changes/*/specs/*/spec.md | wc -l` prints 25 and the `APPROVED`
  form 26. `grep -h "^## Milestone" openspec/changes/*/tasks.md | grep -c
  "\[DONE\]"` prints 136.
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

The order is DEC-RDS-011 and R-RDS-19's: measure; extend the report-target
guard and scope the CI-table reader; then each report with its guards seen red
before its code; then the documents, the reports-table guard and the records.
The red runs are recorded here and never committed. Milestones 1 to 4 land in
one pull request on `claude/m2-report-targets`, one commit per milestone.

## Milestone 0 — Grounding pass at the branch head

- Re-run the gate and record its exit code before the first edit under
  `openspec/`: `planlint --target . validate --fail-on ERROR`. The drafting
  value is exit 0 over 51 specs at `1c8917c` before this draft. With this
  draft present the count is the base's plus one, re-read here.
- Re-measure vulture at the branch head, from the repository root, and record
  each command, exit code and full output:
  - `python -m vulture --version` and `python -m pip index versions
    vulture`. If the index is unreachable, record the refusal and continue
    with the installed version; the floor of DEC-RDS-001 stands on vulture's
    changelog, not on the index.
  - `python -m vulture openspec_graph tools --min-confidence 80`.
  - The same at 60.
  - `python -m vulture openspec_graph tools tests --min-confidence 60`.

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
  - the two `grep -l "Status:\*\* <WORD>"` counts;
  - `grep -n "^> \*\*Status:" openspec/changes/*/proposal.md`;
  - the `[DONE]` count;
  - the CHANGELOG entries in the two shapes, by
    `grep -nE '^### .*\(`[a-z0-9-]+`\)$|^- \*\*`[a-z0-9-]+`\.?\*\*' CHANGELOG.md`;
  - `grep -l "(BLOCKING)" openspec/changes/*/specs/*/spec.md`, which printed
    nothing at drafting.
- Re-read the sites the guards touch, and note any line that moved:
  - `tests/test_ci_makefile.py` 44–57 and 275–293 (the two report-target
    tests) and its `_prerequisites` / `_MAKE_RULE` helpers;
  - `tests/test_ci_workflow.py` 193–207 and 293–330 (the CI-table tests and
    `_hooks_ci_table_cells`);
  - `tests/test_gate_scripts.py` 350–404;
  - `tests/test_suite_shape.py:49`, `MAX_TEST_MODULE_LINES`;
  - `tests/test_agent_artifacts.py:454`, `MAX_NESTED_LINES`;
  - `Makefile` 1 (`.PHONY`), 13–14 (`help`), 45, 79, 82, 91 and 94;
  - `pyproject.toml` 38, 130, 167 and 235–252;
  - `docs/hooks.md` 48, 69–82 and 142;
  - `docs/aqa.md` 193–199;
  - `docs/architecture/c4.md:80`;
  - `tools/AGENTS.md` 29–45.

  Then `wc -l tools/AGENTS.md tests/test_ci_makefile.py tests/test_ci_workflow.py
  tests/test_gate_scripts.py`; the drafting values are 59, 300, 392 and 404.
- Record the coverage before the change, from one `make test`: the four
  scoped lines the checkers print.
- Record `make help` and `make stage-citations` before the change.
- **Gate:** `make validate`

## Milestone 1 — The report-target guard extended and the CI-table reader scoped, seen red first

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
    `.PHONY`, or reachable from `ci` or `pre-pr`, with the path.

  `test_makefile_has_matcher_accuracy_report_target` and
  `test_makefile_has_coverage_per_file_report_target` assert
  `_report_target_violations(...) == []` in place of their repeated `.PHONY`
  and aggregate checks. Their names, docstrings and remaining assertions are
  kept, because AC-PM-14 and AC-MCO-17 cite them; the per-file test keeps its
  prerequisite and recipe assertions. Planned tests:
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
  never committed.
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
  `python -m pytest tests/test_suite_shape.py tests/test_ci_makefile.py tests/test_ci_workflow.py -q`
  and record. If the criterion disagrees with a mark, the mark moves, never
  the criterion.
- **Gate:** `make test`

## Milestone 2 — The dead-code report, its guards seen red first

- `tests/test_dead_code.py` (new), written before the script and run red
  (R-RDS-3 to R-RDS-7, R-RDS-19). In-process through `load_tool` /
  `run_tool_main`, against roots planted under `tmp_path` — a
  `pyproject.toml` with `[tool.coverage.run] source` and `[tool.vulture]`, a
  `tools/dead_code_whitelist.txt`, and the trees — with the vulture runner
  injected where the test is about parsing. Planned tests, named here so the
  verification lines can be re-pointed:
  - `test_vulture_is_a_floored_dev_extra_and_never_a_runtime_dependency`:
    the real `pyproject.toml` through `read_pyproject()` — the `dev` extra
    holds `vulture>=` and no `==` or upper bound, and `dependencies` holds no
    vulture.
  - `test_an_exact_vulture_pin_or_a_runtime_vulture_is_named`: the same
    helper on planted texts.
  - `test_the_confidence_is_read_from_the_vulture_table_and_passed_to_vulture`:
    the argv the runner receives carries `--min-confidence` with the planted
    value and the planted `source` trees, plus `tests` when it exists.
  - `test_findings_outside_the_reported_trees_are_dropped_and_tests_count_as_users`.
  - `test_a_whitelisted_name_is_suppressed_and_an_entry_suppressing_nothing_is_stale`.
  - `test_unreachable_code_is_reported_and_never_whitelisted`.
  - `test_windows_separators_in_vulture_output_name_the_same_tree`.
  - `test_the_header_names_the_trees_the_confidence_the_version_and_the_entries`.
  - `test_dead_code_exits_zero_when_nothing_is_listed`.
  - `test_dead_code_exits_two_when_it_cannot_run`, parametrised over:
    vulture absent (`find_spec` patched to `None`, and the runner asserted
    never called); `min_confidence` absent; no `source` tree; vulture exit 1;
    vulture exit 2; an output line in neither shape; a whitelist line with no
    reason.
  - `test_every_dead_code_whitelist_entry_names_a_binding_in_a_reported_tree`:
    the real tree, through `unbound_whitelist_entries`, with no vulture
    process.
  - `test_a_whitelist_entry_naming_no_binding_is_named`: planted.
  - `test_the_installed_vulture_reports_a_planted_unused_function`: the real
    process on a planted tree. It exits 1 naming the function, then exits 0
    once a planted `tests/test_x.py` calls it. There is no skip, for
    DEC-RDS-013's reason.

  All of these load a `tools/` script and are `integration` by the criterion,
  except any that only exercise a helper on planted text, which take what the
  criterion computes. Record the red run: `ModuleNotFoundError`/`FileNotFoundError`
  from `load_tool` before the script exists.
- `tests/test_ci_makefile.py`: add `dead-code` to
  `test_every_report_target_stays_out_of_the_ladder`'s required set and run
  it red ("dead-code is not a report target") before the target exists.
- `tests/test_gate_scripts.py`: add `"dead_code.py"` to
  `test_gate_script_is_runnable_as_a_script`'s list. Record honestly that this
  test is green *before* the file exists. `python tools/missing.py` exits 2
  with "can't open file" and no load-failure marker, both of which the test
  accepts, so it proves loadability once the file exists and never presence;
  the in-process tests above prove presence.
- `pyproject.toml` (R-RDS-1, R-RDS-2, DEC-RDS-001, DEC-RDS-002):
  - In the `dev` extra, `"vulture>=2.15",` after `"hypothesis",`, with the
    extra's comment gaining a paragraph: dev-only like `hypothesis`; floored,
    not pinned — exit code 3 means "dead code found" from 2.9, Python 3.14 is
    supported from 2.15, pip leaves a satisfied bare requirement alone, and a
    floor needs no update bot.
  - A new `[tool.vulture]` table after `[tool.specgraph]`'s last key, holding
    `min_confidence = 60` under a comment: vulture's level for an unused
    function, method, class, property, attribute or variable; read by
    `tools/dead_code.py`, which passes it explicitly, and by vulture itself
    when run from the root; a reporting threshold that gates nothing; why not
    the plan's 80 (it reports nothing over the two trees); and that no key
    vulture would apply on its own belongs in the table.

  Run `python tools/check_no_hardcoded_thresholds.py` and record PASS. Run
  `planlint --target . detect` and record that the floor locator is
  unchanged.
- `tools/dead_code.py` (R-RDS-3 to R-RDS-7, DEC-RDS-003 to DEC-RDS-006):
  stdlib only, with `sys.path` bootstrapped for `_common` as its siblings do;
  `logger`, `repo_root`, `read_pyproject_int` and `coverage_sources` come from
  `_common`.
  - `VULTURE_SECTION = "[tool.vulture]"`, `CONFIDENCE_KEY = "min_confidence"`,
    `USAGE_ONLY = ("tests",)` and `WHITELIST = Path("tools") /
    "dead_code_whitelist.txt"`.
  - `Finding(path, line, message, name)`, with `name` set only for
    `unused <kind> '<name>'` messages.
  - `parse_line(text) -> Finding | None`, where `None` means neither shape.
  - `read_whitelist(path) -> dict[str, str]`, name to reason, raising
    `ReportError` on a malformed line.
  - `unbound_whitelist_entries(root) -> list[str]`, the `ast` walk over every
    reported tree's `*.py` for bound names.
  - `run_vulture(root, trees, confidence) -> tuple[int, str, str]`, running
    `subprocess.run([sys.executable, "-m", "vulture", *trees, *usage,
    "--min-confidence", str(confidence)], cwd=root, capture_output=True,
    text=True, check=False)`.
  - `build_report(...) -> tuple[list[Finding], list[str]]`, giving the listed
    findings and the stale entries.
  - `main(argv, run=run_vulture) -> int`, with argparse over `argv[1:]` and
    `--root`; the header line; the findings in vulture's form; a
    `stale whitelist entries:` block; and the exit contract of R-RDS-5, with
    `ReportError` mapped to 2 and its message on stderr.

  The docstring states the report's contract, the two halves of staleness,
  and why vulture runs as a process. Run `ruff check tools/dead_code.py` and
  `mypy tools` and record both clean.
- `tools/dead_code_whitelist.txt` (R-RDS-6): a two-line header comment
  saying what an entry is and is not for, then `whitespace_split  # set on a
  shlex.shlex lexer in tools/stage_citations.py and read by the standard
  library` and `commenters  # likewise`. Nothing that is unused goes here.
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
  figures and whether `tools/dead_code.py` is on the per-file list. A floor
  that would fail is answered with a test, never a lower floor (C-RDS-5).
- **Gate:** `make test`

## Milestone 3 — The spec-status report, its guards seen red first

- `tests/test_spec_status.py` (new), written before the script and run red
  (R-RDS-9 to R-RDS-12, R-RDS-19). In-process through `load_tool` /
  `run_tool_main` with `--root` at a planted tree:
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
    parametrised: no header line, the word `IMPLEMENTED`, a proposal word
    outside the vocabulary, no `spec.md` at all.
  - `test_partial_evidence_is_listed_and_is_not_a_finding`: a `DRAFT` package
    with every criterion ticked and one milestone open, and an `APPROVED`
    package with milestones done and no criterion ticked — both rows printed,
    exit 0.
  - `test_a_changelog_entry_is_read_in_both_shapes_and_a_mention_is_not_an_entry`.
  - `test_the_workflow_column_names_verification_stages_no_workflow_runs`.
  - `test_spec_status_exits_two_when_it_cannot_run`, parametrised: no
    `openspec/changes/`; an undecodable `tasks.md`; an undecodable
    `CHANGELOG.md`.
  - `test_absent_changelog_and_workflows_are_empty_columns_not_failures`.
  - `test_spec_status_runs_over_this_repository`: the real tree; exit 0 or 1,
    one row per directory under `openspec/changes/`, and this package's own
    row present. It pins no count.

  All `integration` by the criterion. Record the red run.
- `tests/test_ci_makefile.py`: add `spec-status` to the required report
  targets, and run it red before the target exists.
  `tests/test_gate_scripts.py`: add `"spec_status.py"`, with the same note as
  Milestone 2.
- `tools/spec_status.py` (R-RDS-9 to R-RDS-12, DEC-RDS-007, DEC-RDS-009):
  - Bootstrap `sys.path` for `_common` and `stage_citations` as
    `stage_citations.py` does, and import `detect`, `parse_spec`, `MAKE_REF`
    and `SpecReadError` from `openspec_graph`.
  - `VOCABULARY = {"DRAFT": "draft", "APPROVED": "settled"}` and
    `PROPOSAL_VOCABULARY = {"proposed": "draft", "implemented": "settled"}`,
    with the proposal status line read as `^> \*\*Status: (\w+)\.?\*\*`.
  - `PackageRow` (a dataclass with every column of R-RDS-10).
  - `read_package(path, dialect, runs) -> PackageRow`.
  - `changelog_entries(text) -> dict[str, list[str]]`, holding the two entry
    shapes and the section each sits under.
  - `finding(row) -> str | None`, in R-RDS-11's order.
  - `main(argv) -> int`, with argparse over `argv[1:]` and `--root`, the rows,
    the summary line, and the exit contract of R-RDS-12. `stage_citations`'
    `ReportError` and an `OSError`/`UnicodeDecodeError` on a package file map
    to 2.

  The docstring states the vocabulary, the four findings, why the CHANGELOG
  and workflow columns enter none of them, and that it never edits a header.
  Run `ruff check` and `mypy tools` and record both clean.
- `Makefile`: add `spec-status` to `.PHONY`, and `spec-status: ## Report each
  change package's Status header beside its evidence — a report, not a gate`
  with the recipe `python tools/spec_status.py`. Confirm `make thresholds`
  PASS and `make help`.
- Run `make spec-status` at the branch head and record its complete output
  and exit code here. This is the worklist for the header follow-up of
  DEC-RDS-008. Set beside it the drafting reading — 9 `draft-but-complete`,
  0 `settled-but-empty`, 1 `headers-disagree` (`fix-u003-mandatory-given`),
  0 `header-unrecognised` — and note every difference, and that this
  package's own row, `DRAFT` with nothing done, carries no finding.
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
  cell the backticked command. Under it, one paragraph: none is composed into
  `ci`, `pre-pr` or a CI job; each becomes a gate only through its own package
  after a quarter of an empty report; and `make dead-code` needs the dev
  extra, exiting 2 without it. The `## CI hooks` table is untouched. Run
  `make docs-check`.
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
- `CHANGELOG.md`, under `## [Unreleased]`: `### Added — two hygiene reports:
  dead code and spec status (M2)`, with one bullet led by
  ``- **`report-dead-code-and-spec-status`.**`` naming the items of
  R-RDS-17. The figures in it are dated and name their commands; the
  CHANGELOG is exempt from tracking the tree afterwards.
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
  | AC-RDS-1 | `test_vulture_is_a_floored_dev_extra_and_never_a_runtime_dependency`, `test_an_exact_vulture_pin_or_a_runtime_vulture_is_named` |
  | AC-RDS-3 | the confidence, trees, whitelist, unreachable, separator and header tests |
  | AC-RDS-4 | `test_dead_code_exits_two_when_it_cannot_run`, `test_dead_code_exits_zero_when_nothing_is_listed` |
  | AC-RDS-5 | the two binding tests |
  | AC-RDS-6 | `test_the_installed_vulture_reports_a_planted_unused_function` |
  | AC-RDS-7 | the four finding tests and the checkbox test |
  | AC-RDS-8 | the partial-evidence, changelog-shape, exit-2 and absent-file tests |
  | AC-RDS-9 | adds `test_the_workflow_column_names_verification_stages_no_workflow_runs` |
  | AC-RDS-10 | adds `test_every_report_target_stays_out_of_the_ladder` |
  | AC-RDS-11 | `test_a_report_target_composed_into_the_ladder_is_named` |
  | AC-RDS-12 | adds the two reports-table tests and `test_a_second_table_in_hooks_is_not_read_as_ci_rows` |
  | AC-RDS-15 | the four suite-shape guards by name, which resolve on this branch |
- Confirm this package validates clean
  (`planlint --target . validate --fail-on ERROR --change report-dead-code-and-spec-status`),
  then the whole tree, and record each exit code.
- Confirm C-RDS-6: `git diff --stat <base>..HEAD -- openspec/changes` lists
  only this package's directory. Confirm C-RDS-1: `openspec_graph/`,
  `README.md`'s rules table, `tests/baseline_rules.json` and `[project]
  dependencies` are absent from the diff, and `python -m pytest
  tests/test_decomposition.py -k byte_identical -q` is green.
- Hand off, recorded here:
  - Milestone 3's `make spec-status` output goes to the maintainer as the
    worklist for the header follow-up. That follow-up decides the vocabulary
    and, for each package on `main`, the written exception for its one
    `Status` line or a supersession-style status record (DEC-RDS-008).
  - Milestone 2's `make dead-code` list goes to the M4 package for W5.1–3,
    with `speckit_section_body`, `speckit_subsection_body` and the three
    `report.__all__` names marked as this measurement's additions to the
    plan's list (DEC-RDS-012).
- Record for the plan's M2 row, when it is next updated: both reports exist,
  neither is in the ladder, and the plan's D4 figure was superseded by
  measurement (DEC-RDS-002).
- **Gate:** `make pre-pr`
