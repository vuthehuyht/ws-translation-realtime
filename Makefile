# =============================================================================
# Realtime Speech-to-Speech & Speech-to-Text Translation System
# Makefile for Development, Testing, Linting, and Infrastructure Management
# =============================================================================

.DEFAULT_GOAL := help
SHELL         := /bin/bash
AWS_PROFILE   ?= admin

# Color helpers for terminal output
BLUE   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
RED    := \033[31m
RESET  := \033[0m

.PHONY: help
help: ## Display available commands with descriptions
	@echo ""
	@echo "Realtime Translation System - Available Make Targets:"
	@echo "======================================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-18s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Dependencies Installation
# =============================================================================

.PHONY: install install-fe install-be
install: install-fe install-be ## Install all dependencies for Frontend and Backend

install-fe: ## Install Frontend dependencies (Next.js 15 via pnpm)
	@echo "$(GREEN)==> Installing Frontend dependencies (apps/web)...$(RESET)"
	cd apps/web && pnpm install

install-be: ## Install Backend dependencies (FastAPI via uv)
	@echo "$(GREEN)==> Installing Backend dependencies (apps/backend)...$(RESET)"
	cd apps/backend && uv sync

# =============================================================================
# Code Quality, Formatting & Linting
# =============================================================================

.PHONY: lint lint-fe lint-be lint-tf format format-fe format-be format-tf
lint: lint-fe lint-be lint-tf ## Run all linters (Frontend, Backend, Terraform)

lint-fe: ## Run ESLint and TypeScript typecheck on Frontend
	@echo "$(GREEN)==> Linting Frontend (apps/web)...$(RESET)"
	cd apps/web && pnpm lint && pnpm typecheck

lint-be: ## Run Ruff linter and mypy typecheck on Backend
	@echo "$(GREEN)==> Linting Backend (apps/backend)...$(RESET)"
	cd apps/backend && uv run ruff check . && uv run mypy app

lint-tf: ## Verify formatting and validity of all Terraform configurations
	@echo "$(GREEN)==> Checking Terraform formatting...$(RESET)"
	terraform fmt -check -recursive infra/terraform

format: format-fe format-be format-tf ## Format all Frontend, Backend, and Terraform code

format-fe: ## Format Frontend code
	@echo "$(GREEN)==> Formatting Frontend...$(RESET)"
	cd apps/web && pnpm lint --fix || true

format-be: ## Format Backend code using Ruff
	@echo "$(GREEN)==> Formatting Backend...$(RESET)"
	cd apps/backend && uv run ruff format . && uv run ruff check --fix .

format-tf: ## Format all Terraform files recursively
	@echo "$(GREEN)==> Formatting Terraform...$(RESET)"
	terraform fmt -recursive infra/terraform

# =============================================================================
# Automated Testing
# =============================================================================

.PHONY: test test-fe test-be
test: test-fe test-be ## Run all tests (Frontend Vitest + Backend Pytest)

test-fe: ## Run Frontend unit & component tests (Vitest)
	@echo "$(GREEN)==> Running Frontend tests (Vitest)...$(RESET)"
	cd apps/web && pnpm test:run

test-be: ## Run Backend async unit and integration tests (Pytest)
	@echo "$(GREEN)==> Running Backend tests (Pytest)...$(RESET)"
	cd apps/backend && uv run pytest -v

# =============================================================================
# Application Builds & Docker Packaging
# =============================================================================

.PHONY: build-fe build-docker-fe build-docker-be build-docker
build-fe: ## Build Next.js 15 Standalone application
	@echo "$(GREEN)==> Building Next.js Standalone Frontend...$(RESET)"
	cd apps/web && pnpm build

build-docker-fe: ## Build Frontend Docker container image
	@echo "$(GREEN)==> Building Frontend Docker image...$(RESET)"
	docker build -t ws-translation/web:test ./apps/web

build-docker-be: ## Build Backend Docker container image
	@echo "$(GREEN)==> Building Backend Docker image...$(RESET)"
	docker build -t ws-translation/backend:test ./apps/backend

build-docker: build-docker-fe build-docker-be ## Build both Frontend and Backend Docker images

# =============================================================================
# Local Development Servers
# =============================================================================

.PHONY: dev-fe dev-be
dev-fe: ## Run Next.js frontend development server (Port 3000)
	cd apps/web && pnpm dev

dev-be: ## Run FastAPI backend development server (Port 8000)
	cd apps/backend && uv run uvicorn app.main:app --reload --port 8000

# =============================================================================
# Terraform Infrastructure Validation & Management
# =============================================================================

.PHONY: tf-init tf-validate
tf-init: ## Initialize Terraform for all 3 environments (local, dev, prod)
	@echo "$(GREEN)==> Initializing Terraform environments...$(RESET)"
	terraform -chdir=infra/terraform/environments/local init
	terraform -chdir=infra/terraform/environments/dev init
	terraform -chdir=infra/terraform/environments/prod init

tf-validate: ## Validate Terraform syntax for all 3 environments
	@echo "$(GREEN)==> Validating Terraform environments...$(RESET)"
	terraform -chdir=infra/terraform/environments/local validate
	terraform -chdir=infra/terraform/environments/dev validate
	terraform -chdir=infra/terraform/environments/prod validate

# =============================================================================
# Deployment: Local Environment (DevBox EC2 + S3 + Cognito + AppSync)
# =============================================================================

.PHONY: plan-local deploy-local destroy-local
plan-local: ## Plan Terraform deployment for Local environment
	@echo "$(YELLOW)==> Planning Local Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/local plan

deploy-local: ## Deploy Local environment (DevBox EC2, S3, Cognito, AppSync, auto-generate .env)
	@echo "$(GREEN)==> Deploying Local Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/local apply -auto-approve

destroy-local: ## Destroy Local environment resources
	@echo "$(RED)==> Destroying Local Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/local destroy -auto-approve

# =============================================================================
# Deployment: Dev Environment (Custom VPC, RDS, ElastiCache, ECS Fargate, ALB)
# =============================================================================

.PHONY: plan-dev deploy-dev destroy-dev
plan-dev: ## Plan Terraform deployment for Dev environment
	@echo "$(YELLOW)==> Planning Dev Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/dev plan

deploy-dev: ## Deploy Dev environment on AWS
	@echo "$(GREEN)==> Deploying Dev Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/dev apply -auto-approve

destroy-dev: ## Destroy Dev environment resources
	@echo "$(RED)==> Destroying Dev Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/dev destroy -auto-approve

# =============================================================================
# Deployment: Prod Environment (Multi-AZ RDS, Autoscaling ECS, WAFv2, CloudWatch)
# =============================================================================

.PHONY: plan-prod deploy-prod destroy-prod
plan-prod: ## Plan Terraform deployment for Production environment
	@echo "$(YELLOW)==> Planning Production Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/prod plan

deploy-prod: ## Deploy Production environment on AWS (interactive confirmation required)
	@echo "$(GREEN)==> Deploying Production Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/prod apply

destroy-prod: ## Destroy Production environment resources (interactive confirmation required)
	@echo "$(RED)==> Destroying Production Environment (Profile: $(AWS_PROFILE))...$(RESET)"
	AWS_PROFILE=$(AWS_PROFILE) terraform -chdir=infra/terraform/environments/prod destroy
