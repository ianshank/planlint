.PHONY: help test coverage-tools lint typecheck security validate graph graph-mermaid e2e-live ci pre-pr docs-check thresholds matcher-accuracy wheel-check skill-catalog skill-manifests skill-artifacts clean

# pytest-cov's own --cov-fail-under is disabled for `coverage-tools` so the
# two scoped checkers below are the single gate on that run -- they read the
# real floors from pyproject.toml, which is where rule G003 says a threshold
# belongs. Spelled as a variable rather than a literal because a bare 0 in a
# recipe is indistinguishable, to `tools/check_no_hardcoded_thresholds.py`,
# from the pinned floor that guard exists to reject.
NO_FLOOR := 0

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'

test: ## Run the test suite; line + branch coverage floors read from pyproject.toml
	@# Erase first: [tool.coverage.run] parallel = true means coverage COMBINES
	@# every .coverage.* it finds, so data left by an ad-hoc run (a different
	@# --cov= source, an interrupted run) silently merges into this one. It can
	@# raise the number as easily as lower it, and a gate that can be talked up
	@# by a stale file in the working tree is not a gate.
	python -m coverage erase
	python -m pytest tests/ --cov=openspec_graph --cov-branch \
		--cov-report=term-missing --cov-report=json:coverage.json -q
	python tools/check_coverage_floor.py coverage.json
	python tools/check_branch_coverage.py coverage.json

coverage-tools: ## Coverage floors for the tools/ gate scripts themselves
	@# A separate run from `test`, not a second --cov= on it: pytest-cov's own
	@# --cov-fail-under applies to the combined total of everything measured,
	@# so folding tools/ into that run would replace two honest per-tree
	@# numbers with one diluted one -- and the diluted one is what the gate
	@# would then enforce. The floors come from [tool.specgraph]
	@# tools_*_fail_under via the same two checkers, under --scope.
	python -m coverage erase
	python -m pytest tests/ --cov=tools --cov-branch --cov-fail-under=$(NO_FLOOR) \
		--cov-report=json:coverage-tools.json -q
	python tools/check_coverage_floor.py coverage-tools.json --scope tools
	python tools/check_branch_coverage.py coverage-tools.json --scope tools

lint: ## Ruff check across the package, tests, and tools — a hard gate
	python -m ruff check openspec_graph tests tools

typecheck: ## mypy with config from pyproject.toml — a hard gate
	python -m mypy openspec_graph tools

security: ## Secret scan (gitleaks if installed, deterministic fallback otherwise)
	python tools/check_secrets.py

validate: ## Validate this repo's own OpenSpec change packages with planlint
	planlint --target . validate --fail-on ERROR

graph: ## Emit the spec dependency graph as JSON
	planlint --target . graph --format json

graph-mermaid: ## Emit the spec dependency graph as a Mermaid flowchart
	planlint --target . graph --format mermaid

# The no-mocks e2e track: the installed CLI against this live repo, once
# normally and once under an ASCII-only console (the Defect D repro
# environment). The env-prefix line is POSIX shell syntax -- on Windows run
# it under Git Bash, or set the variable for the whole shell instead.
e2e-live: ## Live self-validation of the installed CLI against this repo
	planlint --target . detect
	planlint --target . validate --fail-on ERROR
	planlint --target . graph --format json
	planlint --target . waivers
	PYTHONIOENCODING=ascii planlint --target . validate --fail-on ERROR

ci: test lint validate ## The authoritative local core gate
	@echo "ci: core gates passed"

pre-pr: ci typecheck security docs-check thresholds coverage-tools ## The full enterprise AQA gate before opening a PR
	@echo "pre-pr: all enterprise gates passed"

docs-check: ## Confirm required docs exist and are linked from README
	python tools/check_docs.py

thresholds: ## Confirm no hard-coded thresholds in the Makefile or workflow YAML
	python tools/check_no_hardcoded_thresholds.py

matcher-accuracy: ## Report G002/U004 precision + recall per pattern; floors read from pyproject.toml
	python tools/matcher_accuracy.py --check --patterns

wheel-check: ## Build the wheel and confirm it carries its declared SPDX licence
	python -m build --wheel --outdir dist
	python tools/check_wheel_metadata.py dist

skill-catalog: ## Regenerate the distributable skill's rule catalog from the registry
	python tools/render_rule_catalog.py --write

skill-manifests: ## Regenerate .claude-plugin/ manifests from the package version + SKILL.md
	python tools/render_plugin_manifests.py --write

skill-artifacts: skill-catalog skill-manifests ## Regenerate every generated agent-facing artifact
	@echo "skill-artifacts: catalog and manifests regenerated"

clean: ## Remove build, cache, and coverage artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -f coverage.json coverage-tools.json coverage.xml .coverage .coverage.* spec-graph.json spec-findings.json head.json base.json
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
