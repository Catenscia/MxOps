"""
author: Etienne Wallet

This module contains derived classes from api or proxy providers
"""

import logging
from time import sleep

from multiversx_sdk import (
    AccountStorage,
    AccountStorageEntry,
    Address,
    GenericResponse,
    ProxyNetworkProvider,
)
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout

from mxops.config.config import Config
from mxops.enums import LogGroupEnum
from mxops.errors import MaxIterationError, StorageIterationError
from mxops.utils.logger import get_logger
from mxops.utils.progress import ProgressLogger


def set_state_with_batching(
    proxy: ProxyNetworkProvider,
    account_state: dict,
    overwrite: bool = True,
    batch_size: int | None = None,
    min_batch_size: int = 50,
    request_delay: float | None = None,
) -> None:
    """
    Set account state with batched storage pairs to avoid timeouts.
    If the account has many storage pairs, they are split into batches.
    On timeout, batch size is reduced and the request is retried.

    The first request sets account metadata (nonce, balance, code, etc.) along
    with the first batch of pairs. Subsequent requests only set additional
    pairs batches using the same address.

    Note: Unlike get_account_storage_with_fallback which can fall back to a
    standard endpoint, this function raises an error if all retries are
    exhausted, since there is no alternative way to set state.

    :param proxy: proxy network provider with set_state/set_state_overwrite methods
    :param account_state: account state dict containing address, balance,
        nonce, code, pairs, etc.
    :param overwrite: if True, use set_state_overwrite; otherwise use set_state
    :param batch_size: number of pairs per request (default from config)
    :param min_batch_size: minimum batch size before giving up (must be >= 1)
    :param request_delay: delay between requests in seconds (default: 1/API_RATE_LIMIT)
    :raises ValueError: if account_state missing address or min_batch_size < 1
    :raises RuntimeError: if setting state fails after all retries
    """
    logger = get_logger(LogGroupEnum.GNL)

    # Validate inputs
    if min_batch_size < 1:
        raise ValueError("min_batch_size must be at least 1")

    if "address" not in account_state:
        raise ValueError("account_state must contain 'address' key")

    if batch_size is None:
        batch_size = int(Config.get_config().get("STORAGE_ITERATION_BATCH_SIZE"))

    if request_delay is None:
        request_delay = 1.0 / float(Config.get_config().get("API_RATE_LIMIT"))

    pairs = account_state.get("pairs", {})
    address = account_state["address"]

    # If no pairs or few pairs, just send as-is
    if len(pairs) <= batch_size:
        if overwrite:
            proxy.set_state_overwrite([account_state])
        else:
            proxy.set_state([account_state])
        return

    # Split pairs into batches
    # Note: Python 3.7+ guarantees dict insertion order, so list() is deterministic
    # for a given input dict
    pairs_list = list(pairs.items())
    current_batch_size = batch_size
    pairs_sent = 0
    batches_sent = 0
    is_first_request = True

    while pairs_sent < len(pairs_list):
        # Build batch of pairs
        batch_end = min(pairs_sent + current_batch_size, len(pairs_list))
        batch_pairs = dict(pairs_list[pairs_sent:batch_end])

        # Build state for this request
        if is_first_request:
            # First request includes all account metadata
            state_to_send = {**account_state, "pairs": batch_pairs}
        else:
            # Subsequent requests only include address and pairs
            state_to_send = {"address": address, "pairs": batch_pairs}

        # Try to send with retry logic
        while current_batch_size >= min_batch_size:
            try:
                if is_first_request and overwrite:
                    proxy.set_state_overwrite([state_to_send])
                else:
                    proxy.set_state([state_to_send])

                # Success - move to next batch
                pairs_sent = batch_end
                is_first_request = False
                batches_sent += 1
                break

            except Exception as e:
                if _is_retryable_error(e):
                    new_batch_size = current_batch_size // 2
                    logger.info(
                        f"Set state for {address} failed with batch size "
                        f"{current_batch_size}, reducing to {new_batch_size}: {e}"
                    )
                    current_batch_size = new_batch_size

                    if current_batch_size >= min_batch_size:
                        # Rebuild batch with smaller size
                        batch_end = min(
                            pairs_sent + current_batch_size, len(pairs_list)
                        )
                        batch_pairs = dict(pairs_list[pairs_sent:batch_end])
                        if is_first_request:
                            state_to_send = {**account_state, "pairs": batch_pairs}
                        else:
                            state_to_send = {"address": address, "pairs": batch_pairs}

                        if request_delay > 0:
                            sleep(request_delay)
                else:
                    raise
        else:
            # Exhausted min batch size
            raise RuntimeError(
                f"Failed to set state for {address}: batch size reduced below "
                f"minimum ({min_batch_size}) after repeated timeouts. "
                f"Sent {pairs_sent}/{len(pairs_list)} pairs successfully. "
                f"The chain simulator may be in a partial state. "
                f"Consider retrying or increasing min_batch_size."
            )

        # Delay between successful batches
        if pairs_sent < len(pairs_list) and request_delay > 0:
            sleep(request_delay)

    logger.debug(
        f"Set state for {address} completed: {len(pairs_list)} pairs "
        f"in {batches_sent} batches"
    )


def _is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable (timeout or connection related).

    :param error: exception to check
    :return: True if the error is retryable
    """
    if isinstance(error, (Timeout, RequestsConnectionError)):
        return True
    if isinstance(error, HTTPError):
        # Retry on server errors (502, 503, 504)
        if error.response is not None:
            return error.response.status_code in (502, 503, 504)
    return False


def get_account_storage_with_fallback(
    proxy: ProxyNetworkProvider,
    address: Address,
    num_keys: int | None = None,
    request_delay: float | None = None,
    max_iterations: int = 100000,
    min_batch_size: int = 50,  # Reasonable minimum that balances retries vs giving up
    progress_logger: logging.Logger | None = None,
) -> AccountStorage:
    """
    Fetch all account storage with automatic fallback.
    First tries the paginated /address/iterate-keys endpoint, then falls back
    to the standard /address/{address}/keys endpoint if iteration is not available.

    When a request fails due to timeout or connection errors, the batch size is
    automatically reduced by half and the request is retried, preserving the
    current iterator state. The reduced batch size persists for subsequent
    iterations as large storage values may continue causing issues. If the batch
    size drops below min_batch_size, the function falls back to the standard
    endpoint.

    Note: Empty storage on the first request is treated as the endpoint not being
    enabled, triggering the fallback to the standard endpoint.

    :param proxy: proxy network provider to use
    :param address: address to fetch storage for
    :param num_keys: number of keys per request for iteration (default from config)
    :param request_delay: delay between requests in seconds (default: 1/API_RATE_LIMIT)
    :param max_iterations: maximum iterations to prevent infinite loops
    :param min_batch_size: minimum batch size before falling back to standard endpoint
    :param progress_logger: optional logger for progress reporting on slow operations
    :return: AccountStorage with all entries
    """
    logger = get_logger(LogGroupEnum.GNL)

    if num_keys is None:
        num_keys = int(Config.get_config().get("STORAGE_ITERATION_BATCH_SIZE"))

    if request_delay is None:
        request_delay = 1.0 / float(Config.get_config().get("API_RATE_LIMIT"))

    # Setup progress logger if progress_logger provided
    progress: ProgressLogger | None = None
    if progress_logger is not None:
        # Truncate to first 20 chars of bech32 address for readable logs
        label = address.to_bech32()[:20] + "..."
        progress = ProgressLogger(progress_logger, f"Storage key fetching for {label}")
        progress.start()

    # Try paginated endpoint first
    all_pairs: dict[str, str] = {}
    iterator_state: list[list[int]] = []
    iteration_succeeded = False
    current_batch_size = num_keys
    bech32_address = address.to_bech32()

    try:
        for iteration in range(max_iterations):
            if iteration > 0 and request_delay > 0:
                sleep(request_delay)

            # Inner retry loop with batch size reduction
            while current_batch_size >= min_batch_size:
                try:
                    url = "address/iterate-keys"
                    data = {
                        "address": bech32_address,
                        "numKeys": current_batch_size,
                        "iteratorState": iterator_state,
                    }
                    response = proxy.do_post_generic(url, data).to_dictionary()
                    pairs = response.get("pairs", {})
                    new_state = response.get("newIteratorState", [])

                    # Check if endpoint is not enabled (empty on first request)
                    if iteration == 0 and not pairs and not new_state:
                        raise StorageIterationError(
                            bech32_address,
                            "endpoint returned empty results "
                            "(feature may not be enabled)",
                        )

                    all_pairs.update(pairs)

                    # Report progress after each batch
                    if progress is not None:
                        progress.update(len(all_pairs))

                    if not new_state:  # Iteration complete
                        iteration_succeeded = True

                    iterator_state = new_state
                    break  # Success - exit inner retry loop

                except StorageIterationError:
                    raise  # Don't retry on this error

                except Exception as e:
                    if _is_retryable_error(e):
                        new_batch_size = current_batch_size // 2
                        logger.info(
                            f"Storage iteration for {bech32_address} failed with "
                            f"batch size {current_batch_size}, reducing to "
                            f"{new_batch_size}. Error: {type(e).__name__}: {e}"
                        )
                        current_batch_size = new_batch_size
                        if current_batch_size >= min_batch_size and request_delay > 0:
                            sleep(request_delay)
                    else:
                        raise

            else:
                # Min batch size exceeded - fall back to standard endpoint
                logger.debug(
                    f"Storage iteration for {bech32_address} exhausted minimum "
                    f"batch size ({min_batch_size}), falling back to standard endpoint"
                )
                break

            if iteration_succeeded:
                break

        else:
            raise MaxIterationError()

    except (StorageIterationError, MaxIterationError):
        iteration_succeeded = False

    except (Timeout, RequestsConnectionError, HTTPError):
        # Expected network errors - fallback silently
        iteration_succeeded = False

    except Exception as e:
        logger.warning(
            f"Unexpected error during storage iteration for {bech32_address}: "
            f"{type(e).__name__}: {e}"
        )
        iteration_succeeded = False

    # If iteration succeeded, convert to AccountStorage
    if iteration_succeeded and all_pairs:
        if progress is not None:
            progress.finish(len(all_pairs))
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
    if progress is not None:
        progress.finish(len(all_pairs) if all_pairs else 0)
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
