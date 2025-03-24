"""
author: Etienne Wallet

This subpackage contains all the smart values that can be used with MxOps
"""

from mxops.smart_values.base import SmartValue
from mxops.smart_values.custom import (
    SmartOnChainTokenTransfer,
    SmartOnChainTokenTransfers,
    SmartResultsSaveKeys,
)
from mxops.smart_values.mx_sdk import (
    SmartAddress,
    SmartAddresses,
    SmartBech32,
    SmartToken,
    SmartTokenTransfer,
    SmartTokenTransfers,
)
from mxops.smart_values.native import (
    SmartBytes,
    SmartInt,
    SmartFloat,
    SmartBool,
    SmartStr,
    SmartDict,
    SmartList,
    SmartPath,
)

__all__ = [
    "SmartAddress",
    "SmartAddresses",
    "SmartBech32",
    "SmartBool",
    "SmartBytes",
    "SmartDict",
    "SmartFloat",
    "SmartInt",
    "SmartList",
    "SmartOnChainTokenTransfer",
    "SmartOnChainTokenTransfers",
    "SmartPath",
    "SmartResultsSaveKeys",
    "SmartStr",
    "SmartToken",
    "SmartTokenTransfer",
    "SmartTokenTransfers",
    "SmartValue",
]
