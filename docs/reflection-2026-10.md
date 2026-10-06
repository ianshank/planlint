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
| CI on `main` | run #171 at `9c4b6e9`: 17/17 jobs success |
| Local ladder (`make pre-pr`) | exit 0; package 99.3% line (2276/2292), 97.6% branch (744/762); `tools/` 96.0% (823/857), 93.3% (278/298) |
| Spec gate | 44 specs, 0 error / 0 warn / 0 info |
| Tests | 1498 collected, all passing; 43 modules, 17,850 lines |
| Static | ruff (selected families) clean; mypy clean on 43 files; `mypy --strict` is **2 errors** away (`tools/diff_spec_graph.py:20,24`, both `type-arg`) |
| Dependencies | `[project] dependencies = []`, pinned by test; dev extras unpinned by decision |
| Security | gitleaks in CI, fallback scanner locally; ruff `S` family on; the only subprocess is `git rev-parse` with a named timeout |
| Dead public code | 0 of 405 top-level symbols is unreferenced repository-wide |

### 1.2 Debt, measured

| Dimension | Baseline at `9c4b6e9` | Note |
|---|---|---|
| Largest modules | `cli.py` 1029, `parse_semantics.py` 764, `detect.py` 758, `report.py` 590, `graph.py` 355, `thresholds.py` 305 (of 30 modules, 6,956 lines) | `decompose-god-files` split `parse.py`/`rules.py` and left `detect.py`/`cli.py` intact by decision (R-DG-6, pinned by `test_detect_and_cli_remain_unsplit`) |
| Functions > 60 lines | 15 of 266: `build_parser` 148, `cmd_validate` 119, `build_delta` 107, `build_graph` 102, `to_sarif` 84, `cmd_report` 84, `parse_spec` 83, `find_threshold` 71, `parse_speckit` 71, `parse_makefile` 71, `scoped_fail_under` 68, `to_step_summary` 68, `hard_coded` 66, `cmd_delta` 66, `profile` 64 | |
| Complexity (`C901` > 10) | 7: `parse_makefile` 15, `cmd_validate` 14, `build_delta` 14, `cmd_report` 12, `find_threshold` 12, `scoped_fail_under` 11, `witness._load_one` 11 | `_load_one` is new since N8b counted six; the per-reason logging added a branch per skip |
| Wide signatures (`PLR0913` > 5 args) | 3, all in `graph.py` (`:99`, `:132`, `:151`, 6 args each) | same six parameters threaded three times |
| Magic values (`PLR2004`) | 5: `cli.py:809` `100.0`; `detect.py:606` `3`, `:633` `5` (path-depth arithmetic); `tools/diff_spec_graph.py:38` `3` and `tools/render_mermaid.py:26` `2` (argv lengths) | |
| Boolean positional parameters (`FBT001`) | 3: `log.py:28`, `log.py:46`, `scaffold.py:154` | |
| Line length (`E501` at 100) | 37 in package + tools, 110 in tests | `next-steps.md` item 18; a third count without a rewrap |
| `print` in library code (`T201`) | 123: 81 in `cli.py` (by design), 42 in `tools/` (scripts), **0** in any other package module | an invariant nothing enforces |
| Loops that are appends (`PERF401`) | 12 (`delta.py` 4, `parse_model.py` 2, `check_wheel_metadata.py` 2, four singles) | |
| Logging | 9 of 30 modules own a logger; three that do file I/O do not: `delta.py`, `ledger.py`, `scaffold.py` (the last one *writes*) | |
| Unused symbols | `parse_model.Criterion.has_selector` (0 refs); `matcher_accuracy.precision_pct` / `recall_pct` (0 refs); `report.__all__` exports `STATUSES`, `STATUS_ERROR`, `FindingRecord` that nothing imports | vulture at 60% confidence agrees and adds nothing real |
| Test-only public API | `detect.filter_speckit_by_feature`, `parse_semantics.section_body`, `speckit_section_body`, `suppressions` are called only by tests | public by accident or by intent — undecided |
| JSON determinism | 11 `json.dumps` call sites, one with `sort_keys=True` (`witness.py`); the other ten rely on insertion order | correct today, by construction rather than by contract |
| Tool-script drift | 2 of 12 scripts (`diff_spec_graph.py`, `render_mermaid.py`) bypass `tools/_common.py`; they also hold the two strict-mypy errors and two of the five magic values | |
| Workflow hardening | `ci.yml`: 12 jobs, **no** top-level `permissions`, one job-level block; `timeout-minutes` on 0 jobs; no `concurrency`; every third-party action pinned to a floating major tag (`checkout@v4` ×12, `setup-python@v5` ×12, `upload-artifact@v4` ×4, `download-artifact@v4`, `gitleaks-action@v2`) and `pypa/gh-action-pypi-publish@release/v1` to a **branch** | `distribution-plan.md` deferred SHA pinning "until Dependabot" — Dependabot has been on since September |
| Configuration literals | the Python version appears 10 times in `ci.yml` (one matrix list, nine `"3.12"` singles) and once in the `Dockerfile` (`python:3.12-slim`); nothing ties them together | `make thresholds` guards thresholds and tool pins, not this |
| Dependabot | 7 open PRs since 2026-09-19, all major bumps (`checkout` 4→7, `setup-python` 5→7, `upload-artifact` 4→7, `download-artifact` 4→8, `gitleaks-action` 2→3, two in the composite action), based on `c0540c4` — two merges behind; `mergeable_state: unknown` | the artifact pair must move together |
| Release | `CHANGELOG.md` `[Unreleased]` has grown to ~355 lines since 0.2.0 (2026-09-12); the `specgraph` alias is deprecated with no removal date | |
| Change packages | 43 under `openspec/changes/`, none archived; the gate reads all 44 specs on every run | OpenSpec's `archive/` convention is unused **[Likely: supported by discovery, to be verified by the package]** |
| Suite shape | 13 of 43 test modules import nothing from `tests/support.py`; 21 use no `parametrize`; no pytest markers are registered; the four largest modules exceed 700 lines | |
| Suite cost | the ladder runs the full suite **twice** (`test`, `coverage-tools`); CI runs it **six** times per pull request (four matrix legs, `test-windows`, `coverage-tools`) | durations below |

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
| `test_the_action_reports_each_fixtures_labelled_status[passing]` (test_action_contract) | 2.6 | the composite action through a module helper **[Likely: a shell subprocess]** |
| `test_an_unprojectable_file_exits_two_with_an_empty_stdout[an-array]` (test_report) | 2.4 | `run_cli`: one `report` subprocess per parametrised bad input |
| `test_an_unprojectable_file_exits_two_with_an_empty_stdout[not-json]` (test_report) | 2.3 | same |

The ten slowest account for ~39 s of 235, and nine of them cross a process
boundary on purpose: `tests/support.run_cli` is the *subprocess* path, kept
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

1. **Dependabot batch.** Rebase the seven PRs onto `main`; merge
   `upload-artifact` 4→7 and `download-artifact` 4→8 in one commit (the
   consumer and the producer must agree); `setup-python` 5→7 and
   `checkout` 4→7 next (Node 24 runtimes — GitHub-hosted runners qualify);
   `gitleaks-action` 2→3 last and alone (it is the `security` gate). The
   composite action's two bumps ride with their root-level twins. Each merge
   is one CI run; `action-contract` already asserts the composite action end
   to end.
2. **SHA-pin every third-party action** with the version in a trailing
   comment (`uses: actions/checkout@<sha> # v7.0.1`), and pin
   `pypa/gh-action-pypi-publish` to a tag SHA instead of `release/v1`.
   Dependabot keeps SHAs fresh; this closes `distribution-plan.md`'s deferral
   on its own terms. Guard: a `test_ci_hardening` test that every `uses:` is a
   40-hex ref with a version comment.
3. **Least privilege and bounded runs.** Top-level `permissions: contents:
   read` in `ci.yml` with job-level widening only where needed (`graph-diff`
   and `self-validate` upload artifacts — `actions: none` suffices for
   `upload-artifact`; **[Likely]**, the package checks); `timeout-minutes` on
   every job (sized from the durations table: the longest job today is the
   Windows test leg); `concurrency: { group: ci-${{ github.ref }},
   cancel-in-progress: true }` for pull-request runs. Guard: tests for each
   in `test_ci_hardening.py`, which already parses the workflow.
4. **One Python version, one place.** The nine `"3.12"` singles and the
   Dockerfile's `3.12-slim` become one value: a `PYTHON_DEFAULT` repository
   variable read as `${{ vars.PYTHON_DEFAULT }}` with the Dockerfile `ARG`
   defaulting to the same string, and a test that the Dockerfile's version is
   a member of the CI matrix. (GitHub Actions has no YAML anchors; a reusable
   workflow is heavier than this repository needs.)
5. **Release 0.3.0.** Cut the ~355 `[Unreleased]` lines into a release
   section; tag; let `release.yml` publish; add PyPI attestations
   (`attestations: true` on the publish step **[Likely: supported by
   `release/v1`; verify]**). State the deprecation window for `specgraph`:
   warns through 0.3.x, removed in 0.4.0.

*Proof:* CI green on every merge; `make thresholds` still passes; the new
`test_ci_hardening` tests fail on an unpinned `uses:` or a job without a
timeout.

### W2 — God-file reduction, phase two: `cli.py`

*Baseline:* 1029 lines, `build_parser` 148, `cmd_validate` 119 (complexity
14), `cmd_report` 84 (12), `cmd_delta` 66; 81 `print` calls.

Shape: `openspec_graph/cli/` as a package — `__init__.py` keeps `main`,
`main_deprecated` and every name tests import today (so `from openspec_graph
import cli` and `python -m openspec_graph.cli` are unchanged);
`parser.py` holds `build_parser` decomposed into one `add_<verb>_parser` per
verb; `commands/<verb>.py` holds each `cmd_<verb>`; `output.py` holds the
shared print/JSON helpers (which is where the ten `json.dumps` sites meet W5's
single `dumps_stable`). `decompose-god-files` R-DG-6 and its guard
`test_detect_and_cli_remain_unsplit` are superseded explicitly by the new
package (the guard is replaced, not deleted, by a boundary test for the new
layout).

*Proof (guardrail 5):* test-name set identical; golden hashes unmoved; a new
`test_cli_help_byte_identical` snapshot taken *before* the move and asserted
after; `test_import_boundary_discipline` extended to the subpackage.

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
   keyword-only (additive: every current caller already passes them by name
   **[Likely; the package verifies by grep]**).
4. The E501 rewrap (`next-steps.md` item 18), in two PRs: package + tools
   (37 lines), then tests (110). Select `E501` after the second.
5. `PERF401`: the twelve append-loops become comprehensions; select `PERF`.
6. Configuration literals in workflows: W1 item 4.

*Proof:* each selected family is a one-line pyproject change whose CI run is
the proof; `make thresholds` extended to assert the new families stay
selected (a config that silently drops a family is how debt returns).

### W5 — Dead, redundant and drifting code

1. Remove `Criterion.has_selector`, `precision_pct`, `recall_pct` (zero
   references; a CHANGELOG line each since `has_selector` is on a public
   dataclass).
2. Decide the four test-only helpers: `filter_speckit_by_feature` stays
   public (it is a discovery primitive a consumer may want); the three
   `parse_semantics` section readers become private, with the tests moved to
   the behaviour they exercise. Trim `report.__all__` to what is imported.
3. `openspec_graph/_json.py`: one `dumps_stable(obj, *, indent)` with
   `sort_keys=True`, used by every machine-readable output; `witness.py`'s
   compact form stays its own (its bytes are hashed). Guard: a test that no
   module calls `json.dumps` directly except `_json.py` and `witness.py`.
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
2. Loggers for `delta.py`, `ledger.py`, `scaffold.py` as `planlint.<module>`
   children, DEBUG on every file read and write; `scaffold` names each file it
   creates. Same pattern and tests as the witness logging landed in #36.
3. A `make security` that also runs `pip-audit` against the dev extras when
   available (report, not gate: the runtime surface has nothing to audit).
4. Inputs: the three readers of untrusted text (`witness` store, `run:`
   scripts, target-repo Makefiles) each already fail closed; add the
   `hypothesis` property tests the repository already depends on for
   `shell_invocations` and `parse_makefile` (never raises, never credits on
   garbage).

### W7 — Coverage and the test suite

1. **Ratchet the floors** to two points under measured: package 97 / 95,
   `tools/` 94 / 91. Floors live in `pyproject.toml` only (`make thresholds`
   already guards that).
2. **One suite run for both trees.** `make test` measures `--cov=openspec_graph
   --cov=tools` into one `coverage.json`; `check_coverage_floor.py --scope`
   and `check_branch_coverage.py --scope` read the two trees from it; the
   `coverage-tools` target becomes an alias of those two checks. The
   Makefile's objection — a diluted combined total — never arises because
   pytest-cov's `--cov-fail-under` is set to 0 and the scoped checkers hold the
   floors. Saves one full suite run per ladder and one CI job.
3. **Per-file minimum** as a report first: `check_coverage_floor.py
   --per-file-min 85` lists modules below (coverage.py's `fail_under` is a
   total, Appendix B); gate when the list is empty.
4. **Suite hygiene:** split the four 700+-line test modules by concern
   (`test_ci_hardening` → workflow / action / makefile); register markers
   (`unit`, `integration`, `e2e`) in `pyproject.toml` and apply them, so a
   fast `-m unit` loop exists for the hook ladder without changing the
   directory topology #35 fixed; route the 13 helper-less modules through
   `tests/support.py` where they duplicate `run_cli`/`write_spec` shapes.
5. **Parallelism:** `pytest-xdist` as a dev extra for the matrix legs
   (`[tool.coverage.run] parallel = true` is already set, so data combines);
   measure first with the durations table, adopt only if a leg drops by a
   third **[Likely]**.

### W8 — Enterprise organisation

1. **Package layout, phase three** (after W2): `openspec_graph/{parse,
   rules, detect, output, cli}` subpackages with the flat module names kept as
   facades for one minor version — exactly the pattern `parse.py` and
   `rules.py` already follow.
2. **Archive implemented change packages** under `openspec/changes/archive/`
   per OpenSpec convention, so `openspec/changes/` lists the open work (3
   DRAFT packages today) and the gate reads the active set; the archive stays
   validated by `--target` in a scheduled job. Precondition: a package proving
   `detect`/`find_spec_files` handles the archive directory the way the
   convention expects.
3. **Policies written down, once:** versioning and deprecation
   (`schema_version` bumps, the `specgraph` window), the count-cites-a-command
   rule (R2), the one-agent-per-thread convention (R3) — in
   `docs/agents-skills-harness.md` and `openspec/AGENTS.md`.
4. `CODEOWNERS` naming `openspec/`, `.github/`, `tools/` owners — low value
   with one maintainer, zero cost, useful the day a second arrives.

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
| **M0 — Guard the green** (days) | W1.1 Dependabot batch; W1.3 permissions, timeouts, concurrency; W4.2 `T201` scoped; W6.1 strict mypy (+ W5.4 tools adopt `_common`) | CI green on `main` after each merge; `test_ci_hardening` covers each new guard |
| **M1 — Pin and release** (days) | W1.2 SHA pins; W1.5 release 0.3.0 with attestations; W8.3 policies | tag published; `pip install planlint==0.3.0` runs `validate` on this repo |
| **M2 — Measure cheaper** (one week) | W7.2 one-run coverage; W7.1 floor ratchet; W7.3 per-file report; W5.5 dead-code report; W7.4 markers | ladder wall time down by the `coverage-tools` leg; floors hold |
| **M3 — Split `cli.py`** (one week) | W2 with its proofs; W3 items 1 and 3 (ratchet config, `GraphBuild`) | golden hashes, `--help` snapshot and test-name set unchanged |
| **M4 — Reduce** (two weeks, many small PRs) | W3.2 complexity; W4.1/3/5 constants, FBT, PERF; W5.1–3 dead code and `_json`; W6.2 loggers; W6.4 property tests; W4.4 rewrap ×2 | each lint family selected at its default when the last offender falls |
| **M5 — Organise** (after M4) | W8.1 subpackages; W8.2 archive; W2 phase three (`parse_semantics`, `detect`, `report`); W9 | facades keep every public import; archive validated on a schedule |

W9.1 (SessionStart hook) can land any time after M0; it blocks nothing.

---

## 6. Decisions

- **D1 — Ratchet, not gate.** New lint limits are configured at today's
  maxima and lowered as code improves. *Alternative rejected:* select at
  defaults and carry a `# noqa` per offender — that turns the backlog into
  annotations nobody is asked to remove.
- **D2 — One coverage run, two scoped checks.** The Makefile's two-run design
  protected two honest numbers from one diluted total; the scoped checkers
  this repository already owns protect them from one data file. *Rejected:*
  a third floor on the combined total (the diluted number the Makefile
  refused).
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
- **D8 — Phase three waits for phase two.** Splitting `detect.py` and
  `parse_semantics.py` before `cli.py` has moved would run two pure-move
  proofs through the same facades at once; one at a time keeps every golden
  hash's failure attributable.

---

## 7. End state the plan is accountable to

| Measure | Now | Target |
|---|---|---|
| Largest module | 1029 lines | ≤ 500, with a budget test |
| Functions > complexity 10 | 7 | 0, `C901` selected at 10 |
| Functions > 60 lines | 15 | ≤ 5, each with a comment saying why |
| `PLR2004`, `FBT001`, `PERF401`, `E501` (package + tools) | 5, 3, 12, 37 | 0, families selected |
| `print` outside `cli.py`/`tools/` | 0 (unenforced) | 0 (enforced) |
| mypy | pragmatic | `strict = true` |
| Coverage floors (package / tools) | 90/80 / 90/80 | 97/95 / 94/91, plus a per-file report |
| Full-suite runs per ladder / per PR | 2 / 6 | 1 / 5 |
| Workflow jobs with timeout / least-privilege token | 0 / 1 | all / all |
| Third-party actions pinned by SHA | 0 of 6 | 6 of 6, updated by Dependabot |
| Open Dependabot PRs older than a week | 7 | 0 |
| I/O modules without a logger | 3 | 0 |
| Unreferenced symbols | 3 | 0, with `make dead-code` reporting |
| Release | 0.2.0 + 355 unreleased lines | 0.3.0 tagged, attested, `specgraph` window stated |

---

## Appendix A — Commands behind the numbers

```
git rev-parse --short origin/main                               # 9c4b6e9
wc -l openspec_graph/*.py tools/*.py tests/*.py
python - <<'PY'  # functions > 60 lines, via ast over openspec_graph/ and tools/
PY
ruff check --select C901 --config "lint.mccabe.max-complexity=10" --statistics openspec_graph tools
ruff check --select PLR0912,PLR0913,PLR0915,PLR2004,E501,T201,PERF401,FBT001,TRY003 --statistics openspec_graph tools
ruff check --select E501 --statistics tests
mypy --strict openspec_graph tools
python -m vulture openspec_graph tools --min-confidence 60
grep -L getLogger $(grep -lE "read_text|open\(|subprocess|write_text|mkdir" openspec_graph/*.py)
grep -c "json.dumps(" openspec_graph/*.py ; grep -c "sort_keys=True" openspec_graph/*.py
grep -hoE "uses: [^ ]+" .github/workflows/*.yml .github/actions/planlint/action.yml | sort | uniq -c
grep -c "timeout-minutes\|^permissions:\|^concurrency:" .github/workflows/ci.yml
make pre-pr                                                      # floors and measured coverage
python -m pytest tests/ -p no:cacheprovider -q --durations=12 -o addopts=""
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
