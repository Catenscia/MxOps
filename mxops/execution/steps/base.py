"""
author: Etienne Wallet

This module contains abstract base Steps that are used to construct other Steps
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from multiversx_sdk import Transaction, TransactionOnNetwork

from mxops import errors
from mxops.common.providers import MyProxyNetworkProvider
from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData
from mxops.enums import LogGroupEnum, NetworkEnum
from mxops.execution.account import AccountsManager
from mxops.execution.checks.factory import SmartChecks
from mxops.execution.checks import SuccessCheck
from mxops.execution.network import send, send_and_wait_for_result
from mxops.smart_values import SmartValue
from mxops.smart_values.factory import extract_first_smart_value_class
from mxops.smart_values.mx_sdk import SmartAddress
from mxops.utils.msc import get_tx_link


@dataclass
class Step(ABC):
    """
    Represents an instruction for MxOps to execute
    within a scene
    """

    def execute(self):
        """
        Function that manage the workflow of the execution of a step
        Currently, it only evaluate all the smart values before triggering
        the actual execution of the step
        """
        self.evaluate_smart_values()
        self._execute()

    @abstractmethod
    def _execute(self):
        """
        Interface for the method to execute the action described by a Step instance.
        Each child class must overrid this method
        """

    def _auto_convert_smart_values_attributes(self):
        """
        Automatically convert attributes that are expected to be smart values
        into their expected class
        """
        # pylint: disable=no-member
        for attr_name, attr in self.__dataclass_fields__.items():
            attr_value = getattr(self, attr_name)
            smart_type = extract_first_smart_value_class(attr.type)
            if attr_value is None or smart_type is None:
                continue
            if isinstance(attr_value, smart_type):
                continue
            if not issubclass(smart_type, SmartValue):
                continue
            setattr(self, attr_name, smart_type(attr_value))

    def __post_init__(self):
        """
        Trigger functions after instantiation of the class
        """
        self._auto_convert_smart_values_attributes()

    def _initialize(self):
        """
        Function called just before smart values evaluation.
        Does nothing by default
        """

    def evaluate_smart_values(self):
        """
        Trigger the evaluation method of all smart values fields
        """
        self._initialize()
        # pylint: disable=no-member
        for attr_name in self.__dataclass_fields__:
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, SmartValue):
                attr_value.evaluate()


@dataclass(kw_only=True)
class TransactionStep(Step):
    """
    Represents a step that produces and send a transaction
    """

    sender: SmartAddress
    checks: SmartChecks = field(default_factory=lambda: SmartChecks([SuccessCheck()]))

    @abstractmethod
    def build_unsigned_transaction(self) -> Transaction:
        """
        Interface for the method that will build transaction to send. This transaction
        is meant to contain all the data specific to this Step.
        The signature will be done at a later stage in the method sign_transaction

        :return: transaction created by the Step
        :rtype: Transaction
        """

    def set_nonce_and_sign_transaction(self, tx: Transaction):
        """
        Set the nonce in the transaction, sign it and increment the
        sender account nonce.
        If the account is unknown and the network is the chain simulator,
        the signature and increment step will be skipped to allow to send transactions
        with any account within the chain simulator

        :param tx: transaction to sign
        :type tx: Transaction
        """
        network = Config.get_config().get_network()
        try:
            sender_account = AccountsManager.get_account(tx.sender)
        except errors.UnknownAccount as err:
            if network != NetworkEnum.CHAIN_SIMULATOR:
                raise err
            sender_account = None
        if sender_account is None:
            account_on_network = MyProxyNetworkProvider().get_account(tx.sender)
            tx.nonce = account_on_network.nonce
            tx.signature = b"aaaaa"
        else:
            sender_account = AccountsManager.get_account(tx.sender)
            tx.nonce = sender_account.get_nonce_then_increment()
            tx.signature = sender_account.sign_transaction(tx)

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Interface for the function that will be executed after the transaction has
        been successfully executed

        :param on_chain_tx: on chain transaction that was sent by the Step
        :type on_chain_tx: TransactionOnNetwork | None
        """
        # by default, do nothing

    def _execute(self):
        """
        Execute the workflow for a transaction Step: build, send, check
        and post execute
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        tx = self.build_unsigned_transaction()
        self.set_nonce_and_sign_transaction(tx)

        checks = self.checks.get_evaluated_value()
        if len(checks) > 0:
            on_chain_tx = send_and_wait_for_result(tx)
            for check in checks:
                check.raise_on_failure(on_chain_tx)
            logger.info(
                f"Transaction successful: {get_tx_link(on_chain_tx.hash.hex())}"
            )
        else:
            on_chain_tx = None
            send(tx)
            logger.info("Transaction sent")

        self._post_transaction_execution(on_chain_tx)
