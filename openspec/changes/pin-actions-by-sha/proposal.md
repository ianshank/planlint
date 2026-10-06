# Change: Pin Every Third-Party Action to a Commit SHA, With Its Release Tag in a Trailing Comment

## Why

Milestone M0 (`harden-ci-workflows`) moved every third-party action this
repository runs onto a Node 24 major and put a floor under each one, and left
every ref a floating tag on purpose: `actions/checkout@v7`,
`actions/setup-python@v7`, `actions/upload-artifact@v7`,
`actions/download-artifact@v8`, `gitleaks/gitleaks-action@v3` and
`github/codeql-action/upload-sarif@v3`, plus
`pypa/gh-action-pypi-publish@release/v1` — a *branch* ref on the one action
that holds write access to a package index. A major tag is a ref the action's
maintainers move on every release, and anyone with push access to that
repository can move it anywhere; GitHub resolves it at run time, so what ran
on one green build is not what will run on the next. The repository already
tells its adopters to pin exactly — the README's snippet and the template pin
this repository's own action to a 40-hex SHA — while handing them
`actions/checkout@v7` on the line above.

Three records in this tree say SHA pinning is deferred "until the pins can be
resolved and verified": the deferred row in `docs/next-steps.md`, and the
header of `.github/dependabot.yml` and the CHANGELOG's Dependabot entry, both
of which send the reader to `docs/distribution-plan.md` for that row — a file
that owns the own-action SHA's switch to the first public tag and holds no
third-party deferral at all. The precondition is met on its own terms. The
pins are resolved below, from each repository's own refs advertisement;
Dependabot — the thing the deferral named as the prerequisite — watches both
action directories and rewrites a SHA pin and its version comment together;
and M0's per-action floor gives a pinned SHA the one invariant it otherwise
lacks, provided the version it pins is written where the floor guard can read
it. That is why the pin format carries the release tag in a trailing comment:
the SHA is the pin, the comment is what the floor, Dependabot and a reviewer
read.

M0's guard forbids exactly this: `C-HCW-3` says no third-party ref may become
a commit SHA and names SHA pinning as a separate package; `AC-HCW-24` asserts
it. This is that package, and it supersedes both. `harden-ci-workflows` is on
this same unmerged branch, so its record is amended in place — one sentence
each on C-HCW-3 and R-HCW-17, and AC-HCW-24 re-pointed at the tests that
remain true — rather than left as written. The two supersessions this
repository has on record went the other way for a reason that does not hold
here: `select-zero-cost-guards`' R-ZCG-13 left `gate-tools-coverage`'s stale
count as it was and its DEC-ZCG-003 named `post-merge-quality-review`'s
reversed criterion without editing it, because both of those packages were on
`main` when they were superseded. It is item W1.2 of milestone M1 of the
October 2026 reflection plan; the plan is on its own branch and not in this
tree at drafting time, so its item is restated here and every fact below is
re-measured against this tree.

This package lands first of M1's three, ahead of `write-down-policies` and
then `prepare-release-0-3-0`, which moves the CHANGELOG's `[Unreleased]`
body under the release heading and must come last. The three touch the same
lines in three files, and the order is what keeps each merge clean
(DEC-ASP-012).

**Evidence:** measured at `5fe043e` on branch `claude/m1-pin-and-release`,
the tree M0 landed on; `write-down-policies`' draft has since landed on the
branch as `openspec/` only, moving nothing below. A sibling package landing
first may move a line number without moving the fact.

- **Every third-party ref floats.** `grep -n uses:` over the scan set:
  `.github/workflows/ci.yml` carries `actions/checkout@v7` at lines 45, 78,
  111, 132, 173, 202, 282, 360, 398, 410; `actions/setup-python@v7` at 47,
  80, 113, 134, 175, 207, 364, 399, 411; `actions/upload-artifact@v7` at 156,
  230; `gitleaks/gitleaks-action@v3` at 377. `.github/workflows/release.yml`:
  checkout at 34, 56; setup-python at 38, 58; upload-artifact at 94;
  `actions/download-artifact@v8` at 112; `pypa/gh-action-pypi-publish@release/v1`
  at 117. `.github/actions/planlint/action.yml`: setup-python at 163,
  upload-artifact at 337. `templates/spec-gate.yml`: checkout at 52,
  `github/codeql-action/upload-sarif@v3` at 82; its byte copy
  `skills/planlint-spec-governance/assets/spec-gate.yml` is identical
  (`cmp` reports no difference; `tests/test_skill_contract.py::test_skill_asset_matches_template`
  holds it so). `README.md`'s copyable workflow block: checkout at 400. The
  only SHA-pinned `uses:` lines are this repository's own action —
  `templates/spec-gate.yml` line 65, `README.md` lines 403 and 451 — which
  `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
  requires until the first public tag, numbered by `prepare-release-0-3-0`,
  exists.
- **The guard forbids a SHA today, and would go blind on one.**
  `tests/test_workflow_hardening.py`: `ACTION_REF_SCAN` (line 40) is the
  workflows, `ACTION_YML` (line 27 — the single path
  `.github/actions/planlint/action.yml`, not the `.github/actions/*/action.yml`
  glob R-HCW-1 names), `templates/*.yml` and the README;
  `OWN_ACTION_PREFIX = "ianshank/planlint/"` (line 46) is skipped by
  `_uses_refs` (line 113) along with `./` local actions. `_code_lines`
  (line 70) returns each line with everything after `#` removed, so a
  trailing version comment is invisible to every helper built on it —
  `_uses_refs` included. `_major` (line 149) matches `^v(\d+)(?:\.\d+)*$`
  and returns `None` for a SHA; `_floor_offenders` (line 161) `continue`s on
  `None`, so once every ref is a SHA
  `test_every_third_party_action_meets_its_major_floor` (line 536) passes
  having checked nothing. `_sha_refs` (line 185) and
  `test_no_third_party_action_ref_is_a_commit_sha` (line 572) assert no
  third-party ref is a 40-hex SHA; `test_the_own_action_ref_is_exempt_from_the_sha_check`
  (line 578) shows the own-action exemption. `_ref_disagreements` (line 134)
  compares refs only. `pyproject.toml` lines 181–187,
  `[tool.specgraph.action_major_floors]`: checkout 7, setup-python 7,
  upload-artifact 7, download-artifact 8, gitleaks-action 3, codeql-action 3
  — no entry for `pypa/gh-action-pypi-publish`, which R-HCW-17 excluded as
  "a branch ref [that] has no major"; the table's header comment (lines
  170–180) says so in its last two lines.
- **What M0 said this package would be, and who repeats it.**
  `openspec/changes/harden-ci-workflows/specs/ci-workflow-hardening/spec.md`:
  C-HCW-3 "No third-party action ref MAY become a commit SHA, and
  `pypa/gh-action-pypi-publish@release/v1` MUST be untouched. SHA pinning is
  a separate package"; AC-HCW-24 cited
  `test_no_third_party_action_ref_is_a_commit_sha` and
  `test_the_own_action_ref_is_exempt_from_the_sha_check`; R-HCW-2 (one ref
  per action across the scan set) and R-HCW-17 / DEC-HCW-014 (the floor, "a
  ratchet a bump never edits") are the two invariants this package keeps
  meaningful; DEC-HCW-012 puts the templates and the README in the scan and
  accepts that Dependabot watches neither; DEC-HCW-014's last sentence:
  "`pypa/gh-action-pypi-publish@release/v1` has no major; W1.2 moves it with
  the SHA pins." `prepare-release-0-3-0`'s spec restates the constraint as
  C-REL-4 ("SHA pinning is W1.2's package") and its AC-REL-12 cites the same
  `test_no_third_party_action_ref_is_a_commit_sha`.
- **The pins, resolved.** Each repository's refs advertisement, fetched over
  HTTPS on 2026-10-06 — the same data `git ls-remote --tags
  https://github.com/<owner>/<repo>` prints, and the command the
  implementation re-runs:
  `actions/checkout` `v7` = `3d3c42e5aac5ba805825da76410c181273ba90b1` =
  `v7.0.1`; `actions/setup-python` `v7` =
  `5fda3b95a4ea91299a34e894583c3862153e4b97` = `v7.0.0`;
  `actions/upload-artifact` `v7` = `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
  = `v7.0.1`; `actions/download-artifact` `v8` =
  `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` = `v8.0.1`;
  `gitleaks/gitleaks-action` `v3` = `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e`
  = `v3.0.0`. Two are **annotated** tags, where the advertised SHA is a tag
  object and the `^{}` line is the commit a `uses:` must name:
  `github/codeql-action` `v3` is tag object `87ef0dc9…` peeling to
  `1190a975f95ce23525efb6a3fc21ea29567c1b52`, which is also `v3.38.2^{}`;
  `pypa/gh-action-pypi-publish` `v1.14.2` (newest by version sort) is tag
  object `a892a5a6…` peeling to `dc37677b2e1c63e2034f94d8a5b11f265b73ba33`,
  which is also the `release/v1` branch head at drafting. Every release tag
  named here is three-part, so one comment shape fits all seven.
- **The publisher's payload is a Docker image named after the ref.**
  `pypa/gh-action-pypi-publish` is a composite action whose publishing step
  runs the image `ghcr.io/pypa/gh-action-pypi-publish:<ref>` with the ref's
  `/` written as `-`, so `@release/v1` pulls `:release-v1` and
  `@dc37677b…` pulls `:dc37677b…`. Checked at review: the `:dc37677b…` tag
  exists and carries the same manifest digest (`sha256:a68d05…`) as
  `:release-v1` today, while `:v1.14.2` resolves to a different digest. A
  SHA pin therefore fixes the shim that runs on the runner; the payload still
  arrives through a registry tag that happens to be named after the SHA.
- **Dependabot is the prerequisite, and is in place — in two entries.**
  `.github/dependabot.yml` lines 16–22 record the deferral and name an update
  bot as "the prerequisite for closing that item, not a substitute for it".
  Its two `github-actions` entries — `/` (lines 26–50) and
  `/.github/actions/planlint` (lines 52–61) — carry the same weekly schedule,
  limit, labels and `ci` commit prefix; only the first carries the
  `actions-minor` group (lines 40–50), which collects `actions/*` minor and
  patch updates and leaves `pypa/gh-action-pypi-publish` on its own pull
  request. Two entries means one upstream release produces two pull
  requests, one per directory, each of which moves its own copy of an action
  and fails R-HCW-2's agreement guard until the other merges. Dependabot
  writes a SHA pin's version as a trailing ` # vX.Y.Z` comment
  (dependabot-core, `version_commenter.rb`). It watches neither `templates/`
  nor `README.md`, so a bump there is carried by hand — which the agreement
  guard enforces, and DEC-HCW-012 calls the intended effect.
  `tests/test_workflow_hardening.py::_dependabot_entries` (line 456) and
  `tests/test_ci_hardening.py::_dependabot_directories` (line 834, the regex
  `^\s*directory:\s*"([^"]+)"` at line 842, feeding
  `test_every_composite_action_directory_is_watched_by_dependabot`) both read
  the singular `directory:` key only.
- **The records that close, and where they point.** `docs/next-steps.md`
  line 227 is the deferred row "SHA-pinning the third-party actions inside
  `action.yml`", reopened when "the pins can be resolved and verified";
  `.github/dependabot.yml` line 19 and `CHANGELOG.md` line 339 ("Added —
  Dependabot") both attribute that deferral to `docs/distribution-plan.md`,
  whose only SHA sentences (lines 15, 132) are about this repository's own
  action ref; `docs/aqa.md` line 40 gives `actions/checkout@v7` as the
  example of a CI pin outside the thresholds gate; `docs/hooks.md` lines
  66–70 describe the floor posture in terms of major tags.
- **What deleting the old test touches.** `tests/test_spec_test_citations.py`
  resolves every `pytest -k` selector in every file matching
  `openspec/changes/*/specs/*/spec.md` by substring over the test function
  names under `tests/`, read from the AST. `test_no_third_party_action_ref_is_a_commit_sha`
  is cited on two verification lines in that glob: `harden-ci-workflows`'
  AC-HCW-24 (re-pointed in this stack) and `prepare-release-0-3-0`'s
  AC-REL-12 (spec line 438), which must be re-pointed before that package
  lands. `harden-ci-workflows/tasks.md` line 52 lists the name as a record
  of what shipped; `tasks.md` is outside the citation guard's glob.
- **What the release test pins, and does not.**
  `tests/test_agent_artifacts.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
  (line 491) asserts the `gate → build → publish` chain, `make pre-pr` in
  `gate`, the clean-venv smoke test and `id-token: write` on `publish`, over
  the job blocks with comments stripped; it asserts only that the publisher
  appears, not its ref, so the pin changes nothing it checks.
  `prepare-release-0-3-0` adds `with: attestations: true` directly under the
  publisher's `uses:` line this package rewrites.
- **The thresholds guard is quiet on a pin.**
  `tools/check_no_hardcoded_thresholds.py::check_workflow` (lines 92–104)
  matches a line only on `--cov-fail-under`/`fail[-_]under` followed by a
  digit, or `ruff==`/`mypy==`/`pytest==`; a SHA-pinned `uses:` line with a
  `# vX.Y.Z` comment matches neither.

## What Changes

- `tests/test_workflow_hardening.py`: `ACTION_YML` becomes the sorted glob
  `.github/actions/*/action.yml`, so a second composite action is inside the
  scan without an edit. `_uses_refs` reads each `uses:` line raw — the code
  half for the action and ref, the comment half as data — and returns a fifth
  element, the stripped comment text after the first `#`, or `None` when the
  line has no comment. A `_pin_offenders(paths)` helper applies the
  `vMAJOR.MINOR.PATCH` pattern and classifies: a ref that is not a 40-hex
  SHA; a SHA whose comment is `None` ("has no `# vX.Y.Z` release-tag
  comment"); a comment present but malformed, named as malformed with the
  expected shape quoted. `_ref_disagreements` compares the (SHA, comment)
  pair and its message ends by naming the three unwatched files and that the
  SHA and comment are carried there by hand; `_floor_offenders` reads the
  major from the comment when the ref is a SHA, with the message quoting the
  comment version and never the bare SHA, and `continue`s on any ref with no
  derivable major — the shape guard's business, not the floor's.
  `test_no_third_party_action_ref_is_a_commit_sha` and `_sha_refs` are
  deleted. New guards:
  `test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag`
  on the real tree and
  `test_a_sha_pin_without_its_release_tag_comment_is_named` on a planted
  one, plus planted counter-examples for a tag ref, a branch ref, a malformed
  comment, a comment below the floor, uniformly retired comments across two
  files, a comment disagreement behind one SHA, the raw-line read, the
  thresholds guard's silence on a pinned line, and a Dependabot entry read
  through the plural `directories:` key. `test_the_own_action_ref_is_exempt_from_the_sha_check`,
  `test_every_third_party_action_meets_its_major_floor`,
  `test_a_uniformly_retired_major_is_named_with_file_and_line`,
  `test_an_action_without_a_floor_is_named` and
  `test_a_leftover_retired_major_is_reported_with_file_and_line` keep their
  names with their planted text moved to the pinned shape. `_dependabot_entries`
  reads `directories:` as well as `directory:`. Every message names file and
  line.
- `tests/test_ci_hardening.py`: `_dependabot_directories` reads the plural
  `directories:` list as well as the singular key, so
  `test_every_composite_action_directory_is_watched_by_dependabot` keeps
  reading the real file after the entries consolidate. Nothing else in the
  module changes.
- `pyproject.toml`: `[tool.specgraph.action_major_floors]` gains
  `"pypa/gh-action-pypi-publish" = 1`, because the action now carries a
  version the floor guard reads and a pinned action with no floor is an
  offender. The table's header comment is rewritten: the floor applies to
  the release tag in a pin's comment, and its last two lines — the publisher
  "rides a branch ref" and "has no major to floor" — become the publisher's
  own rationale: a Docker-backed action whose floor of 1 is the baseline a
  future v2 would have to clear. No existing row moves.
- `.github/workflows/ci.yml`, `.github/workflows/release.yml`,
  `.github/actions/planlint/action.yml`: every third-party `uses:` becomes
  `@<40-hex> # vX.Y.Z`, the SHA being the peeled commit of the tag the
  comment names, in one batch; `release.yml`'s publisher becomes the
  `v1.14.2` commit with `# v1.14.2`. Nothing else in any of the three files
  changes.
- `templates/spec-gate.yml` and its byte copy
  `skills/planlint-spec-governance/assets/spec-gate.yml`: `actions/checkout`
  and `github/codeql-action/upload-sarif` pinned the same way; the comment
  block above the own-action step gains sentences saying what the pins are,
  that a `github-actions` Dependabot entry in the adopter's repository moves
  SHA and comment together, and that in this repository the template is not
  watched and is refreshed by hand — it no longer claims Dependabot keeps it
  fresh for us. `README.md`'s workflow block: its `actions/checkout` line
  pinned the same way. The `ianshank/planlint/.github/actions/planlint@a1b686…`
  lines in all three are untouched.
- `.github/dependabot.yml`: the two `github-actions` entries consolidate into
  one with `directories: ["/", "/.github/actions/planlint"]`, keeping the
  schedule, limit, labels, `ci` commit prefix and the `actions-minor` group,
  so one upstream release produces one grouped pull request that moves every
  copy under `.github/` together and satisfies the agreement guard for that
  directory on its own. The header's deferral paragraph is rewritten to
  record that the pins are resolved, how the comment is what Dependabot and
  the floor read, and the correct location of the deferred row
  (`docs/next-steps.md`). The `docker` entry is unchanged.
- The cost of patch-level pins, stated: a major tag moves only when a major
  ships, so under `@v7` Dependabot opened a pull request only for a major;
  under a patch-level SHA pin every patch release of every pinned action
  opens one. The template, its skill copy and the README are not watched, so
  each such pull request is red on the agreement guard until the pin is
  hand-carried into those three files. `github/codeql-action` lives only in
  the template and the skill copy, so under a SHA pin it has no refresh path
  in this repository at all: that is accepted in writing (DEC-ASP-013) and
  the pin is refreshed by hand when the template changes.
- `docs/next-steps.md`: the deferred row records its closing by this package
  and the guard that holds it, rather than a reopen condition.
- `docs/aqa.md`: the `actions/checkout@v7` example becomes a description of
  the pinned shape; `docs/hooks.md`: the floor paragraph says every
  third-party action is pinned to a commit SHA with its release tag in a
  trailing comment, and that the floor reads the comment.
- `CHANGELOG.md` `[Unreleased]`: a `Changed` entry for this package naming the
  pin format, the publisher's move from a branch to a tagged commit, the
  floor table's new row, the Dependabot consolidation, and the supersession
  of C-HCW-3 and AC-HCW-24; the entry also corrects where the deferral was
  recorded. `prepare-release-0-3-0` moves it under the release heading when
  it lands.
- `openspec/changes/harden-ci-workflows/specs/ci-workflow-hardening/spec.md`:
  amended in this stack with this draft — C-HCW-3 gains "Superseded by
  `pin-actions-by-sha`, which pins every third-party action to a commit";
  R-HCW-17 gains "`pin-actions-by-sha` applies the floor to the release tag
  in a pin's comment"; AC-HCW-24 drops its no-SHA clause and cites
  `test_rule_set_matches_baseline` and
  `test_the_own_action_ref_is_exempt_from_the_sha_check`.
- `openspec/changes/prepare-release-0-3-0/specs/release-readiness/spec.md`:
  not edited by this draft. Its AC-REL-12 cites the test this package
  deletes, so its selector must be re-pointed — at the deleting commit, or
  before that package lands — to the pinned-tree guard and the floor guard;
  C-REL-4 is that package's own statement to amend. Named here so it is a
  sequencing step, not a surprise (DEC-ASP-012).
- `openspec/changes/pin-actions-by-sha/tasks.md`: the `git ls-remote --tags`
  output for every action, including the peeled line of each annotated tag,
  the GHCR manifest check for the publisher's image tag, and the red run of
  the shape guard on the unpinned tree, recorded at implementation beside
  the drafting values above.

## Non-Goals

- **No change to this repository's own action ref.** The
  `ianshank/planlint/.github/actions/planlint@a1b686…` lines in the template,
  the skill asset and the README stay exactly as they are, as does
  `./.github/actions/planlint` in `ci.yml`. The own ref is a SHA already,
  belongs to `test_ci_template_pins_the_floor_the_skill_enforces` and
  `docs/distribution-plan.md`, and moves to the first public tag, numbered
  by `prepare-release-0-3-0`, at the release (W1.5), not here. The guard's
  `OWN_ACTION_PREFIX` exemption stays.
- **No release (W1.5).** No tag, no version bump, no change to
  `release.yml`'s jobs, `needs:` chain, permissions or `id-token: write`.
  The publisher's new commit is the one `release/v1` already points at, so
  what the action does — including the PEP 740 attestations it generates by
  default under trusted publishing — is unchanged by this package and is not
  claimed by it; `prepare-release-0-3-0` declares `attestations: true` under
  the pinned line, and the first `v*` tag is where that is observed.
- **No change to the publisher's payload path.** The SHA pin fixes the
  composite shim; the Docker image it runs still arrives through a GHCR tag
  named after the ref. Pinning that image by digest would mean forking or
  vendoring the action, and is not this package. The fact is recorded in
  DEC-ASP-005 and the manifest's existence is checked at implementation,
  because nothing short of a `v*` tag exercises the publish job.
- **No network in the test suite.** The guard checks shape, floor and
  agreement offline. That a SHA is the commit its comment names is resolved
  by `git ls-remote` at implementation, and that the publisher's image tag
  exists by one `HEAD` against GHCR, both recorded in `tasks.md`; a test
  that fetched refs would be red on a sandboxed runner and on a fork pull
  request with no token, for a reason unrelated to the tree.
- **No pinned version in any test, and no SHA of a real action in any
  test.** Planted counter-examples use synthetic SHAs; a test that said
  `3d3c42e…` would be a second copy of the pin that the next Dependabot bump
  has to edit — DEC-HCW-008's objection, which still holds.
- **No change to Dependabot's scope or grouping.** The ecosystems stay
  `github-actions` and `docker` with no `pip`; no `ignore:`; the
  `actions-minor` group keeps its patterns and update types; no entry for
  `templates/` or `README.md` (Dependabot's `github-actions` ecosystem does
  not read either). What changes is the number of `github-actions` entries —
  two become one with a `directories:` list — so the scope is the same two
  directories watched as one. The hand-carried bump for the unwatched files
  is the cost DEC-HCW-012 accepted and the agreement guard enforces, now
  named in the guard's own message.
- **No edit to any package that is on `main`.** `harden-ci-workflows` is
  amended because it is on this same unmerged branch — three sentences, each
  naming this package — and the precedents that left a superseded record as
  written (`gate-tools-coverage` via R-ZCG-13, `post-merge-quality-review`
  via DEC-ZCG-003) were on `main` when they were superseded.
  `prepare-release-0-3-0` is on this branch too and is not edited by this
  draft; its AC-REL-12 re-point is a named sequencing step.
- **No change to any rule, `make` target, workflow job name, or to the
  composite action's inputs, outputs and defaults.** `RULES`, the README's
  rules table and `tests/baseline_rules.json` are untouched; the Makefile is
  not edited; the action's only diff is two `uses:` lines.
- **No floor raised or lowered.** The six existing entries in
  `[tool.specgraph.action_major_floors]` stay; the one new row is the
  publisher's, at the major it is pinned to today.
- **No `.pre-commit-hooks.yaml` change.** It switches to the first public
  tag with `prepare-release-0-3-0`; it carries no third-party `uses:` and is
  not in the scan set.

## Affected Capabilities

- `action-sha-pinning`
