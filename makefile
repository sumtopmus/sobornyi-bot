.PHONY: run debug clean

run: clean
	python src/main.py

debug: clean
	python src/main.py --debug

clean:
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__