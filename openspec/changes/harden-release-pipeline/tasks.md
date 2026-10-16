# Tasks: harden-release-pipeline

Drafted at `4278d4c` on `claude/lean-production-tree` (`dev` at `c0ff090`
plus `lean-production-tree`'s draft) on 2026-10-16, as Phase 2.1 of the
session plan for a lean production branch, with that plan's Phase 2.3
deferrals and its review resolutions B1–B14 and A17. Revised on
`claude/harden-release-pipeline` (`dev` at `c0ff090`) to resolve the first
adversarial review, read at `f96b7d1` (Milestone 1). That plan is not tracked
(`lean-production-tree` DEC-LPT-005). Every decision this package takes from
it is restated in `specs/release-pipeline/spec.md`.

**This package's implementation must not merge into `dev` before `v0.3.0`
is tagged and published, nor before `lean-production-tree`'s implementation
has merged** (Milestone 2, DEC-HRP-025). #59 carries this package alone into
`dev`, editing no workflow, as #58 did for `lean-production-tree` (squash
`9f5c693`, 2026-10-16). The implementation is a new pull request from `dev`.
It opens as a GitHub draft, stays one through Milestone 2, and is marked
ready for review only after Milestone 6's dry run is recorded here.

Every line number below is re-read at the implementation branch's head
before the milestone that uses it, because a sibling landing first may move a
line without moving the fact. Every number names the command that produced
it.

## Measured at `4278d4c`, 2026-10-16 (drafting)

- **The gate before the draft.** `planlint --target . validate --fail-on ERROR`
  printed `55 spec(s) checked · 0 error · 0 warn · 0 info` and `PASS`, exit 0,
  before any file of this package existed.
- **The checkout default.** `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`'s
  `action.yml:52-54` declares `persist-credentials` with `default: true`.
- **The CLI.** `gh --version` printed 2.89.0 in this environment.
  - `gh release create --help` documents three things: a missing tag is
    created "from the latest state of the default branch" unless
    `--verify-tag` is given; assets are attached through a draft that is
    then published; and immutability is enforced only after publishing.
  - `gh attestation verify --help` lists `--repo`, `--signer-workflow`,
    `--source-ref`, `--source-digest` and `--deny-self-hosted-runners`, and
    the default predicate `https://slsa.dev/provenance/v1`.
  - `gh release --help` lists `verify` and `verify-asset`.
- **The platform documentation**, read from `github/docs` on GitHub:
  - `content/actions/concepts/security/artifact-attestations.md`: "Artifact
    attestations by itself provides SLSA v1.0 Build Level 2", and L3 is
    reached through reusable workflows (DEC-HRP-003).
  - `content/code-security/reference/supply-chain-security/dependabot-options-reference.md`:
    `cooldown` is "only available for _version_ updates, not _security_
    updates"; a 3-day default applies when it is unset; GitHub Actions
    supports `default-days` and not the per-semver keys (DEC-HRP-014).
- **Stage citations, with this package's draft present** (and
  `prepare-release-0-4-0`'s, drafted concurrently): `make stage-citations`
  reports the stages invoked by no scanned workflow as `ci, coverage-tools,
  security, thresholds, validate, wheel-check`. That is the same set
  `lean-production-tree` measured at `c0ff090`. This package's verification
  lines cite `test` and `pre-pr` only, so it adds none.

## Measured for the first review's revision, 2026-10-16

- **The whole-tree gate at `f96b7d1`.** `planlint --target . validate --fail-on ERROR`
  printed `55 spec(s) checked`: the 54 at `c0ff090` plus this package. The
  drafting run's 57 was taken in the shared checkout with two sibling drafts
  on disk, and does not describe this branch.
- **The attesting action's pin.** The refs advertisement of
  `https://github.com/actions/attest.git/info/refs?service=git-upload-pack`,
  fetched over HTTPS (the data `git ls-remote --tags` prints):
  - `1e69f48acb82d1966a394da916b4c1698aa569d6 refs/tags/v4.2.2`;
  - `1e69f48acb82d1966a394da916b4c1698aa569d6 refs/tags/v4`;
  - `508db95dd578ae2727ebd6217d5ba78e4fbda05d refs/tags/v4.2.1`;
  - no `refs/tags/v5`.
- **The action at that commit**, read from
  `https://raw.githubusercontent.com/actions/attest/1e69f48acb82d1966a394da916b4c1698aa569d6/`:
  - `action.yml:102-103` is `runs: using: node24`, and
    `grep -c "uses:" action.yml` prints 0 (DEC-HRP-005);
  - `src/detect.ts:10-27`: `sbom-path` selects SBOM mode, any predicate input
    selects custom mode, and otherwise the action makes provenance
    (R-HRP-3);
  - `src/main.ts:99` writes the bundle to
    `path.join(await tempDir(), ATTESTATION_FILE_NAME)`, and `tempDir`
    (`:234-239`) is `RUNNER_TEMP` (DEC-HRP-001);
  - `src/attest.ts:45` creates a storage record only inside
    `if (subjects.length === 1 && opts.pushToRegistry)`, and `:70-74` wraps
    it in a try for a token without `artifact-metadata: write`;
  - `README.md:67-70` lists `id-token`, `attestations` and
    `artifact-metadata` write.
- **GitHub's how-to.** `github/docs`,
  `content/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations.md`,
  shows `uses: actions/attest@v4` under `id-token: write`, `contents: read`
  and `attestations: write`, at `:39-48` and again at `:61-71`, `:100-109` and
  `:123-133`.
- **The wrapper the plan named, and why it was replaced** (DEC-HRP-004):
  - `actions/attest-build-provenance` `refs/tags/v4.2.2` is
    `4d101475d8b20a2381f78447822ac1eab6504dd8`;
  - its `action.yml` there is `using: "composite"`, passes
    `predicate-type`, `predicate` and `predicate-path` through, and runs
    `actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d # v4.2.1`, one
    patch behind `actions/attest`'s own `v4.2.2`;
  - its README says it "is simply a wrapper on top of `actions/attest`" and
    that "new implementations should use `actions/attest` instead".
- **Where the checkout keeps the token.**
  `actions/checkout@3d3c42e…`'s `src/git-auth-helper.ts`:
  - `:46` names the credentials config file in `RUNNER_TEMP`;
  - `:326-358` writes the token into it;
  - `:360-378` adds the `includeIf.gitdir:<git dir>.path` entry that points
    the repository's git configuration at it.
- **The lexing failure modes**, reproduced with `shlex.shlex(…, posix=True,
  punctuation_chars=";&|()")`, `whitespace_split = True`:
  - a whole script `gh attestation verify "$f" --repo x\nmake pre-pr\n`
    yields `make` and `pre-pr` as further words of the `gh` command, with no
    separator;
  - the raw line `gh attestation verify "$f" --repo x \` raises
    `ValueError: No escaped character`;
  - with `commenters = "#"`,
    `gh release create "$T" --title planlint-${GITHUB_REF_NAME#v}; make pre-pr`
    yields `…, 'planlint-${GITHUB_REF_NAME'` and nothing after.

  With `commenters = ""` the same line yields `';', 'make', 'pre-pr'`, and the
  continuation joined by `replace("\\\n", " ")` lexes whole (DEC-HRP-007).
- **The longest notes body.** The `[0.3.0]` section of `CHANGELOG.md`, from
  the line after its heading to the next `## ` heading, with outer blank lines
  stripped, measures 45,185 characters over 708 lines (a one-off read-only
  Python count). The review's 45,186 counts one more character, a trailing
  newline. The link definitions are lines 1793 to 1796 of 1796 and close the
  `[0.1.0]` section (DEC-HRP-026).
- **The nested-file budget.** `wc -l tools/AGENTS.md` printed 59, against
  `MAX_NESTED_LINES = 60` in `tests/test_agent_artifacts.py`. The budget is
  one added line. A natural reflow of the edited sentences reaches 61 and
  fails `test_nested_agents_file_stays_short`.

## Milestone 0 — Grounding at the implementation branch's head

- Run the gate and record its exit code before the first edit outside this
  package: `planlint --target . validate --fail-on ERROR`.
- Re-read every line number `proposal.md` cites at the head, and record any
  that moved beside its drafting value.
- Re-confirm the pin. Run `git ls-remote --tags https://github.com/actions/attest`
  and record the `v4.2.2` line, the `v4` line and the newest tag. If a newer
  release exists, pin that one instead. At whatever commit is pinned, re-read
  three things:
  - `action.yml`'s `runs:` block, which must stay a JavaScript action with no
    `uses:` (DEC-HRP-005);
  - `src/detect.ts`, whose mode rule must be unchanged (R-HRP-3);
  - `src/main.ts`, whose bundle path must stay under `RUNNER_TEMP`
    (DEC-HRP-001).

  Record each line. If any of the three moved, stop and reopen DEC-HRP-004.
- Confirm where the release runbook lives. `docs/hooks.md` "Releasing" must
  carry the numbered runbook, with its "GitHub release cut from the
  `[X.Y.Z]` section" step, and `docs/distribution-plan.md` must be gone. If
  the runbook is still in `docs/distribution-plan.md`, `lean-production-tree`
  has not landed: stop, because Milestone 2's precondition is not met
  (DEC-HRP-017).
- Read `prepare-release-0-4-0`'s state on `dev` and record which of the shared
  edit sites `proposal.md` lists it has already changed: `pyproject.toml`'s
  `requires-python`, classifiers and `[tool.mypy]`, the `docs/hooks.md`
  `test` row, `docs/next-steps.md` items 7a and 9, and `SECURITY.md`'s
  "Supported versions" clause.
- **Gate:** `make test`

## Milestone 1 — The change package

- `proposal.md`, `specs/release-pipeline/spec.md` and `tasks.md` are written
  spec-first, with every criterion unticked and `Status: DRAFT`. They are
  reviewed by `spec-adversary` before any edit outside this directory, and
  each finding is resolved by a decision and recorded here.
- What the first draft resolved that the plan did not record:
  - **(a) The attesting action.** First kept as the plan's wrapper, and
    replaced at review 1; see below.
  - **(b) A read scope.** The `release` job declares `attestations: read`
    beside `contents: write`: R-HRP-5, DEC-HRP-008.
  - **(c) A hosted-runner check.** `--deny-self-hosted-runners` on the
    verification: R-HRP-7, DEC-HRP-003.
  - **(d) The runbook and the release skill** gain the `release` job, so this
    package lands after `lean-production-tree`: R-HRP-17, DEC-HRP-017,
    DEC-HRP-025.
  - **(e) The private-repository remedy is scoped to the step**, not to one
    fetch: R-HRP-2, DEC-HRP-011.
  - **(f) The SBOM reopen shape** uses SBOM mode (`sbom-path`), not a custom
    `predicate-type`: DEC-HRP-021.
  - **(g) An allow-list.** "No `run:` invoking a tree path" is sharpened into
    an allow-list of the two `gh` commands, with no checkout: R-HRP-6,
    DEC-HRP-007.
  - **(h) Where the bundle goes.** Checked against the pinned source:
    DEC-HRP-001.
  - **(i) A cooldown guard** beside the existing Dependabot readers:
    R-HRP-11, DEC-HRP-019.
  - **(j) Two more documents**, `tools/AGENTS.md` and
    `docs/architecture/c4.md`: R-HRP-19.
  - **(k) Reopen triggers** for the dev lockfile, Scorecard, signed commits
    and `CONTRIBUTING.md`: DEC-HRP-022, DEC-HRP-023.
- **Review 1** (`spec-adversary`, against `f96b7d1`; no HIGH), resolved in
  this revision. Each finding is listed with the coordinator's decision and
  the clauses that carry it:
  - **MEDIUM-1, the allow-list lexing failed both ways.** Continuations are
    joined first; each line is lexed alone with `commenters = ""`; only a word
    starting with `#` is a comment; an unreadable line is an offender. AC-HRP-11
    gains a forbidden command on its own line after a `gh` line, and an
    unquoted `${GITHUB_REF_NAME#v}` before `; make pre-pr`. Clauses: R-HRP-6,
    DEC-HRP-007, AC-HRP-11, Milestone 3, "Measured for the first review's
    revision".
  - **MEDIUM-2, the reason for keeping the wrapper was wrong.** The package
    pins `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2`
    with floor `"actions/attest" = 4`, and the guarantee of provenance is the
    input rule. Clauses: R-HRP-3 ("no predicate input and no `sbom-path`"),
    R-HRP-10 (the composite sentence dropped), DEC-HRP-004 (rewritten),
    DEC-HRP-005 (shrunk), DEC-HRP-021 (no action switch), AC-HRP-3, AC-HRP-4,
    AC-HRP-5, AC-HRP-19, Milestones 0 and 4, the proposal's evidence.
  - **MEDIUM-3, MUST conditions were never shown to fail.** New plantings,
    each its own MUST: a missing `--source-ref`; a missing
    `--deny-self-hosted-runners`; `if: always()`, `if: failure()` and
    `continue-on-error` on a step; `GH_TOKEN` from `secrets.*`; `gh api` and
    `gh release upload`; a third artifact download; and an omitted
    `if-no-files-found: error`. Clauses: AC-HRP-7, AC-HRP-11, R-HRP-4,
    R-HRP-6, AC-HRP-6, DEC-HRP-019.
  - **LOW-1, R-LPT-4 does not say "by hand".** DEC-HRP-017 now says the step
    names no actor and falls to a person only because no job exists in that
    runbook. The step keeps its place and its `[X.Y.Z]` source, and the skill
    step is named by its heading. Clauses: DEC-HRP-017, R-HRP-17, AC-HRP-21,
    Milestone 5, the proposal's evidence.
  - **LOW-2, the precise reason for `attestations: read`.** It is kept,
    unverified until the 0.4.0 run: DEC-HRP-008.
  - **LOW-3, proposal wording.** The proposal now explains why
    `artifact-metadata: write` is omitted; says the checkout keeps the token
    in a `RUNNER_TEMP` file included through `includeIf.gitdir`, not
    `.git/config`; and no longer claims the skill mentions a GitHub release.
    Clauses: the proposal's Why, its evidence and its Non-Goals; the spec's
    Problem Statement and evidence.
  - **LOW-4, the remedy is exported in the script.** An `env:` expression
    cannot base64-encode. Clauses: R-HRP-2, DEC-HRP-011, AC-HRP-1,
    Milestone 4.
  - **LOW-5, the notes boundary.** A link definition ends the body only when
    every later non-blank line of the section is one, and otherwise the tool
    exits 2. The in-section case is planted, and there is no length ceiling.
    Clauses: R-HRP-13, R-HRP-14, DEC-HRP-026, AC-HRP-13, AC-HRP-14,
    Milestones 3 and 4.
  - **LOW-6, dated facts out of the spec.** The `tools/AGENTS.md` measurement
    and "one patch behind" moved here; the count at `f96b7d1` is 55; the
    budget is one added line. Clauses: the spec's evidence and DEC-HRP-004,
    "Measured for the first review's revision", Milestone 5.
  - **LOW-7, DEC-GA-011 cited by its archive URL.** Clauses: DEC-HRP-018, the
    proposal's evidence.
  - **LOW-8, `--source-digest "$GITHUB_SHA"`, and the deletion bypass.**
    Clauses: R-HRP-7, DEC-HRP-009, AC-HRP-10, AC-HRP-11, Milestones 4 and 7.
- **Copilot's review of #59** (2026-10-16, against `f58c715`; one High),
  resolved in this revision:
  - **HIGH, the command reader admitted commands bash runs.** Reproduced
    with the reader exactly as Milestone 3 specified it:
    - `gh release create v0.4.0 --title "#notes"; printf x` and
      `gh release create v0.4.0 --title "$(printf x)"` both passed, and so
      did the backtick form;
    - an unquoted `$(printf x)` and the first review's `; make pre-pr` case
      were caught.

    The reader is replaced by a whole-script comparison with the two fixed
    scripts, which parses no shell, and a `shell:` override is refused. The
    coordinator chose the fixed shapes, the review's own alternative, over
    patching the reader. Clauses: R-HRP-6, DEC-HRP-007, AC-HRP-10,
    AC-HRP-11, Milestones 3, 4 and 6.
- **Review 2** (`spec-adversary`, against `26eeb5d` after #59 merged it as
  `40c12c9`; two HIGH), resolved in a follow-up pull request into `dev`:
  - **HIGH-1, a flow-mapping step is invisible.** `run_scripts`'s `_RUN_KEY`
    matches a block-style `run:` only. So `- {name: x, run: make pre-pr}`
    is a third step that GitHub runs and the script check never saw.
  - **HIGH-2, the environment was unpinned.** The script check compared
    only the text, so these all passed:
    - a step `env:` adding `BASH_ENV` (sourced by a non-interactive bash)
      or `PATH`;
    - a step `env:` redefining `GITHUB_SHA`, which DEC-HRP-009's binding
      reads;
    - a job `container:` or `services:`, or a step `working-directory:`.
  - **MEDIUM-1, a blank line in the folded create.** `run_scripts` joins a
    `>-` scalar with spaces. YAML makes the blank line a newline, which
    splits the command while the folded text still matched.
  - **MEDIUM-2, LOW-1.** The proposal still described the shlex reader, and
    AC-HRP-11 still spoke of an allow-list.
  - **LOW-2.** Collapsing spaces inside quotes is moot now, because only
    trailing whitespace is stripped.
  - **Added by the coordinator.** R-HRP-5 counted a `contents: write` line
    only, so `permissions: write-all` on another job would also have held
    the write scope unseen.

  All are resolved by pinning the `release` job's whole text rather than its
  scripts. The top-level `env:` (`PYTHON_DEFAULT` alone) and the absence of
  a top-level `defaults:` are held beside it, and `write-all` is counted as
  a write scope. Clauses: R-HRP-5, R-HRP-6, DEC-HRP-007, AC-HRP-9,
  AC-HRP-10, AC-HRP-11, Milestones 3, 4 and 6, the proposal.
- **Review 3** (`spec-adversary`, against `d630412` in #62; two HIGH, one
  MEDIUM), resolved in #62:
  - **HIGH-1, a column-0 line ends the job block.** `workflow_job_blocks`
    stops at the first column-0 line, and a column-0 `#` comment is valid
    YAML inside a job. A step, a `container:`, or a whole `contents: write`
    job after one passed the pin and the holder count. The existing posture
    tests missed it too.
  - **HIGH-2, the write scope matched one spelling.** These all held the
    scope unseen: `"write"`, `'write'`, a quoted key, `contents : write`, a
    next-line value, a folded value, an alias, `"\x77rite"` and `Write`.
  - **MEDIUM-1, the top level was unspecified.** These all passed the
    natural readers:
    - `defaults:` written in flow form, or as `defaults :`;
    - a second `env:` after `jobs:`;
    - an extra write scope beside the top-level `contents: read`;
    - `cache-mode`;
    - a scalar `concurrency:`;
    - a new trigger.
  - **LOWs.**
    - `rstrip()` and `splitlines()` disagree with YAML on a no-break space
      and on Unicode line breaks.
    - `GITHUB_*` variables cannot be overwritten, according to GitHub's
      documentation.
    - The spec's evidence still leaned on `run_scripts`.
    - AC-HRP-11 listed the workflow default twice and named no test for the
      header.
    - This record lacked the review-2 revision run.
    - The pin was self-referential.

  The coordinator's decision fixes the root cause, not each spelling:
  - `release.yml` is pinned whole against
    `tests/fixtures/release-workflow.golden`. The file must be ASCII, it is
    split on `\n` only, and only trailing `" \t\r"`, the action pins and
    the `PYTHON_DEFAULT` value may vary.
  - The write scope is held across every workflow by the list
    `_WRITE_LINES`, and escapes are refused.

  This closes every HIGH and MEDIUM case. The escaped line break inside a
  double-quoted scalar is named as left to review. The self-reference is
  accepted, because review reads the commit that edits both the workflow
  and its copy. Clauses: R-HRP-5, R-HRP-6, DEC-HRP-007, AC-HRP-9,
  AC-HRP-10, AC-HRP-11, the spec's evidence, Milestones 3, 4 and 6, and the
  proposal.
- **Review 4** (`spec-adversary`, against `ff3c4cb` in #62; no HIGH, three
  MEDIUM, eight LOW). It was checked against PyYAML and against `yaml` 2.9.1,
  the library GitHub's open-source workflow parser uses. Resolved in #62:
  - **MEDIUM-1, a lone carriage return.** Stripping a trailing `\r` admitted
    `dist/*\r\r\n`, which a YAML reader takes as a blank line inside the
    folded create. Now `\r\n` becomes `\n` and any other `\r` is refused,
    the input being bytes.
  - **MEDIUM-2, the write list's line model.** A split on `\n` missed a
    Unicode line break after a comment. The escaped line break, which
    GitHub's parser honours, was left to review. Both are now read through
    `str.splitlines` and a join at a trailing `\`, and the named gap is
    closed.
  - **MEDIUM-3, the pin placeholder.** Any 40-hex commit is admitted. This is
    now named in DEC-HRP-007, with the review step that checks a hand-made
    pin change against its tag.
  - **LOWs.**
    - The reader-level parametrized test is limited to the plantings the
      readers can see.
    - The red-by-design list names the golden-copy test.
    - "pins the whole job" now reads "pins the whole file".
    - The escape fact cites its own `grep`.
    - The write list reads every file under `.github/workflows/` and
      counts lines with a `Counter`.
    - Milestone 2 records `default_workflow_permissions`.
    - Tags, directives and the `\u` and `\U` escapes are refused and
      planted.
    - DEC-HRP-007 now answers `harden-ci-workflows` DEC-HCW-008's
      objection to a test copy of a pin.

  No HIGH changed the design, so no fifth review is required. Clauses:
  R-HRP-5, R-HRP-6, DEC-HRP-007, AC-HRP-9, AC-HRP-11, Milestones 2 and 3,
  the proposal.
- The review-2 revision run, at `d630412` on
  `claude/harden-release-pipeline-followup`:
  - `planlint --target . validate --fail-on INFO --change harden-release-pipeline`
    printed `1 spec(s) checked · 0 error · 0 warn · 0 info`, exit 0;
  - `planlint --target . validate --fail-on ERROR` printed
    `57 spec(s) checked · 0 error · 0 warn · 0 info`, exit 0.

  The whole-tree count moves as sibling packages land.
  `tests/test_release_surface.py` is 266 lines at `d630412`
  (`wc -l tests/test_release_surface.py`), against `MAX_TEST_MODULE_LINES`
  of 700. The golden copy lives in a fixture so that the module's growth is
  readers and plantings only. It is re-measured at implementation.
- AC-HRP-1, 2, 4, 7, 9, 10, 11, 13, 14 and 15 cite their stage only, because
  the tests that will verify them do not exist yet. AC-HRP-19 cites its stage
  only because it is read directly. Every other criterion cites existing tests
  whose names survive this change. Milestone 6 adds the new selectors
  (DEC-HRP-020).
- The drafting run, on 2026-10-16:
  - The first draft's
    `planlint --target . validate --fail-on INFO --change harden-release-pipeline`
    exited 1, with one `WARN H003`: a sequencing constraint no criterion could
    verify. It was resolved as a decision and a `tasks.md` gate (DEC-HRP-025,
    Milestone 2), and the constraints were renumbered.
  - The re-run printed `1 spec(s) checked · 0 error · 0 warn · 0 info` and
    `PASS`, exit 0.
  - `python -m pytest tests/test_spec_test_citations.py -q -p no:cacheprovider`
    exited 0.
- The revision run, in the `claude/harden-release-pipeline` worktree:
  - `planlint --target . validate --fail-on INFO --change harden-release-pipeline`
    printed `1 spec(s) checked · 0 error · 0 warn · 0 info` and `PASS`, exit
    0. The two `INFO` lines saying G006 and G009 are skipped in a scoped run
    are notices, not findings.
  - `planlint --target . validate --fail-on ERROR` printed
    `55 spec(s) checked · 0 error · 0 warn · 0 info` and `PASS`, exit 0.
  - `python -m pytest tests/test_spec_test_citations.py tests/test_spec_status.py tests/test_stage_citations.py -q -p no:cacheprovider`
    exited 0.
  - `planlint --target . graph --format json --change harden-release-pipeline`
    yields all 26 `AC-HRP` criteria with `has_stage` true.
- Hand the revision back to `spec-adversary` before any edit outside this
  directory.
- **Gate:** `make pre-pr`

## Milestone 2 — Preconditions, recorded before any edit outside this package (owner)

- The implementation pull request stays a GitHub draft through this
  milestone. No criterion observes a tag, a release or a merge on `dev`, so
  the draft state is what keeps the change from merging early (DEC-HRP-025).
  - 2026-10-16: #59 was marked ready for review. The same day #58 merged
    `lean-production-tree` package-first, and the owner chose the same for
    this package: #59 carries the package alone, and the hold moves to the
    implementation pull request.
- `v0.3.0` is tagged, published and back-merged:
  - `git ls-remote --tags origin v0.3.0` prints the tag and its peeled line;
  - `curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/0.3.0/json`
    prints `200`;
  - `git fetch origin && git merge-base --is-ancestor 'v0.3.0^{commit}' origin/dev`
    exits 0.

  Record all three with their output and the date. Also record that 0.3.0's
  GitHub release was created by hand, as its own runbook said. That is the
  last release this package's `release` job does not create.
- `lean-production-tree`'s implementation has merged into `dev`, not only
  its package (#58, `9f5c693`). Record the implementation's squash commit, and
  `git show origin/dev:docs/hooks.md` showing the "Releasing" runbook step
  this package amends. `git cat-file -e origin/dev:docs/distribution-plan.md`
  must fail.
- Bring this branch to `origin/dev` by merging it in, never by force-pushing.
- The owner settings this package relies on, read back and recorded as they
  stand. This package changes none of them:
  - private vulnerability reporting enabled
    (`gh api repos/ianshank/planlint/private-vulnerability-reporting`), which
    `SECURITY.md`'s reporting route needs;
  - the `v*` tag ruleset (`gh api repos/ianshank/planlint/rulesets`), which
    DEC-HRP-018 relies on, and its bypass for tag creation and deletion,
    which Milestone 7 uses;
  - the Actions settings (`gh api repos/ianshank/planlint/actions/permissions`):
    the allowed-actions setting and whether full-length SHA pinning is
    required (DEC-HRP-005);
  - the default token permission
    (`gh api repos/ianshank/planlint/actions/permissions/workflow`), whose
    `default_workflow_permissions` must read `read`. It is the backstop for
    any job with no `permissions:` key;
  - immutable releases (Settings → General → Releases), which DEC-HRP-009 and
    DEC-HRP-016 name.

  A setting that is off is recorded as off. Only a disabled private
  vulnerability reporting stops this milestone, because a security policy
  whose route is a dead link is worse than the one it replaces.
- **Gate:** every precondition above recorded here with its sha, its output
  and the date, then `make test` on the branch after the merge from
  `origin/dev`. No milestone below starts until this is recorded.

## Milestone 3 — The guards, seen red first

- `tests/test_release_surface.py`, in the release-workflow section, beside
  the existing tests, which keep their names and bodies (C-HRP-2,
  DEC-HRP-019). The pure readers, each `(text) -> list[str]` of offenders
  naming the job and the line:
  - `_checkout_credential_offenders`: every `actions/checkout` step's `with:`
    holds `persist-credentials: false` (R-HRP-1).
  - `_publish_attestation_offenders`: one `actions/attest` step after the
    download and before the publisher, with `subject-path: dist/*` under its
    `with:`. It must carry none of `predicate-type`, `predicate`,
    `predicate-path` or `sbom-path`, and `publish`'s permissions must be
    exactly the three of R-HRP-3. Split the job into steps the way
    `_publisher_step_declares` in `tests/test_workflow_posture.py` does.
  - `_release_notes_step_offenders`: the two tag-only `build` steps, the
    artifact name `release-notes`, the upload's `if-no-files-found: error`,
    and their place between the version check and the `dist` upload
    (R-HRP-4).
  - `_release_job_offenders`: covers R-HRP-5 to R-HRP-8. That is:
    - `needs: publish` and the exact `if:`;
    - the permissions;
    - no `actions/checkout`, and exactly two downloads, of `dist` and
      `release-notes`;
    - `GH_TOKEN: ${{ github.token }}`, never `secrets.*`;
    - these name offenders one at a time, and they are the layer that still
      holds when a commit edits both `release.yml` and its golden copy. A
      form they miss is refused by the golden copy below;
    - all five verification flags present;
    - verification before creation, and `--verify-tag`;
    - no `SOFT_FAIL` token from `tests/workflow_support.py`, and no `if:` on
      any step;
    - no `${{` inside any `run:` script.
  - `_write_line_offenders(files)` (R-HRP-5) reads every file under
    `.github/workflows/`, whatever its extension.
    - `_logical_lines(text)` splits with `str.splitlines()`. It joins a
      line ending in `\` to the next line, with that line's leading
      whitespace dropped, unless the first line is a full-line comment.
    - An offender is a `collections.Counter` of the `(file, stripped line)`
      pairs whose lower-cased text contains `write` that differs from
      `_WRITE_LINES`. So is a line holding a `\x`, `\u`, `\U` or `\N`
      escape, a `!!` or `!<` tag, or a leading `%`.
    - `_WRITE_LINES` holds two kinds of line:
      - the qualifying lines measured at `d630412` with
        `grep -n -i write .github/workflows/*.yml | grep -v -E ':[0-9]+:\s*#'`:
        `release.yml`'s `id-token: write`, and `ci.yml`'s `::error::` echo,
        in its joined form
        `[ ! -f "$EVIDENCE/findings.json" ] || { echo "::error::an unscannable target must write no envelope"; fail=1; }`;
      - the two lines this change adds: `attestations: write` in `publish`
        and `contents: write` in `release`.

    `grep -n -E '\\[xuUN]|(^|\s)(!!|!<)|^%' .github/workflows/*.yml` found
    nothing at `ff3c4cb`, exit 1. On 2026-10-16 the joined reader was
    quiet on the real tree, and it named:
    - an escaped line break;
    - a Unicode line separator, a next line and a lone carriage return
      after a comment;
    - `!!binary`;
    - every spelling `_write_line_offenders` already named.
- The golden copy (R-HRP-6, DEC-HRP-007). It parses neither YAML nor shell.
  - `_normalised_workflow(data: bytes)`: refuse non-ASCII bytes. Turn each
    `\r\n` into `\n`, and refuse any carriage return that remains. Then
    split on `"\n"`, strip each line's trailing `" \t"`, and replace
    `@[0-9a-f]{40} # v[\w.-]+$` with `@<pin>` and
    `^(  PYTHON_DEFAULT: )"[0-9.]+"$` with `\1"<python>"`. Then drop the
    trailing blank lines.
  - Require `_normalised_workflow(RELEASE_YML)` to equal the same function
    of `tests/fixtures/release-workflow.golden`. Name the first differing
    line by number, through `itertools.zip_longest`, so that an added or a
    missing last line is named too.
  - The `.golden` suffix keeps the copy out of every reader that globs
    `*.yml`.

  Checked on 2026-10-16 with this normalisation, against `release.yml` at
  `d630412` as its own golden copy:
  - admitted: the file unchanged, the whole file in CRLF, trailing spaces, a
    Dependabot pin bump, and a `PYTHON_DEFAULT` bump;
  - refused:
    - a column-0 comment followed by a step;
    - a tab-only line;
    - `---` followed by a second document;
    - a job after the last one;
    - a second `env:` after `jobs:`;
    - `defaults:` in flow form;
    - `cache-mode: write` and a scalar `concurrency:`;
    - an `on: release` trigger;
    - a no-break space;
    - a `PYTHON_DEFAULT` value carrying more than digits and dots;
    - text after a pin;
    - the last line removed.

  `_write_line_offenders` was checked against the same tree plus `ci.yml`
  plantings. It is quiet on the real tree. It names `"write"`, a quoted
  key, `Write`, the flow form, a next-line value, a folded value, an
  anchor with its alias, `"\x77rite"`, `write-all` and a write scope
  after a column-0 comment.
- Planned test functions, named here so the stage-only verification lines can
  be re-pointed once they exist:
  - `test_every_release_checkout_drops_its_credential` (AC-HRP-1);
  - `test_a_release_checkout_that_keeps_its_credential_is_named` (AC-HRP-2);
  - `test_publish_attests_build_provenance_before_it_uploads` (AC-HRP-3);
  - `test_a_publish_job_that_attests_late_wrongly_or_not_at_all_is_named`
    (AC-HRP-4), parametrized over the plantings AC-HRP-4 lists;
  - `test_build_renders_the_release_notes_on_a_tag_only` (AC-HRP-6);
  - `test_a_release_notes_step_that_runs_untagged_late_or_loose_is_named`
    (AC-HRP-7), parametrized over the plantings AC-HRP-7 lists;
  - `test_the_release_job_is_wired_after_publish_and_holds_one_write_scope`
    (AC-HRP-8);
  - `test_a_second_contents_write_or_a_loose_release_condition_is_named`
    (AC-HRP-9);
  - `test_the_release_job_is_checkout_free_and_verifies_before_it_creates`
    (AC-HRP-10);
  - `test_a_release_job_that_reaches_the_tree_or_weakens_verification_is_named`
    (AC-HRP-11), parametrized over the plantings the line readers can see,
    each asserting its own offender text. These are the ones inside the
    `release` job's steps, its flags, its conditions and its `env:`. The
    rest go to the golden-comparison test below;
  - `test_release_workflow_matches_its_golden_copy` (AC-HRP-10), the real
    file against `tests/fixtures/release-workflow.golden`;
  - `test_the_golden_comparison_admits_only_the_pinned_workflow`
    (AC-HRP-11), a unit test of `_normalised_workflow` and the comparison
    over every planting AC-HRP-11 lists, with the admitted forms above;
  - `test_write_appears_only_on_the_named_lines` (AC-HRP-8), the real tree;
  - `test_a_write_scope_spelled_any_other_way_is_named` (AC-HRP-9), over
    every spelling AC-HRP-9 lists.

  Real-tree tests read `RELEASE_YML` and `WORKFLOWS` from
  `tests/workflow_support.py` and are `integration`. Planted tests feed
  strings to the readers and are `unit`, except where they load `_common`,
  which makes them `integration`. `tests/test_suite_shape.py` decides, not
  this list.
- `tests/test_workflow_pins.py`, beside `_dependabot_entries` and the
  Dependabot tests: `_cooldown_offenders(text)` reads the `github-actions`
  entry's `cooldown:` mapping for a `default-days` integer. The test is
  `test_github_actions_version_updates_wait_out_a_cooldown`. It checks the
  real file, and that a planted entry without `cooldown` is named (AC-HRP-18,
  R-HRP-11). The value seven is read in review, not pinned in the test,
  following DEC-HCW-008's objection to a test that is a second copy of a
  config value.
- New `tests/test_release_notes.py`, flat under `tests/`, fully typed, with a
  module docstring naming this package. Each test runs `main` in-process
  through `run_tool_main("release_notes", "release_notes.py", ...)` (program
  name first), or calls the script's pure function through
  `load_tool("release_notes", "release_notes.py")`. Planned:
  - `test_release_notes_print_the_body_of_the_named_section`;
  - `test_release_notes_keep_subsections_and_stop_at_the_next_section`;
  - `test_release_notes_drop_link_definitions_that_close_the_section`;
  - `test_release_notes_find_the_current_version_in_this_changelog`, which
    reads `CHANGELOG.md` and `openspec_graph.__version__`;
  - `test_release_notes_refuse_a_version_with_no_section`;
  - `test_release_notes_refuse_an_empty_section`;
  - `test_release_notes_refuse_a_malformed_version`, parametrized over
    `v0.4.0`, `Unreleased`, `0.0.0-gate-rehearsal` and `0.4`;
  - `test_release_notes_refuse_a_duplicated_section`;
  - `test_release_notes_refuse_a_link_definition_inside_the_section`;
  - `test_release_notes_refuse_a_missing_changelog`;
  - `test_release_notes_write_utf8_under_an_ascii_console`, which uses
    `monkeypatch` to put an `io.TextIOWrapper(io.BytesIO(), encoding="ascii")`
    in `sys.stdout` and decodes the bytes;
  - `test_release_notes_import_only_the_standard_library`, an AST read of the
    script against `sys.stdlib_module_names` plus `_common`.

  Every refusal asserts exit 2, empty stdout, and one stderr line naming the
  version and the path (AC-HRP-13 to AC-HRP-15).
- `tests/test_gate_scripts.py`: add `"release_notes.py",` to
  `test_gate_script_is_runnable_as_a_script`'s parametrize list (AC-HRP-16).
- Run `python -m pytest tests/test_release_surface.py tests/test_workflow_pins.py tests/test_release_notes.py -q`
  against the unchanged workflow with the tool absent, and record here what
  each real-tree guard names. Expected:
  - both checkouts named as keeping the credential;
  - no attest step;
  - no notes steps;
  - no `release` job;
  - no cooldown;
  - the notes tests erroring because the script does not exist;
  - the golden-copy test erroring because
    `tests/fixtures/release-workflow.golden` does not exist until
    Milestone 4;
  - the write-line test naming nothing, since the tree has no unlisted
    line yet.

  The planted tests pass where they need no file. Do not commit this state,
  because a commit whose suite is red by design is one the ladder cannot
  bisect past (`pin-actions-by-sha` DEC-ASP-011).
- **Gate:** `make test`. It is red by design here, with exactly the offenders
  recorded and nothing else. The commit is Milestone 4's.

## Milestone 4 — The workflow, the tool and the configuration, in the same commit as Milestone 3

- `.github/workflows/release.yml`, `gate`. The checkout's `with:` gains
  `persist-credentials: false` below `fetch-depth: 0`. The comment above the
  ancestry step gains these sentences (R-HRP-2, DEC-HRP-011):
  - the checkout persists no credential, so this step's fetches, its own and
    `tag-ancestry`'s, run unauthenticated, which a public repository allows;
  - on a repository that needs authentication to fetch, the first fetch exits
    128 before `make pre-pr` runs;
  - the remedy is for the step's script, with `GH_TOKEN` from
    `${{ github.token }}` in its `env:`, to export three variables before the
    first fetch:
    - `GIT_CONFIG_COUNT=1`;
    - `GIT_CONFIG_KEY_0=http.https://github.com/.extraheader`;
    - `GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"`.

    The header must be computed in the shell because an `env:` expression
    has no base64, and the exports die with the step. Never use
    `persist-credentials: true`.
- `build`: the checkout gains `with: persist-credentials: false`. After the
  "Confirm the tag matches the packaged version" step and before the `dist`
  upload, add (R-HRP-4, DEC-HRP-006):

  ```yaml
      # Tag runs only: a dry run on the integration branch precedes the
      # version's changelog section. Before the dist upload, so a tag pushed
      # without its section uploads nothing and publishes nothing.
      - name: Render this version's release notes from the changelog
        if: github.ref_type == 'tag'
        run: python tools/release_notes.py "${GITHUB_REF_NAME#v}" > "$RUNNER_TEMP/notes.md"

      - name: Upload the release notes
        if: github.ref_type == 'tag'
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: release-notes
          path: ${{ runner.temp }}/notes.md
          if-no-files-found: error
  ```

  The upload pin is the one the `dist` upload carries. Re-read it at the
  head, because the agreement guard needs the pair identical.
- `publish`: the comment above `permissions:` is extended in place (R-HRP-3).
  `pypa/gh-action-pypi-publish` mints the OIDC token through
  `id-token: write`, and `actions/attest` signs the build provenance with the
  same token and stores it through `attestations: write`. It needs no
  `artifact-metadata: write`, which is only for a registry push's storage
  record. Nothing else in this job needs more than `contents: read`,
  restated because a job-level block replaces the top-level one. The block
  gains `attestations: write`. Between the `dist` download and the publisher:

  ```yaml
      # SLSA v1 build provenance for the exact bytes uploaded below, attested
      # here rather than in build: no dry-run attestation, and this job runs
      # no repository code. No predicate input and no sbom-path, which is what
      # selects provenance. The bundle goes under RUNNER_TEMP, so dist/ still
      # holds only the build output when the publisher uploads it.
      - uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
        with:
          subject-path: dist/*
  ```

  The publisher step and its `with:` block are untouched (C-HRP-2).
- A new job after `publish` (R-HRP-5 to R-HRP-8, DEC-HRP-007 to DEC-HRP-010,
  DEC-HRP-013):

  ```yaml
    release:
      name: Create the GitHub release
      needs: publish
      if: github.ref_type == 'tag'
      runs-on: ubuntu-latest
      timeout-minutes: 5
      # gh release create needs contents: write; gh attestation verify reads
      # the attestations API (attestations: read). No checkout and no
      # repository code: the one write token in either workflow never meets
      # the tagged tree.
      permissions:
        contents: write
        attestations: read
      steps:
        - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
          with:
            name: dist
            path: dist/

        - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
          with:
            name: release-notes
            path: ${{ runner.temp }}/release-notes

        - name: Verify every file's build provenance before it is released
          env:
            GH_TOKEN: ${{ github.token }}
            GH_REPO: ${{ github.repository }}
          run: |
            for f in dist/*; do
              gh attestation verify "$f" --repo ianshank/planlint \
                --signer-workflow ianshank/planlint/.github/workflows/release.yml \
                --source-ref "refs/tags/$GITHUB_REF_NAME" \
                --source-digest "$GITHUB_SHA" \
                --deny-self-hosted-runners
            done

        - name: Create the release from the verified files
          env:
            GH_TOKEN: ${{ github.token }}
            GH_REPO: ${{ github.repository }}
          run: >-
            gh release create "$GITHUB_REF_NAME" dist/*
            --verify-tag
            --title "planlint ${GITHUB_REF_NAME#v}"
            --notes-file "$RUNNER_TEMP/release-notes/notes.md"
  ```

  The comment sits inside the job body, between `release:` and
  `permissions:` (`tests/workflow_support.py`'s comment rule). An empty
  `dist/` leaves the glob literal, so `gh attestation verify` fails on a
  missing file and the step fails closed. Write
  `tests/fixtures/release-workflow.golden` as a byte copy of the new
  `release.yml` in the same commit (R-HRP-6). Every later edit of the
  workflow edits it too. Re-read the
  download pin at the head. No `concurrency` block (R-HRP-9).
- New `tools/release_notes.py` (R-HRP-13, R-HRP-14, DEC-HRP-026):
  - A module docstring naming this package and the exit contract.
  - A `sys.path` bootstrap and `from _common import repo_root`, as
    `tools/check_docs.py` does.
  - `VERSION = re.compile(r"^\d+\.\d+\.\d+$")`,
    `SECTION = re.compile(r"^## \[(?P<version>[^\]]+)\]")` and
    `LINK_DEFINITION = re.compile(r"^\[[^\]]+\]:\s")`.
  - `section_body(text: str, version: str) -> str`, a pure function raising
    `NotesError(ValueError)` with the refusal's message. In order:
    - count the headings whose captured version equals the argument (zero
      means absent, two or more means duplicated);
    - take the lines from the heading to the next `## ` line or the end of
      the file;
    - find the first `LINK_DEFINITION` line among them. If every non-blank
      line from there on is one, cut there; if not, refuse;
    - strip outer blank lines;
    - refuse an empty result.

    No length check.
  - `parse_args(argv: Sequence[str]) -> argparse.Namespace`.
  - `main(argv: Sequence[str] | None = None) -> int`:
    - parses `argv[1:]`, taking `sys.argv` when `None`;
    - resolves `--changelog` from `repo_root()` only when not given;
    - reads with `path.read_text(encoding="utf-8")`, catching `OSError` and
      `UnicodeDecodeError`, and never through `_common.read_text`, whose `""`
      for a missing file would read as "no section";
    - reconfigures stdout to UTF-8 the way `openspec_graph/cli.py` does,
      guarded by `hasattr`, then writes the body and one newline and returns
      0;
    - on a refusal prints one line to stderr and returns 2.
  - `if __name__ == "__main__": sys.exit(main())`.
  - Every public function, and the exception class, carries a docstring. No
    entry is added to the docstring ratchet in `pyproject.toml`.
- `pyproject.toml`, `[tool.specgraph.action_major_floors]`: add
  `"actions/attest" = 4` after the `download-artifact` row. The header comment
  is unchanged; the action is an ordinary pinned JavaScript action (R-HRP-10).
- `.github/dependabot.yml`, the `github-actions` entry, after `schedule:`: add
  `cooldown:` with `default-days: 7`, under a comment. Version updates wait a
  week after an action release, so a compromised or broken one has time to
  be pulled first. Security updates are exempt by the platform's rule. GitHub
  Actions supports `default-days` only. Nothing else in the entry changes
  (R-HRP-11, DEC-HRP-014).
- New `.github/CODEOWNERS`: a comment, then `* @ianshank`. The comment says
  the file names the owner of every path and requests their review on pull
  requests others open, and enforces nothing while the branch rulesets
  require no approving review. Enforcement is reopened when a second
  maintainer exists (R-HRP-12, DEC-HRP-015).
- Confirm `python tools/check_no_hardcoded_thresholds.py` prints its PASS
  line, with the script absent from the diff (C-HRP-3).
- **Gate:** `make test`, then `make thresholds`.

## Milestone 5 — Documents

- `SECURITY.md` (R-HRP-16, DEC-HRP-016). Keep "Reporting a vulnerability",
  the threat model and "What is not a vulnerability", and add:
  - **Scope.** In: the `planlint` package on PyPI, the composite action under
    `.github/actions/`, the skill and plugin manifests, and this repository's
    workflows. Out: third-party actions this repository uses (report those
    upstream), GitHub itself, and adopters' own repositories and workflows.
  - **Timeline and disclosure.** Acknowledged within 7 days; a fix or a
    reasoned statement within 90. A GitHub security advisory, with a CVE
    where one applies, at the fix or at day 90, whichever is first. The
    reporter may publish after day 90.
  - **Safe harbour.** One sentence: good-faith research that follows this
    policy, touches no one else's data and disrupts nothing is welcome, and
    will not be pursued.
  - **How fixes ship.** A `hotfix/*` branch into `main` and the next patch of
    the latest minor (`docs/hooks.md` "Branching and promotion"); earlier
    minors receive nothing. This sits beside the existing "Supported
    versions".
  - **Verifying a release.** Download the published files with
    `python -m pip download --no-deps planlint==<version>` or from the
    GitHub release. Check the publish attestation with
    `pipx run pypi-attestations verify pypi --repository https://github.com/ianshank/planlint pypi:<file>`.
    Check the build provenance with
    `gh attestation verify <file> --repo ianshank/planlint --signer-workflow ianshank/planlint/.github/workflows/release.yml --source-ref refs/tags/v<version>`.
    Then one sentence: the build provenance meets SLSA Build L2.

  No L3 anywhere. Every version in these commands is a placeholder, and no
  line reads `ianshank/planlint…@v<digits>` (the adopter corpus's
  `_TAG_REF`). The "Supported versions" section keeps its literal version:
  it is release-prep's to edit, not this package's (R-HRP-16). The
  existing `planlint --version` and `rules --json` block stays.
- `docs/hooks.md` (R-HRP-17, DEC-HRP-017):
  - **The `release` row**, after `make pre-pr` and the clean-venv smoke test,
    gains: the release notes rendered from the version's changelog section;
    SLSA build provenance for both files (`actions/attest`) beside trusted
    publishing's PEP 740 attestations; and the checkout-free `release` job
    that verifies the provenance with `gh attestation verify` and creates the
    GitHub release with both files.
  - **In "Releasing"**, the verify step gains the `gh attestation verify`
    command of `SECURITY.md`, run on both files. The GitHub-release step
    stays where R-LPT-4 puts it and keeps naming the `[X.Y.Z]` section, and
    now reads: the GitHub release, cut from the `[X.Y.Z]` section by the
    release workflow's `release` job. Confirm it with
    `gh release view vX.Y.Z --json assets --jq '.assets|length'`, which
    prints 2, and never create it by hand. If the job failed, re-run it, and
    failing that verify locally and run the job's own `gh release create`
    with `--verify-tag` (DEC-HRP-010).
- `.claude/skills/planlint-release/SKILL.md`, the "Tag the production merge
  commit" step: after the tag, the release workflow publishes and its
  `release` job creates the GitHub release; verify both attestations. It
  names no new path, and every command it names is real
  (`test_path_like_backtick_references_resolve_to_real_files`,
  `test_release_skill_uses_only_real_promotion_subcommands`).
- `docs/next-steps.md`, the floating-`v1` row (`:231` at drafting), second
  cell (R-HRP-18, DEC-HRP-018). The decision stays: the contract is declared
  stable at 1.0. Draft text for the new reason: a floating major promises that
  every later release under it is compatible with the one a workflow pinned,
  which a pre-1.0 contract does not promise. Both need a root `action.yml` or
  a moving tag. The release workflow's one `contents: write` belongs to its
  checkout-free `release` job, which creates the release for the exact tag
  pushed and moves no tag, and the `v*` tag ruleset forbids updating one.
- `tools/AGENTS.md` (R-HRP-19). The budget is one added line: the file is 59
  lines against `MAX_NESTED_LINES = 60`. A natural reflow of the edited
  sentences reaches 61 and fails `test_nested_agents_file_stays_short`, so
  shorten wording to fit rather than letting the paragraph wrap. The edits:
  - the mermaid `rel` node names `release_notes` beside `check_promotion` and
    `smoke_wheel`;
  - the stdlib-only sentence names `release_notes` beside the nine gate
    scripts, as a stdlib-only release helper that judges nothing;
  - the program-name-first argv list gains `release_notes`;
  - the gate count stays nine.

  Run `wc -l tools/AGENTS.md` after the edit and record it here.
  `docs/architecture/c4.md`'s `tools/*` row names `release_notes.py`
  (stdlib-only, run by `release.yml` `build` on a tag). Its group sentence
  says `release_notes` is stdlib-only like the gate scripts and is not one of
  them.
- `CHANGELOG.md`, `[Unreleased]`: a new heading,
  ``### Changed — the release workflow attests its build, verifies it and creates its own GitHub release (`harden-release-pipeline`)``.
  The backticked name in parentheses is the shape `tools/spec_status.py`'s
  `_CHANGELOG_HEADING` reads. Under it go bullets for each item R-HRP-19
  names. It lands under `[Unreleased]`, and the 0.4.0 release-prep moves it.
  Order relative to `lean-production-tree`'s and `prepare-release-0-4-0`'s
  entries is whichever merged first. Keep all of them.
- **Gate:** `make pre-pr`

## Milestone 6 — Verification, records and the selectors

- Re-point the stage-only verification lines in
  `specs/release-pipeline/spec.md` to the tests Milestones 3 and 4 created,
  keeping each stage:
  - AC-HRP-1, 2: the two checkout tests;
  - AC-HRP-4: the planted publish test;
  - AC-HRP-7: the planted notes test;
  - AC-HRP-9: the planted write-scope test;
  - AC-HRP-10, 11: the release-job tests and the two golden-copy tests;
  - AC-HRP-8, 9: also the two write-line tests;
  - AC-HRP-13, 14, 15: the notes-tool tests;
  - AC-HRP-3, 6, 8, 18: also cite their new real-tree tests beside the
    existing ones.

  Then run `python -m pytest tests/test_spec_test_citations.py -q` and
  confirm every selector in every spec resolves.
- Record the exit codes of
  `planlint --target . validate --fail-on INFO --change harden-release-pipeline`
  and of the unscoped `planlint --target . validate --fail-on ERROR`.
- Run `make stage-citations` and confirm the set of stages no workflow
  invokes is unchanged from the drafting measurement above.
- Dry run of the implementation branch's workflow:
  `gh workflow run release.yml --ref <branch>`, then
  `ID=$(gh run list --workflow release.yml --branch <branch> -L1 --json databaseId --jq '.[0].databaseId'); gh run watch "$ID" --exit-status`.
  Expect `gate` and `build` green, `make pre-pr` passing with no persisted
  credential, the two notes steps skipped, and `publish` and `release`
  skipped. Record the run id. A red `gate` here is a step that needed the
  credential: find it, and never restore persistence to pass (DEC-HRP-011).
- Only then mark the pull request ready for review.
- **Gate:** `make pre-pr`

## Milestone 7 — After the merge (owner): the dry run on `dev` and the gate rehearsal

- `gh workflow run release.yml --ref dev`, watched as above. Record the run
  id: `gate` and `build` green; `publish` and `release` skipped.
- Before the rehearsal tag, run
  `git fetch origin && python tools/check_promotion.py tag-ancestry --sha "$(git rev-parse origin/dev)" --fetch; echo $?`.
  It must print 1. Had it printed 0, the `dev` tip would be on `main`'s
  first-parent chain and the rehearsal would reach `make pre-pr` and
  `build`, so stop and record.
- Push the tag. `R=$(git rev-parse origin/dev); git tag -a v0.0.0-gate-rehearsal "$R" -m "Gate rehearsal for harden-release-pipeline; delete after the run"`,
  then `git push origin v0.0.0-gate-rehearsal`, by the owner and never
  `GITHUB_TOKEN`. The tag ruleset's creation bypass applies, and the
  PreToolUse guard asks.
- Watch the run and record its id. Expected (DEC-HRP-024):
  - the ancestry step's log shows the default-branch fetch succeeding without
    a credential and the worktree added;
  - `tag-ancestry` prints that the commit is not on the production branch,
    and the step exits 1, not 128;
  - `make pre-pr`, `build`, `publish` and `release` do not run;
  - `curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/0.0.0-gate-rehearsal/json`
    prints 404;
  - `gh release view v0.0.0-gate-rehearsal` finds no release.
- Delete the tag: `git push origin :refs/tags/v0.0.0-gate-rehearsal && git tag -d v0.0.0-gate-rehearsal`.
  The remote deletion needs the tag ruleset's deletion bypass as well as the
  creation bypass the push used. The ruleset forbids deleting a `v*` tag, so
  only the owner's bypass role can remove it. Then
  `git ls-remote --tags origin v0.0.0-gate-rehearsal` prints nothing. No
  release references the tag, so immutability does not lock it.
- Hand-off to the 0.4.0 release, which first exercises the attest step and
  the `release` job. Its record carries:
  - `gh attestation verify` on both published files, with the flags of
    `SECURITY.md`;
  - `gh release view v0.4.0 --json assets --jq '.assets|length'` printing 2;
  - whether the `release` job's verification passed with the declared
    `attestations: read`, which DEC-HRP-008 leaves unverified until then;
  - the release run's id, also copied here before the post-release sweep
    removes this package.
- **Gate:** every observation above recorded here with its run id, sha and
  date, in a pull request into `dev` whose own `make pre-pr` exits 0.
