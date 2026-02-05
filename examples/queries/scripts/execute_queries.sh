#!/bin/bash

uv run mxops execute \
        -n mainnet \
        -s queries_tutorial \
        -d \
        mxops_scenes/single_pair_queries.yaml \
        mxops_scenes/all_pairs_queries.yaml
