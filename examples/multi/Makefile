transpile: main.py
.PHONY: transpile

run: transpile
	python main.py
.PHONY: run

main.py: main.en lib.py
	enc "$<" -o "$@" --context-files lib.py

lib.py: lib.en
	enc "$<" -o "$@"
