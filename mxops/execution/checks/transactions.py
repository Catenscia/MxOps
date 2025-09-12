"""
author: Etienne Wallet

This module contains Checks related to transactions
"""

from dataclasses import dataclass, field

from multiversx_sdk import TransactionOnNetwork

from mxops.data.execution_data import ScenarioData
from mxops.enums import LogGroupEnum
from mxops.errors import TransactionError
from mxops.execution.checks.base import Check
from mxops.execution.network import get_on_chain_transfers, raise_on_errors
from mxops.smart_values import SmartBool, SmartOnChainTokenTransfers, SmartStr
from mxops.smart_values.native import SmartList
from mxops.utils.msc import list_contains_every_patterns, text_contains_all_patterns


@dataclass
class SuccessCheck(Check):
    """
    Check that an on-chain transaction is successful
    """

    def _get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Check that an on-chain transaction is successful

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        :return: True if the check pass
        :rtype: bool
        """
        raise_on_errors(onchain_tx)
        return True


@dataclass
class FailCheck(Check):
    """
    Check that an on-chain transaction is a failure
    """

    def _get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Check that an on-chain transaction is a failure

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        :return: True if the check pass
        :rtype: bool
        """
        try:
            raise_on_errors(onchain_tx)
        except TransactionError:
            return True
        return False


@dataclass
class TransfersCheck(Check):
    """
    Check the transfers that an on-chain transaction contains specified transfers
    """

    expected_transfers: SmartOnChainTokenTransfers
    condition: SmartStr = field(default_factory=lambda: SmartStr("exact"))
    include_gas_refund: SmartBool = False

    def _get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Check the transfers that an on-chain transaction contains specified transfers

        :param onchain_tx: _description_
        :type onchain_tx: TransactionOnNetwork
        :return: true if correct transfers were found
        :rtype: bool
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        condition = self.condition.get_evaluated_value()
        if condition not in ["included", "exact"]:
            raise ValueError(
                f"Uknown condition for TransferCheck {condition}. Must be one of "
                "exact or included"
            )
        onchain_transfers = get_on_chain_transfers(
            onchain_tx, include_refund=self.include_gas_refund.get_evaluated_value()
        )
        for expected_transfer in self.expected_transfers.get_evaluated_value():
            try:
                i_tr = onchain_transfers.index(expected_transfer)
            except ValueError:
                logger.error(
                    (
                        f"Expected transfer found no match:\n{expected_transfer} "
                        f"Remaining on-chain transfers:\n{onchain_transfers}"
                    )
                )
                return False
            onchain_transfers.pop(i_tr)

        if condition == "exact" and len(onchain_transfers) > 0:
            logger.error(
                (
                    f"Found {len(onchain_transfers)} more transfers than expected:"
                    f"\n {onchain_transfers}"
                )
            )
            return False
        return True


@dataclass
class LogCheck(Check):
    """
    Check that an on-chain transaction is successful
    """

    event_identifier: SmartStr
    mandatory_topic_text_patterns: SmartList = field(
        default_factory=lambda: SmartList([])
    )
    mandatory_data_text_patterns: SmartList = field(
        default_factory=lambda: SmartList([])
    )

    def _get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Check that an on-chain transaction is successful

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        :return: True if the check pass
        :rtype: bool
        """
        for event in onchain_tx.logs.events:
            # check event identifier
            if event.identifier != self.event_identifier.get_evaluated_value():
                continue

            # check all mandatory topic text patterns
            topic_patterns = self.mandatory_topic_text_patterns.get_evaluated_value()
            topic_texts = []
            for raw_topic in event.topics:
                try:
                    topic_texts.append(raw_topic.decode())
                except UnicodeDecodeError:
                    continue

            if not list_contains_every_patterns(topic_texts, topic_patterns):
                # not the event we are looking for
                continue

            # check all mandatory data text patterns
            data_patterns = self.mandatory_data_text_patterns.get_evaluated_value()
            if text_contains_all_patterns(event.data.decode(), data_patterns):
                # event found!
                return True

        return False
