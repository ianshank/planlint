# Spec: Release 0.4.0

> **Change:** `prepare-release-0-4-0`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

0.4.0 is the release in which the 0.3.0 notes said the Python 3.10 floor
and the `specgraph` alias would go. `CHANGELOG.md`'s `[0.3.0]` `Deprecated`
group announces that Python 3.10 support ends in 0.4.0, with
`requires-python` moving to `>=3.11` and the `tomli` extra going. It also
announces that the `specgraph` alias is removed in 0.4.0, while the waiver
prefix, the config file and the `[tool.specgraph]` table stay.
`docs/policies.md`, "Versioning and deprecation", is the rule both follow:
announced in a 0.Y.0's notes with the removal version, working through every
0.Y.x, removable from 0.(Y+1).0 and never in a patch.

So the removals carry a precondition and a completeness problem. The
precondition is that 0.3.0 has actually shipped with 3.10 and the alias
intact: at drafting no `v0.3.0` tag is on origin and PyPI has no `planlint`.
The completeness problem is that the floor is written by hand far beyond
the facts the announcement names, and the tree binds only the classifiers
and the hooks row to the matrix. `requires-python`, mypy's `python_version`,
the README's install line and the skill's `compatibility:` field are bound
to nothing, so a bump that misses one stays green.

A further surface should go, and it was never announced: the `Dockerfile`,
its `.dockerignore` and the `docker` Dependabot entry. The image is built,
published and scanned nowhere, and `harden-ci-workflows` hardened the recipe
with guards that read the file and never build it. The repository's own
records call it a user-facing surface, though, so it gets the window like
everything else. 0.4.0 announces its deprecation, names 0.5.0 as the
removal version, and leaves the file in place through 0.4.x.

The alias removal also deletes tests that other specs cite. The citation
guard fails on a selector that names nothing, so where the removal lands
relative to `lean-production-tree` decides which specs need amending.

Finally, this is the release-prep package for 0.4.0. After the removals,
`lean-production-tree` and `harden-release-pipeline` have merged, the
mechanism 0.3.0 built runs end to end: bump one literal, regenerate the
manifests, then let the suite name every remaining hand edit, cut the
changelog and run the release through the promotion model. Pushing the tag
and publishing are the maintainer's actions outside the tree. What is
observed afterwards is recorded in `tasks.md`.

**Evidence:** measured at `4278d4c`, 2026-10-16, and re-checked at `f0063a6`
and `eb14cba` for the first and second adversarial reviews; outside the
packages each adds, these trees are `dev` at `c0ff090`. Each command and
line number is in the proposal.

- **Release state.** `git ls-remote --tags origin` lists `v0.1.0` alone, and
  the PyPI JSON API answers 404 for `planlint`. `openspec_graph.__version__`
  is `0.3.0` and `CHANGELOG.md` carries `## [0.3.0] — 2026-10-08`.
- **The floor.**
  - `pyproject.toml` declares `requires-python = ">=3.10"`, the 3.10
    classifier, a `tomli` dev-extra entry with a marker, `[tool.mypy]
    python_version = "3.10"` and a `[[tool.mypy.overrides]]` entry for
    `tomli`.
  - `.github/workflows/ci.yml`'s `test` matrix starts at `"3.10"`.
    `tests/ratchet_support.py`'s `MYPY_FIXED` and
    `test_mypy_is_strict_and_warns_on_unreachable_code` hold the `"3.10"`
    literal.
  - `tests/support.py`'s `read_pyproject` chooses `tomllib` or `tomli` by
    `sys.version_info`. That branch is the single site
    `tests/ratchet_support.py`'s `ALLOWED_VERSION_CHECK` exempts in
    `hidden_code`, with the planted cases `allowed-site` and
    `second-check-at-the-site` in `tests/test_static_ratchets_planted.py`
    (R-TDR-6 of `ratchet-test-types-and-docstrings`).
  - Ruff's `UP` family, run at a 3.11 target, names `openspec_graph/cli.py`
    (UP017, the `datetime.UTC` alias) and `tests/support.py` (UP036, that
    version block).
  - Prose and comments state the 3.10 floor as a present fact in
    `README.md`, `docs/aqa.md`, `docs/hooks.md`'s `test` row,
    `docs/policies.md`, `SKILL.md`'s `compatibility:`,
    `openspec_graph/log.py`, `openspec_graph/thresholds.py`,
    `tools/_common.py`, `tools/check_wheel_metadata.py` and a number of test
    docstrings. `docs/next-steps.md` item 7a waits for "when 3.10 leaves the
    matrix".
- **The alias.**
  - `pyproject.toml` `[project.scripts]` maps `specgraph` to
    `openspec_graph.cli:main_deprecated`, which prints
    `_DEPRECATION_WARNING` and delegates.
  - `tests/test_cli_surface.py` holds `test_entry_points_wired_in_pyproject`
    and the `test_deprecated_alias_` tests. One of them derives its expected
    window from `__version__`, so a bump to 0.4.0 with the alias still
    present turns it red.
  - `SPECGRAPH_LOG_LEVEL` is read in `openspec_graph/log.py` and
    `tools/_common.py`, and no `Deprecated` group names it.
- **The Dockerfile.**
  - Its header says the image "is not built in CI", and documents a build
    and a run for "CI sandboxes that want a hermetic, dependency-free CLI
    invocation". No workflow builds or pushes one.
  - The records treat it as user-facing. `CHANGELOG.md`'s `[0.1.0]` lists it
    under `Added`; `enterprise-hardening` DEC-EH-001 calls it "a convenience
    image for CI sandboxes"; `write-down-policies` names "the Docker
    surface".
  - No `Deprecated` group names it. The window in `docs/policies.md`
    covers interpreter versions, which the tool does not ship either.
  - Its header is read by `test_dockerfile_documents_the_user_override_for_writing_verbs`,
    which requires the `--user` override and the writing verbs to appear in
    its comment lines.
- **The citations.** `tests/test_spec_test_citations.py` resolves every
  test selector in every spec against the test function names. The alias
  tests are cited by `prepare-release-0-3-0`, `rename-cli-and-positioning`
  and `write-down-policies`. In the tree `lean-production-tree` leaves, only
  `prepare-release-0-3-0` remains, and it stays until the post-0.4.0 sweep.
  `add-witness-ci-artifacts` DEC-WCA-022 once planned a verification-line
  edit to a shipped package, `add-finding-line-hits`, and
  `lean-production-tree` DEC-LPT-007 mooted it by deleting that package.
- **The bump set.**
  - The tests `prepare-release-0-3-0` left are
    `test_skill_metadata_version_matches_the_package`,
    `test_ci_template_pins_the_floor_the_skill_enforces`,
    `test_compatibility_prose_matches_the_declared_minimum`,
    `test_every_changelog_version_links_to_its_release_tag` and
    `test_every_copyable_tag_ref_names_the_current_version`, with
    `test_skill_min_version_is_not_ahead_of_the_package`.
  - The hand edits no test names are `SKILL.md`'s "Wiring it into CI"
    sentence, the composite action's `version` example and `SECURITY.md`'s
    supported-versions sentence, which also calls `0.3.0` "the first release
    published to PyPI".
  - `.claude/skills/planlint-release/SKILL.md` gives the order.

---

## Requirements

### Ordering

- R-RFR-1: The removals — every change R-RFR-3 to R-RFR-11, R-RFR-15,
  R-RFR-16 and R-RFR-23 require — MUST NOT merge into the integration
  branch until `v0.3.0` is tagged on origin, `planlint` 0.3.0 is
  installable from PyPI and `v0.3.0^{commit}` is an ancestor of the
  integration branch. The pull request that carries them MUST stay a GitHub
  draft until those facts are recorded in `tasks.md` with their output and
  the date.
- R-RFR-2: The removals MUST merge after `lean-production-tree`'s
  implementation has merged into the integration branch: the pull request
  that makes its deletions, not the one that carried its package alone. The
  release-prep pull request of R-RFR-17 to R-RFR-20 MUST merge after the
  implementations of `lean-production-tree` and `harden-release-pipeline`,
  and the removals, have all merged. No other pull request MAY merge into the
  integration branch between it and the promotion that carries it to
  production: its squash commit is recorded in `tasks.md`, and the
  integration branch's tip MUST equal that commit when the promotion to the
  candidate branch is opened.

### The Python floor

- R-RFR-3: `requires-python` MUST read `>=3.11`. The 3.10 classifier and
  the 3.10 leg of the `test` matrix MUST leave together, so the classifiers
  still equal the hard legs, and `docs/hooks.md`'s `test` row MUST name 3.11
  as its lower bound. `[tool.mypy] python_version` MUST read `"3.11"`, as
  MUST the copy in `tests/ratchet_support.py`'s `MYPY_FIXED`.
  `test_mypy_is_strict_and_warns_on_unreachable_code` MUST compare
  `python_version` with the lower bound of `requires-python`, read from the
  file, rather than with a literal. The built wheel's `Requires-Python` MUST
  therefore exclude a 3.10 interpreter.
- R-RFR-4: The dev extra's `tomli` entry and the sentence of its comment
  that explains it MUST be removed, as MUST the `[[tool.mypy.overrides]]`
  entry for `module = "tomli"` with its comment, and the `sys.version_info`
  branch in `tests/support.py`'s `read_pyproject`. `read_pyproject` MUST
  import `tomllib` unconditionally and still return the parsed table through
  an annotated local, and its docstring MUST NOT name a 3.10 leg or R-TDR-6.
- R-RFR-5: `ALLOWED_VERSION_CHECK` MUST be deleted from
  `tests/ratchet_support.py`.
  - `hidden_code` MUST report every branch test on `sys.version_info` or
    `sys.platform` in every file under `tests/`, with no exempt path and no
    exempt scope.
  - In `tests/test_static_ratchets_planted.py`, the planted case that shows
    the exempt site passing MUST become one that shows a version branch
    inside `tests/support.py`'s `read_pyproject` reported. The planted case
    for a second check at that site MUST be deleted.
  - The comments and docstrings that describe "R-TDR-6's one" site MUST
    state that there is none. R-TDR-6 is retired by this requirement
    (DEC-RFR-002).
- R-RFR-6: A guard in `tests/test_workflow_python.py` MUST hold the
  interpreter floor to a single value across these sources:
  - the lower bound of `requires-python`;
  - the lowest hard leg of the `test` matrix;
  - the lowest `Programming Language :: Python :: 3.x` classifier;
  - `[tool.mypy] python_version`;
  - the "Python X.Y+" floor in `README.md`, read from the whole file;
  - the "Python X.Y or newer" floor in
    `skills/planlint-spec-governance/SKILL.md`, read from the whole file,
    where its only match is the `compatibility:` field.

  Every value MUST be read from its file through a reader the planted
  counterpart also calls, and never restated. Versions MUST be compared by
  their numeric parts, never as strings. A source in which no floor is
  found — an empty matrix, a `requires-python` that is not exactly
  `>=X.Y`, a prose pattern with no match or more than one — MUST fail with
  a message naming the source, never with an exception and never by being
  skipped. A disagreement MUST fail with a single message naming every
  source and its value, and the file and line for each prose source. The
  planted counterpart MUST feed planted text through the prose reader and a
  planted specifier through the `requires-python` reader (DEC-RFR-003).
- R-RFR-7: Every comment, docstring and document that states Python 3.10
  support as a present fact MUST be reworded to the 3.11 floor or to the
  past tense. That covers:
  - `README.md`, `docs/aqa.md`'s ranges, `docs/policies.md`'s Python 3.10
    instance and `SKILL.md`'s `compatibility:` field;
  - the comments and docstrings of `openspec_graph/log.py`,
    `openspec_graph/thresholds.py` (its module docstring and
    `scoped_fail_under`), `tools/_common.py`'s scanner docstrings and
    `tools/check_wheel_metadata.py`'s `_declared_license`;
  - `tests/support.py`'s `working_directory`, `tests/test_enterprise.py`'s
    stdlib-inventory comment, `tests/test_properties.py`'s module docstring,
    `tests/test_ci_workflow.py`'s mypy test docstring and
    `tests/test_static_ratchets.py`'s hidden-code test docstring.

  `docs/next-steps.md` item 7a MUST say that the floor has unblocked the
  `tomllib` parse and that the parse remains its own package. A reworded
  docstring that explains why a hand-rolled scanner is used instead of
  `tomllib` MUST say the scanner was chosen under the 3.10 floor and that
  replacing it is item 7a's change. It MUST NOT claim that `tomllib` is
  missing on a supported interpreter.
- R-RFR-8: `make lint` MUST pass with ruff's `UP` family floored at the new
  `requires-python`. Each finding it reports MUST be fixed in this change by
  the upgrade ruff names. None MAY be waived, ignored per file, or
  suppressed by a `target-version` below `requires-python`.

### The `specgraph` alias

- R-RFR-9: `[project.scripts]` MUST declare `planlint` and nothing else,
  under a comment that records the alias's removal in 0.4.0 and names the
  stable identifiers that keep the old name. `main_deprecated` and
  `_DEPRECATION_WARNING` MUST be deleted from `openspec_graph/cli.py`, and
  the comment in `main` that names a deprecated entry point MUST name only
  the `planlint` entry point.
- R-RFR-10: The tests that exercise the alias MUST be deleted with it:
  those for the warning, the delegated exit code, the clean stdout and the
  removal version.
  - The test that asserted both entry points MUST be replaced by a test
    under a new name that asserts absence. `[project.scripts]`, read
    structurally through `tests/support.py`'s `read_pyproject`, MUST have
    exactly the key `planlint`, mapped to `openspec_graph.cli:main`, and
    `openspec_graph.cli` MUST have no attribute `main_deprecated`.
  - The test that the `planlint` command emits no deprecation warning MUST
    stay unchanged.
  - Whatever the deletions leave unused in `tests/test_cli_surface.py` —
    an import, a fixture, a section header with no test under it — MUST go
    in the same commit.
- R-RFR-11: The waiver prefix `specgraph:allow`, the config file
  `openspec/specgraph.json`, the `[tool.specgraph]` table and the legacy
  `SPECGRAPH_LOG_LEVEL` variable MUST keep working unchanged. `README.md`'s
  alias paragraph and `docs/policies.md`'s `specgraph` instance MUST say, in
  the past tense, that the alias warned through every 0.3.x release and was
  removed in 0.4.0. The README paragraph MUST keep naming the stable
  identifiers.

### The Dockerfile's deprecation

- R-RFR-23: The Dockerfile's removal MUST be announced in 0.4.0 and
  performed no earlier than 0.5.0 (DEC-RFR-006).
  - `Dockerfile`'s header MUST gain a single comment line saying that the
    file is deprecated in 0.4.0 and removed in 0.5.0, and pointing at the
    changelog. That line MUST carry no install command and no `@v` or
    `rev:` tag token, so the adopter-corpus scans that read the file are
    unaffected.
  - Apart from that line, this package MUST NOT edit `Dockerfile`,
    `.dockerignore`, the `docker` entry of `.github/dependabot.yml`, or any
    test or helper that reads them, and every test that reads the header
    MUST stay green.
  - `docs/next-steps.md` item 9 MUST record the window — deprecated in
    0.4.0, removed in 0.5.0 — with the reason, the delivery paths
    (`pip install` and the composite action) and the trigger that would
    reopen a published image.

### Release notes and the open packages

- R-RFR-15: `CHANGELOG.md`'s `[Unreleased]` section MUST gain two groups
  for this change, beside any group a sibling wrote. Their entries MUST be
  led by this package's bold backticked name, as the file's entries are.
  - A group headed `### Removed`, with an em dash and the removals' names,
    MUST say that Python 3.10 support is gone — `requires-python` is
    `>=3.11`, the 3.10 classifier and matrix leg, the `tomli` dev extra and
    its mypy override are removed, mypy checks against 3.11 — and that the
    `specgraph` command is gone, so users run `planlint`, while the waiver
    prefix, the config file, the `[tool.specgraph]` table and
    `SPECGRAPH_LOG_LEVEL` are unchanged. Both were announced in the 0.3.0
    notes.
  - A group headed `### Deprecated` MUST announce that `Dockerfile`,
    `.dockerignore` and the `docker` Dependabot entry are removed in 0.5.0,
    that they are unchanged through every 0.4.x release, and that
    `pip install planlint` in any `python` image, or the composite action,
    replaces them.
- R-RFR-16: A spec under `openspec/changes/` other than this package's that
  cites, on any line, a test this change deletes or renames MUST be amended
  in place at that citation's verification line and nothing else, in the
  commit that deletes or renames the test.
  - At drafting this means AC-REL-5's and AC-REL-6's verification lines in
    `prepare-release-0-3-0`. Those edits supersede, for these two lines
    only, `lean-production-tree` DEC-LPT-004's rule that no change edits a
    shipped package's text (DEC-RFR-007).
  - Each amended line MUST carry exactly this marker: "(amended by
    `prepare-release-0-4-0`, superseding DEC-LPT-004 for this line only:
    0.4.0 removed the `specgraph` alias and deleted the tests of it that
    this line cited; the original line is read at the `v0.3.0` tag)". The
    marker names what was deleted, never every test the criterion cited:
    AC-REL-5's surviving selector stays.
  - If the citation measure, re-run at the implementation branch's head,
    names any other spec, implementation MUST stop and this package MUST be
    revised before the alias is deleted. The revision is a new, named
    supersession if that spec's package has shipped, or an in-place
    amendment of the DEC-LPT-007 kind if it is open. This requirement
    authorises no other amendment as written.
  - `tests/test_spec_test_citations.py` decides which citation no longer
    resolves. A citation MUST be re-pointed to a surviving test that
    verifies the same clause, or reduced to its stage. It MUST never be
    kept resolving by a test kept or renamed for that purpose.
  - An amended criterion in a shipped package keeps its tick and its text.

### The 0.4.0 release

- R-RFR-17: `openspec_graph/__init__.py` MUST read `__version__ = "0.4.0"`
  and remain the only version literal in code.
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` MUST be
  regenerated by `make skill-manifests`, MUST be fresh under the generator's
  `--check` mode, and MUST never be edited by hand.
- R-RFR-18: The planlint version in `SKILL.md`'s `compatibility:` field,
  `metadata.version` and `metadata.planlint-min-version` MUST equal
  `__version__`, held by the tests that already bind them. The "Wiring it
  into CI" prose MUST say to pin `@v0.4.0`.
- R-RFR-19: Every copyable tag reference in the adopter corpus other than
  `CHANGELOG.md` MUST equal `v0.4.0`, held by the guard
  `prepare-release-0-3-0` added. The template and its byte copy under
  `skills/` MUST stay byte-identical. The `version` input's example in
  `.github/actions/planlint/action.yml` MUST name `"0.4.0"`, with the input
  set unchanged.
  - `SECURITY.md`'s supported-versions sentence MUST name 0.4.0 as the
    latest released version and the only supported version.
  - It MUST be reworded so it stays true after the bump: it no longer calls
    the supported version "the first release published to PyPI", which
    stays a fact about 0.3.0.
  - Its verification commands keep the version placeholders
    `harden-release-pipeline` requires there. That package's R-HRP-16
    scopes the placeholder rule to "Its commands", so both rules hold
    (DEC-RFR-011).
- R-RFR-20: `CHANGELOG.md` MUST gain `## [0.4.0] — <date>` in the file's
  em-dash form, the date being the day the tag is pushed.
  - Every line under `## [Unreleased]` at the release-prep commit, every
    sibling's group included, MUST move under it verbatim, keeping its `###`
    groupings and order.
  - An empty `## [Unreleased]` MUST stay at the top.
  - The link definitions MUST gain
    `[0.4.0]: https://github.com/ianshank/planlint/releases/tag/v0.4.0`, and
    the `[Unreleased]:` line MUST compare from `v0.4.0`.
  - No released section MAY change.
  - If the tag is not pushed on the date written, the date MUST be corrected
    by a new release-prep pull request and a new promotion, never by a
    commit on production (DEC-RFR-009).
- R-RFR-21: The release MUST follow `.claude/skills/planlint-release/SKILL.md`
  and `docs/hooks.md`, "Releasing":
  - The release-prep pull request is squash-merged into the integration
    branch with `make pre-pr` exiting 0 on its head.
  - It is promoted to the candidate branch and then to production, each by
    merge commit, once the route check passes and the required checks have
    finished green.
  - A `workflow_dispatch` dry run of `release.yml` runs on the production
    merge commit, with its gate and build green.
  - `tools/check_promotion.py tag-ancestry` passes on that commit.
  - `v0.4.0` is pushed on it by a person or an App token.

  The production merge commit's first parent MUST be production's previous
  tip, which is `v0.3.0^{commit}` unless a hotfix release followed it, and
  its tree MUST equal the candidate branch's. Nothing MAY be committed to
  production after the tag.
- R-RFR-22: The post-tag observations MUST be recorded in this package's
  `tasks.md` with run ids, shas and dates, in a later pull request into the
  integration branch, and MUST NOT be claimed before they are observed:
  - the release run and the result of every job it defines;
  - the attestations on the published wheel and sdist, verified as the
    runbook says: the PEP 740 publish attestations through PyPI's Integrity
    API and `pypi-attestations`, and any build provenance
    `harden-release-pipeline` added, through the command it names;
  - the GitHub Release and its assets;
  - that the tagged tree carries none of the paths the squash commit of
    `lean-production-tree`'s implementation deleted, the list being derived from that commit's diff
    against its first parent rather than from a pattern;
  - a fresh-venv install of `planlint==0.4.0` that prints `planlint 0.4.0`,
    installs no `specgraph` script, and exits 0 from `validate --fail-on
    ERROR` on this repository;
  - an install of `planlint==0.4.0` for a 3.10 interpreter, refused.

### Constraints

- C-RFR-1: No hand-rolled TOML scanner MAY be replaced by `tomllib`: not
  `openspec_graph/thresholds.py`'s, the readers in `tools/_common.py`, or
  `tools/check_wheel_metadata.py`'s. No code MAY change for the floor except
  where a branch can no longer run (R-RFR-4) or ruff's `UP` family names an
  upgrade (R-RFR-8). The dialect card, the findings envelope and every
  golden hash MUST be byte-identical.
- C-RFR-2: These MUST be unchanged: the `RULES` tuple, the README rules
  table, `tests/baseline_rules.json`, every `make` target's recipe, every
  workflow job name, the composite action's inputs and defaults, every
  workflow's `PYTHON_DEFAULT` and the CLI's verb set.
- C-RFR-3: No runtime or dev dependency MAY be added, `[project]
  dependencies` MUST stay empty, and no script MAY be added under `tools/`.
- C-RFR-4: No released `CHANGELOG.md` section MAY change. The `[0.3.0]`
  `Deprecated` group stays as written.
- C-RFR-5: These MUST NOT be edited: the planted fixtures that spell `3.10`
  or `tomli` as test data, in `tests/test_workflow_python.py`,
  `tests/test_ci_workflow.py` and `tests/test_static_ratchets_planted.py`'s
  derived and marker cases; the dated measurement in the comment above
  `pyproject.toml`'s `tools/` coverage floors; comments that attribute a
  fact to its origin; and the old name in `.pre-commit-config.yaml`'s
  contributor hook ids.
- C-RFR-6: Pushing the tag, publishing, the dry run and every GitHub or
  PyPI setting are the maintainer's actions outside the tree. Nothing in
  this package performs them, and no criterion claims one before it is
  observed and recorded.

---

## Decisions

- **DEC-RFR-001** (amended after the first adversarial review, HIGH-1 and
  LOW)**:** the ordering gates, each for its own reason.
  - **First: after `v0.3.0` is published.** This is the window itself.
    0.3.0's notes and `docs/policies.md` make 0.3.0 the release that still
    runs on 3.10 and still installs `specgraph`. The integration branch
    promotes to the candidate branch and then to production, so a removal
    merged before the tag would sit in the tree the 0.3.0 tag is cut from.
    No criterion can observe a release before it exists, so the draft state
    is what holds the merge back, as `lean-production-tree` DEC-LPT-017 does.
    The gate is a set of facts: the tag on origin, the release on PyPI and
    its ancestry.
  - **Second: after `lean-production-tree`.** This is the citation guard.
    Every test selector in every spec must name a substring of a real test
    function. In today's tree the alias tests are cited by
    `rename-cli-and-positioning` and `write-down-policies` as well as by
    `prepare-release-0-3-0`, and `lean-production-tree` deletes the first
    two. Amending them first would edit records that leave the tree in the
    same release. Landing afterwards, only `prepare-release-0-3-0` needs a
    verification-line amendment (DEC-RFR-007).
  - **Third: the release-prep pull request last.** The changelog cut moves
    the whole `[Unreleased]` body, so every sibling's entry must already be
    there (`prepare-release-0-3-0` DEC-REL-011). The copyable-tag guard
    globs `docs/**/*.md`, and until `lean-production-tree` lands that corpus
    holds dated plans spelling `@v0.3.0`. The alias's removal-version test
    derives its window from `__version__`, so the bump turns it red while
    the alias exists; removing the alias first keeps the bump a single
    literal. And the 0.4.0 observations verify what
    `harden-release-pipeline` adds to the pipeline.
  - **Nothing merges in between.** "No other pull request merges" is
    enforced by a recorded fact: the release-prep squash commit is
    recorded, and the integration branch's tip is compared with it before
    the promotion opens, so a stray merge is caught before it is promoted.

  Rejected:
  - Combining the removals and the release prep in one pull request: the
    removals would wait on the pipeline package for no reason, and the
    bump's review would carry a deletion set.
  - Removals before `lean-production-tree`: the second gate above.
  - A release-prep pull request that edits a sibling's files: the merge
    hazards are named in `tasks.md` instead.

- **DEC-RFR-002:** R-TDR-6 is retired, and `ALLOWED_VERSION_CHECK` is
  deleted rather than kept.
  - **What R-TDR-6 required.** `read_pyproject` chose `tomllib` or `tomli`
    by `sys.version_info`, which mypy reads, so that mypy's verdict was the
    same on the leg that installs `tomli` and on the legs that do not. The
    allowance was that requirement's exemption from DEC-TDR-016's
    hidden-code scan.
  - **Why it is dead.** With `requires-python` at `>=3.11` the branch's
    else arm cannot run, ruff reports it as UP036, and R-RFR-4 deletes it.
  - **Why the allowance goes too.** Kept, it would exempt a site where no
    check remains, and a future version branch in `read_pyproject` would
    pass the scanner unannounced. That is the hidden-code shape the scan
    exists to report. Deleting it makes the scan strictly tighter: every
    version or platform branch under `tests/` is reported, and the planted
    case that proved the exemption flips to prove its absence.
  - **Why the `tomli` override goes.** It existed so the import's verdict
    held when the module was not installed, and the import is gone.

  Rejected:
  - Keeping the allowance for the next floor bump: a branch the floor makes
    dead is deleted at that bump, not authorised in advance.
  - Rewriting R-TDR-6 in its own package: that package is shipped and
    leaves with `lean-production-tree`. The retirement is recorded here,
    and the requirement is read at
    `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/ratchet-test-types-and-docstrings/specs/static-check-ratchets/spec.md`.

- **DEC-RFR-003** (amended after the first adversarial review, MEDIUM-3, and
  the second, LOW-8)**:** a single guard for the floor, whose readers are
  themselves planted.
  - **The gap.** The announcement named `requires-python`, the `tomli` extra
    and the matrix, but the tree spells the floor in more places, and only
    the classifiers and the hooks row are bound to the matrix.
    `requires-python`, mypy's `python_version`, the README's install line
    and the skill's `compatibility:` floor are bound to nothing. At the
    next floor bump any of them could be missed with the suite green. That
    is the drift the bump-set guard closed for the package version
    (DEC-REL-004).
  - **The guard.** A single test reads every source and asserts a single
    value. It sits beside the classifier and hooks-row guards in
    `tests/test_workflow_python.py`, which already reads the matrix and the
    classifiers.
  - **Its readers are what the planted test exercises.** The prose
    sources go through one reader that takes the text, the pattern and the
    source's name, and `requires-python` goes through one reader of the
    specifier. The planted test feeds planted text and a planted specifier
    to those same readers. Planting already-parsed values would test the
    comparison and leave every reader untested.
  - **Whole files, exactly one match.** Each prose reader reads the whole
    file. The skill's file holds its "Python X.Y or newer" floor once, in
    the `compatibility:` field, so no frontmatter parser is needed and a
    second copy of the sentence anywhere in the file fails the guard.
  - **Numbers, not strings.** Versions compare by their numeric parts. As
    strings, `"3.10"` sorts below `"3.9"`, so a stray 3.9 leg would hide
    from the minimum. An empty matrix fails with a message naming the
    matrix, never with the `ValueError` a bare `min` raises.
  - **Red first, the only way it can be.** On the unedited tree every
    source reads 3.10, so the guard is green there. It is written green at
    3.10, then seen red with `requires-python` bumped alone, then green
    with every source bumped.
  - **What it leaves out.** `docs/aqa.md`'s ranges are read in review rather
    than parsed. They are ranges inside sentences whose wording varies, and
    the range the CI table states already has its own guard.

  Rejected:
  - A generator for the prose floors: a single number in the README's and
    the skill's prose does not justify one.
  - Asserting a literal `"3.11"`: that is a second copy of the floor, which
    the next bump would have to edit.

- **DEC-RFR-004:** code changes only where the floor kills a branch or lint
  asks for an upgrade.
  - **The temptation.** Raising a floor invites modernisation: `tomllib` in
    the scanners, `contextlib.chdir`, `logging.getLevelNamesMapping`. Each is
    a behaviour change.
  - **Why the scanners stay.** The ones that matter most carry contracts.
    The hand-rolled TOML scanners are why the dialect card is byte-identical
    across interpreters (DEC-TC-002), and `docs/next-steps.md` item 7a is
    the package that must re-prove that under `tomllib`.
  - **What this change does.** It is the removal the notes announced. It
    deletes the branches the floor kills (R-RFR-4) and applies what ruff's
    `UP` family reports (R-RFR-8): at drafting, the behaviour-identical
    `datetime.UTC` alias and the version block R-RFR-4 deletes anyway. It
    also rewords every sentence that claims 3.10 support, and rewords item
    7a to "now unblocked", so the reason it waited is visibly gone.

  Rejected:
  - The `tomllib` swap here: it is item 7a's own package, with its own
    tests.
  - Leaving the stale docstrings: a comment claiming `tomllib` is missing
    on a supported interpreter is a false reason a reviewer would trust.

- **DEC-RFR-005:** the alias goes, a single test flips, and the identifiers
  stay.
  - **The removal.** The 0.3.0 notes, and the warning itself, named 0.4.0.
    The entry point, `main_deprecated` and the warning leave together: a
    function with no entry point is dead code, and a public import nobody
    installs.
  - **The tests.** The tests that exercise the alias go. The entry-point
    test flips to the non-success direction — the command is absent —
    under a new name. A test that kept its name while asserting the
    opposite would be an old name surviving as an alias for an assertion
    it contradicts, which `add-witness-ci-artifacts`' Milestone 5 rule
    forbids. It reads `[project.scripts]` structurally rather than grepping
    text, so a reformatted line cannot hide an entry. The primary-command
    test stays: `planlint` must still not warn about itself.
  - **The identifiers that stay.** The waiver prefix, the config file and
    `[tool.specgraph]` are contract identifiers in adopters' repositories
    (`rename-cli-and-positioning` C-CP-1). The 0.3.0 `Deprecated` entry
    says the removal does not affect them.
  - **`SPECGRAPH_LOG_LEVEL`.** It is a legacy name too, but it was never
    announced, and `docs/policies.md` forbids an unnamed window. Removing
    it now would break the rule this release exists to honour. Announcing
    it is a decision for a later minor. The same reading of the policy —
    the surface list illustrates what a user relies on, it does not close
    the set — is what DEC-RFR-006 applies to the Dockerfile.

- **DEC-RFR-006** (rewritten after the first adversarial review, HIGH-1;
  amended after the second, MEDIUM-1 and LOW-4)**:** the Dockerfile is
  deprecated in 0.4.0 and removed in 0.5.0. It is not removed here.
  - **Why the window applies.** The first draft argued that the policy
    protects only what the tool ships. The policy's own list disproves
    that: it includes an interpreter version, which the tool does not ship
    either. Shipping is not the test; reliance is. The repository's records
    call the Dockerfile something users rely on. `CHANGELOG.md`'s `[0.1.0]`
    lists it under `Added`. Its header documents a build and a run for CI
    sandboxes. DEC-EH-001 calls it "a convenience image for CI sandboxes".
    `write-down-policies` names "the Docker surface". And DEC-RFR-005 reads
    the list as open when it keeps `SPECGRAPH_LOG_LEVEL`; reading it as
    closed here would apply one policy two ways in one package.
  - **Why it still goes, in 0.5.0.** The reasons for removal stand. It is
    built, published and scanned nowhere. Its hardening (`harden-ci-workflows`
    R-HCW-13, R-HCW-14) is asserted by guards that read the file and never
    build it, and AC-HCW-18 records that even the manual build was not run.
    Keeping a container to 2026 practice would mean a CI build, a registry
    push under `packages: write`, an attestation by digest, base-image CVE
    triage and a second supported artifact in `SECURITY.md` — a second
    product for a stdlib CLI that installs with a single `pip` line in any
    `python` image.
  - **The window's substance, by the policy's own scope.** The policy's
    stderr clause applies "where it is something the tool runs", and
    planlint runs neither the Dockerfile nor the image built from it: the
    image runs planlint. So the applicable minimum is the form the policy
    gives for an interpreter version: a named removal version and a full
    minor series of notice. It is recorded in three places: the
    `### Deprecated` entry in the 0.4.0 notes, a single comment line in the
    Dockerfile's header where a builder reads, and `docs/next-steps.md`
    item 9.
  - **The header line is safe for the tests.** The header is read by
    `test_dockerfile_documents_the_user_override_for_writing_verbs`, which
    joins every comment line and requires the `--user` override and the
    writing verbs to be present. A new line removes neither, so the test
    stays green. The other Dockerfile readers see only code lines (`FROM`,
    `USER`, `COPY`). The adopter-corpus scans read the file too, and the
    line carries no install command and no tag token.
  - **The cost of waiting.** The file stays through 0.4.x, and Dependabot
    keeps moving a digest that no gate builds. Because the `docker` entry
    stays as long as the file does, the "dependency file not found" window
    a Dependabot entry without its file would open does not arise in 0.4.0.
  - **What the 0.5.0 package must do.** R-RFR-12 to R-RFR-14 and AC-RFR-13
    to AC-RFR-15 of the first draft are withdrawn from this package, and
    their numbers are not reused. A 0.5.0 package carries the removal:
    - delete `Dockerfile`, `.dockerignore` and the `docker` Dependabot entry,
      with its `target-branch` and the header sentence naming it, in one
      commit, so Dependabot never watches a missing file;
    - delete the tests and helpers that read them: the build-context tests
      in `tests/test_release_surface.py`, the Dockerfile and docker-watch
      guards in `tests/test_workflow_pins.py` (keeping `_dependabot_entries`
      and its parser test), and `DOCKERFILE`, `WRITING_VERBS` and
      `_dockerfile_from` in `tests/workflow_support.py`;
    - drop `import re` from `tests/workflow_support.py` only if nothing else
      in the module uses it, because this package adds
      `requires_python_floor` there;
    - drop the Dockerfile source from the default-Python agreement test,
      renaming it so its name no longer names the image;
    - drop `"Dockerfile"` from `tests/test_adopter_urls.py`'s globs;
    - reword the prose: `docs/aqa.md`, `docs/hooks.md`'s posture paragraph,
      `.claude/agents/planlint-verifier.md` and `.gitignore`;
    - amend any open spec that still cites a deleted test;
    - record that it supersedes R-HCW-13, R-HCW-14, C-HCW-5, R-HCW-9's
      Dockerfile clause and DEC-EH-001's runner, by archive URL.

    The inventory measured for that package is in this package's proposal.
  - **Not extended.** `docs/policies.md`'s list of instances illustrates
    the rule and states its own count, so it is not extended here. The
    notes and item 9 carry this window.

  Rejected:
  - An entrypoint wrapper that warns on stderr before handing over to
    planlint, for instance `sh -c 'echo … >&2; exec planlint "$@"'`. It
    would leave stdout and the exit code unchanged, but it is runtime code
    that no gate builds or runs: C-HCW-5 keeps the image unbuilt in CI, and
    AC-HCW-18 records that even the manual build was not run, so its warning
    would be unverified. It would also change more than the single header
    line R-RFR-23 allows.

- **DEC-RFR-007** (rewritten after the first adversarial review, MEDIUM-1;
  amended after the second, MEDIUM-3, LOW-1 and LOW-8; supersedes, for these
  two verification lines only, `lean-production-tree` DEC-LPT-004's rule
  that no change edits a shipped package's text):
  `prepare-release-0-3-0`'s AC-REL-5 and AC-REL-6 lose their alias
  selectors.
  - **What DEC-LPT-004 protects.** A shipped package is kept exactly as it
    shipped. The record is `CHANGELOG.md` and the archive tag, and an edit
    would make the tag and the tree disagree about what shipped.
  - **Why these two lines cannot stay.** The citation guard reads the tree,
    not the tag. Once the alias tests are deleted, AC-REL-5's and AC-REL-6's
    selectors name nothing and the guard fails every merge.
  - **Why no honest rename exists.** Keeping a test whose name the old
    token matches as a substring would make the token resolve while the
    test asserts the opposite of what the criterion says.
  - **The precedent, planned and mooted.** `add-witness-ci-artifacts`
    DEC-WCA-022 planned this kind of edit: in the commit that replaced a
    test, re-point the verification citation of AC-GA-29 in
    `add-finding-line-hits`, a package that shipped in 0.2.0.
    `lean-production-tree` DEC-LPT-007 then mooted that edit by deleting the
    package it would have touched, so it was never carried out. DEC-WCA-022
    is the planned precedent this decision follows. DEC-LPT-004 has since
    made the no-edit rule explicit, so the edit is recorded as a narrow
    supersession of that rule, not as a silent application of the
    precedent.
  - **Why the package cannot leave early.** `lean-production-tree` could
    moot DEC-WCA-022's edit because it deleted the target in a deletion it
    was entitled to make. Here, deleting `prepare-release-0-3-0` before
    0.4.0 would be off-cycle: the cumulative sweep is a post-release step
    (DEC-LPT-012), the 0.3.0 package's sweep comes after this release, and
    this package does not schedule it. The target is still in the tree
    when the alias tests go.
  - **What still holds the original.** The `v0.3.0` tag and
    `archive/dev-record-2026-10` keep the original text byte for byte.
  - **The smallest edit.** Only the two verification lines change, each
    carrying R-RFR-16's exact marker, with the criterion text, its tick and
    every other line of the package unchanged. AC-REL-5 keeps its surviving
    selector, the primary-command test, which is why the marker names what
    was deleted rather than saying the criterion's tests are gone. AC-REL-6
    reduces to its stage.
  - **No other package is touched.** With the Dockerfile staying
    (DEC-RFR-006), `lean-production-tree`'s R-LPT-7 and AC-LPT-11 still hold
    as written. If the citation measure re-run at the implementation head
    names any further spec, implementation stops and this package is
    revised first (R-RFR-16). That revision carries a new named
    supersession for a shipped package, or a DEC-LPT-007-style amendment
    for an open one, rather than the edit going in under this decision.

  Rejected:
  - Running the sweep early so `prepare-release-0-3-0` leaves first: the
    off-cycle deletion above.
  - Leaving the citations red: a red citation guard blocks every merge.

- **DEC-RFR-008** (amended after the first adversarial review, HIGH-1)**:**
  the notes.
  - **The groups.** This package writes a `Removed` group, for the removals
    the 0.3.0 notes announced, and a `Deprecated` group, for the
    Dockerfile. The file groups by subject under repeated heading kinds —
    `### Added — …` recurs within a single release — so a `Removed` group
    beside `lean-production-tree`'s reads as the file already reads. The
    `Deprecated` group follows the `[0.3.0]` form, and the cut carries it
    into `[0.4.0]`, where the 0.5.0 package reads its window.
  - **The 0.3.0 entries.** The `[0.3.0]` `Deprecated` entries stay: they
    are the announcement this release executes (C-RFR-4).

- **DEC-RFR-009:** the cut.
  - **The rules.** These are DEC-REL-002's, restated here because
    `prepare-release-0-3-0` leaves the tree in the sweep after this
    release. Keep a Changelog in the file's em-dash spelling. The date is
    the day the tag is pushed. The body moves verbatim. An empty
    `[Unreleased]` stays, with its compare line.
  - **A slipped date.** Under the promotion model the release-prep commit
    is promoted rather than tagged directly (`adopt-branch-promotion-model`
    DEC-BPM-020, and the runbook's move in DEC-LPT-006). A slipped date
    therefore means a new release-prep pull request and a new promotion,
    never an amend and never a commit on production.
  - **No preamble.** 0.3.0's preamble explained a release history that no
    longer needs explaining, so none is required.
  - **No count.** Nothing is counted: whatever sits under `[Unreleased]` at
    the release-prep commit moves, the siblings' groups included.

- **DEC-RFR-010** (amended after the first adversarial review, MEDIUM-2, and
  the second, MEDIUM-2)**:** how each criterion is verified.
  - **The stages.** Verification lines cite `make test` or `make pre-pr`
    and nothing else. `make test` runs every guard. `make pre-pr` is the
    ladder `release.yml`'s gate runs by name, so citing it adds no stage
    that nobody runs (DEC-REL-009, DEC-HCW-013). The validate target is not
    cited: on the lean tree no workflow invokes it by name (DEC-LPT-018).
  - **The selectors.** Tests that exist at drafting are cited by selector.
    The new floor guard, its planted twin and the flipped entry-point test
    are cited by stage until they exist, and `tasks.md` adds their
    selectors in the implementation commit.
  - **After the tag.** Criteria observable only after the tag cite
    `make pre-pr`, name the observation, and stay unchecked until it is
    recorded in `tasks.md` under its run id.
  - **The 3.10 refusal.** It needs no 3.10 interpreter. pip resolves for a
    target interpreter with `--python-version`, and `pip download` refuses a
    wheel whose `Requires-Python` excludes it. The review measured that
    `pip install --dry-run` with `--python-version` exits 0 for the same
    wheel on pip 24.0 and 24.1, and refuses only from 24.2, so the recipe is
    `pip download`, which refuses on 24.0 and later. The refusal must say
    "requires a different Python", and a 3.11 control must succeed, so the
    refusal is shown to come from the requirement and nothing else. Each
    output is recorded with the pip version that produced it.
  - **The tagged tree, by list rather than pattern.** Whether `v0.4.0`
    still carries a path `lean-production-tree` deleted is checked against
    the list its implementation's squash commit deleted — its diff against its
    first parent, the integration branch just before it merged — and not
    against a pattern. A pattern cannot see every deleted plan, the
    retired skill or the deleted package directories. The Dockerfile is not
    on that list, which is right: it stays until 0.5.0.

- **DEC-RFR-011** (amended after the first adversarial review, LOW, and the
  second, LOW-6)**:** `SECURITY.md` after 0.4.0.
  - **No new policy.** "Only the latest released version is supported"
    already holds, so 0.3.x gets nothing once 0.4.0 is out.
  - **Only the version moves, truthfully.** `harden-release-pipeline`
    rewrites the file's scope and response policy. This package touches
    only the supported-versions sentence, in the release-prep pull request,
    after that package has merged. The sentence currently calls the
    supported version "the first release published to PyPI", which is true
    of 0.3.0 and false of 0.4.0, so it is reworded and the clause keeps its
    fact about 0.3.0.
  - **No clash with the placeholder rule, on one reading.**
    `harden-release-pipeline` requires version placeholders in
    `SECURITY.md`, and this decision relies on its R-HRP-16 scoping that
    rule to "Its commands": the supported-versions sentence names 0.4.0,
    and the commands keep their placeholders. `harden-release-pipeline`'s
    implementation must confirm that its AC-HRP-20 takes the same scoped
    reading. `tasks.md` Milestone 0 checks it before the removals leave
    draft, and Milestone 5 before the sentence is edited.

---

## Acceptance Criteria

- [ ] **AC-RFR-1:** `requires-python` reads `>=3.11`, the classifiers equal
  the hard matrix legs with 3.10 in neither, and `docs/hooks.md`'s `test`
  row names the lowest and highest hard legs. The first clause is read
  directly until the floor guard of AC-RFR-5 holds it. (R-RFR-3)
  _Verified by:_ `pytest -k "test_classifiers_equal_the_hard_matrix_legs or test_hooks_test_row_names_the_matrix_bounds"` · stage: `make test`

- [ ] **AC-RFR-2:** mypy is strict with `warn_unreachable` and checks
  against the lower bound of `requires-python`, read from the file rather
  than compared with a literal; the ratchet's fixed mypy values carry the
  same version. (R-RFR-3)
  _Verified by:_ `pytest -k test_mypy_is_strict_and_warns_on_unreachable_code` · stage: `make test`

- [ ] **AC-RFR-3:** the dev extra still floors mypy and pins nothing; it has
  no `tomli` entry, no `[[tool.mypy.overrides]]` entry names `tomli`, and
  `read_pyproject` imports `tomllib` with no version branch. The cited test
  holds the first clause only; the `tomli` entry, the override and the
  import are read directly. (R-RFR-4)
  _Verified by:_ `pytest -k test_the_dev_extra_floors_mypy_and_pins_nothing` · stage: `make test`

- [ ] **AC-RFR-4 (non-success):** no branch test on `sys.version_info` or
  `sys.platform` survives anywhere under `tests/`, `ALLOWED_VERSION_CHECK`
  no longer exists, and a planted version branch inside `read_pyproject` in
  `tests/support.py` is reported rather than exempted. (R-RFR-5,
  DEC-RFR-002)
  _Verified by:_ `pytest -k "test_no_stub_name_or_condition_hides_code_from_mypy or test_a_planted_ratchet_violation_is_named"` · stage: `make test`

- [ ] **AC-RFR-5:** the lower bound of `requires-python`, the lowest hard
  matrix leg, the lowest version classifier, `[tool.mypy] python_version`,
  the README's floor and the skill's floor — each prose floor read from its
  whole file, with exactly one match — all name the same version, each read
  from its file and compared numerically. The guard was seen green at
  3.10, red with `requires-python` bumped alone, and green with every
  source bumped, each recorded in `tasks.md`. The guard is written with
  this change; until it exists the stage is the citation, and `tasks.md`
  adds its selector. (R-RFR-6, DEC-RFR-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-RFR-6 (non-success):** each of these fails the floor guard with
  a message naming the source, and none raises an exception:
  - planted README text still saying "Python 3.10+", read through the prose
    reader beside a `requires-python` of `>=3.11`, which names the file,
    the line and both values;
  - planted text with no match, or with two;
  - a planted `requires-python` of `~=3.11`, which the specifier reader
    reports as "no floor";
  - a planted matrix with a 3.9 leg, whose numeric minimum is 3.9, not
    3.10;
  - a planted empty matrix.

  The test is written with this change; until it exists the stage is the
  citation. (R-RFR-6, DEC-RFR-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-RFR-7:** `make lint` passes with ruff's `UP` family floored at
  the new `requires-python`. Every finding ruff reported at the new floor is
  fixed by the upgrade it named — at drafting the `datetime.UTC` alias in
  `openspec_graph/cli.py` and the version block R-RFR-4 deletes — and no
  ignore, waiver or `target-version` override is added, which is read from
  the diff. (R-RFR-8, C-RFR-1, DEC-RFR-004)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-8:** no comment, docstring or document outside released
  history states 3.10 support as present: `README.md`, `docs/aqa.md`,
  `docs/policies.md`, the skill's `compatibility:`, the docstrings R-RFR-7
  lists, and `docs/next-steps.md` item 7a, which says the `tomllib` parse is
  now unblocked and remains its own package. No hand-rolled scanner was
  replaced, and every required document is still present and linked. The
  prose is read directly. (R-RFR-7, C-RFR-1, DEC-RFR-004)
  _Verified by:_ `pytest -k test_docs_check_passes` · stage: `make pre-pr`

- [ ] **AC-RFR-9 (non-success):** the wheel built from the removals' head
  declares `Requires-Python: >=3.11`. `pip download` of it for a 3.10
  interpreter is refused with output containing "requires a different
  Python", while the same command for 3.11 succeeds — observed at
  implementation and recorded in `tasks.md` with each output and the pip
  version. (R-RFR-3, DEC-RFR-010)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-10 (non-success):** the `specgraph` command is absent.
  `[project.scripts]`, read structurally, has exactly the key `planlint`;
  `openspec_graph.cli` has no `main_deprecated`; and the wheel built from
  the removals' head declares `planlint` as its only console script, which
  is observed and recorded in `tasks.md`. The flipped test is written with
  this change; until it exists the stage is the citation. (R-RFR-9,
  R-RFR-10, DEC-RFR-005)
  _Verified by:_ stage: `make test`

- [ ] **AC-RFR-11:** `planlint` still runs, still emits no deprecation
  warning on its own path, and its verb set is still exactly the
  allow-list; nothing the alias deletions left unused remains in
  `tests/test_cli_surface.py`, which `make lint` and the diff show.
  (R-RFR-10, C-RFR-2)
  _Verified by:_ `pytest -k "test_primary_command_emits_no_deprecation_warning or test_planlint_module_runs or test_cli_verbs_are_exactly_the_allow_list"` · stage: `make test`

- [ ] **AC-RFR-12:** the stable identifiers survive the alias: a
  `specgraph:allow` waiver is still read, `init` still writes
  `openspec/specgraph.json`, `[tool.specgraph]` is still where the
  dead-code confidence is read, and `SPECGRAPH_LOG_LEVEL` still turns on
  debug logging. (R-RFR-11, DEC-RFR-005)
  _Verified by:_ `pytest -k "test_waivers_format_json_emits_parseable_json or test_cli_init_writes_config_and_project or test_the_confidence_lives_only_in_the_specgraph_table or test_verbose_via_env_var"` · stage: `make test`

- [ ] **AC-RFR-16:** `README.md`'s alias paragraph and `docs/policies.md`'s
  instances read in the past tense, with the stable identifiers named.
  `docs/next-steps.md` item 9 records the Dockerfile's window — deprecated
  in 0.4.0, removed in 0.5.0 — with the reason, the delivery paths and the
  reopen trigger. Every backticked path in the agent and skill prose
  resolves, and the docs gate and the CI-table guard pass. The prose is
  read directly. (R-RFR-11, R-RFR-23, DEC-RFR-006)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_path_like_backtick_references_resolve_to_real_files or test_hooks_ci_table_lists_every_ci_job"` · stage: `make pre-pr`

- [ ] **AC-RFR-17:** `CHANGELOG.md`'s `[Unreleased]` carries this package's
  `Removed` group, with an entry for Python 3.10 and one for the
  `specgraph` command, and its `Deprecated` group naming 0.5.0 as the
  Dockerfile's removal version. No released section — the `[0.3.0]`
  `Deprecated` group included — differs from the branch base. Read directly
  from the file and the diff. (R-RFR-15, C-RFR-4, DEC-RFR-008)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-18 (non-success):** every test citation in every spec under
  `openspec/changes/` still resolves after the alias deletions and the
  entry-point rename.
  - The amended lines in `prepare-release-0-3-0` are its AC-REL-5 and
    AC-REL-6 verification lines, each carrying R-RFR-16's exact marker.
  - They are the only lines of that package in the diff, and no other
    package's line is in the diff: a further spec named by the citation
    measure stops implementation rather than being amended here.
  - The citation corpus still holds citations, so the guard has not gone
    blind.

  (R-RFR-16, DEC-RFR-007)
  _Verified by:_ `pytest -k "test_every_spec_test_citation_resolves_to_a_real_test or test_the_spec_corpus_actually_contains_citations"` · stage: `make test`

- [ ] **AC-RFR-19 (non-success):** the rule inventory still matches
  `tests/baseline_rules.json`, the golden `validate`, `graph` and `rules`
  hashes are unchanged, the package still imports only the standard
  library, and the diff touches none of the planted fixtures or dated
  comments C-RFR-5 lists. (C-RFR-1, C-RFR-2, C-RFR-3, C-RFR-5)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_new_modules_stdlib_only"` · stage: `make test`

- [ ] **AC-RFR-20:** `tasks.md` records each of these, as an observation
  with its output and date and never as a test:
  - before the removals' pull request leaves draft: `v0.3.0` on origin,
    `planlint` 0.3.0 on PyPI, `v0.3.0^{commit}` an ancestor of the
    integration branch, and `lean-production-tree`'s implementation merged;
  - before the release-prep pull request opens: `harden-release-pipeline`'s
    implementation and the removals merged;
  - before the promotion opens: the integration branch's tip is the
    release-prep squash commit.

  (R-RFR-1, R-RFR-2, C-RFR-6, DEC-RFR-001)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-21:** with `__version__` at `0.4.0`, the skill's version
  fields equal it and its minimum is not ahead of it, the template pins the
  floor the skill enforces, `CHANGELOG.md` has a `[0.4.0]` heading with its
  release-tag link, and every copyable tag ref in the adopter corpus names
  `v0.4.0`. On the bump alone, `test_skill_metadata_version_matches_the_package`,
  `test_ci_template_pins_the_floor_the_skill_enforces`,
  `test_every_changelog_version_links_to_its_release_tag` and
  `test_every_copyable_tag_ref_names_the_current_version` are watched red
  and then green after the edits. The other two cited tests stay green on
  the bump alone and hold the edits once made. (R-RFR-17, R-RFR-18,
  R-RFR-19, R-RFR-20)
  _Verified by:_ `pytest -k "test_skill_metadata_version_matches_the_package or test_ci_template_pins_the_floor_the_skill_enforces or test_compatibility_prose_matches_the_declared_minimum or test_every_changelog_version_links_to_its_release_tag or test_every_copyable_tag_ref_names_the_current_version or test_skill_min_version_is_not_ahead_of_the_package"` · stage: `make test`

- [ ] **AC-RFR-22:** the `.claude-plugin/` manifests are fresh under the
  generator's check mode at the release-prep commit, and the generator reads
  `__version__` rather than restating it. (R-RFR-17)
  _Verified by:_ `pytest -k "test_generated_artifacts_are_fresh or test_manifest_version_tracks_the_package_not_a_literal"` · stage: `make test`

- [ ] **AC-RFR-23:** the template and its byte copy under `skills/` are
  identical at `@v0.4.0`. The composite action's input set is exactly the
  set it declared before, with `"0.4.0"` as the `version` example. The
  skill's "Wiring it into CI" prose says to pin `@v0.4.0`. `SECURITY.md`'s
  supported-versions sentence names 0.4.0 as the only supported version
  without calling it the first release published to PyPI, while its
  verification commands keep their placeholders. The prose is read
  directly. (R-RFR-18, R-RFR-19, DEC-RFR-011)
  _Verified by:_ `pytest -k "test_skill_asset_matches_template or test_the_action_declares_exactly_the_v1_inputs"` · stage: `make test`

- [ ] **AC-RFR-24:** `## [0.4.0] — <date>` sits under an empty
  `## [Unreleased]`, dated the day the tag is pushed. Every line that sat
  under `[Unreleased]` at the release-prep commit, each sibling's group
  included, is under it verbatim with its groupings. The `[Unreleased]:`
  line compares from `v0.4.0`, and no released section changed. Read
  directly; the date is checked against the tag in `tasks.md`. (R-RFR-20,
  C-RFR-4, DEC-RFR-009)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-25:** the full ladder exits 0 on the removals' head, on the
  release-prep head, and on the production merge commit that the release
  workflow's gate runs it on. (R-RFR-2, R-RFR-21, C-RFR-2)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-26 (observed after the tag):** each of these is recorded in
  `tasks.md` with its run id or sha and the date:
  - the production merge commit's first parent is production's previous
    tip, and its tree equals the candidate branch's;
  - `tag-ancestry` passed on it, and the dry run's gate and build were
    green;
  - the `v0.4.0` push ran every job `release.yml` defines, all green;
  - the attestations on the published wheel and sdist verify as the
    runbook says;
  - the GitHub Release carries the wheel and the sdist;
  - no path that `lean-production-tree`'s implementation squash deleted, by the list
    that commit's diff against its first parent gives, is in the tagged
    tree.

  (R-RFR-21, R-RFR-22, C-RFR-6, DEC-RFR-010)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-27 (observed after the tag):** in a fresh virtual
  environment, `pip install planlint==0.4.0` prints `planlint 0.4.0` from
  `planlint --version`, installs no `specgraph` script, and its
  `validate --fail-on ERROR` on this repository exits 0. `pip download` of
  `planlint==0.4.0` from the index for a 3.10 interpreter is refused, its
  output naming the `Requires-Python` the version declares, while the 3.11
  control succeeds. Recorded in `tasks.md` with the date and the pip
  version. (R-RFR-22, C-RFR-6, DEC-RFR-010)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-28:** the Dockerfile's header carries the single deprecation
  line naming 0.4.0 and 0.5.0, with no install command and no tag token.
  Every guard that reads the Dockerfile, its build context or its
  Dependabot entry still passes, the header reader included.
  `Dockerfile`'s code lines, `.dockerignore` and the `docker` Dependabot
  entry are unchanged by this package's diff, which is read directly.
  (R-RFR-23, DEC-RFR-006)
  _Verified by:_ `pytest -k "test_dockerfile_documents_the_user_override_for_writing_verbs or test_dockerfile_from_is_digest_pinned_with_the_tag_in_the_reference or test_dockerfile_switches_to_a_non_root_user_after_install or test_docker_build_context_is_sufficient_for_the_dynamic_version or test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry or test_agent_artifacts_are_excluded_from_the_docker_context"` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-RFR-1 to 6, 10 to 12, 18, 19, 21 to 23, 28: the floor bound in one place, the alias absent, the Dockerfile's guards still green under its deprecation line, the citations resolving, the bump set named by its tests |
| Lint | `make lint` | AC-RFR-7, 11: ruff's `UP` family at the new floor and nothing the alias deletions left unused (composed into the full ladder) |
| Types | `make typecheck` | mypy at the new `python_version`; the per-code ceilings follow the deletions down (composed into the full ladder) |
| Wheel | `make wheel-check` | the wheel on which AC-RFR-9's refusal and AC-RFR-10's console-script set are observed |
| Docs | `make docs-check` | AC-RFR-8, 16: every required document present and linked after the rewording |
| Generated | `make skill-manifests` | AC-RFR-22: the manifests regenerated from the bumped version |
| Full | `make pre-pr` | AC-RFR-7 to 9, 16, 17, 20, 24 to 27: the ladder `release.yml` gates on, the diff properties, and the recorded observations |
| Self-check | `planlint --target . validate --fail-on ERROR --change prepare-release-0-4-0` | this package validates clean against the repository's own rules |
