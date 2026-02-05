"""
author: Etienne Wallet

This module contains Steps used to setup environment, chain or workflow
"""

from configparser import NoOptionError
from copy import deepcopy
from dataclasses import dataclass
import json
import os
import time
from typing import ClassVar

from multiversx_sdk import Address, ProxyNetworkProvider
import requests

from mxops import errors
from mxops.common.constants import ESDT_MODULE_BECH32
from mxops.common.providers import (
    MyProxyNetworkProvider,
    get_account_storage_with_fallback,
)
from mxops.config.config import Config
from mxops.data.data_cache import (
    save_account_data,
    save_account_storage_data,
    save_esdt_module_entry,
    save_esdt_token_data,
    try_load_account_data,
    try_load_account_storage_data,
    try_load_esdt_module_entry,
    try_load_esdt_token_data,
)
from mxops.data.execution_data import ScenarioData
from mxops.enums import LogGroupEnum, NetworkEnum, parse_network_enum
from mxops.execution import utils
from mxops.execution.account import AccountsManager
from mxops.smart_values import SmartInt, SmartPath, SmartValue
from mxops.smart_values.mx_sdk import SmartAddress, SmartAddresses
from mxops.smart_values.native import SmartBool, SmartDatetime, SmartStr
from mxops.execution.steps.base import Step
from mxops.execution.steps.transactions import TransferStep
from mxops.utils.account_storage import (
    ESDT_BALANCE_STORAGE_HEX_PREFIX,
    ESDT_BALANCE_ROLE_HEX_PREFIX,
    extract_identifier_from_hex_key,
)
from mxops.utils.msc import get_account_link
from mxops.utils.progress import ProgressLogger
from mxops.utils.wallets import generate_keystore_wallet, generate_pem_wallet


@dataclass
class GenerateWalletsStep(Step):
    """
    Represents a step to generate some MultiversX wallets
    Supports PEM and keystore formats
    """

    save_folder: SmartPath
    wallets: SmartValue
    shard: SmartInt | None = None
    format: SmartStr = "pem"
    password_env_var: SmartStr | None = None

    def _execute(self):
        """
        Create the wanted wallets at the designated location

        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        save_folder = self.save_folder.get_evaluated_value()
        save_folder.mkdir(parents=True, exist_ok=True)
        wallets = self.wallets.get_evaluated_value()
        shard = None if self.shard is None else self.shard.get_evaluated_value()
        wallet_format = (
            self.format.get_evaluated_value()
            if isinstance(self.format, SmartStr)
            else self.format
        )

        # Validate keystore requirements
        if wallet_format == "keystore":
            if self.password_env_var is None:
                raise errors.InvalidSceneDefinition(
                    "GenerateWalletsStep with format='keystore' "
                    "requires password_env_var"
                )
            password_env_var = self.password_env_var.get_evaluated_value()
            password = os.environ.get(password_env_var)
            if password is None:
                raise errors.KeystorePasswordNotFound(password_env_var)

        account_manager = AccountsManager()
        if isinstance(wallets, int):
            n_wallets = wallets
            names = [None] * n_wallets
        elif isinstance(wallets, list):
            n_wallets = len(wallets)
            names = wallets
        else:
            raise ValueError(
                "the wallets argument must be of type int or list[str], "
                f"got {type(wallets)}"
            )
        for i, name in enumerate(names):
            if name is None:
                wallet_name = None
            else:
                wallet_name = utils.retrieve_value_from_any(name)

            if wallet_format == "pem":
                pem_wallet, wallet_address = generate_pem_wallet(shard)
                if wallet_name is None:
                    wallet_name = wallet_address.to_bech32()
                wallet_path = save_folder / f"{wallet_name}.pem"
                if os.path.isfile(wallet_path.as_posix()):
                    raise errors.WalletAlreadyExist(wallet_path)
                pem_wallet.save(wallet_path)
                account_manager.load_register_pem_account(wallet_path, wallet_name)
            else:  # keystore
                keystore_wallet, wallet_address = generate_keystore_wallet(
                    shard, password
                )
                if wallet_name is None:
                    wallet_name = wallet_address.to_bech32()
                wallet_path = save_folder / f"{wallet_name}.json"
                if os.path.isfile(wallet_path.as_posix()):
                    raise errors.WalletAlreadyExist(wallet_path)
                keystore_wallet.save(wallet_path)
                account_manager.load_register_keystore_account(
                    wallet_path, password_env_var, wallet_name
                )

            logger.info(
                f"Wallet n°{i + 1}/{n_wallets} generated with address "
                f"{wallet_address.to_bech32()} at {wallet_path}"
            )


@dataclass
class R3D4FaucetStep(Step):
    """
    Represents a step to request some EGLD from the r3d4 faucet
    """

    targets: SmartAddresses
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.DEV, NetworkEnum.TEST)

    def get_egld_details(self) -> dict:
        """
        Request r3d4 for the details regarding the EGLD token faucet

        :return: token id, max amount and available
        :rtype: Tuple[int, int]
        """
        config = Config.get_config()
        url = f"{config.get('R3D4_API')}/faucet/tokens"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        chain = config.get("CHAIN")
        for token_data in data:
            if token_data["network"] != chain:
                continue
            if token_data["identifier"] in ("xEGLD", "dEGLD", "EGLD", "tEGLD"):
                return token_data
        raise errors.TokenNotFound("Could not found EGLD in the faucet")

    def _execute(self):
        """
        Seach for the r3d4 token id of EGLD in the current network and
        ask for EGLD from the faucet
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        egld_details = self.get_egld_details()
        request_amount = float(egld_details["max"])
        for target in self.targets.get_evaluated_value():
            logger.info(
                f"Requesting {request_amount} {egld_details['identifier']}"
                f" from r3d4 faucet for {target.to_bech32()}"
            )
            self.request_faucet(
                target.to_bech32(), egld_details["id"], str(request_amount)
            )
            logger.info(
                f"Check the account for funds arrival: {get_account_link(target)}"
            )

    def request_faucet(self, bech32: str, token_id: str, amount: str):
        """
        Request the faucet for a token amount for an address

        :param bech32: address where to receive the tokens
        :type bech32: str
        :param token_id: r3d4 token id to receive
        :type token_id: int
        :param amount: amount of token to receive, with decimal
        :type amount: str
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        config = Config.get_config()
        url = f"{config.get('R3D4_API')}/faucet/list"
        headers = {
            "accept": "application/json",
        }
        data = {
            "formdata": {
                "network": config.get("CHAIN"),
                "token": token_id,
                "address": bech32,
                "amount": amount,
            }
        }
        response = requests.post(url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        return_data = response.json()
        if "error" in return_data:
            raise errors.FaucetFailed(return_data["error"])
        logger.info(f"Response from faucet: {return_data['success']}")


@dataclass
class ChainSimulatorFaucetStep(Step):
    """
    Represents a step to request some EGLD from the chain-simulator faucet
    (aka initial wallets of the chain simulator)
    """

    targets: SmartAddresses
    amount: SmartInt
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.CHAIN_SIMULATOR,)

    def _execute(self):
        """
        Retrieve the initial wallets of the chain simulator and
        make them send some funds
        """
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        proxy = MyProxyNetworkProvider()
        initial_wallet_data = proxy.get_initial_wallets()
        sender = initial_wallet_data["balanceWallets"]["0"]["address"]["bech32"]
        for target in self.targets.get_evaluated_value():
            egld_transfer_step = TransferStep(
                sender=sender, receiver=target, value=self.amount.get_evaluated_value()
            )
            egld_transfer_step.execute()


@dataclass
class AccountCloneStep(Step):
    """
    Represent a step that clone an account from another network
    to the current network
    If needed, ESDT that do not exist in the current network will
    be created to be identical to the other network
    """

    address: SmartAddress
    source_network: SmartStr
    clone_balance: SmartBool = True
    clone_code: SmartBool = True
    clone_storage: SmartBool = True
    clone_esdts: SmartBool = True
    overwrite: SmartBool = True
    caching_period: SmartDatetime = "10 days"
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.CHAIN_SIMULATOR,)

    def get_account_clone_data(self) -> dict:
        """
        Fetch and construct the raw data to clone the account, the balance
        and the code of the account

        :return: raw data to clone and set in the current network
        :rtype: dict
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        address = self.address.get_evaluated_value()

        # fetch the source account from cache or proxy
        source_account = try_load_account_data(
            source_network, address, self.caching_period.get_evaluated_value()
        )
        if source_account is None:
            logger.debug(
                f"Fetchting account of {address.to_bech32()} on {source_network.value}"
            )
            source_proxy = ProxyNetworkProvider(
                Config.get_config().get("PROXY", source_network)
            )
            source_account = source_proxy.get_account(address)
            save_account_data(source_network, source_account)

        # fetch current account and build the account to set
        proxy = MyProxyNetworkProvider()
        current_raw_account = proxy.get_account(address).raw["account"]
        raw_account_to_set = deepcopy(source_account.raw["account"])
        raw_account_to_set["rootHash"] = current_raw_account["rootHash"]

        if not self.clone_balance.get_evaluated_value():
            raw_account_to_set["balance"] = current_raw_account["balance"]

        if not self.clone_code.get_evaluated_value():
            raw_account_to_set["code"] = current_raw_account["code"]
            raw_account_to_set["codeHash"] = current_raw_account["codeHash"]
            raw_account_to_set["codeMetadata"] = current_raw_account["codeMetadata"]
        return raw_account_to_set

    def _fetch_source_storage(self, source_network: NetworkEnum, address: Address):
        """Fetch source storage from cache or proxy."""
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        source_storage = try_load_account_storage_data(
            source_network, address, self.caching_period.get_evaluated_value()
        )
        if source_storage is None:
            logger.debug(
                f"Fetchting storage of {address.to_bech32()} on {source_network.value}"
            )
            source_proxy = ProxyNetworkProvider(
                Config.get_config().get("PROXY", source_network)
            )
            source_storage = get_account_storage_with_fallback(
                source_proxy, address, progress_logger=logger
            )
            save_account_storage_data(source_network, address, source_storage)
        return source_storage

    def get_storage_clone_data(self) -> tuple[dict, set[str]]:
        """
        Fetch and construct the raw data to clone the storage of the account.
        Optimized to work directly with the pairs dict in a single pass,
        avoiding object creation overhead.

        :return: raw storage data to clone and seen esdt in the storage to clone
        :rtype: tuple[dict, set[str]]
        """
        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        address = self.address.get_evaluated_value()
        source_storage = self._fetch_source_storage(source_network, address)

        # Work directly with pairs dict instead of creating entry objects
        # This avoids triple iteration: object creation, separation, and dict updates
        raw_data = {}
        seen_esdt = set()
        clone_storage = self.clone_storage.get_evaluated_value()
        clone_esdts = self.clone_esdts.get_evaluated_value()

        for hex_key, hex_value in source_storage.raw.get("pairs", {}).items():
            is_esdt_or_role = hex_key.startswith(
                ESDT_BALANCE_STORAGE_HEX_PREFIX
            ) or hex_key.startswith(ESDT_BALANCE_ROLE_HEX_PREFIX)

            if is_esdt_or_role:
                if clone_esdts:
                    raw_data[hex_key] = hex_value
                    identifier = extract_identifier_from_hex_key(hex_key)
                    if identifier:
                        seen_esdt.add(identifier)
            elif clone_storage:
                raw_data[hex_key] = hex_value

        return raw_data, seen_esdt

    def _find_missing_esdt_identifiers(
        self, esdt_identifiers: set[str], current_hex_keys: set[str]
    ) -> list[str]:
        """Find ESDT identifiers not present in current network."""
        return [
            identifier
            for identifier in esdt_identifiers
            if identifier.encode("utf-8").hex() not in current_hex_keys
        ]

    def _fetch_missing_esdt_entries(
        self,
        missing_identifiers: list[str],
        esdt_module_address: Address,
        source_network: NetworkEnum,
        caching_threshold,
    ) -> dict[str, str]:
        """Fetch missing ESDT entries from cache or source network."""
        pairs = {}
        source_proxy = None  # Lazy init only if needed

        for identifier in missing_identifiers:
            hex_identifier = identifier.encode("utf-8").hex()

            # Try cache first
            cached_value = try_load_esdt_module_entry(
                source_network, identifier, caching_threshold
            )
            if cached_value is not None:
                pairs[hex_identifier] = cached_value
                continue

            # Lazy init source proxy only when needed
            if source_proxy is None:
                source_proxy = ProxyNetworkProvider(
                    Config.get_config().get("PROXY", source_network)
                )

            # Fetch from source and cache
            source_entry = source_proxy.get_account_storage_entry(
                esdt_module_address, identifier
            )
            pairs[hex_identifier] = source_entry.raw["value"]
            save_esdt_module_entry(
                source_network, identifier, source_entry.raw["value"]
            )

        return pairs

    def get_esdt_module_clone_data(self, esdt_identifiers: set[str]) -> dict:
        """
        Using a set of identifiers, determine for each esdt if it is already known
        to the current network, otherwise fetch the data on the source network.
        Optimized with batch fetching (1 call instead of N for target) and caching.

        :param esdt_identifiers: esdt identifiers to check
        :type esdt_identifiers: set[str]
        :return: data to set for the esdt module
        :rtype: dict
        """
        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        proxy = MyProxyNetworkProvider()
        esdt_module_address = Address.new_from_bech32(ESDT_MODULE_BECH32)

        raw_account_data = proxy.get_account(esdt_module_address).raw["account"]
        raw_account_data["pairs"] = {}

        # Batch fetch current ESDT module storage (1 call instead of N)
        current_storage = get_account_storage_with_fallback(proxy, esdt_module_address)
        current_hex_keys = set(current_storage.raw.get("pairs", {}).keys())

        missing_identifiers = self._find_missing_esdt_identifiers(
            esdt_identifiers, current_hex_keys
        )
        if not missing_identifiers:
            return raw_account_data

        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        logger.debug(
            f"Need to clone {len(missing_identifiers)} ESDT module entries "
            f"from {source_network.value}"
        )

        raw_account_data["pairs"] = self._fetch_missing_esdt_entries(
            missing_identifiers,
            esdt_module_address,
            source_network,
            self.caching_period.get_evaluated_value(),
        )

        return raw_account_data

    def _fetch_with_backoff(
        self,
        url: str,
        max_retries: int = 5,
        base_delay: float = 1.0,
    ) -> requests.Response | None:
        """
        Fetch a URL with exponential backoff on 429 rate limit errors.

        :param url: URL to fetch
        :type url: str
        :param max_retries: maximum number of retry attempts
        :type max_retries: int
        :param base_delay: base delay in seconds for exponential backoff
        :type base_delay: float
        :return: the response if successful, None if all retries exhausted
        :rtype: requests.Response | None
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        for attempt in range(max_retries + 1):
            response = requests.get(url, timeout=10)
            if response.status_code != 429:
                return response

            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                logger.debug(
                    f"Rate limited (429), retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

        return response

    def insert_tokens_in_elasticsearch(
        self, esdt_identifiers: set[str], requests_per_second: float = 4.0
    ):
        """
        Fetch token data from the source network's Elasticsearch and insert
        it into the local chain simulator's Elasticsearch.
        This is required to make tokens visible in the chain simulator terminal
        and available through the API.

        See: https://github.com/multiversx/mx-chain-simulator-go/issues/109

        :param esdt_identifiers: set of esdt identifiers to insert
        :type esdt_identifiers: set[str]
        :param requests_per_second: rate limit for API requests (default: 4.0)
        :type requests_per_second: float
        """
        if not esdt_identifiers:
            return

        request_interval = 1.0 / requests_per_second
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        config = Config.get_config()

        try:
            source_es_url = config.get("ELASTICSEARCH", source_network)
        except NoOptionError:
            logger.debug(
                f"No Elasticsearch URL configured for {source_network.value}, "
                "skipping token insertion"
            )
            return

        try:
            local_es_url = config.get("ELASTICSEARCH")
        except NoOptionError:
            logger.debug(
                "No Elasticsearch URL configured for local network, "
                "skipping token insertion"
            )
            return

        caching_threshold = self.caching_period.get_evaluated_value()

        # Collect all token data first
        tokens_to_insert: dict[str, dict] = {}

        # Setup progress logging for slow token fetches
        progress = ProgressLogger(logger, "Token data fetching")
        progress.start()
        processed_count = 0

        for identifier in esdt_identifiers:
            # Try to load token data from cache first
            token_source = try_load_esdt_token_data(
                source_network, identifier, caching_threshold
            )

            if token_source is None:
                # Fetch token data from source Elasticsearch with backoff
                source_url = f"{source_es_url}/tokens/_doc/{identifier}"
                try:
                    response = self._fetch_with_backoff(source_url)
                    if response is None or response.status_code != 200:
                        status = response.status_code if response else "no response"
                        logger.warning(
                            f"Could not fetch token {identifier} from source "
                            f"Elasticsearch: {status}"
                        )
                        continue
                    token_data = response.json()
                    if not token_data.get("found", False):
                        logger.warning(
                            f"Token {identifier} not found in source Elasticsearch"
                        )
                        continue
                    token_source = token_data.get("_source", {})
                    # Save to cache for future use
                    save_esdt_token_data(source_network, identifier, token_source)
                except requests.RequestException as e:
                    logger.warning(
                        f"Error fetching token {identifier} from source "
                        f"Elasticsearch: {e}"
                    )
                    continue

                # Rate limit to avoid 429 errors from source Elasticsearch
                time.sleep(request_interval)

            tokens_to_insert[identifier] = token_source
            processed_count += 1
            progress.update(processed_count)

        progress.finish(processed_count)

        # Batch insert tokens into local Elasticsearch using bulk API
        if not tokens_to_insert:
            return

        bulk_lines = []
        for identifier, token_source in tokens_to_insert.items():
            # Each document needs an action line and a source line
            action = {"index": {"_index": "tokens", "_id": identifier}}
            bulk_lines.append(json.dumps(action))
            bulk_lines.append(json.dumps(token_source))

        # Bulk API requires newline-delimited JSON with trailing newline
        bulk_body = "\n".join(bulk_lines) + "\n"

        bulk_url = f"{local_es_url}/_bulk"
        try:
            response = requests.post(
                bulk_url,
                data=bulk_body,
                headers={"Content-Type": "application/x-ndjson"},
                timeout=30,
            )
            if response.status_code not in (200, 201):
                logger.warning(
                    f"Bulk insert to local Elasticsearch failed: "
                    f"{response.status_code} - {response.text}"
                )
            else:
                result = response.json()
                if result.get("errors", False):
                    failed = sum(
                        1
                        for item in result.get("items", [])
                        if "error" in item.get("index", {})
                    )
                    logger.warning(
                        f"Bulk insert had {failed} errors out of "
                        f"{len(tokens_to_insert)} tokens"
                    )
                else:
                    logger.debug(
                        f"{len(tokens_to_insert)} tokens inserted into "
                        "local Elasticsearch"
                    )
        except requests.RequestException as e:
            logger.warning(f"Error during bulk insert to local Elasticsearch: {e}")

    def _execute(self):
        """
        Retrieve the source  account and its storage
        and set this state to the current network
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        logger.info(
            f"Cloning account {self.address.get_evaluation_string()} from "
            f"{source_network.value}"
        )
        proxy = MyProxyNetworkProvider()

        account_state = self.get_account_clone_data()
        if (
            self.clone_esdts.get_evaluated_value()
            or self.clone_storage.get_evaluated_value()
        ):
            account_state["pairs"], esdt_seen = self.get_storage_clone_data()
        else:
            esdt_seen = set()

        if len(esdt_seen) > 0:
            esdt_module_state = self.get_esdt_module_clone_data(esdt_seen)
            proxy.set_state([esdt_module_state])
            # Insert tokens into Elasticsearch to make them visible in the
            # chain simulator terminal and available through API
            self.insert_tokens_in_elasticsearch(esdt_seen)

        if self.overwrite.get_evaluated_value():
            proxy.set_state_overwrite([account_state])
        else:
            proxy.set_state([account_state])
