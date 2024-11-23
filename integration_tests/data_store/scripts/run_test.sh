#!/bin/bash
set -e

if ! [[ " ${1} " =~ " localnet "|" devnet "|" chain-simulator " ]]; then
    echo "Data store tests not available on ${1}"
    exit 0
fi

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_data_store \
            -c \
            integration_tests/setup_scenes/01_accounts.yaml \
            integration_tests/data_store/mxops_scenes
