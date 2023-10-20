"""
author: Etienne Wallet

This module contains utils various functions
"""
import logging
import os


def get_logger(name: str) -> logging.Logger:
    """
    Generate a logger for a given name

    :param name: name of the logger
    :type name: str
    :return: logger
    :rtype: logging.Logger
    """
    logger = logging.getLogger(name)
    log_level = os.environ.get("MXOPS_LOG_LEVEL", "INFO")
    logger.setLevel(log_level)

    # create formatter and add it to the handlers
    log_format = (
        "[%(asctime)s %(name)s %(levelname)s]"
        " %(message)s [%(filename)s:%(lineno)d in %(funcName)s]"
    )
    formatter = logging.Formatter(log_format)

    # create console handler for logger.
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level=log_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
