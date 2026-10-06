# Spec: Zero-Cost Guards

> **Change:** `select-zero-cost-guards`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Three properties of this tree are true and unenforced. `print` appears in
`openspec_graph/cli.py` and in the scripts under `tools/` — where stdout is
the product — and nowhere else in the package, but nothing stops the next
helper module from printing. `mypy --strict` is two findings from clean, both
in one file, but the configured gate is the pragmatic subset
`post-merge-quality-review` chose when the strict run had more to say. And
two scripts under `tools/` hand-roll their argument handling and file reads
instead of using `tools/_common.py`, which is why those two findings exist
and why the two scripts are the only ones in the directory that log nothing.

A property the gates do not enforce is a property a reviewer has to re-check
by hand on every pull request. The configuration this spec adds is at zero
violations after its own edits — it locks in what is already true, and
starts no backlog. That is the ratchet-then-gate posture: families with a
backlog are measured and reduced first and selected only when they reach
zero; families already at zero are selected now, because the cost of turning
them on is the cost of editing one table.

**Evidence:** measured at the drafting commit (`9c4b6e9`).
`python -m ruff check --select T201 --statistics openspec_graph tools` reports
123 findings — 80 in `openspec_graph/cli.py`, 43 under `tools/`, none in any
other `openspec_graph` module — and the same scan over `tests/`, which
`make lint` also covers, reports two in `tests/test_decomposition.py`'s
`test_output_byte_identical`. `python -m mypy --strict openspec_graph tools`
reports exactly two `[type-arg]` errors, `tools/diff_spec_graph.py:20` and
`:24`, and `--warn-unreachable` adds none; `python -m mypy --help` lists the
flags `--strict` enables and `--warn-unreachable` is not among them.
`tools/diff_spec_graph.py` and `tools/render_mermaid.py` are the only
scripts under `tools/` that do not import `_common`; both compare `len(argv)`
to a literal (`diff_spec_graph.py:38`, `render_mermaid.py:26`). Their
contracts are pinned by `tests/test_ci_hardening.py` and by
`.github/workflows/ci.yml:194`, which runs
`python tools/diff_spec_graph.py base.json head.json`. The `Makefile`'s
`graph-mermaid` target invokes the CLI, not the script; nothing in the
`Makefile` or the workflows invokes `render_mermaid.py`, so
`test_render_mermaid_matches_to_mermaid_byte_for_byte` is the whole of its
external contract.

---

## Requirements

- R-ZCG-1: `pyproject.toml`'s `[tool.ruff.lint] select` MUST include `T201`,
  and `[tool.ruff.lint.per-file-ignores]` MUST exempt exactly two paths from
  it: `openspec_graph/cli.py` and `tools/*`. No other per-file-ignores entry
  may name `T201`, and `make lint` MUST exit 0 on the tree after this
  change's edits.
- R-ZCG-2: A `print` call in any `openspec_graph` module other than
  `cli.py`, or anywhere under `tests/`, MUST fail `make lint`. The exemption
  is a statement about where stdout is the product, not a convenience.
- C-ZCG-1: The two diagnostic `print` calls in `test_output_byte_identical`
  MUST be folded into the assertion message that test already builds, so the
  per-verb dump still reaches the CI log on failure. This change MUST NOT
  add a `tests/*` exemption for `T201` and MUST NOT add a `noqa: T201`
  anywhere.
- R-ZCG-3: `[tool.mypy]` MUST set `strict = true` and
  `warn_unreachable = true`, and MUST keep `python_version = "3.10"` and
  `files = ["openspec_graph", "tools"]`. `make typecheck` MUST exit 0 on the
  tree after this change's edits.
- R-ZCG-4: A generic type without type arguments in any module under
  `openspec_graph/` or `tools/` MUST fail `make typecheck`. The two
  annotations in `tools/diff_spec_graph.py` MUST be fully parameterised
  rather than silenced.
- R-ZCG-5: `tools/diff_spec_graph.py` and `tools/render_mermaid.py` MUST
  import from `tools/_common.py` and MUST parse their arguments with
  `argparse`, declaring the same positional arguments they accept today —
  `base.json head.json` and `graph.json` respectively — and no new positional
  arguments. The only new accepted argument is argparse's own `-h`/`--help`;
  a `-`-prefixed token that was a filename before now exits 2 as a usage
  error (today it is a `FileNotFoundError` traceback).
  Each `main(argv)` MUST keep receiving `sys.argv` with the program name
  first and MUST strip it itself by parsing `argv[1:]`, as
  `matcher_accuracy.py` and `stage_citations.py` already do, so
  `run_tool_main`'s default `pass_argv0` and every existing caller are
  unchanged.
- R-ZCG-6: Exit codes MUST be preserved: 0 for a clean diff or a rendering,
  1 for a regression, 2 for a usage error. The usage error MUST be
  argparse's own `SystemExit(2)` with the usage text on stderr and nothing
  on stdout, and `--help` on each script MUST exit 0 with the usage text on
  stdout.
- R-ZCG-7: `render_mermaid.py`'s stdout MUST be byte-identical to
  `openspec_graph.mermaid.to_mermaid(graph)` with nothing appended, and
  `diff_spec_graph.py`'s `PASS:` and `FAIL:` stdout lines MUST be unchanged
  in wording and placement.
- R-ZCG-8: Both scripts MUST emit a DEBUG record on `_common.logger` for
  each file they read and for each decision they take — for the diff, the
  base and head `broken_links` and the number of new orphans; for the
  rendering, how many nodes and edges were rendered. Those records MUST go
  to stderr only, through the logger's existing handler, and MUST be silent
  at the default level, so stdout is byte-for-byte what it was.
- R-ZCG-9: `tools/_common.py` MUST gain `read_json(path)`, returning a fully
  parameterised mapping type and emitting the file-read DEBUG record, and
  MUST remain stdlib-only. It MUST read `path.read_text(encoding="utf-8")`
  directly — not through `read_text`, whose missing-file `""` would turn a
  clear `FileNotFoundError` into a `JSONDecodeError` — so a missing file
  still raises `FileNotFoundError` as today; and a document whose top level
  is not a mapping MUST raise `ValueError` naming the path, where today the
  caller fails later with a `TypeError` traceback.
- R-ZCG-10: Two guard tests in `tests/test_ci_hardening.py` MUST parse
  `pyproject.toml` structurally and assert, respectively, that `T201` is
  selected with exactly the two exemptions of R-ZCG-1, and that
  `[tool.mypy]` has `strict` and `warn_unreachable` both true. Neither test
  may duplicate the `select` list or any other configuration beyond the
  values it asserts.
- R-ZCG-11: Each configured gate MUST be shown to fire: a test MUST run ruff
  under this repository's own configuration against a planted `print` in a
  library-module path and assert it is reported there and not in a `cli.py`
  or `tools/` path, and a test MUST run mypy under this repository's own
  configuration against a planted bare `dict` annotation and assert a
  `type-arg` error.
- R-ZCG-12: The new argparse, help, error and logging paths in both scripts
  MUST be exercised in-process, so that `make coverage-tools` still meets
  `[tool.specgraph] tools_line_fail_under` and `tools_branch_fail_under`
  after this change.
- R-ZCG-13: The argv-convention grouping in `tests/support.py`'s
  `run_tool_main` docstring and in `tools/AGENTS.md` MUST be updated to
  reflect the move — the hand-rolled group shrinks by two and the
  argparse-strips-the-name group grows by two — as MUST
  `_common.parse_coverage_argv`'s docstring, which already miscounts ("the
  other eight scripts") — and `pyproject.toml`'s comment naming `T20` as
  unselected MUST be rewritten to state what is now true.
  (`gate-tools-coverage` R-GTC-4 carries the same stale count; it is a
  shipped package's record and is not edited here.)
- R-ZCG-14: Tests that assert records on the `planlint.tools` logger MUST
  attach `caplog.handler` to that logger directly, through one helper in
  `tests/support.py`, because `_common` sets `propagate = False` at import
  and pytest attaches its capture handler only to loggers that are already
  non-propagating when the test starts — a test that imports `_common` for
  the first time inside its own body sees no records. The existing
  `test_plugin_manifests_verbose_logs_without_polluting_stdout` MUST adopt
  the helper, so it passes in isolation (it fails under `-k` today).
- C-ZCG-2: This change MUST NOT select `C901`, `PLR`, `E501`, `FBT`, `PERF`,
  `D`, or any ruff family that has violations after this change's edits.
  Those are ratchets with a backlog; the two `PLR2004` findings clearing as a
  side effect does not make `PL` a zero-cost family.
- C-ZCG-3: No `make` target, workflow step or script invocation may change.
  `make lint` and `make typecheck` keep their recipes; the `graph-diff` job's
  step "Diff graphs (fail on new broken edges or orphans)" keeps its command
  line, `python tools/diff_spec_graph.py base.json head.json`; the `RULES`
  tuple, `README.md`'s rules table and `tests/baseline_rules.json` are
  untouched.

---

## Decisions

- **DEC-ZCG-001:** `T201` is selected, with `openspec_graph/cli.py` and
  `tools/*` exempted, rather than written down as a convention. A convention
  in a document is what the tree had — the pyproject comment said `print` is
  the product, and it was true of one file — and a convention that nothing
  checks is re-verified by a reviewer or not at all. The rule costs nothing
  today because the violation count outside the two exempt paths is zero;
  the moment a `print` lands in a parser or a rule module, `make lint` says
  so on every matrix leg. The exemption is a path, so when `cli.py` is
  decomposed (`docs/next-steps.md` item 22) the split modules that print
  must be named here — loudly, which is the point.
- **DEC-ZCG-002:** the two diagnostic prints in `test_output_byte_identical`
  are folded into the assertion message, not exempted. Two alternatives were
  rejected. A `tests/*` exemption would widen the rule's blind spot to the
  largest tree `make lint` scans, where a stray `print` is log noise rather
  than product; and a `noqa: T201` on each line is two waivers for one
  diagnostic that pytest will already display when it sits in the assertion
  message. The dump keeps its content — per drifting verb, the line count,
  the first and last lines and any path-bearing ones — so the comment above
  it about a self-diagnosing failure stays true.
- **DEC-ZCG-003:** `strict = true` with an explicit `warn_unreachable = true`,
  not a comment explaining why strict stays off. The explanation on record
  (DEC-PR-001: "`tools/` would require further annotation churn") was
  measured against a different tree; at the drafting commit the churn is two
  annotations in a file this change rewrites regardless. This decision
  **supersedes** DEC-PR-001 and `post-merge-quality-review`'s non-success
  criterion that `mypy --strict` stays an advisory diagnostic and never a
  hard gate — named here so the reversal is on record, not discovered. `warn_unreachable`
  is named separately because `--strict` does not imply it — checked against
  `python -m mypy --help`'s own list rather than remembered — and because the
  run with it reports nothing new, so it is zero-cost too.
- **DEC-ZCG-004:** the flags `strict` subsumes — `check_untyped_defs`,
  `warn_unused_ignores`, `warn_redundant_casts`, `warn_return_any` — and the
  default-on `no_implicit_optional` are removed from the table rather than
  left beside `strict = true`. A list that is a strict subset of what
  `strict` already turns on reads, to anyone without mypy's implication
  table in their head, as the whole policy; that is the "config that looks
  like a gate and is not" shape pyproject's ruff comment already calls out
  for the `S` per-file-ignores. The table that remains is `python_version`,
  `strict`, `warn_unreachable`, `files`: the interpreter floor, the policy,
  the one flag the policy does not imply, and the scope. Rejected: keeping
  them with a comment saying they are redundant, which is a comment doing a
  table's job.
- **DEC-ZCG-005:** each script's `main` builds its own
  `argparse.ArgumentParser` from argparse directly; `_common` does not gain a
  parser factory. The two scripts have different arities and different
  help text, and what they would share is argparse's own API — a factory
  over two call sites would be a third convention for `run_tool_main`'s
  docstring to explain, not a de-duplication. Both parse `argv[1:]`
  themselves, so they move from the hand-rolled program-name-first group to
  the argparse program-name-first group that `matcher_accuracy` and
  `stage_citations` already occupy, and `pass_argv0` stays at its default
  for every caller. Rejected: `main(sys.argv[1:])`, which would move them to
  the arguments-only group and change the one in-process convention their
  tests rely on, for no behavioural gain.
- **DEC-ZCG-006:** `_common` gains exactly one helper, `read_json`. The
  repeated line across the two scripts is
  `json.loads(path.read_text(encoding="utf-8"))` — three call sites between
  them — and R-ZCG-8's per-file-read DEBUG record would otherwise be written
  three times beside it. One helper is where the encoding, the parse and
  the record live once, the same argument that put `read_text` there — but
  `read_json` does not call `read_text`: that helper returns `""` for a
  missing path, which would surface as a `JSONDecodeError` where today's
  behaviour is a `FileNotFoundError` naming the file; the direct read keeps
  the clearer error. The return is a fully parameterised mapping so neither
  caller needs a bare generic, and the narrowing is a real `isinstance`
  branch — a non-mapping document raises `ValueError` naming the path — with
  its own test, not a `cast` that would hide a list at the top level until a
  `TypeError` deep in the caller. Rejected: inlining the three reads with
  three log lines; building on `read_text`.
- **DEC-ZCG-007:** a usage error is argparse's own `SystemExit(2)`,
  propagating out of `main`, rather than caught and converted to a returned
  2. Catching it would make these two scripts behave unlike the five
  argparse scripts already in the directory (none catches `SystemExit`), and
  would convert `--help`'s
  exit 0 into a return 0 that the `__main__` guard re-raises as the same
  exit — more code for the same process behaviour. The process-level
  contract is unchanged in every direction: 0, 1 and 2 as before, usage on
  stderr, nothing on stdout, and `test_gate_script_is_runnable_as_a_script`
  runs both scripts with no arguments and still sees one of the documented
  codes with no load-failure marker (it asserts 0, 1 or 2, per DEC-GTC-006).
  The in-process tests follow
  `test_plugin_manifests_require_a_mode`'s `pytest.raises(SystemExit)` form
  and keep their names, so the citations in this spec survive the rewrite.
- **DEC-ZCG-008:** logging goes through `_common.logger` — stderr, level from
  `PLANLINT_LOG_LEVEL`, silent by default — and no `-v` flag is added.
  `render_mermaid`'s stdout is the artifact and `diff_spec_graph`'s is read
  by CI and by people, so the only safe channel for diagnostics is the one
  `_common` already configured and documented as never stdout. The
  environment variable already covers the CLI and every other tool; a flag
  would be a second spelling. The records are asserted by attaching
  `caplog.handler` to `logging.getLogger("planlint.tools")` directly for the
  duration of the test, the pattern `tests/test_witness.py`'s `_captured`
  and `tests/test_repo_io.py` already use and explain — not `caplog.at_level`
  alone. The mechanism: `_common.py` sets `logger.propagate = False` at
  import, and pytest's logging plugin attaches its capture handler to the
  root and to the loggers that are *already* non-propagating when the test
  begins; a test whose `load_tool` call is the first import of `_common`
  therefore sees `caplog.records == []` while the line visibly reaches the
  captured stderr. The precedent this draft first cited,
  `test_plugin_manifests_verbose_logs_without_polluting_stdout`, has exactly
  that order dependence and fails under `-k` isolation today; adversarial
  review reproduced it, so the helper lands in `tests/support.py` once and
  that test adopts it too (R-ZCG-14). `capsys` is still the wrong tool for
  the positive assertion for the reason the earlier precedent gave; it
  remains the right tool for asserting stdout is untouched.
- **DEC-ZCG-009:** `render_mermaid.py` takes the
  `sys.path.insert(0, str(repo_root()))` bootstrap its sibling generators
  carry, and `diff_spec_graph.py` does not import `repo_root` at all. The
  first imports `openspec_graph` and should run from a checkout the way
  `matcher_accuracy.py` and `stage_citations.py` do; the second reads two
  files at the paths it is given and nothing relative to any root — its
  tests say so, passing absolute paths with no cwd. One observable effect,
  recorded as compatibility: with the checkout root first on `sys.path`, a
  checkout's `openspec_graph` shadows any installed one for this script, as
  it already does for its two siblings; `test_gate_script_is_runnable_as_a_
  script` shows the file still loads and reaches its own argument handling,
  not which copy resolved. Rejected: importing `repo_root` into
  `diff_spec_graph` for symmetry, which would be an unused import that
  `make lint` fails on anyway.
- **DEC-ZCG-010:** the guard tests live in `tests/test_ci_hardening.py`, in
  the section headed as claims about the CI configuration itself, beside
  `test_lint_is_a_hard_gate`. That section already asserts properties of
  this repository's gate configuration against the committed files;
  `tests/test_enterprise.py`'s mypy tests exercise mypy's behaviour on a
  synthetic module and say nothing about this repository's table. The TOML
  is parsed with `tomllib`, falling back to `tomli` on 3.10 — already a
  declared dev extra that every CI leg installs — rather than scanned with
  a regular expression; `_common.read_pyproject_int` is deliberately
  integer-only and a list-valued key is exactly what a regex gets wrong.
  Two structural tests rather than one, so a failure names the gate that
  regressed. Two coordination notes. The sibling package on this branch,
  `harden-ci-workflows`, decides the opposite for *its* guards (DEC-HCW-008:
  a new `tests/test_workflow_hardening.py`, because the existing module is
  already large); the two decisions agree on the reason and differ on the
  facts — these guards sit beside the script tests and the lint-gate test
  they extend, and locality wins for four short tests, while that package's
  twenty-odd workflow guards would double the module. And the plan's W4
  proof named `make thresholds` as the place to assert selected families;
  that is deliberately replaced by these pytest guards: the thresholds gate
  is a stdlib, 3.10-safe integer reader by design, a list-valued TOML key is
  what it must not learn, and `harden-ci-workflows` C-HCW-2 forbids editing
  it in this milestone.
- **DEC-ZCG-011:** each gate is also shown to fire, not only configured.
  A structural test proves the table says `T201`; it cannot prove ruff reads
  the exemption the way the table intends — a glob that matched nothing
  would pass it. The behavioural tests run ruff and mypy against planted
  violations under a copy of this repository's own configuration, in the
  spirit of `test_mypy_fails_on_a_type_error` and of this repository's
  standing argument that a gate which cannot be shown to fail is a
  decoration. The planted tree is in a temporary directory so the real
  package is never edited.
- **DEC-ZCG-012:** only zero-after-edit families are selected. `C901`, `PLR`,
  `E501`, `FBT`, `PERF` and `D` each have a backlog today, and selecting one
  would turn a measurable debt into a red build that someone silences in a
  hurry. The sequence is ratchet first — count, reduce, re-count — and gate
  when the count is zero, which is what later milestones do for each. The
  two `PLR2004` findings clearing here is a side effect of the rewrite, not
  a reason to select `PL`.
- **DEC-ZCG-013:** `tools/AGENTS.md` and `tests/support.py`'s docstring are
  updated because each pins the argv-convention grouping by count and by
  name, and both would be wrong the moment this lands.
  `docs/architecture/c4.md`'s `tools/*` row is not, because it groups the
  scripts by dependency — stdlib-only gates versus package-importing
  generators — and neither script changes group: `diff_spec_graph` stays
  stdlib-only through `_common`, and `render_mermaid` already imported the
  package.

---

## Acceptance Criteria

- [ ] **AC-ZCG-1:** `pyproject.toml` selects `T201`, and the only
  per-file-ignores entries naming it are `openspec_graph/cli.py` and
  `tools/*`; `make lint` exits 0 on the tree. (R-ZCG-1, R-ZCG-10)
  _Verified by:_ stage: `make lint`

- [ ] **AC-ZCG-2 (non-success):** under a copy of this repository's ruff
  `per-file-ignores`, with `T201` selected, a `print` planted in a
  library-module path is reported as `T201`, while the same `print` planted
  at a `cli.py` path and under a `tools/` path is not. (R-ZCG-2, R-ZCG-11, DEC-ZCG-011)
  _Verified by:_ stage: `make lint`

- [ ] **AC-ZCG-3:** `[tool.mypy]` has `strict = true` and
  `warn_unreachable = true` with `python_version = "3.10"` kept, and
  `make typecheck` exits 0 on the tree. (R-ZCG-3, R-ZCG-10, DEC-ZCG-003)
  _Verified by:_ `pytest -k test_typecheck_passes_on_clean_repo` · stage: `make typecheck`

- [ ] **AC-ZCG-4 (non-success):** under a copy of this repository's mypy
  configuration, a module annotating a parameter as bare `dict` is reported
  with a `type-arg` error. (R-ZCG-4, R-ZCG-11)
  _Verified by:_ stage: `make typecheck`

- [ ] **AC-ZCG-5:** `diff_spec_graph.py` reaches the same four verdicts it
  reaches today — 0 on an unchanged graph, 1 on new broken edges, 1 on a new
  orphan, 0 when an orphan is fixed — through the argparse `main`.
  (R-ZCG-5, R-ZCG-6, R-ZCG-7)
  _Verified by:_ `pytest -k "test_graph_diff_passes_when_clean or test_graph_diff_fails_on_new_broken_edges or test_graph_diff_fails_on_new_orphan or test_graph_diff_passes_when_orphan_fixed"` · stage: `make test`

- [ ] **AC-ZCG-6 (non-success):** `diff_spec_graph.py` given one argument
  raises `SystemExit` with code 2, writes the usage text to stderr, and
  writes nothing to stdout. (R-ZCG-6, DEC-ZCG-007)
  _Verified by:_ `pytest -k test_graph_diff_rejects_bad_args` · stage: `make test`

- [ ] **AC-ZCG-7:** `render_mermaid.py`'s stdout for a saved graph is
  byte-identical to `to_mermaid(graph)`, with nothing appended, through the
  argparse `main`. (R-ZCG-5, R-ZCG-7)
  _Verified by:_ `pytest -k test_render_mermaid_matches_to_mermaid_byte_for_byte` · stage: `make test`

- [ ] **AC-ZCG-8 (non-success):** `render_mermaid.py` given no argument
  raises `SystemExit` with code 2, writes the usage text to stderr, and
  writes nothing to stdout. (R-ZCG-6, DEC-ZCG-007)
  _Verified by:_ `pytest -k test_render_mermaid_rejects_bad_args` · stage: `make test`

- [ ] **AC-ZCG-9:** `--help` on each script raises `SystemExit` with code 0
  and writes the usage text to stdout. (R-ZCG-6)
  _Verified by:_ stage: `make test`

- [ ] **AC-ZCG-10:** both scripts still start as `python tools/<script>.py`
  from a throwaway cwd with no arguments, emit no load-failure marker on
  stderr, and exit one of the documented codes — so the file still loads
  under script execution and reaches its own argument handling, and the
  `graph-diff` step's invocation shape, `python tools/diff_spec_graph.py
  base.json head.json`, is intact. (R-ZCG-5, C-ZCG-3)
  _Verified by:_ `pytest -k test_gate_script_is_runnable_as_a_script` · stage: `make test`

- [ ] **AC-ZCG-11:** with the `planlint.tools` logger at DEBUG, a diff run
  records each file read and its decision, and a rendering run records the
  file read and the node and edge counts; none of those records appear on
  stdout. (R-ZCG-8, DEC-ZCG-008)
  _Verified by:_ stage: `make test`

- [ ] **AC-ZCG-12:** `tools/_common.py` is still stdlib-only after
  `read_json` lands. (R-ZCG-9)
  _Verified by:_ `pytest -k common_module_is_stdlib_only` · stage: `make test`

- [ ] **AC-ZCG-13:** the scoped coverage run still meets
  `tools_line_fail_under` and `tools_branch_fail_under` with the argparse,
  help, error and logging paths of both scripts measured in-process.
  (R-ZCG-12)
  _Verified by:_ stage: `make coverage-tools`

- [ ] **AC-ZCG-14 (non-success):** the rule inventory is unchanged — the
  live rule table still matches `tests/baseline_rules.json`. (C-ZCG-3)
  _Verified by:_ `pytest -k test_rule_set_matches_baseline` · stage: `make test`

- [ ] **AC-ZCG-15:** `make lint` keeps a recipe with no escape hatch and CI
  still runs it, and `make typecheck` still exits 0 against the repository;
  neither recipe changed. (C-ZCG-3)
  _Verified by:_ `pytest -k "test_lint_is_a_hard_gate or test_typecheck_passes_on_clean_repo"` · stage: `make pre-pr`

- [ ] **AC-ZCG-16 (non-success):** `test_output_byte_identical` still passes
  with its diagnostic carried in the assertion message, and `make lint`
  passes with no `tests/*` exemption for `T201` and no `noqa: T201` in the
  tree. (C-ZCG-1, DEC-ZCG-002)
  _Verified by:_ `pytest -k test_output_byte_identical` · stage: `make ci`

- [ ] **AC-ZCG-17:** `tests/support.py`'s `run_tool_main` docstring and
  `tools/AGENTS.md` name five hand-rolled scripts and four argparse scripts
  that strip the program name themselves, listing `diff_spec_graph` and
  `render_mermaid` in the second group; the `T20` comment in
  `pyproject.toml` states the rule is on with two exemptions. No automated
  guard asserts prose; it is read directly. (R-ZCG-13, DEC-ZCG-013)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-ZCG-18 (non-success):** `make lint` exits 0 with the new `select`
  list — any selected family with outstanding violations would fail it, so a
  green lint is the proof that only zero-cost families were added.
  (C-ZCG-2, DEC-ZCG-012)
  _Verified by:_ stage: `make lint`

- [ ] **AC-ZCG-19 (non-success):** `read_json` on a document whose top level
  is a list raises `ValueError` naming the path, and on a missing path raises
  `FileNotFoundError` — never a `JSONDecodeError` for an absent file.
  (R-ZCG-9, DEC-ZCG-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-ZCG-20 (non-success):** the logging-capture precedent passes when
  run in isolation, which it does not today: the helper attaches
  `caplog.handler` to the `planlint.tools` logger directly, so the records
  are seen whether or not `_common` was imported before the test began.
  (R-ZCG-14, DEC-ZCG-008)
  _Verified by:_ `pytest -k test_plugin_manifests_verbose_logs_without_polluting_stdout` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Lint | `make lint` | AC-ZCG-1, 2, 18 — `T201` on, two exemptions, zero findings |
| Typecheck | `make typecheck` | AC-ZCG-3, 4 — strict plus `warn_unreachable`, zero findings |
| Focused | `make test` | AC-ZCG-5..12, 14 |
| Scoped coverage | `make coverage-tools` | AC-ZCG-13 — `tools/` meets both floors read from `pyproject.toml` |
| Core | `make ci` | AC-ZCG-16 — the folded diagnostic passes its test and lint together |
| Self-check | `make validate` | this package validates clean against the repo's own rules |
| Full | `make pre-pr` | AC-ZCG-15, 17 — full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
