#!/bin/bash

rm wallets/*

mxops execute \
        -n devnet \
        -s first_scenario \
        -c \
        scenes/01_setup.yaml