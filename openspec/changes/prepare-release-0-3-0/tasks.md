# Tasks: prepare-release-0-3-0

Measured at drafting against this tree (`__version__ = "0.2.0"`; 401 lines
under `[Unreleased]`; both generator `--check` modes exit 0; `make validate`
exit 0). Every line number below is re-checked against the tree before the
milestone that uses it; a sibling package landing first may move a line
without moving the fact. Milestones 1 and 2 happen in the tree and land in
one pull request; Milestone 3 is the maintainer's, outside the tree, and its
bullets are filled in after the fact with what was observed.

## Milestone 1 — The bump set, the changelog cut, and the guards

- `openspec_graph/__init__.py`: line 15 becomes `__version__ = "0.3.0"`.
  Nothing else in the module changes (R-REL-1).
- Run `make skill-manifests`; commit the regenerated
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Confirm
  `python tools/render_plugin_manifests.py --check` and
  `python tools/render_rule_catalog.py --check` both exit 0 afterwards
  (R-REL-3, AC-REL-3).
- `skills/planlint-spec-governance/SKILL.md`: lines 5, 7 and 8 — `0.2.0` →
  `0.3.0` in `compatibility:`, `metadata.version` and
  `metadata.planlint-min-version`; lines 178–179 — "Until `v0.3.0` is
  tagged, that ref is a commit SHA; after the tag exists, switch it to
  `@v0.3.0`" (R-REL-2, DEC-REL-003). The three existing binding tests go
  red on the version bump alone and green here; watch that happen once.
- `CHANGELOG.md`: insert `## [0.3.0] — <date>` directly below the
  `[Unreleased]` heading and its blank line, with the date to be set to the
  day the tag is pushed (DEC-REL-002); below it, a preamble blockquote:
  `v0.3.0` is the first tag pushed under the `planlint` name and the first
  release published to PyPI; `v0.2.0` was never tagged, and its section
  below records the version that existed in the tree from 2026-09-12 and
  was installable from git by commit. Everything that was under
  `[Unreleased]` — every `###` group from `Changed — the CI workflows…`
  through `Fixed — pre-release adopter-surface drift`, verbatim and in
  order — now sits under the new heading, so `## [Unreleased]` is empty
  above it (R-REL-4, R-REL-5, DEC-REL-001).
- `CHANGELOG.md`, the `### Deprecated` group now under `[0.3.0]`: keep the
  Python 3.10 entry as it is; add an entry — **the `specgraph` alias is
  removed in 0.4.0.** It warns to stderr through every 0.3.x release and
  delegates with the exit code preserved; in 0.4.0 the entry point goes and
  `specgraph` is no longer installed. The waiver syntax, the config file
  name and the `[tool.specgraph]` section are stable identifiers and are
  not affected (R-REL-6, DEC-REL-005).
- `CHANGELOG.md`, the `[0.2.0]` preamble (lines 410–416): append one
  sentence — the `v0.2.0` tag was never pushed; `v0.3.0` is the first, see
  that section. Nothing else in the section changes (R-REL-5, DEC-REL-001).
- `CHANGELOG.md`, link definitions (lines 1476–1477): add
  `[Unreleased]: https://github.com/ianshank/planlint/compare/v0.3.0...HEAD`
  above and `[0.3.0]: https://github.com/ianshank/planlint/releases/tag/v0.3.0`
  before the `[0.2.0]` line (R-REL-4, AC-REL-1).
- `openspec_graph/cli.py`: `_DEPRECATION_WARNING` (lines 1010–1013) becomes
  "`specgraph` is deprecated; use `planlint` instead. The `specgraph`
  command is a backwards-compatible alias through 0.3.x and will be removed
  in 0.4.0." `main_deprecated` is untouched (R-REL-7, DEC-REL-005).
- `pyproject.toml`, the `[project.scripts]` comment: add that the alias
  warns through 0.3.x and is removed in 0.4.0. No other line in the file
  changes (R-REL-6, C-REL-1).
- `README.md`: the alias paragraph (lines 84–89) gains the window sentence;
  the "Not on PyPI yet" note (lines 54–59) and the Action-section prose
  (lines 415–417) say `v0.3.0` in place of `v0.2.0`; the two own-action
  `uses:` lines (403, 451) and the `git+https://…@a1b6868…` install (57)
  stay as they are until Milestone 3 (R-REL-6, R-REL-9, R-REL-13).
- `templates/spec-gate.yml`: the comment block (lines 60–63) says `v0.3.0`
  and `@v0.3.0`; line 65's SHA stays. Copy the file over
  `skills/planlint-spec-governance/assets/spec-gate.yml` so
  `test_skill_asset_matches_template` stays green (R-REL-9, R-REL-13,
  AC-REL-9).
- `.pre-commit-hooks.yaml`: the example's comment (lines 10–11) says
  "Until v0.3.0 is tagged … rev: v0.3.0 instead"; line 12's SHA stays
  (R-REL-9, R-REL-13).
- `docs/distribution-plan.md`: lines 15, 132 and 138 — `@v0.2.0` →
  `@v0.3.0`, so the new guard is green on this milestone; the full §3
  rewrite is Milestone 2 (R-REL-11).
- `docs/next-steps.md`: line 7's heading becomes "After the first public
  tag (0.3.0)" and line 9 names `v0.3.0` (R-REL-13).
- `.github/workflows/release.yml`: under the
  `uses: pypa/gh-action-pypi-publish@release/v1` step, add
  `with:` / `attestations: true`, preceded by a comment: this is the
  action's default made explicit so the W1.2 SHA pin cannot drop it
  silently; the input exists on every `release/v1` build since the release
  that introduced PEP 740 support, and that release is the floor the pin
  must satisfy. No other line changes; confirm `make thresholds` still
  prints PASS (R-REL-10, C-REL-2, DEC-REL-006).
- `tests/test_adopter_urls.py`: add
  `test_every_copyable_tag_ref_names_the_current_version` — over
  `ADOPTER_FILES` minus `CHANGELOG`, collect every `@v\d+\.\d+\.\d+` and
  `rev: v\d+\.\d+\.\d+` token with its file and line; assert the list is
  non-empty; assert each equals `v{__version__}`, with a message listing
  every offender as `path:line token`. Add
  `test_a_stale_tag_ref_is_named_with_file_and_line` — plant a file with
  `@v0.2.0` under `tmp_path`, run the same collector against it with the
  current version, and assert the offender string names the file and line;
  plant a file with no tag ref and assert the presence check fails rather
  than passes. Write both against the current tree first so their red
  state is seen once (the tree says `v0.2.0` in seven places), then land
  the edits above and watch them go green (R-REL-8, DEC-REL-004,
  AC-REL-7, AC-REL-8).
- `tests/test_cli_surface.py`: add
  `test_deprecated_alias_names_its_removal_version` beside the three alias
  tests — call `main_deprecated` on a clean fixture tree, read `capsys`
  stderr, assert it contains `0.4.0` and `0.3.x` and still contains
  "is deprecated; use `planlint`" (R-REL-7, DEC-REL-005, AC-REL-6).
- `tests/test_workflow_hardening.py`: add
  `test_publish_declares_attestations_explicitly` — read `RELEASE_YML`,
  take the `publish` block through `workflow_job_blocks`, strip comments,
  and assert `attestations: true` appears after the
  `pypa/gh-action-pypi-publish` line; assert the `uses:` ref is still
  `release/v1` so W1.2 is the package that moves it (R-REL-10, C-REL-4,
  AC-REL-11).
- Confirm every `0.2.0` left under `tests/` is one C-REL-5 lists, and that
  the diff touches none of them (AC-REL-23, DEC-REL-010).
- Confirm `planlint --version` prints `planlint 0.3.0` from the editable
  install, and `make wheel-check` builds and passes (AC-REL-15).
- Re-point AC-REL-6, 7, 8 and 11 in `specs/release-readiness/spec.md` from
  stage-only verification to the four tests above, now that they exist;
  run `python -m pytest tests/test_spec_test_citations.py -q` and confirm
  every selector resolves.
- **Gate:** `make pre-pr`

## Milestone 2 — The maintainer's runbook and the recurring checklist

- `docs/distribution-plan.md` §0: re-run every row at the release commit
  and record the results with that commit's SHA; replace the 0.2.0 framing
  ("The engineering side of 0.2.0 is done") with 0.3.0's; keep the
  still-true facts (`v0.1.0` at `cdc94ca`, nothing on PyPI) and date them.
- `docs/distribution-plan.md` §3, rewritten for 0.3.0 in this order
  (R-REL-11, DEC-REL-008): (1) pre-tag checks on the release commit —
  `make pre-pr`, both generator `--check` modes, `make e2e-live`, a local
  `python -m build` installed into a fresh venv whose `planlint --version`
  prints `planlint 0.3.0`; (2) one-time: the pending trusted publisher on
  PyPI (project `planlint`, owner `ianshank`, repository `planlint`,
  workflow `release.yml`, environment `pypi`) and the GitHub environment
  `pypi`, with the note that the environment string must match
  `release.yml` exactly; (3) `workflow_dispatch` `release.yml` on the
  release commit — `gate` and `build` run, `publish` is skipped — and stop
  if either is red; (4) tag the release commit `v0.3.0` and push the tag;
  (5) watch `gate`, `build` and `publish`, noting that `build` fails if the
  tag and the packaged version disagree; (6) verify the attestations on
  both published files: `GET https://pypi.org/integrity/planlint/0.3.0/<filename>/provenance`
  for the wheel and the sdist, expecting HTTP 200 and at least one bundle
  whose publisher is GitHub, then
  `pipx run pypi-attestations verify pypi --repository https://github.com/ianshank/planlint pypi:<filename>`
  for each, expecting success; (7) in a fresh venv,
  `pip install planlint==0.3.0`, `planlint --version`, and
  `planlint --target <this clone> validate --fail-on ERROR` expecting exit
  0; (8) the post-tag commit: every own-action ref to `@v0.3.0`
  (`templates/spec-gate.yml`, its `skills/` copy, `README.md` ×2), the
  `.pre-commit-hooks.yaml` example to `rev: v0.3.0`, the README "Not on
  PyPI yet" note deleted, the README `git+` install line replaced by
  `pip install planlint`, SKILL.md lines 178–179 rewritten to "pin
  `@v0.3.0`", `SECURITY.md`'s supported-versions paragraph naming 0.3.0;
  `make pre-pr` green on it; (9) the GitHub release created from the
  `[0.3.0]` section; (10) the Context7 submission. Exit criterion: M1's —
  the tag is published and `pip install planlint==0.3.0` runs `validate`
  on this repository. Failure mode paragraph kept: a tag without the
  publisher is a red workflow and a half-product; do (2)–(7) in one
  sitting (DEC-REL-007).
- `docs/distribution-plan.md`: confirm no `@v0.2.0` remains anywhere in
  the file, and that the "First foreign CI adopter" paragraph says
  `@v0.3.0`.
- `docs/hooks.md`, "Releasing a skill change": widen to "Releasing" — the
  policy paragraph stays; add the checklist: edit `__version__` in
  `openspec_graph/__init__.py`; run `make skill-manifests`; run
  `make test` and follow its failures, which name every remaining hand
  edit — `test_skill_metadata_version_matches_the_package`,
  `test_ci_template_pins_the_floor_the_skill_enforces` and
  `test_compatibility_prose_matches_the_declared_minimum` for the three
  SKILL.md fields, `test_every_changelog_version_links_to_its_release_tag`
  for the changelog section and link, and
  `test_every_copyable_tag_ref_names_the_current_version` for every
  copyable tag ref; then the changelog cut of DEC-REL-002 and the runbook
  in `docs/distribution-plan.md` §3 (R-REL-12, DEC-REL-004, DEC-REL-008).
- `docs/hooks.md`, the CI table's `release` row: append "and uploads PEP
  740 attestations for both files" (R-REL-12).
- Confirm `make docs-check` prints its pass line: every required document
  present and linked (AC-REL-16).
- **Gate:** `make docs-check`

## Milestone 3 — Tag, publish, observe, record (the maintainer, outside the tree)

- Precondition: Milestones 1 and 2 are merged to `main` and the merge
  commit's `make pre-pr` and CI are green. The release commit is that merge
  commit, or a follow-up on `main` that only sets the changelog date.
- Run §3 steps (1)–(3) of the runbook. Record here: the `workflow_dispatch`
  run id, and that `gate` and `build` succeeded with `publish` skipped.
- Run §3 steps (4)–(5). Record here: the tag's commit SHA, the `release.yml`
  run id, the result and duration of `gate`, `build` and `publish`, and
  that the `build` job's tag-versus-package check passed (AC-REL-19).
- Run §3 step (6). Record here, for the wheel and the sdist: the Integrity
  API's HTTP status and bundle count, the publisher kind, and the
  verifier's verdict line, with the date (AC-REL-20, DEC-REL-006).
- Run §3 step (7). Record here: the `planlint --version` output from the
  fresh venv and the exit code of `validate --fail-on ERROR` against this
  repository — the plan's M1 exit criterion (AC-REL-21).
- Run §3 step (8), commit, and confirm `make pre-pr` is green on the
  post-tag commit. Record its SHA here (AC-REL-22, DEC-REL-007).
- Run §3 steps (9)–(10). Record the GitHub release URL and the Context7
  submission date here.
- Check AC-REL-19, 20, 21 and 22 in `specs/release-readiness/spec.md` only
  once each observation above is recorded, and confirm this package
  validates clean under the repo's own rules
  (`planlint --target . validate --fail-on ERROR --change
  prepare-release-0-3-0`), then the whole tree (DEC-REL-009, C-REL-6).
- Record for the plan's M1 row, when `docs/reflection-plan-2026-10.md`
  merges: the SKILL.md fields were already pinned by three existing tests
  (DEC-REL-003); the bump-set guard is a test, not a `tools/` script
  (DEC-REL-004); attestations are declared on the publish step and verified
  by hand (DEC-REL-006).
- **Gate:** `make pre-pr`
