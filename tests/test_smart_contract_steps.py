from mxops.execution.steps import (
    ContractCallStep,
    ContractDeployStep,
    ContractUpgradeStep,
)


def test_deploy_step():
    # Given
    step = ContractDeployStep(
        sender="alice",
        contract_id="empty-sc",
        gas_limit=100000000,
        abi_path="./tests/data/contracts/emptysc.abi.json",
        wasm_path="./tests/data/contracts/emptysc.wasm",
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq6gq4hu"
    )
    assert tx.data == (
        b"0061736d01000000010d036000006000017f60027f7f00023e0303656e760f6765744e756d41"
        b"7267756d656e7473000103656e760b7369676e616c4572726f72000203656e760e636865636b"
        b"4e6f5061796d656e74000003030200000503010003060f027f00419980080b7f0041a080080b"
        b"074106066d656d6f7279020004696e697400030863616c6c4261636b00040775706772616465"
        b"00030a5f5f646174615f656e6403000b5f5f686561705f6261736503010a1802120010021000"
        b"04404180800841191001000b0b0300010b0b210100418080080b1977726f6e67206e756d6265"
        b"72206f6620617267756d656e7473@0500@0500"
    )


def test_upgrade_step():
    # Given
    step = ContractUpgradeStep(
        sender="alice",
        contract="erd1qqqqqqqqqqqqqpgqq75vtleur5rg74nk4f88ql6a7ajas073l3tsc5ljc9",
        gas_limit=100000000,
        abi_path="./tests/data/contracts/emptysc.abi.json",
        wasm_path="./tests/data/contracts/emptysc.wasm",
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd1qqqqqqqqqqqqqpgqq75vtleur5rg74nk4f88ql6a7ajas073l3tsc5ljc9"
    )
    assert tx.data == (
        b"upgradeContract@0061736d01000000010d036000006000017f60027f7f00023e0303656e76"
        b"0f6765744e756d417267756d656e7473000103656e760b7369676e616c4572726f7200020365"
        b"6e760e636865636b4e6f5061796d656e74000003030200000503010003060f027f0041998008"
        b"0b7f0041a080080b074106066d656d6f7279020004696e697400030863616c6c4261636b0004"
        b"077570677261646500030a5f5f646174615f656e6403000b5f5f686561705f6261736503010a"
        b"180212001002100004404180800841191001000b0b0300010b0b210100418080080b1977726f"
        b"6e67206e756d626572206f6620617267756d656e7473@0500"
    )


def test_call_step():
    # Given
    step = ContractCallStep(
        sender="alice",
        contract="piggy-bank",
        endpoint="deposit",
        gas_limit=100000,
        esdt_transfers=[["MYESDT-abcdef", 123456]],
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd1qqqqqqqqqqqqqpgqxt0y7s830gh5r38ypsslt9hrd2zxn98rv5ys0jd2mg"
    )
    assert tx.data == b"ESDTTransfer@4d59455344542d616263646566@01e240@6465706f736974"
