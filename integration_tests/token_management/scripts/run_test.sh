#!/bin/bash
set -e

mxops \
    execute \
    -n $1 \
    -s integration_test_token_management \
    -c \
    integration_tests/setup_scenes/01_accounts.yaml \
    integration_tests/token_management/mxops_scenes
