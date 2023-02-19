#!/bin/bash
set -e

python -m mxops \
            data \
            delete \
            -n DEV \
            -s integration_test_wrapping \
            -y

python -m mxops \
            execute \
            -n DEV \
            -s integration_test_wrapping \
            integration_tests/wrapping/mxops_scenes/accounts/devnet_accounts.yaml \
            integration_tests/wrapping/mxops_scenes/
