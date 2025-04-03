"""
author: Etienne Wallet

This module contains native python smart values (int, float, ...)
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import dateparser

from mxops import errors
from mxops.smart_values.base import SmartValue


@dataclass
class SmartInt(SmartValue):
    """
    Represent a smart value that should result in an int
    """

    @staticmethod
    def type_enforce_value(value: Any) -> int:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: int
        """
        return int(value)

    def get_evaluated_value(self) -> int:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: int
        """
        return super().get_evaluated_value()


@dataclass
class SmartFloat(SmartValue):
    """
    Represent a smart value that should result in a float
    """

    @staticmethod
    def type_enforce_value(value: Any) -> int:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: float
        """
        return float(value)

    def get_evaluated_value(self) -> float:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: float
        """
        return super().get_evaluated_value()


@dataclass
class SmartBool(SmartValue):
    """
    Represent a smart value that should result in a boolean
    """

    @staticmethod
    def type_enforce_value(value: Any) -> bool:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: bool
        """
        return bool(value)

    def get_evaluated_value(self) -> bool:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: int
        """
        return super().get_evaluated_value()


@dataclass
class SmartStr(SmartValue):
    """
    Represent a smart value that should result in a string
    """

    @staticmethod
    def type_enforce_value(value: Any) -> str:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: str
        """
        return str(value)

    def get_evaluated_value(self) -> str:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: str
        """
        return super().get_evaluated_value()


@dataclass
class SmartDict(SmartValue):
    """
    Represent a smart value that should result in a dict
    """

    @staticmethod
    def type_enforce_value(value: Any) -> dict:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: dict
        """
        return dict(value)

    def get_evaluated_value(self) -> dict:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: dict
        """
        return super().get_evaluated_value()


@dataclass
class SmartRawDict(SmartValue):
    """
    Represent a smart value that should result in a dict without evaluating
    the smart values that may be present in the dict
    """

    @staticmethod
    def type_enforce_value(value: Any) -> dict:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: dict
        """
        return dict(value)

    def get_evaluated_value(self) -> dict:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: dict
        """
        return super().get_evaluated_value()

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until a
        dict is reached. The evaluation of the element of the dict is a
        responsibility left to caller
        """

        def result_is_not_dict(_previous_value: Any, current_value: Any) -> bool:
            return not isinstance(current_value, dict)

        self._conditional_evaluation(result_is_not_dict)
        self._enforce_add_value()


@dataclass
class SmartList(SmartValue):
    """
    Represent a smart value that should result in a list
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list
        """
        return list(value)

    def get_evaluated_value(self) -> list:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: list
        """
        return super().get_evaluated_value()


@dataclass
class SmartRawList(SmartValue):
    """
    Represent a smart value that should result in a list without evaluating
    the smart values that may be present in the list
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list
        """
        return list(value)

    def get_evaluated_value(self) -> list:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: list
        """
        return super().get_evaluated_value()

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until a
        list is reached. The evaluation of the element of the list is a
        responsibility left to caller
        """

        def result_is_not_list(_previous_value: Any, current_value: Any) -> bool:
            return not isinstance(current_value, list)

        self._conditional_evaluation(result_is_not_list)
        self._enforce_add_value()


@dataclass
class SmartPath(SmartValue):
    """
    Represent a smart value that should result in a path
    """

    @staticmethod
    def type_enforce_value(value: Any) -> Path:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Path
        """
        return Path(value)

    def get_evaluated_value(self) -> Path:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: Path
        """
        return super().get_evaluated_value()


class SmartBytes(SmartValue):
    """
    Represent a smart value that should result in bytes
    """

    @staticmethod
    def type_enforce_value(value: Any) -> bytes:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: bytes
        """
        return bytes(value, encoding="utf-8")

    def get_evaluated_value(self) -> bytes:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: bytes
        """
        return super().get_evaluated_value()


@dataclass
class SmartDatetime(SmartValue):
    """
    Represent a smart value that should result in a datetime
    """

    @staticmethod
    def type_enforce_value(value: Any) -> datetime:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: datetime
        """
        result = dateparser.parse(
            str(value), settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True}
        )
        if isinstance(result, datetime):
            return result
        raise errors.ParsingError(value, "datetime")

    def get_evaluated_value(self) -> datetime:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: datetime
        """
        return super().get_evaluated_value()
