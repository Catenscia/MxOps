"""
author: Etienne Wallet

This module contains some utils functions and classes
"""

import os
from pathlib import Path

from importlib_resources import files

from mxops.enums import LogGroupEnum
from mxops.utils.logger import get_logger


def dump_default_config():
    """
    Take the default config and dump it in the working directory as mxops_config.ini
    """
    logger = get_logger(LogGroupEnum.GNL)
    dump_path = Path("./mxops_config.ini")
    if os.path.exists(dump_path.as_posix()):
        raise RuntimeError("A config file already exists in the working directory")

    default_config = files("mxops.resources").joinpath("default_config.ini")

    with open(dump_path.as_posix(), "w+", encoding="utf-8") as dump_file:
        dump_file.write(default_config.read_text())
    logger.info(f"Copy of the default config dumped at {dump_path.absolute()}")
