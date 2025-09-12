#!/bin/bash
set -e

mxops \
    execute \
    -n $1 \
    -s integration_test_piggy_bank_user_exploit \
    -c \
    integration_tests/setup_scenes/01_accounts.yaml \
    integration_tests/piggy_bank/mxops_scenes/user_exploit \
    integration_tests/piggy_bank/mxops_scenes/endpoint_verification
