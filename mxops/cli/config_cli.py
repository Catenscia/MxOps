"""
author: Etienne Wallet

This module contains the cli for the config subpackage
"""

from argparse import _SubParsersAction, Namespace, RawDescriptionHelpFormatter
from mxops.config.utils import dump_default_config
from mxops.data.utils import json_dumps

from mxops.enums import parse_network_enum
from mxops.config.config import Config


def add_subparser(subparsers_action: _SubParsersAction):
    """
    Add the steps subparser to a parser

    :param subparsers_action: subparsers interface for the parent parser
    :type subparsers_action: _SubParsersAction[ArgumentParser]
    """
    config_parser = subparsers_action.add_parser(
        "config",
        formatter_class=RawDescriptionHelpFormatter,
    )

    config_parser.add_argument(
        "-n", "--network", help="Name of the network to use", type=parse_network_enum
    )

    config_parser.add_argument(
        "-o",
        "--options",
        action="store_true",
        help=("list of options in the config for the specified network"),
    )

    config_parser.add_argument(
        "-v",
        "--values",
        action="store_true",
        help=(
            "list of options and their values in the config for the specified network"
        ),
    )

    config_parser.add_argument(
        "-d",
        "--dump-default",
        action="store_true",
        help=(
            "take the default config and dump it in "
            "the working directory as mxops_config.ini"
        ),
    )


def execute_cli(args: Namespace):
    """
    Execute the config cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != "config":
        raise ValueError(f"Command config was expected, found {args.command}")

    if args.dump_default:
        dump_default_config()

    if args.network:
        Config.set_network(args.network)

    config = Config.get_config()
    if args.options:
        print(config.get_options())

    if args.values:
        print(json_dumps(config.get_values()))
