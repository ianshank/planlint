# Tasks: prepare-release-0-4-0

Drafted at `4278d4c` on `claude/lean-production-tree`, 2026-10-16, as Phase
2.2 and Phase 3 of the session plan for a lean production branch, and
revised at `f0063a6` and `eb14cba` on `claude/prepare-release-0-4-0` to
resolve the first and second adversarial reviews (Milestone 0). Outside the
change package each branch adds, these trees are `dev` at `c0ff090`. The
plan is not tracked; every decision this package takes from it is restated
in `specs/release-0-4-0/spec.md`.

The package lands in two pull requests and a maintainer's sitting:

- **Pull request 1, the removals and the Dockerfile's deprecation**
  (Milestones 0 to 4) **must not merge before `v0.3.0` is tagged and
  published**, and not before `lean-production-tree` has merged
  (DEC-RFR-001). It stays a GitHub draft until Milestone 0's gate is
  recorded here.
- **Pull request 2, the release prep** (Milestone 5), opens only after
  `lean-production-tree`, `harden-release-pipeline` and pull request 1 have
  merged into `dev`.
- **Milestone 6 is the maintainer's**, outside the tree. Its bullets are
  filled in afterwards with what was observed, in a later pull request into
  `dev`.

Every line number below was measured at `4278d4c`, `f0063a6` or `eb14cba`
and is re-read at the implementation branch's head before the milestone
that uses it. A sibling landing first moves a line without moving the fact.
Every number names the command that produced it.

## Measured at `4278d4c`, re-checked at `f0063a6` and `eb14cba`

- **The gate before the draft.** `planlint --target . validate --fail-on
  ERROR` at `4278d4c`: `55 spec(s) checked · 0 error · 0 warn · 0 info`,
  `PASS`, exit 0, before any file of this package existed. At `f0063a6`
  and at `eb14cba`, before each revision: `55 spec(s) checked · 0 error · 0
  warn · 0 info`, `PASS`, exit 0. The counts include this package's spec on
  `claude/prepare-release-0-4-0` and `lean-production-tree`'s on
  `claude/lean-production-tree`.
- **The window is not open.** `git ls-remote --tags origin` prints
  `refs/tags/v0.1.0` and its peeled line, and nothing else.
  `curl -sS -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/planlint/json`
  prints `404`.
- **The 3.10 sites.** The caller's grep (`grep -rn "3\.10\|tomli"
  --include=*.py --include=*.toml --include=*.yml --include=*.md . | grep -v
  '^./openspec/changes/\|^./.git/'`), read with the untracked, ignored
  `build/` set aside, gives the sites the proposal's Evidence lists. Its
  lines in `docs/differentiation-roadmap.md` and
  `docs/reflection-plan-2026-10.md` — eight, by the same grep piped to
  `grep -c 'differentiation-roadmap\|reflection-plan'` — are set aside too,
  because `lean-production-tree` deletes both files. Three sites carry the
  same reason without the string: `openspec_graph/thresholds.py:10-12`,
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
  disables, so they are re-measured in Milestone 1, not inferred.
- **The citations the alias deletion would break.** At `f0063a6`, the
  script in the proposal's Evidence (`gone` = the `test_deprecated_alias_`
  tests and `test_entry_points_wired_in_pyproject`) prints citations from
  three packages:
  - `prepare-release-0-3-0`: the four alias tests and the entry-point test;
  - `rename-cli-and-positioning`: `test_deprecated_alias` and
    `test_deprecated_alias_keeps_stdout_parseable`;
  - `write-down-policies`: three alias tests.

  `shape-the-test-suite` mentions the tests and cites none.
  `lean-production-tree` deletes the second and third, so only
  `prepare-release-0-3-0` survives into the tree this change lands on.
- **pip.** `pip --version` prints `pip 24.0`. The review measured that
  `pip install --dry-run --python-version 3.10` accepts the wheel on pip
  24.0 and 24.1, and that `pip download ... --python-version 3.10` refuses it
  from 24.0 on (DEC-RFR-010).
- **The release-prep sites.** The copyable-tag grep in the proposal prints
  `templates/spec-gate.yml:68`,
  `skills/planlint-spec-governance/assets/spec-gate.yml:68`,
  `skills/planlint-spec-governance/SKILL.md:178`, `README.md:403,449`,
  `.pre-commit-hooks.yaml:10`, and lines of `docs/distribution-plan.md` and
  `docs/reflection-plan-2026-10.md`, both deleted by `lean-production-tree`.
  `SECURITY.md:56-57` calls the supported `0.3.0` "the first release
  published to PyPI".
- **The artifact names.** `grep -rn "coverage-\${{\|coverage-Linux"
  .github/ tests/*.py tools/*.py docs/hooks.md` finds only the two upload
  steps in `ci.yml` (`:79`, `:127`). No job downloads a leg's artifact by
  name.
- **`lean-production-tree`'s pull request.** That package's `tasks.md`
  records `gh api repos/ianshank/planlint/pulls/58 --jq
  '{draft,base:.base.ref,head:.head.ref}'` as
  `{"base":"dev","draft":true,"head":"claude/lean-production-tree"}`, and
  `git ls-tree --name-only origin/dev openspec/changes/` does not list
  `lean-production-tree`, so the squash that merges it is the commit that
  adds its package to `dev`.

## Milestone 0 — Preconditions and review, recorded before pull request 1 leaves draft

- Pull request 1 stays a GitHub draft through this milestone. It is marked
  ready only after this milestone's gate is recorded here. No criterion can
  observe the release, so the draft state is what keeps the removals out of
  `dev` early (DEC-RFR-001).
- The package is reviewed by `spec-adversary` before any code. Its findings
  are resolved in the package and listed here with what changed.
  **Recorded — first review, at `f0063a6`:**
  - **HIGH-1.** Removing the Dockerfile without a window contradicted
    `docs/policies.md:66-73`. The fallback is adopted: the Dockerfile is
    deprecated in 0.4.0 and removed in 0.5.0, with one header line and
    `docs/next-steps.md` item 9. R-RFR-12 to R-RFR-14, AC-RFR-13 to
    AC-RFR-15 and the deletion milestone are withdrawn, with their numbers
    not reused. The renamed agreement test is dropped as no longer needed.
    R-RFR-23, AC-RFR-28 and Milestone 3 now carry the deprecation, and
    DEC-RFR-006 is rewritten with what the 0.5.0 package must do.
  - **MEDIUM-1.** The edit to `prepare-release-0-3-0` now names itself a
    supersession of DEC-LPT-004's no-edit rule for two verification lines
    only, with its reasons (DEC-RFR-007). The `lean-production-tree`
    amendment is dropped.
  - **MEDIUM-2.** The 3.10 refusal uses `pip download`, requires "requires
    a different Python", and keeps a 3.11 control. The "pip 22.2 or later"
    note is gone (DEC-RFR-010, AC-RFR-9, Milestone 4).
  - **MEDIUM-3.** The floor guard's red-first sequence, the planted
    readers, the `~=` specifier and the numeric comparison (R-RFR-6,
    DEC-RFR-003, AC-RFR-5, AC-RFR-6, Milestone 1).
  - **LOW.** These were also resolved:
    - AC-RFR-21's red claim is narrowed;
    - Milestone 5 reinstalls after the bump;
    - AC-RFR-3's `tomli` clause is read directly;
    - AC-RFR-12 loses its non-success label;
    - the leftovers are named in Milestone 2;
    - the citation count is re-derived with a named script, and the
      policies range is corrected;
    - R-RFR-2's "nothing merges between" gets a tip check (Milestones 5
      and 6);
    - the Dependabot timing note is in DEC-RFR-006;
    - R-RFR-19 is reconciled with the placeholder rule (DEC-RFR-011).

  **Recorded — second review, at `eb14cba` (no HIGH):**
  - **MEDIUM-1.** The no-stderr reason was false. DEC-RFR-006 now grounds
    the window in the policy's scope: its stderr clause covers what the tool
    runs, and planlint runs neither the recipe nor the image. It also
    rejects an entrypoint wrapper.
  - **MEDIUM-2.** The tagged-tree check is a list derived from
    `lean-production-tree`'s squash commit, not a pattern (R-RFR-22,
    AC-RFR-26, DEC-RFR-010, Milestone 6). `LPT` is found as the commit
    that adds that package's proposal to `dev`, cross-checked against its
    pull request's merge commit, below.
  - **MEDIUM-3.** DEC-RFR-007 cites DEC-WCA-022 as the planned precedent
    and DEC-LPT-007's mooting as why it never ran.
  - **LOW-1.** A further spec named by the citation measure stops
    implementation for a revision; it is never amended in passing
    (R-RFR-16, AC-RFR-18, DEC-RFR-007, the proposal's What Changes and
    Non-Goals, Milestones 0 and 2).
  - **LOW-2.** The stale-metadata tests are described as a set with
    examples, not counted (Milestone 5).
  - **LOW-3.** The merge-hazard list gains `docs/next-steps.md`,
    `README.md`, `pyproject.toml` and `tests/support.py`.
  - **LOW-4.** The 0.5.0 brief drops `import re` only if nothing else uses
    it.
  - **LOW-5.** Branch diffs use `origin/dev...HEAD`.
  - **LOW-6.** `SECURITY.md:56-57` is reworded to stay true, and
    DEC-RFR-011 records its reliance on R-HRP-16, checked below and in
    Milestone 5.
  - **LOW-7.** The roadmap and reflection-plan lines of the 3.10 grep are
    set aside.
  - **LOW-8.** One exact marker string is used. AC-REL-5's marker names
    what was deleted, the moot "once it exists" is gone, `_prose_floor`
    reads the whole `SKILL.md`, and the Milestone 5 alias check covers
    `pyproject.toml`.
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
    `rename-cli-and-positioning` or `write-down-policies`, the shipped
    packages that cite the alias tests.
  - `git ls-tree origin/dev openspec/changes/lean-production-tree` prints
    its tree.

  Record its squash commit's sha as `LPT`. That squash both adds the
  package to `dev` and makes its deletions, so it is the one commit on
  `dev`'s first-parent line that added the package's proposal:

  ```
  LPT=$(git log --first-parent --diff-filter=A --format=%H origin/dev -- openspec/changes/lean-production-tree/proposal.md)
  gh pr view 58 --json mergeCommit --jq .mergeCommit.oid
  ```

  The first prints exactly one sha, and the second prints the same sha
  (pull request #58 carries `lean-production-tree`; if it was closed in
  favour of another, cross-check against the one that merged). A squash
  subject is the pull request's title and need not name the package, so
  the subject is not how `LPT` is found. Milestone 6 derives its
  deleted-path list from `LPT`.
- Bring this branch to that tip by merging `origin/dev` into it, never by
  rebasing or force-pushing. Re-run every measurement above at the branch
  head, and note any line that moved beside the bullet that uses it below.
- **The citation dependencies at the branch head.** Re-run the proposal's
  script. Expect `prepare-release-0-3-0` alone. `harden-release-pipeline`,
  if it has merged or is on `dev` by then, is read too. If the script
  names any further spec, stop here and revise this package before
  Milestone 2 (R-RFR-16, DEC-RFR-007). The revision is a new, named
  supersession if the spec's package has shipped, or an amendment of the
  DEC-LPT-007 kind if it is open. No further spec is amended under this
  package as written.
- **The placeholder reading.** Read `harden-release-pipeline`'s spec as it
  merged, or as it stands on `dev`. Confirm that R-HRP-16 scopes its
  version-placeholder rule to `SECURITY.md`'s verification commands ("Its
  commands"), and that AC-HRP-20 is satisfied by a supported-versions
  sentence naming a version while the commands keep placeholders. If
  AC-HRP-20 reads the rule as file-wide, stop and reconcile the two
  packages before Milestone 5 edits that sentence (DEC-RFR-011).
- **The required checks.** Record `gh api repos/ianshank/planlint/rulesets`.
  If any branch ruleset's `required_status_checks` names a `test (3.10)`
  leg rather than `ci-ok` alone, the owner edits that ruleset in the same
  sitting as the merge, or pull request 1 cannot pass its own checks.
- **Merge hazards**, resolved on purpose whichever sibling lands first:
  - `docs/hooks.md`: `harden-release-pipeline` edits the `release` row,
    while this change edits the `test` row only.
  - `docs/aqa.md`: `lean-production-tree` edits `:113-114`, while this change
    edits the ranges at `:150` and `:287` only.
  - `docs/next-steps.md`: `lean-production-tree` edits rows throughout and
    `harden-release-pipeline` edits `:231`, while this change edits items 7a
    and 9.
  - `README.md`: `lean-production-tree` edits it throughout, while this
    change edits `:39` and the alias paragraph at `:77-84`.
  - `pyproject.toml`: `harden-release-pipeline` edits
    `[tool.specgraph.action_major_floors]`, while this change edits
    `requires-python`, the classifiers, `[project.scripts]`, the dev extra
    and the mypy tables.
  - `tests/support.py`: `lean-production-tree` adds `shipped_files`, while
    this change edits `read_pyproject` and the `working_directory`
    docstring.
  - `SECURITY.md`: `harden-release-pipeline` rewrites it, and only
    Milestone 5 touches its supported-versions sentence.
  - `CHANGELOG.md` `[Unreleased]`: all three packages add groups there.
  - `Dockerfile`: no sibling edits it, and this change adds one comment
    line.
- **Gate:** every precondition above recorded with its output and the date
  — the tag, the PyPI `200`, the ancestry exit 0, `lean-production-tree`'s
  squash commit as `LPT` with both commands that find it, and the archive
  tag, the citation dependencies, the placeholder reading and the rulesets
  — then `make test` on the branch head. Only then is pull request 1 marked
  ready, and no milestone below starts before this is recorded.

## Milestone 1 — The Python 3.11 floor

- **The floor guard first, green at 3.10.** In `tests/workflow_support.py`,
  add `requires_python_floor(pyproject: dict[str, Any]) -> str | None` with
  a full docstring. It returns `X.Y` when `project.requires-python` is
  exactly `>=X.Y`, and `None` for any other shape, so a `~=`, an `==` or a
  compound specifier fails the guards rather than being read loosely. In
  `tests/test_workflow_python.py` (R-RFR-6, DEC-RFR-003):
  - `_prose_floor(text: str, pattern: str, name: str) -> tuple[str | None, str]`
    returns `(value, "<name>:<line>")` when `pattern` matches exactly one
    line of `text`, and `(None, "<name>: <n> matches for <pattern>")`
    otherwise.
  - `_floor_disagreements(sources: dict[str, tuple[str | None, str]]) -> list[str]`
    is a pure function over `{source name: (value, locator)}`. It names
    every source with no value, and, when the values differ, every source
    with its value and locator.
  - The two matrix sources take `min(..., key=_version_key)`, the numeric
    key the hooks-row test already uses, and an empty set becomes
    `(None, "the matrix has no hard leg")` before `min` is reached.
  - `test_the_python_floor_agrees_across_every_source` (integration) feeds
    it six sources:
    - `requires_python_floor(read_pyproject())`;
    - the lowest hard leg from `_matrix_versions(_ci_text())`;
    - the lowest of `_classifier_versions(...)`;
    - `[tool.mypy] python_version`;
    - `_prose_floor` over the whole of `README.md` with
      `Python (\d+\.\d+)\+`;
    - `_prose_floor` over the whole of
      `skills/planlint-spec-governance/SKILL.md` with
      `Python (\d+\.\d+) or newer`, whose only match is the `compatibility:`
      line.
  - `test_a_stale_python_floor_is_named_with_its_source` (unit,
    non-success) uses the same readers on planted input (AC-RFR-6):
    - a planted README text saying "Python 3.10+" through `_prose_floor`,
      beside `3.11` from every other source, must name `README:<line>` and
      both values;
    - planted text with no match, and with two, must each be named;
    - `requires_python_floor({"project": {"requires-python": "~=3.11"}})`
      must give `None`, reported as no floor;
    - a planted matrix whose legs are `{"3.9", "3.10"}` must give `3.9` as
      its minimum, so a planted `3.10` elsewhere is named;
    - a planted empty matrix must be named, not raise.

  Write both on the unedited tree and record the guard green at 3.10,
  since every source reads 3.10 there. Then bump `requires-python` alone to
  `>=3.11` and record the guard red, naming the five other sources and
  their value. The edits below then bring every source to 3.11 and the guard
  green again.
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
- `tests/test_ci_workflow.py`: `test_mypy_is_strict_and_warns_on_unreachable_code`
  (`:49-56`) asserts `mypy.get("python_version") == requires_python_floor(read_pyproject())`
  and that the floor is not `None`. Its docstring says "the floor
  `requires-python` declares", not "3.10" (R-RFR-3, AC-RFR-2).
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
  - `test_deprecated_alias_warns_to_stderr_and_delegates`,
    `test_deprecated_alias_preserves_failure_exit_code`,
    `test_deprecated_alias_keeps_stdout_parseable` (`:258-301`) and
    `test_deprecated_alias_names_its_removal_version` (`:514-530`) are
    deleted.
  - The leftovers go in the same commit, as `make lint` and a read of the
    file confirm:
    - `main_deprecated` leaves the import at `:20`;
    - the module-level `from openspec_graph import __version__` (`:19`),
      used only by the deleted window test, is deleted (ruff F401 names it;
      the version tests at `:155` and `:175` import it locally);
    - the `repo_root` fixture (`:509-511`), used only by the replaced
      entry-point test, is deleted.

    No section header is left without a test under it: the
    `# --- AC-RP-1 …` header at `:224` keeps the replacement test and the
    surviving entry-path tests, and its text drops "deprecation alias".
  - The module docstring (`:1`) says "entry point" and drops "deprecation
    alias".
  - `test_primary_command_emits_no_deprecation_warning` and
    `test_planlint_log_level_env_var_works` are unchanged (R-RFR-10,
    AC-RFR-11).
- In the same commit as the deletions,
  `openspec/changes/prepare-release-0-3-0/specs/release-readiness/spec.md`
  is amended at these lines and nowhere else (R-RFR-16, DEC-RFR-007):
  - AC-REL-5's verification line keeps only
    `test_primary_command_emits_no_deprecation_warning` in its selector,
    with its stage;
  - AC-REL-6's verification line becomes its stage alone;
  - each of the two lines carries exactly R-RFR-16's marker:
    "(amended by `prepare-release-0-4-0`, superseding DEC-LPT-004 for this
    line only: 0.4.0 removed the `specgraph` alias and deleted the tests of
    it that this line cited; the original line is read at the `v0.3.0`
    tag)".

  The criteria keep their ticks and their text. No other spec is amended:
  Milestone 0 stopped for a revision if its re-run named one. Run
  `python -m pytest tests/test_spec_test_citations.py -q` on that commit,
  and confirm that `git diff --stat origin/dev...HEAD -- openspec/changes/`
  lists only `prepare-release-0-3-0`'s spec and this package.
- Prose (R-RFR-11):
  - `README.md:77-84`: the command was renamed from `specgraph` to
    `planlint`; the `specgraph` alias warned through every 0.3.x release and
    was removed in 0.4.0, so run `planlint`. The waiver comment syntax, the
    config file and the `[tool.specgraph]` section keep the name as stable
    contract identifiers, and the link to `docs/policies.md` stays.
  - `docs/policies.md:74-79`: past tense — the alias warned through every
    0.3.x release and was removed in 0.4.0.
- Confirm `SPECGRAPH_LOG_LEVEL` is untouched: `git diff origin/dev...HEAD -- openspec_graph/log.py tools/_common.py`
  shows only Milestone 1's comment rewording, and `test_verbose_via_env_var`
  passes (R-RFR-11, AC-RFR-12).
- **Gate:** `make test`

## Milestone 3 — The Dockerfile's deprecation, announced (its removal is 0.5.0's)

- `Dockerfile`: add one comment line to the header, after the build and run
  lines (`:8-9`):
  `# Deprecated in 0.4.0 and removed in 0.5.0 (CHANGELOG.md, Deprecated): use the published package or the composite action instead.`
  It carries no install command and no `@v` or `rev:` token. Nothing else in
  the file changes, and no entrypoint wrapper is added (R-RFR-23,
  DEC-RFR-006).
- Confirm the tests that read the file stay green with the line in place,
  and record the run (AC-RFR-28):
  - `test_dockerfile_documents_the_user_override_for_writing_verbs`, whose
    `_user_override_offenders` joins every comment line and needs only
    `--user`, `id -u` and the backticked writing verbs, all still there;
  - `test_dockerfile_from_is_digest_pinned_with_the_tag_in_the_reference`
    and `test_dockerfile_switches_to_a_non_root_user_after_install`, which
    read code lines through `_code_lines`;
  - `test_docker_build_context_is_sufficient_for_the_dynamic_version`, whose
    `COPY` regex is anchored at line start;
  - `test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry` and
    `test_agent_artifacts_are_excluded_from_the_docker_context`, which read
    files this change does not touch;
  - the adopter-corpus scans of `tests/test_adopter_urls.py`, which read the
    file for install commands and tag tokens, under `make test`.
- `.dockerignore`, `.github/dependabot.yml`'s `docker` entry and every test
  and helper that reads them are not edited:
  `git diff --stat origin/dev...HEAD -- .dockerignore .github/dependabot.yml tests/test_workflow_pins.py tests/test_release_surface.py`
  prints nothing. `git diff origin/dev...HEAD -- tests/workflow_support.py`
  shows only Milestone 1's `requires_python_floor` (R-RFR-23). The
  Dependabot entry staying with its file means the "dependency file not
  found" window cannot open in 0.4.0; the 0.5.0 package deletes both in one
  commit (DEC-RFR-006).
- `docs/next-steps.md:254-256`, item 9, is rewritten. The `Dockerfile` is
  deprecated in 0.4.0 and removed in 0.5.0, because it is built, published
  and scanned nowhere and keeping it would mean a second supported
  artifact. `pip install planlint` in any `python` image, or the composite
  action, is the delivery path. Reopen a published image only for an
  adopter who needs one, and then with a CI build, a registry push, an
  attestation by digest and base-image CVE triage, not the recipe alone.
  Name this package (R-RFR-23, AC-RFR-16).
- `docs/policies.md`'s list of instances is not extended (DEC-RFR-006).
- **Gate:** `make test`

## Milestone 4 — Release notes, the selectors and the observations

- `CHANGELOG.md` `[Unreleased]` gains two groups, after any group a sibling
  wrote, each entry led by **`prepare-release-0-4-0`**, in the file's voice
  (R-RFR-15, DEC-RFR-008):
  - `### Removed — Python 3.10 and the specgraph alias`, with `specgraph`
    in backticks in the file, holding these entries:
    - **Python 3.10:** `requires-python` is `>=3.11`; the classifier, the
      matrix leg, the `tomli` dev extra and its mypy override are gone; mypy
      checks against 3.11; announced in the 0.3.0 notes.
    - **The `specgraph` command:** removed, so run `planlint`; the waiver
      syntax, `openspec/specgraph.json`, `[tool.specgraph]` and
      `SPECGRAPH_LOG_LEVEL` are unchanged; announced in the 0.3.0 notes.
  - `### Deprecated`, holding one entry: **the `Dockerfile` is removed in
    0.5.0**, with `.dockerignore` and the `docker` Dependabot entry. They
    are unchanged through every 0.4.x release, and `pip install planlint` in
    any `python` image, or the composite action, replaces them.

  No released section changes. `git diff origin/dev...HEAD -- CHANGELOG.md`
  shows only `[Unreleased]` lines (C-RFR-4, AC-RFR-17).
- Re-point this package's stage-only criteria to the tests that now exist,
  keeping each stage:
  - AC-RFR-5 → `test_the_python_floor_agrees_across_every_source`;
  - AC-RFR-6 → `test_a_stale_python_floor_is_named_with_its_source`;
  - AC-RFR-10 → `test_entry_points_declare_planlint_and_no_alias`.

  Then run `python -m pytest tests/test_spec_test_citations.py -q` and
  confirm every selector resolves (AC-RFR-18).
- **The wheel observations** (AC-RFR-9, AC-RFR-10, DEC-RFR-010). Run
  `make wheel-check`, record `python -m pip --version`, then:
  - `unzip -p dist/planlint-*.whl '*.dist-info/METADATA' | grep '^Requires-Python'`
    prints `Requires-Python: >=3.11`.
  - `python -m pip download --no-deps --only-binary=:all: --python-version 3.10 -d "$(mktemp -d)" dist/planlint-*.whl`
    exits non-zero, and its output contains `requires a different Python`.
  - The same command with `--python-version 3.11` exits 0.
  - `unzip -p dist/planlint-*.whl '*.dist-info/entry_points.txt'` prints
    `[console_scripts]` and the single line
    `planlint = openspec_graph.cli:main`.

  Record each output.
- Run `make stage-citations` and confirm that this package's verification
  lines add no stage to the set no workflow runs by name: only `test` and
  `pre-pr` are cited (DEC-RFR-010).
- Confirm the diff touches none of the fixtures and dated comments C-RFR-5
  lists, using `git diff -U0 origin/dev...HEAD -- tests/test_workflow_python.py tests/test_ci_workflow.py tests/test_static_ratchets_planted.py pyproject.toml .pre-commit-config.yaml`
  read for those lines (AC-RFR-19).
- Run `planlint --target . validate --fail-on INFO --change prepare-release-0-4-0`,
  then `planlint --target . validate --fail-on ERROR` on the whole tree,
  and record both exit codes.
- Record AC-RFR-20's first part (Milestone 0's facts) and AC-RFR-25's first
  run (`make pre-pr` on the removals' head) here, and tick each criterion
  of Milestones 1 to 4 only as it is verified.
- **Gate:** `make pre-pr`

## Milestone 5 — The 0.4.0 release-prep pull request

- **Preconditions**, each recorded with its output and the date. Run
  `git fetch origin`, then check on `origin/dev`:
  - `lean-production-tree` has merged (Milestone 0's facts);
  - `harden-release-pipeline` has merged: its merge commit is recorded,
    `release.yml` carries what its spec names, and Milestone 0's
    placeholder reading still holds for its spec as merged;
  - pull request 1 has merged: its merge commit is recorded, and
    `git grep -q main_deprecated origin/dev -- openspec_graph pyproject.toml`
    exits 1, since the alias is gone from both the code and the entry
    points.

  (R-RFR-2, AC-RFR-20.)
- Cut the branch from `origin/dev` and follow
  `.claude/skills/planlint-release/SKILL.md` §1 and `docs/hooks.md`
  "Releasing", as `lean-production-tree` left it (R-RFR-21).
- `openspec_graph/__init__.py:15` → `__version__ = "0.4.0"`, and nothing
  else in the module (R-RFR-17). Then run `pip install -e ".[dev]"`: an
  editable install's metadata is written at install time. Until it is
  refreshed, the tests that compare the installed distribution's metadata
  with `__version__` go red for a reason that is not the bump set; among
  them are
  `test_installed_distribution_version_matches_the_package_attribute` and
  `test_envelope_carries_the_tool_version`.
- Run `make test` on the bump alone and record which tests fail. Expect,
  among others:
  - `test_skill_metadata_version_matches_the_package`;
  - `test_ci_template_pins_the_floor_the_skill_enforces`;
  - `test_every_changelog_version_links_to_its_release_tag`;
  - `test_every_copyable_tag_ref_names_the_current_version`, naming each
    stale ref with its file and line;
  - `test_generated_artifacts_are_fresh`.

  `test_compatibility_prose_matches_the_declared_minimum` and
  `test_skill_min_version_is_not_ahead_of_the_package` stay green on the
  bump alone and are recorded as such (AC-RFR-21). Record the offender list
  `test_every_copyable_tag_ref_names_the_current_version` prints; it must
  equal what the copyable-tag grep prints at that commit.
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
- The hand edits no test names (R-RFR-19, DEC-RFR-011):
  - `.github/actions/planlint/action.yml:34` → `e.g. "0.4.0"`, with nothing
    else in the file changed (`test_the_action_declares_exactly_the_v1_inputs`);
  - `SECURITY.md:56-57`, as `harden-release-pipeline` left it. "Only the
    latest released version is supported: `0.3.0`, the first release
    published to PyPI" is reworded so it stays true after the bump: it names
    `0.4.0` as the latest released and only supported version, and keeps
    "the first release published to PyPI" only as a fact about `0.3.0`,
    never as a description of `0.4.0`. Its verification commands keep the
    placeholders R-HRP-16 requires.
- `CHANGELOG.md` (R-RFR-20, DEC-RFR-009):
  - Insert `## [0.4.0] — <date>` directly below `## [Unreleased]` and its
    blank line, the date being the day the tag will be pushed. Set it the
    morning of the sitting and finish Milestone 6 that day.
  - Every group that sat under `[Unreleased]` — `lean-production-tree`'s,
    `harden-release-pipeline`'s, this package's `Removed` and `Deprecated`
    groups and any other — now sits under the new heading, verbatim and in
    order.
  - Add `[0.4.0]: https://github.com/ianshank/planlint/releases/tag/v0.4.0`
    above the `[0.3.0]:` line, and make the `[Unreleased]:` line
    `https://github.com/ianshank/planlint/compare/v0.4.0...HEAD`.
  - `git diff origin/dev...HEAD -- CHANGELOG.md` shows no line of a released
    section changed.
- `make test` green, recording that each test listed above went green on
  its edit, then `make pre-pr` exit 0 on the head (AC-RFR-21, AC-RFR-23,
  AC-RFR-24, AC-RFR-25).
- Squash-merge into `dev`, and record the squash commit's sha here as
  `PREP`. No other pull request merges into `dev` from here until the
  promotion (R-RFR-2).
- **Gate:** `make pre-pr`

## Milestone 6 — Promote, tag, publish, observe, record (the maintainer, outside the tree)

- **Nothing merged in between.** `git fetch origin && test "$(git rev-parse origin/dev)" = "$PREP"`
  exits 0 before the `dev → qa` pull request is opened. If it does not, a
  pull request merged after the release prep: stop, and re-run Milestone 5's
  checks on the new tip before promoting (R-RFR-2, AC-RFR-20).
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
  - The paths `lean-production-tree` deleted are absent from the tag, by
    the list its squash commit `LPT` (Milestone 0) gives rather than by a
    pattern (DEC-RFR-010):

    ```
    git rev-list --parents -n 1 "$LPT"
    deleted=$(mktemp); git diff --name-only --diff-filter=D "$LPT^1" "$LPT" > "$deleted"; wc -l < "$deleted"
    git ls-tree -r --name-only v0.4.0 | grep -Fxf "$deleted"; echo $?
    ```

    The first prints two shas, the commit and its one parent: a squash
    has a single parent, the `dev` it landed on. Were it a merge commit
    instead, its diff against the first parent would still be the whole
    pull request's change. The count the second prints is not `0`, since
    an empty list would make the third pass vacuously. The third prints no
    path, then `1`. The list holds every file of the deleted plans, the
    retired skill and the deleted package directories, which no pattern
    covered. The `Dockerfile` is not on it: it stays until 0.5.0 and is
    deliberately outside this check.

  Record each command's output (AC-RFR-26).
- **A fresh install.** In a fresh venv:
  - `python -m pip install planlint==0.4.0`;
  - `planlint --version` prints `planlint 0.4.0`;
  - `test ! -e "$VIRTUAL_ENV/bin/specgraph"` exits 0;
  - `planlint --target <clone at M2> validate --fail-on ERROR` exits 0, and
    the spec count it prints is recorded.

  Then `python -m pip download --no-deps --only-binary=:all: --python-version 3.10 -d "$(mktemp -d)" planlint==0.4.0`
  exits non-zero, its output naming `Requires-Python >=3.11`, and the
  `--python-version 3.11` control succeeds. Record all of it with the pip
  version (AC-RFR-27).
- **Back-merge.** `git switch -c sync/main-into-dev origin/dev && git merge --no-ff origin/main`,
  then a pull request into `dev` merged by merge commit. `qa` is never
  back-merged.
- **Record**, in a later pull request into `dev`, never a commit on `main`:
  M2, the tag's commit and date, the run ids, every observation above, and
  AC-RFR-20's remaining parts. Tick AC-RFR-20 and AC-RFR-24 to AC-RFR-27
  only once each is recorded. Then run
  `planlint --target . validate --fail-on ERROR --change prepare-release-0-4-0`
  and the whole tree, and record both exit codes (C-RFR-6, DEC-RFR-010).
- **The sweep.** It is the runbook's last step and not this package's: it
  removes every package 0.4.0 or an earlier release shipped once its
  `tasks.md` records the release. This package goes with
  `lean-production-tree`, `harden-release-pipeline` and the two 0.3.0
  packages, whose open owner actions move to `docs/next-steps.md`. The
  sweep never empties `openspec/changes/`: if no open package would remain,
  the next package lands first (DEC-LPT-012). The 0.5.0 package that
  removes the Dockerfile reads its brief from DEC-RFR-006 at the `v0.4.0`
  tag.
- **Gate:** `make pre-pr`
