#!/bin/bash

rm -rf ./contract
git clone https://github.com/multiversx/mx-ping-pong-sc contract
touch ./contract/.gitkeep
sc-meta all build