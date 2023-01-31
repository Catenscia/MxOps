import json
from pathlib import Path

from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.execution.msc import OnChainTransfer
from mxops.execution.network import get_on_chain_transfers


def test_add_liquidity(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'add_liquidity.json') as file:
        tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    transfers = get_on_chain_transfers(tx)

    # Then
    expected_result = [
        OnChainTransfer(
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'WEGLD-bd4d79',
            '2662383390769244262'),
        OnChainTransfer(
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'RIDE-7d18e9',
            '1931527217545745197301'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'EGLDRIDE-7bd51a',
            '1224365948567992620'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'RIDE-7d18e9',
            '37'),
    ]

    assert transfers == expected_result


def test_claim(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'claim.json') as file:
        tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    transfers = get_on_chain_transfers(tx)

    # Then
    expected_result = [
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7',
            'erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch',
            'EGLD',
            '32138287366664708')
    ]
    for tr in transfers:
        print(tr)

    assert transfers == expected_result


def test_exit_farm(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'exit_farm.json') as file:
        tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    transfers = get_on_chain_transfers(tx)

    # Then
    expected_result = [
        OnChainTransfer(
            'erd155kylmjd5qman3dknh0mch0cj65d73yck952h6yc8jesv5lzjjmqjg7yt0',
            'erd1qqqqqqqqqqqqqpgq6v5ta4memvrhjs4x3gqn90c3pujc77takp2sqhxm9j',
            'ASHWEGLDFL-9612cf-3aee',
            '4030067946664876184'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgq6v5ta4memvrhjs4x3gqn90c3pujc77takp2sqhxm9j',
            'erd155kylmjd5qman3dknh0mch0cj65d73yck952h6yc8jesv5lzjjmqjg7yt0',
            'ASHWEGLD-38545c',
            '2015000000000000000'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgq6v5ta4memvrhjs4x3gqn90c3pujc77takp2sqhxm9j',
            'erd155kylmjd5qman3dknh0mch0cj65d73yck952h6yc8jesv5lzjjmqjg7yt0',
            'ASHWEGLDFL-9612cf-3aee',
            '2015067946664876184'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgq6v5ta4memvrhjs4x3gqn90c3pujc77takp2sqhxm9j',
            'erd155kylmjd5qman3dknh0mch0cj65d73yck952h6yc8jesv5lzjjmqjg7yt0',
            'XMEX-fda355-2f',
            '7995358737478580000')
    ]

    assert transfers == expected_result


def test_nft_transfer(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'nft_transfer.json') as file:
        tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    transfers = get_on_chain_transfers(tx)

    # Then
    expected_result = [
        OnChainTransfer(
            'erd1w9njtx572ppvuz0elgs9kfvnvzt930ea0ukqftkqltg2ap5acvmsrw83ls',
            'erd12j4gqamtx6su92elpxwe2l5pjt5ae09h87tyf95waly3z8cejuwqcwkzd2',
            'GIANTS-93cadd-247e',
            '1')
    ]
    assert transfers == expected_result


def test_swap(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'swap.json') as file:
        tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    transfers = get_on_chain_transfers(tx)

    # Then
    expected_result = [
        OnChainTransfer(
            'erd13vafnpmmtuq76ecq2ay4lma6ep9mcg9pwayde6ckqywrjsy68phqm0y2g2',
            'erd1qqqqqqqqqqqqqpgqp32ecg03fyxgt2pf2fsxyg4knvhfvtgz2jps6rx6gf',
            'BHAT-c1fde3',
            '1693877000000000000000'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgqp32ecg03fyxgt2pf2fsxyg4knvhfvtgz2jps6rx6gf',
            'erd1qqqqqqqqqqqqqpgqjsnxqprks7qxfwkcg2m2v9hxkrchgm9akp2segrswt',
            'BHAT-c1fde3',
            '846938500000000000'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgqp32ecg03fyxgt2pf2fsxyg4knvhfvtgz2jps6rx6gf',
            'erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2',
            'WEGLD-bd4d79',
            '9346448536282620'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgqp32ecg03fyxgt2pf2fsxyg4knvhfvtgz2jps6rx6gf',
            'erd13vafnpmmtuq76ecq2ay4lma6ep9mcg9pwayde6ckqywrjsy68phqm0y2g2',
            'WEGLD-bd4d79',
            '1864267714109103556'),

    ]
    assert transfers == expected_result


def test_token_unlock(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'token_unlock.json') as file:
        tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    transfers = get_on_chain_transfers(tx)

    # Then
    expected_result = [
        OnChainTransfer(
            'erd1hfyadkpxtfxj6xqu5dvm7fhlav3q0qvxtljd3pzpeq0f6pq8mqgqcm4p65',
            'erd1qqqqqqqqqqqqqpgqawujux7w60sjhm8xdx3n0ed8v9h7kpqu2jpsecw6ek',
            'LKASH-10bd00-01',
            '4004547342103966875339'),
        OnChainTransfer(
            'erd1qqqqqqqqqqqqqpgqp32ecg03fyxgt2pf2fsxyg4knvhfvtgz2jps6rx6gf',
            'erd1qqqqqqqqqqqqqpgqjsnxqprks7qxfwkcg2m2v9hxkrchgm9akp2segrswt',
            'ASH-a642d1',
            '4004547342103966875339')

    ]
    assert transfers == expected_result
