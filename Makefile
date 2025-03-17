.PHONY: install init-dev run debug backup clean clean-state clean-cache clean-logs clean-data clean-conversations test test-unit test-integration test-cov migrate migrate-help config

install: config
	conda env create -f environment.yaml

init-dev: install
	pip install -r requirements-dev.txt
	pre-commit install

run: clean-cache
	@ENV_FOR_DYNACONF=prod python src/bot.py

debug: clean-state
	@ENV_FOR_DYNACONF=dev python src/bot.py

backup:
	@timestamp=$$(date +%Y%m%d) && \
	mkdir -p backup/$$timestamp && \
	cp -r data backup/$$timestamp/. && \
	cp -r logs/bot.log backup/$$timestamp/. && \
	cp -r backup/$$timestamp/* backup/.

migrate:
	@python tools/migration.py

migrate-help:
	@python tools/migration.py --help

test:
	@pytest

test-unit:
	@pytest -m "not integration"

test-integration:
	@pytest -m integration

test-cov:
	@pytest --cov=src --cov-report=term --cov-report=html
	-@echo
	@echo "Coverage report: htmlcov/index.html"
	@open htmlcov/index.html

display-coverage:
	@open htmlcov/index.html

clean: clean-cache clean-logs clean-data

clean-state: clean-cache clean-logs clean-conversations

clean-cache:
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__

clean-logs:
	@rm -rf logs

clean-data:
	@rm -rf data

clean-conversations:
	@rm -rf data/db_conversations
	@rm -rf data/db_callback_data

config:
	@echo "Generating configuration files from templates..."
	@echo "Note: This requires template files in config/templates/ directory."
	@python tools/generate_config.py
	@echo "Configuration files have been created in the config/ directory."
	@echo "Please update them with your own settings before running the application."
