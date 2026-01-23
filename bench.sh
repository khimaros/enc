#!/bin/bash

set -euo pipefail

TMP=$(mktemp -d '/tmp/enc-bench-XXXXXXX')

cleanup() {
	popd &>/dev/null
	if [[ "${CLEANUP:-"true"}" != "true" ]]; then
		echo "[*] skipping cleanup, kept ${TMP}"
		return
	fi
	echo "[*] cleaning up temporary dir ${TMP}"
	rm -rf "${TMP}"
}

trap cleanup EXIT

ENC="${ENC:-"${PWD}/target/release/enc"}"

echo "[*] using ${ENC} for bootstrap ..."
echo "[*] running benchmark in ${TMP} ..."

mkdir "${TMP}/src"
cp "src/enc.en" "${TMP}/src/"
cp ".enc.env.example" "${TMP}/"
cp "Makefile" "${TMP}/"
cp "Cargo.toml" "${TMP}/"
cp -r "res/" "${TMP}/"
cp -a "enc" "${TMP}/"

cp ".enc.env" "${TMP}/"

mkdir "${TMP}/testdata"
cp -r "testdata/goldens/" "${TMP}/testdata/"
cp -r "test.sh" "${TMP}/"
cp -r "tests/" "${TMP}/"

pushd "${TMP}" &>/dev/null

#find .

make -s -t bootstrap-deps

touch src/enc.en

make -s ENC="${ENC}" TEST_COMMAND="make test" TEST_ITERATIONS=30 src/main.rs

echo "[*] benchmark completed!"
