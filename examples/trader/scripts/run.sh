#!/bin/bash

rm ./wallets/*

mxops execute \
        -n chain-simulator \
        -s mxops_tutorial_account_clone \
        -c \
        mxops_scenes