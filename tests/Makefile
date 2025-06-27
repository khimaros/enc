default: test test-anthropic
.PHONY: default

test:
	@make -B -C simple
.PHONY: test

test-anthropic:
	@make -B -C simple PROVIDER=anthropic MODEL=claude-3-7-sonnet-20250219
.PHONY: test-anthropic

test-release:
	@make -B -C simple ENC_EDITION=enc-release
.PHONY: test-release

test-rust:
	@make -B -C simple ENC_EDITION=enc-rust
.PHONY: test-rust

test-python:
	@make -B -C simple ENC_EDITION=enc-python
.PHONY: test-python
