"""
author: Etienne Wallet

This module contains the classes used to check on-chain transactions
"""
from dataclasses import dataclass
import sys
from typing import Dict, List, Literal

from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops import errors
from mxops.execution.msc import ExpectedTransfer
from mxops.execution.network import get_on_chain_transfers, raise_on_errors
from mxops.utils.logger import get_logger


LOGGER = get_logger("Checks")


@dataclass
class Check:
    """
    Represents a check to operate on the content of an on-chain transaction
    """

    def raise_on_failure(self, onchain_tx: TransactionOnNetwork):
        """
        Perform the check on the transaction and raise an error if it failed.

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        """

        try:
            check_status = self.get_check_status(onchain_tx)
        except Exception as err:
            raise errors.CheckFailed(self, onchain_tx) from err
        if not check_status:
            raise errors.CheckFailed(self, onchain_tx)

    def get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Interface for the method to execute the check described by a Check instance.
        Each child class must overrid this method

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        :return: True if the check pass
        :rtype: bool
        """
        raise NotImplementedError


@dataclass
class SuccessCheck(Check):
    """
    Check that an on-chain transaction is successful
    """

    def get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
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
class TransfersCheck(Check):
    """
    Check the transfers that an on-chain transaction contains specified transfers
    """

    expected_transfers: List[ExpectedTransfer]
    condition: Literal["exact", "included"] = "exact"
    include_gas_refund: bool = False

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be Dict, will try to convert them to TransfersCheck instances.
        Usefull for easy loading from yaml files
        """
        if self.condition not in ["exact", "included"]:
            raise ValueError(
                (
                    f"{self.condition} is not an accepted value for "
                    "TransfersCheck.condition"
                )
            )
        expected_transfers = []
        for transfer in self.expected_transfers:
            if isinstance(transfer, Dict):
                expected_transfers.append(ExpectedTransfer(**transfer))
            elif isinstance(transfer, ExpectedTransfer):
                expected_transfers.append(transfer)
            else:
                raise TypeError(
                    f"Type {type(transfer)} not supproted for ExpectedTransfer"
                )
        self.expected_transfers = expected_transfers

    def get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Check the transfers that an on-chain transaction contains specified transfers

        :param onchain_tx: _description_
        :type onchain_tx: TransactionOnNetwork
        :return: true if correct transfers were found
        :rtype: bool
        """
        onchain_transfers = get_on_chain_transfers(onchain_tx, self.include_gas_refund)
        for expected_transfer in self.expected_transfers:
            try:
                i_tr = onchain_transfers.index(expected_transfer)
            except ValueError:
                evaluated_transfer = expected_transfer.get_dynamic_evaluated()
                LOGGER.error(
                    (
                        f"Expected transfer found no match:\n{evaluated_transfer} "
                        f"Remaining on-chain transfers:\n{onchain_transfers}"
                    )
                )
                return False
            onchain_transfers.pop(i_tr)

        if self.condition == "exact" and len(onchain_transfers) > 0:
            LOGGER.error(
                (
                    f"Found {len(onchain_transfers)} more transfers than expected:"
                    f"\n {onchain_transfers}"
                )
            )
            return False
        return True


def instanciate_checks(raw_checks: List[Dict]) -> List[Check]:
    """
    Take checks as dictionaries and convert them to their corresponding check classes.

    :param raw_checks: checks to instantiate
    :type raw_checks: List[Dict]
    :return: checks instances
    :rtype: List[Check]
    """
    checks_list = []
    for raw_check in raw_checks:
        check_class_name = raw_check.pop("type") + "Check"
        try:
            check_class_object = getattr(sys.modules[__name__], check_class_name)
        except AttributeError as err:
            raise ValueError(f"Unkown check type: {check_class_name}") from err
        checks_list.append(check_class_object(**raw_check))
    return checks_list
