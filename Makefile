VERSION := 0.8.0

BOOTSTRAP_FLAGS := --context-files ./.enc.env.example

BOOTSTRAP_DEPS := ./.enc.env.example ./res/pricing.json ./res/languages.json

ENC ?= ./enc-release

TEST_ITERATIONS ?= 5

###############
### INSTALL ###
###############

default: build-release
.PHONY: default

install: install-rust-release
.PHONY: install

install-rust-release: build-rust-release
	install ./target/release/enc ${HOME}/.local/bin/enc
.PHONY: install-rust-release

install-python: build-python install-resources
	install ./src/enc.py ${HOME}/.local/bin/enc
.PHONY: install-python

install-cpp: build-cpp install-resources
	install ./build/enc-cpp ${HOME}/.local/bin/enc
.PHONY: install-cpp

install-resources:
	install -d ./res/ ${XDG_DATA_HOME}/enc/res/
	install ./res/prompt.tmpl ${XDG_DATA_HOME}/enc/res/prompt.tmpl
	install ./res/pricing.json ${XDG_DATA_HOME}/enc/res/pricing.json
	install ./res/languages.json ${XDG_DATA_HOME}/enc/res/languages.json
.PHONY: install-resources

uninstall:
	rm -fv "${HOME}/.local/bin/enc"
	rm -rfv "${XDG_DATA_HOME}/enc/"
.PHONY: uninstall

#############
### BUILD ###
#############

release: build/release/enc-linux-x64-$(VERSION).tgz
.PHONY: release

build/release/enc-linux-x64-$(VERSION).tgz: build-release build
	mkdir -p build/release/enc-$(VERSION)/
	cp ./README.md ./build/release/enc-$(VERSION)/
	cp ./.enc.env.example ./build/release/enc-$(VERSION)/
	cp ./target/release/enc ./build/release/enc-$(VERSION)/
	cp ./src/enc.py ./build/release/enc-$(VERSION)/
	cp ./src/enc.ts ./build/release/enc-$(VERSION)/
	cp ./build/enc-cpp ./build/release/enc-$(VERSION)/
	cp ./package-lock.json ./build/release/enc-$(VERSION)/
	cp ./requirements.txt ./build/release/enc-$(VERSION)/
	cp -r ./res/ ./build/release/enc-$(VERSION)/
	tar -C ./build/release/ -cvzf "$@" ./enc-$(VERSION)/

build: build-rust build-cpp build-python build-typescript
.PHONY: build

build-release: build-rust-release
.PHONY: build-release

build-rust: target/debug/enc
.PHONY: build-rust

build-rust-release: target/release/enc
.PHONY: build-rust-release

build-python: build/python.state
.PHONY: build-python

build/python.state: src/enc.py
	chmod +x src/enc.py
	python -m py_compile src/enc.py
	touch "$@"

build-cpp: build/enc-cpp
.PHONY: build-cpp

build-typescript: build/typescript.state
.PHONY: build-typescript

build/typescript.state: src/enc.ts
	npm install
	touch "$@"

target/debug/enc: src/enc.rs
	cargo build

target/release/enc:
	cargo build --release

target/release/enc-linux-x64:
	cd target/release/ && ln -sf enc enc-linux-x64

build/enc-cpp: src/enc.cpp CMakeLists.txt
	cmake -B build
	cmake --build build

clean:
	rm -rfv ./__pycache__/ ./target/ ./build/ ./examples/hello
.PHONY: clean

#####################
### TRANSPILATION ###
#####################

transpile-rust: src/enc.rs
.PHONY: transpile-rust

transpile-python: src/enc.py
.PHONY: transpile-python

transpile-cpp: src/enc.cpp
.PHONY: transpile-cpp

transpile-typescript: src/enc.ts
.PHONY: transpile-typescript

transpile-haskell: src/enc.hs
.PHONY: transpile-haskell

ifneq ($(filter src/enc.rs transpile-rust,$(MAKECMDGOALS)),)
src/enc.rs: src/enc.en Cargo.toml $(BOOTSTRAP_DEPS)
	$(ENC) "$<" -o "$@" $(BOOTSTRAP_FLAGS):./Cargo.toml
endif

ifneq ($(filter src/enc.py transpile-python,$(MAKECMDGOALS)),)
src/enc.py: src/enc.en $(BOOTSTRAP_DEPS)
	$(ENC) "$<" -o "$@" $(BOOTSTRAP_FLAGS):./requirements.txt
endif

ifneq ($(filter src/enc.cpp transpile-cpp,$(MAKECMDGOALS)),)
src/enc.cpp: src/enc.en CMakeLists.txt $(BOOTSTRAP_DEPS)
	$(ENC) "$<" -o "$@" $(BOOTSTRAP_FLAGS):CMakeLists.txt
endif

ifneq ($(filter src/enc.ts transpile-typescript,$(MAKECMDGOALS)),)
src/enc.ts: src/enc.en package.json $(BOOTSTRAP_DEPS)
	$(ENC) "$<" -o "$@" $(BOOTSTRAP_FLAGS):./package.json
endif

ifneq ($(filter src/enc.hs transpile-haskell,$(MAKECMDGOALS)),)
src/main.hs: src/enc.en $(BOOTSTRAP_DEPS)
	$(ENC) "$<" -o "$@" $(BOOTSTRAP_FLAGS)
endif

### RESOURCES ###

bootstrap-deps: $(BOOTSTRAP_DEPS)
.PHONY: bootstrap-deps

ifneq ($(filter res/languages.json,$(MAKECMDGOALS)),)
res/languages.json: res/languages.en
	$(ENC) "$<" -o "$@"
endif

ifneq ($(filter res/pricing.json,$(MAKECMDGOALS)),)
res/pricing.json:
	./scripts/pricing.py
endif

scripts: scripts/pricing.py
.PHONY: scripts

ifneq ($(filter scripts/pricing.py scripts,$(MAKECMDGOALS)),)
scripts/pricing.py: scripts/pricing.en
	$(ENC) "$<" -o "$@" --context-files ./res/pricing.json:requirements.txt
endif

###############
### TESTING ###
###############

precommit: test
.PHONY: precommit

update-testdata: test.sh
	./test.sh update tests-rust
	./test.sh update tests-python
	./test.sh update tests-cpp
	./test.sh update tests-typescript
.PHONY: update-testdata

test: test-rust
.PHONY: test

test-rust: build-rust
	./test.sh test tests-rust
.PHONY: test-rust

test-python: build-python
	./test.sh test tests-python
.PHONY: test-python

test-cpp: build-cpp
	./test.sh test tests-cpp
.PHONY: test-cpp

test-typescript: build-typescript
	./test.sh test tests-typescript
.PHONY: test-typescript

tests: tests-rust
.PHONY: tests

tests-rust:
	@make -C tests ENC_EDITION=enc
.PHONY: tests-rust

tests-cpp:
	@make -C tests ENC_EDITION=enc-cpp
.PHONY: tests-cpp

tests-python:
	@make -C tests ENC_EDITION=enc-python
.PHONY: tests-python

tests-typescript:
	@make -C tests ENC_EDITION=enc-typescript
.PHONY: tests-python

tests-release:
	@make -C tests ENC_EDITION=enc-release
.PHONY: tests-release

###################
### DEVELOPMENT ###
###################

ifneq ($(filter test.sh,$(MAKECMDGOALS)),)
test.sh: test.en
	$(ENC) "$<" -o "$@" --context-files Makefile
endif

format: format-python
.PHONY: format

format-rust:
	rustfmt
.PHONY: format-rust

format-python:
	black src/*.py
.PHONY: format-python

### BOOTSTRAPPING ###

bootstrap-python: src/enc.en requirements.txt $(BOOTSTRAP_DEPS)
	./src/enc.bootstrap.py "$<" -o "src/enc.py" $(BOOTSTRAP_FLAGS):./requirements.txt
.PHONY: bootstrap-python

bootstrap-rust: src/enc.en Cargo.toml $(BOOTSTRAP_DEPS)
	./src/enc.bootstrap.py "$<" -o "src/enc.rs" $(BOOTSTRAP_FLAGS):./Cargo.toml
.PHONY: bootstrap-rust

touch:
	touch src/enc.en doc/booklet.en doc/icon.en test.en
	touch examples/hello.en
	touch examples/multi/lib.en examples/multi/main.en
	touch examples/balloons/main.en examples/balloons/assets/balloon.en
	touch examples/web/index.en examples/web/styles.en examples/web/main.en
.PHONY: touch

###############################
### EXAMPLES AND VALIDATION ###
###############################

hello: examples/hello.en
	./enc "$<" -o "examples/hello.c" --provider=google --model=gemini-2.5-flash
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello

hello-release: examples/hello.en
	./enc-release "$<" -o "examples/hello.c" --provider=google --model=gemini-2.5-flash
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-release

hello-bootstrap: examples/hello.en
	./src/enc.bootstrap.py "$<" -o "examples/hello.c"
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-bootstrap

hello-python: examples/hello.en
	./enc-python "$<" -o "examples/hello.c" --provider=google --model=gemini-2.5-flash
	cc "examples/hello.c" -o examples/hello
	./examples/hello fnord
.PHONY: hello-python

hello-rust: examples/hello.en
	./enc-rust "$<" -o "examples/hello.c" --provider=google --model=gemini-2.5-flash
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

#####################
### DOCUMENTATION ###
#####################

docs: doc/icon.png doc/booklet.md doc/enc.cast.gif
.PHONY: docs

doc/icon.png: doc/icon.svg
	convert -background none "$<" "$@"

ifneq ($(filter doc/icon.svg docs,$(MAKECMDGOALS)),)
doc/icon.svg: doc/icon.en
	./enc "$<" -o "$@" --context-files README.md:src/enc.en
endif

ifneq ($(filter doc/pitch.md docs,$(MAKECMDGOALS)),)
doc/pitch.md: doc/pitch.en src/enc.en
	$(ENC) "$<" -o "$@" --context-files src/enc.en
endif

ifneq ($(filter doc/booklet.md docs,$(MAKECMDGOALS)),)
doc/booklet.md: doc/booklet.en .enc.env.example Makefile README.md src/enc.en examples/multi/README.md examples/parasite/README.md examples/balloons/README.md examples/web/README.md
	$(ENC) "$<" -o "$@" --context-files README.md:.enc.env.example:Makefile:src/enc.en:examples/multi/README.md:examples/parasite/README.md:examples/balloons/README.md:examples/web/README.md
endif

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
