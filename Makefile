.PHONY: init run debug backup clean clean-state clean-cache clean-logs clean-data clean-conversations

init:
	conda env create -f environment.yaml

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
