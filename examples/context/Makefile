run: transpile
	python main.py
.PHONY: run

transpile: main.py
.PHONY: transpile

main.py: main.en context.txt
	enc "$<" -o "$@" --context-files context.txt
