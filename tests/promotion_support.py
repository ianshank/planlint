"""Helpers shared by the ``tools/check_promotion.py`` test modules -- read, never assert.

The pattern of ``tests/graft_support.py``: a module pytest does not collect,
holding what more than one collected module uses, so no collected module
imports another (``shape-the-test-suite`` R-TSS-2). The planted topology uses
role names deliberately unlike this repository's (``trunk``/``staging``/
``live``), so a branch name hard-coded in the tool fails a test rather than
passing by coincidence.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import ModuleType

from tests.support import load_tool

TOOL = "check_promotion.py"

#: Role names unlike this repository's, so a literal in the tool cannot pass.
ROLES = {
    "integration_branch": "trunk",
    "candidate_branch": "staging",
    "production_branch": "live",
    "hotfix_prefix": "urgent/",
}


def promotion_tool() -> ModuleType:
    """``tools/check_promotion.py``, loaded in-process (coverage sees it)."""
    return load_tool("check_promotion", TOOL)


def write_promotion_pyproject(tmp_path: Path, roles: dict[str, str] | None = None, *, extra: str = "") -> Path:
    """A ``pyproject.toml`` with a decoy table, then the promotion table, then ``extra``."""
    body = "\n".join(f'{key} = "{value}"  # role' for key, value in (roles or ROLES).items())
    path = tmp_path / "pyproject.toml"
    path.write_text(
        f'[tool.other]\nproduction_branch = "decoy"\n\n[tool.specgraph.promotion]\n{body}\n{extra}',
        encoding="utf-8",
    )
    return path


def needs(**results: str) -> dict[str, dict[str, object]]:
    """A ``toJSON(needs)`` shape: ``release_tier="skipped"`` -> ``{"release-tier": {...}}``."""
    return {job.replace("_", "-"): {"result": result, "outputs": {}} for job, result in results.items()}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout.strip()
