# enc

the english to anything transpiler

inspired by https://github.com/theletterf/english-lang

`enc` is self hosting and the english definition is at [./src/enc.en](./src/enc.en)

detailed docs are available in [./doc/booklet.md](doc/booklet.md)

## overview

`enc` transpiles plain english description of code to any other
programming language, with the help of Generative AI.

![enc asciicast](./doc/enc.cast.gif)

assuming the following `examples/hello.en`:

```
hello: output the string "hello, <input>!" based on the user's input

main: call the hello function with the first argv. default to "world"
```

with this incantation of `enc`:

```console
$ enc ./examples/hello.en -o ./examples/hello.rs
```

will produce the following `examples/hello.rs`:

```rust
use std::env;

// hello: output the string "hello, <input>!" based on the user's input
fn hello(name: &str) {
    println!("hello, {}!", name);
}

// main: call the hello function with the first argv. default to "world"
fn main() {
    let name = env::args().nth(1).unwrap_or_else(|| "world".to_string());
    hello(&name);
}
```

## quickstart

```console
$ cp ./.enc.env.example ~/.enc.env

$ editor ~/.enc.env  # add your keys

$ make

$ make hello
```

there are three editions of `enc` here:

- [./src/enc.bootstrap.py](./src/enc.bootstrap.py): bootstrap edition built with aider
- [./src/enc.py](./src/enc.py): python edition built by `enc` from [./src/enc.en](./src/enc.en)
- [./src/main.rs](./src/main.rs): rust edition built by `enc` from [./src/enc.en](./src/enc.en)

the default edition is the rust edition

there are also make targets for the `-bootstrap`, `-rust`, and `-python` editions,
such as `make hello-bootstrap` or `make hello-rust`

mise is recommended for a more contained/reproducible build

## examples

browse the [examples](./examples/) for more use cases

some examples require that `enc` be [installed](#installation#)

## installation

ensure that `${HOME}/.local/bin/` is in your PATH

```console
$ cp ./.enc.env.example ~/.enc.env

$ editor ~/.enc.env  # add your keys

$ make install
```

you can easily uninstall with `make uninstall`

## acknowledgments

the bootstrap edition of `enc` was vibe coded with `aider` and `gemini-2.5-pro`

other editions were transpiled from english by `enc` and `gemini-2.5-pro`

model prices were pulled from [aider](https://github.com/Aider-AI/aider/blob/main/aider/resources/model-metadata.json)
