#!/bin/bash
set -e

# create a new env and activate it
ENV_NAME=".mxops_examples_env"
uv venv $ENV_NAME --python 3.11
source ${ENV_NAME}/bin/activate

# install project
uv pip install .

# launch first scene example
cd examples/first_scene
bash scripts/build_contract.sh
bash scripts/execute_first_scene.sh

# launch enhanced first scene example
cd ../enhanced_first_scene
bash scripts/build_contract.sh
bash scripts/execute_deploy_scene.sh
bash scripts/execute_ping_scene.sh
bash scripts/execute_pong_scene.sh

# launch queries tutorial
cd ../queries
bash scripts/execute_onedex.sh

# remove env
cd ../..
deactivate
rm -rf ${ENV_NAME}