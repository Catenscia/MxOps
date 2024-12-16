"""
author: Etienne Wallet

This module contains derrived classes from api or proxy providers
"""

from typing import Dict
from multiversx_sdk_core import Address
from multiversx_sdk_network_providers import GenericResponse, ProxyNetworkProvider
from mxops.config.config import Config


class MyProxyNetworkProvider(ProxyNetworkProvider):
    _instance = None

    def __init__(self):
        super().__init__(self.url)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MyProxyNetworkProvider, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.url = Config.get_config().get("PROXY")

    def get_initial_wallets(self) -> Dict:
        url = "simulator/initial-wallets"
        return self.do_get_generic(url).to_dictionary()

    def generate_blocks_until_tx_completion(self, tx_hash: str) -> GenericResponse:
        url = f"simulator/generate-blocks-until-transaction-processed/{tx_hash}"
        return self.do_post_generic(url, None)

    def generate_blocks(self, n_blocks: int) -> GenericResponse:
        url = f"simulator/generate-blocks/{n_blocks}"
        return self.do_post_generic(url, None)

    def get_address_storage_by_key(self, address: Address, key: str) -> str:
        url = f"address/{address.bech32()}/key/{key}"
        return self.do_get_generic(url).get("value")

    def get_address_full_storage(self, address: Address) -> Dict[str, str]:
        url = f"address/{address.bech32()}/keys"
        return self.do_get_generic(url).get("pairs", {})
