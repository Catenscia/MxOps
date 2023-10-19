"""
author: Etienne Wallet

This module contains the cli for the analyze subpackage
"""
from argparse import (
    _SubParsersAction,
    ArgumentError,
    ArgumentParser,
    Namespace,
)
import os

from multiversx_sdk_core import Address
from mxops.analyze import plots
from mxops.analyze.fetching import update_transactions_data

from mxops.data import path
from mxops.config.config import Config
from mxops.data.analyze_data import TransactionsData
from mxops.data.execution_data import ScenarioData
from mxops.enums import parse_network_enum
from mxops.execution.utils import get_address_instance
from mxops.utils.logger import get_logger


LOGGER = get_logger("analyze cli")


def add_subparser(subparsers_action: _SubParsersAction):
    """
    Add the analyze subparser to a parser

    :param subparsers_action: subparsers interface for the parent parser
    :type subparsers_action: _SubParsersAction[ArgumentParser]
    """
    analyze_parser: ArgumentParser = subparsers_action.add_parser("analyze")

    # create sub parser for analyze cli
    analyze_subparsers_actions = analyze_parser.add_subparsers(
        dest="analyze_command",
    )

    # add update-tx command
    update_parser = analyze_subparsers_actions.add_parser("update-tx")

    update_parser.add_argument(
        "-n",
        "--network",
        help="Name of the network to use",
        type=parse_network_enum,
        required=True,
    )

    update_parser.add_argument(
        "-c",
        "--contract",
        help="Bech32 address or contract name if a Scenario is provided",
        required=True,
    )

    update_parser.add_argument(
        "-s",
        "--scenario",
        help="Name of the scenario that contains the provided contract",
    )

    # add plot command
    plot_parser = analyze_subparsers_actions.add_parser("plots")

    plot_parser.add_argument(
        "-n",
        "--network",
        help="Name of the network to use",
        type=parse_network_enum,
        required=True,
    )

    plot_parser.add_argument(
        "-c",
        "--contract",
        help="Bech32 address or contract name if a Scenario is provided",
        required=True,
    )

    plot_parser.add_argument(
        "-s",
        "--scenario",
        help="Name of the scenario that contains the provided contract",
    )

    plot_parser.add_argument(
        "plots",
        nargs="+",
        type=str,
        help="Plots to create",
    )

    # add list command
    analyze_subparsers_actions.add_parser("list-plot")


def get_bech32_address(contract: str, scenario: str | None = None) -> str:
    """
    Parse the scenario and contract argument to retrieve the contract address

    :param contract: name of bech32 address of the contract
    :type contract: str
    :param scenario: sceneario name, defaults to None
    :type scenario: str | None, optional
    :return: bech32 address
    :rtype: str
    """
    if scenario:
        ScenarioData.load_scenario(scenario)
        bech32_address = get_address_instance(contract)
    else:
        bech32_address = contract
    return Address.from_bech32(bech32_address).bech32()


# pylint: disable=R0912
def execute_cli(args: Namespace):
    """
    Execute the analyze cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != "analyze":
        raise ValueError(f"Command analyze was expected, found {args.command}")
    path.initialize_data_folder()

    sub_command = args.analyze_command

    if sub_command == "update-tx":
        Config.set_network(args.network)
        bech32_address = get_bech32_address(args.contract, args.scenario)
        try:
            txs_data = TransactionsData.load_from_file(bech32_address)
        except FileNotFoundError:
            txs_data = TransactionsData(bech32_address)
        update_transactions_data(txs_data)
    elif sub_command == "plots":
        try:
            os.makedirs("./mxops_analyzes")
        except FileExistsError:
            pass
        Config.set_network(args.network)
        bech32_address = get_bech32_address(args.contract, args.scenario)
        txs_data = TransactionsData.load_from_file(bech32_address)
        for plot in args.plots:
            LOGGER.info(f"Plotting {plot}")
            func_name = f"get_{plot}_fig"
            func = getattr(plots, func_name)
            fig = func(txs_data)
            fig.savefig(
                f"./mxops_analyzes/{bech32_address}_{plot}.png",
                dpi=300,
                bbox_inches="tight",
            )
    elif sub_command == "list-plot":
        print("available plots:")
        for name in sorted(plots.get_all_plots()):
            print(name)
    else:
        raise ArgumentError(None, f"Unkown command: {args.command}")
