#!/bin/bash

mxops data delete \
            -n devnet \
            -s mxops_tutorial_first_scene \
            -y

mxops execute \
        -n devnet \
        -s mxops_tutorial_first_scene \
        first_scene.yaml