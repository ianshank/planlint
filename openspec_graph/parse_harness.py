"""Parser for the harness dialect spec (lists of R-/C- requirements and ACs)."""

from __future__ import annotations

from .parse_model import Criterion, Requirement
from .parse_semantics import (
    AC,
    REQ_DECL,
    REQ_REF,
    VERIFIED_BY,
    line_of,
    section_span,
    strip_waiver_comments,
)

__all__ = ["parse_harness"]


def parse_harness(text: str) -> tuple[tuple[Requirement, ...], tuple[Criterion, ...]]:
    req_origin, req_body = section_span(text, "Requirements")
    reqs = tuple(
        Requirement(
            ident=m.group(1),
            text=m.group(2),
            kind="constraint" if m.group(1).startswith("C-") else "functional",
            line=line_of(text, req_origin + m.start()),
        )
        for m in REQ_DECL.finditer(req_body)
    )

    ac_origin, ac_body = section_span(text, "Acceptance Criteria")
    matches = list(AC.finditer(ac_body))
    criteria: list[Criterion] = []
    for idx, match in enumerate(matches):
        stop = matches[idx + 1].start() if idx + 1 < len(matches) else len(ac_body)
        block = ac_body[match.start() : stop]
        # A waiver comment's own reason text must never leak a spurious
        # `make X` citation into verified_by -- the same bug class already
        # fixed for the spec-wide make_refs/invariant_refs/adr_refs fields
        # (parse.py's citation_text), now closed at the per-criterion level
        # too (found by adversarial review while designing CP-WM: W001/W002
        # turn this citation into a build-gating verdict, not just a
        # cosmetic graph edge).
        verified = VERIFIED_BY.search(strip_waiver_comments(block))
        # The same class, one field over: a waiver's reason text ("the
        # coverage floor fails otherwise") is not the criterion's prose, and
        # letting it into `text` handed G002 a non-success word the author
        # never wrote -- switching the rule off for the document. Found by
        # adversarial review of fix-prose-matcher-precision.
        criteria.append(
            Criterion(
                ident=match.group(2),
                note=match.group(3).strip(" ()"),
                text=strip_waiver_comments(match.group(4)).strip(),
                verified_by=verified.group(1) if verified else "",
                requirement_refs=tuple(sorted(set(REQ_REF.findall(block)))),
                # Span origin plus match.start(), not text.find of a prefix:
                # the first sixty characters of the block include the ident,
                # but a quoted copy earlier in the document used to win
                # (DEC-LH-007).
                line=line_of(text, ac_origin + match.start()),
            )
        )
    return reqs, tuple(criteria)
