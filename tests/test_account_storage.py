from multiversx_sdk import AccountStorageEntry, Token
import pytest
from mxops.utils.account_storage import (
    extract_token_from_entry,
    separate_esdt_related_storage,
)


@pytest.mark.parametrize(
    "entry,expected_result",
    [
        (
            AccountStorageEntry(
                raw={"454c524f4e44657364744d544b2d333132303263": "1204000186a0"},
                key="ELRONDesdtMTK-31202c",
                value=b"\x12\x04\x00\x01\x86\xa0",
                block_coordinates=None,
            ),
            Token("MTK-31202c"),
        ),
        (
            AccountStorageEntry(
                raw={"454c524f4e44657364744d544b2d393466366430": "12040001b207"},
                key="ELRONDesdtMTK-94f6d0",
                value=b"\x12\x04\x00\x01\xb2\x07",
                block_coordinates=None,
            ),
            Token("MTK-94f6d0"),
        ),
        (
            AccountStorageEntry(
                raw={
                    "454c524f4e446573647442494458424f544556542d66663139303301": "080312020001"  # noqa
                },
                key="ELRONDesdtBIDXBOTEVT-ff1903\x01",
                value=b"\x08\x03\x12\x02\x00\x01",
                block_coordinates=None,
            ),
            Token("BIDXBOTEVT-ff1903", 1),
        ),
        (
            AccountStorageEntry(
                raw={
                    "454c524f4e44657364744753504143454150452d3038626332622acd": "080112020001"  # noqa
                },
                key="ELRONDesdtGSPACEAPE-08bc2b*",
                value=b"\x08\x01\x12\x02\x00\x01",
                block_coordinates=None,
            ),
            Token("GSPACEAPE-08bc2b", 10957),
        ),
    ],
)
def test_token_extract(entry: AccountStorageEntry, expected_result: Token | None):
    # Given
    # When
    result = extract_token_from_entry(entry)
    # Assert
    assert result == expected_result


def test_split_entries():
    # Given
    entries = [
        AccountStorageEntry(
            raw={
                "454c524f4e446573647445474c444d4558462d3562636335370b63a1": "08011209000103f4b75f8828ea226308a1c72d1a200000000000000000050026751893d6789be9e5a99863ba9eeaa8088dd25f548332003a390000000803efbeedecc14f6d00000000000001de00000000000001de02010000000781fa5bafc4147500000000000000080103f4b75f8828ea"  # noqa
            },
            key="ELRONDesdtEGLDMEXF-5bcc57\x0bc",
            value=b'\x08\x01\x12\t\x00\x01\x03\xf4\xb7_\x88(\xea"c\x08\xa1\xc7-\x1a \x00\x00\x00\x00\x00\x00\x00\x00\x05\x00&u\x18\x93\xd6x\x9b\xe9\xe5\xa9\x98c\xba\x9e\xea\xa8\x08\x8d\xd2_T\x832\x00:9\x00\x00\x00\x08\x03\xef\xbe\xed\xec\xc1Om\x00\x00\x00\x00\x00\x00\x01\xde\x00\x00\x00\x00\x00\x00\x01\xde\x02\x01\x00\x00\x00\x07\x81\xfa[\xaf\xc4\x14u\x00\x00\x00\x00\x00\x00\x00\x08\x01\x03\xf4\xb7_\x88(\xea',  # noqa
            block_coordinates=None,
        ),
        AccountStorageEntry(
            raw={
                "454c524f4e44657364744c4b4d45582d6161623931301e57": "0801120b001fc3adcdf60b67ec0000226408d73c1a20000000000000000005009056f001101b6e1518044064b48c2e4fb492cd88548332003a3b00000006000000000000033a1100000000000003581100000000000003761100000000000003941100000000000003b21000000000000003d01000"  # noqa
            },
            key="ELRONDesdtLKMEX-aab910\x1eW",
            value=b'\x08\x01\x12\x0b\x00\x1f\xc3\xad\xcd\xf6\x0bg\xec\x00\x00"d\x08\xd7<\x1a \x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x90V\xf0\x01\x10\x1bn\x15\x18\x04@d\xb4\x8c.O\xb4\x92\xcd\x88T\x832\x00:;\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x03:\x11\x00\x00\x00\x00\x00\x00\x03X\x11\x00\x00\x00\x00\x00\x00\x03v\x11\x00\x00\x00\x00\x00\x00\x03\x94\x11\x00\x00\x00\x00\x00\x00\x03\xb2\x10\x00\x00\x00\x00\x00\x00\x03\xd0\x10\x00',  # noqa
            block_coordinates=None,
        ),
        AccountStorageEntry(
            raw={
                "454c524f4e44726f6c65657364745745474c442d626434643739": "0a1145534454526f6c654c6f63616c4d696e740a1145534454526f6c654c6f63616c4275726e"  # noqa
            },
            key="ELRONDroleesdtWEGLD-bd4d79",
            value=b"\n\x11ESDTRoleLocalMint\n\x11ESDTRoleLocalBurn",
            block_coordinates=None,
        ),
        AccountStorageEntry(
            raw={"7772617070656445676c64546f6b656e4964": "5745474c442d626434643739"},
            key="wrappedEgldTokenId",
            value=b"WEGLD-bd4d79",
            block_coordinates=None,
        ),
    ]
    # When
    esdt_entries, other_entries = separate_esdt_related_storage(entries)

    # Then
    assert len(esdt_entries) == 3
    assert len(other_entries) == 1
    assert len(esdt_entries["WEGLD-bd4d79"]) == 1
    assert len(esdt_entries["EGLDMEXF-5bcc57"]) == 1
    assert (
        esdt_entries["WEGLD-bd4d79"][0].value
        == b"\n\x11ESDTRoleLocalMint\n\x11ESDTRoleLocalBurn"
    )
