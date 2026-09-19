"""Threshold detection and optional-config reading, at the unit level (CP-TC).

The corpus under ``tests/corpus/targets/`` pins whole-repository shapes. These
tests pin the three helpers underneath -- ``as_threshold_number``,
``scoped_fail_under`` and ``read_text_or_none`` -- on the inputs an
adversarial review showed the corpus did not reach: ``float()``'s permissive
grammar, TOML constructs that look like keys or headers, and files that are
not regular files. Each case here was a real misbehaviour before it was a
test.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from openspec_graph import delta, detect
from openspec_graph.parse import parse_spec
from openspec_graph.parse_semantics import threshold_values

TABLE = detect.COVERAGE_REPORT_TABLE


# --- as_threshold_number ----------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("90", 90),
        ("90.0", 90),
        ("85.5", 85.5),
        (" 90 ", 90),
        (90, 90),
        (90.0, 90),
        (0, 0),
        (100, 100),
    ],
)
def test_as_threshold_number_accepts_plain_decimals_in_range(raw: object, expected: object) -> None:
    value = detect.as_threshold_number(raw)
    assert value == expected
    assert type(value) is type(expected), "integral values must stay int; fractions float"


@pytest.mark.parametrize(
    "raw",
    [
        True,
        False,
        None,
        [90],
        {"lines": 90},
        "abc",
        "",
        "nan",
        "inf",
        float("inf"),
        float("nan"),
        # float() would accept every one of these; a coverage floor is none of them.
        "1e2",
        "1_000",
        "-5",
        "٩٠",
        "\uff11\uff12",  # full-width digits
        "+90",
        "90.",
        ".5",
        # In range for float(), out of range for a percentage.
        -1,
        101,
        "150",
        10**30,
    ],
)
def test_as_threshold_number_rejects_what_is_not_a_percentage(raw: object) -> None:
    assert detect.as_threshold_number(raw) is None


def test_as_threshold_number_can_refuse_strings_for_the_json_policy_path() -> None:
    """``governance-policy.json`` always took numbers only; a quoted value is
    a misconfiguration there, not a floor."""
    assert detect.as_threshold_number("90", accept_str=False) is None
    assert detect.as_threshold_number(90, accept_str=False) == 90


# --- scoped_fail_under ------------------------------------------------------


def _scoped(text: str) -> int | float | None:
    return detect.scoped_fail_under(text, TABLE)


def test_scoped_fail_under_reads_only_its_table() -> None:
    assert _scoped("[tool.coverage.report]\nfail_under = 90\n") == 90
    assert _scoped("[tool.other]\nfail_under = 50\n") is None
    assert _scoped("fail_under = 50\n[tool.coverage.report]\nshow_missing = true\n") is None


def test_scoped_fail_under_ignores_lines_inside_multiline_strings() -> None:
    """``exclude_lines`` is a free-text list that lives in exactly this table."""
    text = '[tool.coverage.report]\nexclude_lines = """\nfail_under = 42\n"""\nfail_under = 90\n'
    assert _scoped(text) == 90
    # A header-looking line inside the string must not reset the table either.
    text = '[tool.coverage.report]\nexclude_lines = """\n[tool.other]\n"""\nfail_under = 90\n'
    assert _scoped(text) == 90
    # ...and with no real floor after the string, there is no floor.
    assert _scoped('[tool.coverage.report]\nexclude_lines = """\nfail_under = 42\n"""\n') is None
    # Single-quoted delimiters behave the same.
    text = "[tool.coverage.report]\nexclude_lines = '''\nfail_under = 42\n'''\nfail_under = 90\n"
    assert _scoped(text) == 90


def test_scoped_fail_under_ignores_lines_inside_multiline_arrays() -> None:
    text = (
        "[tool.coverage.report]\n"
        "exclude_also = [\n"
        '  "fail_under = 3",\n'
        '  "[not a table]",\n'
        "  [1, 2],\n"
        "]\n"
        "fail_under = 90\n"
    )
    assert _scoped(text) == 90


@pytest.mark.parametrize(
    "header",
    ["[tool.coverage.report]", "[ tool.coverage.report ]", '["tool"."coverage"."report"]',
     "[tool . coverage . report]", "[tool.coverage.report]  # trailing comment"],
)
def test_scoped_fail_under_normalises_equivalent_table_headers(header: str) -> None:
    assert _scoped(f"{header}\nfail_under = 90\n") == 90


def test_scoped_fail_under_does_not_treat_an_array_of_tables_as_the_table() -> None:
    assert _scoped("[[tool.coverage.report]]\nfail_under = 90\n") is None


def test_scoped_fail_under_rejects_a_quoted_string_floor() -> None:
    assert _scoped('[tool.coverage.report]\nfail_under = "90"\n') is None


def test_scoped_fail_under_is_bom_tolerant_as_a_pure_function() -> None:
    """Same principle as ``machinery.parse_makefile``: public API that takes
    text must not depend on the caller having decoded carefully."""
    assert _scoped("﻿[tool.coverage.report]\nfail_under = 90\n") == 90


def test_scoped_fail_under_first_match_wins_and_subtables_do_not_count() -> None:
    assert _scoped("[tool.coverage.report]\nfail_under = 90\nfail_under = 80\n") == 90
    assert _scoped("[tool.coverage.report.extra]\nfail_under = 90\n") is None


# --- _read_ini_fail_under ---------------------------------------------------


def test_read_ini_fail_under_reads_a_bom_prefixed_file(tmp_path: Path) -> None:
    path = tmp_path / ".coveragerc"
    path.write_bytes(b"\xef\xbb\xbf[report]\nfail_under = 75\n")
    assert detect._read_ini_fail_under(path, "report") == 75


@pytest.mark.parametrize(
    "body",
    [
        "fail_under = 90\n",  # no section header -> configparser.Error
        "[report]\nfail_under = 80\nfail_under = 90\n",  # duplicate option
        "[report]\nshow_missing = true\n",  # key absent
        "[report]\nfail_under = abc\n",  # not a number
        "[report]\nfail_under = 1e2\n",  # float() grammar, not a percentage
    ],
)
def test_read_ini_fail_under_returns_none_rather_than_guessing(tmp_path: Path, body: str) -> None:
    path = tmp_path / ".coveragerc"
    path.write_text(body, encoding="utf-8")
    assert detect._read_ini_fail_under(path, "report") is None


def test_read_ini_fail_under_keeps_a_fractional_floor(tmp_path: Path) -> None:
    path = tmp_path / ".coveragerc"
    path.write_text("[report]\nfail_under = 85.5\n", encoding="utf-8")
    assert detect._read_ini_fail_under(path, "report") == 85.5


# --- governance-policy.json path -------------------------------------------


@pytest.mark.parametrize(
    "policy",
    [
        '{"coverage": []}',
        '{"coverage": {"lines": "abc"}}',
        '{"coverage": {"lines": "90"}}',  # numbers only on this locator
        '{"coverage": {"lines": -5}}',
        '{"coverage": {"lines": true}}',
        "[1, 2]",
        "not json",
    ],
)
def test_governance_policy_without_a_numeric_floor_falls_through(tmp_path: Path, policy: str) -> None:
    (tmp_path / "governance-policy.json").write_text(policy, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.coverage.report]\nfail_under = 90\n")
    profile = detect.profile(tmp_path)
    assert profile.threshold is not None
    assert profile.threshold.locator == f"pyproject.toml:[{TABLE}].fail_under"
    assert profile.threshold.value == 90


def test_governance_policy_accepts_a_bom_and_a_fractional_floor(tmp_path: Path) -> None:
    (tmp_path / "governance-policy.json").write_bytes(
        b'\xef\xbb\xbf{"coverage": {"lines": 85.5}}'
    )
    profile = detect.profile(tmp_path)
    assert profile.threshold is not None
    assert profile.threshold.value == 85.5


# --- read_text_or_none: not a regular file ---------------------------------


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are a POSIX feature")
def test_a_fifo_where_a_config_file_belongs_does_not_hang(tmp_path: Path) -> None:
    """``exists()`` is true for a FIFO and ``open()`` on one blocks until a
    writer appears -- forever, here. ``is_file()`` first, so ``detect`` never
    opens it. A clone cannot contain one, but a working tree can."""
    os.mkfifo(tmp_path / "Makefile")
    os.mkfifo(tmp_path / "pyproject.toml")
    profile = detect.profile(tmp_path)  # would block here before the fix
    assert profile.make_targets == ()
    assert profile.threshold is None


# --- the float floor reaches every consumer correctly ---------------------


def test_threshold_values_keeps_a_fraction_so_g003_compares_like_with_like() -> None:
    assert threshold_values("coverage >= 85.5%") == (85.5,)
    assert threshold_values("coverage >= 90%") == (90,)
    assert threshold_values("from 80% to 90%") == (80, 90)


def test_g003_does_not_flag_a_criterion_that_cites_the_exact_fractional_floor(
    tmp_path: Path,
) -> None:
    """Before ``threshold_values`` learned fractions, a repo whose floor was
    85.5 got a G003 on every criterion that cited it correctly."""
    from openspec_graph import rules

    (tmp_path / "Makefile").write_text("test:\n\t@echo t\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.coverage.report]\nfail_under = 85.5\n")
    spec = tmp_path / "openspec" / "changes" / "c1" / "specs" / "cap" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "# Spec\n\n## Requirements\n\n- R-XY-1: Coverage holds.\n\n"
        "## Acceptance Criteria\n\n"
        "- [ ] **AC-XY-1:** Line coverage is >= 85.5% as pyproject.toml gates it. (R-XY-1)\n"
        "  _Verified by:_ `pytest -k test_x` · stage: `make test`\n"
        "- [ ] **AC-XY-2 (non-success):** A drop below the floor fails `make test`. (R-XY-1)\n"
        "  _Verified by:_ `pytest -k test_y` · stage: `make test`\n",
        encoding="utf-8",
    )
    profile = detect.profile(tmp_path)
    findings = rules.evaluate(parse_spec(spec, "harness"), profile)
    assert not [f for f in findings if f.rule == "G003"], [f.message for f in findings]


def test_delta_reads_a_fractional_baseline_floor_and_ignores_booleans() -> None:
    assert delta._baseline_threshold({"threshold": {"value": 85.5}}) == 85.5
    assert delta._baseline_threshold({"threshold": {"value": 90}}) == 90
    assert delta._baseline_threshold({"threshold": {"value": True}}) is None
    assert delta._baseline_threshold({"threshold": None}) is None


# --- BOM tolerance reaches spec parsing too --------------------------------


def test_a_bom_prefixed_spec_keeps_its_first_line_criterion(tmp_path: Path) -> None:
    """``detect_dialect`` and ``parse_spec`` must see the same first line.

    The section grammar is ``^##`` anchored: a BOM ahead of a first-line
    ``## Acceptance Criteria`` heading made the section invisible, so every
    criterion under it vanished and the spec drew a G001 -- while dialect
    detection, already BOM-tolerant, happily classified the same file.
    """
    spec = tmp_path / "spec.md"
    spec.write_bytes(
        b"\xef\xbb\xbf## Acceptance Criteria\n\n"
        b"- [ ] **AC-XY-1:** First. (R-XY-1)\n"
        b"- [ ] **AC-XY-2 (non-success):** Second. (R-XY-1)\n"
    )
    parsed = parse_spec(spec, "harness")
    assert [c.ident for c in parsed.criteria] == ["AC-XY-1", "AC-XY-2"]


# --- byte specimens survive checkout ----------------------------------------


CORPUS = Path(__file__).resolve().parent / "corpus" / "targets"


@pytest.mark.parametrize(
    ("shape", "needle"),
    [
        ("bom-rule-first", b"\xef\xbb\xbf"),
        ("bom-phony-first", b"\xef\xbb\xbf"),
        ("crlf-makefile", b"\r\n"),
    ],
)
def test_byte_specimens_survived_checkout(shape: str, needle: bytes) -> None:
    """``.gitattributes`` marks the corpus ``-text``. If that ever regresses,
    a Windows checkout rewrites these bytes and the shapes silently test
    nothing; fail loudly instead."""
    assert needle in (CORPUS / shape / "repo" / "Makefile").read_bytes()


def test_detection_is_byte_stable_across_hash_seeds() -> None:
    """Card bytes must not depend on the interpreter's hash seed.

    Comparing two in-process calls cannot see set-iteration instability --
    the seed is fixed for the life of the process -- so the second card comes
    from a subprocess started with a different ``PYTHONHASHSEED``.
    """
    script = (
        "import json, sys; from pathlib import Path; from openspec_graph import detect; "
        "print(json.dumps({p.name: detect.profile(p / 'repo').to_card() "
        "for p in sorted(Path(sys.argv[1]).iterdir()) if (p / 'expected.json').is_file()}, "
        "sort_keys=True))"
    )
    outputs = []
    for seed in ("1", "4242"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, "-c", script, str(CORPUS)],
            capture_output=True, text=True, check=True, env=env,
            cwd=Path(__file__).resolve().parent.parent,
        )
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0]), "the subprocess produced no cards"


def test_hard_coded_reads_bullets_and_table_rows_only() -> None:
    """Pins G003's documented scope limit (docs/peer-review-2026-09.md F5).

    Bullets and table rows are scanned; prose, headings and trailing
    `_Verified by:_` lines are not. Recorded as a test so widening it later
    is a decision with a failing assertion attached, rather than drift.
    """
    from openspec_graph.parse_semantics import hard_coded

    assert hard_coded("- **THEN** branch coverage is at least 97%")
    assert hard_coded("| Gate | 97% |")

    # Not scanned -- the documented limit.
    assert hard_coded("_Verified by: `make regression`, coverage floor 97%_") == ()
    assert hard_coded("The suite must hold branch coverage at 97% or better.") == ()
    assert hard_coded("## Coverage at 97%") == ()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are a POSIX feature")
def test_a_fifo_where_a_spec_file_belongs_does_not_hang(tmp_path: Path) -> None:
    """The same hazard at the paths that read the most files.

    The guard above covered `Makefile` and `pyproject.toml`; the two *spec*
    read sites bypassed `read_text_or_none` with their own `read_text()`, so
    a FIFO named `spec.md` blocked forever. `detect` hangs first, and every
    verb calls `profile()`, so this took the whole CLI down on a tree it was
    merely pointed at — the one failure a "safe to point at an unfamiliar
    repository" promise cannot survive.
    """
    (tmp_path / "Makefile").write_text("test:\n\t@echo t\n", encoding="utf-8")
    feature = tmp_path / "specs" / "001-x"
    feature.mkdir(parents=True)
    os.mkfifo(feature / "spec.md")

    profile = detect.profile(tmp_path)  # would block here before the fix
    assert profile.speckit_root is None


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are a POSIX feature")
def test_a_fifo_spec_raises_spec_read_error_rather_than_blocking(tmp_path: Path) -> None:
    """`parse_spec` owes a `SpecReadError`, not `None`.

    Exit 2 ("this repository could not be inspected") has to stay
    distinguishable from exit 1 ("its specs have findings"), so the precheck
    raises rather than skipping. A directory, socket or device node lands on
    the same branch, and "not a regular file" is the honest reason for all.
    """
    from openspec_graph.parse import SpecReadError, parse_spec

    target = tmp_path / "spec.md"
    os.mkfifo(target)
    with pytest.raises(SpecReadError) as excinfo:
        parse_spec(target, "auto")  # would block here before the fix
    assert "not a regular file" in str(excinfo.value)


# --- SC_DECL: the twin of the FR_DECL defect -------------------------------


def test_sc_and_fr_declarations_share_one_grammar() -> None:
    """Built from `_bullet_decl`, so a fix cannot land on one and miss the other.

    It already did once: `FR_DECL` was line-anchored and `SC_DECL`, four lines
    below, kept the cross-line body — `- **SC-001**:` swallowed the whole of
    the next bullet's line and that criterion left the graph, invisible to
    every rule (S005 keys on FR bullets only).
    """
    from openspec_graph.parse_semantics import FR_DECL, SC_DECL

    for pattern, prefix in ((FR_DECL, "FR"), (SC_DECL, "SC")):
        doc = f"- **{prefix}-001**:\n- **{prefix}-002**: a real body\n"
        assert [(m.group(1), m.group(2)) for m in pattern.finditer(doc)] == [
            (f"{prefix}-001", ""),
            (f"{prefix}-002", "a real body"),
        ], prefix
        # And the leading hyphen may not cross a newline either.
        assert pattern.search(f"-\n**{prefix}-001**: x") is None, prefix


# --- hard_coded: blank the real span, not the first identical one ----------


def test_speckit_exemption_blanks_the_success_criteria_span_not_a_twin() -> None:
    """`text.index(body)` found the FIRST occurrence of the body text.

    When an earlier section's body was byte-identical, the wrong region was
    blanked: the exemption silently failed and a legitimate bare percentage in
    a Success Criterion became a false G003 ERROR — failing a clean repository
    on the one construct the exemption exists to permit.
    """
    from openspec_graph.parse_semantics import hard_coded

    body = "- **SC-001**: 95% of new users complete onboarding.\n"
    doc = "# F\n\n## Notes\n\n" + body + "\n## Success Criteria *(mandatory)*\n\n" + body

    offenders = hard_coded(doc, "speckit")
    # Exactly one: the copy under `## Notes`, which is not exempt. The copy
    # under Success Criteria is. Before the fix the exempted span was the
    # `## Notes` one, so the Success Criteria copy was reported instead.
    assert len(offenders) == 1, offenders
