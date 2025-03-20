"""
author: Etienne Wallet

This modules contains the functions to migration mxops data from v0.1.0 to v1.0.0
"""

from copy import deepcopy
import json

from multiversx_sdk import Address

from mxops.config.config import Config
from mxops.data.path_versions import v0_1_0, v1_0_0
from mxops.enums import NetworkEnum


def recursive_attribute_drop(data: dict, attribute_name: str) -> dict:
    """
    Recusrively remove the provided attribute of a dictionnary
    if the value is a list of null length

    :param data: dict to inspect
    :type data: dict
    :param attribute_name: name of the attribute to inspect
    :type attribute_name: str
    :return: pruned dictionnary
    :rtype: dict
    """
    if attribute_name in data and len(data[attribute_name]) == 0:
        data.pop(attribute_name)
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = recursive_attribute_drop(value, attribute_name)
        if isinstance(value, list):
            data[key] = [
                recursive_attribute_drop(v, attribute_name)
                if isinstance(v, dict)
                else v
                for v in value
            ]
    return data


def reconstruct_endpoint_data(data: dict, is_constructor: bool = False) -> dict:
    """
    From the endpoint data of a serializer, reconstruct the data
    for an abi file

    :param data: endpoint to reconstruct
    :type data: dict
    :param is_constructor: if the endpoint is a constructor endpoint, defaults to False
    :type is_constructor: bool, optional
    :return: reconstructed endpoint
    :rtype: dict
    """
    data = recursive_attribute_drop(data, "docs")
    if is_constructor:
        data.pop("mutability", "")
        data.pop("name", "")
    return data


def reconstruct_struct_data(data: dict) -> dict:
    """
    From the struct data of a serializer, reconstruct the data for
    an abi file

    :param data: struct to reconstruct
    :type data: dict
    :return: reconstructed struct
    :rtype: dict
    """
    data.pop("name", "")
    data = recursive_attribute_drop(data, "docs")
    data = recursive_attribute_drop(data, "fields")
    data["type"] = "struct"
    return data


def reconstruct_enum_data(data: dict) -> dict:
    """
    From the enum data of a serializer, reconstruct the data for
    an abi file

    :param data: enum to reconstruct
    :type data: dict
    :return: reconstructed enum
    :rtype: dict
    """
    data.pop("name", "")
    data = recursive_attribute_drop(data, "docs")
    data = recursive_attribute_drop(data, "fields")
    data["type"] = "enum"
    return data


def reconstruct_abi_from_serializer_dict(
    contract_id: str, serializer_data: dict
) -> dict:
    """
    Reconstruct a partial abi file from the dictionary representation
    of a AbiSerializer

    :param contract_id: id of the contract that had the provided serializer
    :type contract_id: str
    :param serializer_data: AbiSerializer as a dict
    :type serializer_data: dict
    :return: partial abi file
    :rtype: dict
    """
    data_copy = deepcopy(serializer_data)
    endpoints: dict = data_copy.get("endpoints", {})
    contract_abi = {
        "name": contract_id,
        "esdtAttributes": [],
        "hasCallback": False,
        "types": {},
    }
    contract_abi["constructor"] = reconstruct_endpoint_data(endpoints.pop("init"), True)

    upgrade_endpoint = None
    if "upgrade" in endpoints:
        upgrade_endpoint = endpoints.pop("upgrade")
    elif "upgradeConstructor" in endpoints:
        upgrade_endpoint = endpoints.pop("upgradeConstructor")
    if upgrade_endpoint is not None:
        contract_abi["upgradeConstructor"] = reconstruct_endpoint_data(
            upgrade_endpoint, True
        )

    contract_abi["endpoints"] = [
        reconstruct_endpoint_data(e) for e in endpoints.values()
    ]

    for struct in data_copy["structs"].values():
        struct_name = struct["name"]
        contract_abi["types"][struct_name] = reconstruct_struct_data(struct)

    for enum in data_copy["enums"].values():
        enum_name = enum["name"]
        contract_abi["types"][enum_name] = reconstruct_enum_data(enum)
    return contract_abi


def convert_scenario(source_data: dict) -> tuple[dict, dict[Address, dict]]:
    """
    Convert a scenario file from v0.1.0 to the elements needed for v.1.0.0

    :param source_data: json file of a scenario under the v0.1.0
    :type source_data: dict
    :return: json file of the scenario under v1.0.0 and the reconstructed json abis
    :rtype: tuple[dict, dict[str, dict]]
    """
    abis = {}
    dest_data = deepcopy(source_data)
    new_contracts_data = {}
    for contract_id, contract_data in dest_data.pop("contracts_data").items():
        contract_data["account_id"] = contract_data.pop("contract_id")
        contract_bech32 = contract_data.pop("address")
        contract_data["bech32"] = contract_bech32
        serializer_data = contract_data.pop("serializer", None)
        if serializer_data is not None:
            abis[contract_bech32] = reconstruct_abi_from_serializer_dict(
                contract_id, serializer_data
            )
        is_external = contract_data.pop("is_external")
        if is_external == "true":
            contract_data["__class__"] = "ExternalContractData"
        else:
            contract_data["__class__"] = "InternalContractData"
        new_contracts_data[contract_bech32] = contract_data
    dest_data["accounts_data"] = new_contracts_data
    for token_data in dest_data["tokens_data"].values():
        token_data["__class__"] = "TokenData"
    return dest_data, abis


def migrate_scenario(scenario_name: str, scenario_data: dict):
    """
    Convert the data of a scenario from version v0.1.0 to version
    v1.0.0 and save the resulting data

    :param scenario_name: name of the scenario to convert
    :type scenario_name: str
    :param scenario_data: data to convert
    :type scenario_data: dict
    """
    converted_data, abis = convert_scenario(scenario_data)
    data_file_path = v1_0_0.get_scenario_current_data_path(scenario_name)
    data_file_path.parent.mkdir(parents=True, exist_ok=True)
    data_file_path.write_text(json.dumps(converted_data, indent=4))

    for contract_bech32, abi_data in abis.items():
        contract_address = Address.new_from_bech32(contract_bech32)
        abis_file_path = v1_0_0.get_contract_abi_file_path(
            scenario_name, contract_address
        )
        abis_file_path.parent.mkdir(parents=True, exist_ok=True)
        abis_file_path.write_text(json.dumps(abi_data, indent=4))


def migrate_scenario_checkpoint(
    scenario_name: str, checkpoint_name: str, scenario_data: dict
):
    """
    Convert the data of a checkpoint of a scenario from version v0.1.0 to version
    v1.0.0 and save the resulting data

    :param scenario_name: name of the scenario to convert
    :type scenario_name: str
    :param checkpoint_name: name of the checkpoint of the scenario
    :type checkpoint_name: str
    :param scenario_data: data to convert
    :type scenario_data: dict
    """
    converted_data, abis = convert_scenario(scenario_data)
    data_file_path = v1_0_0.get_scenario_checkpoint_data_path(
        scenario_name, checkpoint_name
    )
    data_file_path.parent.mkdir(parents=True, exist_ok=True)
    data_file_path.write_text(json.dumps(converted_data, indent=4))

    for contract_bech32, abi_data in abis.items():
        contract_address = Address.new_from_bech32(contract_bech32)
        abis_file_path = v1_0_0.get_checkpoint_contract_abi_file_path(
            scenario_name, checkpoint_name, contract_address
        )
        abis_file_path.parent.mkdir(parents=True, exist_ok=True)
        abis_file_path.write_text(json.dumps(abi_data, indent=4))


def migrate():
    """
    Operate the migration of mxops data from v0.1.0 to v1.0.0
    """
    root_source_path = v0_1_0.get_data_path()
    for network in NetworkEnum:
        env_source_path = root_source_path / network.name
        if not env_source_path.exists():
            continue
        Config.set_network(network)
        scenarios_names = v0_1_0.get_all_scenarios_names()
        for scenario_name in scenarios_names:
            scenario_data = json.loads(
                v0_1_0.get_scenario_file_path(scenario_name).read_text()
            )
            migrate_scenario(scenario_name, scenario_data)
            checkpoints_names = v0_1_0.get_all_checkpoints_names(scenario_name)
            for checkpoint_name in checkpoints_names:
                scenario_data = json.loads(
                    v0_1_0.get_scenario_file_path(
                        scenario_name, checkpoint_name
                    ).read_text()
                )
                migrate_scenario_checkpoint(
                    scenario_name, checkpoint_name, scenario_data
                )
