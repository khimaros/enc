**Show HN: I wrote a transpiler for English**

Tired of boilerplate? Me too. I wanted a tool that would let me scaffold projects by just describing what I need in plain English, but without sacrificing control.

So I built `enc`: a command-line transpiler that turns `.en` files into any programming language.

`$ enc ./spec.en -o ./src/main.go`

It's not just another GPT wrapper. I built it with the kind of nerdy, paranoid software engineering principles we all appreciate:

*   **Provider Agnostic & No Middleman:** Plug in your own API key for OpenAI, Google, or Anthropic. You pay the provider directly. `enc` is just a stateless tool.

*   **Deterministic Builds:** Pass a `--seed` to get reproducible output. Because "it worked once" isn't good enough.

*   **You Control The Prompt:** The entire meta-prompt is a simple `prompt.tmpl` file you can edit. No hidden "secret sauce" you have to guess at.

*   **Enforce Your Style Guide:** `enc` injects a `HACKING_CONVENTIONS` file into the context. It's like `.editorconfig` for your AI. The generated code adheres to *your* standards for things like comments, line length, and library usage.

*   **Sanity, Not Magic:** It has layered configuration (`.enc.env` in home/project dir + CLI flags), transparent cost estimation after every run, detailed timestamped logs, and robust handling of real-world provider quirks (like Anthropic's `<thinking>` tags or Google's chunked responses).

Here's an example run:

```console
$ enc ./examples/hello.en -o ./examples/hello.rs

debug log path: ./log/20250624_173200.log
provider: google, model: gemini-2.5-pro
transpiling './examples/hello.en' to './examples/hello.rs' (rust)
successfully transpiled './examples/hello.rs'

--- api cost summary ---
tokens: 422 input, 139 output, 1095 thinking
estimated cost: $0.013320
```

The goal is to make scaffolding new projects or tackling boilerplate feel less like typing and more like directing. It's highly configurable and designed to be a predictable, reliable part of a real toolchain.

I've been using it to generate everything from shell scripts to Go servers to SVG graphics.

Check out the full spec/design doc here: [github-link-to-enc.en]

Let me know what you think.