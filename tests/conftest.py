"""Shared pytest fixtures.

Deliberately minimal: this repository keeps tailored fixtures inline in the
module that uses them (see ``tests/support.py``'s note), so only genuinely
cross-cutting state belongs here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from openspec_graph import cli
from tests.graft_support import CONTRACT, MAKEFILE, PYPROJECT


@pytest.fixture(autouse=True)
def _reset_version_cache() -> None:
    """Drop the memoized package-version lookup around every test.

    ``cli._package_version`` is cached so that one CLI run performs one
    metadata lookup and therefore prints at most one ambiguous-environment
    warning (R-FE-8) — argparse resolves it when the parser is built, and
    ``cmd_validate`` needs the same value again for the findings envelope's
    ``tool_version``.

    In-process tests that patch ``importlib.metadata`` would otherwise read a
    value memoized by whichever test ran first, making them pass or fail on
    execution order. Clearing on both sides means no test inherits another's
    resolved version, and none leaks its own.
    """
    cli._package_version.cache_clear()
    yield
    cli._package_version.cache_clear()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A minimal target repository: a Makefile, a pyproject, and a contract.

    Here rather than in `tests/graft_support.py` beside the constants it is
    built from, because importing a fixture *by name* makes it collide with
    every test's own `repo` parameter -- one shared fixture, 163 ruff F811
    reports. A conftest fixture is shared without the importer naming it,
    which is the mechanism pytest provides for exactly this.

    `tests/test_ci_hardening.py` defines its own `repo` with different
    contents. That is not a conflict: pytest resolves a fixture defined in a
    test module ahead of a conftest one, so its definition still wins there.
    """
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    (tmp_path / "CONTRACT.md").write_text(CONTRACT)
    return tmp_path
