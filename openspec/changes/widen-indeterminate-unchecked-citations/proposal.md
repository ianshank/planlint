# Change: Widen `indeterminate` to Unchecked `make` Citations (R8 / D3.3)

## Why

The composite Action's `status` exists so that a green check means the specs
were measured. `add-github-action-contract` closed the first hole — a run that
checked zero specs is `indeterminate`, not `pass` — and deliberately left a
second one open: a run whose specs cite `make` stages against a target where
not one of those citations could be checked. `report-unchecked-make-citations`
then shipped G010, so the CLI now *says* when the cited-stage check could not
run. The Action still projects that run as `pass`. The headline claim of this
project is about citations; that run checked document shape and not a single
citation, and the check is green.

**Evidence:** re-measured 2026-10 against this tree at `6666444`, and
tabulated in `docs/peer-review-2026-10.md` (N5, D3, R8).

1. **`status_of` cannot see an unchecked run.**
   `openspec_graph/report.py::status_of` (`report.py:339-357`) returns `fail`
   when `blocking > 0`, `indeterminate` only when `specs_checked == 0`, and
   `pass` otherwise. Reproduced (`docs/peer-review-2026-10.md` N5, item 1): a
   target with no Makefile and no coverage floor whose one spec cites a make
   stage yields `INFO  G010 ... 1 distinct `make` stage(s) not checked: no
   make targets were detected in the target repo, so G004 could not run`,
   the summary `1 spec(s) checked · 0 error · 2 warn · 1 info`, `PASS`, exit
   0 — and `report --format github-outputs` over that envelope with the
   target's card prints `status=pass`, `infos=1`, `make-targets=0`,
   `discovery-warnings=2`. The only signal is two warning annotations, which
   the gate step (`action.yml:348-384`) never reads.
2. **`fail-on: INFO` is too blunt an escalation.**
   `openspec_graph/rules.py::evaluate` (`rules.py:118`) builds every waived
   finding as `severity=INFO if suppressed else rule.severity`, so every
   justified waiver of every rule is also an INFO finding. A consumer who sets
   `fail-on: INFO` to catch unchecked citations fails on every waiver in the
   tree as well (N5, item 3). The severity contract in `rules.py:18-21` —
   "INFO: observation, never blocks" — is the right contract for the CLI and
   the wrong lever for this question.
3. **A waiver of G010 has no effect today.**
   `<!-- specgraph:allow G010 reason -->` yields
   `INFO  G010 ... [waived] 1 distinct `make` stage(s) not checked ...` —
   still INFO, still counted at `--fail-on INFO` (reproduced, exit 1; N5,
   item 2). `tests/test_e2e_corpus.py::test_a_waived_g010_still_fails_a_fail_on_info_run`
   and `tests/test_graft_rules.py::test_g010_and_g011_waivers_keep_the_finding_visible`
   pin exactly this, and `CHANGELOG.md`'s `Unreleased` entry records it as
   "G010 is effectively unwaivable". The waiver is the ledgered, reasoned
   escape this project built (`planlint waivers` lists it; G007 refuses it
   without a reason), and for this one rule it currently changes nothing but
   a prefix.
4. **The envelope does not record waived-ness.**
   `openspec_graph/rule_types.py::Finding.as_dict` (`rule_types.py:93-100`)
   emits `rule, severity, message, path, line, subject` and nothing that says
   whether the finding was waived. The only trace is the `[waived] ` message
   prefix that `rules.evaluate` (`rules.py:119`) and `rules.evaluate_tree`
   (`rules.py:151`, `rules.py:164`) prepend. `report._REQUIRED_FINDING_KEYS`
   (`report.py:113`) reads five of those six keys; a status predicate that
   needs waived-ness has nothing to read.
5. **The discriminating case is real and must stay `pass`.**
   A target with no Makefile whose specs never cite a make stage produces no
   G010 — pinned by
   `tests/test_graft_rules.py::test_g010_is_silent_when_the_spec_cites_no_make_target`,
   and reproduced: G003/H001/H006 fire on such a spec, G010 does not
   (`docs/peer-review-2026-10.md` Appendix H). A tox or npm repository whose
   specs do not pretend to use Make has nothing unchecked. That is why the
   2026-09 review's D3 (`docs/peer-review-2026-09.md:307-331`) rejected the
   card-shaped predicate "no Makefile and no coverage floor", why the 2026-10
   review's D3 (`docs/peer-review-2026-10.md:313-337`, "What should
   `indeterminate` mean?") rejected the deferral table's reopen trigger of
   the same shape, and why `report.discovery_notes()` (`report.py:379-408`)
   is the wrong input for a status change: it fires whenever the card has no
   make targets, citation or not — the point `report-unchecked-make-citations`'s
   revision of DEC-UMC-007 made explicit. The same lesson was learned on
   R6/S005: key on data loss, not document shape.
6. **A missing coverage floor is not part of this.**
   `openspec_graph/rules_generic.py::_hard_coded_threshold`
   (`rules_generic.py:45`) has no empty guard; with no floor detected it falls
   back to `locator = "the governance policy"` and fires normally (F2,
   reproduced again: `ERROR G003 hard-coded threshold; read it from the
   governance policy instead`). A missing floor leaves nothing unchecked, so
   it contributes nothing to `indeterminate`.
7. **The predicate has a cost in the harness dialect, and it is stated here
   rather than discovered.** `openspec_graph/parse_model.py::Criterion.has_stage`
   (`parse_model.py:55-56`) is a `MAKE_REF` match over the `_Verified by:_`
   line, and `openspec_graph/rules_harness.py` H001 (**ERROR**,
   `rules_harness.py:21-25`, registered at `rules_harness.py:78`) fires on
   every harness criterion whose line names no `make` stage. Harness is also
   the fallback dialect (`parse.py:133`). G010
   (`rules_generic.py:97-113`) has no `GENERIC_STAGES` exemption, so a
   citation of `test` alone triggers it where no make targets are detected;
   `rules.py:103` scopes a waiver to the spec file that carries it; and
   `openspec_graph/scaffold.py::pick_stage` (`scaffold.py:61`) returns
   `"test"` on a Makefile-less target, which `DEC-UMC-008` kept on purpose.
   Measured: a harness spec with its citations removed, or replaced by a
   `tox` command, is `ERROR H001 ×2`, `status=fail`; with a citation of
   `test` only it is `INFO G010` — which this change makes `indeterminate`.
   So "stop citing make stages" is an exit only for the upstream and SpecKit
   dialects; a harness-dialect repository that does not use Make is forced to
   cite a stage, always gets G010, and under this change is `indeterminate`
   on every spec until each spec file carries its own reasoned waiver (or the
   workflow uses `continue-on-error`), and `planlint new` on such a target
   scaffolds a spec that is `indeterminate` until that line is added.
   `DEC-UMC-004` argued that a tox repository writing a generic stage "is not
   lying" and that G011's narrowing "costs nothing in the tox case"; both
   statements are about rule severity and both stay true — G010 is INFO, the
   CLI still exits 0, `rule_types.py:39-47` still documents the exemption.
   What changes is only what the Action's `status` says about a run that
   checked no citation, and the per-spec waiver is the explicit, ledgered
   statement that the citations are shorthand: one line per spec, each
   visible in `planlint waivers`. The cost is accepted, not avoided, and the
   scaffold question is deferred with a reopen trigger below rather than
   folded in.
8. **The deferral was explicit and its condition has been met.**
   `DEC-GA-010`: "changing what the rules do about it is policy, belongs in
   the rules, and gets its own design pass." `report-unchecked-make-citations`
   `tasks.md` Milestone 4: the `indeterminate`-widening item "stays open and
   records that its prerequisite has landed." `docs/peer-review-2026-09.md`
   D3.3: "Change what `status` says. Only now is this a policy question, and
   with 1 and 2 landed it is a much smaller one." `docs/peer-review-2026-10.md`
   D3 is the design pass itself — it names the predicate (an unwaived G010),
   the escape (a reasoned waiver), the unchanged exit code and the two
   fixtures — and its rewritten remainder (`peer-review-2026-10.md:383`,
   `:386`) files this package as R8 and N5. This package is what that row
   describes.

## What Changes

- **`openspec_graph/rule_types.py`** — `Finding` gains `waived: bool = False`
  and `as_dict()` emits `"waived"` as a JSON boolean after `"subject"`.
  `FINDINGS_SCHEMA_VERSION` stays `1`: the constant's own comment
  (`rule_types.py:35-36`) says "additive keys do not bump it", and
  `tests/test_report.py::test_an_unknown_finding_key_is_tolerated` already
  pins that an extra finding key is accepted.
- **`openspec_graph/rules.py`** — `evaluate()` passes `waived=suppressed` and
  `evaluate_tree()` passes `waived=waived_invariant` / `waived=waived_adr` at
  the three `Finding(...)` sites that already downgrade to INFO and prefix
  `[waived] `. Severity, message and prefix are unchanged; the field records
  the fact the prefix displays.
- **`openspec_graph/report.py`** — `FindingRecord` gains `waived`;
  `_parse_finding` reads an optional boolean `waived` defaulting to `False`
  and refuses a present non-boolean with `EnvelopeError`. New module constants
  `UNCHECKED_CITATION_RULE = "G010"`, `CAUSE_NO_SPECS = "no-specs"`,
  `CAUSE_UNCHECKED_CITATIONS = "unchecked-citations"` and a `CAUSES` tuple,
  all in `__all__`. New `indeterminate_cause(envelope) -> str | None`.
  `status_of` returns `indeterminate` also when `blocking == 0` and at least
  one finding has `rule == UNCHECKED_CITATION_RULE` and `waived is False`.
  `to_outputs` gains `indeterminate-cause`, always present, empty when the
  status is not `indeterminate`. `to_step_summary` prints a cause-specific
  paragraph that names the exits honestly per dialect. The module docstring
  (`report.py:6-8`: "never decides policy; `--fail-on` has already been
  applied ... and `blocking` records the result") and `status_of`'s docstring
  are rewritten, because both become false. `discovery_notes`, `parse_card`,
  `to_annotations` and the SARIF pass-through are untouched. Still zero
  intra-package imports.
- **`openspec_graph/cli.py`** — no edit required, stated so nobody looks for
  one: `cmd_validate` serializes through `Finding.as_dict` (`cli.py:481`) and
  `cmd_report` prints every key `to_outputs` returns (`cli.py:781-782`).
- **`.github/actions/planlint/action.yml`** — the `outputs:` block gains
  `indeterminate-cause`; the `status` description (`action.yml:80-86`) and the
  `specs-checked` description ("Zero is what makes a run indeterminate",
  `action.yml:106`) are rewritten for two causes; the gate step's
  `indeterminate)` branch (`action.yml:368-376`) forks on the cause, with the
  existing "no spec was checked, so this run gates nothing" text as the
  default branch and a new message for `unchecked-citations` that names the
  ways out and says in so many words that a harness-dialect repository
  without a Makefile needs a reasoned G010 waiver in each spec. No new input.
- **New `tests/fixtures/action/no-machinery/`** — one change package whose
  spec cites a make stage, no Makefile, a `pyproject.toml` with no coverage
  floor. Labelled `indeterminate`, `validate` exit 0, cause
  `unchecked-citations`. **New `tests/fixtures/action/no-machinery-waived/`**
  — the same, plus a reasoned `specgraph:allow G010` waiver in the spec.
  Labelled `pass`, exit 0. Both rows added to `tests/fixtures/action/README.md`.
- **`tests/test_report.py`** — two rows in `FIXTURE_CONTRACT`; unit tests for
  the predicate, the cause, the output, the summary text, the tolerant parse,
  the refused non-boolean, the rule-id pin, the prefix-free source (an AST
  scan of string constants, docstrings excluded), and the card-free tox
  shape.
- **`tests/test_action_contract.py`** — `EXPECTED_OUTPUTS` gains
  `indeterminate-cause`; two rows in `ACTION_CONTRACT`, each with a gate
  phrase distinct from `empty-tree`'s "gates nothing".
- **`tests/test_findings_envelope.py`** — the `waived` field: set by
  `evaluate` and `evaluate_tree` exactly where they downgrade, `False`
  otherwise, serialized as a boolean, schema version still `1`.
- **`.github/workflows/ci.yml`** — two legs in the `action-contract` matrix
  (`no-machinery`: `outcome: failure`, `status: indeterminate`,
  `exit_code: "0"`; `no-machinery-waived`: `outcome: success`,
  `status: pass`, `exit_code: "0"`).
  `tests/test_ci_hardening.py::test_every_action_fixture_has_a_contract_leg`
  discovers fixtures from disk, so the suite fails without them.
- **`tests/test_decomposition.py`** — verified, not assumed.
  `_EXPECTED_HASHES["graph"]` cannot move (`graph.py:181`, `graph.py:219`
  build their own finding dict literal and never call `as_dict`);
  `["rules"]` cannot move (no registry change); `["validate"]` moves only if
  the `_build_repo` fixture envelope carries a finding, which is expected not
  to be the case and is confirmed by running the test. If it moves, it is
  re-pinned once with the comment-block discipline `DEC-FE-008` set.
- **Docs and contracts that move together — against their current text.**
  The planning record already names this package as *drafted* or *planned*;
  the work is the transition to *shipped*, plus the surfaces that still
  describe the old status. `README.md`: the "related honesty gap" paragraph
  (`README.md:208-213`, which still says the Action reports the gap "rather
  than relabelling the run `indeterminate`") and the `indeterminate` row of
  the four-status table (`README.md:433`);
  `skills/planlint-spec-governance/SKILL.md`: the "four results" paragraph
  (`SKILL.md:184-189`) — statuses unchanged, the two causes added;
  `docs/next-steps.md`: item 1's close ("is the drafted package",
  `next-steps.md:27-29`), the "Widening `indeterminate`" bullet under item 5
  (`next-steps.md:156-160`, "plans ... as"), and the deferral-table row
  (`next-steps.md:229`, "**Planned since:**"), plus a new deferred item for
  the scaffold with its reopen trigger; `docs/peer-review-2026-09.md`: the R8
  row (`peer-review-2026-09.md:349`, "**planned**") and the "G010 is
  effectively unwaivable" limitation note (`peer-review-2026-09.md:369-371`),
  which this narrows rather than removes; `docs/peer-review-2026-10.md`: the
  R8 and N5 rows of its rewritten remainder (`peer-review-2026-10.md:383`,
  `:386`, "drafted"); `docs/differentiation-roadmap.md`: "Status as of 0.2.0"
  item 1's close (`differentiation-roadmap.md:602-605`, "is the drafted
  package"); `CHANGELOG.md` `Unreleased`: no CLI exit code changes; the
  envelope's findings gain a `waived` boolean at schema version 1; an Action
  consumer whose specs cite make stages against a target with no detected
  make targets will newly see `indeterminate` and a red job; the ways out are
  a reasoned G010 waiver in the spec or `continue-on-error` on the step; in
  so many words, a harness-dialect repository without a Makefile needs that
  waiver in each spec, and `planlint new`'s own output on a Makefile-less
  target is `indeterminate` until one is added; the existing "effectively
  unwaivable" sentence is narrowed to the CLI's `--fail-on INFO`.

## Non-Goals

- **No CLI exit-code change.** `validate` exits 0 on this shape at the default
  threshold before and after. INFO never blocks — the severity contract in
  `rules.py`'s docstring stands, and `--fail-on INFO` remains the CLI-side
  escalation. This change is the Action-layer escalation D3.3 described.
- **No fifth status.** R-GA-5's four values are a consumer contract, and a
  workflow branching on `status` must not meet a value it has never seen. The
  cause is an additive output beside `status`, which R-GA-4 permits.
- **No card-shaped predicate.** "No Makefile" or "no make targets detected"
  relabels the tox/npm repository whose specs never cite Make — the case
  `test_g010_is_silent_when_the_spec_cites_no_make_target` protects.
- **No narrowing of the predicate to soften the harness cost, and no
  `GENERIC_STAGES` exemption added to G010.** Exempting `test` from G010
  would reopen the exact vacuous pass G010 was written to report
  (`DEC-UMC-004` kept the exemption for G004 only), and a predicate that
  skipped harness specs would make the status depend on dialect rather than
  on what went unchecked. The cost is paid with a one-line reasoned waiver
  per spec, which is the mechanism this project already has for "this
  citation is shorthand".
- **No change to what `planlint new` scaffolds — deferred, with a reopen
  trigger.** `scaffold.pick_stage()` keeps returning `test` on a
  Makefile-less target (`DEC-UMC-008`), so the scaffold's own output on such
  a target is `indeterminate` under this change until the author adds a
  reasoned G010 waiver. Having the scaffold emit that waiver (or no stage)
  changes `new`'s output and belongs in its own package. Reopen when the
  first harness-dialect adopter who does not use Make hits it; recorded in
  `docs/next-steps.md`'s deferral table with that trigger.
- **No `allow-indeterminate` input, and no new input of any kind.**
  `DEC-GA-005` stands: a knob whose only purpose is to make a false green
  available by configuration. The waiver and `continue-on-error` remain the
  only escapes, and both are visible in the tree or the workflow.
- **No change to G010's id, severity, message or one-finding-per-spec shape,
  and none to G011, G004 or H001.** The rule is the honest signal; this
  change decides what the Action does about it. `RULES`,
  `tests/baseline_rules.json` and the generated rule catalog do not move.
- **No change to `discovery-warnings` or `discovery_notes()`.**
  `DEC-UMC-007` — and its revision — still hold: the function also covers the
  coverage-floor case, which has no rule id, and it fires on citation-free
  targets where G010 does not. Two derivations stay two derivations.
- **No treatment of a missing coverage floor.** F2: G003 does not fail open,
  so a missing floor leaves nothing unchecked and has no bearing on status.
- **No `FINDINGS_SCHEMA_VERSION` bump.** `waived` is additive, defaults are
  defined on read, and an envelope from an older build still projects.
- **No change to how waived findings are rendered in text output.** The
  `[waived] ` prefix is the display contract several suites pin; the new field
  is the fact behind it, not a replacement for it.
- **No change to the SARIF projection.** `sarif.to_sarif` reads named keys,
  so `waived` does not reach SARIF and `R-GA-13`'s byte-identity holds.

## Affected Capabilities

- `indeterminate-status`
