"""
author: Etienne Wallet

This module contains Steps used to setup environment, chain or workflow
"""

from configparser import NoOptionError
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import json
import os
import time
from typing import ClassVar

from multiversx_sdk import AccountStorage, Address, ProxyNetworkProvider
from multiversx_sdk.network_providers.config import NetworkProviderConfig
import requests

from mxops import errors
from mxops.common.constants import ESDT_MODULE_BECH32
from mxops.common.providers import (
    MyProxyNetworkProvider,
    get_account_storage_with_fallback,
    set_state_with_batching,
    set_states_batched,
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
from mxops.smart_values import SmartDict, SmartInt, SmartPath, SmartValue
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
class ChainSimulatorSetStateStep(Step):
    """
    Represents a step to set specific storage key-value pairs for an address
    on the chain simulator using hex-encoded keys and values.
    """

    address: SmartAddress
    keys: SmartDict
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.CHAIN_SIMULATOR,)

    @staticmethod
    def _validate_hex_keys(keys: dict[str, str]):
        """Validate that all keys and values are valid hex strings."""
        if not keys:
            raise errors.InvalidSceneDefinition(
                "ChainSimulatorSetState requires at least one key-value pair"
            )
        for k, v in keys.items():
            try:
                bytes.fromhex(k)
            except ValueError as exc:
                raise errors.InvalidSceneDefinition(
                    f"ChainSimulatorSetState key must be hex-encoded, got: '{k}'"
                ) from exc
            try:
                bytes.fromhex(v)
            except ValueError as exc:
                raise errors.InvalidSceneDefinition(
                    f"ChainSimulatorSetState value must be hex-encoded, got: '{v}'"
                ) from exc

    def _execute(self):
        """
        Post hex-encoded key-value pairs to the chain simulator's
        address-specific set-state endpoint.
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        proxy = MyProxyNetworkProvider()
        bech32 = self.address.get_evaluated_value().to_bech32()
        keys = self.keys.get_evaluated_value()
        self._validate_hex_keys(keys)
        logger.info(
            f"Setting {len(keys)} storage key(s) for {bech32} on chain simulator"
        )
        response = proxy.set_address_state(bech32, keys)
        logger.debug(f"set-state response: {response.to_dictionary()}")


def _build_source_proxy(source_network: NetworkEnum) -> ProxyNetworkProvider:
    """Build a ProxyNetworkProvider for the source network with configured timeout."""
    config = Config.get_config()
    url = config.get("PROXY", source_network)
    timeout = int(config.get("PROXY_TIMEOUT", source_network))
    provider_config = NetworkProviderConfig(requests_options={"timeout": timeout})
    return ProxyNetworkProvider(url, config=provider_config)


def _fetch_account_clone_data(
    address: Address,
    source_network: NetworkEnum,
    caching_period: datetime,
    clone_balance: bool,
    clone_code: bool,
    fetch_current_state: bool = True,
) -> dict:
    """
    Fetch and construct the raw data to clone an account's balance and code.

    :param address: address to clone
    :param source_network: network to clone from
    :param caching_period: caching threshold for data freshness
    :param clone_balance: whether to clone the balance
    :param clone_code: whether to clone the code
    :param fetch_current_state: whether to fetch the current account state
        from the local proxy to preserve rootHash/balance/code. Set to False
        for batch cloning where accounts don't yet exist on the target.
    :return: raw account data to set in the current network
    """
    logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)

    source_account = try_load_account_data(source_network, address, caching_period)
    if source_account is None:
        logger.debug(
            f"Fetching account of {address.to_bech32()} on {source_network.value}"
        )
        source_proxy = _build_source_proxy(source_network)
        source_account = source_proxy.get_account(address)
        save_account_data(source_network, source_account)

    raw_account_to_set = deepcopy(source_account.raw["account"])

    if fetch_current_state:
        proxy = MyProxyNetworkProvider()
        current_raw_account = proxy.get_account(address).raw["account"]
        raw_account_to_set["rootHash"] = current_raw_account["rootHash"]

        if not clone_balance:
            raw_account_to_set["balance"] = current_raw_account["balance"]

        if not clone_code:
            raw_account_to_set["code"] = current_raw_account["code"]
            raw_account_to_set["codeHash"] = current_raw_account["codeHash"]
            raw_account_to_set["codeMetadata"] = current_raw_account["codeMetadata"]

    return raw_account_to_set


def _fetch_source_storage(
    source_network: NetworkEnum, address: Address, caching_period: datetime
) -> AccountStorage:
    """Fetch source storage from cache or proxy."""
    logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
    source_storage = try_load_account_storage_data(
        source_network, address, caching_period
    )
    if source_storage is None:
        logger.debug(
            f"Fetching storage of {address.to_bech32()} on {source_network.value}"
        )
        source_proxy = _build_source_proxy(source_network)
        source_storage = get_account_storage_with_fallback(
            source_proxy, address, progress_logger=logger
        )
        save_account_storage_data(source_network, address, source_storage)
    return source_storage


def _get_storage_clone_data(
    address: Address,
    source_network: NetworkEnum,
    caching_period: datetime,
    clone_storage: bool,
    clone_esdts: bool,
) -> tuple[dict, set[str]]:
    """
    Fetch and construct the raw data to clone the storage of an account.

    :param address: address to clone storage for
    :param source_network: network to clone from
    :param caching_period: caching threshold for data freshness
    :param clone_storage: whether to clone non-ESDT storage
    :param clone_esdts: whether to clone ESDT entries
    :return: raw storage data and set of seen ESDT identifiers
    """
    source_storage = _fetch_source_storage(source_network, address, caching_period)

    raw_data = {}
    seen_esdt = set()

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
    esdt_identifiers: set[str], current_hex_keys: set[str]
) -> list[str]:
    """Find ESDT identifiers not present in current network."""
    return [
        identifier
        for identifier in esdt_identifiers
        if identifier.encode("utf-8").hex() not in current_hex_keys
    ]


def _fetch_missing_esdt_entries(
    missing_identifiers: list[str],
    esdt_module_address: Address,
    source_network: NetworkEnum,
    caching_threshold: datetime,
) -> dict[str, str]:
    """Fetch missing ESDT entries from cache or source network."""
    pairs = {}
    source_proxy = None

    for identifier in missing_identifiers:
        hex_identifier = identifier.encode("utf-8").hex()

        cached_value = try_load_esdt_module_entry(
            source_network, identifier, caching_threshold
        )
        if cached_value is not None:
            pairs[hex_identifier] = cached_value
            continue

        if source_proxy is None:
            source_proxy = _build_source_proxy(source_network)

        source_entry = source_proxy.get_account_storage_entry(
            esdt_module_address, identifier
        )
        pairs[hex_identifier] = source_entry.raw["value"]
        save_esdt_module_entry(source_network, identifier, source_entry.raw["value"])

    return pairs


def _get_esdt_module_clone_data(
    esdt_identifiers: set[str],
    source_network: NetworkEnum,
    caching_period: datetime,
) -> dict:
    """
    Using a set of identifiers, determine for each ESDT if it is already known
    to the current network, otherwise fetch the data from the source network.

    :param esdt_identifiers: ESDT identifiers to check
    :param source_network: network to fetch missing entries from
    :param caching_period: caching threshold for data freshness
    :return: data to set for the ESDT module
    """
    proxy = MyProxyNetworkProvider()
    esdt_module_address = Address.new_from_bech32(ESDT_MODULE_BECH32)

    raw_account_data = proxy.get_account(esdt_module_address).raw["account"]
    raw_account_data["pairs"] = {}

    current_storage = get_account_storage_with_fallback(proxy, esdt_module_address)
    current_hex_keys = set(current_storage.raw.get("pairs", {}).keys())

    missing_identifiers = _find_missing_esdt_identifiers(
        esdt_identifiers, current_hex_keys
    )
    if not missing_identifiers:
        return raw_account_data

    logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
    logger.debug(
        f"Need to clone {len(missing_identifiers)} ESDT module entries "
        f"from {source_network.value}"
    )

    raw_account_data["pairs"] = _fetch_missing_esdt_entries(
        missing_identifiers,
        esdt_module_address,
        source_network,
        caching_period,
    )

    return raw_account_data


def _fetch_with_backoff(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> requests.Response | None:
    """
    Fetch a URL with exponential backoff on 429 rate limit errors.

    :param url: URL to fetch
    :param max_retries: maximum number of retry attempts
    :param base_delay: base delay in seconds for exponential backoff
    :return: the response (may be a 429 if all retries were exhausted)
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


def _insert_tokens_in_elasticsearch(
    esdt_identifiers: set[str],
    source_network: NetworkEnum,
    caching_period: datetime,
    requests_per_second: float = 4.0,
):
    """
    Fetch token data from the source network's Elasticsearch and insert
    it into the local chain simulator's Elasticsearch.
    This is required to make tokens visible in the chain simulator terminal
    and available through the API.

    See: https://github.com/multiversx/mx-chain-simulator-go/issues/109

    :param esdt_identifiers: set of ESDT identifiers to insert
    :param source_network: network to fetch token data from
    :param caching_period: caching threshold for data freshness
    :param requests_per_second: rate limit for API requests (default: 4.0)
    """
    if not esdt_identifiers:
        return

    request_interval = 1.0 / requests_per_second
    logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
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

    tokens_to_insert: dict[str, dict] = {}

    progress = ProgressLogger(logger, "Token data fetching")
    progress.start()
    processed_count = 0

    for identifier in esdt_identifiers:
        token_source = try_load_esdt_token_data(
            source_network, identifier, caching_period
        )

        if token_source is None:
            source_url = f"{source_es_url}/tokens/_doc/{identifier}"
            try:
                response = _fetch_with_backoff(source_url)
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
                save_esdt_token_data(source_network, identifier, token_source)
            except requests.RequestException as e:
                logger.warning(
                    f"Error fetching token {identifier} from source Elasticsearch: {e}"
                )
                continue

            time.sleep(request_interval)

        tokens_to_insert[identifier] = token_source
        processed_count += 1
        progress.update(processed_count)

    progress.finish(processed_count)

    if not tokens_to_insert:
        return

    bulk_lines = []
    for identifier, token_source in tokens_to_insert.items():
        action = {"index": {"_index": "tokens", "_id": identifier}}
        bulk_lines.append(json.dumps(action))
        bulk_lines.append(json.dumps(token_source))

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
                    f"{len(tokens_to_insert)} tokens inserted into local Elasticsearch"
                )
    except requests.RequestException as e:
        logger.warning(f"Error during bulk insert to local Elasticsearch: {e}")


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

    def _execute(self):
        """
        Retrieve the source  account and its storage
        and set this state to the current network
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        address = self.address.get_evaluated_value()
        caching_period = self.caching_period.get_evaluated_value()

        logger.info(
            f"Cloning account {self.address.get_evaluation_string()} from "
            f"{source_network.value}"
        )
        proxy = MyProxyNetworkProvider()

        account_state = _fetch_account_clone_data(
            address,
            source_network,
            caching_period,
            self.clone_balance.get_evaluated_value(),
            self.clone_code.get_evaluated_value(),
        )

        clone_esdts = self.clone_esdts.get_evaluated_value()
        clone_storage = self.clone_storage.get_evaluated_value()
        if clone_esdts or clone_storage:
            account_state["pairs"], esdt_seen = _get_storage_clone_data(
                address, source_network, caching_period, clone_storage, clone_esdts
            )
        else:
            esdt_seen = set()

        if len(esdt_seen) > 0:
            esdt_module_state = _get_esdt_module_clone_data(
                esdt_seen, source_network, caching_period
            )
            proxy.set_state([esdt_module_state])
            _insert_tokens_in_elasticsearch(esdt_seen, source_network, caching_period)

        set_state_with_batching(
            proxy,
            account_state,
            overwrite=self.overwrite.get_evaluated_value(),
        )


@dataclass
class AccountBatchCloneStep(Step):
    """
    Represent a step that clones multiple accounts from another network
    to the current network in an optimized batch fashion.
    Unlike AccountCloneStep which pushes each account individually,
    this step collects all data first and then pushes in optimized batches:
    - Single ESDT module reconciliation instead of one per account
    - Single Elasticsearch bulk insert for all tokens
    - Smart batched set_state calls grouped by payload size
    """

    addresses: SmartAddresses
    source_network: SmartStr
    clone_balance: SmartBool = True
    clone_code: SmartBool = True
    clone_storage: SmartBool = True
    clone_esdts: SmartBool = True
    overwrite: SmartBool = True
    caching_period: SmartDatetime = "10 days"
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.CHAIN_SIMULATOR,)

    def _execute(self):
        """
        Collect clone data for all addresses, then push in optimized batches.
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )

        source_network = parse_network_enum(self.source_network.get_evaluated_value())
        addresses = self.addresses.get_evaluated_value()
        caching_period = self.caching_period.get_evaluated_value()
        clone_balance = self.clone_balance.get_evaluated_value()
        clone_code = self.clone_code.get_evaluated_value()
        clone_storage = self.clone_storage.get_evaluated_value()
        clone_esdts = self.clone_esdts.get_evaluated_value()

        logger.info(
            f"Batch cloning {len(addresses)} accounts from {source_network.value}"
        )
        step_start = time.time()

        # Phase 1: Collect all account states and ESDT identifiers
        logger.info(
            f"Phase 1/4: Collecting data for {len(addresses)} accounts "
            f"from {source_network.value}"
        )
        all_account_states: list[dict] = []
        all_esdt_identifiers: set[str] = set()
        source_request_delay = 1.0 / float(
            Config.get_config().get("API_RATE_LIMIT", source_network)
        )

        progress = ProgressLogger(logger, "Account data collection")
        progress.start()

        for i, address in enumerate(addresses):
            logger.debug(
                f"Collecting data for {address.to_bech32()} ({i + 1}/{len(addresses)})"
            )
            # Check cache before fetching to know if we'll hit the network
            account_cached = (
                try_load_account_data(source_network, address, caching_period)
                is not None
            )
            storage_cached = not (clone_esdts or clone_storage) or (
                try_load_account_storage_data(source_network, address, caching_period)
                is not None
            )

            account_state = _fetch_account_clone_data(
                address,
                source_network,
                caching_period,
                clone_balance,
                clone_code,
                fetch_current_state=False,
            )

            if clone_esdts or clone_storage:
                account_state["pairs"], esdt_seen = _get_storage_clone_data(
                    address, source_network, caching_period, clone_storage, clone_esdts
                )
                all_esdt_identifiers.update(esdt_seen)
            else:
                # Remove pairs to avoid carrying source storage
                # when neither storage nor ESDT cloning is requested
                account_state.pop("pairs", None)

            all_account_states.append(account_state)
            progress.update(i + 1)

            # Rate limit only when we actually hit the source network
            if not (account_cached and storage_cached) and i < len(addresses) - 1:
                time.sleep(source_request_delay)

        progress.finish(len(addresses))
        phase1_elapsed = time.time() - step_start
        logger.info(f"Phase 1/4 completed in {phase1_elapsed:.1f}s")

        # Phase 2: Single ESDT module reconciliation
        phase2_start = time.time()
        proxy = MyProxyNetworkProvider()
        if all_esdt_identifiers:
            logger.info(
                f"Phase 2/4: Reconciling {len(all_esdt_identifiers)} "
                f"unique ESDT identifiers with chain simulator"
            )
            esdt_module_state = _get_esdt_module_clone_data(
                all_esdt_identifiers, source_network, caching_period
            )
            # Insert ESDT module state as first element so it is included
            # in the overwrite batch and not wiped by a subsequent
            # set_state_overwrite call
            if esdt_module_state.get("pairs"):
                all_account_states.insert(0, esdt_module_state)
        else:
            logger.info("Phase 2/4: No ESDT identifiers to reconcile, skipping")
        phase2_elapsed = time.time() - phase2_start
        logger.info(f"Phase 2/4 completed in {phase2_elapsed:.1f}s")

        # Phase 3: Single Elasticsearch bulk insert
        phase3_start = time.time()
        if all_esdt_identifiers:
            logger.info(
                f"Phase 3/4: Inserting {len(all_esdt_identifiers)} "
                "tokens into Elasticsearch"
            )
            _insert_tokens_in_elasticsearch(
                all_esdt_identifiers, source_network, caching_period
            )
        else:
            logger.info("Phase 3/4: No tokens to insert, skipping")
        phase3_elapsed = time.time() - phase3_start
        logger.info(f"Phase 3/4 completed in {phase3_elapsed:.1f}s")

        # Phase 4: Smart batched account state push
        phase4_start = time.time()
        logger.info(
            f"Phase 4/4: Pushing {len(all_account_states)} "
            "account states to chain simulator"
        )
        set_states_batched(
            proxy,
            all_account_states,
            overwrite=self.overwrite.get_evaluated_value(),
        )
        phase4_elapsed = time.time() - phase4_start
        total_elapsed = time.time() - step_start
        logger.info(
            f"Phase 4/4 completed in {phase4_elapsed:.1f}s. "
            f"Total batch clone: {total_elapsed:.1f}s"
        )
