# Tasks: harden-release-pipeline

Drafted at `4278d4c` on `claude/lean-production-tree` (`dev` at `c0ff090`
plus `lean-production-tree`'s draft) on 2026-10-16, as Phase 2.1 of the
session plan for a lean production branch, with that plan's Phase 2.3
deferrals and its review resolutions B1–B14 and A17. That plan is not tracked
(`lean-production-tree` DEC-LPT-005). Every decision this package takes from
it is restated in `specs/release-pipeline/spec.md`.

**This package must not merge into `dev` before `v0.3.0` is tagged and
published, nor before `lean-production-tree` has merged** (Milestone 2,
DEC-HRP-025). Its pull request stays a GitHub draft through Milestone 2. It is
marked ready for review only after Milestone 6's dry run is recorded here.

Every line number below is re-read at the implementation branch's head
before the milestone that uses it, because a sibling landing first may move a
line without moving the fact. Every number names the command that produced
it.

## Measured at `4278d4c`, 2026-10-16 (drafting)

- **The gate before the draft.** `planlint --target . validate --fail-on ERROR`
  printed `55 spec(s) checked · 0 error · 0 warn · 0 info` and `PASS`, exit 0,
  before any file of this package existed.
- **The attest pin.** The refs advertisement of
  `https://github.com/actions/attest-build-provenance.git/info/refs?service=git-upload-pack`,
  fetched over HTTPS (the data `git ls-remote --tags` prints):
  - `4d101475d8b20a2381f78447822ac1eab6504dd8 refs/tags/v4.2.2`, a lightweight
    tag;
  - `8beda2b7ed98355c0e97c0a63bec38ae472e66c4 refs/tags/v4`, an annotated tag,
    with `4d101475d8b20a2381f78447822ac1eab6504dd8 refs/tags/v4^{}`;
  - no `refs/tags/v5`.

  The plan's drafting value is unchanged.
- **The composite's inner ref.**
  `https://raw.githubusercontent.com/actions/attest-build-provenance/4d101475d8b20a2381f78447822ac1eab6504dd8/action.yml`
  is `using: "composite"` with one step,
  `uses: actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d # v4.2.1`, a
  40-hex commit (DEC-HRP-005). `actions/attest`'s own refs advertisement lists
  `508db95dd578ae2727ebd6217d5ba78e4fbda05d refs/tags/v4.2.1` and
  `1e69f48acb82d1966a394da916b4c1698aa569d6 refs/tags/v4.2.2`, so the wrapper
  runs one patch behind (DEC-HRP-004). The wrapper's README at that commit
  says it "is simply a wrapper on top of `actions/attest`" and that "new
  implementations should use `actions/attest` instead".
- **Where the bundle goes.** `actions/attest@508db95…`'s `src/main.ts:99`
  writes the bundle to `path.join(await tempDir(), ATTESTATION_FILE_NAME)`.
  `tempDir` (`:234-239`) is `RUNNER_TEMP` and throws without it. Nothing is
  written under `dist/` (DEC-HRP-001).
- **The checkout default.** `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`'s
  `action.yml:52-54` declares `persist-credentials` with `default: true`.
- **The CLI.** `gh --version` printed 2.89.0 in this environment.
  `gh release create --help` documents three things: a missing tag is created
  "from the latest state of the default branch" unless `--verify-tag` is
  given; assets are attached through a draft that is then published; and
  immutability is enforced only after publishing. `gh attestation verify --help`
  lists `--repo`, `--signer-workflow`, `--source-ref` and
  `--deny-self-hosted-runners`, and the default predicate
  `https://slsa.dev/provenance/v1`. `gh release --help` lists `verify` and
  `verify-asset`.
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
- **The nested-file bound.** `wc -l tools/AGENTS.md` printed 59, against
  `MAX_NESTED_LINES` in `tests/test_agent_artifacts.py`. Milestone 5 edits that
  file in place.

## Milestone 0 — Grounding at the implementation branch's head

- Run the gate and record its exit code before the first edit outside this
  package: `planlint --target . validate --fail-on ERROR`.
- Re-read every line number `proposal.md` cites at the head, and record any
  that moved beside its drafting value.
- Re-confirm the pin. Run `git ls-remote --tags https://github.com/actions/attest-build-provenance`
  and record the `v4.2.2` line, the `v4^{}` line and the newest tag. If a
  newer release exists, pin that one instead, re-read its `action.yml` and
  record its inner `uses:` line. If that inner ref is not a 40-hex commit,
  stop: DEC-HRP-005's premise fails, and the choice of action is reopened
  under DEC-HRP-004.
- Re-read the inner `actions/attest` commit's `src/main.ts` and confirm the
  bundle is still written under `RUNNER_TEMP` and never beside the subject
  (DEC-HRP-001). Record the line.
- Confirm where the release runbook lives. `docs/hooks.md` "Releasing" must
  carry the numbered runbook, with its "GitHub release cut from the
  `[X.Y.Z]` section" step, and `docs/distribution-plan.md` must be gone. If
  the runbook is still in `docs/distribution-plan.md`, `lean-production-tree`
  has not landed: stop, because Milestone 2's precondition is not met
  (DEC-HRP-017).
- Read `prepare-release-0-4-0`'s state on `dev` and record which of the shared
  edit sites `proposal.md` lists it has already changed:
  `.github/dependabot.yml`'s header and `docker` entry, the Docker tests in
  `tests/test_release_surface.py` and `tests/test_workflow_pins.py`, and the
  `docs/hooks.md` rows.
- **Gate:** `make test`

## Milestone 1 — The change package

- `proposal.md`, `specs/release-pipeline/spec.md` and `tasks.md` are written
  spec-first, with every criterion unticked and `Status: DRAFT`. They are
  reviewed by `spec-adversary` before any edit outside this directory, and
  each finding is resolved by a decision and recorded here.
- What the draft resolved that the plan did not record, each by the clauses
  beside it, so the review can weigh them:
  - **(a) The wrapper.** The wrapper's README sends new implementations to
    `actions/attest`, and the wrapper runs `actions/attest` one patch behind.
    It is kept, as the plan's B4 chose, with a reopen trigger, in DEC-HRP-004.
    This is the decision most worth a second look.
  - **(b) A read scope.** The `release` job declares `attestations: read`
    beside `contents: write`, because its first run is unrehearsable: R-HRP-5,
    DEC-HRP-008.
  - **(c) A hosted-runner check.** `--deny-self-hosted-runners` on the
    verification: R-HRP-7, DEC-HRP-003.
  - **(d) The runbook and the release skill.** Both had a person cut the
    GitHub release, which the `release` job now does, so this package lands
    after `lean-production-tree`: R-HRP-17, DEC-HRP-017, DEC-HRP-025.
  - **(e) The private-repository remedy is scoped to the step, not to one
    fetch.** `tag-ancestry --fetch` runs its own `git fetch`, which a
    per-command `git -c` would not reach: R-HRP-2, DEC-HRP-011.
  - **(f) The SBOM reopen shape.** It uses `actions/attest`'s SBOM mode
    (`sbom-path`), not a custom `predicate-type`: DEC-HRP-021.
  - **(g) An allow-list.** "No `run:` invoking a tree path" is sharpened into
    an allow-list of the two `gh` commands, with no checkout: R-HRP-6,
    DEC-HRP-007.
  - **(h) Where the bundle goes.** Checked against the pinned source, not
    assumed: DEC-HRP-001.
  - **(i) A cooldown guard.** A guard for the Dependabot cooldown beside the
    existing Dependabot readers: R-HRP-11, DEC-HRP-019.
  - **(j) Two more documents.** `tools/AGENTS.md` and
    `docs/architecture/c4.md` name every script under `tools/`, and the
    nested file sits one line under its bound: R-HRP-19.
  - **(k) Reopen triggers** for the dev lockfile, Scorecard, signed commits
    and `CONTRIBUTING.md`. The plan gave reasons but no triggers, so the draft
    proposes them: DEC-HRP-022, DEC-HRP-023.
- AC-HRP-1, 2, 4, 7, 9, 10, 11, 13, 14 and 15 cite their stage only, because
  the tests that will verify them do not exist yet. AC-HRP-19 cites its stage
  only because it is read directly. Every other criterion cites existing tests
  whose names survive this change. Milestone 6 adds the new selectors
  (DEC-HRP-020).
- The drafting run, on 2026-10-16:
  - The first draft's
    `planlint --target . validate --fail-on INFO --change harden-release-pipeline`
    exited 1, with one `WARN H003`: a sequencing constraint no criterion could
    verify. It was resolved the way `lean-production-tree` holds its own
    preconditions, as a decision and a `tasks.md` gate. The constraint was
    removed, DEC-HRP-025 and Milestone 2 hold the order, and the constraints
    were renumbered.
  - The re-run printed `1 spec(s) checked · 0 error · 0 warn · 0 info` and
    `PASS`, exit 0. The two `INFO` lines saying G006 and G009 are skipped in a
    scoped run are notices, not findings.
  - The unscoped `planlint --target . validate --fail-on ERROR` printed
    `57 spec(s) checked · 0 error · 0 warn · 0 info` and `PASS`, exit 0. That
    count includes this package and the concurrent `prepare-release-0-4-0`
    draft.
  - `python -m pytest tests/test_spec_test_citations.py -q -p no:cacheprovider`
    exited 0.
- Hand the package to `spec-adversary` before any edit outside this
  directory.
- **Gate:** `make pre-pr`

## Milestone 2 — Preconditions, recorded before any edit outside this package (owner)

- The pull request stays a GitHub draft through this milestone. No criterion
  observes a tag, a release or a merge on `dev`, so the draft state is what
  keeps the change from merging early (DEC-HRP-025).
- `v0.3.0` is tagged, published and back-merged:
  - `git ls-remote --tags origin v0.3.0` prints the tag and its peeled line;
  - `curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/0.3.0/json`
    prints `200`;
  - `git fetch origin && git merge-base --is-ancestor 'v0.3.0^{commit}' origin/dev`
    exits 0.

  Record all three with their output and the date. Also record that 0.3.0's
  GitHub release was created by hand, as its own runbook said. That is the
  last release this package's `release` job does not create.
- `lean-production-tree` has merged into `dev`. Record its merge commit, and
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
    DEC-HRP-018 relies on;
  - the Actions settings (`gh api repos/ianshank/planlint/actions/permissions`):
    the allowed-actions setting and whether full-length SHA pinning is
    required (DEC-HRP-005);
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
  - `_publish_attestation_offenders`: one attest step after the download and
    before the publisher, with `subject-path: dist/*` under its `with:` and no
    `predicate` input, and `publish`'s permissions exactly the three of
    R-HRP-3. Split the job into steps the way `_publisher_step_declares` in
    `tests/test_workflow_posture.py` does.
  - `_release_notes_step_offenders`: the two tag-only `build` steps, the
    artifact name `release-notes`, and their place between the version check
    and the `dist` upload (R-HRP-4).
  - `_release_job_offenders`: covers R-HRP-5 to R-HRP-8. That is
    `needs: publish`; the exact `if:`; the permissions; no
    `actions/checkout`; downloads of `dist` and `release-notes` only; every
    command an allowed one; verification flags present; verification before
    creation; `--verify-tag`; no `SOFT_FAIL` token from
    `tests/workflow_support.py`; no `if:` on any step; and no `${{` inside
    any `run:` script.
  - `_contents_write_holders(texts)`: the jobs across every workflow whose
    block grants `contents: write` (R-HRP-5).

  Read the `run:` scripts raw through `_common.run_scripts`
  (`load_tool("_common", "_common.py")`) and lex them with `shlex` in POSIX
  mode with `#` as the comment character. Never read them through
  `_code_lines`: it cuts each line at its first `#`, and would cut the
  `${GITHUB_REF_NAME#v}` in the title. In command position the shell keywords
  `for`, `in`, `do`, `done`, `if`, `then`, `else`, `fi` are skipped, and any
  other word must be `gh` followed by `attestation verify` or
  `release create`.
- Planned test functions, named here so the stage-only verification lines can
  be re-pointed once they exist:
  - `test_every_release_checkout_drops_its_credential` (AC-HRP-1);
  - `test_a_release_checkout_that_keeps_its_credential_is_named` (AC-HRP-2);
  - `test_publish_attests_build_provenance_before_it_uploads` (AC-HRP-3);
  - `test_a_publish_job_that_attests_late_or_not_at_all_is_named` (AC-HRP-4);
  - `test_build_renders_the_release_notes_on_a_tag_only` (AC-HRP-6);
  - `test_a_release_notes_step_that_runs_untagged_or_late_is_named`
    (AC-HRP-7);
  - `test_the_release_job_is_wired_after_publish_and_holds_one_write_scope`
    (AC-HRP-8);
  - `test_a_second_contents_write_or_a_loose_release_condition_is_named`
    (AC-HRP-9);
  - `test_the_release_job_is_checkout_free_and_verifies_before_it_creates`
    (AC-HRP-10);
  - `test_a_release_job_that_reaches_the_tree_or_skips_verification_is_named`
    (AC-HRP-11), parametrized over the ten plantings AC-HRP-11 lists, each
    asserting its own offender text.

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
  - `test_release_notes_keep_subsections_and_stop_at_the_next_section_or_the_link_block`;
  - `test_release_notes_find_the_current_version_in_this_changelog`, which
    reads `CHANGELOG.md` and `openspec_graph.__version__`;
  - `test_release_notes_refuse_a_version_with_no_section`;
  - `test_release_notes_refuse_an_empty_section`;
  - `test_release_notes_refuse_a_malformed_version`, parametrized over
    `v0.4.0`, `Unreleased`, `0.0.0-gate-rehearsal` and `0.4`;
  - `test_release_notes_refuse_a_duplicated_section`;
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
  - the notes tests erroring because the script does not exist.

  The planted tests pass where they need no file. Do not commit this state,
  because a commit whose suite is red by design is one the ladder cannot
  bisect past (`pin-actions-by-sha` DEC-ASP-011).
- **Gate:** `make test`. It is red by design here, with exactly the offenders
  recorded and nothing else. The commit is Milestone 4's.

## Milestone 4 — The workflow, the tool and the configuration, in the same commit as Milestone 3

- `.github/workflows/release.yml`, `gate`. The checkout's `with:` gains
  `persist-credentials: false` below `fetch-depth: 0`. The comment above the
  ancestry step gains these sentences (R-HRP-2): the checkout persists no
  credential, so this step's fetches, its own and `tag-ancestry`'s, run
  unauthenticated, which a public repository allows. On a repository that
  needs authentication to fetch, the first fetch exits 128 before
  `make pre-pr` runs. The remedy is an `http.extraheader` scoped to this step
  through `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0` and `GIT_CONFIG_VALUE_0` in
  its `env:`, never `persist-credentials: true`.
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
  `id-token: write`, and `actions/attest-build-provenance` signs the build
  provenance with the same token and stores it through `attestations: write`.
  Nothing else in this job needs more than `contents: read`, restated because
  a job-level block replaces the top-level one. The block gains
  `attestations: write`. Between the `dist` download and the publisher:

  ```yaml
      # SLSA v1 build provenance for the exact bytes uploaded below, attested
      # here rather than in build: no dry-run attestation, and this job runs
      # no repository code. The bundle goes under RUNNER_TEMP, so dist/ still
      # holds only the build output when the publisher uploads it.
      - uses: actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2
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
                --source-ref "refs/tags/$GITHUB_REF_NAME" --deny-self-hosted-runners
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
  missing file and the step fails closed. Re-read the download pin at the
  head. No `concurrency` block (R-HRP-9).
- New `tools/release_notes.py` (R-HRP-13, R-HRP-14):
  - A module docstring naming this package and the exit contract.
  - A `sys.path` bootstrap and `from _common import repo_root`, as
    `tools/check_docs.py` does.
  - `VERSION = re.compile(r"^\d+\.\d+\.\d+$")`,
    `SECTION = re.compile(r"^## \[(?P<version>[^\]]+)\]")` and
    `LINK_DEFINITION = re.compile(r"^\[[^\]]+\]:\s")`.
  - `section_body(text: str, version: str) -> str`, a pure function raising
    `NotesError(ValueError)` with the refusal's message. It counts the
    headings whose captured version equals the argument (zero means absent,
    two or more means duplicated), stops at the next `SECTION` or `## `
    heading or the first `LINK_DEFINITION`, and strips outer blank lines.
  - `parse_args(argv: Sequence[str]) -> argparse.Namespace`.
  - `main(argv: Sequence[str] | None = None) -> int`. It parses `argv[1:]`,
    taking `sys.argv` when `None`, and resolves `--changelog` from
    `repo_root()` only when not given. It reads with
    `path.read_text(encoding="utf-8")`, catching `OSError` and
    `UnicodeDecodeError`, and never through `_common.read_text`, whose `""`
    for a missing file would read as "no section". It reconfigures stdout to
    UTF-8 the way `openspec_graph/cli.py` does, guarded by `hasattr`, then
    writes the body and one newline, returning 0. On a refusal it prints one
    line to stderr and returns 2.
  - `if __name__ == "__main__": sys.exit(main())`.
  - Every public function, and the exception class, carries a docstring. No
    entry is added to the docstring ratchet in `pyproject.toml`.
- `pyproject.toml`, `[tool.specgraph.action_major_floors]`: add
  `"actions/attest-build-provenance" = 4` after the `download-artifact` row.
  Append one sentence to the header comment: the action is a composite whose
  inner `actions/attest` pin is chosen by the wrapper, outside the files this
  floor and the pin guard read, and is re-read when the pin moves
  (`harden-release-pipeline` DEC-HRP-004, DEC-HRP-005) (R-HRP-10).
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

  No L3 anywhere. Every version is a placeholder, and no line reads
  `ianshank/planlint…@v<digits>` (the adopter corpus's `_TAG_REF`). The
  existing `planlint --version` and `rules --json` block stays.
- `docs/hooks.md` (R-HRP-17, DEC-HRP-017):
  - **The `release` row**, after `make pre-pr` and the clean-venv smoke test,
    gains: the release notes rendered from the version's changelog section;
    SLSA build provenance for both files (`actions/attest-build-provenance`)
    beside trusted publishing's PEP 740 attestations; and the checkout-free
    `release` job that verifies the provenance with `gh attestation verify`
    and creates the GitHub release with both files.
  - **In "Releasing"**, the verify step gains the `gh attestation verify`
    command of `SECURITY.md`, run on both files. The step that cut the GitHub
    release by hand becomes: the `release` job creates it, so confirm it with
    `gh release view vX.Y.Z --json assets --jq '.assets|length'`, which
    prints 2, and never create it by hand. If the job failed, re-run it, and
    failing that verify locally and run the job's own `gh release create`
    with `--verify-tag` (DEC-HRP-010).
- `.claude/skills/planlint-release/SKILL.md` step 3: after the tag, the
  release workflow publishes and its `release` job creates the GitHub
  release; verify both attestations. It names no new path, and every command
  it names is real (`test_path_like_backtick_references_resolve_to_real_files`,
  `test_release_skill_uses_only_real_promotion_subcommands`).
- `docs/next-steps.md`, the floating-`v1` row (`:231` at drafting), second
  cell (R-HRP-18, DEC-HRP-018). The decision stays: the contract is declared
  stable at 1.0. Draft text for the new reason: a floating major promises that
  every later release under it is compatible with the one a workflow pinned,
  which a pre-1.0 contract does not promise. Both need a root `action.yml` or
  a moving tag. The release workflow's one `contents: write` belongs to its
  checkout-free `release` job, which creates the release for the exact tag
  pushed and moves no tag, and the `v*` tag ruleset forbids updating one.
- `tools/AGENTS.md` (R-HRP-19). These are in-place edits, because the file is
  one line under `MAX_NESTED_LINES`:
  - the mermaid `rel` node names `release_notes` beside `check_promotion` and
    `smoke_wheel`;
  - the stdlib-only sentence names `release_notes` beside the nine gate
    scripts, as a stdlib-only release helper that judges nothing;
  - the program-name-first argv list gains `release_notes`;
  - the gate count stays nine.

  `docs/architecture/c4.md`'s `tools/*` row names
  `release_notes.py` (stdlib-only, run by `release.yml` `build` on a tag).
  Its group sentence says `release_notes` is stdlib-only like the gate
  scripts and is not one of them.
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
  - AC-HRP-10, 11: the two release-job tests;
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
  `GITHUB_TOKEN`. The tag ruleset's bypass applies, and the PreToolUse guard
  asks.
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
  Then `git ls-remote --tags origin v0.0.0-gate-rehearsal` prints nothing. No
  release references the tag, so immutability does not lock it.
- Hand-off to the 0.4.0 release, which first exercises the attest step and
  the `release` job. Its record carries:
  - `gh attestation verify` on both published files, with the flags of
    `SECURITY.md`;
  - `gh release view v0.4.0 --json assets --jq '.assets|length'` printing 2;
  - the release run's id, also copied here before the post-release sweep
    removes this package.
- **Gate:** every observation above recorded here with its run id, sha and
  date, in a pull request into `dev` whose own `make pre-pr` exits 0.
