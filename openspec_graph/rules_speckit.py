"""SpecKit-dialect rules: S001-S005."""

from __future__ import annotations

from collections.abc import Iterable

from .detect import StackProfile
from .parse import ParsedSpec, scenario_has_gwt
from .parse_semantics import (
    NEEDS_CLARIFICATION,
    line_of,
    speckit_requirements_heading_line,
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


def _empty_requirements_section(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    """S005: a Requirements section that yielded no requirement at all.

    ``parse_speckit`` scopes its FR scan to a level-3 ``Functional
    Requirements`` nested inside the level-2 ``Requirements`` span, which is
    correct and closes a real over-matching bug (R-SK-30/AC-SK-49). The flip
    side is silent data loss: a hand-edited spec that writes the heading one
    level up yields zero requirements, and every gate agrees nothing is wrong.
    Measured -- the same file with one heading level changed produced graph
    nodes ``FR-001, FR-002, SC-001`` against ``SC-001`` alone, both reporting
    ``0 error · 0 warn · 0 info`` and ``broken_links: 0``.

    G001 does not catch it: a surviving Success Criterion means the spec is not
    requirement-less, so G001 has nothing to say.

    The discrimination, and the reason this is not the false positive
    ``docs/next-steps.md`` item 4b refused: a Requirements-shaped section that
    *exists* and yields nothing is not the same document as one with no such
    section. A user-story-only draft never declares the section and stays
    silent; only a spec that promised requirements and delivered none is
    flagged. Waiver comments are stripped first, so a heading quoted inside a
    waiver's reason is not mistaken for the document's own.

    WARN, so no ``--fail-on ERROR`` consumer changes verdict.
    """
    if spec.requirements:
        return
    stripped = strip_waiver_comments(spec.raw)
    line = speckit_requirements_heading_line(stripped)
    if not line:
        return
    yield CheckHit(
        "a Requirements section is present but no FR- requirement was "
        "extracted from it; requirements declared at the wrong heading level "
        "are dropped from the graph silently",
        line=line,
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
        "a declared Requirements section yields at least one requirement",
        _empty_requirements_section,
    ),
)
