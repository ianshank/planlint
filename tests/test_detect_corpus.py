"""Labelled target-repository corpus for ``detect`` (CP-TC).

``detect`` is the load-bearing primitive: G003's threshold locator, G004's
make-target existence, G005's invariant source and H001's runnable stage are
each only as correct as the dialect card underneath them. Until this module
existed, that card had been validated against two real repositories and a
handful of inline fixtures -- a probe over twenty synthetic shapes then found
five wrong detections and two crashes, one of which produced a *false* G004
against a valid repository.

Each shape under ``tests/corpus/targets/`` carries a hand-written partial card
stating what a correct detector should report. ``dialect_card.diff_cards()``
ignores fields absent from the baseline, so a shape asserts only the dimension
it is about and an additive schema change does not churn every fixture.

See ``tests/corpus/targets/README.md`` for the shape table and the rationale
behind each expectation.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import pytest

from openspec_graph import detect, dialect_card, machinery
from tests import support

CORPUS_ROOT = Path(__file__).resolve().parent / "corpus" / "targets"
CORPUS_README = CORPUS_ROOT / "README.md"

# The placeholder the hostile specimen carries in place of a real path, so a
# committed fixture can name a directory that only exists during the test.
CANARY_PLACEHOLDER = "@@CANARY@@"

# Every side effect the hostile Makefile would produce if anything ever
# executed it. GNU Make fires all three at parse time -- even under `make -n`
# -- which is exactly why planlint must never shell out to it.
HOSTILE_ARTIFACTS = ("shell-touched.txt", "eval-touched.txt", "recipe-touched.txt")


def _shapes() -> list[Path]:
    """Every corpus shape, defined positively as "a directory carrying an
    expectation" rather than as "not one of these names" -- the same argument
    ``tests/test_agent_artifacts.py`` makes about eval cases, so a future
    sibling directory (notes, tooling) cannot silently become a failing shape.
    """
    return sorted(p for p in CORPUS_ROOT.iterdir() if (p / "expected.json").is_file())


SHAPES = _shapes()


def _card_for(repo: Path) -> dict[str, object]:
    return detect.profile(repo).to_card()


def _expected_for(shape: Path) -> dict[str, object]:
    """The shape's partial card, with the live schema version injected.

    Injected rather than committed: pinning the version in thirteen fixtures
    would turn an additive schema bump into thirteen unrelated diffs, while
    ``test_corpus_pins_the_card_schema_version`` keeps the version itself
    under a single, deliberate assertion.
    """
    expected = json.loads((shape / "expected.json").read_text(encoding="utf-8"))
    expected["schema_version"] = dialect_card.SCHEMA_VERSION
    return expected


# --- the corpus itself ------------------------------------------------------


def test_corpus_is_not_empty() -> None:
    """A silently-empty corpus would make every parametrised test below vacuous."""
    assert SHAPES, f"no corpus shapes found under {CORPUS_ROOT}"


@pytest.mark.parametrize("shape", SHAPES, ids=lambda p: p.name)
def test_detected_card_matches_the_labelled_expectation(shape: Path) -> None:
    """The heart of the corpus: detection must agree with the label."""
    drift = dialect_card.diff_cards(_expected_for(shape), _card_for(shape / "repo"))
    assert not drift, f"{shape.name}: detection disagrees with its label:\n  " + "\n  ".join(drift)


@pytest.mark.parametrize("shape", SHAPES, ids=lambda p: p.name)
def test_every_shape_is_documented(shape: Path) -> None:
    """Referential integrity between the corpus and its README.

    An undocumented shape is a fixture whose intent lives only in whoever
    wrote it; the same argument ``test_agent_skill_docs.py`` makes for prose
    that an external reader acts on.
    """
    assert f"`{shape.name}`" in CORPUS_README.read_text(encoding="utf-8"), (
        f"{shape.name} is not described in {CORPUS_README.name}'s shape table"
    )


def test_corpus_pins_the_card_schema_version() -> None:
    """One deliberate place to notice a schema bump, instead of thirteen.

    A bump is legitimate; it must simply be reviewed against the corpus rather
    than absorbed silently by fixtures that each carried their own copy.
    """
    assert dialect_card.SCHEMA_VERSION == 1


# --- the safety invariant ---------------------------------------------------


def test_parsing_a_hostile_makefile_executes_nothing(tmp_path: Path) -> None:
    """R-MP-2/DEC-MP-001, as behaviour rather than as an import guard.

    ``tests/test_decomposition.py`` proves ``machinery`` never *imports*
    subprocess and ``tests/test_machinery.py`` proves it never *calls* a
    patched one. Neither would notice a future reader that shelled out from
    somewhere else in ``detect``. This runs the real CLI path over a Makefile
    whose ``$(shell ...)`` calls would delete a directory, and checks the
    directory afterwards.
    """
    repo = tmp_path / "repo"
    shutil.copytree(CORPUS_ROOT / "hostile-makefile" / "repo", repo)

    canary = tmp_path / "canary"
    canary.mkdir()
    (canary / "keep.txt").write_text("must survive", encoding="utf-8")

    makefile = repo / "Makefile"
    source = makefile.read_text(encoding="utf-8")
    assert CANARY_PLACEHOLDER in source, "the hostile specimen lost its canary placeholder"
    makefile.write_text(source.replace(CANARY_PLACEHOLDER, canary.as_posix()), encoding="utf-8")

    profile = detect.profile(repo)

    assert (canary / "keep.txt").is_file(), "$(shell rm -rf ...) ran: the canary was deleted"
    for artifact in HOSTILE_ARTIFACTS:
        assert not (canary / artifact).exists(), f"{artifact} was created: the Makefile executed"
    # Detection still did its actual job on the file it refused to run.
    assert profile.make_targets == ("all", "build", "test")


# --- shapes that cannot be committed as files -------------------------------


@pytest.mark.parametrize("name", ["Makefile", "pyproject.toml"])
def test_a_directory_where_a_config_file_belongs_does_not_crash(
    tmp_path: Path, name: str
) -> None:
    """Regression: ``IsADirectoryError`` escaped ``detect.profile()``.

    ``exists()`` is true for a directory, so the subsequent ``read_text()``
    raised and every CLI verb died with a traceback and exit 1 -- the code
    reserved for "findings were reported" -- against a repository planlint was
    only inspecting. Cannot be a committed fixture: git stores no empty
    directories.
    """
    (tmp_path / name).mkdir()
    profile = detect.profile(tmp_path)
    assert profile.make_targets == ()
    assert profile.threshold is None


def test_an_unreadable_config_file_is_treated_as_absent(tmp_path: Path) -> None:
    """The same posture for the other unreadable cases: absent, never fatal."""
    (tmp_path / "CONTRACT.md").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ADR.md").mkdir()
    profile = detect.profile(tmp_path)
    assert profile.invariant_ids == ()
    assert profile.adr_ids == ()


def test_a_large_makefile_parses_in_linear_time(tmp_path: Path) -> None:
    """A guard against a pathological (catastrophically backtracking) parser.

    The bound is deliberately loose -- this asserts "not quadratic", not a
    performance budget, so it cannot flake on a slow shared runner.
    """
    count = 20_000
    body = "".join(f"target-{i}:\n\t@echo {i}\n" for i in range(count))
    (tmp_path / "Makefile").write_text(body, encoding="utf-8")

    started = time.monotonic()
    profile = detect.profile(tmp_path)
    elapsed = time.monotonic() - started

    assert len(profile.make_targets) == count
    assert elapsed < 30.0, f"parsing {count} targets took {elapsed:.1f}s; suspect backtracking"


# --- the BOM defect, at the unit level --------------------------------------


def test_strip_bom_is_idempotent_and_leaves_other_text_alone() -> None:
    assert machinery.strip_bom("﻿all:") == "all:"
    assert machinery.strip_bom(machinery.strip_bom("﻿﻿all:")) == "all:"
    assert machinery.strip_bom("all:") == "all:"
    # U+FEFF elsewhere in the text is not a byte-order mark and is left alone.
    assert machinery.strip_bom("a﻿b") == "a﻿b"


def test_both_makefile_parsers_agree_on_a_bom_prefixed_file() -> None:
    """The structural parser and the legacy regex fallback failed differently
    on a BOM -- one fabricated a mangled target, the other silently dropped
    the first one. They must not diverge here any more than on define blocks.
    """
    text = "﻿all: build\n\t@echo a\nbuild:\n\t@echo b\n"
    assert machinery.parse_makefile(text).targets == ("all", "build")
    assert detect._legacy_make_targets(text) == ("all", "build")


# --- makefile filename resolution (GNU Make's own search order) -------------


def test_makefile_names_are_gnu_makes_own_search_order() -> None:
    """The order is the contract, not an implementation detail.

    GNU Make reads the first of these that exists and never opens the rest,
    so a list in any other order would describe a different build.
    """
    assert detect.MAKEFILE_NAMES == ("GNUmakefile", "makefile", "Makefile")


def test_no_makefile_at_all_resolves_to_none(tmp_path: Path) -> None:
    assert detect._resolve_makefile(tmp_path) is None
    assert detect.profile(tmp_path).make_targets == ()


@pytest.mark.parametrize("name", ["GNUmakefile", "makefile", "Makefile"])
def test_each_honoured_name_is_read(tmp_path: Path, name: str) -> None:
    """Regression for the fail-open: a repo using any name GNU Make honours
    must yield targets, or G004's empty-guard silently disables the rule and
    a broken `make` citation passes clean.
    """
    (tmp_path / name).write_text("build:\n\t@echo b\n", encoding="utf-8")
    assert detect.profile(tmp_path).make_targets == ("build",)


def test_gnumakefile_shadows_makefile_rather_than_merging(tmp_path: Path) -> None:
    """Both present: GNU Make reads GNUmakefile and never opens Makefile.

    Reporting the union would describe a build that does not happen -- the
    shadowed file's targets are not runnable via `make <target>`.
    """
    (tmp_path / "GNUmakefile").write_text("gnu-only:\n\t@echo g\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("makefile-only:\n\t@echo m\n", encoding="utf-8")
    assert detect.profile(tmp_path).make_targets == ("gnu-only",)


@pytest.mark.skipif(
    not support.supports_case_sensitive_filenames(),
    reason="case-insensitive filesystem: `makefile` and `Makefile` are one path",
)
def test_lowercase_makefile_shadows_capitalised_makefile(tmp_path: Path) -> None:
    """`makefile` precedes `Makefile` in GNU Make's order.

    Not a committed corpus shape: the two names are the same path on a
    case-insensitive filesystem, so the fixture could not be checked out on
    macOS at all. Generated here instead, behind a capability probe rather
    than a sys.platform guess.
    """
    (tmp_path / "makefile").write_text("lower-only:\n\t@echo l\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("upper-only:\n\t@echo u\n", encoding="utf-8")
    assert detect.profile(tmp_path).make_targets == ("lower-only",)


def test_an_unreadable_candidate_is_terminal_not_a_fall_through(tmp_path: Path) -> None:
    """GNU Make parity: it aborts on an unopenable makefile, it does not skip it.

    An earlier revision fell through to the next name, on the argument that
    planlint never executes what it reads so more detection is safer. That was
    wrong, and the adversarial review of the change package caught it: real
    `make` here prints "GNUmakefile: Is a directory.  Stop." and runs nothing,
    so reporting `Makefile`'s targets green-lights a citation that cannot run
    in this repository -- a confident lie, strictly worse than silence. The
    silence is covered: G010 raises an INFO saying the citations were not
    checked.
    """
    (tmp_path / "GNUmakefile").mkdir()
    (tmp_path / "Makefile").write_text("build:\n\t@echo b\n", encoding="utf-8")
    assert detect.profile(tmp_path).make_targets == ()


def test_an_empty_candidate_does_shadow(tmp_path: Path) -> None:
    """Readable-but-empty is NOT the same as unreadable.

    A zero-byte `GNUmakefile` genuinely declares no rules, so `make build`
    would fail and reporting no targets is correct. The resolver's test must
    therefore be ``is None``, never falsiness -- `""` is a successful read.
    """
    (tmp_path / "GNUmakefile").write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text("build:\n\t@echo b\n", encoding="utf-8")
    assert detect.profile(tmp_path).make_targets == ()


def test_makefile_names_are_not_duplicated_as_inline_literals() -> None:
    """The constant must be the single source, not decoration beside literals.

    Guards the regression where someone re-adds `root / "Makefile"` at a call
    site and the other two names quietly stop being honoured again.
    """
    import ast

    source = Path(detect.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    lowered = {n.lower() for n in detect.MAKEFILE_NAMES}
    for func in ast.walk(tree):
        if not isinstance(func, ast.FunctionDef):
            continue
        offenders = [
            node.value
            for node in ast.walk(func)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.lower() in lowered
        ]
        assert not offenders, (
            f"{func.name}() hard-codes {offenders}; use detect.MAKEFILE_NAMES"
        )


@pytest.mark.skipif(not support.supports_symlinks(), reason="cannot create symlinks here")
def test_a_dangling_symlink_candidate_is_terminal_not_absent(tmp_path: Path) -> None:
    """`Path.exists()` follows symlinks, so a broken link reads as absent.

    That made the resolver fall through to a lower-precedence name, which is
    the same fail-open again: `make` stops with "GNUmakefile: No such file or
    directory" and runs nothing, so reporting the `Makefile`'s targets would
    green-light a citation that cannot run. `lstat()` asks whether the
    directory ENTRY is there, which is the question actually being asked.
    """
    (tmp_path / "GNUmakefile").symlink_to(tmp_path / "nonexistent-target")
    (tmp_path / "Makefile").write_text("build:\n\t@echo b\n", encoding="utf-8")
    assert not (tmp_path / "GNUmakefile").exists()  # the trap, made explicit
    assert (tmp_path / "GNUmakefile").is_symlink()
    assert detect.profile(tmp_path).make_targets == ()
