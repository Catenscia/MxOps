from pathlib import Path
from typing import Any, Union

from multiversx_sdk import Address, Token, TokenTransfer
import pytest

from mxops import errors
from mxops.data.execution_data import ScenarioData
from mxops.execution.msc import OnChainTokenTransfer
from mxops.smart_values import (
    SmartAddress,
    SmartBech32,
    SmartBool,
    SmartFloat,
    SmartInt,
    SmartPath,
    SmartStr,
    SmartToken,
    SmartTokenTransfer,
    SmartTokenTransfers,
    SmartValue,
)
from mxops.smart_values.custom import SmartOnChainTokenTransfers
from mxops.smart_values.factory import extract_first_smart_value_class


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        ("abcdef", "abcdef", "abcdef"),
        (
            12241412,
            12241412,
            "12241412",
        ),
        (
            "%{${OWNER_NAME}_%{suffix}.identifier}",
            "BOBT-123456",
            (
                "BOBT-123456 (%{${OWNER_NAME}_%{suffix}.identifier} "
                "-> %{${OWNER_NAME}_token.identifier} -> %{bob_token.identifier})"
            ),
        ),
        (
            "bytes:AQIECA==",
            b"\x01\x02\x04\x08",
            "b'\\x01\\x02\\x04\\x08' (bytes:AQIECA==)",
        ),
        ("=123456", 123456, "123456 (=123456)"),
        ("={123456}", 123456, "123456 (={123456})"),
        ("={'123456'}", "123456", "123456 (={'123456'})"),
        ("={(1+2+3) * 10}", 60, "60 (={(1+2+3) * 10})"),
        (
            "={int(%{my_dict.key1}) // %{my_dict.key2}}",
            0,
            (
                "0 (={int(%{my_dict.key1}) // %{my_dict.key2}} "
                "-> ={int(%{my_dict.key1}) // 2} "
                "-> ={int(1) // 2})"
            ),
        ),
        (
            "={int(%{my_dict.key1}) * 7.0 / %{my_dict.key2}}",
            3.5,
            (
                "3.5 (={int(%{my_dict.key1}) * 7.0 / %{my_dict.key2}} "
                "-> ={int(%{my_dict.key1}) * 7.0 / 2} "
                "-> ={int(1) * 7.0 / 2})"
            ),
        ),
        (r"={42 \% 5}", 2, "2 (={42 % 5})"),
        (r"={42 % 5}", 2, "2 (={42 % 5})"),
        (r"={dict(a\=156)}", {"a": 156}, "{'a': 156} (={dict(a=156)})"),
        (r"={dict(a=156)}", {"a": 156}, "{'a': 156} (={dict(a=156)})"),
        (r"={\{'a': 156\}}", {"a": 156}, "{'a': 156} (={{'a': 156}})"),
        (r"={{'a': 156}}", {"a": 156}, "{'a': 156} (={{'a': 156}})"),
        (
            "%alice.address",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3 (%alice.address)",  # noqa
        ),
        (
            "%alice.bech32",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3 (%alice.bech32)",  # noqa
        ),
        ("=10**18", 10**18, "1000000000000000000 (=10**18)"),
        ("=10**6*10**3", 10**9, "1000000000 (=10**6*10**3)"),
        ("=10**6 * 10**3", 10**9, "1000000000 (=10**6 * 10**3)"),
        ("=10**(6+3)", 10**9, "1000000000 (=10**(6+3))"),
    ],
)
def test_smart_value(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartValue(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


def test_deeply_nested_smart_value():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value(
        "deep_nested_list",
        ["%my_list", ["%my_dict", "%my_test_contract.query_result_1"]],
    )
    scenario_data.set_value("list_name", "deep_nested_list")
    smart_value = SmartValue("%{%{list_name}}")

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == [
        ["item1", "item2", "item3", {"item4-key1": "e"}],
        [{"key1": "1", "key2": 2, "key3": ["x", "y", "z"]}, [0, 1, {2: "abc"}]],
    ]
    assert smart_value.get_evaluation_string() == (
        "["
        "['item1', 'item2', 'item3', {'item4-key1': 'e'}], "
        "[{'key1': '1', 'key2': 2, 'key3': ['x', 'y', 'z']}, "
        "[0, 1, {2: 'abc'}]]] "
        "(%{%{list_name}} -> %{deep_nested_list} -> "
        "['%my_list', ['%my_dict', '%my_test_contract.query_result_1']])"
    )


def test_infinite_evaluation():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("inf_a", "%inf_b")
    scenario_data.set_value("inf_b", "%inf_a")
    smart_value = SmartValue("%inf_a")

    # When
    with pytest.raises(errors.MaxIterationError):
        smart_value.evaluate()


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            12241412,
            12241412,
            "12241412",
        ),
        (
            "12241412",
            12241412,
            "12241412",
        ),
        (
            3.1415,
            3,
            "3 (3.1415)",
        ),
    ],
)
def test_smart_int(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartInt(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            12241412.23,
            12241412.23,
            "12241412.23",
        ),
        (
            "12241412.23",
            12241412.23,
            "12241412.23",
        ),
        (
            3,
            3,
            "3.0 (3)",
        ),
    ],
)
def test_smart_float(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartFloat(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            True,
            True,
            "True",
        ),
        (
            1,
            True,
            "True (1)",
        ),
        (
            None,
            False,
            "False (None)",
        ),
    ],
)
def test_smart_bool(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartBool(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() is expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            True,
            "True",
            "True",
        ),
        (
            1,
            "1",
            "1",
        ),
        (
            "%user",
            "alice",
            "alice (%user)",
        ),
    ],
)
def test_smart_str(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartStr(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            "my_test_contract",
            Address.from_bech32(
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
            ),
            (
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t "
                "(my_test_contract)"
            ),
        ),
        (
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            Address.from_bech32(
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
            ),
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
        ),
        (
            "%user",
            Address.from_bech32(
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
            ),
            (
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3 "
                "(%user -> alice)"
            ),
        ),
    ],
)
def test_smart_address(raw_value: Any, expected_result: Address, expected_str: str):
    # Given
    smart_value = SmartAddress(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            "my_test_contract",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            (
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t "
                "(my_test_contract)"
            ),
        ),
        (
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
        ),
        (
            "%user",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
            (
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3 "
                "(%user -> alice)"
            ),
        ),
    ],
)
def test_smart_bech32(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartBech32(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            ["WEGLD-abcdef", 123456],
            TokenTransfer(Token("WEGLD-abcdef"), 123456),
            ("123456 WEGLD-abcdef (['WEGLD-abcdef', 123456])"),
        ),
        (
            ["WEGLD-abcdef", 123456, 5],
            TokenTransfer(Token("WEGLD-abcdef", 5), 123456),
            ("123456 WEGLD-abcdef-05 (['WEGLD-abcdef', 123456, 5])"),
        ),
        (
            {"identifier": "WEGLD-abcdef", "amount": 123456},
            TokenTransfer(Token("WEGLD-abcdef"), 123456),
            ("123456 WEGLD-abcdef ({'identifier': 'WEGLD-abcdef', 'amount': 123456})"),
        ),
        (
            {"identifier": "WEGLD-abcdef", "amount": 123456, "nonce": 5},
            TokenTransfer(Token("WEGLD-abcdef", 5), 123456),
            (
                "123456 WEGLD-abcdef-05 ({'identifier': 'WEGLD-abcdef', "
                "'amount': 123456, 'nonce': 5})"
            ),
        ),
        (
            {"token_identifier": "WEGLD-abcdef", "amount": 123456, "token_nonce": 5},
            TokenTransfer(Token("WEGLD-abcdef", 5), 123456),
            (
                "123456 WEGLD-abcdef-05 ({'token_identifier': 'WEGLD-abcdef', "
                "'amount': 123456, 'token_nonce': 5})"
            ),
        ),
    ],
)
def test_smart_token_transfer(
    raw_value: Any, expected_result: TokenTransfer, expected_str: str
):
    # Given
    smart_value = SmartTokenTransfer(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    evaluated_transfer = smart_value.get_evaluated_value()
    assert evaluated_transfer == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            [
                ["WEGLD-abcdef", 123456],
                {"identifier": "WEGLD-ghijkl", "amount": 789, "nonce": 8},
            ],
            [
                TokenTransfer(Token("WEGLD-abcdef"), 123456),
                TokenTransfer(Token("WEGLD-ghijkl", 8), 789),
            ],
            (
                "['123456 WEGLD-abcdef', '789 WEGLD-ghijkl-08'] ([['WEGLD-abcdef', "
                "123456], {'identifier': 'WEGLD-ghijkl', 'amount': 789, 'nonce': 8}])"
            ),
        ),
    ],
)
def test_smart_token_transfers(
    raw_value: Any, expected_result: list[TokenTransfer], expected_str: str
):
    # Given
    smart_value = SmartTokenTransfers(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    evaluated_transfers = smart_value.get_evaluated_value()
    assert len(evaluated_transfers) == 2
    assert evaluated_transfers == expected_result

    assert smart_value.get_evaluation_string() == expected_str


def test_randint():
    # Given
    smart_value = SmartValue("=randint(2, 12)")

    # When
    smart_value.evaluate()

    # Then
    assert isinstance(smart_value.get_evaluated_value(), int)
    assert 2 <= smart_value.get_evaluated_value() < 12


def test_rand():
    # Given
    smart_value = SmartValue("=rand()")

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert isinstance(smart_value.get_evaluated_value(), float)
    assert 0 <= smart_value.get_evaluated_value() <= 1


def test_randchoice():
    # Given
    smart_value = SmartValue("=choice([1, 2, 3, 4])")

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() in [1, 2, 3, 4]


def test_randchoice_nested():
    # Given
    scenario_data = ScenarioData.get()
    smart_value = SmartValue("={choice(%{my_list})}")

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() in scenario_data.get_value("my_list")


def test_smart_path():
    # Given
    smart_value = SmartPath("./tests")

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == Path("./tests")


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            ["WEGLD-abcdef"],
            Token("WEGLD-abcdef"),
            "WEGLD-abcdef (['WEGLD-abcdef'])",
        ),
        (
            ["NFT-abcdef", 5],
            Token("NFT-abcdef", 5),
            "NFT-abcdef-05 (['NFT-abcdef', 5])",
        ),
        (
            {"identifier": "WEGLD-abcdef"},
            Token("WEGLD-abcdef"),
            "WEGLD-abcdef ({'identifier': 'WEGLD-abcdef'})",
        ),
        (
            {"identifier": "NFT-abcdef", "nonce": 5},
            Token("NFT-abcdef", 5),
            "NFT-abcdef-05 ({'identifier': 'NFT-abcdef', 'nonce': 5})",
        ),
        (
            {"token_identifier": "NFT-abcdef", "token_nonce": 5},
            Token("NFT-abcdef", 5),
            "NFT-abcdef-05 ({'token_identifier': 'NFT-abcdef', 'token_nonce': 5})",
        ),
    ],
)
def test_smart_token(raw_value: Any, expected_result: Token, expected_str: str):
    # Given
    smart_value = SmartToken(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    evaluated_token = smart_value.get_evaluated_value()
    assert evaluated_token.identifier == expected_result.identifier
    assert evaluated_token.nonce == expected_result.nonce
    assert smart_value.get_evaluation_string() == expected_str


def test_smart_on_chain_transfers():
    # Given
    raw_value = [
        {
            "sender": "my_test_contract",
            "receiver": "alice",
            "token_identifier": "WEGLD-bd4d79",
            "amount": 1000000000000000000,
        }
    ]

    # When
    smart_value = SmartOnChainTokenTransfers(raw_value)
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    evaluated_transfers = smart_value.get_evaluated_value()
    assert Address.new_from_bech32(
        "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
    ) == Address.new_from_bech32(
        "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
    )
    assert evaluated_transfers == [
        OnChainTokenTransfer(
            sender=Address.new_from_bech32(
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
            ),
            receiver=Address.new_from_bech32(
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
            ),
            token=Token("WEGLD-bd4d79"),
            amount=1000000000000000000,
        )
    ]


@pytest.mark.parametrize(
    "input_value, expected_result",
    [
        (SmartInt, SmartInt),
        ("SmartValue", SmartValue),
        (SmartPath | str, SmartPath),
        (Union[SmartPath, str], SmartPath),
        (str, None),
        (SmartBech32 | None, SmartBech32),
        ("SmartFloat | None", SmartFloat),
        (int | None, None),
    ],
)
def test_extract_first_smart_value_class(input_value: Any, expected_result: Any):
    # Given
    # When
    extracted_type = extract_first_smart_value_class(input_value)

    # Then
    if expected_result is None:
        assert extracted_type is None
    else:
        assert extracted_type == expected_result


def test_all_extraction():
    # Given
    names = [
        "SmartAddress",
        "SmartBech32",
        "SmartBool",
        "SmartCheck",
        "SmartChecks",
        "SmartDict",
        "SmartFloat",
        "SmartInt",
        "SmartList",
        "SmartOnChainTokenTransfer",
        "SmartOnChainTokenTransfers",
        "SmartPath",
        "SmartResultsSaveKeys",
        "SmartStep",
        "SmartSteps",
        "SmartStr",
        "SmartToken",
        "SmartTokenTransfer",
        "SmartTokenTransfers",
        "SmartValue",
    ]
    # When
    for name in names:
        extracted_type = extract_first_smart_value_class(name)
        assert issubclass(extracted_type, SmartValue)


def test_randomness():
    # Given
    value_a = SmartValue("=randint(0,10**18)")
    value_b = SmartValue("=randint(0,10**18)")

    # When
    value_a.evaluate()
    value_b.evaluate()

    # Then
    assert value_a.get_evaluated_value() != value_b.get_evaluated_value()
