# Spec: Test Suite Shape

> **Change:** `shape-the-test-suite`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The suite has three shape problems and one measurement to be accountable
to. Five test modules are over the line bound the plan set, and the largest
holds twelve sections from six change packages under a name that describes
none of them; `harden-ci-workflows` opened a new module rather than add to
it, which is how the sixth over-bound module came to exist. No marker
distinguishes a test that starts a process from one that calls a parser on
a string, so there is no fast tier for a contributor to run and the hook
ladder's "fast inner loop" is the whole suite. Two modules spawn the CLI
through their own `subprocess.run` in the exact argv shape
`tests/support.run_cli` exists for, and three write the harness spec path
by hand that `write_spec` exists for, so a fix to the shared helper — the
UTF-8 encoding, the coverage-hook variable — does not reach them. And four
of the slowest tests loop over `run_cli` where the property under test is
the output, paying a process per iteration for a verdict `cli.main` returns
in-process.

The one right thing about the shape is load-bearing and must survive every
edit: `tests/` is flat because `test_spec_test_citations.py` and
`test_decomposition.py` glob `tests/test_*.py` non-recursively, specs cite
tests by function name, and the citation test resolves those names by AST
across the flat modules. So this package moves tests between flat modules
and never renames one, puts a guard on the flatness and the bound, tiers
every test by a mechanical criterion with a guard in both directions, routes
the duplicated shapes through `tests/support.py` with guards that keep them
there, converts the four loops with one subprocess kept each, and records
the durations command before and after on the same container.

**Evidence:** measured at `f7118a0` (`main`, the squash of #41; the tree is
byte-identical at `bb4e4ad`), 2026-10-07; every command is in the proposal.
`wc -l tests/test_*.py | sort -n | tail -8` reads five modules over 700
lines and `test_action_contract.py` at exactly 700; `grep -n "^# --- "
tests/test_ci_hardening.py` finds twelve seams; `grep -rn "pytest.mark\."
tests/` finds only `parametrize` and `skipif`, one of them a module-level
`pytestmark` (`tests/test_spec_discovery_identity.py:28`);
`[tool.pytest.ini_options]` holds `testpaths` and `addopts = "-q"`; an argv
list passing `-m openspec_graph.cli` to `subprocess.run` appears in
`tests/test_decomposition.py:108–109` (with `--target`) and
`tests/test_skill_contract.py:657` (`--version`, without); the harness spec
path is written by hand at `tests/test_e2e_corpus.py:39–43`,
`tests/test_detect_thresholds.py:257` and `tests/test_decomposition.py:102–105`
and the SpecKit path at `tests/test_e2e_corpus.py:338` and
`tests/test_detect_speckit.py:105`, in modules of which the second already
imports `write_speckit_spec` and the first does not; `grep -rln
write_speckit_spec tests/test_*.py` lists nine modules.
`tests/support.py:261–262` defers `test_agent_artifacts.py`'s
`_workflow_jobs` near-copy to W7.4. The Appendix A durations command reports
1602 passed in 149.98 s, 155.74 s and 157.68 s in three sessions on this
unchanged tree, with `test_projections_are_byte_stable_across_runs` at
3.54 s and `test_sarif_returns_the_same_exit_code_as_the_text_run` at
2.92–3.21 s in every top twelve and the other two named tests below it; the
plan's figure was 235 s at `9c4b6e9` and `measure-coverage-once`'s 212.5 s
and 210.46 s at `5246931`. `tests/test_ci_hardening.py:843`'s
`_one_run_violations` names every recipe line other than `coverage-run`'s
that invokes pytest. `openspec_graph/cli.py:980`'s `main(argv)` returns an
`int` and is already called in-process under `capsys` by
`tests/test_cli_surface.py`. In that module the `repo_root` fixture
(`:480–482`) reads the repository's `pyproject.toml` for
`test_entry_points_wired_in_pyproject` and the `fixtures` fixture
(`:471–477`) builds `Path(__file__)`-rooted paths under `fixtures/` for the
`test_deprecated_alias_*` tests; `tests/test_detect_corpus.py:307` spells a
root as `Path(detect.__file__)`. Eight shipped records name
`tests/test_ci_hardening.py` or `tests/test_workflow_hardening.py` as where
a guard lives: R-ZCG-10 and DEC-ZCG-010, R-HCW-15, R-HCW-16 and
DEC-HCW-008, R-ASP-8 and R-ASP-11, DEC-REL-011.

---

## Requirements

- R-TSS-1: `tests/` MUST stay flat: every collected test module is
  `tests/test_*.py` and no directory under `tests/` holds a `test_*.py`.
  Every collected test module MUST be at or under `MAX_TEST_MODULE_LINES`,
  a module-level constant of `tests/test_suite_shape.py` in the form of
  `MAX_NESTED_LINES`, counted as `wc -l` counts. Both properties MUST be
  read from the tree by a guard test in that module, never asserted in
  prose alone.
- R-TSS-2: Every module over the bound at the measurement commit MUST be
  split along its existing `# --- ` section seams into modules each named
  for the subject its sections share. No test function MAY be renamed, and
  no test function MAY be deleted: the sorted set of `def test_*` names
  read by AST over `tests/test_*.py` excluding `tests/test_suite_shape.py`
  — the one module this package creates with tests of its own — and the
  collected count over the same set (`--ignore=tests/test_suite_shape.py`)
  MUST be identical to Milestone 0's after every split and at every stage
  commit, both recorded in `tasks.md`. A helper MUST move with its only
  user; a helper two of the resulting collected modules need MUST move to
  `tests/support.py` when it is a general test helper or to a non-collected
  `<subject>_support.py` sibling when it is specific to one subject, never
  be copied and never be imported from one collected module into another.
  A fixture a module defines for itself (`test_ci_hardening.py`'s `repo`)
  MUST move with the tests that use it. Each resulting module's docstring
  MUST name what it holds and which package's criteria it verifies.
- R-TSS-3: The splits are these, each resulting module under the bound.
  `tests/test_ci_hardening.py` is removed and its sections go to
  `tests/test_ci_workflow.py` (the claims about the CI configuration; the
  two-track `ci.yml` jobs, the `_ci_job_blocks` alias and the hooks-table
  guard; the per-leg upload guards and the reverse hooks-table guard; the
  two `ci.yml` tests of the composite action's wiring),
  `tests/test_ci_makefile.py` (every test that reads the Makefile: the
  `e2e-live` and `matcher-accuracy` targets, the one-run guards with their
  readers and `_one_run_violations`, the per-file report target, the
  contract job's absence from any Make target),
  `tests/test_coverage_checkers.py` (the branch-floor and line-floor
  sections, the nested-pytest floor tests, the ambient-coverage test and
  the environment-stripping test, together with `tests/test_gate_scripts.py`'s
  scoped-floor, one-run and per-file sections, so the two checkers are
  tested in one place), `tests/test_graph_tools.py` (graph-diff and
  `render_mermaid.py` with their `repo` fixture),
  `tests/test_threshold_guard.py` (the threshold guard's own coverage,
  together with `tests/test_gate_scripts.py`'s `check_no_hardcoded_thresholds.py`
  section), `tests/test_gate_scripts.py` (the runnable-as-a-script
  contract), `tests/test_rule_registry_docs.py` (the rule baseline) and
  `tests/test_workflow_pins.py` (the Dependabot section).
  `tests/test_workflow_hardening.py` is removed and goes to
  `tests/workflow_support.py` (not collected; the readers more than one
  collected module uses, `_uncommented_permission_blocks` among them),
  `tests/test_workflow_pins.py` (action refs, SHA pins and major floors;
  the Dockerfile and its update bot; Dependabot),
  `tests/test_workflow_posture.py` (permissions, timeouts, concurrency, the
  thresholds guard's silence, the attestations input) and
  `tests/test_workflow_python.py` (the one Python default; the experimental
  leg, the classifiers and the docs). `tests/test_agent_artifacts.py` gives
  its release-workflow, generated-artifacts and packaging-surface sections
  to `tests/test_release_surface.py`. `tests/test_skill_contract.py` gives
  its generated-catalog, manifest-agreement, shipped-CI-asset,
  packaging-and-gate-coverage and distribution-rename sections to
  `tests/test_skill_distribution.py` and keeps `READ_ONLY_INVOCATIONS` where
  `tests/test_report.py` imports it. `tests/test_action_contract.py` is not
  split. `test_suite_survives_an_ambient_coverage_file` MUST name its new
  module in the path of the pytest it nests, and MUST still select
  `test_coverage_floor_passes_at_threshold`, which moves with it.
- R-TSS-4: Every live pointer to a moved section MUST name the module that
  now holds it: `tests/AGENTS.md` (diagram nodes and the sentence at line
  32), `docs/architecture/c4.md` (§4's `tests/*` row, §4b's diagram and
  prose), `docs/hooks.md` (the guard named at line 64; the module-level
  remedies stay true because the modules they name keep the tests they
  describe), `.claude/hooks/nudge_rule_registry.sh` (the Dependabot arm
  names `tests/test_workflow_pins.py`; the SKILL.md arm adds
  `tests/test_skill_distribution.py`), `tests/conftest.py`'s `repo`
  docstring, `tools/_common.py`'s docstring at line 157,
  `tests/support.py`'s `workflow_job_blocks` docstring (lines 259–262),
  `tests/test_gate_scripts.py`'s and `tests/test_action_contract.py`'s
  module docstrings, the `pyproject.toml` comments at lines 156 and 200,
  the `.github/dependabot.yml` comments at lines 21 and 35,
  `.github/workflows/ci.yml:10`, `.github/workflows/release.yml:24`,
  `docs/aqa.md`, `skills/AGENTS.md`, `README.md:354`,
  `.claude/agents/planlint-verifier.md` and `docs/distribution-plan.md`'s
  table rows — the set found by `grep -rn` over the five module names with
  `.git/`, `openspec/changes/` and the plan excluded. `tests/AGENTS.md`
  MUST stay within `MAX_NESTED_LINES` with its precedence clause, its
  balanced Mermaid block and resolving links. Dated records — `CHANGELOG.md`'s
  released sections, `docs/next-steps.md`, the peer reviews, the plan —
  MUST NOT be edited, and no file of any other change package MAY be
  edited: `measure-coverage-once`'s, `harden-ci-workflows`',
  `select-zero-cost-guards`', `pin-actions-by-sha`'s and
  `prepare-release-0-3-0`'s tests move under their names and their
  `pytest -k` citations resolve by name, and the eight records among them
  that name a deleted module as a guard's home are superseded by name in
  DEC-TSS-016.
- R-TSS-5: `pyproject.toml`'s `[tool.pytest.ini_options]` MUST register
  exactly three markers under `markers` — `unit`, `integration`, `e2e` —
  each with its criterion of R-TSS-6 in the description, and `addopts`
  MUST carry `--strict-markers` so an unregistered marker fails collection
  loudly. The markers MUST be registered under `markers`, not only through
  `addopts`, because the Appendix A durations command clears `addopts`.
  `testpaths` MUST be unchanged. Every collected test MUST carry exactly one
  of the three, counted at the item level: a module-level `pytestmark` —
  a single mark or a list of marks, the list form where a module already
  has a `pytestmark` — applies to every test in the module, so a module
  whose tests are not all one tier MUST carry no module-level tier mark and
  MUST mark each test function. A tier MUST be written only as a
  `@pytest.mark.<tier>` decorator or a `pytest.mark.<tier>` entry of
  `pytestmark`; an alias (`name = pytest.mark.<tier>`, the `needs_bash`
  pattern) MUST NOT be used for a tier and MUST be named by the guard.
  `skipif`, `parametrize` and pytest's other built-in marks are not tiers
  and are unconstrained.
- R-TSS-6: The tier of a test is decided by what it uses, and by what is
  used by every definition it reaches: a function, class or module constant
  its body names in its own module; a fixture it requests — as a parameter,
  through `usefixtures`, or by being autouse in its module or in
  `tests/conftest.py`; and a function, class or constant it imports from
  another module under `tests/` — resolved transitively, a class reached
  contributing every method it defines. A use counts and a binding does
  not: a name bound to a tree path counts where it is used, and where it is
  bound only when nothing uses it; an annotation is never a use. A test is
  `e2e` if and only if it reaches a process start: a reference — called,
  passed or aliased — to a process-starting function of `subprocess`, `os`,
  `asyncio` or `pty`, the set kept as one constant of the criterion;
  `subprocess.CompletedProcess` and `subprocess.TimeoutExpired` start
  nothing and do not count, and `run_cli` is `e2e` through its body. A test
  is `integration` if and only if it is not `e2e` and reads this
  repository's own tree: it uses `__file__`, as a bare name or as an
  attribute such as `detect.__file__`, or a name bound to it — a module
  constant, a local, or a constant of an imported module — in a path
  expression whose chain carries no segment equal to `fixtures` or
  `corpus`; or it uses a name imported from a script under `tools/`, which
  runs that script in-process. `load_tool`, `run_tool_main` and the
  `read_pyproject` this package adds are `integration` through their
  bodies, and no list names them. A test is `unit` if and only if it
  reaches neither. The criterion stops at `tests/`: writing fixtures under
  `tmp_path`, reading the labelled corpora under `tests/fixtures/` and
  `tests/corpus/`, and calling the package — `cli.main` included — in-process
  do not change a tier, including where the code under test starts a
  process itself. The criterion errs upward: it MAY place a test above its
  runtime cost, and MUST NOT place in `unit` a test whose own code under
  `tests/` starts a process or reads the tree. The criterion MUST be
  computed by AST in an uncollected module under `tests/`; a guard test
  MUST assert every marker agrees with it in both directions over every
  `tests/test_*.py`, and MUST be shown red on planted module texts: an
  unmarked test, a test carrying two tiers, a `unit`-marked test that calls
  `run_cli`, an `e2e`-marked test that names no process start, a
  `unit`-marked test that names a tree constant, a `unit`-marked test that
  reads the tree through a fixture parameter, a `unit`-marked test under an
  autouse fixture that starts a process, a `unit`-marked test that starts a
  process only through a method of a class it imports, a `unit`-marked test
  that binds a tree read to a local it never uses, a tier written through
  an alias, and a module over the bound; and MUST be shown quiet on a
  planted `unit` test whose body builds a `__file__`-rooted path under
  `fixtures`, a `fixtures`-rooted module constant, a
  `subprocess.CompletedProcess` annotation and constructor, and a module
  exactly at the bound.
- R-TSS-7: The fast tier is the command `python -m pytest -m unit`,
  documented in `docs/hooks.md` beside the optional pre-push hook and in
  `tests/AGENTS.md`'s run sentence, with what the tier excludes stated in a
  sentence. No Make target MAY be added for it: `test_the_suite_runs_once_through_coverage_run`,
  merged to `main` in #41, holds that `coverage-run` is the only recipe
  invoking pytest and MUST stay green unedited. `.pre-commit-config.yaml`
  MUST NOT change. The tier's collected count (`python -m pytest -m unit
  --collect-only -q`) and wall time (`python -m pytest -m unit -q -p
  no:cacheprovider -o addopts=""`) MUST be recorded in `tasks.md`, dated
  with the commit.
- R-TSS-8: `tests/support.run_cli` MUST be the only place a test module
  passes an argv list containing both `-m openspec_graph.cli` and
  `--target` to `subprocess.run`; `tests/test_decomposition.py`'s inline
  `_run_cli` MUST become `run_cli(...).stdout`, with the golden hashes
  unmoved. `tests/support.write_spec` and `write_speckit_spec` MUST be the
  only writers of the harness path `openspec/changes/<change>/specs/<capability>/spec.md`
  and the SpecKit path `specs/<feature>/spec.md`: `tests/test_e2e_corpus.py`'s
  `_harness_spec` becomes `write_spec(repo, change, "cap", body)`, its
  SpecKit write and `tests/test_detect_speckit.py:105` become
  `write_speckit_spec`, `tests/test_detect_thresholds.py:257` and
  `tests/test_decomposition.py:102–105` become `write_spec`; a path built
  for a read-error fixture (a FIFO, a directory named `spec.md`, an
  unreadable file) or asserted rather than written is not a writer.
  The release workflow's `_workflow_jobs` near-copy (in
  `tests/test_agent_artifacts.py` until the split moves it, unchanged, to
  `tests/test_release_surface.py`) MUST be replaced by
  `tests/support.workflow_job_blocks`, closing DEC-HCW-009's deferral.
  Two guard tests MUST read the shapes by AST — a `subprocess.run` call
  whose argv list holds the two literals and `--target`; a `write_text`
  call on a path expression whose chain holds `openspec`, `changes`,
  `specs` and `spec.md`, or `specs` and `spec.md` directly under a
  repository root, resolving a local name to its assignment — and MUST be
  shown red on planted module texts. `tests/test_skill_contract.py:657`,
  which runs `--version` without `--target`, is not `run_cli`'s shape and
  stays; the bare `tmp_path / "spec.md"` writes, the `-c` script spawns,
  the `tools/` script and `make`, `git`, `bash` and `python -m build`
  spawns are named in `tasks.md` as having nothing to route and stay.
- R-TSS-9: Each of `test_projections_are_byte_stable_across_runs`,
  `test_an_unprojectable_file_exits_two_with_an_empty_stdout`,
  `test_sarif_returns_the_same_exit_code_as_the_text_run` and
  `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict`
  MUST run its loop through `openspec_graph.cli.main(argv)` with `--target`
  in `argv` and `capsys` capturing, and MUST keep exactly one `run_cli`
  call in its body — per parametrised case where the test is
  parametrised — as the entry-point check, whose result MUST be asserted
  equal to the in-process result on the same property (the stdout bytes of
  one format, the exit code of one run), so the loop's verdicts are tied
  to the real process. Every assertion the test makes today MUST still be
  made: byte stability across two runs per format, exit 2 with an empty
  stdout and a non-empty diagnostic per format, text/SARIF/JSON exit-code
  parity on a failing and on a clean repository with both outcomes
  exercised, and exit 0/0/1 across the three thresholds with `G010`
  present and `G004` absent. `tests/test_e2e_corpus.py`'s `_findings`
  helper MUST NOT change for its other callers; the converted test parses
  the captured JSON itself or through an in-process sibling helper. A
  guard test MUST read the four bodies by AST and assert exactly one
  `run_cli` call and a reference to `main` in each.
- R-TSS-10: A test whose process boundary is the property MUST NOT be
  converted or edited beyond the import lines a move requires: one that
  sets an environment variable for the child (`PYTHONIOENCODING`,
  `COVERAGE_FILE`, `PYTHONHASHSEED`), runs a program other than the CLI
  (pytest, `python -m build`, `make`, `git`, bash, a `tools/` script, a
  `-c` script), or asserts on the tree or the environment after the process
  rather than on its output. By name at the measurement commit:
  `test_common_verbs_do_not_crash_under_ascii_stdout_encoding`,
  `test_arbitrary_non_ascii_spec_content_survives_graph_mermaid_under_ascii_encoding`,
  `test_matcher_accuracy_tool_runs_headless_and_exits_zero`,
  `test_suite_survives_an_ambient_coverage_file`,
  `test_the_real_wheel_passes_the_gate`, every test of
  `tests/test_action_contract.py` that runs the action,
  `test_module_is_importable_without_the_rest_of_the_package`,
  `test_gate_script_is_runnable_as_a_script`, the one-warning test of
  `tests/test_findings_envelope.py`, the hash-seed test of
  `tests/test_detect_thresholds.py` and
  `test_read_only_verbs_leave_tree_byte_identical`.
- R-TSS-11: The Appendix A durations command — `python -m pytest tests/ -p
  no:cacheprovider -q --durations=12 -o addopts=""` — MUST be run on the
  finished tree in the same container as the before figure, back to back
  with a before run on the tree immediately preceding the loop conversion,
  and both recorded in `tasks.md` dated with their commits: each total, each
  twelve slowest, and the per-test call durations of the four named tests
  from `python -m pytest tests/test_report.py tests/test_sarif.py
  tests/test_e2e_corpus.py -k "<the four names joined by or>"
  --durations=0 -p no:cacheprovider -q -o addopts=""` before and after.
  Each of the four per-test figures MUST be lower after than before, and
  none of the four MUST appear in the after table's twelve. The totals are
  recorded with their spread stated — the three readings of the unchanged
  tree in the proposal are the measure of it — and no MUST is placed on a
  total; the plan's 200 s row is reported in the proposal and `tasks.md`
  as the plan's figure, never claimed as this package's saving.
- R-TSS-12: Every guard this spec adds MUST read the file it judges, MUST
  be written and run red before the change it covers — the flatness and
  bound guards red on the unsplit tree, the marker guards red on the
  unmarked tree, the routing guards red on the unrouted tree, the loop
  guard red on the unconverted tests — with the red run recorded in
  `tasks.md` and never committed as a tree state, and MUST be shown red on
  the planted counter-examples R-TSS-6 and R-TSS-8 name.
- R-TSS-13: `CHANGELOG.md`'s `[Unreleased]` section MUST carry a `Changed`
  entry for this package naming the removed and the new modules, the three
  tiers and the strict markers with the fast-tier command, the routing,
  the four converted loops with the before/after per-test figures and
  totals with their commits, and the eight superseded records of
  DEC-TSS-016 by id.
- R-TSS-14: `tasks.md` MUST record, dated with the commit and naming the
  command: `wc -l tests/test_*.py | sort -n | tail -8` before and after;
  the AST test-name set's hash and the collected count of R-TSS-2 at
  Milestone 0, after each split and at each stage commit; the red run of
  every guard; the durations figures of R-TSS-11; the fast tier's count
  and time of R-TSS-7; `grep -ln "subprocess.run" tests/test_*.py` and the
  two routing greps before and after; the pointer grep of R-TSS-4 before
  and after.
- C-TSS-1: No change under `openspec_graph/`, no rule, no golden hash, no
  runtime or dev dependency: the `RULES` tuple, `README.md`'s rules table,
  `tests/baseline_rules.json`, the `validate`/`graph`/`rules` hashes,
  `[project] dependencies` and the dev extra are untouched; no `pytest-xdist`.
- C-TSS-2: No Makefile recipe, target or prerequisite, no workflow job or
  step, and no composite-action line MAY change; the only edits under
  `.github/` are the comment lines R-TSS-4 names. The four coverage floors
  MUST be unchanged in value and MUST hold on the finished tree.
- C-TSS-3: No test function MAY be renamed or deleted, no `tests/<subdir>/`
  MAY be created, no ruff family MAY be selected or deselected, and
  `.pre-commit-config.yaml` MAY NOT change.
- C-TSS-4: This spec's requirements and criteria MUST NOT pin a count that
  another package changes — a module count, a test count, a line count, a
  duration. Measurements belong in the proposal and in `tasks.md`, dated
  with their commit and naming their command.
- C-TSS-5: The tests R-TSS-10 names MUST have bodies identical before and
  after this package apart from import lines; the diff of each is read at
  review.
- C-TSS-6: `make lint` MUST exit 0 on every new and edited test module, and
  the `tests/*` per-file-ignores MUST NOT widen.
- C-TSS-7: The converted tests stay `e2e` under R-TSS-6, because one
  process start remains in each; the saving is in their per-test figures,
  not their tier.

---

## Decisions

- **DEC-TSS-001:** split along the section seams, names kept, helpers
  following their users, and the two parents removed rather than kept slim.
  The seams are the package boundaries the authors already drew — every
  section comment names a package's criteria or a script — so a split
  along them is a move and not a rewrite, and a reviewer can check it as
  one: the sorted test-name set and the collected count over the
  pre-existing modules are identical before and after, and every spec
  citation resolves. The parents go because no section left in either
  would be "CI hardening" or "workflow hardening" as a subject: both names
  describe the first package that wrote into them, which is how
  `test_ci_hardening.py` came to hold the graph tools and the Dependabot
  config — a module named for history accretes, a module named for a
  subject refuses. Rejected: a `tests/ci/` package (orphans every test from
  two gates, #35's lesson); keeping one parent under its old name as the
  workflow module (every pointer to it would then be half right); renaming
  any test to fit its new module (the citations).
- **DEC-TSS-002:** the third module out of `test_ci_hardening.py` is not
  "action". The plan's shorthand was workflow / action / makefile; the
  module measured by section holds three tests about the composite action,
  two of which read `ci.yml` and one the Makefile, while
  `tests/test_action_contract.py` — the module that owns the action — sits
  at exactly the bound and cannot absorb them. The sections that are
  actually the third concern are the `tools/` scripts exercised in-process:
  the two coverage checkers, graph-diff, `render_mermaid.py`, the threshold
  guard and the runnable-as-a-script contract. So the three `ci.yml` tests
  go with the workflow, the Makefile one with the Makefile, and the scripts
  go to the modules of DEC-TSS-003 — which is what "by concern" means when
  the concern is measured rather than remembered.
- **DEC-TSS-003:** the coverage checkers' tests from both parents merge into
  `tests/test_coverage_checkers.py`, the threshold guard's into
  `tests/test_threshold_guard.py`, the graph consumers' into
  `tests/test_graph_tools.py`, and `tests/test_gate_scripts.py` keeps the
  scripts no other module tests and gains the one contract its docstring
  already points at. The two checkers were the one case of the same scripts
  tested in two modules — `test_ci_hardening.py`'s floor sections from
  `harden-ci-gates` and `test_gate_scripts.py`'s from `gate-tools-coverage`
  and `measure-coverage-once` — which is the duplication W7.4 names.
  `test_suite_survives_an_ambient_coverage_file` nests a pytest over its
  own module path selecting `test_coverage_floor_passes_at_threshold`; both
  move together and the path follows, so the nested run still runs one
  test from the module it names. The `repo` fixture `test_ci_hardening.py`
  defines for the graph-diff tests moves with them, and `conftest.py`'s
  docstring, which explains that a module-level `repo` wins over the
  conftest one by naming that module, names the new one. Rejected: folding
  the floor sections into `test_gate_scripts.py` (it would stay over the
  bound); one `tests/test_ci_scripts.py` for every script (the subject is
  the script family, and a module for all of them is the parent under
  another name).
- **DEC-TSS-004:** the line bound is `MAX_TEST_MODULE_LINES`, a module-level
  constant of `tests/test_suite_shape.py`, initial value the plan's 700,
  compared with `<=`. It mirrors `MAX_NESTED_LINES` in
  `tests/test_agent_artifacts.py`: a test-shape budget is the suite's
  business, lives beside the test that reads it, and is not a
  `[tool.specgraph]` key because the thresholds guard scans the Makefile
  and the workflow YAML for numbers that gate a build, and a budget on a
  test module gates nothing a build measures. The command behind every
  line count this package states is `wc -l tests/test_*.py | sort -n |
  tail -8`. `test_action_contract.py` at exactly 700 is at the bound, and
  the bound is inclusive so that a split is never forced by a module that
  the plan itself counted as "reaching" rather than exceeding it. Rejected:
  a key in `pyproject.toml` (a second place for a number one test reads);
  a strict `<` (would split a module the plan did not).
- **DEC-TSS-005:** three tiers, registered under `markers` with
  `--strict-markers` on, applied per function wherever a module mixes
  tiers and as a module-level `pytestmark` entry only where it does not,
  with exactly one tier per item counted across both levels and no alias.
  Strict because an unregistered mark is otherwise a silent typo that
  selects nothing and fails nothing — fail-closed is this repository's
  posture for every gate. Both levels count because pytest applies a
  module mark and a function mark cumulatively, so a module-level `e2e`
  with a function-level `unit` "override" would be an item with two tiers
  that `-m unit` selects wrongly; the rule that a mixed module carries no
  module-level tier keeps the source readable as the truth. Per-function
  marks are the expected shape, not the exception: the criterion simulated
  over `test_report`, `test_sarif` and `test_cli_surface` gives 30 / 2 / 13,
  8 / 3 / 13 and 8 / 6 / 14 across `unit` / `integration` / `e2e`, so the
  modules that spawn are mostly in-process tests with a spawning minority,
  and the fast tier is larger than a module-level view would make it. The
  list form is required where a `pytestmark` already exists
  (`tests/test_spec_discovery_identity.py:28` carries a `skipif`), and the
  guard reads both forms. An alias (`name = pytest.mark.<tier>`) is
  forbidden for tiers because a reader grepping for `pytest.mark.unit`
  would miss every test marked through it and the guard would have to
  resolve module-level names to find them; `needs_bash` stays as it is
  because `skipif` is not a tier. Registered under `markers` and not only
  in `addopts` because the durations command passes `-o addopts=""`.
  Rejected: deriving marks at collection in `conftest.py` from the same
  signals (a reviewer could not read a test's tier in its source, and the
  criterion would live in a hook rather than in the file it classifies);
  four tiers with a `slow` mark (the durations table is the slow list, and
  a tier named for a measurement drifts).
- **DEC-TSS-006:** the criteria are cost signals, not pyramid purity. The
  cost that dominates this suite is the process start — the durations table
  is a list of tests that spawn — and the coupling that makes a test fragile
  is a read of this repository's own tree, which changes under every pull
  request. So `e2e` means "starts a process", `integration` means "reads
  the tree or runs a `tools/` script in-process", and `unit` means neither,
  which deliberately includes a test that writes a fixture under `tmp_path`
  and runs `cli.main` in-process: it is fast and it is coupled to nothing
  but the package. `fixtures/` and `corpus/` are excluded from the tree
  signal because they are labelled input to planlint, not documents of this
  repository — `tests/AGENTS.md` already says so — and a parser test over a
  labelled corpus is the unit tier's heart. Rejected: "touches the
  filesystem" (every parser test writes a fixture, so the unit tier would
  be nearly empty); "uses the `repo` fixture" (a conftest fixture that
  writes three files under `tmp_path` is not a boundary).
- **DEC-TSS-007:** the tier guard is an AST scan over `tests/test_*.py`,
  `tests/conftest.py` and the modules under `tests/` they import,
  non-recursive like the two existing guards, with transitive resolution
  through helpers, classes, constants and fixtures, the signals of R-TSS-6,
  and agreement asserted in both directions. The criterion lives in the
  uncollected `tests/shape_support.py`, beside `workflow_support.py`, so
  `tests/test_suite_shape.py` holds assertions and planted texts and stays
  inside the bound it enforces. Both directions because a stale `e2e` mark on a test that no
  longer spawns is a test the fast tier is wrongly missing, and a `unit`
  mark on a test that does spawn is a slow test the fast tier is wrongly
  paying for; one direction would guard half the property. Fixture
  parameters resolve exactly like called helpers because the simulation
  over `tests/test_cli_surface.py` showed the two failure modes of not
  doing so: `test_entry_points_wired_in_pyproject` reads the repository's
  `pyproject.toml` only through its `repo_root` parameter and would be
  `unit` while reading the tree, and the five `test_deprecated_alias_*`
  tests take a `fixtures` parameter whose body is `Path(__file__)` under
  `fixtures/` — the canonical unit case of DEC-TSS-006 — and would be
  `integration` under a body-level `__file__` rule with no exemption; the
  same `fixtures` body rooted at `tests/test_skill_contract.py:133`'s
  `populated_repo` and `tests/test_rules_speckit.py:266` says the exemption
  must apply to every `__file__`-rooted expression, body-level or constant,
  not to module constants alone. `__file__` is matched as a name or an
  attribute because `tests/test_detect_corpus.py:307` spells its root as
  `Path(detect.__file__)`. A reader that lives in `support.py` names no
  `__file__` at its call site, so a caller would be `unit` while reading
  the repository's `pyproject.toml` unless the criterion follows the
  import; it follows imports into every module under `tests/` and takes
  `load_tool`, `run_tool_main` and `read_pyproject` to `integration` from
  their bodies. This supersedes the enumerated set of tree-readers the
  round-1 draft kept as a constant: implementation found that a hand list
  misses what nobody listed — `tests/test_action_contract.py`'s runner
  simulator starts `bash` from a class method, and
  `tests/test_wheel_metadata.py` puts `tools/` on `sys.path` and runs
  `check_wheel_metadata` in-process with no support helper at all — and
  the derived form needs no line added when a helper is. For the same
  reason a process start is any reference to a process-starting function,
  not only a call, and an assignment defers to its uses but never hides a
  process start. `subprocess.CompletedProcess` and
  `subprocess.TimeoutExpired` do not count, because the first is a result
  type — in an annotation or a fake built for a monkeypatch — and the
  second is an exception class. Rejected: `request.session.items`
  from inside a guard (pytest's own deselection hook runs first, so under
  `-k` or `-m` the guard would see only the selected items and pass on a
  tree it never checked); `item.iter_markers()` for the same reason; a
  criterion that ignores fixtures (the `repo_root` case above).
- **DEC-TSS-008:** no Make target for the fast tier. `test_the_suite_runs_once_through_coverage_run`
  — `measure-coverage-once`'s guard, R-MCO-2 and R-MCO-6, merged to `main`
  in #41 — enumerates every recipe line that invokes pytest other than
  `coverage-run`'s and names it, so a `-m unit` recipe is a red test on the
  day it lands; amending a shipped guard, and the two requirements behind
  it, to carve out a convenience is the wrong trade. The ladder's promise
  in `docs/hooks.md` — a commit cannot bypass what CI checks — is a promise
  about gates, and a partial suite is not a gate: it is a loop a
  contributor runs between edits. So the fast tier is the command
  `python -m pytest -m unit`, written where a contributor looks for it, and
  this package records its collected count and wall time so a later
  package that wants a target has the figure that justifies one.
  `.pre-commit-config.yaml` stays as it is for the same reason: its hooks
  are the gates. Rejected: a target composed into neither `ci` nor
  `pre-pr` (still a second pytest recipe); a target that calls
  `coverage-run` with a `-m unit` variable (the one run would then not be
  the suite, and the floors would be read from a partial report).
- **DEC-TSS-009:** route the shapes `tests/support.py` already owns and
  guard them there; name what has nothing to route. `test_decomposition.py`'s
  `_run_cli` is `run_cli` with the coverage variable and the UTF-8 decode
  that `run_cli` carries for a reason its own comment repeats; routing it
  cannot move a golden hash, because `COVERAGE_PROCESS_START` changes what
  the child measures and not what it prints, and the hash test is the proof.
  `_harness_spec` is `write_spec` with `cap` fixed. The two hand-written
  SpecKit paths are stragglers behind an established helper, not a helper
  waiting for a first caller: nine modules already import
  `write_speckit_spec`, and one of the two sites sits in
  `tests/test_detect_speckit.py`, which itself calls it fifteen times,
  while the other sits in `tests/test_e2e_corpus.py`, which never imported
  it. The `_workflow_jobs` near-copy in `test_agent_artifacts.py` is the one
  DEC-HCW-009 deferred to this item by name. The guards read the two shapes
  by AST — `test_helpers_not_duplicated_inline` forbids a redeclared
  `write_spec`, and a hand-built path with `write_text` is the same drift
  under a different spelling — and are narrowed to writers: a FIFO, a
  directory named `spec.md` and an unreadable file are read-error fixtures
  that must build the path by hand, and an assertion on a path writes
  nothing. `test_skill_contract.py:657` runs `--version` with no `--target`,
  which `run_cli` cannot express, so the CLI guard keys on the presence of
  `--target` in the argv — exactly `run_cli`'s shape — and that call stays.
  Rejected: a `run_cli` variant without `--target` (one caller); widening
  `write_spec` to the SpecKit layout (two layouts, two helpers, as now).
- **DEC-TSS-010:** each converted loop keeps one `run_cli` whose result is
  compared with the in-process result on the same property. The property
  under test in all four is the output — bytes, an exit code — and
  `cli.main(argv)` returns the exit code and prints to the streams
  `capsys` replaces; `main`'s docstring already names in-process calls
  under `capsys` as how this suite does it. One subprocess stays because a
  loop that never touches the real entry point proves the function, not
  the program, and the comparison — the subprocess's stdout equals the
  in-process stdout for one format, the subprocess's exit code equals the
  in-process code for one run — is what makes the in-process verdicts
  evidence about the process. Per parametrised case for the unprojectable
  test, because each payload is a separate test item and each should tie
  to the real process once. `_findings` in `test_e2e_corpus.py` is not
  converted because its other callers are not in W7.6's list and a shared
  helper's conversion would convert them silently; the G010 test parses
  the JSON it captures, or an in-process sibling does. One mechanism is
  recorded for the implementer: the CLI's diagnostics reach stderr through
  a logging handler bound at `configure_logging` time, so if an in-process
  stderr assertion proves order-dependent under `capsys`, the assertion is
  "a diagnostic, not a half-written document on stdout" and is made through
  `captured_logger` on the package logger — the property does not change,
  only the capture. Rejected: converting the subprocess-free way with no
  entry-point check (the function, not the program); converting
  `_findings` (the silent spread).
- **DEC-TSS-011:** the process-boundary rule is stated mechanically and the
  tests it protects are named. A test that sets the child's environment,
  runs a program other than the CLI, or asserts on the tree afterwards is
  testing the process, and an in-process call would test something else
  with the same name. `test_read_only_verbs_leave_tree_byte_identical` is
  the slowest test in the table and is deliberately left: its property is
  what a real `planlint` process leaves on disk, including anything a
  `.pth` hook or a verb's own side effect might write from the process's
  cwd, which an in-process call cannot show; the plan's W7.6 list omits it
  for that reason, and this package does not second-guess the list. The
  action-contract tests run GitHub's bash; the wheel test builds the wheel;
  the encoding tests set `PYTHONIOENCODING`; the ambient-coverage test is a
  nested pytest; the fresh-interpreter tests exist to see an interpreter
  with nothing imported. C-TSS-5 makes the promise checkable: their bodies
  are byte-identical apart from import lines.
- **DEC-TSS-012:** the saving is held to the four converted tests' own
  call durations and to their absence from the after table's twelve; the
  totals are recorded with their spread, and the plan's absolute target is
  reported as already met at the measurement commit rather than claimed.
  The same command read 235 s at `9c4b6e9` (1498 tests), 212.5 s and
  210.46 s at `5246931` (1578), and 149.98 s, 155.74 s and 157.68 s in
  three sessions on the one tree at `f7118a0`/`bb4e4ad` (1602) — the suite
  grew by a hundred tests while its wall time fell by a third, with no
  package claiming that drop, and three readings of an unchanged tree
  spread over about eight seconds. The four named tests cost about 13.6 s
  of that total today, and the seven subprocesses the conversion keeps will
  cost about 2.5 s, so the expected saving is about eleven seconds — of the
  same order as the spread. A MUST on the total would therefore be met or
  missed by the weather; a MUST on the per-test figures, which the
  conversion moves directly and which the spread does not reach, is the
  measurement this package can be held to, and the pair is taken back to
  back on the finished tree so the totals are at least comparable. The
  plan's 200 s row is the plan's figure: met before this package, reported
  after it, never this package's claim. Rejected: claiming 235 to 200 (the
  plan's row describes a different commit on a different day); a MUST that
  the after total is at or under the before total (noise decides it).
- **DEC-TSS-013:** documents that describe the design are updated; dated
  records are left; no other change package is edited. `tests/AGENTS.md`,
  `docs/architecture/c4.md`, `docs/hooks.md`, the hook script, the
  docstrings and the configuration comments say where a guard lives and
  must say where it lives after this change; `CHANGELOG.md`'s released
  sections, `docs/next-steps.md`, the peer reviews and the plan record what
  was true on a date. `measure-coverage-once`'s `tasks.md` names
  `tests/test_ci_hardening.py` as where its guards were written, which is a
  record of what happened; its guards move under their names and its
  `pytest -k` citations resolve by name, so that package needs nothing
  from this one. Where a shipped package's spec requires a guard to live
  in a module this change deletes, the form is DEC-MCO-006's: the record
  is superseded by name, with the property it protected and the module
  that now carries it, and the shipped package is not edited — DEC-TSS-016
  holds the eight. `tests/AGENTS.md` is edited by replacing where it can
  and adding only the one bullet and the one node the shape now needs,
  because it sits nine lines under its budget and the budget is the point.
- **DEC-TSS-014:** one pull request — this branch's, #42 — with the three
  stages as separate commits, each recording the test-name hash and the
  collected count of R-TSS-2. The loop this repository follows is one pull
  request per package, and a commit boundary already gives the durations
  comparison what it needs: the before figure of R-TSS-11 is taken on the
  tree as the second stage leaves it, which is a commit, and the after
  figure on the third, so the pair brackets exactly the loop conversion
  whichever pull request the commits ride in. The stages stay distinct
  because each is a different kind of change to review — moves proven by an
  unchanged name set and count, then configuration and three helpers, then
  four test bodies — and a reviewer reads them in that order. Rejected:
  three pull requests (the first draft's shape; it inverted the loop and
  bought nothing a commit boundary does not); one undivided commit (a
  durations pair across a move cannot attribute its delta, and a review of
  moves mixed with edits is a review of neither).
- **DEC-TSS-015:** the guards live in one new module, `tests/test_suite_shape.py`,
  rather than beside `test_helpers_not_duplicated_inline` in
  `tests/test_decomposition.py`. That module pins the package's module
  layout and golden hashes and reaches the bound's neighbourhood with the
  rules-verb diagnostics; a module whose subject is the shape of the suite
  itself — flatness, bound, tiers, the two routed shapes, the four loops —
  is a subject, and the capability this package is named for. The existing
  guard stays where it is: a move of a cited test for tidiness is exactly
  the kind of churn the citation test exists to make unnecessary. Because
  this module is the one place the package adds tests, the baseline of
  R-TSS-2 excludes it, so every comparison is against Milestone 0's
  figures and not a moving target.
- **DEC-TSS-016:** eight records of four shipped packages are superseded by
  name, each with the property it protected and the module that now
  carries it, and none of those packages is edited — DEC-MCO-006's form,
  because each is merged to `main` and a record of what shipped. From
  `select-zero-cost-guards`: R-ZCG-10 ("Two guard tests in
  `tests/test_ci_hardening.py` MUST parse `pyproject.toml` structurally")
  and DEC-ZCG-010 (the guards "live in `tests/test_ci_hardening.py`, in the
  section headed as claims about the CI configuration itself") — the two
  guards and that whole section live in `tests/test_ci_workflow.py`, beside
  `test_lint_is_a_hard_gate` as before, and the structural-parse property
  is unchanged. From `harden-ci-workflows`: R-HCW-15 ("Every guard this
  spec adds MUST live in the new module `tests/test_workflow_hardening.py`")
  and DEC-HCW-008 (a new module "not in `tests/test_ci_hardening.py`"
  because that module "is 859 lines across five change packages' concerns
  already") — the guards live in `tests/test_workflow_pins.py`,
  `tests/test_workflow_posture.py` and `tests/test_workflow_python.py` by
  section, each under the bound DEC-HCW-008 was reaching for, with the
  dynamic read-the-file property and the collect-every-offender property
  unchanged; and R-HCW-16 ("`tests/test_ci_hardening.py` MUST keep
  `_ci_job_blocks` as an alias") — the alias and its two parser tests live
  in `tests/test_ci_workflow.py`, and `workflow_job_blocks` stays in
  `tests/support.py` as DEC-HCW-009 placed it, now with the
  `test_agent_artifacts.py` copy that decision deferred routed through it.
  From `pin-actions-by-sha`: R-ASP-8 ("Every guard this spec adds or amends
  MUST live in `tests/test_workflow_hardening.py`", with the one helper
  amended outside it, "`tests/test_ci_hardening.py`'s
  `_dependabot_directories`") — the pin guards live in
  `tests/test_workflow_pins.py` with their planted counter-examples, and
  `_dependabot_directories` moves there with the Dependabot section it
  serves; and R-ASP-11 ("Both readers of that file —
  `tests/test_workflow_hardening.py::_dependabot_entries` and
  `tests/test_ci_hardening.py::_dependabot_directories` — MUST read the
  plural `directories:` list") — both readers live in
  `tests/test_workflow_pins.py` and the plural-list property is unchanged,
  which the planted plural entry still shows. From `prepare-release-0-3-0`:
  DEC-REL-011 ("`tests/test_workflow_hardening.py` is the sibling's alone:
  this package reads it under `make pre-pr` for C-REL-4's no-pin property
  and edits no line of it") — the attestations-input guard that package
  placed in that module's last section lives in
  `tests/test_workflow_posture.py`, and the merge-hazard sentence describes
  a merge that has happened. Every one of those packages' `pytest -k`
  citations resolves by function name after the moves, which is why the
  records can be superseded without a word of them changing; the
  supersession is recorded here and in the CHANGELOG entry so the next
  reader of R-HCW-15 finds the module it names gone and this decision
  saying why. Rejected: amending the shipped specs in place (the precedent
  reserves that for an unmerged sibling, and these are merged); leaving the
  stale records unnamed (a reader would take R-HCW-15 as a requirement this
  package broke).
- **DEC-TSS-017:** the criterion is checked against runtime once, by a
  recorded audit, and stops at `tests/`. Milestone 4 ran the whole suite
  under a `sys.addaudithook` hook recording each test's process starts and
  its opens of repository files, and compared the result with the AST
  tiers: every runtime signal above a test's tier was either a process
  started by the code under test or a tool's own state (the editable
  install's metadata, Hypothesis's cache), and none came from code under
  `tests/`. The record in `tasks.md` names each one. The boundary is
  `tests/` because the package's one process start, `detect._current_sha`'s
  `git rev-parse HEAD`, and `tools/check_secrets.py`'s `git ls-files` are
  behaviour under test, and a name-level reach into `openspec_graph/`
  arrives at `_current_sha` from nearly every in-process CLI test, which
  would empty the `unit` tier of the tests DEC-TSS-006 puts at its heart.
  `docs/hooks.md` says so in the fast-loop paragraph, so the tier is not
  described as starting no process at all. Rejected: a standing audit-hook
  test (it needs the whole suite under the hook, a second full run that
  `measure-coverage-once` removed); extending the criterion into the
  package (above); a `slow` list for the residue (DEC-TSS-005 rejects a
  tier named for a measurement).

---

## Acceptance Criteria

- [ ] **AC-TSS-1:** every collected test module is at or under
  `MAX_TEST_MODULE_LINES` as `wc -l` counts, and no directory under
  `tests/` holds a `test_*.py`, read from the tree by the guards; the
  before and after of `wc -l tests/test_*.py | sort -n | tail -8` are in
  `tasks.md`. The guards are written with this change; until they exist
  the stage is the citation. (R-TSS-1, R-TSS-12, DEC-TSS-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-TSS-2:** the sorted AST set of `def test_*` names over
  `tests/test_*.py` excluding `tests/test_suite_shape.py`, and the
  collected count over the same set, are identical to Milestone 0's after
  each split and at each stage commit, recorded in `tasks.md`; every
  `pytest -k` selector in every spec under `openspec/changes/` still
  resolves to a test function; no module redeclares `write_spec`.
  (R-TSS-2, C-TSS-3, DEC-TSS-001, DEC-TSS-015)
  _Verified by:_ `pytest -k "test_every_spec_test_citation_resolves_to_a_real_test or test_helpers_not_duplicated_inline"` · stage: `make test`

- [ ] **AC-TSS-3:** `measure-coverage-once`'s guards run under their names
  from `tests/test_ci_makefile.py`, `tests/test_ci_workflow.py` and
  `tests/test_coverage_checkers.py`, `harden-ci-workflows`' and
  `pin-actions-by-sha`'s from the three workflow modules,
  `select-zero-cost-guards`' graph-tool and configuration guards from
  `tests/test_graph_tools.py` and `tests/test_ci_workflow.py`, and
  `prepare-release-0-3-0`'s attestations guard from
  `tests/test_workflow_posture.py`; none of those packages' files is in the
  diff, and the eight records DEC-TSS-016 supersedes are named there and
  in the CHANGELOG entry. (R-TSS-3, R-TSS-4, DEC-TSS-003, DEC-TSS-013,
  DEC-TSS-016)
  _Verified by:_ `pytest -k "test_the_suite_runs_once_through_coverage_run or test_test_and_coverage_tools_read_the_one_report_scoped or test_every_hooks_ci_table_row_names_a_job_or_workflow or test_scoped_totals_sum_only_the_named_subtree or test_per_file_report_names_each_module_below_the_minimum or test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag or test_every_job_in_every_workflow_has_a_timeout_inside_the_range or test_no_quoted_python_version_literal_outside_env_and_matrix or test_graph_diff_passes_when_clean or test_render_mermaid_matches_to_mermaid_byte_for_byte or test_t201_is_selected_with_exactly_the_cli_and_tools_exempt or test_lint_is_a_hard_gate"` · stage: `make test`

- [ ] **AC-TSS-4:** the nested pytest of the ambient-coverage test names
  `tests/test_coverage_checkers.py` and still reaches a verdict; the
  runnable-as-a-script contract runs from `tests/test_gate_scripts.py`; the
  rule baseline from `tests/test_rule_registry_docs.py`; the Dependabot
  guards from `tests/test_workflow_pins.py`. (R-TSS-3, DEC-TSS-002,
  DEC-TSS-003)
  _Verified by:_ `pytest -k "test_suite_survives_an_ambient_coverage_file or test_coverage_floor_passes_at_threshold or test_gate_script_is_runnable_as_a_script or test_rule_set_matches_baseline or test_every_composite_action_directory_is_watched_by_dependabot"` · stage: `make test`

- [ ] **AC-TSS-5:** `tests/AGENTS.md` names the new modules and the tier
  rule and stays within `MAX_NESTED_LINES` with its precedence clause, a
  balanced Mermaid block and resolving links; `docs/hooks.md`'s `test` row
  is byte-identical and its hook-case list still names every arm the
  script implements; `docs/architecture/c4.md` §4 and §4b, the hook
  script's two arms, and every pointer R-TSS-4 lists name the module that
  holds what they describe, read directly against the grep in `tasks.md`;
  every required document is present and linked. (R-TSS-4, DEC-TSS-013)
  _Verified by:_ `pytest -k "test_nested_agents_file_stays_short or test_nested_agents_file_states_its_precedence or test_nested_agents_file_has_a_balanced_mermaid_block or test_agent_index_links_resolve or test_hooks_test_row_names_the_matrix_bounds or test_docs_list_every_hook_case_the_script_implements or test_each_documented_file_class_is_nudged"` · stage: `make docs-check`

- [ ] **AC-TSS-6:** `[tool.pytest.ini_options]` registers exactly `unit`,
  `integration` and `e2e` under `markers`, each description stating its
  criterion, `addopts` carries `--strict-markers` and `testpaths` is
  unchanged, read structurally from `pyproject.toml`; and a collection with
  an unregistered mark fails. The test is written with this change; until
  it exists the stage is the citation. (R-TSS-5, DEC-TSS-005)
  _Verified by:_ `pytest -k "test_pytest_registers_exactly_the_three_tier_markers_strictly or test_an_unregistered_marker_fails_collection_under_strict_markers"` · stage: `make test`

- [ ] **AC-TSS-7:** every collected test carries exactly one tier, counted
  across module-level marks — single or list form — and function-level
  marks, written as decorators or `pytestmark` entries and never through an
  alias, and each tier agrees with the mechanical criterion in both
  directions over the whole tree, fixture parameters resolved — the four
  converted tests among them, which the criterion keeps `e2e` because one
  process start remains in each. The guards are written with this change
  and run red on the unmarked tree; until they exist the stage is the
  citation. (R-TSS-5, R-TSS-6, R-TSS-12, C-TSS-7, DEC-TSS-005,
  DEC-TSS-006, DEC-TSS-007, DEC-TSS-017)
  _Verified by:_ `pytest -k "test_every_test_carries_exactly_one_tier_marker or test_every_tier_marker_matches_its_mechanical_criterion"` · stage: `make test`

- [ ] **AC-TSS-8 (non-success):** on planted module texts, the guards'
  helpers name an unmarked test, a test carrying two tiers, a `unit` test
  that calls `run_cli`, an `e2e` test that names no process start, a
  `unit` test that names a tree constant, a `unit` test that reads the
  tree only through a fixture parameter, a `unit` test under an autouse
  fixture that starts a process, a `unit` test that starts a process only
  through an imported class's method, a `unit` test that binds a tree read
  to a local it never uses, a tier written through an alias, a module over
  the bound and a module under a subdirectory; and do not name a `unit`
  test whose body builds a `__file__`-rooted path under `fixtures`, nor a
  `fixtures`-rooted constant, nor a `subprocess.CompletedProcess` annotation
  or constructor, nor a module exactly at the bound. (R-TSS-1, R-TSS-6,
  R-TSS-12, DEC-TSS-007)
  _Verified by:_ `pytest -k test_a_mismarked_or_unmarked_planted_module_is_named` · stage: `make test`

- [ ] **AC-TSS-9:** `python -m pytest -m unit` collects a non-empty
  selection in which no item carries `e2e` or `integration`; its collected
  count and wall time are recorded in `tasks.md` with the commit; the
  command is documented in `docs/hooks.md` and `tests/AGENTS.md`; no Make
  target invokes pytest other than `coverage-run`, and
  `.pre-commit-config.yaml` is unchanged. Read from the recorded output and
  the Makefile guard. (R-TSS-7, C-TSS-2, DEC-TSS-008)
  _Verified by:_ `pytest -k test_the_suite_runs_once_through_coverage_run` · stage: `make test`

- [ ] **AC-TSS-10:** no test module passes an argv list holding `-m
  openspec_graph.cli` and `--target` to `subprocess.run`, and no test
  module writes the harness or the SpecKit spec path by hand, read by AST
  over the tree; `tests/test_decomposition.py`'s golden hashes are unmoved
  with its `_run_cli` routed through `run_cli`; no test module defines
  `_workflow_jobs`. The two guards are written with
  this change and run red on the unrouted tree; until they exist the hash
  test and the stage are the citation. (R-TSS-8, R-TSS-12, DEC-TSS-009)
  _Verified by:_ `pytest -k "test_output_byte_identical or test_public_import_compatibility"` · stage: `make test`

- [ ] **AC-TSS-11 (non-success):** on planted module texts, the routing
  guards' helpers name a `subprocess.run` whose argv holds the two literals
  and `--target`, and a `write_text` on a hand-built harness path and on a
  hand-built SpecKit path, and do not name a `--version` spawn without
  `--target`, a FIFO at a spec path, or an assertion on a spec path. The
  test is written with this change; until it exists the stage is the
  citation. (R-TSS-8, R-TSS-12, DEC-TSS-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-TSS-12:** the four named tests pass with their loops through
  `cli.main` under `capsys`, each still making every assertion it made
  before — byte stability per format, exit 2 with an empty stdout and a
  diagnostic per format and payload, three-way exit-code parity on both
  repositories with both outcomes exercised, 0/0/1 across the thresholds
  with `G010` present and `G004` absent — and each tied to one real
  process by an equality on the same property. (R-TSS-9, DEC-TSS-010)
  _Verified by:_ `pytest -k "test_projections_are_byte_stable_across_runs or test_an_unprojectable_file_exits_two_with_an_empty_stdout or test_sarif_returns_the_same_exit_code_as_the_text_run or test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict"` · stage: `make test`

- [ ] **AC-TSS-13:** each of the four bodies holds exactly one `run_cli`
  call and a reference to `main`, read by AST, and a planted body with two
  `run_cli` calls or none is named. The guard is written with this change
  and runs red on the unconverted tests; until it exists the stage is the
  citation. (R-TSS-9, R-TSS-12, DEC-TSS-010)
  _Verified by:_ stage: `make test`

- [ ] **AC-TSS-14 (non-success):** the process-boundary tests still pass and
  their bodies are identical apart from import lines — the encoding tests,
  the ambient-coverage test, the real wheel, the action's runs, the fresh
  interpreter, the runnable-as-a-script contract and the read-only tree
  hash; the diff is read at review. (R-TSS-10, C-TSS-5, DEC-TSS-011)
  _Verified by:_ `pytest -k "test_common_verbs_do_not_crash_under_ascii_stdout_encoding or test_arbitrary_non_ascii_spec_content_survives_graph_mermaid_under_ascii_encoding or test_matcher_accuracy_tool_runs_headless_and_exits_zero or test_suite_survives_an_ambient_coverage_file or test_the_real_wheel_passes_the_gate or test_the_action_reports_each_fixtures_labelled_status or test_module_is_importable_without_the_rest_of_the_package or test_gate_script_is_runnable_as_a_script or test_read_only_verbs_leave_tree_byte_identical"` · stage: `make test`

- [ ] **AC-TSS-15:** the Appendix A durations command, run back to back on
  the tree before and after the loop conversion in the same container, is
  recorded in `tasks.md` with the commit of each: each of the four named
  tests' call durations from the `--durations=0` selection is lower after
  than before, none of the four is in the after table's twelve, and both
  totals are recorded with the spread of the three unchanged-tree readings
  stated beside them. Read from the recorded output; no test times a
  suite, and no criterion is placed on a total. (R-TSS-11, R-TSS-14,
  DEC-TSS-012)
  _Verified by:_ stage: `make test`

- [ ] **AC-TSS-16:** the rule inventory, the golden hashes, the public
  imports and the empty runtime-dependency list are unchanged; the four
  floors are unchanged in value and both trees meet them on the finished
  tree, with the in-process loops measured directly and the one subprocess
  per converted test still measured through `COVERAGE_PROCESS_START`.
  (C-TSS-1, C-TSS-2)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_public_import_compatibility or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [ ] **AC-TSS-17:** `make lint` exits 0 on the tree with the new and
  edited test modules and no widened `tests/*` exemption; no Makefile
  recipe, workflow step or action line is in the diff beyond the comment
  lines R-TSS-4 names. (C-TSS-2, C-TSS-6)
  _Verified by:_ stage: `make lint`

- [ ] **AC-TSS-18:** `CHANGELOG.md` `[Unreleased]` carries this package's
  `Changed` entry with the items R-TSS-13 names and every versioned section
  still links to its release tag; `tasks.md` records every figure R-TSS-14
  names with its commit and command; no requirement or criterion of this
  spec pins a count another package changes; and this package validates
  clean under the repository's own rules. The entry and the records are
  read directly; the gate confirms the package. (R-TSS-13, R-TSS-14,
  C-TSS-4)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make validate`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-TSS-1..4, 6..16 — the moved guards green under their names, the shape guards green on the finished tree and red on their planted counter-examples, the four loops tied to one process each, the floors held |
| Lint | `make lint` | AC-TSS-17 — ruff clean over every new module, no widened exemption |
| Docs | `make docs-check` | AC-TSS-5 — every pointer re-pointed, the agent file within budget, every required document linked |
| Self-check | `make validate` | AC-TSS-18 — this package, then the whole tree, validate clean; every `pytest -k` selector resolves |
| Core | `make ci` | the suite, lint and the self-check together on the finished tree |
| Full | `make pre-pr` | the whole ladder green at each of the three stage commits; the durations pair recorded with the third |
