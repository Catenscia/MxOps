#!/bin/bash

# delete previous scenario data
python -m mxops \
            data \
            delete \
            -n DEV \
            -s integration_tests

# execute integrations scenes
python -m mxops \
            execute \
            -n DEV \
            -s integration_tests \
            integration_tests/scenes/accounts/devnet_accounts.yaml \
            integration_tests/scenes

# check correct execution