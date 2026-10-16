# Spec: Release Pipeline

> **Change:** `harden-release-pipeline`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The release workflow is the only path by which this repository's code reaches
anyone who did not clone it. It publishes through trusted publishing, and the
PyPI publisher attaches a PEP 740 publish attestation to each file, so a
downloader can check who published a file. Nothing lets them check what built
it, from which commit and in which workflow. The GitHub release that should
carry the same files is cut by hand after the run, from the changelog. Both
checkouts that run the tagged tree leave the job's token where every later
step can reach it: in a credentials file under `RUNNER_TEMP` that the
checkout's git configuration includes. Those later steps are the whole pre-PR
ladder, a `pip install` of the dev extras, the build and the smoke test. The
security policy names a reporting route and nothing else a reporter or a
downloader needs: what is in scope, how long a report waits, when it becomes
public, whether good-faith research is welcome, how a fix ships, and how to
verify a file. No file names the repository's code owner. Dependabot opens a
pull request for an action release the week it ships. And the recorded reason
for deferring a floating `v1` tag is a permission fact this change makes
false.

A constraint shapes all of it. The new job that creates the GitHub release
runs only after a real publish, so no dry run and no rehearsal can exercise
it. Every fact its design leans on is therefore either checked against the
source of the tool it uses or named as unobserved until the first release
that runs it.

**Evidence:** read on `claude/lean-production-tree` at `4278d4c` and re-read
on `claude/harden-release-pipeline` at `f96b7d1` for the first adversarial
review, 2026-10-16; outside `openspec/` both trees are `dev` at `c0ff090`.
Each line number and each external lookup is in `proposal.md` and `tasks.md`;
none is repeated here (C-HRP-4).

- **The workflow.** `.github/workflows/release.yml` runs `gate → build → publish`
  on a `v*` tag, and `gate` and `build` alone on `workflow_dispatch`. The top
  level grants `contents: read`. `publish` adds `id-token: write` under a
  comment, downloads `dist` and runs the pinned PyPI publisher with
  `attestations: true`. No step attests a build, no job creates a release, and
  no checkout sets `persist-credentials`. `gate`'s tag-only ancestry step
  fetches the default branch and runs `tools/check_promotion.py tag-ancestry --fetch`
  from a worktree of it, before `make pre-pr`.
- **The defaults it inherits.** The pinned `actions/checkout` declares
  `persist-credentials` with a default of `true`. It writes the token into a
  credentials file under `RUNNER_TEMP`, which the repository's git
  configuration includes for its git directory. `tag_ancestry` returns exit 2
  when its own fetch fails and exit 1 for a commit off the production branch's
  first-parent chain. The step's own `git fetch` runs first, so on a
  repository that needs authentication to fetch, git's exit 128 ends the step.
- **The attesting action.** `actions/attest` is a JavaScript action on Node 24
  with no nested `uses:`. Given neither an `sbom-path` nor a predicate input,
  it makes SLSA build provenance. It writes the signed bundle under
  `RUNNER_TEMP`, never beside its subject. It needs `id-token: write` and
  `attestations: write`, and `artifact-metadata: write` only for a storage
  record, which it makes only when pushing to a registry. The plan named
  `actions/attest-build-provenance`. That is a composite wrapping
  `actions/attest`: it passes the predicate inputs through, and its README
  directs new implementations to `actions/attest`.
- **The CLI the new job uses.** `gh release create` creates a missing tag from
  the default branch unless `--verify-tag` is given. With assets attached it
  creates a draft, uploads, then publishes, and an immutable release is
  locked only once published. `gh attestation verify` checks SLSA provenance
  by default and takes `--repo`, `--signer-workflow`, `--source-ref`,
  `--source-digest` and `--deny-self-hosted-runners`.
- **The guards already in the tree.** `tests/test_workflow_pins.py` holds
  every third-party `uses:` to a SHA pin with its release tag, one pair per
  action, at or above a per-action floor, and names a pinned action with no
  floor. `tests/test_workflow_posture.py` holds every job to a bounded
  `timeout-minutes`, every job-level `permissions:` block to a comment inside
  its own job, `release.yml` to no `concurrency` block, and the publisher to
  an explicit `attestations: true`. `tests/test_release_surface.py` holds the
  job chain, the ancestry step and the two-workflow set, and says nothing
  about checkouts, attestations, a fourth job or a write permission.
  `tools/_common.py`'s `run_scripts` extracts a workflow's `run:` scripts, and
  its `shell_invocations` joins backslash continuations before lexing.
- **The documents.** `docs/hooks.md`'s `release` row, the release runbook and
  the release skill verify only the publish attestations, and the runbook
  leaves the GitHub release to a person. `SECURITY.md` is in the adopter
  corpus that `tests/test_adopter_urls.py` reads for copyable versions.
  `docs/next-steps.md`'s floating-`v1` row says the release workflow holds no
  `contents: write`.

---

## Requirements

### The release workflow

- R-HRP-1: Every `actions/checkout` step in `.github/workflows/release.yml`
  MUST set `persist-credentials: false` under its own `with:`. That covers
  `gate`'s, which keeps `fetch-depth: 0`, and `build`'s. A checkout that omits
  the key, or sets it to anything else, MUST fail the suite naming the job
  and the line.
- R-HRP-2: The comment above `gate`'s ancestry step MUST say that the step's
  fetches, its own and `tag-ancestry`'s, run unauthenticated. It MUST say that
  this works because the repository is public, and that on a repository
  requiring authentication the first fetch exits 128 before `make pre-pr`
  runs. It MUST name the remedy: an `http.extraheader` the step's own script
  exports through git's environment configuration (`GIT_CONFIG_COUNT` with
  one key and value), computed in the shell, because the header's base64
  value is beyond an `env:` expression. That reaches both fetches and no later
  step. It MUST rule out `persist-credentials: true` as the remedy.
- R-HRP-3: `publish` MUST run `actions/attest`, pinned to a 40-hex commit with
  its release tag in a trailing comment, as a step after the `dist` download
  and before the PyPI publisher step. Its `with:` MUST hold
  `subject-path: dist/*` and MUST hold no predicate input (`predicate-type`,
  `predicate`, `predicate-path`) and no `sbom-path`. That absence is what
  makes the action produce SLSA build provenance. `publish`'s permissions
  block MUST be exactly `contents: read`, `id-token: write` and
  `attestations: write`. The comment already above that block MUST be
  extended in place to name the attest step as the reason for
  `attestations: write` and as a signing use of `id-token: write`. The
  publisher step, its pin and its `attestations: true` MUST be unchanged.
- R-HRP-4: `build` MUST carry two steps, each conditioned exactly on
  `github.ref_type == 'tag'`. One runs `python tools/release_notes.py` with
  the tag name minus its leading `v` and writes the output to a file under
  `RUNNER_TEMP`. The other uploads that file as the artifact `release-notes`,
  with `if-no-files-found: error`. Both MUST come after the step that refuses
  a tag differing from the packaged version, and before the `dist` upload, so
  a tag whose changelog has no section for its version uploads nothing and
  publishes nothing. On a `workflow_dispatch` run neither step runs.
- R-HRP-5: A job `release` MUST exist with `needs: publish` and an `if:`
  condition exactly `github.ref_type == 'tag'`. It MUST carry a
  `timeout-minutes` literal inside the configured range. It MUST carry a
  job-level `permissions:` block of exactly `contents: write` and
  `attestations: read`, with a comment line inside the job's own body, between
  its `release:` line and that block, naming `gh release create` as the reason
  for the first and `gh attestation verify` for the second. No other job in
  any workflow under `.github/workflows/` MAY hold `contents: write`, whether
  by a `contents: write` line, by the flow form `{contents: write}` or by
  `permissions: write-all`, and
  `release.yml`'s top-level block MUST stay `contents: read` alone.
- R-HRP-6: The `release` job MUST NOT check out the repository and MUST NOT
  bring the tagged tree in by any other route. Its steps MUST be exactly the
  `dist` and `release-notes` downloads, through the same pinned
  `actions/download-artifact` the workflow already uses, and `run:` steps
  whose commands are `gh attestation verify` and `gh release create` and
  nothing else. That rules out `make`, an interpreter, a package installer,
  `git`, and every other `gh` subcommand. Those steps MUST take `GH_TOKEN`
  from `github.token`, never from a stored secret, and `GH_REPO` from
  `github.repository`, both through `env:`. They MUST read the tag from
  `GITHUB_REF_NAME` in the environment, never through an inline expression in
  `run:`. The guard MUST pin the job's whole text, never parse its YAML or
  its shell: the `release` block `workflow_job_blocks` returns, with each
  line's trailing whitespace stripped, its leading and trailing blank lines
  dropped, and each action pin's `@<40-hex sha> # v<version>` replaced by
  one placeholder, MUST equal the fixed text the test holds, line for line.
  Any other block is an offender, named by its first differing line. So the
  job's steps, their `env:`, their scalar styles and every key the job
  carries are fixed, and a step, an environment variable, a `container:`, a
  `services:`, a `working-directory:` or a `shell:` the text does not hold
  is refused, however it is written. Outside the block, `release.yml`'s
  top-level `env:` MUST hold `PYTHON_DEFAULT` alone, and the file MUST
  declare no top-level `defaults:`, because both reach every job.
- R-HRP-7: The `release` job MUST run `gh attestation verify` on every file
  in the downloaded `dist` directory, each with the following flags:
  - `--repo` naming this repository;
  - `--signer-workflow` naming this repository's
    `.github/workflows/release.yml`;
  - `--source-ref` naming the pushed tag's ref;
  - `--source-digest` naming the tagged commit (`GITHUB_SHA`);
  - `--deny-self-hosted-runners`.

  A verification that fails for any file MUST fail the job before
  `gh release create` runs. No step of the job MAY carry a soft-fail token
  (`continue-on-error`, `|| true`, `|| :`, `|| echo`, `set +e`), and no step
  MAY carry an `if:` that runs it after a failure.
- R-HRP-8: The `release` job MUST create the release with one
  `gh release create` naming the pushed tag, passing `--verify-tag`, taking
  exactly the verified files as its assets, titling the release
  `planlint <version>` and reading its notes from the downloaded
  `release-notes` file. It MUST NOT create, move or delete a tag, and MUST
  NOT create a draft for a later step to publish.
- R-HRP-9: `release.yml` MUST declare no `concurrency` block at any level.
  The `gate → build → publish` chain, the ancestry step, the smoke step, the
  tag-version check and the trigger set MUST be otherwise unchanged.

### Configuration

- R-HRP-10: `[tool.specgraph.action_major_floors]` in `pyproject.toml` MUST
  gain a row for `actions/attest` at the major this change pins. No existing
  row MAY move.
- R-HRP-11: The `github-actions` entry of `.github/dependabot.yml` MUST
  declare `cooldown` with `default-days: 7`, under a comment saying that the
  wait applies to version updates and never to security updates. Its
  directories, target branch, schedule, pull-request limit, labels, commit
  prefix and `actions-minor` group MUST be unchanged, and no `pip` ecosystem
  MAY be added. A `github-actions` entry with no `cooldown` MUST fail the
  suite.
- R-HRP-12: `.github/CODEOWNERS` MUST exist and hold exactly one rule,
  `* @ianshank`, under a comment saying that it names the owner of every path
  and enforces nothing while the branch rulesets require no approving review.

### The release-notes tool

- R-HRP-13: `tools/release_notes.py` MUST import only the standard library and
  `_common`, never `openspec_graph`. Its `main(argv)` MUST take the program
  name first and parse `argv[1:]`. It MUST accept one positional version and
  a `--changelog` path whose default, the repository's `CHANGELOG.md`, is
  resolved at call time and never bound into a signature default. Given a
  version, it MUST print, and exit 0, the body of the section headed
  `## [<version>]`. The section runs from the line after that heading to the
  next level-2 heading or the end of the file. Link-definition lines at
  column 0 end the body only when every non-blank line from the first of them
  to the section's end is one. Leading and trailing blank lines are removed,
  and every `###` group inside is kept. No length ceiling applies
  (DEC-HRP-026). It MUST write that text as UTF-8 whatever the console's
  encoding. Every public module, function and class in it MUST carry a
  docstring, with no entry in the docstring ratchet.
- R-HRP-14: `tools/release_notes.py` MUST exit 2, print nothing on stdout,
  and print one stderr line naming the version and the changelog path, when:
  - the changelog does not exist, cannot be read, or is not UTF-8;
  - the version is not `MAJOR.MINOR.PATCH` digits, which covers a leading `v`,
    `Unreleased` and a pre-release suffix;
  - no section carries that version;
  - more than one section carries it;
  - the section's body is empty;
  - a link-definition line sits inside the section with other content after
    it.

  It MUST NOT exit 1: it renders notes and judges nothing.
- R-HRP-15: A new module, `tests/test_release_notes.py`, MUST exercise
  `main(argv)` in-process against changelogs planted under `tmp_path`,
  covering each case of R-HRP-13 and each refusal of R-HRP-14, the UTF-8 write
  under an ASCII console, and its import set. It MUST also find a non-empty
  section for the package's current version in this repository's own
  changelog. Its tests MUST carry the tier the suite's mechanical criterion
  computes, stay flat under `tests/`, stay inside the module line bound, and
  add no occurrence of an exempted mypy code. `release_notes.py` MUST join the
  runnable-script list in `tests/test_gate_scripts.py`. The `tools/` coverage
  floors MUST hold with the script measured.

### Documentation

- R-HRP-16: `SECURITY.md` MUST keep its reporting route, its threat model and
  its "What is not a vulnerability" section. It MUST add:
  - **Scope.** In: the PyPI package, the composite action, the skill and
    plugin manifests, and this repository's workflows. Out: third-party
    actions, GitHub itself, and adopters' repositories and workflows.
  - **Timeline.** A report is acknowledged within 7 days and receives a fix
    or a reasoned statement within 90.
  - **Disclosure.** A GitHub security advisory, with a CVE where one applies,
    is published at the fix or at day 90, whichever comes first, and the
    reporter may publish after day 90.
  - **Safe harbour.** One sentence: good-faith research within this policy is
    welcome and will not be pursued.
  - **How fixes ship.** A `hotfix/*` branch into the production branch,
    released as the next patch of the latest minor; earlier minors receive
    nothing.
  - **Verification.** A section with the publish-attestation check
    (`pypi-attestations verify pypi` with `--repository`) and the
    build-provenance check (`gh attestation verify` with `--repo` and
    `--signer-workflow`, plus `--source-ref` naming the release's tag). It
    states that the build provenance meets SLSA Build L2.

  It MUST NOT claim SLSA Build L3. Its commands MUST name a version only
  through placeholders, so that the copyable-tag and install-name guards read
  nothing new and no release-prep edits them.
- R-HRP-17: `docs/hooks.md`'s `release` row MUST name the build provenance
  step, the verification and the automated GitHub release. The release
  runbook in `docs/hooks.md` "Releasing", and the "Tag the production merge
  commit" step of `.claude/skills/planlint-release/SKILL.md`, MUST verify both
  kinds of attestation and MUST say that the `release` job creates the GitHub
  release. The runbook's GitHub-release step MUST keep its place in
  `lean-production-tree` R-LPT-4's sequence and keep naming the `[X.Y.Z]`
  changelog section as the source of the notes, so that R-LPT-4 stays true of
  the runbook. Neither document MAY tell a person to create the release for a
  version tag. Where either names a fallback for a failed `release` job, the
  fallback MUST be to re-run that job, and failing that to verify locally and
  run the same `gh release create` with `--verify-tag`.
- R-HRP-18: `docs/next-steps.md`'s floating-`v1` row MUST keep its decision and
  its trigger, the 1.0 contract. Its reason MUST be re-stated: a floating major
  promises compatibility across every later release under it, which a pre-1.0
  contract does not make. It MUST no longer say the release workflow holds no
  `contents: write`, and MUST say that the one job holding it is checkout-free,
  creates the release for the exact tag pushed and moves no tag.
- R-HRP-19: `tools/AGENTS.md` and `docs/architecture/c4.md` MUST name
  `release_notes` among the stdlib-only scripts. `tools/AGENTS.md` MUST also
  name it among the program-name-first argv convention, and MUST stay within
  the nested-file line bound. Every count either file states MUST be true of
  `tools/` after the change. `CHANGELOG.md`'s `[Unreleased]` section MUST
  carry a `### Changed` entry whose heading ends with this package's
  backticked name in parentheses, naming the provenance step, the `release`
  job, the dropped credentials, the notes tool, the floor row, the cooldown,
  `CODEOWNERS` and the security policy.

### What is not adopted

- R-HRP-20: This change MUST NOT add an SBOM, a dev lockfile, a `pip`
  Dependabot entry, a workflow dependency lockfile, a third workflow file
  (Scorecard, dependency review or any other), a signed-commits ruleset, a
  floating or moving tag, a Marketplace listing, or a `CONTRIBUTING.md`. Each
  is recorded with its reason and its reopen trigger (DEC-HRP-021 to
  DEC-HRP-023). The guards that already hold three of the absences MUST stay
  green unedited: no `pip` ecosystem, exactly two workflow files, and every
  root markdown file wired into the docs gate.

### Constraints

- C-HRP-1: No file under `openspec_graph/` and neither the Makefile, `ci.yml`,
  the composite action nor the templates MAY change. No rule changes, no
  version bump, and `[project] dependencies` stays empty.
- C-HRP-2: The existing tests other packages' verification lines cite MUST
  keep their names and pass, and
  `test_release_workflow_is_gated_and_uses_trusted_publishing`,
  `test_release_gate_checks_tag_ancestry_against_production` and
  `test_publish_declares_attestations_explicitly` MUST be unedited.
- C-HRP-3: `tools/check_no_hardcoded_thresholds.py` MUST NOT be edited, and
  MUST stay quiet on every line this change adds to a workflow.
- C-HRP-4: This spec pins no count and no line number. Every measurement is
  in `tasks.md`, dated with its commit and naming its command.

---

## Decisions

- **DEC-HRP-001:** the build provenance is attested in `publish`, immediately
  before the PyPI upload, and not in `build`. The plan's three reasons, kept.
  First, no dry-run attestations: `build` runs on every `workflow_dispatch`,
  so an attestation there would sign branch bytes that are never published,
  and any verification made without `--source-ref` would accept them as this
  repository's build. Second, `publish` runs no repository code. The signing
  identity, `id-token: write` with `attestations: write`, lives only in a job
  whose steps are a download and two pinned actions, while `build` executes
  the tagged tree's build backend and smoke test. Third, the attested digests
  are those of the bytes PyPI receives: the same downloaded `dist` directory,
  attested and then uploaded in one job. A fourth fact, checked against the
  pinned source rather than assumed, keeps the third true: `actions/attest`
  writes its bundle under `RUNNER_TEMP`, so `dist/` holds the build output
  alone when the publisher uploads everything in it.
- **DEC-HRP-002:** the PEP 740 publish attestation and the SLSA provenance are
  complementary, and both stay. The publish attestation (predicate
  `https://docs.pypi.org/attestations/publish/v1`, made by the PyPI publisher,
  checked with `pypi-attestations verify pypi`) binds a file to the trusted
  publisher that uploaded it. The build provenance (predicate
  `https://slsa.dev/provenance/v1`, made by the attest step, checked with
  `gh attestation verify`) binds the same digest to the workflow, the run and
  the source commit and ref that produced it. A downloader holding only the
  first knows the uploader. Holding the second, they can check the tag and the
  commit, refuse a self-hosted builder, and find the source.
- **DEC-HRP-003:** "SLSA Build L2", never L3. GitHub's documentation states
  that artifact attestations by themselves provide SLSA v1.0 Build Level 2,
  and that Level 3 needs the build isolated from the calling workflow, which
  is a reusable workflow shared as a trusted builder. Here the build and the
  attestation run in jobs of the calling workflow itself. `SECURITY.md` and
  every other document say L2. `--deny-self-hosted-runners` on the `release`
  job's verification turns the hosted-platform half of L2 from a claim into
  a checked property. Reopen L3 when the build and the attestation move into
  a reusable workflow the release workflow calls.
- **DEC-HRP-004 (revised at the first review):** `actions/attest`, pinned by
  commit to its `v4.2.2` release, with a major floor of 4. It replaces the
  `actions/attest-build-provenance` wrapper the plan named, and the draft's
  reason for keeping the wrapper is withdrawn as wrong. That reason was that
  the wrapper's name fixes the predicate. It does not: the wrapper exposes
  `predicate-type`, `predicate` and `predicate-path` and passes them through
  to `actions/attest`, so in either action the inputs decide what is
  attested. The evidence for the change:
  - the wrapper's README directs new implementations to `actions/attest`;
  - GitHub's how-to for artifact attestations uses `actions/attest` at its
    `v4` major, under `id-token: write`, `contents: read` and
    `attestations: write`;
  - `actions/attest` is a JavaScript action on Node 24 with no nested
    `uses:`, so the commit this repository pins is the code that runs. The
    wrapper adds a second pin, chosen upstream, which this repository's pin
    guard cannot read.

  What guarantees SLSA provenance is R-HRP-3's input rule: `actions/attest`
  makes provenance exactly when given neither an `sbom-path` nor a predicate
  input, and AC-HRP-4's guard refuses either. Reopen if a later
  `actions/attest` major changes how it chooses its mode, which the floor
  would make a deliberate step.
- **DEC-HRP-005:** the attesting action has nothing nested to pin. It is a
  JavaScript action with no nested `uses:`. The plan's owner setting
  "Require actions to be pinned to a full-length commit SHA" therefore has
  nothing inside it to refuse, and the actions allowlist admits it as a
  GitHub-authored action. Confirming the action's `runs:` block at the pin is
  a `tasks.md` step, not a suite assertion, because reading the action's own
  file needs the network (`pin-actions-by-sha` C-ASP-4).
- **DEC-HRP-006:** the release notes are rendered in `build`, on a tag only,
  by a stdlib tool. The `release` job cannot render them: it checks out
  nothing, by DEC-HRP-007. `build` already runs the tagged tree under
  `contents: read`, and the changelog it reads is the tagged one, which is
  the right text for the tag. Tag-only, because a dry run on `dev` precedes
  the version's section and would fail. Placed before the `dist` upload, so a
  tag pushed without its section stops before anything is published, the same
  ordering the tag-version check already has. `if-no-files-found: error` on
  the upload keeps a missing file from passing as an empty artifact. The
  rejected fallback is `gh release create --generate-notes`. Under
  squash-into-`dev` and merge-commit promotions it lists promotion merges and
  pull-request titles, while the changelog is the curated record (Keep a
  Changelog). It is the recorded fallback if the tool is rejected in review.
- **DEC-HRP-007:** the `release` job is checkout-free and runs only two `gh`
  commands. Resolution B1 of the plan's review: a job holding
  `contents: write` must never execute the tagged tree, because a tag's author
  controls that tree, the reason the gate already reads `tag-ancestry` from
  the default branch. "No checkout" alone leaves other doors open: a
  `git clone`, a `gh repo clone`, an interpreter running a downloaded script.
  So the guard pins the whole job rather than denying paths.
  That is stronger than the plan's "no `run:` invoking a tree path", and with
  no checkout there is no tree path to invoke. The tag reaches the shell
  through `GITHUB_REF_NAME` in the environment, the safe form
  `add-witness-ci-artifacts` DEC-WCA-014 models, although only the owner pushes
  tags here.

  The guard parses no shell. That was first decided at Copilot's review of
  #59 (2026-10-16), which replaced the first review's command reader with a
  comparison of the two scripts:
  - That reader joined continuations, lexed each line with `shlex` in POSIX
    mode, and took a word beginning with `#` as a comment.
  - Three scripts passed it while bash ran a command outside the
    allow-list. In `--title "#notes"; printf x`, POSIX lexing removes the
    quotes, so the comment rule swallows the rest of the line. In
    `--title "$(printf x)"`, a quoted command substitution is one
    argument, which the command-position check never inspects. A backtick
    substitution passes the same way.
  - Patching the reader for quotes and substitutions would still leave a
    partial shell parser, and every gap it kept would be a command run
    with `contents: write`.

  Comparing the two scripts was not enough either. The second adversarial
  review (2026-10-16) showed that the job around them still let other code
  run:
  - `run_scripts` matches only a block-style `run:` key, so a step written
    as a flow mapping, `- {name: x, run: make pre-pr}`, is a real step that
    the reader never returns;
  - a step `env:` can set `BASH_ENV`, which a non-interactive bash sources
    before the fixed command, or redefine `GITHUB_SHA` and `GITHUB_REF_NAME`,
    which DEC-HRP-009's binding reads;
  - a job `container:` or `services:`, or a step `working-directory:`, runs
    the same text somewhere else;
  - `run_scripts` folds a `>-` scalar by joining lines with spaces, but YAML
    turns a blank line inside it into a newline, so a blank line splits the
    create in two while the folded text still matches.

  The scripts are not the unit; the job is. So the test pins the job's
  whole text, and a change to the job edits the test in the same commit,
  which is the review a write-scoped job deserves. The text is compared,
  not parsed:
  - PyYAML is deliberately not a dependency;
  - an exact comparison has no grammar to get wrong;
  - only trailing whitespace and the action pins are let vary, the pins so
    that Dependabot's SHA bumps stay green, their form being
    `tests/test_workflow_pins.py`'s to check.

  The top-level `env:` and `defaults:` sit outside the block but reach
  every job, so they are held separately.
- **DEC-HRP-008 (revised at the first review):** the `release` job holds
  `contents: write` and `attestations: read`, the second beyond the plan's
  block. A job-level block replaces the top-level one, so every scope it omits
  is `none`. The REST endpoint `gh attestation verify` calls, "List
  attestations", allows public reads. So on this public repository
  `contents: write` alone likely suffices, which is unverified until the
  0.4.0 run. The scope is declared anyway, for a reason specific to this job.
  It cannot be rehearsed before the first real tag, and a re-run of that tag's
  run uses the same workflow file. A missing scope could therefore not be
  repaired after the files are on PyPI, except by a new version. A read scope
  costs nothing. `contents: write` stays the only write scope in either
  workflow apart from `publish`'s `id-token` and `attestations`.
- **DEC-HRP-009:** verify, then create, in that order and as two steps. A
  verification failure leaves no release rather than an unverified one. The
  files are already on PyPI by then, because the `release` job needs
  `publish`, and that ordering is accepted. A GitHub release must never carry
  bytes the provenance does not cover, and PyPI's own publish attestation
  already covers what PyPI holds.
  - **The ref and the commit.** `--source-ref` binds the verification to the
    tag's ref. `--source-digest "$GITHUB_SHA"` binds it to the one commit
    the tag names when the run starts, which a ref alone does not fix.
  - **`--verify-tag` is load-bearing.** Without it, `gh release create`
    creates a missing tag from the default branch's tip, a tag the release
    model forbids, made by `GITHUB_TOKEN`.
  - **Immutable releases.** One command with the assets attached is
    compatible with them. The CLI creates a draft, uploads and then
    publishes, and immutability applies from the publish, so no step of this
    job edits a published release.
- **DEC-HRP-010:** the `release` job's failure modes, each named with its
  remedy, so none reads as a pass.
  - **(i) Verification fails.** No release is created and the files are on
    PyPI. Investigate before anything else. Never re-run with the verification
    removed or softened.
  - **(ii) `gh release create` fails before publishing** (an API error, an
    upload cut off, a notes body the API refuses). A draft may be left. Drafts
    are mutable, so delete it and re-run the failed job.
  - **(iii) The release already exists**, because a person created it. The
    job fails, and the runbook forbids the hand step for that reason.
  - **(iv) `gh` is absent from the runner, or lacks `gh attestation`.** The
    first step fails. GitHub-hosted images ship a current `gh`, which is
    likely but first observed on the 0.4.0 tag.

  In every case the remedy is "Re-run failed jobs" on the same run. `publish`
  succeeded and is not re-run, and the artifacts are still retained. Failing
  that, verify locally and run the same `gh release create … --verify-tag`.
  A tag is never moved and never re-pushed.
- **DEC-HRP-011:** `persist-credentials: false` on both release checkouts.
  The token is read-only here, but `gate` runs `make pre-pr` over the tagged
  tree after a `pip install` of unpinned dev extras, and nothing in that
  ladder needs a credential. A credential every later step can read is
  exposure with no use, wherever the checkout keeps it. The gate's fetches
  then run unauthenticated, which this public repository permits.
  - **The private-repository failure mode** is recorded in the workflow itself
    (R-HRP-2) rather than only here: the first fetch exits 128 before
    `make pre-pr`.
  - **The remedy** is a header the step's own script exports through git's
    environment configuration. It reaches the step's own fetch and
    `tag-ancestry`'s, which a per-command `git -c` would not, and dies with
    the step's shell. The value is
    `AUTHORIZATION: basic <base64 of x-access-token:TOKEN>`, which an `env:`
    expression cannot compute, hence the export inside the script.
    Re-enabling persistence would hand the token back to every step.
  - **The workflow assumes a public repository elsewhere too.** Artifact
    attestations need GitHub Enterprise Cloud on a private repository, per
    the action's README, so on a private repository under any other plan the
    attest step fails before the `release` job.

  Only a tag can exercise the ancestry step, so the gate rehearsal of
  `tasks.md` is the observation, not a criterion.
- **DEC-HRP-012:** no `concurrency` block anywhere in `release.yml`, the new
  job included. `harden-ci-workflows` DEC-HCW-003 stands: a tag is its own
  ref, two tags are two runs, and a release run must never be cancelled,
  least of all between `publish` and `release`, where cancelling would leave
  files on PyPI with no GitHub release.
- **DEC-HRP-013:** the `release` job's `timeout-minutes` is the configured
  range's floor. DEC-HCW-010's sizing rule, three times the measured duration
  rounded up to a multiple of five, has no measurement to apply until the
  0.4.0 tag. Two verifications and one create are seconds of work, and the
  range keeps a typo from becoming six hours.
- **DEC-HRP-014:** the Dependabot cooldown is seven days on the
  `github-actions` entry. A version update now waits a week after an action
  release instead of the platform's unconfigured three days. That gives a
  compromised or broken release time to be found and pulled before this
  repository proposes it. Security updates are exempt by the platform's rule,
  so a fix still arrives at once. GitHub Actions supports only
  `default-days`, not the per-semver keys, so one number is all there is to
  set. The `actions-minor` group already matches `actions/*`, so
  `actions/attest`'s minor and patch updates join that one grouped pull
  request.
- **DEC-HRP-015:** `CODEOWNERS` declares and does not enforce. One person
  maintains this repository, the branch rulesets require no approving review,
  and GitHub does not let an author approve their own pull request, so
  "require review from code owners" would block every pull request the owner
  opens. What the file does now is name the owner of every path and request
  their review on pull requests others open, Dependabot's included. Reopen
  enforcement when a second maintainer exists.
- **DEC-HRP-016:** the security policy's terms. Seven days to acknowledge and
  ninety to fix or explain are the common coordinated-disclosure defaults,
  and the advisory at the fix or at day ninety puts a bound on silence.
  Fixes ship the way every other change reaches production, a `hotfix/*`
  branch into `main` and a patch release (`docs/hooks.md` "Branching and
  promotion"), and only the latest minor is supported, as the policy already
  says. Before 1.0 a back-port would be a second release line nobody tests.
  The verification commands use placeholders. `SECURITY.md` is root markdown,
  which the adopter-corpus guards read for copyable versions, and a literal
  version there would be one more line each release-prep has to move.
  Immutable-release attestations (`gh release verify-asset`) are not named
  there, because they exist only while the owner's immutable-releases setting
  is on. Naming them waits until that setting is confirmed.
- **DEC-HRP-017 (revised at the first review):** the runbook and the release
  skill change with the workflow. `lean-production-tree`'s R-LPT-4 lists "the
  GitHub release cut from the `[X.Y.Z]` section" as a runbook step. It does
  not say who cuts it. In the runbook it moves into `docs/hooks.md`, no job
  creates a release, so the step can only be a person's. Once the `release`
  job exists, a person following that step would either fail, because the job
  made the release first, or make the job fail, because the person made it
  first. So the step is amended in place. It keeps its position in R-LPT-4's
  sequence and keeps naming the `[X.Y.Z]` section as the source of the notes,
  so R-LPT-4 stays true of the runbook, and it says the `release` job cuts the
  release and the person confirms it. The fallback is "re-run the job", never
  "do it by hand" as a first resort. This change lands after
  `lean-production-tree`, so that it amends the one runbook that package
  writes. Landing first would leave that package writing a step whose actor
  is wrong.
- **DEC-HRP-018:** the floating-`v1` row keeps its decision and changes its
  reason. The decision is `add-github-action-contract` DEC-GA-011: no
  floating major tag and no Marketplace listing before 1.0. That package
  leaves the tree with `lean-production-tree`, and is read at
  `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/add-github-action-contract`.
  DEC-GA-011 and the row give a second reason: moving a tag would need
  `contents: write`, which the release workflow does not hold. That reason is
  false after this change. The first stands, and was always the real one: a
  moving major promises that every release under it is compatible with the
  one a workflow pinned, which a pre-1.0 contract does not promise. The new
  write scope is also no step toward a moving tag. It belongs to a job that
  creates one release for the exact tag pushed, and the plan's tag ruleset
  forbids updating a `v*` tag.
- **DEC-HRP-019:** new tests sit beside the existing ones, which keep their
  names and bodies. `test_release_workflow_is_gated_and_uses_trusted_publishing`
  is cited on other packages' verification lines, and its assertions stay
  true. The new properties go in new functions over pure readers of the
  workflow text, so each real-tree assertion and its planted counter-example
  run through the same code (`harden-ci-workflows` R-HCW-15). The guards that
  already judge the new lines are cited by name and need no edit: the pin,
  agreement and floor guards; the timeout and permission-comment guards; the
  no-`concurrency` guard; and the publisher's explicit-attestations guard.
  The cooldown guard lives in `tests/test_workflow_pins.py` beside both
  Dependabot readers (DEC-TSS-016). Every MUST of R-HRP-4, R-HRP-6 and
  R-HRP-7 has a planted counter-example of its own (AC-HRP-7, AC-HRP-11), so
  none passes only because the real tree happens to satisfy it.
- **DEC-HRP-020:** stages and selectors. Verification lines cite `make test`
  or `make pre-pr`. Existing tests whose names survive are cited by
  selector, and the new tests are not named until they exist, because the
  citation guard resolves every selector against the collected test functions
  (`lean-production-tree` DEC-LPT-018). The implementation commit adds them,
  keeping each stage.
- **DEC-HRP-021 (not adopted):** an SBOM. The publish attestation and the build
  provenance cover integrity. A CycloneDX SBOM of a wheel with no runtime
  dependencies lists one component, and the clean-venv smoke install in
  `build`, `test_new_modules_stdlib_only` and
  `test_runtime_dependencies_stay_empty` already prove that claim. Reopen
  when `[project] dependencies` becomes non-empty, or when an adopter is under
  a regulatory SBOM requirement. The minimal shape for then needs no new
  action:
  - `build` generates a CycloneDX SBOM of the smoke venv with the
    `cyclonedx-bom` package's command-line tool and uploads it as an
    artifact;
  - `publish` gains a second `actions/attest` step with `sbom-path` beside
    `subject-path: dist/*`, which is SBOM mode, while the first step keeps
    R-HRP-3's provenance inputs;
  - the `release` job verifies it with
    `--predicate-type https://cyclonedx.org/bom` and attaches it as a third
    asset.

  The plan's sketch named a custom `predicate-type`, which is
  `actions/attest`'s custom mode and needs a predicate file, not an SBOM.
- **DEC-HRP-022 (not adopted):** a dev lockfile or a `pip` Dependabot entry;
  a workflow dependency lockfile; Scorecard and dependency-review workflows.
  - **The dev lockfile and `pip` entry.** The dev extras float on purpose,
    and `.github/dependabot.yml`'s header, the thresholds guard's tool-pin
    refusal and `test_dependabot_does_not_add_a_pip_ecosystem` hold that.
    Reopen when a floating tool breaks CI twice in one minor series.
  - **The action-lock file.** GitHub's workflow lockfile is a public preview.
    Reopen at general availability, when `tests/test_workflow_pins.py` would
    read it as a second source of the pins.
  - **Scorecard.** A third workflow file, against the two-workflow set
    `test_every_workflow_is_scanned_by_the_threshold_guard` pins, which needs
    `security-events: write` and `id-token: write`. Reopen when an adopter
    asks for the badge.
  - **Dependency review.** Needs only read access but has no runtime
    dependency to review. Reopen with the first runtime dependency.
  - **CodeQL** is the owner's default-setup setting, not a workflow.
- **DEC-HRP-023 (not adopted):** a signed-commits ruleset, a floating `v1`
  tag or Marketplace listing, and a `CONTRIBUTING.md`.
  - **Signed commits.** Integrity rests on provenance and attestations. A
    signed-commit rule judges every commit a promotion merge carries in, so
    one unsigned commit anywhere in a release's history refuses the promotion.
    Reopen when every commit reaching `dev` is made by GitHub or signed.
  - **The floating tag and Marketplace.** Held to 1.0, by DEC-HRP-018.
  - **`CONTRIBUTING.md`.** `AGENTS.md`, `docs/hooks.md` and the pull-request
    template already carry it, and a root markdown file costs a
    `REQUIRED_DOCS` row, which
    `test_every_root_markdown_file_is_wired_into_the_docs_gate` enforces.
    Reopen when a contributor says they could not find the contributing
    rules.
- **DEC-HRP-024:** the hosted observations are `tasks.md` gates, not
  criteria. No test can observe a remote run. A criterion citing a stage that
  cannot see its subject is a pass nobody observed (`lean-production-tree`
  DEC-LPT-017). So every criterion here is observed on the implementation
  branch's tree.
  - **The `dev` dry run** shows `gate` and `build` green, `publish` and
    `release` skipped, and `make pre-pr` passing without a persisted
    credential. It is recorded before the pull request leaves draft.
  - **The gate rehearsal** is the owner's, after the merge. The tag
    `v0.0.0-gate-rehearsal` goes on the `dev` tip, which is not on `main`'s
    first-parent chain. It is the only run that exercises the
    unauthenticated fetch, the worktree and `tag-ancestry` for real, and
    `tag-ancestry` must exit 1, by design, not 128 from git. Nothing
    downstream runs. Were the ancestry check ever to pass, `make pre-pr` would
    still run first, then `build`'s version check refuses
    `0.0.0-gate-rehearsal` before any upload, and the notes tool refuses a
    non-numeric version. No release references the tag, and immutability
    locks only a published release's tag, so the owner deletes it
    afterwards. This retires the plan's risk that a first real tag "burns"
    on a fetch nobody had exercised.
  - **The first real exercise** of `publish`'s attest step and of the
    `release` job is the 0.4.0 tag, recorded by that release.
- **DEC-HRP-025:** sequencing. This change edits the workflow `v0.3.0`'s tag
  runs. Merged into `dev` before that tag, it would be promoted with 0.3.0
  and run unrehearsed on the first public release. So the package and its
  implementation land apart. The package lands first and alone, in #59; it
  edits no workflow, as #58 did for `lean-production-tree`. The
  implementation merges after `v0.3.0` is tagged and published, and after
  `lean-production-tree`'s implementation (DEC-HRP-017), and it ships in
  0.4.0. No criterion can observe a remote tag, so the ordering is held by
  `tasks.md` Milestone 2's gate. The implementation pull request stays a
  GitHub draft until that gate is recorded, so it cannot merge early by
  accident. It is squash-merged into `dev`.
- **DEC-HRP-026 (added at the first review):** the notes' boundary is the
  section, and their length is not capped.
  - **Link definitions.** They end the body only when they close the
    section, as the changelog's link block closes its last one. A link
    definition with other content after it inside a section is a reference
    link the notes would carry without its target, or half of a malformed
    file. Either way it is refused, not guessed at.
  - **No ceiling.** GitHub's limit on a release body is unconfirmed here, and
    the largest section the changelog holds, measured in `tasks.md`, is
    already long. A ceiling chosen without a confirmed limit would refuse a
    good release or admit a bad one. A body the API refuses is DEC-HRP-010's
    case (ii), with its remedy. Reopen with a ceiling once the limit is
    documented and a section approaches it.

---

## Acceptance Criteria

- [ ] **AC-HRP-1:** In `release.yml` every `actions/checkout` step sets
  `persist-credentials: false` under its own `with:`. `gate`'s keeps
  `fetch-depth: 0`. The comment above the ancestry step states the
  unauthenticated fetches, the private-repository exit 128 and the remedy
  exported inside the step's script, which is read directly. (R-HRP-1,
  R-HRP-2, DEC-HRP-011)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-2 (non-success):** A planted release workflow whose checkout has
  no `persist-credentials` key, and one whose checkout sets it `true`, are
  each named with the job and the line, while a checkout setting it `false` is
  not. (R-HRP-1)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-3:** `publish` runs `actions/attest` after the `dist` download
  and before the publisher, with `subject-path: dist/*` under its `with:`, no
  predicate input and no `sbom-path`. Its permissions block is exactly
  `contents: read`, `id-token: write` and `attestations: write`, under the
  extended comment, and the publisher still declares `attestations: true`
  under its own `with:`. (R-HRP-3, DEC-HRP-001, DEC-HRP-002, DEC-HRP-004)
  _Verified by:_ `pytest -k "test_publish_declares_attestations_explicitly or test_every_job_level_permissions_block_carries_a_comment"` · stage: `make test`

- [ ] **AC-HRP-4 (non-success):** Each planted `publish` below is named:
  - one whose attest step follows the publisher;
  - one with no attest step;
  - one whose block lacks `attestations: write`;
  - one attesting a subject other than `dist/*`;
  - one whose attest step carries a predicate input;
  - one whose attest step carries `sbom-path`.

  (R-HRP-3, DEC-HRP-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-5:** `actions/attest` is pinned to a 40-hex commit with its
  release tag in a trailing comment and has a floor row. Every copy of the
  upload and download actions the new steps use carries the same pin as the
  existing copies. (R-HRP-3, R-HRP-6, R-HRP-10, DEC-HRP-004)
  _Verified by:_ `pytest -k "test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag or test_every_third_party_action_meets_its_major_floor or test_every_reference_to_one_action_agrees_on_one_ref"` · stage: `make test`

- [ ] **AC-HRP-6:** `build` runs `tools/release_notes.py` on the tag's version
  into a file under `RUNNER_TEMP`, and uploads it as `release-notes` with
  `if-no-files-found: error`. Both steps are conditioned exactly on the tag
  test and come after the tag-version check and before the `dist` upload.
  The smoke step and the version check are unchanged. (R-HRP-4, R-HRP-9,
  DEC-HRP-006)
  _Verified by:_ `pytest -k "test_release_and_ci_share_one_smoke_tool or test_release_workflow_is_gated_and_uses_trusted_publishing"` · stage: `make test`

- [ ] **AC-HRP-7 (non-success):** Each planted `build` below is named:
  - one whose notes step has no tag condition;
  - one whose notes steps follow the `dist` upload;
  - one uploading under another artifact name;
  - one whose notes upload omits `if-no-files-found: error`.

  (R-HRP-4, DEC-HRP-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-8:** The `release` job needs `publish`, its condition is exactly
  `github.ref_type == 'tag'`, its timeout lies inside the configured range,
  and its permissions block is exactly `contents: write` and
  `attestations: read`, under a comment inside the job's own body. It is the
  only job in either workflow holding `contents: write`, and `ci.yml` holds
  no write permission at all. (R-HRP-5, DEC-HRP-008, DEC-HRP-013)
  _Verified by:_ `pytest -k "test_every_job_in_every_workflow_has_a_timeout_inside_the_range or test_every_job_level_permissions_block_carries_a_comment or test_no_write_permission_anywhere_in_ci"` · stage: `make test`

- [ ] **AC-HRP-9 (non-success):** A planted second job holding
  `contents: write` is named, and so are one holding it in the flow form
  `permissions: {contents: write}` and one holding `permissions: write-all`. So are a `release` job conditioned on anything
  but the exact tag test (an added `always()`, a dispatch alternative), one
  needing `build` instead of `publish`, and one whose block grants any
  further scope. (R-HRP-5)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-10:** The `release` job has no checkout. Its steps are exactly
  the two downloads and the two `run:` steps, and its whole block, once
  normalised, equals the pinned job the test holds. `release.yml`'s top-level
  `env:` holds `PYTHON_DEFAULT` alone, and it declares no top-level
  `defaults:`. `GH_TOKEN` comes from
  `github.token` and `GH_REPO` from `github.repository` through `env:`, and
  the tag through `GITHUB_REF_NAME`. Each downloaded file is verified with
  `--repo`, `--signer-workflow`, `--source-ref`, `--source-digest` and
  `--deny-self-hosted-runners` before the one `gh release create`. That
  command passes `--verify-tag`, the downloaded files and the downloaded
  notes. No step carries a soft-fail token or an after-failure condition.
  (R-HRP-6, R-HRP-7, R-HRP-8, DEC-HRP-007, DEC-HRP-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-11 (non-success):** Through the same check, each planted
  `release` job below is named, each with its own offender.

  Reaching the tree, or running anything but the pinned job:
  - an `actions/checkout` step;
  - a `run:` invoking `python tools/release_notes.py`;
  - `git clone`;
  - `gh repo clone`;
  - `make`;
  - `gh api`;
  - `gh release upload`;
  - a third artifact download;
  - a forbidden command on its own line after a `gh` line;
  - an unquoted `${GITHUB_REF_NAME#v}` followed by `; make pre-pr`;
  - a quoted `"#notes"` followed by `; printf x`;
  - a quoted command substitution, `"$(printf x)"`;
  - the same substitution in backticks;
  - the create command split across two lines;
  - a `shell:` key on a step, and a `defaults.run.shell` on the job and on
    the workflow;
  - a step written as a flow mapping, `- {name: x, run: make pre-pr}`;
  - a step `env:` that adds `BASH_ENV`, or that redefines `GITHUB_SHA`;
  - a job `container:`, a job `services:`, and a step `working-directory:`;
  - a blank line inside the folded create;
  - a top-level `env:` key beside `PYTHON_DEFAULT`, and a top-level
    `defaults:`.

  Weakening the verification:
  - the release created before the verification;
  - a create lacking `--verify-tag`;
  - a verification lacking `--repo`;
  - a verification lacking `--signer-workflow`;
  - a verification lacking `--source-ref`;
  - a verification lacking `--source-digest`;
  - a verification lacking `--deny-self-hosted-runners`.

  Running after a failure, or taking its token or tag the wrong way:
  - a step with `if: always()`;
  - a step with `if: failure()`;
  - a step with `continue-on-error`;
  - a step with `|| true`;
  - `GH_TOKEN` taken from `secrets.*` instead of `github.token`;
  - the tag interpolated inline into `run:`.

  (R-HRP-6, R-HRP-7, R-HRP-8, DEC-HRP-007, DEC-HRP-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-12:** `release.yml` declares no `concurrency` block. The
  `gate → build → publish` wiring, the ancestry step and the read-only top
  level are as they were, and `release` follows `publish`. (R-HRP-9,
  DEC-HRP-012, C-HRP-2)
  _Verified by:_ `pytest -k "test_release_has_no_concurrency_group or test_release_gate_checks_tag_ancestry_against_production or test_release_workflow_is_gated_and_uses_trusted_publishing"` · stage: `make test`

- [ ] **AC-HRP-13:** Against a planted changelog, `tools/release_notes.py`
  prints the named section's body and exits 0. The `###` groups are kept, the
  heading and the next section are excluded, link definitions that close the
  section are dropped, and outer blank lines are trimmed. Against this
  repository's changelog it prints a non-empty section for the package's
  current version. It imports only the standard library and `_common`.
  (R-HRP-13, R-HRP-15, DEC-HRP-026)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-14 (non-success):** In each of these cases the tool exits 2,
  with empty stdout and one stderr line naming the version and the changelog
  path:
  - a version with no section;
  - an empty section;
  - a version written `v0.4.0`;
  - `Unreleased`;
  - `0.0.0-gate-rehearsal`;
  - a version whose section appears twice;
  - a section with a reference-link definition in its middle and content after
    it;
  - a changelog path that does not exist.

  No case exits 1. (R-HRP-14, DEC-HRP-024, DEC-HRP-026)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-15:** With stdout an ASCII-encoded stream, the tool writes the
  section, em dashes and arrows included, as bytes that decode as UTF-8 to the
  section's text, and does not raise. (R-HRP-13)
  _Verified by:_ stage: `make test`

- [ ] **AC-HRP-16:** `python tools/release_notes.py` starts as a script from a
  throwaway working directory and returns a documented exit code, and the
  script is listed for that check. (R-HRP-15)
  _Verified by:_ `pytest -k test_gate_script_is_runnable_as_a_script` · stage: `make test`

- [ ] **AC-HRP-17:** The new script lints with every public docstring and no
  ratchet entry and type-checks under the strict configuration. The new test
  module carries the computed tiers, is flat and inside the line bound, and
  adds no exempted mypy code. The `tools/` coverage floors hold.
  `tools/AGENTS.md` stays within the nested-file line bound. It and
  `docs/architecture/c4.md` name the script as R-HRP-19 says, with every
  count true, which is read directly. (R-HRP-13, R-HRP-15, R-HRP-19)
  _Verified by:_ `pytest -k "test_every_tier_marker_matches_its_mechanical_criterion or test_the_tests_directory_stays_flat or test_no_test_module_exceeds_the_line_bound or test_every_listed_mypy_code_matches_its_ceiling_on_both_platforms or test_nested_agents_file_stays_short"` · stage: `make pre-pr`

- [ ] **AC-HRP-18:** The `github-actions` Dependabot entry declares a cooldown
  of seven days, under the version-updates-only comment, with the rest of the
  entry unchanged and no `pip` ecosystem. A planted entry with no `cooldown`
  is named. The composite action's directory is still watched. (R-HRP-11,
  DEC-HRP-014)
  _Verified by:_ `pytest -k "test_dependabot_does_not_add_a_pip_ecosystem or test_every_composite_action_directory_is_watched_by_dependabot"` · stage: `make test`

- [ ] **AC-HRP-19:** `.github/CODEOWNERS` exists and holds the one rule
  `* @ianshank` under its comment, which is read directly. (R-HRP-12,
  DEC-HRP-015)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-HRP-20:** `SECURITY.md` carries each part R-HRP-16 lists, says SLSA
  Build L2 and nowhere L3, names versions in its commands only through
  placeholders, and is
  still present and linked from the README. Every root markdown file is still
  wired into the docs gate, and every copyable tag still names the current
  version. The prose is read directly. (R-HRP-16, DEC-HRP-003, DEC-HRP-016)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_every_root_markdown_file_is_wired_into_the_docs_gate or test_every_copyable_tag_ref_names_the_current_version"` · stage: `make pre-pr`

- [ ] **AC-HRP-21:** `docs/hooks.md`'s `release` row, its "Releasing" runbook
  and the release skill's "Tag the production merge commit" step say what
  R-HRP-17 requires. The runbook's GitHub-release step keeps its place in
  R-LPT-4's sequence and names the `[X.Y.Z]` section as the notes' source.
  No document tells a person to create the GitHub release for a version tag.
  `docs/next-steps.md`'s floating-`v1` row is re-stated as R-HRP-18 requires.
  Every CI-table row still names a job or a workflow, every backticked path in
  the skill resolves, and the skill invokes only real promotion subcommands.
  The prose is read directly. (R-HRP-17, R-HRP-18, DEC-HRP-017, DEC-HRP-018)
  _Verified by:_ `pytest -k "test_every_hooks_ci_table_row_names_a_job_or_workflow or test_path_like_backtick_references_resolve_to_real_files or test_release_skill_uses_only_real_promotion_subcommands or test_docs_check_passes"` · stage: `make pre-pr`

- [ ] **AC-HRP-22:** `CHANGELOG.md`'s `[Unreleased]` section carries the
  `### Changed` entry R-HRP-19 describes, no released section changed, and
  every versioned section still links to its tag. The entry is read
  directly. (R-HRP-19)
  _Verified by:_ `pytest -k test_every_changelog_version_links_to_its_release_tag` · stage: `make test`

- [ ] **AC-HRP-23 (non-success):** None of what DEC-HRP-021 to DEC-HRP-023
  decline has arrived. The guards holding three of those absences pass
  unedited: no `pip` ecosystem, exactly two workflow files, every root
  markdown file wired. No step, input or asset in `release.yml` names an SBOM,
  and no tag-moving command appears anywhere in it. (R-HRP-20)
  _Verified by:_ `pytest -k "test_dependabot_does_not_add_a_pip_ecosystem or test_every_workflow_is_scanned_by_the_threshold_guard or test_every_root_markdown_file_is_wired_into_the_docs_gate"` · stage: `make test`

- [ ] **AC-HRP-24:** The rule inventory, the golden validate, graph and rules
  hashes and the empty runtime-dependency list are unchanged. The diff
  touches no file under `openspec_graph/` and neither the Makefile, `ci.yml`,
  the composite action nor the templates, which is read against the base.
  (C-HRP-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_runtime_dependencies_stay_empty"` · stage: `make test`

- [ ] **AC-HRP-25:** `tools/check_no_hardcoded_thresholds.py` is absent from
  the diff and passes on the finished tree, every workflow is in its scan,
  and its silence on timeout lines still holds. (C-HRP-3)
  _Verified by:_ `pytest -k "test_every_workflow_is_scanned_by_the_threshold_guard or test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency"` · stage: `make pre-pr`

- [ ] **AC-HRP-26:** The whole ladder is green on the implementation branch's
  head, this repository's own validate over every package included. Every
  selector in every spec resolves, this spec pins no count or line number,
  and every measurement in `tasks.md` names its commit and its command. A
  review property, read directly. The ladder confirms the package validates
  clean. (C-HRP-2, C-HRP-4, DEC-HRP-020)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Preconditions | none — recorded on `tasks.md` Milestone 2's gate | `v0.3.0` tagged, published and an ancestor of `origin/dev`; `lean-production-tree`'s implementation merged into `dev`; the `actions/attest` pin re-confirmed with its `runs:` block; the implementation pull request a draft until all of it is recorded (DEC-HRP-025) |
| Focused | `make test` | AC-HRP-1..16, AC-HRP-18, AC-HRP-22..24 — every new guard green on the real tree and red on its planted counter-example; every guard this change leans on still green unedited |
| Full | `make pre-pr` | AC-HRP-17, AC-HRP-19..21, AC-HRP-25, AC-HRP-26 — lint and strict typecheck of the new script, the docs gate, the thresholds guard, the `tools/` coverage floors, and this repository's own validate over every package |
| Hosted | none — recorded in `tasks.md` | the dry run of the implementation branch before the pull request leaves draft, and of `dev` after the merge (`gate`, `build` green; `publish`, `release` skipped); the owner's gate rehearsal after the merge (`tag-ancestry` exit 1, the fetch succeeded, nothing built); the 0.4.0 tag's first run of the attest step and the `release` job, recorded by that release (DEC-HRP-024) |
