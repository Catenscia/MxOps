#!/bin/bash
set -e

if ! [[ " ${1} " =~ " localnet "|" devnet " ]]; then
    echo "Token management tests not available on ${1}"
    exit 0
fi

# execute integration test for the fungible token
python -m mxops \
            data \
            delete \
            -n $1 \
            -s integration_test_token_management_token_issuances \
            -y

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_token_management_token_issuances \
            "integration_tests/token_management/mxops_scenes/accounts.yaml" \
            integration_tests/token_management/mxops_scenes/tokens_issuances.yaml
