# Tasks: tighten-release-surface

Drafted at `bfbc124` (`origin/dev`) on `claude/tighten-release-surface`,
2026-10-16, from a review of `dev` the same day. Every finding of that
review was re-measured below before any file of this package was written.
Revised at the same commit on 2026-10-17 to resolve the first and second
adversarial reviews (Milestone 0). Every line number is at `bfbc124`, and
is re-read at the implementation branch's head before the milestone that
uses it. A sibling landing first moves a line without moving the fact.
Every number names the command that produced it.

This change arrives in three parts:

- **The package pull request** carries this package into `dev`, with
  R-TRS-19's amendment of `prepare-release-0-4-0`'s
  `specs/release-0-4-0/spec.md`, `proposal.md` and `tasks.md`, and no
  other file. It is held until the 0.3.0 promotion is done (DEC-TRS-012,
  DEC-TRS-015).
- **The implementation pull request** (Milestones 1 to 6) is a new pull
  request from `dev`. It opens as a GitHub draft, and is marked ready only
  after Milestone 0's facts are recorded here.
- **It merges into `dev` before `prepare-release-0-4-0`'s release-prep pull
  request.** That package's Milestone 5 opens that pull request, and with
  the amendment it checks for this change's merge first, so this change's
  `[Unreleased]` entry is cut into `[0.4.0]`.

This file names make targets in prose and gives the commands they run.
Only `make test`, `make docs-check` and `make pre-pr` are written as make
calls, so the stage-citations report counts nothing here.

Scratch directories, none of them in the worktree:

- `$M` is `/tmp/claude-0/-home-user-planlint/76cf7dc8-c47d-5e23-9e51-980965e94a58/scratchpad/measure-trs/`,
  the first draft's;
- `$R` is `/tmp/claude-0/-home-user-planlint/76cf7dc8-c47d-5e23-9e51-980965e94a58/scratchpad/review-trs/`,
  the first review's;
- `$R2` is `/tmp/claude-0/-home-user-planlint/76cf7dc8-c47d-5e23-9e51-980965e94a58/scratchpad/review-trs-2/`,
  the second review's;
- `$S` is `/tmp/claude-0/-home-user-planlint/76cf7dc8-c47d-5e23-9e51-980965e94a58/scratchpad/resolve-trs/`,
  this revision's.

## Measured at `bfbc124`

Measured on 2026-10-16 unless a bullet says 2026-10-17.

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR` printed `57 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`,
  exit 0, before any file of this package existed. The console script is
  `/usr/local/bin/planlint`, an editable install of `/home/user/planlint`.
  `diff -rq --exclude=__pycache__ /home/user/planlint/openspec_graph
  ./openspec_graph` exits 0, and `python -m openspec_graph.cli --target .
  validate --fail-on ERROR` from the worktree printed the same, exit 0.
- **The gate before each revision (2026-10-17).** The same command printed
  `58 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`, exit 0, before
  the first revision and again before the second. The same `diff -rq`
  exits 0.
- **The stage-citations report.** `python tools/stage_citations.py`, which is
  what the stage-citations target runs, exit 0. Each row reads stage,
  mentioned, verified, run directly by:
  - `ci` 15 7 -;
  - `coverage-tools` 3 2 -;
  - `docs-check` 21 20 ci.yml;
  - `e2e-live` 2 1 ci.yml;
  - `lint` 10 5 ci.yml;
  - `matcher-accuracy` 4 0 -;
  - `pre-pr` 52 17 ci.yml, release.yml;
  - `security` 2 1 -;
  - `skill-catalog` 1 0 -;
  - `skill-manifests` 3 0 -;
  - `spec-status` 1 0 -;
  - `stage-citations` 8 0 -;
  - `test` 54 54 ci.yml;
  - `thresholds` 9 6 -;
  - `typecheck` 10 5 ci.yml;
  - `validate` 24 13 -;
  - `wheel-check` 4 2 -.

  The summary line reads `57 spec(s); 17 stage(s) cited; 12 on a
  verification line; 6 of those invoked by no scanned workflow: ci,
  coverage-tools, security, thresholds, validate, wheel-check`.
- **Who cites the six on a verification line.** A read-only script over
  `detect.find_spec_files`, with `parse_spec` and `MAKE_REF.findall` over
  each criterion's `verified_by`:
  - `ci`: `add-github-action-contract`, `add-graph-export`,
    `add-witness-ci-artifacts`, `harden-ci-gates`,
    `migrate-license-metadata-pep639`, `select-zero-cost-guards`,
    `widen-indeterminate-unchecked-citations`;
  - `coverage-tools`: `gate-tools-coverage`, `select-zero-cost-guards`;
  - `security`: `enterprise-hardening`;
  - `thresholds`: `gate-tools-coverage`, `harden-ci-workflows`,
    `measure-coverage-once`, `pin-actions-by-sha`,
    `ratchet-test-types-and-docstrings`, `report-dead-code-and-spec-status`;
  - `validate`: thirteen packages, every one outside `lean-production-tree`'s
    kept set;
  - `wheel-check`: `migrate-license-metadata-pep639`, `prepare-release-0-3-0`.

  The same script, restricted to the packages `lean-production-tree` keeps
  plus the three open siblings, prints `['ci', 'docs-check', 'e2e-live',
  'pre-pr', 'test', 'wheel-check']`. After that package lands and this one
  wires its stages, `ci` is the one verification-line stage no workflow runs
  by name (DEC-TRS-005).
- **The verbs.**
  - `planlint --help` lists `{detect,init,new,validate,rules,graph,waivers,delta,report,witness}`.
  - `README.md:41-52`, the quickstart block, shows `detect` (three lines),
    `init`, `new`, `validate`, `waivers`, `graph` and `--version`.
  - `awk 'NR<41 && /^```/' README.md | wc -l` prints 0, so the quickstart is
    the README's first fenced block.
  - `grep -n -i -w "delta\|witness\|sarif\|waivers" README.md` finds the
    `waivers` lines and rule-table and prose mentions of the others, with no
    CLI line for `rules`, `delta`, `report`, `witness` or `--format sarif`.
  - (2026-10-17) `planlint witness --help` prints `--exit EXIT_CODE  the exit
    code the verifying command actually observed`. `planlint report --help`
    takes `--findings` and `--format {sarif,github-annotations,github-summary,github-outputs}`,
    and `planlint rules --help` takes `--json`.
- **`delta`.** Each run was made with the installed CLI. Scratch files went
  only under `$M`.
  - `planlint --target $M/empty delta --baseline $M/absent.json`, on an
    empty directory, printed `no openspec/ directory and no SpecKit specs/
    tree; run ``planlint init`` first`, exit 2.
  - The same against `tests/fixtures/action/no-tree` printed the same,
    exit 2.
  - `planlint --target . delta --baseline $M/absent.json --fail-on ERROR`
    printed the usage line and `planlint: error: unrecognized arguments:
    --fail-on ERROR`, exit 2.
  - (2026-10-17) `planlint --target . delta --fail-on ERROR`, with no
    `--baseline`, printed `planlint delta: error: the following arguments
    are required: --baseline`, exit 2. With `--baseline
    $R2/card-self.json` added it printed `planlint: error: unrecognized
    arguments: --fail-on ERROR`, exit 2.
  - `planlint --target . delta --baseline $M/absent.json` printed `cannot
    read --baseline …: [Errno 2] No such file or directory: …`, exit 2.
  - `planlint --target . detect --format json > $M/card-self.json`, then
    `delta --baseline $M/card-self.json`, printed `machinery unchanged since
    the baseline` and `no spec cites machinery that changed — nothing
    stale`, exit 0.
  - The stale case: a scratch repository at `$M/repo` from
    `tests/fixtures/Makefile`, `tests/fixtures/pyproject.toml` and
    `tests/fixtures/good_harness.md` as `openspec/changes/c1/specs/cap/spec.md`.
    Its card was saved, then its `regression:` was renamed with `sed`.
    `delta --baseline <card>` printed `1 stale citation(s):` and the
    `make_target` line, exit 1. With `--format json` it printed one `stale`
    entry with `"was": "present", "now": "removed"`, exit 1.
  - `openspec_graph/cli.py`:
    - `cmd_delta` is at `:606`;
    - the tree check is at `:613-615`, before `_load_card` at `:617`;
    - an unreadable spec returns `_report_unreadable(exc, prof.root)` at
      `:625`, the call `validate`, `graph` and `waivers` make at `:457`,
      `:597` and `:684`;
    - `return 1 if entries else 0` is at `:651`, and the text path's
      `return 1` at `:671`;
    - `p_delta` (`:916-927`) has no `--fail-on`.
- **`delta`, three more cases (2026-10-17).** The first review planted three
  repositories under `$R/delta/`, each holding a Makefile, a
  `pyproject.toml` and a spec, with a card saved beside it as
  `$R/delta/<case>.card`. `planlint --target $R/delta/<case> delta
  --baseline $R/delta/<case>.card` printed:
  - `moved`: `threshold changed: {'locator':
    'pyproject.toml:[tool.coverage.report].fail_under', 'value': 90} -> {…
    'value': 95}`, then `1 stale citation(s):` and `threshold
    openspec/changes/c1/specs/cap/spec.md: still cites the old coverage
    floor 90; the detected floor is now 95`, exit 1;
  - `removed`: `threshold changed: {… 'value': 90} -> None`, then `no spec
    cites machinery that changed — nothing stale`, exit 0;
  - `unread`: `ERROR cannot read spec openspec/changes/c2/specs/cap/spec.md:
    Is a directory`, exit 2.

  `openspec_graph/delta.py:204` reads `if baseline_floor is not None and
  live_floor is not None and baseline_floor != live_floor:`, so a floor
  removed outright is never a stale citation. That is recorded as the verb's
  current behaviour, not changed (R-TRS-10, C-TRS-1).
  `tests/test_spec_read_errors.py:33-40`, `PARSING_VERBS`, lists
  `validate`, `waivers` and `graph`, and not `delta`.
- **The contract files.**
  - `skills/planlint-spec-governance/references/exit-codes.md`:
    - `:9` defines exit 1 as findings at or above `--fail-on`;
    - `:12` is "Exit 1 means findings, and only findings.";
    - `:18` is "**`validate` and `waivers`, no spec tree.** Both print
      exactly:";
    - `:46` is "**`validate`, `waivers`, or `graph`, unreadable spec.**";
    - `:67-78` is the unusable-baseline entry;
    - `:119-123`, "## The one exit-1 case that is not a finding", names
      `detect --diff` alone.
  - (2026-10-17) `grep -rn -i "exit-1 case\|exit-1-case\|only findings"`
    over the tree's `*.md`, `*.py`, `*.txt`, `*.json` and `*.yml`, outside
    this package, finds those two lines, a docstring in
    `tests/test_skill_contract.py:385`, and change-package prose. No test
    and no link pins the heading. `add-delta-lint`'s
    `specs/delta-lint/spec.md:211-218`, DEC-DL-008, reads "That section
    becomes two cases and must be updated in the same change". That
    package's spec is `DRAFT` with every criterion unchecked, while `delta`
    is in the CLI.
  - `SKILL.md`:
    - `:79` is the exit-1 row;
    - `:85-90` is the no-spec-tree bullet, naming `validate`, `waivers` and
      `graph`, with "In all three cases";
    - `:5-8` is the frontmatter's version fields, all `0.3.0`.
  - `tools/render_plugin_manifests.py` reads `__version__` and the
    frontmatter `description` only, so a body edit cannot stale the
    manifests.
- **The build, from a scratch copy.**
  - `tar --exclude=./.git -cf - . | tar -xf - -C $M/src`, then
    `python -m build --outdir $M/dist $M/src`, exit 0. The build was
    `build 1.6.1`, with `setuptools>=77` resolved to `setuptools==84.0.0`
    in isolation. The log reads `* Building sdist...` and then `* Building
    wheel from sdist`.
  - **What the build leaves behind (corrected 2026-10-17, LOW-7 of the first
    review).** The build ran from the copy `$M/src`, never from the
    worktree, so the first draft's "the worktree gained nothing" was true and
    beside the point. `ls -d $M/src/build $M/src/planlint.egg-info
    $M/src/dist` finds only `planlint.egg-info/`. A wheel-only build leaves
    `build/` as well: `$S/body`, built with the wheel-only flag below, gained
    both `build/` and `planlint.egg-info/`. So does the checkout that the
    existing `test_the_real_wheel_passes_the_gate` builds from, and
    `/home/user/planlint` carries both. Both are gitignored
    (`git check-ignore -v` names `.gitignore:10` and `:12`). The recipe of
    R-TRS-4, run in a checkout, leaves the gitignored `dist/` and
    `planlint.egg-info/`.
  - `tar -tzf $M/dist/planlint-0.3.0.tar.gz` lists `planlint-0.3.0/PKG-INFO`,
    `planlint-0.3.0/LICENSE`, `planlint-0.3.0/README.md` and
    `planlint-0.3.0/planlint.egg-info/PKG-INFO`, among others. The tests
    directory is in the sdist too.
  - The root `PKG-INFO` has `Metadata-Version: 2.4`, `License-Expression:
    Apache-2.0` and `License-File: LICENSE`.
  - `python tools/check_wheel_metadata.py $M/dist` printed `PASS 1 wheel(s)
    carry License-Expression: Apache-2.0 and 1 licence file(s)`, exit 0.
  - **The bare-sdist directory, and why it is not the gap.** `$M/dist-planted`
    holds the same wheel beside the sdist repacked with its `LICENSE`
    deleted and its `License-Expression:` line removed. The repacked sdist
    lists 0 members named `LICENSE` and 0 `License-Expression` lines. The
    checker printed the same `PASS 1 wheel(s) …` line, exit 0. That
    directory pairs a wheel built from a good sdist with a bad sdist, which
    only separate builds produce, and no workflow builds the two separately
    (DEC-TRS-001).
  - **A wheel built from the bare sdist (2026-10-17).** The first review
    extracted that repacked sdist to `$R/bare-x/planlint-0.3.0/` and built a
    wheel from it. `$R/bare-build.log` shows setuptools warning `Pattern
    'LICENSE' did not match any files.` and then `Successfully built
    planlint-0.3.0-py3-none-any.whl`. Read with `zipfile`, that wheel's
    header carries `License-Expression: Apache-2.0`, regenerated from the
    sdist's own `pyproject.toml`, and it has no `licenses/` member.
    `python tools/check_wheel_metadata.py $R/bare-whl`, re-run from the
    worktree, printed `FAIL planlint-0.3.0-py3-none-any.whl: 'LICENSE' is
    declared in license-files but no matching file was packaged under
    planlint-0.3.0.dist-info/licenses/`, exit 1.
  - **`MANIFEST.in` cannot drop the licence (2026-10-17, second review).**
    `$R2/bare-new` is a copy with `exclude LICENSE` in `MANIFEST.in` and
    R-TRS-4's recipe in its Makefile. `$R2/bare-new.log:17-18` reads
    `warning: no previously-included files found matching 'LICENSE'` and
    then `adding license file 'LICENSE'`. `tar -tzf
    $R2/bare-new/dist/planlint-0.3.0.tar.gz | grep LICENSE` prints
    `planlint-0.3.0/LICENSE`, and the log ends with every smoke probe's
    `PASS` line.
  - **The differential (2026-10-17, second review).** `$R2/mod-base` and
    `$R2/mod-new` are copies with `exclude openspec_graph/mermaid.py` in
    `MANIFEST.in`. `$R2/mod-base` keeps today's recipe, and `$R2/mod-new`
    carries R-TRS-4's. Each was copied without its `dist/`, `build/` and
    `*.egg-info` into `$S/r2-mod-base` and `$S/r2-mod-new`, and run with
    `make -C <dir> wheel-check`, with `setuptools==84.0.0` resolved in
    isolation:
    - `$S/r2-mod-base`: `* Building wheel...`, then `PASS 1 wheel(s) carry
      License-Expression: Apache-2.0 and 1 licence file(s)`, make exit 0;
    - `$S/r2-mod-new`: `* Building wheel from sdist`, the same `PASS` line,
      then five `FAIL …: the console script crashed (exit 1)` lines, one per
      probe, each over `ImportError: cannot import name 'mermaid' from
      'openspec_graph'`. Then `make: *** [Makefile:107: wheel-check] Error
      1`, make exit 2.

    The second review's own `$R2/mod-base.log` and `$R2/mod-new.log` show the
    same lines.
  - `/usr/local/lib/python3.13/dist-packages/build/__main__.py:537-538`:
    "By default, a source distribution (sdist) is built from the project
    root and a binary distribution (wheel) is built from the sdist."
  - `migrate-license-metadata-pep639`'s `specs/license-metadata/spec.md:171-176`,
    DEC-LM-008: "the gate reads wheels only, not sdists … Revisit if an
    sdist-only defect is ever observed." Its stated reasons are the shared
    code path, the doubled surface of a second reader and the wheel being
    the artifact the release smoke installs.
- **The smoke probes (2026-10-17, second review).**
  `tests/test_ci_promotion.py:44` is `SMOKE_PROBES = ("--expect
  tests/fixtures/action/passing=0", "--expect
  tests/fixtures/action/failing=1")`. `smoke_problems` (`:162-179`) reports
  a probe missing from `release-tier` or the release workflow, and nothing
  extra. `$R2/drift` is a copy whose `ci.yml` adds `--expect
  tests/fixtures/action/no-tree=2` to `release-tier`'s smoke step alone
  (`:500`), with R-TRS-4's recipe in its Makefile. From `$R2/drift`,
  `python -m pytest tests/test_ci_promotion.py -q -p no:cacheprovider -k
  test_release_and_ci_share_one_smoke_tool --no-cov` passes, exit 0.
- **The licence-expression check, two false passes (2026-10-17).**
  - Two copies of the worktree:
    `tar --exclude=./.git --exclude=__pycache__ -cf - . | tar -xf - -C $S/<d>`,
    for `<d>` in `body` and `longer`.
  - In `$S/body`, `sed -i '/^license = "Apache-2.0"$/d' pyproject.toml`
    removed the declaration, keeping `license-files = ["LICENSE"]`, and
    `printf '\nLicense-Expression: Apache-2.0\n' >> README.md` appended the
    line to the README. In `$S/longer`, the declaration became
    `license = "Apache-2.0 OR MIT"`.
  - `python -m build --wheel --outdir $S/dist-<d> $S/<d>`, exit 0 for each,
    with `setuptools==84.0.0` in isolation.
  - Each wheel's `METADATA`, read with `zipfile` and split at its first
    empty line:
    - `body`: the header has no `License-Expression` line, and the body has
      `License-Expression: Apache-2.0`;
    - `longer`: the header has `License-Expression: Apache-2.0 OR MIT`;
    - both carry `License-File: LICENSE` and
      `planlint-0.3.0.dist-info/licenses/LICENSE`.
  - `python tools/check_wheel_metadata.py $S/dist-<d>`, run from the
    worktree so that it reads the worktree's declared `Apache-2.0`, printed
    `PASS 1 wheel(s) carry License-Expression: Apache-2.0 and 1 licence
    file(s)`, exit 0, for each.
  - **In the wheel's own tree (2026-10-17, second review).** Run from each
    copy, so that it reads that copy's declaration:
    - `(cd $S/longer && python tools/check_wheel_metadata.py
      $S/dist-longer)` printed `PASS 1 wheel(s) carry License-Expression:
      Apache-2.0 OR MIT and 1 licence file(s)`, exit 0;
    - `(cd $S/body && python tools/check_wheel_metadata.py $S/dist-body)`
      printed `ERROR pyproject.toml declares no SPDX license expression`,
      exit 2.
  - **What setuptools writes (2026-10-17, second review).** The second
    review built `$R2/cases/<c>/tree` with each declaration below and
    checked each wheel with its own copy's checker and with the header-only
    prototype `$R2/proto/check_wheel_metadata.py`:
    - `good`, `long`, `multi`, `paren` and `with`, declaring `Apache-2.0`,
      a long `OR` chain with a `WITH` exception, `Apache-2.0 OR MIT`,
      `(Apache-2.0 OR MIT) AND BSD-3-Clause` and `Apache-2.0 WITH
      LLVM-exception`: each header carries the declared expression, and
      both checkers print `PASS`;
    - `lower`, declaring `apache-2.0 or mit`: with `setuptools==84.0.0`
      the header reads `License-Expression: Apache-2.0 OR MIT`, and both
      checkers print `FAIL … METADATA is missing 'License-Expression:
      apache-2.0 or mit'`;
    - `table`, declaring `license = {text = "Apache-2.0"}`: the isolated
      build under `setuptools>=77` stops at `configuration error:` with
      "`project.license` must be string", and leaves no wheel.
  - `tools/check_wheel_metadata.py:72-73` is `expected =
    f"{_EXPRESSION_KEY} {expression}"` and `if expected not in metadata:`.
    The classifier loop at `:78-83` reads every line.
  - `tests/test_wheel_metadata.py:37-44`, `GOOD_METADATA`, holds no empty
    line, so every existing in-memory fixture is all header, and
    `test_a_mismatched_expression_is_caught` replaces the value with `MIT`.
- **The stages' commands.**
  - `ci.yml:176` is `planlint --target . validate --fail-on ERROR`, and
    `Makefile:60` is the same.
  - `ci.yml:403` is `python tools/check_no_hardcoded_thresholds.py`, and
    `Makefile:89` is the same.
  - `ci.yml:214` and `:217` are `python -m build --wheel --outdir dist` and
    `python tools/check_wheel_metadata.py dist`, and `Makefile:104-105` are
    the same. `packaging` has no smoke step.
  - `Makefile:79` composes `ci` from `test lint validate`, and `:82` composes
    `pre-pr` from `ci typecheck security docs-check thresholds
    coverage-tools`.
  - `Makefile:29-32` run both scopes' floor checkers, and `:42-43` repeat
    the `tools` pair for `coverage-tools`.
  - `tools/check_secrets.py:87-97` runs `shutil.which("gitleaks")`, or falls
    back. `ci.yml:405-411` is `gitleaks/gitleaks-action`.
  - `ci.yml:492-502` (`release-tier`) and `release.yml:82-103` (`build`)
    build both artifacts, run the checker and smoke the wheel.
    `tests/test_ci_promotion.py:46-50` pins `release-tier`'s three steps as
    text.
  - (2026-10-17) `release.yml:101-103` is `python tools/smoke_wheel.py dist
    --venv /tmp/smoke` with the two `--expect` probes and no `--target`.
    `tools/smoke_wheel.py:189` defaults `--target` to `.`, and `:117` makes
    the third probe `validate --fail-on ERROR` on it, so both release paths
    validate this tree in their smoke (DEC-TRS-003).
- **The workflow reader and a flow-mapping step (2026-10-17).**
  `tools/_common.py:530`, `_RUN_KEY`, matches a `run:` key at the start of
  a line. From `tools/`, `python -I -c` calling `run_scripts` on a planted
  `security` job whose steps are `run: make thresholds` and
  `- {name: inline, run: python tools/check_no_hardcoded_thresholds.py}`
  printed `['make thresholds']`, exit 0. Over today's job blocks, from
  `tests.support.workflow_job_blocks` and `tests.workflow_support._code_lines`,
  each stem in `_WIRED` sits on exactly one code line of its job:
  `self-validate` line 22, `security` line 27, and `packaging` lines 21 and
  24, numbered within each block. So the code-line scan is empty once each
  is replaced (R-TRS-8, DEC-TRS-006).
- **Make's exit code.** A scratch Makefile at `$M/mk` whose recipe is
  `sh -c "exit 1"`. Running GNU Make 4.3 on it with `-C $M/mk fail1`
  printed `make: *** [Makefile:2: fail1] Error 1`, exit 2.
- **The thresholds guard's Makefile token.**
  `tools/check_no_hardcoded_thresholds.py:50` is `_THRESHOLD_TOKEN =
  (?<![\w.-])(\d{2,})(?![\w.])`. It flags literals of two or more digits, so
  the single-digit probe codes in `passing=0` and `failing=1` pass it.
- **The triggers and the hooks (2026-10-17).**
  - `ci.yml:9-11` is `push:` with `branches: [main, qa, dev]`, then
    `pull_request:` with no filter.
    `tests/test_ci_promotion.py:199`,
    `test_ci_push_branches_match_the_promotion_config`, holds that list to
    `[tool.specgraph.promotion]` (`pyproject.toml:256-259`).
  - `.pre-commit-config.yaml:16` and `:23` carry `types: [python]` on the
    lint and typecheck hooks. The security, validate, docs-check and
    thresholds hooks carry no type filter.
- **The tier claims.**
  - `docs/hooks.md:3-4`: "Pre-commit and CI hooks enforce the same gate as
    `make pre-pr`, so a commit can never bypass what CI checks."
  - `docs/hooks.md:16-18`: "the same targets CI uses — so a commit can never
    bypass CI".
  - `docs/aqa.md:283`: the comment "the exact bar CI enforces" on the
    `make pre-pr` line.
  - `docs/aqa.md:287`: "CI runs the same gates across Python 3.10–3.14".
  - `README.md:358-359`: "the same bar CI enforces".
  - `.pre-commit-config.yaml:4-5`: "Local hooks call the same … targets CI
    uses, so a commit never bypasses CI".
- **The overclaim grep.** The command, with two patterns added on
  2026-10-17 for the first draft's own wordings:

  ```
  grep -rn -i -e "same gate" -e "bypass" -e "exact bar" -e "the same bar" -e "same targets CI" -e "same .make. targets" -e "every push and pull request" -e "by name only" docs/ README.md AGENTS.md .pre-commit-config.yaml skills/ llms.txt
  ```

  It prints the claims above (`docs/hooks.md:3` and `:4` are one claim). It
  also prints these, all set aside:
  - `docs/peer-review-2026-10.md:169,367` and
    `docs/reflection-plan-2026-10.md:49`, dated documents that
    `lean-production-tree` deletes;
  - `docs/hooks.md:389`, a ruleset bypass;
  - `README.md:339,349`, about other bars.

  The two added patterns print nothing more at `bfbc124`.
- **The `docs/aqa.md` conflict (2026-10-17).** `$R/mergetest/` is a scratch
  repository whose `git -C $R/mergetest log --oneline --all` prints commits
  `base`, `rfr` and `trs`. `git -C $R/mergetest status --short` prints
  `UU aqa.md`. The file holds conflict markers over the range paragraph:
  this change's rewrite, carrying "Python 3.10–3.14", against
  `prepare-release-0-4-0`'s "CI runs the same gates across Python
  3.11–3.14". `$R/mergetest2/`, the same experiment for
  `harden-release-pipeline`'s `docs/hooks.md` edit, merged cleanly.
- **The siblings' texts (2026-10-17).**
  - `add-witness-ci-artifacts`' `specs/witness-ci-artifacts/spec.md`: R-WCA-26
    at `:223-226` adds the security target to `security`; R-WCA-28 at
    `:238-245` and DEC-WCA-016 at `:478-494` run the `ci` and `pre-pr`
    aggregates in a new `ladder` job; R-WCA-22 at `:186-194` is the
    capture idiom.
  - `prepare-release-0-4-0`: its `tasks.md:404` changes `docs/aqa.md:287` to
    "Python 3.11–3.14". In its spec, `grep -c "^- \[x\]"` prints 0 and
    `grep -c "^- \[ \]"` prints 25, under `Status: DRAFT`. Its proposal's
    bold "Pull request 2" sentence is at `:430-432`, and its `tasks.md`
    ordering summary's "Pull request 2" bullet at `:24-26`.
  - The amendment precedents: `measure-coverage-once`'s R-MCO-10 and
    DEC-MCO-007, and `lean-production-tree`'s R-LPT-16 and DEC-LPT-007, whose
    marker form "(amended by `<package>`)" stands in
    `add-witness-ci-artifacts`' spec and `tasks.md`.
- **The other open siblings (2026-10-17, second review).** Each was read in
  its own worktree at `bfbc124`, under
  `/tmp/claude-0/-home-user-planlint/76cf7dc8-c47d-5e23-9e51-980965e94a58/scratchpad/`:
  - `close-gate-script-gaps`, in `wt-close-gate-script-gaps/` (commit
    `e1ced8c`). Its proposal's `:298-313` names the sites it shares with
    this change. Its R-GSG-23 lists the documents it edits, and its C-GSG-2
    keeps it out of `.github/` and confines its Makefile edit to the
    thresholds target's help text. Its DEC-GSG-001 (`spec.md:415-443`)
    requires no order against this change, and requires itself to merge
    before `prepare-release-0-4-0`'s release prep. Its `tasks.md:429-441`
    measured the first draft's recipe, `--sdist` included. Its prototype
    guard is `resolve-gsg/proto_rev.py`. Its `judge`, loaded with
    `importlib` and its pins read from the worktree's dev extra, returned
    `[]` for each line here:
    - with `makefile=True`: `rm -rf dist`, `python -m build --outdir dist`,
      `python tools/check_wheel_metadata.py dist`, the smoke line with both
      `--expect` probes, and the help line of R-TRS-4;
    - with `makefile=False`: `run: make thresholds`, `run: make
      wheel-check` and `run: make validate`.
  - `raise-coding-standards`, in `wt-raise-coding-standards/`. It was under
    revision while this was read: `ls -la --time-style=full-iso` put its
    files' last writes between 16:24 and 16:28 UTC that day, so it is cited
    here by ID, not by line. Its R-RCS-14 adds an empty
    `openspec_graph/py.typed`, and checks it in the source tree and in both
    archives, built through the sdist. Its R-RCS-1 and DEC-RCS-017 make its
    release conditional. It ships in 0.4.0 if its implementation merges
    before `prepare-release-0-4-0`'s release-prep pull request opens, and in
    the next minor otherwise, with the maintainer recording which. Its
    hazard entry for this change records the earlier pin hazard as moot. A
    copy at `$S/typed`, with `: > openspec_graph/py.typed`, built with
    `python -m build --outdir $S/dist-typed $S/typed`, exit 0. The log reads
    `* Building sdist...` and `* Building wheel from sdist`. `tar -tzf` on
    the sdist lists `planlint-0.3.0/openspec_graph/py.typed`, and the
    wheel's file list holds `openspec_graph/py.typed`.
- **Sizes and bounds.** `MAX_TEST_MODULE_LINES = 700`
  (`tests/test_suite_shape.py:44`). `wc -l`:
  - `tests/test_ci_makefile.py`: 525;
  - `tests/test_ci_promotion.py`: 370;
  - `tests/test_skill_contract.py`: 486;
  - `tests/test_stage_citations.py`: 335;
  - `tests/test_wheel_metadata.py`: 280;
  - `tools/check_wheel_metadata.py`: 159;
  - `tools/AGENTS.md`: 59, against `MAX_NESTED_LINES = 60`.

  `tests/test_static_ratchets.py:130` holds `tools/check_wheel_metadata.py`
  at `{"D103": 1}`.
- **The release state.** `curl -sS -o /dev/null -w '%{http_code}\n'
  https://pypi.org/pypi/planlint/json` and the same for
  `/pypi/planlint/0.3.0/json` both printed `404`. This drafting environment
  runs no `git` that writes, so the tag and promotion facts are Milestone
  0's to record.
- **The area code.** `grep -rn -e "-TRS-" -e "TRS"` over the tree's
  `*.md`, `*.py`, `*.yml`, `*.toml`, `*.txt` and `*.json` printed nothing. A
  `grep -rhoE "\b(R|C|AC|DEC)-[A-Z]{2,}-"` over every spec gives the
  declared codes, and `TRS` is not among them.
- **With this package in place, after the second revision (2026-10-17).**
  These were run in the worktree with this package and the amendment
  present:
  - `planlint --target . validate --fail-on INFO --change
    tighten-release-surface`: `1 spec(s) checked · 0 error · 0 warn · 0
    info`, exit 0;
  - `planlint --target . validate --fail-on INFO --change
    prepare-release-0-4-0`: the same, exit 0;
  - `planlint --target . validate --fail-on ERROR`: `58 spec(s) checked · 0
    error · 0 warn · 0 info`, exit 0;
  - `python -m pytest tests/test_spec_test_citations.py
    tests/test_spec_status.py tests/test_stage_citations.py -q -p
    no:cacheprovider`: exit 0;
  - `git diff --numstat -- openspec/changes/prepare-release-0-4-0/`: `3 0`
    for its proposal, `7 0` for its spec and `16 0` for its `tasks.md`,
    insertions only;
  - `python tools/diff_spec_graph.py` on the graph of `git archive HEAD`,
    unpacked at `$S/base`, against the worktree's printed `PASS:
    broken_links 0 -> 0, no new orphan requirements`, exit 0;
  - `python tools/stage_citations.py` printed the same unrun set, over 58
    specs;
  - `python tools/spec_status.py` printed this package's row as `spec DRAFT
    0/20 milestones 0/7` and `prepare-release-0-4-0`'s as `spec DRAFT 0/25
    milestones 0/7`, with no finding for either, and the same 12 findings
    as before. It exits 1 whenever it reports a finding, as it does at the
    base.

## Milestone 0 — Hold, review, and the facts recorded before the implementation leaves draft

- The package pull request into `dev` carries
  `openspec/changes/tighten-release-surface/` and R-TRS-19's amendment of
  `openspec/changes/prepare-release-0-4-0/specs/release-0-4-0/spec.md`,
  `openspec/changes/prepare-release-0-4-0/proposal.md` and
  `openspec/changes/prepare-release-0-4-0/tasks.md`, and nothing else. It is
  held until the 0.3.0 promotion is done. Record, with the date:
  - `git ls-remote --tags origin v0.3.0` prints the tag and its peeled line;
  - `curl -s -o /dev/null -w '%{http_code}\n'
    https://pypi.org/pypi/planlint/0.3.0/json` prints `200`;
  - `git fetch origin && git merge-base --is-ancestor 'v0.3.0^{commit}'
    origin/main` exits 0, and so does the same against `origin/dev` (the
    back-merge).
- The package is reviewed by `spec-adversary` before any code, and its
  findings are resolved here, each with what changed.
  **Recorded — first review, 2026-10-17, at `bfbc124`:**
  - **HIGH-1.** The sdist reader went against DEC-LM-008, whose revisit
    trigger had not fired: a wheel built from an sdist missing `LICENSE`
    fails the existing checker (`$R/bare-build.log`, re-run above).
    Narrowed:
    - the checker stays wheel-only. R-TRS-1 to R-TRS-3, AC-TRS-1, AC-TRS-2,
      AC-TRS-4, AC-TRS-5 and DEC-TRS-002 are withdrawn, and their numbers
      are not reused;
    - DEC-TRS-001 now cites DEC-LM-008 and says the gap is `packaging`'s
      wheel-only flag. DEC-TRS-003 keeps the recipe without it;
    - the `--sdist` smoke is dropped, which retires LOW-5, and
      `tools/smoke_wheel.py` joins C-TRS-2's unedited files;
    - the Why, the Problem Statement and DEC-TRS-001 say a bare sdist
      beside a good wheel arises only from separate builds, which no
      workflow makes;
    - Milestone 2 and Milestone 6's re-pointing follow.

    One correction to the decision as handed over: at `bfbc124`,
    `packaging` smokes nothing. R-TRS-4's recipe adds the smoke the release
    paths run, with their probes, so the job smokes a wheel built from the
    sdist once it lands. What fails an sdist that cannot build is the build
    step, before the smoke.
  - **MEDIUM-1.** "CI runs on every push and pull request" was false:
    `ci.yml:9-10` filters `push` to the promotion branches. Every copy now
    reads "on every pull request, and on every push to the integration,
    candidate and production branches", pointing at
    `[tool.specgraph.promotion]`. That covers R-TRS-9, R-TRS-15, R-TRS-16,
    DEC-TRS-003, DEC-TRS-010, AC-TRS-11, the proposal's Non-Goals and
    Milestones 2 and 5. AC-TRS-11 cites
    `test_ci_push_branches_match_the_promotion_config`.
  - **MEDIUM-2.** The tier sentences claimed exclusivity, which
    `add-witness-ci-artifacts`' `ladder` job and `security` step would make
    false. They now say which jobs run `make pre-pr` by name, and never that
    no other does. gitleaks-action is "a different tool" from the security
    target's, not "in place of" it (R-TRS-15, R-TRS-16, DEC-TRS-010).
    AC-TRS-10 is limited to this change's diff, and DEC-TRS-007 gains the
    either-order re-read.
  - **MEDIUM-3.** The `docs/aqa.md` range is a real textual conflict with
    `prepare-release-0-4-0` (`$R/mergetest/`, above). DEC-TRS-010 says so
    and names the resolution. Milestone 5 reads the merged paragraph at the
    merge, and that package's hazard list names the conflict (R-TRS-16,
    R-TRS-19).
  - **MEDIUM-4.** One scoped exception to C-TRS-4. R-TRS-19, DEC-TRS-015
    and AC-TRS-24 amend `prepare-release-0-4-0`'s R-RFR-2 and AC-RFR-20,
    its Milestone 5 preconditions and its hazard list, each marked, on the
    precedent of R-MCO-10 and DEC-MCO-007, and of R-LPT-16 and DEC-LPT-007.
    DEC-TRS-012 and this milestone's ordering bullet follow. Its IDs are
    unchanged, and the gate is clean on it (measured above).
  - **MEDIUM-5.** `delta` joins the unreadable-spec entry. The exit-1
    section becomes "Exit-1 cases that are not findings", with `delta`
    folded in beside `detect --diff`, and "only findings" is reworded.
    R-TRS-10 says "a coverage floor whose value changed", and a removed
    floor's exit 0 is recorded as current behaviour. That covers R-TRS-10,
    R-TRS-12, DEC-TRS-008, AC-TRS-12 to AC-TRS-14 and Milestone 3, and
    DEC-TRS-008 cites DEC-DL-008, which asked for this edit.
  - **LOW-1.** Replaced commands are looked for over the job's code lines,
    and a flow-mapping step is planted (R-TRS-8, DEC-TRS-006, AC-TRS-9,
    Milestone 1).
  - **LOW-2.** Kept as a wheel-checker hardening: R-TRS-18, DEC-TRS-014,
    AC-TRS-23 and Milestone 2. It was reproduced first. On the way a second
    false pass turned up, a header with a longer expression, and the same
    exact-field reading closes it.
  - **LOW-3.** The README `witness` line passes `--exit "$code"` (R-TRS-13,
    DEC-TRS-009, AC-TRS-16, Milestone 4).
  - **LOW-4.** The hook list says the lint and typecheck hooks run when a
    Python file is staged (R-TRS-15, DEC-TRS-010, Milestone 5).
  - **LOW-5.** Retired with the `--sdist` smoke (HIGH-1).
  - **LOW-6.** The smoke's validate of `.` is accepted in DEC-TRS-003, with
    the reason.
  - **LOW-7.** The build-leftovers sentence is corrected above. The notes on
    an sdist holding two top-level directories and on `fnmatch` crossing a
    `/` concerned the sdist reader, and are moot with it withdrawn.

  **Recorded — second review, 2026-10-17, at `bfbc124` (no HIGH):**
  - **MEDIUM-1.** The recipe's `--expect` probes were a copy that nothing
    tied to `release-tier`; `smoke_problems` checks presence only, and passes
    on `$R2/drift` (measured above). R-TRS-4 now requires a guard holding the
    recipe's probe set equal to `release-tier`'s, read from the workflow, as
    a new function. C-TRS-7 now names `smoke_problems` among the frozen
    helpers. DEC-TRS-003 records why, AC-TRS-6 plants the drift case both
    ways, and Milestones 2 and 6 plan and re-point the two tests.
  - **MEDIUM-2.** The licence-expression item is restated as hardening. Its
    precondition is a wheel checked against a `pyproject.toml` other than its
    own, which no workflow produces. In-tree, the longer expression passes
    correctly, and setuptools writes the canonical header (measured above).
    That covers the Why, the Problem Statement, R-TRS-18 and DEC-TRS-014.
    R-TRS-18 and AC-TRS-23 stay, as defence in depth.
  - **LOW-1.** `delta --fail-on` draws the unrecognised-argument line only
    with `--baseline` given; without it, the missing flag comes first. Both
    were measured, and both lines are in R-TRS-10, R-TRS-12, DEC-TRS-008 and
    AC-TRS-13.
  - **LOW-2.** R-TRS-8 names the stems `_WIRED` uses, matched as
    substrings, so the guard stays green after Milestone 2 (DEC-TRS-006,
    Milestone 1).
  - **LOW-3.** `prepare-release-0-4-0`'s proposal sentence on pull request 2
    and its `tasks.md` ordering summary join R-TRS-19's sites, each an
    insertion with the marker (R-TRS-19, DEC-TRS-015, AC-TRS-24).
  - **LOW-4.** The Milestone 5 precondition also checks this change's
    `### Changed — the release surface` group in `CHANGELOG.md`, the heading
    Milestone 6 writes (R-TRS-19, DEC-TRS-015).
  - **LOW-5.** DEC-TRS-011 names `close-gate-script-gaps` and
    `raise-coding-standards` with their shared sites. The first's prototype
    guard is quiet on the revised recipe, and the second's `py.typed`
    reaches the sdist (measured above). DEC-TRS-015 says the precondition
    list it extends does not name every sibling, and that each sibling's own
    text holds its order.
  - **LOW-6.** "Separate jobs" becomes "separate jobs and steps" (R-TRS-16,
    DEC-TRS-010, Why item 4, Milestone 5).
  - **LOW-7.** The Problem Statement says "consistent with DEC-LM-008" and
    gives that decision no reason it does not state. DEC-TRS-001 and
    DEC-TRS-003 cite the module-dropping differential as the main evidence
    for the recipe. DEC-TRS-001 records that `MANIFEST.in` cannot drop the
    licence file.
- Cut the implementation branch from `dev` once the package has merged,
  open its pull request as a GitHub draft, and bring it to each later `dev`
  tip by merging `origin/dev`. Re-run every measurement above at the branch
  head, and note beside the bullet that uses it any line that moved.
- **The siblings' state at the branch head.** Record which of these have
  merged their implementations into `dev`, by the facts each package names
  for itself, and re-read the regions DEC-TRS-011 lists for each:
  - `lean-production-tree`: `git ls-tree origin/dev
    docs/distribution-plan.md` prints nothing once it has;
  - `harden-release-pipeline`: `test -f
    tests/fixtures/release-workflow.golden`;
  - `prepare-release-0-4-0`'s pull request 1: `git grep -q main_deprecated
    origin/dev -- openspec_graph` exits 1;
  - `add-witness-ci-artifacts`: `grep -n "witness-gate"
    .github/workflows/ci.yml`;
  - `close-gate-script-gaps`: `test -f tools/threshold_whitelist.txt`;
  - `raise-coding-standards`: `test -f openspec_graph/py.typed`.
- **The ordering constraint, for the maintainer.** This change must merge
  before `prepare-release-0-4-0`'s Milestone 5 opens the release-prep pull
  request. With R-TRS-19's amendment, that milestone's preconditions list
  this change: it records this change's merge commit, or the maintainer's
  decision to defer it to the next release (DEC-TRS-012, DEC-TRS-015).
  Record which here as well.
- **Gate:** every fact above recorded with its output and the date, then
  `make test` on the branch head. Only then is the implementation pull
  request marked ready.

## Milestone 1 — Call the equivalent stages by name, nothing else changed

- **The guards first, red on the unedited tree.** In
  `tests/test_ci_makefile.py`, appended after the last function:
  - A constant, `_WIRED`, pairs each job with its target and the stems of
    the commands the target replaced, each matched as a substring
    (R-TRS-8, DEC-TRS-006):
    - `self-validate` with `validate`, and `planlint --target . validate
      --fail-on ERROR`;
    - `security` with `thresholds`, and `python
      tools/check_no_hardcoded_thresholds.py`;
    - `packaging` with `wheel-check`, and `python -m build` and `python
      tools/check_wheel_metadata.py dist`. The first stem is what keeps the
      guard green once Milestone 2's recipe builds with
      `python -m build --outdir dist`.
  - `_wiring_problems(ci_text: str, makefile_text: str) -> list[str]` is a
    pure reader. Per job, it takes the job block from
    `tests.support.workflow_job_blocks`. It names:
    - a job whose `run:` scripts, read through
      `load_tool("stage_citations", "stage_citations.py").run_scripts`, do
      not invoke its target in command position, read through
      `shell_invocations`;
    - a job any of whose code lines still carries a stem. The code lines
      are every line of the block, with comments stripped by
      `tests/workflow_support._code_lines`. The `run:` scripts alone are not
      read for this, because a flow-mapping step is invisible to that reader
      (DEC-TRS-006);
    - a stem found in no line of the target's recipe, read through
      `_recipe_lines`.
  - `test_ci_jobs_call_the_targets_whose_recipes_they_ran_inline`
    (integration) asserts `_wiring_problems` is empty on the real files
    (R-TRS-6, R-TRS-8, AC-TRS-8). Record it red on the unedited tree, naming
    each of the jobs.
  - `test_a_job_running_a_target_recipe_inline_is_named` (unit,
    non-success) runs planted job text through the same reader:
    - the command beside its target;
    - the command in place of its target;
    - the command in a flow-mapping step, `- {name: x, run: <the
      command>}`, beside the step that calls the target;
    - a target whose recipe dropped the command.

    Each is named with the job and the command. A planted spec tree citing an
    unrun stage is not read by the guard at all (R-TRS-8, DEC-TRS-006,
    AC-TRS-9).
- In `tests/test_stage_citations.py`, appended:
  `test_ci_yml_runs_the_wired_stages_by_name` (integration) asserts that
  `sc.workflow_stages(REPO_ROOT, ("ci.yml",))["ci.yml"]` contains
  `validate`, `thresholds` and `wheel-check`.
  `test_this_repository_report_holds_its_invariants` is unedited
  (AC-TRS-8, C-TRS-7).
- **`.github/workflows/ci.yml`:**
  - `self-validate`: the `run:` of the step "Validate every change package
    (hard gate)" becomes the make call for the validate target, with the step
    name kept. The job's install step already puts `planlint` on PATH.
  - `security`: the `run:` of the step "No hard-coded thresholds in Makefile
    / workflow (hard gate)" becomes the make call for the thresholds target.
    The job comment (`:377-379`) says the guard runs through its make target.
    The gitleaks step and the job's `permissions:` are untouched.
  - `packaging`: the two steps at `:213-217` become one step, "Build and
    check the distribution (hard gate)", whose `run:` is the make call for
    the wheel-check target. The "Install build frontend" step stays.
  - No other line of the file changes in this milestone. Confirm with
    `git diff -U0 origin/dev...HEAD -- .github/workflows/ci.yml`.
- **Equivalence, read before committing.** The three recipes are
  byte-identical to the job lines they replace, by reading `Makefile:60`,
  `:89` and `:104-105` beside the removed lines. The Makefile is not edited
  in this commit (R-TRS-6).
- `docs/hooks.md`, the CI table:
  - the `self-validate` cell names the validate target running
    `planlint validate --fail-on ERROR`;
  - the `security` cell names gitleaks-action, as a different tool from the
    security target's scanner, and the thresholds target;
  - the `packaging` cell names the wheel-check target, for now as the wheel
    build and `tools/check_wheel_metadata.py`.

  The first cells keep their backticked job names
  (`test_hooks_ci_table_lists_every_ci_job`,
  `test_every_hooks_ci_table_row_names_a_job_or_workflow`) (R-TRS-9).
- Run `python tools/stage_citations.py` and record its summary line. Expect
  `validate`, `thresholds` and `wheel-check` credited to `ci.yml`, and `ci`,
  `coverage-tools` and `security` still unrun (DEC-TRS-005).
- Run `python tools/check_no_hardcoded_thresholds.py` and record `PASS`
  (C-TRS-2). If `close-gate-script-gaps` has landed, its widened guard is
  the one run.
- **Gate:** `make test`

## Milestone 2 — The build in `packaging`: the wheel from the sdist, checked and smoked, and the header-only licence check

- **`tests/test_wheel_metadata.py`, first, written against the unedited
  checker.** Two planned tests, each marked `integration` as the module's
  others are, each through the existing `_wheel` helper:
  - `test_a_license_expression_only_in_the_body_is_caught`: `GOOD_METADATA`
    without its `License-Expression:` line, then an empty line, then a body
    line `License-Expression: Apache-2.0`. `check_wheel(..., "Apache-2.0",
    ["LICENSE"])` returns a problem containing `License-Expression`.
    Record it **red** against the unedited checker, which returns `[]`
    (DEC-TRS-014, AC-TRS-23).
  - `test_a_longer_header_expression_is_caught`: `GOOD_METADATA` with the
    field's value replaced by `Apache-2.0 OR MIT`, against `Apache-2.0`.
    Record it **red** likewise.
  - Every existing function in the module is unedited (C-TRS-7, AC-TRS-3).
- **`tools/check_wheel_metadata.py`** (R-TRS-18, DEC-TRS-014):
  - A private `_header_lines(metadata: str) -> list[str]`, with a docstring,
    returns the lines before the first empty line, or every line when there
    is none.
  - `check_wheel`'s expression test becomes "`expected` is not one of
    `[line.rstrip() for line in _header_lines(metadata)]`". Its message is
    byte-identical. The classifier loop, the licence-file loop and `main`
    are unchanged.
  - The module docstring's check 1 says the field is read from the
    `METADATA` header, and why: the body is the README, and the check is
    defence in depth.
  - `_declared_license` (`:43-59`) is not touched, because
    `prepare-release-0-4-0` rewords its docstring (DEC-TRS-011). The `D103`
    ceiling of `{"D103": 1}` does not rise. No sdist is read (DEC-TRS-001).
- **`tests/test_ci_makefile.py`, the probe set, first** (R-TRS-4,
  DEC-TRS-003, AC-TRS-6), appended beside Milestone 1's guards:
  - `_release_tier_probes(ci_text: str) -> frozenset[str] | None` reads
    `release-tier`'s block through `tests.support.workflow_job_blocks`, and
    its code lines through `tests.workflow_support._code_lines`. It takes the
    lines from the one carrying `tools/smoke_wheel.py` up to the next line
    that opens a step. It returns the `PATH=CODE` values of every
    `--expect` among them, and `None` when no line carries the smoke call.
  - `_probe_drift(ci_text: str, makefile_text: str) -> list[str]` compares
    that set with the `--expect` values on the `wheel-check` recipe's
    `tools/smoke_wheel.py` line, read through `_recipe_lines`. It names:
    - each value `release-tier` passes and the recipe lacks, as `wheel-check
      lacks --expect <value> that release-tier passes`;
    - each value the recipe passes and `release-tier` lacks, the other way
      round;
    - a smoke line missing from either side.

    Neither set is restated: both come from the files.
    `smoke_problems` and `SMOKE_PROBES` in `tests/test_ci_promotion.py` are
    not edited (C-TRS-7).
  - `test_wheel_check_smokes_with_the_release_tier_probe_set` (integration)
    asserts `_probe_drift` is empty on the real files. Record it **red** on
    the tree before the recipe below lands, where the recipe has no smoke
    line.
  - `test_a_drifted_smoke_probe_set_is_named` (unit, non-success) plants the
    second review's drift case: `release-tier`'s smoke step with
    `--expect tests/fixtures/action/no-tree=2` appended, beside the recipe
    below. It asserts that probe is named as one `wheel-check` lacks. A
    second plant gives the recipe a probe `release-tier` lacks, and asserts
    that probe is named the other way round.
  - Record `_probe_drift` run once over `$R2/drift`'s `ci.yml` and
    `Makefile`, naming `tests/fixtures/action/no-tree=2`.
- **`Makefile`**, `wheel-check` only (R-TRS-4). The help text is "Build the
  sdist and the wheel from it, check the wheel carries the declared SPDX
  licence, and smoke its console script". It does not begin "Report". The
  recipe:

  ```
  	rm -rf dist
  	python -m build --outdir dist
  	python tools/check_wheel_metadata.py dist
  	python tools/smoke_wheel.py dist --expect tests/fixtures/action/passing=0 --expect tests/fixtures/action/failing=1
  ```

  `.PHONY` and every other target are unchanged.
- **`tests/test_ci_makefile.py`**, appended:
  - `test_wheel_check_builds_from_the_sdist_then_checks_and_smokes_the_wheel`
    (integration) asserts `_recipe_lines(makefile, "wheel-check")` equals
    the four lines above;
  - `test_wheel_check_stays_out_of_the_ladder` (integration) asserts
    `wheel-check` is reachable from neither `ci` nor `pre-pr`, through
    `_reachable`, and that its help text does not begin "Report".

  (AC-TRS-6, DEC-TRS-004) Budget: with Milestone 1's additions the module
  stays under `MAX_TEST_MODULE_LINES`. If it would not, the probe-set reader
  and its two tests move to a new module, split per
  `tests/test_suite_shape.py`'s rule.
- **`.github/workflows/ci.yml`**, `packaging` only: the job comment says it
  builds the sdist and the wheel from it, checks that wheel's licence and
  smokes its console script, as the release paths do, on every pull
  request. The step name becomes "Build the sdist and the wheel from it,
  check and smoke the wheel (hard gate)". The step's `run:` is unchanged.
  The job's `timeout-minutes` stays inside the configured range, re-checked
  against the first run.
- `docs/hooks.md`: the `packaging` cell names what the target now builds,
  checks and smokes (R-TRS-9). The `release-tier` cell is not edited: it
  already names the build of both artifacts, the checker and the smoke, and
  the checker stays wheel-only.
- **Run the target locally.** Run the `wheel-check` target from a clean
  checkout of the branch head, and record:
  - the build log's `Building wheel from sdist`;
  - the checker's `PASS` line;
  - each smoke `PASS` line;
  - the exit code;
  - `git status --short --ignored` afterwards, adding only the gitignored
    `dist/` and `planlint.egg-info/`.
- Run `python tools/check_no_hardcoded_thresholds.py`, and record `PASS` on
  the new recipe lines (C-TRS-2, AC-TRS-21).
- Confirm `git diff --stat origin/dev...HEAD -- .github/workflows/release.yml
  .github/actions templates tools/smoke_wheel.py tests/test_ci_promotion.py`
  prints nothing (R-TRS-5, C-TRS-2, C-TRS-7, AC-TRS-7).
- **Gate:** `make test`

## Milestone 3 — `delta`'s exit codes in the operating contract

- **`tests/test_skill_contract.py`, first**, appended after the last
  function. The module-level `READ_ONLY_INVOCATIONS` tuple, which
  `add-witness-ci-artifacts` edits, is left alone. Planned:
  - `_DELTA_ENTRIES`, the guarded phrases of DEC-TRS-008. Per file:
    - `exit-codes.md`: the no-spec-tree heading naming `delta`, the
      `--baseline` ordering sentence, the unreadable-spec heading naming
      `delta`, the `delta --fail-on` entry with both of its parser lines,
      the "Exit-1 cases that are not findings" heading, the `delta`
      paragraph's "a coverage floor whose value changed", and the exit-1
      row's `delta` clause;
    - `SKILL.md`: the exit-1 row's `delta` clause, and the no-spec-tree
      bullet naming `delta`.
  - `_DELTA_RETIRED`, the phrases that must be gone from `exit-codes.md`:
    "Exit 1 means findings, and only findings." and "The one exit-1 case
    that is not a finding".
  - `_delta_contract_gaps(skill_text: str, exit_codes_text: str) ->
    list[str]`, a pure reader naming each missing phrase, and each retired
    phrase still present, with its file.
  - `test_both_contract_files_document_delta` (integration): empty on the
    real files (AC-TRS-12, AC-TRS-14).
  - `test_a_contract_missing_a_delta_entry_is_named` (unit, non-success):
    each phrase deleted from planted copies, and the "only findings"
    sentence restored to one, is named with its file (AC-TRS-13).
  - `test_delta_without_a_spec_tree_prints_the_documented_message` (e2e):
    `run_cli(tmp_path, "delta", "--baseline", str(tmp_path / "absent.json"))`
    on an empty `tmp_path` gives exit 2, and `stderr.strip() ==
    _NO_TREE_SHORT` (AC-TRS-12).
  - `test_delta_on_an_unreadable_spec_prints_the_documented_message` (e2e):
    a target holding `tests/fixtures/Makefile`,
    `tests/fixtures/pyproject.toml` and one readable spec, as
    `tests/test_spec_read_errors.py` builds one. A card is saved from it with
    `detect --format json`, then a directory is made where a second spec
    file belongs. `delta --baseline <card>` gives exit 2, a stderr starting
    `ERROR cannot read spec `, and no `Traceback` (AC-TRS-12).
  - `test_delta_rejects_fail_on_as_a_usage_error` (e2e): `delta --baseline
    <card> --fail-on ERROR` on `populated_repo` gives exit 2, and
    `unrecognized arguments` is in stderr. The `--baseline` is what makes
    that the line the parser prints: without it, the missing flag is
    reported first (AC-TRS-13, DEC-TRS-008).

  Record the first two red on the unedited files. Budget: the module stays
  under `MAX_TEST_MODULE_LINES` with Milestone 4's additions. Split it per
  `tests/test_suite_shape.py`'s rule if it would not.
- **`skills/planlint-spec-governance/references/exit-codes.md`**: the
  wording of DEC-TRS-008, exactly.
  - The top table's exit-1 row.
  - The sentence under the table (`:12`).
  - The no-spec-tree entry (`:18`): "Each prints exactly:", then the
    `--baseline` ordering sentence after the code block.
  - The unreadable-spec entry's heading (`:46`), with its message and
    paragraph unchanged.
  - The `delta --fail-on` entry, placed directly after the unusable-baseline
    entry, which is unchanged. It quotes both parser lines.
  - The exit-1 section (`:119`), retitled "Exit-1 cases that are not
    findings". Its `detect --diff` paragraph is unchanged, and the `delta`
    paragraph follows it.

  Afterwards `grep -rn "only findings\|The one exit-1 case" skills/` prints
  nothing.
- **`skills/planlint-spec-governance/SKILL.md`**, lines `:76-90` only:
  - the exit-1 row's meaning cell;
  - the no-spec-tree bullet names `delta`, and "In all three cases" becomes
    "In each of these cases".

  The frontmatter (`:1-9`) is not touched. Run `python
  tools/render_plugin_manifests.py --check`, and record exit 0 with no
  regeneration (R-TRS-11, C-TRS-3, AC-TRS-15).
- `test_exit_two_messages_match_the_documented_contract` and
  `test_unreadable_spec_exits_2_from_every_parsing_verb` are unedited, and
  still pass for the verbs they cover (C-TRS-7).
- **Gate:** `make test`

## Milestone 4 — The README's verbs

- **`tests/test_skill_contract.py`, first**, appended beside the Milestone 3
  tests:
  - `_readme_quickstart_verbs(text: str) -> tuple[set[str], bool]` is a pure
    reader over the first fenced `bash` block of `README.md`. For each line
    starting `planlint `, it skips the global `--target <arg>`, `-v` and
    `--verbose`, and takes the first remaining non-flag token as the verb.
    `--version` alone yields none. The boolean says whether a `validate`
    line carries `--format sarif`.
  - `test_readme_quickstart_shows_every_cli_verb` (integration): the verb
    set equals `build_parser()`'s subparser choices, read as
    `test_skill_tables_cover_every_verb_the_cli_actually_has` reads them,
    and the sarif flag is true (R-TRS-13, R-TRS-14, AC-TRS-16).
  - `test_a_readme_quickstart_verb_gap_is_named` (unit, non-success): planted
    text missing `delta`, planted text naming `lint`, and planted text with
    no sarif line, each named (AC-TRS-17).

  Record the integration test red on the unedited README, naming `delta`,
  `report`, `rules`, `witness` and the sarif line.
- **`README.md`**, the quickstart block (`:41-52`). Insert, keeping
  `/path/to/clone`, and with no line touching `:39`:
  - after the `validate` line:
    - `planlint --target /path/to/clone validate --format json > findings.json  # the portable findings envelope`;
    - `planlint --target /path/to/clone validate --format sarif > findings.sarif  # SARIF 2.1.0 for code scanning`;
  - after the `graph` line:
    - `planlint --target /path/to/clone delta --baseline prev.json  # exit 1 on any spec citing machinery that moved since the card; no --fail-on`;
    - `planlint rules --json                       # the rule table this build carries`;
    - `planlint report --findings findings.json --format github-summary  # render a saved envelope; reads no repository, never exits 1`;
    - `planlint --target /path/to/clone witness --stage test --exit "$code" --sha "$(git rev-parse HEAD)"  # CI only: the job that ran the stage records the exit it captured`.

  `"$code"` is the exit the stage step captured, never a literal
  (DEC-TRS-009). Align the comments as the block does. No install command
  and no `@v` or `rev:` token is added.
- `README.md`, under the exit-code table (after its last row at `:65`,
  before the "Changed in 0.2.0" note at `:67`): "`delta` has no `--fail-on`
  and exits 1 on any stale citation, and `report` never exits 1; the
  per-verb contract is
  [`exit-codes.md`](skills/planlint-spec-governance/references/exit-codes.md)."
  The link target resolves (R-TRS-13).
- Run `python -m pytest tests/test_adopter_urls.py -q` and record it green
  (AC-TRS-16).
- **Gate:** `make test`

## Milestone 5 — What each tier runs

- **`docs/hooks.md:3-6`**, the opening paragraph, rewritten to R-TRS-15. It
  says:
  - each tier runs a different part of the gate;
  - the commit-time hooks run the security, validate, docs-check and
    thresholds targets whatever is staged, and the lint and typecheck
    targets when a Python file is staged, and they run no tests or
    coverage;
  - CI runs on every pull request, and on every push to the integration,
    candidate and production branches that `[tool.specgraph.promotion]`
    names, whatever the hooks did, as separate jobs and steps:
    - lint, typecheck and the suite with both trees' floors, as steps of
      one job on every leg;
    - the validate, docs-check and thresholds targets;
    - the `security` job's gitleaks-action scan over the full history, a
      different tool from the security target's scanner;
    - the `wheel-check` target in `packaging`, which `make pre-pr` does not
      compose;
    - the live track and the composite action's contract;
  - `release-tier` and the release workflow's gate run `make pre-pr` by
    name.

  No sentence says a job is the only one to run a target (R-TRS-15,
  DEC-TRS-007). The promotion-route sentence stays. Name no change package
  (C-TRS-6).
- **`docs/hooks.md:16-18`**: the pre-commit paragraph keeps "local hooks
  that call `make`" and "no second set of tool-version pins". It drops "the
  same targets CI uses — so a commit can never bypass CI". It adds that the
  hooks run no tests, and that CI does not depend on them because it runs on
  every pull request, and on every push to the integration, candidate and
  production branches. The bullet list (`:20-26`) is unchanged, so
  `close-gate-script-gaps`' edit of its thresholds line merges cleanly.
- **`.pre-commit-config.yaml:4-5`**: the header comment, reworded the same
  way, with no tool name beside a version or operator, so
  `close-gate-script-gaps`' pin rule, which reads comments there, stays
  quiet. No `entry:` line changes
  (`test_the_two_pre_commit_files_do_not_collide`).
- **`docs/aqa.md`:**
  - `:283`: the comment on the `make pre-pr` line becomes "the whole local
    ladder; the release tier runs it by name".
  - `:287-291` is rewritten to R-TRS-16:
    - the ladder's parts that CI runs as separate jobs and steps on every
      pull request, and on every push to the integration, candidate and
      production branches: lint, typecheck and the suite with both trees'
      floors on each leg, and the validate, docs-check and thresholds
      targets;
    - the `security` job's gitleaks-action scan over the full history, a
      different tool from the security target's scanner;
    - its additions: the live track, the `wheel-check` target, the
      composite action's contract, the graph-diff gate on pull requests, the
      `promotion` route check and `ci-ok`.
  - **The range token, read at the merge** (DEC-TRS-010). Write the token as
    it stands at the branch head. Whichever of this change and
    `prepare-release-0-4-0`'s removals merges second meets the conflict. The
    resolution keeps this change's sentence with that package's token:
    "Python 3.11–3.14" once its removals have merged, "Python 3.10–3.14"
    before. After that merge, `grep -n "3\.1[01]–3\.14" docs/aqa.md` prints
    the `:150` range and the rewritten paragraph's, and the two agree.
    Record the output. If this change lands first, that package's hazard
    list carries the same resolution (R-TRS-19).
  - After the paragraph that follows the Gates table (after `:22`): one
    sentence, that the `wheel-check` target is a gate outside the ladder
    which `packaging` runs on every pull request, and on every push to the
    integration, candidate and production branches, and what it builds,
    checks and smokes (R-TRS-9).
- **`README.md:358-359`**: "the full quality bar in one command — the same
  bar CI enforces" becomes:
  - `make pre-pr` runs every row below but `e2e-live` and `wheel-check` in
    one command;
  - CI runs the same rows as separate jobs and steps on every pull request,
    and on every push to the integration, candidate and production branches.
    Its `security` job scans with gitleaks-action, a different tool from the
    `security` row's;
  - the release tier runs `make pre-pr` itself, by name.

  The table gains a `wheel-check` row after `thresholds`, in the table's own
  shape:
  - its Command cell is the make call for that target, written as the other
    rows write theirs;
  - its Checks cell reads "the wheel built from the sdist carries the
    declared licence, and its console script passes and fails the labelled
    fixtures".

  The paragraph at `:372-379` is unchanged.
- **The overclaim grep, run again.** The grep from the measurements, over
  the same paths, prints none of the lines this milestone rewrote, and
  nothing for its two added patterns. Record what it prints (AC-TRS-18).
- **Gate:** `make docs-check`

## Milestone 6 — Release notes, selectors, observations and the self-gate

- **`CHANGELOG.md` `[Unreleased]`**: `### Changed — the release surface`,
  with one entry led by **`tighten-release-surface`** naming each item of
  R-TRS-17, in the file's voice. Placed after any group a sibling wrote.
  The heading is spelled exactly so, because `prepare-release-0-4-0`'s
  Milestone 5 greps for it (R-TRS-19). `git diff origin/dev...HEAD --
  CHANGELOG.md` shows only `[Unreleased]` lines (AC-TRS-19).
- **Re-point this package's stage-only criteria** to the tests that now
  exist, keeping each stage:
  - AC-TRS-9: `test_a_job_running_a_target_recipe_inline_is_named`;
  - AC-TRS-13: `test_delta_rejects_fail_on_as_a_usage_error`,
    `test_a_contract_missing_a_delta_entry_is_named`;
  - AC-TRS-17: `test_a_readme_quickstart_verb_gap_is_named`;
  - AC-TRS-23: `test_a_license_expression_only_in_the_body_is_caught`,
    `test_a_longer_header_expression_is_caught`.

  Add these beside the existing selectors:
  - AC-TRS-6: `test_wheel_check_builds_from_the_sdist_then_checks_and_smokes_the_wheel`,
    `test_wheel_check_stays_out_of_the_ladder`,
    `test_wheel_check_smokes_with_the_release_tier_probe_set`,
    `test_a_drifted_smoke_probe_set_is_named`;
  - AC-TRS-8: `test_ci_jobs_call_the_targets_whose_recipes_they_ran_inline`,
    `test_ci_yml_runs_the_wired_stages_by_name`;
  - AC-TRS-12: `test_both_contract_files_document_delta`,
    `test_delta_without_a_spec_tree_prints_the_documented_message`,
    `test_delta_on_an_unreadable_spec_prints_the_documented_message`;
  - AC-TRS-16: `test_readme_quickstart_shows_every_cli_verb`.

  Then run `python -m pytest tests/test_spec_test_citations.py -q`, and
  confirm every selector resolves (AC-TRS-22).
- **The stage-citations report.** `python tools/stage_citations.py`: record
  the summary line, and confirm this package's verification lines cite only
  `test`, `docs-check` and `pre-pr` (DEC-TRS-013).
- **The first hosted run.** The implementation pull request's first run
  with Milestones 1 and 2 in place. Record:
  - the run id;
  - `packaging`'s duration, against its `timeout-minutes`;
  - the log lines of the build, `Building wheel from sdist` among them, the
    checker's `PASS` line, and each smoke `PASS` line;
  - `self-validate` and `security` green through their targets.

  This is a gate of this file, not a criterion (DEC-TRS-013).
- **The diff confined.** Confirm each of these prints nothing:
  - `git diff --stat origin/dev...HEAD -- openspec_graph
    .github/workflows/release.yml .github/actions templates
    tools/smoke_wheel.py tests/test_ci_promotion.py .claude-plugin
    tests/baseline_rules.json`;
  - `git diff --stat origin/dev...HEAD -- openspec/changes | grep -v
    tighten-release-surface`. R-TRS-19's amendment rode in the package pull
    request, so the implementation's diff holds no other package's text.

  (C-TRS-1 to C-TRS-4, C-TRS-7, AC-TRS-20, AC-TRS-22)
- **No count in the spec.** `grep -nE "\b[0-9]+ (spec|stage|job|package|test|file)s?\b"
  specs/release-surface/spec.md` prints nothing (C-TRS-5).
- **The self-gate.** Run each of these, and record each exit code:
  - `planlint --target . validate --fail-on INFO --change
    tighten-release-surface`;
  - `planlint --target . validate --fail-on INFO --change
    prepare-release-0-4-0`;
  - `planlint --target . validate --fail-on ERROR`;
  - `python -m pytest tests/test_spec_test_citations.py
    tests/test_spec_status.py tests/test_stage_citations.py -q -p
    no:cacheprovider`.
- Tick each criterion only as it is verified. The header stays `DRAFT`, and
  the pull request asks the maintainer to settle it at merge.
- **Gate:** `make pre-pr`
