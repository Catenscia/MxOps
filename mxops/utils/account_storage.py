"""
author: Etienne Wallet

This module contains utils functions related to on-chain acount storage
"""

from multiversx_sdk import AccountStorageEntry, Token


ESDT_BALANCE_STORAGE_HEX_PREFIX = "454c524f4e4465736474"  # ELRONDesdt
ESDT_BALANCE_ROLE_HEX_PREFIX = "454c524f4e44726f6c6565736474"  # ELRONDroleesdt


def extract_token_from_entry(entry: AccountStorageEntry) -> Token | None:
    """
    Scan an account storage entry to see if it is related to an ESDT
    balance or an ESDT role
    Raw key is directly to simplify the parsing of a potential token nonce

    :param entry: entry to inspect
    :type entry: AccountStorageEntry
    :return: Token related to the entry if applicable
    :rtype: Token | None
    """
    raw_key = list(entry.raw.keys())[0]
    try:
        _, raw_token = raw_key.split(ESDT_BALANCE_STORAGE_HEX_PREFIX)
    except ValueError:
        raw_token = None

    if raw_token is None:
        try:
            _, raw_token = raw_key.split(ESDT_BALANCE_ROLE_HEX_PREFIX)
        except ValueError:
            pass
    if raw_token is None:
        return None
    hex_token_ticker, remaining = raw_token.split("2d")
    hex_random = remaining[:12]
    hex_nonce = remaining[12:]
    token_ticker = bytes.fromhex(hex_token_ticker).decode("utf-8")
    random_identifier = bytes.fromhex(hex_random).decode("utf-8")
    if len(hex_nonce) > 0:
        nonce = int(hex_nonce, base=16)
    else:
        nonce = 0
    return Token(f"{token_ticker}-{random_identifier}", nonce)


def extract_identifier_from_hex_key(hex_key: str) -> str | None:
    """
    Extract just the token identifier from a hex key without creating Token objects.
    This is a lightweight alternative to extract_token_from_entry() for cases where
    only the identifier is needed.

    :param hex_key: hex-encoded storage key
    :type hex_key: str
    :return: token identifier (ticker-random) or None if not an ESDT key
    :rtype: str | None
    """
    # Determine which prefix, if any
    if hex_key.startswith(ESDT_BALANCE_STORAGE_HEX_PREFIX):
        raw_token = hex_key[len(ESDT_BALANCE_STORAGE_HEX_PREFIX) :]
    elif hex_key.startswith(ESDT_BALANCE_ROLE_HEX_PREFIX):
        raw_token = hex_key[len(ESDT_BALANCE_ROLE_HEX_PREFIX) :]
    else:
        return None

    try:
        # Split at first dash (0x2d)
        parts = raw_token.split("2d", 1)
        if len(parts) != 2:
            return None

        hex_ticker = parts[0]
        hex_random = parts[1][:12]  # Random is always 6 chars = 12 hex

        ticker = bytes.fromhex(hex_ticker).decode("utf-8")
        random_id = bytes.fromhex(hex_random).decode("utf-8")
        return f"{ticker}-{random_id}"
    except (ValueError, UnicodeDecodeError):
        return None


def separate_esdt_related_storage(
    entries: AccountStorageEntry,
) -> tuple[dict[str, AccountStorageEntry], list[AccountStorageEntry]]:
    """
    Separate the storage entries related to an ESDT and the others
    Esdt entries will be grouped by token identifier (without nonce)

    :param entries: list of storage entries
    :type entries: AccountStorageEntry
    :return: esdt entries grouped by extedned identifier and the rest of the entries
    :rtype: tuple[dict[str, AccountStorageEntry], list[AccountStorageEntry]]
    """
    token_entries = {}
    other_entries = []
    for entry in entries:
        token = extract_token_from_entry(entry)
        if token is None:
            other_entries.append(entry)
            continue
        if token.identifier not in token_entries:
            token_entries[token.identifier] = []
        token_entries[token.identifier].append(entry)
    return token_entries, other_entries
