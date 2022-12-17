"""
author: Etienne Wallet

This module contains the classes used to execute scenes in a scenario
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import sys
from typing import Dict, List

from erdpy.contracts import CodeMetadata
from xops.data.data import ContractData, _ScenarioData

from xops.execution.account import AccountsManager
from xops.execution.contract_interactions import get_contract_deploy_tx
from xops.execution.msc import EsdtTransfer
from xops.execution.network import check_onchain_success, send_and_wait_for_result
from xops.utils.msc import get_file_hash


@dataclass
class Step:
    pass

    def execute(self):
        """
        Interface for the method to execute the action described by a Step instance.
        Each child class must overrid this method

        :raises NotImplementedError: if this method was not overriden by a child class or directly executed.
        """
        raise NotImplementedError


@dataclass
class LoopStep:
    steps: List[Step]
    var_name: str
    var_start: int = None
    var_end: int = None
    var_list: List[int] = None

    def execute(self):
        """
        Execute in loop the inner steps 
        """
        if self.var_start is not None and self.var_end is not None:
            iterator = range(self.var_start, self.var_end)
        elif self.var_list is not None:
            iterator = self.var_list
        else:
            raise ValueError('Loop iteration is not correctly defined')
        for var in iterator:
            os.environ[self.var_name] = str(var)
            for step in self.steps:
                step.execute()

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be Dict, will try to convert them to Steps instances.
        Usefull for easy loading from yaml files
        """
        if len(self.steps) and isinstance(self.steps[0], Dict):
            self.steps = instanciate_steps(self.steps)


@dataclass
class ContractStep(Step):
    contract_id: str


@dataclass
class ContractDeployStep(ContractStep):
    sender: Dict
    wasm_path: str
    gas_limit: int
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=lambda: [])

    def execute(self, scenario_data: _ScenarioData):
        """
        Execute a contract deployment
        """
        sender = AccountsManager.get_account(self.sender)
        metadata = CodeMetadata(self.upgradeable, self.readable,
                                self.payable, self.payable_by_sc)
        wasm_path = Path(self.wasm_path)
        tx, contract = get_contract_deploy_tx(wasm_path, metadata,
                                              self.gas_limit, self.arguments, sender)
        onChainTx = send_and_wait_for_result(tx)
        check_onchain_success(onChainTx)
        sender.nonce += 1

        creation_timestamp = onChainTx.to_dictionary()['timestamp']
        contract_data = ContractData(
            self.contract_id,
            contract.address.bech32(),
            get_file_hash(wasm_path),
            creation_timestamp,
            creation_timestamp,
            {}
        )
        scenario_data.add_contract_data(contract_data)


@dataclass
class ContractCallStep(ContractStep):
    sender: Dict
    endpoint: str
    gas_limit: int
    arguments: List = field(default_factory=lambda: [])
    value: int = 0
    esdt_transfers: List[EsdtTransfer] = field(default_factory=lambda: [])
    wait_for_result: bool = False

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be Dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        checked_transfers = []
        for trf in self.esdt_transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, Dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f'Unexpected type: {type(trf)}')
        self.esdt_transfers = checked_transfers


@dataclass
class ContractQueryStep(ContractStep):
    endpoint: str
    arguments: List = field(default_factory=lambda: [])
    save_keys: List[str] = field(default_factory=lambda: [])
    result_types: List[str] = field(default_factory=lambda: [])
    print_results: bool = False


def instanciate_steps(raw_steps: List[Dict]) -> List[Step]:
    """
    Take steps as dictionaries and convert them to their conrresponding step classes.

    :param raw_steps: steps to instantiate
    :type raw_steps: List[Dict]
    :return: steps instances
    :rtype: List[steps.Step]
    """
    steps_list = []
    for raw_step in raw_steps:
        step_class_name = raw_step.pop('type') + 'Step'
        try:
            step_class_object = getattr(sys.modules[__name__], step_class_name)
        except AttributeError as err:
            raise ValueError(f'Unkown step type: {step_class_name}') from err
        steps_list.append(step_class_object(**raw_step))
    return steps_list
