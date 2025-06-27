ENC_EDITION := enc

ENC := ../../$(ENC_EDITION)

run: transpile
	python main.py
.PHONY: run

transpile: main.py
	$(ENC) --show-config
.PHONY: transpile

main.py: main.en context.txt
	$(ENC) "$<" -o "$@" --context-files context.txt
