from typing import Dict, List

from multiversx_sdk_network_providers.constants import ESDT_CONTRACT_ADDRESS
from multiversx_sdk_cli.contracts import QueryResult

from mxops.data.execution_data import ScenarioData
from mxops.execution.steps import ContractQueryStep
from mxops.execution.utils import parse_query_result


EXPECTED_PROPERTIES = {
    "JeanToken": {
        "IsPaused": False,
        "CanUpgrade": True,
        "CanMint": True,
        "CanBurn": True,
        "CanChangeOwner": False,
        "CanPause": False,
        "CanFreeze": False,
        "CanWipe": False,
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
}


def get_token_properties(query_results: List[QueryResult]) -> Dict:
    """
    Return the properties of a token, giventhe query results of
    the endpoint getTokenProperties

    :param query_results: result of the endpoint getTokenProperties
    :type query_results: List[QueryResult]
    :return: properties of the token
    :rtype: Dict
    """
    properties = {}
    for result in query_results[6:17]:
        name, value = parse_query_result(result, "str").split("-")
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

    query_step = ContractQueryStep(
        ESDT_CONTRACT_ADDRESS.bech32(), "getTokenProperties", [token_identifier]
    )
    query_step.execute()
    token_properties = get_token_properties(query_step.results)
    if token_properties != EXPECTED_PROPERTIES[token_name]:
        raise ValueError(f"Token properties are not as expected: {token_properties}")
