#!/bin/bash

mxops execute \
        -n DEV \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/ping_pong.yaml
