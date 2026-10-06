# Spec: Action SHA Pinning

> **Change:** `pin-actions-by-sha`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Every third-party action this repository runs is referenced by a floating
major tag, and the one action with write access to a package index is
referenced by a branch. A tag or branch is a name the action's maintainers —
or anyone with push access to their repository — move, and GitHub resolves it
when the job starts, so the code that ran on a green build is not what the
next build will run. The repository's own template and README tell adopters
to pin this repository's action to a 40-hex SHA and hand them a floating
`actions/checkout` on the line above.

Three records in the tree defer SHA pinning "until the pins can be resolved
and verified". They are resolved below, from each repository's own refs
advertisement, and the two things a pinned SHA needs to stay honest are both
already in the tree: Dependabot, which rewrites a SHA pin and the version
comment beside it as one update, and `harden-ci-workflows`' per-action major
floor, which a pin alone cannot satisfy because a SHA has no major. Writing
the release tag the SHA resolves to in a trailing comment is what lets the
floor, Dependabot and a reviewer read the pin; the guard therefore requires
the comment, reads it from the raw line (the comment-stripping helper the
other guards share would never see it), applies the floor to it, and holds
every copy of one action to the same SHA and the same comment. M0's
constraint that no third-party ref may become a SHA, and the criterion that
asserts it, are superseded by this spec.

**Evidence:** measured at `5fe043e` on `claude/m1-pin-and-release`. The scan
set `ACTION_REF_SCAN` (`tests/test_workflow_hardening.py` line 40) holds
`actions/checkout@v7`, `actions/setup-python@v7`,
`actions/upload-artifact@v7`, `gitleaks/gitleaks-action@v3` in `ci.yml`;
those plus `actions/download-artifact@v8` and
`pypa/gh-action-pypi-publish@release/v1` (line 117) in `release.yml`;
setup-python and upload-artifact in `action.yml` (lines 163, 337);
`actions/checkout@v7` and `github/codeql-action/upload-sarif@v3`
(lines 52, 82) in `templates/spec-gate.yml` and its byte copy under
`skills/planlint-spec-governance/assets/`; `actions/checkout@v7` at
`README.md` line 400. `_code_lines` (line 70) drops everything after `#`;
`_major` (line 149) returns `None` for a SHA and `_floor_offenders`
(line 161) skips `None`; `_sha_refs` (line 185) feeds
`test_no_third_party_action_ref_is_a_commit_sha` (line 572), which AC-HCW-24
cites and `tests/test_spec_test_citations.py` resolves by substring over
test function names. `[tool.specgraph.action_major_floors]`
(`pyproject.toml` lines 181–187) has no row for the publisher. Resolved on
2026-10-06 from each repository's refs advertisement (what `git ls-remote
--tags https://github.com/<owner>/<repo>` prints): checkout `v7` =
`3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`); setup-python `v7` =
`5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`); upload-artifact `v7`
= `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (`v7.0.1`); download-artifact
`v8` = `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` (`v8.0.1`);
gitleaks-action `v3` = `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e`
(`v3.0.0`); codeql-action `v3` is an annotated tag whose `^{}` line is
`1190a975f95ce23525efb6a3fc21ea29567c1b52` (`v3.38.2^{}`);
gh-action-pypi-publish `v1.14.2` is an annotated tag whose `^{}` line is
`dc37677b2e1c63e2034f94d8a5b11f265b73ba33`, the `release/v1` head at
drafting. `.github/dependabot.yml` lines 16–22 record the deferral and watch
`/` and `/.github/actions/planlint`, not `templates/` or `README.md`;
`docs/next-steps.md` line 227 is the deferred row; `docs/aqa.md` line 40 and
`docs/hooks.md` lines 66–70 describe the major-tag posture.

---

## Requirements

- R-ASP-1: Every third-party `uses:` in the scan set — `.github/workflows/*.yml`,
  `.github/actions/*/action.yml`, `templates/*.yml` and the workflow snippet
  in `README.md`; a third-party action being any `uses:` whose target is
  neither a `./` local path nor this repository's own `ianshank/planlint/`
  action — MUST reference a 40-hex commit SHA, followed on the same line by a
  comment whose text is exactly the release tag that commit is the target of,
  in the form `# vMAJOR.MINOR.PATCH`. A tag ref, a branch ref, a SHA with no
  comment, and a comment of any other shape MUST each fail the suite naming
  the file and line.
- R-ASP-2: The SHA MUST be the *commit* the named tag points at. For an
  annotated tag that is the peeled `^{}` line of `git ls-remote --tags`,
  never the tag object: GitHub resolves a `uses:` SHA as a commit and a
  tag-object SHA fails to check out. Resolution is an implementation step
  whose output is recorded in `tasks.md` for every action; the guard cannot
  check it offline and MUST NOT try (C-ASP-4).
- R-ASP-3: `pypa/gh-action-pypi-publish` MUST be pinned to the peeled commit
  of its newest release tag with that tag in the comment, and MUST gain a row
  in `[tool.specgraph.action_major_floors]` at the major it is pinned to.
  `release/v1` MUST NOT remain anywhere in the scan set.
- R-ASP-4: The floor guard MUST read the major from the comment version when
  the ref is a SHA and hold it to `[tool.specgraph.action_major_floors]`. A
  comment whose major is below the action's floor, and a pinned action with no
  row in the table, MUST each fail the suite naming the file and line. No
  existing row MAY be lowered or removed. This amends R-HCW-17: the floor
  applies to the version the pin's comment names, and its branch-ref
  exemption lapses because no branch ref remains.
- R-ASP-5: All references to one action across the scan set MUST agree on
  both the SHA and the comment version. A disagreement in either MUST fail
  the suite naming every disagreeing file and line. This carries R-HCW-2
  forward onto the pair rather than the ref alone.
- R-ASP-6: The version comment MUST be read from the raw `uses:` line — its
  text after the first `#` — not from the comment-stripped code the shared
  `_code_lines` helper yields. A whole-line comment that mentions a `uses:`
  MUST still satisfy nothing and trip nothing.
- R-ASP-7: `templates/spec-gate.yml`, its byte-identical copy under
  `skills/planlint-spec-governance/assets/`, and `README.md`'s copyable
  workflow block MUST carry the same pins as the workflows, and the
  template's comment block MUST say that the third-party pins are commit SHAs
  with the release tag in the comment and that Dependabot keeps them fresh.
- R-ASP-8: Every guard this spec adds or amends MUST live in
  `tests/test_workflow_hardening.py`, MUST read the files it judges rather
  than compare to a version string or a real action's SHA, MUST collect every
  offender before asserting, and MUST be shown red on a planted
  counter-example: a tag ref, a branch ref, a SHA with no comment, a
  malformed comment, a comment below the floor, uniformly retired comments
  across two files, and a comment disagreement behind one SHA. The guard MUST
  be written and run against the unpinned tree before the pins land, and the
  offenders it names there recorded in `tasks.md`.
- R-ASP-9: `.github/dependabot.yml`'s header, `docs/next-steps.md`'s deferred
  row and `CHANGELOG.md` MUST no longer describe SHA pinning as deferred, and
  `docs/aqa.md`'s CI-pin example and `docs/hooks.md`'s floor paragraph MUST
  describe the pinned posture: a commit SHA, the release tag in a trailing
  comment, the floor read from the comment.
- R-ASP-10: `CHANGELOG.md`'s `[Unreleased]` section MUST carry an entry for
  this change naming the pin format, the publisher's move from a branch ref
  to a tagged commit, the floor table's new row, and the supersession of
  C-HCW-3 and AC-HCW-24.
- C-ASP-1: This repository's own `ianshank/planlint/.github/actions/planlint@<sha>`
  ref in the template, the skill asset and the README MUST be untouched, as
  MUST `./.github/actions/planlint` in `ci.yml` and the guard's own-action
  exemption. `tests/test_adopter_urls.py` and `docs/distribution-plan.md` are
  not edited.
- C-ASP-2: No test function cited by another package's spec MAY be renamed or
  removed. `test_no_third_party_action_ref_is_a_commit_sha` MUST remain a
  substring of a test function name under `tests/`, and every `pytest -k`
  selector in every spec MUST resolve after this change. No shipped
  package's spec is edited.
- C-ASP-3: No rule changes — `RULES`, the README's rules table and
  `tests/baseline_rules.json` are unchanged; no `make` target changes; no
  workflow job is renamed or removed; the composite action's inputs, outputs
  and defaults are unchanged apart from its two `uses:` lines; Dependabot's
  three entries and its `actions-minor` group are unchanged apart from the
  header comment; `tools/check_no_hardcoded_thresholds.py` is not edited and
  stays quiet on a pinned `uses:` line.
- C-ASP-4: No test in the suite MAY open a network connection. Tag
  resolution is a recorded implementation step, not a suite assertion.
- C-ASP-5: No release, tag or version bump; `release.yml`'s job chain,
  permissions and `id-token: write` are unchanged. The publisher's PEP 740
  attestation behaviour is not claimed by this spec: the pinned commit is the
  `release/v1` head, so the action's behaviour is unchanged, and the first
  `v*` tag (W1.5) is where it is observed.

---

## Decisions

- **DEC-ASP-001:** the pin is `@<40-hex> # vMAJOR.MINOR.PATCH` — the peeled
  commit, then one comment holding exactly the release tag that commit is the
  target of. The SHA is the pin; the comment is for the three readers a bare
  SHA defeats: the floor guard, which has no major to read from forty hex
  digits; Dependabot, which classifies a SHA-pinned action's update as major,
  minor or patch from that comment and rewrites it with the SHA; and a
  reviewer, who can check the pair with one `git ls-remote` line. The full
  tag rather than a bare major (`# v7`) because a major says nothing the
  floor table does not already say, while the exact tag names what the SHA
  is. Rejected: pinning the tag with the SHA in the comment, which is
  backwards — GitHub resolves the ref, not the comment; a version in a
  separate `env:` map, which no guard or bot reads against the `uses:` line.
- **DEC-ASP-002:** `_uses_refs` reads the raw line, not `_code_lines`.
  R-HCW-15's rule that a comment satisfies nothing and trips nothing is right
  for every other guard in the module and is kept for every other guard; the
  pin comment is the one comment that *is* data, and it sits on the same
  line as the code it describes. So `_uses_refs` splits each raw line at its
  first `#`, matches `uses:` against the code half, and takes the version
  from the comment half; a whole-line comment has an empty code half and
  still counts for nothing. The helper returns a fifth element — the version
  or `None` — and every caller unpacks it. Rejected: a second pass over the
  raw file to pair comments with lines, which is the same read done twice.
- **DEC-ASP-003:** the guard checks shape, floor and agreement, and nothing
  that needs the network. It cannot know that `3d3c42e…` is `v7.0.1`; it can
  know the ref is a SHA, the comment is a tag, the tag's major clears the
  floor, and every copy agrees. Resolution — that the SHA is the commit the
  comment names — is the implementation step: `git ls-remote --tags
  https://github.com/<owner>/<repo>` per action, the `^{}` line for an
  annotated tag, recorded in `tasks.md` beside the drafting values, and the
  first CI run after the pins cross-checked against the "Download action
  repository" lines in its job log. Rejected: a network assertion in the
  suite, which is red on a sandboxed runner and on a fork pull request with
  no token for reasons unrelated to the tree; a committed lockfile of
  tag-to-SHA mappings, which is a second copy of the pin for Dependabot to
  miss.
- **DEC-ASP-004:** a SHA with no comment, or with a malformed one, is an
  offender, not a skip. Without the comment the floor guard has nothing to
  read, so a silent skip would make the floor vacuous exactly where it is
  needed, and Dependabot could not classify the update. Likewise a comment
  disagreement behind one SHA: two copies with the same SHA and different
  tags means one copy is lying about what it pins, so the agreement guard
  compares the (SHA, version) pair and names both. Both are planted and shown
  red.
- **DEC-ASP-005:** the publisher is pinned to
  `dc37677b2e1c63e2034f94d8a5b11f265b73ba33 # v1.14.2`, the peeled commit of
  its newest release tag, not to the `release/v1` branch head. The two are
  the same commit at drafting, so the choice costs nothing today and decides
  what moves it tomorrow: a tag is cut on purpose and has a version Dependabot
  can write in the comment; a branch head moves whenever its maintainers
  push, with no version to name. The plan's W1.2 says a tag SHA; this agrees.
  The floor table gains `"pypa/gh-action-pypi-publish" = 1` because the
  action now carries a version and R-HCW-17's "no floor" clause would
  otherwise report it. Dependabot's `actions-minor` group still excludes it
  by pattern, so a publisher bump stays its own pull request. The release
  caveat is recorded, not claimed: the pinned commit is the branch head, so
  nothing the action does changes — its default PEP 740 attestations under
  trusted publishing included — and the first `v*` tag (W1.5) is where that
  is observed.
- **DEC-ASP-006:** the template, its byte copy under `skills/` and the README
  snippet are pinned too. DEC-HCW-012 put them in the scan set so adopters
  are not handed what the workflows retire, and a floating `checkout` beside
  a SHA-pinned own-action is the inconsistency `docs/next-steps.md`'s row
  names. The cost is the one DEC-HCW-012 accepted: Dependabot watches neither
  file, so a bump of `.github/` alone fails the agreement guard until the
  template, the asset and the README move too — the intended effect. The
  own-action ref stays, owned elsewhere (C-ASP-1); the template's commented
  `#   uses: ianshank/planlint/...@v0.2.0` line is a whole-line comment and
  inert to the guard.
- **DEC-ASP-007:** C-HCW-3 and AC-HCW-24 are superseded here, and
  `harden-ci-workflows`' spec is not edited. A shipped package's record is
  what it decided when it shipped; later reversals are named in the package
  that reverses them (R-ZCG-13, DEC-ZCG-003). AC-HCW-24's verification line
  cites `test_no_third_party_action_ref_is_a_commit_sha`, which the citation
  guard resolves by substring over every test function name, so the guard
  that replaces it is named
  `test_no_third_party_action_ref_is_a_commit_sha_without_its_version_comment`:
  a true statement of what it checks now — no pin has lost its comment — and
  a name that keeps the retired criterion's citation resolving without
  touching it. `test_the_own_action_ref_is_exempt_from_the_sha_check` keeps
  its name and its meaning. Rejected: deleting the old test, which breaks the
  citation guard for the whole tree and forces an edit to a shipped spec;
  keeping the exact old name over an inverted body, which is a test whose
  name lies.
- **DEC-ASP-008:** the floor stays a *major floor* and is applied to the
  comment. DEC-HCW-014's argument is unchanged by the pin: a floor ratchets,
  a bump never edits it, and it is the invariant the agreement guard lacks —
  every copy sliding back together is still agreement. What changes is where
  the major comes from: `_major(ref)` for a tag ref (which the shape guard
  already names, so the floor guard only meets one on a planted tree), and
  `_major(version)` from the comment for a SHA. Rejected: a per-action pinned
  version in `pyproject.toml`, which is the second copy of the pin
  DEC-HCW-008 rejected.
- **DEC-ASP-009:** `.github/dependabot.yml` changes only in its header. The
  `actions-minor` group's `patterns: ["actions/*"]` and minor/patch
  update-types already express the right policy and work on SHA pins through
  the version comment — the second reason the comment is mandatory. No
  `ignore:`; no entry for `templates/` or `README.md`, because the
  `github-actions` ecosystem reads neither and the agreement guard is what
  carries them.
- **DEC-ASP-010:** the deferral records close in place rather than being
  deleted. `docs/next-steps.md`'s row stays in the deferred table with its
  second cell rewritten as the closing — this package, the guard, and the
  comment the floor reads — so the trail from deferral to closure is
  readable; the Dependabot header's paragraph is rewritten the same way; the
  CHANGELOG's historical Dependabot entry is a dated record and stays, and
  the new `[Unreleased]` entry says it closed.
- **DEC-ASP-011:** the guard lands first and is run red against the unpinned
  tree, then the pins, then the records, then the full ladder. A guard
  written after the pins is never seen to fail against the tree it was
  written for; the red run — naming every tag ref in the scan set and the
  publisher's branch ref — is the proof it reads the real files, and it is
  recorded in `tasks.md` with the offender list.

---

## Acceptance Criteria

- [ ] **AC-ASP-1:** every third-party `uses:` under `.github/workflows/`,
  `.github/actions/`, `templates/` and in `README.md`'s workflow snippet is
  `@<40-hex> # vMAJOR.MINOR.PATCH`, and no tag ref or branch ref remains in
  the scan set. (R-ASP-1, R-ASP-3)
  _Verified by:_ stage: `make test`

- [ ] **AC-ASP-2 (non-success):** a planted tag ref (`@v7`), a planted branch
  ref (`@release/v1`), a planted SHA with no comment, and a planted SHA whose
  comment is not a release tag (`# v7`, `# 7.0.1`) each fail the suite with
  a message naming the file and line; a whole-line comment mentioning a
  `uses:` is not reported; and the version is read from the raw line while
  the comment-stripped code carries none. (R-ASP-1, R-ASP-6, R-ASP-8)
  _Verified by:_ stage: `make test`

- [ ] **AC-ASP-3:** every pinned third-party action's comment names a major
  at or above its row in `[tool.specgraph.action_major_floors]`, and every
  pinned action — the publisher included — has a row. (R-ASP-3, R-ASP-4)
  _Verified by:_ `pytest -k test_every_third_party_action_meets_its_major_floor` · stage: `make test`

- [ ] **AC-ASP-4 (non-success):** two files agreeing on one synthetic SHA
  with a comment below the floor pass the agreement guard and fail the floor
  guard with both files and lines named; a pinned action missing from the
  table is named. (R-ASP-4, R-ASP-8)
  _Verified by:_ `pytest -k "test_a_uniformly_retired_major_is_named_with_file_and_line or test_an_action_without_a_floor_is_named"` · stage: `make test`

- [ ] **AC-ASP-5:** every reference to one action across the scan set carries
  the same SHA and the same comment, and the template under `skills/` is
  byte-identical to `templates/spec-gate.yml` after the pins. (R-ASP-5,
  R-ASP-7)
  _Verified by:_ `pytest -k "test_every_reference_to_one_action_agrees_on_one_ref or test_skill_asset_matches_template"` · stage: `make test`

- [ ] **AC-ASP-6 (non-success):** two copies of one action on different SHAs
  fail naming each file and line, and two copies on the same SHA with
  different comments fail the same way. (R-ASP-5, R-ASP-8)
  _Verified by:_ `pytest -k test_a_leftover_retired_major_is_reported_with_file_and_line` for the SHA half, the comment half by stage until its test exists · stage: `make test`

- [ ] **AC-ASP-7:** this repository's own action ref is exempt: a planted
  own-action SHA with no comment and a planted `./` local action are not
  reported while a third-party SHA with no comment on the next line is; and
  the template still pins the own action to the SHA the adopter-URL test
  requires. (C-ASP-1)
  _Verified by:_ `pytest -k "test_the_own_action_ref_is_exempt_from_the_sha_check or test_ci_template_pins_the_floor_the_skill_enforces"` · stage: `make test`

- [ ] **AC-ASP-8:** `release.yml`'s publisher is the peeled commit of its
  newest release tag with that tag in the comment, `release/v1` appears
  nowhere in the scan set, and the `gate → build → publish` chain, its
  permissions and `id-token: write` are unchanged. (R-ASP-3, C-ASP-5)
  _Verified by:_ `pytest -k test_release_workflow_is_gated_and_uses_trusted_publishing` · stage: `make test`

- [ ] **AC-ASP-9:** `tasks.md` records, for every third-party action, the
  `git ls-remote --tags` line the pin was taken from — the `^{}` line for an
  annotated tag — and the SHA in the tree equals it; the first CI run on the
  branch after the pins shows each action downloaded at its pinned SHA, with
  the run number recorded. (R-ASP-2, C-ASP-4)
  _Verified by:_ the recorded `ls-remote` lines against the tree, and the run's job log · stage: `make pre-pr`

- [ ] **AC-ASP-10:** the composite action's inputs, outputs and defaults are
  unchanged and it still declares no token input and no `permissions:`; its
  only diff is two `uses:` lines. (C-ASP-3)
  _Verified by:_ `pytest -k "test_the_action_declares_exactly_the_v1_inputs or test_the_action_needs_no_token_and_no_privileged_permission"` · stage: `make test`

- [ ] **AC-ASP-11:** the rule set is unchanged, Dependabot still watches
  every composite-action directory, and it still has no `pip` ecosystem.
  (C-ASP-3)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_every_composite_action_directory_is_watched_by_dependabot or test_dependabot_does_not_add_a_pip_ecosystem"` · stage: `make test`

- [ ] **AC-ASP-12:** every `pytest -k` selector in every spec under
  `openspec/changes/` resolves to a test function after this change,
  AC-HCW-24's included, with no shipped package's spec edited. (C-ASP-2,
  DEC-ASP-007)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make test`

- [ ] **AC-ASP-13:** the Dependabot header, the `docs/next-steps.md` row and
  the CHANGELOG no longer describe SHA pinning as deferred; `docs/aqa.md` and
  `docs/hooks.md` describe the pinned posture; the required documents still
  exist and are linked. No automated guard asserts the prose; it is read
  directly. (R-ASP-9, R-ASP-10)
  _Verified by:_ stage: `make docs-check`

- [ ] **AC-ASP-14 (non-success):** the pin-shape guard, run against the tree
  before the pins land, fails naming every floating tag ref in the scan set
  and the publisher's branch ref, each with file and line; the offender list
  is recorded in `tasks.md`. (R-ASP-8, DEC-ASP-011)
  _Verified by:_ the recorded red run · stage: `make test`

- [ ] **AC-ASP-15:** no workflow job is renamed or removed; `docs/hooks.md`'s
  CI table still lists every `ci.yml` job. (C-ASP-3)
  _Verified by:_ `pytest -k test_hooks_ci_table_lists_every_ci_job` · stage: `make test`

- [ ] **AC-ASP-16:** `tools/check_no_hardcoded_thresholds.py` is unedited and
  reports PASS on the finished tree, with a planted pinned `uses:` line and
  its version comment yielding no finding from `check_workflow`. (C-ASP-3)
  _Verified by:_ the guard's PASS line on the finished tree, with the script absent from the diff · stage: `make thresholds`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-ASP-1..8, 10..12, 14, 15 — every pin-shape, floor and agreement guard green on the real tree and red on its planted counter-example; every spec citation resolves |
| Threshold guard | `make thresholds` | AC-ASP-16 — the guard is unedited and prints PASS with the pinned lines in place |
| Docs | `make docs-check` | AC-ASP-13 — the deferral records closed, the posture prose updated, the document set intact |
| Self-check | `make validate` | this package validates clean against the repo's own rules, then the whole tree |
| Full | `make pre-pr` | AC-ASP-9 as the local equivalent of the observed run; full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
