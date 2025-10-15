# CONTRIBUTING

see style guidelines in HACKING.md

## build

build using `make`

## test

run `make hello` for a quick test during development

run `make test` for comprehensive tests before committing to git

if there are intentional changes to behavior run `make update-goldens`

always inspect the goldens diff closely

## release

update version in Cargo.toml

prepare a release with `make release`

update the version number in README.md

cut a release in GitHub using the template
