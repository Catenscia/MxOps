"""
Checks for the token_thin_air integration test.
Verifies that ESDT balances set "from thin air" via
ChainSimulatorSetTokenBalanceStep are observable through the standard
proxy ESDT lookup endpoints.
"""

from multiversx_sdk import Address, Token

from mxops.common.providers import MyProxyNetworkProvider
from mxops.data.execution_data import ScenarioData


def assert_account_token_balance(
    account_id: str, token_identifier: str, expected_amount: int
):
    """
    Query the chain simulator for the ESDT balance of an account and assert
    it matches the expected amount.

    :param account_id: MxOps account id (must resolve to a bech32 address)
    :param token_identifier: ESDT token identifier (e.g. "WEGLD-bd4d79")
    :param expected_amount: balance the account should hold (integer units)
    """
    scenario_data = ScenarioData.get()
    bech32 = scenario_data.get_account_value(account_id, "bech32")
    address = Address.new_from_bech32(bech32)
    expected_amount = int(expected_amount)

    proxy = MyProxyNetworkProvider()
    on_network = proxy.get_token_of_account(address, Token(token_identifier))
    actual = int(on_network.amount)
    if actual != expected_amount:
        raise AssertionError(
            f"Balance mismatch for {account_id} / {token_identifier}: "
            f"expected {expected_amount}, got {actual}"
        )
