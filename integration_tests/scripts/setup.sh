set -e

if ! [[ " ${1} " =~ " localnet "|" devnet "|" chain-simulator " ]]; then
    echo "integration setup not available on ${1}"
    exit 0
fi

python -m mxops \
            execute \
            -n $1 \
            -s integration_test \
            integration_tests/setup_scenes