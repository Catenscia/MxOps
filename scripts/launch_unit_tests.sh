#!/bin/bash

# Some colors
BLUE='\033[0;94m'
RED='\033[0;91m'
GREEN='\033[0;92m'
NC='\033[0m'

printf "${BLUE}############\n# Unit Tests\n############${NC}\n"

OUTPUT=$(coverage run -m pytest tests --color=yes -vv)
EXIT=$?
echo -e "${OUTPUT}"

SUB="FAILED tests/"
if [[ $EXIT -ne 0 || "${OUTPUT}" == *"${SUB}"* ]];
then
    printf "${RED}Unit tests failed${NC}\n"
    exit 1
else
    coverage html
    printf "${GREEN}Unit tests success${NC}\n\n\n"
fi
