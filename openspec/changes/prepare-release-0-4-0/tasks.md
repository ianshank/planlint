# Tasks: prepare-release-0-4-0

Drafted at `4278d4c` on `claude/lean-production-tree`, 2026-10-16, as Phase
2.2 and Phase 3 of the session plan for a lean production branch. Outside
`openspec/changes/lean-production-tree/`, that commit's tree is `dev` at
`c0ff090`. The plan is not tracked; every decision this package takes from it
is restated in `specs/release-0-4-0/spec.md`.

The package lands in two pull requests and a maintainer's sitting:

- **Pull request 1, the removals** (Milestones 0 to 4) **must not merge
  before `v0.3.0` is tagged and published**, and not before
  `lean-production-tree` has merged (DEC-RFR-001). It stays a GitHub draft
  until Milestone 0's gate is recorded here.
- **Pull request 2, the release prep** (Milestone 5), opens only after
  `lean-production-tree`, `harden-release-pipeline` and pull request 1 have
  merged into `dev`.
- **Milestone 6 is the maintainer's**, outside the tree. Its bullets are
  filled in afterwards with what was observed, in a later pull request into
  `dev`.

Every line number below was measured at `4278d4c` and is re-read at the
implementation branch's head before the milestone that uses it. A sibling
landing first moves a line without moving the fact. Every number names the
command that produced it.

## Measured at `4278d4c`

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR`: `55 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`, exit 0.
  That was before any file of this package existed.
- **The window is not open.** `git ls-remote --tags origin` prints
  `refs/tags/v0.1.0` and its peeled line, and nothing else.
  `curl -sS -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/json`
  prints `404`.
- **The 3.10 sites.** The caller's grep (`grep -rn "3\.10\|tomli"
  --include=*.py --include=*.toml --include=*.yml --include=*.md . | grep -v
  '^./openspec/changes/\|^./.git/'`), read with the untracked, ignored
  `build/` set aside, gives the sites the proposal's Evidence lists. Three
  sites carry the same reason without the string: `openspec_graph/thresholds.py:10-12`,
  `tests/test_static_ratchets.py:217-219` and `docs/next-steps.md:182-194`.
  `git grep -n "version_info\|py310\|(3, 10)\|(3, 11)\|contextlib.chdir\|tomllib"`
  finds no further code site.
- **Ruff at the new floor.** `python -m ruff check --no-cache
  --target-version py311 --select UP --output-format concise openspec_graph
  tools tests` (ruff 0.17.0) reports two findings and nothing else:
  `openspec_graph/cli.py:819:34: UP017` and `tests/support.py:89:8: UP036`.
  At the current floor, `python -m ruff check --no-cache --select UP ...`
  prints `All checks passed!`.
- **mypy at both floors.** `python -m mypy --config-file pyproject.toml
  --cache-dir=/dev/null --python-version 3.10` and the same with `3.11` both
  print `Success: no issues found in 119 source files`, exit 0. The per-code
  ceilings in `tests/test_static_ratchets.py` count codes the config
  disables, so they are re-measured in Milestones 1 and 3, not inferred.
- **The citations a deletion would break.** `grep -ln -- <name>
  openspec/changes/*/specs/*/spec.md`, per deleted or renamed test:
  - The Dockerfile guards are cited by `harden-ci-workflows`, and by
    `pin-actions-by-sha` for `test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry`.
  - The `test_deprecated_alias` substring is cited by `prepare-release-0-3-0`,
    `rename-cli-and-positioning`, `shape-the-test-suite` and
    `write-down-policies`.
  - `test_entry_points_wired_in_pyproject` is cited by
    `prepare-release-0-3-0` and `shape-the-test-suite`.
  - `test_the_default_python_agrees_across_workflows_action_and_dockerfile`
    is cited by `harden-ci-workflows`.
  - `test_agent_artifacts_are_excluded_from_the_docker_context` is cited by
    `lean-production-tree` alone.

  Of these, only `prepare-release-0-3-0` and `lean-production-tree` survive
  `lean-production-tree`'s deletion.
- **The release-prep sites.** The copyable-tag grep in the proposal prints
  `templates/spec-gate.yml:68`,
  `skills/planlint-spec-governance/assets/spec-gate.yml:68`,
  `skills/planlint-spec-governance/SKILL.md:178`, `README.md:403,449`,
  `.pre-commit-hooks.yaml:10`, and lines of `docs/distribution-plan.md` and
  `docs/reflection-plan-2026-10.md`, both deleted by `lean-production-tree`.
- **The artifact names.** `grep -rn "coverage-\${{\|coverage-Linux"
  .github/ tests/*.py tools/*.py docs/hooks.md` finds only the two upload
  steps in `ci.yml` (`:79`, `:127`). No job downloads a leg's artifact by
  name.

## Milestone 0 — Preconditions and review, recorded before pull request 1 leaves draft

- Pull request 1 stays a GitHub draft through this milestone. It is marked
  ready only after this milestone's gate is recorded here. No criterion can
  observe the release, so the draft state is what keeps the removals out of
  `dev` early (DEC-RFR-001).
- The package is reviewed by `spec-adversary` before any code. Its findings
  are resolved in the package and listed here with what changed.
- **`v0.3.0` is tagged, published and back-merged.** Record each output with
  the date:
  - `git ls-remote --tags origin v0.3.0` prints the tag and its peeled line.
  - `curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/0.3.0/json`
    prints `200`.
  - `git fetch origin && git merge-base --is-ancestor 'v0.3.0^{commit}' origin/dev`
    exits 0.
- **`lean-production-tree` has merged into `dev`.**
  - `git ls-remote --tags origin 'archive/*'` prints
    `refs/tags/archive/dev-record-2026-10`.
  - `git ls-tree --name-only origin/dev openspec/changes/` no longer lists
    `harden-ci-workflows`, `rename-cli-and-positioning`,
    `enterprise-hardening` or `ratchet-test-types-and-docstrings`.
  - `git ls-tree origin/dev openspec/changes/lean-production-tree` prints
    its tree.

  Record the merge commit.
- Bring this branch to that tip by merging `origin/dev` into it, never by
  rebasing or force-pushing. Re-run every grep under "Measured at `4278d4c`"
  at the branch head, and note any line that moved beside the bullet that
  uses it below.
- **The citation dependencies at the branch head.** Re-run the per-test
  grep. Expect `prepare-release-0-3-0` and `lean-production-tree`.
  `harden-release-pipeline`, if it has merged or is on `dev` by then, is
  read too. Any spec it adds to the list is amended in the milestone that
  deletes its test, in the same commit (R-RFR-16).
- **The required checks.** Record `gh api repos/ianshank/planlint/rulesets`.
  If any branch ruleset's `required_status_checks` names a `test (3.10)`
  leg rather than `ci-ok` alone, the owner edits that ruleset in the same
  sitting as the merge, or pull request 1 cannot pass its own checks.
- **Merge hazards**, resolved on purpose whichever sibling lands first:
  - `.github/dependabot.yml`: `harden-release-pipeline` adds `cooldown:` to
    the `github-actions` entry, and this change deletes the `docker` entry.
    Keep both.
  - `tests/test_release_surface.py`: `harden-release-pipeline` adds
    release-job assertions near the top, and this change deletes the two
    packaging tests further down. They are separate hunks.
  - `docs/hooks.md`: `harden-release-pipeline` edits the `release` row,
    while this change edits the `test` row and the posture paragraph.
  - `SECURITY.md`: `harden-release-pipeline` rewrites it, and only
    Milestone 5 touches its version.
  - `CHANGELOG.md` `[Unreleased]`: all three packages add groups there.
  - `.claude/agents/planlint-verifier.md:22` and `docs/aqa.md:113-114`:
    `lean-production-tree` has already edited both lines. Edit the merged
    text.
- **Gate:** every precondition above recorded with its output and the date
  — the tag, the PyPI `200`, the ancestry exit 0, `lean-production-tree`'s
  merge commit and the archive tag, the citation dependencies and the
  rulesets — then `make test` on the branch head. Only then is pull
  request 1 marked ready, and no milestone below starts before this is
  recorded.

## Milestone 1 — The Python 3.11 floor

- `pyproject.toml`:
  - line 35 → `requires-python = ">=3.11"`;
  - line 47's classifier is deleted;
  - lines 271-273 (the `tomli` sentence and the `#` line after it) and line
    301 (the `tomli` entry) are deleted, and the rest of the dev extra and
    its comment stay;
  - line 431 → `python_version = "3.11"`;
  - lines 464-470 (the `tomli` override and its comment, with the blank line
    before them) are deleted.

  Line 156's dated measurement stays (C-RFR-5) (R-RFR-3, R-RFR-4).
- `.github/workflows/ci.yml:48` → `python-version: ["3.11", "3.12", "3.13",
  "3.14"]`, in the same commit as the classifier
  (`test_classifiers_equal_the_hard_matrix_legs` goes red with either alone).
  `docs/hooks.md:76` → `` `test` (3.11–3.14) `` in that commit too
  (`test_hooks_test_row_names_the_matrix_bounds`) (R-RFR-3).
- `tests/support.py`:
  - `read_pyproject` (`:74-95`) imports `tomllib` with the module's other
    imports and opens the file with it directly, still returning through
    `parsed: dict[str, Any]`;
  - its docstring keeps the first paragraph's purpose and drops the 3.10 leg
    and the R-TDR-6 paragraph;
  - `working_directory`'s docstring (`:228-235`) says why the helper is
    spelled out — it restores in a `finally` — without claiming the 3.10
    floor, and the helper is unchanged.

  This also clears ruff's UP036 (R-RFR-4, R-RFR-7, DEC-RFR-004).
- `tests/ratchet_support.py`:
  - `:47` `MYPY_FIXED["python_version"]` → `"3.11"`;
  - `:62-64`, the comment loses ", and R-TDR-6's one allowed site", and
    `ALLOWED_VERSION_CHECK` is deleted;
  - in `hidden_code` (`:356-369`), the `allowed` flag and its branch are
    deleted, so every version or platform branch test is a problem, and the
    docstring ends at "on ``sys.version_info`` or ``sys.platform``"
    (R-RFR-3, R-RFR-5, DEC-RFR-002).
- `tests/test_static_ratchets_planted.py`:
  - `:25`, the `ALLOWED_VERSION_CHECK` import is deleted;
  - `:181`, `second-check-at-the-site`, is deleted;
  - `:182`, `allowed-site`, becomes `former-allowed-site`, the same planted
    text with the literals `"tests/support.py"` and `"read_pyproject"`,
    expecting `"branch test in read_pyproject"`.

  Write that case first against the unedited `hidden_code` and record it red
  once (the old exemption passes it), then green after the deletion
  (R-RFR-5, AC-RFR-4).
- `tests/test_static_ratchets.py:217-219`: the docstring ends "no unchecked
  name or version or platform branch under `tests/`" (R-RFR-7).
- `tests/workflow_support.py`: add `requires_python_floor(pyproject:
  dict[str, Any]) -> str | None`. It returns `X.Y` when
  `project.requires-python` is exactly `>=X.Y`, and `None` for any other
  shape, so that a `~=` or a compound specifier fails the guards rather
  than being read loosely. Full docstring.
- `tests/test_ci_workflow.py`: `test_mypy_is_strict_and_warns_on_unreachable_code`
  (`:49-56`) asserts `mypy.get("python_version") == requires_python_floor(read_pyproject())`
  and that the floor is not `None`. Its docstring says "the floor
  `requires-python` declares", not "3.10" (R-RFR-3, AC-RFR-2).
- `tests/test_workflow_python.py`, the floor guard. Write both tests against
  the unedited tree first, so the red state is seen once; record the
  offender list here, then land the edits above and watch them go green
  (R-RFR-6, DEC-RFR-003):
  - `_floor_disagreements(sources: dict[str, tuple[str | None, str]]) -> list[str]`
    is a pure function over `{source name: (value, locator)}`. It names
    every missing value and, on disagreement, every source with its value
    and locator.
  - `test_the_python_floor_agrees_across_every_source` (integration) feeds
    it six sources:
    - `requires_python_floor(read_pyproject())`;
    - `min(hard legs)` from `_matrix_versions(_ci_text())`;
    - `min` of `_classifier_versions(...)`;
    - `[tool.mypy] python_version`;
    - the one line of `README.md` matching `Python (\d+\.\d+)\+`, located as
      `README.md:<line>` (zero or several matches is a failure);
    - the `compatibility:` frontmatter line of
      `skills/planlint-spec-governance/SKILL.md` matching
      `Python (\d+\.\d+) or newer`, located the same way.
  - `test_a_stale_python_floor_is_named_with_its_source` (unit, non-success)
    plants a README source at `3.10` against `3.11` elsewhere and asserts the
    message names `README.md:<line>` and both values. It plants
    `requires-python` at `3.10` against a lowest leg of `3.11` and asserts
    both sources are named. It plants a source with no value and asserts it
    is reported, not skipped (AC-RFR-5, AC-RFR-6).
- `openspec_graph/cli.py:35` and `:819`: ruff's UP017 —
  `from datetime import UTC, datetime` and `datetime.now(UTC)`. This is a
  behaviour-identical alias, and nothing else in the file changes in this
  milestone (R-RFR-8).
- Comments and docstrings, each a rewording (R-RFR-7, C-RFR-1):
  - `openspec_graph/log.py:40-41`: the stdlib mapping is used; the claim
    that the repository supports 3.10 is dropped. The code is unchanged.
  - `openspec_graph/thresholds.py:10-12` and `:128-133`: the scanner was
    chosen under the 3.10 floor so the card could not differ across the
    matrix (DEC-TC-002); `tomllib` is on every supported interpreter now,
    and swapping it in is `docs/next-steps.md` item 7a's change. The code is
    unchanged.
  - `tools/_common.py:203-205`, `:231-233` and `:333-334`, and
    `tools/check_wheel_metadata.py:46-49`: the same form.
  - `tests/test_enterprise.py:493`: "(3.11+)".
  - `tests/test_properties.py:31`: "so 3.11 and 3.13 draw different
    characters".
- Prose (R-RFR-7):
  - `README.md:39` → "Python 3.11+.";
  - `docs/aqa.md:150` → "Ubuntu 3.11–3.14" and `:287` → "Python 3.11–3.14";
  - `skills/planlint-spec-governance/SKILL.md:5` → "Python 3.11 or newer",
    with the planlint version unchanged in this pull request;
  - `docs/policies.md:82-85` → past tense: Python 3.10 was announced in the
    0.3.0 notes, supported through every 0.3.x release and dropped in 0.4.0;
  - `docs/next-steps.md:182-194`, item 7a: the last two sentences become
    "now unblocked: the 3.11 floor puts `tomllib` on every supported
    interpreter, and the swap stays its own package, which must show the
    dialect card byte-identical".
- Run `make lint`. Record every finding the new floor produced and its fix.
  Expect only the UP017 above, since UP036 left with the branch. Add no
  ignore, no waiver and no `target-version` (R-RFR-8, AC-RFR-7).
- Run `make typecheck` and `python -m pytest tests/test_static_ratchets.py -q`.
  Lower any per-code ceiling the run names to the measured count, and
  record each change. A ceiling only falls.
- **Gate:** `make pre-pr`

## Milestone 2 — The `specgraph` alias

- `tests/test_cli_surface.py`, written first so its red state is seen once.
  `test_entry_points_declare_planlint_and_no_alias` replaces
  `test_entry_points_wired_in_pyproject` (`:227-234`). It reads
  `read_pyproject()["project"]["scripts"]`, asserts it equals
  `{"planlint": "openspec_graph.cli:main"}`, and asserts
  `not hasattr(openspec_graph.cli, "main_deprecated")`, with messages naming
  what was found. Record it red against the unedited tree, then green after
  the edits below (R-RFR-10, AC-RFR-10).
- `pyproject.toml:61-69`: `specgraph = …` is deleted. The comment says
  `planlint` is the command; the `specgraph` alias warned through every
  0.3.x release and was removed in 0.4.0; the waiver prefix,
  `openspec/specgraph.json` and `[tool.specgraph]` keep the name as stable
  identifiers (R-RFR-9).
- `openspec_graph/cli.py`: `_DEPRECATION_WARNING` and `main_deprecated`
  (`:1010-1026`) are deleted, and the comment at `:991-992` says "the
  `planlint` entry point calls main()" (R-RFR-9).
- `tests/test_cli_surface.py`, the rest:
  - `main_deprecated` leaves the import at `:20`;
  - the module docstring (`:1`) says "entry point" and drops "deprecation
    alias", and the section comment at `:224` follows;
  - `test_deprecated_alias_warns_to_stderr_and_delegates`,
    `test_deprecated_alias_preserves_failure_exit_code`,
    `test_deprecated_alias_keeps_stdout_parseable` (`:258-301`) and
    `test_deprecated_alias_names_its_removal_version` (`:514-530`) are
    deleted;
  - `test_primary_command_emits_no_deprecation_warning` and
    `test_planlint_log_level_env_var_works` are unchanged (R-RFR-10).
- In the same commit as the deletions,
  `openspec/changes/prepare-release-0-3-0/specs/release-readiness/spec.md`
  is amended at these lines and nowhere else (R-RFR-16, DEC-RFR-007):
  - AC-REL-5's verification line keeps only
    `test_primary_command_emits_no_deprecation_warning` in its selector,
    with its stage;
  - AC-REL-6's verification line becomes its stage alone;
  - each line carries "(amended by `prepare-release-0-4-0`: the alias and
    the tests that verified it at 0.3.0 were removed in 0.4.0; they are read
    at the `v0.3.0` tag)".

  The criteria keep their ticks and their text. Run
  `python -m pytest tests/test_spec_test_citations.py -q` on that commit.
- Prose (R-RFR-11):
  - `README.md:77-84`: the command was renamed from `specgraph` to
    `planlint`; the `specgraph` alias warned through every 0.3.x release and
    was removed in 0.4.0, so run `planlint`. The waiver comment syntax, the
    config file and the `[tool.specgraph]` section keep the name as stable
    contract identifiers, and the link to `docs/policies.md` stays.
  - `docs/policies.md:74-79`: past tense — the alias warned through every
    0.3.x release and was removed in 0.4.0.
- Confirm `SPECGRAPH_LOG_LEVEL` is untouched: `git diff -- openspec_graph/log.py tools/_common.py`
  shows only Milestone 1's comment rewording, and `test_verbose_via_env_var`
  passes (R-RFR-11, AC-RFR-12).
- **Gate:** `make test`

## Milestone 3 — The Dockerfile

- The order is set by the one-directional couples. Deleting `Dockerfile`
  or `.dockerignore` while a test reads it goes red, while deleting the
  tests first stays green. The Dependabot `docker` entry leaving while
  `test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry` still
  reads a digest-pinned `FROM` goes red. Land the test deletions, the file
  deletions, the Dependabot edit and the `lean-production-tree` amendment
  in one commit (R-RFR-12, R-RFR-13).
- `tests/test_release_surface.py:193-235`:
  `test_docker_build_context_is_sufficient_for_the_dynamic_version` and
  `test_agent_artifacts_are_excluded_from_the_docker_context` are deleted,
  along with any import only they used (`make lint` names it).
- `tests/test_workflow_pins.py`:
  - the docstring (`:1-6`) drops "the Dockerfile and its update bot" and
    R-HCW-13 and R-HCW-14;
  - `DOCKERFILE`, `WRITING_VERBS` and `_dockerfile_from` leave the import
    (`:20-34`);
  - `_dockerfile_offenders` and `_user_override_offenders` (`:154-191`) and
    `_docker_watch_offenders` (`:230-236`) are deleted;
  - the R-HCW-13/14 section is deleted: `:416-471`, the four tree tests,
    `test_a_non_root_dockerfile_without_the_override_is_named` and
    `test_a_weak_dockerfile_is_named` with its parametrize;
  - `test_an_unwatched_digest_is_named` (`:491-499`) is deleted;
  - `_dependabot_entries` (`:194-228`) and
    `test_a_plural_directories_entry_is_read_as_one_pair_per_directory`
    (`:473-489`) stay, their fixture unchanged (R-RFR-13).
- `tests/workflow_support.py`: `DOCKERFILE` (`:31`), the `WRITING_VERBS`
  comment and constant (`:64-68`), and `_FROM` with `_dockerfile_from`
  (`:156-163`) are deleted.
- `tests/test_workflow_python.py`:
  - `DOCKERFILE` and `_dockerfile_from` leave the import (`:18`, `:23`);
  - `_dockerfile_tag_version` (`:129-134`) is deleted;
  - `test_the_default_python_agrees_across_workflows_action_and_dockerfile`
    (`:187-201`) becomes `test_the_default_python_agrees_across_workflows_and_action`.
    Its docstring says the two env values and the composite action's input
    default are one version (AC-HCW-13, with its image source retired by
    DEC-RFR-006), and it loses only the line that adds the image's base tag
    to `sources`;
  - `test_a_disagreeing_default_is_named` loses only its
    `_dockerfile_tag_version` assertion (`:214`).
- `tests/test_adopter_urls.py:168`: `"Dockerfile"` leaves the glob tuple.
- Delete `Dockerfile` and `.dockerignore`.
- `.github/dependabot.yml`: `:3-4` becomes "Scope is deliberately narrow:
  GitHub Actions only.", and the `docker` entry is deleted (`:61-78`, with
  the blank line before it). `test_route_enforcement_and_dependabot_flip_together`
  stays green, since the entry and its `target-branch` leave together
  (R-RFR-12, AC-RFR-13).
- In the same commit,
  `openspec/changes/lean-production-tree/specs/production-tree/spec.md` is
  amended at these clauses only, each marked "(amended by
  `prepare-release-0-4-0`, which deletes `.dockerignore`)" (R-RFR-16,
  DEC-RFR-007):
  - R-LPT-7's "`.dockerignore` MUST keep excluding …" clause becomes
    conditional on the file existing;
  - AC-LPT-11 loses its "`.dockerignore` still keeps every agent artifact
    out of the build context" clause and the
    `test_agent_artifacts_are_excluded_from_the_docker_context` token from
    its selector, keeping its stage.

  Any `harden-release-pipeline` clause Milestone 0 listed is amended the
  same way. Run `python -m pytest tests/test_spec_test_citations.py -q` on
  that commit.
- Prose (R-RFR-14, DEC-RFR-006):
  - `docs/aqa.md:39-48`: the image's base tag leaves the list of pins that
    are not thresholds, which keeps the action versions and the Python
    matrix; the second pin held by a test becomes "the composite action's
    `python-version` default must equal the workflows' `PYTHON_DEFAULT`".
  - `docs/aqa.md:113-114`, as `lean-production-tree` left it: the
    build-context clause goes.
  - `docs/hooks.md:111-112`: "the guard holds that value equal to the
    composite action's input default and to one of the `test` matrix's hard
    legs".
  - `docs/next-steps.md:254-256`, item 9, is rewritten. The `Dockerfile` was
    removed in 0.4.0: it was built, published and scanned nowhere, and
    `pip install planlint` in any `python` image, or the composite action,
    is the delivery path. Reopen only for an adopter who needs a published
    image, and then with a CI build, a registry push, an attestation by
    digest and base-image CVE triage, not the recipe alone. Name the package
    that removed it.
  - `.claude/agents/planlint-verifier.md:22`: ", the `.dockerignore` build
    context" goes from the list.
  - `.gitignore:57-58`: the `# Docker / local builds` block goes.
- Re-run `make typecheck` and the static ratchets after the deletions, and
  lower any ceiling they name.
- Record the grep: `git ls-files | grep -v -e '^CHANGELOG.md$' -e '^openspec/changes/' | xargs grep -n -i -e dockerfile -e dockerignore -e 'docker base' -e 'docker image'`.
  Expect only `docs/next-steps.md` item 9's record of the removal
  (AC-RFR-15).
- **Gate:** `make pre-pr`

## Milestone 4 — Release notes, the selectors and the observations

- `CHANGELOG.md` `[Unreleased]`: add one group, headed
  `### Removed — Python 3.10, the specgraph alias, the Dockerfile` (with
  `specgraph` in backticks in the file), after any `Removed` group a sibling
  wrote. Its entries are led by **`prepare-release-0-4-0`** and say what
  R-RFR-15 says, in the file's voice:
  - **Python 3.10:** `requires-python` is `>=3.11`; the classifier, the
    matrix leg, the `tomli` dev extra and its mypy override are gone; mypy
    checks against 3.11; announced in the 0.3.0 notes.
  - **The `specgraph` command:** removed, so run `planlint`; the waiver
    syntax, `openspec/specgraph.json`, `[tool.specgraph]` and
    `SPECGRAPH_LOG_LEVEL` are unchanged; announced in the 0.3.0 notes.
  - **`Dockerfile`, `.dockerignore` and the `docker` Dependabot entry:**
    removed. The image was never built in CI, published or scanned, and
    `pip install planlint` in any `python` image or the composite action
    replaces it. The entry says plainly that this removal was not announced
    under `Deprecated`, because nothing was shipped to deprecate, and that
    it supersedes `harden-ci-workflows`' Dockerfile requirements.

  No released section changes. `git diff -- CHANGELOG.md` shows only
  `[Unreleased]` lines (R-RFR-15, C-RFR-4, AC-RFR-17).
- Re-point this package's stage-only criteria to the tests that now exist,
  keeping each stage:
  - AC-RFR-5 → `test_the_python_floor_agrees_across_every_source`;
  - AC-RFR-6 → `test_a_stale_python_floor_is_named_with_its_source`;
  - AC-RFR-10 → `test_entry_points_declare_planlint_and_no_alias`;
  - AC-RFR-14 gains `test_the_default_python_agrees_across_workflows_and_action`
    in its selector.

  Then run `python -m pytest tests/test_spec_test_citations.py -q` and
  confirm every selector resolves (AC-RFR-18).
- **The wheel observations** (AC-RFR-9, AC-RFR-10, DEC-RFR-010). Run
  `make wheel-check`, then:
  - `unzip -p dist/planlint-*.whl '*.dist-info/METADATA' | grep '^Requires-Python'`
    prints `Requires-Python: >=3.11`.
  - `python -m pip install --dry-run --no-deps --only-binary=:all: --python-version 3.10 dist/planlint-*.whl`
    exits non-zero, and its message names the Python requirement.
  - The same command with `--python-version 3.11` exits 0.
  - `unzip -p dist/planlint-*.whl '*.dist-info/entry_points.txt'` prints
    `[console_scripts]` and the single line
    `planlint = openspec_graph.cli:main`.

  Record each output with the pip version (pip 22.2 or later accepts
  `--dry-run` with `--python-version`).
- Run `make stage-citations` and confirm that this package's verification
  lines add no stage to the set no workflow runs by name: only `test` and
  `pre-pr` are cited (DEC-RFR-010).
- Confirm the diff touches none of the fixtures and dated comments C-RFR-5
  lists, using `git diff -U0 origin/dev -- tests/test_workflow_python.py tests/test_ci_workflow.py tests/test_static_ratchets_planted.py pyproject.toml .pre-commit-config.yaml`
  read for those lines (AC-RFR-19).
- Run `planlint --target . validate --fail-on INFO --change prepare-release-0-4-0`,
  then `planlint --target . validate --fail-on ERROR` on the whole tree,
  and record both exit codes.
- Record AC-RFR-20's first half (Milestone 0's facts) and AC-RFR-25's first
  run (`make pre-pr` on the removals' head) here, and tick each criterion
  of Milestones 1 to 4 only as it is verified.
- **Gate:** `make pre-pr`

## Milestone 5 — The 0.4.0 release-prep pull request

- **Preconditions**, each recorded with its output and the date. `git fetch
  origin`, then on `origin/dev`:
  - `lean-production-tree` has merged (Milestone 0's facts);
  - `harden-release-pipeline` has merged: its merge commit is recorded, and
    `release.yml` carries what its spec names;
  - pull request 1 has merged: its merge commit is recorded, and
    `git ls-tree origin/dev Dockerfile` prints nothing.

  No other pull request merges into `dev` from here until the promotion
  (R-RFR-2, AC-RFR-20).
- Cut the branch from `origin/dev` and follow
  `.claude/skills/planlint-release/SKILL.md` §1 and `docs/hooks.md`
  "Releasing", as `lean-production-tree` left it (R-RFR-21).
- `openspec_graph/__init__.py:15` → `__version__ = "0.4.0"`, and nothing
  else in the module (R-RFR-17). Run `make test` on the bump alone and
  record which tests fail. Expect, among others:
  - `test_skill_metadata_version_matches_the_package`;
  - `test_ci_template_pins_the_floor_the_skill_enforces`;
  - `test_every_changelog_version_links_to_its_release_tag`;
  - `test_every_copyable_tag_ref_names_the_current_version`, naming each
    stale ref with its file and line;
  - `test_generated_artifacts_are_fresh`.

  Record the offender list `test_every_copyable_tag_ref_names_the_current_version`
  prints. It must equal what the copyable-tag grep prints at that commit.
- Run `make skill-manifests` and commit the regenerated
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
  `python tools/render_plugin_manifests.py --check` and
  `python tools/render_rule_catalog.py --check` both exit 0 (R-RFR-17,
  AC-RFR-22).
- `skills/planlint-spec-governance/SKILL.md` (R-RFR-18):
  - `:5`: "version 0.4.0 or newer", with Milestone 1's "Python 3.11 or
    newer" kept;
  - `:7` and `:8`: `0.4.0`;
  - `:178`: "pin `@v0.4.0`".
- The own-action refs, all in this commit, before the tag (R-RFR-19):
  - `templates/spec-gate.yml:68` → `@v0.4.0`, then copy the file over
    `skills/planlint-spec-governance/assets/spec-gate.yml`
    (`test_skill_asset_matches_template`);
  - `README.md:403,449` → `@v0.4.0`;
  - `.pre-commit-hooks.yaml:10` → `rev: v0.4.0`;
  - any `@v0.3.0` the guard names in `docs/hooks.md`'s runbook.
- The hand edits no test names:
  - `.github/actions/planlint/action.yml:34` → `e.g. "0.4.0"`, with nothing
    else in the file changed (`test_the_action_declares_exactly_the_v1_inputs`);
  - `SECURITY.md`'s supported-versions statement, as
    `harden-release-pipeline` left it, names `0.4.0` as the latest released
    and only supported version (R-RFR-19, DEC-RFR-011).
- `CHANGELOG.md` (R-RFR-20, DEC-RFR-009):
  - Insert `## [0.4.0] — <date>` directly below `## [Unreleased]` and its
    blank line, the date being the day the tag will be pushed. Set it the
    morning of the sitting and finish Milestone 6 that day.
  - Every group that sat under `[Unreleased]` — `lean-production-tree`'s,
    `harden-release-pipeline`'s, this package's and any other — now sits
    under the new heading, verbatim and in order.
  - Add `[0.4.0]: https://github.com/ianshank/planlint/releases/tag/v0.4.0`
    above the `[0.3.0]:` line, and make the `[Unreleased]:` line
    `https://github.com/ianshank/planlint/compare/v0.4.0...HEAD`.
  - `git diff -- CHANGELOG.md` shows no line of a released section changed.
- `make test` green, recording that each test listed above went green on
  its edit, then `make pre-pr` exit 0 on the head (AC-RFR-21, AC-RFR-23,
  AC-RFR-24, AC-RFR-25). Squash-merge into `dev`.
- **Gate:** `make pre-pr`

## Milestone 6 — Promote, tag, publish, observe, record (the maintainer, outside the tree)

- **Route and promotions.**
  - `python tools/check_promotion.py route --event pull_request --base qa --head dev --base-repo ianshank/planlint --head-repo ianshank/planlint`
    exits 0.
  - Open the `dev → qa` pull request, wait for `ci-ok` on its
    `pull_request` run, and merge with a merge commit.
  - Then `qa → main` by merge commit, which is **M2**. No other pull request
    merges into `dev` during the sitting (R-RFR-21).
- **Prove M2.** Run:

  ```
  git fetch origin; M2=$(git rev-parse origin/main)
  git rev-parse "$M2^1"                 # production's previous tip: v0.3.0^{commit}, unless a hotfix tag followed it
  test "$(git rev-parse "$M2^2")" = "$(git rev-parse origin/qa)"
  git diff --quiet origin/qa "$M2" && git diff --quiet origin/dev "$M2"
  python tools/check_promotion.py tag-ancestry --sha "$M2" --fetch; echo $?   # 0
  ```

  Record each output (AC-RFR-26).
- **The dry run.** `gh workflow run release.yml --ref main`, then
  `gh run watch <id> --exit-status`. `gate` and `build` must be green, and
  the tag-only jobs skipped. Confirm the `[0.4.0]` heading reads today; if
  not, open a new release-prep pull request and promote again, and never
  commit on `main` (DEC-RFR-009).
- **Tag.** `git tag -a v0.4.0 "$M2" -m "planlint 0.4.0" && git push origin v0.4.0`,
  pushed by the owner's token. Record the tag's commit and the date
  (R-RFR-21).
- **Watch.** Record the run id and every job `release.yml` defines, each
  with its result. That includes the jobs `harden-release-pipeline` added,
  and the `build` job's tag-versus-package check (R-RFR-22, AC-RFR-26).
- **Attestations.** For the wheel and the sdist:
  - `https://pypi.org/integrity/planlint/0.4.0/<filename>/provenance`
    returns HTTP `200` with a bundle whose publisher is GitHub;
  - `pipx run pypi-attestations verify pypi --repository https://github.com/ianshank/planlint pypi:<filename>`
    reports success;
  - where `harden-release-pipeline` added build provenance,
    `gh attestation verify <file> --repo ianshank/planlint --signer-workflow ianshank/planlint/.github/workflows/release.yml`
    passes.

  Record each verdict with the date (AC-RFR-26).
- **The Release and the tree.**
  - `gh release view v0.4.0 --json assets --jq '[.assets[].name]'` names the
    wheel and the sdist.
  - `git ls-tree -r --name-only v0.4.0 | grep -E '^(evals/|docs/.*-plan\.md|docs/peer-review-|Dockerfile$|\.dockerignore$)'`
    prints nothing.

  Record both (AC-RFR-26).
- **A fresh install.** In a fresh venv:
  - `python -m pip install planlint==0.4.0`;
  - `planlint --version` prints `planlint 0.4.0`;
  - `test ! -e "$VIRTUAL_ENV/bin/specgraph"` exits 0;
  - `planlint --target <clone at M2> validate --fail-on ERROR` exits 0, and
    the spec count it prints is recorded.

  Then `python -m pip install --dry-run --no-deps --only-binary=:all: --python-version 3.10 planlint==0.4.0`
  exits non-zero, naming the Python requirement, and the `3.11` control
  resolves. Record all of it (AC-RFR-27).
- **Back-merge.** `git switch -c sync/main-into-dev origin/dev && git merge --no-ff origin/main`,
  then a pull request into `dev` merged by merge commit. `qa` is never
  back-merged.
- **Record**, in a later pull request into `dev`, never a commit on `main`:
  M2, the tag's commit and date, the run ids, every observation above, and
  AC-RFR-20's second half. Tick AC-RFR-20 and AC-RFR-24 to AC-RFR-27 only
  once each is recorded. Then run
  `planlint --target . validate --fail-on ERROR --change prepare-release-0-4-0`
  and the whole tree, and record both exit codes (C-RFR-6, DEC-RFR-010).
- **The sweep.** It is the runbook's last step and not this package's: it
  removes every package 0.4.0 or an earlier release shipped once its
  `tasks.md` records the release. This package goes with
  `lean-production-tree`, `harden-release-pipeline` and the two 0.3.0
  packages, whose open owner actions move to `docs/next-steps.md`. The
  sweep never empties `openspec/changes/`: if no open package would remain,
  the next package lands first (DEC-LPT-012).
- **Gate:** `make pre-pr`
