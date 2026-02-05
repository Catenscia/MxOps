#!/bin/bash

rm wallets/*

uv run mxops execute \
        -n devnet \
        -s first_scenario \
        -c \
        scenes/01_setup.yaml