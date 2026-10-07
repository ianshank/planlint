# Change: Shape the Test Suite — Split by Concern, Tier by Cost, Loop In-Process

## Why

The suite is the gate every other change in this repository is held to, and
it has grown faster than its shape. Five test modules are now over the
700-line bound the reflection plan set for W7.4, and the largest,
`tests/test_ci_hardening.py`, holds twelve sections from six change packages
— coverage checkers, graph tools, Makefile shape, workflow claims, the
composite action's wiring, Dependabot — under a name that describes the first
package that wrote into it rather than anything it now tests. Nothing in the
tree distinguishes a test that spawns a process from one that calls a parser
on an in-memory string, so there is no fast local loop: a contributor who
wants a verdict runs the whole suite under coverage, and the hook ladder's
"fast inner loop" is `make ci`, which runs the whole suite too. And four of
the slowest tests spend their time spawning the CLI in a loop where the
property under test is the output — bytes on stdout, an exit code — that an
in-process call through `openspec_graph.cli.main` would show in a fraction
of the time, with one real subprocess kept as the entry-point check.

The flat `tests/` topology is the one thing about the shape that is right,
and it is load-bearing: `tests/test_spec_test_citations.py` and
`tests/test_decomposition.py` both glob `tests/test_*.py` non-recursively,
so a `tests/<subdir>/` would silently orphan its tests from both gates — the
reason the 2321-line `test_graft.py` was split into flat siblings. Specs cite
tests by function name on their verification lines and the citation test
resolves them by AST across those flat modules, so a move between flat
modules is free and a rename is not. This package moves and never renames.

This is milestone M2's W7.4 (suite hygiene) and W7.6 (in-process loops) of
the October 2026 reflection plan (`docs/reflection-plan-2026-10.md` §4 W7,
items 4 and 6; §5's M2 row; §7's "Suite wall time, single process" row).
W7.1–W7.3 shipped in `measure-coverage-once`, merged to `main` in #41; W7.5
is deferred by the plan itself.

**Evidence:** measured at `f7118a0` (`main`, the squash of #41; the tree is
byte-identical at `bb4e4ad`, the commit that carries this draft),
2026-10-07; each command re-measures it.

- **Five modules over the bound, one at it.** `wc -l tests/test_*.py |
  sort -n | tail -8` reads `test_graft_rules.py` 684,
  `test_action_contract.py` 700, `test_skill_contract.py` 821,
  `test_agent_artifacts.py` 836, `test_gate_scripts.py` 849,
  `test_workflow_hardening.py` 1237, `test_ci_hardening.py` 1378, out of
  19722 lines in the 45 modules `ls tests/test_*.py | wc -l` counts. The
  plan measured four over the bound at `9c4b6e9` (859, 836, 821, 700);
  since then `measure-coverage-once` wrote into `test_ci_hardening.py` and
  `test_gate_scripts.py`, and `harden-ci-workflows` added
  `test_workflow_hardening.py` as a new module because DEC-HCW-008 found the
  existing one already too large — which is the drift this package ends.
- **The seams are already drawn.** `grep -c "def test_"
  tests/test_ci_hardening.py` reads 60; `grep -n "^# --- "
  tests/test_ci_hardening.py` finds twelve section comments, at lines 40,
  100, 231, 395, 452, 512, 530, 662, 766, 1133, 1195 and 1261, each naming
  the package or script it covers. Counting `def test_` between seams (an
  `awk` over the same two patterns) gives 4 (branch-coverage floor), 8
  (line-coverage floor), 7 (graph-diff), 4 (`render_mermaid.py`), 1 (the
  runnable-as-a-script contract), 1 (the rule baseline), 6 (claims about
  the CI configuration), 7 (the two-track e2e gates), 8
  (`measure-coverage-once`'s one run), 3 (the composite action is
  executed), 3 (Dependabot) and 6 (the threshold guard's own coverage). The
  other four over-bound modules carry the same seam comments: nine sections
  and 47 tests in `test_workflow_hardening.py` (the first, at line 70, is
  five hundred lines of read-never-assert helpers), eight and 52 in
  `test_gate_scripts.py` (seams at 30, 96, 222, 323, 428, 582, 731, 829),
  eight and 28 in `test_agent_artifacts.py`, nine and 38 in
  `test_skill_contract.py`; `grep -c "def test_"` over each.
- **No tiers exist.** `grep -rn "pytest.mark\." tests/ | cut -d: -f3 |
  sort | uniq -c` lists only `parametrize` and `skipif` forms — the bare
  `@pytest.mark.parametrize(` openers and their one-line variants, the
  capability-probe `skipif`s, one module-level `pytestmark =
  pytest.mark.skipif(` (`tests/test_spec_discovery_identity.py:28`, which
  is why a module tier there needs the list form) and the two `needs_bash`
  aliases of a `skipif`. `grep -n "markers\|strict" pyproject.toml` matches
  only `[tool.mypy]` (lines 296, 298, 303 and `strict = true` at 306);
  `[tool.pytest.ini_options]` at line 82 holds `testpaths = ["tests"]` and
  `addopts = "-q"` and nothing else. `grep -n "pytest\|-m " docs/hooks.md
  .claude/hooks/*` finds module-level `pytest tests/test_<x>.py` remedies
  (`docs/hooks.md` 131, 142, 147, 153, 166; the hook script's arms) and no
  tier anywhere; `docs/hooks.md`'s one-run paragraph calls `make ci` "the
  fast inner loop".
- **The CLI is spawned outside `tests/support.py` in two places, and a
  harness spec is written by hand in three.** `grep -ln "subprocess.run"
  tests/test_*.py` lists 16 modules (`test_action_contract`,
  `test_agent_artifacts`, `test_ci_hardening`, `test_claude_hooks`,
  `test_cli_surface`, `test_decomposition`, `test_detect_thresholds`,
  `test_e2e_corpus`, `test_enterprise`, `test_findings_envelope`,
  `test_gate_scripts`, `test_graft_witness`, `test_machinery`,
  `test_report`, `test_skill_contract`, `test_wheel_metadata`; in
  `test_cli_surface` and `test_machinery` the match is a comment or a
  docstring). Of those, an argv list that passes `-m openspec_graph.cli` to
  `subprocess.run` appears in `tests/test_decomposition.py:108–109` (its
  own `_run_cli`, with `--target`, the exact shape of `support.run_cli`)
  and `tests/test_skill_contract.py:657` (`--version` with no `--target`, a
  shape `run_cli` cannot express). `grep -n '"spec.md"' tests/test_*.py`
  finds the harness path `openspec/changes/<c>/specs/<cap>/spec.md` built
  and written by hand at `tests/test_e2e_corpus.py:39–43`
  (`_harness_spec`, a verbatim `write_spec` with the capability fixed to
  `cap`), `tests/test_detect_thresholds.py:257` and
  `tests/test_decomposition.py:102–105`, and the SpecKit layout
  `specs/<feature>/spec.md` written by hand at `tests/test_e2e_corpus.py:338`
  and `tests/test_detect_speckit.py:105` — the second in a module that
  imports `write_speckit_spec` at line 21 and calls it fifteen times, the
  first in one that does not import it at all; `grep -rln
  write_speckit_spec tests/test_*.py` lists nine modules, so the helper is
  the established shape and these two sites are the stragglers. The other
  literals are bare `tmp_path / "spec.md"` writes (`test_parse_speckit` ×3,
  `test_detect_thresholds` :291 and :397, `test_spec_read_errors` :169,
  :183, :195, `test_finding_line_hits` :154), a FIFO
  (`test_detect_thresholds:380`), path assertions and reads
  (`test_detect_speckit`, `test_graft_cli`, `test_graph:564`,
  `test_stage_citations:329`), `Finding` paths (`test_sarif`,
  `test_rules_speckit`) and `tmp_path / "openspec" / "spec.md"`
  (`test_findings_envelope:191`) — none the harness shape.
  `tests/support.py:261–262` records that `tests/test_agent_artifacts.py`
  "still carries its own near-copy" of `workflow_job_blocks` —
  `_workflow_jobs` at line 448 — "which is W7.4's business (DEC-HCW-009)".
  `grep -L "from tests.support\|from tests import support\|import
  tests.support" tests/test_*.py` lists 15 of the 45 modules importing
  nothing from `tests/support.py` (`test_action_contract`,
  `test_adopter_urls`, `test_agent_skill_docs`, `test_claude_hooks`,
  `test_decomposition`, `test_detect_thresholds`, `test_dialect_card`,
  `test_ledger`, `test_machinery`, `test_mermaid`, `test_parse_speckit`,
  `test_properties`, `test_rule_registry_docs`, `test_spec_test_citations`,
  `test_wheel_metadata`); all but `test_decomposition` and
  `test_detect_thresholds` have nothing to route.
- **The durations table, re-measured three times on one tree.** `python -m
  pytest tests/ -p no:cacheprovider -q --durations=12 -o addopts=""` on this
  four-core container reports **1602 passed in 149.98 s** in the drafter's
  run (load average 0.02 when the run ended), **155.74 s** in the adversarial
  reviewer's (load 0.25) and **157.68 s** in the coordinator's at `bb4e4ad`
  (load 1.38 at the end). The drafter's twelve slowest, call phase:
  `test_read_only_verbs_leave_tree_byte_identical` (`test_skill_contract`)
  6.71 s; `test_projections_are_byte_stable_across_runs` (`test_report`)
  3.54 s; `test_sarif_returns_the_same_exit_code_as_the_text_run`
  (`test_sarif`) 2.92 s; `test_suite_survives_an_ambient_coverage_file`
  (`test_ci_hardening`) 1.95 s; `test_the_real_wheel_passes_the_gate`
  (`test_wheel_metadata`) 1.94 s;
  `test_common_verbs_do_not_crash_under_ascii_stdout_encoding`
  (`test_cli_surface`) 1.82 s; then six `test_action_contract` tests between
  1.72 s and 1.54 s (`test_annotation_paths_resolve_from_the_repository_root`,
  `test_the_action_reports_each_fixtures_labelled_status[passing]`,
  `test_a_nested_target_is_scanned_at_its_own_root`,
  `test_a_failing_run_populates_the_whole_evidence_bundle`,
  `test_the_action_reports_each_fixtures_labelled_status[failing]`,
  `test_the_evidence_directory_is_outside_the_scanned_tree`). The
  coordinator's twelve at `bb4e4ad`: the read-only tree hash 7.41 s, the
  projections 3.54 s, the SARIF parity 3.21 s, the real wheel 2.08 s,
  `labelled_status[passing]` 1.99 s, the ASCII encoding 1.84 s, then six
  `test_action_contract` tests between 1.74 s and 1.62 s. Two of the four
  tests W7.6 names are in every reading; the other two —
  `test_an_unprojectable_file_exits_two_with_an_empty_stdout` (four
  parametrised cases at this commit, not the plan's three) and
  `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict` —
  fall below the twelfth entry today, where the plan read them at 2.4, 2.3
  and 2.6 s at `9c4b6e9`. The same command read 1498 passed in 235 s at
  `9c4b6e9` in the plan and 1578 passed in 212.5 s and 210.46 s at
  `5246931` in `measure-coverage-once`'s two sessions, so the plan's
  absolute figure — at or under 200 s single-process in this container — is
  already met at this head before a line of this package lands, by a suite
  that has grown by a hundred tests; and three readings of one unchanged
  tree spread over about eight seconds. That spread is the variance, and a
  total is therefore a figure this package records with its spread, not one
  it can be held to; what the loop conversion directly moves — the four
  named tests' own call durations, about 13.6 s of the 150 today, of which
  the seven kept subprocesses will cost about 2.5 s — is what the package
  holds itself to (DEC-TSS-012). The plan's 200 s row is reported here and
  in `tasks.md` as the plan's figure, met before and after.
- **What the moves must not disturb.** Each of the four W7.6 tests is read
  in its body: `test_projections_are_byte_stable_across_runs`
  (`tests/test_report.py:605`) runs `validate --format json` once and then
  `report` twice per format over four formats through `run_cli`, nine
  subprocesses; `test_an_unprojectable_file_exits_two_with_an_empty_stdout`
  (`:528`) runs `report` once per format per parametrised payload, four
  each; `test_sarif_returns_the_same_exit_code_as_the_text_run`
  (`tests/test_sarif.py:306`) runs three formats over two repositories and
  two confirming runs, eight; `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict`
  (`tests/test_e2e_corpus.py:257`) runs three thresholds and the module's
  `_findings` helper, four. `openspec_graph/cli.py:980`'s `main(argv)`
  reconfigures `sys.stdout`/`sys.stderr` and returns an `int`, and its own
  docstring says the project's tests call it in-process "always wrapped in
  `capsys`/`monkeypatch`", which `tests/test_cli_surface.py:240–281` do.
  The process-boundary tests the plan's rule protects are in the table
  above by name. `tests/test_ci_hardening.py:197` names its own module path
  inside the nested pytest of `test_suite_survives_an_ambient_coverage_file`;
  `tests/conftest.py:48` says `test_ci_hardening.py` defines its own `repo`
  fixture; `tests/support.py:259`, `tools/_common.py:157`,
  `tests/test_gate_scripts.py:11`, `tests/test_action_contract.py:14`,
  `.claude/hooks/nudge_rule_registry.sh:43` (`pytest
  tests/test_ci_hardening.py -k dependabot`), `tests/AGENTS.md:16–20` and
  `:32`, `docs/architecture/c4.md:81` and `:217–221`, `docs/hooks.md:64`,
  `docs/aqa.md:48` and `:108`, `pyproject.toml:156` and `:200`,
  `.github/dependabot.yml:21` and `:35`, `.github/workflows/ci.yml:10`,
  `release.yml:24`, `skills/AGENTS.md:13` and `:27`, `README.md:350` and
  `:354` and `.claude/agents/planlint-verifier.md:21` and `:24` name a test
  module by path (`grep -rn` over the five module names, `.git/`, the
  change packages and the plan excluded). Eight shipped records name the
  two modules this package deletes as the place a guard lives — R-ZCG-10
  and DEC-ZCG-010, R-HCW-15, R-HCW-16 and DEC-HCW-008, R-ASP-8 and
  R-ASP-11, DEC-REL-011 — and are superseded by name in DEC-TSS-016 rather
  than edited. `wc -l tests/AGENTS.md` reads 51 against `MAX_NESTED_LINES =
  60` (`tests/test_agent_artifacts.py:702`).
  `test_the_suite_runs_once_through_coverage_run`'s helper
  `_one_run_violations` (`tests/test_ci_hardening.py:843`) names every
  recipe line in the Makefile that invokes pytest other than
  `coverage-run`'s, so a second pytest recipe is a red test, not a free
  target. The tier criterion was simulated over five modules before it was
  written down: in `tests/test_cli_surface.py` the `repo_root` fixture
  (`:480–482`) reads the repository's `pyproject.toml` on behalf of
  `test_entry_points_wired_in_pyproject` (`:212–214`), and the `fixtures`
  fixture (`:471–477`) builds its paths from `Path(__file__)` under
  `fixtures/` for the four `test_deprecated_alias_*` tests — so a criterion
  that ignores fixture parameters classes the first as `unit` while it
  reads the tree, and one that resolves them but exempts only module
  constants classes the second as `integration` while it reads a labelled
  corpus; `tests/test_detect_corpus.py:307` spells the root as
  `Path(detect.__file__)`, an attribute, not a name. R-TSS-6 is written to
  those cases.

## What Changes

- `tests/test_ci_hardening.py` — removed; its twelve sections move, test
  names unchanged, to: `tests/test_ci_workflow.py` (the claims about the CI
  configuration; the two-track jobs, the `_ci_job_blocks` alias and the
  hooks-table guard; the per-leg upload guards and the reverse hooks-table
  guard; the two `ci.yml` tests of the composite action's wiring),
  `tests/test_ci_makefile.py` (`e2e-live`, `matcher-accuracy`, the one-run
  Makefile guards and their helpers, the per-file report target, the
  contract job's absence from any Make target), `tests/test_coverage_checkers.py`
  (the branch-floor and line-floor sections, with the nested-pytest tests
  and the ambient-coverage test, which re-points its nested path to its new
  module), `tests/test_graph_tools.py` (graph-diff and `render_mermaid.py`,
  with the module-local `repo` fixture), `tests/test_threshold_guard.py`
  (the threshold guard's own coverage), `tests/test_gate_scripts.py`
  (`test_gate_script_is_runnable_as_a_script`, which that module's
  docstring already points at), `tests/test_rule_registry_docs.py`
  (`test_rule_set_matches_baseline`) and `tests/test_workflow_pins.py` (the
  Dependabot section).
- `tests/test_workflow_hardening.py` — removed; `tests/workflow_support.py`
  (new, not collected, the pattern of `tests/graft_support.py`) takes the
  read-never-assert helpers more than one collected module uses —
  `_uncommented_permission_blocks` among them, because
  `tests/test_release_surface.py` reads it too; `tests/test_workflow_pins.py`
  takes the action-ref, SHA-pin and major-floor section, the
  Dockerfile-and-its-update-bot section and the Dependabot section above;
  `tests/test_workflow_posture.py` takes permissions, timeouts,
  concurrency, the thresholds-guard-is-quiet check and the attestations
  input; `tests/test_workflow_python.py` takes the one-Python-default
  section and the experimental-leg, classifiers and docs section (which
  holds `test_hooks_test_row_names_the_matrix_bounds`).
- `tests/test_gate_scripts.py` — gives its three coverage sections (scoped
  floors, one run read scoped, the per-file report) to
  `tests/test_coverage_checkers.py` and its `check_no_hardcoded_thresholds.py`
  section to `tests/test_threshold_guard.py`; keeps `check_docs.py`,
  `check_secrets.py`, `render_plugin_manifests.py` and `_common.read_json`;
  gains the runnable-as-a-script contract.
- `tests/test_agent_artifacts.py` — gives its release-workflow,
  generated-artifacts and packaging-surface sections to
  `tests/test_release_surface.py` (new), its `_workflow_jobs` near-copy and
  `_uncommented` moving with them unchanged; the routing stage replaces them
  with `tests/support.workflow_job_blocks` and `tests/workflow_support.py`'s
  `_code_lines` (DEC-HCW-009's deferral, closed); keeps evals, `context7.json`,
  `llms.txt`, the nested `AGENTS.md` contract and the cited-command check.
- `tests/test_skill_contract.py` — gives its generated-catalog,
  manifest-agreement, shipped-CI-asset, packaging-and-gate-coverage and
  distribution-rename sections to `tests/test_skill_distribution.py` (new);
  keeps the read-only claim (and `READ_ONLY_INVOCATIONS`, which
  `tests/test_report.py` imports), the exit-code contract, the exit-2
  remainder and the boundaries.
- `tests/test_action_contract.py` — at the bound when this package was
  drafted, so its Action runner simulator (`ActionRun`, the step reader and
  the expression resolver) moves to the uncollected `tests/action_support.py`
  to make room for its tier marks; `EXPECTED_INPUTS` stays, because R-WCA-15
  and R-GA-33 name it there.
- `tests/shape_support.py` — new, uncollected: the R-TSS-6 criterion, by
  AST, that the tier guards assert against (DEC-TSS-007).
- `tests/test_report.py` → `tests/test_decomposition.py` —
  `test_report_has_no_intra_package_imports` moves beside the
  `test_new_modules_stdlib_only` its docstring explains itself against,
  when the in-process loops take `test_report.py` past the bound.
- `tests/test_graft_rules.py` → `tests/test_rule_registry_docs.py` —
  `test_rule_registry_baseline_is_unchanged`, the one test there that reads
  the tree, moves beside the other baseline guard, so the module is one
  tier and stays inside the bound once marked.
- `tests/test_suite_shape.py` — new; the guards of this package: the tree
  stays flat, no module exceeds `MAX_TEST_MODULE_LINES`, the three tier
  markers are registered and strict, every test carries exactly one tier,
  each tier agrees with its mechanical criterion (fixture parameters
  resolved like called helpers, the `fixtures`/`corpus` exemption applied
  to every `__file__`-rooted path, the tree-readers of `tests/support.py`
  followed into their bodies), and no tier is written through an alias —
  each shown red on a planted counter-example.
- `tests/test_suite_routing.py` — new, split from `test_suite_shape.py` by
  R-TSS-1: no test module spawns the CLI in `run_cli`'s shape or writes a
  harness spec by hand, and the four converted loops keep exactly one
  subprocess — each shown red on a planted counter-example.
- `pyproject.toml` — `[tool.pytest.ini_options]` gains `markers` (`unit`,
  `integration`, `e2e`, each with its criterion in the description) and
  `--strict-markers` in `addopts`; the comments at lines 156 and 200 that
  name `tests/test_workflow_hardening.py` name `tests/test_workflow_pins.py`.
  No floor, no ruff family, no mypy setting changes.
- Every collected test module — a per-function `@pytest.mark.<tier>` where
  the module's tests are not all one tier, which the criterion simulated
  over `test_report`, `test_sarif` and `test_cli_surface` says is the
  expected shape wherever in-process and spawning tests share a module
  (the shipped tally is recorded in `tasks.md`); a module-level
  `pytestmark` entry where they are, in the
  list form where a `pytestmark` already exists; never an alias of a tier
  mark.
- `tests/test_decomposition.py` — its inline `_run_cli` becomes
  `support.run_cli(...).stdout` and its fixture writer becomes `write_spec`;
  the golden hashes do not move. `tests/test_e2e_corpus.py` — `_harness_spec`
  becomes `write_spec` with `cap`, the SpecKit write becomes
  `write_speckit_spec`; `tests/test_detect_thresholds.py:257` and
  `tests/test_detect_speckit.py:105` likewise.
- `tests/test_report.py`, `tests/test_sarif.py`, `tests/test_e2e_corpus.py`
  — the four named tests loop through `openspec_graph.cli.main` with
  `capsys` and keep exactly one `run_cli` each as the entry-point check,
  compared with the in-process result on the same property; the shared
  `_findings` helper is not changed for its other callers.
- `tests/AGENTS.md` — the diagram gains `workflow_support.py` under "shared,
  not collected" and the guard module under "split by subject"; a fourth
  "thing to know" states the one-tier rule and the criterion; the run
  sentence names `python -m pytest -m unit` as the fast tier; stays within
  `MAX_NESTED_LINES`. `docs/architecture/c4.md` §4's `tests/*` row and §4b's
  diagram and prose name the modules that now hold what they describe, and
  the flat-topology paragraph gains the tier sentence. `docs/hooks.md` —
  line 64 names the three workflow modules; a short paragraph after the
  optional pre-push hook describes the fast tier as a command, and why it
  is not a Make target; the CI table is untouched.
  `.claude/hooks/nudge_rule_registry.sh:43` — the Dependabot arm names
  `tests/test_workflow_pins.py`; the SKILL.md arm adds
  `tests/test_skill_distribution.py` beside `tests/test_skill_contract.py`.
  `tests/conftest.py:48`, `tools/_common.py:157`, `tests/support.py:259–262`,
  `tests/test_gate_scripts.py:11`, `tests/test_action_contract.py:14`,
  `.github/dependabot.yml:21` and `:35`, `.github/workflows/ci.yml:10`,
  `.github/workflows/release.yml:24`, `docs/aqa.md:48` and `:108`,
  `skills/AGENTS.md:13` and `:27`, `README.md:354`,
  `.claude/agents/planlint-verifier.md:21` and `:24`,
  `docs/distribution-plan.md`'s rows — each pointer names the module that
  now holds the guard it refers to. Dated records are not edited; the eight
  shipped spec records that name the deleted modules are superseded by
  name in DEC-TSS-016 and not edited.
- `CHANGELOG.md` — a `Changed` entry under `[Unreleased]` naming the split,
  the tiers and the strict markers, the routing, the loop conversion, the
  eight superseded records and the before/after figures.
- `openspec/changes/shape-the-test-suite/tasks.md` — records, dated with
  the commit and naming the command: line counts, the test-name set and the
  collected count (over the pre-existing modules, `tests/test_suite_shape.py`
  and `tests/test_suite_routing.py` excluded) at Milestone 0 and after each split and at each stage's commit,
  the red runs of every guard, the durations before (above) and after with
  their spread, the per-test figures of the four loops, the fast tier's
  collected count and wall time.

## Non-Goals

- **W7.5, `pytest-xdist`.** The plan defers the dev extra until the hosted
  runners are re-measured (§4 W7.5; the two tests that counted differently
  under four workers are to be understood first). No `-n`, no dev extra,
  no change to `[tool.coverage.run] parallel`.
- **W7.1–W7.3.** The floors, the one run and the per-file report shipped in
  `measure-coverage-once`, merged to `main` in #41; this package moves that
  package's guard tests with their sections under their names and edits
  none of its files.
- **Editing the shipped packages whose records name the deleted modules.**
  `select-zero-cost-guards` (R-ZCG-10, DEC-ZCG-010), `harden-ci-workflows`
  (R-HCW-15, R-HCW-16, DEC-HCW-008), `pin-actions-by-sha` (R-ASP-8,
  R-ASP-11) and `prepare-release-0-3-0` (DEC-REL-011) each name
  `tests/test_ci_hardening.py` or `tests/test_workflow_hardening.py` as the
  module a guard lives in. Each property survives in a named new module;
  the records are superseded by name in DEC-TSS-016, in DEC-MCO-006's form,
  and the packages are not edited because they are shipped.
- **Anything under `openspec_graph/`, any rule, any golden hash.** The
  `RULES` tuple, `README.md`'s rules table, `tests/baseline_rules.json`, the
  `validate`/`graph`/`rules` hashes and `[project] dependencies` are
  untouched; `test_rule_set_matches_baseline`, `test_output_byte_identical`
  and `test_runtime_dependencies_stay_empty` hold that.
- **A `tests/<subdir>/`.** The two gates glob non-recursively (#35); the
  guard this package adds makes the flat topology a red test rather than a
  paragraph.
- **A rename of any test function.** Specs cite tests by name; every move
  is between flat modules and `test_every_spec_test_citation_resolves_to_a_real_test`
  proves the set intact.
- **A Make target for the unit tier.** `test_the_suite_runs_once_through_coverage_run`
  holds that `coverage-run` is the only recipe that invokes pytest
  (R-MCO-2, R-MCO-6), a sibling's guard merged to `main` in #41; amending
  it for a convenience is the wrong trade, and the ladder's promise — a
  commit cannot bypass what CI checks — is about gates, which a partial
  suite is not. The fast tier is a documented command (DEC-TSS-008); a
  later package may give it a target once its measured wall time says it
  is worth one. `.pre-commit-config.yaml` is unchanged.
- **A wall-time target.** The plan's 200 s row is met at `f7118a0` before
  this package and is reported, not enforced: three readings of one tree
  spread over about eight seconds, so a MUST on the total would be met or
  missed by the container's weather. The package's MUSTs are on the four
  converted tests' own call durations and on their absence from the after
  table's twelve (R-TSS-11, DEC-TSS-012).
- **Converting a test whose process boundary is the property.** Encoding
  (`test_common_verbs_do_not_crash_under_ascii_stdout_encoding`,
  `test_arbitrary_non_ascii_spec_content_survives_graph_mermaid_under_ascii_encoding`,
  `test_matcher_accuracy_tool_runs_headless_and_exits_zero`), an ambient
  coverage file (`test_suite_survives_an_ambient_coverage_file`), the real
  wheel (`test_the_real_wheel_passes_the_gate`), the composite action
  (`test_action_contract.py`'s bash runs), a fresh interpreter
  (`test_module_is_importable_without_the_rest_of_the_package`, the
  one-warning test in `test_findings_envelope.py`, the hash-seed test in
  `test_detect_thresholds.py`), a script run as the Makefile runs it
  (`test_gate_script_is_runnable_as_a_script`) and what a real process
  leaves on disk (`test_read_only_verbs_leave_tree_byte_identical`, the
  slowest test in the table and deliberately not in W7.6's list) stay as
  they are (R-TSS-10).
- **A new ruff family, or mypy over `tests/`.** `select-zero-cost-guards`
  chose the rule set; tests under mypy is W6.5, a separate M2 item.
- **Any change to a workflow file, the composite action or a Makefile
  recipe.** Two comment lines in `.github/dependabot.yml`, one in `ci.yml`
  and one in `release.yml` that name a moved module are re-pointed; no
  step, job, recipe or target changes.
- **Splitting `tests/test_action_contract.py`.** It read 700 lines at the
  measurement commit, the bound, not over it. Its tests stay together; only
  its runner simulator moved, to the uncollected `tests/action_support.py`,
  to make room for the tier marks. R-TSS-2's rule that a helper moves with
  its only user governs splits between test modules; a helper moving into
  an uncollected support module beside its user, as `workflow_support.py`
  does for the workflow modules, is not such a split.
- **More than one pull request.** This branch's pull request (#42) carries
  the whole package; its three stages — the splits and pointers, the tiers
  and routing, the loops and records — are separate commits, each recording
  the test-name hash and the collected count, so the durations pair
  brackets exactly the loop conversion (DEC-TSS-014).

## Affected Capabilities

- `test-suite-shape`
