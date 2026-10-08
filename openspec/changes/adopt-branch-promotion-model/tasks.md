# Tasks: adopt-branch-promotion-model

Implemented on `claude/branch-promotion-model`, 2026-10-07. Milestones 1–5
land in one pull request, which merges only after `v0.3.0` is tagged on trunk
(C-BPM-4, DEC-BPM-010). Milestone 6 is the owner's, outside the tree; its
bullets are filled in after the fact with what was observed.

## Milestone 1 — Topology and the config reader — done

- [x] `pyproject.toml` `[tool.specgraph.promotion]`: `integration_branch`,
  `candidate_branch`, `production_branch`, `hotfix_prefix`, and
  `enforce_routes = "false"` for the bootstrap window (R-BPM-1, DEC-BPM-004,
  DEC-BPM-013).
- [x] `tools/_common.py::read_pyproject_str`, on `read_pyproject_int`'s
  table-tracking loop (R-BPM-2), with
  `test_read_pyproject_str_reads_exactly_the_shape_this_repo_writes`.
- [x] DEC-BPM-013 resolved before `route` was written: option (b), the
  enforcement switch; R-BPM-1 and R-BPM-4 amended, AC-BPM-29 added.

## Milestone 2 — `tools/check_promotion.py` — done

- [x] Stdlib-only, arguments-only `main(argv)`, logging through
  `planlint.tools` (R-BPM-3). Subcommands `branches`, `route`,
  `tag-ancestry`, `aggregate` per R-BPM-4..8; every branch name read from the
  table, none in code.
- [x] `tests/test_promotion.py`: every planted `pyproject.toml` names roles
  unlike this repository's (`trunk`/`staging`/`live`), so a branch literal in
  the tool cannot pass by coincidence. The ancestry test drives real git in a
  throwaway repository with a planted `origin/<production>` ref
  (AC-BPM-1..11, 29).
- [x] Added to `test_gate_script_is_runnable_as_a_script` (AC-BPM-22).

## Milestone 3 — `tools/smoke_wheel.py` — done

- [x] Stdlib-only; exactly one wheel or exit 2; `--venv` (default: a fresh
  temporary directory), `--target`, `--fail-on`, repeatable `--expect`;
  Windows and POSIX venv layouts (R-BPM-9, DEC-BPM-012).
- [x] `tests/test_smoke_wheel.py`: probes recorded through an injected runner,
  plus one `e2e` test that builds this project's real wheel and smokes it
  against the `passing`/`failing` fixtures — the `release-tier` invocation
  (AC-BPM-12..14).
- [x] Added to the runnable-script list (AC-BPM-22).

## Milestone 4 — The workflows — done

- [x] `ci.yml`: push branches `[main, qa, dev]`; jobs `promotion`,
  `release-tier` (timeout 30, as `release.yml`'s `gate`) and `ci-ok`
  (timeout 5); no job-level `permissions:` on any of them (R-BPM-10,
  R-BPM-11, C-BPM-1). Route inputs reach the script through `env:`, never
  interpolated into the shell line, since a head branch name is chosen by
  whoever opens the pull request.
- [x] `release.yml`: tag-only `tag-ancestry --fetch` step in `gate` before
  `make pre-pr`; `build` calls `tools/smoke_wheel.py dist --venv /tmp/smoke`,
  which the tag-versus-version step reads; `publish` gains `contents: read`
  (R-BPM-12, DEC-BPM-006).
- [x] `test_release_workflow_is_gated_and_uses_trusted_publishing` edited: it
  now asserts `build` calls the shared smoke tool where it asserted an inline
  `python -m venv` (DEC-BPM-012). `test_every_workflow_is_scanned_by_the_threshold_guard`
  passes unedited.
- [x] New guards, each shown to fail on a planted violation before being
  kept (a job removed from `ci-ok`'s needs; a branch removed from the push
  list; an undeclared conditional job; the ancestry step made unconditional;
  the release smoke step removed): AC-BPM-15..19.
- [x] `python tools/check_no_hardcoded_thresholds.py`: PASS.

## Milestone 5 — Docs and citations — done

- [x] `docs/hooks.md`: CI table rows for the three jobs; the release row
  names the ancestry check and the shared smoke tool; a "Branching and
  promotion" section (R-BPM-13); the release checklist points at it.
- [x] `docs/distribution-plan.md`: the §3 runbook stays the 0.3.0 trunk
  release; a paragraph states what changes from the next release on
  (R-BPM-14).
- [x] `.github/pull_request_template.md`: a Branch section with the base and
  merge-method checkboxes.
- [x] `CHANGELOG.md` `[Unreleased]`: an `Added` entry.
- [x] Every AC-BPM-1..19 citation re-pointed to its test, keeping the stage;
  `python -m pytest tests/test_spec_test_citations.py -q` green.

## Milestone 5b — Adversarial review (`spec-adversary`), every finding resolved — done

Each finding was reproduced, fixed with a counter-example test, and the
reviewer's planted workflow violations re-run against the new guards: all ten
now fail a named test.

- [x] HIGH-1 (`tag-ancestry` accepted second-parent ancestors): first-parent
  check, DEC-BPM-014, R-BPM-7 rewritten, AC-BPM-11 extended with a real
  promotion-shaped repository.
- [x] HIGH-2 (guards satisfied by comments, no soft-fail check): guards read
  comment-stripped code only; `continue-on-error` / `|| true` forbidden in the
  promotion jobs and the ancestry step; the ancestry `if:` pinned exactly
  (R-BPM-11, AC-BPM-16, AC-BPM-19).
- [x] MEDIUM-1 (empty tier output read as false): tier read from the needs
  JSON, strictly; the route step id wiring guarded (DEC-BPM-016, R-BPM-8).
- [x] MEDIUM-2 (null head repository skipped the fork check): counted as
  foreign (R-BPM-5).
- [x] MEDIUM-3 (AC-BPM-18 / R-BPM-12 not pinned): probes, build, metadata
  step and the shared venv path asserted.
- [x] MEDIUM-4 (a crash exits 1 like findings): a traceback fails the probe
  (R-BPM-9).
- [x] LOW-1, LOW-2 (unquoted switch read as absent; commented header leaked
  keys): exit 2, and the shared readers stop at any header (DEC-BPM-015).
- [x] LOW-3: DEC-BPM-013 now says the fork refusal is downgraded too.
- [x] LOW-4: explicit refspec on `--fetch`.
- [x] LOW-5: cross-repo message names the head; R-BPM-6 and R-BPM-8 state
  what the code does; AC-BPM-29 moved; `release-tier` checkout drops
  persisted credentials.

## Milestone 5c — Branch audit (code, docs wiring, harness) — done

Three read-only audits of the branch against `main` (a code peer review, a
docs and configuration wiring sweep, a skills/agents/hooks inventory), every
finding resolved or recorded:

- [x] Review H1: the release tag check reads the tool and configuration from
  the default branch (DEC-BPM-017). M1: an incomplete route is exit 2
  (DEC-BPM-018). M2: an undecided tier still names every failed job. M3: the
  real-wheel test skips only when the build frontend is missing. M4: the
  promotion guards moved to `tests/test_ci_promotion.py`, the aggregate and
  ancestry tests to `tests/test_promotion_gates.py`, helpers to
  `tests/promotion_support.py`. M5: the release smoke carries the same probes.
  M6: the smoke venv is created with `--clear`. LOW items: one soft-fail token
  list in `tests/workflow_support.py`, shared constants reused, the console
  script read from `[project.scripts]`, the parser description names no
  branch, DEBUG records for route inputs, fetch and needs, and the known limits
  of `table_header` documented.
- [x] Harness (DEC-BPM-019): `.claude/hooks/guard_promotion.py` (`PreToolUse`),
  new nudge arms, `.claude/skills/planlint-release/SKILL.md`, the verifier's
  CI-only gates, and `test_harness_docs_list_every_agent_and_skill`.
- [x] Docs: `docs/architecture/c4.md`, `docs/aqa.md`, `docs/hooks.md`,
  `README.md`, `llms.txt`, the root, `docs/` and `tools/` agent indexes,
  `docs/next-steps.md`, `docs/policies.md`, `docs/distribution-plan.md` and the
  changelog. `.gitignore`, `.dockerignore`, `.gitleaks.toml`, the Makefile and
  the pre-commit configuration needed no change (checked, not assumed).

## Observed

- [x] AC-BPM-26: CI run 37575715654 (#226) on `318383e`, this package's pull
  request into `main`: `promotion` success (route printed as `WARN` while
  `enforce_routes` is off), `release-tier` success (its first run: `make
  pre-pr`, build, metadata, smoke with both fixture probes), `ci-ok` success.
  The run before it (#225, `04ab618`, cancelled by the next push) showed
  `ci-ok` failing on exactly `release-tier: cancelled`, `test: cancelled`
  and `test-windows: failure`.

## Milestone 6 — Owner actions, outside the tree (Phase 2)

- [x] Precondition **not held, recorded rather than rewritten**: this change
  merged into `main` as `e30289d` on 2026-10-08 with no `v0.3.0` tag on origin
  (C-BPM-4). Nothing broke -- the tag-ancestry step runs `main`'s own tool, and
  `e30289d` is on `main`'s first-parent chain -- but the trunk runbook in
  `docs/distribution-plan.md` §3 no longer applies: 0.3.0 ships through the
  promotion flow, its step-8 ref flips and CHANGELOG date in a release-prep
  pull request into `dev` (the `planlint-release` skill).
- [x] `dev` and `qa` created from `main` at `e30289d` on 2026-10-08, with the
  GitHub branch API (the PreToolUse guard rightly refuses a direct
  `git push` to `qa`); all three branches at one SHA.
- [x] In the same sitting, a pull request into `dev` setting
  `enforce_routes = "true"` and `target-branch: "dev"` on both
  `.github/dependabot.yml` entries (DEC-BPM-011, DEC-BPM-013), held together
  by `test_route_enforcement_and_dependabot_flip_together`.
- [ ] That pull request promoted `dev` → `qa` → `main` by merge commits, as
  the first promotion; record both runs.
- [ ] Rulesets: `main` and `qa` — pull request required, `ci-ok` required,
  merge commits only, no force-push, no deletion; `dev` — pull request
  required, `ci-ok` required, squash **and** merge commits allowed (the
  `sync/` back-merge is a merge commit), no force-push, no deletion. The owner
  is the only bypass. A `v*` tag ruleset: owner creates, no update or delete.
  The `pypi` environment's deployment rule: tags matching `v*` only.
- [ ] Record the first refused feature pull request into `qa` and the first
  `dev` → `qa` promotion running `release-tier` (AC-BPM-28).
