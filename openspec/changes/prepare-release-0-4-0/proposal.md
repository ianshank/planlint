# Change: Prepare the 0.4.0 Release — the Announced Removals, the Dockerfile's Deprecation, the Bump Set and the Cut

## Why

The 0.3.0 release notes announce two removals for 0.4.0. `CHANGELOG.md`'s
`[0.3.0]` section carries a `### Deprecated` group with exactly these two
entries: Python 3.10 support ends in 0.4.0, when `requires-python` moves to
`>=3.11` and the `tomli` extra goes, and the `specgraph` alias is removed in
0.4.0. `docs/policies.md`, "Versioning and deprecation", makes both instances
of one rule: a minor release 0.Y.0 announces a deprecation and names the
version that removes it, the surface keeps working through the whole 0.Y.x
series, and it may be removed from 0.(Y+1).0, never in a patch. 0.4.0 is
that release. Two conditions follow. The window has to have opened first:
0.3.0 must be tagged and published with 3.10 and the alias intact. And the
removal has to be complete: the floor is written by hand in more places than
the announcement lists, and no test binds `requires-python` to the matrix,
the classifiers or the prose, so a partial bump stays green.

A third surface should go, and it was **not** announced: the `Dockerfile`,
with its `.dockerignore` and the `docker` Dependabot entry. It is built,
published and scanned nowhere. `harden-ci-workflows` made it a
digest-pinned, non-root recipe (R-HCW-13, R-HCW-14), and every check it
added is a text check that never builds the image. Keeping it to 2026
practice would mean a second supported artifact, a lot of machinery for a
stdlib CLI that installs in one line in any `python` image. But the
repository's records call it user-facing, and the policy's window covers
surfaces the tool does not ship, interpreter versions among them. So 0.4.0
announces its deprecation, names 0.5.0 as the removal version, and changes
nothing in it but one header line (DEC-RFR-006). The first draft removed it
outright; the first adversarial review showed that was not defensible under
the policy, and the removal moved to a 0.5.0 package.

0.4.0 is also the release that first reaches production with the lean tree
(`lean-production-tree`) and the hardened release pipeline
(`harden-release-pipeline`), so its release-prep pull request lands last, as
0.3.0's did (`prepare-release-0-3-0` DEC-REL-011). The bump mechanism 0.3.0
built runs end to end here for the first time: edit one literal, run
`make skill-manifests`, then run `make test` and follow its failures, which
name every remaining hand edit. `.claude/skills/planlint-release/SKILL.md`
gives the order of operations.

This package is Phase 2.2 and Phase 3 of the session plan for a lean
production branch. That plan is not tracked, so every decision this package
takes from it is restated in `specs/release-0-4-0/spec.md`, and every number
below was re-measured here rather than copied from it.

**Evidence:** measured at `4278d4c` on `claude/lean-production-tree`,
2026-10-16, and re-checked at `f0063a6` on `claude/prepare-release-0-4-0`
for the first adversarial review. Outside the change package each branch
adds, both trees are `dev` at `c0ff090`: `git diff --name-only c0ff090 HEAD
| grep -v '^openspec/changes/'` prints nothing on either. Line numbers are
at those commits. A sibling landing first moves a line without moving the
fact, and `tasks.md` re-reads each line before the milestone that uses it.

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR`: exit 0, no finding at any severity, before any file of this package
  existed.
- **The window has not opened yet.** `git ls-remote --tags origin` lists
  only `v0.1.0`, and `https://pypi.org/pypi/planlint/json` answers 404.
  `CHANGELOG.md:8` reads `## [0.3.0] — 2026-10-08`, and
  `openspec_graph/__init__.py:15` is `__version__ = "0.3.0"`: the tree is cut
  for 0.3.0 and the tag is the owner's next step. `docs/next-steps.md:9-11`
  starts nothing until `v0.3.0` is tagged and `pip install planlint` resolves.
- **What was announced, and what was not.** `CHANGELOG.md:350-364` is the
  `[0.3.0]` `### Deprecated` group, with the 3.10 and `specgraph` entries
  only. `docs/policies.md:66-85` states the window and its three instances:
  `specgraph`, `detect --json` (removal named as 1.0) and Python 3.10. Its
  surface list (`:66-68`) is "a command or alias, a flag, an output shape, a
  public import, an interpreter version". The Dockerfile appears in no
  `Deprecated` group.
- **The 3.10 sites.** The caller's grep is `grep -rn "3\.10\|tomli"
  --include=*.py --include=*.toml --include=*.yml --include=*.md . | grep -v
  '^./openspec/changes/\|^./.git/'`, read with untracked `build/` (ignored by
  `.gitignore:10`) set aside. It finds:
  - `pyproject.toml` lines 35 (`requires-python = ">=3.10"`), 47 (the 3.10
    classifier), 271-273 (the dev extra's `tomli` comment), 301 (`"tomli;
    python_version < \"3.11\""`), 431 (`[tool.mypy] python_version =
    "3.10"`) and 464-470 (the `[[tool.mypy.overrides]]` entry for `tomli`
    and its comment).
  - `.github/workflows/ci.yml:48`, the matrix `["3.10", "3.11", "3.12",
    "3.13", "3.14"]`.
  - `tests/ratchet_support.py:47`, whose `MYPY_FIXED` holds `"python_version":
    "3.10"`, and `tests/test_ci_workflow.py:52,56`, where
    `test_mypy_is_strict_and_warns_on_unreachable_code` asserts the literal.
  - `tests/support.py:74-95`, `read_pyproject`'s `sys.version_info` branch
    choosing `tomllib` or `tomli`, and `:232-233`, the `working_directory`
    docstring.
  - `docs/hooks.md:76`, the `(3.10–3.14)` `test` row; `README.md:39`
    ("Python 3.10+"); `docs/aqa.md:150,287`;
    `skills/planlint-spec-governance/SKILL.md:5` ("Python 3.10 or newer");
    and `docs/policies.md:82-85`.
  - The comments and docstrings at `openspec_graph/log.py:40`,
    `openspec_graph/thresholds.py:128-133`, `tools/_common.py:203-205`,
    `:231-233` and `:333-334`, `tools/check_wheel_metadata.py:46-49`,
    `tests/test_enterprise.py:493` and `tests/test_properties.py:31`.

  Three more sites carry the same reason without the string "3.10":
  `openspec_graph/thresholds.py:10-12`, the module docstring ("``tomllib`` is
  3.11+ and this package has no runtime dependencies"); `tests/test_static_ratchets.py:217-219`
  ("but R-TDR-6's one"); and `docs/next-steps.md:182-194`, item 7a, which
  ends "Revisit when 3.10 leaves the matrix". Planted fixtures that spell
  3.10 or `tomli` as data stay as they are:
  `tests/test_workflow_python.py:173,254,262,289`,
  `tests/test_ci_workflow.py:343,361` and
  `tests/test_static_ratchets_planted.py:145,223`. So does the dated
  measurement in the comment at `pyproject.toml:156` ("every leg — Linux
  3.10–3.14 and Windows 3.12 — read the same 944/979 lines" at run
  37553098324). `CHANGELOG.md`'s mentions are released history.
- **R-TDR-6's exception becomes dead.** `tests/ratchet_support.py:64` is
  `ALLOWED_VERSION_CHECK = ("tests/support.py", "read_pyproject")`.
  `hidden_code` (`:356-369`) exempts exactly one `sys.version_info` branch
  at that site and reports every other. The planted cases
  `second-check-at-the-site` and `allowed-site`
  (`tests/test_static_ratchets_planted.py:181-182`, imported at `:25`) prove
  the exemption. `ratchet-test-types-and-docstrings` R-TDR-6 required the
  branch and the `tomli` override. With the floor at 3.11, the branch's else
  arm can never run.
- **What ruff and mypy say at the new floor.** `[tool.ruff]` sets no
  `target-version`, so ruff's `UP` family floors at `requires-python` (the
  comment at `pyproject.toml:326`). `python -m ruff check --no-cache
  --target-version py311 --select UP --output-format concise openspec_graph
  tools tests` (ruff 0.17.0) reports
  `openspec_graph/cli.py:819:34: UP017 [*] Use datetime.UTC alias` and
  `tests/support.py:89:8: UP036 Version block is outdated for minimum Python
  version`, and nothing else. `python -m mypy --config-file pyproject.toml
  --cache-dir=/dev/null --python-version 3.11` and the same at `3.10` both
  print `Success: no issues found in 119 source files`. The exact per-code
  ceilings `tests/test_static_ratchets.py` holds are measured with codes the
  config disables, so they are re-measured at implementation.
- **Nothing binds the floor.** `grep -rn "requires-python\|requires_python"
  tests/*.py tools/*.py` finds only the docstring at `tests/support.py:233`.
  `test_classifiers_equal_the_hard_matrix_legs` and
  `test_hooks_test_row_names_the_matrix_bounds`
  (`tests/test_workflow_python.py:264-283`) bind the classifiers and the hooks
  row to the matrix, but nothing binds `requires-python`, mypy's
  `python_version`, `README.md:39` or `SKILL.md`'s `compatibility:` floor to
  anything. `test_compatibility_prose_matches_the_declared_minimum` reads
  only the planlint version in that line (`tests/test_agent_skill_docs.py:500-519`).
  `_matrix_versions` returns version strings, and as strings `"3.10"` sorts
  below `"3.9"`. `_version_key` (`tests/test_workflow_python.py:31-32`) is
  the numeric key the hooks-row test already uses.
- **The alias.** `pyproject.toml:61-69` declares `planlint =
  "openspec_graph.cli:main"` and `specgraph =
  "openspec_graph.cli:main_deprecated"` under a comment stating the window.
  `openspec_graph/cli.py:1010-1026` holds `_DEPRECATION_WARNING` and
  `main_deprecated`, and `:991-992`'s comment in `main` names "both the
  `planlint` and deprecated `specgraph` entry points". The plan filed that
  comment under the 3.10 comments; it belongs to the alias. In
  `tests/test_cli_surface.py`:
  - the module docstring (`:1`) and the import of `main_deprecated` (`:20`);
  - `test_entry_points_wired_in_pyproject` (`:227-234`), which asserts both
    entries as text, and the `repo_root` fixture (`:509-511`) that only it
    uses;
  - `test_deprecated_alias_warns_to_stderr_and_delegates`,
    `test_deprecated_alias_preserves_failure_exit_code` and
    `test_deprecated_alias_keeps_stdout_parseable` (`:258-301`);
  - `test_deprecated_alias_names_its_removal_version` (`:514-530`), the only
    user of the module-level `from openspec_graph import __version__`
    (`:19`); the version tests at `:155` and `:175` import it locally.

  That last test derives the window from `__version__`, so it goes red on
  the 0.4.0 bump while the alias still exists.
  `test_primary_command_emits_no_deprecation_warning` (`:246-255`) does not
  touch the alias. `README.md:77-84` and `docs/policies.md:74-79` describe
  the window in the present tense.
- **What keeps the old name.** The waiver prefix `specgraph:allow`,
  `openspec/specgraph.json` and `[tool.specgraph]` are stable identifiers,
  per `rename-cli-and-positioning` C-CP-1 and the `[0.3.0]` `Deprecated`
  entry. `SPECGRAPH_LOG_LEVEL`, the legacy log variable
  (`openspec_graph/log.py:9-24`, `tools/_common.py:30`, `README.md:384`,
  `tests/test_enterprise.py:153-159`), was never announced in any
  `Deprecated` group, so under `docs/policies.md` it cannot go in 0.4.0. The
  contributor hook ids in `.pre-commit-config.yaml` (`specgraph-lint` and
  its siblings) and comments such as `pyproject.toml:123,133` name nothing
  a user runs.
- **The Dockerfile is a user-facing surface by the repository's own
  records.**
  - `CHANGELOG.md:1775`, in `[0.1.0]`'s `Added`, introduced it as "Optional
    `Dockerfile` + `.dockerignore` for hermetic CLI invocation".
  - `Dockerfile:1-16` documents a build and a run "for CI sandboxes that
    want a hermetic, dependency-free CLI invocation", and says at `:3-4` the
    image "is not built in CI".
  - `enterprise-hardening` DEC-EH-001 calls it "a convenience image for CI
    sandboxes".
  - `write-down-policies`' spec (`:412`) names "the Docker surface".
- **What reads the Dockerfile's header.**
  - `test_dockerfile_documents_the_user_override_for_writing_verbs`
    (`tests/test_workflow_pins.py:432-438`) calls `_user_override_offenders`
    (`:177-191`). That joins every comment line and requires `--user`,
    `id -u` and each backticked writing verb, so an added comment line
    removes nothing it needs.
  - The `FROM` and `USER` readers go through `_code_lines`
    (`tests/workflow_support.py:86`), which drops comments, and the `COPY`
    reader (`tests/test_release_surface.py:202`) is anchored at `^COPY`.
  - `tests/test_adopter_urls.py:168` globs the file into the adopter
    corpus, whose scans look for install commands and `@v`/`rev:` tag
    tokens.
- **For the 0.5.0 package: what the removal touches.** The inventory
  measured for the first draft, and handed to that package:
  - `.github/dependabot.yml:3-4,62-78`, the `docker` entry with its own
    `target-branch`. `test_route_enforcement_and_dependabot_flip_together`
    (`tests/test_ci_promotion.py:349-370`) requires one `target-branch` per
    entry.
  - `tests/test_release_surface.py:193-235`.
  - `tests/test_workflow_pins.py:1-6,23,30,32,154-191,230-236,416-471,491-499`,
    keeping `_dependabot_entries` (`:194-228`) and its parser test
    (`:473-489`).
  - `tests/workflow_support.py:31,64-68,156-163`, whose `import re` (`:12`)
    is used only by `_FROM` and goes with it.
  - `tests/test_workflow_python.py:18,23,129-134,198,214`.
  - `tests/test_adopter_urls.py:168`.
  - `docs/aqa.md:39-48,113-114`, `docs/hooks.md:111-112`,
    `.claude/agents/planlint-verifier.md:22` and `.gitignore:57-58`.

  A citation measure for the Dockerfile tests, the script below with that
  set as `gone`, names `harden-ci-workflows` and `pin-actions-by-sha` at
  `f0063a6`, and `lean-production-tree`'s AC-LPT-11 at `4278d4c`.
- **Which specs cite a test this change deletes.** At `f0063a6` the
  citations that resolve today but would not once the alias tests are
  deleted and `test_entry_points_wired_in_pyproject` is renamed are listed
  by:

  ```
  python - <<'EOF'
  import sys; sys.path.insert(0, ".")
  from tests.test_spec_test_citations import _citations, _collected_test_names, REPO_ROOT
  known = _collected_test_names()
  gone = {n for n in known if n.startswith("test_deprecated_alias_")} | {"test_entry_points_wired_in_pyproject"}
  after = (known - gone) | {"test_entry_points_declare_planlint_and_no_alias"}
  for spec, tok in _citations():
      if any(tok in n for n in known) and not any(tok in n for n in after):
          print(spec.relative_to(REPO_ROOT).parts[2], tok)
  EOF
  ```

  It names three packages: `prepare-release-0-3-0` (the four alias tests
  and the entry-point test), `rename-cli-and-positioning` (the
  `test_deprecated_alias` substring and the stdout test) and
  `write-down-policies` (three alias tests). `shape-the-test-suite` mentions
  the tests but cites none of them. The first draft's "six shipped packages
  and one open package" counted the Dockerfile tests too, and counted
  mentions as citations. `lean-production-tree` deletes
  `rename-cli-and-positioning` and `write-down-policies` and keeps
  `prepare-release-0-3-0` until the post-0.4.0 sweep (DEC-LPT-012).
  `harden-release-pipeline` is re-checked at implementation.
- **The release-prep sites.**
  - `openspec_graph/__init__.py:15`.
  - `skills/planlint-spec-governance/SKILL.md:5,7,8`, the three frontmatter
    fields, and `:178`, "pin `@v0.3.0`".
  - The copyable tag refs. The 0.3.0 package's grep (DEC-REL-004),
    `grep -rnE '@v[0-9]+\.[0-9]+\.[0-9]+|rev:\s*v[0-9]+\.[0-9]+\.[0-9]+'
    --include='*.md' --include='*.yml' --include='*.yaml' . --exclude-dir=.git
    --exclude-dir=openspec --exclude-dir=build` minus `CHANGELOG.md`, prints
    `templates/spec-gate.yml:68`, its byte copy
    `skills/planlint-spec-governance/assets/spec-gate.yml:68`, `SKILL.md:178`,
    `README.md:403,449` and `.pre-commit-hooks.yaml:10`.
  - The same grep prints `docs/distribution-plan.md` and
    `docs/reflection-plan-2026-10.md`, both deleted by
    `lean-production-tree`. Before it lands, the 0.4.0 bump would demand
    rewriting dated plans.
  - `.github/actions/planlint/action.yml:34` (`e.g. "0.3.0"`),
    `SECURITY.md:54-59` and `CHANGELOG.md`'s `[Unreleased]` (line 6) with its
    link definitions (`:1793-1796`).
  - The tests that name each edit:
    `test_skill_metadata_version_matches_the_package`,
    `test_compatibility_prose_matches_the_declared_minimum` and
    `test_skill_min_version_is_not_ahead_of_the_package`
    (`tests/test_agent_skill_docs.py:470,500,437`), and
    `test_ci_template_pins_the_floor_the_skill_enforces`,
    `test_every_changelog_version_links_to_its_release_tag` and
    `test_every_copyable_tag_ref_names_the_current_version`
    (`tests/test_adopter_urls.py:285,338,453`).
  - On the bump alone, the 0.3.0 record (`prepare-release-0-3-0/tasks.md:62-68`)
    saw the metadata, template-floor and changelog tests go red while the
    compatibility test stayed green; the minimum-ahead test cannot go red
    on a bump, since the minimum is still the older version.
- **The 3.10 refusal depends on pip's version.** The review measured that
  `pip install --dry-run --python-version 3.10 <wheel>` exits 0 on pip 24.0
  and 24.1 and refuses only from 24.2, while `pip download --no-deps
  --only-binary=:all: --python-version 3.10 -d <dir> <wheel>` refuses on
  24.0 and later. This environment has pip 24.0.
- **The checks a removed leg could strand.** The promotion model's planned
  rulesets require the `ci-ok` check alone. `gh api
  repos/ianshank/planlint/rulesets` returned `[]` at `04d1622`
  (`lean-production-tree/tasks.md`). No artifact consumer keys on the 3.10
  leg: the per-leg upload is named `coverage-${{ runner.os }}-${{
  matrix.python-version }}` (`ci.yml:79`) and nothing downloads it by name.

## What Changes

**Pull request 1 — the removals and the Dockerfile's deprecation (Milestones
0 to 4), squash into `dev`, after `v0.3.0` is published and
`lean-production-tree` has merged.**

- **`pyproject.toml`.**
  - `requires-python = ">=3.11"`, and the 3.10 classifier is dropped.
  - The dev extra loses `"tomli; python_version < \"3.11\""` and the
    sentence of its comment that explains it.
  - `[tool.mypy] python_version = "3.11"`.
  - The `[[tool.mypy.overrides]]` entry for `tomli` goes, with its comment.
  - `[project.scripts]` declares `planlint` alone, under a comment that
    records the alias's removal in 0.4.0. The dated measurement comment in
    the coverage floors block stays.
- **`.github/workflows/ci.yml`**: the matrix becomes `["3.11", "3.12",
  "3.13", "3.14"]`.
- **`tests/support.py`**: `read_pyproject` imports `tomllib`
  unconditionally, and its docstring drops the 3.10 leg and R-TDR-6. The
  `working_directory` docstring no longer claims the 3.10 floor; the helper
  is kept.
- **`tests/ratchet_support.py`**:
  - `MYPY_FIXED`'s `python_version` is `"3.11"`.
  - `ALLOWED_VERSION_CHECK` is deleted, and `hidden_code` reports every
    `sys.version_info` or `sys.platform` branch under `tests/` with no
    exempt site.
  - The comment and docstring that name "R-TDR-6's one" say so.
- **`tests/test_static_ratchets_planted.py`**:
  - The import goes.
  - `allowed-site` flips to the non-success direction: a version branch in
    `read_pyproject` is reported.
  - `second-check-at-the-site` is deleted, since with no exemption the
    first check is already reported.
- **`tests/test_static_ratchets.py`**: the docstring of
  `test_no_stub_name_or_condition_hides_code_from_mypy` says "no version or
  platform branch under `tests/`". Any per-code ceiling the run names is
  lowered: a ceiling only falls.
- **`tests/workflow_support.py`**: a `requires_python_floor` reader, shared
  by the two modules below.
- **`tests/test_ci_workflow.py`**: `test_mypy_is_strict_and_warns_on_unreachable_code`
  asserts that `python_version` equals the lower bound of `requires-python`,
  read from the file, in place of the `"3.10"` literal.
- **`tests/test_workflow_python.py`**: a new floor guard and its planted
  non-success twin.
  - The lower bound of `requires-python`, the lowest hard matrix leg, the
    lowest `Programming Language :: Python :: 3.x` classifier,
    `[tool.mypy] python_version`, `README.md`'s "Python X.Y+" and
    `SKILL.md`'s `compatibility:` "Python X.Y or newer" must all name one
    version, compared numerically.
  - Prose is read through a `_prose_floor` reader, and the twin plants text
    and a specifier through the same readers.
  - The function names are fixed in `tasks.md` and added as selectors when
    the tests exist.
- **`openspec_graph/cli.py`**:
  - `main_deprecated` and `_DEPRECATION_WARNING` are deleted.
  - The comment in `main` names one entry point.
  - Ruff's UP017 is applied: `timezone.utc` becomes `UTC`, a
    behaviour-identical alias.
- **`tests/test_cli_surface.py`**:
  - The four alias tests are deleted.
  - `test_entry_points_wired_in_pyproject` flips to the absence direction
    under a new name: `[project.scripts]`, read structurally, has exactly
    the key `planlint`, and `openspec_graph.cli` has no `main_deprecated`.
  - The import of `main_deprecated`, the now-unused module-level
    `__version__` import and the `repo_root` fixture go, and the module
    docstring follows.
  - `test_primary_command_emits_no_deprecation_warning` stays.
- **`Dockerfile`**: one header comment line — deprecated in 0.4.0, removed
  in 0.5.0, see the changelog. Nothing else in it, in `.dockerignore`, in
  the `docker` Dependabot entry or in any test that reads them changes.
- **Prose**:
  - `README.md:39` reads "Python 3.11+", and the alias paragraph is past
    tense with the stable identifiers kept.
  - `docs/hooks.md`: the `test` row reads `(3.11–3.14)`.
  - `docs/aqa.md`: the two version ranges.
  - `docs/policies.md`: the 3.10 and `specgraph` instances are past tense.
  - `docs/next-steps.md`: item 7a reads "now unblocked", with the swap still
    its own package; item 9 records the Dockerfile's window and its reopen
    trigger.
  - `skills/planlint-spec-governance/SKILL.md:5`: "Python 3.11 or newer".
  - The comments and docstrings listed in the Evidence are reworded to stop
    stating the 3.10 floor as a present fact. Code changes only where a
    branch can no longer run or where ruff names an upgrade.
- **`CHANGELOG.md` `[Unreleased]`**: a `### Removed — Python 3.10 and the
  `specgraph` alias` group, beside `lean-production-tree`'s
  `### Removed — the development record`, and a `### Deprecated` group
  announcing the Dockerfile's removal in 0.5.0.
- **One shipped package, amended at two lines**: `prepare-release-0-3-0`'s
  AC-REL-5 and AC-REL-6 verification lines, marked "(amended by
  `prepare-release-0-4-0`)", superseding `lean-production-tree` DEC-LPT-004's
  no-edit rule for those two lines only (DEC-RFR-007). Any further spec the
  citation guard names at implementation is amended the same way.

**Pull request 2 — the 0.4.0 release prep (Milestone 5), squash into `dev`,
after `lean-production-tree`, `harden-release-pipeline` and pull request 1
have merged.**

- `openspec_graph/__init__.py`: `__version__ = "0.4.0"`. Then
  `make skill-manifests`, and `pip install -e ".[dev]"` so the installed
  metadata reads the new version.
- `skills/planlint-spec-governance/SKILL.md`: the three frontmatter fields
  read `0.4.0`, and the "Wiring it into CI" prose says pin `@v0.4.0`.
- `templates/spec-gate.yml` and its byte copy, `README.md`'s own-action
  snippets and `.pre-commit-hooks.yaml`'s example: `@v0.4.0` /
  `rev: v0.4.0`.
- `.github/actions/planlint/action.yml`: the `version` example reads
  `"0.4.0"`.
- `SECURITY.md`: the supported-versions sentence names 0.4.0; the
  verification commands keep their placeholders.
- `CHANGELOG.md`: `## [0.4.0] — <the day the tag is pushed>`, with every line
  under `[Unreleased]` moved verbatim, the Dockerfile's `Deprecated` group
  included. The `[0.4.0]:` tag link is added, and the `[Unreleased]:`
  compare line moves to `v0.4.0...HEAD`.

**Then the maintainer (Milestone 6)**: confirm `dev`'s tip is the recorded
release-prep commit, promote `dev` → `qa` → `main` by merge commits,
dry-run, tag the production merge commit `v0.4.0`, publish, verify and
back-merge. The observations are recorded in this package's `tasks.md` in a
later pull request into `dev`. The cumulative sweep that follows, the
runbook's last step, removes this package with the others 0.4.0 shipped.

## Non-Goals

- **No merge before `v0.3.0` is published.** 0.3.0 must still support 3.10
  and still install `specgraph`. Pull request 1 stays a GitHub draft until
  Milestone 0 records the tag, the PyPI release and its ancestry
  (DEC-RFR-001).
- **No Dockerfile removal in 0.4.0.** The file, `.dockerignore`, the
  `docker` Dependabot entry and their guards stay through every 0.4.x
  release, apart from the one header line. The removal, with the inventory
  the proposal measured, is a 0.5.0 package's (DEC-RFR-006).
- **No `tomllib` in the hand-rolled scanners.** `scoped_fail_under`, the
  `tools/_common.py` readers and `tools/check_wheel_metadata.py` keep their
  line scanners. Replacing them is `docs/next-steps.md` item 7a's own
  package, which this change makes possible and does not start: the dialect
  card's byte identity is the contract that package must re-prove.
- **No modernisation beyond what the floor forces.** Code changes where a
  branch can no longer run and where ruff's `UP` family names an upgrade,
  and nowhere else. `contextlib.chdir` does not replace `working_directory`,
  and `logging.getLevelNamesMapping` does not replace `getLevelName`. Each
  is a behaviour change with a tested contract of its own.
- **No removal that was not announced; the one new deprecation announced
  here is the Dockerfile's.** `SPECGRAPH_LOG_LEVEL` stays, and so do
  `detect --json` (named for 1.0), the waiver prefix,
  `openspec/specgraph.json`, `[tool.specgraph]`, the contributor hook ids in
  `.pre-commit-config.yaml` and the comments that use the old name.
- **No container image of any kind.** No ghcr.io package and no
  `packages: write`. Reopening is recorded in `docs/next-steps.md` item 9
  with its trigger (DEC-RFR-006).
- **No change to `PYTHON_DEFAULT`, the composite action's inputs or
  defaults, any workflow job name, any rule, any `make` target or any
  golden hash.**
- **No edit to a released `CHANGELOG.md` section.** The `[0.3.0]`
  `Deprecated` group stays as written. That is the announcement this
  package executes.
- **No edit to a shipped package beyond two verification lines.** No line
  of `prepare-release-0-3-0` other than AC-REL-5's and AC-REL-6's
  verification lines changes, and no other shipped or open package is
  edited; `lean-production-tree`'s R-LPT-7 and AC-LPT-11 hold as written
  while the Dockerfile stays.
- **No release-pipeline change, no lean-tree deletion, no sweep.** Those
  are `harden-release-pipeline`'s, `lean-production-tree`'s and the
  runbook's. The 0.3.0 packages leave in the post-0.4.0 sweep by
  DEC-LPT-012, not here.
- **No tag push, no publish, no settings from inside the tree.** Pushing
  `v0.4.0`, the dry run and the GitHub settings are the maintainer's. What
  they observe is recorded after the fact.

## Affected Capabilities

- `release-0-4-0`
