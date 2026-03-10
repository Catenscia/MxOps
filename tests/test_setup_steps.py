import os
from pathlib import Path
import shutil
from unittest.mock import patch

from multiversx_sdk import Account
import pytest

from mxops import errors
from mxops.enums import NetworkEnum
from mxops.execution.steps import ChainSimulatorSetStateStep, GenerateWalletsStep


def test_generate_n_wallet_step():
    # Given
    step = GenerateWalletsStep("./tests/data/TEMP_UNIT_TEST/wallets/folder", 3)

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/folder")
    files = os.listdir(save_folder)
    assert len(files) == 3
    for file in files:
        account = Account.new_from_pem(save_folder / file)
        bech32, extension = file.split(".")
        assert bech32 == account.address.to_bech32()
        assert extension == "pem"

    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")


def test_generate_named_wallet_step():
    # Given
    step = GenerateWalletsStep(
        "./tests/data/TEMP_UNIT_TEST/wallets/folder", ["charles", "david"]
    )

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/folder")
    files = os.listdir(save_folder)
    assert set(files) == {"charles.pem", "david.pem"}
    for file in files:
        _ = Account.new_from_pem(save_folder / file)

    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")


def test_generate_keystore_wallet_step():
    # Given
    os.environ["TEST_WALLET_PASSWORD"] = "test_password_123"
    step = GenerateWalletsStep(
        "./tests/data/TEMP_UNIT_TEST/wallets/keystore_folder",
        ["alice_ks", "bob_ks"],
        format="keystore",
        password_env_var="TEST_WALLET_PASSWORD",
    )

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/keystore_folder")
    files = os.listdir(save_folder)
    assert set(files) == {"alice_ks.json", "bob_ks.json"}
    for file in files:
        _ = Account.new_from_keystore(
            save_folder / file, os.environ["TEST_WALLET_PASSWORD"]
        )

    # Cleanup
    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")
    del os.environ["TEST_WALLET_PASSWORD"]


def test_generate_n_keystore_wallet_step():
    # Given
    os.environ["TEST_WALLET_PASSWORD"] = "test_password_456"
    step = GenerateWalletsStep(
        "./tests/data/TEMP_UNIT_TEST/wallets/keystore_n",
        2,
        format="keystore",
        password_env_var="TEST_WALLET_PASSWORD",
    )

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/keystore_n")
    files = os.listdir(save_folder)
    assert len(files) == 2
    for file in files:
        account = Account.new_from_keystore(
            save_folder / file, os.environ["TEST_WALLET_PASSWORD"]
        )
        name, extension = file.rsplit(".", 1)
        assert name == account.address.to_bech32()
        assert extension == "json"

    # Cleanup
    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")
    del os.environ["TEST_WALLET_PASSWORD"]


MOCK_BECH32 = "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
MOCK_KEYS = {"736166655f70726963655f63757272656e745f696e646578": "00000000"}


@pytest.fixture
def chain_simulator_scenario(scenario_data, chain_simulator_network):
    """Set both Config and ScenarioData to chain simulator network."""
    original = scenario_data.network
    scenario_data.network = NetworkEnum.CHAIN_SIMULATOR
    yield scenario_data
    scenario_data.network = original


def test_chain_simulator_set_state_wrong_network(scenario_data):
    """Network is LOCAL by default, step should reject it."""
    step = ChainSimulatorSetStateStep(address=MOCK_BECH32, keys=MOCK_KEYS)
    with pytest.raises(errors.WrongNetworkForStep):
        step.execute()


def test_chain_simulator_set_state_success(chain_simulator_scenario):
    step = ChainSimulatorSetStateStep(address=MOCK_BECH32, keys=MOCK_KEYS)
    with patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_address_state"
    ) as mock_set:
        step.execute()
        mock_set.assert_called_once_with(MOCK_BECH32, MOCK_KEYS)


def test_chain_simulator_set_state_empty_keys(chain_simulator_scenario):
    step = ChainSimulatorSetStateStep(address=MOCK_BECH32, keys={})
    with pytest.raises(errors.InvalidSceneDefinition):
        step.execute()


def test_chain_simulator_set_state_invalid_hex_key(chain_simulator_scenario):
    step = ChainSimulatorSetStateStep(
        address=MOCK_BECH32, keys={"not_hex!": "00"}
    )
    with pytest.raises(errors.InvalidSceneDefinition, match="key must be hex-encoded"):
        step.execute()


def test_chain_simulator_set_state_invalid_hex_value(chain_simulator_scenario):
    step = ChainSimulatorSetStateStep(
        address=MOCK_BECH32, keys={"00": "not_hex!"}
    )
    with pytest.raises(
        errors.InvalidSceneDefinition, match="value must be hex-encoded"
    ):
        step.execute()
