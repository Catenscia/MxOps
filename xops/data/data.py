"""
author: Etienne Wallet

This module contains the functions to load, write and update contracts data
"""
from dataclasses import dataclass
import json
from typing import Any, Dict
from xops.enums import NetworkEnum

from xops.utils.logger import get_logger


LOGGER = get_logger('data')


@dataclass
class ContractData:
    """
    Dataclass representing the data that can be locally saved for a contract
    """
    contract_id: str
    address: str
    wasm_has: str
    deploy_time: int
    last_upgrade_time: int
    saved_values: Dict[str, Any]

@dataclass
class ScenarioData:
    """
    Dataclass representing the data that can be locally saved for a scenario
    """
    name: str
    network: NetworkEnum
    creation_time: int
    last_update_time: int
    contracts: Dict[str, ContractData]
