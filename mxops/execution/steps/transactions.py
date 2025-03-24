"""
author: Etienne Wallet

This module contains Steps for regular transactions
"""

from dataclasses import dataclass, field

from multiversx_sdk import (
    Transaction,
    TransactionsFactoryConfig,
    TransferTransactionsFactory,
)

from mxops.config.config import Config
from mxops.enums import LogGroupEnum
from mxops.smart_values import SmartAddress, SmartInt, SmartTokenTransfers
from mxops.execution.steps.base import TransactionStep
from mxops.utils.logger import get_logger


LOGGER = get_logger(LogGroupEnum.EXEC)


@dataclass
class TransferStep(TransactionStep):
    """
    This step is used to transfer some tokens to an address
    """

    receiver: SmartAddress
    value: SmartInt = 0
    transfers: SmartTokenTransfers = field(default_factory=list)

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for transfer

        :return: transaction built
        :rtype: Transaction
        """
        value = self.value.get_evaluated_value()
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config)
        tr_message = ""
        if self.value.get_evaluated_value() > 0:
            tr_message = f"{self.value.get_evaluation_string()} eGLD"
        if len(self.transfers.get_evaluated_value()) > 0:
            if len(tr_message) > 0:
                tr_message += " and "
            tr_message += f"{self.transfers.get_evaluation_string()}"

        LOGGER.info(
            f"Sending {tr_message} from {self.sender.get_evaluation_string()} "
            f"to {self.receiver.get_evaluation_string()}"
        )
        return tr_factory.create_transaction_for_transfer(
            sender=self.sender.get_evaluated_value(),
            receiver=self.receiver.get_evaluated_value(),
            native_amount=value,
            token_transfers=self.transfers.get_evaluated_value(),
        )
