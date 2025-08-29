default: test test-anthropic
.PHONY: default

test:
	@make -B -C simple
.PHONY: test

test-anthropic:
	@make -B -C simple PROVIDER=anthropic MODEL=claude-sonnet-4-20250514
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
