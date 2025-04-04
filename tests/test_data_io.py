from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from multiversx_sdk import Address
import pytest
from multiversx_sdk.network_providers.proxy_network_provider import (
    account_from_proxy_response,
    account_storage_from_response,
)

from mxops import errors
from mxops.data.data_cache import (
    save_account_data,
    save_account_storage_data,
    try_load_account_data,
    try_load_account_storage_data,
)
from mxops.data.execution_data import (
    _ScenarioData,
    ExternalContractData,
    InternalContractData,
    SavedValuesData,
    TokenData,
    parse_value_key,
)
from mxops.data.migrations.v0_1_0__to__v1_0_0 import convert_scenario
from mxops.enums import NetworkEnum, TokenTypeEnum


@pytest.mark.parametrize(
    "scenario_path",
    [
        Path("tests/data/scenarios/scenario_A.json"),
        Path("tests/data/scenarios/scenario_B.json"),
    ],
)
def test_scenario_loading(scenario_path: Path):
    """
    Test that contract data is correctly loaded and that both environment syntax are
    handeld
    """
    # Given
    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.network == NetworkEnum.DEV
    assert scenario.name == "___test_mxops_tutorial_first_scene"
    assert scenario.accounts_data == {
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k": InternalContractData(  # noqa
            account_id="egld-ping-pong",
            bech32="erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
            saved_values={},
            code_hash=(
                "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451"
            ),
            deploy_time=1677134892,
            last_upgrade_time=1677134892,
        )
    }


def test_scenario_loading_current_migration_version():
    """
    Test that contract data is correctly loaded and that both environment syntax are
    handeld
    """
    # Given
    scenario_path = Path("tests/data/migrations/v1_0_0.json")
    # When
    _ = _ScenarioData.load_from_path(scenario_path)


def test_contract_add(scenario_data: _ScenarioData):
    # Given
    contract_bech32 = "erd1qqqqqqqqqqqqqpgqtccau7hl9djzdtwfe4354u0egp0x2c3futhse96haz"
    contract_id = "extr-contract"
    contract_data = ExternalContractData(
        contract_id,
        contract_bech32,
        saved_values={},
    )
    # When
    scenario_data.add_account_data(contract_data)
    address_fetched = scenario_data.get_account_address(contract_id)
    contract_id_fetched = scenario_data.get_account_value(
        contract_bech32, "contract_id"
    )

    # Then
    assert address_fetched.to_bech32() == contract_bech32
    assert contract_id_fetched == contract_id
    assert contract_bech32 in scenario_data.accounts_data
    assert contract_id not in scenario_data.accounts_data


def test_key_path_fetch():
    """
    Test that data is fetched correctly from a key path
    """
    # Given
    saved_values = SavedValuesData(
        saved_values={
            "key_1": {
                "key_2": [
                    {"data": "wrong value"},
                    {"data": "wrong value"},
                    {"data": "desired value"},
                ]
            }
        }
    )

    # When
    data = saved_values.get_value("key_1.key_2[2].data")

    # Then
    assert data == "desired value"


def test_key_path_fetch_errors():
    """
    Test that errors are correctly raise for wrong key path
    """
    # Given
    saved_values = SavedValuesData(
        saved_values={
            "key_1": {
                "key_2": [
                    {"data": "wrong value"},
                    {"data": "wrong value"},
                    {"data": "desired value"},
                ]
            }
        }
    )

    # When
    with pytest.raises(
        errors.WrongDataKeyPath,
        match=re.escape(
            "Wrong key 'key_3' from keys ['key_3'] for data element {'key_1': "
            "{'key_2': [{'data': 'wrong value'}, {'data': 'wrong value'}, "
            "{'data': 'desired value'}]}}"
        ),
    ):
        saved_values.get_value("key_3")

    with pytest.raises(
        errors.WrongDataKeyPath,
        match=re.escape(
            "Wrong key 'key_3' from keys ['key_1', 'key_3'] for data element {'key_2': "
            "[{'data': 'wrong value'}, {'data': 'wrong value'}, {'data': "
            "'desired value'}]}"
        ),
    ):
        saved_values.get_value("key_1.key_3")

    with pytest.raises(
        errors.WrongDataKeyPath,
        match=re.escape(
            "Wrong key 4 from keys ['key_1', 'key_2', 4] for data element [{'data': "
            "'wrong value'}, {'data': 'wrong value'}, {'data': 'desired value'}]"
        ),
    ):
        saved_values.get_value("key_1.key_2[4]")


@pytest.mark.parametrize(
    "value_key, expected_result",
    [
        ("key_1.key_2[0].data", ["key_1", "key_2", 0, "data"]),
        ("ping_pong.address", ["ping_pong", "address"]),
        ("ping-pong.address", ["ping-pong", "address"]),
    ],
)
def test_parse_value_key(value_key: str, expected_result: list[str | int]):
    # When
    # Given
    result = parse_value_key(value_key)

    # Then
    assert result == expected_result


@pytest.mark.parametrize(
    "key_path, value",
    [
        ("key_1.key_2[0].data", "value"),
        ("key_1[0][0].data", 1584),
        ("key_3", [1, 5, 6, 8]),
    ],
)
def test_key_path_set(key_path: str, value: Any):
    """
    Test that values can be set and retrieved correctly
    """
    # Given
    saved_values = SavedValuesData(saved_values={})

    # When
    saved_values.set_value(key_path, value)
    retrieved_value = saved_values.get_value(key_path)

    # Then
    assert retrieved_value == value


def test_key_path_set_errors():
    """
    Test that errors are correctly raise for wrong key path
    """
    # Given
    saved_values = SavedValuesData(
        saved_values={
            "key_1": {
                "key_2": [
                    {"data": "wrong value"},
                    {"data": "wrong value"},
                    {"data": "desired value"},
                ]
            }
        }
    )

    # When
    try:
        saved_values.set_value("", "value")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args == ("Key path is empty",)
    try:
        saved_values.set_value("[1]", "value")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args[0].startswith("Expected a tuple or a list but found {")
    try:
        saved_values.set_value("key_1.key_2.key_3", "value")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args[0].startswith("Expected a dict but found [")


def test_token_data_loading():
    """
    Test that token data is correctly loaded
    """
    # Given
    scenario_path = Path("tests/data/scenarios/scenario_C.json")

    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.tokens_data == {
        "My Token": TokenData(
            name="My Token",
            ticker="MTK",
            identifier="MTK-abcdef",
            saved_values={},
            type=TokenTypeEnum.FUNGIBLE,
        )
    }


@pytest.mark.parametrize(
    "scenario_path",
    [
        Path("tests/data/scenarios/scenario_D.json"),
        Path("tests/data/scenarios/scenario_E.json"),
    ],
)
def test_io_unicity(scenario_path: Path):
    """
    Test the loading and writing are consistent
    """
    # Given
    with open(scenario_path.as_posix(), encoding="utf-8") as file:
        raw_data = json.load(file)

    # When
    scenario = _ScenarioData.load_from_path(scenario_path)
    scenario_dict = scenario.to_dict()

    # Then
    assert scenario_dict == raw_data


def test_migration_v0_1_0_to_v1_0_0():
    """
    Test that a scenario file is correctly transformed from version v0.1.0
    to v1.0.0
    """
    # Given
    initial_scenario = json.loads(Path("tests/data/migrations/v0_1_0.json").read_text())

    # When
    result_scenario, abis = convert_scenario(initial_scenario)

    # Then
    expected_scenario = json.loads(
        Path("tests/data/migrations/v1_0_0.json").read_text()
    )
    assert expected_scenario == result_scenario
    assert len(abis) == 1
    expected_abi = json.loads(
        Path("tests/data/migrations/reconstructed.abi.json").read_text()
    )
    assert (
        abis["erd1qqqqqqqqqqqqqpgq5d4kvm8mdznek3e3ty6npluuneuhxsxajmwqvya7p8"]
        == expected_abi
    )


def test_account_data_cache():
    # Given
    account = account_from_proxy_response(
        {
            "account": {
                "address": "erd1qqqqqqqqqqqqqpgqs8r2jhfymgle49dqx42xyypx6r2smt602jps2kcn8f",  # noqa
                "nonce": 0,
                "balance": "0",
                "username": "",
                "code": "01010101",
                "codeHash": "6fEXlxljyzwksU4qdpjUjBcDNa8vXIFnd0xIw8HGVOM=",
                "rootHash": "e8Q66wDcKKbUSsGMu8TWzbifcuwINVXOKe3XnryurmY=",
                "codeMetadata": "BQQ=",
                "developerReward": "4965025595400558975",
                "ownerAddress": "erd1qqqqqqqqqqqqqpgqq66xk9gfr4esuhem3jru86wg5hvp33a62jps2fy57p",  # noqa
            },
            "blockInfo": {
                "nonce": 24357191,
                "hash": "1aed3ef7e850bb5876302488fafd34bdc8949c9724c0364d053de464d2d8021a",  # noqa
                "rootHash": "2d7d98e1f35755344a500f440168b2e191a9ad9bbe15907472d9f463eea39686",  # noqa
            },
        }
    )
    network = NetworkEnum.DEV

    # When
    save_account_data(
        network, account, data_datetime=datetime(2025, 2, 1, tzinfo=timezone.utc)
    )
    loaded_account = try_load_account_data(network, account.address)
    loaded_account_2 = try_load_account_data(
        network,
        account.address,
        datetime_threshold=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    wrong_network = try_load_account_data(NetworkEnum.MAIN, account.address)
    too_old = try_load_account_data(
        network,
        account.address,
        datetime_threshold=datetime(2025, 3, 1, tzinfo=timezone.utc),
    )
    wrong_address = try_load_account_data(
        network,
        Address.new_from_bech32(
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
        ),
    )

    # Then
    assert loaded_account == account
    assert loaded_account_2 == account
    assert wrong_network is None
    assert too_old is None
    assert wrong_address is None


def test_storage_data_cache():
    # Given
    address = Address.new_from_bech32(
        "erd1qqqqqqqqqqqqqpgqs8r2jhfymgle49dqx42xyypx6r2smt602jps2kcn8f"
    )
    storage = account_storage_from_response(
        {
            "blockInfo": {
                "hash": "5af3c9fe5e74d433c9f493d59a534b8a5f1f04536b6b573452dfdbf86db04bf2",  # noqa
                "nonce": 24357404,
                "rootHash": "cde6249d26bcf13bf9c5bafa3ab4156c4d267c91540c018c1bf8ebd61cd78fe5",  # noqa
            },
            "pairs": {
                "454c524f4e446573647445474c445553482d653633313537": "12030003e8",  # noqa
                "454c524f4e44657364745553482d313131653039": "120c00015d650347ae260628715b",  # noqa
                "454c524f4e44657364745745474c442d626434643739": "120b0013202041d1cef3b4f095",  # noqa
                "454c524f4e44726f6c656573647445474c445553482d653633313537": "010101",  # noqa
            },
        }
    )
    network = NetworkEnum.DEV

    # When
    save_account_storage_data(
        network,
        address,
        storage,
        data_datetime=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    loaded_storage = try_load_account_storage_data(network, address)
    loaded_storage_2 = try_load_account_storage_data(
        network,
        address,
        datetime_threshold=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    wrong_network = try_load_account_storage_data(NetworkEnum.MAIN, address)
    too_old = try_load_account_data(
        network,
        address,
        datetime_threshold=datetime(2025, 3, 1, tzinfo=timezone.utc),
    )
    wrong_address = try_load_account_storage_data(
        network,
        Address.new_from_bech32(
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
        ),
    )

    # Then
    assert loaded_storage == storage
    assert loaded_storage_2 == storage
    assert wrong_network is None
    assert too_old is None
    assert wrong_address is None
