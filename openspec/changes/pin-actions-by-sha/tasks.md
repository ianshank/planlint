# Tasks: pin-actions-by-sha

Measured at `5fe043e` on `claude/m1-pin-and-release`. Every line number
below is re-checked against the tree before the milestone that uses it; a
sibling package landing first may move a line without moving the fact. The
order is deliberate (DEC-ASP-011): the guard first and seen red, then the
pins, then the records, then the full ladder.

## Milestone 1 — The guard, red on the unpinned tree

- `tests/test_workflow_hardening.py`: rewrite `_uses_refs(paths)` to iterate
  `text.splitlines()` raw, split each line at its first `#` into a code half
  and a comment half, match `_USES` against the code half, and return
  `(path, lineno, owner_repo, ref, version)` where `version` is the comment
  half when it is exactly `vMAJOR.MINOR.PATCH` after stripping whitespace,
  else `None`. A line whose code half is blank is a whole-line comment and
  yields nothing, so `_code_lines`'s posture is kept for every other guard
  (R-ASP-6, DEC-ASP-002). Update every caller to the five-tuple.
- `tests/test_workflow_hardening.py`: add `_PIN_COMMENT = re.compile(r"^v\d+\.\d+\.\d+$")`
  and `_pin_offenders(paths) -> list[str]`: for each third-party ref, a
  non-SHA ref is `"{file}:{line} {action}@{ref} is not a commit SHA"`, a SHA
  with `version is None` is `"… has no `# vX.Y.Z` release-tag comment"`, and
  a comment present but not matching `_PIN_COMMENT` is named as malformed
  (R-ASP-1, DEC-ASP-001, DEC-ASP-004). Replace `_sha_refs` with
  `_uncommented_sha_refs(paths)`: the SHA-ref offenders only.
- `tests/test_workflow_hardening.py`: `_ref_disagreements` groups on the
  `(ref, version)` pair and names each copy as `"{file}:{line} @{ref} #
  {version}"` (R-ASP-5, DEC-ASP-004). `_floor_offenders` takes
  `_major(version)` when `_SHA.match(ref)` and `_major(ref)` otherwise, and
  reports a SHA whose comment yields no major as having no version to hold to
  the floor (R-ASP-4, DEC-ASP-008); its docstring's "the plan's W1.2 owns
  those" sentence goes, since this is W1.2.
- `tests/test_workflow_hardening.py`: rename
  `test_no_third_party_action_ref_is_a_commit_sha` to
  `test_no_third_party_action_ref_is_a_commit_sha_without_its_version_comment`
  — the old name stays a substring, so AC-HCW-24's citation keeps resolving
  (C-ASP-2, DEC-ASP-007) — asserting `_uncommented_sha_refs(ACTION_REF_SCAN)
  == []`, with a docstring naming AC-HCW-24 as superseded and why the name
  carries the prefix. Add
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  asserting `_pin_offenders(ACTION_REF_SCAN) == []` after the existing
  "found no third-party uses: at all" sanity assertion (AC-ASP-1). Update the
  section comment above these tests from "none is a SHA" to "every one is".
- `tests/test_workflow_hardening.py`: keep the names and move the planted
  text to the pinned shape with synthetic SHAs (`"a" * 40`, `"b" * 40`):
  `test_a_leftover_retired_major_is_reported_with_file_and_line` (two
  different SHAs, each with its comment, plus the inert whole-line comment);
  `test_a_uniformly_retired_major_is_named_with_file_and_line` (two files on
  one SHA with `# v4.2.2`, agreement empty, floor naming both);
  `test_an_action_without_a_floor_is_named` (`some/action@<sha> # v2.0.0`
  with no row, named; keep the `_major` assertions and add
  `_major("v3.38.2") == 3`); `test_the_own_action_ref_is_exempt_from_the_sha_check`
  (own-action bare SHA and `./` local not reported; the third-party bare SHA
  on the next line is) (R-ASP-8, C-ASP-1).
- `tests/test_workflow_hardening.py`: new planted tests, each collecting
  offenders and asserting file and line in the message (R-ASP-8):
  `test_an_unpinned_ref_is_named_with_file_and_line` — `@v7`, `@release/v1`,
  a bare SHA, `# v7`, `# 7.0.1`, and a whole-line `# uses:` that is not
  reported (AC-ASP-2); `test_the_version_comment_is_read_from_the_raw_line`
  — `_uses_refs` yields the version while `_code_lines` of the same text
  carries no `#` (AC-ASP-2); `test_a_comment_disagreement_behind_one_sha_is_named`
  — one SHA, `# v7.0.1` and `# v7.0.0`, both named (AC-ASP-6);
  `test_a_version_comment_below_the_floor_is_named` — `# v4.2.2` against a
  floor of 7 (AC-ASP-4); `test_threshold_guard_stays_quiet_on_a_sha_pinned_uses_line`
  — a planted workflow step `uses: actions/checkout@<sha> # v7.0.1` yields
  `[]` from `check_workflow`, and a planted `--cov-fail-under` in the same
  file still does not (AC-ASP-16).
- `pyproject.toml`: under `[tool.specgraph.action_major_floors]`, add
  `"pypa/gh-action-pypi-publish" = 1` with a comment: pinned to a tagged
  commit by `pin-actions-by-sha`, so it has a version for the floor to read
  (R-ASP-3, DEC-ASP-005). No other row moves.
- Run `python -m pytest tests/test_workflow_hardening.py -q` against the
  still-unpinned tree and record here the offender list
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  prints: it must name every `uses:` line in the Evidence list of
  `proposal.md` — the ten checkout and nine setup-python lines in `ci.yml`,
  its two upload-artifact and one gitleaks lines, `release.yml`'s seven,
  `action.yml`'s two, the template's two, the README's one — and
  `release.yml:117 pypa/gh-action-pypi-publish@release/v1 is not a commit
  SHA`. The floor guard must also go red: the publisher now has a row and no
  version (AC-ASP-14, DEC-ASP-011).
- **Gate:** `make test` — red by design at the end of this milestone, with
  exactly the offenders recorded above and nothing else; green is Milestone
  2's gate.

## Milestone 2 — The pins, as one batch

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
  (C-ASP-5).
- `.github/actions/planlint/action.yml`: setup-python at 163 and
  upload-artifact at 337 as above. Nothing else changes (C-ASP-3).
- `templates/spec-gate.yml`: checkout at 52 as above;
  `github/codeql-action/upload-sarif@v3` →
  `github/codeql-action/upload-sarif@1190a975f95ce23525efb6a3fc21ea29567c1b52 # v3.38.2`
  at 82; in the comment block at lines 59–63, add two sentences: the
  third-party steps are pinned to commit SHAs with the release tag in the
  trailing comment, and a `github-actions` Dependabot entry in the adopter's
  repository moves SHA and comment together. Line 65's own-action ref
  untouched. Copy the file over
  `skills/planlint-spec-governance/assets/spec-gate.yml` so
  `test_skill_asset_matches_template` stays green (R-ASP-7, DEC-ASP-006,
  C-ASP-1).
- `README.md`: the workflow block's `actions/checkout@v7` at line 400 as
  above; lines 403 and 451 untouched (R-ASP-7, C-ASP-1).
- Confirm `cmp templates/spec-gate.yml
  skills/planlint-spec-governance/assets/spec-gate.yml` is silent, and that
  `grep -rn "release/v1"` over the scan set finds nothing (AC-ASP-8).
- **Gate:** `make test`

## Milestone 3 — Records and docs

- `.github/dependabot.yml`: rewrite the header paragraph at lines 16–22 —
  every third-party action is pinned to a commit SHA with its release tag in
  a trailing comment (`pin-actions-by-sha`); Dependabot rewrites SHA and
  comment as one update and classifies the update from the comment, which is
  why the comment is required; the publisher is on a tagged commit rather
  than a branch and stays out of the `actions-minor` group. The three
  `updates:` entries and the group are unchanged (R-ASP-9, DEC-ASP-009,
  C-ASP-3).
- `docs/next-steps.md`: the row at line 227 keeps its first cell and its
  second cell becomes the closing — closed by `pin-actions-by-sha`: every
  third-party `uses:` in the workflows, the composite action, the templates
  and the README is a commit SHA with the release tag in a trailing comment,
  `tests/test_workflow_hardening.py` holds the shape, the floor reads the
  comment, Dependabot moves both (R-ASP-9, DEC-ASP-010).
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
  floor table's new row, the renamed guard, and that this supersedes
  `harden-ci-workflows`' C-HCW-3 and AC-HCW-24 and closes the deferral the
  "Added — Dependabot" entry below records (R-ASP-10, DEC-ASP-007,
  DEC-ASP-010). That older entry stays as written.
- Confirm `python tools/check_no_hardcoded_thresholds.py` still prints PASS
  on the pinned tree (C-ASP-3, AC-ASP-16).
- **Gate:** `make docs-check`, then `make thresholds`

## Milestone 4 — Confirm and record

- Re-point the stage-only verification lines in
  `specs/action-sha-pinning/spec.md` to the tests Milestone 1 named, now
  that they exist — AC-ASP-1 to
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  and `test_no_third_party_action_ref_is_a_commit_sha_without_its_version_comment`;
  AC-ASP-2 to `test_an_unpinned_ref_is_named_with_file_and_line` and
  `test_the_version_comment_is_read_from_the_raw_line`; AC-ASP-4 adds
  `test_a_version_comment_below_the_floor_is_named`; AC-ASP-6 adds
  `test_a_comment_disagreement_behind_one_sha_is_named`; AC-ASP-16 adds
  `test_threshold_guard_stays_quiet_on_a_sha_pinned_uses_line` — keeping each
  stage. Run `python -m pytest tests/test_spec_test_citations.py -q` and
  confirm every selector in every spec resolves, AC-HCW-24's included
  (AC-ASP-12, C-ASP-2).
- Record here the first CI run on the branch after Milestone 2: its run
  number, and from each job's log the "Download action repository" lines
  showing `actions/checkout@3d3c42e5…`, `actions/setup-python@5fda3b95…`,
  `actions/upload-artifact@043fb46d…` and `gitleaks/gitleaks-action@e0c47f4f…`
  at exactly the pinned SHAs; `security` green under gitleaks-action's
  pinned commit; every artifact upload green. `release.yml`'s
  download-artifact and publisher pins run only on a `v*` tag and are
  recorded by W1.5 with the release, not here (AC-ASP-9, DEC-ASP-003).
- Confirm this package validates clean under the repo's own rules
  (`planlint --target . validate --fail-on ERROR --change
  pin-actions-by-sha`), then the whole tree.
- Run `make stage-citations` and confirm this package added no stage to the
  set no workflow invokes by name (the stages cited here — `make test`,
  `make thresholds`, `make docs-check`, `make pre-pr` — are the ones
  `harden-ci-workflows` already cites).
- Record for the plan's M1 row, when `docs/reflection-plan-2026-10.md`
  merges: the publisher is pinned to the `v1.14.2` commit, which is also the
  `release/v1` head at pinning time (DEC-ASP-005); the guard's flip kept the
  old test name as a prefix rather than renaming it away (DEC-ASP-007); and
  the floor table gained a row for the publisher.
- **Gate:** `make pre-pr`
