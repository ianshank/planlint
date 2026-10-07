# Tasks: shape-the-test-suite

Measured at `f7118a0` (`main`, the squash of #41; the tree is byte-identical
at `bb4e4ad`, the commit that carries this draft on
`claude/m2-shape-the-test-suite`), 2026-10-07. Every line number below is
re-checked against the branch head before the milestone that uses it; a
sibling package landing first may move a line without moving the fact.
Every number here names the command that produced it. At `f7118a0`: the
gate (`planlint --target . validate --fail-on ERROR`) exits 0 before the
first write under `openspec/` (50 specs, 0 error / 0 warn / 0 info; 51 with
this draft present); `wc -l tests/test_*.py | sort -n | tail -8` reads
`test_graft_rules.py` 684, `test_action_contract.py` 700,
`test_skill_contract.py` 821, `test_agent_artifacts.py` 836,
`test_gate_scripts.py` 849, `test_workflow_hardening.py` 1237,
`test_ci_hardening.py` 1378, 19722 total, over the 45 modules `ls
tests/test_*.py | wc -l` counts; `grep -c "def test_"` reads 60, 47, 52,
28, 38 and 25 for `test_ci_hardening`, `test_workflow_hardening`,
`test_gate_scripts`, `test_agent_artifacts`, `test_skill_contract` and
`test_action_contract`; `grep -n "^# --- "` finds seams in
`test_ci_hardening.py` at lines 40, 100, 231, 395, 452, 512, 530, 662, 766,
1133, 1195 and 1261, in `test_workflow_hardening.py` at 70, 576, 754, 824,
857, 894, 961, 1036, 1121 and 1174, in `test_gate_scripts.py` at 30, 96,
222, 323, 428, 582, 731 and 829, in `test_agent_artifacts.py` at 150, 319,
355, 445, 554, 604, 682 and 791, in `test_skill_contract.py` at 149, 298,
363, 474, 552, 575, 599, 625 and 740; `grep -rn "pytest.mark\." tests/ |
cut -d: -f3 | sort | uniq -c` lists only `parametrize` and `skipif` forms,
one of them the module-level `pytestmark` at
`tests/test_spec_discovery_identity.py:28` and two the `needs_bash` aliases;
`grep -n "markers\|strict" pyproject.toml` matches only `[tool.mypy]`
(lines 296, 298, 303, 306) and `[tool.pytest.ini_options]` at line 82 holds
`testpaths = ["tests"]` and `addopts = "-q"`; `grep -ln "subprocess.run"
tests/test_*.py` lists 16 modules and `grep -ln '"openspec_graph.cli"'
tests/test_*.py` two (`test_decomposition.py:108–109` with `--target`,
`test_skill_contract.py:657` without); `grep -rln write_speckit_spec
tests/test_*.py` lists nine modules, `test_detect_speckit.py` among them and
`test_e2e_corpus.py` not; `grep -L "from tests.support\|from tests import
support\|import tests.support" tests/test_*.py` lists 15 modules; `wc -l
tests/AGENTS.md` reads 51 against `MAX_NESTED_LINES = 60`
(`tests/test_agent_artifacts.py:702`). The baseline of R-TSS-2 — the sorted
`def test_*` names by AST over `tests/test_*.py` excluding
`tests/test_suite_shape.py`, hashed, and `python -m pytest tests/
--collect-only -q -o addopts="" -p no:cacheprovider
--ignore=tests/test_suite_shape.py | tail -1` — reads **1057 names, sha256
prefix `2f62db0aee56ef40`, 1602 collected**. The Appendix A durations
command (`python -m pytest tests/ -p no:cacheprovider -q --durations=12 -o
addopts=""`) on this four-core container, three sessions on the one tree:
**1602 passed in 149.98 s** (the drafter; load average 0.02 at the end),
**155.74 s** (the adversarial reviewer; load 0.25) and **157.68 s** (the
coordinator, at `bb4e4ad`; load 1.38 at the end). The drafter's twelve
slowest, call phase: `test_read_only_verbs_leave_tree_byte_identical`
6.71 s, `test_projections_are_byte_stable_across_runs` 3.54 s,
`test_sarif_returns_the_same_exit_code_as_the_text_run` 2.92 s,
`test_suite_survives_an_ambient_coverage_file` 1.95 s,
`test_the_real_wheel_passes_the_gate` 1.94 s,
`test_common_verbs_do_not_crash_under_ascii_stdout_encoding` 1.82 s,
`test_annotation_paths_resolve_from_the_repository_root` 1.72 s,
`test_the_action_reports_each_fixtures_labelled_status[passing]` 1.65 s,
`test_a_nested_target_is_scanned_at_its_own_root` 1.63 s,
`test_a_failing_run_populates_the_whole_evidence_bundle` 1.55 s,
`test_the_action_reports_each_fixtures_labelled_status[failing]` 1.54 s,
`test_the_evidence_directory_is_outside_the_scanned_tree` 1.54 s. The
coordinator's twelve at `bb4e4ad`: the read-only tree hash 7.41 s, the
projections 3.54 s, the SARIF parity 3.21 s, the real wheel 2.08 s,
`labelled_status[passing]` 1.99 s, the ASCII encoding 1.84 s,
`test_annotation_paths_resolve_from_the_repository_root` 1.74 s,
`test_the_evidence_directory_is_outside_the_scanned_tree` 1.69 s,
`labelled_status[failing]` 1.66 s, `labelled_status[sub]` 1.64 s,
`test_the_step_summary_reaches_the_job_summary_file` 1.62 s,
`test_a_nested_target_is_scanned_at_its_own_root` 1.62 s. Three readings
of an unchanged tree spread over about eight seconds: that spread is the
variance DEC-TSS-012 and Milestone 6 rest on. The same command read 1498
passed in 235 s at `9c4b6e9` (the plan) and 1578 passed in 212.5 s and
210.46 s at `5246931` (`measure-coverage-once`'s two sessions): the plan's
200 s row is already met at this head, by container variance and not by
any package's saving. Order (DEC-TSS-014): measure, then the splits as pure
moves with the flatness and bound guards seen red first, then the pointers,
then the tiers with their guards seen red, then the routing with its guards
seen red, then the loops with their guard seen red and the durations pair
bracketing exactly that change, then the records. One pull request — this
branch's, #42 — carries the whole package; the three stages (Milestones
0–3, 4–5, 6–7) are separate commits, each recording the baseline hash and
collected count; the red runs are recorded here and never committed.

## Milestone 0 — Grounding pass at the branch head  [DONE]

- Re-run the gate and record its exit code before the first edit:
  `planlint --target . validate --fail-on ERROR`.
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** exit 0 (51 specs, 0/0/0) before the first move.
- Re-take the measurements in the header and record what moved:
  `git rev-parse --short HEAD`; `wc -l tests/test_*.py | sort -n | tail -8`;
  `grep -c "def test_"` over the six modules; `grep -n "^# --- "` over the
  five over-bound modules; the marker, `pyproject.toml`, `subprocess.run`,
  `"openspec_graph.cli"`, `"spec.md"`, `write_speckit_spec` and helper-less
  greps; `wc -l tests/AGENTS.md`.
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** at `bb4e4ad` (main `f7118a0` + the draft): the header's figures held, with
  `test_gate_scripts.py` 849 lines and 19722 in total; 45 modules; markers only
  `parametrize` and `skipif`; 16 `subprocess.run` modules; 15 helper-less;
  `tests/AGENTS.md` 51 lines. The durations command, re-run at `bb4e4ad`: 1602
  passed in 157.68 s (load average 1.38 at the end).
- Record the baseline every split and every stage commit is checked
  against, as the commands Milestones 1–3 and 7 re-run: the sorted
  test-name set, `python - <<'PY'` over `ast` collecting every
  `FunctionDef` named `test_*` across `tests/test_*.py` with
  `tests/test_suite_shape.py` skipped, printed sorted and hashed with
  `sha256`; and the collected count, `python -m pytest tests/
  --collect-only -q -o addopts="" -p no:cacheprovider
  --ignore=tests/test_suite_shape.py | tail -1`. At `f7118a0`: 1057 names,
  `2f62db0aee56ef40`, 1602 collected. The exclusion is what makes every
  later comparison a comparison with this figure (R-TSS-2, DEC-TSS-015).
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** re-taken at `bb4e4ad`: 1057 names, `2f62db0aee56ef40`, 1602 collected.
- Record the pointer set R-TSS-4 re-points, as the grep Milestone 3 re-runs:
  `grep -rn "test_ci_hardening\|test_workflow_hardening\|test_gate_scripts\.py\|test_agent_artifacts\.py\|test_skill_contract\.py" --include=*.py --include=*.md --include=*.sh --include=*.yml --include=*.toml . | grep -v "^./.git/\|^./openspec/changes/\|^./docs/reflection-plan\|^./build/"`.
  At `f7118a0` the live pointers are `tests/conftest.py:48`,
  `tools/_common.py:157`, `tests/support.py:259–262`,
  `tests/test_gate_scripts.py:11`, `tests/test_action_contract.py:14`,
  `tests/test_workflow_hardening.py:83`, `tests/test_detect_corpus.py:48`,
  `tests/test_agent_artifacts.py:565`, `tests/test_claude_hooks.py:42–44`,
  `.claude/hooks/nudge_rule_registry.sh:43` (and the arms at 51, 55),
  `tests/AGENTS.md:16–20, 32`, `docs/architecture/c4.md:81, 217–221`,
  `docs/hooks.md:64, 131, 142, 199`, `docs/aqa.md:48, 108`,
  `docs/distribution-plan.md:88, 210–212`, `pyproject.toml:156, 200`,
  `.github/dependabot.yml:21, 35`, `.github/workflows/ci.yml:10`,
  `.github/workflows/release.yml:24`, `skills/AGENTS.md:13, 27`,
  `evals/AGENTS.md:13`, `README.md:350, 354`, `openspec_graph/cli.py:60,
  94`, `.claude/agents/planlint-verifier.md:21, 22, 24` and the two skills
  under `.claude/skills/`; the dated records are `CHANGELOG.md:73, 95, 929,
  986`, `docs/peer-review-2026-09.md:220`, `docs/next-steps.md:232, 298, 396`
  and `docs/eval-corpus-plan.md:233`, which stay. The one hard dependency
  on a module path is `tests/test_ci_hardening.py:197`, which passes its
  own path to the pytest it nests (R-TSS-3). The eight shipped spec records
  that name a deleted module — `select-zero-cost-guards` spec `:110`
  (R-ZCG-10) and `:277` (DEC-ZCG-010); `harden-ci-workflows` spec `:156`
  (R-HCW-15), `:162` (R-HCW-16) and `:286` (DEC-HCW-008);
  `pin-actions-by-sha` spec `:157` (R-ASP-8) and `:184` (R-ASP-11);
  `prepare-release-0-3-0` spec `:481` (DEC-REL-011, the sentence at
  `:512–514`) — are superseded in DEC-TSS-016 and not edited.
- Confirm the facts the loop conversion rests on: `openspec_graph/cli.py:980`
  `main(argv)` returns `int(args.func(args))` after reconfiguring the
  streams; `tests/test_cli_surface.py:240–281` call `main_deprecated` under
  `capsys`; `tests/test_e2e_corpus.py:245–255` `_findings` is called by
  `test_a_waived_g010_still_fails_a_fail_on_info_run` too; the four bodies
  are at `tests/test_report.py:528` and `:605`, `tests/test_sarif.py:306`,
  `tests/test_e2e_corpus.py:257`, with nine, four-per-case, eight and four
  `run_cli` calls.
- Confirm the facts the tier criterion rests on (R-TSS-6, DEC-TSS-007):
  `tests/test_cli_surface.py`'s `fixtures` fixture (`:471–477`,
  `Path(__file__)` under `fixtures/`) and `repo_root` fixture (`:480–482`,
  `Path(__file__).resolve().parents[1]`), `test_entry_points_wired_in_pyproject`
  (`:212–214`) reading through `repo_root`;
  `tests/test_skill_contract.py:133`'s `populated_repo` and
  `tests/test_rules_speckit.py:266` building `__file__`-rooted paths under
  `fixtures/` in a body; `tests/test_detect_corpus.py:307`'s
  `Path(detect.__file__)`; `tests/support.py`'s `load_tool` and
  `run_tool_main` as the tree-readers that name no `__file__` at their
  call sites.
- Confirm `tests/test_ci_hardening.py:843` `_one_run_violations` still
  names every pytest recipe other than `coverage-run`'s (DEC-TSS-008 rests
  on it), and that `grep -rln write_speckit_spec tests/test_*.py` still
  lists the nine modules with `test_e2e_corpus.py` absent and
  `test_detect_speckit.py` present (DEC-TSS-009).
- **Gate:** `make validate`

## Milestone 1 — Split `test_ci_hardening.py` and `test_gate_scripts.py`, guards seen red first  [DONE]

- `tests/test_suite_shape.py` (new), written before any move and run red
  (R-TSS-1, R-TSS-12, DEC-TSS-004, DEC-TSS-015): `MAX_TEST_MODULE_LINES =
  700` with a comment naming the plan item and the `wc -l` command; planned
  tests, named here so AC-TSS-1 can be re-pointed when they exist:
  `test_the_tests_directory_stays_flat` (no `test_*.py` under any
  subdirectory of `tests/`, through a recursive glob compared with the flat
  one) and `test_no_test_module_exceeds_the_line_bound` (every
  `tests/test_*.py` has at most the bound's lines, the offenders named with
  their counts). Run the module and record the red: the bound test names
  the five modules of the header; the flatness test is green from the
  start, which is the expected shape, and its planted half — a
  `tests/<dir>/test_x.py` under a temporary copy — is red in
  `test_a_mismarked_or_unmarked_planted_module_is_named` (Milestone 4).
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** red as expected — `test modules over 700 lines … [('test_agent_artifacts.py',
  836), ('test_ci_hardening.py', 1378), ('test_gate_scripts.py', 849),
  ('test_skill_contract.py', 821), ('test_workflow_hardening.py', 1237)]`; the
  flatness test green. The moves were made by a script that copies each top-level
  node with its decorators and its comment block, bodies byte-for-byte, and prunes
  imports with `ruff --fix` (F401, F811, I001); it refuses to place a helper two
  destinations need without a decision, so each shared helper below is a recorded
  choice.
- Create the new modules with a docstring naming what each holds and whose
  criteria it verifies (R-TSS-2), then move the sections of
  `tests/test_ci_hardening.py` by seam, bodies untouched, imports pruned to
  what each module uses (at `f7118a0`, tests per seam from the `awk` count
  in the proposal): `tests/test_ci_workflow.py` ← the CI-configuration
  claims (lines 530–662, 6 tests: `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt`,
  `test_mypy_is_strict_and_warns_on_unreachable_code`,
  `test_a_print_in_a_library_module_fails_lint`,
  `test_a_bare_generic_in_tools_fails_typecheck`, `test_lint_is_a_hard_gate`,
  `test_graph_diff_artifact_uploaded`, with `_pyproject()` until Milestone
  4 moves it to `tests/support.py`), the five `ci.yml` and hooks-table
  tests of the two-track section (662–766:
  `test_ci_job_blocks_returns_empty_when_jobs_key_is_absent`,
  `test_ci_job_blocks_ignores_comments_mentioning_jobs`,
  `test_ci_workflow_has_a_windows_job`,
  `test_ci_workflow_has_an_encoding_stress_job`,
  `test_hooks_ci_table_lists_every_ci_job`, with the `_ci_job_blocks`
  alias R-HCW-16 placed), the four workflow and hooks tests of the one-run
  section (1038–1133: `test_every_job_running_the_suite_uploads_its_coverage_report`,
  `test_a_suite_job_without_a_coverage_upload_is_named`,
  `test_every_hooks_ci_table_row_names_a_job_or_workflow`,
  `test_a_hooks_row_naming_no_job_is_named`, with
  `_suite_jobs_without_coverage_upload` and `_hooks_rows_naming_no_job`),
  and `test_ci_workflow_has_an_action_contract_job` and
  `test_every_action_fixture_has_a_contract_leg` (1133–1188);
  `tests/test_ci_makefile.py` ← `test_makefile_has_e2e_live_target`,
  `test_makefile_has_matcher_accuracy_report_target`, the four Makefile
  tests of the one-run section (766–1038:
  `test_the_suite_runs_once_through_coverage_run`,
  `test_test_and_coverage_tools_read_the_one_report_scoped`,
  `test_a_recipe_that_pins_a_cov_source_or_skips_the_run_dependency_is_named`,
  `test_makefile_has_coverage_per_file_report_target`, with
  `_makefile_text`, `_make_targets`, `_recipe_lines`, `_prerequisites`,
  `_one_run_violations` and their constants) and
  `test_the_contract_job_is_not_wired_into_a_make_target`;
  `tests/test_coverage_checkers.py` ← the branch-floor section (40–100, 4
  tests) and the line-floor section (100–231, 8 tests, including
  `test_coverage_floor_fails_below_threshold_pytest`,
  `test_coverage_floor_passes_at_threshold`,
  `test_suite_survives_an_ambient_coverage_file` — whose nested path at
  line 197 becomes `tests/test_coverage_checkers.py` — and
  `test_env_without_coverage_strips_every_coverage_variable`);
  `tests/test_graph_tools.py` ← graph-diff (231–395, 7 tests) and
  `render_mermaid.py` (395–452, 4 tests) with the module's own `repo`
  fixture and `_graph_json` helpers; `tests/test_threshold_guard.py` ← the
  threshold guard's own coverage (1261–1378, 6 tests);
  `tests/test_gate_scripts.py` ← `test_gate_script_is_runnable_as_a_script`
  (452–512) with its parametrize list; `tests/test_rule_registry_docs.py` ←
  `test_rule_set_matches_baseline` (512–530); `tests/test_workflow_pins.py`
  (created in Milestone 2; hold the Dependabot section, 1195–1261, 3 tests,
  with `_dependabot_directories`, in `tests/test_ci_workflow.py` until then
  and move it in Milestone 2) — then delete `tests/test_ci_hardening.py`.
- `tests/test_gate_scripts.py`: move its scoped-floor section (428–582, 9
  tests), one-run section (582–731, 6 tests) and per-file section
  (731–829, 5 tests) with `_pyproject(path, **keys)`,
  `_pyproject_with_sources` and the report writers into
  `tests/test_coverage_checkers.py`; move its
  `check_no_hardcoded_thresholds.py` section (323–428, 9 tests) into
  `tests/test_threshold_guard.py`; the `_common.read_json` section (829 to
  the end) stays; a helper both halves need goes to `tests/support.py`
  once (R-TSS-2). Update the comment `measure-coverage-once` rewrote above
  the scoped-floor tests to sit above them in their new module; update the
  module docstring's pointer at line 11.
- Re-run the baseline and record: the test-name hash `2f62db0aee56ef40` and
  the collected count 1602 with `tests/test_suite_shape.py` excluded;
  `python -m pytest tests/test_ci_workflow.py tests/test_ci_makefile.py
  tests/test_coverage_checkers.py tests/test_graph_tools.py
  tests/test_threshold_guard.py tests/test_gate_scripts.py
  tests/test_rule_registry_docs.py -q` green; `python -m pytest
  tests/test_spec_test_citations.py -q` green; `wc -l` of each new module
  under the bound; the bound guard still red on the four remaining
  over-bound modules.
- **Gate:** `make test`, with the bound guard the one failure until
  Milestone 3 (written red first, it cannot be green while a module is over
  the bound); every moved test green.
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** hash `2f62db0aee56ef40`, 1057 names, 1602 collected — equal. Sizes:
  `test_ci_workflow.py` 448, `test_ci_makefile.py` 293, `test_coverage_checkers.py`
  572, `test_graph_tools.py` 228, `test_threshold_guard.py` 225, `test_gate_scripts.py`
  380, `test_rule_registry_docs.py` 116. `REPO_ROOT`, `TOOLS` and
  `_COVERAGE_REPORT` are per-module constants, written once in each module that
  uses them. The nested pytest in `test_suite_survives_an_ambient_coverage_file`
  names its own module through `Path(__file__).name`, so a later move cannot
  orphan it again. `make test`: exit 2, wall 169 s, the bound guard the only failure
  (three modules still over: `test_agent_artifacts.py` 836, `test_skill_contract.py`
  821, `test_workflow_hardening.py` 1237 — the header expected four because it
  counted `test_gate_scripts.py`, whose split is part of this milestone).

## Milestone 2 — Split `test_workflow_hardening.py`  [DONE]

- `tests/workflow_support.py` (new, not collected): the readers more than
  one collected module uses (at `f7118a0`, from the helper block at lines
  70–576: `_rel`, `_code_lines`, `_indent`, `_top_level_block`, `_ci_text`,
  `_pyproject`, `_job_level_keys`, `_uncommented_permission_blocks` (273)
  — which `tests/test_release_surface.py` reads in Milestone 3 — and the
  `WORKFLOWS`, `CI`, `RELEASE`, `PYPROJECT`, `DOCKERFILE` and `DEPENDABOT`
  path constants), each keeping its docstring; a reader one section uses
  moves with that section. Note in its docstring that it is the pattern of
  `tests/graft_support.py`, and that no collected module imports another
  (R-TSS-2, DEC-HCW-009).
- `tests/test_workflow_pins.py` ← action refs agree, every ref is a pinned
  SHA with its tag comment, every action at or above its major floor
  (576–754, 12 tests, with `_uses_refs`, `_pin_offenders`,
  `_ref_disagreements`, `_major`, `_action_major_floors`,
  `_floor_offenders`); the Dockerfile and its update bot (1036–1121, 8
  tests, with `_dockerfile_from`, `_dockerfile_tag_version`,
  `_dockerfile_offenders`, `_user_override_offenders`, `_dependabot_entries`,
  `_docker_watch_offenders`); and the Dependabot section held in
  `tests/test_ci_workflow.py` since Milestone 1
  (`test_dependabot_config_exists_and_watches_github_actions`,
  `test_every_composite_action_directory_is_watched_by_dependabot`,
  `test_dependabot_does_not_add_a_pip_ecosystem`, with
  `_dependabot_directories`) — so both readers R-ASP-11 names live in one
  module (DEC-TSS-016).
- `tests/test_workflow_posture.py` ← least privilege (754–824, 6 tests,
  with `_job_permission_blocks` and `_write_permissions`;
  `_uncommented_permission_blocks` comes from `workflow_support`), timeouts
  (824–857, 4, with `_timeout_range`, `_timeout_offenders`), concurrency
  (857–894, 3, with `_concurrency_offenders`), the thresholds guard's
  silence (1121–1174, 2) and the attestations input (1174–1237, 1 — the
  guard DEC-REL-011 left in this module, DEC-TSS-016).
- `tests/test_workflow_python.py` ← one Python default (894–961, 5, with
  `_quoted_version_literals`, `_matrix_versions`, `_workflow_env`,
  `_action_input_default`) and the experimental leg, classifiers and docs
  (961–1036, 6, with `_experimental_leg_offenders`, `_classifier_versions`,
  `_hooks_test_row_bounds`; this is where
  `test_hooks_test_row_names_the_matrix_bounds` lives). Then delete
  `tests/test_workflow_hardening.py`.
- Re-run the baseline and record equality with Milestone 0's hash and
  count; `python -m pytest tests/test_workflow_pins.py
  tests/test_workflow_posture.py tests/test_workflow_python.py
  tests/test_ci_workflow.py -q` green; `wc -l` of each under the bound; the
  bound guard red on the two remaining modules.
- **Gate:** `make test`, the bound guard again the one failure.
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** hash and count equal; sizes `tests/workflow_support.py` 169,
  `test_workflow_pins.py` 538, `test_workflow_posture.py` 329,
  `test_workflow_python.py` 278, `test_ci_workflow.py` 387 after the Dependabot
  section left it. The shared readers in `tests/workflow_support.py` are the
  listed ones plus `_job_permission_blocks` (which `_uncommented_permission_blocks`
  calls), `_FROM` and `_dockerfile_from` (read by the pins and the Python modules),
  and the module's path and table constants. The four modules' tests and the
  citation test green; the bound guard red on `test_agent_artifacts.py` and
  `test_skill_contract.py` only.

## Milestone 3 — Split `test_agent_artifacts.py` and `test_skill_contract.py`, re-point every pointer  [DONE]

- `tests/test_release_surface.py` (new) ← `tests/test_agent_artifacts.py`'s
  release workflow (445–554, 2 tests), generated artifacts (554–604, 3) and
  packaging surface (604–682, 3) sections, its `_workflow_jobs` (448) and
  `_uncommented` (477) helpers moving with them unchanged so this stage
  stays pure moves; Milestone 5 routes them (R-TSS-8, DEC-HCW-009's
  deferral closed; no import from a collected module).
  `test_agent_artifacts.py` keeps evals (150–319), `context7.json`
  (319–355), `llms.txt` (355–445), the nested `AGENTS.md` contract
  (682–791) and the cited-command check (791–836), with `_ids`,
  `_frontmatter*`, `_readme_tables` and `_index_id`.
- `tests/test_skill_distribution.py` (new) ← `tests/test_skill_contract.py`'s
  generated catalog (474–552, 5 tests, with `RENDERER` and `_run_renderer`),
  manifest agreement (552–575, 1), shipped CI asset (575–599, 2), packaging
  and gate coverage (625–740, 7) and distribution rename (740–821, 3).
  `test_skill_contract.py` keeps the read-only claim (149–298, with
  `READ_ONLY_INVOCATIONS` and `populated_repo`), the exit-code contract
  (298–363), the exit-2 remainder (363–474) and the boundaries (599–625).
- Re-run the baseline and record equality; `wc -l tests/test_*.py |
  sort -n | tail -8` with every module at or under the bound;
  `test_no_test_module_exceeds_the_line_bound` green for the first time —
  record it.
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** hash and count equal; `wc -l tests/test_*.py | sort -n | tail -8` tops
  out at `test_action_contract.py` 700 and `test_graft_rules.py` 684, 19530 in
  total; the bound guard green, 2 passed. `test_agent_artifacts.py` 568,
  `test_release_surface.py` 251, `test_skill_contract.py` 466,
  `test_skill_distribution.py` 334; the skill module's path constants and its
  `_load_tool = load_tool` alias are written in both halves.
- Re-point every live pointer of Milestone 0's grep to the module that now
  holds the guard it names, and record the after-grep: `tests/conftest.py:48`
  → `tests/test_graph_tools.py`; `tools/_common.py:157` →
  `tests/test_coverage_checkers.py`; `tests/support.py:259–262` → the alias
  lives in `tests/test_ci_workflow.py`, and the sentence deferring
  `test_agent_artifacts.py`'s near-copy to W7.4 is replaced by one saying
  it was routed here; `tests/test_gate_scripts.py:11` → the contract is
  local; `tests/test_action_contract.py:14` → `tests.support.workflow_job_blocks`;
  `tests/test_detect_corpus.py:48` and `tests/test_agent_artifacts.py:565`
  → unchanged if the named test stayed, else the new module;
  `.claude/hooks/nudge_rule_registry.sh:43` → `pytest
  tests/test_workflow_pins.py -k dependabot`; the arm at 51 adds
  `tests/test_skill_distribution.py` after `tests/test_skill_contract.py`
  (the `NUDGED` remedy substring in `tests/test_claude_hooks.py:42–43`
  still matches); `docs/hooks.md:64` → the three workflow modules, and the
  remedies at 131 and 142 add `tests/test_skill_distribution.py` and
  `tests/test_release_surface.py` where the test they point at moved;
  `docs/aqa.md:48` → `tests/test_workflow_python.py`, `:108` adds
  `tests/test_release_surface.py`; `pyproject.toml:156, 200` and
  `.github/dependabot.yml:21, 35` → `tests/test_workflow_pins.py`;
  `.github/workflows/ci.yml:10` → `tests/test_workflow_posture.py`;
  `.github/workflows/release.yml:24` → `tests/test_workflow_python.py`;
  `skills/AGENTS.md:13, 27` → `tests/test_skill_distribution.py` for the
  catalog and manifests; `README.md:354` → adds `tests/test_release_surface.py`
  for the release workflow; `.claude/agents/planlint-verifier.md:21` →
  `tests/test_skill_distribution.py::test_rule_catalog_is_fresh` and
  `tests/test_release_surface.py::test_generated_artifacts_are_fresh`,
  `:22, 24` → unchanged if the named tests stayed;
  `docs/distribution-plan.md:88, 210–212` → likewise; the two
  `.claude/skills/` checklists likewise. Only comment lines change under
  `.github/` (C-TSS-2); `README.md:350`, `evals/AGENTS.md:13` and
  `openspec_graph/cli.py:60, 94` stay true and are not touched. Dated
  records and the eight shipped spec records of DEC-TSS-016 are not edited
  (R-TSS-4, DEC-TSS-013).
- `tests/AGENTS.md`: in the diagram, add `ws["workflow_support.py<br/>workflow
  readers, never asserting"]` under "shared, not collected" and
  `s["test_suite_shape.py<br/>flat, bounded, tiered"]` under "split by
  subject" (the gate_scripts node's text stays true); the sentence at line
  32 keeps its fact; Milestone 4 adds the tier bullet and the run sentence.
  `wc -l tests/AGENTS.md` after, against `MAX_NESTED_LINES`.
- `docs/architecture/c4.md`: §4's `tests/*` row names
  `test_coverage_checkers.py` for the two checkers, `test_gate_scripts.py`
  for the scripts no other module tests, `test_suite_shape.py` for the
  shape; §4b's diagram adds a `checkers["test_coverage_checkers.py<br/>both
  floors, scoped reads, per-file"]` node feeding `covrun` beside
  `gatetests`, and the "Why in-process" paragraph keeps
  `test_gate_script_is_runnable_as_a_script` by name. Run `python -m pytest
  tests/test_rule_registry_docs.py -q` (it reads §4's module map, not this
  row) and record green.
- `CHANGELOG.md`, under `## [Unreleased]`: `### Changed — the test suite
  split by concern (M2)` with a `shape-the-test-suite` entry naming the two
  removed modules and the ten new ones, and the eight records DEC-TSS-016
  supersedes by id; Milestones 4, 5 and 7 extend it (R-TSS-13).
- Run `make docs-check`, `python -m pytest tests/test_agent_artifacts.py
  tests/test_claude_hooks.py tests/test_adopter_urls.py -q` and the
  citation test; record green. Commit the first stage (Milestones 0–3),
  recording the baseline hash and count in the commit message, and record
  PR #42's CI run on it: every leg green.
  **Recorded (stage 1, 2026-10-07, on `26e4f8c` + the moves):** every pointer of Milestone 0's grep re-pointed as listed — with
  `pyproject.toml:156` to `tests/test_workflow_posture.py` (the timeout bounds) and
  `:200` to `tests/test_workflow_pins.py` (the major floors), and
  `.claude/agents/planlint-verifier.md:22, 24` to `tests/test_release_surface.py`,
  which holds the Docker-context and root-markdown tests; the after-grep finds
  the two module names only in the new modules' "Moved from" docstrings,
  `tests/support.py`'s history sentence and dated records. `make docs-check`
  passes; the agent-artifact, release-surface, hooks, adopter, rule-registry,
  citation, skill and suite-shape modules: 330 passed. `make test`: exit 0, wall 166 s, all four scoped floors met (`openspec_graph/` 2276/2292 and 744/762, `tools/` 946/981 and 323/344 — the two extra `tools/` statements are the scope normalisation of #41's review fix, already on `main`).
- **Gate:** `make docs-check`, then `make test`

## Milestone 4 — Tiers, their guards seen red first  [DONE]

- `tests/test_suite_shape.py`, written before any mark and run red
  (R-TSS-5, R-TSS-6, R-TSS-12, DEC-TSS-005, DEC-TSS-007): planned tests,
  named here so AC-TSS-6, 7 and 8 can be re-pointed when they exist —
  `test_pytest_registers_exactly_the_three_tier_markers_strictly`
  (`[tool.pytest.ini_options].markers` parsed with `tomllib`/`tomli`
  through the `_pyproject()` reader — moved from `tests/test_ci_workflow.py`
  to `tests/support.py` as `read_pyproject()` now that two modules need
  it, with `tests/workflow_support.py`'s private copy routed through it in
  the same commit — holds
  exactly `unit`, `integration`, `e2e` by name, each description
  non-empty; `addopts` contains `--strict-markers`; `testpaths ==
  ["tests"]`);
  `test_an_unregistered_marker_fails_collection_under_strict_markers` (a
  planted module with `@pytest.mark.nonsuch` under a copied
  `pyproject.toml`, `python -m pytest --collect-only -q` in a subprocess
  under `env_without_coverage()`, non-zero exit naming the mark — an `e2e`
  test by its own criterion); `test_every_test_carries_exactly_one_tier_marker`
  (AST over `tests/test_*.py`: module-level `pytestmark` tiers — a single
  `pytest.mark.<tier>` or a list of marks — ∪ decorator tiers per `def
  test_*`, exactly one, offenders named with their tiers; any module-level
  `name = pytest.mark.<tier>` alias named as a violation);
  `test_every_tier_marker_matches_its_mechanical_criterion` (per test, the
  tier R-TSS-6 computes — the criterion in the uncollected
  `tests/shape_support.py`, which follows helpers, classes, constants,
  requested and autouse fixtures and imports into every module under
  `tests/`, so `load_tool`, `run_tool_main`, `read_pyproject` and `run_cli`
  take their signals from their bodies and no list names them — against
  the one tier the test carries; disagreements named with the chain of
  names that decided the tier, and the per-module tally logged at INFO);
  `test_a_mismarked_or_unmarked_planted_module_is_named` (the helpers over
  planted texts, one parameter each: an unmarked test; a test with two
  tiers; a `unit` test calling `run_cli`; an `e2e` test naming no spawn; a
  `unit` test naming a `__file__`-bound constant; a `unit` test that reads
  the tree only through a planted `repo_root` fixture parameter; a `unit`
  test under a planted autouse fixture that spawns; a `unit` test that
  spawns only through a method of a class imported from a planted support
  module; a `unit` test that binds a tree read to a local it never uses; a
  tier written through an alias; a module over the bound; a
  `tests/<dir>/test_x.py` under a temporary copy named by the flatness
  helper; and, not named, a `unit` test whose body builds
  `Path(__file__).parent / "fixtures" / ...`, a `fixtures`-rooted module
  constant, a `-> subprocess.CompletedProcess` annotation with the
  constructor in a fake, and a module exactly at the bound).
  Record the red: the registration test red on the unchanged
  `pyproject.toml`; the exactly-one test naming every test in the tree;
  the criterion test idle until marks exist and red on the first module
  marked wrongly, if any — record which.
- `pyproject.toml` `[tool.pytest.ini_options]`: `markers = [...]` with the
  three entries, each `"<tier>: <criterion in one sentence>"` as R-TSS-6
  states it; `addopts = "-q --strict-markers"`; `testpaths` unchanged; a
  comment above saying the tiers are cost signals, that both levels count,
  that a mixed module marks per function, that a tier is never aliased,
  and that `tests/test_suite_shape.py` holds the guards (DEC-TSS-005,
  DEC-TSS-006).
- Apply the marks, module by module, letting the criterion guard decide:
  per-function `@pytest.mark.<tier>` wherever the guard reports a mix,
  with no module-level tier — the expected shape for every module that
  spawns, because the simulation at `f7118a0` gives `test_report` 30 unit /
  2 integration / 13 e2e, `test_sarif` 8 / 3 / 13 and `test_cli_surface`
  8 / 6 / 14; `pytestmark = pytest.mark.<tier>` under the imports only where
  the guard reports one tier for every test in the module, and the list
  form `pytestmark = [pytest.mark.skipif(...), pytest.mark.<tier>]` where a
  `pytestmark` already exists (`tests/test_spec_discovery_identity.py:28`).
  Expected single-tier modules at `f7118a0`, to be confirmed by the guard
  and recorded: `integration` for the repository-reading guards (the three
  workflow modules, `test_ci_workflow`, `test_ci_makefile`,
  `test_threshold_guard`, `test_agent_artifacts`, `test_release_surface`,
  `test_adopter_urls`, `test_rule_registry_docs`,
  `test_spec_test_citations`, among others); `unit` for the parser, rule,
  graph, ledger, mermaid, dialect-card and property modules; `e2e` for
  `test_action_contract` and `test_wheel_metadata` if every test spawns;
  mixed, hence per-function, for `test_report`, `test_sarif`,
  `test_cli_surface`, `test_e2e_corpus`, `test_graft_cli`,
  `test_decomposition`, `test_skill_contract`, `test_gate_scripts`,
  `test_coverage_checkers`, `test_graph_tools` and `test_suite_shape`
  itself. Record the tally the guard prints per tier.
- Record the fast tier (R-TSS-7): `python -m pytest -m unit --collect-only
  -q -o addopts="" | tail -1` and `python -m pytest -m unit -q -p
  no:cacheprovider -o addopts=""`'s last line, with the commit; and
  `python -m pytest -m "not unit" --collect-only -q -o addopts="" | tail -1`
  so the two sum to the collected count.
- `docs/hooks.md`: after the optional pre-push section, a paragraph headed
  as the fast local loop: `python -m pytest -m unit` runs the tier that
  starts no process and reads none of this repository's own files, in the
  time Milestone 4 recorded; what `-m "not unit"` adds; why it is a command
  and not a Make target (DEC-TSS-008, naming the one-run guard); the CI
  table and the `test` row untouched. `tests/AGENTS.md`: a fourth "thing to
  know" — every test carries exactly one of `unit`, `integration`, `e2e`
  by the criterion `tests/test_suite_shape.py` checks, so a new test
  without a mark fails collection — and the run sentence gains "`python -m
  pytest -m unit` is the fast tier" before `make test`; replace where
  possible, `wc -l` after against the budget; run `python -m pytest
  tests/test_agent_artifacts.py -q -k "nested_agents or agent_index_links"`
  and record green.
- `CHANGELOG.md`: extend the entry with the tiers, the strict markers and
  the fast-tier command.
- **Gate:** `make test` — the suite green under `--strict-markers`, the
  four guards green on the tree and red on their planted texts, the floors
  held; then `make lint`.
  **Recorded (Milestone 4, 2026-10-07, on `378bd54` + the Milestone 4 tree):**
  - *Red first.* `python -m pytest tests/test_suite_shape.py -q -o addopts=""`
    on the unchanged `pyproject.toml`: 3 failed. The registration test read
    no markers (`registered markers [] are not exactly the tiers`); the
    nested collection of the planted `@pytest.mark.nonsuch` module exited 0
    with only a `PytestUnknownMarkWarning`; the exactly-one test named all
    1064 test functions with no tier, and no alias. The criterion test was
    idle (0 disagreements with no marks), and the planted test passed every
    case from its first run, its helpers being written with it. With the
    markers and `--strict-markers` in place, both registration tests pass.
    The marks were written by a script from the criterion's own verdicts, so
    no module was marked wrongly on the tree; red on the real tree is shown
    on a copy with `tests/test_graph.py`'s `pytestmark` flipped to
    `integration`: 44 tests named, each with the criterion's verdict.
  - *Corrections found while implementing,* folded into R-TSS-6, DEC-TSS-007
    and DEC-TSS-017. The hand list of tree-readers gave way to following
    imports into every module under `tests/`. A class reached now contributes
    its methods: `ActionRun.run_step` starts `bash`. A name imported from a
    `tools/` script counts as running it in-process:
    `tests/test_wheel_metadata.py` puts `tools/` on `sys.path`. Function-local
    imports, autouse fixtures and `usefixtures` resolve. A process start is
    any reference to a process-starting function, and a tree read bound to
    a local nobody uses still counts.
  - *Moves made to fit the marks.* `tests/test_action_contract.py` was at 700
    lines, so its runner simulator moved to the uncollected
    `tests/action_support.py` (446 lines after). `test_graft_rules.py` was
    684 lines with 59 `unit` tests and one `integration` test, so per-function
    marks would have reached 744; `test_rule_registry_baseline_is_unchanged`
    moved beside `test_rule_set_matches_baseline` in
    `tests/test_rule_registry_docs.py`, its body unchanged but for `RULES`
    in place of `rules.RULES`. The two `_pyproject()` copies became
    `tests.support.read_pyproject()`. After: 1057 names, sha256 prefix
    `2f62db0aee56ef40`, and 1602 collected with `tests/test_suite_shape.py`
    ignored — both unchanged.
  - *Shapes and tally.* 23 modules carry one `pytestmark` tier under their
    imports and 31 mark per function. `tests/test_spec_discovery_identity.py`
    is mixed, so its `skipif` `pytestmark` stays as it was and the list form
    had no module to apply to. The criterion's tally is 575 `unit`, 291
    `integration` and 198 `e2e` of 1064 test functions. Against the expected
    shapes: `test_graft_cli` and `test_graft_detection` are single-tier
    `unit` (their CLI tests run `cli.main` in-process); `test_action_contract`
    (15 `integration`, 10 `e2e`) and `test_wheel_metadata` (16 and 1) are
    mixed; `test_cli_speckit` and `test_e2e_corpus` are single-tier `e2e`.
    The largest module after the marks is `tests/test_report.py`, 690 lines.
  - *Fast tier (R-TSS-7).* `python -m pytest -m unit --collect-only -q -o
    addopts=""`: `733/1622 tests collected (889 deselected)`; `-m "not unit"`:
    `889/1622 tests collected (733 deselected)`, the two summing to the
    collected count. `python -m pytest -m unit -q -p no:cacheprovider -o
    addopts=""`: `733 passed, 889 deselected in 12.96s`, wall 13.4 s.
  - *Runtime audit (DEC-TSS-017).* The whole suite ran once under a
    `sys.addaudithook` plugin kept in the session scratchpad, not committed.
    It recorded each test's `subprocess.Popen` and `os` process events and
    its `open` events under the checkout: `1604 passed in 159.04s`, 759
    items with any event. `.egg-info/` metadata reads by `importlib.metadata`
    and Hypothesis's `.hypothesis/` state were excluded as tool state. Four
    items show a runtime signal above their tier, all outside `tests/` (wrong, as
    the round-2 review found: this audit excluded `openspec_graph/` and missed
    two `inspect` reads; see Milestone 7):
    `test_gate_scripts.py::test_fallback_scan_returns_nothing_outside_a_git_repo`
    (`integration`; `git ls-files` inside `tools/check_secrets.py`);
    `test_graft_witness.py::test_current_sha_returns_none_outside_a_git_repo`
    and `::test_profile_witnesses_field_reads_the_planlint_witnesses_directory`
    (`unit`; `git rev-parse HEAD` inside `detect._current_sha`); and
    `test_properties.py::test_parse_makefile_is_deterministic_with_sorted_unique_targets`
    (`unit`; Hypothesis reading loaded `tools/` modules' source for its
    constants). The first comparison found two more,
    `test_wheel_metadata.py::test_main_exits_0_on_a_good_wheel` and
    `::test_main_exits_1_on_a_bad_wheel`, reading `pyproject.toml` through
    `tools/check_wheel_metadata.py`. That miss was under `tests/` and was
    fixed by the `tools/` script rule before any mark was applied. Forty
    items sit above their runtime cost, which R-TSS-6 allows: 38 `e2e` tests
    with no runtime process (skipped `bash` cases and monkeypatched spawns)
    and 2 `integration` tests with no runtime read.
  - *Gate.* `make test`: exit 0; `openspec_graph/` 99.3% (2276/2292) lines and
    97.6% (744/762) branches, `tools/` 96.4% (946/981) and 93.9% (323/344).
    `make lint`, `make typecheck`, `make docs-check` and `make thresholds`:
    exit 0. `tests/AGENTS.md` is 59 lines against `MAX_NESTED_LINES`;
    `python -m pytest tests/test_agent_artifacts.py -q -k "nested_agents or
    agent_index_links"`: 43 passed. `planlint --target . validate --fail-on
    ERROR`: exit 0 before and after the package corrections. Milestone 4 is
    committed on its own, so a container restart cannot lose it; the second
    stage's commit is Milestone 5's.

## Milestone 5 — Route the duplicated shapes through `tests/support.py`, guards seen red first  [DONE]

- `tests/test_suite_shape.py`, written first and run red (R-TSS-8,
  R-TSS-12, DEC-TSS-009): planned tests, named here so AC-TSS-10 and 11
  can be re-pointed — `test_no_test_module_spawns_the_cli_outside_support`
  (AST: a `subprocess.run` call whose first argument is a list holding the
  constants `-m`, `openspec_graph.cli` and `--target`, in any module other
  than `tests/support.py`, named); `test_no_test_module_writes_a_spec_path_by_hand`
  (AST: a `.write_text` call whose receiver, resolved through local
  assignments in the same function, is a path chain holding the constants
  `openspec`, `changes`, `specs` and `spec.md`, or `specs` and `spec.md`
  under a root with no `openspec` segment, in any module other than
  `tests/support.py`, named; `mkfifo`, `mkdir` and bare comparisons are not
  writes); `test_a_planted_inline_spawn_or_hand_written_spec_is_named` (the
  helpers over planted texts: the `run_cli` shape named; a `--version`
  spawn without `--target` not named; a harness `write_text` named; a
  SpecKit `write_text` named; a FIFO at a spec path not named; an
  `assert ... .exists()` on a spec path not named). Record the red: the
  spawn guard naming `tests/test_decomposition.py`; the writer guard naming
  `tests/test_e2e_corpus.py` (two sites), `tests/test_detect_thresholds.py`,
  `tests/test_decomposition.py` and `tests/test_detect_speckit.py`, and
  whatever else it finds — route or exempt each with its reason here.
- `tests/test_decomposition.py`: `_run_cli(root, *args)` becomes
  `run_cli(root, *args).stdout` from `tests.support` (keeping the UTF-8
  comment's fact, which `run_cli` carries); the fixture writer at 102–105
  becomes `write_spec(root, change, cap, (FX / fname).read_text(...))`;
  `_EXPECTED_HASHES` must not move — run `python -m pytest
  tests/test_decomposition.py -q` and record green, which is the proof of
  DEC-TSS-009's claim about the coverage variable.
- `tests/test_e2e_corpus.py`: `_harness_spec(repo, body, change="c1")`
  becomes a one-line wrapper over `write_spec(repo, change, "cap", body)` or
  is inlined at each call; the SpecKit write at 338 becomes
  `write_speckit_spec`, which this module imports for the first time.
  `tests/test_detect_thresholds.py:257` → `write_spec`;
  `tests/test_detect_speckit.py:105` → `write_speckit_spec`, which that
  module already imports at line 21. The bare `tmp_path / "spec.md"`
  writes, the FIFO, the path assertions and the `Finding` paths stay, named
  here as having nothing to route; the `-c` script spawns
  (`test_findings_envelope.py:283`, `test_detect_thresholds.py:338`,
  `test_report.py:641`), the `tools/` script spawns
  (`test_skill_contract.py:482`, `test_e2e_corpus.py:201`,
  `test_enterprise.py`), `make` (`test_e2e_corpus.py:213`), `git`
  (`test_gate_scripts.py:109–111`, `test_graft_witness.py`,
  `test_agent_artifacts.py:714`), bash (`test_claude_hooks.py`,
  `test_action_contract.py`), `python -m build` (`test_wheel_metadata.py`)
  and `python -m pytest`/`mypy`/`ruff` (`test_coverage_checkers.py`,
  `test_ci_workflow.py`, `test_enterprise.py`) stay too, and
  `test_skill_contract.py:657`'s `--version` without `--target` stays
  (R-TSS-8). Of the 15 helper-less modules, `test_decomposition` and
  `test_detect_thresholds` now import from `tests/support.py`; the other
  thirteen have nothing to route.
- `tests/test_agent_artifacts.py` / `tests/test_release_surface.py`:
  replace `_workflow_jobs` with `tests.support.workflow_job_blocks` (the
  missing-`jobs:` assertion kept at the call site) and `_uncommented` with a
  join over `tests.workflow_support._code_lines` — the comment stripper it
  duplicates; `_uncommented_permission_blocks`, which an earlier draft named,
  lists uncommented permission blocks and is a different function — then
  confirm `_workflow_jobs` is gone and `grep -rn
  "def _workflow_jobs\|def _ci_job_blocks" tests/` finds only the alias in
  `tests/test_ci_workflow.py`.
- Re-run `grep -ln "subprocess.run" tests/test_*.py`, `grep -ln
  '"openspec_graph.cli"' tests/test_*.py`, `grep -rln write_speckit_spec
  tests/test_*.py` and `grep -L "from tests.support\|from tests import
  support\|import tests.support" tests/test_*.py`; record the after lists
  beside the header's.
- `CHANGELOG.md`: extend the entry with the routing. Commit the second
  stage (Milestones 4–5), recording the baseline hash and count — equal to
  Milestone 0's with `tests/test_suite_shape.py` excluded — and record PR
  #42's CI run on it.
- **Gate:** `make test`, then `make lint`
  **Recorded (Milestone 5, 2026-10-07, on `3044694` + the Milestone 5 tree):**
  - *Red first.* Both guards read each helper's shape from its own body in
    `tests/support.py`: `run_cli`'s `subprocess.run` argv literals (`-m`,
    `openspec_graph.cli`, `--target`) and the path chains of `write_spec`
    (`openspec/changes/<change>/specs/<capability>/spec.md`) and
    `write_speckit_spec` (`specs/<feature>/spec.md`), so no shape is
    restated in the guard. Before routing, `python -m pytest
    tests/test_suite_shape.py -q -o addopts=""`: 2 failed. The spawn guard
    named `test_decomposition.py:110`. The writer guard named
    `test_decomposition.py:106`, `test_detect_speckit.py:107`,
    `test_detect_thresholds.py:278`, `test_e2e_corpus.py:44` and `:340`, and
    one site this list did not foresee: `test_skill_contract.py:345`, which
    rewrote a fixture-written spec in place by hand. It is routed through
    `write_spec` like the rest; nothing was exempted. The seven planted
    routing cases passed from their first run, including a main-spec path
    (`openspec/specs/<cap>/spec.md`) that no routed writer owns and that
    must stay unnamed.
  - *Routed.* `test_decomposition.py`'s `_run_cli` spawns through `run_cli`
    and keeps its JSON normalisation; its fixture writer is `write_spec`;
    `python -m pytest tests/test_decomposition.py -q`: 9 passed, the golden
    hashes unmoved, which is DEC-TSS-009's claim about the coverage
    variable shown. `test_e2e_corpus.py`'s `_harness_spec` is a one-line
    wrapper over `write_spec` and its SpecKit write is `write_speckit_spec`;
    `test_detect_thresholds.py`, `test_detect_speckit.py` and
    `test_skill_contract.py` write through the helpers. The five routed
    modules: 168 passed. `test_release_surface.py` reads the release jobs
    through `workflow_job_blocks`, with the missing-`jobs:` assertion at
    the call site, and strips comments through `_code_lines`; `grep -rn
    "def _workflow_jobs\|def _ci_job_blocks" tests/` finds nothing, the
    alias in `tests/test_ci_workflow.py` being an assignment
    (`_ci_job_blocks = workflow_job_blocks`).
  - *After-greps,* beside the header's at `f7118a0`. `subprocess.run`: 17
    modules. `test_decomposition` left by the routing; `test_action_contract`
    left when its simulator moved to `tests/action_support.py`;
    `test_ci_hardening` and the spawning halves of `test_skill_contract`
    and `test_agent_artifacts` moved by the splits to `test_ci_workflow`,
    `test_coverage_checkers`, `test_skill_distribution` and
    `test_release_surface`; `test_suite_shape` holds the nested collection
    and the planted texts. `"openspec_graph.cli"`: `test_skill_distribution.py`
    (the `--version` spawn without `--target`, moved from
    `test_skill_contract.py` in Milestone 3) and `test_suite_shape.py` (planted
    texts). `write_speckit_spec`: 11 modules, the nine plus
    `test_e2e_corpus.py` and `test_suite_shape.py`. Helper-less: 14 modules,
    `test_decomposition` and `test_detect_thresholds` now importing from
    `tests/support.py`, and `test_agent_artifacts` helper-less since its
    release half moved out in Milestone 3; the others have nothing to route.
  - *Gate.* `make test`: exit 0, wall 174 s; `openspec_graph/` 99.3% (2276/2292)
    lines and 97.6% (744/762) branches, `tools/` 96.4% (946/981) and 93.9%
    (323/344). `make lint`: exit 0. The criterion's tally with the three
    routing guards added: 575 `unit`, 294 `integration`, 198 `e2e` of 1067.
    Baseline: 1057 names, sha256 prefix `2f62db0aee56ef40`, 1602 collected
    with `tests/test_suite_shape.py` ignored — equal to Milestone 0's.
    `make pre-pr`, the whole ladder at the second stage's commit: exit 0,
    wall 178 s.

## Milestone 6 — In-process loops, one subprocess each, the durations pair  [DONE]

- `tests/test_suite_shape.py`, written first and run red (R-TSS-9,
  R-TSS-12, DEC-TSS-010): `test_the_converted_loops_keep_exactly_one_subprocess`
  (AST over the four named bodies: exactly one `Call` whose function is
  `run_cli`, and at least one reference to `main` — `cli.main` or an
  imported `main`; a planted body with two `run_cli` calls and one with
  none are each named). Record the red: nine, four, eight and four
  `run_cli` calls at `f7118a0`.
- Take the before figure on the tree as the second stage's commit leaves
  it, in this container: the Appendix A durations command and
  `python -m pytest tests/test_report.py tests/test_sarif.py
  tests/test_e2e_corpus.py -k "test_projections_are_byte_stable_across_runs
  or test_an_unprojectable_file_exits_two_with_an_empty_stdout or
  test_sarif_returns_the_same_exit_code_as_the_text_run or
  test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict"
  --durations=0 -p no:cacheprovider -q -o addopts=""`; record the total,
  the twelve, and each named test's call duration with the commit
  (R-TSS-11). At `f7118a0` the four cost about 13.6 s together in the
  drafter's run; the seven subprocesses the conversion keeps are expected
  to cost about 2.5 s.
- `tests/test_report.py` `test_projections_are_byte_stable_across_runs`:
  build the envelope through `cli.main(["--target", str(FIXTURES /
  "failing"), "validate", "--format", "json"])` and `capsys.readouterr().out`;
  for each of the four formats run `report` twice through `cli.main`,
  reading stdout between, and assert the two equal; keep one
  `run_cli(tmp_path, "report", "--findings", ..., "--format", "sarif")`
  and assert its stdout equals the in-process first run for `sarif` — the
  entry-point check tied on the same property. Add `capsys` to the
  signature.
- `tests/test_report.py` `test_an_unprojectable_file_exits_two_with_an_empty_stdout`:
  for each format, `code = cli.main([... "report", "--findings",
  str(saved), "--format", fmt])`, `out, err = capsys.readouterr()`, assert
  `code == 2`, `out.strip() == ""` and a non-empty diagnostic (`err`, or if
  the handler binding makes `err` order-dependent, `captured_logger` on the
  package logger — DEC-TSS-010); keep one `run_cli` for the first format
  per parametrised case and assert `returncode == 2`, empty stdout,
  non-empty stderr, equal to the in-process verdict.
- `tests/test_sarif.py` `test_sarif_returns_the_same_exit_code_as_the_text_run`:
  for each repository and each of the three forms, the exit code through
  `cli.main` (reading and discarding `capsys` between runs), the three
  equal; the two outcome assertions (`failing` is 1, `clean` is 0)
  in-process; keep one `run_cli(failing, "validate", "--fail-on", "ERROR",
  "--format", "sarif")` and assert its `returncode` equals the in-process
  SARIF code for `failing`.
- `tests/test_e2e_corpus.py` `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict`:
  the three thresholds through `cli.main`, asserting 0, 0, 1; the findings
  from an in-process `validate --fail-on INFO --json` parsed from
  `capsys.readouterr().out` (a sibling `_findings_in_process(capsys,
  repo, *args)` if a second caller appears; `_findings` itself unchanged),
  `G010` present and `G004` absent; keep one `run_cli(tmp_path,
  "validate", "--fail-on", "INFO")` and assert its `returncode` equals the
  in-process code, 1.
- Confirm C-TSS-5 by diff: `git diff <the second stage's commit>..HEAD --
  tests/test_cli_surface.py tests/test_wheel_metadata.py
  tests/test_action_contract.py tests/test_coverage_checkers.py
  tests/test_gate_scripts.py tests/test_skill_contract.py
  tests/test_findings_envelope.py tests/test_detect_thresholds.py` prints
  nothing, and `test_module_is_importable_without_the_rest_of_the_package`
  in `tests/test_report.py` is outside the hunk.
- Take the after figure the same way, back to back with the before, and
  record both: each of the four per-test figures lower than its before;
  none of the four in the twelve; the two totals side by side with the
  header's three-reading spread stated beside them and no claim made on
  the difference beyond what the spread allows; the plan's 200 s row,
  reported as met before and after. Run `make test` and record the four
  scoped checker lines — the in-process loops raise the package's measured
  lines, never lower them — with the floors unchanged.
- `CHANGELOG.md`: extend the entry with the four tests, the one-subprocess
  shape, the four per-test figures before and after and the totals with
  their commits.
- **Gate:** `make test`
  **Recorded (Milestone 6, 2026-10-07, on `2daeca5` + the Milestone 6 tree):**
  - *Red first.* `test_the_converted_loops_keep_exactly_one_subprocess`, before
    any conversion, named all four bodies. `test_projections_are_byte_stable_across_runs`
    had 3 `run_cli` calls, one inside a loop, and no `main`.
    `test_an_unprojectable_file_exits_two_with_an_empty_stdout` had 1 call,
    inside its loop, and no `main`. `test_sarif_returns_the_same_exit_code_as_the_text_run`
    had 5 calls, three inside a loop, and no `main`.
    `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict` had
    3 calls and no `main`. The guard also names a `run_cli` inside a loop,
    because one call in a loop is still one process per iteration.
    `test_a_planted_loop_with_the_wrong_subprocess_count_is_named` names two
    calls, none, one inside a loop and no `main`, and stays quiet on the
    converted shape.
  - *Converted.* Each loop runs through `cli.main` with `capsys`, and one
    `run_cli` outside the loop is held to the in-process verdict on the
    same property. That is the SARIF bytes for the projections, the
    first format's exit code, empty stdout and non-empty stderr for the
    unprojectable file, the failing repository's SARIF exit code for the
    parity test, and the INFO exit code for G010. Every earlier assertion
    is still made. `tests/test_report.py`'s two copies of the format list
    became one `REPORT_FORMATS` constant. The conversion took
    `tests/test_report.py` to 720 lines, and `test_no_test_module_exceeds_the_line_bound`
    named it. `test_report_has_no_intra_package_imports` therefore moved to
    `tests/test_decomposition.py`, beside the `test_new_modules_stdlib_only`
    its docstring explains itself against (692 and 394 lines after). Its
    citations are by name.
  - *C-TSS-5.* `git diff 2daeca5 -- tests/test_cli_surface.py
    tests/test_wheel_metadata.py tests/test_action_contract.py
    tests/test_coverage_checkers.py tests/test_gate_scripts.py
    tests/test_skill_contract.py tests/test_findings_envelope.py
    tests/test_detect_thresholds.py` prints nothing.
    `test_module_is_importable_without_the_rest_of_the_package` is outside
    every hunk of `tests/test_report.py`.
  - *Durations (R-TSS-11),* in this container, back to back: before on
    `2daeca5` at 02:38Z and after on the converted tree at 02:45Z. The
    Appendix A command gave `1631 passed in 161.17s` before (load 0.95) and
    `1637 passed in 148.80s` after (load 0.96); six more items, the new
    guards. The header's three readings of an unchanged tree spread from
    149.98 s to 157.68 s, so the totals are recorded side by side and no
    claim is made on their difference. The plan's 200 s row is met before
    and after. Before, the slowest twelve held three of the four:
    `test_projections_are_byte_stable_across_runs` 3.60 s,
    `test_sarif_returns_the_same_exit_code_as_the_text_run` 2.96 s, and
    three `test_an_unprojectable_file_exits_two_with_an_empty_stdout` cases
    at 1.62–1.75 s. After, the twelve hold none of them; its tail is 1.59 s.
    The four-test command, per test, before → after:
    `test_projections_are_byte_stable_across_runs` 3.55 → 0.55 s;
    `test_sarif_returns_the_same_exit_code_as_the_text_run` 3.18 → 0.55 s;
    `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict`
    1.53 → 0.56 s; `test_an_unprojectable_file_exits_two_with_an_empty_stdout`
    1.45–1.52 → 0.50–0.59 s per case. The command's total went from 14.80 s
    to 4.08 s.
  - *Gate.* `make test`: exit 0, wall 167 s; `openspec_graph/` 99.3%
    (2276/2292) lines and 97.6% (744/762) branches, unchanged and not lowered;
    `tools/` 96.4% (946/981) and 93.9% (323/344); floors unchanged.
    Baseline: 1057 names, sha256 prefix `2f62db0aee56ef40`, unchanged.

## Milestone 7 — Confirm, re-point, and record for the plan  [DONE]

- Re-point the stage-only verification lines in
  `specs/test-suite-shape/spec.md` to the tests Milestones 1, 4, 5 and 6
  named, now that they exist, keeping each stage: AC-TSS-1 →
  `test_the_tests_directory_stays_flat` and
  `test_no_test_module_exceeds_the_line_bound`; AC-TSS-6 →
  `test_pytest_registers_exactly_the_three_tier_markers_strictly` and
  `test_an_unregistered_marker_fails_collection_under_strict_markers`;
  AC-TSS-7 → `test_every_test_carries_exactly_one_tier_marker` and
  `test_every_tier_marker_matches_its_mechanical_criterion`; AC-TSS-8 →
  `test_a_mismarked_or_unmarked_planted_module_is_named`; AC-TSS-10 adds
  `test_no_test_module_spawns_the_cli_outside_support` and
  `test_no_test_module_writes_a_spec_path_by_hand`; AC-TSS-11 →
  `test_a_planted_inline_spawn_or_hand_written_spec_is_named`; AC-TSS-13 →
  `test_the_converted_loops_keep_exactly_one_subprocess`. Run `python -m
  pytest tests/test_spec_test_citations.py -q` and record that every
  selector in every spec resolves.
- Confirm this package validates clean under the repository's own rules
  (`planlint --target . validate --fail-on ERROR --change shape-the-test-suite`),
  then `--change measure-coverage-once`, `--change harden-ci-workflows`,
  `--change select-zero-cost-guards`, `--change pin-actions-by-sha` and
  `--change prepare-release-0-3-0` (unedited, must still be clean), then
  the whole tree; record each exit code.
- Confirm no change-package directory other than this one is in the diff
  (`git diff --stat $(git merge-base origin/main HEAD)..HEAD -- openspec/changes | grep -v
  shape-the-test-suite` prints nothing), that `openspec_graph/`,
  `tests/baseline_rules.json`, `Makefile`, `.pre-commit-config.yaml` and
  `[project] dependencies` are absent from it, and that the only hunks
  under `.github/` are the comment lines (C-TSS-1, C-TSS-2, C-TSS-3).
- Re-take the header's measurements on the finished tree and record them
  beside the before figures: `wc -l tests/test_*.py | sort -n | tail -8`;
  the baseline hash and collected count with `tests/test_suite_shape.py`
  excluded (equal to Milestone 0's) and, separately, the full collected
  count with it included; the marker tally; the three routing greps; the
  pointer grep; `wc -l tests/AGENTS.md`.
- Tick each criterion only against its recorded evidence; AC-TSS-15 only
  once the Milestone 6 pair is recorded.
- Record for the plan's M2 row and §7 table, when they are next updated:
  the four loops' per-test figures before and after and the totals with
  their spread, as the Milestone 6 pair says, not as the plan's 235 s row
  says; every test module at or under the bound with the guard holding it;
  three tiers with the fast tier's count and time; the four loops at one
  subprocess each; the eight superseded records; the plan's 200 s row
  already met at `f7118a0` before this package and still met after it.
  Commit the third stage (Milestones 6–7), recording the baseline hash and
  count, and record PR #42's CI run on it.
- **Gate:** `make pre-pr`
  **Recorded (Milestone 7 and the round-2 review, 2026-10-07, on `af5b0b5` + the corrections):**
  - *Round-2 review.* The spec-adversary's second pass reviewed `3044694`
    (gate exit 0, every AC selector collecting) and found one high, six
    medium and five low findings. All were folded in before the third stage.
    - *Found, then fixed.* A `unit` test whose own code read the tree:
      `test_parse_spec_dispatch_is_not_dict_based` calls
      `inspect.getsource(parse.parse_spec)`, which opens
      `openspec_graph/parse.py`. `test_property_settings_are_derandomized_and_nothing_is_xfailed`
      reads its own source the same way. The Milestone 4 audit missed the
      first because it excluded every open under `openspec_graph/`, so its
      "all outside `tests/`" was wrong. The criterion gained `SOURCE_READERS`
      (`inspect`'s source readers, `linecache`, `importlib.resources`).
      Imports now resolve to dotted names, so `import os.path` then
      `os.system`, and an unaliased `import tests.support`, are seen.
      `multiprocessing` and `concurrent.futures` joined the process starts.
      Labelled input is judged by a path's final segments after `.parent` and
      `..`, so a word in a method argument no longer exempts a read, and
      climbing out of `fixtures/` counts. The one-tier guard names a test class
      and a tier inside `pytest.param` marks. Of 1069 test functions exactly
      the two named tests changed tier, both to `integration`; their modules,
      `test_parse_speckit.py` and `test_properties.py`, now mark per
      function. The routing shapes and offenders are unchanged.
    - *Red against the old engine.* The ten new planted cases ran against
      the `af5b0b5` engine in a scratch copy. Nine were red: source through
      `inspect`, a labelled word as a method argument, climbing out by
      `.parent`, climbing out by `..`, an unaliased import, a dotted import,
      `multiprocessing`, a test class, and a tier in `pytest.param` marks.
      The `tools/` script case passed there because that rule already
      existed; it is the regression case L4 asked for.
    - *Audit re-run* without the `openspec_graph/` exclusion, excluding only
      `tests/fixtures`, `tests/corpus`, `.git`, `.pytest_cache`,
      `.hypothesis`, bytecode and `.egg-info`: `1647 passed in 154.23s`, 707
      items with any event. It now records `openspec_graph/parse.py` for the
      `inspect` test. Four items sit above their AST tier, all outside code
      under `tests/`. Three are process starts by the code under test: the
      `check_secrets` `git ls-files` and two `_current_sha` `git rev-parse`.
      The fourth, `test_parse_makefile_is_deterministic_with_sorted_unique_targets`,
      is Hypothesis harvesting constants from loaded `tools/` modules. The
      derandomization test's own-source read is invisible to any audit once
      linecache holds the file; DEC-TSS-017 now says an audit samples and
      never replaces the criterion. 43 `e2e` items had no runtime process,
      which errs upward.
    - *Wording.* The `integration` and `e2e` marker descriptions,
      `tests/AGENTS.md`'s tier bullet and the CHANGELOG now say "its own code
      under `tests/`". C-TSS-5, R-TSS-10, DEC-TSS-011 and AC-TSS-14 allow
      R-TSS-3's nested module path. R-TSS-12 and AC-TSS-7 state the red as it
      was obtained. R-TSS-4 and R-TSS-8 name sites by module and function
      instead of line numbers. DEC-TSS-005 and the proposal drop the
      superseded simulation tallies, and the `test_deprecated_alias_*` count
      reads four. The proposal's Non-Goal explains the `ActionRun` move. The
      stale "until it exists" clauses of AC-TSS-1, 6, 7, 8, 10, 11 and 13 are
      gone, each citing its tests. Milestone 7's diff base is
      `$(git merge-base origin/main HEAD)`. `test_action_contract.py` is 471
      lines once marked, not the 446 recorded before its marks.
  - *Re-pointed.* AC-TSS-1, 6, 7, 8, 10, 11 and 13 cite their tests.
    `python -m pytest tests/test_spec_test_citations.py -q`: 6 passed, every
    selector in every spec resolving.
  - *Validated.* `planlint --target . validate --fail-on ERROR --change X`,
    exit 0 for `shape-the-test-suite`, `measure-coverage-once`,
    `harden-ci-workflows`, `select-zero-cost-guards`, `pin-actions-by-sha`
    and `prepare-release-0-3-0`; the whole tree: exit 0, 51 specs, 0/0/0.
  - *Boundaries.* `git diff --name-only $(git merge-base origin/main HEAD)`
    names no other change package and none of `openspec_graph/`,
    `tests/baseline_rules.json`, `Makefile` or `.pre-commit-config.yaml`.
    No `dependencies` line moves, and the `.github/` hunks are the four
    comment lines. The pointer grep for the two removed module names found
    one live pointer Milestone 3 had missed, the `Dockerfile` comment on the
    base-tag guard. It now names `tests/test_workflow_python.py`, and R-TSS-4
    lists it. Every other hit is a "Moved from" docstring,
    `tests/support.py`'s history sentence, the plan, or a dated review or
    `docs/next-steps.md` closed-item entry.
  - *Finished-tree measurements.* `wc -l tests/test_*.py | sort -n | tail
    -8`: the largest are `test_report.py` 692, `test_suite_shape.py` 689,
    `test_graft_rules.py` 677 and `test_graft_detection.py` 658; total 20584.
    Baseline: 1057 names, sha256 prefix `2f62db0aee56ef40`, and 1602
    collected with `tests/test_suite_shape.py` ignored — equal to Milestone
    0's; 1647 collected in full. Tally: 573 `unit`, 298 `integration`, 198
    `e2e` of 1069 test functions; 22 modules carry one `pytestmark` tier and
    33 mark per function. Fast tier: `-m unit` collects `731/1647 (916
    deselected)` and `-m "not unit"` `916/1647 (731 deselected)`; `python -m
    pytest -m unit -q -p no:cacheprovider -o addopts=""` gives `731 passed,
    916 deselected in 13.06s`, wall 13.5 s. Routing guards: no offender.
    `tests/AGENTS.md`: 59 lines.
  - *For the plan's M2 row and §7 table.* The four loops: 3.55 → 0.55 s,
    1.45–1.52 → 0.50–0.59 s per case, 3.18 → 0.55 s and 1.53 → 0.56 s. The
    totals were 161.17 s before and 148.80 s after, beside the 149.98–157.68 s
    spread of three unchanged-tree readings, and are not claimed as a
    saving. Every test module is at or under 700 lines with the guard
    holding it. There are three tiers, with the fast tier at 731 items in
    about 13 s. The four loops keep one subprocess each. Eight records are
    superseded by name (DEC-TSS-016). The plan's 200 s row was already met
    at `f7118a0` and is still met.
  - *Gate.* `make pre-pr` on the finished tree: exit 0, wall 171 s;
    `openspec_graph/` 99.3% (2276/2292) lines and 97.6% (744/762) branches,
    `tools/` 96.4% (946/981) and 93.9% (323/344), the four floors unchanged
    in value. Every criterion is ticked against the evidence recorded above
    and in Milestones 0–6.
