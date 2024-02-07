#!/bin/bash

export PING_PONG_AMOUNT=1000000000000000000
export PONG_WAIT_TIME=1

mxops data delete \
            -n devnet \
            -s mxops_tutorial_enhanced_first_scene \
            -y

mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/01_deploy.yaml
