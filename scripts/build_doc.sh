#!/bin/bash

# Some colors
BLUE='\033[0;94m'
RED='\033[0;91m'
GREEN='\033[0;92m'
NC='\033[0m'

printf "${BLUE}#########################\n# Documentation Build\n#########################${NC}\n"

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
    printf "${GREEN}Documentation build success${NC}\n\n\n"
fi