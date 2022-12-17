"""
author: Etienne Wallet

This modules contains the class and functions to manage multiversX accounts
"""
from typing import Optional
from erdpy.accounts import Account, LedgerAccount
from erdpy.proxy.core import ElrondProxy

from xops.config.config import Config


class AccountsManager:
    """
    This class is used to load and sync the MultiversX accounts
    This allows to handle nonce incrementation in a centralised place
    """
    _accounts = {}

    @classmethod
    def load_account(cls,
                     account_name: str,
                     pem_path: Optional[str] = None,
                     ledger_account_index: Optional[int] = None,
                     ledger_address_index: Optional[int] = None):
        """
        Load an account from a pem path or ledger indices

        :param account_name: name that will be used to reference this account. Must be unique.
        :type account_name: str
        :param pem_path: string path to the PEM file, defaults to None
        :type pem_path: Optional[str], optional
        :param ledger_account_index: index of the ledger account, defaults to None
        :type ledger_account_index: Optional[int], optional
        :param ledger_address_index: index of the ledger address, defaults to None
        :type ledger_address_index: Optional[int], optional
        """
        if account_name in cls._accounts:
            raise ValueError(f'{account_name} is already used by another wallet')
        
        if ledger_account_index is not None and ledger_address_index is not None:
            cls._accounts[account_name] = LedgerAccount(ledger_account_index, ledger_address_index)
        elif isinstance(pem_path, str):
            cls._accounts[account_name] = Account(pem_file=pem_path)
        else:
            raise ValueError(f'{account_name} is not correctly configured')

    @classmethod
    def get_account(cls, account_name: str):
        try:
            return cls._accounts[account_name]
        except KeyError:
            cls._accounts[account_name] = cls._load_account(account_name)
        return cls._accounts[account_name]

    @classmethod
    def sync_account(cls, account_name: str):
        config = Config.get()
        proxy = ElrondProxy(config.get('PROXY'))
        try:
            cls._accounts[account_name].sync_nonce(proxy)
        except KeyError as err:
            raise RuntimeError(f'Unkown account {account_name}') from err