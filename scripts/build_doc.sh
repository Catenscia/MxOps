#!/bin/bash

# Some colors
RED='\033[0;91m'
GREEN='\033[0;92m'
NC='\033[0m'

OUTPUT=$(pyspelling)
SUB="Spelling check passed"
if [[ "${OUTPUT}" != *"${SUB}"* ]];
then
    printf "${RED}Spelling check failed${NC}\n"
    echo "${OUTPUT}"
    exit 1
else
    printf "${GREEN}PySpelling success${NC}\n"
fi

cd docs
OUTPUT=$(make html)

if [[ "${OUTPUT}" == *"ERROR"* ]];
then
    printf "${RED}Documentation build got some errors${NC}\n"
    echo "${OUTPUT}"
    exit 1
else
    printf "${GREEN}Documentation build success${NC}\n"
fi