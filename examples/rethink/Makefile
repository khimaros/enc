describe.md: main.py
	enc "$<" -o "$@"

main.py: prompt.en
	enc "$<" -o "$@"

prompt.en: start.en
	enc "$<" -o "$@"

run: main.py
	python main.py
.PHONY: run
