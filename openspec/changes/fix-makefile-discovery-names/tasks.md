# Tasks: fix-makefile-discovery-names

## Milestone 1 — Reproduce the defect before touching code

- Build the three shapes by hand — a repo whose only makefile is
  `GNUmakefile`, one whose only makefile is lowercase `makefile`, and one
  holding `GNUmakefile` and `Makefile` with different targets in each —
  and confirm against `c60f894` that `detect` reports no targets for the
  first two and only `Makefile`'s targets for the third.
- Confirm the fail-open end to end: add one spec citing a stage the
  makefile does not declare, and record that `validate` exits 0 with no
  G004 under the `GNUmakefile` and `makefile` spellings while exiting 1
  under `Makefile`. Reproduce *before* the fix, per `DEC-MFD-007` — the
  expectations below are written from this, not from the detector.
- **Gate:** `make test`

## Milestone 2 — Resolve the makefile by GNU Make's search order

- `openspec_graph/detect.py`: add
  `MAKEFILE_NAMES: tuple[str, ...] = ("GNUmakefile", "makefile", "Makefile")`
  beside `MANIFESTS` / `INVARIANT_SOURCES` / `ADR_SOURCES`, with a comment
  in the same style recording that the order is GNU Make's own, that the
  first match wins, and that `GNUmakefile` shadows rather than extends
  `Makefile` (R-MFD-4, DEC-MFD-001). Not added to `__all__`, matching its
  three siblings.
- `openspec_graph/detect.py`: rewrite `_make_target_facts` to walk
  `MAKEFILE_NAMES` and use the first candidate for which
  `read_text_or_none` returns a value that `is not None` — never a
  truthiness test, so a zero-byte higher-precedence file still shadows
  (R-MFD-1, R-MFD-2, R-MFD-3, R-MFD-6, DEC-MFD-003, DEC-MFD-004). Delete
  the `root / "Makefile"` literal and its separate `.exists()` pre-check.
  Record the resolved candidate and each skipped one at `logger.debug`,
  never on stdout (C-MFD-3, DEC-MFD-005). No change to `machinery.py`, and
  no change to the existing low-confidence widening through
  `_legacy_make_targets`.
- **Gate:** `make test`

## Milestone 3 — The labelled corpus shapes

- `tests/corpus/targets/gnumakefile-only/{repo/,expected.json}`,
  `tests/corpus/targets/lowercase-makefile-only/{repo/,expected.json}`,
  `tests/corpus/targets/gnumakefile-wins-over-makefile/{repo/,expected.json}`:
  each a minimal textual repository plus a **partial** card pinning
  `make_targets` only, hand-written from Milestone 1's expectation and
  expected to fail before Milestone 2 lands (R-MFD-8, DEC-MFD-007). The
  precedence shape declares a target that exists only in the shadowed
  `Makefile`, so a union would be visible as extra entries.
- `tests/corpus/targets/README.md`: one row per new shape in the shape
  table, naming the card field it pins and why, plus a sentence in the
  generated-cases paragraph for the three cases below.
- `tests/support.py`: `supports_case_sensitive_filenames()`, a real
  `tempfile` probe written in the style of `supports_symlinks()` — never a
  `sys.platform` check (DEC-MFD-006).
- `tests/test_detect_corpus.py`: three generated cases beside the existing
  directory-named-`Makefile` and large-Makefile ones — a directory named
  `GNUmakefile` shadowing a real `Makefile` (falls through, no traceback),
  a zero-byte `GNUmakefile` shadowing a real `Makefile` (reports no
  targets), and `Makefile` + `makefile` as two distinct files under a
  `supports_case_sensitive_filenames()` skip guard (exactly one is read).
- **Gate:** `make test`

## Milestone 4 — Pin the constant, the call site, and the end-to-end inversion

- `tests/test_detect_names.py` (new module): pin `MAKEFILE_NAMES`'s exact
  contents and order against GNU Make's documented search order; an
  `ast`-based guard that `_make_target_facts`'s body holds no string
  literal equal to any candidate name, in the style of
  `tests/test_decomposition.py`'s import guards (AC-MFD-5).
- `tests/test_detect_names.py`: a case-insensitivity test proving a
  `Makefile`-only repository produces the identical card regardless of
  which candidate matched, so the resolution is observationally identical
  across the CI matrix (AC-MFD-10).
- `tests/test_graft.py`: the end-to-end inversion — a `GNUmakefile`-only
  repository whose spec cites an undeclared stage now reports `ERROR G004`
  and exit 1 (AC-MFD-4). Leave
  `test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all`
  unchanged; it is the C-MFD-2 guard and must keep passing as written.
- Confirm no pinned hash in `tests/test_decomposition.py` needs editing
  and that `dialect_card.SCHEMA_VERSION` is untouched (AC-MFD-11).
- **Gate:** `make test`

## Milestone 5 — Record it

- `README.md`: a ledger item for the defect, in the voice of the existing
  numbered "and what it got wrong" entries — a valid repository whose
  makefile was named `GNUmakefile` or `makefile` was told it had no
  stages, so the cited-stage rule evaluated nothing.
- `CHANGELOG.md`: the behaviour change, stated as what a previously-green
  target repository may now report.
- `docs/peer-review-2026-09.md`: mark **R1** closed in the remediation
  table, naming this change package; leave F2/F3 and R2–R8 untouched.
- `docs/next-steps.md` item 1: strike the "find `GNUmakefile`/`makefile`"
  half of the R1–R3 sentence and leave the `GENERIC_STAGES` and
  `hard_coded()` halves standing as separate work.
- `docs/architecture/c4.md`: the one line describing how `detect.profile`
  feeds `machinery.parse_makefile`, updated to say which file it resolves
  and by what order.
- **Gate:** `make pre-pr`
