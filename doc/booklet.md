<!-- NOTICE: this file was generated by https://github.com/khimaros/enc -->
<!-- invocation: ./enc doc/booklet.en -o doc/booklet.md --context-files README.md:.enc.env.example:Makefile:src/enc.en:examples/multi/README.md:examples/parasite/README.md:examples/balloons/README.md:examples/web/README.md:examples/context/README.md -->

# enc: The English to Anything Transpiler

`enc` is a powerful, self-hosting transpiler that converts plain English descriptions of code into any other programming language with the help of Generative AI. You write your logic in simple `.en` files, and `enc` handles the translation, allowing you to focus on the "what" rather than the "how."

Inspired by `english-lang`, `enc` takes this concept further by being entirely self-hosting. The English definition for `enc` itself can be found in `src/enc.en`, which is used to generate the Rust and Python implementations of the tool.

## Quick Start

Get up and running with `enc` in a few simple steps:

1.  **Copy the example environment file:**
    ```console
    $ cp ./.enc.env.example ~/.enc.env
    ```
    This creates your personal configuration file in your home directory.

2.  **Add your API Keys:**
    ```console
    $ editor ~/.enc.env
    ```
    Open the newly created `~/.enc.env` file and add your API key for your preferred AI provider (e.g., Google, OpenAI, Anthropic).

3.  **Build the project:**
    ```console
    $ make
    ```
    This command transpiles `enc.en` into Rust source code and compiles the binary.

4.  **Run the "hello world" example:**
    ```console
    $ make hello
    ```
    This will use the newly built `enc` to transpile `examples/hello.en` to C, compile it, and run the resulting executable.

## Installation

To install `enc` for system-wide use:

1.  **Ensure `~/.local/bin` is in your `PATH`:**
    `enc` installs its binary to `${HOME}/.local/bin/`. Make sure this directory is included in your system's `PATH` environment variable.
    ```console
    $ export PATH="${HOME}/.local/bin:$PATH"
    ```
    You may want to add this line to your shell's startup file (e.g., `~/.bashrc`, `~/.zshrc`).

2.  **Create and configure your environment file:**
    ```console
    $ cp ./.enc.env.example ~/.enc.env
    $ editor ~/.enc.env  # add your keys
    ```

3.  **Run the installation command:**
    ```console
    $ make install
    ```
    This builds the project and installs the `enc` binary and its necessary resource files.

To uninstall `enc`, simply run:
```console
$ make uninstall
```

## Basic Usage

The primary function of `enc` is to take an English source file (`.en`) and produce a source file in a target language. The target language is inferred from the output file's extension.

For example, given the following English source file `examples/hello.en`:

```english
hello: output the string "hello, <input>!" based on the user's input

main: call the hello function with the first argv. default to "world"
```

You can transpile it to Rust with this command:

```console
$ enc ./examples/hello.en -o ./examples/hello.rs
```

This will produce the following `examples/hello.rs` file:

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

## Design and Architecture

`enc` is designed to be a flexible and transparent interface to code-generating Large Language Models (LLMs). Its architecture is centered around a few key concepts.

### Layered Configuration

`enc` uses a layered configuration system to provide flexibility. Settings are loaded in the following order of precedence, with later sources overriding earlier ones:

1.  **Home Config:** `~/.enc.env` (for user-wide defaults)
2.  **Working Directory Config:** `./.enc.env` (for project-specific settings)
3.  **Command-line Flags:** (for one-off overrides)

The final "consolidated configuration" is logged at the start of each run (with secrets redacted). You can view this configuration without running a transpilation by using the `--show-config` flag.

### Prompt Templating

`enc` does not have any hardcoded prompts. Instead, it uses a template file (located at `PROMPT_TEMPLATE_PATH`, typically `./res/prompt.tmpl`) to construct the final prompt sent to the LLM. This allows for easy experimentation and customization of the prompt.

The template engine performs a single-pass replacement of the following variables:

*   `{{generation_command}}`: The full command used to invoke `enc`.
*   `{{generation_config}}`: The redacted, consolidated configuration.
*   `{{target_language}}`: The programming language inferred from the output file's extension.
*   `{{output_path}}`: The destination file path.
*   `{{english_content}}`: The full content of the input `.en` file.
*   `{{hacking_conventions}}`: The content of the file specified by `HACKING_CONVENTIONS`, if it exists.
*   `{{context_files}}`: The formatted content of all files provided via `CONTEXT_FILES`. Each file is presented with a markdown header containing its path, followed by its content in a fenced code block.

### Code Generation

The core logic of `enc` is the code generation itself.

*   **Language Detection:** The target language is automatically determined from the output file's extension (e.g., `.rs` -> `rust`, `.py` -> `python`). If the extension is not recognized, the extension itself is passed to the LLM as the language name.
*   **Output Cleaning:** `enc` anticipates that LLMs may wrap their generated code in markdown code fences (e.g., ` ```rust ... ``` `). It automatically strips these fences from the first and last lines of the output before writing to the destination file.

### AI Provider Support

`enc` can work with multiple LLM providers. At runtime, you only need to provide an API key for the selected provider.
*   **Google:** Supports models like `gemini-2.5-pro`.
*   **OpenAI:** Supports OpenAI-compatible APIs and models like `gpt-4o-mini`.
*   **Anthropic:** Supports models like `claude-3-7-sonnet-20250219`.

### Logging and Cost Tracking

For transparency and debugging, `enc` maintains detailed logs.

*   A new log file is created for each invocation in the `LOGS_PATH` directory, with a timestamped filename (e.g., `20250624_173200.log`).
*   The log file contains the consolidated configuration (with redacted API keys), the fully expanded prompt, and the raw response from the LLM.
*   After each successful API call, a cost summary is printed to the console. It breaks down the cost by input, output, and thinking tokens, based on pricing data from `PRICING_DATA_PATH`.

## Configuration Reference

All aspects of `enc`'s behavior can be configured via environment variables or command-line flags. Flags always take precedence over environment variables. The input `.en` file is a required positional argument, and the output file is specified with `-o`/`--output`.

| Environment Variable | Command-line Flag | Description |
| --- | --- | --- |
| `PROVIDER` | `--provider` | The AI provider to use: "google", "openai", or "anthropic". |
| `MODEL` | `--model` | The specific language model for inference (e.g., "gemini-2.5-pro"). |
| `MAX_TOKENS` | `--max-tokens` | The maximum number of tokens for the LLM to generate in its response. Defaults to the model's maximum. |
| `THINKING_BUDGET` | `--thinking-budget` | The maximum number of tokens allocated for "thinking" or pre-processing steps, for models that support it. |
| `GROUNDED_MODE` | `--grounded-mode` | If `true`, adds the existing content of the output file (if it exists) to the context files, to guide the LLM. Defaults to `false`. |
| `SEED` | `--seed` | An integer seed for deterministic, reproducible outputs. If empty, a random seed is used. Note: The "google" provider does not support this; it sets temperature to 0 instead. |
| `HACKING_CONVENTIONS` | `--hacking-conventions` | Path to a markdown file containing coding conventions and style guides to be included in the prompt. |
| `CONTEXT_FILES` | `--context-files` | A colon-separated list of additional file paths to include as context in the prompt. |
| `GEMINI_API_KEY` | `--gemini-api-key` | Your API key for the Google Generative AI service. |
| `OPENAI_API_KEY` | `--openai-api-key` | Your API key for OpenAI or an OpenAI-compatible service. |
| `OPENAI_API_BASE` | `--openai-api-base` | The base URL for an OpenAI-compatible API endpoint. |
| `LOGS_PATH` | `--logs-path` | The directory where log files will be stored. Defaults to `./log/`. |
| `PROMPT_TEMPLATE_PATH` | `--prompt-template-path` | The path to the prompt template file. Defaults to `./res/prompt.tmpl`. |
| `PRICING_DATA_PATH` | `--pricing-data-path` | The path to the JSON file containing model pricing data. Defaults to `./res/pricing.json`. |
| *N/A* | `--show-config` | Prints the final, redacted configuration and exits immediately. |

## Makefile Targets

The `Makefile` provides a comprehensive set of targets for building, testing, and managing the `enc` project.

### Main Targets

| Target | Description |
| --- | --- |
| `all` | The default target. Transpiles `enc` to Rust, builds the Rust binary, and generates all documentation. |
| `install` | Builds the `enc` binary and installs it to `${HOME}/.local/bin/` along with its resource files to `${XDG_DATA_HOME}/enc/`. |
| `uninstall` | Removes the installed `enc` binary and its associated resource directory. |
| `build` | A shortcut to transpile `enc.en` to Rust and compile the resulting `src/main.rs`. |
| `clean` | Removes build artifacts, including the `target` directory, Python cache, and compiled examples. |

### Transpilation & Bootstrapping

`enc` is self-hosting, which involves an initial "bootstrap" version to generate the primary versions.

| Target | Description |
| --- | --- |
| `transpile` | Generates all target language versions of `enc` (`src/enc.py`, `src/main.rs`) from `src/enc.en`. |
| `transpile-rust` | Uses the existing `enc` binary to transpile `src/enc.en` to Rust (`src/main.rs`). |
| `transpile-python` | Uses the existing `enc` binary to transpile `src/enc.en` to Python (`src/enc.py`). |
| `bootstrap-rust` | Uses the initial bootstrap script (`src/enc.bootstrap.py`) to transpile `src/enc.en` to Rust. |
| `bootstrap-python`| Uses the initial bootstrap script (`src/enc.bootstrap.py`) to transpile `src/enc.en` to Python. |

### Testing & Formatting

| Target | Description |
| --- | --- |
| `precommit` | A convenience target to run `format` and `test` before committing changes. |
| `test` | Runs the primary test suite, which consists of golden file tests. |
| `test-goldens` | Executes golden file tests by running `./test.sh test`. |
| `update-goldens` | Updates the expected "golden" output files for the tests by running `./test.sh update`. |
| `format` | Formats all supported source code in the project (currently Python). |
| `format-python` | Formats Python source files using `black`. |
| `format-rust` | Formats Rust source files using `rustfmt`. |

### Examples & Demos

| Target | Description |
| --- | --- |
| `hello` | Runs the "hello world" example using the default Rust-based `enc` binary. |
| `hello-bootstrap` | Runs the "hello world" example using the bootstrap Python script. |
| `hello-python` | Runs the "hello world" example using the Python-based `enc-python` runner. |
| `hello-rust` | Runs the "hello world" example using the Rust-based `enc-rust` runner. |
| `examples` | Builds and runs all the project examples in the `examples/` subdirectories. |

### Documentation

| Target | Description |
| --- | --- |
| `docs` | Generates all documentation artifacts, including `doc/booklet.md` (this file), `doc/icon.png`, and the `doc/enc.cast.gif` animation. |
| `doc/enc.cast.gif` | Creates an animated GIF terminal session demonstrating `enc`'s usage. |

## Examples

The `examples/` directory contains several projects that demonstrate `enc`'s capabilities. Each example has its own `Makefile` and can typically be run with `make run` from within its directory.

*   **`context`**: Demonstrates how to provide additional context files to the LLM using the `--context-files` flag to inform code generation.
*   **`multi`**: Shows how to structure a project with multiple `.en` files that depend on each other, creating a stable API between components.
*   **`parasite`**: Illustrates how `enc`-generated code can be integrated into a larger, hand-crafted codebase.
*   **`balloons`**: A simple game written in Rust, entirely generated by `enc`, demonstrating a more complex application.
*   **`web`**: A simple web application, demonstrating `enc`'s ability to generate HTML, CSS, and server-side logic.

## Acknowledgments

*   The bootstrap edition of `enc` was vibe coded with `aider` and `gemini-2.5-pro`.
*   Other editions were transpiled from English by `enc` itself and `gemini-2.5-pro`.
*   Model pricing data was sourced from the [Aider project](https://github.com/Aider-AI/aider/blob/main/aider/resources/model-metadata.json).