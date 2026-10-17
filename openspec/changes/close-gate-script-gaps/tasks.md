# Tasks: close-gate-script-gaps

Drafted at `bfbc124` (`origin/dev`) on `claude/close-gate-script-gaps`,
2026-10-16, from a review of `dev` the same day, and revised at `bfbc124` on
2026-10-17 to resolve `spec-adversary`'s first review. The package lands
first, then its work, in two pull requests (DEC-GSG-001, C-GSG-7):

- **The package pull request** carries this directory alone into `dev`, with
  no code, as #58 did for `lean-production-tree` and #60 for
  `prepare-release-0-4-0`. It is held until the 0.3.0 promotion is done:
  `v0.3.0` tagged and published, and its record merged into `dev`.
- **The implementation pull request** (Milestones 0 to 6) is a new pull
  request from `dev`. It opens as a GitHub draft and is marked ready for
  review only after Milestone 0's gate is recorded here. It must merge before
  `prepare-release-0-4-0`'s release-prep pull request is cut, or the change
  misses 0.4.0.

Every line number below was read at `bfbc124` and is re-read at the
implementation branch's head before the milestone that uses it. A sibling
landing first may move a line without moving the fact. Every number names
the command that produced it. The scratch scripts named here were one-off,
read-only with respect to the repository, run from the session's scratch
directory, and are not committed. Each loaded the real script from the
worktree by path and wrote planted trees only under that scratch directory.

## Measured at `bfbc124` (2026-10-16)

- **The gate, before any file of this package existed.** `planlint --target
  . validate --fail-on ERROR`: `57 spec(s) checked · 0 error · 0 warn · 0
  info`, `PASS`, exit 0. `python tools/stage_citations.py`, which the
  stage-citations target runs: `57 spec(s); 17 stage(s) cited; 12 on a
  verification line; 6 of those invoked by no scanned workflow: ci,
  coverage-tools, security, thresholds, validate, wheel-check`, exit 0. Those
  six are why this package's verification lines cite only `make test`,
  `make docs-check` and `make pre-pr`.
- **The siblings.** `grep -c '^- \[x\] \*\*AC-'` over each spec and `grep -c
  '^## Milestone.*\[DONE\]'` over each `tasks.md`: `lean-production-tree` 0
  ticked of 20, 0 milestones done; `harden-release-pipeline` 0 of 26, 0;
  `prepare-release-0-4-0` 0 of 25, 0. `tools/release_notes.py` does not exist.
- **The threshold guard, planted** (scratch `plant_thresholds.py`). It built
  one root per case under scratch, each holding a clean `Makefile`
  (`test:\n\tpytest -q\n`), a clean `.github/workflows/ci.yml` and a copy of
  this repository's `pyproject.toml`, plus the case's one file. It ran the
  current guard's `main(["x"], root)` in-process and the scratch prototype
  (`proto_guard.py`) as a process. The prototype's word list was the
  superset DEC-GSG-005 now adopts — `minimum`, `maximum` and trailing-s
  plurals included — not the narrower list the first draft of DEC-GSG-005
  stated. The clean baseline: current 0, prototype 0. Per case, current /
  prototype:

  | # | Planted | Current | Prototype |
  |---|---|---|---|
  | 00 | control: `--cov-fail-under=90` in a workflow `run:` | caught | caught |
  | 01 | `pytest --cov-fail-under=9` in the Makefile | missed | caught |
  | 02 | `pytest --cov-fail-under=97.5` in the Makefile | missed | caught |
  | 03 | `COV_FAIL_UNDER: 90` under a workflow `env:` | missed | caught |
  | 04 | `pytest --cov-fail-under 90` in a workflow | missed | caught |
  | 05 | `--per-file-min 85` in a workflow | missed | caught |
  | 06 | `pip install coverage==7.6.1` in a workflow | missed | missed |
  | 07 | `pip install pytest-cov==5.0.0` in a workflow | missed | caught |
  | 08 | `pip install 'ruff>=0.4'` in a workflow | missed | caught |
  | 09 | `pip install 'mypy~=1.11'` in a workflow | missed | caught |
  | 10 | `--cov-fail-under=90` in `.github/actions/x/action.yml` | missed | caught |
  | 11 | the same in `templates/spec-gate.yml` | missed | caught |
  | 12 | the same in `skills/s/assets/spec-gate.yml` | missed | caught |
  | 13 | the same as an `entry:` in `.pre-commit-config.yaml` | missed | caught |
  | 14 | the same as a `RUN` in the `Dockerfile` | missed | caught |
  | 15 | `COVERAGE_FLOOR = 90` in `tools/t.py` | missed | caught |

  Summary line: `current guard caught 1 of 16; prototype caught 15 of 16`.
  The review reported 1 of 10 on its own set; the shapes agree. Case 06 is
  missed by the prototype because `coverage` is not a dev-extra name
  (DEC-GSG-006).
- **The prototype on the real tree** (`python -I proto_guard.py
  <worktree>`). It scanned `Makefile`, `.github/workflows/ci.yml`,
  `.github/workflows/release.yml`, `.github/actions/planlint/action.yml`,
  `templates/spec-gate.yml`,
  `skills/planlint-spec-governance/assets/spec-gate.yml`,
  `.pre-commit-config.yaml`, `.pre-commit-hooks.yaml` and `Dockerfile`, plus
  `tools/*.py` for constants. It read the dev-extra names `pytest`,
  `pytest-cov`, `ruff`, `mypy`, `build`, `hypothesis`, `vulture`, `tomli`.
  - Output: `named-flag Makefile:11: NO_FLOOR 0 in: NO_FLOOR := 0`, then
    `1 hit(s)`, exit 1. The same with comment lines scanned in every file:
    the same single hit.
  - The first prototype run, before Make's assignment operators were in the
    separator class, printed `0 hit(s)`. That is the miss DEC-GSG-005
    records.
- **Every module-level numeric constant in `tools/*.py`, any name** (scratch
  `all_consts.py`, `ast` over each module): `tools/dead_code.py:93:
  VULTURE_CLEAN = 0`, `tools/dead_code.py:94: VULTURE_FOUND = 3`,
  `tools/stage_citations.py:69: SCHEMA_VERSION = 1`. None carries a word of
  R-GSG-3, so the constants rule reports nothing on the tree.
- **The quiet and loud strings** (scratch `quiet_check.py`, the prototype's
  line rules plus `coverage` as a name):
  - Quiet, all 18:
    - workflow keys: `timeout-minutes: 15`, `PYTHON_DEFAULT: "3.12"`,
      `fail-fast: false`, `fetch-depth: 0  # gitleaks scans history`,
      `python-version: ['3.11', '3.12', '3.13', '3.14']`;
    - workflow lines: a SHA-pinned `uses:` with `# v7.0.1`, the
      `concurrency.group` expression, `- run: make test`;
    - installs and builds: `pip install -e ".[dev]"`, `pip install build`,
      `python -m build --outdir dist`, `ruff check . > ruff.txt`,
      `python -m pip install --quiet "planlint==${INPUT_VERSION}"`;
    - the `Dockerfile`'s digest-pinned `FROM` and its `useradd --uid 10001`;
    - Makefile lines: `$(PY) tools/check_coverage_floor.py coverage.json`,
      `python -m pytest tests/`, and the `coverage-per-file` help line.
  - Loud, all 15:
    - named flags and keys: `COV_FAIL_UNDER: 90`, `--cov-fail-under 90`,
      `--cov-fail-under=9`, `--cov-fail-under=97.5`, `--per-file-min 85`,
      `--max-ratio 0.25`, `--threshold=3`, `NO_FLOOR := 0`, `FLOOR ?= 5`,
      `fail_under: 97`;
    - pins: `coverage==7.6.1`, `'pytest_cov ~= 5.0'`, `'ruff[x]>=0.4'`,
      `'mypy!=1.11'`, `'vulture<3'`.
- **The reader** (scratch `measure_reader.py`). Values planted as
  `[tool.coverage.report]\nfail_under = <value>\n`. First number:
  `_common.read_pyproject_int(p, "[tool.coverage.report]", "fail_under")`.
  Second: `thresholds.as_threshold_number` over `thresholds._TOML_FAIL_UNDER`'s
  capture.

  | Value | Tools reader | Product reader |
  |---|---|---|
  | `97` | `97` | `97` |
  | `97.5` | `97` | `97.5` |
  | `9_5` | `9` | `None` |
  | `97 # why` | `97` | `97` |
  | `+97` | `None` | `None` |
  | `0x61` | `0` | `None` |
  | `97e0` | `97` | `None` |
  | `"97"` | `None` | `None` |
  | `97abc` | `97` | `None` |
  | `-1` | `None` | `None` |

  End to end, `check_coverage_floor.main(["check_coverage_floor.py",
  "coverage.json"])` in a planted tree with `num_statements` 1000 and
  `covered_lines` 972:
  - `fail_under = 97.5` gave exit 0, `line coverage 97.2% (972/1000) meets
    floor 97%`;
  - `fail_under = 9_5` gave exit 0, `line coverage 97.2% (972/1000) meets
    floor 9%`.
- **The secret scan** (scratch `measure_secrets.py`). No git process was
  started. The loaded script's `subprocess.run` was replaced by a stub
  returning git's result, and `run_gitleaks` by one returning `(-1, "gitleaks
  not installed")`. Each tree held one file carrying an AWS-shaped key,
  assembled at run time as the suite assembles it.
  - Exit 128, `fatal: not a git repository (or any of the parent
    directories): .git`: `main` exit 0, `PASS: no secrets found (gitleaks
    absent, fallback scan clean)`.
  - Exit 128, `fatal: detected dubious ownership in repository at '/x'`: the
    same PASS, exit 0.
  - Exit 0, stdout `"cl\303\251.py"\n`, with the key in a file named
    `clé.py`: the same PASS, exit 0. `_tracked_files` returned
    `['"cl\\303\\251.py"']`, and `is_file()` was `[False]`. The NUL-split
    form `clé.py\0` gives `is_file()` `[True]`.
  - `which gitleaks` in this container: exit 1.
  - A `pathlib` walk of the worktree, `.git` excluded, found no non-ASCII
    path.
  - Every `gitleaks` in `.github/workflows/*.yml` is the `security` job's
    `gitleaks/gitleaks-action` step (`grep -n gitleaks`). `make pre-pr` runs
    at `ci.yml:490` (`release-tier`) and `release.yml:68` (`gate`).
- **The coverage checkers** (scratch `measure_cwd.py`). Each script was run
  as `python tools/<script>.py <report>` against one planted report
  (`num_statements` 100, `covered_lines` 50, `num_branches` 10,
  `covered_branches` 5):
  - **From a directory with no `pyproject.toml`.** `check_coverage_floor.py`
    exit 2, `no line floor set in pyproject.toml [tool.coverage.report]
    fail_under`. `check_branch_coverage.py` exit 2, `no branch_fail_under set
    in pyproject.toml [tool.specgraph]`.
  - **From a directory whose `pyproject.toml` sets `fail_under = 40` and
    `branch_fail_under = 40`.** `check_coverage_floor.py` exit 0, `line
    coverage 50.0% (50/100) meets floor 40%`. `check_branch_coverage.py`
    exit 0, `branch coverage 50.0% (5/10) meets floor 40%`.
  - **From the worktree root.** `check_coverage_floor.py` exit 1, `line
    coverage 50.0% (50/100) below floor 97% from pyproject.toml`.
    `check_branch_coverage.py` exit 1, `branch coverage 50.0% (5/10
    branches) below floor 95% from pyproject.toml`.
- **The citations** (`grep -l <name> openspec/changes/*/specs/*/spec.md | wc
  -l`):
  - `test_fallback_scan_returns_nothing_outside_a_git_repo`: 0;
  - `test_threshold_guard_passes_on_a_clean_tree` and
    `test_threshold_guard_fails_on_a_hard_coded_coverage_floor`: 3 each;
  - `test_threshold_guard_fails_on_a_floor_pinned_in_a_workflow`,
    `test_threshold_guard_fails_on_a_pinned_tool_version` and
    `test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency`: 2
    each;
  - `test_every_workflow_is_scanned_by_the_threshold_guard`: 3;
  - `test_threshold_guard_scans_every_workflow`: 1;
  - `test_gate_script_is_runnable_as_a_script`: 7.
- **The sites, with line numbers at `bfbc124`.**
  - `tools/check_no_hardcoded_thresholds.py`:
    - the docstring, with "pinned path", at 1–13;
    - `_THRESHOLD_TOKEN` at 50;
    - `check_makefile`'s `except OSError: return findings` at 78–79;
    - `check_workflow`'s two `re.search` rules at 99 and 102;
    - `targets` at 107–135;
    - the PASS line at 153.
  - `tools/_common.py`:
    - `read_pyproject_int` at 200–224, its pattern at 219 and its 3.10
      sentence at 203–205;
    - `has_pyproject_key` at 188–197;
    - `coverage_sources` at 329–367;
    - `ReportError` at 518.
  - `tools/check_secrets.py`:
    - the allowlist claim at 8–10;
    - `_tracked_files` at 44–51;
    - the silent `except OSError: continue` at 78–79.
  - The coverage checkers:
    - `tools/check_coverage_floor.py`'s `Path("pyproject.toml")` at 105,
      139 and 146;
    - `tools/check_branch_coverage.py`'s at 70 and 80;
    - `tools/_common.py`'s `parse_coverage_argv` default `coverage.json` at
      484.
  - The other callers: `tools/dead_code.py`'s `read_config` at 143–161, and
    `tools/matcher_accuracy.py`'s `_floor` at 237–238.
  - The tests:
    - `tests/test_gate_scripts.py`:
      `test_fallback_scan_returns_nothing_outside_a_git_repo` at 164–168,
      and `test_gate_script_is_runnable_as_a_script` at 401–464;
    - `tests/test_threshold_guard.py`'s `_guard_tree` at 142–148;
    - `tests/test_skill_distribution.py`'s
      `test_threshold_guard_scans_every_workflow` at 194–219, with the
      per-target assertion at 219.
  - The documents and config:
    - the `Makefile`: `NO_FLOOR := 0` at 11 and the thresholds help text at 88;
    - `README.md`: the gates row at 369 and the paragraph at 381–385;
    - `docs/hooks.md`: 26, and the every-workflow note at 148–150;
    - `docs/aqa.md`: 30–37;
    - `tools/AGENTS.md`: the bullet at 29–32;
    - `pyproject.toml`: the dev extra at 270–302.
- **The budgets.** `wc -l`: `tools/AGENTS.md` 59 against `MAX_NESTED_LINES =
  60` (`tests/test_agent_artifacts.py:454`). `tests/test_gate_scripts.py`
  464, `tests/test_threshold_guard.py` 227, `tests/test_coverage_checkers.py`
  604 and `tests/test_skill_distribution.py` 352, against
  `MAX_TEST_MODULE_LINES = 700` (`tests/test_suite_shape.py:44`).
  `DOCSTRING_CEILINGS` (`tests/test_static_ratchets.py`):
  - `tools/check_no_hardcoded_thresholds.py` `{"D103": 3}`;
  - `tools/check_secrets.py` `{"D103": 1}`;
  - `tools/check_coverage_floor.py` and `tools/check_branch_coverage.py`
    `{"D103": 2}`;
  - `tools/matcher_accuracy.py` `{"D102": 3, "D103": 1}`.
- **`coverage` as a dependency.** `python -m pip show coverage pytest-cov`:
  `coverage 7.16.2`, `pytest-cov 7.1.0`, `Requires: coverage, pluggy,
  pytest`. `Makefile:24`: `python -m coverage erase`.

## Re-checked at `bfbc124`, 2026-10-17 (the first review)

Every figure here was re-measured for this revision at `bfbc124`, Python
3.13.16, from session scratch. The scripts are `proto_rev.py`,
`lines_rev.py`, `reader_rev.py`, `secrets_rev.py` and `guard_ascii.py`, not
committed, and the reviewer's fixtures were read in place.

- **The gate before the revision.** `planlint --target . validate --fail-on
  ERROR`: `58 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`, exit 0.
- **The revised rules on the real tree** (`python -I proto_rev.py tree
  <worktree>`). This is R-GSG-1 to R-GSG-5 as revised:
  - `Dockerfile*`;
  - R-GSG-2's floor and pin rules over every non-makefile line;
  - the named rule with the widened words and the argument-list separator,
    skipping whole-line comments, with `max-parallel` excluded;
  - the pin rule over comment lines outside the makefile;
  - one finding per number and per pin.

  It scanned the nine files listed above, plus `tools/*.py`, with the
  dev-extra names above plus `coverage`. Output: `named:NO_FLOOR=0
  Makefile:11: NO_FLOOR := 0`, then `1 hit(s) over 9 text file(s)`, exit 1.
  This is the same single hit as the drafting prototype. The constants rule,
  with the widened words, reports nothing. The named rule over the tree's
  whole-line comments alone (`python -I lines_rev.py <worktree>`, part 2)
  gives `0 comment hit(s)`, so skipping them changes nothing on the tree.
- **The planted table, re-run** (`python -I proto_rev.py tree <case>` over
  each of the reviewer's `plants-thresholds/` roots): the baseline gives
  `0 hit(s)`. Every one of cases 00 to 15 gives exactly `1 hit(s)`, so 16 of
  16 are caught, each once:
  - 00 and 10 to 14 by R-GSG-2's floor rule, which now runs over every
    non-makefile target;
  - 01 to 05 by the named rule;
  - 06 to 09 by the pin rule, `coverage` included;
  - 15 by the constants rule.
- **The reviewer's planted lines** (`python -I lines_rev.py <worktree>`,
  part 1, the table of the reviewer's `planted_lines.py` plus the
  argument-list lines of `argv_sep.py`). Each through the revised model:
  - **Quiet.** `timeout-minutes: 15`, `fetch-depth: 0`, both
    `python-version` spellings, `open-pull-requests-limit: 5`,
    `retention-days: 7`, `max-parallel: 4`, `pytest --maxfail=1` and
    `--maxfail 2`, and the four comment-prose lines ("under 5 minutes",
    "max 3 times", "the floor 97", "the threshold: 1"). Also `min-version:`,
    `ruff check --line-length 100`, the cache key, the `HEALTHCHECK`,
    `head -n 1`, `python-version: '>=3.10'`, `pip install --timeout 60` and
    `$(MAKE) -j 4 test`.
  - **Flagged by design** (DEC-GSG-005): `--hypothesis-max-examples=200`,
    `--max-count=1`, `--max-time 30` and `--retry-max-time 60`.
  - **Loud, as wanted.**
    - Named: `--minimum 90`, `--maximum-ratio-pct 5`, `COVERAGE_FLOORS: 90`,
      `--thresholds=3`, `MIN_COVERAGE: 90`, a quoted `run:` and a quoted
      value, `args: [--cov-fail-under, "90"]`, its unquoted and both-quoted
      spellings, `RUN ["pytest", "--cov-fail-under", "90"]`, a YAML anchor
      `&floor 90`, a flow-map `env:`, `FLOOR=90 make test`,
      `export COV_MIN=90`, `--min-coverage 90%` and
      `--cov-fail-under=9` in a makefile.
    - Pins: `'coverage[toml]==7.6'`, `'ruff == 0.4'`, `pytest_cov==5`,
      `Pytest-Cov==5` and `mypy===1.11`.
    - Pins already caught by today's rule, each reported once with its
      message: `python -m pip install pytest==8`, `pip install ruff==0.4.2`,
      and the same in a comment line.

    Without the argument-list separator, `argv_sep.py` shows the three
    argument-list spellings quiet; with it, the Python version list, the SHA
    line, `timeout-minutes`, `types: [python]` and `fetch-depth: 0` stay
    quiet.
  - **Accepted misses, quiet** (DEC-GSG-005): `${FLOOR:-90}` in a makefile,
    `${{ inputs.floor || 90 }}` in a workflow, `rev: v0.4.2  # ruff`.
  - **Quiet under `proto_rev.py`, and since decided**, as "The five lines
    left open, decided" below records: `COVERAGE: 90` and `COV ?= 9`, whose
    names carry no word; `"fail_under": 90`, whose closing quote before `:`
    no separator then allowed; `pip install ruff@git+https://x` and
    `uvx ruff@0.4.2 check .`, whose `@` was not then a pin operator.
- **`max-parallel` and `rev:` on the tree.** `grep -rn max-parallel` outside
  this package: nothing. `grep -n "rev:" .pre-commit-config.yaml
  .pre-commit-hooks.yaml`: one line, `.pre-commit-hooks.yaml:10`, a comment
  `#       rev: v0.3.0`, the adopter's example pin of planlint itself.
- **The reader** (`python -I reader_rev.py <worktree>`, in memory). Each
  line was read by today's pattern, R-GSG-11's anchored pattern with
  refusal, the product's `_TOML_FAIL_UNDER` with `as_threshold_number`, and
  `tomllib.loads`. `THRESHOLD_MIN, THRESHOLD_MAX = 0 100`.

  | Line value | Today | R-GSG-11 | Product | `tomllib` |
  |---|---|---|---|---|
  | `97` | `97` | `97` | `97` | `97` (int) |
  | `97  # why` | `97` | `97` | `97` | `97` (int) |
  | `0` | `0` | `0` | `0` | `0` (int) |
  | `100` | `100` | `100` | `100` | `100` (int) |
  | `101` | `101` | `101` | `None` | `101` (int) |
  | `097` | `97` | `97` | `97` | `TOMLDecodeError` |
  | `97.5` | `97` | refuse | `97.5` | `97.5` (float) |
  | `9_5` | `9` | refuse | `None` | `95` (int) |
  | `+97` | `None` | refuse | `None` | `97` (int) |
  | `-1` | `None` | refuse | `None` | `-1` (int) |
  | `0x61` | `0` | refuse | `None` | `97` (int) |
  | `0o141` | `0` | refuse | `None` | `97` (int) |
  | `97e0` | `97` | refuse | `None` | `97.0` (float) |
  | `"97"` | `None` | refuse | `None` | `'97'` (str) |
  | `97abc` | `97` | refuse | `None` | `TOMLDecodeError` |
  | `"fail_under" = 97` | `None` | refuse | `None` | `97` (int) |
  | `'fail_under' = 97` | `None` | refuse | `None` | `97` (int) |

  Every in-range value R-GSG-11 reads agrees with the product. `101` is the
  one out-of-range value it reads. `097` is read as 97 by both regular
  expressions and rejected by `tomllib`. A `tomllib` reader would refuse
  more there, never less, so it is not a disagreement R-GSG-13 governs.
- **`101` end to end.** A planted tree with `fail_under = 101` and a report
  at 10 of 10 statements: `python tools/check_coverage_floor.py
  coverage.json` printed `line coverage 100.0% (10/10) below floor 101% from
  pyproject.toml`, exit 1. The product's reader of the same line:
  `None`.
- **The coverage checkers, below the project root** (the reviewer's
  `covproj/`, `[tool.coverage.report] fail_under = 60` at its root, the
  report at `out/coverage.json`):
  - `ls -A out`: `coverage.json` alone;
  - from `covproj/`, `python <worktree>/tools/check_coverage_floor.py
    out/coverage.json`: `line coverage 75.0% (3/4) meets floor 60%`, exit 0;
  - from `covproj/out/`, the same script on `coverage.json`: `no line floor
    set in pyproject.toml [tool.coverage.report] fail_under`, exit 2. This
    is what the first draft's "beside the report" rule would have read from
    anywhere.
- **A missing report.** From a directory holding neither a report nor a
  `pyproject.toml` (the reviewer's `fx/nogit/`), `check_coverage_floor.py
  missing.json` printed `no line floor set in pyproject.toml
  [tool.coverage.report] fail_under`, exit 2, and `check_branch_coverage.py
  missing.json` printed `no branch_fail_under set in pyproject.toml
  [tool.specgraph]`, exit 2. From the worktree root,
  `check_coverage_floor.py /nonexistent/coverage.json` printed `coverage
  file not found: /nonexistent/coverage.json; run coverage first`, exit 2.
- **The secret scan, nothing to scan** (`python -I secrets_rev.py
  <worktree> <review> allskipped`, over the reviewer's `fx/allskipped/`: a
  `git init` repository whose one commit tracks `node_modules/k.js`, since
  deleted from disk; the loaded script runs `git ls-files` itself).
  `_tracked_files` listed `['node_modules/k.js']`, on disk `[False]`,
  skip-listed `[True]`. `main` printed `PASS: no secrets found (gitleaks
  absent, fallback scan clean)` and returned 0.
- **The console** (`PYTHONIOENCODING=ascii python -s <script>`, since `-I`
  ignores that variable):
  - `secrets_rev.py ... nonascii`, with `_tracked_files` stubbed to the
    NUL-split `[root / "clé.py"]` over the reviewer's `fx/nonascii/`. The
    traceback ends `UnicodeEncodeError: 'ascii' codec can't encode character
    '\xe9' in position 8: ordinal not in range(128)`, the process exits 1,
    and stdout is empty. On a UTF-8 console the same run prints `FAIL:
    clé.py: potential secret (AKIAIOSFODNN...)` and `main` returns 1.
  - `guard_ascii.py`, the current guard's `main` over a planted root named
    `racine-é` whose `Makefile` holds `pytest --cov-fail-under=90`. The same
    `UnicodeEncodeError`, at position 107, and exit 1. On a UTF-8 console it
    prints the FAIL line with the absolute path.
  - `grep -rn reconfigure tools/`: nothing. `openspec_graph/cli.py:1003-1004`
    calls `stream.reconfigure(encoding="utf-8", errors="backslashreplace")`
    under `contextlib.suppress(ValueError, OSError)`, the
    `fix-stdout-encoding-crash` mechanism (R-SE-1, R-SE-3, DEC-SE-004).
  - The same reconfigure under `PYTHONIOENCODING=ascii` (`python -s -c`
    printing `FAIL: templates/spé.yml` and a lone surrogate, piped to
    `od -c`): `é` is written as the UTF-8 bytes `303 251`, the surrogate as
    `\udce9`, exit 0. A path is written as UTF-8, not escaped.
  - `ci.yml:130-152`: the `encoding-stress` job sets `PYTHONIOENCODING:
    ascii` and runs the e2e-live target, which exercises the product only.
- **The workflow assertion.** `tests/test_release_surface.py:119-138`:
  `test_every_workflow_is_scanned_by_the_threshold_guard` ends `assert
  mod.check_workflow(WORKFLOWS / name) == []` for each workflow, before any
  whitelist. `harden-release-pipeline`'s AC-HRP-23 cites it, as a test that
  passes unedited.
- **The whitelist precedent.** `tools/dead_code.py:88`: `WHITELIST =
  Path("tools") / "dead_code_whitelist.txt"`, read as `root / WHITELIST` at
  230 and 301. `:108`: `_WHITELIST_LINE =
  re.compile(r"^(?P<name>\S+)\s+#\s*(?P<reason>\S.*)$")`.
- **The two skip lists.** `tools/check_secrets.py:41`: `_SKIP_DIRS = {".git",
  ".venv", "venv", "__pycache__", ".ruff_cache", ".mypy_cache",
  "node_modules"}`. `.gitleaks.toml`'s `[allowlist] paths`: `.git/.*`,
  `.venv/.*`, `node_modules/.*`.
- **Outside the dev extra.** `pyproject.toml:15`: `requires =
  ["setuptools>=77"]`. `grep -rn "upgrade pip" .github/workflows/*.yml | wc
  -l`: 10, each `python -m pip install --upgrade pip`, unpinned.
- **The documents R-GSG-23 now adds.**
  - `tools/_common.py:91-92`, in `resolve_makefile`'s docstring: "which is
    why ``check_makefile`` tolerates a path it cannot open".
  - `docs/aqa.md:13`: the security row, `committed secret → exit 1`.
  - `tests/support.py:345-346`, in `run_tool_main`'s docstring: "These
    scripts read ``Path("pyproject.toml")`` from the cwd".
  - `.claude/agents/planlint-verifier.md:16`: "it allowlists comments,
    `$(...)`, `@echo`, and recursive `make` invocations".
    `tests/test_agent_skill_docs.py` checks every backticked path and target
    in that file.
- **The siblings not on `dev`** (read in their own worktrees at `bfbc124`,
  where each package is the one untracked directory):
  - `tighten-release-surface`. Its proposal edits `README.md`'s gates table
    (a `wheel-check` row), `docs/hooks.md`'s opening and pre-commit
    paragraphs and the CI table's `security` cell, and `docs/aqa.md`'s
    "Reproducing CI locally" and a sentence after its Gates table. It also
    edits `.pre-commit-config.yaml`'s header comment, the `Makefile`'s
    `wheel-check` recipe, and `ci.yml`'s `security` step, which then calls
    the thresholds target. Its tasks.md leaves `docs/hooks.md:20-26`
    unchanged. Its planned recipe lines (`rm -rf dist`, `python -m build
    --outdir dist`, `python tools/check_wheel_metadata.py dist`, `python
    tools/smoke_wheel.py dist --sdist --expect
    tests/fixtures/action/passing=0 --expect
    tests/fixtures/action/failing=1`), and a `run:` line calling the
    thresholds or the wheel-check target, are each quiet under
    `proto_rev.py`'s `judge`.
  - `raise-coding-standards`. Its tasks.md lists `tools/_common.py:317`
    (`_SOURCE_ARRAY`, FURB167) and `:324` (`normalize_scope`, FURB188), above
    `coverage_sources` at 329. It adds the families BLE, G, LOG and FURB, the
    rule PT011, and `filterwarnings = ["error"]`, `xfail_strict = true` and
    `--strict-config`. It adds `RUN_CLI_TIMEOUT_SECONDS` above `run_cli`
    (`tests/support.py:139`), and `run_tool_main` is at 332. The constant's
    segments `RUN`, `CLI`, `TIMEOUT` and `SECONDS` carry no word of R-GSG-3.
- **The prefix.** `grep -rlE "(R|AC|DEC|C)-GSG-[0-9]+"` over every
  `openspec/changes/` in this worktree and both sibling worktrees: this
  package's files alone.
- **The five lines left open, decided** (2026-10-17, at `bfbc124`). The
  five lines the first revision left open were decided after it. Scratch
  `proto_rev2.py` is `proto_rev.py` with two changes:
  - the named rule's separator admits an optional closing quote before `:`
    or `=` (`["']?\s*[:=]`);
  - the pin rule treats `@` directly after a dev-extra name as a pin, with
    nothing required after it.

  The measurements:
  - **The real tree** (`python -I -B proto_rev2.py tree <worktree>`): the
    same nine files, then `named:NO_FLOOR=0  Makefile:11: NO_FLOOR := 0` and
    `1 hit(s) over 9 text file(s)`, exit 1.
  - **The planted table** (`python -I -B proto_rev2.py tree <case>` over each
    of the reviewer's `plants-thresholds/` roots): the baseline `0 hit(s)`,
    and each of cases 00 to 15 `1 hit(s)`.
  - **The planted lines** (`python -I -B proto_rev2.py lines`):
    - caught: `"fail_under": 90`, `'fail_under': 90` and `fail_under" = 90`,
      each `named:fail_under=90`; `uvx ruff@0.4.2 check .`,
      `pipx run ruff@0.4.2 check .` and `pip install ruff@git+https://x`,
      each `pin:ruff@`;
    - `pip install ruff==0.4.2`: one finding, `old-pin:ruff==`;
    - accepted, quiet (DEC-GSG-005): `COVERAGE: 90` and `COV ?= 9`;
    - quiet, bare and quoted: `timeout-minutes: 15`, `fetch-depth: 0`,
      `python-version` as a list, a scalar and a quoted key,
      `retention-days: 7`, `open-pull-requests-limit: 5` and
      `max-parallel: 4`;
    - quiet `@`: a SHA-pinned `uses: actions/checkout@` and
      `uses: actions/setup-python@`, a makefile's `@pytest -q` and `$@`, the
      `Dockerfile`'s `FROM python:3.12-slim@sha256:`, and
      `"planlint==${INPUT_VERSION}"`.
  - **Every `@` in the guard's targets** (`grep -noE "[A-Za-z0-9._-]+@"`
    over the nine files): `checkout@` 16, `setup-python@` 14,
    `upload-artifact@` 6, `upload-sarif@` 2, `planlint@` 2,
    `gitleaks-action@` 1, `gh-action-pypi-publish@` 1,
    `download-artifact@` 1 and `3.12-slim@` 1. No dev-extra name stands
    directly before an `@` on the tree.
  - **Three further shapes**, measured here and since decided, as "The
    three further shapes, decided" below records. Under `proto_rev2.py`
    the PEP 508 spelling `pip install 'ruff @ git+https://x'` was quiet, and
    both `uses: someorg/build@v1` and `# ask pytest@example.org` were loud.
- **The three further shapes, decided** (2026-10-17, at `bfbc124`). Scratch
  `proto_rev3.py` is `proto_rev2.py` with the `@` form changed:
  - a dev-extra name directly after a `/` is not a pin, because
    `owner/name@ref` is an action or repository reference;
  - whitespace around the `@` is allowed only when a URL scheme follows it
    (`git+`, `http://`, `https://` or `file:`).

  The measurements:
  - **The real tree** (`python -I -B proto_rev3.py tree <worktree>`): the
    same nine files, then `named:NO_FLOOR=0  Makefile:11: NO_FLOOR := 0` and
    `1 hit(s) over 9 text file(s)`.
  - **Every `uses:` line on the tree** (`python -I -B proto_rev3.py uses
    <worktree>`): `44 uses: line(s) scanned, 0 with a finding`.
  - **The planted table** (`python -I -B proto_rev3.py tree <case>` over each
    of the reviewer's `plants-thresholds/` roots): the baseline `0 hit(s)`,
    and each of cases 00 to 15 `1 hit(s)`.
  - **The planted lines** (`python -I -B proto_rev3.py lines`, the lines of
    `proto_rev2.py` plus these):
    - quiet: `uses: someorg/build@v1`, `uses: someorg/pytest@<sha>`, a
      comment naming `https://github.com/astral-sh/ruff@v1`, and
      `echo ruff @ noon`, a spaced `@` with no scheme after it;
    - loud, each `pin:ruff@`: `pip install 'ruff @ git+https://x'`,
      `'ruff @ https://x/ruff.whl'`, `'ruff @ file:///tmp/ruff.whl'` and
      `'ruff[x] @ git+https://x'`;
    - loud, the accepted false positive of DEC-GSG-005:
      `# ask pytest@example.org`, `pin:pytest@`;
    - every line of `proto_rev2.py` with the same verdict as before.

The first review's findings, each resolved by a decision in the package:

- **M1, the `tomllib` contract.** The type refusals carry forward, and the
  normalised spellings are item 7a's to decide and to re-test. See R-GSG-14,
  DEC-GSG-002 and AC-GSG-12, `dev_extra_names` included, and Milestones 1
  and 4.
- **M2, out of range.** The agreement is scoped to `THRESHOLD_MIN` to
  `THRESHOLD_MAX`, and `101` is recorded as exit 1: R-GSG-13, DEC-GSG-003
  and AC-GSG-12.
- **M3, workflows.** A workflow hit is never whitelisted, and `max-parallel`
  is quiet: R-GSG-3, R-GSG-6, R-GSG-9, DEC-GSG-008, DEC-GSG-009,
  DEC-GSG-013 and AC-GSG-8.
- **M4, comments and `max-*` flags.** The named rule alone skips comment
  lines, and other tools' `max-*` flags are flagged: R-GSG-2, R-GSG-3,
  R-GSG-4 and DEC-GSG-005.
- **M5, the walk.** The nearest `pyproject.toml` at or above the report is
  read, the report is checked first, and `run_tool_main`'s docstring is
  updated: R-GSG-19, R-GSG-23, DEC-GSG-012 and AC-GSG-16.
- **M6, the siblings.** `tighten-release-surface` and
  `raise-coding-standards`: the proposal's "Shared edit sites" and
  DEC-GSG-001.
- **M7, names and subjects.** The script holds no name list beyond R-GSG-2's
  pattern, the old rules' findings carry subjects, a pin is reported once,
  and the source-literal assertion is dropped: R-GSG-4, R-GSG-6, AC-GSG-4
  and Milestone 4.
- **The lower findings, in order.**
  1. The word list: DEC-GSG-005, and the evidence wording above.
  2. The argument-list separator and the accepted misses: R-GSG-3 and
     DEC-GSG-005.
  3. The whitelist under the scanned root, `dead_code.py`'s separator, and
     relative POSIX matching: R-GSG-6 and DEC-GSG-008.
  4. Files scanned, not files listed: R-GSG-16, R-GSG-17 and DEC-GSG-010.
  5. The console: R-GSG-24, DEC-GSG-015 and AC-GSG-23.
  6. Three more documents, and "no runtime dependency": R-GSG-23 and the
     proposal's Non-Goals.
  7. `Dockerfile*`, the security job's inline call, the two skip lists, and
     what the dev extra is not: R-GSG-1, R-GSG-18, DEC-GSG-004, DEC-GSG-006,
     and the proposal's Why.
  8. The report before the configuration: R-GSG-19 and DEC-GSG-012.
  9. `GIT_CEILING_DIRECTORIES`: DEC-GSG-011, AC-GSG-14 and Milestone 2.
  10. Rebuilding the prototype: DEC-GSG-009 and Milestone 0.
- **The five lines the revision left open**, decided afterwards:
  - `COVERAGE: 90` and `COV ?= 9`: accepted misses, DEC-GSG-005;
  - `"fail_under": 90`: caught by the closing quote before `:` or `=`,
    R-GSG-3 and DEC-GSG-005;
  - `uvx ruff@0.4.2` and `ruff@git+...`: caught by `@` as a pin, R-GSG-4,
    R-GSG-6 and DEC-GSG-006.

  Each is in the planted corpus (DEC-GSG-013, Milestone 4).
- **The three further shapes**, decided afterwards:
  - `uses: someorg/build@v1`: quiet, because a name after a `/` is not a pin
    in the `@` form, R-GSG-4 and DEC-GSG-006;
  - `'ruff @ git+https://x'`: caught, because whitespace around the `@` is
    allowed before a URL scheme, R-GSG-4 and DEC-GSG-006;
  - `pytest@example.org` in a comment: an accepted false positive,
    DEC-GSG-005.

  The first two are in the planted corpus (DEC-GSG-013, Milestone 4).

## Milestone 0 — Grounding at the implementation branch's head, recorded before the draft is marked ready

- Confirm the preconditions of DEC-GSG-001 and record each with its output:
  - `v0.3.0` is tagged and published;
  - this package is in `dev` as its own squash, with no code;
  - the implementation pull request is a GitHub draft from `dev`.
- Run the gate and record its exit code before the first edit outside this
  package: `planlint --target . validate --fail-on ERROR`.
- Record which siblings have merged into `dev` since `bfbc124`, with the
  criteria and milestone counts above:
  - `prepare-release-0-4-0`'s pull request 1;
  - the implementations of `lean-production-tree`, `harden-release-pipeline`,
    `tighten-release-surface` and `raise-coding-standards`.

  For each that has merged:
  - re-read the shared sites the proposal names;
  - record whether `read_pyproject_int`'s docstring carries pull request 1's
    wording, which this change then keeps (DEC-GSG-001);
  - record whether the dev extra still lists `tomli`. The pin rule reads the
    extra, so either answer is fine; the record says which tree the
    measurement describes;
  - if `raise-coding-standards` has merged, record its ruff `select` and
    its pytest `filterwarnings`, which this change's code and tests must
    then pass.
- Rebuild the scratch prototype from R-GSG-3 and R-GSG-4 as this spec states
  them, since the drafting scripts are not committed. Then re-run every
  measurement in "Measured at `bfbc124`" and "Re-checked at `bfbc124`" at the
  head, and record the figures beside the drafting ones, each with its
  commit. In particular:
  - re-run the rebuilt patterns over the real tree, now including
    `tools/release_notes.py` and any new `release.yml`, `ci.yml`, `Makefile`
    or `.pre-commit-config.yaml` lines a sibling added;
  - list every hit and decide each by R-GSG-9's test, recording the decision
    and its reason. A hit in a file under `.github/workflows/` is never
    whitelisted. If its sibling has merged, this package cannot move it
    (C-GSG-2): stop, and amend the package by a recorded decision before
    going on (DEC-GSG-009);
  - run `python -m pytest tests/test_release_surface.py -q -k
    test_every_workflow_is_scanned_by_the_threshold_guard` and record it
    green.

  A hit not in the drafting list is a finding to decide here, never a
  pattern to weaken.
- Reproduce the two git-dependent secret-scan cases against real
  repositories, through the suite's own `_git_repo` helper in a scratch
  directory, never committed:
  - a directory with no `.git`, with `GIT_CEILING_DIRECTORIES` set to its
    parent;
  - a committed `clé.py` carrying the planted key.

  Record `main`'s exit and stdout for each with `run_gitleaks` forced absent.
  The drafting measurement injected git's output instead of running git.
- Re-read `tests/test_coverage_checkers.py` and confirm every in-process
  test still passes `coverage.json` with its planted tree as the working
  directory. A test that does otherwise changes DEC-GSG-012's "nothing
  changes" claim and is recorded here.
- Record `spec-adversary`'s review of any revision after this one, if it was
  not resolved before the package pull request merged. Each finding is
  resolved in the package by a decision and listed here, as the first
  review's are above.
- **Gate:** `make test`

## Milestone 1 — The reader reads exactly or refuses, seen red first

- `tests/test_pyproject_reader.py` (new, flat under `tests/`), written
  before the code and run red. Its module `pytestmark` is the tier the
  criterion computes: each test loads `tools/_common.py` in-process and is
  `integration`. Planned tests:
  - `test_read_pyproject_int_reads_only_an_exact_integer`, parametrised:
    - read as the integer: `97`, `97  # why` and `101`;
    - raise, naming file, table, key and value: `"fail_under" = 97`,
      `'fail_under' = 97`, `97.5`, `9_5`, `+97`, `0x61`, `0o141`, `97e0`,
      `"97"`, `97abc` and `-1`;
    - return `None`: an absent key, an absent table and an absent file.

    Each parameter's id says whether it is a type refusal (`97.5`, `97e0`,
    `"97"`), which item 7a keeps, or a spelling `tomllib` normalises (`9_5`,
    `+97`, `0x61`, `0o141`, a quoted key, and `-1`), which item 7a replaces
    (R-GSG-11, R-GSG-14, AC-GSG-10).
  - `test_the_gate_reader_never_disagrees_with_the_product_on_a_floor`. It
    runs over the same corpus. For each in-range line, either the tools
    reader raises, or its integer equals `thresholds.as_threshold_number` of
    `thresholds._TOML_FAIL_UNDER`'s capture. For `101` it asserts the
    recorded outcome instead: the tools reader returns 101, the product's
    returns `None`, and `check_coverage_floor.py`, through `run_tool_main`
    over a planted report at full coverage, exits 1. It asserts that at
    least one line of each kind was compared (R-GSG-13, AC-GSG-12).
  - `test_a_floor_the_reader_cannot_read_exactly_exits_two`, parametrised
    over the callers of R-GSG-12, each fed a planted `= 97.5`:
    - `check_coverage_floor.py`, gate mode, through `run_tool_main` with the
      planted tree as working directory;
    - `check_coverage_floor.py --per-file-min`, on `per_file_line_min`;
    - `check_branch_coverage.py`, on `branch_fail_under`;
    - `dead_code.py`, on `dead_code_min_confidence`, through `--root`;
    - `matcher_accuracy.py --check`, on a floor key, its `repo_root`
      monkeypatched to the planted tree.

    Each asserts exit 2, the key and the value on stderr, no `Traceback`, and
    no `meets floor` or `PASS` on stdout (AC-GSG-11).

  Record the red run as it happens. The drafting expectation is that the
  first test fails on every refused line, which today reads as an integer or
  as absent, and that no caller of the third exits 2: each reads the
  truncated integer and reaches a verdict of its own.
- `tests/test_gate_scripts.py`:
  `test_gate_scripts_print_a_non_ascii_path_on_an_ascii_console` (`e2e`),
  written before the code and run red. It runs each script as a process with
  `PYTHONIOENCODING=ascii` in its environment. This milestone's case is the
  line checker over a planted tree under `tmp_path / "arbre-é"` whose
  `pyproject.toml` holds `fail_under = 97.5`. It asserts exit 2, the UTF-8
  bytes of the `pyproject.toml` path on stderr, and no `Traceback`.
  Milestones 2 and 4 add their cases (R-GSG-24, AC-GSG-23). The drafting
  expectation for the red run is the truncated floor's verdict, exit 0 or 1,
  never 2.
- `tools/_common.py`:
  - `ReportError` moves above `read_pyproject_int`, with
    `PyprojectValueError(ReportError)` beside it.
  - `read_pyproject_int` takes the anchored pattern of R-GSG-11 for the
    bare key. Presence is decided by `has_pyproject_key`, so a present key —
    a quoted spelling included — never returns `None`.
  - Its docstring follows R-GSG-14:
    - the scanner was chosen under the 3.10 floor, and replacing it with
      `tomllib` is `docs/next-steps.md` item 7a's change;
    - the type refusals (a float, an exponent, a string) carry forward to
      item 7a's `tomllib` reader, so their cases in
      `tests/test_pyproject_reader.py` are kept;
    - the spellings `tomllib` normalises (`9_5`, `+97`, `0x61`, `0o141`, a
      quoted key), and with them `-1`, are a decision item 7a records, and
      it replaces those cases rather than keeping them.

    It makes no claim about which interpreters ship `tomllib`.
  - The console helper of R-GSG-24, beside `logger`: it reconfigures
    `sys.stdout` and `sys.stderr` to `encoding="utf-8",
    errors="backslashreplace"`, each call under
    `contextlib.suppress(ValueError, OSError)`, with a docstring citing
    `fix-stdout-encoding-crash`'s DEC-SE-004.
  - Stdlib only: `test_common_module_is_stdlib_only` holds the line.
- `tools/check_coverage_floor.py` and `tools/check_branch_coverage.py`:
  `main` calls the console helper first, and catches `PyprojectValueError`
  around every floor read and returns 2 with the message on stderr.
  `tools/dead_code.py`: `main` calls the console helper first, and needs no
  new branch, because `ReportError` already maps to 2. Confirm with the
  planted case. `tools/matcher_accuracy.py`: `main` calls the console helper
  first, catches the refusal around `_check` and returns 2.
- Run `python -m pytest tests/test_pyproject_reader.py tests/test_coverage_checkers.py
  tests/test_dead_code.py tests/test_matcher_accuracy.py tests/test_gate_scripts.py -q`
  and record it green. Then run `python -m pytest tests/test_suite_shape.py
  tests/test_suite_routing.py -q` for the new module's tier and bound.
- **Gate:** `make test`

## Milestone 2 — The secret scan fails closed, seen red first

- `tests/test_gate_scripts.py`, in the `check_secrets.py` section, written
  before the code and run red:
  - Delete `test_fallback_scan_returns_nothing_outside_a_git_repo`, which no
    spec cites (DEC-GSG-011).
  - `test_fallback_scan_refuses_a_tree_git_cannot_list` (`integration`).
    Its cases:
    - a real `tmp_path` with no `.git`, with `GIT_CEILING_DIRECTORIES` set
      to `tmp_path.parent` through `monkeypatch.setenv`, so git does not walk
      up into an enclosing repository;
    - `subprocess.run` stubbed to exit 128 with git's dubious-ownership
      message;
    - `subprocess.run` stubbed to raise `FileNotFoundError`.

    Each runs `main` with `run_gitleaks` forced absent and asserts exit 2,
    the cause on stderr (git's own stderr for the second), no `PASS` on
    stdout and no `Traceback`.
  - `test_fallback_scan_refuses_undecodable_output_or_nothing_to_scan`
    (`integration`). Stubbed `-z` output of `b"\xff\0"`, of `b""`, and of
    `b"node_modules/k.js\0gone.py\0"` over a tree holding neither path. Each
    gives exit 2, the last naming that no listed file was scanned (R-GSG-16,
    the reviewer's all-skipped repository).
  - `test_fallback_scan_refuses_an_unreadable_tracked_file`
    (`integration`): the stub lists a planted regular file, and
    `PermissionError` is injected into its read, as
    `tests/test_stage_citations.py` injects one. Exit 2, naming the file.
  - `test_tracked_files_asks_git_for_nul_separated_names` (`integration`):
    the stub records its argv, which carries `-z`, and its output `clé.py\0`
    names the planted file.
  - `test_fallback_scan_reads_a_non_ascii_tracked_name` (`e2e`, through
    `_git_repo`): a committed `clé.py` carrying the planted key is a finding
    naming `clé.py`. It must pass on the Windows leg too; record that leg's
    run in Milestone 6.
  - `test_gate_scripts_print_a_non_ascii_path_on_an_ascii_console` gains the
    secret scan's case: the same `_git_repo` with `clé.py`, run as a process
    under `PYTHONIOENCODING=ascii`, exits 1 with the UTF-8 bytes of `clé.py`
    on stdout and no `Traceback`.

  Record the red run as it happens. The drafting expectation:
  - the PASS line with exit 0, or a traceback, in every refusal case, never
    exit 2;
  - no `-z` in the recorded argv;
  - no finding in the e2e test;
  - no finding, so no FAIL line, in the console case.
- `tools/check_secrets.py`:
  - `_tracked_files` runs `["git", "ls-files", "-z"]` with
    `capture_output=True` and no `text`, then decodes `stdout` as strict
    UTF-8 and splits on `"\0"`, dropping the empty tail. It raises a
    module-level `ScanError` naming the cause in three cases:
    - git cannot be started (`OSError`);
    - git exits non-zero, carrying its `stderr` decoded with replacement;
    - git emits undecodable bytes.
  - `fallback_scan` counts the files it reads. It raises `ScanError` when
    the count is zero, after the absent, non-regular and skip-listed paths
    are dropped, and on an `OSError` reading a listed regular file. It keeps
    its skip for an absent or non-regular path, with a DEBUG record whose
    arguments are passed lazily, as `raise-coding-standards`' G and LOG
    families require.
  - `main` calls the console helper first and maps `ScanError` to exit 2,
    with `ERROR: <cause>` on stderr.
  - The module docstring follows R-GSG-18: `_SKIP_DIRS` and
    `.gitleaks.toml`'s allowlist as two lists, what the fallback alone
    skips, `tests/` scanned on purpose, and the refusals.

  Every new public name carries a docstring. Re-run
  `python -m pytest tests/test_static_ratchets.py -q`, and lower
  `tools/check_secrets.py`'s ceiling only if the count fell.
- Run `python -m pytest tests/test_gate_scripts.py tests/test_enterprise.py -q`
  and record it green: the five cited secret tests and
  `test_secret_scan_fallback_catches_fake_key` pass unedited.
- **Gate:** `make test`

## Milestone 3 — The coverage checkers read the nearest configuration at or above their report, seen red first

- `tests/test_coverage_checkers.py`, written before the code and run red:
  - `test_the_coverage_checkers_read_the_nearest_pyproject_at_or_above_the_report`
    (`integration`), parametrised over the line gate, the per-file report and
    the branch gate:
    - The report and a `pyproject.toml` declaring the planted floors sit in
      `tmp_path / "tree"`. A `pyproject.toml` with lower floors sits in
      `tmp_path / "elsewhere"`, which is the working directory. The report is
      passed as an absolute path.
    - A second case moves the report to `tree / "out" / "coverage.json"` and
      runs from `tree`, passing `out/coverage.json`.

    Each asserts the tree's floor in the verdict, and the tree's
    `pyproject.toml` path in the message.
  - `test_a_report_with_no_pyproject_at_or_above_it_exits_two`
    (`integration`): the report alone in a directory, run from a working
    directory holding a `pyproject.toml` with lower floors. It first asserts
    that no `pyproject.toml` exists at or above its `tmp_path`, so a
    `--basetemp` inside a checkout fails that precondition loudly rather than
    the test passing for the wrong reason. Exit 2, naming the directory the
    walk started from.
  - `test_a_missing_report_is_named_before_the_configuration`
    (`integration`): a missing report, run from a directory holding no
    `pyproject.toml`. Both checkers exit 2 with `coverage file not found`
    and no mention of a floor (R-GSG-19).

  Record the red run. The drafting expectation:
  - the first two read the working directory's lower floors and exit 0, as
    "Measured at `bfbc124`" shows;
  - the `out/` case reads `tree/pyproject.toml` from the working directory
    and passes, which is red only on the asserted message;
  - the third reports "no line floor set", as "Re-checked at `bfbc124`"
    shows.
- `tools/check_coverage_floor.py` and `tools/check_branch_coverage.py`:
  - `main` checks `cov_path.exists()` before any configuration read, in
    both modes.
  - The `pyproject.toml` path is found once in `main`, by a stdlib walk:
    `cov_path.resolve().parent`, then each of its parents, the first holding
    a `pyproject.toml` winning. It lives in `tools/_common.py` beside
    `parse_coverage_argv`, so both checkers share it.
  - The path is passed to every read, including `missing_floor_message` and
    the per-file mode. Every message names that path.
  - When the walk finds none, `main` returns 2 with a message naming the
    starting directory.
  - The argv contract and `parse_coverage_argv` are unchanged.
- `tests/support.py`: `run_tool_main`'s docstring sentence "These scripts
  read ``Path("pyproject.toml")`` from the cwd" becomes R-GSG-19's walk. The
  scripts read the `pyproject.toml` nearest their report, at or above it,
  and their tests write both into the throwaway directory they run from.
  The coverage-resolution reasoning that follows is unchanged (R-GSG-23).
- Run `python -m pytest tests/test_coverage_checkers.py tests/test_ci_makefile.py -q`
  and record it green, with every planted-tree test unedited. Run
  `wc -l tests/test_coverage_checkers.py` against `MAX_TEST_MODULE_LINES`.
- **Gate:** `make test`

## Milestone 4 — The threshold guard sees what it claims, seen red first

- `tests/test_threshold_guard.py`, written before the code and run red. Each
  test is `integration` by the module's `pytestmark`, which the criterion
  computes, since each loads the script. Planned tests:
  - `test_threshold_guard_selects_every_widened_target_by_glob`:
    `targets(root)` on a planted root holding one file of each pattern of
    R-GSG-1, a `Dockerfile.dev` among them. It also plants decoys that must
    not be selected: a `.github/dependabot.yml`, a `templates/AGENTS.md` and
    a nested `skills/s/assets/sub/x.yml` (AC-GSG-1).
  - `test_threshold_guard_fails_on_each_widened_shape`, parametrised over
    DEC-GSG-013's loud set: every row of "Measured at `bfbc124`" but the
    control, plus:
    - a `max`, a `ratio` and a `threshold` flag;
    - `--minimum 90`, `COVERAGE_FLOORS: 90` and `--thresholds=3`;
    - `args: [--cov-fail-under, "90"]` in a pre-commit file and
      `RUN ["pytest", "--cov-fail-under", "90"]` in a `Dockerfile`;
    - a `!=` pin, an extras-bracketed pin and a pin in a workflow comment;
    - `pip install ruff==0.4.2` in a workflow;
    - `"fail_under": 90`, a quoted key;
    - `uvx ruff@0.4.2 check .`, `pip install ruff@git+https://x` and
      `pip install 'ruff @ git+https://x'`, each `ruff@`.

    Each asserts exit 1. The FAIL line begins with the planted file's
    relative POSIX path and carries the subject, and the `ruff==` case has
    exactly one FAIL line (AC-GSG-1, AC-GSG-2, AC-GSG-4, AC-GSG-6).
  - `test_threshold_guard_flags_a_max_flag_of_another_tool_until_whitelisted`:
    `--max-count=1` and `--hypothesis-max-examples=200` in a planted
    composite action each exit 1, and each exits 0 once the planted tree's
    `tools/threshold_whitelist.txt` carries its entry and reason
    (DEC-GSG-005, AC-GSG-2).
  - `test_threshold_guard_stays_quiet_on_the_shapes_it_must_not_flag`: one
    planted tree holding every quiet string of "Measured at `bfbc124`" and of
    DEC-GSG-013 across a workflow, a composite action, a `Dockerfile` and a
    `Makefile`: `max-parallel: 4`, the legitimate keys of DEC-GSG-013 written
    as quoted keys, `uses: someorg/build@v1`, the comment-prose lines and
    `pytest --maxfail=1` among them. Exit 0 (AC-GSG-3).
  - `test_the_pin_rule_takes_its_names_from_the_dev_extra`. The real
    `pyproject.toml`'s dev names, read through `tests.support.read_pyproject`,
    each produce a finding when pinned in a planted workflow, `coverage`
    among them. A name planted only in the fixture's dev extra (`plantedtool`)
    is caught when pinned, which shows the names are read at run time
    (AC-GSG-4).
  - `test_a_threshold_constant_in_tools_fails_the_guard`: plain, annotated,
    tuple-unpacked and negated bindings each fail. `SCHEMA_VERSION = 1`, a
    `bool`, and a binding inside a function do not (AC-GSG-6).
  - `test_a_threshold_whitelist_entry_suppresses_exactly_its_finding`:
    - one entry, the same literal planted in two files, one finding left;
    - an entry written with the `#` directly after one space, which the
      `\s+#\s*` separator accepts;
    - a planted tree with no whitelist of its own is judged with none, not
      with this repository's (AC-GSG-7).
  - `test_a_stale_threshold_whitelist_entry_fails_the_guard`: exit 1, naming
    the entry. An absent whitelist behaves as an empty one (AC-GSG-7).
  - `test_threshold_guard_exits_two_when_it_cannot_read_an_input`,
    parametrised: no `pyproject.toml`; a dev extra with no entry; a
    whitelist line with no reason; a target whose read raises an injected
    `PermissionError`; a target holding `b"\xff"`; a `tools/` module with a
    syntax error. Each asserts exit 2, the file named, and no `Traceback`
    (AC-GSG-5).
  - `test_the_real_tree_passes_only_with_its_threshold_whitelist`: `main` on
    `REPO_ROOT` exits 0. The same with the whitelist path redirected to an
    absent file exits 1, naming `Makefile` and `NO_FLOOR=0`. No entry of the
    real whitelist names a path under `.github/workflows/` (AC-GSG-8).
  - `test_gate_scripts_print_a_non_ascii_path_on_an_ascii_console`, in
    `tests/test_gate_scripts.py`, gains the guard's case: a planted root
    whose `templates/spé.yml` holds `--cov-fail-under=90`, run as a process
    under `PYTHONIOENCODING=ascii`. Exit 1, the UTF-8 bytes of
    `templates/spé.yml` on stdout, no `Traceback` (AC-GSG-23).

  Record the red run as it happens. The drafting expectation:
  - every loud case but the control exits 0;
  - the selection test misses each added pattern;
  - the whitelist, constants and exit-2 tests fail on names that do not exist
    yet, or on an exit other than the one they assert;
  - the console case exits 0, because `templates/` is not scanned yet.
- `tests/test_threshold_guard.py`'s `_guard_tree` writes a minimal
  `pyproject.toml` whose dev extra lists `pytest`, `ruff` and `mypy`. That is
  its only change, and every test built on it keeps its name and assertions
  (R-GSG-20, AC-GSG-9). Run them before the code change and record them
  green, which shows the helper change alone moves nothing.
- `tests/test_skill_distribution.py`'s `test_threshold_guard_scans_every_workflow`:
  the per-target loop asserts the target's findings after the whitelist are
  `[]`, and a final assertion holds that no whitelist entry is stale. The
  name, the docstring and the selection assertions are unchanged (R-GSG-20,
  AC-GSG-8). `tests/test_release_surface.py` is not edited.
- `pyproject.toml`: `"coverage",` in the dev extra after `"pytest-cov",`,
  under a comment. The comment says the coverage-run recipe invokes
  `python -m coverage` directly, that `[tool.coverage.run]` relies on
  coverage's own subprocess hook, and that the threshold guard's pin rule
  takes its names from this list (R-GSG-10, DEC-GSG-006). Run
  `python -m pip install -e ".[dev]"` and record that it changes nothing
  installed.
- `tools/_common.py`:
  - `dev_extra_names(pyproject) -> list[str]`, on the table-tracking loop
    `coverage_sources` uses. It reads the leading distribution name of each
    quoted entry of `[project.optional-dependencies] dev` and skips comment
    lines inside the array. Stdlib only.
  - Its docstring carries R-GSG-14's wording. The scanner was chosen under
    the 3.10 floor, and replacing it with `tomllib` is item 7a's change. Its
    refusals on a value's type carry forward. The spellings `tomllib`
    normalises are item 7a's decision, which replaces those tests rather
    than keeping them.
  - `resolve_makefile`'s docstring: "which is why ``check_makefile``
    tolerates a path it cannot open" becomes a path that is not a regular
    file, nothing to scan, while an unreadable regular file is the guard's
    exit 2 (R-GSG-7, R-GSG-23).
- `tools/check_no_hardcoded_thresholds.py`:
  - `targets(root)` per R-GSG-1, `Dockerfile*` by pattern.
  - `check_makefile(path)` and `check_workflow(path)` keep their shapes.
    Each gains the named rule of R-GSG-3 and the pin rule of R-GSG-4:
    - the named rule skips whole-line comments and never reports
      `max-parallel`;
    - each reports a number and a pin once, R-GSG-2's rule winning, with
      that rule's message and the subject R-GSG-6 defines;
    - each raises a module-level `GuardError` on an unreadable or
      undecodable regular file;
    - with one argument they read the dev extra of `REPO_ROOT` at call time.
  - `check_tools_constants(root) -> list[str]` per R-GSG-5.
  - `read_threshold_whitelist(root) -> dict[tuple[str, str], str]` and the
    stale check per R-GSG-6. It reads `root / "tools/threshold_whitelist.txt"`
    with the `\s+#\s*` separator of `tools/dead_code.py`'s `_WHITELIST_LINE`,
    and matches on `path.relative_to(root).as_posix()` and the subject.
  - `main` calls the console helper first and applies the whitelist. It
    prints `FAIL:` lines that begin with the relative POSIX path and carry
    each subject, and it maps `GuardError` to exit 2 with `ERROR:` on stderr.
  - The docstring per R-GSG-8, including which rules read comment lines. The
    PASS line names the scanned kinds.

  Every new public function carries a docstring. Re-run
  `python -m pytest tests/test_static_ratchets.py -q` and lower the
  script's `D103` ceiling only if the count fell.
- `tools/threshold_whitelist.txt` (new) opens with a two-line header. The
  first line says what an entry is for: a literal the guard reports that is
  not a threshold this repository enforces, never a workflow line. The
  second says that renaming to dodge the guard is never the fix. Then the
  entry:

  ```
  Makefile NO_FLOOR=0  # turns pytest-cov's own floor off on the one coverage-run, whose total is the diluted figure for both trees; the scoped checkers under test and coverage-tools gate each tree against the floors in pyproject.toml
  ```

  Each further hit Milestone 0 decided gets its entry or its move here
  (DEC-GSG-009).
- Run `python tools/check_no_hardcoded_thresholds.py` and record its PASS
  line and exit 0. Re-run the scratch planted table, the planted lines and
  the rebuilt prototype at the head, and record each beside the drafting
  figures. The expectation is that the guard catches 16 of 16 planted
  shapes, as "Re-checked at `bfbc124`" measured with `coverage` declared.
- **Gate:** `make test`

## Milestone 5 — Documents and the record

- The `Makefile`'s thresholds help text names the widened scope with no
  number in it, and its recipe line is unchanged (R-GSG-23, C-GSG-2). The
  guard must stay quiet on it; run it.
- `README.md`: the gates row (369 at drafting) and the paragraph
  (381–385) name the scanned kinds, the pin rule's source, the `tools/`
  constants rule and the whitelist.
- `docs/hooks.md`: the commit-hook line (26) and the every-workflow note
  (148–150), which also names the added patterns.
- `docs/aqa.md`:
  - the externalisation paragraph (30–37), with the same facts;
  - the Gates table's security row (13), which gains the fallback's exit 2
    beside a committed secret's exit 1.
- `tools/AGENTS.md`: the "Never hard-code a threshold" bullet gains three
  things, by replacing text: an exemption is one line in
  `tools/threshold_whitelist.txt` with its reason; a workflow line is never
  exempted; and renaming a constant to dodge the guard is never the fix.
  Run `wc -l tools/AGENTS.md` against `MAX_NESTED_LINES` and `python -m
  pytest tests/test_agent_artifacts.py -q -k "nested_agents or
  agent_index_links"`, and record both. If `harden-release-pipeline` has
  spent the last line, replace more text rather than add.
- `.claude/agents/planlint-verifier.md:16`: "it allowlists comments" becomes
  which rules skip whole-line comments (the named rule everywhere, every
  rule in the makefile) and which read them (R-GSG-2's rules and the pin
  rule outside the makefile). The `$(...)`, `@echo` and remediation clauses
  stay. Run `python -m pytest tests/test_agent_skill_docs.py -q` and record
  it.
- `CHANGELOG.md` `[Unreleased]`: `### Fixed — the gate scripts fail closed`
  with one bullet led by ``- **`close-gate-script-gaps`.**``. It names:
  - the widened guard and its whitelist;
  - the anchored reader and its refusal;
  - the secret scan's `-z` enumeration and its refusals;
  - the coverage checkers' walk to the nearest configuration;
  - non-ASCII paths written as UTF-8 on an ASCII console;
  - `coverage` joining the dev extra.

  The released sections are untouched.
- Run `make docs-check` and `python -m pytest tests/ -q -o addopts="" -k
  changelog`, and record both.
- **Gate:** `make docs-check`

## Milestone 6 — Verification, the selectors and the hand-off

- Re-point the stage-only verification lines in
  `specs/fail-closed-gate-scripts/spec.md` to the tests Milestones 1 to 4
  named, keeping each stage. Then run `python -m pytest
  tests/test_spec_test_citations.py -q` and record it. The mapping:

  | AC | Adds |
  |---|---|
  | AC-GSG-1 | `test_threshold_guard_selects_every_widened_target_by_glob`, `test_threshold_guard_fails_on_each_widened_shape` |
  | AC-GSG-2 | `test_threshold_guard_fails_on_each_widened_shape`, `test_threshold_guard_flags_a_max_flag_of_another_tool_until_whitelisted` |
  | AC-GSG-3 | `test_threshold_guard_stays_quiet_on_the_shapes_it_must_not_flag` |
  | AC-GSG-4 | `test_the_pin_rule_takes_its_names_from_the_dev_extra` |
  | AC-GSG-5 | `test_threshold_guard_exits_two_when_it_cannot_read_an_input` |
  | AC-GSG-6 | `test_a_threshold_constant_in_tools_fails_the_guard` |
  | AC-GSG-7 | `test_a_threshold_whitelist_entry_suppresses_exactly_its_finding`, `test_a_stale_threshold_whitelist_entry_fails_the_guard` |
  | AC-GSG-8 | `test_the_real_tree_passes_only_with_its_threshold_whitelist` |
  | AC-GSG-10 | `test_read_pyproject_int_reads_only_an_exact_integer` |
  | AC-GSG-11 | `test_a_floor_the_reader_cannot_read_exactly_exits_two` |
  | AC-GSG-12 | `test_the_gate_reader_never_disagrees_with_the_product_on_a_floor` |
  | AC-GSG-13 | `test_fallback_scan_reads_a_non_ascii_tracked_name`, `test_tracked_files_asks_git_for_nul_separated_names` |
  | AC-GSG-14 | `test_fallback_scan_refuses_a_tree_git_cannot_list`, `test_fallback_scan_refuses_undecodable_output_or_nothing_to_scan`, `test_fallback_scan_refuses_an_unreadable_tracked_file` |
  | AC-GSG-16 | `test_the_coverage_checkers_read_the_nearest_pyproject_at_or_above_the_report`, `test_a_report_with_no_pyproject_at_or_above_it_exits_two`, `test_a_missing_report_is_named_before_the_configuration` |
  | AC-GSG-23 | `test_gate_scripts_print_a_non_ascii_path_on_an_ascii_console` |
- Confirm C-GSG-1, C-GSG-2 and C-GSG-5 by diff against the implementation
  branch's base, and record each command and its output:
  - nothing under `openspec_graph/` or `.github/` changed;
  - the `Makefile` diff is the help text alone;
  - nothing under `openspec/changes/` changed but this package.

  `python -m pytest tests/test_decomposition.py -k byte_identical -q` is
  green.
- Record the CI run of the implementation pull request, the `test-windows`
  leg included, for `test_fallback_scan_reads_a_non_ascii_tracked_name` and
  `test_gate_scripts_print_a_non_ascii_path_on_an_ascii_console`.
- Close the milestones and tick the criteria, leaving the spec's `Status`
  header `DRAFT`. The pull request asks the maintainer to settle it at merge,
  as `report-dead-code-and-spec-status` DEC-RDS-008 describes. Run `python
  tools/spec_status.py` and record this package's row.
- Confirm this package validates clean (`planlint --target . validate
  --fail-on INFO --change close-gate-script-gaps`), then the tree, and record
  each exit code.
- **Gate:** `make pre-pr`

## Drafting record

Measured at `bfbc124` with this package's three files written, 2026-10-16:

- `planlint --target . validate --fail-on INFO --change
  close-gate-script-gaps`: the two notes `INFO G006 skipped` and `INFO G009
  skipped` that a scoped run prints, then `1 spec(s) checked · 0 error · 0
  warn · 0 info`, `PASS`, exit 0.
- `planlint --target . validate --fail-on ERROR`: `58 spec(s) checked · 0
  error · 0 warn · 0 info`, `PASS`, exit 0.
- `python -m pytest tests/test_spec_test_citations.py
  tests/test_spec_status.py tests/test_stage_citations.py -q -p
  no:cacheprovider`: exit 0.
- `python tools/stage_citations.py`: `58 spec(s); 17 stage(s) cited; 12 on a
  verification line; 6 of those invoked by no scanned workflow: ci,
  coverage-tools, security, thresholds, validate, wheel-check`, exit 0. The
  figures include this package's spec. Against the drafting run, `test` reads
  55 mentioned and 55 verified (from 54 and 54), `docs-check` 22 and 21 (from
  21 and 20) and `pre-pr` 53 and 18 (from 52 and 17). `thresholds` and
  `security` are unchanged at 9 and 6 and at 2 and 1, so this package adds no
  citation of either.
- `python tools/spec_status.py`: this package's row reads `spec DRAFT`,
  `0/22`, `milestones 0/7`, no unrun stage and no finding. The report exits 1
  on the tree's existing findings, none of them this package's.

Re-measured at `bfbc124` with the first review's revision written,
2026-10-17:

- `planlint --target . validate --fail-on INFO --change
  close-gate-script-gaps`: the same two `INFO` notes, then `1 spec(s)
  checked · 0 error · 0 warn · 0 info`, `PASS`, exit 0.
- `planlint --target . validate --fail-on ERROR`: `58 spec(s) checked · 0
  error · 0 warn · 0 info`, `PASS`, exit 0.
- `python -m pytest tests/test_spec_test_citations.py
  tests/test_spec_status.py tests/test_stage_citations.py -q -p
  no:cacheprovider`: exit 0.
- `python tools/stage_citations.py`: the same summary line, exit 0. `test`
  55 and 55, `docs-check` 22 and 21, `pre-pr` 53 and 18, `thresholds` 9 and
  6 and `security` 2 and 1, so the revision adds no stage citation.
- `python tools/spec_status.py`: this package's row reads `spec DRAFT`,
  `0/23`, `milestones 0/7`, no unrun stage and no finding. The report exits 1
  on the tree's existing findings, none of them this package's.

Re-run at `bfbc124` after the five open lines were decided, 2026-10-17: the
same five commands give the same figures and exit codes, and this package's
`spec_status` row still reads `spec DRAFT`, `0/23`, `milestones 0/7`.

Re-run at `bfbc124` after the three further shapes were decided,
2026-10-17: the same five commands give the same figures and exit codes, and
this package's `spec_status` row still reads `spec DRAFT`, `0/23`,
`milestones 0/7`.
