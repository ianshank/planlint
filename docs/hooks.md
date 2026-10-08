# Hooks

Pre-commit and CI hooks enforce the same gate as `make pre-pr`, so a commit can
never bypass what CI checks. CI additionally enforces the promotion route and,
into the release-candidate and production branches, the release tier (see
*Branching and promotion*).

## Pre-commit

```bash
pip install -e ".[dev]"
pip install pre-commit
pre-commit install
```

`.pre-commit-config.yaml` uses **local hooks that call `make`** — the same
targets CI uses — so a commit can never bypass CI and there is no second set of
tool-version pins to drift from the dev extras:

- `make lint` (ruff) across `openspec_graph/`, `tests/`, `tools/`
- `make typecheck` (mypy) across `openspec_graph/`, `tools/`, `tests/`, with
  `tests/` under a per-code baseline in `[[tool.mypy.overrides]]`
- `make security` (gitleaks or fallback)
- `planlint validate` (self-dogfooding: the tool validates its own specs)
- `make docs-check` (required docs present + linked from README)
- `make thresholds` (no hard-coded thresholds in the Makefile or workflow YAML)

Every hook is fail-closed: a violation blocks the commit.

## Optional pre-push hook

The commit-time hooks run lint + typecheck + security + validate + docs-check +
thresholds. If you also want to block a broken **push** (catching what CI
would catch, including the full test suite + coverage floor) before it leaves
your machine, install a pre-push hook that runs the one-command gate:

```bash
cat > .git/hooks/pre-push <<'EOF'
#!/usr/bin/env sh
# Run the full enterprise gate before a push reaches CI.
exec make pre-pr
EOF
chmod +x .git/hooks/pre-push
```

This is **optional and not installed by default** — `make pre-pr` runs the full
coverage suite, so it is slower than the commit-time hook. Pre-commit + CI
already cover the common case; the pre-push hook is for contributors who want
a local net before the round-trip to CI.

## Fast local loop

`python -m pytest -m unit` runs the tier whose code under `tests/` starts no
process and reads none of this repository's own files outside the labelled
corpora under `tests/fixtures/` and `tests/corpus/` — about 13 s when
`shape-the-test-suite` recorded it, against about 150 s for the whole suite.
`python -m pytest -m "not unit"` runs the rest: `integration`, which reads the
repository (the workflow, Makefile, docs and agent-artifact guards, every
`tools/` script run in-process, and package source read through `inspect`),
and `e2e`, which starts a process
(`run_cli`, a nested pytest, ruff, mypy, bash). The criterion stops at
`tests/`: the package's own `git rev-parse HEAD` and `tools/check_secrets.py`'s
`git ls-files` run inside the code under test, so a few tests in the cheaper
tiers still start `git`. Every test carries exactly one tier, and
`tests/test_suite_shape.py` fails on a missing, doubled, aliased or wrong one.

It is a command, not a Make target: `coverage-run` is the only recipe that
invokes pytest (`test_the_suite_runs_once_through_coverage_run`), and the fast
loop measures nothing. It is a local convenience, never a gate; the CI `test`
row below still runs every tier.

## CI hooks (`.github/workflows/`)

| Job | Trigger | Gate |
|---|---|---|
| `test` (3.10–3.14) | push + PR | `make lint` + `make typecheck` + `make test` (both trees' floors, read scoped from one report; the leg's `coverage.json` is uploaded) |
| `test-windows` (PYTHON_DEFAULT) | push + PR | same three gates on `windows-latest` (GNU make via Chocolatey), and the same upload |
| `encoding-stress` | push + PR | `make e2e-live` under `PYTHONIOENCODING=ascii` (hard) |
| `self-validate` | push + PR | `planlint validate --fail-on ERROR` (hard) |
| `packaging` | push + PR | wheel build + `tools/check_wheel_metadata.py` (hard) |
| `action-contract` | push + PR | the composite action run against every labelled fixture under `tests/fixtures/action/`, under a read-only token with no secrets (hard) |
| `graph-diff` | PR only | `tools/diff_spec_graph.py` base→head (AC-CH-5/6) |
| `security` | push + PR | gitleaks + no-hardcoded-thresholds (hard) |
| `docs` | push + PR | `make docs-check` (hard) |
| `promotion` | push + PR | `tools/check_promotion.py route`: a PR into the release-candidate branch must come from the integration branch, one into production from the candidate or a hotfix branch, never from a fork; emits whether the run needs the release tier (hard) |
| `release-tier` | PR into / push to the candidate or production branch | `make pre-pr`, sdist + wheel build, `tools/check_wheel_metadata.py`, and `tools/smoke_wheel.py` — the release workflow's own smoke tool — plus the installed CLI against the `passing` and `failing` action fixtures (hard) |
| `ci-ok` | push + PR | `tools/check_promotion.py aggregate` over every other job: the **single required status check** for the branch rulesets; fails on any failed, cancelled or wrongly skipped job (hard) |
| `release` (separate workflow) | `v*` tag | `tools/check_promotion.py tag-ancestry` (the tag must be on the production branch), `make pre-pr`, then `tools/smoke_wheel.py` in a clean venv, then trusted publishing to PyPI, which uploads PEP 740 attestations for both files |

The workflow holds itself to the posture the gates inside it enforce
(`harden-ci-workflows`; `tests/test_workflow_pins.py`, `tests/test_workflow_posture.py`
and `tests/test_workflow_python.py` are the guard).
Every third-party action is pinned to a commit SHA with its release tag in a
trailing comment, every copy of one action must agree on both, and each sits
at or above a per-action major floor in `pyproject.toml`
(`[tool.specgraph.action_major_floors]`) read from that tag -- a ratchet that
a bump never edits and only a regression trips, including every copy sliding
back together, which an agreement check alone cannot see.
Every job runs with a read-only token: `ci.yml` declares `permissions:
contents: read` at the top, and a job widens only in its own block, under a
comment naming the step that needs it (`security`, for gitleaks-action's
commit listing on a pull request). Every job carries a `timeout-minutes`
inside the range `[tool.specgraph] ci_job_timeout_minutes_min..max` in
`pyproject.toml`, so a hung step costs minutes rather than GitHub's six-hour
default. A `concurrency` group cancels a pull-request run when a newer push to
the same branch arrives; a push to a promotion branch keys on its SHA, so it is neither
cancelled nor left pending to be superseded. The single-interpreter Python
version is `env: PYTHON_DEFAULT` at the top of each workflow and nowhere else
(the `PYTHON_DEFAULT` cells above); a new single-version job reads
`${{ env.PYTHON_DEFAULT }}` rather than pasting a literal, and the guard holds
that value equal to the composite action's input default and the Dockerfile's
base tag, and to one of the `test` matrix's hard legs. A matrix leg added
through `include:` with `experimental: true` is advisory -- its result is
visible and cannot turn the run red -- and is not listed in the `test` row
until it is hard.

`typecheck` runs as a step inside the `test` matrix (so every supported Python
version is type-checked), not as a standalone job.

`make test` runs the suite once, through `make coverage-run`, over both trees
in `[tool.coverage.run] source`, and reads the one `coverage.json` scoped:
`openspec_graph/` against `[tool.coverage.report] fail_under` and
`[tool.specgraph] branch_fail_under`, `tools/` against
`tools_line_fail_under` / `tools_branch_fail_under`, through the same two
checkers under `--scope`. pytest-cov's own total gates nothing on that run —
it is the diluted figure for everything measured — so neither tree's headroom
hides the other's regression. `coverage-tools` remains a documented target
that depends on the run and re-reads `tools/` alone; it has no job of its own
and is reached in CI as a prerequisite of the `make pre-pr` that the
`release-tier` job and the release workflow run. Locally it is part of `make pre-pr`, not `make ci`, which stays
the fast inner loop. Every leg that runs the suite uploads its `coverage.json`
as an artifact; those per-leg reports are what the floors are set from — two
points under the minimum green leg, never down.

The `graph-diff` job checks out the PR head SHA (not the synthetic merge
commit) so `merge-base` resolves to the true branch point (DEC-CH-001).

`release` lives in its own workflow file because it is tag-triggered, not
push/PR-triggered. Its clean-venv step (`tools/smoke_wheel.py`) is not
redundant with the `test` matrix: the suite runs the CLI as
`python -m openspec_graph.cli`, so only this tool exercises the console script
a wheel actually installs and proves the package declares no runtime
dependencies. It is the same tool, with the same fixture probes, that
`release-tier` runs before any tag exists, and
`test_the_real_wheel_passes_the_shared_smoke_tool` runs it inside the suite
when the build frontend is available.

Note that `tools/check_no_hardcoded_thresholds.py` scans **every** file under
`.github/workflows/`, not a named one — a workflow added later would otherwise
escape the guard while it still printed PASS.

## Reports, not gates

What is deliberately outside the ladder: each target below lists something
for a person or an agent to read, and none decides a build.

| Target | Reads | Exit |
|---|---|---|
| `make coverage-per-file` | the one run's `coverage.json`, against `[tool.specgraph] per_file_line_min` | 0 no module below it, 1 a module listed, 2 cannot run |
| `make matcher-accuracy` | `tests/fixtures/phrasing/`, scoring G002 and U004 per pattern against the `[tool.specgraph]` accuracy floors | 0 every floor met, 1 a floor missed |
| `make stage-citations` | every spec's `make` citations and the workflows under `.github/workflows/` | 0 whatever it counts, 2 cannot run |
| `make dead-code` | the `[tool.coverage.run] source` trees, through vulture as a process at `[tool.specgraph] dead_code_min_confidence`, with `tests/` counted as a user and `tools/dead_code_whitelist.txt` applied by name | 0 nothing listed, 1 an unreferenced symbol or a stale whitelist entry, 2 cannot run (vulture absent among the causes) |
| `make spec-status` | each change package's `Status` headers beside its criteria, milestones, CHANGELOG entries and unrun verification stages | 0 no finding, 1 a finding, 2 cannot run; stays red until `settle-package-status-headers` lands |

None of these is composed into `ci`, `pre-pr` or a CI job, and the report
targets in the `Makefile` are held to that by
`test_every_report_target_stays_out_of_the_ladder`, through prerequisites
followed transitively. Each becomes a gate only through a package of its own,
after a quarter of an empty report. `make dead-code` needs the dev extra,
which installs vulture, and exits 2 without it. `make spec-status` never
edits a header, and it stays red, exiting non-zero, until
`settle-package-status-headers` lands
([`next-steps.md`](next-steps.md) item 24); its quiet quarter starts only
then.

## Claude Code hooks (`.claude/hooks/`)

A third, distinct layer from pre-commit/CI above: a
[Claude Code](https://claude.com/claude-code) `PostToolUse(Edit|Write)` hook,
wired in `.claude/settings.json`, that fires inside an agentic coding session
right after a file write — before the agent considers the change done, not at
commit or push time. It targets drift classes that recurred multiple times in
this repo's own history and are easy for an agent (or a human) to forget
mid-edit:

- Editing `skills/planlint-spec-governance/**` or `.claude-plugin/**` → reminds to
  run `pytest tests/test_skill_contract.py tests/test_skill_distribution.py tests/test_agent_skill_docs.py`. These
  are prose and metadata an *external* agent acts on, so no other gate catches
  drift in them. The glob names the distributable skill specifically: a bare
  `*/skills/*` also matched `.claude/skills/`, nudging contributors toward a test
  that does not cover their file.
- Editing `openspec_graph/rules.py` or `rules_*.py` → reminds to regenerate
  `tests/baseline_rules.json` and run `tests/test_rule_registry_docs.py`
  (see the `planlint-add-rule` skill below).
- Editing the `Makefile` or a `.github/workflows/*.yml` file → reminds to run
  `make thresholds`, and for a workflow
  `pytest tests/test_ci_promotion.py tests/test_ci_workflow.py tests/test_release_surface.py`:
  a new `ci.yml` job must join `ci-ok`'s `needs` and the CI table above, a job
  with an `if:` must be declared to the aggregator, and no promotion job may
  soften its own failure.
- Editing `pyproject.toml` → reminds that floors move up, never down
  (`make thresholds`), and for the `[tool.specgraph.promotion]` table to run
  `pytest tests/test_promotion.py tests/test_ci_promotion.py`: the push-branch
  list must equal the table, and `enforce_routes` flips only together with
  Dependabot's `target-branch`.
- Editing `tools/check_promotion.py`, `tools/smoke_wheel.py` or
  `tools/_common.py` → reminds to run
  `pytest tests/test_promotion.py tests/test_promotion_gates.py tests/test_smoke_wheel.py tests/test_gate_scripts.py`
  and then `make coverage-tools`.
- Editing `.github/dependabot.yml` or a composite action → reminds to run
  `pytest tests/test_workflow_pins.py -k dependabot`, and that a
  `target-branch:` must name the integration branch exactly when routes are
  enforced.
- Editing anything under `evals/` → reminds to run
  `pytest tests/test_agent_artifacts.py`. The `planlint-add-eval-case` skill
  under `.claude/skills/` carries the full checklist. The suite's structure is asserted,
  not assumed: a case with no README row, or a `regex` grader with no
  `pattern`, grades nothing and still reports a pass.
- Editing `README.md`, `llms.txt`, `AGENTS.md` or `templates/**` → reminds to
  run `pytest tests/test_adopter_urls.py`. This is the drift class that already
  cost this project eight dead install commands: prose and packaging metadata
  disagreed and every gate stayed green, because nothing compared them.
- Editing a change package's `spec.md`
  (`openspec/changes/*/specs/*/spec.md`) → reminds to run
  `planlint validate --fail-on ERROR` and
  `pytest tests/test_spec_test_citations.py` before finishing, and names four
  traps: a backticked `make <target>` in prose is read as a citation; prose
  that quotes a dialect's own marker strings (a heading name in backticks,
  while *documenting* that dialect) can misclassify the spec as the dialect
  it merely describes; the verification marker written inside an acceptance
  criterion's own prose becomes that criterion's verification line, so H001
  fires on a criterion that does cite a stage; and every `pytest -k`
  selector must name a real test. Until this branch the dialect warning sat
  in a second `case` arm with the same pattern as the first, so it had never
  fired; `test_no_case_alternative_is_shadowed_by_an_earlier_identical_one`
  now fails on any duplicated arm.
- Editing anything under `tests/corpus/targets/` → reminds that each
  `expected.json` is a hand-written label, never a snapshot of the detector,
  and to run `pytest tests/test_detect_corpus.py`. The
  `planlint-add-detect-shape` skill carries the checklist.
- Editing `tests/fixtures/phrasing/**`, `openspec_graph/parse_semantics.py`
  or `openspec_graph/parse_model.py` → reminds to run `make matcher-accuracy`
  (the per-pattern misfire column is the review) and then `make validate`,
  because a tightened negation pattern must not strip the last non-success
  criterion from any of this repo's own change packages. The
  `planlint-add-phrasing-case` skill carries the checklist.

A second hook, `PreToolUse`, runs **before** a Bash command or a GitHub
pull-request tool call: `.claude/hooks/guard_promotion.py`
(`adopt-branch-promotion-model`). It denies a direct push to the candidate or
production branch (a push with no refspec is judged against the checked-out
branch), a force-push or delete of any long-lived branch, `--all`/`--mirror`,
a GitHub tool writing a file straight to either protected branch, and a pull
request -- the GitHub tool or `gh pr create` -- whose route
`tools/check_promotion.py route` refuses (it proceeds while `enforce_routes` is
off, as in CI); it asks before a `v*` tag push or `--tags` (a tag publishes to
PyPI), a squash merge (promotions are merge commits) and a retarget onto a
protected branch (a retarget does not re-run CI). It sees through `VAR=value`
prefixes, `env`, git's own options and multi-line commands, not through
`bash -c`. Branch names come from
`[tool.specgraph.promotion]` through that tool, never from the guard. Input
it cannot parse it lets through: it is a seat belt for the window before the
rulesets exist, not the gate. `tests/test_claude_guard.py` holds both
directions.

`.claude/hooks/nudge_rule_registry.sh` implements every check above via a
single shell script (no `jq` dependency — not guaranteed to be on `PATH` in
every dev environment this repo is used from). Despite the JSON key's name,
`"decision": "block"` does **not** undo the edit — `PostToolUse` fires after
the write already landed — it is `PostToolUse`'s contract for surfacing
`reason` to the agent prominently, i.e. a strong reminder, not an actual
block.

See also `.claude/agents/` (spec-drafter, spec-adversary, planlint-verifier —
this repo's own dogfooded OpenSpec change-package workflow) and the
contributor skills under `.claude/skills/`: `planlint-add-rule` (the checklist
the first hook case above points at), `planlint-add-eval-case`,
`planlint-add-detect-shape`, `planlint-add-phrasing-case`,
`planlint-change-package` (the draft → gate → adversarial review → revise
loop that `spec-drafter` and `spec-adversary` run inside), and
`planlint-release` (release prep, the two promotions, the tag, the back-merge,
hotfix and rollback, under *Branching and promotion* above). `spec-drafter`
carries a shell for read-only checks so it can run the gate its own hook asks
for; it writes only under its package. The hook script
itself is held to its wiring by `tests/test_claude_hooks.py`: every path
class above must produce a reason, an unrelated path must produce none, and
`.claude/settings.json` must point at the script.

## Adding a custom rule

Adding or changing a rule also requires regenerating the distributable
skill's rule catalog with `make skill-catalog`; `tests/test_skill_distribution.py`
fails on a stale one, and the `.claude/` hook nudges for it.

Rules live in `openspec_graph/rules.py` as `Rule(ident, severity, dialects,
summary, check)`. A rule is a pure function
`(ParsedSpec, StackProfile) -> Iterable[str]` that yields one message per
violation. Add the `Rule` to the `RULES` tuple, regenerate the baseline:

```bash
planlint rules --json > tests/baseline_rules.json
```

…then add a deterministic test to `tests/`. The baseline test
(`test_rule_set_matches_baseline`) fails if the rule set changes without the
baseline being updated — a conscious decision, not an accident (C-CH-1).

**A whole-tree rule** (a property of the entire spec tree, not one spec —
e.g. G006 "a declared invariant is cited by *some* living spec", or G009's
identical shape for ADRs) can't be expressed as a per-spec `Rule.check` at
all; that signature only ever sees one `ParsedSpec` at a time. Both existing
instances follow the same recipe instead: register an *inert* stub `Rule`
whose `check` always returns nothing (so `planlint rules`/`rules --json`
still lists the ident), then add the real logic as its own block in
`rules.evaluate_tree()` (`rules.py`) — a plain function over
`Sequence[ParsedSpec]`, called once per `validate`/`graph` run, never per
spec. Every whole-tree `Finding` sets `path=` to the entity's own declaring
source, not any one spec's path (`DEC-WL-004`); its `--change` interaction
is an explicit decision, not silence (`DEC-WL-003`/`DEC-AD-004` — does a
`--change`-filtered spec list put this check's correctness at risk, or
not?). `evaluate_tree()` stays two parallel blocks rather than a registry
for two instances; revisit that only if a third whole-tree rule arrives
(`DEC-AD-003`).

## Branching and promotion

`adopt-branch-promotion-model`. Three long-lived branches, named in
`pyproject.toml` `[tool.specgraph.promotion]` and nowhere else that a tool
reads (`ci.yml`'s `on.push.branches` is the one literal copy, held equal to the
table by `test_ci_push_branches_match_the_promotion_config`):

```
feature/* --squash--> dev --merge commit--> qa --merge commit--> main --tag vX.Y.Z--> PyPI
                       ^                                          |
                       +------- sync/main-into-dev (merge) -------+   after each release
```

| Branch | Holds | Pull requests from | Merge method | CI |
|---|---|---|---|---|
| dev (integration) | the next release, integrating | any branch (`feature/*`, `dependabot/*`, `sync/*`) | squash; a merge commit for `sync/*` | every job above; `release-tier` skipped |
| qa (release candidate) | exactly the bits that will ship | `dev` only | merge commit | every job, `release-tier` included |
| main (production) | released code only | `qa`, or `hotfix/*` | merge commit | every job, `release-tier` included |

- **`ci-ok` is the only required status check.** Every other job is in its
  `needs`, and `tools/check_promotion.py aggregate` fails it on any failed,
  cancelled or wrongly skipped job. A matrix job's check names change with its
  matrix and a skipped required check reads as passing, so neither is required
  by name.
- **The route is enforced in CI, not only by convention.** The `promotion` job
  fails a pull request into `qa` whose head is not `dev`, one into `main` whose
  head is neither `qa` nor `hotfix/*`, and any head from a fork into either.
  `[tool.specgraph.promotion] enforce_routes` is `"true"`: `dev` and `qa`
  exist (created from `main` at `e30289d`). While it was `"false"`, before
  they existed, a refused route printed only a `WARN`.
  Known limit: retargeting an open pull request's base does not re-run CI (the
  `edited` event is not a trigger, because an all-skipped run would report a
  passing `ci-ok`); push a commit or re-run the workflow after retargeting.
- **Promotions are merge commits, never squashes.** A squash gives the target
  a commit the source does not have, so the branches diverge on every release
  and the next promotion conflicts. `graph-diff` on a promotion pull request
  therefore diffs the whole release since the previous promotion, not one
  feature (an accepted widening of DEC-CH-001).
- **A release is cut from a release-prep pull request on `dev`**: the version
  bump, the changelog cut, and every own-action ref flip that the 0.3.0 runbook
  called the post-tag commit. It then promotes `dev → qa → main` unchanged, so
  the `release-tier` job has already run the release workflow's gate and smoke
  test on the exact commit. Tag the `main` merge commit; the release workflow's
  `gate` refuses a tag on any commit that is not on `main`'s first-parent
  chain -- a `dev` commit that merely reached `main` inside a promotion is
  refused, because no release tier ran on it. **Nothing is
  committed to `main` after the tag**; if publishing fails, fix forward with
  the next patch version.
- **After every release** open `sync/main-into-dev`, cut from `dev`, and merge
  `main` into it with a merge commit. `qa` is never back-merged; it catches up
  at the next promotion.
- **Hotfix:** `hotfix/*` from `main`, pull request into `main` (the release
  tier runs because the base is `main`), tag, then the same `sync/` back-merge.
  Dependabot security updates always target the default branch (`main`) and
  the route refuses them there: re-open the change as a `hotfix/*` branch.
- **Rollback:** PyPI versions are immutable. Yank the release, revert the
  promotion merge with `git revert -m 1` through a pull request, and release
  the next patch version. Never force-push `main`.
- **Tags and back-merge pull requests are made by a person or a personal or
  App token, never `GITHUB_TOKEN`**: events it causes do not start workflows,
  so its pull request would never report `ci-ok` and its tag would never run
  `release.yml`.
- **Owner-only settings, outside this tree:** a ruleset per branch (pull
  request required, `ci-ok` required, the merge methods above, no force-push
  or deletion, the owner as the only bypass), a tag ruleset on `v*` (owner
  creates; no update or delete), and the `pypi` environment limited to `v*`
  tags. `main` stays the default branch, because the plugin marketplace
  install, the changelog URL and adopters all resolve it and it holds
  released code.

## Releasing

The `.claude-plugin/` manifests carry a `version`, generated from
`openspec_graph.__version__` by `make skill-manifests`. That number is not
decoration: Claude Code caches an installed plugin by version and refreshes it
only when the string changes. A rewrite of `SKILL.md`'s refusal text under an
unchanged version therefore reaches nobody who already installed the plugin --
they keep the cached copy, and the skill they run is not the skill in this
repository.

So: **any change under `skills/` or `.claude-plugin/` ships in a package
release.** A prose-only fix is still a patch bump, and the tag is what
publishes it. `SKILL.md`'s own `metadata.version` mirrors
`openspec_graph.__version__` for the same reason, and
`tests/test_agent_skill_docs.py` fails if the two drift, so there is one number
to bump rather than three to keep in step by hand.

The alternative — omitting `version` from the manifests so Claude Code falls
back to the resolved commit sha — was rejected: the manifests are pinned to the
package version by `AC-SD-7`, and releases here are already tag-driven, so a
sha-tracking plugin would refresh on every unrelated commit to the default branch while the
distribution it invokes stayed put.

The release checklist, in order (`prepare-release-0-3-0`): edit `__version__`
in `openspec_graph/__init__.py`; run `make skill-manifests`; run `make test`
and follow its failures, which name every remaining hand edit --
`test_skill_metadata_version_matches_the_package`,
`test_ci_template_pins_the_floor_the_skill_enforces` and
`test_compatibility_prose_matches_the_declared_minimum` for the three SKILL.md
fields, `test_every_changelog_version_links_to_its_release_tag` for the
changelog section and its link, and
`test_every_copyable_tag_ref_names_the_current_version` for every copyable tag
ref in the adopter corpus; then the hand edits no test names -- the SKILL.md
"Wiring it into CI" prose and the `version` example in
`.github/actions/planlint/action.yml`; then the changelog cut (the
`[Unreleased]` body moves verbatim under `## [X.Y.Z] — <date>`, the date being
the day the tag is pushed) and the runbook in `docs/distribution-plan.md` §3.
A future bump is one literal, one regeneration and one suite run.
From the release after 0.3.0, that whole list -- including the
runbook's post-tag ref flip -- lands as one release-prep pull request on
`dev` and promotes as described under *Branching and promotion* above.

## Adding a new pure derived-output module

`dialect_card.py`, `ledger.py`, `mermaid.py`, `sarif.py`, and `report.py` are
all the same shape: a
pure, stdlib-only module that projects a data structure some other module
already computed (a `StackProfile`, a `ParsedSpec` tree, `build_graph()`'s
dict, a findings envelope) into a derived output — a diffable snapshot, a ledger, a diagram,
SARIF, GitHub annotations — without registering a `Rule` or doing its own filesystem/network I/O.
`dialect_card.py`, `mermaid.py`, `sarif.py` and `report.py` import no sibling
module at all;
`ledger.py` imports `detect.to_posix_relative` — a shared pure-formatting
helper, not a data type it consumes — to render its `path` field the same
way every other consumer of that function does.

Follow the same shape for a new one:

1. One public function, `to_<thing>(data) -> <output>`, taking a shape the
   caller already has in hand rather than recomputing it. A module whose input
   comes from *outside* this process rather than from a sibling may instead
   expose one validating entry point plus a projection per output shape --
   `report.py` is the instance: it is handed a file somebody else wrote,
   possibly by another build, so `parse_envelope` raises a typed error once and
   every projection downstream of it is total. The rule the split preserves is
   the same one: no projection may re-check a field or raise.
2. Stdlib-only — no new dependency (`dependencies = []` in `pyproject.toml`
   is a load-bearing product boundary; see `docs/architecture/c4.md`).
3. Deterministic: same input, byte-identical output, every call. Add a
   `test_*_is_deterministic` test alongside the module's other pure-function
   unit tests, and — if the module is reachable from a CLI verb — a second,
   subprocess-level determinism test in `tests/test_enterprise.py` (see
   `test_graph_format_mermaid_is_deterministic` for the pattern).
4. Register the module in `tests/test_decomposition.py::_NEW_MODULES` so the
   decomposition/import-boundary tests cover it.
5. If the module renders a CLI-visible format, wire the dispatch in `cli.py`
   only — the module itself never calls `print`/`sys.exit`/`argparse`.
