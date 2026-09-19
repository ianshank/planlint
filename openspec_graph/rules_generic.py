"""Universal (dialect-agnostic) rules: G001-G011.

G006/G009's real checks are cross-tree (a declared invariant/ADR cited by no
living spec anywhere), so neither can be expressed as a per-spec
``Rule.check`` -- see ``orphan_invariant_ids()``/``orphan_adr_ids()`` below
and ``rules.evaluate_tree()``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .detect import StackProfile
from .parse import ParsedSpec, threshold_values
from .rule_types import ERROR, GENERIC_STAGES, INFO, WARN, CheckHit, CheckResult, Rule

__all__ = ["GENERIC_RULES"]


def _no_criteria(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    if spec.criteria:
        return
    if spec.requirements:
        yield (
            f"{len(spec.requirements)} requirement(s) but no Scenario or acceptance "
            "criterion; the obligations are stated but nothing verifies them"
        )
    else:
        yield (
            "no requirements and no verifiable criteria recognized; the document "
            "uses neither the `### Requirement:`/`#### Scenario:` form nor "
            "`- [ ] **AC-<AREA>-<n>:**`, so 'done' is undefined"
        )


def _needs_negative(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    if spec.criteria and not spec.has_negative_criterion:
        yield (
            "no criterion names a non-success outcome; a plan that only describes "
            "success has not said what going wrong looks like"
        )


def _hard_coded_threshold(spec: ParsedSpec, profile: StackProfile) -> Iterable[CheckResult]:
    locator = profile.threshold.locator if profile.threshold else "the governance policy"
    real_value = profile.threshold.value if profile.threshold else None
    for offender in spec.hard_coded_thresholds:
        if real_value is not None:
            values = threshold_values(offender)
            # Suppress only on a single, unambiguous match -- never on "the
            # real value merely appears somewhere in the line," which would
            # wrongly excuse a genuine violation sitting next to a
            # coincidentally-matching, unrelated number (e.g. a delta
            # description: "raised from 80% to 90%").
            if len(values) == 1 and values[0] == real_value:
                continue
        yield f"hard-coded threshold; read it from {locator} instead -- {offender!r}"


def _unknown_make_target(spec: ParsedSpec, profile: StackProfile) -> Iterable[CheckResult]:
    # No confidence-level branching needed here: detect._make_target_facts
    # already widens profile.make_targets with the regex fallback whenever
    # structural parsing is low-confidence, so this rule, graph.py, and
    # scaffold.pick_stage() all see the same, already-resolved picture of
    # "what targets exist" (AC-MP-3/AC-MP-4).
    if not profile.make_targets:
        return
    known = set(profile.make_targets)
    for target in spec.make_refs:
        if target not in known and target not in GENERIC_STAGES:
            yield (
                f"cites `make {target}` which is not a target in the target "
                f"repo's Makefile; the criterion cannot be executed as written"
            )


def _unchecked_make_citations(spec: ParsedSpec, profile: StackProfile) -> Iterable[CheckResult]:
    """G010: the citations G004 could not check, no make targets being detected.

    G004 returns early when ``profile.make_targets`` is empty, and that is
    correct -- a repo that does not use Make has not lied by mentioning it.
    What was wrong is that the CLI then said nothing at all, so a spec citing
    a stage that cannot exist reported PASS with zero findings even at
    ``--fail-on INFO``. The Action computed this separately as
    ``discovery-warnings``; the CLI, which pre-commit and every agent
    invocation use, did not.

    INFO precisely because it changes no verdict: ``--fail-on ERROR`` and
    ``--fail-on WARN`` runs keep a byte-identical pass/fail outcome. It reports
    an *unrun check*, never a missing makefile -- a spec with no `make`
    citation has nothing unchecked and stays silent.

    One finding per spec, not per citation: the fact being reported is a
    property of the run, and n copies of one unrun check would drown the
    findings a reader can act on.
    """
    if profile.make_targets or not spec.make_refs:
        return
    # "no make targets were detected" and not "no makefile was found": the
    # only fact available here is `profile.make_targets == ()`, which conflates
    # a missing makefile, a present-but-empty one, one declaring nothing but
    # special targets, and one that exists and cannot be read. Naming the
    # wrong cause sends the author looking for a file that is sitting right
    # there. `detect` prints which names it looked for; this reports what it
    # found.
    #
    # `make_refs` is a deduplicated set of target names (parse.parse_spec), so
    # this counts distinct stages, not citation occurrences. Said plainly
    # rather than left for a reader to discover from a surprising number.
    yield (
        f"{len(spec.make_refs)} distinct `make` stage(s) not checked: no make "
        f"targets were detected in the target repo, so G004 could not run"
    )


def _generic_stage_not_a_target(spec: ParsedSpec, profile: StackProfile) -> Iterable[CheckResult]:
    """G011: a generic stage cited against a Makefile that does not declare it.

    ``GENERIC_STAGES`` are exempt from G004 for a real reason: "run `make
    test`" is idiomatic English for "run the suite", and a repo using tox, npm
    scripts or `just` is not lying by writing it. That argument holds only
    while the repo has not shown that it uses Make.

    So this fires only when ``make_targets`` is non-empty -- the repo
    demonstrably uses Make and still declares no such target. WARN, not ERROR,
    because the shorthand reading survives even then. Where there is no
    makefile at all, G010 covers the citation and this stays silent, so no
    citation is ever reported by two rules.
    """
    if not profile.make_targets:
        return
    known = set(profile.make_targets)
    for target in spec.make_refs:
        if target in GENERIC_STAGES and target not in known:
            yield (
                f"cites `make {target}`, which this repo's Makefile does not "
                f"declare; it is exempt from G004 as a conventional stage name, "
                f"but the repo does use Make, so the citation may not run"
            )


def _unknown_invariant(spec: ParsedSpec, profile: StackProfile) -> Iterable[CheckResult]:
    if not profile.invariant_ids:
        return
    known = set(profile.invariant_ids)
    for ref in spec.invariant_refs:
        if ref not in known:
            yield f"references {ref}, which is not declared in {profile.invariant_source_name}"


def _unjustified_waiver(spec: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    for waiver in spec.waivers:
        if not waiver.reason:
            yield CheckHit(
                f"waiver of {waiver.rule} at line {waiver.line} has no reason; "
                "a waiver is a claim that must justify itself",
                line=waiver.line,
            )


def orphan_invariant_ids(specs: Sequence[ParsedSpec], profile: StackProfile) -> tuple[str, ...]:
    """Declared invariants cited by no spec in ``specs``.

    A whole-tree question, not a per-spec one -- called once by
    ``rules.evaluate_tree()``, never per-spec. See that function and
    DEC-WL-001 for why no ``Rule.check`` signature can express this.
    """
    if not profile.invariant_ids:
        return ()
    cited = {ref for spec in specs for ref in spec.invariant_refs}
    return tuple(inv for inv in profile.invariant_ids if inv not in cited)


def _orphan_invariant_registry_stub(_s: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    # Inert: the real cross-tree check is orphan_invariant_ids(), run once
    # per validate/graph pass by rules.evaluate_tree(), not per spec. This
    # stub exists only so `planlint rules`/`rules --json` lists G006.
    return ()


def _unknown_adr(spec: ParsedSpec, profile: StackProfile) -> Iterable[CheckResult]:
    if not profile.adr_ids:
        return
    known = set(profile.adr_ids)
    for ref in spec.adr_refs:
        if ref not in known:
            yield f"references {ref}, which is not declared in {profile.adr_source_name}"


def orphan_adr_ids(specs: Sequence[ParsedSpec], profile: StackProfile) -> tuple[str, ...]:
    """Declared ADRs cited by no spec in ``specs``.

    A whole-tree question, not a per-spec one -- called once by
    ``rules.evaluate_tree()``, never per-spec. Same shape as
    ``orphan_invariant_ids()`` above (DEC-AD-003).
    """
    if not profile.adr_ids:
        return ()
    cited = {ref for spec in specs for ref in spec.adr_refs}
    return tuple(adr for adr in profile.adr_ids if adr not in cited)


def _orphan_adr_registry_stub(_s: ParsedSpec, _p: StackProfile) -> Iterable[CheckResult]:
    # Inert: the real cross-tree check is orphan_adr_ids(), run once per
    # validate/graph pass by rules.evaluate_tree(), not per spec. This stub
    # exists only so `planlint rules`/`rules --json` lists G009.
    return ()


GENERIC_RULES: tuple[Rule, ...] = (
    Rule("G001", ERROR, ("*",), "spec declares verifiable criteria", _no_criteria),
    Rule(
        "G002",
        ERROR,
        ("harness", "upstream"),
        "at least one non-success criterion",
        _needs_negative,
    ),
    Rule("G003", ERROR, ("*",), "no hard-coded thresholds", _hard_coded_threshold),
    Rule("G004", ERROR, ("*",), "cited make targets exist", _unknown_make_target),
    Rule("G005", WARN, ("*",), "cited invariants are declared", _unknown_invariant),
    Rule(
        "G006",
        WARN,
        ("*",),
        "declared invariants are cited by a living spec or waived",
        _orphan_invariant_registry_stub,
    ),
    Rule("G007", ERROR, ("*",), "every waiver states a reason", _unjustified_waiver),
    Rule("G008", WARN, ("*",), "cited ADRs are declared", _unknown_adr),
    Rule(
        "G009",
        WARN,
        ("*",),
        "declared ADRs are cited by a living spec or waived",
        _orphan_adr_registry_stub,
    ),
    Rule(
        "G010",
        INFO,
        ("*",),
        "make citations are reported when no make targets were detected",
        _unchecked_make_citations,
    ),
    Rule(
        "G011",
        WARN,
        ("*",),
        "cited generic stages exist when the repo uses Make",
        _generic_stage_not_a_target,
    ),
)
