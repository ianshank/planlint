# Tasks: ratchet-test-types-and-docstrings

Measured at `1c8917c` (`claude/m2-tests-under-mypy`, stacked on the unmerged
#42, `shape-the-test-suite`), 2026-10-07, in a four-core container with Python
3.13.16, mypy 2.4.0, ruff 0.16.10, pytest 9.1.1 and hypothesis 6.168.5, and no
`tomli`. Every line number below is re-checked against the branch head before
the milestone that uses it; a sibling package landing first may move a line
without moving the fact. Every number here names the command that produced
it, and every mypy run used a cache directory outside the worktree (or
`--cache-dir /dev/null` where a cold time is given). At `1c8917c`: the gate
(`planlint --target . validate --fail-on ERROR`) exits 0 before the first
write under `openspec/` (51 specs, 0 error / 0 warn / 0 info); `python -m mypy
tests --explicit-package-bases --cache-dir <scratch>` reports "Found 185
errors in 32 files (checked 60 source files)", and counting only the trailing
code of its `error:` lines (`grep ": error:" | grep -oE "\[[a-z-]+\]$" | sort
| uniq -c`) gives `no-untyped-def` 96, `attr-defined` 19, `arg-type` 18,
`type-arg` 16, `no-any-return` 9, `index` 7, `union-attr` 4, `list-item` 3,
`unused-ignore` 2, `operator` 2, `misc` 2, `import-not-found` 2,
`call-overload` 2, `var-annotated` 1, `unreachable` 1, `assignment` 1 — the
`str` 4 and `bytes` 1 of an unfiltered grep are note-line text, not codes;
without `--explicit-package-bases` the run stops at "Source file found twice
under different module names" for `tests/graft_support.py`, exit 2; `python
-m mypy openspec_graph tools --explicit-package-bases` reports 19 errors in
12 files (twelve `_common` imports), and with `MYPYPATH=tools` none in 43;
`MYPYPATH=tools python -m mypy tests --explicit-package-bases` reports 184 in
31 files, and 188 under `--platform win32`, the four extra `attr-defined` on
`os.mkfifo` in `tests/test_detect_thresholds.py`; with the seven codes of
R-TDR-2 disabled for `tests.*` through an in-memory INI configuration the
three trees report 23 errors in 15 files in 3.7 s cold — fifteen occurrences
of nine codes on fourteen lines, and eight `unused-ignore` on inline ignores
the override makes redundant; the guard-shaped run (tests only, override
lifted, `--platform linux`, `--cache-dir /dev/null`) takes 3.6 s; today's
recipe command, `python -m mypy openspec_graph tools --cache-dir /dev/null`,
takes 0.9 s. `python -m ruff check --select D100,D101,D102,D103 <tree>
--statistics` reads 52 in 18 files of `openspec_graph/`, 25 in 12 files of
`tools/` and 584 in 47 files of `tests/`; the emulated configuration (the
four codes added, thirty file entries and the `tests/*` key passed inline)
passes `python -m ruff check openspec_graph tests tools`; the pydocstyle
convention changes no `D100`–`D103` finding (661 under none, Google, pep257
and numpy) and the Google convention leaves the fewest of the wider family
(37 against 67). `make thresholds` prints PASS; `make stage-citations` reads
51 specs with `typecheck` mentioned in 7, verified by 4 and run directly by
`ci.yml`; `wc -l tests/AGENTS.md` reads 59 against `MAX_NESTED_LINES = 60`;
`tests/test_suite_shape.py` is 689 lines. Order (DEC-TDR-013): measure, then
the mypy guards seen red, then the nine codes fixed and the override landed
with its ceilings (the W6.5 commit), then the docstring guards seen red and
the entries landed with theirs (the W6.6 commit), then the documents and the
records. One pull request carries the package; the red runs are recorded
here and never committed.

## Milestone 0 — Grounding pass at the branch head

- Re-run the gate and record its exit code before the first edit:
  `planlint --target . validate --fail-on ERROR`.
- Re-take the header's measurements and record what moved, with the commit:
  `python -m mypy tests --explicit-package-bases --cache-dir <scratch>`
  counted by the code of `error:` lines only; the same with
  `MYPYPATH=tools`, under `--platform linux` and under `--platform win32`,
  and the `diff` of the two platforms' `error:` lines; `python -m mypy
  openspec_graph tools --explicit-package-bases` with and without
  `MYPYPATH=tools`; the per-file distribution of the seven listed codes; the
  ruff statistics per tree and the per-file list over `openspec_graph` and
  `tools` (`--isolated --output-format concise`); `make thresholds`;
  `make stage-citations`; `wc -l tests/AGENTS.md`; `wc -l tests/test_*.py |
  sort -n | tail -4`. Use a scratch cache directory for every mypy run, never
  the tree's `.mypy_cache`.
- Re-derive the code split from the re-measurement, not from this file: the
  override lists exactly those of R-TDR-2's seven that still occur; every
  other code that occurs is fixed in Milestone 2 (R-TDR-3). If a sibling has
  added a code outside the sixteen, it joins the fixed set and is recorded
  here by site; if one of the seven is gone, it is not listed.
- Record the cold wall time of the type gate before the change, by the
  recipe's own command with a throwaway cache: `TIMEFORMAT='%R s'; time
  python -m mypy openspec_graph tools --cache-dir /dev/null` (0.9 s at
  drafting).
- Confirm the facts the decisions rest on: `Makefile` `typecheck` recipe
  still names two paths (DEC-TDR-001); `.pre-commit-config.yaml`'s
  typecheck hook still has `types: [python]` and `pass_filenames: false`;
  `ci.yml` still runs `make typecheck` in the `test` matrix and in
  `test-windows`; `python -c "import tomli"` fails here and `tomli` is still
  the dev extra's 3.10-only entry (DEC-TDR-007); `_pytest/py.typed` and
  `hypothesis/py.typed` exist (C-TDR-1); the eight inline ignores of the
  proposal still carry `arg-type` or `attr-defined` (`grep -n "type: ignore"
  tests/*.py`); `select-zero-cost-guards`' R-ZCG-3 still reads as quoted and
  `shape-the-test-suite`'s C-TSS-6 likewise, and whether #42 has merged —
  if it has, DEC-TDR-011's sentence about it is updated to say so, and
  C-TSS-6 is still named.
- **Gate:** `make validate`

## Milestone 1 — The mypy guards, seen red first

- `tests/test_static_ratchets.py` (new), written before any configuration
  change and run red (R-TDR-1, R-TDR-2, R-TDR-4, R-TDR-5, R-TDR-7, R-TDR-11,
  R-TDR-12, DEC-TDR-004, DEC-TDR-005, DEC-TDR-012). A module docstring naming
  what the module holds and that it verifies this package's criteria. A
  `MYPY_TESTS_CEILINGS: dict[str, int] = {}` under the comment R-TDR-4
  requires. Pure helpers, each taking its input as an argument so the
  planted test is `unit`: the derived configuration (a parsed `[tool.mypy]`
  table in, mypy INI text out — every global key but `files`, every override
  but the `tests.*` one as a `[mypy-<module>]` section, booleans as
  `True`/`False`, lists comma-joined); the occurrence counter (mypy's stdout
  in, a code-to-count mapping out — `error:` lines only, path under `tests/`
  after normalising `\` to `/`); the ceiling comparison (listed codes,
  ceilings and counts in, the named offenders out: stale, above ceiling,
  occurring but unlisted, listed without a ceiling, ceiling without a listed
  code); the ignore-comment reader (module texts in, each `# type:
  ignore[...]` comment's codes out, read with `tokenize` so a string that
  looks like a comment is not one). Planned tests, named here so AC-TDR-3, 4,
  5, 8 and 9 can be re-pointed when they exist:
  `test_typecheck_reads_its_trees_from_the_mypy_files_list` (`integration`:
  the `typecheck` recipe's lines hold `python -m mypy` and no path argument;
  `[tool.mypy] files` holds `openspec_graph`, `tools` and `tests`;
  `explicit_package_bases` is true; `mypy_path` holds `tools`);
  `test_the_tests_override_is_one_entry_listing_exactly_the_ceilinged_codes`
  (`integration`: exactly one `[[tool.mypy.overrides]]` entry whose `module`
  matches `tests.*`, its keys exactly `module` and `disable_error_code`, its
  codes a subset of R-TDR-2's seven and equal to `MYPY_TESTS_CEILINGS`'
  keys; every other override is the `tomli` one with
  `ignore_missing_imports`);
  `test_every_listed_mypy_code_still_occurs_within_its_ceiling` (`e2e`: the
  derived configuration written under `tmp_path`, `[sys.executable, "-m",
  "mypy", "--config-file", <it>, "--cache-dir", <tmp_path>/cache,
  "--platform", "linux", "tests"]` from the repository root under
  `env_without_coverage()`, its stdout counted and compared);
  `test_every_unused_ignore_waiver_names_a_code_the_override_lists`
  (`integration`: every `tests/*.py`'s ignore comments; one holding
  `unused-ignore` and no listed code is named with its path and line);
  `test_a_planted_ratchet_violation_is_named` (`unit`, one parameter per
  case of R-TDR-11's mypy half: a stale code, a code occurring but unlisted,
  a code above its ceiling, a code listed without a ceiling, a ceiling
  without a code, a second option on the `tests.*` override, a `note:` line
  ending `[str]` not counted, an `error:` line with `tests\` counted, a
  derived configuration from a planted table that keeps every option and
  drops the `tests.*` override, an `unused-ignore` beside only `index` with
  `index` unlisted named; and the well-formed shape of each, quiet).
- Run `python -m pytest tests/test_static_ratchets.py -q -o addopts=""` and
  record the red: the recipe guard naming the recipe's two paths and a
  `files` without `tests`; the override guard finding no `tests.*` override;
  the occurrence guard naming every occurring code as unlisted (nothing is
  lifted because nothing is listed). The waiver guard is green on the tree —
  no comment carries `unused-ignore` yet, which is the expected shape — and
  its red on real input is shown by running its helper over the tree's own
  eight ignores, each given `unused-ignore` in memory, against a list without
  their codes, which names all eight; record that. Record whether the
  planted test passes from its first run, its helpers being written with it.
- Run `python -m pytest tests/test_suite_shape.py -q -o addopts=""` and
  record the new module's tiers agreeing with the criterion and its line
  count under the bound.
- **Gate:** `make test`, with this milestone's three red guards the only
  failures (written red first, they cannot be green before Milestone 2).

## Milestone 2 — The nine codes fixed, the override landed with its ceilings (the W6.5 commit)

- Fix the nine codes in `tests/`, each by annotation, narrowing, a typed
  local or a corrected call — never a new ignore, a cast to `Any`, a `noqa`
  or a removed assertion (R-TDR-3, C-TDR-3), at drafting:
  `tests/support.py` `read_pyproject` — `if sys.version_info >= (3, 11):
  import tomllib as toml_reader` / `else: import tomli as toml_reader`, no
  inline ignore, `parsed: dict[str, Any] = toml_reader.load(handle)` then
  `return parsed` (R-TDR-6; clears `import-not-found`, the `unused-ignore`
  and one `no-any-return`); `tests/conftest.py` `_reset_version_cache` →
  `-> Iterator[None]`; `tests/shape_support.py` `_class_facts` — the
  `nodes` list typed so `cls.bases` and `cls.decorator_list` (`list[expr]`)
  fit; `tests/test_mermaid.py` — the three single-node lists and `_graph`'s
  parameters typed so a `dict[str, str]` node is accepted (a `Sequence` of
  `Mapping[str, object]`, or the node annotated where it is built);
  `tests/test_dialect_card.py` `test_diff_cards_detects_an_adr_source_change`
  — `old` and `new` annotated as the `dict[str, object]` `diff_cards`
  takes; `tests/test_suite_shape.py`
  `test_a_mismarked_or_unmarked_planted_module_is_named` — the `str | None`
  narrowed before the `in`, on the same line count;
  `tests/test_cli_surface.py`
  `test_run_cli_injects_coverage_process_start_by_default` — the captured
  `env` narrowed to a mapping before the `in`; `tests/test_graph.py`
  `test_graph_covers_every_parsed_spec_when_multiple` — `graph["nodes"]`
  narrowed to a list of mappings before the generator;
  `tests/test_finding_line_hits.py`
  `test_section_body_still_returns_only_the_span_text` — the `not
  isinstance(result, tuple)` assertion kept, written so mypy does not judge
  it unreachable (the result widened to `object` for that check);
  `tests/test_action_contract.py`
  `test_the_step_extractor_sees_the_whole_action` — `scan["env"]` narrowed
  to a mapping before `set(...)`; `tests/test_graft_witness.py` `spy` in
  `test_current_sha_is_not_invoked_when_no_witnesses_are_present` — the
  spy's parameters and return typed so `original_run(*args, **kwargs)`
  matches an overload, and its stale `arg-type` ignore removed (unused
  before any override). Every edited test keeps its assertions; a fix that
  narrows with `assert isinstance(...)` adds an assertion and removes none.
- Re-run the guard's measurement by hand with nothing listed —
  `MYPYPATH=tools python -m mypy tests --explicit-package-bases --platform
  linux --cache-dir <scratch>` — and record: none of the nine codes occurs;
  the seven's per-code counts. These are the counts the first commit records
  (the plan's "per-code counts so the list only shrinks").
- `pyproject.toml` `[tool.mypy]`: `files`, `explicit_package_bases`,
  `mypy_path` and the two overrides of the proposal's What Changes, each
  with its comment; `Makefile` `typecheck` recipe → `python -m mypy`, help
  text naming `[tool.mypy] files`. Run `make typecheck` and record the eight
  `unused-ignore` it then reports — the expected red of R-TDR-7 — then give
  each of the eight comments `unused-ignore` beside its code (DEC-TDR-006)
  and re-run: exit 0.
- Fill `MYPY_TESTS_CEILINGS` from the occurrence guard's own measurement on
  this tree (its failure message names each code's count while the mapping
  is empty), and record the mapping here with the commit.
- Run `python -m pytest tests/test_static_ratchets.py tests/test_ci_workflow.py
  tests/test_enterprise.py -q -o addopts=""` and record green, with
  `test_a_bare_generic_in_tools_fails_typecheck`,
  `test_mypy_fails_on_a_type_error` and `test_typecheck_passes_on_clean_repo`
  among them — the planted-tree tests under a copy of the new configuration,
  the clean-repo test now checking `tests/` too (AC-TDR-1, AC-TDR-2). Record
  the call durations of the occurrence guard and of
  `test_typecheck_passes_on_clean_repo` from `--durations=0` over that
  selection, and the type gate's cold wall time after: `TIMEFORMAT='%R s';
  time python -m mypy --cache-dir /dev/null` (3.7 s expected from the
  emulation).
- `CHANGELOG.md` `[Unreleased]`: `### Changed — tests under mypy, public
  docstrings by ratchet (M2)`, the W6.5 half — the three trees from `files`,
  the search path and why, the override's codes with their ceilings, the
  nine codes fixed instead, the `tomli` override, the waivers, the guard
  module, and R-ZCG-3's `files` clause superseded by name (R-TDR-14,
  R-TDR-15).
- Commit (the W6.5 commit), naming the ceilings in the message, and record
  the pull request's first CI run on it: the type gate and the occurrence
  guard green on every `test` leg and on `test-windows`, with the run id
  (AC-TDR-20, C-TDR-5). A leg that differs is a fact about the leg, recorded
  here, and is fixed before Milestone 3 — never by raising a ceiling.
- **Gate:** `make typecheck`, then `make test`

## Milestone 3 — Docstrings by ratchet, guards seen red first (the W6.6 commit)

- `tests/test_static_ratchets.py`, written before the configuration and run
  red (R-TDR-8, R-TDR-9, R-TDR-11, DEC-TDR-008, DEC-TDR-009): a
  `DOCSTRING_CEILINGS: dict[str, dict[str, int]] = {}` under the same
  comment; pure helpers for the per-file-ignores shape (a parsed
  `per-file-ignores` table in, offenders out) and for ruff's JSON (findings
  and a root in, a file-to-code-to-count mapping out, paths relative and in
  POSIX form). Planned tests, named here so AC-TDR-12 and 13 can be
  re-pointed: `test_docstring_exemptions_are_file_entries_matching_their_ceilings`
  (`integration`: `D100`–`D103` in `select` and no other `D` rule; every
  `D` code under a concrete file key under `openspec_graph/` or `tools/` or
  under `tests/*`, which carries all four; the ratchet pairs equal to
  `DOCSTRING_CEILINGS`' pairs; no `[tool.ruff.lint.pydocstyle]` table);
  `test_every_docstring_exemption_still_offends_within_its_ceiling` (`e2e`:
  `[sys.executable, "-m", "ruff", "check", "--no-cache", "--select",
  "D100,D101,D102,D103", "--config", "lint.per-file-ignores = {}",
  "--output-format", "json", "--exit-zero", "openspec_graph", "tools"]` from
  the repository root under `env_without_coverage()`, its findings counted
  and compared: stale, above ceiling, offending but unlisted); and the
  docstring half of `test_a_planted_ratchet_violation_is_named` (a pair with
  no finding, a pair offending but unlisted, a pair above its ceiling, a
  pair without a ceiling, a `D` code under `openspec_graph/*`, a `D` code
  under `tests/test_x.py`, a Windows path in ruff's JSON normalised; the
  well-formed shape of each, quiet). Record the red: the shape guard finding
  `D` unselected; the occurrence guard naming every offending pair as
  unlisted.
- `pyproject.toml`: the `select` entries and their comment; the `ANN/D`
  comment rewritten with the measured convention and the command behind it
  (R-TDR-10, DEC-TDR-010); `tests/*` gains the four codes; one entry per
  offending file of Milestone 0's list with exactly its codes, `cli.py`'s
  joining its `T201` entry; a comment above them naming the ratchet, the
  guard, and that an entry leaves in the pull request that documents its
  file. No convention key.
- Fill `DOCSTRING_CEILINGS` from the occurrence guard's measurement and
  record it here with the commit. Run `make lint` (exit 0) and `python -m
  pytest tests/test_static_ratchets.py tests/test_ci_workflow.py -q -o
  addopts=""` and record green, `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt`
  and `test_a_print_in_a_library_module_fails_lint` among them (AC-TDR-10,
  AC-TDR-11). Record the docstring guard's call duration.
- `CHANGELOG.md`: the W6.6 half — the four codes, the per-file entries with
  their count, the `tests/` policy exemption and why, the convention
  recorded and not configured.
- Commit (the W6.6 commit) and record the pull request's CI run on it.
- **Gate:** `make lint`, then `make test`

## Milestone 4 — Documents, records and the verification lines

- `docs/hooks.md:19` → `make typecheck` (mypy) across `openspec_graph/`,
  `tools/`, `tests/`, with `tests/` under a per-code baseline in
  `[[tool.mypy.overrides]]`. `tests/AGENTS.md` — one sentence that
  `make typecheck` covers this directory and that a new occurrence of an
  exempted code fails `test_static_ratchets.py`, written by replacing, not
  adding: the closing run paragraph's five lines can carry it in five, for
  example by folding "`make coverage-tools` re-reads `tools/` from the same
  report. The `planlint-verifier` subagent runs the whole ladder." into one
  line; record `wc -l` after against `MAX_NESTED_LINES`.
  `.claude/agents/planlint-verifier.md:28` — the `ruff`/`mypy` bullet names
  the standing configuration and the remediation norm of R-TDR-13, in the
  shape of the coverage and matcher-floor bullets beside it. Run `python -m
  pytest tests/test_agent_artifacts.py -q -k "nested_agents or
  agent_index_links"` and `make docs-check`; record green.
- Re-point the stage-only verification lines in
  `specs/static-check-ratchets/spec.md` to the guards now that they exist,
  keeping each stage: AC-TDR-3 →
  `test_typecheck_reads_its_trees_from_the_mypy_files_list`; AC-TDR-4 →
  `test_the_tests_override_is_one_entry_listing_exactly_the_ceilinged_codes`;
  AC-TDR-5 → `test_every_listed_mypy_code_still_occurs_within_its_ceiling`;
  AC-TDR-8 → `test_every_unused_ignore_waiver_names_a_code_the_override_lists`;
  AC-TDR-9 and AC-TDR-13 → `test_a_planted_ratchet_violation_is_named`;
  AC-TDR-12 → `test_docstring_exemptions_are_file_entries_matching_their_ceilings`
  and `test_every_docstring_exemption_still_offends_within_its_ceiling`. Run
  `python -m pytest tests/test_spec_test_citations.py -q -p
  no:cacheprovider` and record that every selector in every spec resolves.
- Confirm this package validates clean (`planlint --target . validate
  --fail-on ERROR --change ratchet-test-types-and-docstrings`), then
  `--change select-zero-cost-guards` and `--change shape-the-test-suite`
  (unedited, must still be clean), then the whole tree; record each exit
  code.
- Confirm the boundaries in the diff against the branch base: no file under
  `openspec_graph/`, `.github/` or another change package; no
  `.pre-commit-config.yaml` hunk; the only `Makefile` hunk the `typecheck`
  recipe and its help text; no `[project] dependencies` or dev-extra line
  (C-TDR-1, C-TDR-2). `make thresholds`: PASS. `make stage-citations` after,
  recorded with the note that its figures include this package's spec.
- Re-take the header's measurements on the finished tree: the per-code
  counts with the override lifted (equal to the ceilings), the per-file
  docstring counts (equal to theirs), `wc -l tests/AGENTS.md`, the new
  module's line count, the two guards' durations.
- Tick each criterion only against its recorded evidence; AC-TDR-20 only with
  the CI run id of Milestone 2.
- Record for the plan's §7 rows, when they are next updated: tests under
  mypy, with the override's codes and ceilings as recorded here rather than
  the plan's "86 errors, ~52 real"; public symbols without a docstring as
  the package's and `tools/`'s ceilings, with `tests/` exempt by policy.
- **Gate:** `make pre-pr`
