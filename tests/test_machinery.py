"""CP-3: structural parsers for repository machinery (Makefile, pyproject floor).

These exercise `openspec_graph.machinery` directly with text inputs — no repo
fixture needed. The parsers replace line-regex parsing with structural
tokenization so the coverage floor is read from the correct TOML section and
Makefile targets are recognized without recipe/variable noise.
"""

from __future__ import annotations

from openspec_graph.machinery import parse_makefile, parse_pyproject_fail_under

# --- parse_makefile ----------------------------------------------------------


def test_parse_makefile_multi_target_rule() -> None:
    """`a b c: prereq` defines three targets, not one."""
    mk = "test lint ci:\n\tpytest\n"
    assert set(parse_makefile(mk)) == {"test", "lint", "ci"}


def test_parse_makefile_phony_members() -> None:
    """.PHONY members are invokable targets even without their own rule."""
    mk = ".PHONY: clean dist\n"
    assert set(parse_makefile(mk)) == {"clean", "dist"}


def test_parse_makefile_phony_strips_inline_comment() -> None:
    """An inline comment after .PHONY members is not added as a target."""
    mk = ".PHONY: clean dist # helper targets\n"
    assert set(parse_makefile(mk)) == {"clean", "dist"}
    assert "helper" not in parse_makefile(mk)


def test_parse_makefile_other_dot_targets_ignored() -> None:
    ".SUFFIXES / .DEFAULT_GOAL prereqs are not invokable targets."
    mk = ".SUFFIXES: .out .c\n.DEFAULT_GOAL := real\nreal:\n\t:\n"
    targets = set(parse_makefile(mk))
    assert targets == {"real"}
    assert ".out" not in targets and ".c" not in targets


def test_parse_makefile_ignores_recipe_lines() -> None:
    """A tab-prefixed recipe line containing `make nope` is not a target."""
    mk = "test:\n\tmake nope\n\techo done\n"
    assert "nope" not in parse_makefile(mk)
    assert set(parse_makefile(mk)) == {"test"}


def test_parse_makefile_ignores_variable_assignments() -> None:
    """Variable assignments (`:=`/`=`/`?=`/`+=`) are not targets."""
    mk = "NAME := value\nOTHER ?= fallback\nTHIRD += more\nreal:\n\techo hi\n"
    targets = set(parse_makefile(mk))
    assert "NAME" not in targets
    assert "OTHER" not in targets
    assert "THIRD" not in targets
    assert "real" in targets


def test_parse_makefile_double_colon_rule() -> None:
    """Double-colon rules (`target::`) are real targets."""
    mk = "build::\n\techo build\n"
    assert "build" in parse_makefile(mk)


def test_parse_makefile_ignores_pattern_targets() -> None:
    """Pattern (`%.o:`) and variable (`$(TARGET):`) targets are not invokable."""
    mk = "%.o: %.c\n\tcc -c $<\n$(TARGET): main.o\n\tcc -o $@ $<\nreal:\n\t:\n"
    targets = set(parse_makefile(mk))
    assert "real" in targets
    assert not any(t.startswith("%") for t in targets)
    assert not any("$" in t for t in targets)


def test_parse_makefile_ignores_comments() -> None:
    mk = "# this is not: a target\nreal:\n\t:\n"
    assert set(parse_makefile(mk)) == {"real"}


def test_parse_makefile_returns_sorted_unique() -> None:
    mk = "lint:\n\t:\ntest:\n\t:\nlint:\n\t:\n"
    assert parse_makefile(mk) == ("lint", "test")


# --- parse_pyproject_fail_under ---------------------------------------------


def test_parse_pyproject_reads_correct_section() -> None:
    toml = (
        "[tool.specgraph]\nbranch_fail_under = 80\n"
        "[tool.coverage.report]\nfail_under = 90\n"
    )
    assert parse_pyproject_fail_under(toml) == 90


def test_parse_pyproject_ignores_wrong_section() -> None:
    """`fail_under` in a section other than [tool.coverage.report] is ignored."""
    toml = "[tool.specgraph]\nfail_under = 75\n"
    assert parse_pyproject_fail_under(toml) is None


def test_parse_pyproject_handles_whitespace_and_inline_comment() -> None:
    toml = "[tool.coverage.report]\nfail_under   =   88   # line floor\n"
    assert parse_pyproject_fail_under(toml) == 88


def test_parse_pyproject_returns_none_when_absent() -> None:
    toml = "[tool.ruff]\nline-length = 100\n"
    assert parse_pyproject_fail_under(toml) is None


def test_parse_pyproject_first_match_in_correct_section_wins() -> None:
    """If [tool.coverage.report] appears twice, the first fail_under wins."""
    toml = (
        "[tool.coverage.report]\nfail_under = 92\n"
        "[tool.ruff]\nline-length = 100\n"
        "[tool.coverage.report]\nfail_under = 99\n"
    )
    assert parse_pyproject_fail_under(toml) == 92
