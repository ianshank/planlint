"""Tests for openspec_graph.witness (change package: add-witness-mode).

Pure, no CLI/subprocess -- mirrors test_ledger.py's/test_dialect_card.py's
style. Direct function calls against openspec_graph.witness, not through
detect.profile() (that's covered separately in test_graft_witness.py, since it also
exercises the git-dependent _current_sha() lazy wiring).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

import pytest

from openspec_graph import witness
from openspec_graph.witness import Witness
from tests import support

pytestmark = pytest.mark.unit

# Windows needs Administrator rights or Developer Mode to create any symlink
# at all -- probed once, at this module's import time, not assumed from
# sys.platform, so a Windows box that does have one of those enabled still
# runs this test.
_CAN_SYMLINK = support.supports_symlinks()

SHA = "a" * 40
# A filename in the shape ``write_witness`` produces, whose content will
# never hash to it: the fixture for "well-formed name, wrong content".
_ZERO_NAME = "0" * witness.HEX_DIGEST_LENGTH + witness.WITNESS_SUFFIX


def _witness(**overrides: object) -> Witness:
    fields: dict[str, object] = {
        "schema_version": witness.WITNESS_SCHEMA_VERSION,
        "stage": "test",
        "exit_code": 0,
        "coverage": 97.5,
        "sha": SHA,
        "recorded_at": "2026-01-01T00:00:00Z",
    }
    fields.update(overrides)
    return Witness(**fields)  # type: ignore[arg-type]


def _write_raw(root: Path, data: dict[str, object]) -> Path:
    """Write a witness file directly from a dict, bypassing write_witness() --
    simulates a hand-edited, tampered, or cross-version file, matching
    DEC-WM-018's own reasoning for validating at load time, not just record
    time."""
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    directory = root / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{witness.compute_hash(payload)}.json"
    path.write_bytes(payload)
    return path


def test_witness_round_trips_through_write_and_load(tmp_path: Path) -> None:
    w = _witness()
    witness.write_witness(tmp_path, w)
    assert witness.load_witnesses(tmp_path) == (w,)


def test_witness_filename_is_the_sha256_of_its_own_content(tmp_path: Path) -> None:
    path = witness.write_witness(tmp_path, _witness())
    assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()


def test_write_witness_creates_the_planlint_witnesses_directory_if_absent(tmp_path: Path) -> None:
    assert not (tmp_path / witness.WITNESS_DIR_NAME).exists()
    witness.write_witness(tmp_path, _witness())
    assert (tmp_path / witness.WITNESS_DIR_NAME).is_dir()


def test_write_witness_is_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A concurrently-running load_witnesses() must never observe a
    # partially-written file (DEC-WM-012) -- proven by verifying the only
    # operation that makes the file appear at its final path is a single
    # rename of an already-fully-written temp file: nothing exists at the
    # target before that rename, and the temp file already holds the
    # complete payload when it happens.
    w = _witness()
    real_replace = os.replace
    calls: list[tuple[bytes, bool]] = []

    def spy_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        calls.append((Path(src).read_bytes(), Path(dst).exists()))
        real_replace(src, dst)

    monkeypatch.setattr(witness.os, "replace", spy_replace)  # type: ignore[attr-defined]
    path = witness.write_witness(tmp_path, w)
    assert len(calls) == 1
    payload_at_rename_time, target_existed_before = calls[0]
    assert payload_at_rename_time == witness.serialize(w)
    assert target_existed_before is False
    assert path.read_bytes() == witness.serialize(w)


def test_write_witness_cleans_up_the_temp_file_and_reraises_on_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(src: object, dst: object) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(witness.os, "replace", boom)  # type: ignore[attr-defined]
    with pytest.raises(OSError, match="simulated rename failure"):
        witness.write_witness(tmp_path, _witness())
    directory = tmp_path / witness.WITNESS_DIR_NAME
    leftover = list(directory.glob("*"))
    assert leftover == [], f"a failed write must not leave a temp file behind: {leftover}"


def test_load_witnesses_returns_empty_tuple_when_the_directory_is_absent(tmp_path: Path) -> None:
    assert witness.load_witnesses(tmp_path) == ()


@pytest.mark.skipif(not _CAN_SYMLINK, reason="platform/user lacks symlink-creation privilege")
def test_load_witnesses_skips_a_dangling_symlink_without_raising(tmp_path: Path) -> None:
    # glob("*.json") lists directory entries by name pattern only, not
    # readability -- mirrors the exact class of bug fixed for ADR discovery
    # this session (detect._adrs()'s directory branch).
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    (directory / _ZERO_NAME).symlink_to(directory / "does-not-exist.json")
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_a_file_whose_content_does_not_match_its_filename_hash(tmp_path: Path) -> None:
    # AC-WM-16 (non-success): a tampered/corrupt witness must fail closed,
    # not raise and not be treated as a pass.
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    (directory / _ZERO_NAME).write_bytes(witness.serialize(_witness()))
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_malformed_json_without_raising(tmp_path: Path) -> None:
    payload = b"not valid json {"
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    (directory / f"{witness.compute_hash(payload)}.json").write_bytes(payload)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_valid_json_that_is_not_an_object(tmp_path: Path) -> None:
    # Well-formed JSON whose top-level value isn't a dict at all (a bare
    # array here) -- distinct from malformed JSON above; .get() would raise
    # AttributeError on this without the isinstance(data, dict) guard.
    payload = b"[1, 2, 3]"
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    (directory / f"{witness.compute_hash(payload)}.json").write_bytes(payload)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_non_utf8_bytes_without_raising(tmp_path: Path) -> None:
    # GitHub Copilot review finding on PR #14: json.loads(bytes) decodes
    # internally before parsing, and non-UTF-8 bytes raise
    # UnicodeDecodeError (a ValueError sibling, not a json.JSONDecodeError
    # subclass) directly from that step -- a real, previously-uncaught
    # violation of load_witnesses()'s "never raises" contract (R-WM-9) for
    # any hash-matching-but-non-UTF-8 file (this is content-addressed, so
    # naturally-corrupted bytes would fail the hash check first; the real
    # trigger is a hand-crafted or non-first-party-tool-written file --
    # still a real concern given .planlint/witnesses/ is part of the
    # target repo's own, potentially untrusted, working tree).
    payload = b'{"stage": "test\xc3\x28"}'  # \xc3 starts a 2-byte UTF-8
    # sequence; \x28 ("(") is not a valid continuation byte.
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    (directory / f"{witness.compute_hash(payload)}.json").write_bytes(payload)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_a_schema_version_that_is_a_bool_not_an_int(tmp_path: Path) -> None:
    # GitHub Copilot review finding on PR #14: bool is an int subclass in
    # Python (True == 1), so schema_version: true would otherwise silently
    # pass the `== WITNESS_SCHEMA_VERSION` check -- defeating the strict
    # schema-version validation DEC-WM-018 specifically added to close this
    # exact bug class (the same shape as the already-fixed
    # dialect_card.diff_cards() schema bug).
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    payload = witness.serialize(_witness(schema_version=True))
    (directory / f"{witness.compute_hash(payload)}.json").write_bytes(payload)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_an_exit_code_that_is_a_bool_not_an_int(tmp_path: Path) -> None:
    # Same bug class as schema_version above, one line down in the same
    # function -- not itself flagged by the review, but exit_code == 0
    # means "the assertion held" in W001's own logic, so silently coercing
    # exit_code: false to 0 would be a stricter, more consequential version
    # of the identical type-confusion bug, not a hypothetical one.
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    payload = witness.serialize(_witness(exit_code=False))
    (directory / f"{witness.compute_hash(payload)}.json").write_bytes(payload)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_a_file_missing_a_required_field_without_raising(tmp_path: Path) -> None:
    data = {"schema_version": witness.WITNESS_SCHEMA_VERSION, "stage": "test", "exit_code": 0}
    _write_raw(tmp_path, data)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_a_file_with_an_unrecognized_schema_version(tmp_path: Path) -> None:
    data = {
        "schema_version": witness.WITNESS_SCHEMA_VERSION + 1,
        "stage": "test",
        "exit_code": 0,
        "coverage": 97.0,
        "sha": SHA,
        "recorded_at": "2026-01-01T00:00:00Z",
    }
    _write_raw(tmp_path, data)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_a_file_with_non_finite_coverage(tmp_path: Path) -> None:
    data = {
        "schema_version": witness.WITNESS_SCHEMA_VERSION,
        "stage": "test",
        "exit_code": 0,
        "coverage": float("nan"),
        "sha": SHA,
        "recorded_at": "2026-01-01T00:00:00Z",
    }
    _write_raw(tmp_path, data)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_skips_a_file_with_a_boolean_coverage(tmp_path: Path) -> None:
    # bool is a subclass of int in Python; a JSON `true`/`false` must not be
    # silently coerced into a coverage number.
    data = {
        "schema_version": witness.WITNESS_SCHEMA_VERSION,
        "stage": "test",
        "exit_code": 0,
        "coverage": True,
        "sha": SHA,
        "recorded_at": "2026-01-01T00:00:00Z",
    }
    _write_raw(tmp_path, data)
    assert witness.load_witnesses(tmp_path) == ()


def test_load_witnesses_accepts_a_witness_with_no_recorded_coverage(tmp_path: Path) -> None:
    w = _witness(coverage=None)
    witness.write_witness(tmp_path, w)
    assert witness.load_witnesses(tmp_path) == (w,)


def test_matching_witnesses_filters_by_stage_and_sha_only_not_exit_code() -> None:
    # matching_witnesses() itself is exit-code-agnostic -- callers (W001/W002)
    # decide what "matches" means for their own check (DEC-WM-019).
    w_match = _witness()
    w_wrong_stage = _witness(stage="lint")
    w_wrong_sha = _witness(sha="b" * 40)
    w_failing = _witness(exit_code=1)
    result = witness.matching_witnesses([w_match, w_wrong_stage, w_wrong_sha, w_failing], "test", SHA)
    assert set(result) == {w_match, w_failing}


# --- The atomic-write rollback (DEC-WM-012) ---------------------------------
#
# `write_witness` writes to a temp file and `os.replace`s it into place so a
# crash mid-write can never leave a partially-written record that a later run
# would read as real. The rollback arm of that -- unlinking the temp file when
# the write or the replace fails -- had never executed under test, which meant
# the guarantee the whole tempfile dance exists to provide was asserted only in
# a docstring.


def test_write_witness_removes_its_temp_file_when_the_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed write leaves no debris in the witness store."""
    record = Witness(
        schema_version=witness.WITNESS_SCHEMA_VERSION,
        stage="test", exit_code=0, coverage=None, sha="a" * 40,
        recorded_at="2026-01-01T00:00:00Z",
    )

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(witness.os, "replace", _fail)
    with pytest.raises(OSError):
        witness.write_witness(tmp_path, record)

    store = tmp_path / witness.WITNESS_DIR_NAME
    leftovers = sorted(p.name for p in store.iterdir()) if store.exists() else []
    assert leftovers == [], (
        f"a failed write left {leftovers} behind; the temp file must be removed so "
        "the store never accumulates debris that looks like a partial record"
    )


def test_write_witness_reraises_the_original_error_not_the_cleanup_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cleanup is best-effort; the caller must still see what actually failed.

    If the rollback's own ``unlink`` raises, suppressing it is correct -- the
    disk-full error is the diagnosis, and replacing it with a
    file-not-found from the cleanup path would send the reader after the
    wrong problem.
    """
    record = Witness(
        schema_version=witness.WITNESS_SCHEMA_VERSION,
        stage="test", exit_code=0, coverage=None, sha="b" * 40,
        recorded_at="2026-01-01T00:00:00Z",
    )

    def _fail_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError(28, "No space left on device")

    def _fail_unlink(*_args: object, **_kwargs: object) -> None:
        raise OSError(2, "No such file or directory")

    monkeypatch.setattr(witness.os, "replace", _fail_replace)
    monkeypatch.setattr(witness.os, "unlink", _fail_unlink)
    with pytest.raises(OSError) as caught:
        witness.write_witness(tmp_path, record)
    assert "No space left on device" in str(caught.value)


# --- debug logging: why a record was skipped ---------------------------------
#
# The loader fails closed by dropping a bad record. That is right for the
# verdict and opaque for whoever is debugging a CI run that reports W001
# "never witnessed" against a store that visibly holds files, so every skip
# names its file and cause at DEBUG. Captured with ``support.captured_logger``,
# which attaches to the emitting logger directly: ``log.configure()`` sets
# ``planlint.propagate = False``, so records never reach the root handler
# caplog installs. The helper used to live here; test_repo_io.py and the
# gate-script tests needed the same body, so it moved.


def _messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records]


_GOOD = {
    "schema_version": witness.WITNESS_SCHEMA_VERSION,
    "stage": "test",
    "exit_code": 0,
    "coverage": 97.5,
    "sha": SHA,
    "recorded_at": "2026-01-01T00:00:00Z",
}


@pytest.mark.parametrize(
    ("label", "record", "reason"),
    [
        ("wrong-schema", {**_GOOD, "schema_version": 2}, "schema_version 2 is not"),
        ("bool-schema", {**_GOOD, "schema_version": True}, "schema_version True is not"),
        ("nan-coverage", {**_GOOD, "coverage": float("nan")}, "coverage nan is not a finite number"),
        ("bool-exit", {**_GOOD, "exit_code": False}, "exit_code False is not an integer"),
        ("missing-stage", {k: v for k, v in _GOOD.items() if k != "stage"}, "missing required field 'stage'"),
    ],
)
def test_each_skipped_record_logs_its_file_and_reason(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, label: str, record: dict[str, object], reason: str
) -> None:
    """Non-success: a dropped record is still dropped, and now says why."""
    path = _write_raw(tmp_path, record)
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
    lines = _messages(caplog)
    assert any(path.name in line and reason in line for line in lines), (label, lines)
    assert any("loaded 0 of 1 record(s)" in line for line in lines), lines


def test_a_hash_mismatch_is_logged_as_such(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    forged = directory / _ZERO_NAME
    forged.write_bytes(witness.serialize(_witness()))
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
    assert any(
        forged.name in line and "does not match the sha256" in line for line in _messages(caplog)
    )


@pytest.mark.parametrize(
    ("payload", "reason"),
    [(b"{not json", "not valid UTF-8 JSON"), (b"\xff\xfe\x00", "not valid UTF-8 JSON"), (b"[1, 2]", "not an object")],
)
def test_undecodable_and_non_object_records_are_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, payload: bytes, reason: str
) -> None:
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    (directory / f"{witness.compute_hash(payload)}.json").write_bytes(payload)
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
    assert any(reason in line for line in _messages(caplog)), _messages(caplog)


def test_an_absent_store_and_a_loaded_record_are_both_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
        recorded = witness.write_witness(tmp_path, _witness())
        assert witness.load_witnesses(tmp_path) == (_witness(),)
    lines = _messages(caplog)
    assert any("no store at" in line for line in lines), lines
    assert any("recorded stage 'test'" in line and recorded.name in line for line in lines), lines
    assert any("loaded 1 of 1 record(s)" in line for line in lines), lines


def test_skip_logging_is_silent_at_the_default_level(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The default run stays quiet: nothing is emitted above DEBUG."""
    _write_raw(tmp_path, {**_GOOD, "schema_version": 2})
    target = logging.getLogger("planlint.witness")
    target.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.WARNING, logger="planlint.witness"):
            witness.load_witnesses(tmp_path)
    finally:
        target.removeHandler(caplog.handler)
    assert caplog.records == []


def test_an_oversized_untrusted_value_is_truncated_in_the_log(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Non-success: a record's values are untrusted, so one huge field must not
    flood a CI log, and an embedded newline must not forge a second line."""
    path = _write_raw(tmp_path, {**_GOOD, "exit_code": "x" * 10_000 + "\n::error::forged"})
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
    line = next(m for m in _messages(caplog) if path.name in m)
    assert len(line) < 300, len(line)
    assert "\n" not in line
    assert line.endswith("... is not an integer"), line


@pytest.mark.parametrize("error", [TypeError, ValueError])
def test_a_record_the_dataclass_refuses_is_skipped_and_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    error: type[Exception],
) -> None:
    """Non-success: the defensive arm. JSON-decoded values cannot make today's
    ``Witness`` raise, but a validating one (a ``__post_init__`` range check,
    say) would, and the loader's never-raises contract (R-WM-9) must hold
    then too -- skipped, named, never a traceback and never a pass."""
    path = _write_raw(tmp_path, _GOOD)

    def refuse(**_fields: object) -> Witness:
        raise error("refused")

    monkeypatch.setattr(witness, "Witness", refuse)
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
    assert any(
        path.name in line and f"malformed field ({error.__name__})" in line for line in _messages(caplog)
    ), _messages(caplog)


def _can_name_a_file_with_a_newline(directory: Path) -> bool:
    """Capability probe: POSIX allows a newline in a filename; Windows does not."""
    try:
        probe = directory / "probe\nname"
        probe.write_bytes(b"")
        probe.unlink()
    except OSError:
        return False
    return True


def test_an_artifact_controlled_filename_cannot_forge_a_log_line(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Non-success: a store is whatever an artifact download put there, so a
    file's *name* is as untrusted as its content. A newline in it must not
    start a second log line (a GitHub workflow command such as ``::error::``
    is honoured only at the start of a line), and its length is bounded."""
    directory = tmp_path / witness.WITNESS_DIR_NAME
    directory.mkdir(parents=True)
    if not _can_name_a_file_with_a_newline(directory):
        pytest.skip("this filesystem cannot hold a newline in a filename (capability probe)")
    (directory / ("x\n::error::forged" + "y" * 200 + ".json")).write_bytes(b"{}")
    with support.captured_logger(caplog, "planlint.witness"):
        assert witness.load_witnesses(tmp_path) == ()
    # A set: the capture handler is attached to the emitting logger and, via
    # propagation, to the root, so one record can arrive twice.
    skipped = {m for m in _messages(caplog) if "skipping" in m}
    assert len(skipped) == 1, skipped
    (line,) = skipped
    assert "\n" not in line
    assert len(line) < 200, len(line)
    assert "content does not match the sha256" in line


def test_an_ordinary_hash_filename_is_logged_bare(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """The escaping applies to a hostile name only: the normal content-hash
    filename an operator greps for appears unquoted."""
    path = _write_raw(tmp_path, {**_GOOD, "schema_version": 2})
    with support.captured_logger(caplog, "planlint.witness"):
        witness.load_witnesses(tmp_path)
    assert any(f"skipping {path.name}: " in m for m in _messages(caplog)), _messages(caplog)


def test_the_filename_shape_is_derived_from_the_hash_function(tmp_path: Path) -> None:
    """Regression guard for the writer/reader contract: the digest length the
    loader expects in a filename is the length ``compute_hash`` produces, and
    a file the writer just produced is one the loader logs bare (unescaped)."""
    assert len(witness.compute_hash(b"")) == witness.HEX_DIGEST_LENGTH
    written = witness.write_witness(tmp_path, _witness())
    assert written.suffix == witness.WITNESS_SUFFIX
    assert witness._HASH_NAME.fullmatch(written.name) is not None
    assert witness._HASH_NAME.fullmatch(written.stem) is None
