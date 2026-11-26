# Project template - task runner. `make help` lists every target.
# The day cycle targets (day-start, smoke-test) implement
# docs/protocol.md; the quality targets implement ADR-0004.

UV := uv
PYTHON := $(UV) run python
CONSOLE_SCRIPT := $(UV) run notify
DAY_TAG := daily-$(shell date +%F)

.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck imports test check security build \
        english-only day-start smoke-test mutate notify review merge-pr \
        probe-merge night clean

help: ## List available targets with their description.
	@grep --extended-regexp '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install: ## Install the environment and the pre-commit hooks.
	$(UV) sync --locked
	$(UV) run pre-commit install --hook-type pre-commit --hook-type commit-msg

lint: ## Lint every file (Ruff, ADR-0002/0004).
	$(UV) run ruff check .

format: ## Format every file in place (Ruff).
	$(UV) run ruff format .

english-only: ## Fail on French artifacts over the repository (ADR-0008 G4/N4).
	$(PYTHON) -m scripts english-only

typecheck: ## Run the reference type checker (mypy strict, ADR-0003).
	$(UV) run mypy tools/notify/src tools/notify/tests scripts

imports: ## Verify the onion layer contract (import-linter, ADR-0002).
	$(UV) run lint-imports

test: ## Run the full test suite with the coverage floor (ADR-0004).
	$(UV) run pytest

check: english-only lint typecheck imports test ## Full quality gate: run before reporting work.

security: ## Secret scan of the whole history (gitleaks, ADR-0004).
	gitleaks git --no-banner --redact .

build: ## Build the wheel and the sdist (ADR-0001).
	$(UV) build

day-start: ## Tag the morning restore point on `daily` (docs/protocol.md).
	git tag "$(DAY_TAG)"

smoke-test: ## Verify the notification pipeline via console delivery.
	$(CONSOLE_SCRIPT) smoke

mutate: ## Run mutation testing (ADR-0004; EOD on daily).
	$(UV) run mutmut run

notify: ## Notify the owner: make notify severity=... message=... [issue-identifier=...]
	$(CONSOLE_SCRIPT) send \
		--severity "$(severity)" \
		--message "$(message)" \
		--issue-identifier "$(issue_identifier)"

review: ## Run the per-commit review of pull request PR=N (ADR-0006).
	$(PYTHON) -m scripts review --pr-number $(PR)

merge-pr: ## Merge pull request PR=N into daily after review and CI (ADR-0005).
	$(PYTHON) -m scripts merge-pr --pr-number $(PR)

probe-merge: ## Replay this branch onto BASE=origin/daily, probe each commit (ADR-0008 N5/H5).
	$(PYTHON) -m scripts probe-merge --base-ref "$(BASE)"

night: ## Run the unattended loop: ISSUES="12,13,14", MILESTONES="3,4", or auto-discovery when empty (ADR-0007).
	$(PYTHON) -m scripts night --issues "$(ISSUES)" --milestones "$(MILESTONES)"

clean: ## Remove caches, build outputs and mutation cache.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .mutmut-cache htmlcov \
		build dist .coverage coverage.xml .review
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
