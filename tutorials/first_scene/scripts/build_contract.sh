#!/bin/bash

rm -rf ./contract/*
touch ./contract/.gitkeep
git clone https://github.com/multiversx/mx-ping-pong-sc contract
cd contract/ping-pong
mxpy contract build