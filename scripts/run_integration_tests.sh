#!/bin/bash
set -e

# create a new env and activate it
ENV_NAME=".mxops_integration_test_env_$1"
uv venv $ENV_NAME --python 3.11
source ${ENV_NAME}/bin/activate

# install project
uv pip install .

# Check if there are at least 2 arguments and second is "true"
if [ $# -ge 2 ] && [ "$2" = "faucet" ]; then
    bash integration_tests/scripts/setup.sh $1
fi

# execute integration_tests
bash scripts/launch_integration_tests.sh $1

# remove env
deactivate
rm -rf ${ENV_NAME}