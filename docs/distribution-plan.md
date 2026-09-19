# planlint distribution plan

> Planning artifact, not a change package. It supersedes an earlier plan
> ("Publish `planlint-spec-governance`") that was written against `875ab72`,
> before `add-agent-skill-distribution` merged. Current as of that merge.
> Contract changes named below get their own OpenSpec change package; nothing
> here authorizes an edit on its own.

The skill, its generated catalog and manifests, the retrieval config, the
evaluation suite and the release workflow all exist. The composite Action
already works from any git ref of this repository (checkout install). What
does not exist is a **PyPI release**: no `v0.2.0` tag has been pushed, so
`pip install planlint`, the skill preflight, and the Action `version:`
index override still 404. That is the remaining critical path. Adopter
templates pin a commit SHA until the tag exists; switch them to `@v0.2.0`
in the same sitting as the publish. Everything else on this page is hygiene
that should not delay §3.

---

## 0. Release readiness, verified at `a1b6868`

Every row below was **run**, not read. The engineering side of 0.2.0 is done;
what remains is §3, and §3 is entirely outside this repository.

| Gate | Command | Result |
|---|---|---|
| Full enterprise ladder | `make pre-pr` | exit 0 |
| Coverage | `tools/check_coverage_floor.py`, `check_branch_coverage.py` | line 99.3% (floor 90), branch 97.6% (floor 80) |
| Self-validation | `planlint --target . validate --fail-on ERROR` | 40 specs, 0 error / 0 warn / 0 info (37 at `a1b6868`; three change packages added since) |
| Types, lint | `make typecheck`, `make lint` | mypy clean over 42 files; ruff clean |
| Live CLI, incl. ASCII console | `make e2e-live` | exit 0 |
| Prose-matcher floors | `make matcher-accuracy` | every configured floor met |
| Generated-artifact freshness | both `render_*.py --check` | both fresh |
| Install from git | `pip install git+…@a1b6868` in a clean venv | prints `planlint 0.2.0` |

Still unpublished, confirmed live rather than inferred: `planlint` and
`openspec-graph` both 404 on PyPI; the only GitHub release is `v0.1.0`
(2026-08-30, pre-rename); no `v0.2.0` tag exists on `origin`.

**GitHub surface, still outstanding** — each checked against the repository
API, not the plan's memory of it:

| Field | Now | Should be |
|---|---|---|
| Homepage | still points at the pre-rename `OpenSpec-Graph` repository | `https://github.com/ianshank/planlint` |
| Description | "A dependency-graph linter for OpenSpec specs…" | the README wedge sentence |
| Topics | `developer-tools`, `linter`, `openspec`, `python`, `specification` | add `agent-skills`; `speckit` is also a shipped dialect and absent |
| Wiki | enabled and empty | disabled, or a one-line stub pointing at the README |

---

## 1. Where we are

| Original plan item | Status | Evidence |
|---|---|---|
| Decide the distribution name | Done | `pyproject.toml` `[project] name = "planlint"` |
| Adopter-facing rename off `OpenSpec-Graph` | Done | one historical mention remains, in a merged change package |
| Skill tree, references, CI asset | Done | `skills/planlint-spec-governance/` |
| Rule catalog generated, staleness gated | Done | `tools/render_rule_catalog.py`, `test_rule_catalog_is_fresh` |
| Claude plugin + marketplace manifests | Done, generated | `tools/render_plugin_manifests.py` |
| Trusted-publishing release workflow | Done, never run | `.github/workflows/release.yml` |
| `context7.json` committed | Done | repo root |
| `llms.txt` committed | Done | repo root |
| Evaluation suite | Done, with remaining gaps | `evals/`; structure gated; most cases still LLM-graded; the suite has never been executed by its intended runner. See §2. |
| Machine-readable findings schema | **Done** | `add-findings-json-envelope`; `validate --json` carries `schema_version` + `tool_version`, paths relative |
| Slice 1 hygiene (`AGENTS.md`, name disambiguation, adopter-URL tests, skill metadata version, eval grader fixes) | **Done** | shipped in PR #18 and follow-ups; this document's earlier "Not started" row was stale |
| Slice 2 findings JSON envelope | **Done** | see the Slice 2 heading below |
| Tag, publish, index, topics | **Not started** | §3 — the remaining owner path |
| Wrapper script, `--version --json`, per-agent copies, dataset export | **Cut** | §5 |

## 2. Facts the earlier plan, or the tree, got wrong

Each row was checked against the checkout or the live index, not inferred.

| Claim | Reality |
|---|---|
| `0.1.0` was never tagged (CHANGELOG) | `v0.1.0` exists on `origin` at `cdc94ca`, under the pre-rename distribution name |
| `v0.2.0` is the first tagged release, first published to PyPI (CHANGELOG) | No `v0.2.0` tag exists; the release workflow has never run; nothing is published |
| The distribution name was undecided | Decided and merged; `planlint` is free on PyPI, `plan-lint` is taken by an unrelated project |
| `pip install planlint` works (README, skill preflight, CI template) | `pip install` and the skill preflight still 404 until §3. The CI template and README Action snippet no longer go through PyPI: they pin a commit SHA and the Action installs from checkout. |
| Findings JSON is portable | `validate --json` emits absolute, native-separator paths and no schema version, while the CI template uploads that file as a cross-machine artifact |
| Evaluations are graded on tool calls and file state (both READMEs) | Most cases are adjudicated by a model reading the transcript; only a few carry a deterministic grader. Still true: ~15 of 24 cases are LLM-only. |
| One evaluation case proves the skill refuses to record a witness | **Fixed.** `evals/fabricate-witness/graders/witness-not-run.md` is a regex grader on `planlint\s+witness` with `match: false` — it forbids the verb, not the shell. A correct CLI run that never calls `witness` passes it. |
| Eval summaries belong under `reports/` | **Mitigated.** The runner writes `evals/results/`, which is gitignored. `tests/test_agent_artifacts.py` discovers cases by `prompt.md`, so `results/` is not treated as a malformed case. |
| `--json` is the way to get either command's structured output (skill body) | For `detect` it selects a legacy shape with machine-specific paths; the portable card is `--format json`. The skill body now says so. |
| The skill's own metadata version tracks the package | **Fixed.** `metadata.version` / `planlint-min-version` are gated against `__version__`. |
| A wrapper script is needed so agents can invoke the CLI | The project already declined a wrapper, for reasons that still hold |
| Copies of the skill are needed under other agents' directories | The marketplace source form in use is the documented one, and the skill carries no repository-relative references |

## 3. Phase 0 — release unblock

Manual, outside the repository, in this order. Slice 1 and slice 2 are
already in `main`. Nothing in §4 blocks these.

GitHub surface, before the tag:

- Repository description → the README wedge sentence.
- Homepage → `https://github.com/ianshank/planlint` (today it still names
  `OpenSpec-Graph`).
- Topics: add `agent-skills`. The existing `developer-tools`, `linter`,
  `openspec`, `python`, `specification` set can stay.
- Disable the empty wiki, or put a one-line stub that points at the README.
  An enabled empty wiki is a dead product surface.

Then the publish sequence:

1. Confirm the distribution name is still unclaimed on PyPI (`planlint`
   404s; `plan-lint` is somebody else's project).
2. Register a **pending trusted publisher** on PyPI: project `planlint`, owner
   `ianshank`, repository `planlint`, workflow `release.yml`, environment
   `pypi`. The environment string must match the release workflow's
   `environment:` value exactly; a mismatch fails only at the final step,
   after the whole gate has already run.
3. Create the GitHub environment `pypi` (today only `copilot` exists). A
   required reviewer here means the publish job waits for approval rather
   than failing.
4. `workflow_dispatch` `.github/workflows/release.yml` once on `main`. `gate`
   and `build` run; `publish` is `if: github.ref_type == 'tag'` and must be
   skipped. This is the dry-run. Do not push a tag until it is green.
5. Tag the merge commit whose package version matches the tag (`0.2.0`),
   and push `v0.2.0`. The build job compares the two and fails on a mismatch.
   Do not push the tag as a documentation convenience without steps 2–3:
   the workflow will run and the publish job will go red.
6. Watch the three jobs. `gate` is the first time the full pre-PR ladder runs
   in continuous integration on a tag; `build` is the only thing anywhere that
   exercises the installed console script; `publish` needs the OIDC identity
   from step 2.
7. Install the published distribution into a fresh virtual environment, run
   the version command, and re-run by hand every install line this repository
   prints. Switch the Action `uses:` refs in the README, both `spec-gate.yml`
   copies, and `.pre-commit-hooks.yaml` from the interim SHA to `@v0.2.0`.
8. Create the GitHub release from the `[0.2.0]` changelog section.
9. Submit the repository to Context7. The committed configuration means the
   indexed scope does not depend on choices made in a web form.

**Exit criterion:** `pip install planlint` in a fresh venv prints
`planlint 0.2.0`, and `uses: ianshank/planlint/.github/actions/planlint@v0.2.0`
resolves.

**Failure mode:** tag without the publisher → the Action pin starts working,
PyPI still 404s, the release workflow is red. That is a half-product. Do
steps 2–6 in one sitting.

**First foreign CI adopter (after the tag, or on the SHA until then).** Copy
`templates/spec-gate.yml` into `ianshank/Agents` at `fail-on: ERROR`. A live
scan of that clone at this writing is exit 0 with four G009 WARNs — keep
ERROR so those warnings do not fail the first install. Do not enable the
gate on `Mouse-Droid-AGI` (45 ERROR; unstable default branch) or
`Hex-vision` (zero specs checked, dialect `unknown`: a hollow pass). A
follow-up in Agents, not here: eval-corpus-plan D6 — `planlint validate
--fail-on ERROR` as the objective grader for `openspec-quality-plan` /
`openspec-peer-review`, paired with `detect` so exit 2 is not conflated
with fail.

## 4. Phase 1 — in-repo slices

### Slice 1 — hygiene, guards, evaluation fixes — **shipped**

Shipped across PR #18 and follow-ups. The table below is the original
checklist, kept as a record; do not re-open it as a backlog.

No published contract changes. Files and the test that pins each:

| Work | Files | Pinned by |
|---|---|---|
| Agent entry point | `AGENTS.md`, `.dockerignore` | link-resolution test alongside the existing one for `llms.txt` |
| Name disambiguation | `README.md`, `llms.txt`, `context7.json` | `tests/test_adopter_urls.py` |
| Install-line guard | `tests/test_adopter_urls.py` (new) | itself |
| Changelog corrections | `CHANGELOG.md` | `tests/test_adopter_urls.py` |
| Architecture doc corrections | `docs/architecture/c4.md` | prose review |
| Stale milestone sentence | the merged change package's `tasks.md` | `make validate` |
| Skill metadata version + policy | `SKILL.md`, `docs/hooks.md` | new test in `tests/test_agent_skill_docs.py` |
| Evaluation defects and gaps | `evals/**` | `tests/test_agent_artifacts.py` |
| Structural test tightening | `tests/test_agent_artifacts.py` | itself |
| Unpinned exit-code quotes | `tests/test_skill_contract.py` | itself |
| Build backend in the dev extra | `pyproject.toml` | none needed |

**Merge gate:** `make pre-pr`, plus both generator `--check` modes, plus a
self-validation run at the warning level so the graph-diff job cannot regress.

### Slice 2 — findings JSON envelope — **shipped**

> Shipped as `add-findings-json-envelope`, before the first tag, exactly as
> the sequencing below required. `DEC-FE-001` records the supersession and
> narrows it honestly: the artifact-upload evidence defeats `DEC-PS-002`'s
> first argument only, and `Finding.as_dict()`'s default stays absolute for
> backwards compatibility. `detect --json` was deprecated in the same change,
> since removing a flag after publication is a break.

Its own change package, because it supersedes a recorded decision. The
decision held that absolute paths were acceptable because none of the affected
fields is ever compared across two checkouts. The CI template refutes that: it
uploads the findings file as a build artifact, produced on a runner and read
elsewhere.

Shape of the work: give each finding a repository-relative POSIX path, using
the helper already applied at every other call site; wrap the payload in a
schema version and the tool version; keep the top-level target absolute, since
it is now the base those relative paths resolve against; keep the existing key
spelling, because renaming it is a second break that buys nothing. Re-pin the
golden output hash and normalize the version out of that fixture so future
releases stop re-pinning it.

### Slice 3 — evaluation fixtures (optional, later)

Per-case scaffolding would unlock file-state graders for the destructive
cases and a discovery case where both dialects are present. Not a gate: the
existing stance on running the suite in continuous integration stands.

## 5. Deferred, with the trigger that reopens each

| Deferred | Reopen when |
|---|---|
| A wrapper script inside the skill | A named consumer cannot shell out to the CLI directly |
| Version output as JSON, with a ruleset fingerprint | A consumer needs the fingerprint and the version in one call; today the rules verb and the version flag cover it between them |
| Exporting the evaluation suite as a dataset | Someone wants to run these cases outside the runner they were written for; the export is mechanical from what is already committed |
| Copies of the skill under other agents' directories | An agent's installer cannot read a skill directory from a git source |
| Declaring allowed tools in the skill frontmatter | A recorded evaluation failure traces to a permission prompt, and only after confirming what the declaration pre-approves |
| Running the evaluation suite in continuous integration | A headless, deterministic runner exists |
| A freshness check target in the pre-PR ladder | A stale generated artifact reaches CI, contradicting the reasoning that keeps writers out of the gate table |

## 6. Non-goals

Unchanged from the project's standing position: no spec authoring, no MCP
server, no rename of the import package or the waiver prefix, no container as
the primary delivery path, and no skill capability that would let an agent
write a waiver, record a witness, or edit a threshold. Added here: no second
copy of the skill inside this repository, and no claim in the README about an
agent load path this project has not tested.

## 7. Verification ledger

```
make pre-pr
python tools/render_plugin_manifests.py --check
python tools/render_rule_catalog.py --check
planlint --target . validate --fail-on WARN
```
