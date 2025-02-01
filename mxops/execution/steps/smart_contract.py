"""
author: Etienne Wallet

This module contains Steps for smart-contract transactions
"""

from dataclasses import dataclass, field

from multiversx_sdk import (
    SmartContractTransactionsFactory,
    SmartContractTransactionsOutcomeParser,
    Transaction,
    TransactionOnNetwork,
    TransactionsFactoryConfig,
)
from multiversx_sdk.abi import Abi
from multiversx_sdk.core.errors import BadAddressError

from mxops import errors
from mxops.config.config import Config
from mxops.data.execution_data import InternalContractData, ScenarioData
from mxops.execution import utils
from mxops.execution.smart_values import (
    SmartBool,
    SmartInt,
    SmartList,
    SmartPath,
    SmartStr,
)
from mxops.execution.steps.base import TransactionStep
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_file_hash

LOGGER = get_logger("smart contract steps")


@dataclass
class ContractDeployStep(TransactionStep):
    """
    Represents a smart contract deployment
    """

    wasm_path: SmartPath
    contract_id: SmartStr
    gas_limit: SmartInt
    abi_path: SmartPath | None = None
    upgradeable: SmartBool = field(default_factory=lambda: SmartBool(True))
    readable: SmartBool = field(default_factory=lambda: SmartBool(True))
    payable: SmartBool = field(default_factory=lambda: SmartBool(False))
    payable_by_sc: SmartBool = field(default_factory=lambda: SmartBool(False))
    arguments: SmartList = field(default_factory=lambda: SmartList([]))

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract deployment

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Deploying contract {self.contract_id.get_evaluation_string()}")
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        contract_id = self.contract_id.get_evaluated_value()
        try:
            scenario_data.get_contract_value(contract_id, "address")
            raise errors.ContractIdAlreadyExists(contract_id)
        except errors.UnknownContract:
            pass

        if self.abi_path is not None:
            abi = Abi.load(self.abi_path.get_evaluated_value())
        else:
            abi = None

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=abi)
        bytecode = self.wasm_path.get_evaluated_value().read_bytes()

        arguments = self.arguments.get_evaluated_value()
        sender = utils.get_address_instance(self.sender.get_evaluated_value())

        return sc_factory.create_transaction_for_deploy(
            sender=sender,
            bytecode=bytecode,
            arguments=arguments,
            gas_limit=self.gas_limit,
            is_upgradeable=self.upgradeable,
            is_readable=self.readable,
            is_payable=self.payable,
            is_payable_by_sc=self.payable_by_sc,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Save the new contract data in the Scenario

        :param on_chain_tx: successful deployment transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        scenario_data = ScenarioData.get()

        # save the abi
        contract_id = utils.retrieve_value_from_any(self.contract_id)
        scenario_data.set_contract_abi_from_source(contract_id, self.abi_path)

        # get the new deployed address
        parser = SmartContractTransactionsOutcomeParser()
        parsed_outcome = parser.parse_deploy(on_chain_tx)
        try:
            parsed_contract = parsed_outcome.contracts[0]
            contract_address = parsed_contract.address
        except (IndexError, BadAddressError) as err:
            raise errors.ParsingError(
                parsed_outcome, "contract deployment address"
            ) from err

        LOGGER.info(
            f"The address of the deployed contract {contract_id} is "
            f"{contract_address.to_bech32()}"
        )

        # register the new contract
        file_hash = get_file_hash(self.wasm_path.get_evaluated_value())
        contract_data = InternalContractData(
            contract_id=contract_id,
            address=contract_address.to_bech32(),
            saved_values={},
            wasm_hash=file_hash,
            deploy_time=on_chain_tx.timestamp,
            last_upgrade_time=on_chain_tx.timestamp,
        )
        scenario_data.add_contract_data(contract_data)


@dataclass
class ContractUpgradeStep(TransactionStep):
    """
    Represents a smart contract upgrade
    """

    contract: SmartStr
    wasm_path: SmartPath
    gas_limit: SmartInt
    abi_path: SmartPath | None = None
    upgradeable: SmartBool = field(default_factory=lambda: SmartBool(True))
    readable: SmartBool = field(default_factory=lambda: SmartBool(True))
    payable: SmartBool = field(default_factory=lambda: SmartBool(False))
    payable_by_sc: SmartBool = field(default_factory=lambda: SmartBool(False))
    arguments: SmartList = field(default_factory=lambda: SmartList([]))

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract upgrade

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Upgrading contract {self.contract.get_evaluation_string()}")

        contract_designation = self.contract.get_evaluated_value()
        contract_address = utils.get_address_instance(contract_designation)

        if self.abi_path is not None:
            abi = Abi.load(self.abi_path.get_evaluated_value())
        else:
            abi = None

        arguments = self.arguments.get_evaluated_value()

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=abi)
        bytecode = self.wasm_path.get_evaluated_value().read_bytes()
        sender = utils.get_address_instance(self.sender.get_evaluated_value())

        return sc_factory.create_transaction_for_upgrade(
            sender=sender,
            contract=contract_address,
            bytecode=bytecode,
            arguments=arguments,
            gas_limit=self.gas_limit,
            is_upgradeable=self.upgradeable,
            is_readable=self.readable,
            is_payable=self.payable,
            is_payable_by_sc=self.payable_by_sc,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Save the new contract data in the Scenario

        :param on_chain_tx: successful upgrade transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        contract = self.contract.get_evaluated_value()
        scenario_data = ScenarioData.get()
        scenario_data.set_contract_abi_from_source(
            contract, self.abi_path.get_evaluated_value()
        )
        try:
            scenario_data.set_contract_value(
                contract, "last_upgrade_time", on_chain_tx.timestamp
            )
        except errors.UnknownContract:  # any contract can be upgraded
            pass
