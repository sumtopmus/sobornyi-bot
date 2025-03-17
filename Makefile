.DEFAULT_GOAL := help

# Colors for terminal output
BOLD := $(shell tput bold)
GREEN := $(shell tput setaf 2)
YELLOW := $(shell tput setaf 3)
BLUE := $(shell tput setaf 4)
RED := $(shell tput setaf 1)
RESET := $(shell tput sgr0)

# Project version - update this when releasing new versions
VERSION := 1.0.4

.PHONY: env init-dev run debug backup clean clean-state clean-cache clean-logs clean-data clean-conversations test test-unit test-integration test-cov migrate migrate-help config help setup check-conda check-deps version docs

help:
	@echo "${BOLD}🔍 Available commands:${RESET}"
	@echo "  ${BOLD}make${RESET}                       - ℹ️  Show this help message"
	@echo "  ${BOLD}make setup${RESET}                 - 🏗️  First-time setup: install dependencies and configure project"
	@echo "  ${BOLD}make env${RESET}                   - 📦 Create conda environment and install dependencies"
	@echo "  ${BOLD}make init-dev${RESET}              - 🛠️  Setup development environment with pre-commit hooks"
	@echo "  ${BOLD}make run${RESET}                   - 🚀 Run bot in production mode"
	@echo "  ${BOLD}make debug${RESET}                 - 🐞 Run bot in debug mode"
	@echo "  ${BOLD}make backup${RESET}                - 💾 Create backup of data and logs"
	@echo "  ${BOLD}make migrate${RESET}               - 🔄 Run database migrations"
	@echo "  ${BOLD}make migrate-help${RESET}          - 🚑 Show migration help"
	@echo "  ${BOLD}make test${RESET}                  - 🧪 Run all tests"
	@echo "  ${BOLD}make test-unit${RESET}             - 🔬 Run unit tests only"
	@echo "  ${BOLD}make test-integration${RESET}      - 🔌 Run integration tests only"
	@echo "  ${BOLD}make test-cov${RESET}              - 📊 Run tests with coverage report"
	@echo "  ${BOLD}make display-coverage${RESET}      - 📈 Open coverage report in browser"
	@echo "  ${BOLD}make clean${RESET}                 - 🧹 Remove all generated files"
	@echo "  ${BOLD}make clean-state${RESET}           - 🧼 Clean cache and logs"
	@echo "  ${BOLD}make clean-cache${RESET}           - 🗑️  Remove cache files"
	@echo "  ${BOLD}make clean-logs${RESET}            - 📝 Remove log files"
	@echo "  ${BOLD}make clean-data${RESET}            - 📁 Remove data files"
	@echo "  ${BOLD}make clean-conversations${RESET}   - 💬 Remove conversation files"
	@echo "  ${BOLD}make config${RESET}                - 🧰 Generate configuration files"
	@echo "  ${BOLD}make version${RESET}               - 🏷️  Show the project version"
	@echo "  ${BOLD}make docs${RESET}                  - 📚 Generate project documentation"
	@echo "  ${BOLD}make check-conda${RESET}           - 🐍 Check if conda is installed"
	@echo "  ${BOLD}make check-deps${RESET}            - ✅ Check if required tools are installed"

setup: check-conda env check-deps config
	@echo "${GREEN}🎉 Project setup complete! Run 'make run' to start the bot.${RESET}"

check-conda:
	@echo "✅ Checking for conda..."
	@which conda > /dev/null || (echo "${RED}❌ conda is not installed. Please install miniconda or anaconda first.${RESET}" && exit 1)
	@echo "${GREEN}✅ conda is installed.${RESET}"

check-deps:
	@echo "✅ Checking for required dependencies..."
	@which conda > /dev/null || (echo "${RED}❌ conda is not installed. Please install miniconda or anaconda first.${RESET}" && exit 1)
	@which python > /dev/null || (echo "${RED}❌ python is not installed. Please install python first.${RESET}" && exit 1)
	@which pip > /dev/null || (echo "${RED}❌ pip is not installed. Please install pip first.${RESET}" && exit 1)
	@echo "${GREEN}✅ All required dependencies are installed.${RESET}"

version:
	@echo "${BOLD}🏷️  Project version:${RESET} ${VERSION}"

docs:
	@echo "📚 Generating project documentation..."
	@echo "${YELLOW}Note: This requires sphinx to be installed.${RESET}"
	@if [ -d "docs" ]; then \
		cd docs && make html; \
		echo "${GREEN}Documentation generated in docs/_build/html/${RESET}"; \
	else \
		echo "${YELLOW}⚠️  Documentation directory not found. Run 'sphinx-quickstart docs' to create it.${RESET}"; \
	fi

env: config
	@echo "📦 Creating conda environment and installing dependencies..."
	conda env create -f environment.yaml
	@echo "${GREEN}✅ Dependencies installed successfully.${RESET}"

init-dev: env
	@echo "🛠️  Setting up development environment with pre-commit hooks..."
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "${GREEN}✅ Development environment set up successfully.${RESET}"

run: check-deps clean-cache
	@echo "🚀 Running bot in production mode..."
	@ENV_FOR_DYNACONF=prod python src/bot.py

debug: check-deps clean-state
	@echo "🐞 Running bot in debug mode..."
	@ENV_FOR_DYNACONF=dev python src/bot.py

backup:
	@echo "💾 Creating backup of data and logs..."
	@timestamp=$$(date +%Y%m%d) && \
	mkdir -p backup/$$timestamp && \
	cp -r data backup/$$timestamp/. && \
	cp -r logs/bot.log backup/$$timestamp/. && \
	cp -r backup/$$timestamp/* backup/.
	@echo "${GREEN}✅ Backup created successfully at backup/$$(date +%Y%m%d)/${RESET}"

migrate:
	@echo "🔄 Running database migrations..."
	@python tools/migration.py

migrate-help:
	@echo "ℹ️  Showing migration help..."
	@python tools/migration.py --help

test: check-deps
	@echo "🧪 Running all tests..."
	@pytest
	@echo "${GREEN}✅ All tests passed.${RESET}"

test-unit: check-deps
	@echo "🔬 Running unit tests only..."
	@pytest -m "not integration"
	@echo "${GREEN}✅ Unit tests passed.${RESET}"

test-integration: check-deps
	@echo "🔌 Running integration tests only..."
	@pytest -m integration
	@echo "${GREEN}✅ Integration tests passed.${RESET}"

test-cov: check-deps
	@echo "📊 Running tests with coverage report..."
	@pytest --cov=src --cov-report=term --cov-report=html
	-@echo
	@echo "Coverage report: htmlcov/index.html"
	@open htmlcov/index.html

display-coverage:
	@echo "📈 Opening coverage report in browser..."
	@open htmlcov/index.html

clean: clean-cache clean-logs clean-data
	@echo "🧹 Removed all generated files"
	@echo "${GREEN}✅ Cleanup complete.${RESET}"

clean-state: clean-cache clean-logs clean-conversations
	@echo "🧼 Cleaned cache and logs"
	@echo "${GREEN}✅ State cleanup complete.${RESET}"

clean-cache:
	@echo "🗑️ Removing cache files..."
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "${GREEN}✅ Cache files removed.${RESET}"

clean-logs:
	@echo "📝 Removing log files..."
	@rm -rf logs
	@echo "${GREEN}✅ Log files removed.${RESET}"

clean-data:
	@echo "📁 Removing data files..."
	@rm -rf data
	@mkdir -p data
	@touch data/.gitkeep
	@echo "${GREEN}✅ Data files removed.${RESET}"

clean-conversations:
	@echo "💬 Removing conversation files..."
	@rm -rf data/db_conversations
	@rm -rf data/db_callback_data
	@mkdir -p data/db_conversations data/db_callback_data
	@touch data/db_conversations/.gitkeep data/db_callback_data/.gitkeep
	@echo "${GREEN}✅ Conversation files removed.${RESET}"

config:
	@echo "🧰 Generating configuration files from templates..."
	@echo "Note: This requires template files in config/templates/ directory."
	@python tools/generate_config.py
	@echo "${GREEN}✅ Configuration files have been created in the config/ directory.${RESET}"
	@echo "${YELLOW}Please update them with your own settings before running the application.${RESET}"
