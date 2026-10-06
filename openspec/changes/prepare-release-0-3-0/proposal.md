# Change: Prepare the 0.3.0 Release — Bump Set, Changelog Cut, Deprecation Window, Attested Publish

## Why

This project has never published a release. `openspec_graph/__init__.py`
says `0.2.0`, `CHANGELOG.md` has a dated `[0.2.0]` section whose preamble
promises that "publication happens when the tag is pushed", and
`docs/distribution-plan.md` records — checked against `origin`, not
remembered — that no `v0.2.0` tag exists, that `.github/workflows/release.yml`
has never run, and that `pip install planlint` 404s. Since that section was
dated, the `[Unreleased]` heading has accumulated every change the two
October review rounds produced: three new rules, the findings envelope's
line hits, the stage-citation report, the per-directory agent files, the
`tools/` coverage floors, and milestone M0's workflow hardening with its
`Deprecated` notice that 0.4.0 drops Python 3.10. The release that carries
all of it is 0.3.0, and the plan's M1 exit criterion is concrete: the tag is
published and `pip install planlint==0.3.0` runs `validate` on this
repository.

Cutting a release here is wider than one literal. The version is written by
hand in three frontmatter fields of the distributable skill; two plugin
manifests are generated from it; the changelog must gain a section and a
link definition the test suite checks for; and the adopter-facing surface —
the CI template and its byte-identical copy under `skills/`, two README
snippets, the pre-commit example, the skill's own prose and the distribution
plan — names the tag an adopter should switch to once it exists. Every one
of those names `v0.2.0` today. The `specgraph` alias has been deprecated
since the rename with no removal version anywhere a user would read it. And
the publish step relies on the PyPA action's default to generate PEP 740
attestations — a behaviour stated nowhere in this tree, that depends on the
version of the action being at or above the release that made it the
default, and that the sibling `pin-actions-by-sha` fixes to one commit which
Dependabot will move.

This package makes the tree release-ready and writes down what the
maintainer does next. It is workstream W1.5 of milestone M1 in the October
2026 reflection plan; that plan is on its own branch and not in this tree at
drafting time, so its items are restated here and every number below is
re-measured against this checkout rather than cited from it. It is the
**last** of the three M1 packages to land, after `pin-actions-by-sha` (W1.2)
and `write-down-policies` (W8.3): it moves the whole `[Unreleased]` body of
the changelog, so every sibling's entry must already be under that heading
(DEC-REL-011). Pushing the tag and publishing are the maintainer's actions,
outside the tree; what they observe afterwards — the attestations on the
published files, the fresh-venv install running `validate` — is recorded in
`tasks.md` after the fact, exactly as the sibling `harden-ci-workflows`
records its CI run evidence.

**Evidence:** measured at `ea40bc2` on `claude/m1-pin-and-release`,
2026-10-06, before either sibling has landed; each command re-measures it,
and a sibling landing first moves a line number without moving the fact.

- **One version source, many copies.** `openspec_graph/__init__.py` line 15
  is `__version__ = "0.2.0"`, and `pyproject.toml` reads it through
  `dynamic = ["version"]` with `attr:` (DEC-SD-009). Hand-written copies:
  `skills/planlint-spec-governance/SKILL.md` lines 5 (`compatibility:`
  prose), 7 (`metadata.version`) and 8 (`metadata.planlint-min-version`),
  plus lines 178–179 (`v0.2.0` / `@v0.2.0` in the "Wiring it into CI"
  prose). Generated copies: `.claude-plugin/plugin.json` line 3 and
  `.claude-plugin/marketplace.json` lines 9 and 16, written by
  `tools/render_plugin_manifests.py` from `__version__`
  (`make skill-manifests`); `python tools/render_plugin_manifests.py --check`
  and `python tools/render_rule_catalog.py --check` both exit 0 today. One
  more hand-written copy that no test reads:
  `.github/actions/planlint/action.yml` line 34, where the `version` input's
  description gives `"0.2.0"` as its example of an exact version to install
  from the index — a version that will never be on the index.
- **The SKILL.md fields are already pinned — the plan's conditional is
  answered.** `tests/test_agent_skill_docs.py` holds
  `test_skill_metadata_version_matches_the_package` (`metadata.version ==
  __version__`), `test_compatibility_prose_matches_the_declared_minimum`
  (the numeric version in `compatibility:` equals `planlint-min-version`)
  and `test_skill_min_version_is_not_ahead_of_the_package`;
  `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
  asserts `planlint-min-version == __version__` and that
  `templates/spec-gate.yml`'s own-action `uses:` ref is either
  `v{__version__}` or a 40-hex SHA with `@v{__version__}` named in the file.
  Together they bind all three frontmatter lines to the package; no new
  SKILL.md test is needed. The two prose mentions on lines 178–179 are bound
  by nothing.
- **The changelog.** `grep -n '^## ' CHANGELOG.md` at `ea40bc2`: line 6 is
  `## [Unreleased]`, line 408 is `## [0.2.0] — 2026-09-12`, line 1464 is
  `## [0.1.0] — 2026-08-30`; the difference between the first two is what
  sits under Unreleased (the plan counted about 355 lines at `9c4b6e9`; M0's
  `Changed` and `Deprecated` entries landed since, and both siblings add
  more before this package moves it). The `### Deprecated` heading at line
  45 carries the 0.4.0 removal of Python 3.10, `requires-python >= 3.11`
  and the `tomli` marker (R-HCW-12). The only link definitions are `[0.2.0]`
  and `[0.1.0]` (lines 1476–1477); there is no `[Unreleased]` link. The
  `[0.2.0]` preamble (lines 410–416) says "`v0.2.0` is the first release
  under the `planlint` name and the first intended for PyPI; publication
  happens when the tag is pushed … through PR #24"; its "release-train
  honesty" entry (lines 437–440) says the section was folded from an earlier
  `2026-09-02` heading and that "the date is the first public tag, not the
  freeze that never shipped" — a sentence that was a promise when written
  and is false now, because the tag was never pushed; `2026-09-12` is the
  day the fold landed (PR #25), not a tag date.
  `test_every_changelog_version_links_to_its_release_tag` asserts
  `__version__` has a `## [X.Y.Z]` heading and that every such heading has a
  `[X.Y.Z]: https://github.com/ianshank/planlint/releases/tag/vX.Y.Z` line,
  so the bump cannot land without the `[0.3.0]` section and link.
- **Nothing was ever tagged under this name.** `docs/distribution-plan.md`
  §0 and §2: `v0.1.0` exists on `origin` at `cdc94ca` under the pre-rename
  distribution; no `v0.2.0` tag exists; `release.yml` has never run;
  `planlint` and `openspec-graph` both 404 on PyPI. `README.md` lines 54–59
  carry a "Not on PyPI yet" note that gives the `git+https://…@a1b6868…`
  install and "says to delete itself when the tag is cut"; lines 415–417
  say `v0.2.0` "is **not on GitHub until the release workflow cuts it**".
  `docs/next-steps.md` line 7 is headed "After the first public tag (0.2.0)".
  `SECURITY.md` line 56 supports "only the latest released version".
- **The release workflow.** `.github/workflows/release.yml` triggers on
  `push: tags: v*` and `workflow_dispatch`; `gate` runs `make pre-pr`;
  `build` runs `python -m build`, `tools/check_wheel_metadata.py dist`,
  installs the wheel into a fresh venv, runs the `planlint` console script
  (`--version`, `detect`, `validate --fail-on ERROR`) and fails when
  `${GITHUB_REF_NAME#v}` differs from `planlint --version`'s second word;
  `publish` is `if: github.ref_type == 'tag'`, `environment: pypi`,
  `permissions: id-token: write`, and its last step (line 117) is
  `uses: pypa/gh-action-pypi-publish@release/v1` with no `with:` block.
  `pin-actions-by-sha` (R-ASP-3, DEC-ASP-005) rewrites that one line to
  `@dc37677b2e1c63e2034f94d8a5b11f265b73ba33 # v1.14.2` before this package
  lands; this package writes a `with:` block directly beneath it and touches
  no `uses:` line.
  `tests/test_agent_artifacts.py::test_release_workflow_is_gated_and_uses_trusted_publishing`
  pins the gate → build → publish chain, the venv smoke test, `id-token:
  write` and the absence of a stored token, and does not name the
  publisher's ref; `tests/test_workflow_hardening.py` holds the per-job
  timeouts and the absence of a `concurrency` group.
- **Attestations are a default, not a declaration — and a default with a
  version floor.** The PyPA action's `action.yml` on `release/v1`, fetched
  at drafting, declares an input `attestations` — "Enable support for PEP
  740 attestations. Only works with PyPI and TestPyPI via Trusted
  Publishing." — with `default: 'true'`. The input's history, from the
  action's own release notes: it was added in v1.10.0 with `default: false`
  and marked experimental; v1.11.0 made it `default: true`; the sibling's
  pin, v1.14.2, carries it non-experimental and on by default. So the
  behaviour this release relies on is a property of the pinned version: a
  pin at or above v1.11.0 attests by default, a v1.10.x pin attests only if
  told to, and a pin older than v1.10.0 does not know the input at all and
  answers an explicit one with GitHub's "Unexpected input" warning
  annotation. PyPI's Integrity API answers
  `GET https://pypi.org/integrity/<project>/<version>/<filename>/provenance`
  with the attestation bundles: probed at drafting against
  `pypi-attestations` 0.0.30's wheel, HTTP 200, one bundle, publisher kind
  `GitHub`. No verifier is installed in this environment
  (`import pypi_attestations` fails), and `[project] dependencies = []` is
  load-bearing.
- **The alias names no removal version.** `openspec_graph/cli.py` lines
  1010–1013: `_DEPRECATION_WARNING` is "`specgraph` is deprecated; use
  `planlint` instead. The `specgraph` command is a backwards-compatible
  alias and will be removed." — no version. `main_deprecated` (line 1016)
  prints it to stderr and delegates to `main`, preserving the exit code.
  `tests/test_cli_surface.py` holds
  `test_deprecated_alias_warns_to_stderr_and_delegates`,
  `test_deprecated_alias_preserves_failure_exit_code`,
  `test_deprecated_alias_keeps_stdout_parseable` (which asserts the
  substring "is deprecated; use `planlint`" on stderr and not on stdout) and
  `test_primary_command_emits_no_deprecation_warning`. `README.md` lines
  84–89, the `[project.scripts]` comment in `pyproject.toml` and the
  `[0.2.0]` rename entry describe the alias; none names when it goes. The
  sibling `write-down-policies` states the general deprecation rule in
  `docs/policies.md` and writes the `specgraph` line into the `Deprecated`
  group under `[Unreleased]`, where the verbatim move of R-REL-4 carries it
  into `[0.3.0]` (its DEC-POL-009; R-REL-6 here).
- **Every copyable tag ref says 0.2.0.** The set is produced by
  `grep -rnE '@v[0-9]+\.[0-9]+\.[0-9]+|rev:\s*v[0-9]+\.[0-9]+\.[0-9]+' --include='*.md' --include='*.yml' --include='*.yaml' . --exclude-dir=.git --exclude-dir=openspec`
  with `CHANGELOG.md` dropped from its output; at `ea40bc2` it names eight
  tokens in six files — `templates/spec-gate.yml:63`,
  `skills/planlint-spec-governance/assets/spec-gate.yml:63`,
  `skills/planlint-spec-governance/SKILL.md:179`, `README.md:417`,
  `.pre-commit-hooks.yaml:11` and `docs/distribution-plan.md:15,132,138` —
  all `v0.2.0`. No third-party action ref is among them: the third-party
  refs in the corpus are bare majors (`@v7`, `@v3`) today and become
  `@<sha> # vX.Y.Z` once `pin-actions-by-sha` lands, and neither shape
  carries `@v<semver>`. The pinned SHA those files hold meanwhile is
  `a1b686864282e27c754ec1d49ac6f931e1e140e1` (`templates/spec-gate.yml:65`,
  the asset copy, `README.md:403,451`, `.pre-commit-hooks.yaml:12`,
  `README.md:57`). `tests/test_adopter_urls.py` already globs this corpus
  (`_adopter_files()`, excluding `openspec/`) and reads `__version__`; its
  `test_skill_asset_matches_template` sibling in `tests/test_skill_contract.py`
  holds the two template copies byte-identical.
- **Nothing in `tests/` pins the version to a release.** The remaining
  `0.2.0` literals under `tests/` are fixtures and comments:
  `tests/test_wheel_metadata.py:40` (a METADATA fixture the checker never
  compares), `tests/test_finding_line_hits.py:426,433` (`tool_version`
  fixture values), `tests/test_agent_skill_docs.py:351,357,396,399`
  (frontmatter-parser fixtures), `tests/test_adopter_urls.py:116,339` and
  `tests/test_skill_contract.py:812` (comments). The golden `validate`
  hashes in `tests/test_decomposition.py` normalise `tool_version` away
  (`_TOOL_VERSION`, line 75), so a bump re-pins nothing.
- **Stages a workflow runs by name.** `make stage-citations` at `ea40bc2`:
  `pre-pr` is run directly by `release.yml`; `e2e-live` and `docs-check` by
  `ci.yml`; `wheel-check` by no workflow (the `packaging` job runs its two
  commands directly) and it is already cited on another package's
  verification line.
- **The interim window.** Between the commit that bumps `__version__` to
  `0.3.0` and the tag, the README's `git+https://…@a1b6868…` install and
  the own-action `@a1b6868…` refs still install the code of that commit,
  which reports `planlint 0.2.0`; the skill's `planlint-min-version`, bound
  to `__version__` by the tests above, reads `0.3.0` and refuses that CLI.
  The composite Action does not consult the skill's floor and keeps working.
  `test_ci_template_pins_the_floor_the_skill_enforces` accepts both the
  pre-tag SHA and the post-tag `@v0.3.0`, so no test turns red while the
  window is open — the runbook is what closes it (DEC-REL-007).

## What Changes

- `openspec_graph/__init__.py`: `__version__ = "0.3.0"`. The only version
  literal in code.
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`:
  regenerated with `make skill-manifests`; no hand edit.
- `skills/planlint-spec-governance/SKILL.md`: lines 5, 7 and 8 become
  `0.3.0`; lines 178–179 name `v0.3.0` as the tag to switch to, and after
  the tag exists say to pin `@v0.3.0`.
- `CHANGELOG.md`: the `[Unreleased]` body — every line of it, with its
  `###` groupings, including M0's `Changed` entry, the `Deprecated` notice
  for Python 3.10, `pin-actions-by-sha`'s `Changed` entry and
  `write-down-policies`' `Added` entry and `specgraph` `Deprecated` line —
  moves verbatim under a new `## [0.3.0] — <date>` heading that opens with a
  preamble stating `v0.3.0` is the first tag pushed under the `planlint`
  name and the first release on PyPI, and that `v0.2.0` was never tagged;
  if `write-down-policies` has not landed, the `specgraph` window (warns
  through 0.3.x, removed in 0.4.0) is written into the `Deprecated` group
  here instead; an empty `## [Unreleased]` stays at the top; link
  definitions `[Unreleased]: …/compare/v0.3.0...HEAD` and
  `[0.3.0]: …/releases/tag/v0.3.0` are added; the `[0.2.0]` section and
  link stand, with one sentence appended to its preamble saying what its
  date is (the day the section was folded, PR #25), that the tag was never
  pushed, and that its link is kept for the file's convention and does not
  resolve.
- `openspec_graph/cli.py`: `_DEPRECATION_WARNING` keeps its first sentence
  and its second becomes "The `specgraph` command is a backwards-compatible
  alias through 0.3.x and will be removed in 0.4.0." `main_deprecated` is
  unchanged.
- `pyproject.toml`: the `[project.scripts]` comment states the same window.
  Nothing else in the file changes.
- `README.md`: the alias paragraph (lines 84–89) states the window; the
  "Not on PyPI yet" note names `v0.3.0` and gains the interim-window
  sentence of DEC-REL-007 (between the bump and the tag the git install
  gives 0.2.0-era code, which the skill's floor rejects; use the Action, or
  wait for the tag); the Action section's tag prose (lines 415–417) names
  `v0.3.0`; after the tag, the note is deleted and the two own-action
  `uses:` snippets (lines 403, 451) become `@v0.3.0`.
- `templates/spec-gate.yml` and its byte-identical copy
  `skills/planlint-spec-governance/assets/spec-gate.yml`: the comment block
  (lines 59–63 at `ea40bc2`; `pin-actions-by-sha` adds two sentences to it
  first) names `v0.3.0`; the `uses:` SHA on line 65 stays until the tag
  exists, then becomes `@v0.3.0`.
- `.pre-commit-hooks.yaml`: the example's comment names `v0.3.0`; the
  `rev:` SHA stays until the tag exists, then becomes `rev: v0.3.0`.
- `.github/actions/planlint/action.yml`: the `version` input's description
  example becomes `"0.3.0"` (DEC-REL-012). The input set, every default and
  every `uses:` line are untouched.
- `.github/workflows/release.yml`: the `pypa/gh-action-pypi-publish` step
  — whose `uses:` line `pin-actions-by-sha` has already pinned — gains
  `with: attestations: true` and the comment of R-REL-10 naming it as the
  action's default since v1.11.0, stated so a pin cannot drop it, with the
  floor the pin must satisfy. No `uses:` line and no other line changes.
- `tests/test_adopter_urls.py`: two new tests —
  `test_every_copyable_tag_ref_names_the_current_version` (every
  copyable tag token in the adopter corpus other than `CHANGELOG.md` equals
  `v{__version__}`, with a presence floor so the scan cannot pass on an
  empty match set, and a pattern anchored so a third-party
  `owner/repo@vX.Y.Z` is never read as this project's tag) and
  `test_a_stale_tag_ref_is_named_with_file_and_line` (a planted `@v0.2.0`
  is reported with file and line).
- `tests/test_cli_surface.py`: one new test,
  `test_deprecated_alias_names_its_removal_version` — the stderr warning
  names `0.4.0` and still carries the substring the sibling tests assert.
- `tests/test_workflow_hardening.py`: one new test,
  `test_publish_declares_attestations_explicitly` — the `publish` job's
  `pypa/gh-action-pypi-publish` step has `attestations: true` under
  `with:`, read from the uncommented job block. It asserts nothing about
  the step's `uses:` ref, which `pin-actions-by-sha`'s guards own.
- `docs/distribution-plan.md`: §0 re-measured on the branch head as a dry
  run and again on the merge commit (the SHA recorded after the merge); §3
  rewritten as the 0.3.0 runbook — pre-tag checks, the one-time PyPI
  pending publisher and the `pypi` environment, the `workflow_dispatch`
  dry run, tag and push, watching the three jobs, verifying attestations
  through the Integrity API and a verifier run ephemerally, the fresh-venv
  install that runs `validate` on this repository, the post-tag ref flip,
  the GitHub release from the `[0.3.0]` section, Context7; every `@v0.2.0`
  becomes `@v0.3.0`; the exit criterion becomes M1's.
- `docs/hooks.md`: the "Releasing a skill change" section widens to the
  package-release checklist — one literal, one regeneration, and the test
  names that enumerate every remaining hand edit; the `release` row of the
  CI table mentions attestations.
- `docs/next-steps.md`: the heading and first sentence name 0.3.0.
- `SECURITY.md`: after publication, the supported-versions paragraph names
  0.3.0 as the latest released version.
- `tasks.md` of this package: the post-publish observations, with run ids,
  dates and the verifier's output, recorded after the fact.

## Non-Goals

- **No tag push, no publish, no PyPI or GitHub settings from inside this
  package.** Registering the pending trusted publisher, creating the `pypi`
  environment, dispatching the dry run, pushing `v0.3.0` and creating the
  GitHub release are the maintainer's actions outside the tree. The package
  claims readiness and records what was observed; it performs none of them.
- **No edit to any third-party `uses:` ref.** Every one of those — the
  publisher's included — is `pin-actions-by-sha`'s, which lands before this
  package. This one adds a single input beneath the publisher's already
  pinned line and a guard for that input; the guard reads the input and not
  the ref, so its meaning does not depend on which package landed first
  (C-REL-4, DEC-REL-011).
- **No 0.4.0 work.** `requires-python`, the classifiers, the 3.10 matrix
  leg, `[tool.mypy] python_version`, the `tomli` marker and the `specgraph`
  entry point are unchanged. 0.3.0 announces both removals; 0.4.0 performs
  them.
- **No new runtime or dev dependency, no new `tools/` script, no new
  generator.** Attestation verification runs a verifier ephemerally from
  the maintainer's shell once per release; the bump-set guard is a test in
  the module that already globs the adopter corpus. Nothing new is
  installed by `pip install -e ".[dev]"` and `tools/` stays as it is.
- **No new document.** The runbook lives in `docs/distribution-plan.md`,
  which `harden-ci-workflows` (C-HCW-3, DEC-HCW-012) already names as the
  owner of the switch from the SHA to the tag; the recurring checklist
  lives in `docs/hooks.md`, which `tools/check_docs.py` requires and the
  README links. The general deprecation rule lives in `docs/policies.md`,
  which `write-down-policies` creates; this package states the `specgraph`
  instance where each audience reads it and does not restate the rule. The
  plan's W9.3 release skill, when it arrives, reads these.
- **No rewriting of history to satisfy a guard.** The `[0.2.0]` section
  keeps its heading, date, body and link; fixtures and comments carrying
  `0.2.0` under `tests/`, the "Changed in 0.2.0" README note, the `cli.py`
  comment and the dated planning documents are not edited. The guard's
  scope is copyable instructions, not mentions.
- **No change to any rule, `make` target, workflow job name or coverage
  floor.** The `RULES` tuple, the README rules table,
  `tests/baseline_rules.json`, the `Makefile` and every job name are
  untouched.
- **No advance of the interim SHA inside this package.** The pinned
  `a1b6868…` installs the CLI from that checkout, so it runs the code of
  that commit, not 0.3.0; the remedy is the tag, flipped to in the same
  sitting as the publish. Moving the SHA to the release commit inside this
  package would be a commit that cannot name itself. If the sitting is
  expected to slip, DEC-REL-007 offers the one-line follow-up commit on
  `main` that points the README's `git+` line at the merge SHA — a later
  commit can name the merge commit — as the maintainer's option, not this
  package's edit.

## Affected Capabilities

- `release-readiness`
