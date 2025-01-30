from typing import Any
from multiversx_sdk import Address
from multiversx_sdk.core.constants import ESDT_CONTRACT_ADDRESS_HEX
from multiversx_sdk.abi import TokenIdentifierValue

from mxops.data.execution_data import ScenarioData
from mxops.execution.legacy_steps import ContractQueryStep


EXPECTED_PROPERTIES = {
    "JeanToken": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": False,
        "CanPause": False,
        "CanFreeze": False,
        "CanWipe": False,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": False,
        "NFTCreateStopped": False,
    },
    "JeanTokenAllProp": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": True,
        "CanPause": True,
        "CanFreeze": True,
        "CanWipe": True,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": False,
        "NFTCreateStopped": False,
    },
    "MarcNFT": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": False,
        "CanPause": True,
        "CanFreeze": True,
        "CanWipe": True,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": True,
        "NFTCreateStopped": False,
    },
    "MarcNFTAllProp": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": True,
        "CanPause": True,
        "CanFreeze": True,
        "CanWipe": True,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": True,
        "NFTCreateStopped": False,
    },
    "MartheSFT": {
        "IsPaused": False,
        "CanUpgrade": False,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": True,
        "CanPause": False,
        "CanFreeze": False,
        "CanWipe": False,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": True,
        "NFTCreateStopped": False,
    },
    "MartheSFTAllProp": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": True,
        "CanPause": True,
        "CanFreeze": True,
        "CanWipe": True,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": True,
        "NFTCreateStopped": False,
    },
    "ThomasMeta": {
        "IsPaused": False,
        "CanUpgrade": False,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": False,
        "CanPause": False,
        "CanFreeze": False,
        "CanWipe": False,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": False,
        "NFTCreateStopped": False,
    },
    "ThomasMetaAllProp": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": False,
        "CanBurn": False,
        "CanChangeOwner": True,
        "CanPause": True,
        "CanFreeze": True,
        "CanWipe": True,
        "CanAddSpecialRoles": True,
        "CanTransferNFTCreateRole": True,
        "NFTCreateStopped": False,
    },
}


def get_token_properties(query_data_parts: list[Any]) -> dict:
    """
    Return the properties of a token, giventhe query results of
    the endpoint getTokenProperties

    :param query_results: result of the endpoint getTokenProperties
    :type query_results: list[Any]
    :return: properties of the token
    :rtype: dict
    """
    properties = {}
    for result in query_data_parts[6:17]:
        name, value = result.decode().split("-")
        if value not in ("true", "false"):
            raise ValueError(f"properties {name} has a non-boolean value: {value}")
        properties[name] = value == "true"
    return properties


def check_token_properties(token_name: str):
    """
    Given a token name, checks that it got the correct properties set
    for the integration tests.

    :param token_name: name of the token
    :type token_name: str
    """
    scenario_data = ScenarioData.get()
    token_identifier = scenario_data.get_token_value(token_name, "identifier")

    contract_address = Address.from_hex(ESDT_CONTRACT_ADDRESS_HEX, hrp="erd")

    query_step = ContractQueryStep(
        contract_address.to_bech32(),
        "getTokenProperties",
        [TokenIdentifierValue(token_identifier)],
    )
    query_step.execute()
    token_properties = get_token_properties(query_step.returned_data_parts)
    if token_properties != EXPECTED_PROPERTIES[token_name]:
        raise ValueError(
            f"The properties of token {token_name} are not as expected: "
            f"{token_properties}"
        )
