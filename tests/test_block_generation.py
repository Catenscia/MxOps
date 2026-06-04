"""
Unit tests for should_generate_blocks, the helper that decides whether MxOps
should manually drive block production on the chain simulator.
"""

from configparser import NoOptionError

import pytest
import pytest_mock

from mxops import errors
from mxops.common.providers import should_generate_blocks
from mxops.config.config import Config


def test_should_generate_blocks_false_on_other_networks():
    """Default test network is LOCAL: MxOps never generates blocks."""
    assert should_generate_blocks() is False


def test_should_generate_blocks_true_on_chain_simulator_by_default(
    chain_simulator_network,
):
    """Chain simulator with the default config keeps today's behavior."""
    assert should_generate_blocks() is True


def test_should_generate_blocks_false_when_disabled(chain_simulator_network):
    """AUTO_GENERATE_BLOCKS=false means the simulator auto-produces blocks."""
    config = Config.get_config()
    prev = config.get("AUTO_GENERATE_BLOCKS")
    config.set_option("AUTO_GENERATE_BLOCKS", "false")
    try:
        assert should_generate_blocks() is False
    finally:
        config.set_option("AUTO_GENERATE_BLOCKS", prev)


def test_should_generate_blocks_rejects_invalid_value(chain_simulator_network):
    """A malformed value must raise rather than silently disabling blocks."""
    config = Config.get_config()
    prev = config.get("AUTO_GENERATE_BLOCKS")
    config.set_option("AUTO_GENERATE_BLOCKS", "ture")  # typo
    try:
        with pytest.raises(errors.InvalidConfigValue, match="AUTO_GENERATE_BLOCKS"):
            should_generate_blocks()
    finally:
        config.set_option("AUTO_GENERATE_BLOCKS", prev)


def test_should_generate_blocks_defaults_true_when_option_missing(
    chain_simulator_network, mocker: pytest_mock.MockerFixture
):
    """A user config without the option must keep working (defaults to True)."""
    config = Config.get_config()
    mocker.patch.object(
        config,
        "get",
        side_effect=NoOptionError("AUTO_GENERATE_BLOCKS", "CHAIN_SIMULATOR"),
    )
    assert should_generate_blocks() is True
