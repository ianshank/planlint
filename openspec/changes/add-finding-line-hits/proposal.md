# Change: Attach Honest Line Hits to Findings, and Name `--change` / `--dialect` on the Action

## Why

Every finding the CLI emits carries `Finding.line == 0`. SARIF and GitHub
annotations already know what to do with a real line — they emit
`region.startLine` / `line=` only when the value is `>= 1`, and they
deliberately never clamp `0` to `1` — but no rule ever supplies one. The
composite Action has the same class of hole one layer up: `validate` already
accepts `--change` and `--dialect`, and the Action does not pass them.

**Evidence:**

1. **`evaluate()` never passes `line=`.** `openspec_graph/rules.py:85-93`
   constructs each `Finding` from `rule.check`'s yielded strings with
   `rule=`, `severity=`, `message=`, and `path=spec.path` — and no
   `line=` argument. `Finding.line` therefore stays at its dataclass
   default of `0` (`openspec_graph/rule_types.py:46`). `Rule.check` is
   typed `Callable[[ParsedSpec, StackProfile], Iterable[str]]`
   (`rule_types.py:99`), so a check has no channel that could carry a
   locus even if it had one.
2. **The locus is already sitting next to the check.** G007's message
   embeds `waiver.line` (`openspec_graph/rules_generic.py:86-92`:
   `"waiver of {waiver.rule} at line {waiver.line} has no reason"`) while
   the `Finding` it becomes still has `line == 0`. `Criterion.line` is
   already 1-based for harness ACs, upstream scenarios, and SpecKit GWT
   (`parse_model.py:35`); `Waiver.line` is already 1-based
   (`parse_semantics.py:574`). `Requirement` has no `line` field at all
   (`parse_model.py:64-69`), so H003/U002/U004/S003 have nothing to copy.
3. **The one line the harness parser *does* set is a known false locus.**
   `openspec_graph/parse_harness.py:55` sets `Criterion.line` with
   `line_of(text, text.find(block[:60]))`. `str.find` returns the first
   occurrence of that prefix in the whole document, so two ACs that share
   a leading sixty characters — or an AC whose leading text also appears
   in the Problem Statement — get the earlier line, not the bullet.
4. **The projections already refuse to invent a line.**
   `openspec_graph/sarif.py:92-99` omits `region` when `line < 1`, with a
   comment that clamping would annotate the first line of a real file.
   `openspec_graph/report.py:424-430` omits the workflow-command `line=`
   property on the same test. Both behaviours are pinned:
   `tests/test_sarif.py::test_a_line_of_zero_emits_no_region`,
   `tests/test_report.py::test_a_line_of_zero_emits_no_line_property`.
   `docs/next-steps.md` item 2 records this as the deferred check-contract
   change; this package is that change.
5. **The Action scan step only passes `--target` and `--fail-on`.**
   `.github/actions/planlint/action.yml:222-224` runs
   `planlint --target "$INPUT_TARGET" validate --fail-on "$INPUT_FAIL_ON"
   --format json`. The CLI already has the flags
   (`openspec_graph/cli.py:879-880`, `p_val.add_argument("--change")` and
   `"--dialect"`). `openspec/changes/add-github-action-contract/specs/github-action-contract/spec.md`'s
   `R-GA-3` requires the Action's inputs to be *exactly* `target`,
   `version`, `fail-on`, `python-version`, `upload-artifact`, and
   `artifact-name`. `docs/next-steps.md` item 3 is the recorded reopen
   trigger for named `--change` / `--dialect` inputs, with no raw
   `extra-args` and with `--require-witness` left off the Action.

**This supersedes `R-GA-3` in part, deliberately.** The closed list of six
input names becomes those six plus `change` and `dialect`. The rest of
`R-GA-3` stands: no raw argument pass-through, no input whose name contains
`token`. `DEC-GA-017` in this package records the split.

**This does not bump `FINDINGS_SCHEMA_VERSION`.** `DEC-FE-010` started the
constant at `1` and said additive keys do not bump it. `Finding.as_dict()`
already emits a `line` key (`rule_types.py:81`); filling in a 1-based value
where a check has a real locus is a value change of an existing field, not
a shape change. The constant stays `1`. The package version stays `0.2.0`.

## What Changes

- **`openspec_graph/rule_types.py`** — a frozen dataclass
  `CheckHit(message: str, line: int = 0)` beside `Finding`, sharing
  `Finding.line`'s default. A type alias `CheckResult = str | CheckHit` and
  a helper `as_check_hit(item: CheckResult) -> CheckHit` (a bare `str`
  becomes `CheckHit(message=item, line=0)`; a `CheckHit` is returned
  unchanged). `Rule.check` becomes
  `Callable[[ParsedSpec, StackProfile], Iterable[CheckResult]]`. Both new
  names join `__all__`.
- **`openspec_graph/rules.py`** — re-exports `CheckHit`, `CheckResult`, and
  `as_check_hit` from the facade `__all__` (R-DG-1), so `cli.py` and tests
  never need a direct `rule_types` import for them. `evaluate()` coerces
  every yielded item through `as_check_hit` and copies `hit.line` onto the
  `Finding` only when it is `>= 1`; otherwise it stores `0`. It never
  clamps `0` (or a negative) to `1`. `evaluate_tree()` keeps omitting
  `line=` for G006/G009. A module logger `logging.getLogger("planlint.rules")`
  — a child of `planlint`, no extra handler — records at DEBUG the rule id
  and the attached line or `unset`. Finding message bodies are not logged
  at INFO (or at the default WARNING). Default WARNING stays quiet.
- **`openspec_graph/parse_model.py`** — `Requirement` gains `line: int = 0`
  as its last field, matching `Criterion.line`'s default and the
  append-at-the-end discipline `ParsedSpec` already documents for
  positional safety.
- **`openspec_graph/parse_semantics.py`** — new `section_span(text, name)
  -> tuple[int, str]` returning `(body_start_offset, body)`.
  `section_body` becomes `return section_span(...)[1]`, so every existing
  caller keeps receiving a `str`.
- **`openspec_graph/parse_harness.py`** — `Requirement.line` via
  `line_of(full_text, span_origin + match.start())`. Harness
  `Criterion.line` stops using `text.find(block[:60])` and uses the
  Acceptance Criteria span origin plus `match.start()` instead.
- **`openspec_graph/parse_upstream.py`** / **`parse_speckit.py`** —
  `Requirement.line` via `line_of(full_text, absolute_match_start)`.
  SpecKit FR/SC bullets use the nested-span origin plus `match.start()`,
  not `text.find` of a bullet prefix. SpecKit GWT already uses
  `story.start() + scen.start()` and keeps that.
- **`openspec_graph/rules_generic.py`** — G007 yields `CheckHit` with
  `waiver.line`. Message strings unchanged.
- **`openspec_graph/rules_harness.py`** — H001, H002, H004 yield
  `CheckHit` with `crit.line`. H003 looks up `Requirement.line` by ident
  from `spec.orphan_requirements` (the property stays a tuple of idents).
- **`openspec_graph/rules_upstream.py`** — U003 uses `crit.line`; U002 and
  U004 use `req.line`.
- **`openspec_graph/rules_speckit.py`** — S001 uses
  `NEEDS_CLARIFICATION.finditer` + `line_of` (waiver-stripped text already
  preserves length). S002 both halves use the duplicate item's line. S003
  uses `req.line`. S004 uses `crit.line`.
- **`openspec_graph/rules_witness.py`** — W001 and W002 yield `CheckHit`
  with `crit.line`.
- **Leave `line=0` (honest absence, still a bare `str`):** G001, G002,
  G003, G004, G005, G008, G006, G009, H005, H006, U001, U005. No
  first-match search is added for G003–G005/G008 citation strings.
- **`.github/actions/planlint/action.yml`** — inputs `change` and
  `dialect`, both `required: false`, default `""`. The scan step grows
  `INPUT_CHANGE` / `INPUT_DIALECT`, builds the `validate` argv as an
  array, and appends `--change` / `--dialect` only when the value is
  non-empty. Empty does not pass `--dialect auto`. No `extra-args`. No
  `--require-witness`.
- **`tests/test_action_contract.py`** — `EXPECTED_INPUTS` and
  `ActionRun` defaults include `change` and `dialect` (empty). New tests
  named in this package's acceptance criteria.
- **New tests** named in the two specs (CheckHit coercion, evaluate line
  copy and non-clamp, logger quietness, parser loci, migrated-rule
  samples, SARIF round-trip, Action flag construction). Existing
  `test_a_line_of_zero_emits_no_region` and
  `test_a_line_of_zero_emits_no_line_property` stay and pin the omit
  path.
- **`CHANGELOG.md`** / **`docs/next-steps.md`** — record the line
  plumbing and the two Action inputs without a version bump; mark items
  2–3 of the post-tag list as shipped by this change. Templates need not
  start passing the new inputs.

## Non-Goals

- **No `FINDINGS_SCHEMA_VERSION` bump.** The `line` key already exists;
  filling it is not a shape change (`DEC-FE-010`).
- **No package version bump.** `0.2.0` is untagged; this rides in that
  release.
- **No `extra-args` input**, and no `--require-witness` on the Action.
  The witness store is gitignored; a fresh CI checkout always fails W001
  closed. Each flag becomes a named input only when it has a tested
  contract, which `--require-witness` does not on this wrapper.
- **No vacuous-pass policy change**, and no extra `validate` stderr notes
  about missing machinery. That is `docs/next-steps.md` item 1 and stays
  there.
- **No `0→1` clamp** in `evaluate()`, in SARIF, or in GitHub annotations.
  A missing locus stays omitted.
- **No rule-pack plugins**, no CP-8 agent-threat corpus, no Marketplace
  listing, no floating `v1` tag.
- **No first-match enrichment** of G003/G004/G005/G008 citation strings.
  A guessed line on the wrong copy of a threshold or make-target mention
  is a worse annotation than none.
- **No message-string edits** on migrated rules. G007 still says
  `at line {waiver.line}` in the message; the `Finding` now carries the
  same number in `line`.

## Affected Capabilities

- `findings-envelope`
- `github-action-contract`
