# Tasks: prepare-release-0-3-0

Measured at `ea40bc2` on `claude/m1-pin-and-release` (the branch head, read
from `.git/refs/heads/`), 2026-10-06 — the siblings' records say `5fe043e`;
every fact below was re-measured at `ea40bc2` and agrees. Every number here
names the command that produced it: `python -c "import openspec_graph;
print(openspec_graph.__version__)"` prints `0.2.0`; `grep -n '^## '
CHANGELOG.md` puts `## [Unreleased]` at line 6 and `## [0.2.0]` at line 408,
so the body under Unreleased is the lines between; `python
tools/render_plugin_manifests.py --check` and `python
tools/render_rule_catalog.py --check` both exit 0; `make validate` exits 0;
the copyable-tag grep in the proposal's Evidence prints eight tokens in six
files. These measurements predate `pin-actions-by-sha` and
`write-down-policies` landing on the branch: both land before this package
(DEC-REL-011), and Milestone 1 re-measures every line number and every count
at the branch head it starts from, so a sibling moving a line is expected
and does not move the fact. Milestones 1 and 2 happen in the tree and land
in one pull request; Milestone 3 is the maintainer's, outside the tree, and
its bullets are filled in after the fact with what was observed.

## Milestone 1 — The bump set, the changelog cut, and the guards

- Preconditions, checked before the first edit: `pin-actions-by-sha` and
  `write-down-policies` are both in the tree this branch starts from
  (`grep -n 'release/v1' .github/workflows/release.yml` finds nothing;
  `test -f docs/policies.md`). If either is absent, stop and land it first
  — this package moves the whole `[Unreleased]` body and would strand its
  entry (DEC-REL-011). Then re-measure every line number below at the branch
  head and note any that moved beside the bullet that uses it.
- Merge hazards to resolve on purpose if this branch is rebased over a
  sibling rather than started after it (DEC-REL-011): `release.yml`'s
  publish step — the sibling rewrote the `uses:` line, this package adds
  `with:` directly beneath it, keep both; `templates/spec-gate.yml` lines
  59–65 and its byte copy under `skills/` — the sibling added two comment
  sentences to the block, this package rewrites the version in it, then the
  template is copied over the asset so `test_skill_asset_matches_template`
  is green; `CHANGELOG.md` `[Unreleased]` — both siblings' entries must be
  under it before the cut; `README.md` lines 400–417 — the sibling pinned
  `actions/checkout` at 400, this package edits 415–417 now and 403 after
  the tag.
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
  `[Unreleased]` heading and its blank line, the date being the day the tag
  is intended to be pushed; if the sitting slips, the date is amended in
  the commit that gets tagged (R-REL-4, DEC-REL-002). Below it, a preamble
  blockquote: `v0.3.0` is the first tag pushed under the `planlint` name
  and the first release published to PyPI; `v0.2.0` was never tagged, and
  its section below records the version that existed in the tree from
  2026-09-12 and was installable from git by commit. Everything that was
  under `[Unreleased]` — every `###` group from the first to the last,
  verbatim and in order, the siblings' entries included — now sits under
  the new heading, so `## [Unreleased]` is empty above it (R-REL-4,
  R-REL-5, DEC-REL-001).
- `CHANGELOG.md`, the `### Deprecated` group now under `[0.3.0]`: keep the
  Python 3.10 entry as it is. Run `grep -n -i 'specgraph' CHANGELOG.md` over
  the group: if `write-down-policies` has already written the `specgraph`
  line, leave it and confirm it states the window this package states —
  warns through 0.3.x, removed in 0.4.0 — and names `docs/policies.md` as
  the rule it instantiates; if the line is absent, add it here — **the
  `specgraph` alias is removed in 0.4.0.** It warns to stderr through every
  0.3.x release and delegates with the exit code preserved; in 0.4.0 the
  entry point goes and `specgraph` is no longer installed; the waiver
  syntax, the config file name and the `[tool.specgraph]` section are
  stable identifiers and are not affected. Never both (R-REL-6,
  DEC-REL-005).
- `CHANGELOG.md`, the `[0.2.0]` preamble (lines 410–416): append one
  sentence — this section's date is the day it was folded from the earlier
  `2026-09-02` heading (PR #25), not a tag date; the `v0.2.0` tag was never
  pushed, so the "first public tag" the release-train honesty entry below
  promised became `v0.3.0`; the `[0.2.0]` link definition is kept for the
  file's one-link-per-version convention and does not resolve. Nothing
  else in the section changes — the "not the freeze" sentence at line 440
  stays as the record of what was promised (R-REL-5, DEC-REL-001).
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
  the "Not on PyPI yet" note (lines 54–59) says `v0.3.0` in place of
  `v0.2.0` and gains the interim-window sentence — between the 0.3.0 bump
  and the tag, the git install gives 0.2.0-era code, which this skill's
  `planlint-min-version` rejects; use the Action, or wait for the tag; the
  Action-section prose (lines 415–417) says `v0.3.0`; the two own-action
  `uses:` lines (403, 451) and the `git+https://…@a1b6868…` install (57)
  stay as they are until Milestone 3 (R-REL-6, R-REL-9, R-REL-13,
  DEC-REL-007).
- `templates/spec-gate.yml`: the comment block above the own-action step
  (lines 59–63 at `ea40bc2`; two sentences longer after the sibling) says
  `v0.3.0` and `@v0.3.0`; the own-action `uses:` SHA stays. Copy the file
  over `skills/planlint-spec-governance/assets/spec-gate.yml` so
  `test_skill_asset_matches_template` stays green (R-REL-9, R-REL-13,
  AC-REL-9).
- `.pre-commit-hooks.yaml`: the example's comment (lines 10–11) says
  "Until v0.3.0 is tagged … rev: v0.3.0 instead"; line 12's SHA stays
  (R-REL-9, R-REL-13).
- `.github/actions/planlint/action.yml`: line 34, the `version` input's
  description — `e.g. "0.2.0"` → `e.g. "0.3.0"`. Nothing else in the file;
  the sibling's two `uses:` lines (163, 337) are not in this diff (R-REL-13,
  DEC-REL-012, AC-REL-24).
- `docs/distribution-plan.md`: lines 15, 132 and 138 — `@v0.2.0` →
  `@v0.3.0`, so the new guard is green on this milestone; the full §3
  rewrite is Milestone 2 (R-REL-11).
- `docs/next-steps.md`: line 7's heading becomes "After the first public
  tag (0.3.0)" and line 9 names `v0.3.0` (R-REL-13).
- `.github/workflows/release.yml`: beneath the publisher's `uses:` line —
  which the sibling has already pinned to
  `pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33 # v1.14.2`;
  do not touch it — add `with:` / `attestations: true`, preceded by a
  comment: `attestations: true` is the action's default since v1.11.0 (the
  input exists since v1.10.0, where it defaulted to false), stated
  explicitly so a SHA pin cannot drop it; a pin must be at or above v1.11.0
  for this to be a no-op — against a v1.10.x pin this line is what turns
  attestations on; older than v1.10.0 produces GitHub's "Unexpected input"
  warning annotation. No other line changes; confirm `make thresholds`
  still prints PASS (R-REL-10, C-REL-2, C-REL-4, DEC-REL-006).
- `tests/test_adopter_urls.py`: add
  `test_every_copyable_tag_ref_names_the_current_version` — over
  `ADOPTER_FILES` minus `CHANGELOG`, collect every match of
  `(?<![\w/.-])@v\d+\.\d+\.\d+|ianshank/planlint\S*@v\d+\.\d+\.\d+|rev:\s*v\d+\.\d+\.\d+`
  with its file and line; assert the list is non-empty; assert each token's
  version equals `v{__version__}`, with a message listing every offender
  as `path:line token`. Add `test_a_stale_tag_ref_is_named_with_file_and_line`
  — plant a file with `@v0.2.0` under `tmp_path`, run the same collector
  against it with the current version, and assert the offender string names
  the file and line; plant a file with no tag ref and assert the presence
  check fails rather than passes; plant a file whose only tag-shaped token
  is `some/action@v7.0.1` and assert it is not collected. Write both against
  the branch head first so their red state is seen once, and record the
  offender list the first test prints here — it must equal what the grep in
  the proposal's Evidence prints at that commit — then land the edits above
  and watch them go green (R-REL-8, DEC-REL-004, AC-REL-7, AC-REL-8).
- `tests/test_cli_surface.py`: add
  `test_deprecated_alias_names_its_removal_version` beside the three alias
  tests — call `main_deprecated` on a clean fixture tree, read `capsys`
  stderr, assert it contains `0.4.0` and `0.3.x` and still contains
  "is deprecated; use `planlint`" (R-REL-7, DEC-REL-005, AC-REL-6).
- `tests/test_workflow_hardening.py`: add
  `test_publish_declares_attestations_explicitly` — read `RELEASE_YML`,
  take the `publish` block through `workflow_job_blocks`, strip comments,
  find the step whose `uses:` names `pypa/gh-action-pypi-publish`, and
  assert `attestations: true` appears under that step's `with:`. Assert
  nothing about the step's ref: it is the sibling's, and
  `test_every_reference_to_one_action_agrees_on_one_ref` and the sibling's
  pin-shape guard already hold it (R-REL-10, DEC-REL-006, DEC-REL-011,
  AC-REL-11).
- Confirm every `0.2.0` left under `tests/` is one C-REL-5 lists, and that
  the diff touches none of them (AC-REL-23, DEC-REL-010).
- Confirm the diff touches no third-party `uses:` line: `git diff --stat`
  against the branch base names `release.yml` with one hunk, and
  `git diff -U0 -- .github templates README.md | grep -E '^[-+].*uses:'`
  prints nothing (C-REL-4, AC-REL-12).
- Confirm `planlint --version` prints `planlint 0.3.0` from the editable
  install, and `make wheel-check` builds and passes (AC-REL-15).
- Re-point AC-REL-6, 7, 8 and 11 in `specs/release-readiness/spec.md` from
  stage-only verification to the four tests above, now that they exist;
  run `python -m pytest tests/test_spec_test_citations.py -q` and confirm
  every selector resolves.
- **Gate:** `make pre-pr`

## Milestone 2 — The maintainer's runbook and the recurring checklist

- `docs/distribution-plan.md` §0, as a dry run on the branch head: re-run
  every row and record the results with the branch-head SHA and the word
  "dry run"; replace the 0.2.0 framing ("The engineering side of 0.2.0 is
  done") with 0.3.0's; keep the still-true facts (`v0.1.0` at `cdc94ca`,
  nothing on PyPI) and date them. The merge commit does not exist yet, so
  its SHA is not written here; Milestone 3 re-runs the rows on it and
  records that SHA (R-REL-11).
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
  `make pre-pr` green on it — with the sentence that no test demands this
  step (`test_ci_template_pins_the_floor_the_skill_enforces` accepts both
  states), so this list is the only trigger; (9) the GitHub release created
  from the `[0.3.0]` section; (10) the Context7 submission. Exit criterion:
  M1's — the tag is published and `pip install planlint==0.3.0` runs
  `validate` on this repository. Failure mode paragraph kept: a tag without
  the publisher is a red workflow and a half-product; do (2)–(7) in one
  sitting. Add the interim-window paragraph: between the merge and the tag
  the git install reports `planlint 0.2.0` and the skill refuses it; if
  the sitting will slip, the option is one follow-up commit on `main`
  pointing the README's `git+` line at the merge SHA — a later commit can
  name the merge commit — and the tag then goes on that commit
  (DEC-REL-007).
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
  copyable tag ref; then the hand edits no test names — the SKILL.md prose
  and the `action.yml` example; then the changelog cut of DEC-REL-002 and
  the runbook in `docs/distribution-plan.md` §3 (R-REL-12, DEC-REL-004,
  DEC-REL-008, DEC-REL-012).
- `docs/hooks.md`, the CI table's `release` row: append "and uploads PEP
  740 attestations for both files" (R-REL-12).
- Confirm `make docs-check` prints its pass line: every required document
  present and linked (AC-REL-16).
- **Gate:** `make docs-check`

## Milestone 3 — Tag, publish, observe, record (the maintainer, outside the tree)

- Precondition: `pin-actions-by-sha` and `write-down-policies` are merged
  to `main`, then Milestones 1 and 2 of this package, and the merge commit's
  `make pre-pr` and CI are green. Record the merge commit's SHA here
  (R-REL-14). The release commit is that merge commit, or a follow-up on
  `main` that only sets the changelog date (DEC-REL-002) — or, if the
  interim-window option of DEC-REL-007 was taken, the follow-up that also
  points the README's `git+` line at the merge SHA.
- `docs/distribution-plan.md` §0: re-run every row on the merge commit and
  replace the branch-head dry-run results with these, recording the merge
  commit's SHA beside them; this edit rides in the post-tag commit of step
  (8) (R-REL-11).
- Run §3 steps (1)–(3) of the runbook. Record here: the `workflow_dispatch`
  run id, and that `gate` and `build` succeeded with `publish` skipped.
- Run §3 steps (4)–(5). Record here: the tag's commit SHA and the date the
  tag was pushed (which the `[0.3.0]` heading must read), the `release.yml`
  run id, the result and duration of `gate`, `build` and `publish`, and
  that the `build` job's tag-versus-package check passed (AC-REL-19,
  DEC-REL-002).
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
  (DEC-REL-004); attestations are declared on the publish step with the
  v1.11.0 floor named and verified by hand (DEC-REL-006); the three M1
  packages landed in the order pin, policies, release (DEC-REL-011).
- **Gate:** `make pre-pr`
