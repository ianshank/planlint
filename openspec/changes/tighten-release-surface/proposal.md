# Change: Tighten the Release Surface — the Wheel Built From the Sdist on Every Pull Request, the Equivalent Stages Called by Name, `delta`'s Exit Codes, the README's Verbs, and What Each Tier Runs

## Why

The release surface is what an adopter meets before reading any code: the
two files PyPI publishes, the README that is also the PyPI long description,
and the operating contract an agent follows. A 2026-10-16 review of `dev`
found five places where that surface says less, or more, than the tree does.
Each was re-measured here before this package was written. Two measured
differently from the review, and this package follows the measurement. An
adversarial review of the first draft, on 2026-10-17, corrected the first of
them and widened two others. A second review the same day recast the
licence-expression item as hardening and tied the recipe's smoke probes to
their source. `tasks.md` Milestone 0 records each finding and what changed.

1. **The per-pull-request build skips the sdist.** The release workflow and
   `release-tier` build with `python -m build` and no distribution flag,
   which builds the sdist and then the wheel *from* that sdist. The wheel
   they check and smoke is therefore built from the sdist they publish.
   Reproduced, an sdist missing its `LICENSE` yields a wheel with no licence
   file, and the existing checker fails it. That is consistent with
   `migrate-license-metadata-pep639`'s DEC-LM-008, which reads wheels only,
   and the decision stands. The gap is narrower. The `packaging` job, the
   packaging check that runs on every pull request, builds with `--wheel`.
   Its wheel comes from the source tree and never from the sdist, so an
   sdist defect reaches no check until `release-tier`, on the candidate and
   production branches, or the tag. The defect that matters is a missing
   module, not a missing licence. setuptools adds the declared
   `license-files` back even when `MANIFEST.in` excludes them. A module
   excluded there is absent from the sdist. Measured, today's recipe passes
   such a tree, and the recipe this change writes fails it on every smoke
   probe. The first draft took a different directory for the gap: a bare
   sdist beside a good wheel. The checker does pass that directory, but it
   arises only when the two are built separately, and no workflow builds
   them that way. Beside this, and as hardening rather than a gap any
   workflow exposes, the checker's licence-expression test is a substring
   search over the whole `METADATA`, whose body is the README. Checked
   against a `pyproject.toml` other than its own, a wheel whose header
   lacks the field passes when the README carries the line, and so does a
   header with a longer expression than the declared one. No workflow
   checks a wheel against another tree, and setuptools 77 and later write
   the canonical field into the header.
2. **`delta`'s exit codes are missing from the operating contract.** `delta`
   exits 1 on any stale citation. It does not "ignore" `--fail-on`, as the
   review put it: it has no such flag, and passing one is a usage error that
   exits 2. It exits 2 with the short no-spec-tree message, and it checks for
   the tree before it reads `--baseline`. It also exits 2 on an unreadable
   spec, through the same path as the other parsing verbs. The per-verb
   reference documents `delta`'s unusable-baseline exit 2 and none of the
   others. It also says "Exit 1 means findings, and only findings" above a
   section titled for the one exit-1 case that is not a finding.
   `add-delta-lint`'s DEC-DL-008 required that section to grow a second
   case, and it never did. `SKILL.md` documents none of them, and its exit-1
   row speaks only of `--fail-on`.
3. **The README leaves out verbs.** Its quickstart shows `detect`, `init`,
   `new`, `validate`, `waivers`, `graph` and `--version`. It never shows
   `rules`, `delta`, `report` or `witness`, or `validate --format sarif`,
   although the parser declares all four verbs and the format.
4. **Stage wiring.** The stage-citations report names `ci`,
   `coverage-tools`, `security`, `thresholds`, `validate` and `wheel-check`
   as stages a verification line cites and no workflow invokes by name.
   Three of them run inline in CI with exactly their target's recipe:
   `self-validate` runs the validate recipe, `security` runs the thresholds
   recipe, and `packaging` runs the wheel-check recipe. The other three are
   not equivalent to anything a job runs. `ci` is an aggregate whose parts run
   in separate jobs and steps. `coverage-tools`' floors are already checked
   inside `make test`. And the security target scans with a different tool
   from the `security` job's. The `wheel-check` target is in no job, is not
   in `make pre-pr`, and appears neither in `docs/hooks.md`'s ladder nor in
   `docs/aqa.md`.
5. **The docs overclaim.** `docs/hooks.md` opens by saying pre-commit and CI
   enforce the same gate as `make pre-pr`, and `docs/aqa.md` calls
   `make pre-pr` "the exact bar CI enforces". Pre-commit runs no tests. CI
   runs on every pull request, and on every push to the integration,
   candidate and production branches. At `bfbc124` the `ci.yml` job that runs
   `make pre-pr` by name is `release-tier`, for pull requests into and pushes
   to the candidate and production branches. The same claim stands in two
   more places the review did not name: `README.md`'s AQA section and the
   header comment of `.pre-commit-config.yaml`.

**Evidence:** measured at `bfbc124` (`origin/dev`) on
`claude/tighten-release-surface`, 2026-10-16, and re-measured at the same
commit on 2026-10-17 for both reviews. Line numbers are at that commit. A
sibling landing first moves a line without moving the fact, and `tasks.md`
re-reads each one before the milestone that uses it. Every command and its
output are in `tasks.md`.

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR` printed `57 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`,
  exit 0, before any file of this package existed. Before each revision it
  printed `58 spec(s) checked`, with this package in place, exit 0. The
  installed console script is an editable install of a checkout whose
  `openspec_graph/` is byte-identical to this worktree's (`diff -rq`, exit
  0).
- **The build.**
  - `.github/workflows/release.yml:82-103`: `build` runs `python -m build`,
    then `python tools/check_wheel_metadata.py dist`, then
    `tools/smoke_wheel.py dist` with the labelled-fixture probes.
    `.github/workflows/ci.yml:492-502`: `release-tier` does the same with
    `--outdir dist`.
  - `ci.yml:213-217`: `packaging` runs `python -m build --wheel --outdir dist`
    and then the checker, and smokes nothing.
  - `Makefile:103-105`: the `wheel-check` recipe is that same pair.
  - `tools/check_wheel_metadata.py:132` globs `*.whl` only.
  - `migrate-license-metadata-pep639`'s
    `specs/license-metadata/spec.md`, DEC-LM-008: wheels only, "Revisit if an
    sdist-only defect is ever observed."
  - Built from a scratch copy of this tree, with `python -m build` 1.6.1
    resolving `setuptools>=77` to 84.0.0 in isolation, the log reads
    `Building sdist...` and then `Building wheel from sdist`. The sdist holds
    `planlint-0.3.0/PKG-INFO` and `planlint-0.3.0/LICENSE`.
  - A wheel built from that sdist with its `LICENSE` and its
    `License-Expression` line stripped still carries `License-Expression:
    Apache-2.0`, regenerated from the sdist's `pyproject.toml`, and no
    `licenses/` member. The unedited checker prints `FAIL
    planlint-0.3.0-py3-none-any.whl: 'LICENSE' is declared in license-files
    but no matching file was packaged under
    planlint-0.3.0.dist-info/licenses/`, exit 1.
  - With `exclude LICENSE` in `MANIFEST.in`, setuptools logs `warning: no
    previously-included files found matching 'LICENSE'` and then `adding
    license file 'LICENSE'`, and the sdist lists `planlint-0.3.0/LICENSE`.
  - **The differential.** With `exclude openspec_graph/mermaid.py` in
    `MANIFEST.in`, today's `wheel-check` recipe builds from the source tree,
    prints the checker's `PASS` line, and exits 0. The recipe this change
    writes logs `Building wheel from sdist` and the same `PASS` line. Then
    every smoke probe prints `FAIL …: the console script crashed (exit 1)`
    over `ImportError: cannot import name 'mermaid' from 'openspec_graph'`,
    and make exits 2.
  - `tests/test_ci_promotion.py:44` holds `SMOKE_PROBES`, and
    `smoke_problems` (`:162-179`) checks only that each is present in
    `release-tier` and in the release workflow. An extra `--expect` in
    `release-tier` alone passes it.
- **The licence-expression check.**
  - `tools/check_wheel_metadata.py:72-73`: `expected not in metadata`, over
    the whole decoded `METADATA`.
  - Two wheels built from scratch copies of this tree, checked by the
    worktree's unedited checker, each print `PASS 1 wheel(s) carry
    License-Expression: Apache-2.0 and 1 licence file(s)`, exit 0:
    - a copy with `license = "Apache-2.0"` deleted from `pyproject.toml` and
      the line `License-Expression: Apache-2.0` appended to its README. The
      header has no `License-Expression` line, and the body has one;
    - a copy declaring `license = "Apache-2.0 OR MIT"`, whose header reads
      `License-Expression: Apache-2.0 OR MIT`.
  - Each was checked against a `pyproject.toml` other than its own. Checked
    by its own copy's checker, the second prints `PASS 1 wheel(s) carry
    License-Expression: Apache-2.0 OR MIT …`, exit 0, which is correct, and
    the first prints `ERROR pyproject.toml declares no SPDX license
    expression`, exit 2.
  - With `setuptools==84.0.0`, a declared `apache-2.0 or mit` reaches the
    header as `License-Expression: Apache-2.0 OR MIT`. An isolated build
    under `setuptools>=77` refuses `license = {text = "Apache-2.0"}`,
    stopping at `configuration error:` with "`project.license` must be
    string".
- **`delta`.**
  - `openspec_graph/cli.py:606-671` is `cmd_delta`. Its tree check
    (`:613-615`) prints `_NO_SPEC_TREE` and returns 2 before the baseline
    is read at `:617`. An unreadable spec returns `_report_unreadable` at
    `:625`. It returns `1 if entries else 0` on the JSON path (`:651`) and 1
    after listing stale citations on the text path (`:671`).
  - `openspec_graph/delta.py:204` compares floors only when
    `baseline_floor is not None and live_floor is not None`.
  - `p_delta` (`:916-927`) declares `--baseline`, `--dialect` and `--format`,
    and no `--fail-on`.
  - Measured with the installed CLI:
    - an empty directory and an absent baseline print `no openspec/
      directory and no SpecKit specs/ tree; run ``planlint init`` first`,
      exit 2, and so does `tests/fixtures/action/no-tree`;
    - `delta --baseline <card> --fail-on ERROR` prints `planlint: error:
      unrecognized arguments: --fail-on ERROR`, exit 2, and `delta --fail-on
      ERROR` with no `--baseline` prints `planlint delta: error: the
      following arguments are required: --baseline`, exit 2;
    - a card saved from this tree by `detect --format json` gives `machinery
      unchanged since the baseline`, exit 0;
    - a scratch copy of the test fixture repository with `regression`
      renamed in its Makefile after the card was saved gives `1 stale
      citation(s)`, exit 1, and the same exit 1 from `--format json`;
    - a planted repository whose floor moved from 90 to 95 gives one stale
      `threshold` citation, exit 1; with the floor removed it prints
      `threshold changed: … -> None` and `nothing stale`, exit 0; with a
      directory where a spec file belongs it prints `ERROR cannot read spec
      openspec/changes/c2/specs/cap/spec.md: Is a directory`, exit 2.
  - The tests already pin most of it: `tests/test_delta.py`'s
    `test_delta_names_the_removed_make_target` (exit 1),
    `test_cli_delta_exits_zero_on_an_identical_baseline` (exit 0) and
    `test_cli_delta_without_a_spec_tree_is_a_usage_error` (exit 2).
    `tests/test_spec_read_errors.py`'s `PARSING_VERBS` leaves `delta` out.
  - `skills/planlint-spec-governance/references/exit-codes.md`:
    - `:9` defines exit 1 as findings at or above `--fail-on`, and `:12`
      reads "Exit 1 means findings, and only findings.";
    - `:18` names only `validate` and `waivers` for the no-spec-tree message;
    - `:46` names `validate`, `waivers` and `graph` for an unreadable spec;
    - `:67-78` is `delta`'s unusable-baseline entry;
    - `:119-123`, "The one exit-1 case that is not a finding", names
      `detect --diff` alone.
  - `add-delta-lint`'s `specs/delta-lint/spec.md`, DEC-DL-008: "That
    section becomes two cases and must be updated in the same change".
  - `skills/planlint-spec-governance/SKILL.md:79` defines exit 1 as findings
    at or above `--fail-on`, and `:85-90` names `validate`, `waivers` and
    `graph` for the no-spec-tree case.
  - `tests/test_skill_contract.py::test_exit_two_messages_match_the_documented_contract`
    is parametrised over `validate` and `waivers` only.
  - `.claude-plugin/plugin.json` and `marketplace.json` are generated from
    `__version__` and the skill's frontmatter `description` only
    (`tools/render_plugin_manifests.py`), so a body edit leaves them fresh.
- **The README.**
  - `README.md:41-52` is the quickstart block.
  - `planlint --help` lists `detect, init, new, validate, rules, graph,
    waivers, delta, report, witness`.
  - `grep -n -i -w "delta\|witness\|sarif"` over `README.md` finds rule-table
    rows and prose, and no CLI line for any of them.
  - `pyproject.toml:27` is `readme = "README.md"`.
  - `tests/test_adopter_urls.py` reads the README for install commands and
    `@v`/`rev:` tag tokens.
  - `tests/test_skill_contract.py::test_skill_tables_cover_every_verb_the_cli_actually_has`
    holds `SKILL.md`'s verb tables to the parser. Nothing does that for the
    README.
  - `planlint witness --help` requires `--exit EXIT_CODE`, "the exit code
    the verifying command actually observed".
- **The stages.**
  - `python tools/stage_citations.py`, which is what the stage-citations
    target runs, ends `57 spec(s); 17 stage(s) cited; 12 on a verification
    line; 6 of those invoked by no scanned workflow: ci, coverage-tools,
    security, thresholds, validate, wheel-check`.
  - The equivalents are at `ci.yml:176` (`planlint --target . validate
    --fail-on ERROR`, the validate recipe at `Makefile:60`), `ci.yml:403`
    (`python tools/check_no_hardcoded_thresholds.py`, the thresholds recipe
    at `Makefile:89`) and `ci.yml:214,217` (the wheel-check recipe at
    `Makefile:104-105`).
  - `Makefile:79` composes `ci` from `test lint validate`. The `test` job
    (`ci.yml:61-68`) runs lint, typecheck and test as separate steps, and
    `self-validate` runs validate.
  - `Makefile:28-32` puts the `tools/` floor checks inside `make test`, and
    `:42-43` repeats them for `coverage-tools`.
    `tests/test_ci_makefile.py::test_test_and_coverage_tools_read_the_one_report_scoped`
    pins both recipes.
  - `tools/check_secrets.py` runs a `gitleaks` binary found on PATH, or a
    fallback scanner. The `security` job (`ci.yml:405-411`) runs
    `gitleaks/gitleaks-action` over full history.
  - `tools/_common.py:530` is `_RUN_KEY`, which matches a `run:` key at the
    start of a line. Fed a job whose second step is
    `- {name: inline, run: python tools/check_no_hardcoded_thresholds.py}`,
    `run_scripts` returns the first step's script alone.
  - GNU Make 4.3 exits 2 when a recipe line exits 1, printing `Error 1`.
  - `add-witness-ci-artifacts` R-WCA-26
    (`specs/witness-ci-artifacts/spec.md:223-226`) requires the same three
    substitutions, plus the security target in `security`. Its R-WCA-28 and
    DEC-WCA-016 put `ci` and `pre-pr` in a new `ladder` job. That package is
    open, with no milestone done.
  - `docs/peer-review-2026-10.md:355-367` recommended the same three
    substitutions.
- **What the siblings change.** Counted by the same parser over the packages
  `lean-production-tree` keeps, the stages on a verification line are `ci`,
  `docs-check`, `e2e-live`, `pre-pr`, `test` and `wheel-check`. Every package
  that cites `coverage-tools`, `security`, `thresholds` or `validate` on one
  is a package that change deletes.
- **The other open siblings.** `close-gate-script-gaps` widens the threshold
  guard over the Makefile, every workflow and `.pre-commit-config.yaml`, and
  edits `README.md`'s gates table, `docs/hooks.md` and `docs/aqa.md` beside
  this change. Its prototype guard, run over this change's revised recipe
  lines and its make-call `run:` lines, reports nothing.
  `raise-coding-standards` adds an empty `openspec_graph/py.typed`. Built
  through the sdist with that file in place, the sdist lists
  `planlint-0.3.0/openspec_graph/py.typed`, and the wheel built from it lists
  `openspec_graph/py.typed`.
- **The tiers.**
  - `.pre-commit-config.yaml:11-47` calls the lint, typecheck, security,
    validate, docs-check and thresholds targets, and no test target. The
    lint and typecheck hooks carry `types: [python]` (`:16`, `:23`).
  - `ci.yml:9-11`: `push` is filtered to `branches: [main, qa, dev]`, and
    `pull_request` is not filtered.
    `tests/test_ci_promotion.py::test_ci_push_branches_match_the_promotion_config`
    holds that list equal to `[tool.specgraph.promotion]`
    (`pyproject.toml:256-259`).
  - `ci.yml:461-502`: at `bfbc124`, `release-tier` is the `ci.yml` job that
    runs `make pre-pr`. It runs when the promotion job decides it should, on
    pull requests into and pushes to the candidate and production branches.
  - The claims are at `docs/hooks.md:3-4` and `:16-18`, `docs/aqa.md:283`
    and `:287`, `README.md:358-359` and `.pre-commit-config.yaml:4-5`.
  - `prepare-release-0-4-0`'s `tasks.md` Milestone 1 rewrites
    `docs/aqa.md:287` to "Python 3.11–3.14". A scratch merge of that edit
    with this change's rewrite of the same paragraph stops on a conflict.
- **The release state.** `https://pypi.org/pypi/planlint/json` and
  `.../planlint/0.3.0/json` both answer 404. 0.3.0 is not yet published,
  and this package's pull request is held for the 0.3.0 promotion.

## What Changes

**The package lands in `dev` in one pull request, with its one amendment of
`prepare-release-0-4-0`, held until the 0.3.0 promotion is done. The
implementation follows as a GitHub draft pull request and merges into `dev`
before `prepare-release-0-4-0`'s release-prep pull request, so that it ships
in 0.4.0.** It changes the following.

- **`.github/workflows/ci.yml`.**
  - `self-validate`: the validate step calls the `validate` target through
    `make`.
  - `security`: the thresholds step calls the `thresholds` target. Its
    gitleaks step is unchanged.
  - `packaging`: the build-and-check pair becomes one step calling the
    `wheel-check` target.
  - The comments over `packaging` and `security` follow.
  - No job is added, renamed or removed. `release-tier`, the matrix and
    every other step are untouched.
- **`Makefile`**: `wheel-check`'s recipe and help text, after the wiring lands
  unchanged.
  - The recipe removes `dist/`, builds with `python -m build --outdir dist`
    (the sdist, then the wheel from it), runs `tools/check_wheel_metadata.py`,
    and runs `tools/smoke_wheel.py` on that wheel with exactly the `--expect`
    probes `release-tier` passes, which a new guard holds to `release-tier`'s
    step.
  - The target keeps its name and stays out of `ci` and `pre-pr`. No other
    target changes.
- **`tools/check_wheel_metadata.py`**: the licence-expression check reads
  one exact field in the header of `METADATA`, not a substring of the whole
  file, as defence in depth.
  - Its message, the classifier check, the licence-file checks, the exit-2
    cases and the `PASS` line are unchanged.
  - It reads no sdist (DEC-TRS-001).
  - `_declared_license` is not touched, because `prepare-release-0-4-0`
    rewords its docstring.
- **Tests.** New functions in `tests/test_wheel_metadata.py`,
  `tests/test_ci_makefile.py`, `tests/test_stage_citations.py` and
  `tests/test_skill_contract.py`, named in `tasks.md`. No existing test
  function, and no helper an existing test calls, changes.
- **`skills/planlint-spec-governance/references/exit-codes.md`**:
  - `delta` joins the no-spec-tree entry and the unreadable-spec entry;
  - an entry for `delta --fail-on` is added, with the parser line it draws
    with and without `--baseline`;
  - "The one exit-1 case that is not a finding" becomes "Exit-1 cases that
    are not findings", with `delta`'s stale-citation exit 1 beside
    `detect --diff`;
  - "Exit 1 means findings, and only findings" is reworded to point there;
  - the top table's exit-1 row names `delta`.
- **`skills/planlint-spec-governance/SKILL.md`**, body only: the exit-1 row
  and the no-spec-tree bullet name `delta`. Its frontmatter is untouched.
- **`README.md`**:
  - quickstart lines for `rules`, `delta`, `report`, `witness`,
    `validate --format json` and `validate --format sarif`. The `witness`
    line passes a captured `"$code"`, never a literal exit;
  - one sentence under the exit-code table pointing to the per-verb contract;
  - the AQA section's opening says what CI runs and gains a `wheel-check`
    row.
- **`docs/hooks.md`**: the opening paragraph and the pre-commit paragraph
  state what each tier runs. The CI table's `self-validate`, `packaging` and
  `security` cells name what those jobs run now, and the ladder names the
  `wheel-check` target.
- **`docs/aqa.md`**: the "Reproducing CI locally" comment and the paragraph
  after it, and one sentence after the Gates table on the `wheel-check`
  target.
- **`.pre-commit-config.yaml`**: its header comment only.
- **`CHANGELOG.md` `[Unreleased]`**: `### Changed — the release surface`.
- **`openspec/changes/prepare-release-0-4-0/`**, in this package's own pull
  request, each edit an insertion marked "(amended by
  `tighten-release-surface`)" (R-TRS-19, DEC-TRS-015):
  - `specs/release-0-4-0/spec.md`: R-RFR-2 and AC-RFR-20;
  - `proposal.md`: the bold "Pull request 2" sentence;
  - `tasks.md`: the "Pull request 2" summary bullet, the Milestone 5
    preconditions and the merge-hazard list.

## Non-Goals

- **No sdist reader, and no sdist install.** DEC-LM-008's wheels-only
  decision stands, consistent with what was measured: the wheel the release
  paths and now `packaging` check is built from the sdist. An sdist that
  cannot build fails the build step before any install could (DEC-TRS-001).
- **No edit to `release.yml`.** `harden-release-pipeline` pins the file
  whole against a golden copy (R-HRP-6, DEC-HRP-007), so any edit costs a
  golden-copy edit on that package's critical path. It already builds the
  wheel from the sdist, and the header-only check reaches it through the
  checker it already runs, with its text unchanged.
- **No edit to `release-tier`, and none to `tools/smoke_wheel.py` or to
  `smoke_problems`.** `release-tier` mirrors `release.yml` step for step,
  held by `test_release_and_ci_share_one_smoke_tool`. The smoke tool is
  called as it is, and the probe-set guard is a new function beside the old
  one.
- **No CLI change.** `delta`'s behaviour is documented, not altered. Giving
  it a `--fail-on`, or making a removed floor stale, would be a change to the
  verb's contract, and that needs a package of its own.
- **No `ci`, `coverage-tools` or `security` target called from CI, no
  `ladder` job, and no witness recording.** Each of those changes what a job
  checks or adds a job. They are `add-witness-ci-artifacts`' to make
  (DEC-TRS-005, DEC-TRS-007).
- **The `wheel-check` target stays out of `make pre-pr`.** Composing it there
  would change what the release tier and the release workflow's gate run by
  name (DEC-TRS-004).
- **No gate on the stage-citations report.** It stays a report (DEC-TRS-006).
- **No new script under `tools/`, no new dependency** (no `twine`), and no
  rename of `check_wheel_metadata.py`, `smoke_wheel.py` or the
  `wheel-check` target.
- **No narrowing of the legacy-classifier check, and no canonical-form
  comparison.** Each errs closed, and nothing observed asks for more
  (DEC-TRS-014).
- **No edit to `docs/architecture/c4.md`, `tools/AGENTS.md`, `llms.txt` or
  `docs/next-steps.md`.** Each statement those files make about these tools
  and verbs stays true. And `harden-release-pipeline` and
  `lean-production-tree` edit the same lines of the first three.
- **No version bump, and no edit to `SKILL.md`'s frontmatter.** The
  `.claude-plugin/` manifests stay as generated.
- **No edit to another package's text but R-TRS-19's.** That covers
  `add-witness-ci-artifacts`, whose R-WCA-26 overlaps this change
  (DEC-TRS-007), and `close-gate-script-gaps` and `raise-coding-standards`,
  whose shared sites DEC-TRS-011 names. `prepare-release-0-4-0` is amended
  at its release-prep ordering and its hazard list alone (DEC-TRS-015).
- **No real build inside the suite beyond the one it has.** A real build is
  network-bound and slow. The build from the sdist runs in the `packaging`
  job on every pull request, and on every push to the integration, candidate
  and production branches, and it is recorded at implementation
  (DEC-TRS-003).
- **No change to how a corrupt wheel is handled.** That is not in the
  finding.

## Affected Capabilities

- `release-surface`
