set -e

if [ "$1" == "chain-simulator" ]; then
    scene="integration_tests/setup_scenes/02a_chain_simulator_faucet.yaml"
else
    scene="integration_tests/setup_scenes/02b_r3d4_faucet.yaml"
fi

python -m mxops \
            execute \
            -n $1 \
            -s integration_test \
            integration_tests/setup_scenes/01_accounts.yaml \
            $scene \
