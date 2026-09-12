"""GitHub-surface projections of a ``validate --format json`` envelope (CP-GA).

A pure projection, like ``sarif.py`` and ``mermaid.py``: it is handed the
findings envelope some earlier run already produced and reshapes it into the
surfaces GitHub Actions understands -- workflow-command annotations, a job
summary, and step outputs. It never evaluates a rule, never reads a file, and
never decides policy; ``--fail-on`` has already been applied by the run that
wrote the envelope, and ``blocking`` records the result.

Stdlib-only, no I/O, and **zero intra-package imports** -- the posture
``sarif.py`` holds and for the same reason: a projection that reaches back
into the package is one refactor away from depending on evaluation order. The
schema version it validates against is passed in rather than imported, so
``rule_types.FINDINGS_SCHEMA_VERSION`` stays the single source of that number.

The one gate is :func:`parse_envelope`. Everything downstream of it takes the
typed :class:`Envelope` it returns and is total: a projection can neither
raise nor have to re-check a field. That split is deliberate. The CLI verb
built on this module must never exit 1 -- exit 1 means "findings were
reported" everywhere else in this tool -- so every way a malformed envelope
can go wrong has to become one ``EnvelopeError`` at one place, not a
``KeyError`` from somewhere in the middle of a renderer.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence

__all__ = [
    "ANNOTATION_LIMIT_PER_SEVERITY",
    "SEVERITIES",
    "STATUSES",
    "STATUS_ERROR",
    "STATUS_FAIL",
    "STATUS_INDETERMINATE",
    "STATUS_PASS",
    "DiscoveryCard",
    "Envelope",
    "EnvelopeError",
    "FindingRecord",
    "counts_by_severity",
    "discovery_notes",
    "parse_card",
    "parse_envelope",
    "status_of",
    "to_annotations",
    "to_outputs",
    "to_step_summary",
]

# --- statuses ---------------------------------------------------------------
#
# Four, and the distinction between the last two is the point. A gate that
# cannot tell "the specs are fine" from "there were no specs to check" or
# "the tool never ran" reports a green check for gating nothing, which is the
# defect this module exists to close.

# ruff: noqa: S105 -- "pass" here is a gate verdict, not a credential.
STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_ERROR = "error"
STATUS_INDETERMINATE = "indeterminate"

STATUSES: tuple[str, ...] = (STATUS_PASS, STATUS_FAIL, STATUS_ERROR, STATUS_INDETERMINATE)

# The severity vocabulary of the findings envelope, in descending order of
# seriousness. Ordering is load-bearing: it is the order the summary table
# groups by and the order the annotation cap spends its budget in.
SEVERITIES: tuple[str, ...] = ("ERROR", "WARN", "INFO")

# GitHub renders at most ten annotations of each type per step (and fifty per
# job), so a run with more findings than that silently loses the overflow in
# the pull-request view. The cap is therefore a property of the surface, not a
# policy an adopter tunes, which is why it lives here as a named constant
# rather than as an action input -- and why it is applied *per severity*: one
# shared budget spent in envelope order (path, then rule) would let a file
# full of INFO findings withhold every ERROR in the run.
ANNOTATION_LIMIT_PER_SEVERITY = 10

# planlint severities to workflow-command names. Total over SEVERITIES; an
# unrecognized severity maps *up* to "error" rather than down to "notice", the
# same fail-upward reasoning sarif.py's level map records: under-reporting
# hides a finding in the one surface a reviewer actually reads.
_COMMANDS: Mapping[str, str] = {"ERROR": "error", "WARN": "warning", "INFO": "notice"}
_DEFAULT_COMMAND = "error"

# Workflow-command escaping, as the Actions toolkit defines it. Order is
# load-bearing: "%" must be substituted first, or the "%" introduced by a
# later replacement would itself be re-escaped into "%25".
_DATA_ESCAPES: tuple[tuple[str, str], ...] = (
    ("%", "%25"),
    ("\r", "%0D"),
    ("\n", "%0A"),
)
# Property values sit inside the comma-separated, colon-terminated property
# list, so those two characters need escaping there and only there.
_PROPERTY_ESCAPES: tuple[tuple[str, str], ...] = (
    *_DATA_ESCAPES,
    (":", "%3A"),
    (",", "%2C"),
)

# The envelope keys this projection depends on. Named once so the validator,
# its error messages, and the tests all read from one list.
_REQUIRED_ENVELOPE_KEYS: tuple[str, ...] = (
    "schema_version",
    "tool_version",
    "specs_checked",
    "findings",
    "blocking",
)
_REQUIRED_FINDING_KEYS: tuple[str, ...] = ("rule", "severity", "message", "path", "line")

# The dialect-card keys the discovery notes below read. The card carries more
# than this; only what is projected is required, so a card gaining fields stays
# readable by an older build.
_REQUIRED_CARD_KEYS: tuple[str, ...] = ("schema_version", "dialect", "make_targets", "threshold")


class EnvelopeError(ValueError):
    """A payload that is not a findings envelope this build can project.

    Raised by :func:`parse_envelope` only. Its message is written to be shown
    verbatim to an operator, so it names the offending key and what was found
    rather than describing a type error.
    """


@dataclasses.dataclass(frozen=True)
class FindingRecord:
    """One finding, with the fields every GitHub surface needs.

    A parsed view of an envelope finding rather than the raw mapping, so the
    renderers below are total. The raw mappings are kept separately on
    :class:`Envelope` for the SARIF projection, which consumes them directly.
    """

    rule: str
    severity: str
    message: str
    path: str | None
    line: int

    @property
    def command(self) -> str:
        """The workflow-command name for this finding's severity."""
        return _COMMANDS.get(self.severity, _DEFAULT_COMMAND)


@dataclasses.dataclass(frozen=True)
class DiscoveryCard:
    """The facts a run measured the specs against, from ``detect --format json``.

    Carried separately from the findings because it answers a different
    question. The envelope says which claims failed; this says what there was
    to check them against -- and a rule with nothing to check against reports
    nothing, which is indistinguishable from a clean pass unless somebody says
    so out loud.
    """

    dialect: str
    make_target_count: int
    threshold_locator: str | None

    @property
    def has_make_targets(self) -> bool:
        return self.make_target_count > 0

    @property
    def has_threshold(self) -> bool:
        return self.threshold_locator is not None


@dataclasses.dataclass(frozen=True)
class Envelope:
    """A validated ``validate --format json`` payload."""

    schema_version: int
    tool_version: str
    specs_checked: int
    blocking: int
    findings: tuple[FindingRecord, ...]
    # The finding mappings exactly as they arrived. sarif.to_sarif() consumes
    # these, not the parsed records above, which is what keeps
    # `report --format sarif` byte-identical to `validate --format sarif`:
    # both renderings read the same dicts rather than two shapes somebody has
    # to keep in step.
    raw_findings: tuple[Mapping[str, object], ...]


# --- validation -------------------------------------------------------------


def _require_int(container: Mapping[str, object], key: str, *, where: str) -> int:
    value = container.get(key)
    # bool is a subclass of int, and `True` as a count is a producer bug worth
    # reporting rather than silently reading as 1.
    if isinstance(value, bool) or not isinstance(value, int):
        raise EnvelopeError(f"{where}: {key!r} must be an integer, got {type(value).__name__}")
    if value < 0:
        raise EnvelopeError(f"{where}: {key!r} must not be negative, got {value}")
    return value


def _require_str(container: Mapping[str, object], key: str, *, where: str) -> str:
    value = container.get(key)
    if not isinstance(value, str):
        raise EnvelopeError(f"{where}: {key!r} must be a string, got {type(value).__name__}")
    return value


def _parse_finding(raw: object, index: int) -> FindingRecord:
    where = f"findings[{index}]"
    if not isinstance(raw, Mapping):
        raise EnvelopeError(f"{where}: must be an object, got {type(raw).__name__}")
    missing = [key for key in _REQUIRED_FINDING_KEYS if key not in raw]
    if missing:
        raise EnvelopeError(f"{where}: missing required key(s) {', '.join(sorted(missing))}")

    path = raw["path"]
    if path is not None and not isinstance(path, str):
        raise EnvelopeError(f"{where}: 'path' must be a string or null, got {type(path).__name__}")

    return FindingRecord(
        rule=_require_str(raw, "rule", where=where),
        severity=_require_str(raw, "severity", where=where),
        message=_require_str(raw, "message", where=where),
        path=path,
        line=_require_int(raw, "line", where=where),
    )


def parse_envelope(payload: object, *, schema_version: int) -> Envelope:
    """Validate a decoded findings envelope, or raise :class:`EnvelopeError`.

    ``schema_version`` is the version this build understands, passed in rather
    than imported so this module keeps its zero-intra-package-import posture
    and ``rule_types.FINDINGS_SCHEMA_VERSION`` stays the one place that number
    is declared.

    Every field the projections below read is checked here, including types.
    That breadth is the requirement, not thoroughness for its own sake: an
    envelope missing ``findings`` or carrying ``blocking`` as a string would
    otherwise surface as a ``TypeError`` from inside a renderer, and a
    traceback exits 1 -- which in this tool means "findings were reported".
    """
    if not isinstance(payload, Mapping):
        raise EnvelopeError(
            f"expected a findings envelope object, got {type(payload).__name__}"
        )

    missing = [key for key in _REQUIRED_ENVELOPE_KEYS if key not in payload]
    if missing:
        raise EnvelopeError(f"not a findings envelope: missing {', '.join(sorted(missing))}")

    found_version = _require_int(payload, "schema_version", where="envelope")
    if found_version != schema_version:
        raise EnvelopeError(
            f"findings schema_version {found_version} is not the {schema_version} this "
            "build reads; regenerate the envelope with this version of planlint"
        )

    raw_findings = payload["findings"]
    if not isinstance(raw_findings, Sequence) or isinstance(raw_findings, (str, bytes)):
        raise EnvelopeError(
            f"envelope: 'findings' must be a list, got {type(raw_findings).__name__}"
        )

    records = tuple(_parse_finding(raw, index) for index, raw in enumerate(raw_findings))
    # Re-read the mappings for the SARIF pass-through only after every one has
    # been validated above, so the two views cannot disagree about which
    # findings exist.
    originals = tuple(raw for raw in raw_findings if isinstance(raw, Mapping))

    return Envelope(
        schema_version=found_version,
        tool_version=_require_str(payload, "tool_version", where="envelope"),
        specs_checked=_require_int(payload, "specs_checked", where="envelope"),
        blocking=_require_int(payload, "blocking", where="envelope"),
        findings=records,
        raw_findings=originals,
    )


def parse_card(payload: object, *, schema_version: int) -> DiscoveryCard:
    """Validate a decoded dialect card, or raise :class:`EnvelopeError`.

    Strict for the same reason ``delta --baseline`` is strict about the card it
    is handed: a silently-degraded read would report "no machinery detected"
    for a repository that has plenty, which is the opposite of the warning this
    card exists to raise.
    """
    if not isinstance(payload, Mapping):
        raise EnvelopeError(f"expected a dialect card object, got {type(payload).__name__}")

    missing = [key for key in _REQUIRED_CARD_KEYS if key not in payload]
    if missing:
        raise EnvelopeError(f"not a dialect card: missing {', '.join(sorted(missing))}")

    found_version = _require_int(payload, "schema_version", where="card")
    if found_version != schema_version:
        raise EnvelopeError(
            f"dialect card schema_version {found_version} is not the {schema_version} "
            "this build reads; regenerate it with this version of planlint"
        )

    targets = payload["make_targets"]
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        raise EnvelopeError(
            f"card: 'make_targets' must be a list, got {type(targets).__name__}"
        )

    # `threshold` is null when no coverage floor was found, and an object
    # carrying `locator` and `value` when one was. Only the locator is
    # projected: the number is the target repository's business, and quoting
    # it here would be this tool restating a threshold it exists to make
    # specs read from config.
    threshold = payload["threshold"]
    locator: str | None = None
    if isinstance(threshold, Mapping):
        candidate = threshold.get("locator")
        locator = candidate if isinstance(candidate, str) else ""
    elif threshold is not None:
        raise EnvelopeError(
            f"card: 'threshold' must be an object or null, got {type(threshold).__name__}"
        )

    return DiscoveryCard(
        dialect=_require_str(payload, "dialect", where="card"),
        make_target_count=len(targets),
        threshold_locator=locator,
    )


# --- projections ------------------------------------------------------------


def status_of(envelope: Envelope) -> str:
    """The gate verdict this envelope describes.

    ``fail`` when the run reported findings at or above its own ``--fail-on``;
    ``indeterminate`` when it reported none because there was nothing to
    check; ``pass`` otherwise. ``STATUS_ERROR`` is never returned here -- it
    describes the absence of an envelope, which is the caller's observation,
    not a property of one.

    Derived from ``blocking`` rather than from a separately supplied exit
    code: ``cmd_validate`` computes both from the same list, so passing the
    exit code in as well would be one fact stated twice, with two ways to
    disagree.
    """
    if envelope.blocking > 0:
        return STATUS_FAIL
    if envelope.specs_checked == 0:
        return STATUS_INDETERMINATE
    return STATUS_PASS


def counts_by_severity(envelope: Envelope) -> dict[str, int]:
    """Finding counts keyed by severity, with every known severity present.

    Total over :data:`SEVERITIES` so a consumer never has to distinguish "zero
    errors" from "the key is missing", plus any unrecognized severity actually
    seen, so an unknown one is reported rather than silently dropped.
    """
    counts = dict.fromkeys(SEVERITIES, 0)
    for finding in envelope.findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def _escape(value: str, table: tuple[tuple[str, str], ...]) -> str:
    for needle, replacement in table:
        value = value.replace(needle, replacement)
    return value


def discovery_notes(card: DiscoveryCard) -> list[str]:
    """Plain-text warnings about what this run had nothing to check against.

    Two rules relax rather than fire when the fact they compare against is
    absent: the cited-make-target check returns early on a target repository
    with no Makefile, and the hard-coded-threshold check cannot report a
    citation as matching a floor that was never found. Both are the right
    behaviour for a rule -- inventing a finding from missing evidence would be
    worse -- and both mean a green run over such a repository proves less than
    it looks like it proves. Saying so is this function's whole job; it never
    changes the status, which stays a property of the findings.

    Returns an empty list when the target has both kinds of machinery, so a
    normal repository gets no extra noise.
    """
    notes: list[str] = []
    if not card.has_make_targets:
        notes.append(
            "No make targets were detected in this target, so the cited-stage check "
            "(G004) had nothing to compare citations against. A pass here means the "
            "specs are well-formed, not that they cite stages this repository runs."
        )
    if not card.has_threshold:
        notes.append(
            "No coverage-floor locator was detected in this target, so the "
            "hard-coded-threshold check (G003) could not confirm any cited number "
            "against config. Declare a floor, or read findings about thresholds as "
            "unverified."
        )
    return notes


def _properties(finding: FindingRecord, path_prefix: str = "") -> str:
    """The ``file=...,line=...,title=...`` property list for one finding.

    ``path_prefix`` prepends the target's position inside the repository, for a
    run whose ``--target`` is a subdirectory: finding paths are relative to the
    target, while GitHub resolves an annotation's ``file=`` against the
    repository root, so without it every annotation for a nested target lands
    on a path that does not exist.
    """
    parts = [f"title={_escape(finding.rule, _PROPERTY_ESCAPES)}"]
    if finding.path:
        located = f"{path_prefix.rstrip('/')}/{finding.path}" if path_prefix else finding.path
        parts.insert(0, f"file={_escape(located, _PROPERTY_ESCAPES)}")
        # SARIF's startLine minimum is 1 and a workflow command's is the same,
        # so a line of 0 -- which is every finding this tool produces today,
        # since no rule sets one -- emits no line property at all rather than
        # being clamped to 1. A wrong location a reviewer cannot tell is wrong
        # costs more than no location.
        if finding.line >= 1:
            parts.append(f"line={finding.line}")
    return ",".join(parts)


def _withheld_notice(withheld: int, limit: int) -> str:
    return (
        f"::notice title=planlint::{withheld} further finding(s) not annotated "
        f"(GitHub renders at most {limit} annotations per severity per step); "
        "the complete set is in the run's evidence directory."
    )


def to_annotations(
    envelope: Envelope,
    *,
    card: DiscoveryCard | None = None,
    path_prefix: str = "",
    limit: int = ANNOTATION_LIMIT_PER_SEVERITY,
) -> list[str]:
    """Workflow-command annotation lines, one per finding, in envelope order.

    Capped per severity (see :data:`ANNOTATION_LIMIT_PER_SEVERITY`). When
    anything is withheld, exactly one trailing notice says how many, so a
    capped run can never be mistaken for a complete one.
    """
    lines: list[str] = []
    spent: dict[str, int] = {}
    withheld = 0
    for finding in envelope.findings:
        key = finding.severity
        if spent.get(key, 0) >= limit:
            withheld += 1
            continue
        spent[key] = spent.get(key, 0) + 1
        message = _escape(finding.message, _DATA_ESCAPES)
        lines.append(f"::{finding.command} {_properties(finding, path_prefix)}::{message}")
    if withheld:
        lines.append(_withheld_notice(withheld, limit))
    if card is not None:
        # Appended, not prepended: a discovery caveat is context for the
        # findings above it, and burying the findings under it would trade one
        # readability problem for another.
        lines += [
            f"::warning title=planlint::{_escape(note, _DATA_ESCAPES)}"
            for note in discovery_notes(card)
        ]
    return lines


def _cell(value: str) -> str:
    """One Markdown table cell: no pipes, no line breaks, never empty."""
    collapsed = " ".join(value.split())
    return collapsed.replace("|", "\\|") or "-"


def to_step_summary(
    envelope: Envelope,
    *,
    card: DiscoveryCard | None = None,
    limit: int = ANNOTATION_LIMIT_PER_SEVERITY,
) -> str:
    """The job-summary Markdown for this run.

    A pure function of the envelope: no timestamps, no run identifiers, no
    environment lookups, so two calls over one envelope are byte-identical and
    the summary can be regenerated from a downloaded artifact.
    """
    counts = counts_by_severity(envelope)
    status = status_of(envelope)
    tally = ", ".join(f"{counts.get(sev, 0)} {sev.lower()}" for sev in SEVERITIES)

    lines = [
        "## planlint",
        "",
        f"**Status:** `{status}` — {tally} across {envelope.specs_checked} spec(s) checked",
        "",
        f"{envelope.blocking} finding(s) at or above this run's failure threshold.",
    ]

    if status == STATUS_INDETERMINATE:
        lines += [
            "",
            (
                "No spec was checked, so this run proves nothing about the "
                "repository. Add a change package under `openspec/changes/`, or a "
                "SpecKit feature under `specs/`, before treating a pass here as a gate."
            ),
        ]

    if card is not None:
        floor = card.threshold_locator or "(none found)"
        lines += [
            "",
            (
                f"**Detected:** dialect `{_cell(card.dialect)}`, "
                f"{card.make_target_count} make target(s), coverage floor "
                f"`{_cell(floor)}`"
            ),
        ]
        for note in discovery_notes(card):
            lines += ["", "> [!WARNING]", f"> {note}"]

    if envelope.findings:
        lines += ["", "| Rule | Severity | Path | Message |", "|---|---|---|---|"]
        spent: dict[str, int] = {}
        withheld = 0
        for finding in envelope.findings:
            if spent.get(finding.severity, 0) >= limit:
                withheld += 1
                continue
            spent[finding.severity] = spent.get(finding.severity, 0) + 1
            lines.append(
                f"| {_cell(finding.rule)} | {_cell(finding.severity)} "
                f"| {_cell(finding.path or '')} | {_cell(finding.message)} |"
            )
        if withheld:
            lines += [
                "",
                f"_{withheld} further finding(s) not listed; see the run's evidence._",
            ]

    lines.append("")
    return "\n".join(lines)


def _single_line(value: str) -> str:
    """Collapse a value to one line, for a ``key=value`` output file.

    ``$GITHUB_OUTPUT`` is line-oriented, so an embedded newline would end the
    value early and the remainder would be read as another key.
    """
    return " ".join(value.split())


def to_outputs(envelope: Envelope, *, card: DiscoveryCard | None = None) -> dict[str, str]:
    """The action outputs derivable from this envelope, as strings.

    The dialect card is threaded through rather than read here because this
    module touches no file: the caller has already read it and passes the
    parsed result. When it is absent the discovery outputs are simply omitted,
    so a consumer can tell "not measured" from "measured as zero".
    """
    counts = counts_by_severity(envelope)
    rules_triggered = sorted({finding.rule for finding in envelope.findings})
    outputs = {
        "status": status_of(envelope),
        "errors": str(counts.get("ERROR", 0)),
        "warnings": str(counts.get("WARN", 0)),
        "infos": str(counts.get("INFO", 0)),
        "findings": str(len(envelope.findings)),
        "blocking": str(envelope.blocking),
        "specs-checked": str(envelope.specs_checked),
        "rules-triggered": ",".join(rules_triggered),
        "version": _single_line(envelope.tool_version),
    }
    if card is not None:
        outputs["dialect"] = _single_line(card.dialect)
        outputs["make-targets"] = str(card.make_target_count)
        outputs["coverage-floor"] = _single_line(card.threshold_locator or "")
        outputs["discovery-warnings"] = str(len(discovery_notes(card)))
    return outputs
