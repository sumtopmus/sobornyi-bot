.PHONY: run debug clean clean-state clean-cache clean-logs clean-data clean-conversations

run: clean-cache
	@ENV_FOR_DYNACONF=prod python src/bot.py

debug: clean-state
	@ENV_FOR_DYNACONF=dev python src/bot.py

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
