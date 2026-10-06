# Tasks: pin-actions-by-sha

Measured at `5fe043e` on `claude/m1-pin-and-release`; `write-down-policies`'
draft landed on the branch afterwards as `openspec/` only. Every line number
below is re-checked against the tree before the milestone that uses it; a
sibling package landing first may move a line without moving the fact.

Order (DEC-ASP-011, DEC-ASP-012): the guard first and seen red, then the
pins — Milestones 1 and 2 are **one commit**, and the red tree is recorded
here, never committed — then the records, then the full ladder. This
package lands first of M1's three, before `write-down-policies` and before
`prepare-release-0-3-0`; the shared edit sites and what each later package
does at them are listed under Milestone 4.

## Milestone 1 — The guard, red on the unpinned tree [DONE]

- `tests/test_workflow_hardening.py`: replace the single-path `ACTION_YML`
  with `ACTION_YMLS = sorted((REPO_ROOT / ".github" / "actions").glob("*/action.yml"))`
  and splat it into `ACTION_REF_SCAN`, so a second composite action is inside
  the scan without an edit (R-ASP-1). Keep a module-level
  `ACTION_YML = REPO_ROOT / ".github" / "actions" / "planlint" / "action.yml"`
  only if another guard in the module still reads that one file by name;
  otherwise drop it.
- `tests/test_workflow_hardening.py`: rewrite `_uses_refs(paths)` to iterate
  `text.splitlines()` raw, split each line at its first `#` into a code half
  and a comment half, match `_USES` against the code half, and return
  `(path, lineno, owner_repo, ref, comment)` where `comment` is the stripped
  comment half as text, or `None` when the line has no `#`. The reader
  applies no pattern. A line whose code half is blank is a whole-line comment
  and yields nothing, so `_code_lines`'s posture is kept for every other
  guard (R-ASP-6, DEC-ASP-002). Update every caller to the five-tuple.
- `tests/test_workflow_hardening.py`: add `_PIN_COMMENT = re.compile(r"^v\d+\.\d+\.\d+$")`
  and `_pin_offenders(paths) -> list[str]`: for each third-party ref, a
  non-SHA ref is `"{file}:{line} {action}@{ref} is not a commit SHA"`; a SHA
  with `comment is None` is `"{file}:{line} {action}@{ref} has no `# vX.Y.Z`
  release-tag comment"`; a SHA whose comment does not match `_PIN_COMMENT` is
  `"{file}:{line} {action}@{ref} # {comment} is not a release tag; expected
  `# vMAJOR.MINOR.PATCH`"` (R-ASP-1, DEC-ASP-001, DEC-ASP-004). Delete
  `_sha_refs`.
- `tests/test_workflow_hardening.py`: `_ref_disagreements` groups on the
  `(ref, comment)` pair, names each copy as `"{file}:{line} @{ref} #
  {comment}"`, and ends every message with "`templates/spec-gate.yml`, its
  copy under `skills/planlint-spec-governance/assets/` and `README.md` are
  not watched by Dependabot; carry the SHA and its `# vX.Y.Z` comment there
  by hand." (R-ASP-5, DEC-ASP-004, DEC-ASP-006). `_floor_offenders` takes
  `_major(comment or "")` when `_SHA.match(ref)` and `_major(ref)` otherwise,
  `continue`s when the result is `None` — a branch ref, a bare SHA or an
  unparseable comment is the shape guard's to name — and reports a
  below-floor SHA as `"{file}:{line} {action}@{ref} # {comment} is below its
  floor v{floor}"` (R-ASP-4, DEC-ASP-008); its docstring's "the plan's W1.2
  owns those" sentence becomes "the shape guard owns those", since this is
  W1.2.
- `tests/test_workflow_hardening.py`: delete
  `test_no_third_party_action_ref_is_a_commit_sha` (C-ASP-2, DEC-ASP-007).
  Add `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  asserting `_pin_offenders(ACTION_REF_SCAN) == []` after the existing
  "found no third-party uses: at all" sanity assertion (AC-ASP-1), and
  `test_a_sha_pin_without_its_release_tag_comment_is_named` planting a bare
  third-party SHA beside a commented one and asserting the bare one alone is
  named with file and line and the "has no `# vX.Y.Z` release-tag comment"
  text (AC-ASP-2). Update the section comment above these tests from "none
  is a SHA" to "every one is".
- `tests/test_workflow_hardening.py`: keep the names and move the planted
  text to the pinned shape with synthetic SHAs (`"a" * 40`, `"b" * 40`):
  `test_a_leftover_retired_major_is_reported_with_file_and_line` (two
  different SHAs, each with its comment, plus the inert whole-line comment;
  assert the message's hand-carry tail);
  `test_a_uniformly_retired_major_is_named_with_file_and_line` (two files on
  one SHA with `# v4.2.2`, agreement empty, floor naming both with
  `# v4.2.2 is below its floor v7` in the message);
  `test_an_action_without_a_floor_is_named` (`some/action@<sha> # v2.0.0`
  with no row, named; the planted `pypa/gh-action-pypi-publish@release/v1`
  line still not reported by the floor guard; keep the `_major` assertions
  and add `_major("v3.38.2") == 3`); `test_the_own_action_ref_is_exempt_from_the_sha_check`
  (own-action bare SHA and `./` local not reported by `_pin_offenders`; the
  third-party bare SHA on the next line is) (R-ASP-8, C-ASP-1).
- `tests/test_workflow_hardening.py`: new planted tests, each collecting
  offenders and asserting file and line in the message (R-ASP-8):
  `test_an_unpinned_ref_is_named_with_file_and_line` — `@v7`, `@release/v1`,
  `# v7`, `# 7.0.1` (the last two named as malformed with the expected shape
  quoted), and a whole-line `# uses:` that is not reported (AC-ASP-2);
  `test_the_version_comment_is_read_from_the_raw_line` — `_uses_refs` yields
  the comment text while `_code_lines` of the same text carries no `#`
  (AC-ASP-2); `test_a_comment_disagreement_behind_one_sha_is_named` — one
  SHA, `# v7.0.1` and `# v7.0.0`, both named (AC-ASP-6);
  `test_a_version_comment_below_the_floor_is_named` — `# v4.2.2` against a
  floor of 7, the comment version in the message (AC-ASP-4);
  `test_threshold_guard_stays_quiet_on_a_sha_pinned_uses_line` — a planted
  workflow step `uses: actions/checkout@<sha> # v7.0.1` yields `[]` from
  `check_workflow`, and a planted `--cov-fail-under` in the same file still
  does not (AC-ASP-16).
- `tests/test_workflow_hardening.py`: `_dependabot_entries` reads a
  `directories:` key whose value is a flow list (`["/", "/x"]`) or a block
  list (`- "/"` lines under it) as one `(ecosystem, directory)` pair per
  element, alongside the singular `directory:`. Add
  `test_a_plural_directories_entry_is_read_as_one_pair_per_directory`
  planting both forms and asserting the pairs (R-ASP-11, AC-ASP-17).
  `test_an_unwatched_digest_is_named` is unchanged.
- `tests/test_ci_hardening.py`: `_dependabot_directories` returns the union
  of every `directory: "<x>"` value and every element of every
  `directories:` list, flow or block form; its docstring says both keys are
  read and why. `test_every_composite_action_directory_is_watched_by_dependabot`
  is unchanged and keeps reading the real file (R-ASP-11, AC-ASP-11).
- `pyproject.toml`: under `[tool.specgraph.action_major_floors]`, add
  `"pypa/gh-action-pypi-publish" = 1`. Rewrite the header comment above the
  table: the floor applies to the release tag in a pin's trailing comment
  (`pin-actions-by-sha`), and its last two lines — the publisher "rides a
  branch ref" and "has no major to floor" — become: the publisher is pinned
  to a tagged commit and is a Docker-backed action whose image is named
  after the ref; its floor of 1 is the baseline a future v2 would have to
  clear (R-ASP-3, R-ASP-9, DEC-ASP-005). No other row moves.
- `harden-ci-workflows`' three amendments (DEC-ASP-007) are already in this
  stack from drafting. `prepare-release-0-3-0`'s AC-REL-12 cites no test —
  that package's own revision recast it and C-REL-4 as a diff property read
  under `make pre-pr` — so this package edits no sibling (C-ASP-2,
  DEC-ASP-012).
- Run `python -m pytest tests/test_workflow_hardening.py -q` against the
  still-unpinned tree and record here the offender list
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  prints: it must name every `uses:` line in the Evidence list of
  `proposal.md` — the ten checkout and nine setup-python lines in `ci.yml`,
  its two upload-artifact and one gitleaks lines, `release.yml`'s seven,
  `action.yml`'s two, the template's two, the README's one — each as "is not
  a commit SHA", `release.yml:117 pypa/gh-action-pypi-publish@release/v1`
  among them. The floor guard must stay green on that tree: every tag ref
  still clears its floor, and the branch ref is skipped, not reported
  (AC-ASP-14, DEC-ASP-008, DEC-ASP-011). Record the run's output here. Do
  not commit this state.
  **Recorded (2026-10-06, unpinned tree at 5fe043e + the guard edits, never
  committed):** `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  FAILED with 34 offenders, every one "is not a commit SHA", in
  `_pin_offenders`' path-then-line order — `.github/actions/planlint/action.yml`
  163 (setup-python), 337 (upload-artifact); `.github/workflows/ci.yml` 45,
  78, 111, 132, 173, 202, 282, 360, 398, 410 (checkout), 47, 80, 113, 134,
  175, 207, 364, 399, 411 (setup-python), 156, 230 (upload-artifact), 377
  (gitleaks-action); `.github/workflows/release.yml` 34, 56 (checkout), 38,
  58 (setup-python), 94 (upload-artifact), 112 (download-artifact), 117
  (`pypa/gh-action-pypi-publish@release/v1`); `README.md` 400 (checkout);
  `templates/spec-gate.yml` 52 (checkout), 82 (`github/codeql-action`) —
  exactly the Evidence list of `proposal.md`, nothing else. The floor guard
  (`test_every_third_party_action_meets_its_major_floor`) stayed green on
  that tree: every tag ref cleared its floor and the branch ref was skipped.
- **Gate:** `make test` — red by design here, with exactly the offenders
  recorded above and nothing else; the commit is Milestone 2's.

## Milestone 2 — The pins, as one batch, in the same commit [DONE]

- Re-run, for each of the seven repositories, `git ls-remote --tags
  https://github.com/<owner>/<repo>` and record the lines beside the
  drafting values below; use whatever is current, and if a value moved, say
  so here. Drafting values (2026-10-06, from each repository's refs
  advertisement — the same data the command prints):
  `3d3c42e5aac5ba805825da76410c181273ba90b1 refs/tags/v7` and
  `refs/tags/v7.0.1` (actions/checkout);
  `5fda3b95a4ea91299a34e894583c3862153e4b97 refs/tags/v7` and
  `refs/tags/v7.0.0` (actions/setup-python);
  `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a refs/tags/v7` and
  `refs/tags/v7.0.1` (actions/upload-artifact);
  `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c refs/tags/v8` and
  `refs/tags/v8.0.1` (actions/download-artifact);
  `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e refs/tags/v3` and
  `refs/tags/v3.0.0` (gitleaks/gitleaks-action);
  `87ef0dc97def48aa960fbf026a2563ee9dbdb470 refs/tags/v3` **(tag object)**
  with `1190a975f95ce23525efb6a3fc21ea29567c1b52 refs/tags/v3^{}` and
  `refs/tags/v3.38.2^{}` (github/codeql-action — pin the peeled line);
  `a892a5a61159132606e93a2fa6f4358831b04d26 refs/tags/v1.14.2` **(tag
  object)** with `dc37677b2e1c63e2034f94d8a5b11f265b73ba33 refs/tags/v1.14.2^{}`
  and `refs/heads/release/v1` (pypa/gh-action-pypi-publish — pin the peeled
  line; newest tag by `sort -V` of `refs/tags/v1.*`) (R-ASP-2, DEC-ASP-003,
  DEC-ASP-005).
  **Recorded (2026-10-06, re-run before the pins):** every value above
  unchanged — `3d3c42e5…` `refs/tags/v7` (checkout), `5fda3b95…`
  `refs/tags/v7` (setup-python), `043fb46d…` `refs/tags/v7`
  (upload-artifact), `3e5f45b2…` `refs/tags/v8` (download-artifact),
  `e0c47f4f…` `refs/tags/v3` (gitleaks-action), `87ef0dc9…` `refs/tags/v3`
  with `1190a975…` `refs/tags/v3^{}` (codeql-action, peeled line pinned),
  `dc37677b…` `refs/heads/release/v1` = `refs/tags/v1.14.2^{}` (publisher).
  CI's own "Download action repository" lines on run #195 (below) show the
  same SHAs being fetched, which is the cross-check against a wrong pin.
- Publisher image check: obtain an anonymous pull token from
  `https://ghcr.io/token?scope=repository:pypa/gh-action-pypi-publish:pull`
  and issue `HEAD https://ghcr.io/v2/pypa/gh-action-pypi-publish/manifests/<pinned sha>`
  with it; record the status (must be 200) and the `Docker-Content-Digest`
  header here, beside the review's values (`:dc37677b…` and `:release-v1`
  both `sha256:a68d05…`; `:v1.14.2` a different digest). This is the only
  exercise the publish path gets before a `v*` tag (R-ASP-3, DEC-ASP-005,
  AC-ASP-9).
  **Recorded (2026-10-06):** `HEAD …/manifests/dc37677b2e1c63e2034f94d8a5b11f265b73ba33`
  → HTTP 200, `docker-content-digest:
  sha256:a68d05519f6d7e47372aeaddab80b851b69afa89be179ec41775c72c4e3ab2d5`;
  `:release-v1` → 200 with the same digest; `:v1.14.2` → 200 with
  `sha256:5c2f7030fbef8308068eb4cc9080fd3c9e157ccf6d511924d69f8f4b23dc95c1`.
  The review's values hold.
- `.github/workflows/ci.yml`: `actions/checkout@v7` →
  `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` at
  lines 45, 78, 111, 132, 173, 202, 282, 360, 398, 410;
  `actions/setup-python@v7` →
  `@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0` at 47, 80, 113, 134,
  175, 207, 364, 399, 411; `actions/upload-artifact@v7` →
  `@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1` at 156, 230;
  `gitleaks/gitleaks-action@v3` →
  `@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e # v3.0.0` at 377 (R-ASP-1).
  `./.github/actions/planlint` at 291 untouched (C-ASP-1).
- `.github/workflows/release.yml`: checkout at 34, 56 and setup-python at
  38, 58 as above; `actions/upload-artifact@v7` at 94 as above **and**
  `actions/download-artifact@v8` →
  `@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1` at 112 in the same
  commit (R-HCW-3 still holds); `pypa/gh-action-pypi-publish@release/v1` →
  `@dc37677b2e1c63e2034f94d8a5b11f265b73ba33 # v1.14.2` at 117 (R-ASP-3).
  The `publish` job's comment, permissions and `id-token: write` unchanged
  (C-ASP-5). `prepare-release-0-3-0` will add `with: attestations: true`
  directly under this line; leave the line's trailing comment as the only
  thing after the ref so that insert is a clean addition below it.
- `.github/actions/planlint/action.yml`: setup-python at 163 and
  upload-artifact at 337 as above. Nothing else changes (C-ASP-3).
- `templates/spec-gate.yml`: checkout at 52 as above;
  `github/codeql-action/upload-sarif@v3` →
  `github/codeql-action/upload-sarif@1190a975f95ce23525efb6a3fc21ea29567c1b52 # v3.38.2`
  at 82; in the comment block at lines 59–63, add: the third-party steps are
  pinned to commit SHAs with the release tag in the trailing comment; a
  `github-actions` Dependabot entry in the adopter's repository moves SHA and
  comment together; this repository's Dependabot does not read templates, so
  these two pins are refreshed by hand when the template changes (R-ASP-7,
  DEC-ASP-006, DEC-ASP-013). No sentence may say Dependabot keeps the
  template fresh for this repository. Line 65's own-action ref untouched.
  `prepare-release-0-3-0` renames the tag in the same block; keep the new
  sentences after its tag sentence so both diffs apply. Copy the file over
  `skills/planlint-spec-governance/assets/spec-gate.yml` so
  `test_skill_asset_matches_template` stays green (C-ASP-1).
- `README.md`: the workflow block's `actions/checkout@v7` at line 400 as
  above; lines 403 and 451 untouched (R-ASP-7, C-ASP-1).
- `.github/dependabot.yml`: replace the two `github-actions` entries (lines
  26–50 and 52–61) with one carrying
  `directories: ["/", "/.github/actions/planlint"]`, the same weekly
  schedule, `open-pull-requests-limit`, labels, `ci` commit prefix and the
  `actions-minor` group with its patterns and update types; rewrite the
  entry's comment (lines 27–30) to say one entry with both directories
  yields one grouped pull request for every copy under `.github/`, which is
  what the agreement guard needs. The `docker` entry is unchanged (R-ASP-11,
  DEC-ASP-009, C-ASP-3). The header rewrite is Milestone 3's.
- Confirm `cmp templates/spec-gate.yml
  skills/planlint-spec-governance/assets/spec-gate.yml` is silent, and that
  `grep -rn "release/v1"` over the scan set finds nothing; record both here
  (AC-ASP-8).
  **Recorded (7d626ba):** `cmp` silent; `grep -rn "release/v1" .github
  templates skills/planlint-spec-governance/assets README.md` → no matches.
- **Gate:** `make test` — green; this is the commit that carries Milestone 1
  and Milestone 2 together.

## Milestone 3 — Records and docs [DONE]

- `.github/dependabot.yml`: rewrite the header paragraph at lines 16–22 —
  every third-party action is pinned to a commit SHA with its release tag in
  a trailing comment (`pin-actions-by-sha`); Dependabot rewrites SHA and
  comment as one update and classifies the update from the comment, which is
  why the comment is required; the publisher is on a tagged commit rather
  than a branch and stays out of the `actions-minor` group; the deferred row
  this closed is in `docs/next-steps.md` — the earlier attribution to
  `docs/distribution-plan.md` was wrong (R-ASP-9, DEC-ASP-009, DEC-ASP-010).
- `docs/next-steps.md`: the row at line 227 keeps its first cell and its
  second cell becomes the closing — closed by `pin-actions-by-sha`: every
  third-party `uses:` in the workflows, the composite action, the templates
  and the README is a commit SHA with the release tag in a trailing comment,
  `tests/test_workflow_hardening.py` holds the shape, the floor reads the
  comment, Dependabot moves both under `.github/`, and the template, its
  skill copy and the README are carried by hand (R-ASP-9, DEC-ASP-010).
- `docs/aqa.md` line 40: replace the `actions/checkout@v7` example with the
  pinned shape in words — a commit SHA with its release tag in a trailing
  comment — and add that the floor is read from that comment (R-ASP-9).
- `docs/hooks.md` lines 66–70: the floor paragraph says every third-party
  action is pinned to a commit SHA with its release tag in a trailing
  comment, the floor applies to the tag in the comment, and every copy of one
  action must agree on both (R-ASP-9).
- `CHANGELOG.md`, `[Unreleased]`, under the existing "Changed — the CI
  workflows now hold themselves to their own gates (M0)" heading or a
  sibling M1 heading: an entry for `pin-actions-by-sha` naming the pin
  format, the publisher's move from `release/v1` to the `v1.14.2` commit, the
  floor table's new row, the two Dependabot entries becoming one, the
  deleted and new guards, that this supersedes `harden-ci-workflows`'
  C-HCW-3 and AC-HCW-24 (amended in place, same branch), and that it closes
  the deferral the "Added — Dependabot" entry below records — whose row
  lives in `docs/next-steps.md`, not `docs/distribution-plan.md` (R-ASP-10,
  DEC-ASP-007, DEC-ASP-010). That older entry stays as written.
  `prepare-release-0-3-0` moves this entry under the release heading when
  it lands.
- Confirm `python tools/check_no_hardcoded_thresholds.py` still prints PASS
  on the pinned tree (C-ASP-3, AC-ASP-16).
  **Recorded:** `PASS: no hard-coded thresholds in Makefile or workflow
  YAML` on the pinned tree, locally and in run #195's `security` job; the
  script is absent from the diff.
- **Gate:** `make docs-check`, then `make thresholds` — both PASS on the
  finished tree.

## Milestone 4 — Confirm, record, and hand off to the siblings

- Re-point the stage-only verification lines in
  `specs/action-sha-pinning/spec.md` to the tests Milestone 1 named, now
  that they exist — AC-ASP-1 to
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`;
  AC-ASP-2 to `test_an_unpinned_ref_is_named_with_file_and_line`,
  `test_a_sha_pin_without_its_release_tag_comment_is_named` and
  `test_the_version_comment_is_read_from_the_raw_line`; AC-ASP-4 adds
  `test_a_version_comment_below_the_floor_is_named`; AC-ASP-6 adds
  `test_a_comment_disagreement_behind_one_sha_is_named`; AC-ASP-16 adds
  `test_threshold_guard_stays_quiet_on_a_sha_pinned_uses_line`; AC-ASP-17
  to `test_a_plural_directories_entry_is_read_as_one_pair_per_directory` —
  keeping each stage. Run `python -m pytest tests/test_spec_test_citations.py -q`
  and confirm every selector in every spec resolves, the re-pointed
  AC-HCW-24 included (AC-ASP-12, C-ASP-2).
  **Recorded (7d626ba → this commit):** re-pointed as listed, every stage
  kept; `python -m pytest tests/test_spec_test_citations.py -q` → 6 passed,
  every selector in every spec resolving.
- Record here the first CI run on the branch after Milestone 2: its run
  number, and from each job's log the "Download action repository" lines
  showing `actions/checkout@3d3c42e5…`, `actions/setup-python@5fda3b95…`,
  `actions/upload-artifact@043fb46d…` and `gitleaks/gitleaks-action@e0c47f4f…`
  at exactly the pinned SHAs; `security` green under gitleaks-action's
  pinned commit; every artifact upload green. `release.yml`'s
  download-artifact and publisher pins run only on a `v*` tag and are
  recorded by `prepare-release-0-3-0` with the release, not here; the
  manifest check in Milestone 2 is this package's only evidence for the
  publisher (AC-ASP-9, DEC-ASP-003, DEC-ASP-005).
  **Recorded:** CI run #195 (`actions/runs/37534942732`, `pull_request` on
  PR #39, head `7d626ba`), conclusion success, 18 jobs green. Set-up lines
  from the job logs: `security` — `Download action repository
  'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1'
  (SHA:3d3c42e5…)`, `'actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97'`,
  `'gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e'`;
  gitleaks 8.24.3 scanned 7 commits, "no leaks found", SARIF artifact
  finalized. `action-contract (passing)` — the composite action's own
  `'actions/setup-python@5fda3b95…'` and
  `'actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a'`
  downloads, then `planlint-evidence-passing` uploaded (artifact
  11446590498). `self-validate` and `graph-diff` each ran their
  `actions/upload-artifact@043fb46d…` step green. Every job's checkout and
  setup-python step is named with the pinned SHA in the run's step list.
- Confirm this package validates clean under the repo's own rules
  (`planlint --target . validate --fail-on ERROR --change
  pin-actions-by-sha`), then `--change harden-ci-workflows`, then
  `--change prepare-release-0-3-0`, then the whole tree; record each exit
  code here (AC-ASP-18).
  **Recorded (this commit):** `--change pin-actions-by-sha` 0;
  `--change harden-ci-workflows` 0; `--change prepare-release-0-3-0` 0;
  whole tree 0 — see the gate line in the commit message for the count.
- Run `make stage-citations` and confirm this package added no stage to the
  set no workflow invokes by name (the stages cited here — `make test`,
  `make thresholds`, `make docs-check`, `make validate`, `make pre-pr` — are
  ones `harden-ci-workflows` already cites).
  **Recorded:** `make stage-citations` on this tree — 16 stages cited, 12
  on a verification line, 5 invoked by no scanned workflow (`ci`,
  `security`, `thresholds`, `validate`, `wheel-check`), the same five as
  before this package; nothing added.
- Sibling hand-off, recorded here for whoever lands the next two packages
  (R-ASP-12, DEC-ASP-012): (1) `release.yml`'s publisher step — this package
  rewrote the `uses:` line at 117; `prepare-release-0-3-0` inserts
  `with: attestations: true` and its comment directly beneath it, touching
  no part of the pinned line. (2) `templates/spec-gate.yml` lines 59–68 at
  7d626ba (59–63 before the pins) and the byte copy — this package added
  the pin sentences at 64–68;
  `prepare-release-0-3-0` renames the tag in the same block; after its edit,
  re-copy the template over the skill asset so
  `test_skill_asset_matches_template` is green again. (3) `CHANGELOG.md`
  `[Unreleased]` — this package's `Changed` entry and `write-down-policies`'
  `Added` entry both sit there; `prepare-release-0-3-0` moves the whole body
  under the release heading and must land last. (4) Every place this
  package says "the first public tag, numbered by `prepare-release-0-3-0`"
  is a place that package fills in; none carries a literal version. After
  each sibling lands, run the tree gate and
  `pytest -k test_skill_asset_matches_template` and record the exit codes
  here (AC-ASP-18).
- Record for the plan's M1 row, when `docs/reflection-plan-2026-10.md`
  merges: the publisher is pinned to the `v1.14.2` commit, which is also the
  `release/v1` head at pinning time, and its Docker payload still arrives
  through a registry tag named after the SHA (DEC-ASP-005); the old no-SHA
  guard was deleted and `harden-ci-workflows`' record amended in place
  because it was on the same unmerged branch (DEC-ASP-007); the floor table
  gained a row for the publisher; Dependabot's two action entries became one
  (DEC-ASP-009); and `github/codeql-action` has no bot-driven refresh path
  under a SHA pin, accepted in writing (DEC-ASP-013).
- **Gate:** `make pre-pr`
