#!/bin/bash
set -e

# execute integration test for money print
python -m mxops \
            data \
            delete \
            -n DEV \
            -s integration_test_money_print \
            -y

python -m mxops \
            execute \
            -n DEV \
            -s integration_test_money_print \
            integration_tests/scenes/accounts/devnet_accounts.yaml \
            integration_tests/scenes/money_print


# execute integration test for wrapping
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
            integration_tests/scenes/accounts/devnet_accounts.yaml \
            integration_tests/scenes/wrapping
