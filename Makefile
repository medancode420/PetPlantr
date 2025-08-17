SHELL := bash
.DEFAULT_GOAL := help

.PHONY: help sdk-doctor sdk-typecheck sdk-list sdk-showconfig test-ai test-ai-verbose
# PetPlantr Mac ↔ GPU Handoff Automation
# Usage: make prep-embeddings && make fine-tune-mvd

TS_VERSION ?= 5.5.4

.PHONY: help prep-embeddings fine-tune-mvd clean tier1-backlog sprint-report issue-seed-enhanced setup-infra deploy-terraform frontend-dev frontend-build frontend-test e2e-test e2e-open qa-full env-setup deploy-vercel dev-setup prod-check health-check verify-setup help \
	openapi/export openapi/lint openapi/size openapi/diff ci/contract ci/full test sdk-typecheck sdk-list sdk-showconfig

# Tier-1 Priority Backlog automation
tier1-backlog:
	@echo "📊 Running Tier-1 Priority Backlog automation..."
	@echo "📂 Checking for notebook artifacts..."
	@if [ ! -f "reports/github_issues_tier1.json" ]; then \
		echo "⚠️  Running notebook to generate artifacts..."; \
		echo "💡 Open VS Code and run all cells in tier1_priority_backlog.ipynb"; \
		echo "💡 Or run: jupyter notebook tier1_priority_backlog.ipynb"; \
		exit 1; \
	fi
	@echo "✅ Artifacts found! Ready to seed GitHub issues."
	@echo ""
	@echo "🚀 Next steps:"
	@echo "  1. Set your GitHub token: export GITHUB_TOKEN=ghp_your_token"
	@echo "  2. Test: python scripts/seed_gh_issues_v2.py --repo USER/REPO --dry-run"
	@echo "  3. Create: python scripts/seed_gh_issues_v2.py --repo USER/REPO"
	@echo ""
	@python scripts/seed_gh_issues_v2.py --repo petplantr/demo --dry-run | head -20

# On MacBook (M3 Max) - Prepare embeddings
prep-embeddings:
	@echo "🍎 Preparing embeddings on M3 Max..."
	python backend/datasets/export_embeddings.py
	aws s3 sync embeddings/ s3://petplantr-dataset/embeddings/
	@echo "✅ Embeddings ready for GPU training"

# On GPU (Modal) - Fine-tune with pre-computed embeddings
fine-tune-mvd:
	@echo "☁️  Launching GPU fine-tune with embeddings..."
	modal run backend/datasets/shape_mvd_training.py \
		--embedding-dir s3://petplantr-dataset/embeddings/ \
		--freeze-clip \
		--batch-size 1 \
		--grad-accum 8 \
		--gpu T4

# Progressive complexity stages
stage-1-unet:
	modal run backend/datasets/train_unet_stage1.py

stage-2-unet:
	modal run backend/datasets/shape_mvd_training.py \
		--embedding-dir s3://petplantr-dataset/embeddings/ \
		--unet-channels 256 \
		--batch-size 1 \
		--enable-ema

stage-3-full:
	modal run backend/datasets/shape_mvd_training.py \
		--embedding-dir s3://petplantr-dataset/embeddings/ \
		--unet-channels 320 \
		--batch-size 4 \
		--gpu A10G

clean:
	rm -rf embeddings/
	rm -rf models/temp_*

# Quick validation
validate:
	python backend/datasets/validate_embeddings.py

# Enhanced Infrastructure and Sprint Management Commands

# Sprint Management
sprint-report:
	@echo "📊 Generating Sprint burndown chart..."
	@python scripts/generate_sprint_report.py || echo "⚠️ Sprint report script not found"

issue-seed-enhanced:
	@echo "🌱 Seeding Enhanced AI Issues (E-4)..."
	@if [ -z "$(GITHUB_TOKEN)" ]; then \
		echo "❌ Please set GITHUB_TOKEN environment variable"; \
		exit 1; \
	fi
	@python scripts/seed_gh_issues_v2.py --repo medancode420/PetPlantr --issues-file reports/github_issues_tier1_enhanced.json --epics E-4

# Infrastructure Setup
setup-infra:
	@echo "🏗️ Setting up PetPlantr infrastructure..."
	@chmod +x setup-infrastructure.sh
	@./setup-infrastructure.sh

deploy-terraform:
	@echo "☁️ Deploying Terraform infrastructure..."
	@cd infra && terraform init && terraform plan && terraform apply

# Frontend Development
frontend-dev:
	@echo "🚀 Starting frontend development server..."
	@cd frontend && npm run dev

frontend-build:
	@echo "🏗️ Building frontend for production..."
	@cd frontend && npm run build

frontend-test:
	@echo "🧪 Running frontend tests..."
	@cd frontend && npm run test

# E2E Testing
e2e-test:
	@echo "🎭 Running end-to-end tests..."
	@cd frontend && npm run cypress:run

e2e-open:
	@echo "🎭 Opening Cypress test runner..."
	@cd frontend && npm run cypress:open

# Quality Assurance
qa-full:
	@echo "🔍 Running full QA suite..."
	@cd frontend && npm run lint
	@cd frontend && npm run type-check
	@cd frontend && npm run test
	@make e2e-test

# Environment Setup
env-setup:
	@echo "⚙️ Setting up environment files..."
	@cp .env.template .env.local 2>/dev/null || echo "No root .env.template found"
	@cp frontend/.env.enhanced frontend/.env.local 2>/dev/null || echo "No frontend .env.enhanced found"
	@echo "✅ Environment files created. Please edit with your actual values."
	@echo "💡 Next steps:"
	@echo "   1. Edit frontend/.env.local with your API keys"
	@echo "   2. Run 'make frontend-dev' to start development"

# Quick deployment
deploy-vercel:
	@echo "🚀 Deploying to Vercel..."
	@cd frontend && vercel deploy --prod

# Development setup for new contributors
dev-setup:
	@echo "🚀 Setting up development environment..."
	@make env-setup
	@cd frontend && npm install
	@echo "✅ Development setup complete!"
	@echo "💡 Next steps:"
	@echo "  1. Edit frontend/.env.local with your API keys"
	@echo "  2. Run 'make frontend-dev' to start development"
	@echo "  3. Run 'make setup-infra' to deploy infrastructure"

# Production readiness check
prod-check:
	@echo "✅ Running production readiness checks..."
	@make frontend-build
	@make frontend-test
	@make qa-full
	@echo "🎉 Production checks complete!"

# Health Check
health-check:
	@echo "🔍 Running infrastructure health check..."
	@python scripts/health_check.py

# Complete setup verification
verify-setup:
	@echo "🎯 Verifying complete setup..."
	@make health-check
	@make frontend-build
	@echo "✅ Setup verification complete!"

help: ## List Make targets
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_\/.\-]+:.*## / {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "Tip: override TS pin -> make sdk-typecheck TS_VERSION=5.6.3"

# -------- k6 Load Test (Option D) --------
K6?=k6
LOAD_JS?=load/k6/petplantr_load.js
REPORT_DIR?=reports
BASE_URL?=http://localhost:8000
DURATION?=10m
BREED_RPS?=5
MESH_RPS?=1
READ_RPS?=0.5
MESH_BULK_RPS?=

.PHONY: load-test
load-test:
	mkdir -p $(REPORT_DIR)
	BASE_URL=$(BASE_URL) DURATION=$(DURATION) \
	BREED_RPS=$(BREED_RPS) MESH_RPS=$(MESH_RPS) READ_RPS=$(READ_RPS) \
	MESH_BULK_RPS=$(MESH_BULK_RPS) \
	$(K6) run $(LOAD_JS)

.PHONY: load-test-docker
load-test-docker:
	mkdir -p $(REPORT_DIR)
	docker run --rm -i \
		-e BASE_URL=$(BASE_URL) -e DURATION=$(DURATION) \
		-e BREED_RPS=$(BREED_RPS) -e MESH_RPS=$(MESH_RPS) -e READ_RPS=$(READ_RPS) \
		-e MESH_BULK_RPS=$(MESH_BULK_RPS) \
		-v $$PWD/load:/load -v $$PWD/$(REPORT_DIR):/reports \
		grafana/k6 run /load/k6/petplantr_load.js

.PHONY: ops-cfg ops-set ops-kill-on ops-kill-off ops-audit
ops-cfg:
	@bash -lc 'source scripts/ops_quick.sh && op_cfg'
ops-set:
	@bash -lc 'source scripts/ops_quick.sh && op_set $(ARGS)'
ops-kill-on:
	@bash -lc 'source scripts/ops_quick.sh && op_kill_on'
ops-kill-off:
	@bash -lc 'source scripts/ops_quick.sh && op_kill_off'
ops-audit:
	@bash -lc 'source scripts/ops_quick.sh && op_audit $${N:-10}'

# Final verification sweep
.PHONY: final-verify
final-verify:
	./scripts/final_verification_sweep.sh

# ---------------- OpenAPI & Contract Targets ----------------
SHELL := /bin/bash
PYTHON ?= python
OPENAPI_JSON ?= openapi.json
SPECTRAL ?= npx --yes @stoplight/spectral-cli
OASDIFF_IMG ?= ghcr.io/tufin/oasdiff:latest

.PHONY: openapi/export
openapi/export:
	$(PYTHON) scripts/export_openapi.py $(OPENAPI_JSON)

.PHONY: openapi/lint
openapi/lint: openapi/export
	@if command -v npx >/dev/null 2>&1; then \
		$(SPECTRAL) lint $(OPENAPI_JSON) -r spectral.yaml -q; \
	elif command -v docker >/dev/null 2>&1; then \
		echo "npx not found, trying Docker spectral..."; \
		docker run --rm -v "$$PWD:/work" stoplight/spectral:latest lint /work/$(OPENAPI_JSON) -r /work/spectral.yaml -q \
		|| { echo "WARN: Docker spectral failed; skipping local lint (CI still enforces)"; exit 0; }; \
	else \
		echo "WARN: Spectral not available (no npx or docker). Skipping local lint (CI still enforces)."; \
	fi

.PHONY: openapi/size
openapi/size: openapi/export
	@$(PYTHON) -c 'import os,sys; print(f"openapi.json bytes: {os.path.getsize(sys.argv[1])}")' $(OPENAPI_JSON)

.PHONY: openapi/diff
openapi/diff: openapi/export
	@git fetch origin main --depth=1
	@mkdir -p ._main || true
	@{ git worktree add ._main origin/main || true; } >/dev/null 2>&1
	@cd ._main && $(PYTHON) scripts/export_openapi.py ../openapi-main.json
	@docker run --rm -v "$$PWD:/repo" $(OASDIFF_IMG) \
		breaking --fail-on-diff /repo/openapi-main.json /repo/$(OPENAPI_JSON)

.PHONY: openapi/lint-local
openapi/lint-local: openapi/export
	$(PYTHON) scripts/lint_openapi_local.py $(OPENAPI_JSON)

.PHONY: ci/contract
ci/contract:
	pytest -m "contract and not slow" -q

.PHONY: ci/full test
ci/full test:
	pytest -q

.PHONY: test-ai
test-ai: ## Run deterministic AI/ML tests quietly (no coverage noise)
	pytest -q -k ai_model_quality -m ai --no-cov

.PHONY: test-ai-verbose
test-ai-verbose: ## Run deterministic AI/ML tests with -ra summaries (no coverage)
	pytest -ra -k ai_model_quality -m ai --no-cov

.PHONY: sdk-typecheck
sdk-typecheck: ## Type-check SDK with pinned TS (no emit)
	$(MAKE) -C sdk typecheck TS_VERSION=$(TS_VERSION)

.PHONY: sdk-list
sdk-list: ## List TS files included by SDK tsconfig
	$(MAKE) -C sdk ts-list TS_VERSION=$(TS_VERSION)

.PHONY: sdk-showconfig
sdk-showconfig: ## Show effective SDK tsconfig
	$(MAKE) -C sdk ts-show TS_VERSION=$(TS_VERSION)

.PHONY: sdk-doctor
sdk-doctor: ## Run SDK health check (Node/npx/TS pinned + tsconfig coverage + typecheck)
	@{ command -v bash >/dev/null 2>&1 && bash ./scripts/dev/sdk-doctor.sh; } \
	|| { command -v pwsh >/dev/null 2>&1 && pwsh -NoProfile -File ./scripts/dev/sdk-doctor.ps1; } \
	|| { command -v powershell >/dev/null 2>&1 && powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/dev/sdk-doctor.ps1; }

 
