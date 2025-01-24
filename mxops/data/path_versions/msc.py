"""
author: Etienne Wallet

This module contains miscellanious functions for the sub package

"""


def version_name_to_version_path_name(version: str) -> str:
    """
    Convert a version name (v1.0.0) to the equivalent as a path (v1_0_0).
    It replaces the dots by underscores

    :param version: version to convert
    :type version: str
    :return: converted version
    :rtype: str
    """
    return version.replace(".", "_")
