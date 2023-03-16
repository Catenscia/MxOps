#!/bin/bash
set -e

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
