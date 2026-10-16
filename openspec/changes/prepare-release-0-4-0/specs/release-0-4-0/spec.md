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

A further removal belongs to the same release and was never announced: the
`Dockerfile`, its `.dockerignore` and the `docker` Dependabot entry. The
image is built, published and scanned nowhere. `harden-ci-workflows`
hardened the recipe — digest pin, non-root user, an update bot — with
guards that read the file and never build it. Keeping a container to 2026
practice is a second supported artifact. This spec deletes it and records
why the deprecation window does not apply.

Every removal also deletes tests that other specs cite. The citation guard
fails on a selector that names nothing, so where each removal lands relative
to `lean-production-tree` decides which specs need amending.

Finally, this is the release-prep package for 0.4.0. After the removals,
`lean-production-tree` and `harden-release-pipeline` have merged, the
mechanism 0.3.0 built runs end to end: bump one literal, regenerate the
manifests, then let the suite name every remaining hand edit, cut the
changelog and run the release through the promotion model. Pushing the tag
and publishing are the maintainer's actions outside the tree. What is
observed afterwards is recorded in `tasks.md`.

**Evidence:** measured at `4278d4c`, 2026-10-16; outside
`openspec/changes/lean-production-tree/` its tree is `dev` at `c0ff090`. Each
command and line number is in the proposal.

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
  - Its header says the image "is not built in CI". No workflow builds or
    pushes one.
  - `.github/dependabot.yml` carries a `docker` entry with its own
    `target-branch`.
  - Its guards are `tests/test_release_surface.py`'s build-context tests,
    `tests/test_workflow_pins.py`'s Dockerfile and docker-watch tests,
    `tests/workflow_support.py`'s `DOCKERFILE` and `_dockerfile_from`, and
    the Dockerfile source of the default-Python agreement test in
    `tests/test_workflow_python.py`.
  - `tests/test_adopter_urls.py` globs it into the adopter corpus.
- **The citations.** `tests/test_spec_test_citations.py` resolves every
  test selector in every spec against the test function names. In the tree
  `lean-production-tree` leaves, the alias tests are still cited by
  `prepare-release-0-3-0`. The Docker-context test is cited by
  `lean-production-tree` itself, whose R-LPT-7 also requires `.dockerignore`
  to keep excluding the agent artifacts.
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
    supported version.
  - `.claude/skills/planlint-release/SKILL.md` gives the order.

---

## Requirements

### Ordering

- R-RFR-1: The removals — every change R-RFR-3 to R-RFR-16 requires — MUST
  NOT merge into the integration branch until `v0.3.0` is tagged on origin,
  `planlint` 0.3.0 is installable from PyPI and `v0.3.0^{commit}` is an
  ancestor of the integration branch. The pull request that carries them
  MUST stay a GitHub draft until those facts are recorded in `tasks.md` with
  their output and the date.
- R-RFR-2: The removals MUST merge after `lean-production-tree` has merged
  into the integration branch. The release-prep pull request of R-RFR-17 to
  R-RFR-20 MUST merge after `lean-production-tree`, `harden-release-pipeline`
  and the removals have all merged, and no other pull request MAY merge into
  the integration branch between it and the promotion that carries it to
  production.

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
  - the "Python X.Y+" floor in `README.md`'s install paragraph;
  - the "Python X.Y or newer" floor in the `compatibility:` field of
    `skills/planlint-spec-governance/SKILL.md`.

  Every value MUST be read from its file and never restated. A source in
  which no floor is found MUST fail rather than be skipped. A disagreement
  MUST fail with a single message naming every source and its value, and
  the file and line for each prose source. A planted counterpart MUST show a
  stale prose floor and a stale `requires-python` each reported
  (DEC-RFR-003).
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
- R-RFR-11: The waiver prefix `specgraph:allow`, the config file
  `openspec/specgraph.json`, the `[tool.specgraph]` table and the legacy
  `SPECGRAPH_LOG_LEVEL` variable MUST keep working unchanged. `README.md`'s
  alias paragraph and `docs/policies.md`'s `specgraph` instance MUST say, in
  the past tense, that the alias warned through every 0.3.x release and was
  removed in 0.4.0. The README paragraph MUST keep naming the stable
  identifiers.

### The Dockerfile

- R-RFR-12: `Dockerfile` and `.dockerignore` MUST be deleted. So MUST
  `.github/dependabot.yml`'s `docker` entry, with its `target-branch` line
  and the header sentence that puts the Docker base image in scope, all in
  the same commit, so that every remaining Dependabot entry still carries
  the integration branch's `target-branch`.
- R-RFR-13: Every test and test helper that reads a file R-RFR-12 deletes
  MUST be deleted with it, and nothing else:
  - the Dockerfile build-context and Docker-context tests in
    `tests/test_release_surface.py`;
  - the Dockerfile and docker-watch helpers and tests in
    `tests/test_workflow_pins.py`, whose module docstring stops naming
    R-HCW-13 and R-HCW-14;
  - `DOCKERFILE`, `WRITING_VERBS` and `_dockerfile_from` in
    `tests/workflow_support.py`;
  - `_dockerfile_tag_version` in `tests/test_workflow_python.py`.

  The default-Python agreement test MUST keep comparing every workflow's
  `PYTHON_DEFAULT` with the composite action's `python-version` default. It
  MUST drop only the Dockerfile source, and MUST be renamed so its name no
  longer names the Dockerfile. `test_a_disagreeing_default_is_named` MUST
  lose only its Dockerfile assertion. `"Dockerfile"` MUST leave the
  adopter-corpus globs of `tests/test_adopter_urls.py`.
  `_dependabot_entries` and its parser test MUST stay, because the docker
  pair in their fixture is parser input, not a claim about the tree.
- R-RFR-14: Every document and configuration comment that names the
  Dockerfile, the image or its build context as present MUST be reworded or
  lose the clause:
  - `docs/aqa.md`'s paragraph on the pins that are not thresholds, and its
    sentence on what `tests/test_release_surface.py` holds;
  - `docs/hooks.md`'s workflow-posture paragraph;
  - `.claude/agents/planlint-verifier.md`'s agent-artifact bullet;
  - `.gitignore`'s Docker block.

  `docs/next-steps.md` item 9 MUST say that the Dockerfile was removed in
  0.4.0 and why. It MUST name `pip install` and the composite action as the
  delivery paths, and the trigger that would reopen an image (DEC-RFR-006).

### Release notes and the open packages

- R-RFR-15: `CHANGELOG.md`'s `[Unreleased]` section MUST gain a single group
  for this change, headed `### Removed` with an em dash and the removals'
  names, beside any `Removed` group a sibling wrote. Its entries MUST be led
  by this package's bold backticked name, as the file's entries are, and
  MUST say:
  - Python 3.10 support is gone. `requires-python` is `>=3.11`; the 3.10
    classifier and matrix leg, the `tomli` dev extra and its mypy override
    are removed; mypy checks against 3.11. The 0.3.0 notes announced this.
  - The `specgraph` command is gone, and users run `planlint`. The waiver
    prefix, the config file, the `[tool.specgraph]` table and
    `SPECGRAPH_LOG_LEVEL` are unchanged. The 0.3.0 notes announced this
    too.
  - `Dockerfile`, `.dockerignore` and the `docker` Dependabot entry are
    gone. The image was never built in CI, published or scanned, and
    `pip install planlint` in any `python` image, or the composite action,
    replaces it. This removal was not announced under `Deprecated`, for the
    reason DEC-RFR-006 gives.
- R-RFR-16: A spec under `openspec/changes/` other than this package's MUST
  be amended in place, marked "(amended by `prepare-release-0-4-0`)", if it
  cites, on any line, a test this change deletes or renames, or requires
  the preservation of a file this change deletes.
  - The amendment MUST touch that clause and nothing else, in the commit
    that deletes the test or the file.
  - At drafting this means AC-REL-5's and AC-REL-6's verification lines in
    `prepare-release-0-3-0`, and in `lean-production-tree` R-LPT-7's
    `.dockerignore` clause and AC-LPT-11's Docker-context clause and
    selector.
  - `tests/test_spec_test_citations.py` decides which citation no longer
    resolves. A citation MUST be re-pointed to a surviving test that
    verifies the same clause, or reduced to its stage. It MUST never be
    kept resolving by a test kept or renamed for that purpose.
  - An amended clause in a shipped package keeps its tick and its text
    (DEC-RFR-007).

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
  set unchanged. `SECURITY.md`'s supported-versions statement MUST name
  0.4.0 as the latest released version and the only supported version.
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
  - that the tagged tree carries no `Dockerfile`, no `.dockerignore` and
    none of the paths `lean-production-tree` deleted;
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

- **DEC-RFR-001:** the ordering gates, each for its own reason.
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
    function. In today's tree the tests this change deletes are cited by
    several shipped packages, among them `harden-ci-workflows`,
    `pin-actions-by-sha` and `rename-cli-and-positioning`.
    `lean-production-tree` deletes those packages. Amending them first would
    edit records that leave the tree in the same release. Worse,
    `lean-production-tree`'s own R-LPT-7 requires `.dockerignore`'s
    exclusions, so a deletion landing first would leave that package
    impossible to implement as written. Landing afterwards, its criteria
    are true when it merges, and this change amends the single clause it
    supersedes.
  - **Third: the release-prep pull request last.** The changelog cut moves
    the whole `[Unreleased]` body, so every sibling's entry must already be
    there (`prepare-release-0-3-0` DEC-REL-011). The copyable-tag guard
    globs `docs/**/*.md`, and until `lean-production-tree` lands that corpus
    holds dated plans spelling `@v0.3.0`. The alias's removal-version test
    derives its window from `__version__`, so the bump turns it red while
    the alias exists; removing the alias first keeps the bump a single
    literal. And the 0.4.0 observations verify what
    `harden-release-pipeline` adds to the pipeline.

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
    `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/ratchet-test-types-and-docstrings/specs/static-check-ratchets/spec.md`
    once that tag exists.

- **DEC-RFR-003:** a single guard for the floor.
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
  - **The prose sources.** These are matched narrowly — the README's
    "Python X.Y+" and the skill's "Python X.Y or newer" — and a source with
    no match fails, so a reworded sentence cannot pass silently.
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
    it is a decision for a later minor.

- **DEC-RFR-006 (supersedes `harden-ci-workflows` R-HCW-13, R-HCW-14,
  C-HCW-5, R-HCW-9's Dockerfile clause and the Dockerfile halves of
  AC-HCW-13, AC-HCW-18 and AC-HCW-19, and `enterprise-hardening`
  DEC-EH-001's optional reproducible runner):** delete the Dockerfile.
  - **It runs nowhere.** It is built, published and scanned nowhere. Its
    own header says it is not built in CI, no workflow pushes an image, no
    registry holds one, and the README never mentions it.
  - **Its hardening was never exercised.** `harden-ci-workflows` hardened
    the text: a digest pin, a non-root user and an update bot. Every guard
    reads the file and none builds the image, so the posture is asserted,
    never exercised, and AC-HCW-18 records that even the manual build was
    not run.
  - **The 2026 cost.** Keeping a container means building it in CI on every
    change that can break it, pushing it to a registry under
    `packages: write` (a second write scope beside the publish job's
    `id-token`), attesting it by digest, triaging the base image's CVEs and
    naming a second supported artifact in `SECURITY.md`. For a stdlib CLI
    with `[project] dependencies = []` that installs with a single `pip`
    line in any `python` image, that is a second product. DEC-EH-001 had
    already called it a convenience, not a delivery path.
  - **Why there is no deprecation window.** `docs/policies.md` protects a
    user-facing surface the tool ships: a command or alias, a flag, an
    output shape, a public import or an interpreter version. No image was
    ever shipped, so there is none for a user to pull that could vanish. A
    user who built an image built it from a clone at a ref, and that ref
    keeps the file. The removal lands in a minor, the only release kind
    that may remove anything, and the notes record it under `Removed` with
    this reason.
  - **Dependabot.** The `docker` entry goes with the file. The rule that
    every entry targets the integration branch (DEC-BPM-013) is held by the
    entries that remain.
  - **Reopening.** The trigger, recorded in `docs/next-steps.md` item 9, is
    an adopter who needs a published image — and then the whole practice
    above, not the recipe alone.
  - **Fallback.** If review reads the Dockerfile as a shipped surface after
    all, the fallback is the window. R-RFR-12 to R-RFR-14 and the
    Dockerfile entry of R-RFR-15 become a `Deprecated` entry in the 0.4.0
    notes naming 0.5.0, and the file stays unchanged through 0.4.x.
  - **Where the superseded clauses live.** They are in the tree at drafting.
    Once `lean-production-tree` lands they are at
    `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/harden-ci-workflows/specs/ci-workflow-hardening/spec.md`
    and
    `https://github.com/ianshank/planlint/tree/archive/dev-record-2026-10/openspec/changes/enterprise-hardening/specs/enterprise-hardening/spec.md`.

- **DEC-RFR-007:** the open specs are amended in place, and the shipped
  0.3.0 record only at its verification lines.
  - **The specs affected.** At drafting, the specs that would still depend
    on what this change deletes after `lean-production-tree` are
    `prepare-release-0-3-0`, which cites the alias tests (AC-REL-5,
    AC-REL-6) and stays until the post-0.4.0 sweep, and
    `lean-production-tree`, which cites the Docker-context test (AC-LPT-11)
    and whose R-LPT-7 requires `.dockerignore` to keep its exclusions.
    `tasks.md` re-runs the grep at the branch head, so a sibling that
    lands meanwhile is found too.
  - **Why amend.** The citation guard leaves only honest options: re-point
    or reduce the citation, or keep the tests. Keeping the alias tests means
    keeping the alias, and a shell test under the old name that asserts
    something else is an alias for a contradicted assertion. So the
    citations are amended in the commit that deletes the test, marked
    "(amended by `prepare-release-0-4-0`)", in the form DEC-WCA-022 and
    DEC-LPT-007 used.
  - **`prepare-release-0-3-0`.** It is a shipped record that
    `lean-production-tree` deliberately left unedited (DEC-LPT-006), so the
    amendment is the smallest that keeps the guard honest: the verification
    lines of AC-REL-5 and AC-REL-6 and nothing else. The criterion text,
    its tick and every other line record what was true at 0.3.0, and the
    tests that verified them are at the `v0.3.0` tag. AC-REL-5 keeps its
    surviving selector, the primary-command test; AC-REL-6 reduces to its
    stage.
  - **`lean-production-tree`.** It is an open package. R-LPT-7's clause
    becomes conditional on the file existing, which it no longer does, and
    AC-LPT-11's Docker-context clause goes with its selector.

  Rejected:
  - Running the sweep early so the 0.3.0 packages leave first: the sweep is
    a post-release step (DEC-LPT-012), not this package's to schedule.
  - Leaving the citations red: a red citation guard blocks every merge.

- **DEC-RFR-008:** the notes.
  - **The group.** This package's `Removed` group sits beside
    `lean-production-tree`'s. The file groups by subject under repeated
    heading kinds — `### Added — …` recurs within a single release — so a
    second `Removed` group reads as the file already reads.
  - **The 0.3.0 entries.** The `[0.3.0]` `Deprecated` entries stay: they
    are the announcement this release executes (C-RFR-4).
  - **The Dockerfile entry.** It says plainly that it was not announced,
    and why. A reader comparing the 0.3.0 `Deprecated` group with the 0.4.0
    `Removed` group will see the difference and is owed the reason.

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

- **DEC-RFR-010:** how each criterion is verified.
  - **The stages.** Verification lines cite `make test` or `make pre-pr`
    and nothing else. `make test` runs every guard. `make pre-pr` is the
    ladder `release.yml`'s gate runs by name, so citing it adds no stage
    that nobody runs (DEC-REL-009, DEC-HCW-013). The validate target is not
    cited: on the lean tree no workflow invokes it by name (DEC-LPT-018).
  - **The selectors.** Tests that exist at drafting are cited by selector.
    The new floor guard, its planted twin, the flipped entry-point test and
    the renamed agreement test are cited by stage until they exist, and
    `tasks.md` adds their selectors in the implementation commit.
  - **After the tag.** Criteria observable only after the tag cite
    `make pre-pr`, name the observation, and stay unchecked until it is
    recorded in `tasks.md` under its run id.
  - **The 3.10 refusal.** It needs no 3.10 interpreter: pip resolves for a
    target interpreter with `--python-version` and refuses a wheel whose
    `Requires-Python` excludes it. It is observed on the locally built
    wheel at implementation and again from the index after the tag, each
    with a 3.11 control, so the refusal is shown to come from the
    requirement and nothing else.

- **DEC-RFR-011:** `SECURITY.md` after 0.4.0.
  - **No new policy.** "Only the latest released version is supported"
    already holds, so 0.3.x gets nothing once 0.4.0 is out.
  - **Only the version moves.** `harden-release-pipeline` rewrites the
    file's scope and response policy. This package touches only the version
    it names, in the release-prep pull request, after that package has
    merged.

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

- [ ] **AC-RFR-3:** the dev extra still floors mypy and pins nothing, with
  no `tomli` entry left in it; no `[[tool.mypy.overrides]]` entry names
  `tomli`; and `read_pyproject` imports `tomllib` with no version branch.
  The override and import clauses are read directly. (R-RFR-4)
  _Verified by:_ `pytest -k test_the_dev_extra_floors_mypy_and_pins_nothing` · stage: `make test`

- [ ] **AC-RFR-4 (non-success):** no branch test on `sys.version_info` or
  `sys.platform` survives anywhere under `tests/`, `ALLOWED_VERSION_CHECK`
  no longer exists, and a planted version branch inside `read_pyproject` in
  `tests/support.py` is reported rather than exempted. (R-RFR-5,
  DEC-RFR-002)
  _Verified by:_ `pytest -k "test_no_stub_name_or_condition_hides_code_from_mypy or test_a_planted_ratchet_violation_is_named"` · stage: `make test`

- [ ] **AC-RFR-5:** the lower bound of `requires-python`, the lowest hard
  matrix leg, the lowest version classifier, `[tool.mypy] python_version`,
  the README's install-paragraph floor and the skill's `compatibility:`
  floor all name the same version, each read from its file. The guard is
  written with this change; until it exists the stage is the citation, and
  `tasks.md` adds its selector. (R-RFR-6, DEC-RFR-003)
  _Verified by:_ stage: `make test`

- [ ] **AC-RFR-6 (non-success):** a planted `README.md` still saying
  "Python 3.10+" beside `requires-python = ">=3.11"` fails the floor guard
  naming the file, the line and both values; a planted
  `requires-python = ">=3.10"` beside a lowest hard leg of 3.11 fails
  naming both sources; and a planted source with no floor in it fails
  rather than being skipped. The test is written with this change; until
  it exists the stage is the citation. (R-RFR-6, DEC-RFR-003)
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
  declares `Requires-Python: >=3.11`. Resolving it for a 3.10 interpreter is
  refused, naming the Python requirement, while the same resolution for
  3.11 succeeds — observed at implementation and recorded in `tasks.md` with
  each output. (R-RFR-3, DEC-RFR-010)
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
  allow-list. (R-RFR-10, C-RFR-2)
  _Verified by:_ `pytest -k "test_primary_command_emits_no_deprecation_warning or test_planlint_module_runs or test_cli_verbs_are_exactly_the_allow_list"` · stage: `make test`

- [ ] **AC-RFR-12 (non-success):** the stable identifiers survive the alias:
  a `specgraph:allow` waiver is still read, `init` still writes
  `openspec/specgraph.json`, `[tool.specgraph]` is still where the
  dead-code confidence is read, and `SPECGRAPH_LOG_LEVEL` still turns on
  debug logging. (R-RFR-11, DEC-RFR-005)
  _Verified by:_ `pytest -k "test_waivers_format_json_emits_parseable_json or test_cli_init_writes_config_and_project or test_the_confidence_lives_only_in_the_specgraph_table or test_verbose_via_env_var"` · stage: `make test`

- [ ] **AC-RFR-13:** `Dockerfile`, `.dockerignore` and the `docker`
  Dependabot entry are gone. Dependabot still watches GitHub Actions in
  every composite action directory, still has no `pip` ecosystem, and every
  remaining entry still targets the integration branch while routes are
  enforced. The deletions are read from the diff. (R-RFR-12, DEC-RFR-006)
  _Verified by:_ `pytest -k "test_dependabot_config_exists_and_watches_github_actions or test_every_composite_action_directory_is_watched_by_dependabot or test_dependabot_does_not_add_a_pip_ecosystem or test_route_enforcement_and_dependabot_flip_together"` · stage: `make test`

- [ ] **AC-RFR-14:** every workflow's `PYTHON_DEFAULT` and the composite
  action's `python-version` default still agree and name a hard matrix leg,
  no single-version literal sits outside `env:` and the matrix, and the
  disagreement readers still parse each surviving source. The agreement
  test's new name, which no longer names the Dockerfile, is added to this
  line by `tasks.md` once it exists. (R-RFR-13)
  _Verified by:_ `pytest -k "test_the_default_python_is_a_hard_matrix_leg or test_no_quoted_python_version_literal_outside_env_and_matrix or test_a_disagreeing_default_is_named"` · stage: `make test`

- [ ] **AC-RFR-15 (non-success):** no tracked file outside `CHANGELOG.md`
  and `openspec/changes/` names the Dockerfile, the image or `.dockerignore`
  as present, and no test or helper reads either file. The adopter corpus is
  still discovered and non-empty without its `Dockerfile` glob, and the
  Dependabot parser still reads a pair per watched directory. The grep is
  recorded in `tasks.md`. (R-RFR-12, R-RFR-13, R-RFR-14)
  _Verified by:_ `pytest -k "test_the_adopter_corpus_is_discovered_and_not_empty or test_a_plural_directories_entry_is_read_as_one_pair_per_directory"` · stage: `make test`

- [ ] **AC-RFR-16:** `README.md`'s alias paragraph and `docs/policies.md`'s
  instances read in the past tense, with the stable identifiers named.
  `docs/aqa.md`, `docs/hooks.md`'s posture paragraph,
  `.claude/agents/planlint-verifier.md` and `.gitignore` no longer describe
  a Docker image, and `docs/next-steps.md` item 9 records the removal, the
  delivery paths and the reopen trigger. Every backticked path in the agent
  and skill prose resolves, and the docs gate and the CI-table guard pass.
  The prose is read directly. (R-RFR-11, R-RFR-14, DEC-RFR-006)
  _Verified by:_ `pytest -k "test_docs_check_passes or test_path_like_backtick_references_resolve_to_real_files or test_hooks_ci_table_lists_every_ci_job"` · stage: `make pre-pr`

- [ ] **AC-RFR-17:** `CHANGELOG.md`'s `[Unreleased]` carries this package's
  `Removed` group with an entry for each removal, the Dockerfile's saying it
  was not announced and why, and no released section — the `[0.3.0]`
  `Deprecated` group included — differs from the branch base. Read
  directly from the file and the diff. (R-RFR-15, C-RFR-4, DEC-RFR-008)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-18 (non-success):** every test citation in every spec under
  `openspec/changes/` still resolves after the deletions and the renames.
  The amended clauses in `prepare-release-0-3-0` and `lean-production-tree`
  carry the marker and are the only lines of those packages in the diff,
  and the citation corpus still holds citations, so the guard has not gone
  blind. (R-RFR-16, DEC-RFR-007)
  _Verified by:_ `pytest -k "test_every_spec_test_citation_resolves_to_a_real_test or test_the_spec_corpus_actually_contains_citations"` · stage: `make test`

- [ ] **AC-RFR-19 (non-success):** the rule inventory still matches
  `tests/baseline_rules.json`, the golden `validate`, `graph` and `rules`
  hashes are unchanged, the package still imports only the standard
  library, and the diff touches none of the planted fixtures or dated
  comments C-RFR-5 lists. (C-RFR-1, C-RFR-2, C-RFR-3, C-RFR-5)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical or test_new_modules_stdlib_only"` · stage: `make test`

- [ ] **AC-RFR-20:** before the removals' pull request leaves draft,
  `tasks.md` records `v0.3.0` on origin, `planlint` 0.3.0 on PyPI,
  `v0.3.0^{commit}` an ancestor of the integration branch, and
  `lean-production-tree` merged. Before the release-prep pull request
  opens, it records `harden-release-pipeline` and the removals merged. Each
  is an observation with its output and date; none is a test. (R-RFR-1,
  R-RFR-2, C-RFR-6, DEC-RFR-001)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-21:** with `__version__` at `0.4.0`, the skill's version
  fields equal it and its minimum is not ahead of it, the template pins the
  floor the skill enforces, `CHANGELOG.md` has a `[0.4.0]` heading with its
  release-tag link, and every copyable tag ref in the adopter corpus names
  `v0.4.0`. These are the tests that name each hand edit, watched red on the
  bump alone and green after the edits. (R-RFR-17, R-RFR-18, R-RFR-19,
  R-RFR-20)
  _Verified by:_ `pytest -k "test_skill_metadata_version_matches_the_package or test_ci_template_pins_the_floor_the_skill_enforces or test_compatibility_prose_matches_the_declared_minimum or test_every_changelog_version_links_to_its_release_tag or test_every_copyable_tag_ref_names_the_current_version or test_skill_min_version_is_not_ahead_of_the_package"` · stage: `make test`

- [ ] **AC-RFR-22:** the `.claude-plugin/` manifests are fresh under the
  generator's check mode at the release-prep commit, and the generator reads
  `__version__` rather than restating it. (R-RFR-17)
  _Verified by:_ `pytest -k "test_generated_artifacts_are_fresh or test_manifest_version_tracks_the_package_not_a_literal"` · stage: `make test`

- [ ] **AC-RFR-23:** the template and its byte copy under `skills/` are
  identical at `@v0.4.0`. The composite action's input set is exactly the
  set it declared before, with `"0.4.0"` as the `version` example. The
  skill's "Wiring it into CI" prose says to pin `@v0.4.0`, and `SECURITY.md`
  names 0.4.0 as the only supported version. The prose is read directly.
  (R-RFR-18, R-RFR-19, DEC-RFR-011)
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
  - the tagged tree carries no `Dockerfile`, no `.dockerignore` and none of
    the paths `lean-production-tree` deleted.

  (R-RFR-21, R-RFR-22, C-RFR-6, DEC-RFR-010)
  _Verified by:_ stage: `make pre-pr`

- [ ] **AC-RFR-27 (observed after the tag):** in a fresh virtual
  environment, `pip install planlint==0.4.0` prints `planlint 0.4.0` from
  `planlint --version`, installs no `specgraph` script, and its
  `validate --fail-on ERROR` on this repository exits 0. Resolving
  `planlint==0.4.0` from the index for a 3.10 interpreter is refused,
  naming the Python requirement. Recorded in `tasks.md` with the date.
  (R-RFR-22, C-RFR-6, DEC-RFR-010)
  _Verified by:_ stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-RFR-1 to 6, 10 to 15, 18, 19, 21 to 23: the floor bound in one place, the alias absent, the Docker guards gone with their files, the citations resolving, the bump set named by its tests |
| Lint | `make lint` | AC-RFR-7: ruff's `UP` family at the new floor, every finding fixed (composed into the full ladder) |
| Types | `make typecheck` | mypy at the new `python_version`; the per-code ceilings follow the deletions down (composed into the full ladder) |
| Wheel | `make wheel-check` | the wheel on which AC-RFR-9's refusal and AC-RFR-10's console-script set are observed |
| Docs | `make docs-check` | AC-RFR-8, 16: every required document present and linked after the rewording |
| Generated | `make skill-manifests` | AC-RFR-22: the manifests regenerated from the bumped version |
| Full | `make pre-pr` | AC-RFR-7 to 9, 16, 17, 20, 24 to 27: the ladder `release.yml` gates on, the diff properties, and the recorded observations |
| Self-check | `planlint --target . validate --fail-on ERROR --change prepare-release-0-4-0` | this package validates clean against the repository's own rules |
