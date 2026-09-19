# Change: Lint an Empty SpecKit Requirements Section (SER)

> **Status: proposed.** Reproduced at `c60f894`. Deferred once already, on
> purpose, as `docs/next-steps.md` item 4b / R6 and `docs/peer-review-2026-09.md`
> F4 — "needs the same spec-drafter → spec-adversary design pass the rest of
> this rule family got, not a rushed addition." This package is that pass.

## Why

`parse_speckit()` scopes its functional-requirement scan to a level-3
`Functional Requirements` heading nested inside the level-2 `Requirements`
span. That scoping is correct and was added deliberately: R-SK-30/AC-SK-49
closed a real over-matching bug where an `FR-`-shaped bullet under an
unrelated level-3 heading — or under no such heading at all — was picked up as
a declared requirement. Nothing here undoes it.

The flip side is a defect of equal size in the other direction. A hand-edited
spec that writes the heading one level up, as a level-2 `Functional
Requirements` heading, matches neither lookup, extracts zero requirements, and
says nothing about it.

**Evidence:** `openspec_graph/parse_speckit.py:35-36` is the whole mechanism —

```python
req_origin, req_section = speckit_section_span(text, "Requirements")
sub_origin, req_body = speckit_subsection_span(req_section, "Functional Requirements")
```

`speckit_section_span` matches an exact (annotation-stripped) level-2 title, so
`## Functional Requirements` never resolves as `Requirements`; and
`speckit_subsection_span` returns `(0, "")` when the named level-3 heading is
absent from the span it was handed (`parse_semantics.py:508-517`). `FR_DECL`
then iterates an empty string. Reproduced at `c60f894`, same file, one heading
level changed:

| Heading level | Graph nodes |
|---|---|
| level-3 `Functional Requirements` (canonical) | `FR-001`, `FR-002`, `SC-001` |
| `## Functional Requirements` (hand-edited) | `SC-001` |

Both runs report `1 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`, and
`broken_links: 0`. Two requirements leave the dependency graph and every gate
agrees nothing is wrong.

**This is silent data loss, not a missing diagnostic.** G001 cannot catch it:
`rules_generic.py:20-22` returns early when `spec.criteria` is non-empty, and
the surviving `SC-001` keeps it non-empty, so the spec is never
requirement-less in G001's sense. S002 (duplicate ids) and S003 (non-normative
requirements) both iterate `spec.requirements` and have nothing to iterate.
Every rule that could have noticed is structurally blind to it. A tool whose
stated purpose is failing a build when a spec cites machinery a repository does
not have should not itself drop half a document and print PASS.

**Why it was deferred, and what changed.** Item 4b's stated reason was
false-positive risk against a legitimately FR-less, user-story-only draft spec,
and that caution is right — an unconditional "speckit spec with zero
requirements" check would fire on every early draft in the dialect's own
intended workflow. The discrimination that makes the rule safe is narrower than
that check: **a `Requirements`-shaped section that exists and yields zero
FR bullets is not the same state as no such section at all, and only the former
warrants a finding.** A draft that has not written its requirements section yet
has nothing to disagree with; a document that opened one and got nothing out of
it has made a claim the parser could not honour.

## What Changes

- **`openspec_graph/parse_semantics.py`** — the two heading names
  `parse_speckit.py` looks up today as bare string literals become shared
  module constants, `SPECKIT_REQUIREMENTS_HEADING` and
  `SPECKIT_FUNCTIONAL_REQUIREMENTS_HEADING`, sitting beside the existing
  `SPECKIT_SUCCESS_CRITERIA_HEADING` and carrying the same rationale that
  constant already records in its own comment (`parse_semantics.py:51-54`):
  "shared … so the two can't independently drift." A new
  `speckit_requirements_heading(text) -> tuple[str, int] | None` returns the
  annotation-stripped title and 1-based line of the first level-2 **or**
  level-3 heading whose normalized title equals either constant, reusing
  `speckit_section_span`'s own `_TRAILING_ANNOTATION` normalization rather
  than re-implementing it a second time.
- **`openspec_graph/parse_speckit.py`** — its two lookups
  (`"Requirements"`, `"Functional Requirements"`, lines 35-36) are replaced by
  the new constants. No behavioural change: the scoping, the levels, and the
  extraction are untouched, and the parse of every existing fixture stays
  byte-identical.
- **`openspec_graph/rules_speckit.py`** — new rule **S005**, WARN,
  `dialects=("speckit",)`, appended after S004 in `SPECKIT_RULES`:

  | ID | Severity | Dialect | Check |
  |---|---|---|---|
  | S005 | WARN | speckit | A `Requirements`-shaped section exists but no `FR-` bullet was extracted from it |

  The check is two structural reads and nothing else: `spec.requirements` is
  empty, **and** `speckit_requirements_heading(strip_waiver_comments(spec.raw))`
  found a heading. It emits one `CheckHit` per spec, located on the heading's
  own line.
- **`tests/test_rules_speckit.py`** — one fixture per firing shape
  (wrong-level heading; level-2 `Requirements` with no level-3 subheading;
  a section holding only prose; a section holding only non-`FR-`-shaped
  bullets) and one per non-firing shape (no `Requirements`-shaped heading at
  all; the canonical `good_speckit.md`; a non-speckit dialect).
- **`tests/test_parse_speckit.py`** — a check that the parser and S005 read the
  same heading vocabulary, so the rule cannot go blind if the parser's lookup
  names ever move.
- **Registry and doc sync**, per `.claude/skills/planlint-add-rule/SKILL.md` —
  `tests/baseline_rules.json` regenerated, `make skill-catalog` re-run,
  README's rules table, `docs/architecture/c4.md`'s rule count *and* its
  per-family range claims (module map and caption),
  `docs/agents-skills-harness.md`, `docs/next-steps.md` (count, plus item 4b/R6
  struck through), `docs/differentiation-roadmap.md`, and `rules.py`'s own
  module docstring all move from `S001-S004` / 26 rules to `S001-S005` / 27.
  `tests/test_decomposition.py::_EXPECTED_HASHES["rules"]` is re-pinned;
  `["validate"]` and `["graph"]` stay unchanged, for the reason that comment
  already records — the canonical fixture has no `specs/` directory, so no
  speckit rule fires against it.

## Non-Goals

- **No change to `parse_speckit()`'s scoping.** Teaching the parser to accept a
  level-2 `Functional Requirements` heading would re-open exactly the
  over-matching bug R-SK-30/AC-SK-49 closed, and would do it by guessing at an
  author's intent. A diagnostic that names the slip is strictly better than a
  parser that silently repairs it.
- **No promotion to ERROR, now or as a follow-up in this package.** WARN is the
  compatibility guarantee: a consumer running the default `--fail-on ERROR`
  sees no exit-code change from this rule, ever. Same bar S004 is held to
  (DEC-SK-019), for the same reason — this discrimination is newly designed and
  has not been measured against a collected corpus of real SpecKit specs.
- **No symmetric rule for an empty `Success Criteria` section.** Item 4b names
  both sections, and the sibling defect is real, but the discrimination
  argument above was worked out for the requirements section specifically. A
  `Success Criteria` section has a second source of criteria that
  `Functional Requirements` has no analogue of — User Story acceptance
  scenarios synthesize `US<n>-AS<m>` criteria independently — so "the section
  exists and yielded nothing" is a materially different predicate there. It
  gets its own package and its own re-derivation, not an assumed mirror of
  this one.
- **No configuration knob** to tune, disable, or re-severity the rule. Waivers
  (`specgraph:allow S005`) are the existing, tested mechanism for a spec that
  genuinely wants this silenced, and adding a second one would fork the answer
  to "why didn't this fire?"
- **Nothing about Makefile discovery filenames, G004/`GENERIC_STAGES`, or the
  U004 modal-verb design question.** Each is tracked separately and each would
  change a rule this package does not touch.
- **No phrasing-corpus rows and no matcher-accuracy floor.** S005 reads
  document structure, not English (see the spec's DEC-SER-009); step 4a of the
  add-rule checklist does not apply to it, and claiming a precision number for
  a regex over `^##` would be measurement theatre.

## Affected Capabilities

- `speckit-empty-requirements`
