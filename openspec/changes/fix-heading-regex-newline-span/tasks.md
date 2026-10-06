# Milestones

## Milestone 1 — Reproduce, and pin the defect before touching a regex

- Re-run the CLI reproduction exactly as the spec's Problem Statement
  records it (a bare `##` line, a prose `Requirement:` line, one real
  level-3 requirement with two scenarios) and confirm `1 error · 2 warn`,
  exit 1 under `--fail-on INFO`; delete the bare line and confirm
  `0 error · 0 warn · 0 info`, exit 0. Then re-run the adversary's
  split-token prototypes from the Problem Statement through `parse_upstream`
  and `DELTA_HEADER` and confirm each result as recorded. If any number or
  result differs, stop and correct the spec before anything else.
- `tests/test_heading_grammar.py` (new, flat — never `tests/<subdir>/`,
  per `tests/AGENTS.md`):
  - `test_bare_hash_line_matches_no_heading_regex`, parametrised over the
    six regexes with a hashes-only line (plain, two trailing spaces, a
    trailing tab) followed by that regex's keyword-shaped prose line;
    asserts no match (AC-HNS-1). The two-trailing-spaces case is the one
    that defeats a gap-only fix for `SECTION`/`SUBSECTION` (DEC-HNS-012).
  - `test_same_line_heading_still_matches`, parametrised over the six with
    one space, several spaces and a tab after the hashes, each separator the
    regex accepts, `REQ 12`-style numbering and mixed case; asserts the match
    and its captured groups (AC-HNS-2). Passes before and after the fix, by
    design.
  - `test_heading_regexes_share_the_horizontal_whitespace_class`: collect
    every `re.Pattern` attribute of `openspec_graph.parse_semantics`, select
    those with `re.match(r"\^\(?#", pattern.pattern)`, assert the selection
    is exactly `{SECTION, SUBSECTION, DELTA_HEADER, REQUIREMENT, SCENARIO,
    USER_STORY_HEADING}`, and assert `"\\s" not in pattern.pattern` for each
    (AC-HNS-13). Case-sensitive on purpose: `\S` in `[^\S\n]` and `(?=\S)`
    is not `\s`.
  - `test_empty_titled_requirement_does_not_swallow_the_next_heading`:
    `parse_upstream` over an empty-titled level-3 requirement heading, a
    blank line, and a real level-3 requirement heading returns two
    requirements, the first with `text == ""`; the scenario analogue returns
    two criteria (AC-HNS-18).
  - `test_empty_titled_headings_are_reported_not_silent`: U004 on the
    empty-titled requirement whose body has no modal, U002 on one with no
    scenario, U003 on the empty-titled scenario whose block has no WHEN or
    THEN (AC-HNS-21).
  - `test_split_delta_header_is_not_a_header_and_u001_fires`: the verb on
    one line and `Requirements` on the next yields no `DELTA_HEADER` match,
    and `findings_for(..., "upstream")` over a delta whose only header is
    split that way includes `U001` (AC-HNS-19).
  - `test_split_tokens_never_assemble_into_a_heading`: separator on the
    next line for `REQUIREMENT` and `SCENARIO`, `REQ` number on the next
    line, `User Story` number on the next line — none matches (AC-HNS-20).
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
    title, `##Title` with no whitespace, a hash run outside each regex's
    range, and every bare-hash variant match none of the six; the only shape
    that newly matches is the keyworded empty-titled heading (AC-HNS-16).
- `tests/test_properties.py`: add two kinds to `_upstream_spec`'s
  `sampled_from` list (DEC-HNS-007). `bare` appends a line of two to five
  hashes plus an optional trailing run of spaces or a tab, then a line
  `f"{keyword}{separator} {title}"` with no hashes, drawn from the same
  keyword and separator sets the `req` kind uses, and leaves `declared`
  unchanged. `empty_req` appends `f"{'#' * depth} {keyword}{separator}"`
  with no title and increments `declared` by one, with `depth` drawn from
  `st.integers(2, 4)` — the `req` kind's range, never the `bare` kind's
  2–5, since a five-hash keyword heading is outside the requirement
  regex's hash range under the fixed grammar too. Do not add a property
  function and do not touch `PROPERTY_SETTINGS` —
  `test_property_settings_are_derandomized_and_nothing_is_xfailed` counts
  both. The property exercises `REQUIREMENT` only; the other five regexes
  are covered by the deterministic tests above.
- Run the new module and the property before the regex change lands: every
  regex-level negative, the split-token tests, the three dialect-level tests
  and the requirement-count property must fail; record the property's
  shrunk counterexample in this file. The same-line preservation test and
  the controls cited from existing modules pass before and after.
  `tests/AGENTS.md`: a test added here should fail before the change it
  covers — check that, don't assume it.

- **Gate:** `make test` — red on exactly the new negative, split-token and
  dialect-level tests plus the extended property, green everywhere else.
  That failure set is the reproduction.

## Milestone 2 — Close the hole, once, for the family

- `openspec_graph/parse_semantics.py`: add `_HWS = r"[^\S\n]"` above
  `SECTION` with a comment that (a) `re.MULTILINE` makes `^`/`$` line-aware
  but `\s` still contains `\n`, so every `\s+`/`\s*` in a heading pattern
  may consume a line break — the gap after the hashes was only the first
  place it was noticed; (b) points at `_bullet_decl`'s docstring for the
  "two copies, one fixed" history this is the fourth instance of; (c) names
  DEC-HNS-001, DEC-HNS-002 and DEC-HNS-004.
- Same file: in `SECTION`, `SUBSECTION`, `DELTA_HEADER`, `REQUIREMENT`,
  `SCENARIO` and `USER_STORY_HEADING`, replace **every** `\s` with `{_HWS}`
  — the gap after the hashes, both sides of the separator, inside
  `REQ\s*\d+`, after `User Story`, the trailing `\s*$` (R-HNS-1). Use an
  `rf`-string (mind that `#{2,4}` and `#{3,5}` then need doubled braces) or
  plain concatenation; the structural test reads the compiled pattern's
  source either way.
- Same file: in `REQUIREMENT` and `SCENARIO`, the title capture `(.+?)`
  becomes `(.*?)` so an empty title is a recognised-but-empty entry
  (R-HNS-11, DEC-HNS-004). In `SECTION` and `SUBSECTION`, insert `(?=\S)`
  immediately before `(.+?)` so a title must begin at a non-whitespace
  character (R-HNS-2, DEC-HNS-012). Touch nothing else — not the hash
  ranges, not the keyword alternations, not the separator classes, not the
  number or order of capture groups, not the flags (R-HNS-3).
  `GWT_SCENARIO` is not in the list (C-HNS-2).
- Same file: extend the module docstring's heading-grammar sentence to say
  every whitespace span in a heading pattern is horizontal-only and an
  empty-titled keyword heading is a recognised-but-empty entry, so the next
  reader does not "fix" either back.
- Re-run the Milestone 1 reproduction with the bare line still present:
  `0 error · 0 warn · 0 info`, exit 0. Re-run the split-token prototypes:
  two requirements, two scenarios, no delta header. Record both beside the
  Milestone 1 results.

- **Gate:** `make test`

## Milestone 3 — Prove nothing else moved

- `make matcher-accuracy`: the per-pattern G002/U004 table is identical to
  the before-figures below, measured by adversarial review at `6666444`
  with exit 0 and every floor met; no `*_pct` key in `pyproject.toml` is
  edited and no row is added under `tests/fixtures/phrasing/` (AC-HNS-12,
  DEC-HNS-008). Paste the after-table beside it in the PR.

  | Matcher | Precision | Recall | TP / FP / FN / TN | n |
  |---|---|---|---|---|
  | G002 (`Criterion.is_negative`) | 0.919 | 0.983 | 57 / 5 / 1 / 56 | 119 |
  | U004 (`Requirement.is_normative`) | 0.938 | 1.000 | 15 / 1 / 0 / 17 | 33 |

- `tests/test_decomposition.py`: `_EXPECTED_HASHES["validate"]`,
  `["graph"]` and `["rules"]` all still match. Do not re-pin any of them. If
  one moves, stop: the canonical fixture has no bare heading line and no
  empty-titled keyword heading, so a moved hash means the change is not what
  the spec says (DEC-HNS-010).
- `tests/baseline_rules.json`: `planlint rules --json` diffs empty against
  it; no regeneration and no `make skill-catalog` run (C-HNS-3).
- Confirm the fixture and corpus trees still carry neither shape —
  `grep -rnE '^#{2,5}[[:space:]]*$' tests/fixtures tests/corpus` is empty,
  and so is a grep for a `Requirement`/`REQ n`/`Scenario` heading whose
  separator ends the line — so hash stability is explained rather than
  lucky.
- `make validate` against this repository: every package present in the
  tree when this lands, this one included, at `0 error · 0 warn · 0 info`,
  exit 0 (AC-HNS-11). Do not write the spec count into any file; two
  packages landed beside this one during review and a third follows.

- **Gate:** `make ci`

## Milestone 4 — Record it, then let the gates read the record

- `CHANGELOG.md`, under `## [Unreleased]` / `### Fixed`, one entry in the
  house style of the `FR_DECL` entry already there: what was wrong (every
  `\s` in the six heading regexes spans a newline under `re.MULTILINE`), how
  it was reproduced (one bare `##` line, one false U002 ERROR, exit 1;
  deleted, exit 0; and an empty-titled `Requirement:` heading that swallowed
  the next real one), what the fix is (`[^\S\n]` for every span via one
  shared class, `(.*?)` for the keyworded titles, `(?=\S)` for the section
  titles), and what it costs — nothing a passing spec relies on: a line of
  bare hashes was never a declaration in any dialect this tool reads, and an
  empty-titled keyword heading was only ever counted by stealing the next
  line.
- `docs/eval-corpus-plan.md`, lines 324-331: the paragraph already records
  the prediction, the CLI reproduction and "the fix is planned as
  `fix-heading-regex-newline-span`, across all six heading regexes"
  (`fa0a779`). Change "planned as" to "fixed in" and nothing else
  (R-HNS-10, DEC-HNS-011).
- Do not edit `docs/peer-review-2026-10.md` (C-HNS-6). It exists, cites
  this package at lines 21, 355 and 366, and is the document that reports on
  the change, not a file of it.
- Replace each stage-only `_Verified by:_` in the spec with the
  `pytest -k <selector>` form naming the test that now exists;
  `tests/test_spec_test_citations.py` fails on a selector that resolves to
  nothing, so this step is after the tests land, never before. Leave
  `**Status:** DRAFT`; promotion is a human decision after review.

- **Gate:** `make pre-pr`
