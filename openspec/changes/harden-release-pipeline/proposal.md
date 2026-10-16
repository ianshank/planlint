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
leave the job's token where every later step can reach it, including the
whole pre-PR ladder and a `pip install` of the dev extras. It sits in a
credentials file under `RUNNER_TEMP` that the checkout's git configuration
includes. `SECURITY.md` gives a reporting route but no scope, no timeline, no
disclosure terms, no safe harbour, no word on how a fix ships, and no way to
verify a download. No `CODEOWNERS` file exists. Dependabot opens a pull
request for a new action release the week it ships. And one recorded
deferral, the floating `v1` tag, rests on a permission fact this change makes
false.

This is Phase 2.1 of the session plan for a lean, production-grade `main`,
with that plan's Phase 2.3 deferrals and its peer-review resolutions B1–B14
and A17. The plan is not tracked (`lean-production-tree` DEC-LPT-005), so
every decision this package takes from it is restated in
`specs/release-pipeline/spec.md`, and every fact below was re-read against
this tree. Where the first adversarial review (at `f96b7d1`) changed a
decision, the spec marks the decision revised, and `tasks.md` Milestone 1
maps each finding to the clauses that resolve it.

**Evidence:** read on `claude/lean-production-tree` at `4278d4c` (`dev` at
`c0ff090` plus `lean-production-tree`'s draft, which touches only
`openspec/`), 2026-10-16. Re-read on `claude/harden-release-pipeline` at
`f96b7d1` (`dev` at `c0ff090` plus this package) for the first review.
`planlint --target . validate --fail-on ERROR` exited 0 before any file of
this package existed. Line numbers are those of that tree. A sibling landing
first may move a line without moving the fact.

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
- **Where `actions/checkout` keeps the token.** The pinned
  `actions/checkout@3d3c42e…` (`v7.0.1`) declares `persist-credentials` with
  `default: true` (its `action.yml:52-54`). Its `src/git-auth-helper.ts`
  writes the token into a separate credentials file in `RUNNER_TEMP` (`:46`,
  `:326-358`). It then points the repository's git configuration at that file
  with an `includeIf.gitdir:<git dir>.path` entry (`:360-378`), so every later
  git command in the checkout, and any step that reads the file, has the
  token. The token never sits in `.git/config` itself. Of `ci.yml`'s
  checkouts, those at `:311`, `:436`, `:475` and `:528` set it `false` and the
  rest leave the default. `graph-diff` runs
  `git fetch origin "${{ github.base_ref }}"` at `ci.yml:250`.
- **What the gate's fetch does without a credential.** `tag_ancestry`
  (`tools/check_promotion.py:379-430`) runs its own `git fetch` when given
  `--fetch` and returns exit 2 if that fails (`:399-406`). It returns exit 1
  for a commit that is not on the production branch's first-parent chain
  (`:428-429`). The workflow step's own `git fetch` at `release.yml:63` runs
  first, under Actions' `bash -e`, so on a repository that needs
  authentication to fetch, git's own exit 128 ends the step before
  `tag-ancestry` or `make pre-pr` runs. On this public repository the
  unauthenticated fetch succeeds. The ancestry step is tag-only, so no
  `workflow_dispatch` dry run ever exercises it. The remedy for a private
  repository is an `http.extraheader` whose value is
  `AUTHORIZATION: basic <base64 of x-access-token:TOKEN>`. Expressions have
  no base64 function, so an `env:` entry cannot compute that value, and the
  step's script must export it.
- **The attesting action.** The refs advertisement of
  `https://github.com/actions/attest` (fetched over HTTPS on 2026-10-16, the
  data `git ls-remote --tags` prints) lists `refs/tags/v4.2.2` and
  `refs/tags/v4` both at `1e69f48acb82d1966a394da916b4c1698aa569d6`, and no
  `v5`. At that commit:
  - `action.yml` declares `runs: using: node24` and has no `uses:` line.
  - `src/detect.ts:10-27` selects SBOM mode when `sbom-path` is set, custom
    mode when any of `predicate-type`, `predicate` or `predicate-path` is set,
    and SLSA provenance otherwise.
  - `src/main.ts:99` writes the bundle to
    `path.join(await tempDir(), ATTESTATION_FILE_NAME)`, where `tempDir` is
    `RUNNER_TEMP` (`:234-239`), never into the subject's directory.
  - Its README lists three permissions: `id-token: write`,
    `attestations: write` and `artifact-metadata: write`. The third is for the
    artifact storage record, which `src/attest.ts` creates only inside
    `if (subjects.length === 1 && opts.pushToRegistry)` (`:45`), wrapping it
    in a try so a token without the scope does not fail the attestation
    (`:70-74`). This workflow attests files and pushes nothing to a
    registry, so omitting `artifact-metadata: write` is correct, not an
    oversight.

  GitHub's how-to (`github/docs`,
  `content/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations.md`)
  uses `actions/attest@v4` under `id-token: write`, `contents: read` and
  `attestations: write`.
- **The wrapper the plan named.** `actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8`
  (`v4.2.2`) is `using: "composite"`. It exposes `predicate-type`,
  `predicate` and `predicate-path`, passes them to
  `actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d # v4.2.1`, and
  so fixes nothing its name suggests. Its README: "As of version 4,
  `actions/attest-build-provenance` is simply a wrapper on top of
  `actions/attest` … new implementations should use `actions/attest`
  instead". This package pins `actions/attest` directly (DEC-HRP-004).
- **What the GitHub CLI does with a release and an attestation.** From the
  help text of the `gh` 2.89.0 in this environment:
  - `gh release create`: if "a matching git tag does not yet exist, one will
    automatically get created from the latest state of the default branch",
    and `--verify-tag` aborts instead.
  - When assets are attached, "separate API calls are made to create the
    release as a draft, upload the assets, and then publish the release", and
    immutability "is enforced only after a release is published".
  - `gh attestation verify` enforces the `https://slsa.dev/provenance/v1`
    predicate by default. It takes `--repo`, `--signer-workflow`
    (`[host/]<owner>/<repo>/<path>/<to>/<workflow>`), `--source-ref`,
    `--source-digest` ("the digest associated with the source repository")
    and `--deny-self-hosted-runners`.
  - `gh release verify-asset` exists for immutable-release attestations.
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
  - `tests/test_workflow_pins.py`: `ACTION_REF_SCAN` (`:39`) includes every
    workflow. `_pin_offenders` (`:78-97`) requires `@<40-hex> # vX.Y.Z`.
    `_floor_offenders` (`:128-152`) names a pinned action with no row in
    `[tool.specgraph.action_major_floors]` (`:146-149`), and that table
    (`pyproject.toml:239-246`) has no row for `actions/attest`.
  - `tests/test_workflow_posture.py`: every job carries a `timeout-minutes`
    literal inside `pyproject.toml:192-193`'s range (`:162-169`). Every
    job-level `permissions:` block has a comment line above it inside the job
    (`:103-110`, through `tests/workflow_support.py:119-138`, the rule at
    `:136`). `release.yml` has no `concurrency` block (`:224-227`). The publish
    step declares `attestations: true` under its own `with:` (`:285-345`).
    That last reader splits the publish job into steps, so a new step beside
    the publisher does not disturb it.
  - `workflow_job_blocks` (`tests/support.py:297-329`) starts a job's body
    after its two-space `name:` line, so a comment written between two jobs
    belongs to the earlier one.
- **How a shell script can be read.** `tools/_common.py`'s `run_scripts`
  (`:542-571`) returns a workflow's `run:` scripts, and `shell_invocations`
  (`:581-614`) joins backslash continuations (`script.replace("\\\n", " ")`,
  `:593`) before lexing one line at a time. Its `_shell_tokens` (`:574-578`)
  sets `commenters = "#"`. Checked with `shlex` in this environment, three
  ways of reading misbehave:
  - lexing a whole script turns `make pre-pr` on its own line after a `gh`
    line into two more arguments of that `gh` command;
  - lexing a raw line that ends in a backslash raises "No escaped character";
  - with `#` as the comment character, `${GITHUB_REF_NAME#v}; make pre-pr`
    lexes as `${GITHUB_REF_NAME` and the rest vanishes.

  With `commenters = ""` the same line yields the `;` and the `make`.
  Copilot's review of #59 then showed that the repaired reader still passes
  scripts bash runs differently: a quoted `"#notes"` before `; printf x`,
  and a quoted or backtick command substitution. A second adversarial
  review then showed that comparing the scripts still left the job open, to
  a flow-mapping step, a step `env:` such as `BASH_ENV`, a `container:` and
  a blank line in a folded scalar. A third showed that pinning the job's
  block still trusted a line scanner to find where the job ends: a column-0
  comment ended it early. So the guard pins the whole file against a golden
  copy, and holds the write scope by a list of the lines that may say
  `write` (DEC-HRP-007).
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
  begin with `[`. They close the last section, `[0.1.0]`. `tools/spec_status.py:106`
  and `tests/test_adopter_urls.py:338-361` already read the bracketed
  headings. The `[0.3.0]` section is long (measured in `tasks.md`), and
  GitHub's limit on a release body is not confirmed here.
- **What a new tool joins.** `tests/test_gate_scripts.py:401-422` lists every
  script `python tools/<x>.py` must start, and `:443` refuses a listed script
  that is absent. `tools/AGENTS.md:11,33-39` counts the stdlib-only gate
  scripts, and `:41-47` lists the argv conventions. The file is 59 lines
  against `MAX_NESTED_LINES` (`tests/test_agent_artifacts.py:454`).
  `docs/architecture/c4.md:82` names every script under `tools/` by group.
  `tools/_common.py`'s `read_text` returns `""` for a missing file
  (`:109-115`). `openspec_graph/cli.py:999-1004` reconfigures stdout to UTF-8,
  which a script printing the changelog's em dashes needs on an ASCII console.
  `pyproject.toml:382` exempts `tools/*` from `T201`, and the docstring
  ratchet (`:383-420`) never gains an entry, so a new script carries every
  public docstring.
- **The documents that would become false.**
  - `docs/hooks.md:88`, the `release` row, ends at "trusted publishing to
    PyPI, which uploads PEP 740 attestations for both files".
  - The 0.3.0 runbook has a person create the GitHub release
    (`docs/distribution-plan.md:176`, step 9) after verifying only the publish
    attestations (`:155-159`).
  - `lean-production-tree`'s R-LPT-4 moves that runbook into `docs/hooks.md`
    "Releasing", listing "the GitHub release cut from the `[X.Y.Z]` section"
    as a step without naming who cuts it. In that runbook no job does, so the
    step falls to a person.
  - `.claude/skills/planlint-release/SKILL.md`'s "Tag the production merge
    commit" step (`:53-61`) says to "verify the attestations", meaning the
    publish attestations, and does not mention a GitHub release.
  - `SECURITY.md:5-7` is the reporting route, `:54-59` says only the latest
    release is supported, and `:61-70` verifies an install with
    `planlint --version` and `rules --json` alone.
  - `docs/next-steps.md:231` defers the floating `v1` tag because "moving a
    tag on every release needs `contents: write` in the release workflow,
    which currently holds `contents: read` plus `id-token: write` on the
    publish job alone", the same secondary reason as `add-github-action-contract`'s
    DEC-GA-011.
  - `.github/` holds no `CODEOWNERS`, and neither does the root or `docs/`.
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
    that does not, the first fetch exits 128 before `make pre-pr`. The remedy
    is an `http.extraheader` that the step's own script computes and exports
    through `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0` and `GIT_CONFIG_VALUE_0`,
    reaching both fetches and dying with the step, never the persisted
    credential.
  - `publish` gains, before the PyPI step,
    `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2` with
    `subject-path: dist/*` and no predicate or `sbom-path` input. Its
    permissions block gains `attestations: write`, and the comment above it is
    extended in place to name the step that needs it. The publisher step and
    its `attestations: true` are unchanged.
  - `build` gains two tag-only steps after the version check and before the
    `dist` upload. One runs `python tools/release_notes.py "${GITHUB_REF_NAME#v}"`
    into `$RUNNER_TEMP/notes.md`. The other uploads that file as artifact
    `release-notes` with `if-no-files-found: error`, pinned like the existing
    upload.
  - A new job, `release`: `needs: publish`, `if: github.ref_type == 'tag'`,
    `timeout-minutes` inside the configured range, and a comment inside the
    job body above a block of `contents: write` + `attestations: read`. It has
    no checkout. It downloads `dist` and `release-notes` and runs
    `gh attestation verify` on every file, with `--repo`, `--signer-workflow`,
    `--source-ref`, `--source-digest "$GITHUB_SHA"` and
    `--deny-self-hosted-runners`. Only then does it run one
    `gh release create "$GITHUB_REF_NAME" dist/* --verify-tag --title … --notes-file …`.
    `GH_TOKEN` comes from `github.token` and `GH_REPO` from
    `github.repository`.
  - No `concurrency` block, and no other job changes.
- **`pyproject.toml`**: `[tool.specgraph.action_major_floors]` gains
  `"actions/attest" = 4`.
- **`.github/dependabot.yml`**: the `github-actions` entry gains
  `cooldown: { default-days: 7 }`, with a comment that the wait applies to
  version updates and never to security updates. Nothing else in the entry
  moves.
- **`.github/CODEOWNERS`** (new): `* @ianshank`, under a comment saying it
  names the owner and enforces nothing while the rulesets require no
  approving review.
- **`tools/release_notes.py`** (new, stdlib-only): `main(argv)` with
  `parse_args(argv[1:])`. It prints the body of `## [X.Y.Z]` for the version
  given, as UTF-8 whatever the console. Link definitions end the body only
  when they close the section, and no length ceiling applies. It exits 2,
  naming the version and the file on stderr, in these cases:
  - the section is absent, empty or appears twice;
  - a link definition sits mid-section;
  - the version is not `X.Y.Z`;
  - the changelog cannot be read.

  It carries full docstrings.
- **`tests/test_release_notes.py`** (new): in-process against `main(argv)`,
  planted changelogs under `tmp_path`, every refusal of the tool, and the real
  changelog's current-version section.
  **`tests/test_release_surface.py`**: new tests in the release-workflow
  section, built on pure readers of the workflow text, each MUST shown red on
  a planted workflow. They cover the checkouts, the publish job's attestation
  inputs, the notes steps, and the `release` job's wiring, permissions,
  commands and verification flags. `release.yml` itself is pinned whole
  against a golden copy, `tests/fixtures/release-workflow.golden`, with
  only trailing whitespace, action pins and the `PYTHON_DEFAULT` value let
  vary, so no shell or YAML is parsed. Across workflows, every
  non-comment line containing `write` must be on a named list, which holds
  the single `contents: write` however it is spelled. The
  existing tests keep their names and bodies.
  **`tests/test_workflow_pins.py`**: one test beside the Dependabot readers
  that the `github-actions` entry declares a cooldown.
  **`tests/test_gate_scripts.py`**: `release_notes.py` joins the
  runnable-script list.
- **`tools/AGENTS.md`** and **`docs/architecture/c4.md`**: `release_notes`
  is named among the stdlib-only scripts and the program-name-first argv
  convention, and every count either file states stays true. `tools/AGENTS.md`
  gains at most one line.
- **`SECURITY.md`**:
  - Scope. In: the PyPI package, the composite action, the skill and plugin
    manifests, this repository's workflows. Out: third-party actions, GitHub
    itself, adopters' repositories.
  - Timeline: acknowledged within 7 days, a fix or a statement within 90.
  - Disclosure: an advisory, and a CVE where one applies, at the fix or at
    day 90; the reporter may publish after day 90.
  - A safe-harbour sentence.
  - How fixes ship: a `hotfix/*` branch into `main` and the next patch of the
    latest minor; earlier minors get nothing.
  - A verification section with `pipx run pypi-attestations verify pypi …`
    and `gh attestation verify <file> --repo ianshank/planlint --signer-workflow …`,
    with placeholders for the version, stating SLSA Build L2 and never L3.
- **`docs/hooks.md`**: the `release` row names the build provenance, the
  verification and the automated release. In the "Releasing" runbook, the
  verify step gains `gh attestation verify`. The GitHub-release step keeps its
  place and its `[X.Y.Z]` source and now says the `release` job cuts the
  release and the person confirms both files are on it.
  **`.claude/skills/planlint-release/SKILL.md`**'s "Tag the production merge
  commit" step says the same.
- **`docs/next-steps.md`**: the floating-`v1` row is re-stated. The reason
  becomes the 1.0 contract (DEC-GA-011's first reason), and the row no longer
  claims the release workflow holds no `contents: write`.
- **`CHANGELOG.md`** `[Unreleased]`: a `### Changed` entry headed with this
  package's backticked name.
- **Shared edit sites**, named so each merge is prepared rather than found.
  - With `lean-production-tree`:
    - `docs/hooks.md` "Releasing", which that package writes and this one
      amends at two steps;
    - the release skill;
    - `SECURITY.md`, where that package rewrites the "What is not a
      vulnerability" path;
    - `docs/next-steps.md`, where that package edits the rows beside `:231`;
    - `tests/test_release_surface.py`'s Docker-context tuple.
  - With `prepare-release-0-4-0`, which deprecates the Dockerfile in 0.4.0
    and leaves its deletion to a 0.5.0 package, so the `docker` Dependabot
    entry and the Docker tests stay untouched by both packages:
    - `pyproject.toml`, where that package edits `requires-python`, the
      classifiers and `[tool.mypy]` beside this package's
      `action_major_floors` row;
    - `docs/hooks.md`'s CI table, where that package edits the `test` row;
    - `docs/next-steps.md`, where that package edits items 7a and 9;
    - `SECURITY.md`, where that package's release-prep pull request rewords
      the "Supported versions" clause, which this package does not touch.
  - Every package adds to `CHANGELOG.md` `[Unreleased]`.

## Non-Goals

- **No SBOM.** The publish attestation and the build provenance cover
  integrity. A CycloneDX SBOM of a wheel with no runtime dependencies lists
  one component, and `tools/smoke_wheel.py`'s clean venv plus
  `test_new_modules_stdlib_only` and `test_runtime_dependencies_stay_empty`
  already prove that claim. Reopens when `[project] dependencies` becomes
  non-empty or an adopter is under a regulatory SBOM requirement. The
  minimal shape for then, a second `actions/attest` step in SBOM mode, is
  recorded in DEC-HRP-021.
- **No artifact storage record.** `artifact-metadata: write` is for the
  storage record `actions/attest` makes only when pushing to a registry, and
  nothing here is pushed to one.
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
