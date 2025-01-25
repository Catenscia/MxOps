#!/bin/bash
set -e

# create a new env and activate it
ENV_NAME=".mxops_tutorial_env"
uv venv $ENV_NAME --python 3.11
source ${ENV_NAME}/bin/activate

# install project
uv pip install -r pyproject.toml

# launch first scene tutorial
cd tutorials/first_scene
bash scripts/build_contract.sh
bash scripts/execute_first_scene.sh

# launch enhanced first scene tutorial
cd ../enhanced_first_scene
bash scripts/build_contract.sh
bash scripts/execute_deploy_scene.sh
bash scripts/execute_ping_scene.sh
bash scripts/execute_pong_scene.sh

# launch queries tutorial
cd ../queries
bash scripts/execute_onedex_with_abi.sh
bash scripts/execute_xexchange_without_abi.sh

# remove env
deactivate
rm -rf ${ENV_NAME}