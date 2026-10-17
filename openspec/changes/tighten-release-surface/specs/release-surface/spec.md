# Spec: Release Surface

> **Change:** `tighten-release-surface`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

An adopter meets the release surface before any code: the wheel and the
sdist PyPI publishes, the README that is also the PyPI long description, and
the operating contract an agent follows. On `dev`, each of these says less,
or more, than the tree does.

The sdist reaches no check on a pull request into the integration branch.
The release workflow and `release-tier` build with `python -m build` and no
distribution flag, which makes the sdist and then the wheel from it. The
wheel they check and smoke is therefore built from the sdist they publish,
and an sdist missing its licence file yields a wheel the existing checker
fails. That is consistent with `migrate-license-metadata-pep639`'s
DEC-LM-008, which reads wheels only, and that decision stands. But
`packaging`, the packaging check every pull request runs, builds with the
wheel-only flag. Its wheel comes from the source tree and never from the
sdist, so an sdist defect surfaces only at `release-tier`, on the candidate
and production branches, or at the tag. The defect an sdist can carry
unseen is a missing module, not a missing licence. setuptools adds the
declared `license-files` back even when `MANIFEST.in` excludes them, while a
module excluded there is absent from the sdist and from every wheel built
from it. A directory holding a bare sdist beside a good wheel does pass the
checker. It arises only when the two are built separately, and no workflow
builds them that way.

The checker's licence-expression test is also looser than it reads, though
no workflow exposes it. It searches the whole `METADATA` for the expected
line, and the body of `METADATA` is the README. Checked against a
`pyproject.toml` other than its own, a wheel whose header lacks
`License-Expression` passes when its README carries the line, and so does a
header whose expression only begins with the declared one. No workflow
checks a wheel against another tree's declaration, and setuptools 77 and
later always write the canonical field into the header.

The operating contract leaves out `delta`. `delta` exits 1 on any stale
citation and has no `--fail-on`: passing one is a usage error and exits 2. It
also exits 2 with the short no-spec-tree message, before it reads its
baseline, and on an unreadable spec with the message the other parsing verbs
print. The per-verb reference covers only `delta`'s unusable-baseline exit 2.
It says that exit 1 means findings and only findings, above a section that
already names an exit-1 case that is not a finding. `SKILL.md` covers none
of this, and defines exit 1 only as "findings at or above `--fail-on`".
`add-delta-lint`'s DEC-DL-008 required that section to become two cases,
and the reference was never edited.

The README's quickstart leaves out verbs the parser declares, and the
`validate --format sarif` output the composite action and code scanning
consume.

Some stages are not called by the name specs cite. The stage-citations
report lists stages that a criterion's verification line cites and that no
workflow invokes by name. For some of them a CI job runs the target's exact
recipe inline. For the rest, nothing CI runs is equivalent. The
`wheel-check` target is in no job and no aggregate, and no document of the
gate ladder mentions it.

The tier documents overclaim. `docs/hooks.md` and `docs/aqa.md` say
pre-commit and CI enforce the same gate as `make pre-pr`. Pre-commit runs no
tests. CI runs on every pull request, and on every push to the integration,
candidate and production branches. At `bfbc124`, the job in `ci.yml` that
runs `make pre-pr` by name is `release-tier`, for the candidate and
production branches, and the release workflow's gate runs it at a tag. The
README's AQA section and the header comment of `.pre-commit-config.yaml`
repeat the claim.

**Evidence:** measured at `bfbc124` (`origin/dev`), 2026-10-16, and
re-measured on 2026-10-17 for the first and second adversarial reviews. Each
line number, command and output is in `proposal.md` and `tasks.md`, and none
is repeated here (C-TRS-5).

- **The build.**
  - `packaging` and the `wheel-check` recipe build with the wheel-only flag.
    `release-tier` and the release workflow build with none.
  - A scratch build of this tree logs `Building wheel from sdist`, and its
    sdist carries `LICENSE` at its top level.
  - A wheel built from an sdist stripped of `LICENSE` carries no licence
    file, and the current checker fails it.
  - A `MANIFEST.in` that excludes `LICENSE` leaves it in the sdist:
    setuptools reports that nothing matched the exclusion, then adds the
    licence file.
  - A `MANIFEST.in` that excludes a module passes today's recipe. The recipe
    this change writes fails on it, because every smoke probe of the wheel
    built from that sdist crashes on an `ImportError`.
  - The smoke guard holds a fixed probe tuple present in both release paths,
    so a probe added to one of them alone passes it.
  - DEC-LM-008 is revisited if an sdist-only defect is observed in the
    project. None has been; the module case is planted.
- **The licence-expression check.**
  - It is a substring search over the whole `METADATA`.
  - Two wheels built from scratch copies pass it when checked against this
    tree's declaration. One has no header field and a README body carrying
    the line. The other has a header expression longer than the declared
    one.
  - Checked in its own tree, the longer-expression wheel passes, and that is
    correct. setuptools 77 and later write the field into the header in
    canonical form, and refuse a declaration that is not a string.
- **`delta`.**
  - `cmd_delta` checks for a spec tree before it calls `_load_card`. It
    returns 1 whenever an entry exists, on both output paths, and reports an
    unreadable spec through `_report_unreadable`, as `validate`, `waivers`
    and `graph` do.
  - Its parser declares no `--fail-on`. With `--baseline` given, an extra
    `--fail-on` draws the unrecognised-argument line. Without it, the missing
    `--baseline` is reported first. Both exit 2.
  - A floor is compared only when the baseline and the tree both carry one.
    A floor removed outright is a machinery change, and exits 0.
  - The no-tree exit 2, the unrecognised-argument exit 2, the unreadable-spec
    exit 2, the exit 0 on an identical card and the exit 1 on a removed make
    target were each reproduced with the installed CLI.
- **The README.**
  - The quickstart block shows a subset of the verbs that `planlint --help`
    lists.
  - No test holds the README to the parser, as
    `test_skill_tables_cover_every_verb_the_cli_actually_has` holds
    `SKILL.md`.
- **The stages.**
  - `self-validate`, `security` and `packaging` run the validate,
    thresholds and wheel-check recipes inline.
  - `ci` composes test, lint and validate, which CI runs as separate steps
    and jobs.
  - `make test`'s recipe already checks the `tools/` floors that
    `coverage-tools` re-reads.
  - The security target runs `tools/check_secrets.py`, while the `security`
    job runs `gitleaks/gitleaks-action`.
  - The workflow reader returns no `run:` script for a step written as a
    YAML flow mapping.
  - `add-witness-ci-artifacts`, open and unimplemented, requires the same
    substitutions and more.
- **The tiers.**
  - `.pre-commit-config.yaml` calls no test target, and its lint and
    typecheck hooks carry a Python file filter.
  - `ci.yml`'s `push` trigger lists the branches `[tool.specgraph.promotion]`
    names, and its `pull_request` trigger has no filter.
  - At `bfbc124`, `release-tier` runs `make pre-pr` for the candidate and
    production branches.

---

## Requirements

### The build in `packaging`, and the wheel checker

- R-TRS-4: The `wheel-check` target's recipe MUST, in order:
  - remove `dist/`;
  - build with `python -m build --outdir dist`, which makes the sdist and
    then a wheel from that sdist;
  - run `tools/check_wheel_metadata.py dist`;
  - run `tools/smoke_wheel.py dist` with exactly the `--expect` probes
    `release-tier`'s smoke step passes, and no other flag.

  A guard MUST hold the recipe's `--expect` set equal to the set
  `release-tier`'s smoke step passes.
  - It reads both from their files, and restates neither.
  - It names each probe that one side carries and the other lacks, with the
    side that lacks it.
  - It MUST be a new test function, because `smoke_problems` stays as it is
    (C-TRS-7).

  The target MUST keep its name. Its help text MUST NOT begin "Report". It
  MUST NOT be reachable from `ci` or `pre-pr`.
- R-TRS-5: `.github/workflows/release.yml` and `release-tier`'s steps MUST NOT
  be edited. Both already build with no distribution flag, check the wheel
  built from the sdist they publish, and smoke it with the same tool. Their
  behaviour MUST stay as it is, except that the checker they call reads the
  licence expression from the header of `METADATA` (R-TRS-18).
- R-TRS-18: `tools/check_wheel_metadata.py`'s licence-expression check MUST
  read only the header block of each wheel's `METADATA`: the lines before the
  first empty line, or every line when there is none. This is defence in
  depth, not a fix for a case a workflow produces (DEC-TRS-014).
  - It MUST pass a wheel only when a header line reads exactly
    `License-Expression: ` followed by the declared expression, trailing
    whitespace aside.
  - A body line carrying that text MUST NOT satisfy it, and neither MAY a
    header line whose expression is longer than the declared one.
  - Its failure message MUST stay byte-identical.
  - The legacy-classifier check, the licence-file checks, `_declared_license`,
    the exit-2 cases and the `PASS` line MUST be unchanged.
  - The checker MUST read no sdist (DEC-TRS-001).

### Calling the stages by name

- R-TRS-6: In `.github/workflows/ci.yml`, each of these jobs MUST call one
  target through `make`, and MUST then carry none of the commands that
  target replaced:
  - `self-validate` calls the `validate` target in place of its inline
    validate command;
  - `security` calls the `thresholds` target in place of its inline guard
    command;
  - `packaging` calls the `wheel-check` target in place of its inline
    build-and-check pair.

  At the commit that wires them, each target's whole recipe MUST be the
  command or commands its job ran inline, so the substitution changes
  nothing any job checks. R-TRS-4's extension MUST land in a later commit.
- R-TRS-7: This change MUST NOT call the `ci`, `coverage-tools` or `security`
  target from any job:
  - the `test` job keeps running the parts of `ci` as separate steps;
  - `make test` keeps checking the floors `coverage-tools` re-reads;
  - the `security` job keeps gitleaks-action, and this change gives it no
    step for the security target.

  No job MAY be added, renamed or removed by this change. `release-tier` and
  the composition of `ci` and `pre-pr` MUST be unchanged by it.
- R-TRS-8: A guard MUST hold R-TRS-6.
  - It MUST read each job's `run:` scripts through the workflow reader
    `tools/stage_citations.py` uses, and find the job's target in command
    position there.
  - Each replaced command MUST be named by a stem and matched as a
    substring. For `packaging` the stems are `python -m build` and the
    checker call `python tools/check_wheel_metadata.py dist`, the ones
    `tasks.md` names. For `self-validate` and `security` the stem is the
    whole command. R-TRS-4's recipe, which builds with
    `python -m build --outdir dist`, still carries its stem, so the guard
    stays green after it lands.
  - It MUST look for each stem in every code line of the job's block, with
    comments stripped by the workflow guards' comment stripper, and not in
    the `run:` scripts alone. A step written as a YAML flow mapping is
    invisible to the `run:` reader, and a replaced command in one MUST still
    be named.
  - Each stem MUST appear in a line of the target's recipe.
  - A planted job that runs one of those commands inline, whether beside its
    target, in place of it or in a flow-mapping step, MUST be named with the
    job and the command.
  - The guard MUST NOT assert that every stage a spec cites is run by a
    workflow (DEC-TRS-006).
- R-TRS-9: `docs/hooks.md`'s CI table MUST name what each of these jobs runs
  once this change lands:
  - `self-validate`: the `validate` target;
  - `security`: gitleaks-action and the `thresholds` target;
  - `packaging`: the `wheel-check` target, with what it builds, checks and
    smokes.

  The ladder in its opening paragraph MUST name the `wheel-check` target as
  run by `packaging` on every pull request, and on every push to the
  integration, candidate and production branches, and as outside
  `make pre-pr`. `docs/aqa.md` MUST say the same once, outside its Gates
  table's "all of the above" row. `README.md`'s AQA table MUST gain a
  `wheel-check` row.

### `delta`'s exit codes

- R-TRS-10: `skills/planlint-spec-governance/references/exit-codes.md` MUST
  state each of the following:
  - the no-spec-tree entry names `delta` beside `validate` and `waivers` as
    printing the short message exactly, and says that `delta` looks for the
    tree before it reads `--baseline`;
  - the unreadable-spec entry names `delta` beside `validate`, `waivers` and
    `graph`, with its message unchanged;
  - an entry of its own says `delta` takes no `--fail-on`, so passing one is
    a usage error that exits 2 before anything is compared. It says which
    parser line comes first, with and without `--baseline`;
  - the section on the exit-1 case that is not a finding is retitled for
    more than one case. It keeps `detect --diff` as written, and adds
    `delta`: it exits 1 when at least one spec cites machinery that the
    baseline card carried and the repository no longer carries, whatever the
    kind: a make target removed, an invariant or ADR no longer declared, a
    coverage floor whose value changed. There is no threshold. It exits 0
    when nothing went stale, even when the machinery changed, and a citation
    already broken at the baseline never makes it exit 1;
  - the sentence under the top table no longer says that exit 1 means
    findings and only findings, and points to that section;
  - the top table's exit-1 row names `delta`'s case.

  The unusable-baseline entry MUST stay as written. A floor removed outright
  is a machinery change and exits 0, because `delta` compares a floor only
  when the baseline and the tree both carry one. The reference MUST describe
  that as it is, and this change MUST NOT alter it (C-TRS-1).
- R-TRS-11: `SKILL.md`'s "Exit codes" section MUST carry the facts an agent
  acts on:
  - its exit-1 row names `delta`'s stale-citation case and says it has no
    `--fail-on`;
  - its no-spec-tree bullet names `delta` beside `validate` and `waivers`.

  No line of its frontmatter MAY change. The `.claude-plugin/` manifests
  MUST stay fresh without being regenerated.
- R-TRS-12: A guard MUST pin R-TRS-10 and R-TRS-11 against the CLI:
  - run against an empty target with an absent baseline, `delta` exits 2,
    and its stderr is exactly the short message the reference quotes;
  - run against a target holding an unreadable spec, with a readable
    baseline, `delta` exits 2, prints the reference's unreadable-spec line
    and prints no traceback;
  - with a readable `--baseline`, `delta --fail-on ERROR` exits 2, naming
    the unrecognised argument;
  - both contract files carry each `delta` entry, and the reference no
    longer carries the "only findings" sentence. A single reader checks
    this, and its planted counterpart names each entry it does not find.

  `delta`'s exit 1 and exit 0 stay pinned by the existing delta tests.

### The README

- R-TRS-13: `README.md`'s quickstart block MUST show every verb the CLI's
  parser declares, and a `validate --format sarif` line.
  - The new lines carry comments. The `delta` and `report` lines state their
    exit behaviour.
  - The `witness` line MUST pass `--exit "$code"`, the exit a stage step
    captured, and never a literal exit code. Its comment states that the
    line belongs to the CI job that ran the stage.
  - No new line MAY carry an install command or a version tag.
  - A sentence under the README's exit-code table MUST name `delta`'s and
    `report`'s exceptions and point to the per-verb reference.
- R-TRS-14: A guard MUST hold the quickstart to the parser's verb set in both
  directions, and to the sarif line. It MUST read through a single reader,
  whose planted counterpart names a verb missing from the quickstart and a
  verb the parser does not declare.

### The tier documents

- R-TRS-15: `docs/hooks.md`'s opening paragraph and its pre-commit paragraph
  MUST state what each tier runs and nothing more:
  - the commit-time hooks run the security, validate, docs-check and
    thresholds targets whatever is staged, and the lint and typecheck
    targets when a Python file is staged. They run no tests and no
    coverage;
  - CI runs on every pull request, and on every push to the integration,
    candidate and production branches that `[tool.specgraph.promotion]`
    names, whatever the hooks did;
  - `release-tier` and the release workflow's gate run `make pre-pr` by
    name.

  No tier sentence this change writes MAY claim that a job is the only one
  to run a target, or that a target runs nowhere else. Neither paragraph MAY
  say that pre-commit or CI enforces the same gate as `make pre-pr`, or that
  a hook keeps a commit from bypassing CI. `.pre-commit-config.yaml`'s
  header comment MUST be reworded the same way, with its hooks unchanged.
- R-TRS-16: `docs/aqa.md`'s "Reproducing CI locally" MUST NOT call
  `make pre-pr` "the exact bar CI enforces". Its comment on that line says
  the release tier runs it by name. Its next paragraph MUST say, under
  R-TRS-15's rule against exclusive claims:
  - which parts of the ladder CI runs as separate jobs and steps on every
    pull request, and on every push to the integration, candidate and
    production branches;
  - that CI's `security` job scans with gitleaks-action over the full
    history, a different tool from the security target's scanner;
  - which jobs it adds.

  The paragraph's Python version range MUST be the token in force when the
  two edits meet. `prepare-release-0-4-0` edits the same lines, and the two
  edits conflict textually in either merge order. The resolution keeps this
  change's sentence with that package's range token (DEC-TRS-010).
  `README.md`'s AQA section MUST NOT call `make pre-pr` the same bar CI
  enforces.

### Release notes

- R-TRS-17: `CHANGELOG.md`'s `[Unreleased]` section MUST gain
  `### Changed — the release surface` beside any group a sibling wrote,
  with an entry led by **`tighten-release-surface`**. The entry MUST name:
  - the wheel built from the sdist, checked and smoked, in `packaging` on
    every pull request;
  - the licence-expression check confined to the header;
  - the stages now called by name;
  - `delta`'s contract entries;
  - the README's verbs;
  - the tier wording.

  No released section MAY change.

### The sibling amendment

- R-TRS-19: `prepare-release-0-4-0`'s record MUST be amended in this package
  at these sites and nowhere else. Each edit is an insertion, marked
  "(amended by `tighten-release-surface`)":
  - R-RFR-2 gains one sentence: its release-prep pull request merges only
    after this change's implementation has merged, or after the
    maintainer's decision to defer this change to a later release is
    recorded in that package's `tasks.md`;
  - AC-RFR-20 gains one bullet for the same fact, checked before the
    release-prep pull request opens;
  - that package's proposal, after its bold "Pull request 2" sentence,
    gains the same condition;
  - its `tasks.md` ordering summary, the "Pull request 2" bullet, gains it
    too;
  - its Milestone 5 preconditions gain the matching bullet, with the
    commands that show the merge. One finds the retitled exit-1 heading in
    the per-verb reference. The other finds this change's
    `### Changed — the release surface` group in `CHANGELOG.md`;
  - its merge-hazard list gains the `docs/aqa.md` conflict of R-TRS-16 and
    its resolution.

  No ID of that package MAY be added, removed or renumbered, and no other
  line of it MAY change. It MUST stay clean under the gate (DEC-TRS-015).

### Constraints

- C-TRS-1: No file under `openspec_graph/` MAY change: the CLI's verbs,
  flags, messages and exit codes stay as they are. These MUST also be
  unchanged:
  - the `RULES` tuple, the README rules table and
    `tests/baseline_rules.json`;
  - every golden hash;
  - `[project] dependencies`, and every extra's requirements.
- C-TRS-2: None of these MAY be edited: `release.yml`, the composite action,
  `templates/`, `tools/smoke_wheel.py`, and the release workflow's golden copy
  if one exists. No script MAY be added under `tools/`.
  `tools/check_no_hardcoded_thresholds.py` MUST NOT be edited, and MUST stay
  quiet on every line this change adds to the Makefile or a workflow.
- C-TRS-3: There MUST be no version bump and no edit to `SKILL.md`'s
  frontmatter. `.claude-plugin/plugin.json` and `marketplace.json` MUST be
  byte-identical to the base.
- C-TRS-4: No other change package's text MAY be edited, but for R-TRS-19's
  amendment of `prepare-release-0-4-0`.
- C-TRS-5: This spec pins no count and no line number. Every measurement is
  in `tasks.md`, dated with its commit and naming its command.
- C-TRS-6: Prose this change adds to a shipped document MUST name no change
  package. It MUST also name no path that `lean-production-tree` deletes.
- C-TRS-7: Every existing test that another package's verification line
  cites MUST keep its name and pass. No existing test function's name or body
  MAY change, and neither MAY a helper an existing test calls,
  `smoke_problems` among them. The new guards are new functions.

---

## Decisions

- **DEC-TRS-001** (rewritten after the first adversarial review, HIGH-1;
  amended after the second, LOW-7)**:** `migrate-license-metadata-pep639`'s
  DEC-LM-008 stands, and the licence gate reads wheels only. The gap is that
  `packaging` builds its wheel without the sdist.
  - **What DEC-LM-008 says.** Both artifacts carry the same declaration
    through the same code path, and the wheel is what a user receives. The
    decision is revisited if an sdist-only defect is ever observed, and none
    has been. Nothing below adds a reason to it. What follows is this
    package's own reading, which is consistent with it.
  - **Why the wheel already covers the sdist's licence where both are
    built.** `python -m build` with no distribution flag makes the sdist and
    then the wheel from it. setuptools regenerates the wheel's metadata from
    the sdist's own `pyproject.toml`. An sdist missing `LICENSE` therefore
    yields a wheel with no licence file, and the existing checker fails it:
    reproduced, as `tasks.md` records. The release workflow and
    `release-tier` build that way.
  - **The licence cannot be lost through `MANIFEST.in`.** setuptools adds
    the declared `license-files` to the sdist even when `MANIFEST.in`
    excludes them, so the stripped sdist above had to be repacked by hand.
  - **The real gap.** `packaging`, the packaging check on every pull
    request, builds with the wheel-only flag. Its wheel comes from the source
    tree, never from the sdist, so an sdist defect reaches no check until a
    change is promoted. DEC-TRS-003's recipe closes that.
  - **What the gap lets through, measured.** The second review's
    differential is the main evidence for the recipe. With `exclude
    openspec_graph/mermaid.py` in `MANIFEST.in`, today's recipe builds the
    wheel from the source tree, its checker passes, and the target exits 0.
    The recipe this change writes builds the sdist without that module and
    the wheel from that sdist. Every smoke probe then crashes on an
    `ImportError` for the module, and the target exits 2. The licence check
    passes both times, so this is the smoke's catch, not the checker's.
  - **The bare-sdist directory.** A good wheel beside an sdist with no
    licence passes the checker, but that directory arises only when the two
    are built separately. No workflow builds them so. The first draft of this
    package took it for the gap.
  - **No sdist install either.** The wheel `packaging` smokes is built from
    the sdist, so an sdist that cannot build already fails the job at its
    build step. A pip install of the sdist would repeat that build with
    another frontend and check nothing more.
  - **No new script, and the smoke tool unedited.** These stay unchanged,
    whichever package lands first:
    - the runnable-script list in `tests/test_gate_scripts.py`;
    - `tools/AGENTS.md`, which has no room under its nested-file line bound
      once `harden-release-pipeline`'s edit lands;
    - the script counts that package's R-HRP-19 requires to be true in
      `tools/AGENTS.md` and `docs/architecture/c4.md`;
    - that package's "smoke step unchanged" (R-HRP-9), which now holds in
      text and in behaviour.
  - **Withdrawn.** R-TRS-1 to R-TRS-3, AC-TRS-1, AC-TRS-2, AC-TRS-4,
    AC-TRS-5 and DEC-TRS-002 of the first draft are withdrawn with the sdist
    reader and the sdist smoke, and their numbers are not reused.

  Rejected:
  - An sdist reader in the checker, or a new `tools/check_sdist.py`: a
    second archive reader for a case no evidence points at, against a
    decision whose revisit trigger has not fired.
  - A `--sdist` mode for the smoke tool: it repeats the build `packaging`
    already makes from the sdist.
  - An sdist step in `release.yml`: the golden-copy cost of R-HRP-6 and
    DEC-HRP-007, for a check the wheel already makes.
  - `twine check`: a new dependency, which checks that metadata renders and
    not that it states the declared licence.

- **DEC-TRS-003** (amended after the first adversarial review, HIGH-1 and
  LOW-6, and the second, MEDIUM-1 and LOW-7)**:** every pull request builds
  the sdist and then the wheel from it, and checks and smokes that wheel.
  - **The build.** `python -m build` with no distribution flag builds the
    sdist and then a wheel from it: the frontend's help text says so, and
    the scratch build logged it. Dropping the wheel-only flag from the
    recipe makes a build from the sdist part of every `packaging` run, and
    makes `packaging`'s wheel the one `release-tier` and the release
    workflow build. The checker then reads a wheel built from the sdist on
    every pull request, with no new reader.
  - **The smoke, and what it catches.** The recipe then runs the smoke tool
    on that wheel with the probes `release-tier` passes. A wheel that builds
    from the sdist but does not import, run, or fail a failing tree goes red
    on the pull request, not on the candidate branch. The module the
    differential of DEC-TRS-001 drops from the sdist is that case. Every
    probe fails on it here, and today's recipe passes it.
  - **One probe set, held by a guard.** The recipe restates
    `release-tier`'s `--expect` probes, and nothing tied the copy to its
    source. `smoke_problems` checks that a fixed probe tuple is present in
    both release paths, so a probe added to `release-tier` alone passes it.
    - A new test reads the `--expect` set from `release-tier`'s smoke step,
      through the job-block reader and its code lines, and asserts that the
      recipe's smoke line carries exactly that set.
    - It is a new function because C-TRS-7 freezes `smoke_problems`.
    - The second review's drift case is planted and named: one more
      `--expect` in `release-tier` only.
    - Equality runs both ways, so a probe the recipe gains alone is named
      too.
  - **The smoke validates this tree, and that is accepted.** The smoke's
    default probes run `detect` and `validate --fail-on ERROR` on `.`, so a
    spec-tree ERROR turns `packaging` red as well as `self-validate`.
    - The release workflow and `release-tier` build and smoke the same real
      tree with the same probes, and one probe set is the point.
    - A spec-tree ERROR is already red in `self-validate`, so the second
      red hides nothing.
    - Pointing the smoke at a fixture instead would make `packaging`'s
      probes differ from the release paths'.
  - **`dist/` is removed first**, so a wheel from an earlier local build of
    another version never sits beside this one. The checker would read both,
    and the smoke's exactly-one rule would refuse to run.
  - **Not in the suite.** A real build is network-bound and slow. The suite
    keeps `test_the_real_wheel_passes_the_gate` as it is. The real build from
    the sdist runs in `packaging` on every pull request, and on every push to
    the integration, candidate and production branches. Its first hosted run
    and a local run of the target are recorded in `tasks.md`.

- **DEC-TRS-004:** the `wheel-check` target stays outside `make pre-pr` and
  keeps its name.
  - **Outside the aggregate.** `make pre-pr` is what `release-tier` and the
    release workflow's gate run by name. Composing the target into it would
    change what both of them check, and how long they take. Both already
    build, check and smoke the artifacts in steps of their own.
  - **The name.** Specs cite the target, and renaming a target so that a
    citation resolves is out of bounds under `SKILL.md`.
  - **The help text.** It must not begin "Report". If it did, the report
    rules (R-RDS-14) would treat the target as a report, and it is a gate.

- **DEC-TRS-005:** a stage becomes a `make` call where the job's inline
  commands are the target's whole recipe, and nowhere else.
  - **Called by name.**
    - The `validate` target from `self-validate`: the recipe is the job's
      validate command.
    - The `thresholds` target from `security`: the recipe is the job's
      guard command.
    - The `wheel-check` target from `packaging`: the recipe is the job's
      build-and-check pair.

    `packaging`'s new build, check and smoke (R-TRS-4) land in a later commit
    than the wiring, so a regression can be attributed to one or the other.
  - **`ci` stays as its parts.** It is an aggregate of test, lint and
    validate. The `test` job runs lint, typecheck and the suite as separate
    steps on every leg, and `self-validate` runs validate. Calling `ci` in
    the `test` job would add validate to every leg, move lint after the
    suite and change where a red step stops the job. Each of those changes
    what the job checks.
  - **`coverage-tools` stays as it is.** Its floor checks are already in
    `make test`'s recipe on every leg, and
    `test_test_and_coverage_tools_read_the_one_report_scoped` pins both
    recipes. There is no inline command to replace. Calling it beside
    `make test` would repeat a check only to be counted: machinery bent to
    satisfy a citation, which `SKILL.md` forbids. The `make pre-pr` that
    `release-tier` runs reaches it by name, as a prerequisite.
  - **`security` stays as it is.** The target runs `tools/check_secrets.py`,
    which uses a `gitleaks` binary on PATH or falls back to a pattern scan.
    The job runs gitleaks-action over full history instead. Calling the
    target there would add the fallback scan, or a second gitleaks run, to
    the job.
  - **What "equivalent" means here.** The same commands, and the same
    verdict. When a command fails, the step's exit code becomes make's 2, and
    make's `Error` line carries the command's own code: measured with GNU
    Make 4.3. Nothing reads a step's exit code today. `ci-ok` reads job
    results.
  - **Not decided by today's counts.** The siblings move the citations:
    once `lean-production-tree` lands, `coverage-tools`, `security`,
    `thresholds` and `validate` leave every verification line, as measured
    in `tasks.md`. The choice rests on equivalence, which no sibling
    changes.

- **DEC-TRS-006** (amended after the first adversarial review, LOW-1, and
  the second, LOW-2)**:** the guard pins the wiring, not the report.
  - **The report stays a report.** `tools/stage_citations.py` is a report
    that exits 0 whatever it counts. `docs/hooks.md`'s reports section says
    a report becomes a gate only through a package of its own, after a
    quarter of an empty report.
  - **Why not test the report's headline.** A test that every
    verification-line stage is run by a workflow would make the report's
    headline a gate by the back door. It would also go red or green as
    sibling packages land and leave, on facts this package does not own.
  - **What the guard checks instead.** It asserts the wirings of R-TRS-6,
    and that each replaced command is in its target's recipe. It says
    nothing about which stages specs cite. A new test in
    `tests/test_stage_citations.py` asserts that the report's reader credits
    `ci.yml` with the stages this change wired. That is the report read for
    what this change did, not held to a total.
  - **Code lines for the replaced commands.** The `run:` reader takes plain
    and block `run:` keys, and a step written as a flow mapping is invisible
    to it. Measured, a job whose second step is a flow mapping running the
    thresholds command inline gives that reader the first step's make call
    alone. A guard that looked for replaced commands only there would pass
    that job. So the target is found in the `run:` scripts, where command
    position is defined, and the replaced commands in every code line of
    the job, where a step's shape cannot hide one.
  - **Stems, matched as substrings.** A replaced command is named by its
    stem, so the guard reads the same before and after R-TRS-4's recipe
    change. The recipe's `python -m build --outdir dist` carries the
    `python -m build` stem, and a job line still carrying the wheel-only
    build is still named.
  - **Who proposes the stage-level check.** `add-witness-ci-artifacts`'
    R-WCA-30, for witness mode's own reasons.

- **DEC-TRS-007** (amended after the first adversarial review,
  MEDIUM-2)**:** this change lands the equivalent subset of
  `add-witness-ci-artifacts`' R-WCA-26, and leaves the rest to that package.
  - **What R-WCA-26 asks.** The same substitutions, plus a step in
    `security` for the security target.
  - **What R-WCA-27 to R-WCA-31 add.** Witness recorders on each job, a
    `ladder` job running the `ci` and `pre-pr` aggregates, a `witness-gate`
    job, and the CI-table rows for them.
  - **This change takes only the substitutions** that change no check. The
    security step would add a scan to a job. The `ladder` job is where
    R-WCA-28 puts `ci`, and where DEC-WCA-006 records `coverage-tools`. Both
    stay that package's. Its text is not edited (C-TRS-4).
  - **If this change lands first:**
    - the replacements its Milestone 8 shares with this change are already
      true;
    - its "the commands behind those names are the ones the jobs run today"
      is read at its own implementation, and still holds;
    - the step form its recorders use (`set +e`, then the `make` call, then
      the captured code) still calls the target in command position, so this
      change's guard passes it;
    - its `packaging` recorder records the `wheel-check` target this change
      extended.
  - **If it lands first:** this change's Milestone 1 reduces to confirming
    the substitutions and adding the guard.
  - **Either order, the tier sentences.** That package's `ladder` job runs
    `make pre-pr` and the `ci` aggregate by name (R-WCA-28, DEC-WCA-016), and
    its `security` job gains the security target (R-WCA-26). So the tier
    sentences this change writes say which jobs run `make pre-pr` by name at
    this change's merge, and never that no other job does (R-TRS-15).
    Whichever of the two packages lands second re-reads, and brings up to
    date:
    - `docs/hooks.md`'s opening paragraph (R-TRS-15, DEC-TRS-010);
    - the `docs/aqa.md` comment on the `make pre-pr` line, and the paragraph
      after it (R-TRS-16);
    - the opening of the README's AQA section;
    - the shared CI-table cells.

    Each then names the `ladder` job and the `security` job's step for the
    security target where it says what runs.
  - **The shared CI-table cells.** Both packages edit the same
    `docs/hooks.md` cells. The second to land keeps both the target and the
    witness recording.

- **DEC-TRS-008** (amended after the first adversarial review, MEDIUM-5, and
  the second, LOW-1)**:** the contract wording for `delta`, written into the
  files as follows. Each guarded phrase is what R-TRS-12's reader looks for.
  The wording counts nothing, so a verb added to a list later does not stale
  a sentence.
  - **`exit-codes.md`, the top table's exit-1 row.** `The command ran and
    reported findings at or above --fail-on; for delta, which has no
    --fail-on, at least one stale citation.` The flag names stay in
    backticks, as the file writes them.
  - **`exit-codes.md`, the sentence under the table.** "Exit 1 means
    findings, and only findings." becomes "Exit 1 means the command ran and
    reached a verdict: findings, or the drift or stale citations reported by
    the verbs under *Exit-1 cases that are not findings*." The sentences on
    exit 2 after it are unchanged.
  - **`exit-codes.md`, the no-spec-tree entry.** Its heading becomes
    "**`validate`, `waivers` and `delta`, no spec tree.** Each prints
    exactly:", and the quoted message is unchanged. After it comes: "`delta`
    looks for the tree before it reads `--baseline`, so this message is
    the one you see even when the baseline is missing too."
  - **`exit-codes.md`, the unreadable-spec entry.** Its heading becomes
    "**`validate`, `waivers`, `graph` or `delta`, unreadable spec.**". Its
    message and its paragraph are unchanged.
  - **`exit-codes.md`, a new exit-2 entry beside the unusable-baseline
    one.** "**`delta --fail-on`.** `delta` takes no `--fail-on`. Passing one
    is a usage error that exits 2 before anything is compared. With
    `--baseline` given, the parser prints `planlint: error: unrecognized
    arguments: --fail-on <value>`. Without `--baseline`, it reports the
    missing flag first: `planlint delta: error: the following arguments are
    required: --baseline`."
  - **`exit-codes.md`, the exit-1 section.** Its heading, "The one exit-1
    case that is not a finding", becomes "Exit-1 cases that are not
    findings". Its `detect --diff` paragraph stays as written. A `delta`
    paragraph follows it, saying:
    - `delta` exits 1 when at least one spec cites machinery that the
      baseline card carried and the repository no longer carries: a make
      target removed, an invariant or ADR no longer declared, a coverage
      floor whose value changed;
    - a single stale citation of any kind is enough, and there is no
      severity to filter and no `--fail-on` to set;
    - it exits 0 when nothing went stale, and prints the machinery diff even
      then. A floor removed outright appears in that diff and is not a stale
      citation, because `delta` compares a floor only when the baseline and
      the tree both carry one;
    - a citation that was already broken at the baseline is `validate`'s
      finding, and never makes `delta` exit 1;
    - a stale citation is not a rule finding, and it never appears in
      `validate`'s counts. Treat it as one anyway: list it verbatim, then
      repair the citation or hand the list back.
  - **`SKILL.md`, the exit-1 row.** "Findings at or above `--fail-on`; for
    `delta`, which has no `--fail-on`, any stale citation". Its "What to do"
    cell is unchanged.
  - **`SKILL.md`, the no-spec-tree bullet.** "`validate`, `waivers` and
    `delta` print …". Its "In all three cases" becomes "In each of these
    cases".
  - **Why this wording.**
    - "No threshold" is what an agent needs, because the habitual reading of
      exit 1 in both files is "at or above `--fail-on`".
    - The `--fail-on` entry is there because an agent that appends the flag
      out of habit gets exit 2, and could misread it as a failure about the
      specs. It names both parser lines because which one appears depends on
      whether `--baseline` was given, and both were measured.
    - The baseline-ordering sentence records a measured precedence that a
      reader with no tree and no card would otherwise guess at.
    - **One section for every non-finding exit 1.** `add-delta-lint`'s
      DEC-DL-008 required this section to become two cases when `delta`
      shipped, and the edit never landed. A second section beside it would
      leave "the one exit-1 case" false. "Only findings" above it was
      already false for `detect --diff`.
    - **The unreadable spec.** `cmd_delta` reports one through
      `_report_unreadable`, as the three verbs the entry names do. An entry
      that names three verbs reads as if `delta` behaved otherwise.
    - **The removed floor, recorded and not changed.** Whether removing a
      floor should make a citation stale is a question about the verb's
      contract, and C-TRS-1 leaves the CLI alone. The reference says what the
      verb does, so an agent that sees exit 0 after removing a floor is not
      misled. "Whose value changed" is the clause that is true of the code.
    - `SKILL.md` carries only the lines an agent acts on. The reference
      carries the rest.

- **DEC-TRS-009** (amended after the first adversarial review, LOW-3)**:**
  the README shows every verb the parser declares, and a guard reads the
  parser to keep it that way.
  - **Precedent.** The guard sits beside
    `test_skill_tables_cover_every_verb_the_cli_actually_has`, and reads the
    same `build_parser()`. A verb added to the CLI without a README line
    then fails the suite, as one added without a `SKILL.md` row already
    does.
  - **What each new line carries.**
    - Its comment states what the verb reads or writes.
    - `delta` states its exit behaviour, and `report` states that it never
      exits 1.
    - `witness` says it is for the CI job that ran the stage. That matches
      `SKILL.md`'s refusal without restating it.
  - **Why `--exit "$code"`.** The exit a witness records is the one the
    stage step captured: clear errexit, run the stage, keep `$?`, the idiom
    `add-witness-ci-artifacts`' R-WCA-22 documents and the composite action
    already uses. A literal exit code in a copyable line would record a
    verdict nothing observed, which is the fabrication `SKILL.md` refuses.
  - **Why `validate --format sarif`.** It is the format the composite action
    and code scanning consume, and the parser's help names it.
  - **Why the exit sentence.** The README is the PyPI long description, so
    the sentence under its exit-code table states the per-verb exceptions
    there, and points to the reference for the rest.
  - **The adopter corpus.** No new line carries an install command or a tag
    token, so `tests/test_adopter_urls.py` reads nothing new.

- **DEC-TRS-010** (amended after the first adversarial review, MEDIUM-1,
  MEDIUM-2, MEDIUM-3 and LOW-4, and the second, LOW-6)**:** the tier
  documents say what each tier runs. The one property that holds stays: CI
  runs on every pull request, and on every push to the integration,
  candidate and production branches, whatever the hooks did.
  - **The triggers, as `ci.yml` has them.** Its `pull_request` trigger has
    no filter. Its `push` trigger lists the branches
    `[tool.specgraph.promotion]` names, held equal to that table by
    `test_ci_push_branches_match_the_promotion_config`. A push to any other
    branch runs no CI, so the first draft's "every push and pull request"
    was false. The sentences point at the promotion table and do not spell
    the branch names, so a rename there leaves them true.
  - **Every copy, rewritten together.** The same claim stands in
    `docs/hooks.md`'s opening and its pre-commit paragraph, in
    `docs/aqa.md`, in the README's AQA section and in the pre-commit config's
    header. Fixing only the copies the review named would leave the same
    drift in the others.
  - **Where `make pre-pr` runs, with no exclusive claim.** The sentences
    name `release-tier` and the release workflow's gate as running it by
    name. They never say that no other job does, because
    `add-witness-ci-artifacts`' `ladder` job would make that false the day
    it lands (DEC-TRS-007). CI runs the ladder's parts as separate jobs and
    steps: lint, typecheck and the suite are steps of one job on every leg,
    and the other parts are jobs of their own. The `security` job scans with
    gitleaks-action, a different tool from the security target's. The
    sentences do not say it scans "in place of" the target, for the same
    reason.
  - **The hooks, by their filters.** The lint and typecheck hooks carry
    `types: [python]`, so they run when a Python file is staged. The
    security, validate, docs-check and thresholds hooks carry no type
    filter, and run whatever is staged.
  - **The Python range, a real conflict.** `prepare-release-0-4-0`'s
    `tasks.md` changes `docs/aqa.md`'s "Python 3.10–3.14" to "Python
    3.11–3.14", and this change rewrites the same lines. The first draft
    claimed that token's edit would apply in either merge order. It does
    not: a scratch merge of the two edits stops on a conflict over that
    paragraph. The resolution, in either order, keeps this change's sentence
    with the token `prepare-release-0-4-0` has set: "Python 3.11–3.14" once
    its removals have merged. `tasks.md` reads the merged lines at the
    merge, and that package's hazard list names the conflict (R-TRS-19).
  - **No package names.** The added prose names no change package
    (C-TRS-6).

- **DEC-TRS-011** (amended after the second adversarial review,
  LOW-5)**:** the merge hazards with the open siblings.
  - **The rule.** Each hazard is resolved on purpose, whichever package lands
    first. A conflict keeps both edits, and never rewrites a sibling's
    lines. Every region below is re-read at the implementation head.
  - **`lean-production-tree`.** Its C-LPT-1 forbids it to edit
    `.github/workflows/` or the Makefile, so there is no hazard there. It
    computes that check from its own diff against the merge base, so this
    change's `ci.yml` and Makefile edits do not trip it.
    - `README.md`: it edits the test paragraph above the AQA section, the
      Dogfooding section and the documentation list. This change edits the
      quickstart block, a sentence under the exit-code table, and the AQA
      section's opening and table.
    - `docs/hooks.md`: it edits "Releasing", the reports section, the
      evaluation-suite bullet and the skill list. This change edits the
      opening, the pre-commit paragraph and the CI-table cells of R-TRS-9.
    - `docs/aqa.md`: it drops the evaluation-suite claim and rewrites a
      stays-red sentence. This change edits the Gates table's surroundings
      and "Reproducing CI locally".
    - `tests/test_ci_makefile.py`: it rewords a docstring. This change
      appends functions.
    - Its reference scanner reads the shipped prose. Under C-TRS-6, this
      change's prose names no path it deletes.
  - **`harden-release-pipeline`.** Its C-HRP-1 forbids it to edit the
    Makefile and `ci.yml`, and this change does not edit `release.yml`, so
    the workflows do not collide.
    - Its golden copy pins `release.yml`'s text. This change alters only how
      a tool that file calls reads a wheel's header, so the golden copy
      needs no edit in either order.
    - `docs/hooks.md`: it edits the `release` row and "Releasing". This
      change edits neither.
    - It adds a script and edits `tools/AGENTS.md` and
      `docs/architecture/c4.md`. This change does neither (DEC-TRS-001).
  - **`prepare-release-0-4-0`.**
    - `ci.yml`'s matrix and `docs/hooks.md`'s `test` row: not touched here.
    - `README.md`'s floor line and alias paragraph sit outside the regions
      this change edits.
    - `docs/aqa.md`: a real textual conflict over the range paragraph,
      resolved as DEC-TRS-010 says.
    - `tools/check_wheel_metadata.py`: it rewords `_declared_license`'s
      docstring, which this change leaves alone (R-TRS-18). This change edits
      `check_wheel`'s expression test, apart from that docstring.
    - `SKILL.md`: its pull requests edit the frontmatter and the "Wiring it
      into CI" sentence. This change edits only the "Exit codes" section.
    - The manifests follow its bump alone (C-TRS-3).
    - Its spec, proposal and `tasks.md`: this package amends them at the
      sites of R-TRS-19, and nowhere else (DEC-TRS-015).
  - **`close-gate-script-gaps`**, open and not yet on `dev`. It widens the
    threshold guard, and both packages edit these sites:
    - `README.md`'s gates table: it rewords the thresholds row and the
      paragraph on numeric thresholds, and this change adds a `wheel-check`
      row and rewrites the section's opening;
    - `docs/hooks.md`: it edits the thresholds hook line in the bullet list
      this change leaves alone, and its note on the workflows the guard
      scans. This change edits the opening, the pre-commit paragraph and
      the CI table's `security` cell;
    - `docs/aqa.md`: it edits the externalisation paragraph and the Gates
      table's security row, and this change edits "Reproducing CI locally"
      and a sentence after the Gates table;
    - `.pre-commit-config.yaml`'s header comment, which this change rewords
      and its widened guard reads, comments included for its pin rule. The
      rewording carries no pin-shaped token;
    - the Makefile's `wheel-check` recipe, which its widened guard scans.
      Its C-GSG-2 confines its own Makefile edit to the thresholds target's
      help text, so the two packages change different lines. Its own
      measurement read the first draft's recipe. The second review re-ran
      its prototype on the revised recipe lines, and so did this revision,
      and both found them quiet;
    - `ci.yml`'s `security` step, which this change turns into a make call
      for the thresholds target. Its C-GSG-2 keeps it out of `.github/`, so
      only this change edits the line. The line is quiet under its guard, and
      no workflow line can be whitelisted.

    Its DEC-GSG-001 requires no order against this change: whichever lands
    second re-reads these sites at its own head.
  - **`raise-coding-standards`**, open, not yet on `dev`, and under
    revision when it was read. It adds an empty `openspec_graph/py.typed`.
    Its R-RCS-14 checks the file in the source tree and in both archives,
    built through the sdist as the release paths build them, which is the
    build this change's recipe makes.
    - Measured here too, with the setuptools floor resolved in isolation:
      an empty `py.typed` lands in the sdist and in the wheel built from
      it, with no `MANIFEST.in` edit.
    - This change pins no file list of either archive, and that package's
      own text records the earlier hazard as moot.
    - It names this change's recipe and its header-only checker as shared
      sites, and whichever lands second re-reads both as merged.
    - Its `py.typed` guards go in `tests/test_release_surface.py`, which
      this change does not edit.
  - **`add-witness-ci-artifacts`.** The same `ci.yml` steps, tier sentences
    and CI-table cells (DEC-TRS-007), and `tests/test_skill_contract.py`,
    where it edits a tuple near the top while this change appends functions.
  - **`CHANGELOG.md` `[Unreleased]`.** Every one of these packages adds a
    group there. Each keeps its own.

- **DEC-TRS-012** (amended after the first adversarial review,
  MEDIUM-4)**:** sequencing.
  - **The package pull request.** It carries this package into `dev`, with
    R-TRS-19's amendment of `prepare-release-0-4-0`, and is held until the
    0.3.0 promotion is done. A package merged earlier would ride into the
    0.3.0 tree as a draft describing 0.4.0 work.
  - **The implementation pull request.** It is a GitHub draft from the
    start, and leaves draft only after the package has merged and the hold's
    facts are recorded in `tasks.md`.
  - **It merges before `prepare-release-0-4-0`'s release-prep pull
    request.** That pull request moves every `[Unreleased]` line under
    `[0.4.0]`, and nothing may merge between it and the promotion. An entry
    merged after the cut is stranded above it (DEC-REL-011, DEC-RFR-001).
  - **Who holds that order.** `prepare-release-0-4-0`'s preconditions list
    this change once R-TRS-19's amendment lands: its release-prep pull
    request waits for this change's implementation, or for the maintainer's
    recorded decision to defer it. If this change has not merged when those
    preconditions are checked, the maintainer decides whether to hold the
    cut or move this change to the next release, and records which there. A
    deferred change's entry lands under the next `[Unreleased]`.
  - **The other siblings.** This change needs nothing from them, and the
    hazards of DEC-TRS-011 apply in any order.

- **DEC-TRS-013:** stages and selectors.
  - **The stages.** Verification lines cite `make test`, `make docs-check`
    or `make pre-pr`, and nothing else. `make docs-check` is the stage where
    a criterion is about the documents, and CI's `docs` job runs it by name.
  - **The selectors.** Tests that exist at drafting are cited by selector.
    The new guards are cited by stage until they exist. `tasks.md` names
    them, and the implementation commit adds their selectors.
  - **Hosted observations** are `tasks.md` gates, not criteria. That covers
    the first `packaging` run that builds the wheel from the sdist and
    smokes it, and the stage-citations report before and after. A stage
    cannot see a remote run.
  - **The net effect on the report.** This change adds no stage to the set
    no workflow runs by name, and it removes the stages it wires.

- **DEC-TRS-014** (added after the first adversarial review, LOW-2;
  restated after the second, MEDIUM-2)**:** the licence-expression check
  reads one exact field in the header of `METADATA`, as defence in depth. No
  workflow exposes the gap it closes.
  - **The precondition.** Both false passes need a wheel checked against a
    `pyproject.toml` other than its own. The two wheels `tasks.md` records
    were built from scratch copies whose declarations differ from the
    worktree's, then checked by the worktree's checker. No workflow does
    that: each builds and checks in one tree.
  - **In the wheel's own tree.** The longer-expression wheel, checked by its
    own copy's checker, passes, and that is correct, because it states what
    its tree declares. The body-only copy declares no expression, so its own
    checker exits 2.
  - **What setuptools writes.** setuptools 77 and later write
    `License-Expression` into the header from the project's own
    declaration, in canonical form. A declared `apache-2.0 or mit` becomes
    `License-Expression: Apache-2.0 OR MIT`, and a table-form `license` is
    refused at build time. In-tree, then, the header always carries the
    field the checker means to read.
  - **Why harden it anyway.** The checker claims to read a header field, and
    a line of the README is not that field. The cost is a few lines and
    their planted tests. R-TRS-18 and AC-TRS-23 stay, as defence in depth.
  - **The header block.** A `METADATA` file is a block of header fields, an
    empty line, then the body. The check reads the lines before the first
    empty line, or every line when there is none, which is the shape of the
    module's in-memory fixtures. A folded header line begins with
    whitespace, so it cannot begin with the field name.
  - **An exact field.** A header line must read the field name, one space
    and the declared expression, with trailing whitespace ignored. Equality,
    not a prefix, is what makes the longer expression fail.
  - **The message stays.** The failure message is byte-identical, so the
    existing test that reads it, and a log reader, see no change.
  - **The classifier check stays as it is.** It reads every line, so a
    README line beginning with the legacy classifier text would fail a good
    wheel. That errs closed, and shows as a `FAIL` line naming the line. No
    such line has been seen, and narrowing it is not in the finding.
  - **What it leaves as it is.** Both checkers fail the canonicalised
    `apache-2.0 or mit` wheel, because they compare with the declared
    spelling. That errs closed too, and is not in the finding.
  - **Red first.** The body-only and longer-expression tests are written
    against the unedited checker and recorded red there.
  - **Not the sdist.** This hardens the wheel check DEC-TRS-001 keeps, and
    reads no sdist.

  Rejected:
  - The substring search kept, over the header alone: the longer expression
    would still pass.

- **DEC-TRS-015** (added after the first adversarial review, MEDIUM-4;
  amended after the second, LOW-3, LOW-4 and LOW-5)**:**
  `prepare-release-0-4-0` is amended in place at its release-prep ordering
  and its hazard list, as the one exception to C-TRS-4.
  - **Why amend.** The ordering this change needs is that its implementation
    merges before the release-prep pull request cuts `[Unreleased]` into
    `[0.4.0]` (DEC-TRS-012). Recorded only in this package's `tasks.md`, as
    the first draft had it, it is invisible to whoever runs that package's
    Milestone 5. A precondition that package does not list is one it does
    not check.
  - **Why it may be amended.** It is open and unimplemented: `Status:
    DRAFT`, and every criterion unchecked. A draft is a plan, not a record
    of what shipped, so amending it rewrites no history. The precedents:
    - `measure-coverage-once` amended `add-witness-ci-artifacts` in place,
      at sites it named, with each edit naming itself (R-MCO-10,
      DEC-MCO-007);
    - `lean-production-tree` did the same, each edit marked "(amended by
      `lean-production-tree`)" (R-LPT-16, DEC-LPT-007).
  - **The sites.** Every place that package states its release-prep
    ordering gains the condition: R-RFR-2's sentence, AC-RFR-20's bullet,
    the bold "Pull request 2" sentence of its proposal, the "Pull request 2"
    bullet of its `tasks.md` summary, and its Milestone 5 preconditions. Its
    hazard list's `docs/aqa.md` entry gains the conflict of DEC-TRS-010.
    Each is an insertion carrying the marker. No ID is added, removed or
    renumbered, and nothing else in that package changes.
  - **The commands that show the merge.** The precondition checks two facts
    on the integration branch, each one the implementation's own. The first
    is the retitled exit-1 heading in the per-verb reference. The second is
    the `### Changed — the release surface` group Milestone 6 writes in
    `CHANGELOG.md`. That group is what the cut moves, so it is the fact the
    ordering exists for.
  - **Defer, as well as merge.** The bullet accepts the maintainer's
    recorded decision to defer this change, so a late implementation never
    blocks 0.4.0. It makes the choice explicit rather than adding a hard
    dependency.
  - **Not a complete list.** The preconditions this extends name
    `lean-production-tree`, `harden-release-pipeline` and the removals, and
    now this change. They do not name every sibling meant to ship in 0.4.0.
    `close-gate-script-gaps` (DEC-GSG-001) and `raise-coding-standards`
    (R-RCS-1, DEC-RCS-017) each state their own order against the
    release-prep pull request in their own text. This amendment does not
    speak for them.
  - **Where it lands.** In this package's own pull request, so the
    precondition is on `dev` before that package's release prep can begin.

  Rejected:
  - The constraint recorded here alone: it stays invisible where it is
    checked.
  - A hard precondition with no deferral: one package's lateness would hold
    another's release.

---

## Acceptance Criteria

- [ ] **AC-TRS-3:** The wheel checker's contract holds, apart from the header
  reading:
  - a good wheel passes, and a wheel missing its licence fails;
  - a missing expression and a mismatched one are still caught;
  - a directory with no wheel exits 2, and so does a missing directory;
  - every existing test of the checker passes without edit.

  (R-TRS-18, C-TRS-7, DEC-TRS-014)
  _Verified by:_ `pytest -k "test_main_exits_0_on_a_good_wheel or test_a_missing_license_file_is_caught or test_missing_license_expression_is_caught or test_a_mismatched_expression_is_caught or test_main_exits_2_when_there_is_nothing_to_check or test_main_exits_2_on_a_missing_directory"` · stage: `make test`

- [ ] **AC-TRS-6:** The `wheel-check` recipe, in order:
  - removes `dist/`;
  - builds with no distribution flag;
  - runs the checker;
  - smokes the wheel with exactly the `--expect` set `release-tier`'s smoke
    step passes, read from the workflow, and no other flag.

  A planted `release-tier` carrying one more `--expect` than the recipe, the
  review's drift case, is named with that probe, and so is a planted recipe
  carrying one more than `release-tier`. The target keeps its name, its help
  text does not begin "Report", and it is reachable from neither aggregate,
  whose compositions are unchanged. (R-TRS-4, DEC-TRS-003, DEC-TRS-004)
  _Verified by:_ `pytest -k "test_every_report_target_stays_out_of_the_ladder or test_test_and_coverage_tools_read_the_one_report_scoped"` · stage: `make test`

- [ ] **AC-TRS-7:** `release.yml`, `release-tier`'s steps and
  `tools/smoke_wheel.py` are absent from the diff. The release workflow keeps
  its gated, trusted publishing chain, and both release paths still call one
  smoke tool with the same probes, which still requires exactly one wheel.
  The diff is read against the base. (R-TRS-5, C-TRS-2, DEC-TRS-001)
  _Verified by:_ `pytest -k "test_release_and_ci_share_one_smoke_tool or test_release_workflow_is_gated_and_uses_trusted_publishing or test_smoke_requires_exactly_one_wheel"` · stage: `make test`

- [ ] **AC-TRS-8:** `self-validate`, `security` and `packaging` each call
  their target through `make`, and none carries the command it replaced.
  Each replaced command is in its target's recipe. The stage-citations
  reader credits `ci.yml` with the `validate`, `thresholds` and
  `wheel-check` stages, and every cited stage is still a Makefile target.
  At the wiring commit, each recipe was the job's inline command, which is
  read from that commit's diff. (R-TRS-6, R-TRS-8, DEC-TRS-005)
  _Verified by:_ `pytest -k test_this_repository_report_holds_its_invariants` · stage: `make test`

- [ ] **AC-TRS-9 (non-success):** A planted job running a replaced command
  inline is named with the job and the command, whether the command sits
  beside its target, in place of it, or in a flow-mapping step the `run:`
  reader does not return. A planted tree whose spec cites a stage no
  workflow runs does not fail the guard, because the report stays a report.
  (R-TRS-8, DEC-TRS-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-TRS-10:** This change's diff adds, renames and removes no job,
  and adds no call to the `ci`, `coverage-tools` or `security` target. The
  diff is read against the base. On the tree it lands on:
  - `docs/hooks.md`'s CI table and `ci.yml` still list the same jobs, both
    ways;
  - `ci-ok` still needs every other job;
  - the composition of `ci` and `pre-pr` is as this change found it.

  (R-TRS-7, DEC-TRS-005, DEC-TRS-007)
  _Verified by:_ `pytest -k "test_hooks_ci_table_lists_every_ci_job or test_every_hooks_ci_table_row_names_a_job_or_workflow or test_ci_ok_needs_every_other_ci_job or test_test_and_coverage_tools_read_the_one_report_scoped"` · stage: `make test`

- [ ] **AC-TRS-11:** These are read directly, with every required document
  still present and linked:
  - the cells of `docs/hooks.md`'s CI table name what `self-validate`,
    `security` and `packaging` run;
  - its ladder names the `wheel-check` target as run by `packaging` on
    every pull request, and on every push to the integration, candidate and
    production branches, and as outside `make pre-pr`;
  - `docs/aqa.md` and the README's AQA table say the same;
  - the tier paragraphs say what R-TRS-15 and R-TRS-16 require, and the
    push branches they point at are the promotion table's.

  (R-TRS-9, R-TRS-15, R-TRS-16, DEC-TRS-010)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_hooks_ci_table_lists_every_ci_job or test_ci_push_branches_match_the_promotion_config"` · stage: `make docs-check`

- [ ] **AC-TRS-12:** On an empty target with an absent baseline, `delta`
  exits 2, and its stderr is exactly the short message the reference
  quotes. On a target holding an unreadable spec, `delta` exits 2 with the
  unreadable-spec line and no traceback. The reference's no-spec-tree and
  unreadable-spec entries name `delta`, and so does `SKILL.md`'s bullet. The
  existing message and unreadable-spec tests still pass for the verbs they
  cover. (R-TRS-10, R-TRS-11, R-TRS-12, DEC-TRS-008)
  _Verified by:_ `pytest -k "test_cli_delta_without_a_spec_tree_is_a_usage_error or test_exit_two_messages_match_the_documented_contract or test_unreadable_spec_exits_2_from_every_parsing_verb"` · stage: `make test`

- [ ] **AC-TRS-13 (non-success):** With a readable `--baseline`,
  `delta --fail-on ERROR` exits 2, naming the unrecognised argument. The
  reference documents it, and says that without `--baseline` the missing
  flag is reported first. A planted copy of either contract file with any
  `delta` entry removed, or with the "only findings" sentence restored, is
  named by the reader, file and entry both. (R-TRS-10, R-TRS-12,
  DEC-TRS-008)
  _Verified by:_ stage: `make test`

- [ ] **AC-TRS-14:** `delta` exits 1 on a citation made stale by a removed
  target. It lists a spec citing the old value of a floor whose value
  changed, and lists none citing a floor that did not move. It exits 0 on an
  identical card, and ignores a citation already broken at the baseline.
  Both contract files describe exactly that, with no threshold, in the
  wording DEC-TRS-008 fixes, under the retitled section on exit-1 cases that
  are not findings. (R-TRS-10, R-TRS-11, DEC-TRS-008)
  _Verified by:_ `pytest -k "test_delta_names_the_removed_make_target or test_cli_delta_exits_zero_on_an_identical_baseline or test_delta_ignores_a_citation_already_broken_in_the_baseline or test_delta_reports_a_spec_citing_the_old_coverage_floor or test_delta_ignores_a_floor_that_did_not_move"` · stage: `make test`

- [ ] **AC-TRS-15:** `SKILL.md`'s frontmatter is unchanged:
  - its version fields still equal the package version;
  - the manifests are fresh under their generator's check, and still read
    the version from the package;
  - the skill's verb tables still cover the parser.

  (R-TRS-11, C-TRS-3)
  _Verified by:_ `pytest -k "test_generated_artifacts_are_fresh or test_skill_metadata_version_matches_the_package or test_manifest_version_tracks_the_package_not_a_literal or test_skill_tables_cover_every_verb_the_cli_actually_has"` · stage: `make test`

- [ ] **AC-TRS-16:** The README's quickstart shows every verb the parser
  declares and a `validate --format sarif` line, with comments as R-TRS-13
  requires. The `witness` line passes a captured exit and no literal one.
  The sentence under the exit-code table names `delta`'s and `report`'s
  exceptions. The adopter-corpus guards read no new install command and no
  new tag. (R-TRS-13, R-TRS-14, DEC-TRS-009)
  _Verified by:_ `pytest -k "test_install_lines_spell_this_project_the_way_it_is_published or test_every_copyable_tag_ref_names_the_current_version or test_readme_plugin_commands_match_the_generated_manifests"` · stage: `make test`

- [ ] **AC-TRS-17 (non-success):** Planted quickstart text that leaves out a
  verb is named with that verb, and so is text naming a verb the parser
  does not declare. Text with no sarif line is named for that, through the
  same reader the real-tree guard calls. (R-TRS-14, DEC-TRS-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-TRS-18 (non-success):** These claims are gone:
  - that pre-commit or CI enforces the same gate as `make pre-pr`;
  - that a hook keeps a commit from bypassing CI;
  - that `make pre-pr` is the exact bar CI enforces.

  None survives in `docs/hooks.md`, `docs/aqa.md`, the README's AQA section
  or the pre-commit config's header, which is read directly with the grep
  `tasks.md` records. No tier sentence this change writes says CI runs on
  every push, or that a job is the only one to run a target. The two
  pre-commit files still differ, and the hooks are unchanged. (R-TRS-15,
  R-TRS-16, DEC-TRS-010)
  _Verified by:_ `pytest -k "test_the_two_pre_commit_files_do_not_collide or test_docs_check_passes"` · stage: `make docs-check`

- [ ] **AC-TRS-19:** `CHANGELOG.md`'s `[Unreleased]` section carries the
  group R-TRS-17 describes. No released section differs from the base, and
  every versioned section still links to its tag. (R-TRS-17, DEC-TRS-012)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [ ] **AC-TRS-20 (non-success):** None of these moved:
  - the rule inventory;
  - the golden output hashes;
  - the empty runtime-dependency list;
  - the CLI's verb set.

  No file under `openspec_graph/` is in the diff. (C-TRS-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty or test_cli_verbs_are_exactly_the_allow_list"` · stage: `make test`

- [ ] **AC-TRS-21:** The thresholds guard is absent from the diff, scans
  every workflow and stays quiet on every line this change adds to the
  Makefile and `ci.yml`. No script is added under `tools/`, and every listed
  gate script still runs as a script. (C-TRS-2)
  _Verified by:_ `pytest -k "test_every_workflow_is_scanned_by_the_threshold_guard or test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency or test_gate_script_is_runnable_as_a_script"` · stage: `make pre-pr`

- [ ] **AC-TRS-22:** These hold on the implementation head, with the whole
  ladder green:
  - every test citation in every spec resolves;
  - every backticked path and make target in the agent and skill prose is
    real;
  - no other package's text is in the implementation's diff;
  - this spec pins no count or line number;
  - the added prose names no change package and no path
    `lean-production-tree` deletes.

  The diff properties are read against the base. (C-TRS-4, C-TRS-5,
  C-TRS-6, C-TRS-7, DEC-TRS-011, DEC-TRS-013)
  _Verified by:_ `pytest -k "test_every_spec_test_citation_resolves_to_a_real_test or test_path_like_backtick_references_resolve_to_real_files or test_make_target_references_are_real_makefile_targets"` · stage: `make pre-pr`

- [ ] **AC-TRS-23 (non-success):** Each of these is caught by the checker
  with its existing message naming `License-Expression`, and the unedited
  checker was seen to pass both:
  - a wheel whose `METADATA` header lacks the field while its body carries
    the line;
  - a wheel whose header carries a longer expression that begins with the
    declared one.

  (R-TRS-18, DEC-TRS-014)
  _Verified by:_ stage: `make test`

- [ ] **AC-TRS-24:** `prepare-release-0-4-0`'s spec, proposal and `tasks.md`
  carry R-TRS-19's sites, each an insertion with its marker, and no other
  change. The sites are:
  - R-RFR-2's sentence and AC-RFR-20's bullet;
  - the proposal's "Pull request 2" condition and the `tasks.md` summary's;
  - the Milestone 5 precondition, with both of its commands;
  - the `docs/aqa.md` hazard.

  Its IDs are the set they were before the amendment, and it validates
  clean alone and in the whole tree. The diff of the package pull request is
  read against its base. (R-TRS-19, C-TRS-4, DEC-TRS-015)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-TRS-3, AC-TRS-6..10, AC-TRS-12..17, AC-TRS-19, AC-TRS-20, AC-TRS-23: every new guard green on the real tree and red on its planted counterpart; every guard this change leans on still green unedited |
| Docs | `make docs-check` | AC-TRS-11, AC-TRS-18: every required document present and linked after the rewording; the CI table still names every job |
| Full | `make pre-pr` | AC-TRS-21, AC-TRS-22, AC-TRS-24: the thresholds guard, lint and strict typecheck of the edited tool, the `tools/` coverage floors with the new branch covered, and this repository's own validate over every package, the amended sibling included |
| Recorded | none, recorded in `tasks.md` | the `wheel-check` target run locally on the implementation head; the stage-citations report before and after the wiring; the first hosted `packaging` run building the wheel from the sdist and smoking it; the `docs/aqa.md` range paragraph read at the merge; the hold's facts before each pull request leaves draft (DEC-TRS-010, DEC-TRS-012, DEC-TRS-013) |
