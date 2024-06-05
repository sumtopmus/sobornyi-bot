.PHONY: run debug clean-cache clean-logs clean-data

run: clean-cache
	@ENV_FOR_DYNACONF=prod python src/main.py

debug: clean-cache clean-logs
	@ENV_FOR_DYNACONF=dev python src/main.py

clean-cache:
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__

clean-logs:
	@rm -rf logs

clean-data:
	@rm -rf data