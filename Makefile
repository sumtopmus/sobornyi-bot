.PHONY: run debug clean clean-cache clean-logs clean-data

run: clean-cache
	@ENV_FOR_DYNACONF=prod python src/bot.py

debug: clean
	@ENV_FOR_DYNACONF=dev python src/bot.py

clean: clean-cache clean-logs clean-data

clean-cache:
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__

clean-logs:
	@rm -rf logs

clean-data:
	@rm -rf data
