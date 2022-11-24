"""
author: Etienne Wallet

Entry point for the xOps package.
"""
from argparse import ArgumentError, Namespace, RawDescriptionHelpFormatter
import argparse
from importlib import resources

from xops.config import cli as config_cli
from xops.data import cli as data_cli


def parse_args() -> Namespace:
    """
    Parse the user input arguments and return the resulting Namespace

    :return: result of the user inputs parsing
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter)

    description = resources.read_text('xops.resources', 'parser_help.txt')
    subparsers_action = parser.add_subparsers(
        description=description,
        dest='command')

    config_cli.add_subparser(subparsers_action)
    data_cli.add_subparser(subparsers_action)

    return parser.parse_args()


def main():
    """
    Main function of the package, responsible of running the highest level logic execution.
    It will use the arguments provided by the user to execute the intendend functions.
    """
    args = parse_args()

    if args.command == 'config':
        config_cli.execute_cli(args)
    elif args.command == 'data':
        data_cli.execute_cli(args)
    else:
        raise ArgumentError(None, f'Unkown command: {args.command}')


if __name__ == "__main__":
    main()
