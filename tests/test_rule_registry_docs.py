"""Guards every prose claim about the rule registry's count or per-family id
ranges against ``rules.RULES`` itself -- the real source of truth.

Added by CP-AD after the third independent recurrence of the same drift
class in this codebase's history (``docs/architecture/c4.md`` twice, then
``rules.py``'s own module docstring): a single test, not a new tool or
Makefile target, per ``fix-adopter-artifact-drift``'s own pre-authorized
"cheapest form" once recurrence is demonstrated (DEC-AD-006).

``CHANGELOG.md`` is deliberately excluded -- its dated entries are historical
record, correct when written; a changelog is supposed to diverge from the
live count over time, and guarding it would fight its own purpose.

Pure: reads ``rules.RULES`` and doc files as plain text, no CLI/subprocess
needed (mirrors ``test_dialect_card.py``'s style).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from openspec_graph.rules import RULES, rule_table

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent

_FAMILIES = (
    ("G", "rules_generic"),
    ("H", "rules_harness"),
    ("U", "rules_upstream"),
    ("W", "rules_witness"),
    ("S", "rules_speckit"),
)


def _family_range(prefix: str) -> tuple[str, str]:
    idents = sorted(r.ident for r in RULES if r.ident.startswith(prefix))
    return idents[0], idents[-1]


def test_readme_rules_table_matches_rules_exactly() -> None:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    found = dict(
        re.findall(
            r"^\| (G\d{3}|H\d{3}|U\d{3}|W\d{3}|S\d{3}) \| (ERROR|WARN|INFO) \|",
            text,
            re.MULTILINE,
        )
    )
    expected = {r.ident: r.severity for r in RULES}
    assert found == expected, (
        f"README.md's rules table is out of sync with rules.RULES.\n"
        f"missing/extra: {set(expected) ^ set(found)}\n"
        f"severity mismatches: {[k for k in expected if k in found and expected[k] != found[k]]}"
    )


def test_total_rule_count_matches_every_prose_claim() -> None:
    total = len(RULES)
    claims = [
        ("docs/architecture/c4.md", r"(\d+)\s+deterministic rules"),
        ("docs/agents-skills-harness.md", r"The (\d+) rules"),
        ("docs/next-steps.md", r"the (\d+) rules"),
        ("docs/differentiation-roadmap.md", r"(\d+)\s+rules total"),
    ]
    for doc, pattern in claims:
        text = (REPO_ROOT / doc).read_text(encoding="utf-8")
        matches = re.findall(pattern, text)
        assert matches, f"{doc}: no rule-count claim found matching {pattern!r}"
        for m in matches:
            assert int(m) == total, f"{doc} claims {m} rules; rules.RULES actually has {total}"


def test_rules_py_docstring_family_ranges_match_rules() -> None:
    text = (REPO_ROOT / "openspec_graph" / "rules.py").read_text(encoding="utf-8")
    for prefix, module in _FAMILIES:
        low, high = _family_range(prefix)
        assert f"{low}-{high}" in text, (
            f"rules.py's own module docstring doesn't claim {module} covers {low}-{high} "
            f"(the exact drift this test exists to catch)"
        )


def test_c4_module_map_family_ranges_match_rules() -> None:
    text = (REPO_ROOT / "docs" / "architecture" / "c4.md").read_text(encoding="utf-8")
    for prefix, module in _FAMILIES:
        low, high = _family_range(prefix)
        # c4.md's module map is a Mermaid diagram (a caption below it states
        # each family's range) -- tolerate an en dash or hyphen, and any
        # short run of markup/whitespace between the filename and the range
        # rather than requiring the old ASCII tree's "# " comment style.
        # RUF001: the en dash is deliberate -- c4.md writes its line ranges
        # with one, and this character class accepts either spelling.
        pattern = rf"{module}\.py.{{0,40}}?{re.escape(low)}[–-]{re.escape(high)}"  # noqa: RUF001
        assert re.search(pattern, text, re.DOTALL), (
            f"c4.md's module map doesn't claim {module}.py covers {low}-{high}"
        )


# --- AC-CH-8 / C-CH-1: the rule set matches the committed baseline -----------
# A future change that adds or removes a rule without updating the baseline
# fails this test — forcing the change to be a conscious decision (C-CH-1).


def test_rule_set_matches_baseline() -> None:
    baseline_path = REPO_ROOT / "tests" / "baseline_rules.json"
    assert baseline_path.exists(), "baseline_rules.json must be committed"
    baseline = json.loads(baseline_path.read_text())
    live = rule_table()
    assert live == baseline, (
        "the rule set changed; if this is intentional, regenerate "
        "tests/baseline_rules.json with `planlint rules --json > tests/baseline_rules.json`"
    )
    # sanity: the baseline is non-empty and covers the rules we rely on
    assert len(baseline) == len(RULES)


# Moved from tests/test_graft_rules.py by shape-the-test-suite (R-TSS-1): the
# one test there that reads the tree, beside the other baseline guard, so that
# module stays one tier and inside the line bound.
def test_rule_registry_baseline_is_unchanged() -> None:
    """AC-UG-8: no rule id added, no finding emitted for an omitted GIVEN."""

    baseline = json.loads(
        (Path(__file__).resolve().parent / "baseline_rules.json").read_text(encoding="utf-8")
    )
    assert {r["id"] for r in baseline} == {r.ident for r in RULES}
    assert len(baseline) == len(RULES)
