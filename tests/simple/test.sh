#!/bin/bash

set -euo pipefail

CONTEXT=$(cat context.txt)

RESULT=$(/usr/bin/env python3 main.py)

if [[ "${CONTEXT}" != "${RESULT}" ]]; then
	echo "incorrect output from running main.py"
	exit 1
fi
