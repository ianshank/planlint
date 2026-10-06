# Milestones

## Milestone 1 — Reproduce, and pin the defect before touching a regex

- Re-run the CLI reproduction at `6666444` exactly as the spec's Problem
  Statement records it (a bare `##` line, a prose `Requirement:` line, one
  real level-3 requirement with two scenarios) and confirm `1 error · 2
  warn`, exit 1 under `--fail-on INFO`; delete the bare line and confirm
  `0 error · 0 warn · 0 info`, exit 0. If either number differs, stop and
  correct the spec before anything else.
- `tests/test_heading_grammar.py` (new, flat — never `tests/<subdir>/`,
  per `tests/AGENTS.md`):
  - `test_bare_hash_line_matches_no_heading_regex`, parametrised over the
    six regexes with a hashes-only line (plain, trailing spaces, trailing
    tab) followed by that regex's keyword-shaped prose line; asserts no
    match (AC-HNS-1).
  - `test_same_line_heading_still_matches`, parametrised over the six with
    one space, several spaces and a tab after the hashes, each separator the
    regex accepts, `REQ 12`-style numbering and mixed case; asserts the match
    and its captured groups (AC-HNS-2).
  - `test_heading_regexes_share_the_horizontal_whitespace_class`: walk the
    module's compiled `re.Pattern` attributes, select those whose source
    begins with `^#`, and assert none places `\s` directly after its hash
    group (AC-HNS-13).
  - `test_bare_heading_before_prose_requirement_validates_clean`: the CLI
    reproduction inverted — derive the body from `GOOD_UPSTREAM` by
    inserting the bare line and the prose line after the delta header, so
    the control is the fixture already known clean, then
    `findings_for(..., "upstream")`: exactly one requirement, and none of
    `U002`, `U004`, `U005` in the rule ids (AC-HNS-3).
  - `test_bare_heading_does_not_create_a_phantom_speckit_section`:
    `speckit_section_span` over a document with a bare hash line before a
    prose line reading `Success Criteria` returns `(0, "")`, and
    `parse_speckit` extracts no criterion from the prose below (AC-HNS-6).
  - `test_bare_heading_does_not_satisfy_h006_required_sections`: a harness
    body with its real Problem Statement heading replaced by a bare hash
    line plus a prose line reading `Problem Statement` still yields
    `missing required section: Problem Statement` (AC-HNS-7).
  - `test_gwt_scenario_keeps_dotall_and_parses_a_three_line_scenario`
    (AC-HNS-14).
  - `test_heading_fix_adds_no_new_heading_shapes`: a setext-underlined
    title, `##Title` with no whitespace, and a hash run outside each regex's
    range match none of the six (AC-HNS-16).
- `tests/test_properties.py`: add a `bare` kind to `_upstream_spec`'s
  `sampled_from` list. It appends a line of two to five hashes plus an
  optional trailing run of spaces or a tab, then a line
  `f"{keyword}{separator} {title}"` with no hashes, drawn from the same
  keyword and separator sets the `req` kind uses, and leaves `declared`
  unchanged (DEC-HNS-007). Do not add a property function and do not touch
  `PROPERTY_SETTINGS` —
  `test_property_settings_are_derandomized_and_nothing_is_xfailed` counts
  both.
- Run the new module and the property at `6666444`: every regex-level
  negative, the three dialect-level tests and the requirement-count
  property must fail; record the property's shrunk counterexample in this
  file. `tests/AGENTS.md`: a test added here should fail before the change
  it covers — check that, don't assume it.

- **Gate:** `make test` — red on exactly the new tests and the extended
  property, green everywhere else. That failure set is the reproduction.

## Milestone 2 — Close the hole, once, for the family

- `openspec_graph/parse_semantics.py`: add `_HWS = r"[^\S\n]"` above
  `SECTION` with a comment that (a) `re.MULTILINE` makes `^`/`$` line-aware
  but `\s` still contains `\n`, so `^##\s+X` may consume the line break
  between the hashes and `X`; (b) points at `_bullet_decl`'s docstring for
  the "two copies, one fixed" history this is the fourth instance of; (c)
  names DEC-HNS-001 and DEC-HNS-002.
- Same file: in `SECTION`, `SUBSECTION`, `DELTA_HEADER`, `REQUIREMENT`,
  `SCENARIO` and `USER_STORY_HEADING`, replace the `\s+` that directly
  follows the hash group with `{_HWS}+` (an `rf`-string — mind that `#{2,4}`
  and `#{3,5}` then need doubled braces — or plain concatenation; the
  structural test reads the compiled pattern's source either way). Touch
  nothing else in any of the six — not the hash ranges, not the keyword
  alternations, not the separator classes, not the `(.+?)\s*$` tails, not
  the flags (R-HNS-3). `GWT_SCENARIO` is not in the list (C-HNS-2).
- Same file: extend the module docstring's heading-grammar sentence to say
  the gap after the hashes is horizontal-only, so the next reader does not
  "fix" it back.
- Re-run the Milestone 1 reproduction with the bare line still present:
  `0 error · 0 warn · 0 info`, exit 0. Record it beside the Milestone 1
  numbers.

- **Gate:** `make test`

## Milestone 3 — Prove nothing else moved

- `make matcher-accuracy`: the per-pattern G002/U004 table is identical to
  the run taken before Milestone 2; no `*_pct` key in `pyproject.toml` is
  edited and no row is added under `tests/fixtures/phrasing/` (AC-HNS-12,
  DEC-HNS-008). Paste the two tables side by side in the PR.
- `tests/test_decomposition.py`: `_EXPECTED_HASHES["validate"]`,
  `["graph"]` and `["rules"]` all still match. Do not re-pin any of them. If
  one moves, stop: the canonical fixture has no bare heading line, so a
  moved hash means the change is not what the spec says (DEC-HNS-010).
- `tests/baseline_rules.json`: `planlint rules --json` diffs empty against
  it; no regeneration and no `make skill-catalog` run (C-HNS-3).
- Confirm the fixture and corpus trees still carry no bare heading line —
  `grep -rnE '^#{2,5}[[:space:]]*$' tests/fixtures tests/corpus` is empty —
  so hash stability is explained rather than lucky.
- `make validate` against this repository: every package clean, this one
  included — 42 spec(s) checked (the 41 at `6666444` plus this package's
  own), `0 error · 0 warn · 0 info`, exit 0 (AC-HNS-11).

- **Gate:** `make ci`

## Milestone 4 — Record it, then let the gates read the record

- `CHANGELOG.md`, under `## [Unreleased]` / `### Fixed`, one entry in the
  house style of the `FR_DECL` entry already there: what was wrong (`\s+`
  after heading hashes spans a newline under `re.MULTILINE`), how it was
  reproduced (one bare `##` line, one false U002 ERROR, exit 1; deleted,
  exit 0), what the fix is (`[^\S\n]+` in all six heading regexes via one
  shared class), and what it costs — nothing, since a line of bare hashes is
  never a declaration in any dialect this tool reads.
- `docs/eval-corpus-plan.md`, Appendix C, the paragraph at lines 324-328:
  append one sentence — reproduced through the CLI and fixed in
  `fix-heading-regex-newline-span`. Leave the prediction and its "low
  priority" rating as written (DEC-HNS-011).
- Do not create or edit `docs/peer-review-2026-10.md` (C-HNS-6). It is the
  document that cites this package, not a file of it.
- Replace each stage-only `_Verified by:_` in the spec with the
  `pytest -k <selector>` form naming the test that now exists;
  `tests/test_spec_test_citations.py` fails on a selector that resolves to
  nothing, so this step is after the tests land, never before. Leave
  `**Status:** DRAFT`; promotion is a human decision after review.

- **Gate:** `make pre-pr`
