"""
author: Etienne Wallet

This module contains abstract base Steps that are used to construct other Steps
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from multiversx_sdk import Transaction, TransactionOnNetwork

from mxops.execution.account import AccountsManager
from mxops.execution.checks.factory import SmartChecks
from mxops.execution.checks import SuccessCheck
from mxops.execution.network import send, send_and_wait_for_result
from mxops.execution.smart_values import SmartStr, SmartValue
from mxops.execution.smart_values.factory import extract_first_smart_value_class
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_tx_link

LOGGER = get_logger("base steps")


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

    def evaluate_smart_values(self):
        """
        Trigger the evaluation method of all smart values fields
        """
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

    sender: SmartStr
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
        Sign the transaction created by this step and update the account nonce

        :param tx: tra
        :type tx: Transaction
        """
        sender = self.sender.get_evaluated_value()
        sender_account = AccountsManager.get_account(sender)
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
        tx = self.build_unsigned_transaction()
        self.set_nonce_and_sign_transaction(tx)

        if len(self.checks) > 0:
            on_chain_tx = send_and_wait_for_result(tx)
            for check in self.checks.get_evaluated_value():
                check.raise_on_failure(on_chain_tx)
            LOGGER.info(
                f"Transaction successful: {get_tx_link(on_chain_tx.hash.hex())}"
            )
        else:
            on_chain_tx = None
            send(tx)
            LOGGER.info("Transaction sent")

        self._post_transaction_execution(on_chain_tx)
