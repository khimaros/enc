#!/bin/bash

set -euo pipefail

ITERATIONS=5

MODELS=(
	"google/gemini-3-pro-preview"
	"google/gemini-3-flash-preview"
	"anthropic/claude-opus-4-5-20251101"
	#"openai/minimax-m2.1:Q3_K_M"
)

LANGUAGES=(
	"rust"
	"python"
	"typescript"
	#"cpp"
	#"haskell"
)

for lang in "${LANGUAGES[@]}"; do
	./bench.py "${lang}" ${ITERATIONS} "${MODELS[@]}"
done
