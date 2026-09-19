# Next Steps

What is intentionally **not** in scope yet, and the order to consider it. Each
item is deferred deliberately — adding it before the value is proven would be
over-engineering.

## After the first public tag (0.2.0)

Do **not** start this list before `v0.2.0` is tagged and `pip install planlint`
resolves. The in-tree remainder is not more rules; it is 1.0 credibility.
Each item is its own OpenSpec change, spec-drafter → spec-adversary first.

1. **Vacuous-pass policy — superseded by `docs/peer-review-2026-09.md`.**
   This item said "a target with no Makefile and no coverage floor currently
   passes G003/G004 vacuously". That was measured and is **half wrong**:
   G003 has no empty-guard and fires normally with no floor detected,
   falling back to `locator = "the governance policy"`. Only G004 fails
   open, through one line (`if not profile.make_targets: return`), and the
   coverage floor has nothing to do with it.

   The mis-statement was load-bearing. Framed as two rules and two kinds of
   machinery, the item read as a broad rule-semantics question and was
   deferred behind a design pass it does not need. The review splits it into
   R1–R8 there; three of those (find `GNUmakefile`/`makefile`; document
   `GENERIC_STAGES`; document `hard_coded()`'s bullet scoping) are hours of
   work each and close cases where the gate currently says PASS on a spec
   that is lying. Widening `indeterminate` stays a 1.0 policy question,
   exactly as the Action-contract deferral table records.
2. ~~**Finding line numbers.**~~ Shipped in `add-finding-line-hits`.
   `Rule.check` may yield `CheckHit` with a 1-based locus; `evaluate()` copies
   it onto `Finding.line` when `>= 1`. SARIF region and GitHub `line=` still
   omit a missing locus rather than clamping 0 to 1. Citation rules
   (G003–G005/G008) and whole-tree G006/G009 stay at line 0 on purpose.
3. ~~**Named Action inputs** for `--change` and `--dialect`.~~ Shipped in
   `add-finding-line-hits`. Empty defaults omit the flag. No raw
   `extra-args`. `--require-witness` stays off the Action (the store is
   gitignored; a fresh CI checkout always fails it closed).
4. **One real `evals/` run** (item 16 below), then **CP-8** agent-threat
   corpus + H007 with a CI-exposed catch-rate. Detect-corpus and matcher
   floors are already shipped.
5. SpecKit wrong-level heading WARN (item 4b) and U004 modal design (item 7c).
6. **Marketplace + floating `v1` only at 1.0** (DEC-GA-011).

Rule-pack plugins (item 3) and configurable discovery lists (item 4) stay
later than this list. They sharpen a tool nobody has adopted yet.

## Near term

1. ~~**Waiver audit report**~~ — shipped in CP-4 (`add-waiver-ledger-and-inv-lints`)
   as `planlint waivers --format json`: a stable-ordered ledger of every
   waived rule across the tree, with file, line, reason, and owning change.

2. ~~**Mermaid rendering**~~ — shipped in CP-GV (`add-mermaid-graph-export`)
   as `graph --format mermaid`, exactly the "thin renderer that consumes the
   JSON graph, kept out of the core projection" this item used to describe.
   **Dot/Graphviz image rendering stays rejected** (`AC-GR-6`, unrevised) —
   Mermaid is text GitHub/GitLab render natively; producing an actual image
   still needs an external engine and is still out of scope. If a consumer
   ever needs that specifically, `tools/render_mermaid.py`'s pattern (a thin
   external consumer of the saved JSON, not a core-projection change) is the
   template to follow.

3. **Rule-pack plugins** — today the 28 rules are a fixed tuple. If a target
   repo needs a custom convention (e.g. "every AC cites a JIRA ticket"), allow
   registering extra `Rule` objects via entry points. The deterministic
   contract (sorted, byte-stable JSON) must hold for plugins too.

4. **Configurable discovery lists** — `detect.py`'s `INVARIANT_SOURCES`,
   `ADR_SOURCES`, `MANIFESTS`, and the inline `governance-policy.json`
   candidate paths are fixed tuples with no override. Not a bug (nothing
   today is wrong; it's a coverage limitation of a working heuristic), but
   a repo with an invariant/ADR source or manifest convention outside the
   curated list is invisible to `detect`. Deliberately deferred out of the `add-dialect-cards` (CP-2)
   change that surfaced it: making these overridable reopens the same
   "should a hand-editable file change live-detected behavior?" question the
   `fix-init-snapshot-wording` change just resolved against (`detect` always
   re-derives fresh; a config file that overrides it reintroduces the
   stale-cached-belief problem this project exists to catch in target repos).
   Worth doing only with a clear answer to that question in hand.

4a. ~~**Symlinked feature/change directories double-count a spec**~~ — shipped
   in `fix-symlinked-spec-dir-double-count`. `Path.glob()` follows a *valid*
   directory symlink, so a `specs/002-alias -> specs/001-foo` link yielded two
   distinct `Path` entries for one `spec.md`: `feature_dirs` reported 2
   features for 1, and `graph.build_graph()` rendered duplicate `FR-001`/
   `SC-001` nodes. Fixed symmetrically across both discovery functions with a
   shared `_dedupe_by_identity()` helper, as this item required.

   One thing this item did not anticipate: `profile()` computes `change_dirs`
   from its own separate glob, so fixing only the two spec-file functions left
   it still double-counting. A test caught it; reading the code had not. The
   glob stays separate — a change package with no `spec.md` yet is still a
   change package — and simply gets the same dedup.

4b. **A `Functional Requirements`/`Success Criteria` heading at the wrong
   level silently yields zero extracted requirements/criteria, with no
   diagnostic** — `parse_speckit.py` correctly scopes its scan to the exact
   heading level SpecKit's own template uses (R-SK-30/AC-SK-49, closing a
   real over-matching bug), but the flip side is: a hand-edited spec with
   `## Functional Requirements` (H2, not the nested H3) yields `reqs: ()`
   with no warning, and still passes `S002`/`S003` cleanly (there's nothing
   to check). `G001` ("no requirements and no verifiable criteria
   recognized") only catches this if *both* are empty — a spec with working
   Success Criteria or GWT scenarios but a wrong-level FR heading passes
   silently. A candidate fix (e.g. a new WARN-level check surfacing "dialect
   is speckit but zero FR-/SC- bullets were extracted despite a `Requirements`-
   shaped section existing") needs the same spec-drafter → spec-adversary
   design pass the rest of this rule family got, not a rushed addition —
   false-positive risk against a legitimately FR-less, user-story-only draft
   spec needs real design work, not a guess.

   **Reproduced** at `c304a3d` (`docs/peer-review-2026-09.md` F4), and it is
   worse than "no diagnostic": it is silent data loss from the graph. One
   file, one heading level changed — H3 yields nodes `FR-001`, `FR-002`,
   `SC-001`; H2 yields `SC-001` alone. Both report `0 error · 0 warn · 0
   info`, `PASS`, `broken_links: 0`. The deferral reason above still holds,
   and does not apply to the discriminating case: a `Requirements`-shaped
   section that exists and yields zero FR bullets is not the same as no
   section at all, and only the former needs to warn. Tracked as **R6**.

## Medium term

5. ~~**Sarif output**~~ — shipped in `add-sarif-and-actions` as
   `validate --format sarif`, a projection over the findings `validate`
   already computed, plus a composite Action and `.pre-commit-hooks.yaml`.

   One thing this item's framing got wrong, and it is the interesting part:
   findings carry `path`/`line`/`rule`/`severity`, but when SARIF first
   shipped **no rule set a line** — every finding reaching the CLI had
   `line == 0`. SARIF's `startLine` minimum is 1, so clamping would have put
   a wrong annotation on the first line of every file in every pull request,
   with no way for a reviewer to tell it was wrong. The region is omitted
   instead. `add-finding-line-hits` later fills `Finding.line` when a check
   holds a real locus (`CheckHit`); the omit-when-`< 1` rule is unchanged.

   Deferred from `add-github-action-contract`, each with a reopen trigger
   rather than a date:

   - **Pull-request comments via a `workflow_run` reporter.** The action stays
     unprivileged (`contents: read`). Reopen when an adopter needs review
     comments that code-scanning annotations do not cover.
   - **`extra-args` input.** Rejected as a raw pass-through. Reopen only for a
     named, tested flag that the CLI already supports.
   - **Floating major tag and Marketplace listing.** Held until 1.0
     (`DEC-GA-011`). Reopen when the contract is declared stable; a Marketplace
     listing needs a root `action.yml`.
   - **SARIF subdirectory prefix.** `target` other than `.` still places
     annotations relative to the wrong base (`DEC-GA-007`). Reopen when an
     adopter has a monorepo that cannot run the action with a working
     directory.
   - **`evidence-sha256` output.** Reopen if two runs of the same tree need a
     machine-checkable identity stronger than byte-identical evidence files.
   - **Widening `indeterminate`.** Today it is "zero specs checked". Reopen if
     "no machinery detected" (no Makefile, no coverage floor) should fail
     closed the same way.

6. **Coverage trend gating** — `check_coverage_floor.py` gates against an
   absolute floor. A trend gate (branch coverage must not *decrease* vs.
   merge-base) would mirror the graph-diff pattern for coverage.

7. ~~**CI wiring for `detect --diff`**~~ — closed by a different route than
   the one this item imagined. `fix-detect-corpus-defects` added
   `tests/corpus/targets/`: labelled target repositories whose expected
   dialect card is compared through the same `dialect_card.diff_cards()` that
   `--diff` uses, on every `make test`. That *is* a detection-drift gate, run
   against a labelled set of known shapes rather than against one saved baseline of
   this repo, which is the more useful of the two. A `detect --diff` job
   against a committed baseline of this repository stays unwired: its card
   changes only when the Makefile or floors change, and both already fail
   other gates.

7a. **`scoped_fail_under` reads the common TOML forms, not all of them** —
   `[tool.coverage.report]` as a table header — plain, spaced, or with quoted
   segments (`["tool"."coverage"."report"]`) — is recognised, and lines
   inside multi-line strings and arrays under it are skipped. A dotted key at
   top level (`tool.coverage.report.fail_under = 90`) or an inline table
   (`report = { fail_under = 90 }`) reads as "no floor"; both are pinned in
   `tests/corpus/targets/` as limits. Neither was ever read by the old
   whole-file regex either (which matched under every table, and so also
   attributed floors from unrelated tables to this one). The trade was made
   deliberately. A stdlib
   `tomllib` parse would cover every form but only on 3.11+, and detection
   must be byte-identical across the whole matrix. Revisit when 3.10 leaves
   the matrix.

7b. **Mutation testing, evaluated and deferred** — `mutmut` was tried
   against the parsers and cancelled before producing a single kill/survive
   count. What the attempt established is that it cannot run here at all
   without deselecting two of this repo's own self-checks
   (`test_new_modules_stdlib_only` rejects mutmut's injected trampoline
   import; `test_typecheck_passes_on_clean_repo` fails under the mutants
   tree). The Hypothesis half of the same evaluation landed as
   `tests/test_properties.py`. Adopting mutation testing is its own change
   package with a real measurement, and any score floor it introduces goes
   in `pyproject.toml`, never the Makefile.

7c. **U004 counts SHALL/MUST and nothing else** — the eleven requirements in
   `tests/fixtures/phrasing/requirements-modal-variants.jsonl` ("is required
   to", "ought to", "Sessions expire after 30 minutes") are normative in
   spirit and use neither word. U004's message says "uses no SHALL/MUST", so
   they are not scored as misses. Whether the rule *should* accept them is a
   design question with a real false-positive cost (a descriptive "Validation
   happens before apply" is not an obligation) and needs the spec-drafter →
   spec-adversary pass, not a regex widening.

8. ~~**CI runs the platform/encoding guards in the environments they
guard**~~ — shipped in `harden-two-track-e2e-aqa`: a `test-windows` leg
   (the suite on `windows-latest`) and an `encoding-stress` leg (`make
   e2e-live` under `PYTHONIOENCODING=ascii`), closing the ubuntu-only gap
   that let three Windows-blind defects ship green.

## Deferred by the GitHub Action contract (`add-github-action-contract`)

Each was considered while designing the composite action, and each is deferred
with the trigger that reopens it — not omitted.

| Deferred | Reopen when |
|---|---|
| **Pull-request comments.** | An adopter says annotations, the job summary and the evidence artifact are not enough. The shape is already decided: an unprivileged scanner on `pull_request` uploading an artifact, and a separate `workflow_run` workflow that checks out trusted default-branch code, downloads that artifact and comments. Never a write permission on the scan job, and never `pull_request_target`. |
| **An `extra-args` input.** | A named external adopter cannot reach a flag they need. Three real `validate` flags are currently unreachable through the action — `--change`, `--dialect`, `--require-witness` — and each should become its own named input when somebody wants it, rather than a pass-through that makes the whole CLI an undocumented public API. `--require-witness` is the one to leave alone: the witness store is gitignored, so a fresh CI checkout always fails it closed. |
| **A floating `v1` tag and a Marketplace listing.** | The contract is declared stable at 1.0. Both need a root `action.yml` or a moving tag, and moving a tag on every release needs `contents: write` in the release workflow, which currently holds `contents: read` plus `id-token: write` on the publish job alone. Widening that for a convenience is the wrong trade while an exact tag already pins the CLI. |
| **SHA-pinning the third-party actions inside `action.yml`.** | The pins can be resolved and verified. `setup-python@v5` and `upload-artifact@v4` float by major tag today while the README tells adopters to pin exactly — a real inconsistency, deferred only because a wrong sha is worse than a floating tag and this pass could not verify them. |
| **Rebasing SARIF paths for a subdirectory target.** | Someone runs the action in a monorepo. Annotations already carry the prefix (`report --path-prefix`); SARIF does not, because rebasing it would break the byte-identity with `validate --format sarif` that the projection is held to. The fix is the same flag applied to the SARIF projection, behind the same opt-in. |
| **Widening `indeterminate` to "no machinery detected".** | The rule-semantics question gets its own spec-drafter → spec-adversary pass. A target with no Makefile and no coverage floor passes the cited-stage and hard-coded-threshold rules vacuously; the action now *reports* that through `discovery-warnings` and a warning annotation, which is projection. Changing what `status` says about it is policy, and policy belongs in the rules. |
| **A per-rule canonical-envelope snapshot corpus.** | The rule set stops changing shape. Each rule already has passing and violating fixtures in the test suite; what does not exist is a committed golden envelope per rule, which would re-pin on every registry edit for a property the existing tests already hold. |

## Deferred / out of scope

8. **Autonomous spec generation** — using an LLM to *author* specs is explicitly
   out of scope. `planlint` evaluates specs; it does not propose them (see
   `docs/agents-skills-harness.md`). Authoring stays a human responsibility.

9. **Docker as primary delivery** — the `Dockerfile` is a convenience runner.
   `pip install` remains the primary path; Docker is not required for local dev
   and the Makefile never depends on it (DEC-EH-001).

## Hooks & loops (deliberately not wired yet)

Each of these is a real opportunity, but is deferred until the value is proven so
it is not cargo-culted into the v0.1 surface.

10. **`make watch` dev loop** — a file-watcher that re-runs `make validate` (or
    `make test -- -k spec`) on every spec/source change. Worth adding only with a
    dependency-free watcher (stdlib `asyncio` + `os.stat` polling, or `watchdog`
    as an optional extra). Today the pre-commit hook already runs validate on
    commit, which covers the main need.

11. **Scheduled self-validation cron** — a scheduled job that runs `planlint
    validate --fail-on ERROR` + `make security` against `main` to catch spec/rules
    drift introduced by dependency or tooling bumps. Only justified once the repo
    is consumed by more than one team; for a single-consumer v0.1 tool the PR CI
    gate already enforces this on every change.

12. **Pre-push hook** — `make pre-pr` is the one-command gate; a `.git/hooks/
    pre-push` that calls it would catch a broken push before CI. Documented as
    optional in `docs/hooks.md` rather than forced, because the full suite
    (coverage included) is slower than the six commit-time hooks (lint,
    typecheck, security, validate, docs-check, thresholds) and most pushes
    are already covered by pre-commit + CI.

18. **`E501` is configured but not enforced** — `[tool.ruff] line-length = 100`
    has always been set, but ruff's `select` was never set either, so the
    default `E4/E7/E9/F` applied and the `E5` group (line length) was never
    on. Turning it on reported **100 violations** when this note was
    written; re-measured at `c304a3d` it is **122**: 28 in `openspec_graph/`,
    8 in `tools/`, 86 in tests. The debt grew 22% while being tracked here as
    a fixed number, which is the argument for doing the rewrap rather than
    re-counting it again. The `select` list added alongside
    this note enables every family that was already at or near zero, and
    names `E501` as the one deliberate omission. The work owed is the
    rewrap, as its own change: bundling 100 reflowed lines across a dozen
    files into an unrelated branch buries whatever else that branch did.

19. **`tools/` is linted and typechecked but measured by nothing** —
    `[tool.coverage.run] source` is `["openspec_graph"]`, so the gate scripts
    that enforce every other gate have no coverage number of their own. Adding
    `--cov=tools` reported 88.3% line / 84.6% branch when this note was
    written, "which fails the 90% floor". **That premise no longer holds.**
    Re-measured at `c304a3d`: **91.41% line, 89.32% branch — both floors
    pass**, so nothing blocks turning it on. The diagnosis below survives its
    numbers, and is sharper than the figures suggest: `tools/` alone measures
    66.5% line, with four scripts at *literally* 0%
    (`check_coverage_floor`, `check_branch_coverage`, `diff_spec_graph`,
    `render_mermaid`) despite `tests/test_ci_hardening.py` demonstrably
    executing them. The shortfall is mostly *measurement*, not absence:
    several tools are exercised only through `subprocess.run` calls that do
    not inject `COVERAGE_PROCESS_START`, so their lines are invisible even
    though tests run them. `tests/support.py`'s `run_cli` already does this
    correctly for the CLI; the fix is a sibling helper for tool invocations,
    after which the real gaps (`_common.write_or_check`'s check-mode branches,
    `check_secrets`'s gitleaks-present path) can be judged on their merits.
    Worth doing before the floor is ever raised, since today the number does
    not describe what it claims to.

## Skills / agents

13. **Rules as reusable skills** — the 28 rules already are the reusable
    "skills" and the evaluator is the deterministic harness (see
    `docs/agents-skills-harness.md`). The future extension point for composing
    rule packs across repos is item 3 (entry-point `Rule` registration). No
    autonomous agent layer is planned: the harness evaluates, it never proposes
    or acts (INV-16 — the evaluator proposes nothing).

14. **The distributable Agent Skill is a caller, not an agent layer** — since
    `add-agent-skill-distribution`, `skills/planlint-spec-governance/` tells an
    external agent how to *invoke* this CLI. That does not contradict item 13:
    the skill contains no rule logic, its catalog is generated from the
    registry, and the agent reading it is somebody else's, running outside this
    process. The harness still only disposes.

15. ~~**PEP 639 licence metadata**~~ — shipped in
    `migrate-license-metadata-pep639`. `pyproject.toml` now declares the SPDX
    string `license = "Apache-2.0"` plus `license-files = ["LICENSE"]`, with
    `[build-system] requires` raised to `setuptools>=77` in the same commit and
    the redundant `License ::` classifier removed, which PEP 639 forbids
    alongside an expression. A wheel build went from four deprecation warnings
    to none.

    The blocker recorded here was that setuptools 77 needs `packaging>=24.2`
    at build time and the machine had a distro-managed 24.0. That premise was
    wrong rather than merely stale: `python -m build` resolves build
    requirements in an *isolated* environment, so the ambient `packaging`
    version never applied. The lesson is worth more than the item — a
    "cannot verify here" blocker is only real once you have checked that
    "here" is where the thing actually runs.

    The obvious fail-closed criterion, that a build with no `LICENSE` file
    fails, was tested and is **false**: setuptools accepts a `license-files`
    glob matching nothing and ships a wheel with no licence, silently. So the
    gate reads the artifact instead — `tools/check_wheel_metadata.py`
    (`make wheel-check`) fails when the SPDX expression is missing or does not
    match `pyproject.toml`, when a legacy classifier survives, or when a
    declared licence file is absent or empty, and exits 2 when there are no
    wheels at all. It runs in a new `packaging` job on every pull request and
    in the release workflow before anything reaches an index whose versions
    are immutable.

16. **CI wiring for the eval suite** — the cases under `evals/` have no job
    running them. `claude plugin eval` needs a plugin runtime CI does not have,
    and the adversarial half is non-deterministic by nature, so it stays a
    manual pre-release check rather than a gate. `tests/test_agent_artifacts.py`
    validates the suite's *structure* deterministically, which is the part that
    can be gated. Revisit if a headless runner appears.

17. **Deliberately not done for the skill (yet)** — a published tool wrapper
    for programmatic multi-agent frameworks (a subprocess shim with its own
    release cadence, shipping untested from here); a hosted evaluation dataset
    (the suite under `evals/` is the source, an export is mechanical); and any
    skill capability that would let an agent write a waiver, record a witness,
    or edit a threshold. The last one is not a roadmap item but a permanent
    non-goal — those are exactly the moves the adversarial evaluation cases
    exist to prove the skill refuses.
