transpile: index.html
.PHONY: transpile

run: transpile
	open index.html
.PHONY: run

styles.css: styles.en
	enc "$<" -o "$@"

main.js: main.en styles.css
	enc "$<" -o "$@" --context-files styles.css

index.html: index.en main.js
	enc "$<" -o "$@" --context-files styles.css:main.js
