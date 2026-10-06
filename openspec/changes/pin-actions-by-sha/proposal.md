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
resolved and verified": the header of `.github/dependabot.yml`, the deferred
row in `docs/next-steps.md`, and the CHANGELOG's Dependabot entry. The
precondition is met on its own terms. The pins are resolved below, from each
repository's own refs advertisement; Dependabot — the thing the deferral named
as the prerequisite — watches both action directories and rewrites a SHA pin
and its version comment together; and M0's per-action floor gives a pinned
SHA the one invariant it otherwise lacks, provided the version it pins is
written where the floor guard can read it. That is why the pin format carries
the release tag in a trailing comment: the SHA is the pin, the comment is what
the floor, Dependabot and a reviewer read.

M0's guard forbids exactly this: `C-HCW-3` says no third-party ref may become
a commit SHA and names SHA pinning as a separate package; `AC-HCW-24` asserts
it. This is that package, and it supersedes both. It is item W1.2 of
milestone M1 of the October 2026 reflection plan; the plan is on its own
branch and not in this tree at drafting time, so its item is restated here
and every fact below is re-measured against this tree.

**Evidence:** measured at `5fe043e` on branch `claude/m1-pin-and-release`,
the tree M0 landed on; a sibling package landing first may move a line
number without moving the fact.

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
  requires until `v0.2.0` exists and `docs/distribution-plan.md` step 7 then
  moves to `@v0.2.0`.
- **The guard forbids a SHA today, and would go blind on one.**
  `tests/test_workflow_hardening.py`: `ACTION_REF_SCAN` (line 40) is the
  workflows, the composite action, `templates/*.yml` and the README;
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
  "a branch ref [that] has no major".
- **What M0 said this package would be.** `openspec/changes/harden-ci-workflows/specs/ci-workflow-hardening/spec.md`:
  C-HCW-3 "No third-party action ref MAY become a commit SHA, and
  `pypa/gh-action-pypi-publish@release/v1` MUST be untouched. SHA pinning is
  a separate package"; AC-HCW-24 cites
  `test_no_third_party_action_ref_is_a_commit_sha` and
  `test_the_own_action_ref_is_exempt_from_the_sha_check`; R-HCW-2 (one ref
  per action across the scan set) and R-HCW-17 / DEC-HCW-014 (the floor, "a
  ratchet a bump never edits") are the two invariants this package keeps
  meaningful; DEC-HCW-012 puts the templates and the README in the scan and
  accepts that Dependabot watches neither; DEC-HCW-014's last sentence:
  "`pypa/gh-action-pypi-publish@release/v1` has no major; W1.2 moves it with
  the SHA pins."
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
  which is also the `release/v1` branch head at drafting.
- **Dependabot is the prerequisite, and is in place.** `.github/dependabot.yml`
  lines 16–22 record the deferral and name an update bot as "the prerequisite
  for closing that item, not a substitute for it"; it watches `/` (line 31)
  and `/.github/actions/planlint` (line 53), and its `actions-minor` group
  (lines 40–50) collects `actions/*` minor and patch updates while leaving
  `pypa/gh-action-pypi-publish` on its own pull request. It watches neither
  `templates/` nor `README.md`, so a bump there is carried by hand — which
  R-HCW-2's agreement guard enforces, and DEC-HCW-012 calls the intended
  effect.
- **The records that close.** `docs/next-steps.md` line 227 is the deferred
  row "SHA-pinning the third-party actions inside `action.yml`", reopened
  when "the pins can be resolved and verified"; `CHANGELOG.md`'s "Added —
  Dependabot" entry quotes the same deferral; `docs/aqa.md` line 40 gives
  `actions/checkout@v7` as the example of a CI pin outside the thresholds
  gate; `docs/hooks.md` lines 66–70 describe the floor posture in terms of
  major tags.
- **What a rename would break.** `tests/test_spec_test_citations.py`
  resolves every `pytest -k` selector in every spec by substring over the
  test function names under `tests/`, read from the AST;
  `test_no_third_party_action_ref_is_a_commit_sha` is cited by AC-HCW-24 in
  `harden-ci-workflows`' spec, and shipped packages' records are not edited
  by later ones (the convention `select-zero-cost-guards` R-ZCG-13 states).
- **What the release test pins, and does not.**
  `tests/test_agent_artifacts.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
  (line 491) asserts the `gate → build → publish` chain, `make pre-pr` in
  `gate`, the clean-venv smoke test and `id-token: write` on `publish`, over
  the job blocks with comments stripped; it does not name the publisher's
  ref, so the pin changes nothing it checks.

## What Changes

- `tests/test_workflow_hardening.py`: `_uses_refs` reads each `uses:` line
  raw — the code half for the action and ref, the comment half for the
  version — and returns a fifth element, the `vMAJOR.MINOR.PATCH` token after
  the `#` or `None`; a `_pin_offenders(paths)` helper names every third-party
  ref that is not a 40-hex SHA, every SHA with no comment, and every comment
  that is not exactly a release tag; `_ref_disagreements` compares the
  (SHA, version) pair; `_floor_offenders` reads the major from the comment
  when the ref is a SHA. `test_no_third_party_action_ref_is_a_commit_sha`
  becomes `test_no_third_party_action_ref_is_a_commit_sha_without_its_version_comment`
  — the old name stays a substring, so AC-HCW-24's citation keeps resolving
  — and asserts the narrower property that no pin has lost its comment;
  `test_the_own_action_ref_is_exempt_from_the_sha_check`,
  `test_every_third_party_action_meets_its_major_floor`,
  `test_a_uniformly_retired_major_is_named_with_file_and_line`,
  `test_an_action_without_a_floor_is_named` and
  `test_a_leftover_retired_major_is_reported_with_file_and_line` keep their
  names with their planted text moved to the pinned shape. New guards: the
  real-tree pin-shape assertion, and planted counter-examples for a tag ref,
  a branch ref, a bare SHA, a malformed comment, a comment below the floor,
  uniformly retired comments across two files, a comment disagreement behind
  one SHA, the raw-line read, and the thresholds guard's silence on a pinned
  line. Every message names file and line.
- `pyproject.toml`: `[tool.specgraph.action_major_floors]` gains
  `"pypa/gh-action-pypi-publish" = 1`, because the action now carries a
  version the floor guard reads and a pinned action with no floor is an
  offender. No existing entry moves.
- `.github/workflows/ci.yml`, `.github/workflows/release.yml`,
  `.github/actions/planlint/action.yml`: every third-party `uses:` becomes
  `@<40-hex> # vX.Y.Z`, the SHA being the peeled commit of the tag the
  comment names, in one batch; `release.yml`'s publisher becomes the
  `v1.14.2` commit with `# v1.14.2`. Nothing else in any of the three files
  changes.
- `templates/spec-gate.yml` and its byte copy
  `skills/planlint-spec-governance/assets/spec-gate.yml`: `actions/checkout`
  and `github/codeql-action/upload-sarif` pinned the same way; the comment
  block above the own-action step gains two sentences on what the pins are
  and that Dependabot keeps them fresh. `README.md`'s workflow block: its
  `actions/checkout` line pinned the same way. The
  `ianshank/planlint/.github/actions/planlint@a1b686…` lines in all three are
  untouched.
- `.github/dependabot.yml`: the header's deferral paragraph is rewritten to
  record that the pins are resolved and how the comment is what Dependabot
  and the floor read; the three `updates:` entries and the `actions-minor`
  group are unchanged.
- `docs/next-steps.md`: the deferred row records its closing by this package
  and the guard that holds it, rather than a reopen condition.
- `docs/aqa.md`: the `actions/checkout@v7` example becomes a description of
  the pinned shape; `docs/hooks.md`: the floor paragraph says every
  third-party action is pinned to a commit SHA with its release tag in a
  trailing comment, and that the floor reads the comment.
- `CHANGELOG.md` `[Unreleased]`: a `Changed` entry for this package naming the
  pin format, the publisher's move from a branch to a tagged commit, the
  floor table's new row, and the supersession of C-HCW-3 and AC-HCW-24.
- `openspec/changes/pin-actions-by-sha/tasks.md`: the `git ls-remote --tags`
  output for every action, including the peeled line of each annotated tag,
  recorded at implementation beside the drafting values above.

## Non-Goals

- **No change to this repository's own action ref.** The
  `ianshank/planlint/.github/actions/planlint@a1b686…` lines in the template,
  the skill asset and the README stay exactly as they are, as does
  `./.github/actions/planlint` in `ci.yml`. The own ref is a SHA already,
  belongs to `test_ci_template_pins_the_floor_the_skill_enforces` and
  `docs/distribution-plan.md`, and moves to `@v0.2.0` at the release (W1.5),
  not here. The guard's `OWN_ACTION_PREFIX` exemption stays.
- **No release (W1.5).** No tag, no version bump, no change to
  `release.yml`'s jobs, `needs:` chain, permissions or `id-token: write`.
  The publisher's new commit is the one `release/v1` already points at, so
  what the action does — including the PEP 740 attestations it generates by
  default under trusted publishing — is unchanged by this package and is not
  claimed by it; the first `v*` tag is where that is observed.
- **No network in the test suite.** The guard checks shape, floor and
  agreement offline. That a SHA is the commit its comment names is resolved
  by `git ls-remote` at implementation and recorded in `tasks.md`; a test
  that fetched refs would be red on a sandboxed runner and on a fork pull
  request with no token, for a reason unrelated to the tree.
- **No pinned version in any test, and no SHA of a real action in any
  test.** Planted counter-examples use synthetic SHAs; a test that said
  `3d3c42e…` would be a second copy of the pin that the next Dependabot bump
  has to edit — DEC-HCW-008's objection, which still holds.
- **No change to Dependabot's scope or grouping.** No `ignore:`, no new
  ecosystem, no change to the `actions-minor` group's patterns or update
  types, no entry for `templates/` or `README.md` (Dependabot's
  `github-actions` ecosystem does not read either). The hand-carried bump for
  those two files is the cost DEC-HCW-012 accepted and the agreement guard
  enforces.
- **No edit to any shipped package's spec.** `harden-ci-workflows`' C-HCW-3
  and AC-HCW-24 are named as superseded here; their text is a record of what
  M0 decided and is left as written, in the convention R-ZCG-13 and
  DEC-ZCG-003 follow.
- **No change to any rule, `make` target, workflow job name, or to the
  composite action's inputs, outputs and defaults.** `RULES`, the README's
  rules table and `tests/baseline_rules.json` are untouched; the Makefile is
  not edited; the action's only diff is two `uses:` lines.
- **No floor raised or lowered.** The six existing entries in
  `[tool.specgraph.action_major_floors]` stay; the one new row is the
  publisher's, at the major it is pinned to today.
- **No `.pre-commit-hooks.yaml` change.** `docs/distribution-plan.md` step 7
  names it among the files that switch to `@v0.2.0`; it carries no
  third-party `uses:` and is not in the scan set.

## Affected Capabilities

- `action-sha-pinning`
