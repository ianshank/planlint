# Tasks: select-zero-cost-guards

## Milestone 1 — Bring the two scripts onto `_common`

- `tools/_common.py`: add `read_json(path: Path) -> dict[str, Any]`, reading
  `path.read_text(encoding="utf-8")` directly (not via `read_text`, so a
  missing file is still a `FileNotFoundError`), parsing, raising
  `ValueError` naming the path when the top level is not a mapping, and
  emitting one DEBUG record on `logger` naming the file and its size. The
  `isinstance` narrowing is a real branch; `tests/test_gate_scripts.py` gains
  `test_read_json_rejects_a_non_mapping_document` and
  `test_read_json_reports_a_missing_file_by_name` for it (AC-ZCG-19).
  Stdlib imports only — `test_common_module_is_stdlib_only` holds the line
  (R-ZCG-9, DEC-ZCG-006).
- `tools/diff_spec_graph.py`: the `sys.path.insert` bootstrap and
  `from _common import logger, read_json`; `orphan_ids(graph: dict[str, Any])`
  and `diff(base: dict[str, Any], head: dict[str, Any])`; `main(argv)` builds
  an `argparse.ArgumentParser` with positional `base` and `head`, parses
  `list(argv[1:])`, reads both files through `read_json`, and logs one DEBUG
  record for the decision — base and head `broken_links`, count of new
  orphans. Keep the `PASS:` / `FAIL:` lines and the 0/1 returns exactly;
  drop the `len(argv) != 3` branch and the hand-written usage print
  (R-ZCG-4, R-ZCG-5, R-ZCG-6, R-ZCG-7, R-ZCG-8, DEC-ZCG-005, DEC-ZCG-007).
- `tools/render_mermaid.py`: the bootstrap, `from _common import logger,
  read_json, repo_root`, then `sys.path.insert(0, str(repo_root()))` before
  the `openspec_graph.mermaid` import, as `matcher_accuracy.py` and
  `stage_citations.py` do; `main(argv)` with positional `graph`, parsing
  `list(argv[1:])`; one DEBUG record naming the node and edge counts
  rendered. Stdout stays `to_mermaid(graph)` with nothing appended; drop the
  `len(argv) != 2` branch (R-ZCG-5, R-ZCG-6, R-ZCG-7, R-ZCG-8, DEC-ZCG-009).
- `tests/test_ci_hardening.py`: rewrite `test_graph_diff_rejects_bad_args`
  and `test_render_mermaid_rejects_bad_args` under their existing names to
  the `pytest.raises(SystemExit)` form of `test_plugin_manifests_require_a_mode`
  — assert `code == 2`, `usage:` in `capsys` stderr, and an empty stdout
  (AC-ZCG-6, AC-ZCG-8).
- `tests/test_ci_hardening.py`: add `test_graph_diff_help_exits_zero` and
  `test_render_mermaid_help_exits_zero` — `--help` raises `SystemExit` with
  code 0 and the usage text lands on stdout (AC-ZCG-9).
- `tests/support.py`: add `captured_logger(caplog, name)`, a context manager
  that attaches `caplog.handler` to `logging.getLogger(name)` at DEBUG and
  detaches it in `finally` — the body of `tests/test_witness.py`'s
  `_captured`, moved so three modules share one copy (R-ZCG-14).
- `tests/test_gate_scripts.py`: rewrite
  `test_plugin_manifests_verbose_logs_without_polluting_stdout` on the
  helper (same name, so its citation survives) — reproduce first:
  `python -m pytest tests/test_gate_scripts.py -k verbose_logs` fails today
  with `caplog.records == []`; it passes after (AC-ZCG-20).
- `tests/test_ci_hardening.py`: add
  `test_graph_diff_logs_its_decision_without_polluting_stdout` and
  `test_render_mermaid_logs_the_node_count_without_polluting_stdout`, using
  `captured_logger(caplog, "planlint.tools")` and asserting the records are
  absent from `capsys` stdout (AC-ZCG-11, DEC-ZCG-008).
- Confirm the four verdict tests, the byte-for-byte test and the
  runnable-as-a-script test pass unchanged (AC-ZCG-5, AC-ZCG-7, AC-ZCG-10).
- **Gate:** `make coverage-tools`

## Milestone 2 — Select `T201`

- `tests/test_decomposition.py`: in `test_output_byte_identical`, collect the
  per-verb diagnostic lines into a list and join them into the assertion
  message in place of "(normalized per-verb output dumped above)"; delete the
  two `print` calls; keep the comment explaining why the failure is
  self-diagnosing (C-ZCG-1, DEC-ZCG-002).
- `pyproject.toml` `[tool.ruff.lint]`: add `"T201"` to `select` with a
  one-line reason; rewrite the comment-block line that names `T20` as
  deliberately unselected so it states the new fact — `print` is the
  product in `cli.py` and the scripts, and the rule keeps it there
  (R-ZCG-1, R-ZCG-13, DEC-ZCG-001).
- `pyproject.toml` `[tool.ruff.lint.per-file-ignores]`: add
  `"openspec_graph/cli.py" = ["T201"]` and append `"T201"` to the existing
  `"tools/*"` list. No `tests/*` entry for it, and no `noqa: T201` anywhere
  (R-ZCG-1, C-ZCG-1).
- Run `python -m ruff check openspec_graph tests tools` and confirm zero
  findings; the only family added is at zero (C-ZCG-2, AC-ZCG-18).
- **Gate:** `make lint`

## Milestone 3 — Turn on strict

- `pyproject.toml` `[tool.mypy]`: `strict = true` and
  `warn_unreachable = true`; keep `python_version = "3.10"` and
  `files = ["openspec_graph", "tools"]`; remove `check_untyped_defs`,
  `warn_unused_ignores`, `warn_redundant_casts`, `warn_return_any` and
  `no_implicit_optional`; replace the "pragmatic strictness" comment with
  one that names the removed flags as subsumed by `strict` and says why
  `warn_unreachable` is listed on its own (R-ZCG-3, DEC-ZCG-003,
  DEC-ZCG-004).
- Run `python -m mypy openspec_graph tools` and confirm zero findings — the
  two `type-arg` errors were cleared by Milestone 1, and the unreachable
  check was measured at zero before this landed (AC-ZCG-3).
- **Gate:** `make typecheck`

## Milestone 4 — Guard the configuration and update the record

- `tests/test_ci_hardening.py`, in the section headed as claims about the CI
  configuration itself, beside `test_lint_is_a_hard_gate`: a module-level
  `_pyproject()` helper that parses `REPO_ROOT / "pyproject.toml"` with
  `tomllib`, falling back to `tomli` under 3.10 (R-ZCG-10, DEC-ZCG-010).
- `tests/test_ci_hardening.py`: add
  `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt` — `"T201"`
  in `[tool.ruff.lint].select`, and the set of per-file-ignores keys whose
  list contains `"T201"` is exactly `{"openspec_graph/cli.py", "tools/*"}`.
  Assert nothing else about `select` (R-ZCG-10, AC-ZCG-1).
- `tests/test_ci_hardening.py`: add
  `test_mypy_is_strict_and_warns_on_unreachable_code` — `[tool.mypy].strict`
  and `.warn_unreachable` are both `True`, and `python_version` is still
  `"3.10"` (R-ZCG-10, AC-ZCG-3).
- `tests/test_ci_hardening.py`: add
  `test_a_print_in_a_library_module_fails_lint` — copy `pyproject.toml` into
  `tmp_path`, plant `print("x")` in `openspec_graph/leak.py`,
  `openspec_graph/cli.py` and `tools/t.py` under it, run
  `python -m ruff check --select T201 openspec_graph tools` from there, and
  assert exactly one finding, at `leak.py` (R-ZCG-11, AC-ZCG-2,
  DEC-ZCG-011).
- `tests/test_ci_hardening.py`: add
  `test_a_bare_generic_in_tools_fails_typecheck` — plant
  `def f(d: dict) -> None: ...` in a module under `tmp_path`, run
  `python -m mypy --config-file <copied pyproject> <module>`, and assert a
  non-zero exit whose stdout names `type-arg` (R-ZCG-11, AC-ZCG-4,
  DEC-ZCG-011). Build the child environment with `env_without_coverage()`
  as the sibling subprocess tests do.
- `tests/support.py`: `run_tool_main`'s docstring — the program-name-first
  group is the five hand-rolled scripts plus `matcher_accuracy`,
  `stage_citations`, `diff_spec_graph` and `render_mermaid`, which strip the
  name themselves; the arguments-only group is unchanged (R-ZCG-13,
  DEC-ZCG-013).
- `tools/AGENTS.md`: the argv-conventions paragraph, same regrouping. Leave
  the stdlib-only / package-importing split and
  `docs/architecture/c4.md`'s `tools/*` row alone — neither script changes
  group (R-ZCG-13, DEC-ZCG-013, AC-ZCG-17).
- **Gate:** `make test`

## Milestone 5 — Confirm and record

- Re-run the three measurements from the proposal at the finished tree and
  confirm each reads zero: `ruff check --select T201` over
  `openspec_graph tests tools`, `mypy` over `openspec_graph tools`, and the
  unreachable check — so the Evidence paragraph describes a before and the
  gates describe an after.
- Confirm `make lint`, `make typecheck`, `make test` and `make coverage-tools`
  are each green, and that the `Makefile` and `.github/workflows/ci.yml`
  show no diff (C-ZCG-3, AC-ZCG-14, AC-ZCG-15).
- Re-point AC-ZCG-1, 2, 4, 9 and 11 from stage-only verification to the
  tests named in Milestones 1 and 4, now that they exist, and confirm every
  `pytest -k` selector in the spec resolves
  (`tests/test_spec_test_citations.py`).
- Confirm this package validates clean under the repo's own rules.
- **Gate:** `make pre-pr`
