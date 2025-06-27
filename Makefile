BOOTSTRAP_FLAGS := --context-files ./.enc.env.example

BOOTSTRAP_DEPS := ./.enc.env.example ./res/pricing.json ./res/languages.json

default: build
.PHONY: default

install: build
	install ./target/debug/enc ${HOME}/.local/bin/enc
.PHONY: install

install-python: install-resources
	install ./src/enc.py ${HOME}/.local/bin/enc
.PHONY: install-python

install-resources:
	install -d ./res/ ${XDG_DATA_HOME}/enc/res/
	install ./res/prompt.tmpl ${XDG_DATA_HOME}/enc/res/prompt.tmpl
	install ./res/pricing.json ${XDG_DATA_HOME}/enc/res/pricing.json
	install ./res/languages.json ${XDG_DATA_HOME}/enc/res/languages.json
.PHONY: install-resources

res/languages.json: res/languages.en
	./enc-release "$<" -o "$@"

uninstall:
	rm -fv "${HOME}/.local/bin/enc"
	rm -rfv "${XDG_DATA_HOME}/enc/"
.PHONY: uninstall

release: build-release
.PHONY: release

build-release: build-release-rust
.PHONY: build-release

build-release-rust: transpile-rust
	cargo build --release
	cd target/release/ && ln -sf enc enc-linux-x64
.PHONY: build-release-rust

create: create-rust
.PHONY: create

create-rust: transpile-rust build-rust
.PHONY: create-rust

build: build-rust
.PHONY: build

transpile: transpile-python transpile-rust test.sh scripts/pricing.py
.PHONY: transpile

transpile-rust: src/main.rs
.PHONY: transpile-rust

transpile-rust-grounded: src/enc.en $(BOOTSTRAP_DEPS)
	./enc-release  "$<" -o "src/main.rs" $(BOOTSTRAP_FLAGS):./Cargo.toml:./src/main.rs
.PHONY: transpile-rust-grounded

transpile-python: src/enc.py
.PHONY: transpile-python

src/enc.py: src/enc.en $(BOOTSTRAP_DEPS)
	./enc-release "$<" -o "$@" $(BOOTSTRAP_FLAGS):./requirements.txt

build-rust: target/debug/enc
.PHONY: build-rust

target/debug/enc: src/main.rs
	cargo build

src/main.rs: src/enc.en $(BOOTSTRAP_DEPS)
	./enc-release "$<" -o "$@" $(BOOTSTRAP_FLAGS):./Cargo.toml

bootstrap-python: src/enc.en $(BOOTSTRAP_DEPS)
	./src/enc.bootstrap.py "$<" -o "src/enc.py" $(BOOTSTRAP_FLAGS):./requirements.txt
.PHONY: bootstrap-python

bootstrap-rust: src/enc.en $(BOOTSTRAP_DEPS)
	./src/enc.bootstrap.py "$<" -o "src/main.rs" $(BOOTSTRAP_FLAGS):./Cargo.toml
.PHONY: bootstrap-rust

touch:
	touch src/enc.en doc/booklet.en doc/icon.en test.en
	touch examples/hello.en
	touch examples/multi/lib.en examples/multi/main.en
	touch examples/balloons/main.en examples/balloons/assets/balloon.en
	touch examples/web/index.en examples/web/styles.en examples/web/main.en
.PHONY: touch

precommit: test-goldens
.PHONY: precommit

test-goldens: test.sh
	./test.sh test
.PHONY: test-goldens

update-goldens: test.sh
	./test.sh update
.PHONY: update-goldens

tests:
	@make -C tests
.PHONY: tests

tests-python:
	@make -C tests ENC_EDITION=enc-python
.PHONY: tests-python

tests-release:
	@make -C tests ENC_EDITION=enc-release
.PHONY: tests-release

test.sh: test.en
	./enc-release "$<" -o "$@" --context-files Makefile

format: format-python
.PHONY: format

format-rust:
	rustfmt
.PHONY: format-rust

format-python:
	black src/*.py
.PHONY: format-python

hello: examples/hello.en
	./enc "$<" -o "examples/hello.c" --model=gemini-2.5-flash
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello

hello-release: examples/hello.en
	./enc-release "$<" -o "examples/hello.c" --model=gemini-2.5-flash
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-release

hello-bootstrap: examples/hello.en
	./src/enc.bootstrap.py "$<" -o "examples/hello.c"
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-bootstrap

hello-python: examples/hello.en
	./enc-python "$<" -o "examples/hello.c"
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-python

hello-rust: examples/hello.en
	./enc-rust "$<" -o "examples/hello.c"
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-rust

examples: examples/hello
	make -C examples/balloons
	make -C examples/multi
	make -C examples/parasite
	make -C examples/web
.PHONY: examples

examples/hello: examples/hello.c

examples/hello.py: examples/hello.en
	./enc "$<" -o "$@"

examples/hello.rs: examples/hello.en
	./enc "$<" -o "$@"

examples/hello.c: examples/hello.en
	./enc "$<" -o "$@"

res/pricing.json:
	./scripts/pricing.py

scripts: scripts/pricing.py
.PHONY: scripts

scripts/pricing.py: scripts/pricing.en
	./enc-release "$<" -o "$@" --context-files ./res/pricing.json:requirements.txt

docs: doc/icon.png doc/booklet.md doc/enc.cast.gif
.PHONY: docs

doc/icon.png: doc/icon.svg
	convert -background none "$<" "$@"

doc/icon.svg: doc/icon.en
	./enc "$<" -o "$@" --context-files README.md:src/enc.en

doc/booklet.md: doc/booklet.en .enc.env.example Makefile README.md src/enc.en examples/multi/README.md examples/parasite/README.md examples/balloons/README.md examples/web/README.md
	./enc-release "$<" -o "$@" --context-files README.md:.enc.env.example:Makefile:src/enc.en:examples/multi/README.md:examples/parasite/README.md:examples/balloons/README.md:examples/web/README.md --model=gemini-2.5-flash

doc/CAST.md:
	echo "# CAST" > "$@"
	echo >> "$@"
	echo '```console' >> "$@"
	echo '$ cat ./examples/hello.en' >> "$@"
	cat ./examples/hello.en >> "$@"
	make hello | tee -a "$@"
	echo '```' >> "$@"

doc/enc.cast: doc/CAST.md
	md2ac < "$<" > "$@"

doc/enc.cast.gif: doc/enc.cast
	agg --theme github-dark --last-frame-duration 10 "$<" "$@"

clean:
	rm -rfv ./__pycache__/ ./target/ ./examples/hello
.PHONY: clean
