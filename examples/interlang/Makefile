run: main
	./main 10
.PHONY: run

main: main.c
	cc "$<" -o "$@"

main.c: main.py
	enc "$<" -o "$@"

main.py: main.en
	enc "$<" -o "$@"
