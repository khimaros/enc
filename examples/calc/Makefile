transpile: calc.html
.PHONY: transpile

run: transpile
	open calc.html
.PHONY: run

calc.html: calc.en
	enc "$<" -o "$@" --context-files calc.html
