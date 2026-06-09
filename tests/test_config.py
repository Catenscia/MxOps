"""
author: Etienne Wallet

Tests for the config loading, in particular the merge of a custom config file
on top of the packaged defaults.
"""

import os
from pathlib import Path
from unittest import mock

import pytest

from mxops.config.config import Config, _Config
from mxops.enums import NetworkEnum

PARTIAL_CONFIG_PATH = Path(__file__).parent / "data" / "configs" / "partial_config.ini"


def test_custom_config_overrides_default_option():
    """
    A value defined in the custom config overrides the packaged default
    """
    config = _Config(NetworkEnum.DEV, PARTIAL_CONFIG_PATH)
    assert config.get("PROXY") == "https://my-custom-devnet-gateway.example.com"


def test_custom_config_inherits_untouched_option():
    """
    An option not specified in the custom config falls back to the default
    of the same section
    """
    config = _Config(NetworkEnum.DEV, PARTIAL_CONFIG_PATH)
    assert config.get("API") == "https://devnet-api.multiversx.com"


def test_custom_config_keeps_untouched_section():
    """
    A section absent from the custom config is still served from the defaults
    (regression: this previously raised NoSectionError)
    """
    config = _Config(NetworkEnum.DEV, PARTIAL_CONFIG_PATH)
    assert config.get("PROXY", network=NetworkEnum.MAIN) == (
        "https://gateway.multiversx.com"
    )


def test_default_config_without_custom_path():
    """
    Without a custom config path, the packaged defaults are resolved
    """
    config = _Config(NetworkEnum.LOCAL, None)
    assert config.get("PROXY") == "http://localhost:7950"


def test_custom_config_inherits_default_section_option():
    """
    An option defined in the [DEFAULT] section of the packaged config is still
    inherited after merging a custom config
    """
    config = _Config(NetworkEnum.DEV, PARTIAL_CONFIG_PATH)
    assert config.get("TX_TIMEOUT") == "100"


def test_custom_config_can_override_default_section_option(tmp_path):
    """
    A custom config can override an option that lives in the [DEFAULT] section
    """
    cfg = tmp_path / "custom_config.ini"
    cfg.write_text("[DEFAULT]\nTX_TIMEOUT=42\n")
    config = _Config(NetworkEnum.DEV, cfg)
    assert config.get("TX_TIMEOUT") == "42"


def test_custom_config_can_add_new_option(tmp_path):
    """
    A custom config can add an option that does not exist in the defaults
    """
    cfg = tmp_path / "custom_config.ini"
    cfg.write_text("[DEV]\nCUSTOM_KEY=hello\n")
    config = _Config(NetworkEnum.DEV, cfg)
    assert config.get("CUSTOM_KEY") == "hello"


def test_find_config_path_from_env_returns_path(tmp_path):
    """
    When MXOPS_CONFIG points to an existing file, find_config_path returns it as
    a Path (regression: it previously returned a str, breaking _Config)
    """
    cfg = tmp_path / "mxops_config.ini"
    cfg.write_text("[DEV]\nPROXY=http://envtest:9999\n")
    with mock.patch.dict(os.environ, {"MXOPS_CONFIG": str(cfg)}):
        result = Config.find_config_path()
    assert isinstance(result, Path)
    assert result == Path(str(cfg))


def test_find_config_path_from_env_missing_raises():
    """
    When MXOPS_CONFIG points to a missing file, find_config_path raises
    """
    with mock.patch.dict(os.environ, {"MXOPS_CONFIG": "/no/such/file.ini"}):
        with pytest.raises(ValueError):
            Config.find_config_path()


def test_get_config_with_custom_config_does_not_recurse(tmp_path):
    """
    Building the singleton through Config.get_config() while MXOPS_CONFIG points to
    a custom config must not recurse. Resolving the data path triggers
    get_config() again, so any config resolution performed while _Config is still
    being constructed (e.g. logger setup) would re-enter the half-built singleton
    indefinitely.
    """
    cfg = tmp_path / "mxops_config.ini"
    cfg.write_text("[DEFAULT]\nDATA_PATH=./deployment/data\n")
    # pylint: disable=protected-access
    saved_instance = Config._Config__instance
    Config._Config__instance = None
    try:
        with mock.patch.dict(os.environ, {"MXOPS_CONFIG": str(cfg)}):
            config = Config.get_config()
        assert config.get("DATA_PATH") == "./deployment/data"
    finally:
        Config._Config__instance = saved_instance
