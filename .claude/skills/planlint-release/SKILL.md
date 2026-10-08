---
name: planlint-release
description: Cut a planlint release through the dev -> qa -> main branch promotion model -- the release-prep pull request, the two merge-commit promotions, the tag on the production merge commit, the back-merge, and the hotfix and rollback paths. Use when preparing or promoting a release, tagging one, back-merging main into dev, shipping a hotfix, or rolling a published version back.
---

# Releasing planlint

The branch names below are this repository's roles; the names themselves live
in `pyproject.toml` `[tool.specgraph.promotion]`, and
`python tools/check_promotion.py branches` prints them. The model, and why each
rule exists, is in `docs/hooks.md` under *Branching and promotion*; this is the
order of operations.

## Before anything

Run `python tools/check_promotion.py branches`. If `enforce_routes` is not yet
true, the integration and candidate branches may not exist: finish Phase 2 of
`adopt-branch-promotion-model` first. 0.3.0 is this skill's first release;
`docs/distribution-plan.md` §3 is its checklist, in this same order.

## 1. Release-prep pull request, into the integration branch

One pull request carries every edit the release needs, so the candidate tier
runs on exactly the bits that ship:

1. Bump `__version__` in `openspec_graph/__init__.py`; run `make skill-manifests`.
2. Run `make test` and follow its failures: they name every remaining hand edit
   (the SKILL.md version fields, the changelog section and link, every
   copyable tag ref).
3. The hand edits no test names: SKILL.md's "Wiring it into CI" sentence, the
   `version` example in `.github/actions/planlint/action.yml`, the own-action
   refs in `templates/spec-gate.yml` (and its copy under `skills/`), the README,
   `.pre-commit-hooks.yaml` and `SECURITY.md`. Under the promotion model these
   are made **before** the tag, never in a commit after it.
4. Cut `CHANGELOG.md`: the `[Unreleased]` body moves under the new version.
5. `make pre-pr` exit 0, then squash-merge into the integration branch.

## 2. Promote, twice, by merge commit

Check each route before opening it:
`python tools/check_promotion.py route --event pull_request --base <candidate> --head <integration> --base-repo <owner/repo> --head-repo <owner/repo>`.
Integration into candidate, then candidate into production, each merged with a
**merge commit** -- a squash gives the target a commit the source lacks, and
the next promotion conflicts. The `release-tier` and `ci-ok` checks must be
green on both.

## 3. Tag the production merge commit

`python tools/check_promotion.py tag-ancestry --sha <merge sha> --fetch` must
pass: a commit that reached production only inside a merge is refused, because
no release tier ran on it. Run the release workflow by `workflow_dispatch` on
that commit first; tag only when `gate` and `build` are green. A person (or a
personal or App token) pushes the tag -- never `GITHUB_TOKEN`, whose events
start no workflow. Then verify the attestations and install the published
version into a fresh venv, as `docs/distribution-plan.md` steps 5 to 7 say.

## 4. Back-merge

Cut `sync/main-into-dev` from the integration branch, merge production into it
with a merge commit, and open it against the integration branch. The candidate
branch is never back-merged; it catches up at the next promotion.

## Hotfix and rollback

- **Hotfix:** a `hotfix/` branch cut from production, a pull request into
  production (the release tier runs, because the base is production), the
  tag, then the same back-merge. A Dependabot security update aimed at
  production is re-opened as a `hotfix/` branch.
- **Rollback:** PyPI versions are immutable. Yank the release, revert the
  promotion merge with `git revert -m 1` on a `hotfix/` branch cut from
  production -- the only branch besides the candidate that the route admits
  into production -- open it as a pull request, and release the next patch. Never force-push a long-lived branch -- the PreToolUse guard
  in `.claude/hooks/guard_promotion.py` refuses it.

## Never

- Flip `enforce_routes` or edit the promotion table to make a route pass.
- Tag a commit that is not a production merge commit (or pre-model trunk).
- Commit to production after the tag.

Precedence: `skills/planlint-spec-governance/SKILL.md`, then the root
`AGENTS.md`, then `docs/hooks.md`, then this file.
