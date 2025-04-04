"""
author: Etienne Wallet

Define the main cli of MxOps
"""

from argparse import Namespace, RawDescriptionHelpFormatter
import argparse
from importlib import metadata

from mxops.cli import config_cli, data_cli, execution_cli
from mxops.data.migrations.run import check_migrate_data
from mxops.enums import LogGroupEnum
from mxops.utils import chain_simulator
from mxops.utils.logger import get_logger


def parse_args() -> Namespace:
    """
    Parse the user input arguments and return the resulting Namespace

    :return: result of the user inputs parsing
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(
        description="""
-----------
DESCRIPTION
-----------
MxOps is a python package created to automate MultiversX transactions: be it smart
contracts deployments, calls, queries or just simple transfers.
Inspired from DevOps tools and built on top of mx-sdk-py, it aims to ease and make
reproducible any interaction with the blockchain.

MxOps targets a broad audience of users and developers, by providing a clear, easy
to read and write syntax, even for non technical users.

See:
 - https://mxops.readthedocs.io/en/stable/
        """,
        formatter_class=RawDescriptionHelpFormatter,
    )

    subparsers_action = parser.add_subparsers(dest="command")

    config_cli.add_subparser(subparsers_action)
    data_cli.add_subparser(subparsers_action)
    execution_cli.add_subparser(subparsers_action)
    chain_simulator.add_subparser(subparsers_action)

    subparsers_action.add_parser("version")

    return parser.parse_args()


def cli_main():
    """
    Main function of the package, responsible of running the highest level logic
    execution. It will use the arguments provided by the user to execute the
    intendend functions.
    """
    args = parse_args()
    check_migrate_data()
    logger = get_logger(LogGroupEnum.GNL)
    logger.info(
        "MxOps  Copyright (C) 2025  Catenscia"
        "\nThis program comes with ABSOLUTELY NO WARRANTY"
    )

    if args.command == "config":
        config_cli.execute_cli(args)
    elif args.command == "data":
        data_cli.execute_cli(args)
    elif args.command == "execute":
        execution_cli.execute_cli(args)
    elif args.command == "version":
        print(metadata.version("mxops"))
    elif args.command == "chain-simulator":
        chain_simulator.execute_cli(args)
