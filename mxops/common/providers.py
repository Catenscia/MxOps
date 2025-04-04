"""
author: Etienne Wallet

This module contains derrived classes from api or proxy providers
"""

from multiversx_sdk import GenericResponse, ProxyNetworkProvider
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

    def get_initial_wallets(self) -> dict:
        url = "simulator/initial-wallets"
        return self.do_get_generic(url).to_dictionary()

    def generate_blocks_until_tx_completion(self, tx_hash: str) -> GenericResponse:
        url = f"simulator/generate-blocks-until-transaction-processed/{tx_hash}"
        return self.do_post_generic(url, None)

    def generate_blocks(self, n_blocks: int) -> GenericResponse:
        url = f"simulator/generate-blocks/{n_blocks}"
        return self.do_post_generic(url, None)

    def generate_blocks_until_epoch(self, epoch: int) -> GenericResponse:
        url = f"simulator/generate-blocks-until-epoch-reached/{epoch}"
        return self.do_post_generic(url, None)

    def set_state(self, states: list[dict]) -> GenericResponse:
        url = "simulator/set-state"
        return self.do_post_generic(url, states)

    def set_state_overwrite(self, states: list[dict]) -> GenericResponse:
        url = "simulator/set-state-overwrite"
        return self.do_post_generic(url, states)
