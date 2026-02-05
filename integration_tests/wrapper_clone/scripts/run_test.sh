#!/bin/bash
set -e

if ! [[ " ${1} " =~ " chain-simulator " ]]; then
    echo "Wrapper clone tests not available on ${1}"
    exit 0
fi

uv run mxops \
    execute \
    -n $1 \
    -s integration_test_wrapper_clone \
    -c \
    integration_tests/setup_scenes/01_accounts.yaml \
    integration_tests/wrapper_clone/mxops_scenes