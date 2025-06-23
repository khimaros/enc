all: transpile build assets
.PHONY: all

run: all
	cargo run
.PHONY: run

build: target/debug/balloons
.PHONY: build

target/debug/balloons: src/main.rs
	cargo build

tranpsile: src/main.rs assets/balloon.svg
.PHONY: transpile

src/main.rs: main.en
	enc "$<" -o "$@" --context-files Cargo.toml:assets/balloon.svg

assets: assets/balloon.png
.PHONY: assets

assets/balloon.png: assets/balloon.svg
	convert -background none "$<" "$@"

assets/balloon.svg: assets/balloon.en
	enc "$<" -o "$@"

aider:
	aider src/main.rs Cargo.toml
.PHONY: aider
