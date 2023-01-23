"""
author: Etienne Wallet

Entry point for the MxOps package.
"""
from argparse import Namespace, RawDescriptionHelpFormatter
import argparse
from importlib import resources
import pkg_resources

from mxops.config import cli as config_cli
from mxops.data import cli as data_cli
from mxops.execution import cli as execution_cli


def parse_args() -> Namespace:
    """
    Parse the user input arguments and return the resulting Namespace

    :return: result of the user inputs parsing
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter)

    description = resources.read_text('mxops.resources', 'parser_help.txt')
    subparsers_action = parser.add_subparsers(
        description=description,
        dest='command')

    config_cli.add_subparser(subparsers_action)
    data_cli.add_subparser(subparsers_action)
    execution_cli.add_subparser(subparsers_action)

    subparsers_action.add_parser('version')

    return parser.parse_args()


def main():
    """
    Main function of the package, responsible of running the highest level logic execution.
    It will use the arguments provided by the user to execute the intendend functions.
    """
    args = parse_args()

    print("MxOps  Copyright (C) 2023  Catenscia\nThis program comes with ABSOLUTELY NO WARRANTY")

    if args.command == 'config':
        config_cli.execute_cli(args)
    elif args.command == 'data':
        data_cli.execute_cli(args)
    elif args.command == 'execute':
        execution_cli.execute_cli(args)
    elif args.command == 'version':
        print(pkg_resources.get_distribution('mxops').version)


if __name__ == "__main__":
    main()
