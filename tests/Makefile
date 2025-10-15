default: test test-anthropic test-openai test-llama-server
.PHONY: default

test:
	@make -B -C simple
.PHONY: test

test-openai:
	@make -B -C simple PROVIDER=openai MODEL=gpt-5-2025-08-07
.PHONY: test-openai

test-anthropic:
	@make -B -C simple PROVIDER=anthropic MODEL=claude-sonnet-4-5-20250929
.PHONY: test-anthropic

test-llama-server:
	@make -B -C simple PROVIDER=openai MODEL=gpt-oss-20b OPENAI_API_BASE="http://localhost:7860/v1" OPENAI_API_KEY="fake"
.PHONY: test-llama-server

test-release:
	@make -B -C simple ENC_EDITION=enc-release
.PHONY: test-release

test-rust:
	@make -B -C simple ENC_EDITION=enc-rust
.PHONY: test-rust

test-python:
	@make -B -C simple ENC_EDITION=enc-python
.PHONY: test-python
