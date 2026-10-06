# Change: Select the Zero-Cost Guards

## Why

Three properties of this tree hold today and are enforced by nothing. No
module in `openspec_graph/` other than `cli.py` calls `print`; `mypy --strict`
is two findings away from clean; and ten of the twelve scripts under `tools/`
share their repo-root, logging and file-reading conventions through
`tools/_common.py`. Each is a fact a reviewer would have to re-check by hand
on every pull request, because the gates as configured would let any of them
drift without a red build. The reflection plan's milestone M0 (items W4.2,
W5.4 and W6.1; guardrail 4, "ratchet, then gate"; decisions D1 and D6;
findings 6 and 15) names these as the guards that cost nothing to turn on —
the plan itself is on its own branch and not in this tree at drafting time,
so its items are restated here and this package stands on its own evidence.

The posture is the one `pyproject.toml`'s own ruff comment already states:
"every family here was at or near zero violations when it was turned on, so
each one locks in a property the code already has rather than starting a
cleanup backlog." This change adds only families and settings that are at
zero after its own edits. It does not select the families with a backlog;
those are ratchets for later milestones.

**Evidence:** measured at the drafting commit (`9c4b6e9`); each command
re-measures it.

- **`print` is confined to the CLI and the scripts, by accident.**
  `python -m ruff check --select T201 --statistics openspec_graph tools`
  reports 123 findings: 80 in `openspec_graph/cli.py` and 43 across the
  files under `tools/` (three of them in `tools/_common.py`'s
  `write_or_check`). Not one is in any other `openspec_graph` module.
  `pyproject.toml`'s `[tool.ruff.lint] select` lists `E4`, `E7`, `E9`, `F`,
  `I`, `B`, `S`, `UP`, `SIM`, `RET`, `C4`, `PIE`, `ICN`, `TID`, `EXE`,
  `ISC`, `Q`, `DTZ`, `N`, `RUF`; its comment block names `T20` as
  deliberately unselected ("this is a CLI. `print` is the product"), which
  is true of `cli.py` and of nothing else in the package. `make lint` is
  `python -m ruff check openspec_graph tests tools` (`Makefile`, `lint`
  target), so the same scan over `tests/` matters too: it finds two more,
  the self-diagnosing dump in `tests/test_decomposition.py`'s
  `test_output_byte_identical`.
- **`mypy --strict` is two findings from clean, both in one file.**
  `python -m mypy --strict openspec_graph tools` reports exactly two errors,
  both `[type-arg]` "Missing type arguments for generic type `dict`", at
  `tools/diff_spec_graph.py:20` (`orphan_ids(graph: dict)`) and `:24`
  (`diff(base: dict, head: dict)`). Adding `--warn-unreachable` reports the
  same two and nothing else. The current `[tool.mypy]` table is
  `python_version = "3.10"`, `check_untyped_defs`, `warn_unused_ignores`,
  `warn_redundant_casts`, `warn_return_any`, `no_implicit_optional`, and
  `files = ["openspec_graph", "tools"]`. `python -m mypy --help` lists what
  `--strict` enables — `disallow-any-generics` through `extra-checks` — and
  `warn-unreachable` is not among them, so it has to be named separately.
  `post-merge-quality-review`'s DEC-PR-001 declined `strict = true` because
  "`tools/` would require further annotation churn"; the churn is now two
  annotations in a file this change rewrites anyway.
- **Two scripts hand-roll what `_common` provides.** `tools/diff_spec_graph.py`
  and `tools/render_mermaid.py` are the only scripts under `tools/` that do
  not import `tools/_common.py` — which provides `repo_root()`, the
  `planlint.tools` `logger` (stderr, level from `PLANLINT_LOG_LEVEL`, silent
  by default), `read_text()` and `write_or_check()`. Both test `sys.argv` by
  length (`len(argv) != 3` at `diff_spec_graph.py:38`, `len(argv) != 2` at
  `render_mermaid.py:26` — the two `PLR2004` findings `ruff` reports under
  `tools/` when that unselected rule is asked for), and both print their own
  usage line to stderr with exit 2. Their contracts are pinned:
  `tests/test_ci_hardening.py`'s `test_graph_diff_passes_when_clean`,
  `test_graph_diff_fails_on_new_broken_edges`,
  `test_graph_diff_fails_on_new_orphan`,
  `test_graph_diff_passes_when_orphan_fixed`,
  `test_graph_diff_rejects_bad_args`,
  `test_render_mermaid_matches_to_mermaid_byte_for_byte`,
  `test_render_mermaid_rejects_bad_args` and
  `test_gate_script_is_runnable_as_a_script`; and
  `.github/workflows/ci.yml`'s `graph-diff` step runs
  `python tools/diff_spec_graph.py base.json head.json` in the `graph-diff`
  job. The `Makefile`'s `graph-mermaid` target invokes the CLI's
  `--format mermaid` directly and does not call `render_mermaid.py`; nothing
  in the `Makefile` or any workflow does, so the byte-for-byte test is the
  whole of that script's external contract.
- **Both gates are hard, everywhere.** `make lint` and `make typecheck` run
  as steps on every leg of the `test` matrix (3.10 through 3.13) and on
  `test-windows` (`.github/workflows/ci.yml`), and as commit-time hooks
  (`docs/hooks.md`). `tools/` is additionally held to its own coverage floors
  by `make coverage-tools` (`[tool.specgraph] tools_line_fail_under` and
  `tools_branch_fail_under`), so any new code path in the two scripts needs a
  test or the scoped gate reports it.

## What Changes

- `tools/_common.py`: one new helper, `read_json(path) -> dict[str, Any]`,
  which reads UTF-8, parses, and emits a DEBUG record naming the file and
  its size on the existing `planlint.tools` logger. Both scripts read every
  input file through it. Stdlib-only, as the module's own contract and
  `test_common_module_is_stdlib_only` require.
- `tools/diff_spec_graph.py`: the `sys.path` bootstrap and
  `from _common import logger, read_json`; `main(argv)` builds an
  `argparse.ArgumentParser` with the same two positional arguments
  (`base.json`, `head.json`) and parses `argv[1:]`, so `main` still receives
  `sys.argv` program-name-first and `run_tool_main`'s default `pass_argv0`
  still applies; `orphan_ids` and `diff` take `dict[str, Any]`; a DEBUG
  record per file read and one for the decision (base and head
  `broken_links`, how many new orphans). The `PASS:`/`FAIL:` stdout lines
  and the 0/1 verdicts are unchanged; a usage error is argparse's own
  `SystemExit(2)` with the usage text on stderr and nothing on stdout.
- `tools/render_mermaid.py`: the same `_common` adoption with one positional
  argument (`graph.json`), plus `sys.path.insert(0, str(repo_root()))` after
  the `_common` import, the bootstrap its sibling generators
  `matcher_accuracy.py` and `stage_citations.py` already carry so the script
  runs from a checkout without the package installed; a DEBUG record for
  the file read and one naming how many nodes and edges were rendered.
  Stdout stays `to_mermaid(graph)` with nothing appended.
- `pyproject.toml` `[tool.ruff.lint]`: `select` gains `"T201"`;
  `[tool.ruff.lint.per-file-ignores]` gains
  `"openspec_graph/cli.py" = ["T201"]` and adds `"T201"` to the existing
  `"tools/*"` list; the comment block's `T20` line is rewritten to say what
  is now true — `print` is the product in exactly two places, and the rule
  keeps it there.
- `pyproject.toml` `[tool.mypy]`: `strict = true` and
  `warn_unreachable = true`; `python_version = "3.10"` and `files` kept; the
  four flags `strict` subsumes (`check_untyped_defs`, `warn_unused_ignores`,
  `warn_redundant_casts`, `warn_return_any`) and the default-on
  `no_implicit_optional` are removed, with the comment naming them as
  subsumed so the table reads as the whole policy.
- `tests/test_decomposition.py`: `test_output_byte_identical`'s two
  diagnostic `print` calls become part of the assertion message it already
  builds, so the per-verb dump still reaches the CI log on failure and the
  `tests/` tree needs no `T201` exemption.
- `tests/test_ci_hardening.py`: the two `rejects_bad_args` tests keep their
  names and move to the `pytest.raises(SystemExit)` form
  `test_plugin_manifests_require_a_mode` already uses, asserting code 2,
  usage on stderr and an empty stdout; new tests for `--help` exiting 0 on
  each script, for the DEBUG records landing on the logger and not on stdout
  (the `caplog` pattern of
  `test_plugin_manifests_verbose_logs_without_polluting_stdout`), and — in
  the "claims about the CI configuration itself" section beside
  `test_lint_is_a_hard_gate` — two structural guards that parse
  `pyproject.toml` and assert `T201` is selected with exactly the two
  exemptions and that `[tool.mypy]` is strict with `warn_unreachable`, plus
  two behavioural guards that run ruff and mypy under this repository's own
  configuration against a planted `print` in a library module and a planted
  bare `dict` in a `tools/`-shaped module, so each gate is shown to fire.
- `tests/support.py`: `run_tool_main`'s docstring regroups the argv
  conventions — five hand-rolled scripts, and four argparse scripts that
  strip the program name themselves.
- `tools/AGENTS.md`: the same regrouping in its argv-conventions paragraph.
  `docs/architecture/c4.md`'s `tools/*` row is untouched: it groups the
  scripts by dependency (stdlib-only gates versus package-importing
  generators), and neither script changes group.

## Non-Goals

- **No ratchet families.** `C901`, `PLR`, `E501`, `FBT`, `PERF` and `D` are
  not selected. Each has a backlog today (`docs/next-steps.md` items 18 and
  23 count `E501` and `C901`), so selecting one would start a cleanup rather
  than lock in a property — the opposite of guardrail 4. The two `PLR2004`
  findings disappear as a side effect of the argparse rewrite; `PL` stays
  unselected.
- **No new rule.** The `RULES` tuple in `openspec_graph/rules.py`,
  `README.md`'s rules table and `tests/baseline_rules.json` are untouched.
  Nothing here is a finding about anyone's specs.
- **No change to any `make` target, workflow step, or script invocation.**
  `make lint` and `make typecheck` keep their recipes; the `graph-diff` step keeps
  `python tools/diff_spec_graph.py base.json head.json`; both scripts keep
  their positional arguments and their 0/1/2 exit codes.
- **No `-v` flag on either script.** `_common.logger` already reads
  `PLANLINT_LOG_LEVEL`, and one environment variable covering the CLI and
  every tool is the convention `_common.py` states; a per-script flag would
  be a second way to ask for the same thing.
- **No `T203` (`pprint`) and no `T20` family.** The invariant this change
  states is about `print`; nothing in the tree calls `pprint`, so selecting
  it would guard a property no one has asserted.
- **No refactor of `_common.coverage_totals`** onto the new `read_json`,
  although it parses JSON the same way. That is a pure move inside a gate
  script with its own tests, and belongs in its own change if it is worth
  making at all.
- **No change to `run_tool_main` or to the `pass_argv0` default** for the
  two scripts. They stay in the program-name-first group by parsing
  `argv[1:]` themselves, exactly as `matcher_accuracy` and `stage_citations`
  do, so no caller changes.

## Affected Capabilities

- `zero-cost-guards`
