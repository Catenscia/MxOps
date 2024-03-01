#!/bin/bash
set -e

# Initialize Conda
source ~/anaconda3/etc/profile.d/conda.sh

# build
rm dist/*
python -m build

# create a new env
ENV_NAME="mxops_tutorial_test_env"
conda create -n $ENV_NAME python=3.11 -y
conda activate $ENV_NAME

# install project
pip install dist/*whl
pip install -r requirements-dev.txt

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
conda deactivate
conda env remove -n $ENV_NAME -y