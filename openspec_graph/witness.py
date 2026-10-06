"""Witness store: proof a stage actually ran (CP-WM).

Unlike ``dialect_card.py``/``ledger.py``/``mermaid.py`` (whose
``docs/hooks.md`` recipe requires zero file I/O), this module both writes
(the ``witness`` CLI verb) and reads (``validate --require-witness``) --
kept as one module because both sides must agree on the exact wire format
and hash algorithm; splitting them would just force two modules to agree on
a shared contract, more drift-risk than benefit at this size. This is a
deliberate deviation from the "pure derived-output module" recipe, not an
oversight.

A witness is a content-addressed JSON file: its filename is the sha256 hex
digest of its own serialized bytes, so verifying a witness is as cheap as
recomputing the hash and comparing it to the filename -- no signature, no
chain, just tamper/corruption detection (``DEC-WM-010``). ``load_witnesses``
fails closed: any file that can't be read, doesn't parse, doesn't match its
own filename hash, carries an unrecognized ``schema_version``, or has a
non-finite ``coverage`` is silently skipped, never raised and never treated
as a passing witness (``DEC-WM-009``/``DEC-WM-018``). ``write_witness``
writes atomically (temp file, then ``os.replace``) so a concurrently-running
reader never observes a partially-written file (``DEC-WM-012``).
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import logging
import math
import os
import re
import tempfile
from collections.abc import Sequence
from pathlib import Path

WITNESS_SCHEMA_VERSION = 1
WITNESS_DIR_NAME = ".planlint/witnesses"
WITNESS_SUFFIX = ".json"
# ``compute_hash`` is sha256 and its hex digest is the filename stem. Derived
# from the hash function rather than written as a number, so the filename
# shape the reader expects cannot drift from the one the writer produces.
HEX_DIGEST_LENGTH = hashlib.sha256().digest_size * 2

# Child of ``planlint``; ``log.configure()`` owns the handler (DEC-LH-005).
# The loader fails closed by *skipping* a bad record, which is right for the
# verdict and opaque for the person debugging it: a CI run that reports W001
# "never witnessed" against a store that visibly holds files needs to say,
# under ``--verbose``, which file was dropped and why. Every skip below logs
# its reason at DEBUG, so the default run stays quiet and the verdict is
# unchanged (R-WM-9: still never raises, still never a pass).
logger = logging.getLogger("planlint.witness")

__all__ = [
    "HEX_DIGEST_LENGTH",
    "WITNESS_DIR_NAME",
    "WITNESS_SCHEMA_VERSION",
    "WITNESS_SUFFIX",
    "Witness",
    "compute_hash",
    "load_witnesses",
    "matching_witnesses",
    "serialize",
    "write_witness",
]


@dataclasses.dataclass(frozen=True)
class Witness:
    """One recorded proof that ``stage`` ran, at ``sha``, with this outcome.

    ``recorded_at`` (ISO-8601 UTC) is informational/debugging only -- never
    load-bearing for selection (``DEC-WM-019``: no "most recent wins"
    tie-break, since that would trust wall-clock time across potentially
    different, clock-skewed CI runners).
    """

    schema_version: int
    stage: str
    exit_code: int
    coverage: float | None
    sha: str
    recorded_at: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "exit_code": self.exit_code,
            "coverage": self.coverage,
            "sha": self.sha,
            "recorded_at": self.recorded_at,
        }


def compute_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def serialize(witness: Witness) -> bytes:
    """Canonical JSON bytes -- the exact bytes written to disk and hashed.

    Sorted keys, compact separators: the same ``Witness`` always serializes
    to the same bytes, so ``compute_hash`` is deterministic and the on-disk
    file's content is literally what gets hashed (no re-serialization step
    that could silently diverge from what was written).
    """
    return json.dumps(witness.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_witness(root: Path, witness: Witness) -> Path:
    """Write ``witness`` under ``root/.planlint/witnesses/<hash>.json``, atomically.

    Writes to a temp file in the same directory first, then ``os.replace()``s
    it into place -- a concurrently-running ``load_witnesses()`` call (an
    overlapping second ``validate --require-witness``, say) can never observe
    a partially-written file (``DEC-WM-012``). Content-addressing makes this
    idempotent: writing the same ``Witness`` twice produces the same target
    path with the same bytes, harmlessly.
    """
    directory = root / WITNESS_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    payload = serialize(witness)
    target = directory / f"{compute_hash(payload)}{WITNESS_SUFFIX}"
    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=WITNESS_SUFFIX)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        os.replace(tmp_name, target)
    except BaseException:
        # Best-effort cleanup: the original exception is what the caller needs,
        # so a failure to remove the temp file must not replace it.
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise
    logger.debug("witness: recorded stage %r at %s as %s", witness.stage, witness.sha, target.name)
    return target


# The filename ``write_witness`` produces: a hex digest plus the suffix.
_HASH_NAME = re.compile(rf"[0-9a-f]{{{HEX_DIGEST_LENGTH}}}{re.escape(WITNESS_SUFFIX)}")


def _skip(path: Path, reason: str) -> None:
    """One DEBUG line per dropped record, naming the file and the cause.

    The *name* is as untrusted as the content -- a store is whatever an
    artifact download put there, and POSIX lets a filename carry a newline,
    which would start a second log line a CI runner reads as its own (a
    workflow command such as ``::error::`` is honoured only at the start of a
    line). A name in the shape this module writes is logged bare, so the
    hash an operator greps for appears as-is; anything else goes through the
    same escaped, length-bounded ``_brief`` as a record's values.
    """
    name = path.name if _HASH_NAME.fullmatch(path.name) else _brief(path.name)
    logger.debug("witness: skipping %s: %s", name, reason)


# A record's values are untrusted: a store is whatever an artifact download
# put there. ``repr`` already escapes newlines and control characters, so a
# value cannot forge a log line; this also bounds its length, so one oversized
# field cannot flood a CI log.
_BRIEF_LIMIT = 60


def _brief(value: object) -> str:
    text = repr(value)
    return text if len(text) <= _BRIEF_LIMIT else f"{text[:_BRIEF_LIMIT]}..."


def _load_one(path: Path) -> Witness | None:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        _skip(path, f"unreadable ({exc.__class__.__name__})")
        return None
    if compute_hash(payload) != path.stem:
        _skip(path, "content does not match the sha256 in its filename")
        return None
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # json.loads(bytes) decodes internally before parsing -- non-UTF-8
        # bytes raise UnicodeDecodeError (a ValueError sibling, not a
        # JSONDecodeError subclass) directly from that step, before json's
        # own parser ever runs. Must not escape load_witnesses()'s "never
        # raises" contract (R-WM-9).
        _skip(path, "not valid UTF-8 JSON")
        return None
    if not isinstance(data, dict):
        _skip(path, f"top level is {type(data).__name__}, not an object")
        return None
    schema_version = data.get("schema_version")
    # bool is an int subclass in Python (True == 1) -- schema_version: true
    # must not silently pass this check as if it were the real value 1.
    if isinstance(schema_version, bool) or schema_version != WITNESS_SCHEMA_VERSION:
        _skip(path, f"schema_version {_brief(schema_version)} is not {WITNESS_SCHEMA_VERSION}")
        return None
    coverage = data.get("coverage")
    if coverage is not None:
        if isinstance(coverage, bool) or not isinstance(coverage, (int, float)) or not math.isfinite(coverage):
            _skip(path, f"coverage {_brief(coverage)} is not a finite number")
            return None
        coverage = float(coverage)
    exit_code = data.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        _skip(path, f"exit_code {_brief(exit_code)} is not an integer")
        return None
    try:
        return Witness(
            schema_version=schema_version,
            stage=str(data["stage"]),
            exit_code=exit_code,
            coverage=coverage,
            sha=str(data["sha"]),
            recorded_at=str(data["recorded_at"]),
        )
    except KeyError as exc:
        _skip(path, f"missing required field {_brief(exc.args[0])}")
        return None
    except (TypeError, ValueError) as exc:
        _skip(path, f"malformed field ({exc.__class__.__name__})")
        return None


def load_witnesses(root: Path) -> tuple[Witness, ...]:
    """Every valid witness under ``root/.planlint/witnesses/``.

    A missing directory returns ``()``. Fails closed per-file, never
    per-store: one corrupt/malformed/hash-mismatched/wrong-schema-version
    file is skipped like any other non-declaring file, mirroring
    ``detect._adrs()``'s established discipline -- it can't crash every CLI
    verb that calls ``detect.profile()``, and it can't silently count as a
    pass either.
    """
    directory = root / WITNESS_DIR_NAME
    if not directory.is_dir():
        logger.debug("witness: no store at %s", directory)
        return ()
    witnesses: list[Witness] = []
    candidates = sorted(directory.glob(f"*{WITNESS_SUFFIX}"))
    for path in candidates:
        witness = _load_one(path)
        if witness is not None:
            witnesses.append(witness)
    logger.debug(
        "witness: loaded %d of %d record(s) from %s", len(witnesses), len(candidates), directory
    )
    return tuple(witnesses)


def matching_witnesses(witnesses: Sequence[Witness], stage: str, sha: str) -> tuple[Witness, ...]:
    """Every witness recorded for ``stage`` at exactly ``sha``, any exit code.

    No single "best match" -- callers decide what "matches" means for their
    own check (``DEC-WM-019``): W001 asks whether any result has
    ``exit_code == 0``; W002 asks whether every such result clears the
    coverage floor.
    """
    return tuple(w for w in witnesses if w.stage == stage and w.sha == sha)
