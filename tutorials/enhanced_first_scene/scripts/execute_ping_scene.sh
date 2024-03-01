#!/bin/bash

mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/02_ping.yaml
