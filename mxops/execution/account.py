"""
author: Etienne Wallet

This modules contains the class and functions to manage multiversX accounts
"""
from typing import Optional

from multiversx_sdk_cli.accounts import Account, LedgerAccount
from multiversx_sdk_network_providers import ProxyNetworkProvider

from mxops import errors
from mxops.config.config import Config


class AccountsManager:
    """
    This class is used to load and sync the MultiversX accounts
    This allows to handle nonce incrementation in a centralised place
    """

    _accounts = {}

    @classmethod
    def load_account(
        cls,
        account_name: str,
        pem_path: Optional[str] = None,
        ledger_account_index: Optional[int] = None,
        ledger_address_index: Optional[int] = None,
    ):
        """
        Load an account from a pem path or ledger indices

        :param account_name: name that will be used to reference this account.
            Must be unique.
        :type account_name: str
        :param pem_path: string path to the PEM file, defaults to None
        :type pem_path: Optional[str], optional
        :param ledger_account_index: index of the ledger account, defaults to None
        :type ledger_account_index: Optional[int], optional
        :param ledger_address_index: index of the ledger address, defaults to None
        :type ledger_address_index: Optional[int], optional
        """
        if ledger_account_index is not None and ledger_address_index is not None:
            cls._accounts[account_name] = LedgerAccount(
                ledger_account_index, ledger_address_index
            )
        elif isinstance(pem_path, str):
            cls._accounts[account_name] = Account(pem_file=pem_path)
        else:
            raise ValueError(f"{account_name} is not correctly configured")

    @classmethod
    def get_account(cls, account_name: str) -> Account:
        """
        Fetch an account from the pre-loaded account

        :param account_name: name of the account to fetch
        :type account_name: str
        :return: account under the provided name
        :rtype: Account
        """
        try:
            return cls._accounts[account_name]
        except KeyError as err:
            raise errors.UnknownAccount(account_name) from err

    @classmethod
    def sync_account(cls, account_name: str):
        """
        Synchronise the nonce of an account by calling the
        Elrond proxy.

        :param account_name: name of the account to synchronise
        :type account_name: str
        """
        config = Config.get_config()
        proxy = ProxyNetworkProvider(config.get("PROXY"))
        try:
            cls._accounts[account_name].sync_nonce(proxy)
        except KeyError as err:
            raise RuntimeError(f"Unkown account {account_name}") from err
