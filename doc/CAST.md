# CAST

```console
$ cat examples/hello.en

hello: output the string "hello, <input>!" based on the user's input

main: call the hello function with the first argv. default to "world"

$ enc examples/hello.en -o examples/hello.c
transpiling 'examples/hello.en' to c using gemini-2.5-pro...
successfully wrote output to 'examples/hello.c'

--- api cost summary ---
provider: google, model: gemini-2.5-pro
tokens: 281 input, 175 output, 1326 thinking
estimated cost:
  - input   : $0.000351
  - output  : $0.001750
  - thinking: $0.013260
total: $0.015361

$ cc examples/hello.c -o examples/hello

$ ./examples/hello fnord
hello, fnord!
```
