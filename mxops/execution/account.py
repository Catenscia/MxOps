"""
author: Etienne Wallet

This modules contains the class and functions to manage multiversX accounts
"""

import os
from pathlib import Path

from multiversx_sdk import (
    Account,
    Address,
    LedgerAccount,
)

from mxops import errors
from mxops.common.providers import MyProxyNetworkProvider
from mxops.data.execution_data import LedgerAccountData, PemAccountData, ScenarioData
from mxops.enums import LogGroupEnum


class AccountsManager:
    """
    This class is used to load and sync the MultiversX accounts
    This allows to handle nonce incrementation in a centralised place
    """

    _accounts: dict[str, Account | LedgerAccount] = {}

    @classmethod
    def load_register_pem_from_folder(
        cls, name: str, folder_path: str
    ) -> list[Address]:
        """
        Load all the pem account located in the given folder.
        The name of the accounts is the file name and the list of loaded accounts
        is save in the Scenario variable under the key provided (name)

        :param name: key to save the names of the list of loaded accounts
        :type name: str
        :param folder_path: path to the folder where wallets are located
        :type folder_path: str
        :return: addresses of the loaded accounts
        :rtype: list[Address]
        """
        loaded_accounts_names = []
        loaded_account_addresses = []
        for file_name in os.listdir(folder_path):
            file_path = Path(folder_path) / file_name
            if file_path.suffix == ".pem":
                loaded_account_addresses.append(
                    cls.load_register_pem_account(file_path, account_id=file_path.stem)
                )
                loaded_accounts_names.append(file_path.stem)
        scenario_data = ScenarioData.get()
        scenario_data.set_value(name, sorted(loaded_accounts_names))
        return loaded_account_addresses

    @classmethod
    def load_register_pem_account(
        cls, pem_path: str | Path, account_id: str | None = None
    ) -> Address:
        """
        Load a pem account and register it

        :param pem_path: path to the PEM file
        :type pem_path: str | Path
        :param account_id: id of the account for easier reference, defaults to None
        :type account_id: str | None
        :return: address of the loaded account
        :rtype: Address
        """
        if isinstance(pem_path, str):
            pem_path = Path(pem_path)
        account = Account.new_from_pem(pem_path)
        ScenarioData.get().add_account_data(
            PemAccountData(
                account_id=account_id,
                bech32=account.address.to_bech32(),
                pem_path=pem_path.as_posix(),
            )
        )
        cls._register_account(account)
        return account.address

    @classmethod
    def load_register_ledger_account(
        cls, ledger_address_index: int, account_id: str | None = None
    ) -> Address:
        """
        Load a Ledger account and register it

        :param ledger_address_index: index of the ledger address
        :type ledger_address_index: int
        :param account_id: id of the account for easier reference, defaults to None
        :type account_id: str | None
        :return: address of the loaded account
        :rtype: Address
        """
        account = LedgerAccount(ledger_address_index)
        ScenarioData.get().add_account_data(
            LedgerAccountData(
                account_id=account_id,
                bech32=account.address.to_bech32(),
                ledger_address_index=ledger_address_index,
            )
        )
        cls._register_account(account)
        return account.address

    @classmethod
    def _register_account(cls, account: Account | LedgerAccount):
        """
        Register an account in the accounts manager using its bech32 address

        :param account: account to register
        :type account: Account | LedgerAccount
        """
        account_bech32 = account.address.to_bech32()
        cls._accounts[account_bech32] = account
        cls.sync_account(account.address)

    @classmethod
    def get_account(cls, account_designation: str | Address) -> Account | LedgerAccount:
        """
        Fetch an account from the loaded using its address or its name if it
        has one

        :param account_designation: name or adresse of the account to fetch
        :type account_designation: str | Address
        :return: account under the provided name
        :rtype: Account | LedgerAccount
        """
        scenario_data = ScenarioData.get()
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        account_data = scenario_data.get_account_data(account_designation)
        if account_data.bech32 not in cls._accounts:
            logger.info(
                f"account {account_designation} is missing, reloading from "
                "scenario data"
            )
            if isinstance(account_data, PemAccountData):
                cls.load_register_pem_account(
                    account_data.pem_path, account_data.account_id
                )
            elif isinstance(account_data, LedgerAccountData):
                cls.load_register_ledger_account(
                    account_data.ledger_address_index, account_data.account_id
                )
            else:
                raise ValueError(
                    f"Account data of type {type(account_data)} is not handled"
                )
        try:
            return cls._accounts[account_data.bech32]
        except KeyError as err:
            raise errors.UnknownAccount(
                ScenarioData.get().name, account_designation
            ) from err

    @classmethod
    def sync_account(cls, account_designation: str | Address):
        """
        Synchronise the nonce of an account by calling the
        MultiversX proxy.

        :param account_designation: name or adresse of the account to sync
        :type account_designation: str | Address
        """
        proxy = MyProxyNetworkProvider()
        account = cls.get_account(account_designation)
        account_on_network = proxy.get_account(account.address)
        account.nonce = account_on_network.nonce

    @classmethod
    def sync_all_account(cls):
        """
        Synchronise the nonces of all the account by calling the
        MultiversX proxy.
        """
        for account_bech32 in cls._accounts:
            cls.sync_account(account_bech32)
