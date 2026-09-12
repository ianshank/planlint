# Change: Make the Composite Action a Thin, Unprivileged Scan Adapter (CP-GA)

## Why

The composite action shipped by `add-sarif-and-actions` was the right first
move — a foreign repository adds one step and sees findings on its diff — but
it is a red X with nothing behind it. It has never run for anyone, it exposes
no outputs, it produces no evidence a reviewer can download, and in the one
case where the CLI has nothing to say it relays that silence as green. Three
external reviews of this portfolio converged on one exit gate for planlint:
*a second person reproduces it in a clean environment*. The action is the
artifact that gate is measured on, and today it cannot be reproduced at all.

**Evidence:**

1. **The install line cannot resolve.** `.github/actions/planlint/action.yml:21-27`
   installs `planlint>=0.2.0,<1` from PyPI, and `action.yml:54` runs that
   line unconditionally. PyPI returns `404` for `planlint` and
   `pip index versions planlint` reports "No matching distribution found"
   (checked 2026-09-11). The only tag on `origin` is `v0.1.0`, under the
   pre-rename distribution name (`docs/distribution-plan.md` §2, row 1).
   Every consumer of the action, at every ref, fails at the install step.
   `docs/distribution-plan.md` §3 records the manual release unblock and
   makes "every install line resolves" its exit criterion — that plan is
   necessary for `pip install planlint`, but nothing in it is necessary for
   the *action*, which is checked out from this repository by the `uses:`
   reference and can install the CLI from that checkout.
2. **No outputs, no evidence, a file in the linted tree.** `action.yml` has
   an `inputs:` block (lines 11-43) and no `outputs:` block at all, so a
   consuming workflow cannot branch on the result without scraping logs.
   `action.yml:78` redirects `validate --format sarif` to `planlint.sarif`
   in the consumer's working directory — a write into the repository the
   tool promises only to read (`AC-SA-12`'s property, held by the CLI and
   broken by its wrapper). No JSON envelope is produced, nothing is uploaded
   as a workflow artifact, no annotation or step summary is emitted.
3. **A zero-spec run is reported green.** `openspec_graph/cli.py::cmd_validate`
   (`cli.py:404`, `cli.py:496-508`): a target with an `openspec/` directory
   but no change packages yields `0 spec(s) checked · 0 error · 0 warn ·
   0 info` / `PASS`, exit 0, and a `--format json` envelope of
   `{"specs_checked": 0, "findings": [], "blocking": 0}` — reproduced on an
   empty `openspec/changes/` directory. The action's gate step
   (`action.yml:98-112`) maps exit 0 to success, so a repository that just
   ran `planlint init` gets a green check for gating nothing. Exit 2 (no
   spec tree at all) is already reported distinctly, which shows the
   principle is agreed; it is the exit-0 vacuous case that leaks.
4. **Fork pull requests break before the gate.** `action.yml:87-92` guards
   the `upload-sarif` step on `hashFiles` only. On a pull request from a
   fork `GITHUB_TOKEN` is read-only, the upload fails on permissions, and
   the step ordering means the gate step — the one that explains what
   happened — never runs. The one event the action exists for is the one it
   handles worst.
5. **The projections already exist as pure data transforms.**
   `openspec_graph/sarif.py::to_sarif` (`sarif.py:103-109`) takes
   already-serialized finding dicts and the rule table — exactly the
   `findings` list the `validate --format json` envelope carries — so SARIF
   can be computed *from the envelope file*, after the fact, without a second
   `validate` run. That is what makes "one canonical evidence document, every
   other surface a projection of it" a structural property rather than an
   aspiration.
6. **The verb surface is closed on purpose.** `tests/test_cli_surface.py::ALLOWED_VERBS`
   pins nine verbs; `tests/test_skill_contract.py::READ_ONLY_INVOCATIONS`
   is held equal to `SKILL.md`'s read-only table. Adding a verb is a
   reviewed product decision, which is why this package records the
   alternative (a script inside the action directory) and the reason it
   loses.

## What Changes

- **New `openspec_graph/report.py`** — a pure, stdlib-only, zero-intra-package-import
  module in the `sarif.py`/`mermaid.py` shape. One gate, `parse_envelope`,
  turns any malformed payload into one typed error; everything downstream of it
  is total: `status_of`, `to_annotations`, `to_step_summary`, `to_outputs`,
  plus `parse_card`/`discovery_notes` for the detected-machinery facts. The
  schema versions it validates against are parameters, not imports.
- **`openspec_graph/cli.py`** — one new read-only verb,
  `report --findings FILE [--card FILE] [--path-prefix P] --format {sarif,github-annotations,github-summary,github-outputs}`.
  Reads a saved envelope, ignores the global `--target`, prints to stdout,
  writes nothing, exits 0 or 2 and never 1. `--format sarif` reuses
  `sarif.to_sarif` with the producer's version, which is what makes it
  byte-identical to `validate --format sarif`.
- **`.github/actions/planlint/action.yml`** — rewritten: six inputs, eighteen
  outputs, one `validate --format json` run into an evidence directory under
  `RUNNER_TEMP`, every other surface projected from it by `report`, the
  artifact uploaded under `always()`, and a gate that fails on `fail`,
  `indeterminate` and `error` with three distinct messages. The CLI is
  installed from a copy of the action's own checkout, so the build cannot write
  into the repository being scanned; `version` is an exact-version override
  that installs from the package index.
- **SARIF upload moved out of the action** into `templates/spec-gate.yml`,
  where the `security-events: write` it needs is visible to whoever grants it,
  and where a fork pull request and a repository without code scanning are both
  skipped rather than failed.
- **`templates/spec-gate.yml`** and its byte-identical twin in the skill —
  a consumer workflow: `pull_request` (with its own path in the filter, so the
  installing pull request is the first one the gate runs on), `push` to the
  default branch, `workflow_dispatch`; explicit least-privilege `permissions`;
  `persist-credentials: false`; the action pinned to an exact release tag.
- **New `tests/fixtures/action/`** — five labelled targets (`passing`,
  `failing`, `empty-tree`, `no-tree`, `nested`) with a README stating each
  one's expected status, and **new `tests/test_report.py`** and
  **`tests/test_action_contract.py`**. The second extracts the action's own
  shell steps from the YAML and executes them against each fixture with
  GitHub's environment simulated, so the status derivation, the evidence bundle
  and the gate messages are covered by `make test`.
- **`.github/workflows/ci.yml`** — a new `action-contract` job running the real
  action against every fixture under `permissions: contents: read` with no
  secret. The first time the action executes anywhere.
- **Two defects fixed in passing, because leaving either would make a criterion
  untrue rather than merely incomplete.**
  `tests/test_adopter_urls.py::_requirements` now also splits at `$` and `{`,
  so a shell-interpolated install line is seen by the rename guard instead of
  being skipped as somebody else's package. And every fallible step of the
  action clears `errexit` explicitly, because a composite `shell: bash` step
  starts with it on — found by executing the steps, not by reading them.
- **Existing guards extended, never bypassed** — `ALLOWED_VERBS`,
  `READ_ONLY_INVOCATIONS` (with a findings placeholder written outside the
  target, as `delta`'s baseline already is), `_NEW_MODULES`, the SKILL.md
  read-only table, the exit-code reference, `llms.txt`, `docs/hooks.md`'s CI
  table, `docs/architecture/c4.md`'s component table, the changelog, and the
  pin-parity test, which now reads the template's `uses:` ref and additionally
  requires it to equal the package version.
- **No version bump.** `v0.2.0` is not tagged, so `0.2.0` is the release that
  carries `report` and nothing that mirrors the version moves.

## Non-Goals

- **No pull-request comments, no GitHub API client, no token input.** A
  comment needs `pull-requests: write`, which the scan must never hold. If an
  adopter asks, the shape is a second `workflow_run` workflow reading the
  artifact — never a permission on the scan job, and never
  `pull_request_target`.
- **No raw `args` or `extra-args` input**, and no `config`/`rules`/`exclude`/
  `mode` inputs, none of which has a CLI counterpart. Three real flags are
  currently unreachable — `--change`, `--dialect`, `--require-witness` — and
  each becomes its own named input when somebody wants it. Reopen triggers are
  recorded in `docs/next-steps.md`.
- **No floating `v1` tag, no Marketplace listing, no root `action.yml`.**
- **No change to the findings envelope.** `FINDINGS_SCHEMA_VERSION` stays `1`,
  no key moves, the three golden hashes and the rule baseline are untouched.
  Non-deterministic values live in a separate `run.json` precisely so the
  envelope stays byte-stable.
- **No `--output-file` on `validate`.** The stdout-only, read-only stance
  stands; the action redirects, as any caller does. `report` *reads* a file,
  which `delta --baseline` and `detect --diff` already do.
- **No change to what `status` says about a target with no machinery.** The
  action now reports that the cited-stage and threshold rules had nothing to
  check against; changing the rules' own behaviour is policy and gets its own
  design pass.
- **No new rule, no `Rule` field, no third-party dependency, no YAML parser.**
  YAML is read by line scan, as `DEC-SA-013` and `DEC-AQA-005` already argue.
- **No PyPI release.** `docs/distribution-plan.md` §3 stays manual and
  owner-executed. This removes the *action's* dependency on it, not the
  README's or the skill preflight's.

## Affected Capabilities

- `github-action-contract`
