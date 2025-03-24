#!/bin/bash
set -e

mxops \
    execute \
    -n $1 \
    -s integration_test_data_store \
    -c \
    integration_tests/setup_scenes/01_accounts.yaml \
    integration_tests/data_store/mxops_scenes
