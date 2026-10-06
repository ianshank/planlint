# Reflection and consolidation plan — October 2026

Measured at `9c4b6e9` (`main` after #36), 2026-10-06. Every number below came
from a command listed in Appendix A and can be regenerated; where a figure is
inferred rather than measured it is marked **[Likely]**. This is a planning
document in the shape of `docs/next-steps.md`: it decides *what* and *in what
order*. Each workstream becomes its own OpenSpec change package through the
`planlint-change-package` loop (draft → gate → adversarial review → revise)
before any code moves, and inherits that loop's proofs.

The question it answers: with the deep dive merged and CI green, what does the
codebase owe before it grows further — and what did the last three days teach
about how this repository is worked on.

---

## 1. Where the system stands

### 1.1 Health signals that are green

| Signal | Measured |
|---|---|
| CI on `main` | run #171 at `9c4b6e9`: 16 jobs success and `graph-diff` skipped (it runs on pull requests only); on this branch's pull-request runs all 17 succeed |
| Local ladder (`make pre-pr`) | exit 0; package 99.3% line (2276/2292), 97.6% branch (744/762); `tools/` 96.0% (823/857), 93.3% (278/298) |
| Spec gate | 44 specs, 0 error / 0 warn / 0 info |
| Tests | 1498 collected, all passing; 43 test modules, 17,366 lines (17,850 with `support.py`, `graft_support.py` and `conftest.py`) |
| Static | ruff (selected families) clean; mypy clean on 43 files; `mypy --strict` is **2 errors** away (`tools/diff_spec_graph.py:20,24`, both `type-arg`) |
| Dependencies | `[project] dependencies = []`, pinned by test; dev extras unpinned by decision |
| Security | gitleaks in CI, fallback scanner locally; ruff `S` family on; the only subprocess is `git rev-parse` with a named timeout |
| Dead public code | 0 of 405 top-level symbols (functions, classes, constants) is unreferenced repository-wide; the three unreferenced symbols in §1.2 are a property and two methods, which that scan does not see |

### 1.2 Debt, measured

| Dimension | Baseline at `9c4b6e9` | Note |
|---|---|---|
| Largest modules | `cli.py` 1029, `parse_semantics.py` 764, `detect.py` 758, `report.py` 590, `graph.py` 355, `thresholds.py` 305 (of 30 modules, 6,956 lines) | `decompose-god-files` split `parse.py`/`rules.py` and left `detect.py`/`cli.py` intact by decision (R-DG-6, pinned by `test_detect_and_cli_remain_unsplit`) |
| Functions > 60 lines | 15 of 266: `build_parser` 148, `cmd_validate` 119, `build_delta` 107, `build_graph` 102, `to_sarif` 84, `cmd_report` 84, `parse_spec` 83, `find_threshold` 71, `parse_speckit` 71, `parse_makefile` 71, `scoped_fail_under` 68, `to_step_summary` 68, `hard_coded` 66, `cmd_delta` 66, `profile` 64 | |
| Complexity (`C901` > 10) | 7: `parse_makefile` 15, `cmd_validate` 14, `build_delta` 14, `cmd_report` 12, `find_threshold` 12, `scoped_fail_under` 11, `witness._load_one` 11 | `_load_one` is new since N8b counted six; the per-reason logging added a branch per skip. Ratchet maxima for W3: complexity 15, branches 15 (three functions at 13/14/15 against ruff's 12), statements 57 (one against 50), arguments 6 |
| Wide signatures (`PLR0913` > 5 args) | 3, all in `graph.py` (`:99`, `:132`, `:151`, 6 args each) | same six parameters threaded three times |
| Magic values (`PLR2004`) | 5: `cli.py:809` `100.0`; `detect.py:606` `3`, `:633` `5` (path-depth arithmetic); `tools/diff_spec_graph.py:38` `3` and `tools/render_mermaid.py:26` `2` (argv lengths) | |
| Boolean positional parameters (`FBT001`) | 3: `log.py:28` `level_from`, `log.py:46` `configure`, `scaffold.py:154` `apply` | every external caller already passes by keyword (`cli.py:1006` `configure_logging(verbose=…)`, `cli.py:267/291` `apply(plans, force=…)`, tests likewise); the one positional call is internal (`log.py:53`) — keyword-only is a one-line change |
| Line length (`E501` at 100) | 37 in package + tools, 110 in tests | `next-steps.md` item 18; a third count without a rewrap |
| `print` in library code (`T201`) | 123: 81 in `cli.py` (by design), 42 in `tools/` (scripts), **0** in any other package module | an invariant nothing enforces |
| Loops that are appends (`PERF401`) | 12 (`delta.py` 4, `parse_model.py` 2, `check_wheel_metadata.py` 2, four singles) | |
| Logging | 9 of 30 modules own a logger; `scaffold.py` *writes* files without one, and the baseline-card read lives in `cli._load_card`. `ledger.py` and `delta.py` are pure — the first draft listed them because its grep matched the docstrings that say so | |
| Unused symbols | `parse_model.Criterion.has_selector` (0 refs); `matcher_accuracy.precision_pct` / `recall_pct` (0 refs); `report.__all__` exports `STATUSES`, `STATUS_ERROR`, `FindingRecord` that nothing imports | vulture at 60% confidence agrees and adds nothing real |
| Test-only public API | `detect.filter_speckit_by_feature`, `parse_semantics.section_body`, `speckit_section_body`, `suppressions` are called only by tests | public by accident or by intent — undecided |
| JSON determinism | 11 `json.dumps` call sites, one with `sort_keys=True` (`witness.py`); the other ten rely on insertion order | correct today, by construction rather than by contract |
| Tool-script drift | 2 of 12 scripts (`diff_spec_graph.py`, `render_mermaid.py`) bypass `tools/_common.py`; they also hold the two strict-mypy errors and two of the five magic values | |
| Workflow hardening | `ci.yml`: 10 job definitions (17 jobs at run time, with the matrices), **no** top-level `permissions`, one job-level block; `timeout-minutes` on 0 jobs; no `concurrency`; every third-party action pinned to a floating major tag (`checkout@v4` ×12, `setup-python@v5` ×12, `upload-artifact@v4` ×4, `download-artifact@v4`, `gitleaks-action@v2`) and `pypa/gh-action-pypi-publish@release/v1` to a **branch** | `docs/next-steps.md:232` defers SHA pinning until "the pins can be resolved and verified" (`dependabot.yml` and the CHANGELOG attribute the deferral to `distribution-plan.md`, which pins only the *templates*); Dependabot has been on since September, so the precondition is met. `release.yml` already carries a top-level `contents: read`. Permission facts for W1.3: `upload-artifact` authenticates with `ACTIONS_RUNTIME_TOKEN` and reads no `GITHUB_TOKEN` (its `dist/`), yet its own test workflow grants `actions: write`; the gitleaks step passes `GITHUB_TOKEN` (for pull-request comments) |
| Configuration literals | the Python version appears 13 times: nine in `ci.yml` (one matrix list, eight `"3.12"` singles), two in `release.yml`, once as the composite action's input default, once as the `Dockerfile` tag (`python:3.12-slim`); nothing ties them together | `make thresholds` guards thresholds and tool pins, not this |
| Dependabot | 7 open PRs since 2026-09-19, all major bumps (`checkout` 4→7, `setup-python` 5→7, `upload-artifact` 4→7, `download-artifact` 4→8, `gitleaks-action` 2→3, two in the composite action), based on `c0540c4` — two merges behind; `mergeable_state: unknown` | the artifact pair must move together |
| Release | `CHANGELOG.md` `[Unreleased]` has grown to ~355 lines since 0.2.0 (2026-09-12); the `specgraph` alias is deprecated with no removal date | |
| Change packages | 43 under `openspec/changes/`, three of them plans awaiting implementation (this branch's), none archived. **Spec status headers are not maintained:** 18 of 44 `spec.md` files say `DRAFT` and 26 `APPROVED`, and the DRAFT set includes shipped packages — `gate-tools-coverage` runs as a CI job while its header reads `1.0.0-draft` / `DRAFT` | OpenSpec's `archive/` convention is unused, and **planlint does not support it today**: `find_spec_files` globs exactly `changes/*/specs/*/spec.md` (`detect.py:553`), so an archived package's specs leave the gate silently, and `detect.py:710` counts every directory under `changes/` as a change package, so the archive directory itself would be counted as one. Gate cost is not a reason to archive: `validate` over 44 specs runs in 0.36 s here |
| Python support window | classifiers and matrix 3.10–3.13; `requires-python >= 3.10` | 3.10 reaches end-of-life in October 2026 (PEP 619); 3.14 has been final since October 2025 (PEP 745) and is in neither the matrix nor the classifiers; the `tomli` dev extra exists only for 3.10 |
| Type-checking of tests | `[tool.mypy] files = ["openspec_graph", "tools"]` — 17,850 lines of tests are not checked; `mypy tests` stops on a module-mapping error (`graft_support` seen under two names); with `--explicit-package-bases` it reports **86 errors in 37 files**, 34 of them `pytest`/`hypothesis` imports this environment cannot resolve, ~52 real (`arg-type` 18, `no-any-return` 8, `index` 7, `union-attr` 4, `str` 4) | |
| Public docstrings | 52 public symbols without one (30 functions, 15 methods, 7 classes); the `D` family is not selected | |
| Container | `Dockerfile` has no `USER` (runs as root), base `python:3.12-slim` by tag, not digest; `.dockerignore` present | Dependabot has no `docker` ecosystem entry |
| Tool runtime | `planlint validate` 0.36 s, `graph --format json` 0.46 s on this repository (44 specs, this container) | a baseline, so a decomposition that slows the CLI is visible |
| Evals | `evals/` cases run through `claude plugin eval` by design (its README); their structure is pinned by three test modules | not a CI gap; recorded so nobody re-finds it |
| Suite shape | 16 of 43 test modules import nothing from `tests/support.py` — several legitimately (`test_properties`, `test_machinery`, `test_ledger` have no CLI or spec-writing shape to route); 21 use no `parametrize`; no pytest markers are registered; the four largest modules are 859, 836, 821 and 700 lines | |
| Suite cost | the ladder runs the full suite **twice** (`test`, `coverage-tools`); CI runs it **six** times per pull request (four matrix legs, `test-windows`, `coverage-tools`); 235 s single-process here, 66 s on four `xdist` workers | durations below |

### 1.3 Suite durations

Full suite, no coverage, this container: **1498 tests in 235 s** (`pytest -p no:cacheprovider`, single process). Under coverage the ladder's `test` leg takes longer still, and the ladder runs it twice.

| Slowest tests (call phase) | Seconds | How it runs the code (verified in the test body) |
|---|---|---|
| `test_read_only_verbs_leave_tree_byte_identical` (test_skill_contract) | 10.6 | `run_cli` ×3 loops: every read-only verb as a CLI subprocess, then a tree hash |
| `test_projections_are_byte_stable_across_runs` (test_report) | 5.3 | `run_cli` in a loop: `report` twice per projection |
| `test_sarif_returns_the_same_exit_code_as_the_text_run` (test_sarif) | 4.6 | `run_cli` in a loop: text and SARIF runs per fixture |
| `test_suite_survives_an_ambient_coverage_file` (test_ci_hardening) | 3.0 | `subprocess.run` of a nested pytest |
| `test_common_verbs_do_not_crash_under_ascii_stdout_encoding` (test_cli_surface) | 2.8 | `run_cli` under an ASCII `PYTHONIOENCODING` — the subprocess *is* the property |
| `test_the_real_wheel_passes_the_gate` (test_wheel_metadata) | 2.8 | `subprocess.run` of `python -m build`, then the checker's `main` in-process |
| `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict` (test_e2e_corpus) | 2.6 | `run_cli` in a loop over corpus targets |
| `test_the_action_reports_each_fixtures_labelled_status[passing]` (test_action_contract) | 2.6 | the composite action run under GitHub's bash via `subprocess` (`_github_bash()`, `test_action_contract.py:54–82`) |
| `test_an_unprojectable_file_exits_two_with_an_empty_stdout[an-array]` (test_report) | 2.4 | `run_cli`: one `report` subprocess per parametrised bad input |
| `test_an_unprojectable_file_exits_two_with_an_empty_stdout[not-json]` (test_report) | 2.3 | same |

The ten slowest account for ~39 s of 235, and every one of them crosses a
process boundary on purpose: `tests/support.run_cli` is the *subprocess* path, kept
because it injects `COVERAGE_PROCESS_START` so a CLI run is measured
(`fix-subprocess-coverage-blind-spot`), while `run_tool_main` and a direct
`cli.main(...)` call are the in-process paths. The optimisation surface is
therefore narrow and specific: loops that spawn one CLI per iteration where
the property under test is the *output* (byte stability, exit-code parity,
corpus verdicts) can call `cli.main` in-process with `capsys`, keeping one
subprocess per test as the entry-point check; tests where the process
boundary *is* the property (encoding, ambient coverage files, the real wheel,
the composite action) stay as they are. W7.4 carries this; the durations
table is the before-measurement it is accountable to.
---

## 2. Reflection — what the last three days taught

Written by the team that did the work, about the work.

**R1. The scanner was rewritten three times in one day.** `tools/stage_citations.py`
went regex → regex-with-boundaries → `run:`-scalar lexer across three Copilot
rounds, each round finding the hole the previous fix left. The lesson is not
"Copilot is thorough"; it is that a tool whose job is *not* to over-credit
should have been built as a lexer first, and that the adversarial review
step this repository applies to specs (`spec-adversary`) was not applied to
a tool. **Carry forward:** W5 adds tools to the adversary's remit; W9 gives
`planlint-verifier` the dead-code and literal scans so a tool is reviewed by
the same machinery as a spec.

**R2. A count went stale inside its own branch.** DEC-WCA-016 said five specs
cite `ci`; the same branch's packages made it six. The fix (cite the
regenerating command, `make stage-citations`) is the general rule: a number
in a spec is either regenerated by a named command or it is not written.
`spec-adversary` already checks this (checklist item 8); it needs the
`count → command` rule stated once in `openspec/AGENTS.md`, not rediscovered.

**R3. Two agents fixed one thread.** Copilot's coding agent pushed its own
fix while this session's ladder ran; the merge kept the lexer and adopted two
details of theirs. Cost: one merge commit, one re-run of the tools coverage
leg, ~15 minutes. **Carry forward:** a one-line convention in
`docs/agents-skills-harness.md` — a review thread is owned by whoever replies
first with a commit, and the other agent waits for the push — is cheaper than
a second merge.

**R4. Signing was configured after the first commit.** Twenty-five of the
branch's commits are unsigned because the signing program appeared mid-session,
and the hook that noticed asked for a history rewrite the policy could not
grant. **Carry forward:** `next-steps.md` item 20 (a SessionStart hook for
cloud sessions) should also verify `git config commit.gpgsign` and the signing
program *before* the first commit, not after.

**R5. The ladder is honest and slow.** Running the whole suite once to measure
`openspec_graph/` and again to measure `tools/` is the Makefile's own
reasoning (a combined `--cov-fail-under` would dilute two honest numbers into
one), and it doubles wall time. The diluting step is pytest-cov's *total*;
the repository already owns a scoped floor checker (`check_coverage_floor.py
--scope`) that reads per-file data from `coverage.json`. One run, one data
file, two scoped checks keeps both honest numbers and halves the cost (W7).

**R7. The plan's own first draft was wrong in two load-bearing places.**
Verification of this document's **[Likely]** markers overturned the
mechanism behind D2 (the unscoped package floor would have read the
diluted total) and the premise of W8.2 (archiving would have hidden specs
from the gate and miscounted the archive). The marker did its job: it told
the reviewer where to look. An independent adversarial review then found
what the markers had *not* flagged: two proposals reversing recorded
decisions without saying so (W7.2 against `gate-tools-coverage`; the line
budget against `decompose-god-files`), one byte-contract change dressed as
hygiene (`sort_keys`), three "unchanged" claims that were false
(`python -m`, the logger row, an owner-less optimisation) and seven errata
in the baseline (§8). **Carry forward:** a plan states a mechanism only with
the command that demonstrated it, and a plan that touches a shipped package
names the requirement it changes — `planlint validate` checks citations,
not semantics, so only a reviewer catches a silent reversal.

**R6. What went right and should be kept:** every fix reproduced its defect
first; every code change carried a test that failed without it; the gate was
run before every `openspec/` edit and its exit code reported; nothing was
pushed before the ladder said so; the one concurrent-agent race was merged,
not force-pushed. These are the habits the plan must not trade away for speed.

---

## 3. Guardrails for everything below

1. **Additive and backward compatible.** Public imports (`openspec_graph.*`,
   the facades `parse.py` and `rules.py`), CLI verbs and flags, exit codes,
   every `schema_version`, and the golden hashes in `test_decomposition.py`
   are unmoved. A rename ships with a re-export and a deprecation note.
2. **Zero runtime dependencies.** `dependencies = []` stays; dev extras may
   grow (unpinned, by decision).
3. **Floors move up, never down; waivers are not written; `witness` is not
   run by hand** (`SKILL.md`).
4. **Ratchet, then gate.** A new lint family or stricter limit is configured
   at the *current* maximum (zero violations on day one), then lowered as the
   offenders are fixed. CI never turns red from a configuration change.
5. **Pure moves prove themselves.** Any file split ships with: collected test
   names set-identical before and after, `validate`/`graph`/`rules` golden
   hashes unmoved, `--help` output byte-identical, import boundaries re-pinned.
6. **One package per workstream, one PR per milestone.** No planning PR
   carries code; no code PR carries a rewrap.
7. **Reports before gates** (`DEC-PM-011`): a new measurement is a `make`
   report target first, a gate only once its floor has been chosen from data.

---

## 4. Workstreams

### W1 — CI/CD: keep it green, make it hard to break

*Baseline:* green; unhardened (§1.2 rows "Workflow hardening", "Configuration
literals", "Dependabot").

1. **Dependabot batch.** Land the seven proposed bumps in-tree as one
   reviewed batch rather than merging the PRs (their base is two merges
   behind `main`): `upload-artifact` 4→7 with `download-artifact` 4→8 in the
   same commit (the consumer and the producer must agree), `setup-python`
   5→7 and `checkout` 4→7 (Node 24 runtimes — GitHub-hosted runners
   qualify), and `gitleaks-action` 2→3 in the same batch — v3 is
   byte-identical to v2 in source apart from the runtime, and its three
   `GITHUB_TOKEN` calls are enumerated, so a red `security` job stays
   attributable without landing last and alone (`harden-ci-workflows`
   DEC-HCW-001 amends the earlier "last and alone" here). The composite
   action's two bumps ride with their root-level twins; Dependabot closes
   the seven PRs as superseded once the refs are on `main`.
   `action-contract` already asserts the composite action end to end.
2. **SHA-pin every third-party action** with the version in a trailing
   comment (`uses: actions/checkout@<sha> # v7.0.1`), and pin
   `pypa/gh-action-pypi-publish` to a tag SHA instead of `release/v1`.
   Dependabot keeps SHAs fresh; this meets `next-steps.md` item 232's stated
   precondition on its own terms. Guard: the `tests/test_workflow_hardening.py`
   assertion that today forbids a SHA flips to require one — every third-party
   `uses:` a 40-hex ref with a version comment — still exempting the
   repository's own `./.github/actions/planlint` and its
   `ianshank/planlint/...@<sha>` ref in `templates/spec-gate.yml`, the skill's
   `assets/spec-gate.yml` and the README snippet, which
   `distribution-plan.md` deliberately moves to `@v0.3.0`.
3. **Least privilege and bounded runs.** Top-level `permissions: contents:
   read` in `ci.yml` with job-level widening only where needed. The two
   uploading jobs (`graph-diff`, `self-validate`) should need nothing more:
   `upload-artifact` authenticates with the runner's `ACTIONS_RUNTIME_TOKEN`
   and never reads `GITHUB_TOKEN`, though its own test workflow grants
   `actions: write`, so the package proves it on the first run and widens
   those two jobs if the upload is refused. The gitleaks step passes
   `GITHUB_TOKEN`: it looks the owner up on every event, lists a pull
   request's commits (`pull-requests: read`), and posts comments unless
   `GITLEAKS_ENABLE_COMMENTS` is `"false"` — the gate's exit code is what
   matters, so comments are off and the job carries `pull-requests: read`. `timeout-minutes` on every job, sized
   from run #171's own job durations (test legs 2–4 min, `test-windows`
   ≈ 6 min, `coverage-tools` ≈ 2 min, everything else under a minute): 15 for
   the suite jobs, 10 for the rest, bounded by a range in `pyproject.toml`.
   `concurrency` keyed on the workflow and, for pull requests, the ref —
   every other event on its SHA — with `cancel-in-progress: ${{
   github.event_name == 'pull_request' }}`: `cancel-in-progress: false`
   alone would still let a *pending* `main` run be superseded by the next
   push, and a merge commit could end with no run (DEC-HCW-003). Guard:
   tests for each in `tests/test_workflow_hardening.py`, a module of its own
   because `test_ci_hardening.py` already carries five packages' concerns
   (DEC-HCW-008 amends the "in `test_ci_hardening`" here); the job-block
   parser moves to `tests/support.py` as `workflow_job_blocks`.
4. **One Python version, one place — in the tree.** The eleven single
   `"3.12"` values (`ci.yml`, `release.yml:34,52`, `action.yml:163`) become a
   one `env: PYTHON_DEFAULT: "3.12"` per workflow, referenced from each
   `setup-python` step. A workflow-level `env` is scoped to its own file:
   `release.yml` cannot read `ci.yml`'s, the composite action's input default
   cannot inherit a caller's `env`, and the Dockerfile reads neither — so
   this is **guarded duplication, not a single source**: four copies (two
   workflow envs, the action default, the Dockerfile tag) held equal by a
   test that also holds the value to a hard matrix leg. M0 shipped exactly
   this (`harden-ci-workflows` R-HCW-8, R-HCW-9, DEC-HCW-004). Not a
   repository variable: that is configuration no `grep` can see and a value
   an unset variable turns into an empty string. (YAML anchors are
   file-local — GitHub's support for them excludes merge keys — so they
   cannot reach across the four files either; a reusable workflow is heavier
   than this repository needs; the matrix list stays literal.)
5. **Release 0.3.0.** Cut the ~355 `[Unreleased]` lines into a release
   section; tag; let `release.yml` publish. PEP 740 attestations need no
   change: under trusted publishing the PyPA action "generates and uploads
   them automatically by default" (PyPI's own documentation, Appendix B), so
   the release step is to *verify* them on the published files and to keep
   the behaviour when W1.2 pins the action to a SHA. The version bump set
   is wider than `__version__`: `skills/planlint-spec-governance/SKILL.md`
   carries the version three times by hand (lines 5, 7, 8) and the
   `.claude-plugin` manifests are regenerated by `render_plugin_manifests.py`;
   a test pinning the SKILL.md fields to `__version__` lands with the bump if
   none does today. State the deprecation window for `specgraph`: warns
   through 0.3.x, removed in 0.4.0.

6. **Python support window.** Add 3.14 to the matrix and the classifiers
   now (it has been final for a year); announce in the 0.3.0 notes that
   0.4.0 raises `requires-python` to `>= 3.11`, drops the `tomli` extra and
   lets `UP` modernise the syntax 3.10 held back. 3.10 is end-of-life this
   month; a linter that reads other repositories' CI should not test on an
   interpreter that no longer receives security fixes.
7. **Container hardening.** A non-root `USER` in the `Dockerfile`, the base
   image pinned by digest with a `docker` ecosystem entry in
   `dependabot.yml` keeping it fresh, and the base version tied to the same
   single source as item 4.

*Proof:* CI green on every merge; `make thresholds` still passes; the new
`tests/test_workflow_hardening.py` tests fail on an unpinned `uses:` or a
job without a timeout; `test_dockerfile` (new, beside the existing Docker tests if any)
fails on a root user or a tag-only base.

### W2 — God-file reduction, phase two: `cli.py`

*Baseline:* 1029 lines, `build_parser` 148, `cmd_validate` 119 (complexity
14), `cmd_report` 84 (12), `cmd_delta` 66; 81 `print` calls.

Shape: `openspec_graph/cli/` as a package — `__init__.py` re-exports every
name tests import today (`main`, `main_deprecated`, `build_parser`,
`_version_string`, `SEVERITY_ORDER`), and a `cli/__main__.py` is part of the
shape from the first commit, because `python -m openspec_graph.cli` — the path
`tests/support.run_cli`, the golden-hash test and `test_planlint_module_runs`
all take — refuses a package without one; `parser.py` holds `build_parser`
decomposed into one `add_<verb>_parser` per verb; `commands/<verb>.py` holds
each `cmd_<verb>`; `output.py` holds the shared print/JSON helpers (which is
where the ten `json.dumps` sites meet W5's single `dumps_stable`). The
`T201` exemption W4.2 grants to `openspec_graph/cli.py` moves with the code in
the same commit — `per-file-ignores` gains `openspec_graph/cli/*` (or
`cli/output.py` alone, if every print lands there) and drops `cli.py`, and
`test_t201_is_selected_with_exactly_the_cli_and_tools_exempt` is pointed at
the new path — or the pure move fails `make lint` on its own.
`decompose-god-files` R-DG-6 is superseded explicitly; its guard keeps its
*name* — AC-DG-8 cites `pytest -k detect_and_cli_remain_unsplit`, and
`test_spec_test_citations` fails on an unresolved selector — and narrows its
body to `detect.py`. Three sibling guards would miss a nested module
(`c4.md` warns of exactly this): `test_only_detect_imports_subprocess` and
`test_import_boundary_discipline` glob `openspec_graph/*.py` non-recursively
and switch to `rglob` with a path-based exemption; `test_new_modules_stdlib_only`
does not glob at all — it iterates a `_NEW_MODULES` name list and builds
`PKG / f"{name}.py"` (`tests/test_decomposition.py:263–266`) — so it gains the
package's modules by path (a walk of `openspec_graph/cli/`, or the list
rewritten as relative paths) in the same commit. Otherwise a
`cli/commands/x.py` importing `subprocess`, `graph` or a third-party module
would be invisible to all three. `docs/architecture/c4.md` names `cli.py` in three places.

*Proof (guardrail 5):* test-name set identical; golden hashes unmoved; a new
`test_cli_help_byte_identical` snapshot taken *before* the move and asserted
after; the three guards recursive and green on the new layout.

Phase three candidates, each its own package and only once W2 has landed:
`parse_semantics.py` (764 — `hard_coded` and the SpecKit section readers are
separable), `detect.py` (758 — discovery of files vs. profiling of a stack; the
`StackProfile` aggregate stays whole), `report.py` (590 — the step-summary
renderer is a projection like `sarif.py` and can live beside it).

### W3 — Complexity and length, by ratchet

*Baseline:* 7 functions over complexity 10 (max 15); 15 over 60 lines;
3 with 6 parameters.

1. Configure `[tool.ruff.lint.mccabe] max-complexity = 15` and
   `[tool.ruff.lint.pylint] max-branches`, `max-statements`, `max-args` at
   today's maxima, and select `C901`, `PLR0912`, `PLR0915`, `PLR0913` — zero
   violations on day one (guardrail 4). Ruff's defaults are 10, 12, 50 and 5
   (Appendix B); the ratchet ends there.
2. Reduce case by case, in the order the W2 split already touches:
   `cmd_validate` and `cmd_report` fall out of W2; `parse_makefile` (15)
   splits its recipe/target/define states into one helper per state;
   `build_delta` (14) and `find_threshold`/`scoped_fail_under` (12/11) extract
   their per-source branches; `witness._load_one` (11) moves its field checks
   into a `_validate_record` that returns the reason string.
3. `graph.py`'s three 6-argument functions take one `GraphBuild` dataclass.
4. Lower each limit as the last offender above it is fixed. Target: ruff
   defaults, `C901` at 10.

*Proof:* golden hashes unmoved (every function above is on a byte-stable
output path); `make matcher-accuracy` unchanged; coverage floors hold.

### W4 — Hard-coded values and configuration

1. Name the five `PLR2004` values: `COVERAGE_PERCENT_MAX = 100.0` beside
   `THRESHOLD_MAX` in `thresholds.py` (the CLI then imports it); the two
   path-depth constants in `detect.py` as named layout facts
   (`SPECKIT_FEATURE_DEPTH`, `OPENSPEC_CHANGE_DEPTH`) next to the discovery
   docstrings that already explain them; the two argv lengths in `tools/`
   disappear when those scripts adopt `_common`'s argparse pattern (W5).
   Then select `PLR2004`.
2. Select `T201` with per-file-ignores for `cli.py` and `tools/*` — it is
   already at zero elsewhere, so the rule costs nothing and prevents a print
   from entering a library module.
3. Select `FBT001`/`FBT002` after making the three boolean parameters
   keyword-only — additive, verified: every caller outside `log.py` already
   passes them by name (§1.2), and the one positional call is internal.
4. The E501 rewrap (`next-steps.md` item 18), in two PRs: package + tools
   (37 lines), then tests (110). Select `E501` after the second.
5. `PERF401`: the twelve append-loops become comprehensions; select `PERF`.
6. Configuration literals in workflows: W1 item 4.

*Proof:* each selected family is a one-line pyproject change whose CI run is
the proof; `make thresholds` extended to assert the new families stay
selected (a config that silently drops a family is how debt returns).

### W5 — Dead, redundant and drifting code

1. Remove `precision_pct` and `recall_pct` (zero references, internal).
   `Criterion.has_selector` is on a dataclass re-exported from
   `openspec_graph.parse` and the package root, so under guardrail 1 it is
   not removed in a minor: it stays through 0.3.x with a `DeprecationWarning`
   and a CHANGELOG `Deprecated` line, and goes in the announced 0.4.0 break
   alongside Python 3.10.
2. Decide the four test-only helpers: `filter_speckit_by_feature` stays
   public (it is a discovery primitive a consumer may want). The three
   `parse_semantics` section readers carry public names (and `suppressions`
   documents its behaviour as unchanged), and `STATUSES`, `STATUS_ERROR` and
   `FindingRecord` are declared in `report.__all__`; an internal reference
   count cannot show that no adopter imports them, so none is privatised or
   removed in a minor (guardrail 1). Each gets a private implementation with
   the public name kept as a deprecation alias through 0.3.x (warning once;
   CHANGELOG `Deprecated`), the tests move to the behaviour they exercise,
   and the aliases go and `report.__all__` is trimmed in 0.4.0.
3. `openspec_graph/_json.py`: one `dumps_stable(obj, *, indent)` — **not**
   sorting keys. The golden-hash test re-serialises each parsed payload in
   insertion order (`test_decomposition.py:130–137`), so `sort_keys=True`
   would move all three hashes, lose SARIF's conventional `$schema`,
   `version`, `runs` order and churn every adopter's envelope diff: a
   byte-contract change, not hygiene. The helper's value is one import point
   for `indent`/`ensure_ascii` and the guard; key order is asserted by a test,
   not imposed. `witness.py`'s sorted compact form stays the one sorted
   variant (its bytes are hashed). Guard: no module calls `json.dumps`
   directly except `_json.py` and `witness.py`.
4. `tools/diff_spec_graph.py` and `tools/render_mermaid.py` adopt
   `_common` (argparse, `repo_root`, logger); this also clears the two
   strict-mypy errors and two magic values.
5. `make dead-code`: vulture at ≥ 80% confidence over `openspec_graph` and
   `tools` with a checked-in whitelist, a *report* target (`DEC-PM-011`);
   gate it only if a quarter passes with zero findings. vulture is a dev
   extra, not a runtime dependency.
6. `spec-adversary`'s remit grows to tool modules: "does this tool credit,
   count or report anything it cannot see?" — the question R1 was answered by
   three times.

### W6 — Hardening: types, logging, inputs

1. `[tool.mypy] strict = true` (Appendix B lists what it enables); the two
   `type-arg` errors are fixed in W5 item 4. Keep `warn_unreachable = true`
   explicitly — `--strict` does not include it.
2. A logger for `scaffold.py` as a `planlint.scaffold` child, DEBUG for
   every file it creates, plus one line in `cli._load_card` for the baseline
   read. Same pattern and tests as the witness logging landed in #36.
   (`ledger.py` and `delta.py` are pure; nothing to log.)
3. A separate `make audit` report running `pip-audit` against the dev
   extras — not inside `make security`, which is a pre-commit hook and a
   `pre-pr` step and must not depend on a tool that may be absent
   (guardrail 7). The runtime surface has nothing to audit.
4. Inputs: `parse_makefile` already has its never-raises and determinism
   properties (`tests/test_properties.py:88,107`). Add the same shape for
   `shell_invocations` (a `tools/` function, loaded through
   `support.load_tool`, measured by the tools floors) and for
   `witness._load_one`: never raises, never credits or accepts on garbage.
5. **Tests under mypy.** Add `tests` to `[tool.mypy] files` with
   `explicit_package_bases = true` (the module-mapping error) and a
   `[[tool.mypy.overrides]] module = "tests.*"` block. A lenient block
   cannot be `disallow_untyped_defs = false` alone: that only excuses missing
   annotations, while the ~52 measured errors are `arg-type`,
   `no-any-return`, `index`, `union-attr` and `str`, all still enabled under
   global `strict`, and `check_untyped_defs` keeps checking bodies — adding
   `tests` that way is red on day one. The ratchet is a baseline instead:
   the override starts with `disable_error_code` listing exactly the five
   measured codes (green on day one, every *other* code enforced from the
   first day), each code is re-enabled in its own commit once its
   occurrences are fixed, and the first commit records the per-code counts so
   the list only shrinks. Fixing all 52 in one sitting is the alternative if
   it proves cheaper than the baseline. The 34
   unresolved `pytest`/`hypothesis` imports are this container's stub path,
   not the code; CI's `[dev]` install resolves them. Until this lands, a
   typo in a test helper's signature is found by the test run, not before.
6. **Public docstrings by ratchet.** Select `D100`–`D103` with the 52
   current offenders listed in `per-file-ignores`, and shrink the list in
   the W2/W3 PRs that already touch those files; the `D` convention is
   whatever the existing docstrings already follow (they are consistent).

### W7 — Coverage and the test suite

1. **Ratchet the floors** — after W7.2, and against the *minimum leg*, not
   this container. Today the tools floors run once on ubuntu/3.12; after
   W7.2 both floors run on every leg, including Windows (where capability
   probes skip tests) and 3.10, and floors are integers. So: one run that
   uploads `coverage.json` from every leg, floors set two points under the
   lowest leg (expected near package 97 / 95, `tools/` 94 / 91 — the tools
   number already drifted a point between the 2026-10 review and today),
   per-leg figures recorded in the package. Floors live in `pyproject.toml`
   only (`make thresholds` already guards that).
2. **One suite run for both trees — proven, with one precondition.** A
   single run measuring both trees into one report (`combined.json`,
   Appendix A) reproduces the two-run numbers *exactly* when summed per
   scope: `openspec_graph/` 2276/2292 lines and 744/762 branches,
   `tools/` 823/857 and 278/298. Its unscoped `totals` are the diluted
   figure the Makefile warned about, 3099/3149 = 98.4 % — and today's
   checkers behave accordingly: `--scope tools` passes against the combined
   report unchanged; the *unscoped* call (which is how `make test` checks the
   package floor) reads the combined totals; `--scope openspec_graph` exits 2,
   "no line floor set … `openspec_graph_line_fail_under`", because no scoped
   key exists for the package. So the design is: `[tool.coverage.run]
   source = ["openspec_graph", "tools"]` and a bare `--cov` (pytest-cov
   overrides `source` when `--cov=x` is given, Appendix B), pytest-cov's own
   `--cov-fail-under` — a *total*, Appendix B — set to `$(NO_FLOOR)`, and one
   mapping rule in `_common._read_floor`: a scope that names an entry of
   `[tool.coverage.run] source` falls back to `[tool.coverage.report]
   fail_under` / `[tool.specgraph] branch_fail_under`, so the thresholds stay
   in one place and both floors are read scoped. `coverage-tools` keeps its
   name as a documented stage and *depends on* the combined-coverage
   producing target before running the two `--scope tools` checks: a
   standalone `make coverage-tools` on a clean checkout must produce the
   report, not read a missing or stale one, and Make deduplicates `test`
   inside `pre-pr`, so the ladder still runs the suite once. Saves one full
   suite run per
   ladder and one CI job; the subprocess measurement through
   `COVERAGE_PROCESS_START` then covers `tools/` scripts too.

   **This reverses recorded requirements, and says so.** `gate-tools-coverage`
   (shipped; header still DRAFT) requires the opposite: R-GTC-9 ("`make
   coverage-tools` MUST be its own coverage run"), C-GTC-4 ("`make test` MUST
   keep measuring the package alone. No `--cov=tools` may be added to it"),
   R-GTC-12 (its own CI job with a `docs/hooks.md` row), DEC-GTC-009 and
   DEC-GTC-013, verified by AC-GTC-17 through
   `test_hooks_ci_table_lists_every_ci_job`. Those were right when
   pytest-cov's total was the only floor; the scoped checkers make them
   unnecessary. The W7 package names the five as superseded, records the
   reversing decision with this reason, and lists what it edits: `Makefile`
   (`test`, `coverage-tools`), `ci.yml` (the job), `docs/hooks.md` (row and
   paragraph), `docs/architecture/c4.md` (§2, §4b), `tests/AGENTS.md`,
   `pyproject.toml` (the comment), `tools/_common.py` (`_read_floor`'s
   mapping rule, for the line and the branch floor alike),
   `tools/check_coverage_floor.py` and `tools/check_branch_coverage.py`
   (reading the mapped floor) with their contract tests in
   `tests/test_ci_hardening.py` and `tests/test_gate_scripts.py`, and the
   hooks-table test. One sequencing
   constraint: `add-witness-ci-artifacts` lists `coverage-tools` as a
   witnessed stage three times, so W7.2 lands after R7 and re-runs
   `make stage-citations`, or amends R7's stage list in the same package.
3. **Per-file minimum** as a report first: `check_coverage_floor.py
   --per-file-min 85` lists modules below (coverage.py's `fail_under` is a
   total, Appendix B); gate when the list is empty.
4. **Suite hygiene:** split the four 700+-line test modules by concern
   (`test_ci_hardening` → workflow / action / makefile); register markers
   (`unit`, `integration`, `e2e`) in `pyproject.toml` and apply them, so a
   fast `-m unit` loop exists for the hook ladder without changing the
   directory topology #35 fixed; route those of the 16 helper-less modules
   that duplicate `run_cli`/`write_spec` shapes through `tests/support.py`
   (several have nothing to route).
5. **Parallelism — measured.** `pytest-xdist` with four workers on this
   four-core container runs the suite in **66 s against 235 s**
   single-process (3.6×), with every test passing — so no test-order or
   shared-state dependence surfaced on the first parallel run.
   `[tool.coverage.run] parallel = true` is already set, so coverage data
   from workers combines. Two notes for the package: the parallel run
   reported 1500 passed where the serial run reports 1498 — two tests
   behave differently by process context and must be understood, not
   averaged away; and the hosted runners have fewer cores than this
   container, so the matrix legs should be re-measured there before the
   dev extra is added.
6. **In-process loops.** The tests the durations table names —
   `test_projections_are_byte_stable_across_runs`,
   `test_an_unprojectable_file_exits_two_with_an_empty_stdout` (×3),
   `test_sarif_returns_the_same_exit_code_as_the_text_run`,
   `test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict` —
   loop over `run_cli` where the property under test is the *output*. Each
   keeps one subprocess as the entry-point check and runs the loop through
   `cli.main` with `capsys`. Rule: where the process boundary *is* the
   property (encoding, ambient coverage files, the real wheel, the composite
   action), nothing changes. Target: the Appendix A durations command from
   235 s to ≤ 200 s single-process on this container.

### W8 — Enterprise organisation

1. **Package layout, phase three** (after W2): `openspec_graph/{parse,
   rules, detect, output, cli}` subpackages with the flat module names kept as
   facades for one minor version — exactly the pattern `parse.py` and
   `rules.py` already follow.
2. **Archive implemented change packages — after planlint learns to.**
   The motivation is navigability: 43 packages in one directory, three of
   them open. It is not gate cost (`validate` takes 0.36 s). And today the
   OpenSpec `archive/` convention would do harm: `find_spec_files` reads
   only `changes/*/specs/*/spec.md`, so archived specs drop out of every
   gate silently, and `detect.py:710` would count `archive/` itself as a
   change package in `detect`'s report and the dialect card. So the
   precondition is a feature package, and it is larger than one glob:
   `profile()` must skip `archive/` in the package count; bare `--target
   openspec/changes/archive` exits 2 today (`profile()` resolves
   `root/openspec`), so validating the archive needs a flag or a synthetic
   `openspec/changes/<pkg>` tree in a scheduled job; OpenSpec's
   `archive/YYYY-MM-DD-<name>/` prefix would break `--change <name>`;
   `tests/test_spec_test_citations.py` and `tools/stage_citations.py` share
   the discovery, so archived specs would leave the citation gate and
   DEC-WCA-016's counts; and G006/G009 are whole-tree "cited by some living
   spec" rules that can newly fire once the citing specs move. The archive
   criterion is evidence — tasks complete and a CHANGELOG entry — never the
   `Status` header (§1.2: 18 headers say DRAFT, shipped packages among them).
   Only then are the implemented packages moved, one commit, with the
   before/after spec count and a G006/G009-clean `validate` asserted.
3. **Policies written down, once:** versioning and deprecation
   (`schema_version` bumps, the `specgraph` window), the count-cites-a-command
   rule (R2), the one-agent-per-thread convention (R3) — in
   `docs/agents-skills-harness.md` and `openspec/AGENTS.md`.
4. `CODEOWNERS` naming `openspec/`, `.github/`, `tools/` owners — low value
   with one maintainer, zero cost, useful the day a second arrives.
5. **Spec status hygiene.** `make spec-status`: a report (`DEC-PM-011`)
   listing each package's `Status` header beside its evidence (tasks
   complete? CHANGELOG entry? CI job present?), then one commit that sets the
   18 headers to what shipped — `openspec/AGENTS.md` already says the spec
   has to match what shipped. Gate it when the report has been empty for a
   quarter.
6. **Documents.** `docs/AGENTS.md` names `*-plan.md` and `peer-review-*.md`
   as "consumed and retired" by convention; five such plans are still in
   `docs/` — retire each with a one-line pointer to where its content landed
   (this document follows the `*-plan.md` naming for the same reason).
   `docs/architecture/c4.md` §4 omits `delta.py`; add it.
7. **Branch protection, stated.** M0's "CI green after each merge" and the
   Dependabot order assume merges wait for required checks. That is a
   repository setting, outside the tree; `docs/hooks.md` records which checks
   are required (`test (3.x)`, `test-windows`, `self-validate`, `security`,
   the coverage job or its W7.2 successor) so the assumption is visible.
8. **SBOM — deferred, with the reason.** Attestations (W1.5) cover
   provenance; a CycloneDX SBOM for a zero-dependency wheel lists one
   component. Revisit the day `[project] dependencies` is non-empty.

### W9 — Harness, hooks and skills

1. `next-steps.md` item 20, widened by R4: a SessionStart hook for cloud
   sessions that installs dev extras *and* verifies `commit.gpgsign` with a
   working signing program before the first commit; guarded on the remote
   environment; tested in `test_claude_hooks.py`.
2. `planlint-verifier` runs `make dead-code`, the `PLR2004`/`T201` families
   and `make stage-citations` and reports deltas, so a tool is reviewed by the
   same machinery as a spec (R1).
3. A `release` skill: CHANGELOG cut, version bump, tag, watch `release.yml`,
   verify the attestation.
4. The PostToolUse nudge gains an arm for `tools/*.py`: "run
   `make coverage-tools` (or its W7 successor) before finishing".

---

## 5. Sequencing

| Milestone | Scope | Gate to pass before the next |
|---|---|---|
| **M0 — Guard the green** (days) | W1.1 Dependabot batch; W1.3 permissions, timeouts, conditional concurrency; W1.6 Python 3.14 in the matrix; W1.7 container user; W4.2 `T201` scoped; W6.1 strict mypy (+ W5.4 tools adopt `_common`, proven by the gate-script tests in `test_ci_hardening.py`) | CI green on `main` after each merge; `tests/test_workflow_hardening.py` covers each workflow guard and `test_ci_hardening.py` the lint and typecheck ones (PR #38) |
| **M1 — Pin and release** (days) | W1.2 SHA pins; W1.5 release 0.3.0 with attestations and the 3.10 removal notice; W8.3 policies | tag published; `pip install planlint==0.3.0` runs `validate` on this repo |
| **M2 — Measure cheaper** (one week) | W7.2 one-run coverage (with the `_read_floor` rule and the GTC supersession), then W7.1 floors from the minimum leg; W7.3 per-file report; W7.6 in-process loops; W5.5 dead-code report; W8.5 spec-status report; W7.4 markers; W6.5 tests under mypy (lenient override); W6.6 `D1` ratchet config | ladder wall time down by the `coverage-tools` leg and the loop conversion; floors hold on every leg; scoped numbers equal the two-run numbers on the first run |
| **M3 — Split `cli.py`** (one week) | W2 with its proofs (`cli/__main__.py` in the first commit; the three guards recursive; AC-DG-8's test name kept); W3 items 1 and 3 (ratchet config, `GraphBuild`) | golden hashes, `--help` snapshot and test-name set unchanged |
| **M4 — Reduce** (two weeks, many small PRs) | W3.2 complexity; W4.1/3/5 constants, FBT, PERF; W5.1–3 dead code and `_json`; W6.2 loggers; W6.4 property tests; W4.4 rewrap ×2 | each lint family selected at its default when the last offender falls |
| **M5 — Organise** (after M4) | W8.1 subpackages; W8.2 archive; W2 phase three (`parse_semantics`, `detect`, `report`); W9 | facades keep every public import; archive validated on a schedule |

W9.1 (SessionStart hook) can land any time after M0; it blocks nothing.

M1 as landed (PR #39; `pin-actions-by-sha` and `write-down-policies`, with
`prepare-release-0-3-0` following in the same branch): the publisher is
pinned to the v1.14.2 commit, which was also the `release/v1` head at pinning
time, and its Docker payload still arrives through a registry tag named
after the SHA; the guard that forbade a SHA was deleted and
`harden-ci-workflows`' record amended in place because it was on the same
unmerged branch; the floor table gained a row for the publisher; Dependabot's
two action entries became one; and `github/codeql-action` has no bot-driven
refresh path under a SHA pin, accepted in writing. The policies live in
`docs/policies.md`, not in `docs/agents-skills-harness.md` and
`openspec/AGENTS.md` as W8.3 names them — those two files carry one-sentence
pointers — and the deprecation window is the one-minor minimum W1.5 and W5
already assume, so neither needs amending.

---

## 6. Decisions

- **D1 — Ratchet, not gate.** New lint limits are configured at today's
  maxima and lowered as code improves. *Alternative rejected:* select at
  defaults and carry a `# noqa` per offender — that turns the backlog into
  annotations nobody is asked to remove.
- **D2 — One coverage run, two scoped checks, both floors read scoped.**
  The Makefile's two-run design protected two honest numbers from one
  diluted total; the scoped checkers this repository already owns protect
  them from one data file — *provided* the package floor is also read
  scoped, which needs the one `_read_floor` mapping rule in W7.2, because the
  unscoped call reads the report's totals (measured: 98.4 % against 99.3 %).
  It supersedes R-GTC-9, C-GTC-4, R-GTC-12, DEC-GTC-009 and DEC-GTC-013 of
  `gate-tools-coverage`, by name, in the W7 package. *Rejected:* a third
  floor on the combined total (the diluted number the Makefile refused); a
  duplicate `openspec_graph_line_fail_under` key (two places for one
  threshold is how `make thresholds` came to exist).
- **D3 — `cli/` is a package, with `__init__` as the facade.** *Rejected:*
  sibling `cli_*.py` modules — they are what R-DG-6's guard was written to
  forbid, for the reason that a flat family of five `cli_` files is a god
  file with more filenames.
- **D4 — Dead-code detection is a report first.** vulture's confidence
  levels mean a gate at 60% would fail on `shlex` attribute assignments it
  cannot see; at 80% with a whitelist it is useful and quiet, and a quarter
  of quiet earns the gate.
- **D5 — SHA pins because Dependabot exists.** The deferral's stated
  precondition is met; a pin without an updater goes stale, a pin with one
  is the control.
- **D6 — Strict mypy now.** Two errors, both mechanical; the alternative is
  a config comment explaining why not, which costs more to read than the fix.
- **D7 — Floors move to two points under measured, not to measured.** A
  floor at the measured value fails on the first honest deletion of a tested
  branch; two points is the room a refactor needs without hiding a regression
  of real size.
- **D9 — A line budget is a report, not a gate.** `decompose-god-files`
  recorded as a non-success criterion that it "does not introduce a
  line-count gate … not a brittle threshold enforced in CI". The end state's
  "≤ 500" is therefore measured by `make module-sizes` and read in review,
  honouring that criterion and guardrail 7; a gate would need its own
  package reversing the criterion with a reason, and none is offered here.
- **D10 — `dumps_stable` does not sort keys.** Key order is part of the byte
  contract three golden hashes and every adopter diff depend on; stability
  comes from asserting the order, not imposing a different one. *Rejected:*
  `sort_keys=True` as hygiene (W5.3 explains the cost).
- **D8 — Phase three waits for phase two.** Splitting `detect.py` and
  `parse_semantics.py` before `cli.py` has moved would run two pure-move
  proofs through the same facades at once; one at a time keeps every golden
  hash's failure attributable.

---

## 7. End state the plan is accountable to

| Measure | Now | Target |
|---|---|---|
| Largest module | 1029 lines | ≤ 500, reported by `make module-sizes` (a report, not a gate — D9) |
| Functions > complexity 10 | 7 | 0, `C901` selected at 10 |
| Functions > 60 lines | 15 | ≤ 5, each with a comment saying why |
| `PLR2004`, `FBT001`, `PERF401`, `E501` (package + tools) | 5, 3, 12, 37 | 0, families selected |
| `print` outside `cli.py`/`tools/` | 0 (unenforced) | 0 (enforced) |
| mypy | pragmatic | `strict = true` |
| Coverage floors (package / tools) | 90/80 / 90/80 | 97/95 / 94/91, plus a per-file report |
| Full-suite runs per ladder / per PR | 2 / 6 | 1 / 5 |
| Suite wall time, single process → four workers | 235 s → 66 s (measured here) | the matrix legs run with `-n auto` once re-measured on the hosted runners |
| `ci.yml` jobs with a timeout / under a least-privilege token | 0 of 10 / 1 of 10 (`release.yml` is already top-level `contents: read`) | 10 of 10 / 10 of 10 |
| Third-party actions pinned by SHA | 0 of 6 | 6 of 6, updated by Dependabot |
| Open Dependabot PRs older than a week | 7 | 0 |
| File-writing modules without a logger | 1 (`scaffold.py`) | 0 |
| Suite wall time, single process (Appendix A command) | 235 s | ≤ 200 s after W7.6 |
| Spec headers disagreeing with their evidence | 18 of 44 say DRAFT, shipped packages among them | 0, reported by `make spec-status` |
| Unreferenced symbols | 3 | 0, with `make dead-code` reporting |
| Release | 0.2.0 + 355 unreleased lines | 0.3.0 tagged, attested, `specgraph` window stated |
| Python matrix | 3.10–3.13 | 3.11–3.14 at 0.4.0 (3.14 added now, 3.10 announced) |
| Tests under mypy | not checked (86 errors, ~52 real) | checked, overrides tightened to strict |
| Public symbols without a docstring | 52 | 0, `D100`–`D103` selected |
| Container | root user, tag-pinned base | non-root, digest-pinned, Dependabot-maintained |

---

## 8. Peer review of the plan

Two rounds before this document was offered for merge.

**Round 1 — self-verification** of every **[Likely]** marker (commands in
Appendix A): ten claims confirmed and de-marked; two overturned and rewritten
(D2's mechanism, W8.2's premise); five debts found missing and added (support
window, tests under mypy, docstrings, container, tool runtime); one
measurement replaced an assumption (xdist).

**Round 2 — an independent adversarial reviewer** read the plan against the
packages, tests and documents it touches and re-measured every baseline
figure (all reproduced except the errata below). Its findings and their
disposition:

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | HIGH | W7.2/D2 reverse R-GTC-9, C-GTC-4, R-GTC-12, DEC-GTC-009/013 of `gate-tools-coverage` without naming them; six documents and R7's stage list are touched | Accepted — W7.2 and D2 now name the five ids, the documents and the R7 sequencing |
| 2 | HIGH | W5.3's `sort_keys=True` moves all three golden hashes and SARIF's key order — a byte-contract change presented as hygiene | Accepted — `dumps_stable` does not sort; D10 records why |
| 3 | HIGH | `python -m openspec_graph.cli` breaks without `cli/__main__.py`; the re-exports tests import were unnamed | Accepted — in the shape and the proof |
| 4 | HIGH | `ledger.py`/`delta.py` do no I/O; the grep matched docstrings | Accepted — row, W6.2 and end state corrected to `scaffold.py` |
| 5 | HIGH | §1.3 assigned the subprocess-loop conversion to a W7.4 that had no such item | Accepted — W7.6 with tests, rule and a 235 → ≤ 200 s target |
| 6 | HIGH | Errata: 10 job definitions not 12; run #171 was 16 + skipped; test lines 17,366; 16 helper-less modules; "reach" 700; 18 DRAFT headers; an empty heredoc in Appendix A; the pin deferral lives in `next-steps.md:232` | Accepted — each corrected; the ast script is in Appendix A |
| 7 | MEDIUM | Floors measured on one Linux container would be enforced on five legs after W7.2 | Accepted — W7.1 sets floors from the minimum leg, after W7.2 |
| 8 | MEDIUM | Three `test_decomposition` guards glob non-recursively; AC-DG-8 cites the unsplit test by name; `c4.md` names `cli.py` thrice | Accepted — recursive guards, name kept, c4 edits listed |
| 9 | MEDIUM | "≤ 500 with a budget test" reverses `decompose-god-files` non-success 5 | Accepted — report, not gate (D9) |
| 10 | MEDIUM | W6.4's `parse_makefile` property already exists; `shell_invocations` is a tool | Accepted — rewritten |
| 11 | MEDIUM | Support window and `mypy` on `tests/` omitted | Already added in round 1 (W1.6, W6.5) |
| 12 | MEDIUM | W4.3's "every caller by name" false at `log.py:53` | Already corrected in round 1 |
| 13 | LOW | `vars.PYTHON_DEFAULT` is out-of-tree configuration | Accepted — workflow-level `env:` with tests |
| 14 | LOW | Pin guard must exempt the local action and the templates; `cancel-in-progress` must be conditional; timeouts from run durations; attestations default on; `release.yml` already least-privilege | Accepted — each folded into W1 and §7 |
| 15 | LOW | Omitted hygiene: evals wiring (`next-steps` item 16), version bump set, Dockerfile, SBOM, branch protection, performance baseline, docs sprawl, `c4.md` omits `delta.py`, the 0-vs-3 qualifier | Accepted — W1.5, W1.7, W8.6–8, §1.1/§1.2 qualifiers; the runtime baseline is in §1.2; evals' manual execution is recorded as deliberate (its README) and item 16 cited |
| 16 | LOW | `pip-audit` inside `make security` makes a gate environment-dependent | Accepted — `make audit` |
| 17 | LOW | A resolvable tag; "route the 13"; M0 bundles W5.4 without its tests | Accepted |

Verdict received: "ready with corrections — not mergeable as written"; the
three it insisted on (1, 2, 3+8) are applied above. Nothing was rejected: every
finding traced to a file and line, and the two the plan had already fixed were
confirmed independently.

---

## Appendix A — Commands behind the numbers

```
git rev-parse --short origin/main                               # 9c4b6e9
wc -l openspec_graph/*.py tools/*.py ; cat tests/test_*.py | wc -l
python - <<'PY'  # functions > 60 lines (15 of 266) over openspec_graph/ and tools/
import ast, pathlib
rows, total = [], 0
for d in ("openspec_graph", "tools"):
    for p in sorted(pathlib.Path(d).glob("*.py")):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += 1
                n = node.end_lineno - node.lineno + 1
                if n > 60:
                    rows.append((n, f"{p}:{node.lineno}", node.name))
print(len(rows), "of", total)
for row in sorted(rows, reverse=True):
    print(*row)
PY
grep -l "Status:\*\* DRAFT" openspec/changes/*/specs/*/spec.md | wc -l      # 18
awk '/^jobs:/{f=1;next} f&&/^  [a-z0-9_-]+:$/{n++} END{print n}' .github/workflows/ci.yml   # 10
ruff check --select C901 --config "lint.mccabe.max-complexity=10" --statistics openspec_graph tools
ruff check --select PLR0912,PLR0913,PLR0915,PLR2004,E501,T201,PERF401,FBT001,TRY003 --statistics openspec_graph tools
ruff check --select E501 --statistics tests
mypy --strict openspec_graph tools
python -m vulture openspec_graph tools --min-confidence 60
grep -nE "read_text\(|open\(|write_text\(|subprocess" openspec_graph/*.py   # read the hits: ledger.py:3 and delta.py:17-18 are docstrings
grep -c "json.dumps(" openspec_graph/*.py ; grep -c "sort_keys=True" openspec_graph/*.py
grep -hoE "uses: [^ ]+" .github/workflows/*.yml .github/actions/planlint/action.yml | sort | uniq -c
grep -c "timeout-minutes\|^permissions:\|^concurrency:" .github/workflows/ci.yml
make pre-pr                                                      # floors and measured coverage
python -m pytest tests/ -p no:cacheprovider -q --durations=12 -o addopts=""
# verification pass (§1.2 rows added in review)
python -m pytest tests/ --cov=openspec_graph --cov=tools --cov-branch --cov-fail-under=0 \
    --cov-report=json:combined.json -q           # then sum per-file summaries by prefix
python tools/check_coverage_floor.py combined.json --scope tools        # exit 0, 96.0%
python tools/check_coverage_floor.py combined.json                      # exit 0, 98.4% (combined)
python tools/check_coverage_floor.py combined.json --scope openspec_graph   # exit 2, no key
mypy --explicit-package-bases tests
ruff check --select D100,D101,D102,D103 --statistics openspec_graph
TIMEFORMAT='%R s'; time planlint --target . validate --fail-on ERROR
pip install pytest-xdist && time python -m pytest tests/ -p no:cacheprovider -q -n 4 -o addopts=""   # 66.8 s, 1500 passed
grep -n "def find_spec_files" -A 1 openspec_graph/detect.py ; sed -n 700,715p openspec_graph/detect.py
```

## Appendix B — References consulted (Context7, documentation only)

- **Ruff settings** (`docs.astral.sh/ruff/settings`): `[tool.ruff.lint.mccabe]
  max-complexity` (default 10, `C901`); `[tool.ruff.lint.pylint] max-branches`
  (12, `PLR0912`), `max-args` (5, `PLR0913`), `max-statements` (50,
  `PLR0915`). These defaults are the end of the W3 ratchet.
- **coverage.py configuration** (`coverage.readthedocs.io`, `config.rst`,
  `excluding.rst`): `[tool.coverage.report] fail_under` is a *total*
  percentage (exit 2 below it) — there is no per-file floor, which is why W7.3
  is a planlint-owned check; `exclude_also` preserves the default exclusion
  patterns where `exclude_lines` replaces them, so any new exclusion goes in
  `exclude_also`.
- **mypy strict mode** (`mypy.readthedocs.io`, `existing_code.html`,
  `command_line.html`): `strict = true` enables `warn_unused_configs`,
  `warn_redundant_casts`, `warn_unused_ignores`, `strict_equality`,
  `check_untyped_defs`, `disallow_subclassing_any`,
  `disallow_untyped_decorators`, `disallow_any_generics`,
  `disallow_untyped_calls`, `disallow_incomplete_defs`,
  `disallow_untyped_defs`, `no_implicit_reexport`, `warn_return_any`,
  `extra_checks`; it does **not** enable `warn_unreachable`, hence W6.1's
  explicit line. Per-module overrides use `[[tool.mypy.overrides]]`.
- **pytest-cov** (`docs/config.rst`): `--cov-fail-under MIN` fails "if the
  *total* coverage is less than MIN"; giving `--cov=something` overrides
  coverage's `source` option, and with several sources it is "easier to set
  those in the config and always use `--cov` without a value" — the shape
  W7.2 adopts.
- **PyPI attestations** (`docs.pypi.org/attestations/producing-attestations`,
  `trusted-publishers/using-a-publisher`): "for users of the official PyPA
  GitHub Action, attestations are generated and uploaded automatically by
  default without requiring additional configuration"; trusted publishing
  requires `id-token: write` on the publishing job, which `release.yml:99`
  already grants.
- **actions/upload-artifact** (`dist/upload/index.js`, `.github/workflows/
  test.yml`): the action's only credential is `ACTIONS_RUNTIME_TOKEN`
  (`getRuntimeToken()`), with no `GITHUB_TOKEN` in its auth path; its own
  test workflow nonetheless runs with `permissions: contents: read,
  actions: write`, which is why W1.3 proves the narrower grant on the first
  run rather than asserting it.
