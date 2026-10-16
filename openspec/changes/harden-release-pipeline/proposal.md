# Change: Harden the Release Pipeline — Build Provenance, a Verified GitHub Release, No Persisted Credential, a Written Disclosure Policy

## Why

`.github/workflows/release.yml` is the one path by which this repository's
code reaches anyone who did not clone it, and its posture is good but
incomplete. Trusted publishing mints a short-lived OIDC token instead of a
stored secret, and the PyPI publisher uploads a PEP 740 publish attestation
for each file, so a downloader can check *who published* a file. Nothing lets
them check *what built it, from which commit, in which workflow*. The GitHub
release that should carry the same two files is cut by hand from the
changelog section after the run. Both checkouts that run the tagged tree
leave the job's token in `.git/config` for every later step, including the
whole pre-PR ladder and a `pip install` of the dev extras. `SECURITY.md` gives
a reporting route but no scope, no timeline, no disclosure terms, no safe
harbour, no word on how a fix ships, and no way to verify a download. No
`CODEOWNERS` file exists. Dependabot opens a pull request for a new action
release the week it ships. And one recorded deferral, the floating `v1` tag,
rests on a permission fact this change makes false.

This is Phase 2.1 of the session plan for a lean, production-grade `main`,
with that plan's Phase 2.3 deferrals and its peer-review resolutions B1–B14
and A17. The plan is not tracked (`lean-production-tree` DEC-LPT-005), so
every decision this package takes from it is restated in
`specs/release-pipeline/spec.md`, and every fact below was re-read against
this tree.

**Evidence:** read on `claude/lean-production-tree` at `4278d4c` (`dev` at
`c0ff090` plus `lean-production-tree`'s draft, which touches only
`openspec/`), 2026-10-16. `planlint --target . validate --fail-on ERROR`
exited 0 before any file of this package existed. Line numbers are those of
that tree. A sibling landing first may move a line without moving the fact.

- **What the release workflow does today.** `release.yml:14-18` triggers on
  `v*` tags and `workflow_dispatch`; `:20-21` holds the top-level
  `contents: read`. `gate` (`:29-68`) checks out with `fetch-depth: 0` and
  nothing else (`:34-36`). On a tag only (`:59`) its ancestry step fetches the
  default branch (`:63`), adds a worktree of it (`:64`) and runs
  `tools/check_promotion.py tag-ancestry --fetch` from that worktree (`:65`).
  Then it runs `make pre-pr` (`:67-68`). `build` (`:70-117`) checks out with
  no `with:` at all (`:76`), builds, checks the licence, smoke-tests the wheel
  in a clean venv, refuses a tag that differs from the packaged version
  (`:105-112`) and uploads `dist` (`:114-117`). `publish` (`:119-148`) runs on
  a tag only (`:122`), in environment `pypi` (`:125`), under a comment
  (`:126-129`) explaining its block of `contents: read` + `id-token: write`
  (`:130-132`). It downloads `dist` (`:134-137`) and runs the pinned
  `pypa/gh-action-pypi-publish` with `attestations: true` (`:139-148`). There
  is no fourth job, no attestation step, and no `persist-credentials` key
  anywhere in the file.
- **`actions/checkout` persists the token by default.** The pinned
  `actions/checkout@3d3c42e…` (`v7.0.1`) declares `persist-credentials` with
  `default: true`, "Whether to configure the token or SSH key with the local
  git config" (its `action.yml:52-54`). Of `ci.yml`'s checkouts, those at
  `:311`, `:436`, `:475` and `:528` set it `false` and the rest leave the
  default. `graph-diff` runs `git fetch origin "${{ github.base_ref }}"` at
  `ci.yml:250`.
- **What the gate's fetch does without a credential.** `tag_ancestry`
  (`tools/check_promotion.py:379-430`) runs its own `git fetch` when given
  `--fetch` and returns exit 2 if that fails (`:399-406`). It returns exit 1
  for a commit that is not on the production branch's first-parent chain
  (`:428-429`). The workflow step's own `git fetch` at `release.yml:63` runs
  first, under Actions' `bash -e`, so on a repository that needs
  authentication to fetch, git's own exit 128 ends the step before
  `tag-ancestry` or `make pre-pr` runs. On this public repository the
  unauthenticated fetch succeeds. The ancestry step is tag-only, so no
  `workflow_dispatch` dry run ever exercises it.
- **The action the plan names, re-confirmed.** The refs advertisement of
  `https://github.com/actions/attest-build-provenance` (fetched over HTTPS on
  2026-10-16, the data `git ls-remote --tags` prints) lists `refs/tags/v4.2.2`
  at `4d101475d8b20a2381f78447822ac1eab6504dd8` (a lightweight tag). The
  annotated `refs/tags/v4` peels to the same commit (`v4^{}`), and no `v5`
  exists. Its `action.yml` at that commit is `using: "composite"` with one
  step, `uses: actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d # v4.2.1`,
  so the inner ref is a 40-hex commit. Its README: "As of version 4,
  `actions/attest-build-provenance` is simply a wrapper on top of
  `actions/attest` … new implementations should use `actions/attest`
  instead". `actions/attest`'s own refs list `v4.2.2` at
  `1e69f48acb82d1966a394da916b4c1698aa569d6`, one patch ahead of what the
  wrapper runs. `actions/attest@508db95…`'s `src/main.ts` writes the bundle
  to `path.join(await tempDir(), …)` (`:99`), where `tempDir` is
  `RUNNER_TEMP` (`:234-239`), never into the subject's directory. Its README
  lists `id-token: write` and `attestations: write` as the permissions an
  attesting job needs, and names three modes chosen from the inputs given:
  provenance (no SBOM or predicate input), SBOM (`sbom-path`) and custom
  (`predicate-type`/`predicate`).
- **What the GitHub CLI does with a release and an attestation.** From the
  help text of the `gh` 2.89.0 in this environment: `gh release create`, if
  "a matching git tag does not yet exist, one will automatically get created
  from the latest state of the default branch"; `--verify-tag` aborts
  instead. When assets are attached, "separate API calls are made to create
  the release as a draft, upload the assets, and then publish the release",
  and immutability "is enforced only after a release is published".
  `gh attestation verify` enforces the `https://slsa.dev/provenance/v1`
  predicate by default and takes `--repo`, `--signer-workflow`
  (`[host/]<owner>/<repo>/<path>/<to>/<workflow>`), `--source-ref` and
  `--deny-self-hosted-runners`. `gh release verify-asset` exists for
  immutable-release attestations.
- **The SLSA level, from GitHub's documentation source.** `github/docs`,
  `content/actions/concepts/security/artifact-attestations.md`: "Artifact
  attestations by itself provides SLSA v1.0 Build Level 2", and reusable
  workflows "can provide isolation between the build process and the calling
  workflow, to meet SLSA v1.0 Build Level 3".
- **Dependabot's cooldown, from the same source.** `github/docs`,
  `content/code-security/reference/supply-chain-security/dependabot-options-reference.md`,
  `cooldown`: "only available for _version_ updates, not _security_ updates".
  A default of 3 days applies when it is not configured. For GitHub Actions
  `default-days` is supported and the per-semver keys are not.
  `.github/dependabot.yml:29-60` is the one `github-actions` entry
  (`directories: ["/", "/.github/actions/planlint"]` at `:37`,
  `target-branch: "dev"` at `:40`, the `actions-minor` group over `actions/*`
  at `:49-60`), with no `cooldown`.
- **The guards that will judge the new lines already exist.**
  `tests/test_workflow_pins.py`: `ACTION_REF_SCAN` (`:39`) includes every
  workflow. `_pin_offenders` (`:78-97`) requires `@<40-hex> # vX.Y.Z`.
  `_floor_offenders` (`:128-152`) names a pinned action with no row in
  `[tool.specgraph.action_major_floors]` (`:146-149`), and that table
  (`pyproject.toml:239-246`) has no row for an attest action.
  `tests/test_workflow_posture.py`: every job carries a `timeout-minutes`
  literal inside `pyproject.toml:192-193`'s range (`:162-169`); every
  job-level `permissions:` block has a comment line above it inside the job
  (`:103-110`, through `tests/workflow_support.py:119-138`, the rule at
  `:136`). `workflow_job_blocks` (`tests/support.py:297-329`) starts a job's
  body after its two-space `name:` line, so a comment written between two
  jobs belongs to the earlier one. `release.yml` has no `concurrency`
  block (`:224-227`). The publish step declares `attestations: true` under
  its own `with:` (`:285-345`). That last reader splits the publish job into
  steps, so a new step beside the publisher does not disturb it.
- **What the release tests pin, and do not.**
  `tests/test_release_surface.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
  (`:30-77`) asserts the `gate → build → publish` wiring, `make pre-pr`, the
  smoke tool, `id-token: write`, no stored secret and the read-only top level.
  It says nothing about checkouts, attestations, a fourth job or
  `contents: write`. `test_release_gate_checks_tag_ancestry_against_production`
  (`:79-116`) pins the ancestry step. `test_every_workflow_is_scanned_by_the_threshold_guard`
  (`:118-138`) pins the workflow set to exactly `ci.yml` and `release.yml`
  (`:133`). The module stands well under the suite's line bound
  (`tests/test_suite_shape.py`, `MAX_TEST_MODULE_LINES`).
- **The changelog's shape, which the notes tool reads.** `CHANGELOG.md:6` is
  `## [Unreleased]`; versioned sections are `## [X.Y.Z] — <date>` (`:8`,
  `:720`, `:1781`). `###` groups sit inside them, no fenced block exists, and
  the link definitions are the last lines (`:1793-1796`), the only lines that
  begin with `[`. `tools/spec_status.py:106` and
  `tests/test_adopter_urls.py:338-361` already read the bracketed headings.
- **What a new tool joins.** `tests/test_gate_scripts.py:401-422` lists every
  script `python tools/<x>.py` must start, and `:443` refuses a listed script
  that is absent. `tools/AGENTS.md:11,33-39` counts the stdlib-only gate
  scripts, and `:41-47` lists the argv conventions. `docs/architecture/c4.md:82`
  names every script under `tools/` by group. `tools/_common.py`'s
  `read_text` returns `""` for a missing file (`:109-115`), and its
  `run_scripts` (`:542-571`) extracts a workflow's `run:` scripts.
  `openspec_graph/cli.py:999-1004` reconfigures stdout to UTF-8, which a
  script printing the changelog's em dashes needs on an ASCII console.
  `pyproject.toml:382` exempts `tools/*` from `T201`, and the docstring
  ratchet (`:383-420`) never gains an entry, so a new script carries every
  public docstring.
- **The documents that would become false.** `docs/hooks.md:88`, the
  `release` row, ends at "trusted publishing to PyPI, which uploads PEP 740
  attestations for both files". The 0.3.0 runbook has a person create the
  GitHub release (`docs/distribution-plan.md:176`, step 9) after verifying
  only the publish attestations (`:155-159`).
  `.claude/skills/planlint-release/SKILL.md:55-61` says the same.
  `lean-production-tree`'s R-LPT-4 moves that runbook into `docs/hooks.md`
  "Releasing" with "the GitHub release cut from the `[X.Y.Z]` section" as a
  step. `SECURITY.md:5-7` is the reporting route, `:54-59` says only the
  latest release is supported, and `:61-70` verifies an install with
  `planlint --version` and `rules --json` alone. `docs/next-steps.md:231`
  defers the floating `v1` tag because "moving a tag on every release needs
  `contents: write` in the release workflow, which currently holds
  `contents: read` plus `id-token: write` on the publish job alone".
  `.github/` holds no `CODEOWNERS`, and neither does the root or `docs/`.
- **Root markdown is adopter corpus.** `tests/test_adopter_urls.py:157-172`
  reads every root `*.md`, `SECURITY.md` included, for install commands and
  copyable tags (`_TAG_REF`, `:408-412`, matches `ianshank/planlint…@vX.Y.Z`),
  so a literal version in a new `SECURITY.md` command would be one more line
  the 0.4.0 release-prep must edit.
- **Sequencing.** `docs/next-steps.md:9-11` holds the after-0.3.0 work until
  `v0.3.0` is tagged and the package installs from PyPI, and the plan holds
  this phase to the same gate. There is a sharper reason here. This change
  edits the workflow that 0.3.0's tag runs. Merged into `dev` before that tag,
  it would be promoted with 0.3.0 and run untested, on the first public
  release. It ships in 0.4.0.

## What Changes

- **`.github/workflows/release.yml`**
  - `gate`'s and `build`'s checkouts gain `persist-credentials: false`. The
    comment above the ancestry step gains two sentences. The fetches run
    unauthenticated, which this public repository allows. On a repository
    that does not, the first fetch exits 128 before `make pre-pr`, and the
    remedy is an `http.extraheader` scoped to that step through its git
    environment, reaching both fetches and no later step, never the
    persisted credential.
  - `publish` gains, before the PyPI step,
    `actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2`
    with `subject-path: dist/*`. Its permissions block gains
    `attestations: write`, and the comment above it is extended in place to
    name the step that needs it. The publisher step and its
    `attestations: true` are unchanged.
  - `build` gains two tag-only steps after the version check and before the
    `dist` upload. One runs `python tools/release_notes.py "${GITHUB_REF_NAME#v}"`
    into `$RUNNER_TEMP/notes.md`. The other uploads that file as artifact
    `release-notes`, pinned like the existing upload.
  - A new job, `release`: `needs: publish`, `if: github.ref_type == 'tag'`,
    `timeout-minutes` inside the configured range, and a comment inside the
    job body above a block of `contents: write` + `attestations: read`. It
    has no checkout. It downloads `dist` and `release-notes` and runs
    `gh attestation verify` on every file, with `--repo`, `--signer-workflow`,
    `--source-ref` and `--deny-self-hosted-runners`. Only then does it run
    one `gh release create "$GITHUB_REF_NAME" dist/* --verify-tag --title … --notes-file …`.
    `GH_TOKEN` comes from `github.token` and `GH_REPO` from
    `github.repository`.
  - No `concurrency` block, and no other job changes.
- **`pyproject.toml`**: `[tool.specgraph.action_major_floors]` gains
  `"actions/attest-build-provenance" = 4`. Its header comment gains one
  sentence: the action is a composite, and its inner `actions/attest` pin
  is the wrapper's, outside what this repository's pin guard reads.
- **`.github/dependabot.yml`**: the `github-actions` entry gains
  `cooldown: { default-days: 7 }`, with a comment that the wait applies to
  version updates and never to security updates. Nothing else in the entry
  moves.
- **`.github/CODEOWNERS`** (new): `* @ianshank`, under a comment saying it
  names the owner and enforces nothing while the rulesets require no
  approving review.
- **`tools/release_notes.py`** (new, stdlib-only): `main(argv)` with
  `parse_args(argv[1:])`. It prints the body of `## [X.Y.Z]` for the version
  given, as UTF-8 whatever the console. It exits 2, naming the version and
  the file on stderr, when the section is absent or empty, the version is
  not `X.Y.Z`, the section appears twice, or the changelog cannot be read.
  It carries full docstrings.
- **`tests/test_release_notes.py`** (new): in-process against `main(argv)`,
  planted changelogs under `tmp_path`, every refusal of the tool, and the
  real changelog's current-version section.
  **`tests/test_release_surface.py`**: new tests in the release-workflow
  section, built on pure readers of the workflow text, each shown red on a
  planted workflow. They cover the checkouts, the publish job's attestation,
  the notes steps, the `release` job's wiring, permissions and commands,
  and the single `contents: write`. The existing tests keep their names and
  bodies. **`tests/test_workflow_pins.py`**: one test beside the Dependabot
  readers that the `github-actions` entry declares a cooldown.
  **`tests/test_gate_scripts.py`**: `release_notes.py` joins the
  runnable-script list.
- **`tools/AGENTS.md`** and **`docs/architecture/c4.md`**: `release_notes`
  is named among the stdlib-only scripts and the program-name-first argv
  convention, and every count either file states stays true.
- **`SECURITY.md`**: scope (in: the PyPI package, the composite action, the
  skill and plugin manifests, this repository's workflows; out: third-party
  actions, GitHub itself, adopters' repositories). Timeline: acknowledged
  within 7 days, a fix or a statement within 90. Disclosure: an advisory, and
  a CVE where one applies, at the fix or at day 90; the reporter may publish
  after day 90. A safe-harbour sentence. How fixes ship: a `hotfix/*` branch
  into `main` and the next patch of the latest minor; earlier minors get
  nothing. A verification section with `pipx run pypi-attestations verify pypi …`
  and `gh attestation verify <file> --repo ianshank/planlint --signer-workflow …`,
  placeholders for the version, stating SLSA Build L2 and never L3.
- **`docs/hooks.md`**: the `release` row names the build provenance, the
  verification and the automated release. In the "Releasing" runbook, the
  verify step gains `gh attestation verify`, and the step that cut the GitHub
  release by hand becomes a check that the `release` job created it with
  both files. **`.claude/skills/planlint-release/SKILL.md`** step 3 says the
  same.
- **`docs/next-steps.md`**: the floating-`v1` row is re-stated. The reason
  becomes the 1.0 contract, and the row no longer claims the release
  workflow holds no `contents: write`.
- **`CHANGELOG.md`** `[Unreleased]`: a `### Changed` entry headed with this
  package's backticked name.
- **Shared edit sites**, named so each merge is prepared rather than found.
  With `lean-production-tree`: `docs/hooks.md` "Releasing", which that
  package writes and this one amends at two steps; the release skill;
  `SECURITY.md`, where that package rewrites the "What is not a
  vulnerability" path; `docs/next-steps.md`, where that package edits the
  rows beside `:231`; and `tests/test_release_surface.py`'s Docker-context
  tuple. With `prepare-release-0-4-0`: `.github/dependabot.yml`'s header and
  `docker` entry beside this package's `github-actions` edit;
  `tests/test_release_surface.py` and `tests/test_workflow_pins.py`, where
  that package deletes the Docker tests; `docs/hooks.md`'s CI table, where
  that package edits other rows; `docs/next-steps.md`'s Docker item. Every
  package adds to `CHANGELOG.md` `[Unreleased]`.

## Non-Goals

- **No SBOM.** The publish attestation and the build provenance cover
  integrity. A CycloneDX SBOM of a wheel with no runtime dependencies lists
  one component, and `tools/smoke_wheel.py`'s clean venv plus
  `test_new_modules_stdlib_only` and `test_runtime_dependencies_stay_empty`
  already prove that claim. Reopens when `[project] dependencies` becomes
  non-empty or an adopter is under a regulatory SBOM requirement. The
  minimal shape for then is recorded in DEC-HRP-021.
- **No dev lockfile and no `pip` Dependabot entry.** The dev extras are
  unpinned on purpose: `.github/dependabot.yml:6-14`, the
  `ruff==`/`mypy==`/`pytest==` refusal in `tools/check_no_hardcoded_thresholds.py`
  and `test_dependabot_does_not_add_a_pip_ecosystem` hold it.
- **No workflow dependency lockfile.** GitHub's action-lock file is a public
  preview. Reopens at general availability, when `tests/test_workflow_pins.py`
  would read it.
- **No Scorecard and no dependency-review workflow.** Each is a third
  workflow file, which `test_every_workflow_is_scanned_by_the_threshold_guard`
  pins against. Scorecard needs `security-events: write` and
  `id-token: write`. Dependency review needs only read access but has no
  runtime dependency to review. CodeQL runs as a repository setting (default
  setup), not a workflow.
- **No signed-commits ruleset.** Integrity rests on provenance and
  attestations, and the rule would judge every commit a promotion merge
  carries in.
- **No floating `v1` tag and no Marketplace listing.** Held to 1.0. The
  row's reason is re-stated, not its decision.
- **No `CONTRIBUTING.md`.** `AGENTS.md`, `docs/hooks.md` and the pull request
  template carry it, and a root markdown file costs a `REQUIRED_DOCS` row
  (`test_every_root_markdown_file_is_wired_into_the_docs_gate`).
- **No `persist-credentials` change in `ci.yml`.** Its jobs run on pull
  requests with a read-only token, and `graph-diff` fetches the base ref, so
  dropping the credential there needs a per-job audit of git network use.
  That is its own change. This one is about the path where a credential could
  meet published bytes.
- **No reusable-workflow "trusted builder"**, so no SLSA Build L3 claim
  (DEC-HRP-003).
- **No owner setting.** Immutable releases, the rulesets, the actions
  allowlist, "require actions pinned to a full-length commit SHA" and private
  vulnerability reporting are repository settings outside the tree, in the
  plan's owner-settings step. This change names them where it depends on
  them and changes none.
- **No change to `openspec_graph/`, the rule set, the Makefile, `ci.yml`,
  the composite action or the templates; no version bump; no runtime
  dependency** (C-HRP-1).
- **No first-run evidence in this change's criteria.** The `release` job
  first runs on the 0.4.0 tag. The dry runs and the gate rehearsal are
  recorded in `tasks.md`, not ticked as criteria (DEC-HRP-024).

## Affected Capabilities

- `release-pipeline`
