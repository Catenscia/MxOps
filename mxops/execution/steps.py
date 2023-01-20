"""
author: Etienne Wallet

This module contains the classes used to execute scenes in a scenario
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import sys
from typing import Dict, List

from multiversx_sdk_cli.contracts import CodeMetadata

from mxops.data.data import ContractData, ScenarioData
from mxops.execution.account import AccountsManager
from mxops.execution import contract_interactions as cti
from mxops.execution.msc import EsdtTransfer
from mxops.execution.network import raise_on_errors, send, send_and_wait_for_result
from mxops.execution.utils import parse_query_result
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_file_hash, get_tx_link
from mxops import errors

LOGGER = get_logger('steps')


@dataclass
class Step:
    """
    Represents a instruction to execute within a scene
    """

    def execute(self):
        """
        Interface for the method to execute the action described by a Step instance.
        Each child class must overrid this method

        :raises NotImplementedError: if this method was not overriden
        by a child class or directly executed.
        """
        raise NotImplementedError


@dataclass
class LoopStep:
    """
    Represents a set of steps to execute several time
    """
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
        if len(self.steps) > 0 and isinstance(self.steps[0], Dict):
            self.steps = instanciate_steps(self.steps)


@dataclass
class ContractStep(Step):  # pylint: disable=W0223
    """
    Represents a step dealing with a smart contract
    """
    contract_id: str


@dataclass
class ContractDeployStep(ContractStep):
    """
    Represents a smart contract deployment
    """
    sender: Dict
    wasm_path: str
    gas_limit: int
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=lambda: [])

    def execute(self):
        """
        Execute a contract deployment
        """
        LOGGER.info(f'Deploying contract {self.contract_id}')
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        try:
            scenario_data.get_contract_value(self.contract_id, 'address')
            raise errors.ContractIdAlreadyExists(self.contract_id)
        except errors.UnknownContract:
            pass

        # contruct the transaction
        sender = AccountsManager.get_account(self.sender)
        metadata = CodeMetadata(self.upgradeable, self.readable,
                                self.payable, self.payable_by_sc)
        wasm_path = Path(self.wasm_path)
        tx, contract = cti.get_contract_deploy_tx(wasm_path, metadata,
                                                  self.gas_limit, self.arguments, sender)
        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        sender.nonce += 1
        LOGGER.info((f'Deploy successful on {contract.address}'
                     f'\ntx hash: {get_tx_link(on_chain_tx.hash)}'))

        creation_timestamp = on_chain_tx.to_dictionary()['timestamp']
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
    """
    Represents a smart contract endpoint call
    """
    sender: Dict
    endpoint: str
    gas_limit: int
    arguments: List = field(default_factory=lambda: [])
    value: int = 0
    esdt_transfers: List[EsdtTransfer] = field(default_factory=lambda: [])
    check_for_errors: bool = True

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

    def execute(self):
        """
        Execute a contract call
        """
        LOGGER.info(f'Calling {self.endpoint} for {self.contract_id}')
        sender = AccountsManager.get_account(self.sender)
        scenario_data = ScenarioData.get()
        contract_address = scenario_data.get_contract_value(self.contract_id,
                                                            'address')

        tx = cti.get_contract_call_tx(contract_address,
                                      self.endpoint,
                                      self.gas_limit,
                                      self.arguments,
                                      self.value,
                                      self.esdt_transfers,
                                      sender)

        if self.check_for_errors:
            on_chain_tx = send_and_wait_for_result(tx)
            raise_on_errors(on_chain_tx)
            LOGGER.info(
                f'Call successful: {get_tx_link(on_chain_tx.hash)}')
        else:
            tx_hash = send(tx)
            LOGGER.info(f'Call sent: {get_tx_link(tx_hash)}')
        sender.nonce += 1


@dataclass
class ContractQueryStep(ContractStep):
    """
    Represents a smart contract query
    """
    endpoint: str
    arguments: List = field(default_factory=lambda: [])
    expected_results: List[Dict[str, str]] = field(default_factory=lambda: [])
    print_results: bool = False

    def execute(self):
        """
        Execute a query and optionally save the result
        """
        LOGGER.info(f'Query on {self.endpoint} for {self.contract_id}')
        scenario_data = ScenarioData.get()
        contract_address = scenario_data.get_contract_value(self.contract_id,
                                                            'address')
        results = cti.query_contract(contract_address,
                                     self.endpoint,
                                     self.arguments)

        if self.print_results:
            print(results)

        if len(results) == 0 or (len(results) == 1 and results[0] == ''):
            raise errors.EmptyQueryResults
        if len(self.expected_results) > 0:
            LOGGER.info('Saving Query results as contract data')
            for result, expected_result in zip(results, self.expected_results):
                parsed_result = parse_query_result(result,
                                                   expected_result['result_type'])
                scenario_data.set_contract_value(self.contract_id,
                                                 expected_result['save_key'],
                                                 parsed_result)

        LOGGER.info('Query successful')


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
