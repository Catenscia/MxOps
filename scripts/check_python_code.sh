#!/bin/bash

# Some colors
BLUE='\033[0;94m'
RED='\033[0;91m'
GREEN='\033[0;92m'
NC='\033[0m'



# launch bandit on the mxops package
# it is mandatory to obtain a valid check
printf "${BLUE}##########\n# Bandit\n##########${NC}\n"
OUTPUT=$(bandit -r mxops)
echo "${OUTPUT}"
SUB="No issues identified"
if [[ "${OUTPUT}" != *"${SUB}"* ]];
then
    printf "${RED}bandit output is not empty, test failed${NC}\n"
    exit 1
else
    printf "${GREEN}bandit success${NC}\n\n\n"
fi

# launch flake8 on the entire repository
# it is mandatory to obtain valid check
printf "${BLUE}##########\n# Flake8\n##########${NC}\n"
OUTPUT=$(flake8 .)
if [ ! -z "${OUTPUT}" ]
then
    echo "${OUTPUT}"
    printf "${RED}flake8 output is not empty, test failed${NC}\n"
    exit 2
else
    printf "${GREEN}flake8 success${NC}\n\n\n"
fi

# launch pylint only on the mxops package
# score should be equal or above 9.5
printf "${BLUE}##########\n# Pylint\n##########${NC}\n"
OUTPUT=$(pylint mxops)
echo "${OUTPUT}"
SCORE=$(sed -n '$s/[^0-9]*\([0-9.]*\).*/\1/p' <<< "$OUTPUT")
TEST=$(echo "${SCORE} < 9.5" |bc -l)

if echo "$OUTPUT" | grep -q "^mxops/.*: E[0-9]*"
then
    printf "${RED}pylint has detected an error, test failed${NC}\n"
    exit 3
elif [ $TEST -ne 0 ]; then
    printf "${RED}pylint score below 9.5, test failed${NC}\n"
    exit 4
else
    printf "${GREEN}pylint success${NC}\n\n\n"
fi

exit 0