"""
author: Etienne Wallet

This module contains derrived classes from api or proxy providers
"""

from time import sleep

from multiversx_sdk import (
    AccountStorage,
    AccountStorageEntry,
    Address,
    GenericResponse,
    ProxyNetworkProvider,
)
from mxops.config.config import Config
from mxops.errors import MaxIterationError, StorageIterationError


def get_account_storage_with_fallback(
    proxy: ProxyNetworkProvider,
    address: Address,
    num_keys: int | None = None,
    request_delay: float | None = None,
    max_iterations: int = 100000,
) -> AccountStorage:
    """
    Fetch all account storage with automatic fallback.
    First tries the paginated /address/iterate-keys endpoint, then falls back
    to the standard /address/{address}/keys endpoint if iteration is not available.

    :param proxy: proxy network provider to use
    :param address: address to fetch storage for
    :param num_keys: number of keys per request for iteration (default from config)
    :param request_delay: delay between requests in seconds (default: 1/API_RATE_LIMIT)
    :param max_iterations: maximum iterations to prevent infinite loops
    :return: AccountStorage with all entries
    """
    if num_keys is None:
        num_keys = int(Config.get_config().get("STORAGE_ITERATION_BATCH_SIZE"))

    if request_delay is None:
        request_delay = 1.0 / float(Config.get_config().get("API_RATE_LIMIT"))

    # Try paginated endpoint first
    all_pairs: dict[str, str] = {}
    iterator_state: list[list[int]] = []
    iteration_succeeded = False

    try:
        for iteration in range(max_iterations):
            if iteration > 0 and request_delay > 0:
                sleep(request_delay)

            url = "address/iterate-keys"
            data = {
                "address": address.to_bech32(),
                "numKeys": num_keys,
                "iteratorState": iterator_state,
            }
            response = proxy.do_post_generic(url, data).to_dictionary()
            pairs = response.get("pairs", {})
            new_state = response.get("newIteratorState", [])

            # Check if endpoint is not enabled (empty on first request)
            if iteration == 0 and not pairs and not new_state:
                break  # Fall back to standard endpoint

            all_pairs.update(pairs)

            if not new_state:  # Iteration complete
                iteration_succeeded = True
                break

            iterator_state = new_state
        else:
            raise MaxIterationError()
    except Exception:
        iteration_succeeded = False

    # If iteration succeeded, convert to AccountStorage
    if iteration_succeeded and all_pairs:
        entries = [
            AccountStorageEntry(
                raw={k: v},
                key=bytes.fromhex(k).decode("utf-8", errors="replace"),
                value=bytes.fromhex(v),
            )
            for k, v in all_pairs.items()
        ]
        return AccountStorage(raw={"pairs": all_pairs}, entries=entries)

    # Fall back to standard endpoint
    return proxy.get_account_storage(address)


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

    def iterate_keys(
        self,
        address: Address,
        num_keys: int,
        iterator_state: list[list[int]],
    ) -> tuple[dict[str, str], list[list[int]]]:
        """
        Make a single request to the iterate-keys endpoint.

        :param address: address to fetch storage for
        :param num_keys: number of keys to fetch per request
        :param iterator_state: current iterator state (empty list for first request)
        :return: tuple of (pairs dict, new_iterator_state)
        """
        url = "address/iterate-keys"
        data = {
            "address": address.to_bech32(),
            "numKeys": num_keys,
            "iteratorState": iterator_state,
        }
        response = self.do_post_generic(url, data).to_dictionary()
        pairs = response.get("pairs", {})
        new_state = response.get("newIteratorState", [])
        return pairs, new_state

    def get_account_storage_iter(
        self,
        address: Address,
        num_keys: int | None = None,
        request_delay: float | None = None,
        max_iterations: int = 100000,
    ) -> dict[str, str]:
        """
        Fetch all account storage using the paginated /address/iterate-keys endpoint.
        Handles iterator state automatically and aggregates all results.

        :param address: address to fetch storage for
        :param num_keys: number of keys per request (default from config)
        :param request_delay: delay between requests in seconds
            (default: 1/API_RATE_LIMIT)
        :param max_iterations: maximum iterations to prevent infinite loops
        :return: dict of all storage pairs {hex_key: hex_value}
        :raises StorageIterationError: if endpoint returns empty on first request
        :raises MaxIterationError: if max_iterations is exceeded
        """
        if num_keys is None:
            num_keys = int(Config.get_config().get("STORAGE_ITERATION_BATCH_SIZE"))

        if request_delay is None:
            request_delay = 1.0 / float(Config.get_config().get("API_RATE_LIMIT"))

        all_pairs: dict[str, str] = {}
        iterator_state: list[list[int]] = []

        for iteration in range(max_iterations):
            if iteration > 0 and request_delay > 0:
                sleep(request_delay)

            pairs, new_state = self.iterate_keys(address, num_keys, iterator_state)

            # Check if endpoint is not enabled (empty on first request)
            if iteration == 0 and not pairs and not new_state:
                raise StorageIterationError(
                    address.to_bech32(),
                    "endpoint returned empty results (feature may not be enabled)",
                )

            all_pairs.update(pairs)

            if not new_state:  # Iteration complete
                break

            iterator_state = new_state
        else:
            raise MaxIterationError()

        return all_pairs

    def get_all_account_storage(
        self,
        address: Address,
        num_keys: int | None = None,
        request_delay: float | None = None,
        max_iterations: int = 100000,
    ) -> dict[str, str]:
        """
        Fetch all account storage with automatic fallback.
        First tries the paginated /address/iterate-keys endpoint, then falls back
        to the standard /address/{address}/keys endpoint if iteration is not available.

        :param address: address to fetch storage for
        :param num_keys: number of keys per request for iteration (default from config)
        :param request_delay: delay between requests in seconds
            (default: 1/API_RATE_LIMIT)
        :param max_iterations: maximum iterations to prevent infinite loops
        :return: dict of all storage pairs {hex_key: hex_value}
        """
        # Try paginated endpoint first
        try:
            return self.get_account_storage_iter(
                address, num_keys, request_delay, max_iterations
            )
        except StorageIterationError:
            pass  # Fall back to standard endpoint

        # Fall back to standard endpoint
        storage = self.get_account_storage(address)
        all_pairs: dict[str, str] = {}
        for entry in storage.entries:
            all_pairs.update(entry.raw)
        return all_pairs
