# marketing-engineer-tools - dev tasks.
#
# PRIVATE is the upstream repo that mirrored files come from. It is never a
# dependency of this repo at runtime; only `promote` reads it.
PRIVATE ?= $(HOME)/Documents/Brand-OS
PY      ?= python3

.PHONY: help install test lint leak mirror check promote clean

help:
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | expand -t22

install:  ## editable install of every package + test deps
	$(PY) -m pip install -e packages/robot-check -e packages/llm-cost -e packages/editor-rules pytest ruff

test:  ## run every package's tests
	$(PY) -m pytest packages/*/tests -q

lint:  ## ruff
	$(PY) -m ruff check packages tools

leak:  ## scan the whole repo for credentials, identifiers, and client refs
	$(PY) tools/check_brand_leak.py

mirror:  ## verify mirrored files match their recorded hashes
	@shasum -a 256 -c packages/robot-check/VENDORED.sha256 \
		|| (echo ""; echo "  A mirrored file was edited directly."; \
		    echo "  Mirrored files come from a private upstream. See CONTRIBUTING.md."; \
		    echo "  Apply the change upstream, then: make promote"; exit 1)

check: lint test leak mirror  ## everything CI runs

promote:  ## pull mirrored files from the private upstream (never commits)
	$(PY) tools/promote.py --private $(PRIVATE)

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache dist build
