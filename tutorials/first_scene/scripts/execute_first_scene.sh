#!/bin/bash

mxops data delete \
            -n DEV \
            -s mxops_tutorial_first_scene

mxops execute \
        -n DEV \
        -s mxops_tutorial_first_scene \
        first_scene.yaml