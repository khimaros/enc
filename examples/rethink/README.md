# enc/examples/rethink

this is an example of any-to-english transpilation

first a simple prompt is made into a more detailed prompt: `enc start.en -o prompt.en`

then that prompt is used to generate a python program: `enc prompt.en -o main.py`

and finally the python program is described: `enc main.py -o describe.md`
