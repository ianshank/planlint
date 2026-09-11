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
  module in the `mermaid.py`/`sarif.py` shape (`docs/hooks.md`, "Adding a new
  pure derived-output module"). Takes the findings envelope as a plain dict
  and projects it: `status_of(envelope)`, `to_annotations(envelope, *, limit)`,
  `to_step_summary(envelope)`, `to_outputs(envelope)`. It never evaluates a
  rule, never touches the filesystem, and never sees a `Path`.
- **`openspec_graph/cli.py`** — one new read-only verb,
  `report --findings FILE --format {sarif,github-annotations,github-summary,github-outputs}`.
  Reads an envelope written earlier by `validate --format json`, refuses any
  other `schema_version` with exit 2, prints the projection to stdout, writes
  nothing. `--format sarif` reuses `sarif.to_sarif` with the running build's
  rule table. Never exits 1: a projection is not a gate.
- **`.github/actions/planlint/action.yml`** — rewritten to the v1 contract:
  seven inputs (`target`, `version`, `fail-on`, `python-version`,
  `upload-sarif`, `upload-artifact`, `artifact-name`), thirteen outputs
  (`status`, `exit-code`, `errors`, `warnings`, `findings`, `blocking`,
  `specs-checked`, `rules-triggered`, `dialect`, `version`, `evidence-dir`,
  `json-path`, `sarif-path`). One `validate --format json` run into an
  evidence directory under `$RUNNER_TEMP`; SARIF, annotations, step summary
  and outputs projected from that file by `report`; `dialect-card.json` from
  `detect --format json`; `run.json` carrying the non-deterministic run
  metadata; `actions/upload-artifact` with `if: always()`; SARIF upload kept
  as an opt-out convenience and skipped on fork pull requests; the gate last,
  with `status` deciding it and `indeterminate`/`error` failing with their
  own messages. The CLI is installed from the action's own checkout by
  default (`$GITHUB_ACTION_PATH` resolved to the repository root); the
  `version` input becomes an explicit package-index override.
- **New `tests/fixtures/action/`** — five committed fixture targets
  (`passing/`, `failing/`, `empty-tree/`, `no-tree/`, `nested/`) that the
  contract job and the local fixture tests share.
- **`.github/workflows/ci.yml`** — new `action-contract` job: checks out this
  repository, runs `uses: ./.github/actions/planlint` against each fixture
  with `continue-on-error: true` on the step, and asserts the step outcome,
  every output, and the artifact, under `permissions: contents: read` with
  no secrets. The first time the action ever runs anywhere.
- **New `tests/test_report.py`** — unit tests for the module and end-to-end
  tests for the verb, including the byte-identity of `report --format sarif`
  with `validate --format sarif`, the escaping rules, the annotation cap, and
  the four statuses.
- **Existing guards extended, not bypassed** —
  `tests/test_cli_surface.py::ALLOWED_VERBS` gains `report`;
  `tests/test_skill_contract.py::READ_ONLY_INVOCATIONS` gains a `report`
  invocation (with a placeholder path substituted outside the target, the
  way `delta --baseline` already is);
  `tests/test_decomposition.py::_NEW_MODULES` gains `report`;
  `tests/test_sarif.py::test_the_composite_action_declares_the_expected_steps`
  is re-pinned to the new contract;
  `tests/test_adopter_urls.py::test_ci_template_pins_the_floor_the_skill_enforces`
  reads the pin from the template's `uses:` ref instead of a pip range; a
  new structural test in `tests/test_ci_hardening.py` covers the
  `action-contract` job; a new test forbids `pull_request_target` under
  `.github/`, `templates/` and `skills/`.
- **`templates/spec-gate.yml`** and its byte-identical twin
  `skills/planlint-spec-governance/assets/spec-gate.yml` — become a consumer
  workflow for the action: `pull_request` + `push` to the default branch,
  explicit `permissions` (`contents: read`, `security-events: write` only
  for the SARIF upload, with the line to delete if code scanning is off),
  `persist-credentials: false`, and the action pinned to the release tag
  whose version equals `openspec_graph.__version__`.
- **Docs and metadata** — `README.md` ("Wiring it into CI" leads with the
  action and states the pinning rule); `SKILL.md` (read-only table gains
  `report`; the CI paragraph describes the action); `references/exit-codes.md`
  (a `report` section); `llms.txt` (read-only verb list); `docs/hooks.md` (CI
  table row for `action-contract`); `docs/architecture/c4.md` (component row
  for `report.py`); `CHANGELOG.md`; `docs/next-steps.md` (the deferred items
  below, each with its reopen trigger); `docs/differentiation-roadmap.md`
  (CP-6 amendment naming what this change corrected).
- **Version sequencing rule, not a bump** — `report` is a new verb, so the
  skill's `planlint-min-version` must name the first release that carries it.
  If `v0.2.0` has not been tagged when this merges, `0.2.0` *is* that release
  and nothing moves. If it has, `openspec_graph.__version__` becomes `0.3.0`
  in this change and `make skill-manifests` regenerates what mirrors it.

## Non-Goals

- **No pull-request comments, no GitHub API client, no token input.**
  Annotations, the step summary, SARIF and the evidence artifact are the
  native surfaces. A comment adds a privilege boundary (`pull-requests: write`)
  the scan must never hold; if a real adopter asks, it is a *second*,
  `workflow_run`-triggered workflow reading the artifact, never a permission
  on the scan job and never `pull_request_target`. Reopen trigger recorded in
  `docs/next-steps.md`.
- **No raw `args` or `extra-args` input, and no `config`, `rules`, `exclude`
  or `mode` input.** None of the last four has a CLI counterpart today; an
  input with nothing behind it is a documented lie, and a pass-through is an
  undocumented public API. `extra-args` is deferred with a trigger: the first
  external adopter who names a flag they cannot reach.
- **No floating major tag (`@v1`), no Marketplace listing, no root
  `action.yml`.** Adopters pin an exact release tag or a full commit SHA.
  `add-sarif-and-actions` already declined the floating tag; this change
  keeps that and adds the reason it now costs nothing to keep: with the CLI
  installed from the action's own ref, the tag *is* the CLI version, and the
  release workflow already refuses a tag that disagrees with the package
  (`release.yml:78-85`). Revisit at 1.0, when the contract is declared
  stable.
- **No change to the findings envelope.** `rules.FINDINGS_SCHEMA_VERSION`
  stays `1`; no key is added, renamed or moved; the three golden hashes in
  `tests/test_decomposition.py::_EXPECTED_HASHES` are unchanged;
  `tests/baseline_rules.json` is unchanged. Timestamps and the action ref
  live in `run.json`, a separate file, precisely so the envelope stays
  byte-stable.
- **No `--output-file` on `validate`.** The read-only, stdout-only stance
  (`DEC-SA-012`, `AC-SA-12`) stands; the action redirects, as any caller
  does. The `report` verb *reads* a file, which `delta --baseline` and
  `detect --diff` already do.
- **No Docker action, no `actionlint` or `act` in the gate ladder.** The
  hosted `action-contract` job is the proof; a static YAML linter is a
  convenience whose trigger is a syntax error reaching `main`.
- **No PyPI release inside this change.** `docs/distribution-plan.md` §3 is
  manual and owner-executed. This change removes the *action's* dependency
  on it; it does not remove the README's, the skill preflight's or the
  pre-commit hook's.
- **No widening of `indeterminate` to "no machinery detected"** (a tree with
  specs but no Makefile target and no coverage-floor locator, where a pass
  proves little). That is a rule-semantics question — which facts must a
  target have for G003/G004 to mean anything — and gets the
  spec-drafter → spec-adversary pass on its own, not a status flag decided
  in YAML. Trigger recorded in `docs/next-steps.md`.
- **No new rule, no `Rule` field, no third-party dependency, no YAML
  parser.** The YAML artifacts are checked as text, as `DEC-SA-013` and
  `DEC-AQA-005` already argue.

## Affected Capabilities

- `github-action-contract`
