#!/bin/bash
set -e

if ! [[ " ${1} " =~ " chain-simulator " ]]; then
    echo "Token thin-air tests not available on ${1}"
    exit 0
fi

uv run mxops \
    execute \
    -n $1 \
    -s integration_test_token_thin_air \
    -c \
    integration_tests/setup_scenes/01_accounts.yaml \
    integration_tests/token_thin_air/mxops_scenes
