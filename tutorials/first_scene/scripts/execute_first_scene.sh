#!/bin/bash

mxops data delete \
            -n devnet \
            -s mxops_tutorial_first_scene

mxops execute \
        -n devnet \
        -s mxops_tutorial_first_scene \
        first_scene.yaml