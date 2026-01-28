default: test-google test-anthropic test-openai
.PHONY: default

test:
	@make -B -C simple
.PHONY: test

test-google:
	@make -B -C simple PROVIDER=google MODEL=gemini-3-flash-preview
.PHONY: test-google

test-openai:
	@make -B -C simple PROVIDER=openai OPENAI_API_BASE=https://api.openai.com/v1 MODEL=gpt-5-nano-2025-08-07
.PHONY: test-openai

test-anthropic:
	@make -B -C simple PROVIDER=anthropic MODEL=claude-haiku-4-5-20251001
.PHONY: test-anthropic

test-custom:
	@make -B -C simple PROVIDER=openai MODEL=gpt-oss-20b:Q8_0 OPENAI_API_KEY="fake" OPENAI_API_BASE=http://kairos:7860/v1
.PHONY: test-custom

test-release:
	@make -B -C simple ENC_EDITION=enc-release
.PHONY: test-release

test-rust:
	@make -B -C simple ENC_EDITION=enc-rust
.PHONY: test-rust

test-python:
	@make -B -C simple ENC_EDITION=enc-python
.PHONY: test-python
