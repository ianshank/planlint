# Tasks: raise-coding-standards

Drafted on 2026-10-16 at `bfbc124`, the tip of `origin/dev` and the base of
`claude/raise-coding-standards`, from a review of `dev` dated the same day.
Revised twice on 2026-10-17, to resolve the package's first and second
adversarial reviews. Every figure below names the command that produced it
and was taken at `bfbc124` unless its bullet says otherwise. A figure from
an adversarial review's own runs is marked as the review's and points at
its log or tree. Every line number is re-read at the implementation head
before the milestone that uses it, because a sibling landing first moves a
line without moving the fact.

The environment: Python 3.13.16, ruff 0.17.0, mypy 2.4.0 (compiled), pytest
9.1.1, hypothesis 6.169.2, coverage 7.16.2, pytest-cov 7.1.0, pip 24.0 and
four cores (`nproc`). `anyio` 4.15.1 is installed here and registers a pytest
plugin; the dev extra does not install it. PyPI's latest ruff is 0.17.1 and
its latest hypothesis 6.170.1, so a fresh CI install can differ from this
container, and Milestone 0 re-measures on the implementation's own install.

For the revisions, these interpreters were also run, read-only, from the
first review's scratch: CPython 3.10.20 and 3.14.6 (uv builds), 3.15.0 (a
build that needs `LD_LIBRARY_PATH` set to its own `lib/`), and the system's
3.11.17 and 3.12.3. The ruff 0.17.1 binary is the review's
`review-rcs/ruff171/bin/ruff`.

Every ruff run used `--no-cache`, and every mypy run used
`--cache-dir=/dev/null`. Each pytest run used `-p no:cacheprovider`. From the
point noted below, every Python process ran under `PYTHONDONTWRITEBYTECODE=1`.
Scratch inputs were written under the session scratchpad only:
- `measure-rcs/`, for the draft:
  - `rule_types_literal.py`, the shadow copy of `openspec_graph/rule_types.py`;
  - `derived.ini`, the ratchet guard's derived mypy configuration, as
    `tests/ratchet_support.py`'s `derive_config` prints it;
  - `time_cli_calls.py`, a timing plugin.
- `resolve-rcs/`, for the revisions:
  - `strictcfg-both/`, `strictcfg-filter-only/`, `warn-run/` and
    `xpass-run/`, nested pytest trees;
  - `nested-cfg/`, a ruff tree with a nested `tests/ruff.toml` and a
    `pkg/.ignore`;
  - `default-exclude/`, a ruff tree with `openspec_graph/dist/planted.py`.

The reviews' scratch was read and run but never written:
- the first review's `review-rcs/`:
  - its ruff trees, `probe-planted/` and `probe-ignores/`;
  - `pth_probe2.py` and `plugin/rcs_time_cli.py`;
  - `run_suite.sh`, with its per-interpreter logs and its trees;
- the second review's `review-rcs-2/`:
  - `tv/tree-py38/` and `tv2/p.py`;
  - `bin/tv_reader.py`, whose reader functions were evaluated in memory;
  - its `tvr/c*/` trees, where `ruff check --no-cache --show-settings` was
    run.

## Measured at `bfbc124` (2026-10-16, revised 2026-10-17)

### The gate and the reports

- **The gate before any file of this package existed.** `planlint --target .
  validate --fail-on ERROR` printed `57 spec(s) checked · 0 error · 0 warn · 0
  info`, `PASS`, exit 0.
  - The installed `planlint` imports `/home/user/planlint/openspec_graph`,
    the main checkout, which is on another branch
    (`claude/release-0.3.0-tag-day`).
  - So the gate was also run on the worktree's own package:
    `PYTHONPATH=<worktree> python -m openspec_graph.cli --target . validate
    --fail-on ERROR` printed the same, exit 0.
- **The CI run on `bfbc124`.** `gh run list -R ianshank/planlint -b dev -w CI`
  names run 38978395109, event `push`, conclusion `success`. Its jobs:
  - success: every `test` leg 3.10 to 3.14, `test-windows`,
    `encoding-stress`, `self-validate`, `packaging`, `security`, `docs`,
    `promotion`, all five `action-contract` cases and `ci-ok`;
  - skipped: `graph-diff` and `release-tier`, by their conditions.

  The job logs could not be read from here. `gh api
  repos/ianshank/planlint/actions/jobs/<id>/logs` follows a redirect to blob
  storage that the session proxy answers with 403, so no leg's pytest
  warning summary was read.

### Ruff

- **The fifteen zero-hit families.** `python -m ruff check --no-cache --select
  <family> --statistics openspec_graph tools tests` printed nothing and
  exited 0 for each of A, BLE, FA, FLY, G, LOG, PGH, SLOT, T10, YTT, INT,
  ASYNC, FIX, TD and PLE. The same with `--isolated --ignore-noqa
  --output-format concise` printed no finding line for any of them.
- **Their rule counts.** `python -m ruff rule --all --output-format json`,
  counted by code prefix, gives the stable and preview rules of each:

  | family | stable | preview |
  |---|---|---|
  | A | 6 | 0 |
  | BLE | 1 | 0 |
  | FA | 2 | 0 |
  | FLY | 1 | 0 |
  | G | 8 | 0 |
  | LOG | 7 | 0 |
  | PGH | 5 | 0 |
  | SLOT | 3 | 0 |
  | T10 | 1 | 0 |
  | YTT | 10 | 0 |
  | INT | 3 | 0 |
  | ASYNC | 15 | 1 |
  | FIX | 4 | 0 |
  | TD | 7 | 0 |
  | PLE | 36 | 2 |
  | PTH | 35 | 0 |
  | FURB | 22 | 14 |
  | PYI | 55 | 0 |
  | PT | 30 | 1 |
  | ERA | 1 | 0 |

- **FA is inert at this floor.**
  - `python -m ruff rule FA100` and `FA102` each read: "if your project
    targets Python 3.10 and above, adding `from __future__ import
    annotations` does not impact your ability to leverage PEP 604-style
    unions … As such, this rule will only flag such usages if your project
    targets Python 3.9 or below."
  - A probe on stdin, `def f(x: int | None) -> list[int]: return []`
    through `python -m ruff check --no-cache --isolated --select FA
    --target-version <t> --stdin-filename p.py -`, printed "All checks
    passed!" at `py310` and `FA102 Missing from __future__ import
    annotations, but uses PEP 604 union` at `py39`.
- **TD is subsumed by FIX.** Nine comment lines were piped through
  `python -m ruff check --no-cache --isolated --select FIX,TD --output-format
  concise --stdin-filename probe.py -`: `# TODO: a`, `# todo: b`,
  `# TODO(ian): c`, `# FIXME d`, `# XXX e`, `# HACK f`, `# Todo g`,
  `#TODO h` and `# TODO i`.
  - It reported 33 findings.
  - Every line carrying a TD finding (all but `HACK`) also carried a FIX
    finding, and `HACK` carried FIX004 only.
- **The near-zero families, by site.** `python -m ruff check --no-cache
  --select <family> --output-format concise openspec_graph tools tests`:

  | family | count | site | code |
  |---|---|---|---|
  | FURB | 5 (all `[*]`) | `openspec_graph/rules.py:113` | FURB110 |
  | | | `tests/test_properties.py:118` | FURB110 |
  | | | `tools/_common.py:317` (`_SOURCE_ARRAY`) | FURB167 |
  | | | `tools/_common.py:324` (`normalize_scope`) | FURB188 |
  | | | `tools/check_promotion.py:289` (`write_github_output`) | FURB122 |
  | PYI | 1 (`[*]`) | `openspec_graph/delta.py:225` (`_mentions_value`) | PYI041 |
  | PT011 | 6 | `tests/test_claude_guard.py:151` | PT011 |
  | | | `tests/test_release_surface.py:174`, `:176`, `:178` | PT011 |
  | | | `tests/test_witness.py:295`, `:330` | PT011 |
  | PTH | 4 | `openspec_graph/witness.py:130`, `:135` (`os.replace`, `os.unlink`) | PTH105, PTH108 |
  | | | `tests/test_enterprise.py:472` (`glob.glob`) | PTH207 |
  | | | `tools/check_promotion.py:288` (`open`) | PTH123 |
  | ERA | 2 | `openspec_graph/parse_semantics.py:231` | ERA001 |
  | | | `tests/test_parse_speckit.py:36` | ERA001 |

  - The review counted FURB as five, four of them auto-fixable. Ruff 0.17.0
    marks all five safe-fixable.
  - `python -m ruff check --no-cache --select FURB --diff openspec_graph
    tools tests` prints the five fixes:
    - `line if line else "unset"` → `line or "unset"`;
    - `separator if separator else "\n"` → `separator or "\n"`;
    - `re.S` → `re.DOTALL`;
    - `if name.startswith("./"): name = name[2:]` →
      `name = name.removeprefix("./")`;
    - the `for` loop of `handle.write` → `handle.writelines(<generator>)`.

    Each operand of the two `or` rewrites is a local name, so it is
    evaluated once either way.
  - The tests whose bodies hold the PT011 sites:
    - `test_the_guard_stays_quiet_on_ordinary_commands`: shlex's "No
      closing quotation";
    - `test_manifest_generator_rejects_a_folded_description`, three calls:
      `tools/render_plugin_manifests.py`'s "has no frontmatter block", its
      folded-description refusal and "frontmatter has no description";
    - `test_write_witness_removes_its_temp_file_when_the_replace_fails`:
      "No space left on device";
    - `test_write_witness_reraises_the_original_error_not_the_cleanup_one`:
      the same message, which that test also asserts after the call.
  - The ERA findings are prose:
    - `#                 ("cannot", "no X is created", "writes no", "exits
      2"). Every`, a tier comment;
    - a comment quoting the real SpecKit template's two mandatory level-2
      headings, each with its `*(mandatory)*` suffix, in
      `test_parse_speckit_extracts_fr_and_sc_from_canonically_annotated_headings`.
  - The `PT` family as a whole: 115 findings, `PT018` 86, `PT006` 21,
    `PT011` 6, `PT013` 1, `PT007` 1.
- **PTH's witness sites, and why the fix is not neutral on 3.10**
  (2026-10-17). `test_write_witness_is_atomic` and
  `test_write_witness_cleans_up_the_temp_file_and_reraises_on_write_failure`
  patch `witness.os.replace`, and the two write-failure tests above patch
  `witness.os.replace` and `witness.os.unlink`.
  - The review's `pth_probe2.py` patches `os.replace` and `os.unlink` with
    recorders, calls `Path.replace` and `Path.unlink`, and prints what the
    recorders saw. Run as `<python> -I pth_probe2.py` it printed:
    - `3.10.20 []`;
    - `3.11.17`, `3.12.3`, `3.13.16`, `3.14.6` and `3.15.0`, each
      `['replace', 'unlink']`.
  - On 3.10.20, `inspect.getsource(pathlib._NormalAccessor)` holds
    `unlink = os.unlink` and `replace = os.replace`: class attributes bound
    at import, which a later patch of the `os` module does not reach.
- **The proposed selection, together.** `python -m ruff check --no-cache
  --extend-select A,BLE,FLY,G,LOG,PGH,SLOT,T10,YTT,INT,ASYNC,FIX,PLE,FURB,PYI,PT011
  --statistics openspec_graph tests tools` reports 12 findings:
  - PT011 6, FURB110 2, FURB122 1, PYI041 1, FURB167 1 and FURB188 1;
  - `[*] 6 fixable`, and the six PT011 are manual.

  The same with `--isolated --ignore-noqa --select …` reports the same 12.
- **The count guard's command, today** (2026-10-17). `python -m ruff check
  --no-cache --isolated --no-respect-gitignore --ignore-noqa --target-version
  py310 --select A,ASYNC,BLE,FIX,FLY,G,INT,LOG,PGH,PLE,SLOT,T10,YTT,FURB,PYI,PT011
  --output-format json openspec_graph tools tests`, its JSON counted by `code`:
  - exit 1, stderr empty;
  - 12 findings, PT011 6, FURB110 2, PYI041 1, FURB167 1, FURB188 1 and
    FURB122 1, the configured run's 12.

  The target version: `pyproject.toml`'s `[tool.ruff]` holds `line-length`
  only, with no `target-version`, and `requires-python = ">=3.10"`, whose
  lower bound gives `py310`, the version ruff infers for the configured run.
- **The file list, today** (2026-10-17). `python -m ruff check --no-cache
  --isolated --no-respect-gitignore --show-files openspec_graph tools tests`
  lists 134 paths: 119 `.py` modules and 15 `pyproject.toml` fixtures under
  `tests/corpus/` and `tests/fixtures/`, which ruff reads for its own RUF200.
  `find openspec_graph tools tests -name '*.py' -o -name '*.pyi'` finds the
  same 119. The comparison against git's list is Milestone 1's to record,
  because this drafting runs no git command.
- **The target-version hole, by the second review** (2026-10-17).
  - `review-rcs-2/tv/tree-py38/` is a copy of this tree with the proposed
    selection, `[tool.ruff] target-version = "py38"`,
    `requires-python = ">=3.10"`, and `tests/test_planted_tv.py`, which holds
    a hand-rolled prefix strip and `bin(x).count("1")`.
    - The configured run, `python -m ruff check --no-cache --output-format
      concise openspec_graph tools tests`: "All checks passed!", exit 0.
    - The count at `py38`: no finding.
    - The count at `py310`: `tests/test_planted_tv.py:2` FURB188 and `:8`
      FURB161.
  - `review-rcs-2/tv2/p.py` adds `anext`, `aiter` and `EncodingWarning`
    bound as local names. The count over it with `--select …` reads nothing
    at `py38`, and A001 3, FURB188 1 and FURB161 1 at `py310`.
  - Over the first review's `probe-planted/`, `--config 'target-version =
    "<t>"'` at `py310`, `py38` and `py37` reported the same 46 findings: none
    of those planted constructs depends on the version. So the escape case
    plants the version-dependent constructs above.
- **The rule as now written, run on `tv/tree-py38`** (2026-10-17). A reader
  that takes the floor from `requires-python` alone, and names a
  `[tool.ruff] target-version` other than it, was evaluated in memory over
  that tree's `pyproject.toml`:
  - it returned `py310` and the problem "`[tool.ruff] target-version 'py38'`
    is not the `requires-python` floor `'py310'`";
  - the count at `py310` printed FURB188 and FURB161 in
    `tests/test_planted_tv.py`, exit 0 under `--exit-zero`, stderr empty.

  So the guard fails twice over on that tree, by the named problem and by
  the findings, while the lint gate there is green.
- **The reader prototype, against ruff's own inference** (2026-10-17). The
  second review's `bin/tv_reader.py` `reader_packaging` was run in memory on
  its sixteen `requires-python` cases, and `ruff check --no-cache
  --show-settings a.py` was run in each `tvr/c<i>/` for ruff's
  `unresolved_target_version`:

  | `requires-python` | ruff infers | `packaging` reader |
  |---|---|---|
  | `>=3.10` | 3.10 | `py310` |
  | `>=3.11` | 3.11 | `py311` |
  | `>=3.10,<4` | 3.10 | `py310` |
  | `>=3.10, !=3.11.*` | 3.10 | `py310` |
  | `~=3.10` | 3.10 | `py310` |
  | `>3.10` | 3.10 | `py310` |
  | `==3.10.*` | 3.10 | `py310` |
  | `>=3.10.2` | 3.10 | `py310` |
  | `>= 3.10` | 3.10 | `py310` |
  | `<4` | none | "has no lower bound" |
  | empty | none | "has no lower bound" |
  | `>=3` | none | "names no minor version" |
  | `>=3.10,>=3.11` | 3.10 | `py311` |
  | `3.10` | exit 2 | "does not parse" |
  | missing | none | "requires-python is missing" |
  | `>=3.16` | none | `py316` |

  The reader keeps the prototype's behaviour: a compound specifier gives
  its highest lower bound (`>=3.10,>=3.11` gives `py311`, where ruff takes
  `3.10`), and `~=3.10` gives `py310`. A floor ruff does not know, such as
  `py316`, reaches ruff and fails the count with ruff's own error.
- **`requires-python` and the matrix.** `grep -n "requires.python" tests/*.py`
  finds only a docstring in `tests/support.py`. `test_classifiers_equal_the_hard_matrix_legs`
  ties the classifiers to the hard legs, and no test ties `requires-python`
  to the lowest one. That anchor is out of scope (DEC-RCS-016).
- **Every selection fires, planted** (2026-10-17). The first review's
  `probe-planted/` copies this repository's ruff configuration with the
  proposed selection. It plants, in `openspec_graph/`, `tools/` and
  `tests/` alike:
  - `planted.py`: `list = []` (A001), `breakpoint()` (T100), `except
    Exception: pass` (BLE001), `logging.info(f"{x}")` (G004, LOG015),
    `z = 1  # type: ignore` (PGH003), `# TODO: planted` (FIX002),
    `x if x else y` (FURB110) and `x: int | float` (PYI041), plus
    `with pytest.raises(ValueError):` (PT011) in the `tests/` copy only;
  - `planted2.py`: `class S(str)` (SLOT000), `time.sleep(1)` in an `async
    def` (ASYNC251), `sys.version[:3] >= "3.1"` (YTT101), `"".join(["a",
    "b"])` (FLY002), `_(f"hi {name}")` (INT001) and `__all__ = [S]`
    (PLE0604).

  `python -m ruff check --no-cache --output-format concise openspec_graph
  tools tests` from that tree reports each of the fifteen codes at all three
  paths and PT011 at `tests/`: 46 findings of the new selection.
- **The escapes, planted** (2026-10-17). Over the same tree, each escape was
  passed as a `--config "<key> = <value>"` override after `--config
  pyproject.toml`, and the codes of the new selection counted. The
  prose-`noqa` case went through stdin, the version cases through
  `tv/tree-py38/`, and the file cases through `resolve-rcs/`:

  | escape | hidden from the configured run |
  |---|---|
  | `except Exception:  # the old line said # noqa: BLE001 and was wrong` | BLE001 |
  | `except Exception:  # never write "# noqa: BLE001" here` | nothing: ruff warns the directive is invalid and reports BLE001 |
  | per-file `PT` | PT011 |
  | per-file `PT01` | PT011 |
  | per-file `FURB1` | FURB110 at every path |
  | per-file `PL` | PLE0604 at every path |
  | per-file `ALL` | every finding |
  | `lint.ignore = ['BLE']` | BLE001 at every path |
  | `lint.extend-ignore = ['BLE']` | BLE001 at every path |
  | `lint.exclude = ['tests/*']` | every finding under `tests/` |
  | `exclude = ['tests/*']` | every finding under `tests/` |
  | `extend-exclude = ['tests/*']` | every finding under `tests/` |
  | `lint.flake8-pytest-style.raises-require-match-for = []` | PT011 |
  | `lint.flake8-builtins.ignorelist = ['list']` | A001 at every path |
  | `target-version = "py38"` (`tv/tree-py38/`) | FURB188 and FURB161 |
  | `per-file-target-version = {"tests/*" = "py38"}`, with `target-version = "py310"` | FURB188 and FURB161, reported without it |
  | `lint.task-tags = []` | nothing: FIX002 still reported |
  | `lint.logger-objects = []` | nothing |
  | `lint.extend-exclude = ['tests/*']` | not a key: ruff prints "unknown field `extend-exclude`" and exits 2 |
  | `tests/ruff.toml` selecting `E4` only (`nested-cfg/`) | BLE001 in `tests/test_a.py` |
  | `pkg/.ignore` naming `a.py` (`nested-cfg/`) | BLE001 in `pkg/a.py` |
  | `openspec_graph/dist/planted.py` (`default-exclude/`) | BLE001 there, from the count too |

  - The count, `--isolated --no-respect-gitignore --ignore-noqa
    --target-version py310 --select <the set>`, reported every planted
    finding in each case but the last: all 46 over `probe-planted/`, BLE001
    on stdin, FURB188 and FURB161 over `tv/tree-py38/`, and both modules of
    `nested-cfg/`.
  - Without `--no-respect-gitignore`, an isolated count missed `pkg/a.py`:
    the `.ignore` file is why the counting method carries that flag.
  - In `default-exclude/`, the configured run and the count each report
    `openspec_graph/seen.py` alone. `--show-files` lists `seen.py` and not
    `dist/planted.py`, which `find` lists. Naming `dist/planted.py`
    explicitly reports its BLE001, and `--force-exclude` hides it again. So
    the file-list check, and not the count, names this case.
  - An unused directive, `X = 1  # noqa: BLE001` on stdin under the
    configured run, reads `RUF100 [*] Unused noqa directive (unused:
    BLE001)`. RUF is already selected.
- **Preview exposure** (2026-10-17).
  - `python -m ruff check --no-cache --preview --extend-select
    A,ASYNC,BLE,FIX,FLY,G,INT,LOG,PGH,PLE,SLOT,T10,YTT,FURB,PYI,PT011
    --statistics openspec_graph tools tests` on 0.17.0 reports 58 findings.
    They are the 12 above, FURB142 2 (`tests/test_decomposition.py:151` and
    `:177`, `set.add()` in a loop), and S404 30, RUF105 8, RUF069 4 and
    UP052 2.
  - The same without `--extend-select`, today's selection, reports 44:
    S404 30, RUF105 8, RUF069 4 and UP052 2.
  - `review-rcs/ruff171/bin/ruff check --no-cache --preview --select FURB142
    …` on 0.17.1 reports the same two FURB142 sites.
  - CI installs ruff unpinned: `ci.yml`'s jobs run `pip install -e
    ".[dev]"`, and the dev extra lists a bare `"ruff"`.
- **At the 3.11 floor.** The same `--extend-select`, with FA, TD, PTH and
  ERA added and `--target-version py311`, reports the same per-code counts
  for every one of those families. It adds UP017 (`openspec_graph/cli.py`)
  and UP036 (`tests/support.py`), which are `prepare-release-0-4-0`'s.
- **The declined families with a backlog.** `python -m ruff check --no-cache
  --select <sel> --statistics openspec_graph tools tests`:

  | selection | findings | by code |
  |---|---|---|
  | TRY003 | 68 | — |
  | EM | 70 | EM102 60, EM101 10 |
  | TRY003,EM | 138 | `openspec_graph` 32, `tools` 86, `tests` 20 by `--output-format concise` per tree; the review's 118 is the first two |
  | COM812 | 458 | — |
  | D401 | 104 | — |
  | D205 | 354 | — |
  | PLR | 213 | PLR2004 185, PLR0913 9, PLR0911 7, PLR0912 6, PLR0917 5, PLR0915 1 |
  | PLC | 86 | PLC0415 84, PLC0207 1, PLC0414 1 |
  | PLW | 6 | PLW2901 3, PLW0108 2, PLW1510 1 |
  | TC | 86 | TC003 72, TC001 12, TC002 2, all unsafe fixes |
  | E501 | 457 | the existing comment says "~100 places" |
  | ANN | 115 | ANN001 101, ANN401 7, ANN202 7 |
  | T203 | 0 | the existing line says nothing here uses `pprint`, still true |

  - `python -m ruff rule COM812` reads "We recommend against using this
    rule alongside the formatter." `grep -rn "ruff format"` over the
    `Makefile`, `.pre-commit-config.yaml`, the workflows and
    `docs/hooks.md` finds nothing, so the repository runs no formatter.
  - The review's figure for TRY003 and EM, 118, is the command over
    `openspec_graph` and `tools`; the three trees give 138.
- **Outside the linted trees** (2026-10-17). The lint target's recipe is
  `python -m ruff check openspec_graph tests tools`, and `[tool.mypy] files
  = ["openspec_graph", "tools", "tests"]`.
  `.claude/hooks/guard_promotion.py:277` reads `except Exception as exc:  #
  a seat belt never blocks on its own fault`. `python -m ruff check
  --no-cache --isolated --select BLE,A,FIX,T10 --target-version py310
  .claude/hooks/` reports that line's BLE001 and nothing else. Neither gate
  reads the file.

### pytest

- **Configuration.** `[tool.pytest.ini_options]` holds `testpaths`, the
  three tier `markers` and `addopts = "-q --strict-markers"`.
  - `python -m pytest --collect-only -q -p no:cacheprovider --strict-config`
    exited 0.
  - `grep -rn "xfail\|filterwarnings\|pytest.warns\|warnings.catch_warnings\|simplefilter"
    tests/*.py` finds only `test_property_settings_are_derandomized_and_nothing_is_xfailed`,
    which asserts no property test is `xfail`-marked.
- **Tiers.** `python -m pytest --collect-only -q -p no:cacheprovider -o
  addopts="" -m <tier>` collects 867 `unit`, 871 `integration` and 332 `e2e`,
  of 2070.
- **Each tier under `-W error`.** `python -m pytest tests/ -m <tier> -W error
  -p no:cacheprovider -o addopts="--strict-markers" -q -rfE`:
  - `unit`: `867 passed, 1203 deselected in 18.68s`;
  - `integration`: `871 passed, 1199 deselected in 16.28s`;
  - `e2e`: `332 passed, 1738 deselected in 199.88s (0:03:19)`, the
    smoke-wheel test among them.

  No failure to record.
- **The nested runs that read this repository's configuration.**
  `test_suite_survives_an_ambient_coverage_file` runs a nested pytest from
  the repository root, and
  `test_an_unregistered_marker_fails_collection_under_strict_markers` runs
  one under a copied `pyproject.toml`. Each child inherits
  `PYTHONWARNINGS=error`, which is stricter than an ini filter because it
  reaches every child interpreter.
  - The command: `PYTHONWARNINGS=error python -m pytest
    tests/test_coverage_checkers.py tests/test_suite_shape.py -k
    "test_suite_survives_an_ambient_coverage_file or
    test_an_unregistered_marker_fails_collection_under_strict_markers or
    test_coverage_floor_fails_below_threshold_pytest or
    test_coverage_floor_passes_at_threshold" -W error -p no:cacheprovider -o
    addopts="--strict-markers" -q`.
  - It read `4 passed, 69 deselected in 4.19s`.
- **What each strictness option stops, nested** (2026-10-17, pytest 9.1.1).
  Each tree under `resolve-rcs/` has a `tests/` directory and a
  `[tool.pytest.ini_options]` table, and was run as `python -m pytest -p
  no:cacheprovider` from its root:
  - `strictcfg-both/`: `addopts = "-q --strict-markers --strict-config
    -ra"`, `xfail_strict = true`, `filterwarnings = ["error"]` and
    `no_such_key = true`. Exit 4, `ERROR: Unknown config option:
    no_such_key`, and no `INTERNALERROR` anywhere in the output.
  - The same tree with `-o addopts=""`, the durations command's override:
    exit 3, `INTERNALERROR> pytest.PytestConfigWarning: Unknown config
    option: no_such_key`.
  - `strictcfg-filter-only/`: the same table without `--strict-config`.
    Exit 3, the same `INTERNALERROR` line, and the same with `-o
    addopts=""`.
  - `warn-run/`: a test calling `warnings.warn("rcs-planted-warning-7f3a",
    UserWarning, stacklevel=1)`. Exit 1, `FAILED tests/test_warns.py::test_warns
    - UserWarning: rcs-planted-warning-7f3a`.
  - `xpass-run/`: `@pytest.mark.xfail(reason="rcs-planted-xfail")` on a
    passing test. Exit 1, `[XPASS(strict)] rcs-planted-xfail`.

  So `filterwarnings = ["error"]` alone already stops an unknown key, as an
  internal error. `--strict-config` makes it a usage error, and only the ini
  filter holds with `addopts` cleared.
- **The coverage-measured run, by the first review** (2026-10-17, its logs
  under `review-rcs/`). `run_suite.sh <tree> <python> <log>` runs, from a
  copy of `bfbc124` carrying this change's pytest configuration:
  - `coverage erase`;
  - `python -m pytest tests/ --cov --cov-branch --cov-fail-under=0
    --cov-report=json:coverage.json -q -p no:cacheprovider`;
  - `tools/check_coverage_floor.py` and `tools/check_branch_coverage.py` on
    `coverage.json`, each with `--scope openspec_graph` and `--scope tools`.

  The logs print no totals line (the doubled `-q`), so passes and failures
  were counted here from their progress lines:

  | interpreter | log | passed | failed | the four floor checks |
  |---|---|---|---|---|
  | 3.10.20 | `review-rcs/strict-310.log` | 2069 | 1 | each exit 0 |
  | 3.11.17 | `review-rcs/strict-311.log` | 2069 | 1 | each exit 0 |
  | 3.12.3 | `review-rcs/strict-312.log` | 2069 | 1 | each exit 0 |
  | 3.13.16 | `review-rcs/maketest-strict-313.log` | 2069 | 1 | each met |
  | 3.14.6 | `review-rcs/strict-314.log` | 2069 | 1 | each exit 0 |
  | 3.15.0 | `review-rcs/strict-315.log` | 2057 | 13 | each exit 0 |

  - The one failure on every interpreter is
    `test_the_real_wheel_passes_the_shared_smoke_tool`, a `FileNotFoundError`
    for the smoke venv's `bin/planlint`. The same test passed in this
    drafting's `e2e` tier above, run on the worktree itself, so it is the
    copies' environment.
  - The twelve more on 3.15.0 are `test_action_contract.py` tests, each a
    `FileNotFoundError` for an output the action never wrote. The action's
    shell starts that interpreter without its library path:
    `py315/bin/python3.15` run bare prints "error while loading shared
    libraries: libpython3.15.so.1.0". `strict315-fail.txt` and
    `base315-fail.txt`, the latter from an unmodified copy, name the same
    twelve tests (`diff` of the two, test ids only, is empty).
  - No failure on any interpreter names a warning.
- **pytest 9's umbrella.** `python -m pytest --help` lists `strict (bool):
  Enables all strictness options, currently: strict_config, strict_markers,
  strict_xfail, strict_parametrization_ids`, and `strict_xfail` with the
  alias `xfail_strict`.
  - `python -m pytest --collect-only -q -p no:cacheprovider -o
    strict_parametrization_ids=true` exited 2 with two collection errors.
  - `tests/test_adopter_urls.py` has duplicates `AGENTS.md` and
    `spec-gate.yml`.
  - `tests/test_detect_thresholds.py` has duplicates `90-90` and
    `90.0-90`.

### The subprocess calls

- **Counted by AST.** A `python -I` pass over `tests/*.py` counts `Call`
  nodes whose function is `subprocess.run`: 45 calls in 21 files, none with
  a `timeout` keyword. By file:
  - `test_enterprise.py` 8, `test_gate_scripts.py` 4;
  - 3 each: `test_agent_artifacts.py`, `test_coverage_checkers.py`,
    `test_graft_witness.py`, `test_skill_distribution.py` and
    `test_static_ratchets.py`;
  - 2 each: `action_support.py`, `test_ci_workflow.py`,
    `test_e2e_corpus.py` and `test_smoke_wheel.py`;
  - 1 each: `promotion_support.py`, `support.py` (`run_cli`),
    `test_claude_guard.py`, `test_claude_hooks.py`,
    `test_detect_thresholds.py`, `test_findings_envelope.py`,
    `test_release_surface.py`, `test_report.py`, `test_suite_shape.py` and
    `test_wheel_metadata.py`.
- **The text grep.** `grep -c "subprocess.run" tests/*.py` finds 57 lines in
  25 files, the AST's calls plus comments, docstrings and planted strings.
  The review's "one of 50 has a timeout" matches
  `test_graft_witness.py:556`, which asserts
  `kwargs.get("timeout") == detect.GIT_TIMEOUT_SECONDS`: an assertion
  about `detect`'s own call, not a test's call with a timeout.
- **Every `run_cli`-shaped call in the e2e tier, timed.**
  - The plugin wraps `subprocess.run`, keeps calls whose argv holds
    `openspec_graph.cli` and `--target`, and prints at session end. The
    command: `PYTHONPATH=<measure-rcs> python -m pytest tests/ -m e2e -p
    time_cli_calls -p no:cacheprovider -o addopts="--strict-markers" -q`.
  - It read 269 calls, 136.77 s in all, `332 passed` in 196.33 s.
  - The slowest single call took 0.68 s, `validate` in
    `test_a_waived_g010_still_fails_a_fail_on_info_run`. Most of the next
    eleven took 0.57 s.
  - **Under coverage, by the first review.** Its `plugin/rcs_time_cli.py`
    keeps the same calls and prints the slowest five. Under the test stage's
    coverage-measured shape, the review reports 269 calls with the slowest
    at 0.77 s. That figure is the review's, not re-run here: a coverage run
    writes data files, and these revisions made no copy of the tree to
    write them in.
- **The bounds around it.**
  - `ci.yml`'s `test` job has `timeout-minutes: 15`, `test-windows` 20 and
    `encoding-stress` 10.
  - `pyproject.toml`'s timeout comment records `test-windows` at 5m42s
    against the `test` legs' 2m14s–3m41s on CI run #171.
  - `tools/check_no_hardcoded_thresholds.py` scans the Makefile and
    `.github/workflows/*.y*ml` only (its module docstring and `targets()`).
  - `openspec_graph/detect.py`'s `GIT_TIMEOUT_SECONDS` comment reads "Named
    rather than inlined: it bounds a subprocess against a repository
    planlint does not own … Not a quality threshold, so not configuration."
- **The bound's budget, worked.** At 120 s per hung call:
  - a `test` leg has 900 s, less its 134–221 s run, so 679–766 s left: five
    full waits fit on the slowest leg and six on the fastest, and one more
    cancels the job;
  - `test-windows` has 1200 s, less 342 s, so 858 s left: seven full waits
    fit.

  A single hang is named by its test. A hang that strikes every CLI child,
  of which the e2e tier alone makes 269, still ends in cancellation.
- **The sibling guard, as `close-gate-script-gaps` now stands** (read
  2026-10-17, its `spec.md` dated 16:01).
  - R-GSG-3's named-threshold rule matches a name whose segments include
    `min`, `max`, `minimum`, `maximum`, `floor`, `under`, `ratio` or
    `threshold`, each also with a trailing `s`. It runs over the text
    targets of R-GSG-1: the makefile, `.github/workflows/`, the composite
    actions, `templates/`, the skill assets, the root `.pre-commit-*.yaml`
    and the root `Dockerfile*`.
  - R-GSG-5's constants rule reads module-level bindings of `tools/*.py`
    only, and DEC-GSG-007 says "`tests/` is not read".
  - `RUN_CLI_TIMEOUT_SECONDS`'s segments are `RUN`, `CLI`, `TIMEOUT` and
    `SECONDS`. None is a list word or a list word's plural, and
    `tests/support.py` is neither a text target nor under `tools/`.
  - That package's own hazard list names this constant the same way. It
    names BLE, G, LOG, FURB and PT011 as the families that will judge its
    code.

  The first draft read only that package's scratch prototype, which did not
  carry the plurals; this replaces it.

### Typing

- **The severity today.** `openspec_graph/rule_types.py` binds `ERROR, WARN,
  INFO = "ERROR", "WARN", "INFO"`, and `Finding.severity` and
  `Rule.severity` are `str`.
  - `grep -rn "Finding(" openspec_graph/*.py` finds construction in
    `rules.py` only, its three `severity=` arguments all constants.
  - `report.py`'s `FindingRecord.severity` is a separate `str`, read from
    JSON through `_require_str`.
  - The package's severity tables: `openspec_graph/cli.py`'s
    `SEVERITY_ORDER = {"INFO": 0, "WARN": 1, "ERROR": 2}`; `report.py:70`
    `SEVERITIES: tuple[str, ...] = ("ERROR", "WARN", "INFO")`; `report.py:85`
    `_COMMANDS: Mapping[str, str] = {"ERROR": "error", "WARN": "warning",
    "INFO": "notice"}`; `sarif.py:42` `_LEVELS = {"ERROR": "error", "WARN":
    "warning", "INFO": "note"}`.
  - `report.py` imports only `__future__`, `dataclasses`,
    `collections.abc` and the rest of the standard library.
  - No test, module or tool reads a dataclass field's annotation at run
    time (`grep -rn "fields(\|__annotations__\|get_type_hints"`).
- **The `Literal`, emulated.** The shadow copy declares `Severity =
  Literal["ERROR", "WARN", "INFO"]`, `ERROR: Final = "ERROR"` and its
  siblings, and annotates both fields with `Severity`.
  - `python -m mypy --config-file pyproject.toml --cache-dir=/dev/null
    --shadow-file openspec_graph/rule_types.py <shadow>` printed "Success:
    no issues found in 119 source files", the same as without the shadow.
    So did `--platform win32` and `--python-version 3.11`.
  - With the `tests.*` override lifted, the run was `env -u MYPYPATH python
    -m mypy --config-file <derived.ini> --cache-dir=/dev/null --platform <p>
    -O json [--shadow-file …]`, counted by `code` over `severity == "error"`
    objects under `tests/`.
  - With and without the shadow, under `linux` and `win32` alike, it gave
    `arg-type` 17, `attr-defined` 18, `index` 7, `no-any-return` 8,
    `no-untyped-def` 96, `type-arg` 16 and `union-attr` 4: 166 in all, none
    outside `tests/`, equal to `MYPY_TESTS_CEILINGS`.
  - `python -m ruff check --no-cache --stdin-filename
    openspec_graph/rule_types.py - < <shadow>` printed "All checks passed!".
    With `--isolated --ignore-noqa --select D100,D101,D102,D103` it read
    `D101` 2 and `D102` 2, the same as the file and as
    `DOCSTRING_CEILINGS`.
  - `[[tool.mypy.overrides]] module = "tests.*"` disables `no-untyped-def`,
    `attr-defined`, `arg-type`, `type-arg`, `no-any-return`, `index` and
    `union-attr`. So the planted unknown-severity module sits at the root
    of its temporary directory, where its module name is not `tests.*`.
- **`py.typed`.**
  - `find openspec_graph -name py.typed` finds nothing.
  - `[tool.setuptools]` has `dynamic` and `packages.find` (`include =
    ["openspec_graph*"]`) and no package data.
  - `grep -rn "py.typed\|namelist\|package-data\|package_data" tools/*.py
    tests/*.py pyproject.toml` finds only `tools/check_wheel_metadata.py`'s
    `namelist()`, which reads METADATA and the licence directory: nothing
    pins either archive's file list.
  - `curl -sS https://raw.githubusercontent.com/pypa/setuptools/main/NEWS.rst`
    lists under `v69.0.0`: "Include type information (``py.typed``,
    ``*.pyi``) by default (#3136)".
  - `[build-system] requires` names setuptools with a floor of 77. The
    container's system setuptools is 68.1.2, which the isolated build does
    not use.
  - `docs/policies.md`'s deprecation window lists "a public import" among
    the user-facing surfaces.
  - **Built, by the first review** (its `build.log` and `build2.log`, from
    its copy with an empty `openspec_graph/py.typed`). The wheel-only build,
    and the sdist then the wheel from it, both print `adding
    'openspec_graph/py.typed'`. Read here, `zipfile.ZipFile(...).namelist()`
    of each wheel holds `openspec_graph/py.typed`, and `tar tzf` of the
    sdist lists `planlint-0.3.0/openspec_graph/py.typed`.
  - The release paths build the sdist and then the wheel from it:
    `release.yml`'s `python -m build` and `ci.yml`'s `release-tier`
    `python -m build --outdir dist`. `packaging` builds the wheel alone
    today, and `tighten-release-surface` moves it to the wheel-check
    target's sdist-first recipe.
  - The precedent's skip: `test_the_real_wheel_passes_the_gate`
    (`tests/test_wheel_metadata.py`) calls `pytest.skip` on any non-zero
    exit of `python -m build --wheel`, with the tail of its stderr. The
    archive guard narrows that (Milestone 4).

### Python 3.15

- **The download manifest.**
  `curl -sS https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json`
  lists `3.15.0` with `stable: true` (release `3.15.0-38076878863`), after
  `3.15.0-rc.3` and the earlier pre-releases. Its files include
  `linux-22.04`, `linux-24.04` and `linux-26.04` builds for x64 and arm64,
  and `win32` x64, x86 and arm64.
- **The runner images.** The image readmes under
  `https://raw.githubusercontent.com/actions/runner-images/main/images/`
  list their pre-cached Python:
  - `ubuntu/Ubuntu2404-Readme.md`, image `20261012.334.1`: 3.10.22,
    3.11.17, 3.12.15, 3.13.16 and 3.14.8;
  - `windows/Windows2025-VS2026-Readme.md`, image `20261007.264.1`: 3.10.11,
    3.11.9, 3.12.10, 3.13.16 and 3.14.8.

  The repository's `README.md` maps `ubuntu-latest` to `ubuntu-24.04` and
  `windows-latest` to `windows-2025-vs2026`, linking those two readmes. No
  image pre-caches 3.15, so `setup-python` would download it.
- **The dev extra on 3.15.** `curl -sS https://pypi.org/pypi/<p>/json`:
  - `coverage` 7.16.2: 30 `cp315` wheels;
  - `mypy` 2.4.0: 13, and its dependency `librt` 0.16.0: 31;
  - `hypothesis` 6.170.1: 18, uploaded 2026-10-16, `requires_python
    >=3.11`, so the 3.10 leg resolves an older release;
  - `pytest` 9.1.1, `pytest-cov` 7.1.0, `ruff` 0.17.1, `vulture` 2.16 and
    `build` 1.6.1 ship `py3` wheels only.
- **A Linux 3.15.0 run, by the first review.** The `strict-315.log` row
  above: 2057 passed and 13 failed, every failure environmental and
  accounted for, none caused by a warning, and all four floor checks exit 0.
- **The aggregator.** GitHub's contexts reference
  (`github/docs`, `content/actions/reference/workflows-and-actions/contexts.md`)
  documents the step-level behaviour: "When a `continue-on-error` step
  fails, the `outcome` is `failure`, but the final `conclusion` is
  `success`". For `needs.<job_id>.result` it says only "Possible values are
  `success`, `failure`, `cancelled`, or `skipped`." The workflow-syntax
  page shows the `continue-on-error: ${{ matrix.experimental }}` example
  without naming the `needs` result.
- **The guards.** `tests/workflow_support.py`'s `SOFT_FAIL` is applied by
  `soft_fail_problems` to `PROMOTION_JOBS = ("promotion", "release-tier",
  "ci-ok")` (`tests/test_ci_promotion.py`) and by
  `test_release_gate_checks_tag_ancestry_against_production` to the
  ancestry step. `_experimental_leg_offenders`
  (`tests/test_workflow_python.py`) requires a job-level `continue-on-error`
  on `matrix.experimental` whenever an experimental leg exists, as
  R-HCW-10 and DEC-HCW-005 set.
- **What could not be established here:**
  - a Windows 3.15 run, which `test-windows` would not make anyway (it runs
    `PYTHON_DEFAULT`);
  - a run on a hosted runner, and the pinned `actions/setup-python` v7.0.0
    resolving `3.15` there;
  - `needs.test.result` for a failed experimental leg.

### Module sizes

- `wc -l` (2026-10-17), against `MAX_TEST_MODULE_LINES = 700`
  (`tests/test_suite_shape.py:44`):
  - `tests/test_suite_shape.py` 556, the nearest the bound;
  - `tests/test_cli_surface.py` 532;
  - `tests/test_ci_workflow.py` 431;
  - `tests/test_decomposition.py` 393;
  - `tests/test_static_ratchets.py` 280;
  - `tests/test_release_surface.py` 266.

  `tests/ratchet_support.py` (500) is not a `test_*.py` module, so the bound
  does not apply to it.
- Milestone 2 plans a structural guard, a helper and its `unit` test, and
  three nested runs for `tests/test_suite_shape.py`. The nested runs carry
  the planted sources, so they are the part most likely to need the split
  DEC-RCS-014 names.

### Records of this session

- **Writes outside the package during drafting.** Before the bytecode
  switch was set, three commands run from the worktree imported its package
  and wrote `openspec_graph/__pycache__/`. Suite runs made from the worktree
  then wrote their normal by-products: `.coverage.*` files in its root,
  `.hypothesis/`, `.mypy_cache/`, `build/` and `planlint.egg-info/`.
  - Every one is a name `.gitignore` covers, no tracked file changed, and
    they were reported with the draft. This drafting deleted nothing.
  - At these revisions, `find` over the worktree (outside `.git`) finds no
    `__pycache__`, `.coverage*`, `.hypothesis`, `.mypy_cache`,
    `.ruff_cache`, `.pytest_cache`, `build`, `dist`, `*.egg-info` or
    `coverage.json`.
  - Every later Python process set `PYTHONDONTWRITEBYTECODE=1`. The
    revisions' selector-collection runs also set
    `HYPOTHESIS_STORAGE_DIRECTORY` to the scratchpad. The revisions'
    measurements ran from scratch trees or read the worktree only: ruff with
    `--no-cache`, pytest in the scratch trees, and the gate and the citation
    tests on the worktree with `-p no:cacheprovider`.
- **Edits and writes by shell.** One revision of `proposal.md` in the first
  drafting, inside this package's directory, was made with a `python3 -I`
  heredoc rather than the file-writing tool. In the first revision, two
  shell redirects wrote `resolve-rcs/count.err` and `resolve-rcs/both.out`
  in the scratchpad. Every other write used the file-writing tool.
- **No git command was run** by this drafting or its revisions.

## Order and pull requests

1. **This package, alone, into `dev`.** One pull request carrying only
   `openspec/changes/raise-coding-standards/`, held until `v0.3.0` is
   pushed to origin and `v0.3.0^{commit}` is an ancestor of `dev`. Record,
   each with its output and the date (R-RCS-1, AC-RCS-21):
   - `git ls-remote --tags origin 'v0.3.0'`, which prints the tag and its
     peeled line;
   - `git fetch origin && git merge-base --is-ancestor 'v0.3.0^{commit}'
     origin/dev`, which exits 0.

   Then record its merge commit and the date.
2. **The implementation, as a draft pull request from `dev`.** Milestones 1
   to 5, one commit each, each `make pre-pr` green, guards seen red in the
   working tree and never committed red. Its release is one of two
   (R-RCS-1, DEC-RCS-017):
   - **0.4.0**, if it merges before `prepare-release-0-4-0`'s release-prep
     pull request opens. Its `CHANGELOG.md` groups are then under
     `[Unreleased]` when that package cuts 0.4.0;
   - **the next minor**, if it has not merged by then. It is held until
     `v0.4.0` is pushed to origin and `v0.4.0^{commit}` is an ancestor of
     `dev`, recorded by `git ls-remote --tags origin 'v0.4.0'` and `git
     fetch origin && git merge-base --is-ancestor 'v0.4.0^{commit}'
     origin/dev` with their output and the date. It then rebases, and puts
     its groups under the `[Unreleased]` that follows `[0.4.0]`.

   Either way it never merges between the release-prep commit and the
   promotion (that package's R-RFR-2). When the release-prep pull request is
   due, the maintainer records here which release this change took and why.
3. **Milestone 6 records the CI run** on the implementation's pull request,
   in a commit on that pull request.

## Milestone 0 — Grounding at the implementation head

- Run the gate and record its exit code before the first edit, with the
  installed `planlint` and with `PYTHONPATH` set to the worktree:
  `planlint --target . validate --fail-on ERROR`.
- Record the 0.3.0 hold's facts of "Order and pull requests" item 1 as they
  stand at the head, with their output and the date.
- Record `python --version`, `python -m ruff --version`, `python -m mypy
  --version` and `python -c "import pytest, hypothesis; print(pytest.__version__,
  hypothesis.__version__)"` from the implementation's own `pip install -e
  ".[dev]"`. Then re-take every measurement above at the head, with the
  commit:
  - the fifteen zero-hit families, with and without `--isolated
    --ignore-noqa`;
  - the near-zero sites, the `--diff` of the FURB and PYI fixes, and the
    proposed selection together;
  - the count guard's command, at the floor read from `requires-python` as
    it then stands, and whether `[tool.ruff]` sets a `target-version`;
  - ruff's `--show-files` list against `git ls-files --cached --others
    --exclude-standard -- openspec_graph tools tests`, both filtered to
    `*.py` and `*.pyi`;
  - the preview figures, on the installed ruff;
  - the declined table;
  - the pytest collection under `--strict-config`, and the nested
    strictness trees;
  - the AST count of `subprocess.run`;
  - the shadow-file mypy runs, with the derived configuration printed
    again by `derive_config`;
  - the `py.typed` facts;
  - the module sizes;
  - the 3.15 manifest and image readmes.
- **The siblings.** For each of `prepare-release-0-4-0`,
  `close-gate-script-gaps`, `tighten-release-surface`,
  `harden-release-pipeline`, `add-witness-ci-artifacts` and
  `lean-production-tree`, record whether its package and its implementation
  are on `dev`, with the merge commit.
  - Re-read each file and symbol DEC-RCS-013 names for it, and record the
    resolution here. Whichever lands second re-reads.
  - If `prepare-release-0-4-0`'s removals have merged, re-measure PTH at
    the 3.11 floor and record it. DEC-RCS-003's trigger has then fired,
    and its selection is a separate change, not this one. Record the count
    guard's floor as read at the new `requires-python`.
  - If `close-gate-script-gaps` has merged, run its widened threshold guard
    over the tree with `RUN_CLI_TIMEOUT_SECONDS` planted, and record the
    verdict. Re-read the dev extra and
    `test_the_dev_extra_floors_mypy_and_pins_nothing` with its bare
    `coverage` entry, and its edits to `tools/_common.py` and
    `tests/test_static_ratchets.py`. Run every new family, not only the
    ones its hazard list names, over its code.
  - If `tighten-release-surface` has merged, record the wheel-check
    target's recipe and `tools/check_wheel_metadata.py`'s header read as
    they then stand. It pins no file list, so `py.typed` joins none.
  - If `harden-release-pipeline` has merged, record
    `tests/test_release_surface.py`'s size and the line citations of its
    record that this change's edits move.
- If a sibling has added code under `openspec_graph/`, `tools/` or `tests/`
  that a new family reports, it joins Milestone 1's fixes under R-RCS-3's
  rule, or, if no neutral fix exists, this package is revised before
  Milestone 1. No exemption is added in passing.
- **Gate:** `make test`

## Milestone 1 — The lint families

- Guards first, seen red in the working tree (R-RCS-5, DEC-RCS-001,
  DEC-RCS-014, DEC-RCS-016).
  - `tests/ratchet_support.py`, beside `ruff_docstring_command`:
    - `ZERO_COST_SELECTION`, the tuple of R-RCS-2's sixteen selections;
    - `ruff_target_version(pyproject)`, returning `(version, problems)`:
      - the version is `py3NN` from the lower bound of `[project]
        requires-python`, read with `packaging.specifiers.SpecifierSet` as
        the second review's `reader_packaging` reads it. The operators
        `>=`, `>`, `==`, `~=` and `===` give lower bounds, and the highest
        major.minor among them wins;
      - a missing key, a specifier that does not parse, one with no lower
        bound, and one that names no minor version are each a named
        problem, with no version;
      - a `[tool.ruff] target-version` other than that version is a named
        problem, and the version is still returned so the count runs at
        the floor;
    - `ruff_zero_cost_command(target_version, *paths)`: the flags of
      `ruff_docstring_command` (`--no-cache --isolated --no-respect-gitignore
      --ignore-noqa`, `--output-format json --exit-zero`), with
      `--target-version` and `--select` the joined selection. Its findings
      are read the way `docstring_counts` reads them, so a stderr line or a
      non-zero exit is a problem;
    - `ruff_listed_modules(*paths)` and `unlinted_modules(listed, expected)`:
      the first is ruff's `--show-files` under the same flags, kept to
      `*.py` and `*.pyi` and made relative to the root. The second names
      each expected module missing from the list, and each listed module
      not expected.
  - `tests/test_ci_workflow.py`, beside
    `test_t201_is_selected_with_exactly_the_cli_and_tools_exempt`:
    - `test_the_zero_cost_lint_families_are_selected` (`integration`):
      through `read_pyproject()`, every member of `ZERO_COST_SELECTION` is in
      `[tool.ruff.lint] select`. It asserts nothing else.
    - `test_a_planted_violation_of_each_new_lint_family_fails_lint` (`e2e`),
      in the form of `test_a_print_in_a_library_module_fails_lint`. It
      copies `pyproject.toml` into `tmp_path` and plants the two modules
      measured above (`planted.py` and `planted2.py`) under each of
      `openspec_graph/`, `tools/` and `tests/`, PT011's `pytest.raises` in
      the `tests/` copy only. It runs `python -m ruff check --no-cache
      --output-format concise` from there under `env_without_coverage()`,
      and asserts every code of the selection at every path where it is
      planted.
  - `tests/test_static_ratchets.py`, beside
    `test_every_docstring_exemption_matches_its_ceiling`:
    - `test_the_count_reads_the_target_version_the_project_declares`
      (`unit`). `ruff_target_version` gives:
      - `py310` for `requires-python = ">=3.10"`, and `py311` for `>=3.11`;
      - `py310` for the compound `>=3.10,<4`, and `py310` for `~=3.10`;
      - `py310` with no problem when `[tool.ruff] target-version =
        "py310"` sits under `>=3.10`;
      - `py310` and a problem naming both versions when `[tool.ruff]
        target-version = "py38"` sits under `>=3.10`;
      - no version and a named problem for a missing `requires-python`,
        and for `<4`.
    - `test_no_new_lint_family_finding_survives_the_isolated_count` (`e2e`),
      under `env_without_coverage()` from `REPO_ROOT`:
      - `ruff_target_version(read_pyproject())` returns no problem;
      - `ruff_zero_cost_command` at that version, over `openspec_graph`,
        `tools` and `tests`, exits 0 with an empty stderr and no finding,
        each listed as `file:line code`;
      - `unlinted_modules` of ruff's list against `git ls-files --cached
        --others --exclude-standard -- openspec_graph tools tests`, kept to
        `*.py` and `*.pyi`, names nothing. That is the file walk
        `tests/test_agent_artifacts.py` uses, but a non-zero exit of git is
        a named problem here, not an empty list.
    - `test_no_configuration_or_noqa_escape_hides_a_finding_from_the_count`
      (`e2e`), parametrized by escape. Each case copies `pyproject.toml`
      into `tmp_path`, plants the module that carries its code, and runs
      three things:
      - the configured run without the escape, which must report the code
        at the planted site (the control);
      - the configured run with the escape, which must not;
      - the count guard's checks with the escape in place, which must fail.

      The cases are the rows of the escape table above that hid a finding:
      - the prose `noqa`;
      - the per-file `PT`, `PT01`, `FURB1`, `PL` and `ALL`;
      - `[tool.ruff.lint]` `ignore`, `extend-ignore` and `exclude`;
      - `[tool.ruff]` `exclude` and `extend-exclude`;
      - the disarming settings;
      - `[tool.ruff] target-version = "py38"` and a `per-file-target-version`
        of `py38`, over a module holding the `tv2/p.py` constructs. The
        count reports them at the floor, and for the first the reader also
        names the version;
      - a nested `tests/ruff.toml` and an `.ignore` file;
      - `openspec_graph/dist/planted.py`. Both runs miss it, and
        `unlinted_modules`, given the planted tree's `rglob` as the expected
        list, names it.

      Each escape is written into the copied `pyproject.toml` or the planted
      tree, not passed on the command line.

  Record the red, at the unchanged configuration:
  - the presence guard names each missing selection;
  - the planted-violation guard names each unreported code;
  - the count guard lists the twelve findings above;
  - the escape guard's controls fail, because the copied configuration
    does not yet select the families.
- Fix the twelve findings (R-RCS-3, DEC-RCS-006):
  - `python -m ruff check --no-cache --select FURB,PYI --fix openspec_graph
    tools tests` applies the six safe fixes in `openspec_graph/rules.py`,
    `tests/test_properties.py`, `tools/_common.py`,
    `tools/check_promotion.py` and `openspec_graph/delta.py`. Read the diff,
    which must equal the `--diff` recorded above.
  - Add a `match=` to each PT011 site, naming the message measured above:
    `"No closing quotation"`; the three manifest refusals by their own
    words; and `"No space left on device"`. Remove no assertion.
- `pyproject.toml` `[tool.ruff.lint]` (R-RCS-2, R-RCS-4):
  - `select` gains `"A"`, `"ASYNC"`, `"BLE"`, `"FIX"`, `"FLY"`, `"G"`,
    `"INT"`, `"LOG"`, `"PGH"`, `"PLE"`, `"SLOT"`, `"T10"`, `"YTT"`,
    `"FURB"`, `"PYI"` and `"PT011"`, each under its one-line reason.
  - The "Deliberately NOT selected" block is rewritten, one line per
    family, each with its count, its command and `bfbc124` (or the
    implementation head, if Milestone 0 moved a figure):
    - E501 at its true count;
    - ERA at its true count, its reason re-checked;
    - T203 as it is;
    - ANN, with its count beside its reason;
    - D, beyond D100–D103, with D401 and D205;
    - PL: PLE now selected, PLR, PLC and PLW declined with counts, PLW
      named as near zero and unread site by site;
    - FA, inert at a floor of 3.10 or above;
    - TD, subsumed by FIX;
    - PTH, deferred until `prepare-release-0-4-0`'s 3.11 floor, because the
      fix is not neutral for `write_witness`'s tests on 3.10;
    - TRY003/EM, COM812 and TC.
  - No per-file entry, `ignore`, `exclude`, setting or `target-version` is
    added.
- Run `python -m ruff check openspec_graph tests tools` (the lint target's
  recipe) and record exit 0. Run the new guards and the ratchet guards,
  `python -m pytest tests/test_ci_workflow.py tests/test_static_ratchets.py
  -q -p no:cacheprovider`, and the tests of AC-RCS-3. Record all green, and
  the file-list comparison's two lists' sizes.
- `wc -l tests/test_ci_workflow.py tests/test_static_ratchets.py`, against
  `MAX_TEST_MODULE_LINES`. Record both.
- **Gate:** `make pre-pr`

## Milestone 2 — pytest strictness

- Guards first, seen red (R-RCS-8, DEC-RCS-007, DEC-RCS-008). In
  `tests/test_suite_shape.py`, beside
  `test_pytest_registers_exactly_the_three_tier_markers_strictly`:
  - `test_pytest_runs_strict_with_warnings_as_errors` (`integration`):
    - `addopts`, split by `shlex`, holds `--strict-markers`,
      `--strict-config` and `-ra`;
    - `xfail_strict` is `True`;
    - `filterwarnings` is a list whose first entry is `error`;
    - a helper, `_warning_filter_problems(options)`, returns no problem.
  - `test_a_blanket_or_unnarrowed_warning_filter_is_named` (`unit`): the
    helper names each of these:
    - `ignore::DeprecationWarning`;
    - `ignore`;
    - `ignore:msg::mod` with no category;
    - `ignore::UserWarning:` with no module;
    - a list that does not begin with `error`.

    It stays quiet on `ignore::DeprecationWarning:somepkg.mod` after
    `error`.
  - Three nested runs (`e2e`), each copying `pyproject.toml` into
    `tmp_path` and running `python -m pytest -q -p no:cacheprovider` there
    under `env_without_coverage()`, in the form of
    `test_an_unregistered_marker_fails_collection_under_strict_markers`.
    Each asserts its exit code exactly, against `pytest.ExitCode`:
    - `test_a_warning_fails_a_run_under_this_repositorys_config`: a test
      that calls `warnings.warn("rcs-planted-warning-7f3a", UserWarning,
      stacklevel=1)`. `returncode == pytest.ExitCode.TESTS_FAILED`, and
      `rcs-planted-warning-7f3a` in the output on the planted test's
      `FAILED` line;
    - `test_an_unexpected_pass_fails_a_run_under_this_repositorys_config`:
      `@pytest.mark.xfail(reason="rcs-planted-xfail")` on a test that
      passes. `returncode == pytest.ExitCode.TESTS_FAILED`, and
      `[XPASS(strict)] rcs-planted-xfail` in the output;
    - `test_an_unknown_pytest_key_fails_a_run_under_this_repositorys_config`:
      the copied table plus `no_such_key = true`.
      - `returncode == pytest.ExitCode.USAGE_ERROR`, `ERROR: Unknown config
        option: no_such_key` in the output, and `INTERNALERROR` nowhere in
        it.
      - A second run of the same tree with `-o addopts=""`, the durations
        command's override: `returncode != pytest.ExitCode.OK`, and
        `Unknown config option: no_such_key` in the output. The exit
        there is pytest's internal-error code on 9.1.1, recorded above
        and not pinned.

  Record the red on the unchanged configuration: the structural guard names
  each missing option, and each nested run's actual exit and output.
- `pyproject.toml` `[tool.pytest.ini_options]` (R-RCS-6, R-RCS-7):
  - `addopts = "-q --strict-markers --strict-config -ra"`;
  - `xfail_strict = true`;
  - `filterwarnings = ["error"]`;
  - a comment saying three things: that warnings are errors, as measured at
    `bfbc124`; that a later exception is one narrowed `ignore` with its
    reason (R-RCS-7); and why `strict = true` is not used, with what
    `--strict-config` adds over the filter (DEC-RCS-007).

  `testpaths` and `markers` are unchanged.
- The measurement R-RCS-9 requires, on this tree:
  - each tier, `python -m pytest tests/ -m <tier> -p no:cacheprovider -q`;
  - the coverage-measured run, by `make test` itself;
  - the nested runs, inside it.

  Record each total and every failure with its warning and its fix. If a
  warning cannot be fixed at its cause, add one `ignore` under R-RCS-7, and
  record it with the run that needed it.
- `wc -l tests/test_suite_shape.py`, against `MAX_TEST_MODULE_LINES`. It
  stood at 556 of 700 before this milestone.
  - If the guards take it past the bound, the three nested runs and their
    planted sources move, names unchanged, to a module named for the pytest
    configuration, as DEC-RCS-014 says and DEC-TDR-012's split did. The
    structural guard and its helper stay.
  - Record which, with both modules' sizes.
- **Gate:** `make test`

## Milestone 3 — The `run_cli` bound

- Guards first, seen red (R-RCS-11, DEC-RCS-009). In
  `tests/test_cli_surface.py`, beside
  `test_run_cli_injects_coverage_process_start_by_default`, both `e2e` by
  the criterion, since `run_cli`'s body names `subprocess.run`:
  - `test_run_cli_bounds_the_child_with_the_named_timeout`: intercept
    `support.subprocess.run`, call `support.run_cli(repo, "--version")`, and
    assert `captured["timeout"] == support.RUN_CLI_TIMEOUT_SECONDS`;
  - `test_run_cli_lets_a_timeout_propagate_to_its_caller`: the intercepted
    call raises `subprocess.TimeoutExpired(cmd=…, timeout=…)`, and
    `pytest.raises(subprocess.TimeoutExpired)` around `run_cli` sees that
    same object.

  Neither requests the `repo_root` fixture `prepare-release-0-4-0` deletes.
  Record the red: no `timeout` keyword, and an `AttributeError` for the
  missing constant.
- `tests/support.py` (R-RCS-10):
  - `RUN_CLI_TIMEOUT_SECONDS = 120` above `run_cli`, under a comment naming
    four things: what it bounds; `detect.GIT_TIMEOUT_SECONDS` as the
    precedent for a harness constant that is not configuration; this record
    as the value's source; and its limit, that a hang repeating across many
    calls still ends in the job's cancellation;
  - `run_cli` passes `timeout=RUN_CLI_TIMEOUT_SECONDS`;
  - its docstring says a hung child raises `TimeoutExpired` out of the
    helper.

  The value, from the figures above:
  - the slowest CLI child was 0.68 s here and 0.77 s under coverage in the
    first review's run;
  - `test-windows` has run at about twice the Linux legs' wall time;
  - 120 s is more than two orders above that call;
  - the budget worked above holds five or six full waits on a `test` leg
    and seven on `test-windows`.

  Re-time at the head with the scratch plugin under coverage, and record it
  beside the value, with the budget re-worked from that run's job times.
- Confirm the threshold guard is green (`python
  tools/check_no_hardcoded_thresholds.py`, the thresholds target's recipe),
  and record its output. If `close-gate-script-gaps` has merged, record the
  widened guard's verdict too.
- The other 44 call sites are not edited. Their count, by file, stays in
  this record for the package that takes them on.
- **Gate:** `make test`

## Milestone 4 — The typed surface

- Guards first, seen red (R-RCS-12, R-RCS-13, R-RCS-14, DEC-RCS-010,
  DEC-RCS-011):
  - `tests/test_decomposition.py`, beside `test_public_import_compatibility`:
    `test_severity_is_one_literal_shared_by_every_severity_table` (`unit`).
    - `set(typing.get_args(rule_types.Severity))` equals `{ERROR, WARN,
      INFO}`, `set(cli.SEVERITY_ORDER)`, `set(report.SEVERITIES)`,
      `set(report._COMMANDS)` and `set(sarif._LEVELS)`;
    - `len(report.SEVERITIES)` equals that set's size, so the tuple holds
      no duplicate;
    - `"Severity"` is in `rule_types.__all__`.

    It imports `report` and `sarif` from the test, and
    `test_report_has_no_intra_package_imports` stays green.
  - `tests/test_ci_workflow.py`, beside
    `test_a_bare_generic_in_tools_fails_typecheck`:
    `test_a_finding_with_an_unknown_severity_fails_typecheck` (`e2e`).
    - `tmp_path / "planted_severity.py"`, at the temporary directory's root
      and not under a `tests/` path, holds `from openspec_graph.rule_types
      import Finding` and `Finding("X001", "FATAL", "m")`.
    - The guard runs `python -m mypy --config-file <copied pyproject>
      --cache-dir <tmp> planted_severity.py` from `tmp_path`, with the
      repository on `MYPYPATH` so the import resolves and
      `env_without_coverage()` otherwise.
    - It asserts a non-zero exit and an `arg-type` error on that line.
  - `tests/test_release_surface.py`:
    - `test_the_package_ships_a_py_typed_marker` (`integration`):
      `openspec_graph/py.typed` exists and is empty;
    - `test_the_built_wheel_carries_the_py_typed_marker` (`e2e`): `python
      -m build --outdir <tmp> <repo>`, the sdist and then the wheel from
      it. Then `openspec_graph/py.typed` is in the wheel's `namelist()` and
      `<name>-<version>/openspec_graph/py.typed` is in the sdist's
      `tarfile` member names.
      - It skips only when `importlib.util.find_spec("build")` is `None`, or
        when a failed build's combined output carries one of pip's
        resolution or connection messages: "No matching distribution
        found", "Could not find a version that satisfies the requirement",
        "Failed to establish a new connection", "Temporary failure in name
        resolution" or "Network is unreachable".
      - Any other non-zero exit fails, with the exit code and the output's
        tail. That narrows `test_the_real_wheel_passes_the_gate`'s skip on
        any failure, for the reason DEC-RCS-011 gives.

  Record the red: `Severity` missing, `FATAL` accepted, and no marker in the
  tree or either archive.
- `openspec_graph/rule_types.py`:
  - `from typing import Final, Literal`;
  - `Severity = Literal["ERROR", "WARN", "INFO"]`, added to `__all__` in
    ruff's sorted order;
  - `ERROR: Final = "ERROR"`, `WARN: Final = "WARN"` and
    `INFO: Final = "INFO"`, each on its own line, under the existing
    comment;
  - `Finding.severity: Severity` and `Rule.severity: Severity`.

  Nothing else in the module moves, and no docstring is added or removed,
  so its D101 and D102 counts stay at their ceilings. `report.py` and
  `sarif.py` are not edited.
- `openspec_graph/py.typed`: created empty. No `[tool.setuptools]` key.
- Run the type gate (`python -m mypy --config-file pyproject.toml`, the
  typecheck target's recipe) and the ratchet guards. Record the success
  line, and that `MYPY_TESTS_CEILINGS`, `MYPY_WAIVERS` and
  `DOCSTRING_CEILINGS` are unchanged by this change.
- Run the wheel-check target's recipe as it stands at the head, and record
  which recipe that was:
  - at `bfbc124` it is `python -m build --wheel --outdir dist`, then
    `python tools/check_wheel_metadata.py dist`;
  - once `tighten-release-surface`'s implementation has merged, it removes
    `dist/`, builds with `python -m build --outdir dist` (the sdist, then
    the wheel from it), runs `tools/check_wheel_metadata.py` with its
    header-only licence read, and runs `tools/smoke_wheel.py` on that
    wheel.

  Record the wheel's `py.typed` entry from `unzip -l`, and the sdist's from
  `tar tzf` when the recipe built one.
- **Gate:** `make pre-pr`

## Milestone 5 — Documents, records and the verification lines

- `.claude/agents/planlint-verifier.md`: the `ruff`/`mypy` bullet names the
  families this change selects, the pytest posture and the `run_cli`
  bound, with the remediation norm of R-RCS-17, in the shape of the
  sentences beside it. The norm includes that a FIX hit on prose quoting a
  tag word is fixed by rewording the prose, never by a `noqa`.
- `docs/next-steps.md`: one new item, in the "Deferred / out of scope"
  section. It records the Python 3.15 leg (R-RCS-16):
  - deferred by this package;
  - established: the manifest, the images, the dev extra's wheels, and the
    first review's Linux 3.15.0 run under this configuration, with its
    failures named as environmental and none caused by a warning;
  - not established: a Windows 3.15 run, a run on a hosted runner, and how
    `ci-ok` reads a failed experimental leg;
  - DEC-RCS-012's trigger and entry route.
- `CHANGELOG.md` `[Unreleased]` (R-RCS-18), each entry led by
  **`raise-coding-standards`**:
  - `### Changed — the lint families already at zero, pytest strict, the
    CLI subprocess bounded`: the selected families, held by an isolated
    count at the `requires-python` floor, and where the declined list
    lives; `--strict-config`, `-ra`, `xfail_strict` and warnings as errors;
    `RUN_CLI_TIMEOUT_SECONDS`;
  - `### Added — type information for the public API`: `Severity`, and
    `py.typed` (PEP 561), so a typed consumer reads the package's
    annotations.

  If R-RCS-1's deferral was recorded, these go under the `[Unreleased]`
  that follows `[0.4.0]`.
- Re-point the stage-only and partly-cited verification lines of
  `specs/coding-standards/spec.md` to the guards, now that they exist,
  keeping each stage and each selector already there:

  | Criterion | Selector added |
  |---|---|
  | AC-RCS-1 | `test_the_zero_cost_lint_families_are_selected`, `test_the_count_reads_the_target_version_the_project_declares` and `test_no_new_lint_family_finding_survives_the_isolated_count` |
  | AC-RCS-2 | `test_a_planted_violation_of_each_new_lint_family_fails_lint` |
  | AC-RCS-5 | `test_pytest_runs_strict_with_warnings_as_errors` and `test_a_blanket_or_unnarrowed_warning_filter_is_named` |
  | AC-RCS-6 | `test_a_warning_fails_a_run_under_this_repositorys_config`, `test_an_unexpected_pass_fails_a_run_under_this_repositorys_config` and `test_an_unknown_pytest_key_fails_a_run_under_this_repositorys_config` |
  | AC-RCS-8 | `test_run_cli_bounds_the_child_with_the_named_timeout` |
  | AC-RCS-9 | `test_run_cli_lets_a_timeout_propagate_to_its_caller` |
  | AC-RCS-10 | `test_severity_is_one_literal_shared_by_every_severity_table` |
  | AC-RCS-11 | `test_a_finding_with_an_unknown_severity_fails_typecheck` |
  | AC-RCS-13 | `test_the_package_ships_a_py_typed_marker` and `test_the_built_wheel_carries_the_py_typed_marker` |
  | AC-RCS-22 | `test_no_configuration_or_noqa_escape_hides_a_finding_from_the_count` |

  Then run `python -m pytest tests/test_spec_test_citations.py -q -p
  no:cacheprovider`, and record that every selector resolves.
- Run `planlint --target . validate --fail-on INFO --change
  raise-coding-standards`, then the whole tree at `--fail-on ERROR`, and
  record both exit codes. Confirm that `git diff --name-only
  origin/dev...HEAD` names:
  - no other change package;
  - no file under `.github/`;
  - no `Makefile` or `.pre-commit-config.yaml`;
  - no line of `[project]` (C-RCS-1, C-RCS-2, C-RCS-4).
- Re-take Milestone 0's measurements on the finished tree:
  - the count guard's command reads no finding, and the file lists agree;
  - the three tiers' totals;
  - the AST count of `subprocess.run` and of those with a timeout;
  - the per-code counts with the override lifted;
  - the docstring pairs;
  - the run of the stage-citations report (`python tools/stage_citations.py`),
    whose figures include this package.

  Tick each criterion only against its record.
- **Gate:** `make pre-pr`

## Milestone 6 — The CI run, recorded

- Push the implementation's head and record its pull-request run: run id,
  head SHA, the merge SHA it tested (from the `packaging` job's checkout
  line or `git fetch origin refs/pull/<n>/merge`), and every job's verdict.
  Every `test` leg, `test-windows` and `ci-ok` must be green (AC-RCS-20).
  - A leg that is red under the new options is fixed in a follow-up commit,
    itself `make pre-pr` green. The fix is at the cause, or one narrowed
    `ignore` under R-RCS-7 recorded with the leg that needed it, and never
    a widened filter.
  - The CI-ok aggregate's reading of the run is recorded too.
- Record the merge order and the release of AC-RCS-21:
  - the 0.3.0 hold's facts, and this package's merge commit;
  - the implementation's merge commit;
  - either that `prepare-release-0-4-0`'s release-prep pull request had not
    opened, or the maintainer's recorded deferral, with its reason and the
    0.4.0 hold's facts, `git ls-remote --tags origin 'v0.4.0'` and `git
    merge-base --is-ancestor 'v0.4.0^{commit}' origin/dev`, each with its
    output and the date.
- **Gate:** `make pre-pr`
