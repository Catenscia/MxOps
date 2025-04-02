#!/bin/bash
set -e

# create a new env and activate it
ENV_NAME=".mxops_examples_env"
uv venv $ENV_NAME --python 3.11
source ${ENV_NAME}/bin/activate

# install project
uv pip install .

# launch ping_pong example
cd examples/enhanced_first_scene
bash scripts/build_contract.sh
bash scripts/execute_deploy_scene.sh
bash scripts/execute_ping_scene.sh
bash scripts/execute_pong_scene.sh

# launch queries tutorial
cd ../queries
bash scripts/execute_queries.sh

# launch trader tutorial
cd ../trader
bash scripts/run.sh


# remove env
cd ../..
deactivate
rm -rf ${ENV_NAME}