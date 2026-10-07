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

## Milestone 6 — Owner actions, outside the tree (Phase 2)

- [ ] Precondition: `v0.3.0` tagged on trunk and published under the 0.3.0
  runbook; this change merged after it. Record both commits.
- [ ] Record this package's first pull-request run (AC-BPM-26).
- [ ] Create `dev` and `qa` from `main`'s tip; record the SHA. In the same
  sitting, a pull request into `dev` setting `enforce_routes = "true"` and
  adding `target-branch: "dev"` to each `.github/dependabot.yml` entry
  (DEC-BPM-011, DEC-BPM-013), promoted to `qa` and `main` as the first
  promotion.
- [ ] Rulesets: `main` and `qa` — pull request required, `ci-ok` required,
  merge commits only, no force-push, no deletion; `dev` — pull request
  required, `ci-ok` required, squash **and** merge commits allowed (the
  `sync/` back-merge is a merge commit), no force-push, no deletion. The owner
  is the only bypass. A `v*` tag ruleset: owner creates, no update or delete.
  The `pypi` environment's deployment rule: tags matching `v*` only.
- [ ] Record the first refused feature pull request into `qa` and the first
  `dev` → `qa` promotion running `release-tier` (AC-BPM-28).
