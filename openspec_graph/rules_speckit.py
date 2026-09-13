"""SpecKit-dialect rules: S001-S004."""

from __future__ import annotations

from collections.abc import Iterable

from .detect import StackProfile
from .parse import ParsedSpec, scenario_has_gwt
from .parse_semantics import NEEDS_CLARIFICATION, line_of, strip_waiver_comments
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


SPECKIT_RULES: tuple[Rule, ...] = (
    Rule("S001", ERROR, ("speckit",), "no unresolved [NEEDS CLARIFICATION] markers", _unresolved_clarification),
    Rule("S002", ERROR, ("speckit",), "FR-/SC- identifiers are unique", _duplicate_ident),
    Rule("S003", WARN, ("speckit",), "functional requirements are normative", _requirement_without_modal),
    Rule("S004", WARN, ("speckit",), "acceptance scenarios state a stimulus and an outcome", _scenario_without_gwt),
)
