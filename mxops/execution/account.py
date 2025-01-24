"""
author: Etienne Wallet

This modules contains the class and functions to manage multiversX accounts
"""

import os
from pathlib import Path

from multiversx_sdk import (
    Account,
    LedgerAccount,
)

from mxops import errors
from mxops.common.providers import MyProxyNetworkProvider
from mxops.data.execution_data import ScenarioData


class AccountsManager:
    """
    This class is used to load and sync the MultiversX accounts
    This allows to handle nonce incrementation in a centralised place
    """

    _accounts: dict[str, Account | LedgerAccount] = {}

    @classmethod
    def load_register_pem_from_folder(cls, name: str, folder_path: str) -> list[str]:
        """
        Load all the pem account located in the given folder.
        The name of the accounts is the file name and the list of loaded accounts
        is save in the Scenario variable under the key provided (name)

        :param name: key to save the names of the list of loaded accounts
        :type name: str
        :param folder_path: path to the folder where wallets are located
        :type folder_path: str
        :return: names of the loaded accounts
        :rtype: list[str]
        """
        loaded_accounts_names = []
        for file_name in os.listdir(folder_path):
            file_path = Path(folder_path) / file_name
            if file_path.suffix == ".pem":
                cls.load_register_account(file_path.stem, file_path)
                loaded_accounts_names.append(file_path.stem)
        scenario_data = ScenarioData.get()
        scenario_data.set_value(name, sorted(loaded_accounts_names))
        return loaded_accounts_names

    @classmethod
    def load_register_account(
        cls,
        account_name: str,
        pem_path: str | Path | None = None,
        ledger_address_index: int | None = None,
    ):
        """
        Load an account from a pem path or ledger indices and register it
        into the accounts manager

        :param account_name: name that will be used to reference this account.
            Must be unique.
        :type account_name: str
        :param pem_path: string path to the PEM file, defaults to None
        :type pem_path: Optional[Path], optional
        :param ledger_address_index: index of the ledger address, defaults to None
        :type ledger_address_index: Optional[int], optional
        """
        if isinstance(pem_path, str):
            pem_path = Path(pem_path)
        if isinstance(pem_path, Path):
            account = Account.new_from_pem(pem_path)
        elif ledger_address_index is not None:
            account = LedgerAccount(ledger_address_index)
        else:
            raise ValueError(f"{account_name} is not correctly configured")
        cls.register_account(account_name, account)

    @classmethod
    def register_account(cls, account_name: str, account: Account | LedgerAccount):
        """
        Register an account in the accounts manager

        :param account_name: name of the account for registration
        :type account_name: str
        :param account: account to register
        :type account: Account | LedgerAccount
        """
        cls._accounts[account_name] = account
        scenario_data = ScenarioData.get()
        scenario_data.set_value(
            f"{account_name}.address", cls._accounts[account_name].address.to_bech32()
        )

    @classmethod
    def get_account(cls, account_name: str) -> Account | LedgerAccount:
        """
        Fetch an account from the pre-loaded account

        :param account_name: name of the account to fetch
        :type account_name: str
        :return: account under the provided name
        :rtype: Account | LedgerAccount
        """
        try:
            return cls._accounts[account_name]
        except KeyError as err:
            raise errors.UnknownAccount(account_name) from err

    @classmethod
    def sync_account(cls, account_name: str):
        """
        Synchronise the nonce of an account by calling the
        MultiversX proxy.

        :param account_name: name of the account to synchronise
        :type account_name: str
        """
        proxy = MyProxyNetworkProvider()
        try:
            account = cls._accounts[account_name]
        except KeyError as err:
            raise errors.UnknownAccount(account_name) from err
        account_on_network = proxy.get_account(account.address)
        account.nonce = account_on_network.nonce

    @classmethod
    def sync_all_account(cls):
        """
        Synchronise the nonces of all the account by calling the
        MultiversX proxy.
        """
        for account_name in cls._accounts:
            cls.sync_account(account_name)
