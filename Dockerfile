# Optional reproducible runner for `planlint`. Not required for local dev —
# `pip install planlint` (or `pip install -e ".[dev]"` for a checkout) is the
# primary path. This image is not built in CI, so a pyproject change can break
# it silently; `tests/test_agent_artifacts.py` pins the COPY set it depends on,
# and `tests/test_workflow_hardening.py` holds the base tag equal to the
# workflows' PYTHON_DEFAULT -- the one interpreter version this repository
# names, for CI sandboxes that want a hermetic, dependency-free CLI invocation.
# Build:  docker build -t planlint .
# Run:    docker run --rm -v "$PWD":/repo planlint --target /repo validate
#
# The image runs as a non-root user (USER below), so against a host-owned
# bind mount it can read the tree but not write into it. `detect`,
# `validate`, `rules`, `graph`, `waivers`, `delta` and `report` only read;
# `init`, `new` and `witness` write into the target, so run those as the
# mount's owner:
#         docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/repo planlint --target /repo witness ...

# The digest is the pin; the tag stays inside the reference for readers and
# for Dependabot's docker ecosystem, which moves tag and digest together. (A
# Dockerfile has no trailing comments: a `#` after FROM would be an argument.)
FROM python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f

WORKDIR /app

# Install the package and its runtime deps only (no dev extras in the image).
# README.md is required by pyproject's `readme`. LICENSE is copied ahead of
# need: the PEP 639 migration tracked in docs/next-steps.md adds a
# `license-files` glob, which would fail this image build while the repo
# build stayed green -- a coupling that is cheap to pre-empt and easy to miss.
COPY pyproject.toml README.md LICENSE ./
COPY openspec_graph ./openspec_graph
RUN pip install --no-cache-dir .

# Nothing the entrypoint does needs root: the gate verbs read the tree, and
# the three verbs that write into it run as the mount's owner via `--user`
# (header). The install above still runs as root; only what follows is
# unprivileged -- a system user with a fixed uid and no home directory.
RUN useradd --system --uid 10001 --no-create-home planlint
USER planlint

WORKDIR /repo
ENTRYPOINT ["planlint"]
