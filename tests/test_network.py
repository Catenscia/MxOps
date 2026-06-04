"""
Unit tests for send_and_wait_for_result, covering both the block-generating
path and the auto-generate (poll-only) path on the chain simulator.
"""

from unittest.mock import MagicMock, patch

from mxops.config.config import Config
from mxops.execution.network import MIN_TX_REFRESH_PERIOD, send_and_wait_for_result


def _completed_tx():
    on_chain_tx = MagicMock()
    on_chain_tx.status.is_completed = True
    return on_chain_tx


def test_send_and_wait_generates_blocks_on_chain_simulator(chain_simulator_network):
    """Default chain-simulator behavior: MxOps drives blocks until completion."""
    completed = _completed_tx()
    with patch(
        "mxops.execution.network.MyProxyNetworkProvider"
    ) as mock_proxy_cls, patch("mxops.execution.network.time.sleep"):
        proxy = mock_proxy_cls.return_value
        proxy.send_transaction.return_value = bytes.fromhex("ab")
        proxy.get_transaction.return_value = completed

        result = send_and_wait_for_result(MagicMock())

    proxy.generate_blocks_until_tx_completion.assert_called_once_with("ab")
    assert result is completed


def test_send_and_wait_polls_without_generating_when_auto(chain_simulator_network):
    """With AUTO_GENERATE_BLOCKS=false MxOps must not drive blocks and must
    poll at the clamped floor rather than the 0.001s chain-simulator period."""
    config = Config.get_config()
    prev = config.get("AUTO_GENERATE_BLOCKS")
    config.set_option("AUTO_GENERATE_BLOCKS", "false")
    completed = _completed_tx()
    try:
        with patch(
            "mxops.execution.network.MyProxyNetworkProvider"
        ) as mock_proxy_cls, patch(
            "mxops.execution.network.time.sleep"
        ) as mock_sleep:
            proxy = mock_proxy_cls.return_value
            proxy.send_transaction.return_value = bytes.fromhex("ab")
            proxy.get_transaction.return_value = completed

            result = send_and_wait_for_result(MagicMock())

        proxy.generate_blocks_until_tx_completion.assert_not_called()
        # the 0.001s chain-simulator refresh period must be clamped up
        assert mock_sleep.call_args.args[0] == MIN_TX_REFRESH_PERIOD
        assert result is completed
    finally:
        config.set_option("AUTO_GENERATE_BLOCKS", prev)
