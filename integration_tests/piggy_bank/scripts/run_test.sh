#!/bin/bash
set -e

# execute integration test for money print
python -m mxops \
            data \
            delete \
            -n DEV \
            -s integration_test_piggy_bank_user_exploit \
            -y

python -m mxops \
            execute \
            -n DEV \
            -s integration_test_piggy_bank_user_exploit \
            integration_tests/piggy_bank/mxops_scenes/accounts/devnet_accounts.yaml \
            integration_tests/piggy_bank/mxops_scenes/user_exploit