tranpsile: vibes.py
.PHONY: tranpsile

run: transpile
	python main.py
.PHONY: run

vibes.py: vibes.en
	enc "$<" -o "$@"
