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
from mxops.execution import utils
from mxops.execution.smart_values import SmartAddress, SmartInt, SmartTokenTransfers
from mxops.execution.steps.base import TransactionStep


@dataclass
class TransferStep(TransactionStep):
    """
    This step is used to transfer some tokens to an address
    """

    receiver: SmartAddress
    value: SmartInt = field(default_factory=lambda: SmartInt(0))
    transfers: SmartTokenTransfers = field(
        default_factory=lambda: SmartTokenTransfers([])
    )

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for transfer

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender.get_evaluated_value())
        receiver = self.receiver.get_evaluated_value()
        value = self.value.get_evaluated_value()
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config)
        return tr_factory.create_transaction_for_transfer(
            sender=sender,
            receiver=receiver,
            native_amount=value,
            token_transfers=self.transfers.get_evaluated_value(),
        )
