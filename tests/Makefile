test:
	#cd ../examples/context/ && ../../enc --help
	cd ../examples/context/ && ../../enc --show-config
	cd ../examples/context/ && ../../enc main.en -o main.py --context-files context.txt
	cd ../examples/context/ && python main.py
.PHONY: test

test-rust:
	#cd ../examples/context/ && ../../enc-rust --help
	cd ../examples/context/ && ../../enc-rust --show-config
	cd ../examples/context/ && ../../enc-rust main.en -o main.py --context-files context.txt
	cd ../examples/context/ && python main.py
.PHONY: test-rust

test-python:
	#cd ../examples/context/ && ../../enc-python --help
	cd ../examples/context/ && ../../enc-python --show-config
	cd ../examples/context/ && ../../enc-python main.en -o main.py --context-files context.txt
	cd ../examples/context/ && python main.py
.PHONY: test-python
