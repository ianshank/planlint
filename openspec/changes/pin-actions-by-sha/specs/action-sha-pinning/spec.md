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
and verified", and two of the three point the reader at the wrong file for
the deferred row. The pins are resolved below, from each repository's own
refs advertisement, and the two things a pinned SHA needs to stay honest are
both already in the tree: Dependabot, which rewrites a SHA pin and the
version comment beside it as one update, and `harden-ci-workflows`'
per-action major floor, which a pin alone cannot satisfy because a SHA has no
major. Writing the release tag the SHA resolves to in a trailing comment is
what lets the floor, Dependabot and a reviewer read the pin; the guard
therefore requires the comment, reads it from the raw line (the
comment-stripping helper the other guards share would never see it), applies
the floor to it, and holds every copy of one action to the same SHA and the
same comment. M0's constraint that no third-party ref may become a SHA, and
the criterion that asserts it, are superseded by this spec and amended in
`harden-ci-workflows`' own record, which is on this same unmerged branch.

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
`README.md` line 400. The scan's action entry is the single path
`ACTION_YML` (line 27), not a glob. `_code_lines` (line 70) drops everything
after `#`; `_major` (line 149) returns `None` for a SHA and
`_floor_offenders` (line 161) skips `None`; `_sha_refs` (line 185) feeds
`test_no_third_party_action_ref_is_a_commit_sha` (line 572), which
`harden-ci-workflows`' AC-HCW-24 and `prepare-release-0-3-0`'s AC-REL-12
(its spec, line 438) cite and `tests/test_spec_test_citations.py` resolves
by substring over test function names in every file matching
`openspec/changes/*/specs/*/spec.md`. `[tool.specgraph.action_major_floors]`
(`pyproject.toml` lines 181–187) has no row for the publisher, and its
header comment's last two lines (179–180) say the publisher has no major to
floor. Resolved on 2026-10-06 from each repository's refs advertisement
(what `git ls-remote --tags https://github.com/<owner>/<repo>` prints):
checkout `v7` = `3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`);
setup-python `v7` = `5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`);
upload-artifact `v7` = `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
(`v7.0.1`); download-artifact `v8` =
`3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` (`v8.0.1`); gitleaks-action `v3`
= `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e` (`v3.0.0`); codeql-action `v3`
is an annotated tag whose `^{}` line is
`1190a975f95ce23525efb6a3fc21ea29567c1b52` (`v3.38.2^{}`);
gh-action-pypi-publish `v1.14.2` is an annotated tag whose `^{}` line is
`dc37677b2e1c63e2034f94d8a5b11f265b73ba33`, the `release/v1` head at
drafting. Every one of those release tags is three-part. The publisher is a
composite that runs `ghcr.io/pypa/gh-action-pypi-publish:<ref with / as ->`;
the registry tag `:dc37677b…` exists and shares its manifest digest
(`sha256:a68d05…`) with `:release-v1`, while `:v1.14.2` differs. Dependabot
writes a SHA pin's version as a trailing ` # vX.Y.Z` comment
(dependabot-core `version_commenter.rb`). `.github/dependabot.yml` lines
16–22 record the deferral and attribute it to `docs/distribution-plan.md`;
its two `github-actions` entries (lines 26–50, 52–61) share schedule, limit,
labels and prefix, and only the first carries the `actions-minor` group;
neither `templates/` nor `README.md` is watched.
`tests/test_workflow_hardening.py::_dependabot_entries` (line 456) and
`tests/test_ci_hardening.py::_dependabot_directories` (line 834) read only
the singular `directory:` key. `docs/next-steps.md` line 227 is the deferred
row; `CHANGELOG.md` line 339 attributes it to `docs/distribution-plan.md`
too; `docs/aqa.md` line 40 and `docs/hooks.md` lines 66–70 describe the
major-tag posture. `tools/check_no_hardcoded_thresholds.py::check_workflow`
(lines 92–104) is quiet on a SHA-pinned `uses:` line.
`tests/test_agent_artifacts.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
(line 491) asserts only that the publisher appears in `publish`, not its
ref. `prepare-release-0-3-0` adds `with: attestations: true` directly under
the publisher's `uses:` line, and moves the CHANGELOG's `[Unreleased]` body.

---

## Requirements

- R-ASP-1: Every third-party `uses:` in the scan set — `.github/workflows/*.yml`,
  `.github/actions/*/action.yml`, `templates/*.yml` and the workflow snippet
  in `README.md`; a third-party action being any `uses:` whose target is
  neither a `./` local path nor this repository's own `ianshank/planlint/`
  action — MUST reference a 40-hex commit SHA, followed on the same line by a
  comment whose text is exactly the release tag that commit is the target of,
  in the form `# vMAJOR.MINOR.PATCH`. The scan constant MUST hold the
  `.github/actions/*/action.yml` glob, not one composite action's path, so a
  second composite action is inside the scan without an edit. A tag ref, a
  branch ref, a SHA with no comment, and a comment of any other shape MUST
  each fail the suite naming the file and line.
- R-ASP-2: The SHA MUST be the *commit* the named tag points at. For an
  annotated tag that is the peeled `^{}` line of `git ls-remote --tags`,
  never the tag object: GitHub resolves a `uses:` SHA as a commit and a
  tag-object SHA fails to check out. Resolution is an implementation step
  whose output is recorded in `tasks.md` for every action; the guard cannot
  check it offline and MUST NOT try (C-ASP-4).
- R-ASP-3: `pypa/gh-action-pypi-publish` MUST be pinned to the peeled commit
  of its newest release tag with that tag in the comment, and MUST gain a row
  in `[tool.specgraph.action_major_floors]` at the major it is pinned to.
  `release/v1` MUST NOT remain anywhere in the scan set. Because the action's
  payload is a Docker image tagged after the ref, the implementation MUST
  record that the registry manifest for the pinned SHA's image tag exists —
  a `HEAD` against `https://ghcr.io/v2/pypa/gh-action-pypi-publish/manifests/<sha>`
  answering 200 under an anonymous token — since the publish job runs only
  on a `v*` tag and nothing else exercises it before the release.
- R-ASP-4: The floor guard MUST read the major from the comment version when
  the ref is a SHA and hold it to `[tool.specgraph.action_major_floors]`. A
  comment whose major is below the action's floor, and a pinned action with no
  row in the table, MUST each fail the suite naming the file and line; the
  below-floor message MUST quote the comment version beside the SHA (`@<sha>
  # vX.Y.Z is below its floor vN`), never forty hex digits alone. No existing
  row MAY be lowered or removed. R-HCW-17's exemption stays true as written:
  a ref with no derivable major — a branch ref, or a SHA with no readable
  comment — is the shape guard's to name, and the floor guard MUST skip it
  rather than report it twice.
- R-ASP-5: All references to one action across the scan set MUST agree on
  both the SHA and the comment version. A disagreement in either MUST fail
  the suite naming every disagreeing file and line, and the message MUST end
  by naming the three files Dependabot does not watch —
  `templates/spec-gate.yml`, its copy under
  `skills/planlint-spec-governance/assets/` and `README.md` — and that the
  SHA and its `# vX.Y.Z` comment are carried there by hand. This carries
  R-HCW-2 forward onto the pair rather than the ref alone.
- R-ASP-6: The version comment MUST be read from the raw `uses:` line — the
  stripped text after its first `#`, or `None` when the line has no comment
  — not from the comment-stripped code the shared `_code_lines` helper
  yields. The shape pattern is applied by the offender helper, not the
  reader, so a malformed comment is named as malformed with the expected
  shape quoted, and a missing one as missing. A whole-line comment that
  mentions a `uses:` MUST still satisfy nothing and trip nothing.
- R-ASP-7: `templates/spec-gate.yml`, its byte-identical copy under
  `skills/planlint-spec-governance/assets/`, and `README.md`'s copyable
  workflow block MUST carry the same pins as the workflows. The template's
  comment block MUST say that the third-party pins are commit SHAs with the
  release tag in the comment, that a `github-actions` Dependabot entry in
  the adopter's repository moves SHA and comment together, and that in this
  repository the template is not watched and its pins are refreshed by hand;
  it MUST NOT claim that Dependabot keeps the template fresh for us.
- R-ASP-8: Every guard this spec adds or amends MUST live in
  `tests/test_workflow_hardening.py`, MUST read the files it judges rather
  than compare to a version string or a real action's SHA, MUST collect every
  offender before asserting, and MUST be shown red on a planted
  counter-example: a tag ref, a branch ref, a SHA with no comment, a
  malformed comment, a comment below the floor, uniformly retired comments
  across two files, and a comment disagreement behind one SHA. The one
  helper amended outside that module, `tests/test_ci_hardening.py`'s
  `_dependabot_directories`, changes only in which keys it reads (R-ASP-11).
  The shape guard MUST be written and run against the unpinned tree before
  the pins land, and the offenders it names there recorded in `tasks.md`.
- R-ASP-9: `.github/dependabot.yml`'s header, `docs/next-steps.md`'s deferred
  row and `CHANGELOG.md` MUST no longer describe SHA pinning as deferred, and
  the two records that attribute the deferral to `docs/distribution-plan.md`
  MUST name `docs/next-steps.md` instead. `docs/aqa.md`'s CI-pin example and
  `docs/hooks.md`'s floor paragraph MUST describe the pinned posture: a
  commit SHA, the release tag in a trailing comment, the floor read from the
  comment. `pyproject.toml`'s floor-table header comment MUST say the floor
  applies to the tag in a pin's comment, and its sentence about the
  publisher riding a branch MUST become the publisher's own floor rationale:
  a Docker-backed action whose floor of 1 is the baseline a future v2 clears.
- R-ASP-10: `CHANGELOG.md`'s `[Unreleased]` section MUST carry an entry for
  this change naming the pin format, the publisher's move from a branch ref
  to a tagged commit, the floor table's new row, the Dependabot
  consolidation, the corrected location of the deferral, and the
  supersession of C-HCW-3 and AC-HCW-24. The entry lands under
  `[Unreleased]`; `prepare-release-0-3-0` moves it.
- R-ASP-11: `.github/dependabot.yml`'s two `github-actions` entries MUST
  consolidate into one with `directories: ["/", "/.github/actions/planlint"]`,
  keeping the schedule, limit, labels, commit prefix and the `actions-minor`
  group, so one upstream release yields one grouped pull request that moves
  every copy under `.github/` together. Both readers of that file —
  `tests/test_workflow_hardening.py::_dependabot_entries` and
  `tests/test_ci_hardening.py::_dependabot_directories` — MUST read the
  plural `directories:` list as well as the singular `directory:` key, and a
  planted plural entry MUST be shown read. The `docker` entry is unchanged.
- R-ASP-12: This package MUST land before `write-down-policies` and before
  `prepare-release-0-3-0`, and its proposal and `tasks.md` MUST name the
  three shared edit sites and what the later package does at each:
  `release.yml`'s publisher step (the release package adds a `with:` block
  directly under the `uses:` line this package rewrites);
  `templates/spec-gate.yml`'s comment block above the own-action step and
  its byte copy (both packages edit it, and
  `test_skill_asset_matches_template` needs the copy re-synced after each);
  `CHANGELOG.md`'s `[Unreleased]` (this package adds a `Changed` entry,
  `write-down-policies` an `Added` entry, the release package moves the
  body). Every reference in this package to the first public tag MUST name
  it as the tag `prepare-release-0-3-0` numbers, never a literal version.
- C-ASP-1: This repository's own `ianshank/planlint/.github/actions/planlint@<sha>`
  ref in the template, the skill asset and the README MUST be untouched, as
  MUST `./.github/actions/planlint` in `ci.yml` and the guard's own-action
  exemption. `tests/test_adopter_urls.py` and `docs/distribution-plan.md` are
  not edited.
- C-ASP-2: `test_no_third_party_action_ref_is_a_commit_sha` is deleted, not
  renamed, and no other test cited by another package's spec MAY be renamed
  or removed. Every `pytest -k` selector in every spec under
  `openspec/changes/` MUST resolve after this change: `harden-ci-workflows`'
  AC-HCW-24 is re-pointed in this stack, and `prepare-release-0-3-0`'s
  AC-REL-12, which cites the deleted test, MUST be re-pointed in the commit
  that deletes it or before that package lands. No package on `main` is
  edited; `harden-ci-workflows` is amended because it is on this branch
  (DEC-ASP-007).
- C-ASP-3: No rule changes — `RULES`, the README's rules table and
  `tests/baseline_rules.json` are unchanged; no `make` target changes; no
  workflow job is renamed or removed; the composite action's inputs, outputs
  and defaults are unchanged apart from its two `uses:` lines; Dependabot's
  scope (the same two directories and the `docker` entry, no `pip`) and its
  `actions-minor` grouping are unchanged while its two `github-actions`
  entries become one; `tools/check_no_hardcoded_thresholds.py` is not
  edited and stays quiet on a pinned `uses:` line.
- C-ASP-4: No test in the suite MAY open a network connection. Tag
  resolution and the registry manifest check are recorded implementation
  steps, not suite assertions.
- C-ASP-5: No release, tag or version bump; `release.yml`'s job chain,
  permissions and `id-token: write` are unchanged. The publisher's PEP 740
  attestation behaviour is not claimed by this spec: the pinned commit is the
  `release/v1` head, so the action's behaviour is unchanged;
  `prepare-release-0-3-0` declares `attestations: true` under the pinned
  line, and the first `v*` tag (W1.5) is where it is observed.

---

## Decisions

- **DEC-ASP-001:** the pin is `@<40-hex> # vMAJOR.MINOR.PATCH` — the peeled
  commit, then one comment holding exactly the release tag that commit is the
  target of. The SHA is the pin; the comment is for the three readers a bare
  SHA defeats: the floor guard, which has no major to read from forty hex
  digits; Dependabot, which classifies a SHA-pinned action's update as major,
  minor or patch from that comment and rewrites it with the SHA — and writes
  it in exactly this shape, ` # vX.Y.Z`, so the guard requires what the bot
  produces; and a reviewer, who can check the pair with one `git ls-remote`
  line. The full tag rather than a bare major (`# v7`) because a major says
  nothing the floor table does not already say, while the exact tag names
  what the SHA is; every tag pinned here is three-part, so the one shape
  fits all seven. Rejected: pinning the tag with the SHA in the comment,
  which is backwards — GitHub resolves the ref, not the comment; a version
  in a separate `env:` map, which no guard or bot reads against the `uses:`
  line.
- **DEC-ASP-002:** `_uses_refs` reads the raw line, not `_code_lines`, and
  returns the comment as text, not as a verdict. R-HCW-15's rule that a
  comment satisfies nothing and trips nothing is right for every other guard
  in the module and is kept for every other guard; the pin comment is the one
  comment that *is* data, and it sits on the same line as the code it
  describes. So `_uses_refs` splits each raw line at its first `#`, matches
  `uses:` against the code half, and returns a fifth element: the stripped
  comment text, or `None` when the line has no comment; a whole-line comment
  has an empty code half and still counts for nothing. The `vMAJOR.MINOR.PATCH`
  pattern is applied by `_pin_offenders`, which classifies what it sees — a
  bare SHA with `None` "has no `# vX.Y.Z` release-tag comment"; a comment
  present but not matching is named as malformed, quoting the expected shape
  — so a reviewer reading the failure learns which of the two mistakes was
  made. Amended at review: the first draft had the reader apply the pattern
  and return `None` for both cases, which would have reported a typo in the
  comment as a missing comment. Rejected: a second pass over the raw file to
  pair comments with lines, which is the same read done twice.
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
  compares the (SHA, version) pair and names both. All three are planted and
  shown red: the bare SHA by
  `test_a_sha_pin_without_its_release_tag_comment_is_named`, the other two
  by the planted tests Milestone 1 names.
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
  by pattern, so a publisher bump stays its own pull request. What the pin
  does and does not fix, recorded at review: the action is a composite whose
  publishing step runs the Docker image
  `ghcr.io/pypa/gh-action-pypi-publish:<ref with / as ->`, so `@release/v1`
  pulled `:release-v1` and `@dc37677b…` pulls `:dc37677b…` — a registry tag
  that exists and carries the same manifest digest (`sha256:a68d05…`) as
  `:release-v1` today, while `:v1.14.2` resolves to a different digest. The
  SHA pin therefore fixes the shim that runs on the runner, and the payload
  still arrives through a registry tag named after the SHA; pinning the
  image by digest would mean forking or vendoring the action and is not this
  package. Because the publish job runs only on a `v*` tag, Milestone 2
  records one `HEAD` against the manifest URL for the pinned SHA's tag
  answering 200, so the first release does not discover a missing image.
  The attestation caveat is recorded, not claimed: the pinned commit is the
  branch head, so nothing the action does changes; `prepare-release-0-3-0`
  declares `attestations: true` directly under this line and the first `v*`
  tag (W1.5) is where it is observed.
- **DEC-ASP-006:** the template, its byte copy under `skills/` and the README
  snippet are pinned too. DEC-HCW-012 put them in the scan set so adopters
  are not handed what the workflows retire, and a floating `checkout` beside
  a SHA-pinned own-action is the inconsistency `docs/next-steps.md`'s row
  names. The cost is the one DEC-HCW-012 accepted, now larger: Dependabot
  watches none of the three, so a bump of `.github/` alone fails the
  agreement guard until the template, the asset and the README move too —
  the intended effect, and the guard's message now says so and names the
  three files. The template's comment tells the adopter that a
  `github-actions` Dependabot entry in *their* repository moves SHA and
  comment together, and says plainly that in this repository the template
  is refreshed by hand; the first draft's sentence that Dependabot keeps the
  pins fresh was true of the adopter and false of us, and is dropped. The
  own-action ref stays, owned elsewhere (C-ASP-1); the template's
  whole-line comment naming the first public tag's own-action `uses:` is
  inert to the guard.
- **DEC-ASP-007:** C-HCW-3 and AC-HCW-24 are superseded, and
  `harden-ci-workflows`' spec is amended in place — one sentence appended to
  C-HCW-3 ("Superseded by `pin-actions-by-sha`, which pins every third-party
  action to a commit"), one to R-HCW-17 ("`pin-actions-by-sha` applies the
  floor to the release tag in a pin's comment"), and AC-HCW-24 shorn of its
  no-SHA clause and re-pointed at `test_rule_set_matches_baseline` and
  `test_the_own_action_ref_is_exempt_from_the_sha_check`, the two of its
  three tests that remain true. The old guard
  `test_no_third_party_action_ref_is_a_commit_sha` is deleted; its
  replacements are `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  on the real tree and `test_a_sha_pin_without_its_release_tag_comment_is_named`
  on a planted one, names that say what they check. Amended at review: the
  first draft renamed the old test to a longer name carrying the old one as
  a substring so AC-HCW-24's selector would keep matching unedited — a test
  named to satisfy a citation guard rather than to describe its assertion,
  which is the drift this repository lints other repositories for. The
  reason the record is amended rather than left as written is where it is:
  the two supersessions on record — R-ZCG-13 leaving `gate-tools-coverage`'s
  stale count, DEC-ZCG-003 naming `post-merge-quality-review`'s reversed
  criterion — left packages that were already on `main`; `harden-ci-workflows`
  is on this same unmerged branch, so its record can still be made true
  before anyone reads it as history. `prepare-release-0-3-0` is on this
  branch too and its AC-REL-12 cites the deleted test; this draft does not
  edit that package, and the re-point is a named step in the deleting commit
  (C-ASP-2, DEC-ASP-012).
- **DEC-ASP-008:** the floor stays a *major floor* and is applied to the
  comment. DEC-HCW-014's argument is unchanged by the pin: a floor ratchets,
  a bump never edits it, and it is the invariant the agreement guard lacks —
  every copy sliding back together is still agreement. What changes is where
  the major comes from: `_major(ref)` for a tag ref (which the shape guard
  already names, so the floor guard only meets one on a planted tree), and
  `_major(comment)` for a SHA. A ref with no derivable major — a branch ref,
  a bare SHA, a SHA whose comment does not parse — is skipped by the floor
  guard, because the shape guard already names it and R-HCW-17's "a branch
  ref has no major and is outside this rule" stays true as written; the
  first draft expected the floor guard to go red on the unpinned tree as
  well, which would have reported the publisher's branch ref twice and made
  the exemption false. The below-floor message quotes the comment version
  beside the SHA so a reader sees `v4.2.2`, not forty hex digits. Rejected:
  a per-action pinned version in `pyproject.toml`, which is the second copy
  of the pin DEC-HCW-008 rejected.
- **DEC-ASP-009:** `.github/dependabot.yml`'s two `github-actions` entries
  become one with a `directories:` list, and nothing else about its scope or
  grouping moves. Two entries meant one upstream release produced two pull
  requests, one per directory, each moving its own copy of an action and
  each red on the agreement guard until the other merged — tolerable under
  major tags, where that happened once a year per action, and not under
  patch-level pins, where it happens on every patch release. One entry with
  both directories and the `actions-minor` group yields one grouped pull
  request that moves every copy under `.github/` together, so the guard is
  satisfiable for that directory on its own. The cost that remains is
  stated, not hidden: every patch release of every pinned action now opens a
  pull request (under `@v7` only a major did), and each is red on the
  agreement guard until the SHA and comment are hand-carried into the
  template, the skill copy and the README — which the guard's message now
  says. Both readers of the file learn the plural key, because a config the
  tests cannot read is a config the tests silently stop checking. No
  `ignore:`; no entry for `templates/` or `README.md`, because the
  `github-actions` ecosystem reads neither.
- **DEC-ASP-010:** the deferral records close in place rather than being
  deleted, and the mis-pointer is corrected while they are open.
  `docs/next-steps.md`'s row stays in the deferred table with its second
  cell rewritten as the closing — this package, the guard, and the comment
  the floor reads — so the trail from deferral to closure is readable; the
  Dependabot header's paragraph is rewritten the same way and now names
  `docs/next-steps.md` as where the row lives, since `docs/distribution-plan.md`
  never held it; the CHANGELOG's historical Dependabot entry is a dated
  record and stays, and the new `[Unreleased]` entry says it closed and
  where the row actually was.
- **DEC-ASP-011:** the guard is written first and run red against the
  unpinned tree, then the pins land, and the two go into one commit. A guard
  written after the pins is never seen to fail against the tree it was
  written for; the red run — naming every tag ref in the scan set and the
  publisher's branch ref — is the proof it reads the real files. It is
  recorded in `tasks.md` with the offender list and never committed as a
  tree state: a commit whose suite is red by design is a commit the gate
  ladder cannot bisect past. The records and docs follow in a second commit,
  then the full ladder.
- **DEC-ASP-012:** this package lands first of M1's three, then
  `write-down-policies`, then `prepare-release-0-3-0`. The release package
  moves the CHANGELOG's `[Unreleased]` body under the release heading and
  must see every sibling's entry before it does; this package's edits are
  the ones the others build on. The shared edit sites are named so each
  merge is prepared rather than discovered: `release.yml`'s publisher step,
  where this package rewrites the `uses:` line and the release package adds
  `with: attestations: true` directly beneath it; `templates/spec-gate.yml`'s
  comment block above the own-action step and its byte copy, where this
  package adds the pin sentences and the release package renames the tag,
  with `test_skill_asset_matches_template` needing the copy re-synced after
  each; `CHANGELOG.md`'s `[Unreleased]`, where this package adds a `Changed`
  entry, `write-down-policies` an `Added` one, and the release package moves
  all of it. Because the release package numbers the first public tag, this
  package never writes that number: every mention is "the first public tag,
  numbered by `prepare-release-0-3-0`". The release package's AC-REL-12
  cites the test this package deletes, so that selector is re-pointed in the
  deleting commit — the one edit this package makes to a sibling, recorded
  in `tasks.md` rather than performed by this draft.
- **DEC-ASP-013:** `github/codeql-action` has no refresh path in this
  repository under a SHA pin, and that is accepted in writing. It appears
  only in the template and the skill copy, which Dependabot does not read,
  so no bot will ever propose moving its pin; under `@v3` the major tag
  moved itself. The pin is refreshed by hand whenever the template is next
  edited, the template's comment says so, and the agreement guard holds the
  two copies equal in the meantime. Rejected: leaving `codeql-action` on its
  major tag as the one floating ref, which hands adopters a template whose
  two third-party steps follow two different rules; adding a Dependabot
  entry for `templates/`, which the `github-actions` ecosystem cannot read.

---

## Acceptance Criteria

- [ ] **AC-ASP-1:** every third-party `uses:` under `.github/workflows/`,
  `.github/actions/*/action.yml`, `templates/` and in `README.md`'s workflow
  snippet is `@<40-hex> # vMAJOR.MINOR.PATCH`, no tag ref or branch ref
  remains in the scan set, and the scan constant holds the composite-action
  glob. (R-ASP-1, R-ASP-3)
  _Verified by:_ stage: `make test`

- [ ] **AC-ASP-2 (non-success):** a planted tag ref (`@v7`), a planted branch
  ref (`@release/v1`), a planted SHA with no comment, and a planted SHA whose
  comment is not a release tag (`# v7`, `# 7.0.1`) each fail the suite with
  a message naming the file and line — the bare SHA as having no release-tag
  comment, the malformed one as malformed with the expected shape quoted; a
  whole-line comment mentioning a `uses:` is not reported; and the comment
  text is read from the raw line while the comment-stripped code carries
  none. (R-ASP-1, R-ASP-6, R-ASP-8)
  _Verified by:_ stage: `make test`

- [ ] **AC-ASP-3:** every pinned third-party action's comment names a major
  at or above its row in `[tool.specgraph.action_major_floors]`, and every
  pinned action — the publisher included — has a row. (R-ASP-3, R-ASP-4)
  _Verified by:_ `pytest -k test_every_third_party_action_meets_its_major_floor` · stage: `make test`

- [ ] **AC-ASP-4 (non-success):** two files agreeing on one synthetic SHA
  with a comment below the floor pass the agreement guard and fail the floor
  guard with both files and lines named and the comment version quoted in
  the message; a pinned action missing from the table is named; a branch ref
  and a bare SHA are not reported by the floor guard. (R-ASP-4, R-ASP-8)
  _Verified by:_ `pytest -k "test_a_uniformly_retired_major_is_named_with_file_and_line or test_an_action_without_a_floor_is_named"` · stage: `make test`

- [ ] **AC-ASP-5:** every reference to one action across the scan set carries
  the same SHA and the same comment, and the template under `skills/` is
  byte-identical to `templates/spec-gate.yml` after the pins. (R-ASP-5,
  R-ASP-7)
  _Verified by:_ `pytest -k "test_every_reference_to_one_action_agrees_on_one_ref or test_skill_asset_matches_template"` · stage: `make test`

- [ ] **AC-ASP-6 (non-success):** two copies of one action on different SHAs
  fail naming each file and line with the message ending in the three
  unwatched files and the hand-carry instruction, and two copies on the same
  SHA with different comments fail the same way. (R-ASP-5, R-ASP-8)
  _Verified by:_ `pytest -k test_a_leftover_retired_major_is_reported_with_file_and_line` for the SHA half and the message tail, the comment half by stage until its test exists · stage: `make test`

- [ ] **AC-ASP-7:** this repository's own action ref is exempt: a planted
  own-action SHA with no comment and a planted `./` local action are not
  reported while a third-party SHA with no comment on the next line is; and
  the template still pins the own action to the SHA the adopter-URL test
  requires. (C-ASP-1)
  _Verified by:_ `pytest -k "test_the_own_action_ref_is_exempt_from_the_sha_check or test_ci_template_pins_the_floor_the_skill_enforces"` · stage: `make test`

- [ ] **AC-ASP-8:** `release.yml`'s publisher is the peeled commit of its
  newest release tag with that tag in the comment, `release/v1` appears
  nowhere in the scan set, and the `gate → build → publish` chain, its
  permissions and `id-token: write` are unchanged — the release test asserts
  the publisher is present and the chain intact, and the shape guard holds
  the ref. (R-ASP-3, C-ASP-5)
  _Verified by:_ `pytest -k test_release_workflow_is_gated_and_uses_trusted_publishing`, with the `release/v1` search over the scan set recorded in `tasks.md` · stage: `make test`

- [ ] **AC-ASP-9:** `tasks.md` records, for every third-party action, the
  `git ls-remote --tags` line the pin was taken from — the `^{}` line for an
  annotated tag — and the SHA in the tree equals it; it records the `HEAD`
  against the GHCR manifest URL for the publisher's pinned SHA answering 200
  under an anonymous token; and the first CI run on the branch after the
  pins shows each action downloaded at its pinned SHA, with the run number
  recorded. (R-ASP-2, R-ASP-3, C-ASP-4)
  _Verified by:_ the recorded `ls-remote` lines against the tree, the recorded manifest check, and the run's job log · stage: `make pre-pr`

- [ ] **AC-ASP-10:** the composite action's inputs, outputs and defaults are
  unchanged and it still declares no token input and no `permissions:`; its
  only diff is two `uses:` lines. (C-ASP-3)
  _Verified by:_ `pytest -k "test_the_action_declares_exactly_the_v1_inputs or test_the_action_needs_no_token_and_no_privileged_permission"` · stage: `make test`

- [ ] **AC-ASP-11:** the rule set is unchanged; `.github/dependabot.yml` has
  one `github-actions` entry whose `directories:` list covers `/` and every
  composite-action directory, carrying the `actions-minor` group; the
  `docker` entry still watches `/`; and there is still no `pip` ecosystem.
  (C-ASP-3, R-ASP-11)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_every_composite_action_directory_is_watched_by_dependabot or test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry or test_dependabot_does_not_add_a_pip_ecosystem"` · stage: `make test`

- [ ] **AC-ASP-12:** every `pytest -k` selector in every spec under
  `openspec/changes/` resolves to a test function after this change — the
  re-pointed AC-HCW-24 and AC-REL-12 included — and
  `harden-ci-workflows`' spec carries the three amendments DEC-ASP-007
  names, read directly. (C-ASP-2, DEC-ASP-007)
  _Verified by:_ `pytest -k test_every_spec_test_citation_resolves_to_a_real_test` · stage: `make test`

- [ ] **AC-ASP-13:** the Dependabot header, the `docs/next-steps.md` row and
  the CHANGELOG no longer describe SHA pinning as deferred and no record
  attributes the deferral to `docs/distribution-plan.md`; `docs/aqa.md`,
  `docs/hooks.md` and the floor table's header comment describe the pinned
  posture; the template's comment makes no claim that Dependabot refreshes
  it for this repository; the required documents still exist and are
  linked. No automated guard asserts the prose; it is read directly.
  (R-ASP-7, R-ASP-9, R-ASP-10)
  _Verified by:_ stage: `make docs-check`

- [ ] **AC-ASP-14 (non-success):** the pin-shape guard, run against the tree
  before the pins land, fails naming every floating tag ref in the scan set
  and the publisher's branch ref, each with file and line; the floor guard
  does not report the branch ref; the offender list is recorded in
  `tasks.md` and the red tree is never committed. (R-ASP-8, DEC-ASP-011)
  _Verified by:_ the recorded red run · stage: `make test`

- [ ] **AC-ASP-15:** no workflow job is renamed or removed; `docs/hooks.md`'s
  CI table still lists every `ci.yml` job. (C-ASP-3)
  _Verified by:_ `pytest -k test_hooks_ci_table_lists_every_ci_job` · stage: `make test`

- [ ] **AC-ASP-16:** `tools/check_no_hardcoded_thresholds.py` is unedited and
  reports PASS on the finished tree, with a planted pinned `uses:` line and
  its version comment yielding no finding from `check_workflow`. (C-ASP-3)
  _Verified by:_ the guard's PASS line on the finished tree, with the script absent from the diff · stage: `make thresholds`

- [ ] **AC-ASP-17 (non-success):** a planted Dependabot config whose
  `github-actions` entry uses the plural `directories:` list is read by
  `_dependabot_entries` as one pair per directory, and a planted config
  whose list omits a composite-action directory is named by the
  directory-watch guard's helper. (R-ASP-11, R-ASP-8)
  _Verified by:_ stage: `make test`

- [ ] **AC-ASP-18:** the package is merged before `write-down-policies` and
  `prepare-release-0-3-0`; after each later sibling lands, the template and
  its skill copy are byte-identical again and the whole tree validates
  clean. (R-ASP-12, DEC-ASP-012)
  _Verified by:_ `pytest -k test_skill_asset_matches_template` after each sibling lands, and the tree gate's exit code recorded in `tasks.md` · stage: `make validate`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-ASP-1..8, 10..12, 14, 15, 17 — every pin-shape, floor, agreement and Dependabot-reader guard green on the real tree and red on its planted counter-example; every spec citation resolves |
| Threshold guard | `make thresholds` | AC-ASP-16 — the guard is unedited and prints PASS with the pinned lines in place |
| Docs | `make docs-check` | AC-ASP-13 — the deferral records closed and correctly pointed, the posture prose updated, the document set intact |
| Self-check | `make validate` | AC-ASP-18 — this package validates clean against the repo's own rules, then the whole tree, after this package and after each sibling |
| Full | `make pre-pr` | AC-ASP-9 as the local equivalent of the observed run; full regression, lint, typecheck, security, docs, thresholds, scoped coverage |
