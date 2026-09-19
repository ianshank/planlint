"""Rule-engine types: Finding, Rule, and severity constants.

Sits at the bottom of the rules layer. Imports the parsed-spec and stack-profile
types only for type hints (``Rule.check`` signature); performs no analysis.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Iterable
from pathlib import Path

from .detect import StackProfile, to_posix_relative
from .parse import ParsedSpec

__all__ = [
    "ERROR",
    "FINDINGS_SCHEMA_VERSION",
    "INFO",
    "WARN",
    "CheckHit",
    "CheckResult",
    "Finding",
    "ParsedSpec",
    "Rule",
    "StackProfile",
    "as_check_hit",
]

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

# Version of the `validate --json` envelope, declared beside the Finding whose
# serialization it describes -- the same pattern as dialect_card.SCHEMA_VERSION
# and witness.WITNESS_SCHEMA_VERSION, so all three machine-readable outputs
# announce their shape the same way. Bump on any breaking change to the
# envelope or to a finding's own keys; additive keys do not bump it.
FINDINGS_SCHEMA_VERSION = 1

# Make targets a spec may cite without them existing yet in the Makefile.
#
# G004 skips a citation naming any of these, which is a real and deliberate
# narrowing of that rule: "run `make test`" is idiomatic English for "run the
# suite", and a repo using tox, npm scripts or `just` has not lied about its
# machinery by writing it. These are also the five names a spec is most likely
# to cite, so the exemption is not a corner case -- it is most of the traffic,
# and it went undocumented in the rule description, the README and every
# planning document until `docs/peer-review-2026-09.md` F3 measured it.
#
# The exemption is not unconditional any more. G011 (WARN) fires on a cited
# generic stage when `make_targets` is NON-empty -- the repo demonstrably uses
# Make and still declares no such target -- and G010 (INFO) reports the
# citations G004 could not check at all. Between them the silence is gone
# without ERROR-level false positives against a repo that never used Make.
GENERIC_STAGES = {"ci", "test", "validate", "lint", "coverage"}


@dataclasses.dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    path: Path | None = None
    line: int = 0
    subject: str = ""  # entity a tree-scoped finding is about, e.g. an invariant id (G006)

    def as_dict(self, root: Path | None = None) -> dict[str, object]:
        """Serialize for a machine consumer.

        ``root`` renders ``path`` as a POSIX path relative to it, via the same
        ``to_posix_relative`` helper every other serializer in this codebase
        already used -- ``render`` above, ``ledger.build_ledger``,
        ``graph._relative_to``, ``StackProfile.as_dict``. This method was the
        sole holdout, emitting an absolute native-separator path.

        That was a deliberate decision (DEC-PS-002) on the premise that no
        consumer compares the field across two checkouts. The shipped CI
        template refutes it: it uploads ``validate --json`` as a build
        artifact produced on a runner and read elsewhere, where an absolute
        ``/home/runner/work/...`` path resolves to nothing. DEC-FE-001
        supersedes it on that evidence.

        ``root=None`` keeps the pre-existing absolute rendering, so callers
        that have no root to relativize against are unchanged.
        """
        if self.path is None:
            rendered: str | None = None
        elif root is None:
            rendered = str(self.path)
        else:
            # Never dropped and never None when a path exists: a finding
            # outside the target falls back to as_posix() inside the helper.
            rendered = to_posix_relative(self.path, root)
        return {
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "path": rendered,
            "line": self.line,
            "subject": self.subject,
        }

    def render(self, root: Path | None = None) -> str:
        where = ""
        if self.path:
            shown = to_posix_relative(self.path, root)
            where = f"{shown}:{self.line}: " if self.line else f"{shown}: "
        return f"{self.severity:5s} {self.rule}  {where}{self.message}"


@dataclasses.dataclass(frozen=True)
class CheckHit:
    """One rule hit: the message plus an optional 1-based locus.

    ``line`` defaults to the same sentinel ``Finding.line`` uses. A bare
    ``str`` from ``Rule.check`` means the same thing — see ``as_check_hit``.
    """

    message: str
    line: int = 0


CheckResult = str | CheckHit


def as_check_hit(item: CheckResult) -> CheckHit:
    """Total coercion so ``evaluate()`` does not grow an ``isinstance`` ladder.

    A bare ``str`` becomes ``CheckHit(message=item, line=0)``. A ``CheckHit``
    is returned unchanged, including a non-positive ``line``.
    """
    if isinstance(item, CheckHit):
        return item
    return CheckHit(message=item)


@dataclasses.dataclass(frozen=True)
class Rule:
    ident: str
    severity: str
    dialects: tuple[str, ...]  # ("*",) for any
    summary: str
    check: Callable[[ParsedSpec, StackProfile], Iterable[CheckResult]]

    def applies(self, dialect: str) -> bool:
        return "*" in self.dialects or dialect in self.dialects
