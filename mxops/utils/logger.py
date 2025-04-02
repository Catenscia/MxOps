"""
author: Etienne Wallet

This module contains utils various functions
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

from mxops.data import data_path
from mxops.enums import LogGroupEnum


def get_logger_level(name: str) -> str:
    """
    Return the log level associated with the given logger
    Check first if a level is defined for this loger, else
    check if a level is defined for MxOps
    lastly, return a default value

    :param name: name of the loger
    :type name: str
    :return: log level for this logger
    :rtype: str
    """
    log_level = os.environ.get(f"MXOPS_{name.upper()}_LOG_LEVEL", None)
    if log_level is not None:
        return log_level
    return os.environ.get("MXOPS_LOG_LEVEL", "INFO")


def get_logger(
    logger_group: LogGroupEnum, additional_log_file_path: Path | None = None
) -> logging.Logger:
    """
    Generate a logger for a given group
    All logger output to the console and the general MxOps logs

    :param logger_group: group of the logger
    :type logger_group: LogGroupEnum
    :param logger_group: additional file path where to save the logs, default to None
    :type additional_log_file_path: Path | None
    :return: logger
    :rtype: logging.Logger
    """
    logger = logging.getLogger(logger_group.value)
    log_level = get_logger_level(logger_group.name)
    logger.setLevel(log_level)

    # create a log format
    log_format = (
        "[%(asctime)s %(levelname)s] %(message)s [%(name)s in %(filename)s:%(lineno)d]"
    )

    # Add a stream handler if it does not exist
    stream_formatter = logging.Formatter(log_format)
    stream_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    if len(stream_handlers) == 0:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level=log_level)
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

    # Add a general file handler if it does not exist
    general_logs_path = data_path.get_mxops_logs_folders() / "mxops.log"
    absolute_str_path = general_logs_path.absolute().as_posix()
    general_file_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, RotatingFileHandler) and h.baseFilename == absolute_str_path
    ]
    if len(general_file_handlers) == 0:
        general_file_formatter = logging.Formatter(log_format)
        general_logs_path.parent.mkdir(parents=True, exist_ok=True)
        general_file_handler = RotatingFileHandler(
            filename=absolute_str_path,
            maxBytes=1_048_576,  # 1MB
            backupCount=100,
        )
        general_file_handler.setFormatter(general_file_formatter)
        logger.addHandler(general_file_handler)

    # Add a file handler if it does not exist and if additional path is defined
    if additional_log_file_path is not None:
        additional_file_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, RotatingFileHandler)
            and h.baseFilename != absolute_str_path
        ]
        if len(additional_file_handlers) == 0:
            additional_file_formatter = logging.Formatter(log_format)
            additional_log_file_path.parent.mkdir(parents=True, exist_ok=True)
            additional_file_handler = RotatingFileHandler(
                filename=additional_log_file_path.as_posix(),
                maxBytes=1_048_576,  # 1MB
                backupCount=100,
            )
            additional_file_handler.setFormatter(additional_file_formatter)
            logger.addHandler(additional_file_handler)

    return logger
