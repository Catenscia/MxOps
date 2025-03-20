import os
from pathlib import Path
import pytest
from unittest.mock import patch

from multiversx_sdk.network_providers.resources import NetworkConfig

from mxops.config.config import Config
from mxops.data.execution_data import (
    ExternalContractData,
    InternalContractData,
    ScenarioData,
    TokenData,
    delete_scenario_data,
)
from mxops.enums import NetworkEnum, TokenTypeEnum
from mxops.execution.account import AccountsManager


@pytest.fixture(scope="session", autouse=True)
def network():
    Config.set_network(NetworkEnum.LOCAL)
    Config.get_config().set_option("DATA_PATH", "./tests/.mxops_data")


@pytest.fixture(scope="session", autouse=True)
def mock_network_config():
    with patch(
        "mxops.config.config.ProxyNetworkProvider.get_network_config"
    ) as mock_method:
        mock_method.return_value = NetworkConfig(
            {},
            chain_id="D",
            gas_per_data_byte=1500,
            genesis_timestamp=1694000000,
            round_duration=6000,
            num_rounds_per_epoch=2400,
            min_gas_limit=50000,
            min_gas_price=1000000000,
            extra_gas_limit_for_guarded_transactions=10000,
            gas_price_modifier=0.01,
            num_shards=3,
        )
        yield


@pytest.fixture(scope="session", autouse=True)
def test_data_folder_path():
    return Path("./tests/data")


@pytest.fixture(scope="session", autouse=True)
def scenario_data(network):  # must be executed after the network fixture
    ScenarioData.create_scenario("pytest_scenario", overwrite=True)
    contract_id = "my_test_contract"
    address = "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
    wasm_hash = "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451"
    scenario_data = ScenarioData.get()
    scenario_data.add_contract_data(
        InternalContractData(
            contract_id=contract_id,
            bech32=address,
            wasm_hash=wasm_hash,
            deploy_time=1,
            last_upgrade_time=1,
            saved_values={"query_result_1": [0, 1, {2: "abc"}]},
        )
    )
    scenario_data.add_contract_data(
        ExternalContractData(
            "piggy-bank",
            "erd1qqqqqqqqqqqqqpgqxt0y7s830gh5r38ypsslt9hrd2zxn98rv5ys0jd2mg",
            saved_values={},
        )
    )
    scenario_data.set_contract_abi_from_source(
        "piggy-bank", Path("./tests/data/abis/piggy-bank.abi.json")
    )
    scenario_data.add_token_data(
        token_data=TokenData("bob_token", "BOBT", "BOBT-123456", TokenTypeEnum.FUNGIBLE)
    )
    scenario_data.set_value("user", "alice")
    scenario_data.set_value("suffix", "token")
    scenario_data.set_value("my_list", ["item1", "item2", "item3", {"item4-key1": "e"}])
    scenario_data.set_value(
        "my_dict", {"key1": "1", "key2": 2, "key3": ["x", "y", "z"]}
    )

    os.environ["OWNER_NAME"] = "bob"

    yield scenario_data
    delete_scenario_data("pytest_scenario", ask_confirmation=False)


@pytest.fixture(scope="session", autouse=True)
def accounts_manager(scenario_data):  # scenario data must be initialized
    accounts_manager = AccountsManager()
    accounts_manager.load_register_pem_account(
        pem_path=Path("./tests/data/test_user_A.pem"),
        account_id="test_user_A",
    )
    accounts_manager.load_register_pem_account(
        pem_path=Path("./tests/data/test_user_B.pem"),
        account_id="test_user_B",
    )
    accounts_manager.load_register_pem_from_folder(
        name="wallets_folder", folder_path=Path("./tests/data/wallets_folder")
    )
