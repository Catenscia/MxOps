#!/bin/bash

uv run mxops execute \
        -n devnet \
        -s ping_pong_tutorial \
        -c \
        mxops_scenes/setup/account_creation.yaml
