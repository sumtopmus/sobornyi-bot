.PHONY: run debug clean-cache clean-logs

run: clean-cache
	@ENV_FOR_DYNACONF=production python src/main.py

debug: clean-cache clean-logs
	@python src/main.py

clean-cache:
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__

clean-logs:
	@rm -rf logs