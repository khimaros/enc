# enc

`cc` for english or: the english to anything transpiler

`enc` transpiles a plain english description of code to any other
programming language, with the help of Generative AI.

inspired by https://github.com/theletterf/english-lang

`enc` is self hosting (meaning it is used to build itself) and its english definition is at [./src/enc.en](./src/enc.en). also, [list `*.en` in repo](https://github.com/search?q=repo%3Akhimaros%2Fenc+path%3A*.en&type=code).

detailed docs are available in [./doc/booklet.md](doc/booklet.md)

## overview

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

prebuilt rust [releases](https://github.com/khimaros/enc/releases) are available for linux-x64

```console
$ wget -O enc https://github.com/khimaros/enc/releases/download/v0.3.1/enc-linux-x64

$ chmod +x enc

$ wget -O .enc.env https://github.com/khimaros/enc/releases/download/v0.3.1/x.enc.env.example

$ editor .enc.env   # add your API keys

$ ./enc --show-config

$ echo "print the answer to the meaning of life, the universe, and everything" > fnord.en

$ ./enc fnord.en -o fnord.rs

$ rustc fnord.rs

$ ./fnord
42
```

you may want further [#configuration](#configuration)

## examples

browse the [examples](./examples/) for more use cases

some examples require that `enc` be [installed](#installation#)

## building

```console
$ git clone https://github.com/khimaros/enc

$ make
```

mise is recommended for a more contained/reproducible build

## configuration

download the example config [./.enc.env.example](./.enc.env.example)

```console
$ wget -O ~/.enc.env https://raw.githubusercontent.com/khimaros/enc/master/.enc.env.example

$ editor ~/.enc.env  # add your keys
```

you can also copy to the working directory instead of `${HOME}`

`enc` can also be used with any OpenAI compatible endpoint, including openrouter and `llama.cpp`

to use these, set `OPENAI_BASE_URL` to your preferred endpoint

## installation

installation is per-user not system wide

ensure that `${HOME}/.local/bin/` is in your PATH

```console
$ make install
```

you can easily uninstall with `make uninstall`

## editions

there are three editions of `enc` here:

- [./src/enc.bootstrap.py](./src/enc.bootstrap.py): bootstrap edition built with aider
- [./src/enc.py](./src/enc.py): python edition built by `enc` from [./src/enc.en](./src/enc.en)
- [./src/main.rs](./src/main.rs): rust edition built by `enc` from [./src/enc.en](./src/enc.en)

the default edition is the rust edition

there are also make targets for the `-bootstrap`, `-rust`, and `-python` editions,
such as `make hello-bootstrap` or `make hello-rust`

## acknowledgments

the bootstrap edition of `enc` was vibe coded with `aider` and `gemini-2.5-pro`

other editions were transpiled from english by `enc` and `gemini-2.5-pro`

model prices were pulled from [aider](https://github.com/Aider-AI/aider/blob/main/aider/resources/model-metadata.json)
