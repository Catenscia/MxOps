"""
Unit tests for ChainSimulatorSetTokenBalanceStep and its protobuf/key helpers.
"""

from unittest.mock import call, patch

from multiversx_sdk.core.constants import METACHAIN_ID
import pytest

from mxops import errors
from mxops.config.config import Config
from mxops.enums import NetworkEnum
from mxops.execution.steps import ChainSimulatorSetTokenBalanceStep
from mxops.execution.steps.setup import (
    _build_fungible_esdt_storage_key,
    _encode_fungible_esdt_value,
)


MOCK_BECH32_A = "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
MOCK_BECH32_B = "erd1qqqqqqqqqqqqqpgqxt0y7s830gh5r38ypsslt9hrd2zxn98rv5ys0jd2mg"

USDC = "USDC-c76f1f"
WEGLD = "WEGLD-bd4d79"


@pytest.fixture
def chain_simulator_scenario(scenario_data, chain_simulator_network):
    """Set both Config and ScenarioData to chain simulator network."""
    original = scenario_data.network
    scenario_data.network = NetworkEnum.CHAIN_SIMULATOR
    yield scenario_data
    scenario_data.network = original


# ---- _encode_fungible_esdt_value ----------------------------------------


@pytest.mark.parametrize(
    "amount, expected",
    [
        # protobuf field 2 (tag 0x12) || varint length || 0x00 sign byte || amount
        (1, "12020001"),
        (255, "120200ff"),
        (256, "1203000100"),
        (100_000, "120400" + "0186a0"),
        # 10**18 = 0x0DE0B6B3A7640000 (8 bytes) -- typical EGLD-decimals amount.
        # 1 sign byte + 8 amount bytes = 9 bytes total -> length 0x09.
        (10**18, "120900" + "0de0b6b3a7640000"),
        # Cross-check against a real mainnet WEGLD-bd4d79 holder
        # (xExchange WEGLD/USDC pool, balance 194479365022391160170385).
        (194_479_365_022_391_160_170_385, "120b00292ebf5c5c0731866791"),
    ],
)
def test_encode_fungible_esdt_value_known_amounts(amount, expected):
    assert _encode_fungible_esdt_value(amount) == expected


def test_encode_fungible_esdt_value_rejects_zero():
    with pytest.raises(errors.InvalidSceneDefinition, match="strictly positive"):
        _encode_fungible_esdt_value(0)


def test_encode_fungible_esdt_value_rejects_negative():
    with pytest.raises(errors.InvalidSceneDefinition, match="strictly positive"):
        _encode_fungible_esdt_value(-1)


def test_encode_fungible_esdt_value_rejects_overlarge():
    with pytest.raises(errors.InvalidSceneDefinition, match="too large"):
        _encode_fungible_esdt_value(1 << 1024)


# ---- _build_fungible_esdt_storage_key -----------------------------------


def test_build_storage_key_usdc():
    # 454c524f4e4465736474 == ELRONDesdt
    # 55534443 == "USDC", 2d == "-", 633736663166 == "c76f1f"
    expected = "454c524f4e4465736474" + "55534443" + "2d" + "633736663166"
    assert _build_fungible_esdt_storage_key(USDC) == expected


def test_build_storage_key_wegld():
    expected = "454c524f4e4465736474" + "5745474c44" + "2d" + "626434643739"
    assert _build_fungible_esdt_storage_key(WEGLD) == expected


@pytest.mark.parametrize(
    "bad_identifier",
    [
        "usdc-c76f1f",  # lowercase ticker
        "USDCC76F1F",  # missing dash
        "U-c76f1f",  # ticker too short
        "TOOLONGNAME12-c76f1f",  # ticker too long (12 chars > 10)
        "USDC-C76F1F",  # uppercase random
        "USDC-c76f1g",  # non-hex char
        "USDC-c76f1f-01",  # NFT-style nonce suffix
        "",
    ],
)
def test_build_storage_key_rejects_bad_identifier(bad_identifier):
    with pytest.raises(errors.InvalidSceneDefinition, match="not a valid"):
        _build_fungible_esdt_storage_key(bad_identifier)


# ---- ChainSimulatorSetTokenBalanceStep.execute --------------------------


def _make_step(balances, source_network="mainnet"):
    return ChainSimulatorSetTokenBalanceStep(
        balances=balances, source_network=source_network
    )


def _patched_run(step):
    """Execute the step under all mocks the new step needs.

    Returns the (module, ES, set_state, set_address_state, generate_blocks)
    mocks for assertion. Default _get_esdt_module_clone_data return value
    means "no token needed cloning" so the cheap path is exercised.
    """
    with patch(
        "mxops.execution.steps.setup._get_esdt_module_clone_data",
        return_value=({"address": "esdt-mod", "pairs": {}}, set()),
    ) as mock_module, patch(
        "mxops.execution.steps.setup._insert_tokens_in_elasticsearch"
    ) as mock_es, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_state"
    ) as mock_state, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_address_state"
    ) as mock_addr, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.generate_blocks"
    ) as mock_blocks:
        step.execute()
    return mock_module, mock_es, mock_state, mock_addr, mock_blocks


def test_step_wrong_network(scenario_data):
    """Network is LOCAL by default, step should reject it."""
    step = _make_step(
        [{"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100}]
    )
    with pytest.raises(errors.WrongNetworkForStep):
        step.execute()


def test_step_wrong_network_skips_all_work(scenario_data):
    """The wrong-network gate must run before any source-network or
    chain-simulator work, regardless of how the balances list looks."""
    step = _make_step(
        [{"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100}]
    )
    with patch(
        "mxops.execution.steps.setup._get_esdt_module_clone_data"
    ) as mock_module, patch(
        "mxops.execution.steps.setup._insert_tokens_in_elasticsearch"
    ) as mock_es, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_address_state"
    ) as mock_addr, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_state"
    ) as mock_state, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.generate_blocks"
    ) as mock_blocks:
        with pytest.raises(errors.WrongNetworkForStep):
            step.execute()
    mock_module.assert_not_called()
    mock_es.assert_not_called()
    mock_addr.assert_not_called()
    mock_state.assert_not_called()
    mock_blocks.assert_not_called()


def test_step_empty_balances_rejected(chain_simulator_scenario):
    step = _make_step([])
    with pytest.raises(errors.InvalidSceneDefinition, match="at least one"):
        step.execute()


def test_step_missing_balance_key_rejected(chain_simulator_scenario):
    step = _make_step([{"receiver": MOCK_BECH32_A, "token_identifier": USDC}])
    with pytest.raises(errors.InvalidSceneDefinition, match="missing the required"):
        step.execute()


def test_step_duplicate_token_per_receiver_rejected(chain_simulator_scenario):
    step = _make_step(
        [
            {"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100},
            {"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 200},
        ]
    )
    with pytest.raises(
        errors.InvalidSceneDefinition, match="specified more than once"
    ):
        _patched_run(step)


def test_step_invalid_identifier_rejected(chain_simulator_scenario):
    step = _make_step(
        [
            {
                "receiver": MOCK_BECH32_A,
                "token_identifier": "usdc-c76f1f",
                "amount": 100,
            }
        ]
    )
    with pytest.raises(errors.InvalidSceneDefinition, match="not a valid"):
        _patched_run(step)


def test_step_success_groups_by_receiver(chain_simulator_scenario):
    """Two tokens to A and one to B should produce one set_address_state call
    per unique receiver (with all that receiver's keys merged into a single
    payload), a single ESDT-module reconciliation pass, and exactly one
    generate_blocks(1) call. When _get_esdt_module_clone_data reports nothing
    was newly cloned, ES insertion and module set_state must be skipped."""
    step = _make_step(
        [
            {"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100},
            {"receiver": MOCK_BECH32_A, "token_identifier": WEGLD, "amount": 200},
            {"receiver": MOCK_BECH32_B, "token_identifier": USDC, "amount": 300},
        ]
    )

    mock_module, mock_es, mock_state, mock_addr, mock_blocks = _patched_run(step)

    # ESDT module reconciliation called once with the deduped identifier set.
    assert mock_module.call_count == 1
    called_ids, _, _ = mock_module.call_args.args
    assert called_ids == {USDC, WEGLD}

    # Nothing was newly cloned -> no ES insertion, no module set_state.
    mock_es.assert_not_called()
    mock_state.assert_not_called()

    # set_address_state called once per unique receiver.
    assert mock_addr.call_count == 2
    calls_by_addr = {c.args[0]: c.args[1] for c in mock_addr.call_args_list}
    assert set(calls_by_addr.keys()) == {MOCK_BECH32_A, MOCK_BECH32_B}

    # Receiver A has both keys.
    a_pairs = calls_by_addr[MOCK_BECH32_A]
    assert len(a_pairs) == 2
    usdc_key = _build_fungible_esdt_storage_key(USDC)
    wegld_key = _build_fungible_esdt_storage_key(WEGLD)
    assert a_pairs[usdc_key] == _encode_fungible_esdt_value(100)
    assert a_pairs[wegld_key] == _encode_fungible_esdt_value(200)

    # Receiver B has only the USDC key with its own amount.
    b_pairs = calls_by_addr[MOCK_BECH32_B]
    assert b_pairs == {usdc_key: _encode_fungible_esdt_value(300)}

    # The state must be committed via generate_blocks so proxy reads see it.
    mock_blocks.assert_called_once_with(1)


def test_step_auto_generate_blocks_disabled_waits(chain_simulator_scenario):
    """When AUTO_GENERATE_BLOCKS is off, the simulator produces blocks on its
    own: the step must not force a block and must instead wait for every shard
    (the receivers' user shards and the metachain) to advance, so the set-state
    is committed there before returning. num_shards is 3 in the mocked config."""
    config = Config.get_config()
    prev = config.get("AUTO_GENERATE_BLOCKS")
    config.set_option("AUTO_GENERATE_BLOCKS", "false")
    step = _make_step(
        [{"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100}]
    )
    try:
        with patch(
            "mxops.execution.steps.setup._get_esdt_module_clone_data",
            return_value=({"address": "esdt-mod", "pairs": {}}, set()),
        ), patch(
            "mxops.execution.steps.setup._insert_tokens_in_elasticsearch"
        ), patch(
            "mxops.execution.steps.setup.MyProxyNetworkProvider.set_state"
        ), patch(
            "mxops.execution.steps.setup.MyProxyNetworkProvider.set_address_state"
        ), patch(
            "mxops.execution.steps.setup.MyProxyNetworkProvider.generate_blocks"
        ) as mock_blocks, patch(
            "mxops.execution.steps.setup.utils.wait_for_n_blocks"
        ) as mock_wait:
            step.execute()

        mock_blocks.assert_not_called()
        assert mock_wait.call_args_list == [
            call(0, 1),
            call(1, 1),
            call(2, 1),
            call(METACHAIN_ID, 1),
        ]
    finally:
        config.set_option("AUTO_GENERATE_BLOCKS", prev)


def test_step_pushes_esdt_module_only_for_newly_cloned(chain_simulator_scenario):
    """If _get_esdt_module_clone_data signals that some tokens were cloned
    (newly_cloned non-empty), the step must push the ESDT-module state via
    set_state and call ES insertion only with the newly-cloned set, not
    with already-known identifiers."""
    step = _make_step(
        [
            {"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100},
            {"receiver": MOCK_BECH32_A, "token_identifier": WEGLD, "amount": 200},
        ]
    )

    fake_module_state = {
        "address": "esdt-mod-bech32",
        "pairs": {"identifier-hex": "registration-bytes"},
    }
    with patch(
        "mxops.execution.steps.setup._get_esdt_module_clone_data",
        return_value=(fake_module_state, {USDC}),
    ), patch(
        "mxops.execution.steps.setup._insert_tokens_in_elasticsearch"
    ) as mock_es, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_state"
    ) as mock_state, patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.set_address_state"
    ), patch(
        "mxops.execution.steps.setup.MyProxyNetworkProvider.generate_blocks"
    ):
        step.execute()

    mock_state.assert_called_once_with([fake_module_state])
    assert mock_es.call_count == 1
    es_ids, _, _ = mock_es.call_args.args
    assert es_ids == {USDC}


def test_step_overwrite_existing_balance(chain_simulator_scenario):
    """Calling the step twice for the same (receiver, token) replaces the
    prior amount with the new one — no merge logic, no read-before-write,
    just a fresh set_address_state call with the new encoded value."""
    step1 = _make_step(
        [{"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 100}]
    )
    step2 = _make_step(
        [{"receiver": MOCK_BECH32_A, "token_identifier": USDC, "amount": 9999}]
    )

    *_, mock_addr1, _ = _patched_run(step1)
    *_, mock_addr2, _ = _patched_run(step2)

    usdc_key = _build_fungible_esdt_storage_key(USDC)
    assert mock_addr1.call_args_list[0].args == (
        MOCK_BECH32_A,
        {usdc_key: _encode_fungible_esdt_value(100)},
    )
    assert mock_addr2.call_args_list[0].args == (
        MOCK_BECH32_A,
        {usdc_key: _encode_fungible_esdt_value(9999)},
    )
    # No accidental merging: encoded payload for 100 != encoded payload for 9999.
    assert _encode_fungible_esdt_value(100) != _encode_fungible_esdt_value(9999)
