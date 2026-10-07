# Change: Type-Check the Tests by a Per-Code Baseline, Select Public Docstrings by a Per-File Ratchet

## Why

The type gate stops at the suite's edge. `make typecheck` runs `python -m mypy
openspec_graph tools` and `[tool.mypy] files` names the same two trees, so the
22,555 lines under `tests/` — the helpers every spec's verification line
depends on among them — are type-checked by nothing: a helper whose signature
drifts from its callers is found by the test run that trips on it, if one
does, and never before. The lint gate has the matching gap one level up:
no docstring rule is selected, and the comment that says so
(`pyproject.toml:297`, "`ANN/D` -- annotation and docstring coverage in
tests; large, low-yield") gives a reason about tests and none about the
package, whose public functions, methods and classes ship undocumented with
nothing to say so.

Both are debts too large to clear in one change, and the plan's D1 says how
to carry them: configure at today's state, so the first commit is green and
everything not yet listed is enforced from it, and let the listed state only
shrink. This package does that for both, and holds each list to a guard that
names a listed entry whose debt is gone, so the shrinking is forced rather
than remembered.

This is milestone M2's W6.5 (tests under mypy) and W6.6 (public docstrings by
ratchet) of the October 2026 reflection plan (`docs/reflection-plan-2026-10.md`
§4 W6 items 5 and 6; §5's M2 row; §6 D1; §7's "Tests under mypy" and "Public
symbols without a docstring" rows). It is drafted on
`claude/m2-tests-under-mypy`, stacked on the unmerged #42
(`shape-the-test-suite`), whose tier criterion, line bound and suite layout
it builds on.

The plan's W6.5 mechanism does not survive the tree it would run on, and the
measurements below say where. Adding `tests` to `files` with
`explicit_package_bases = true` turns today's clean `tools/` run red (explicit
bases rename `tools/_common.py`, which every gate script imports as `_common`)
and changes nothing the gate runs (the recipe's positional paths override
`files`). Its tally — "~52 real", five codes — predates the test-suite split
and the tier work, and its `str` code is not a mypy code: it is the
`PathLike[str]` at the end of note lines. Disabling codes for `tests.*` makes
eight existing inline ignores redundant, which strict mode reports. The one
TOML import in `tests/` is checked on its 3.10 branch on every leg, so its
verdict flips with whether the leg installed `tomli`. And a count taken on
Linux is not the count on Windows. This package takes its own baseline and
answers each of those; the decisions that depart from the plan are named in
the spec (DEC-TDR-001, 002, 003, 004, 008, 010).

**Evidence:** measured at `1c8917c` (`claude/m2-tests-under-mypy`, stacked on
#42), 2026-10-07, in this four-core container (Python 3.13.16, mypy 2.4.0,
ruff 0.16.10, pytest 9.1.1, hypothesis 6.168.5; `tomli` not installed). Every
mypy run used a cache directory outside the worktree, or `--cache-dir
/dev/null` where a cold time is stated; every command was read-only on the
tree. `tasks.md` Milestone 0 re-measures at the branch head before the first
edit.

- **The gate's scope, and why `files` alone does not move it.** `Makefile:53–54`:
  `typecheck: ## mypy with config from pyproject.toml — a hard gate` with the
  recipe `python -m mypy openspec_graph tools`; `pyproject.toml:309–322`:
  `[tool.mypy]` with `python_version = "3.10"`, `strict = true`,
  `warn_unreachable = true`, `files = ["openspec_graph", "tools"]` (line
  322). mypy reads `files` only when no path is given on the command line,
  so the recipe's two positional paths are what the gate checks.
  `.github/workflows/ci.yml` runs `make typecheck` in the `test` matrix (line
  60, five interpreters) and in `test-windows` (line 108);
  `.pre-commit-config.yaml:18–23` runs it as the `specgraph-typecheck` hook
  with `types: [python]` and `pass_filenames: false`, so a staged test module
  already fires it. `python -m mypy openspec_graph tools --cache-dir
  /dev/null`: "Success: no issues found in 43 source files", 0.9 s.
- **Today's tests, by code.** `python -m mypy tests --explicit-package-bases
  --cache-dir <scratch>`: "Found 185 errors in 32 files (checked 60 source
  files)", 8.5 s with a fresh cache. Counted by the trailing code of the 185
  `error:` lines (`grep ": error:" | grep -oE "\[[a-z-]+\]$" | sort | uniq
  -c`): `no-untyped-def` 96, `attr-defined` 19, `arg-type` 18, `type-arg`
  16, `no-any-return` 9, `index` 7, `union-attr` 4, `list-item` 3,
  `unused-ignore` 2, `operator` 2, `misc` 2, `import-not-found` 2,
  `call-overload` 2, `var-annotated` 1, `unreachable` 1, `assignment` 1 —
  sixteen codes. The same grep without the `": error:"` filter also counts
  `[str]` 4 and `[bytes]` 1, from the `PathLike[str]` and `PathLike[bytes]`
  closing the overload signatures mypy prints as notes under
  `tests/test_graft_witness.py:107`; that is where the plan's `str` came
  from, and the briefing this package was drafted from repeated it. Without
  `--explicit-package-bases`, `python -m mypy tests` stops at
  "tests/graft_support.py: error: Source file found twice under different
  module names" and exits 2. pytest and hypothesis resolve here and ship
  `py.typed` (`_pytest/py.typed`, `hypothesis/py.typed`), so the plan's 34
  unresolved imports are gone, and `no-untyped-def`, `attr-defined` and
  `type-arg` now show; `pip install -e ".[dev]"` installs both on every CI
  leg, and their `Requires-Python` is `>=3.10`, as mypy's is, so no leg's
  interpreter holds it to an older release.
- **The plan's mechanism, measured.** `python -m mypy openspec_graph tools
  --explicit-package-bases`: "Found 19 errors in 12 files" — every gate
  script's `from _common import …` is `import-not-found` and the values read
  through it become `no-any-return`. With `MYPYPATH=tools` added: "Success:
  no issues found in 43 source files". `MYPYPATH=tools python -m mypy tests
  --explicit-package-bases`: 184 errors in 31 files — `import-not-found`
  falls to 1, because `tests/test_wheel_metadata.py:26–29`'s
  `sys.path.insert(0, str(TOOLS))` then `from check_wheel_metadata import …`
  now resolves statically; the other is `tests/support.py:84`'s `import
  tomllib`, which `python_version = "3.10"` makes missing on every leg. All
  three trees in one run (`MYPYPATH=tools python -m mypy openspec_graph
  tools tests --explicit-package-bases`): 184 errors, every one under
  `tests/`.
- **What disabling seven codes leaves, and what it creates.** Emulating the
  configuration with no file written — an INI configuration through process
  substitution (`--config-file <(printf '[mypy]\n…\n[mypy-tests.*]\ndisable_error_code
  = no-untyped-def, attr-defined, arg-type, type-arg, no-any-return, index,
  union-attr\n')`, with `explicit_package_bases`, `mypy_path = tools` and
  `files = openspec_graph, tools, tests`) — reports "Found 23 errors in 15
  files (checked 103 source files)" in 3.7 s cold: the fifteen occurrences of
  the nine other codes, and eight `unused-ignore` that did not exist before,
  on inline ignores of a now-disabled code: `tests/test_witness.py:47`
  (`_witness`, `arg-type`), `:95` (`test_write_witness_is_atomic`,
  `attr-defined`), `:110`
  (`test_write_witness_cleans_up_the_temp_file_and_reraises_on_write_failure`,
  `attr-defined`), `tests/test_suite_shape.py:111`
  (`test_pytest_registers_exactly_the_three_tier_markers_strictly`,
  `attr-defined`), `tests/test_rules_speckit.py:149`
  (`_minimal_speckit_spec`, `arg-type`), `tests/test_matcher_accuracy.py:329`
  (`test_annotation_tier_matches_the_whole_marker_only`, `arg-type`),
  `tests/test_stage_citations.py:233` (`refuse` in
  `test_an_unreadable_workflow_exits_two_rather_than_a_traceback`,
  `arg-type`) and `tests/test_graft_witness.py:168` (`_witness`,
  `arg-type`). A command-line `--enable-error-code arg-type` beside a
  per-module `disable_error_code = arg-type` still reports no `arg-type`
  (counted with `grep -c` over `tests/test_mermaid.py`'s run: 0 and 0), so a
  per-module disable cannot be lifted from the command line. A one-line
  program with `# type: ignore[arg-type, unused-ignore]` is clean under
  `--strict` with `arg-type` disabled, with it enabled, and with no error on
  the line at all — which is why that form needs the guard of DEC-TDR-006.
- **The nine codes this package fixes, by site.** `assignment`:
  `tests/shape_support.py:571` (`_class_facts`). `import-not-found`:
  `tests/support.py:84` (`read_pyproject`) and
  `tests/test_wheel_metadata.py:29` (module level, by the search path).
  `unused-ignore`: `tests/support.py:86` (`read_pyproject`, the `tomli`
  import) and `tests/test_graft_witness.py:107` (`spy` in
  `test_current_sha_is_not_invoked_when_no_witnesses_are_present`, whose
  `arg-type` ignore sits on a `call-overload`). `call-overload`: that line
  and `tests/test_action_contract.py:250`
  (`test_the_step_extractor_sees_the_whole_action`). `operator`:
  `tests/test_suite_shape.py:536`
  (`test_a_mismarked_or_unmarked_planted_module_is_named`) and
  `tests/test_cli_surface.py:203`
  (`test_run_cli_injects_coverage_process_start_by_default`). `misc`:
  `tests/conftest.py:19` (`_reset_version_cache`, a generator annotated
  `-> None`) and `tests/test_graph.py:119`
  (`test_graph_covers_every_parsed_spec_when_multiple`). `list-item`:
  `tests/test_mermaid.py:31`, `:47`, `:53`
  (`test_node_ids_are_sanitized_to_synthetic_identifiers`,
  `test_node_label_combines_ident_and_text_for_requirement_nodes`,
  `test_node_label_escapes_embedded_quotes`). `var-annotated`:
  `tests/test_dialect_card.py:49`
  (`test_diff_cards_detects_an_adr_source_change`). `unreachable`:
  `tests/test_finding_line_hits.py:322`
  (`test_section_body_still_returns_only_the_span_text`, an `assert not
  isinstance(result, tuple)` after an `isinstance(result, str)` the type
  already guarantees). `tests/support.py:88`'s `no-any-return` is the same
  reader and goes with it, so `no-any-return` is listed at one fewer than
  measured.
- **The seven listed codes, by file** (same run, `MYPYPATH=tools`,
  `--platform linux`): `no-untyped-def` 96 in 15 files (`test_graph.py` 24,
  `test_gate_scripts.py` 12, `test_graft_cli.py` 10, `test_graft_witness.py`
  10, `test_graft_detection.py` 9, and ten more); `attr-defined` 19 in 7
  (`test_detect_speckit.py` 7, most of them `detect.subprocess`, which mypy
  does not see as re-exported); `arg-type` 18 in 5 (`test_mermaid.py` 10);
  `type-arg` 16 in 11; `no-any-return` 9 in 7; `index` 7 in 3
  (`test_sarif.py` 5); `union-attr` 4, all in `test_enterprise.py`'s two
  hand-rolled `spec_from_file_location` loads.
- **Windows sees more.** `MYPYPATH=tools python -m mypy tests
  --explicit-package-bases --platform win32`: 188 errors; `diff` against the
  Linux run shows exactly four more, all `Module has no attribute "mkfifo"
  [attr-defined]` at `tests/test_detect_thresholds.py:250`, `:251`
  (`test_a_fifo_where_a_config_file_belongs_does_not_hang`), `:406`
  (`test_a_fifo_where_a_spec_file_belongs_does_not_hang`) and `:425`
  (`test_a_fifo_spec_raises_spec_read_error_rather_than_blocking`), tests
  that skip at runtime where `os.mkfifo` is absent. `openspec_graph tools`
  under `--platform win32`: no issues.
- **The guard's cost.** The occurrence guard's run — `tests` only, override
  lifted, `--platform linux`, `--cache-dir /dev/null` — took 3.6 s and
  reported the 184.
- **The TOML import.** `tests/support.py:83–88` tries `import tomllib`,
  falls back to `import tomli as toml_reader  # type:
  ignore[import-not-found,no-redef]` and returns `toml_reader.load(handle)`.
  A one-file program in the `sys.version_info >= (3, 11)` form with an
  annotated local is clean under `--strict --warn-unreachable` at
  `--python-version 3.10` and `3.11`; a one-file analogue of the current form
  at 3.10 reports three errors, among them an unused `no-redef` ignore and a
  `no-any-return`. A `[mypy-tomli] ignore_missing_imports = True` section
  makes the 3.10-branch import silent with `tomli` absent, and a run whose
  configuration carried sections matching no processed module printed no
  warning and exited 0.
- **Docstrings, measured.** `python -m ruff check --select
  D100,D101,D102,D103 <tree> --statistics`: `openspec_graph/` 52 —
  `D103` 30, `D102` 15, `D101` 7, `D100` 0 — exactly the plan's figure, in
  18 files; `tools/` 25 — `D103` 21, `D102` 4 — in 12 files; `tests/` 584 —
  `D103` 575, `D102` 8, `D101` 1 — in 47 files. Per file (`--isolated
  --output-format concise`): `openspec_graph/cli.py` `D103` 8;
  `parse_semantics.py` `D103` 7; `parse_model.py` `D101` 2, `D102` 4;
  `scaffold_templates.py` `D103` 4; `scaffold.py` `D101` 1, `D102` 1,
  `D103` 3; `detect.py` `D101`, `D102`, `D103` 1 each; `rule_types.py`
  `D101` 2, `D102` 2; `ledger.py` `D101` 1, `D102` 1; `delta.py` and
  `report.py` `D102` 2; `witness.py` `D102` 1, `D103` 1; `thresholds.py`
  `D102` 1; `machinery.py`, `parse.py`, `parse_harness.py`,
  `parse_speckit.py`, `parse_upstream.py`, `rules.py` `D103` 1 each;
  `tools/check_no_hardcoded_thresholds.py`, `render_plugin_manifests.py`
  `D103` 3; `stage_citations.py` `D102` 1, `D103` 3; `matcher_accuracy.py`
  `D102` 3, `D103` 1; `check_branch_coverage.py`, `check_coverage_floor.py`,
  `diff_spec_graph.py` `D103` 2; `check_docs.py`, `check_secrets.py`,
  `check_wheel_metadata.py`, `render_mermaid.py`, `render_rule_catalog.py`
  `D103` 1. The proposed configuration, emulated with no file written
  (`--config 'lint.extend-select = ["D100","D101","D102","D103"]'` and the
  thirty entries plus `tests/*` passed as one inline `lint.per-file-ignores`
  table): `python -m ruff check openspec_graph tests tools` — "All checks
  passed!", exit 0.
- **The convention, measured.** `python -m ruff check --isolated --select D
  --ignore D100,…,D107 --config 'lint.pydocstyle.convention = "<c>"'
  openspec_graph tools --statistics`: Google 37 findings (`D205` 23, `D209`
  10, `D301` 4); pep257 and numpy 67 each, the difference being `D401` 29
  (non-imperative summaries) and `D400` 1. `D100`–`D103` over all three trees
  read 661 under no convention and under each of the three — the setting
  changes no presence finding.
- **ruff's exemptions, measured.** A file entry and a matching glob entry
  union (`tools/check_docs.py`'s `D103` is reported under `{"tools/*" =
  ["T201"]}` and not under that plus `{"tools/check_docs.py" = ["D103"]}`);
  an entry that exempts nothing draws no warning (`tools/_common.py` with a
  `D103` entry and no finding: "All checks passed!"); a `--config
  'lint.per-file-ignores = {}'` replaces the table rather than merging (80
  `T201` findings reappear in `openspec_graph/cli.py`).
- **What reads this configuration today.** `tests/test_ci_workflow.py:37–55`:
  `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt` (the
  `T201` keys must be exactly `openspec_graph/cli.py` and `tools/*`) and
  `test_mypy_is_strict_and_warns_on_unreachable_code` (strict,
  `warn_unreachable`, `python_version`; not `files`); `:69–104`, two
  planted-tree tests that copy the real `pyproject.toml` and run ruff and
  mypy on a path given on the command line, so `files` is not read;
  `tests/test_enterprise.py:225` and `:241`,
  `test_mypy_fails_on_a_type_error` (a module under `tmp_path`, outside every
  package base) and `test_typecheck_passes_on_clean_repo` (runs
  `make typecheck` from the repository root, so it will check `tests/` too).
  `select-zero-cost-guards`' R-ZCG-3 (`specs/zero-cost-guards/spec.md:67–70`)
  requires `[tool.mypy]` to "keep … `files = ["openspec_graph", "tools"]`";
  that package shipped in 0.3.0 (`CHANGELOG.md:134`). `shape-the-test-suite`'s
  C-TSS-6 forbids its own diff from widening the `tests/*` per-file-ignores.
  No shipped spec records a decision about selecting `D` (`grep -rn
  "pydocstyle\|D10[0-3]\|ANN"` over every spec and proposal finds nothing).
- **Where the scope is written down.** `docs/hooks.md:19`: "`make typecheck`
  (mypy) across `openspec_graph/`, `tools/`"; `:111–112`: `typecheck` runs
  inside the `test` matrix on every interpreter (stays true).
  `tests/AGENTS.md`: 59 lines against `MAX_NESTED_LINES = 60`
  (`tests/test_agent_artifacts.py:454`). `.claude/agents/planlint-verifier.md:28`
  still calls the configuration "pragmatic strictness, not `--strict`",
  stale since `select-zero-cost-guards` made mypy strict. `README.md:375`
  and `docs/aqa.md:12` say "mypy (config in `pyproject.toml`)", which stays
  true. `docs/distribution-plan.md:34`'s "mypy clean over 43 files" is a
  dated measurement and stays.
- **The neighbourhood this package writes into.** `wc -l tests/test_*.py |
  sort -n | tail -4`: `test_graph.py` 647, `test_graft_rules.py` 677,
  `test_suite_shape.py` 689, `test_report.py` 692; `tests/test_ci_workflow.py`
  392. `make thresholds`: "PASS: no hard-coded thresholds in Makefile or
  workflow YAML". `make stage-citations`: 51 specs; `typecheck` mentioned in
  7 and verified by 4, run directly by `ci.yml`; `lint` 7 and 4; `test` 48
  and 48. The gate before the first write under `openspec/`: `planlint
  --target . validate --fail-on ERROR`, exit 0, 51 specs, 0 error / 0 warn /
  0 info.

## What Changes

- `pyproject.toml` `[tool.mypy]`: `files = ["openspec_graph", "tools",
  "tests"]`; `explicit_package_bases = true` and `mypy_path = "tools"`, each
  with a comment giving its measured reason (DEC-TDR-002); `strict`,
  `warn_unreachable` and `python_version` unchanged. Two overrides: `module =
  "tests.*"` with `disable_error_code` listing the codes of R-TDR-2 that
  still occur when it lands, under a comment naming the ratchet, the guard
  module that holds its ceilings and the rule that a code leaves in the
  commit that fixes its last occurrence; and `module = "tomli"` with
  `ignore_missing_imports = true`, under a comment saying why only the 3.10
  leg has it.
- `pyproject.toml` `[tool.ruff.lint]`: `select` gains `"D100", "D101",
  "D102", "D103"` with a comment; the "Deliberately NOT selected" comment's
  `ANN/D` line is rewritten as R-TDR-10 requires, with the measured
  convention and its command. `[tool.ruff.lint.per-file-ignores]`: `tests/*`
  gains the four codes; one entry per offending file under `openspec_graph/`
  and `tools/` lists exactly its `D` codes (thirty at drafting), with
  `openspec_graph/cli.py`'s joining its `T201` entry; a comment above them
  names the ratchet and its guard. No `[tool.ruff.lint.pydocstyle]` table.
- `Makefile`: the `typecheck` recipe becomes `python -m mypy`; its help text
  says it checks the trees `[tool.mypy] files` names. Nothing else.
- `tests/support.py`: `read_pyproject` picks `tomllib` or `tomli` by
  `sys.version_info` and returns an annotated local; the inline ignore goes.
  `tests/conftest.py`, `tests/shape_support.py`, `tests/test_action_contract.py`,
  `tests/test_cli_surface.py`, `tests/test_dialect_card.py`,
  `tests/test_finding_line_hits.py`, `tests/test_graft_witness.py`,
  `tests/test_graph.py`, `tests/test_mermaid.py` and `tests/test_suite_shape.py`:
  the sites the proposal lists for the nine codes, fixed by annotation,
  narrowing or a typed local, every assertion kept, no line added to
  `tests/test_suite_shape.py`.
- `tests/test_witness.py`, `tests/test_suite_shape.py`,
  `tests/test_rules_speckit.py`, `tests/test_matcher_accuracy.py`,
  `tests/test_stage_citations.py`, `tests/test_graft_witness.py`: the eight
  inline ignores the override makes redundant gain `unused-ignore` beside
  their code (DEC-TDR-006).
- `tests/test_static_ratchets.py` (new): `MYPY_TESTS_CEILINGS` and
  `DOCSTRING_CEILINGS`, each under its never-raised, never-added comment; the
  pure helpers — the derived mypy configuration, the mypy-output counter, the
  ceiling comparison, the ignore-comment reader, the per-file-ignores shape
  check, the ruff-JSON counter — each taking its input as an argument; and
  the guards of R-TDR-1, 2, 4, 5, 7 and 9 with the planted-input test of
  R-TDR-11, each with one tier marker, the module marking per function.
- `docs/hooks.md:19`: `make typecheck` (mypy) across `openspec_graph/`,
  `tools/`, `tests/`, with `tests/` under its per-code baseline.
  `tests/AGENTS.md`: one sentence, replacing rather than adding, within
  `MAX_NESTED_LINES`. `.claude/agents/planlint-verifier.md`: the `ruff`/`mypy`
  bullet states the standing configuration and the ratchet remediation norm
  (R-TDR-13).
- `CHANGELOG.md` `[Unreleased]`: `### Changed — tests under mypy, public
  docstrings by ratchet (M2)`, with the items R-TDR-15 names.
- `openspec/changes/ratchet-test-types-and-docstrings/tasks.md`: the records
  R-TDR-15 names, and the verification lines of AC-TDR-3, 4, 5, 8, 9, 12 and
  13 re-pointed to the guards once they exist.

## Non-Goals

- **Clearing the baseline.** No listed code is re-enabled and no docstring is
  written here. Each code leaves the override in its own later commit, which
  fixes its last occurrence, removes its ceiling and strips `unused-ignore`
  from the waivers that named it; each docstring entry leaves in the W2 or W3
  pull request that touches its file. The plan's §7 target ("checked,
  overrides tightened to strict"; "0, `D100`–`D103` selected") is the end of
  those commits, not of this package.
- **Anything under `openspec_graph/`.** No docstring, no re-export for the
  `attr-defined` sites that patch `detect.subprocess` or `witness.os`, no
  rule, no golden hash. `test_rule_set_matches_baseline`,
  `test_output_byte_identical` and `test_public_import_compatibility` hold
  that.
- **A dependency or a pin.** No stub package (pytest and hypothesis ship
  types), no `tomli` for every interpreter, no version pin on mypy or ruff:
  the dev extras stay unpinned by decision, and
  `test_threshold_guard_fails_on_a_pinned_tool_version` holds that.
- **A workflow, composite-action or `.pre-commit-config.yaml` change.** Every
  leg and the hook already run `make typecheck`; the hook's `types: [python]`
  already includes a test module.
- **A `tests/__init__.py` or `tools/__init__.py`.** Either would change how
  pytest or mypy names modules; the search path does the job (DEC-TDR-002).
- **`ANN`, or any `D` rule beyond `D100`–`D103`, or a `pydocstyle`
  convention.** mypy's `no-untyped-def` is the annotation check; the
  remaining `D` findings are formatting debt that a later package can select
  with the convention it then needs (DEC-TDR-010).
- **Docstrings in `tests/`.** Exempt by policy, not by ratchet (DEC-TDR-008).
- **The stale verifier sentence's wider claim.** `.claude/agents/planlint-verifier.md:28`
  is re-worded for the mypy and ruff configuration this package changes; the
  agent's other guidance is W9's.
- **Editing `select-zero-cost-guards` or `shape-the-test-suite`.** The R-ZCG-3
  clause is superseded by name and C-TSS-6 is named as not reversed
  (DEC-TDR-011); neither package's files change.
- **More than one pull request.** The guards, then W6.5, then W6.6, as
  separate commits in one (DEC-TDR-013).

## Affected Capabilities

- `static-check-ratchets`
