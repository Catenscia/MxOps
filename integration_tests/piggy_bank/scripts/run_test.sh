#!/bin/bash
set -e

# execute integration test for money print
python -m mxops \
            data \
            delete \
            -n $1 \
            -s integration_test_piggy_bank_user_exploit \
            -y

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_piggy_bank_user_exploit \
            "integration_tests/piggy_bank/mxops_scenes/accounts/${1}_accounts.yaml" \
            integration_tests/piggy_bank/mxops_scenes/user_exploit
