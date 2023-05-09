#!/bin/bash
set -e

if ! [[ " ${1} " =~ " devnet " ]]; then
    echo "Wrapping tests not available on ${1}"
    exit 0
fi

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_wrapping \
            -d \
            integration_tests/setup_scenes/01_accounts.yaml \
            integration_tests/wrapping/mxops_scenes/
