"""SpecKit-dialect rules: S001-S005."""

from __future__ import annotations

from collections.abc import Iterable

from .detect import StackProfile
from .parse import ParsedSpec, scenario_has_gwt
from .parse_semantics import (
    FR_DECL,
    NEEDS_CLARIFICATION,
    blank_html_comments,
    line_of,
    strip_waiver_comments,
)
from .rule_types import ERROR, WARN, CheckHit, CheckResult, Rule

__all__ = ["SPECKIT_RULES"]


def _unresolved_clarification(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    # A waiver's own free-text reason quoting the literal marker while
    # explaining why S001 is being waived must not itself count as an
    # unresolved marker -- scan waiver-stripped text, never raw (R-SK-16),
    # matching this codebase's established reference-extraction discipline.
    # strip_waiver_comments is length-preserving, so line_of on the stripped
    # text matches the raw document (DEC-LH / R-LH-14).
    stripped = strip_waiver_comments(spec.raw)
    for m in NEEDS_CLARIFICATION.finditer(stripped):
        question = (m.group(1) or "").strip() or "no question given"
        yield CheckHit(
            f"unresolved [NEEDS CLARIFICATION] marker ({question[:80]}); the spec admits it is incomplete",
            line=line_of(stripped, m.start()),
        )


def _duplicate_ident(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    seen: set[str] = set()
    for req in spec.requirements:
        if req.ident in seen:
            yield CheckHit(f"duplicate requirement id {req.ident}", line=req.line)
        seen.add(req.ident)
    for crit in spec.criteria:
        if crit.ident in seen:
            yield CheckHit(f"duplicate criterion id {crit.ident}", line=crit.line)
        seen.add(crit.ident)


def _requirement_without_modal(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    for req in spec.requirements:
        if not req.is_normative:
            yield CheckHit(
                f"requirement {req.ident} ({req.text[:60]!r}) uses no SHALL/MUST; it is not normative",
                line=req.line,
            )


def _scenario_without_gwt(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    # crit.note is only ever set for Given/When/Then-derived criteria
    # (parse_speckit.py) -- an SC-00N Success Criterion never carries one,
    # so this guard keeps every Success Criterion from being reported as
    # "missing WHEN/THEN", a claim it never made in the first place.
    for crit in spec.criteria:
        if crit.note and not scenario_has_gwt(crit):
            yield CheckHit(
                f"{crit.ident} ({crit.text[:50]}...) is missing WHEN or THEN and is therefore not executable",
                line=crit.line,
            )


def _dropped_requirement_bullets(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    """S005: the document declares FR- bullets and none reached the graph.

    ``parse_speckit`` scopes its FR scan to a level-3 ``Functional
    Requirements`` nested inside the level-2 ``Requirements`` span. That
    scoping is correct and closes a real over-matching bug (R-SK-30/AC-SK-49);
    it is not touched here. Its flip side is silent data loss: the same file
    with the heading one level up yielded graph nodes ``FR-001, FR-002,
    SC-001`` against ``SC-001`` alone, both reporting ``0 error · 0 warn · 0
    info`` and ``broken_links: 0``. G001 cannot catch it, because the
    surviving Success Criterion means the spec is not requirement-less.

    The predicate is **data loss, not document shape**: FR-shaped bullets
    exist in the text and ``spec.requirements`` is empty, so those bullets
    were written and dropped. Keying on the bullets rather than on a
    ``Requirements``-shaped heading is what keeps this out of the false
    positive ``docs/next-steps.md`` item 4b refused. A heading-based predicate
    fires on a spec whose ``## Requirements`` section holds only
    ``### Non-Functional Requirements`` -- the canonical SpecKit wrapper is
    mandatory, so matching it swallows every legitimately NFR-only document
    and tells its author that requirements were "dropped" when none existed.
    A user-story-only draft and a prose-only section are silent for the same
    reason: nothing was lost.

    It also catches a shape a heading predicate misses -- FR bullets under an
    H3 titled anything else (``### Core Requirements``), which the parser
    refuses by design and which is exactly as lost.

    The locus is the first dropped bullet, not the heading, because that is
    the token the author has to move. HTML comments are blanked first, and via
    ``blank_html_comments`` rather than ``strip_waiver_comments``: the latter
    only blanks comments ``SUPPRESS`` matched, and ``SUPPRESS`` has no
    ``re.DOTALL``, so a multi-line waiver's own reason text still reads as
    document content.

    WARN, so no ``--fail-on ERROR`` consumer changes verdict.
    """
    if spec.requirements:
        return
    text = blank_html_comments(strip_waiver_comments(spec.raw))
    match = FR_DECL.search(text)
    if match is None:
        return
    yield CheckHit(
        f"declares {match.group(1)} but no FR- requirement reached the graph; "
        f"the canonical form is a level-3 `### Functional Requirements` "
        f"heading inside the level-2 `## Requirements` section",
        line=line_of(text, match.start()),
    )


SPECKIT_RULES: tuple[Rule, ...] = (
    Rule("S001", ERROR, ("speckit",), "no unresolved [NEEDS CLARIFICATION] markers", _unresolved_clarification),
    Rule("S002", ERROR, ("speckit",), "FR-/SC- identifiers are unique", _duplicate_ident),
    Rule("S003", WARN, ("speckit",), "functional requirements are normative", _requirement_without_modal),
    Rule("S004", WARN, ("speckit",), "acceptance scenarios state a stimulus and an outcome", _scenario_without_gwt),
    Rule(
        "S005",
        WARN,
        ("speckit",),
        "declared FR- bullets reach the graph",
        _dropped_requirement_bullets,
    ),
)
