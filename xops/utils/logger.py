"""
author: Etienne Wallet

This module contains utils various functions
"""
import logging

from xops.config.config import Config


def get_logger(name: str) -> logging.Logger:
    """
    Generate a logger for a given name

    :param name: name of the logger
    :type name: str
    :return: logger
    :rtype: logging.Logger
    """
    config = Config.get_config()
    logger = logging.getLogger(name)
    try:
        log_level = config.get('LOGGING_LEVEL')
    except KeyError:
        log_level = 'WARNING'
    logger.setLevel(log_level)

    # create formatter and add it to the handlers
    log_format = ('[%(asctime)s %(name)s %(levelname)s]'
                  ' %(message)s [%(name)s:%(lineno)d in %(funcName)s]')
    formatter = logging.Formatter(log_format)

    # create console handler for logger.
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level=log_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
