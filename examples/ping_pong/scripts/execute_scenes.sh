#!/bin/bash

export PING_PONG_AMOUNT=100000000000000000
export PONG_WAIT_TIME=1

mxops execute \
        -n devnet \
        -s ping_pong_tutorial \
        -d \
        mxops_scenes/setup/reload_account.yaml \
        mxops_scenes
