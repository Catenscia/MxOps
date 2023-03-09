#!/bin/bash

# Some colors
BLUE='\033[0;94m'
NC='\033[0m'

printf "${BLUE}####################\n# Package Build\n####################${NC}\n"

python -m build
EXIT_CODE=$?
printf "\n\n"
exit $EXIT_CODE