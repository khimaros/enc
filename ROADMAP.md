# ROADMAP

```
[ ] macos builds: https://github.com/OlaProeis/Ferrite/blob/master/.github/workflows/release.yml
[ ] make test attempts and retries more KV cache optimal
[ ] introduce diff mode as an alterantive to whole file output

[ ] make test should search for key fragment AIza
[ ] ensure deterministic output with the same input file
[?] solution for build boilerplate (Cargo.toml, requirements.txt, etc)
[x] add package.json and tsconfig.json for Node.js support
[?] split src/enc.en into separate files

[x] enhance benchmark mode: support provider/model pairs, target languages, and HTML report
[x] benchmark mode: how many shots to produce enc with passing tests?
[x] automated testing for PROVIDER=openai
[x] automated testing for PROVIDER=anthropic
[x] automated testing for llama.cpp server provider
[x] allow english to english tranpilation (enc main.en -o main.better.en)
[x] standardize writing style in prompt template
[x] build ./res/ resources into the rust binary
[x] move language map out into separate data file
[x] golden tests
[x] rust port
[x] create an example with multiple source files
[x] move pricing data out into a separate data file
[x] support for additional context files
[x] incorporate system prompt formatting from cline/cursor/etc

[~] add a test for grounded mode
```
