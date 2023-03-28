#!/bin/bash
set -e

if ! [[ " ${1} " =~ " devnet " ]]; then
    echo "Wrapping tests not available on ${1}"
    exit 0
fi

python -m mxops \
            data \
            delete \
            -n $1 \
            -s integration_test_wrapping \
            -y

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_wrapping \
            "integration_tests/wrapping/mxops_scenes/accounts/${1}_accounts.yaml" \
            integration_tests/wrapping/mxops_scenes/
