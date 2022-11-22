"""
author: Etienne Wallet

Entry point for the xOps package.
"""
import logging
import time


LOGGER = logging.getLogger('main')


def main():
    """
    Main function of the package, responsible of running the highest level logic execution.
    It will use the arguments provided by the user to execute the intendend functions.
    """
    pass


if __name__ == "__main__":
    t0 = time.time()
    main()
    LOGGER.info('Done: program exit')
    LOGGER.info(f'Duration: {int(time.time() - t0)} seconds')
