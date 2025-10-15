ENC_EDITION := enc

ENC := ../../$(ENC_EDITION)

run: show-config transpile
	python main.py
.PHONY: run

show-config:
	$(ENC) --show-config
.PHONY: show-config

transpile: main.py
.PHONY: transpile

main.py: main.en context.txt
	$(ENC) "$<" -o "$@" --context-files context.txt
