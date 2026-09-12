"""GitHub Action projections of a validate findings envelope (CP-GA).

A pure projection, like ``sarif.py``: it is handed the findings envelope
``cmd_validate`` already printed and reshapes it. It never evaluates a rule,
never touches the filesystem, and never sees a ``Path``. Stdlib-only, no I/O,
and **zero intra-package imports** -- SARIF dispatch stays in ``cli.py`` so
this module cannot reach ``sarif.to_sarif`` or the rule table.

The four public functions are the four surfaces the composite action needs:
status, workflow-command annotations, a step-summary Markdown document, and
the envelope-derivable ``key=value`` outputs. ``error`` is not among the
statuses this module can produce: it is the action's mapping for "there was
no envelope to read".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeGuard

__all__ = [
    "ANNOTATION_LIMIT",
    "OUTPUT_KEYS",
    "STATUSES",
    "status_of",
    "to_annotations",
    "to_outputs",
    "to_step_summary",
]

# GitHub's Checks UI has long truncated workflow-command annotations at ten
# per step (DEC-GA-010). A higher cap would emit commands the UI never shows
# and could hide the trailing withheld-count notice.
ANNOTATION_LIMIT = 10

STATUSES = ("pass", "fail", "error", "indeterminate")

OUTPUT_KEYS = (
    "status",
    "errors",
    "warnings",
    "findings",
    "blocking",
    "specs-checked",
    "rules-triggered",
    "version",
)

_SEVERITY_TO_COMMAND = {"ERROR": "error", "WARN": "warning", "INFO": "notice"}

# Workflow-command escaping tables. Applied in order; ``%`` first so a later
# replacement cannot re-escape a ``%`` we just introduced. Property values
# additionally escape ``:`` and ``,`` because those delimit the command grammar.
_DATA_ESCAPES: tuple[tuple[str, str], ...] = (
    ("%", "%25"),
    ("\r", "%0D"),
    ("\n", "%0A"),
)
_PROPERTY_ESCAPES: tuple[tuple[str, str], ...] = (
    *_DATA_ESCAPES,
    (":", "%3A"),
    (",", "%2C"),
)

_WITHHELD_NOTE = (
    "{n} findings withheld; the full envelope is in the evidence artifact"
)


def _escape_data(value: str) -> str:
    for src, dst in _DATA_ESCAPES:
        value = value.replace(src, dst)
    return value


def _escape_property(value: str) -> str:
    for src, dst in _PROPERTY_ESCAPES:
        value = value.replace(src, dst)
    return value


def _is_int(value: object) -> TypeGuard[int]:
    """True for integers that are not bool.

    ``bool`` is a subclass of ``int`` in Python, so a bare ``isinstance(...,
    int)`` would treat ``True`` as ``1`` and flip ``status`` silently.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _int_field(envelope: Mapping[str, object], key: str) -> int:
    value = envelope.get(key)
    return value if _is_int(value) else 0


def _findings(envelope: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw = envelope.get("findings")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, Mapping)]


def _counts(findings: Sequence[Mapping[str, object]]) -> tuple[int, int, int]:
    errors = sum(1 for finding in findings if finding.get("severity") == "ERROR")
    warnings = sum(1 for finding in findings if finding.get("severity") == "WARN")
    return errors, warnings, len(findings)


def status_of(envelope: Mapping[str, object]) -> str:
    """The gate status implied by a findings envelope (R-GA-5).

    ``fail`` when ``blocking > 0``; ``indeterminate`` when ``blocking`` is
    zero and ``specs_checked`` is zero; ``pass`` otherwise. ``error`` is not
    produced here -- it is the action's mapping for a missing envelope.
    """
    if _int_field(envelope, "blocking") > 0:
        return "fail"
    if _int_field(envelope, "specs_checked") == 0:
        return "indeterminate"
    return "pass"


def _annotation_line(finding: Mapping[str, object]) -> str:
    severity = str(finding.get("severity") or "")
    command = _SEVERITY_TO_COMMAND.get(severity, "error")
    props: list[str] = []
    path = finding.get("path")
    if path:
        props.append(f"file={_escape_property(str(path))}")
    line = finding.get("line")
    if _is_int(line) and line >= 1:
        props.append(f"line={line}")
    rule = finding.get("rule")
    if rule:
        props.append(f"title={_escape_property(str(rule))}")
    message = _escape_data(str(finding.get("message") or ""))
    prop_str = f" {','.join(props)}" if props else ""
    return f"::{command}{prop_str}::{message}"


def to_annotations(
    envelope: Mapping[str, object], *, limit: int = ANNOTATION_LIMIT
) -> list[str]:
    """One workflow command per finding, capped, in envelope order (R-GA-12)."""
    findings = _findings(envelope)
    shown = findings[:limit]
    lines = [_annotation_line(finding) for finding in shown]
    withheld = len(findings) - len(shown)
    if withheld:
        lines.append(f"::notice::{_WITHHELD_NOTE.format(n=withheld)}")
    return lines


def to_outputs(envelope: Mapping[str, object]) -> dict[str, str]:
    """Envelope-derivable action outputs as ``key=value`` strings (R-GA-13)."""
    findings = _findings(envelope)
    errors, warnings, n_findings = _counts(findings)
    rules = sorted({str(finding.get("rule")) for finding in findings if finding.get("rule")})
    return {
        "status": status_of(envelope),
        "errors": str(errors),
        "warnings": str(warnings),
        "findings": str(n_findings),
        "blocking": str(_int_field(envelope, "blocking")),
        "specs-checked": str(_int_field(envelope, "specs_checked")),
        "rules-triggered": ",".join(rules),
        "version": str(envelope.get("tool_version") or ""),
    }


def _cell(value: object) -> str:
    text = str(value or "").replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return text.replace("|", "\\|")


def to_step_summary(
    envelope: Mapping[str, object], *, limit: int = ANNOTATION_LIMIT
) -> str:
    """Markdown step summary derived only from the envelope (R-GA-14).

    Always ends in a newline. The withheld-count note here is the guaranteed
    surface when GitHub truncates the annotation stream (DEC-GA-010).
    """
    findings = _findings(envelope)
    errors, warnings, n_findings = _counts(findings)
    status = status_of(envelope)
    lines = [
        f"## planlint: {status}",
        "",
        f"- status: `{status}`",
        f"- specs checked: {_int_field(envelope, 'specs_checked')}",
        f"- errors: {errors}",
        f"- warnings: {warnings}",
        f"- findings: {n_findings}",
        f"- blocking: {_int_field(envelope, 'blocking')}",
        "",
        "| Rule | Severity | Path | Message |",
        "| --- | --- | --- | --- |",
    ]
    shown = findings[:limit]
    for finding in shown:
        lines.append(
            "| {rule} | {severity} | {path} | {message} |".format(
                rule=_cell(finding.get("rule")),
                severity=_cell(finding.get("severity")),
                path=_cell(finding.get("path") or ""),
                message=_cell(finding.get("message")),
            )
        )
    withheld = len(findings) - len(shown)
    if withheld:
        lines.append("")
        lines.append(_WITHHELD_NOTE.format(n=withheld) + ".")
    return "\n".join(lines) + "\n"
