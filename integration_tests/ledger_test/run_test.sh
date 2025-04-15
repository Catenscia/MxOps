#!/bin/bash
set -e

if ! [[ " ${1} " =~ " chain-simulator " ]]; then
    echo "Ledger test not available on ${1}"
    exit 0
fi

mxops \
    execute \
    -n $1 \
    -s integration_test_ledger \
    -c \
    integration_tests/ledger_test/mxops_scene.yaml