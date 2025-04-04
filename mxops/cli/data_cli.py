"""
author: Etienne Wallet

This module contains the cli for the data subpackage
"""

from argparse import (
    _SubParsersAction,
    ArgumentError,
    ArgumentParser,
    Namespace,
    RawDescriptionHelpFormatter,
)
import argparse
from typing import Literal


from mxops.data import data_path
from mxops.config.config import Config
from mxops.data.execution_data import (
    ScenarioData,
    clone_scenario_data,
    create_scenario_data_checkpoint,
    delete_scenario_data,
    load_scenario_data_checkpoint,
)
from mxops.data.utils import json_dumps
from mxops.enums import parse_network_enum
from mxops.smart_values.base import SmartValue


def add_subparser(subparsers_action: _SubParsersAction):
    """
    Add the data subparser to a parser

    :param subparsers_action: subparsers interface for the parent parser
    :type subparsers_action: _SubParsersAction[ArgumentParser]
    """
    data_parser: ArgumentParser = subparsers_action.add_parser(
        "data", formatter_class=RawDescriptionHelpFormatter
    )

    # create sub parser for data cli
    data_subparsers_actions = data_parser.add_subparsers(
        dest="data_command",
    )

    # add get command
    get_parser = data_subparsers_actions.add_parser("get")

    get_parser.add_argument(
        "-n",
        "--network",
        help="Name of the network to use",
        type=parse_network_enum,
        default="chain-simulator",
    )

    get_parser.add_argument(
        "-p",
        "--path",
        action="store_true",
        help="Display the root path for the user data",
    )

    get_parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="Display the names of all scenarios saved for the specified network",
    )

    get_parser.add_argument(
        "-s", "--scenario", help="Name of the scenario of which to display the content"
    )

    get_parser.add_argument(
        "-c",
        "--checkpoint",
        default="",
        help=(
            "Name of the checkpoint of the scenario to inspect,"
            "default leads to current data"
        ),
    )

    get_parser.add_argument(
        "expression",
        nargs="?",
        default=None,
        help="Optional expression to evaluate in the given scenario context",
    )

    # add delete command
    delete_parser = data_subparsers_actions.add_parser("delete")

    delete_parser.add_argument(
        "-n",
        "--network",
        help="Name of the network to use",
        type=parse_network_enum,
        required=True,
    )

    delete_parser.add_argument(
        "-s", "--scenario", help="Name of the scenario for the data deletion"
    )

    delete_parser.add_argument(
        "-c",
        "--checkpoint",
        default="",
        help=(
            "Name of the checkpoint of the scenario to delete,"
            "default will delete all checkpoints and current scenario data"
        ),
    )

    delete_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Delete all scenarios saved for the specified network",
    )

    delete_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation step"
    )

    # add a checkpoint command
    checkpoint_parser = data_subparsers_actions.add_parser("checkpoint")
    checkpoint_parser.add_argument(
        "-n",
        "--network",
        help="Name of the network to use",
        type=parse_network_enum,
        required=True,
    )

    checkpoint_parser.add_argument(
        "-s", "--scenario", help="Name of the scenario for the checkpoint"
    )

    checkpoint_parser.add_argument(
        "-c",
        "--checkpoint",
        required=True,
        help="Name of the checkpoint of the scenario to create/load/delete",
    )

    checkpoint_parser.add_argument(
        "-a",
        "--action",
        type=valid_checkpoint_action,
        help="Name of the checkpoint action to perform",
    )

    # add a clone command
    clone_parser = data_subparsers_actions.add_parser("clone")
    clone_parser.add_argument(
        "-n",
        "--network",
        help="Name of the network to use",
        type=parse_network_enum,
        required=True,
    )

    clone_parser.add_argument(
        "-s", "--source-scenario", help="Name of the source scenario"
    )

    clone_parser.add_argument(
        "-d", "--destination-scenario", help="Name of the destination scenario"
    )

    clone_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation step"
    )


def valid_checkpoint_action(action: str) -> Literal["create", "load", "delete"]:
    """
    validate the action value for the checkpoint subparser

    :rtype: the loaded action
    """
    if action not in ["create", "load", "delete"]:
        raise argparse.ArgumentTypeError(
            f"Invalid action type: {action}. "
            "Valid actions are 'create', 'load', 'delete'"
        )
    return action


def execute_cli(args: Namespace):  # pylint: disable=R0912
    """
    Execute the data cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != "data":
        raise ValueError(f"Command data was expected, found {args.command}")
    Config.set_network(args.network)

    sub_command = args.data_command

    if sub_command == "get":
        if args.scenario:
            ScenarioData.load_scenario(args.scenario, args.checkpoint)
            if args.expression is not None:
                value = SmartValue(args.expression)
                value.evaluate()
                result = value.get_evaluated_value()
            else:
                result = json_dumps(ScenarioData.get().to_dict())
            print(result)
        elif args.list:
            scenarios_names = data_path.get_all_scenarios_names()
            data = {"names": sorted(scenarios_names)}
            print(json_dumps(data))
        elif args.path:
            print(f"Root data path: {data_path.get_mxops_data_path()}")
        else:
            raise ArgumentError(None, "This set of options is not valid")
    elif sub_command == "delete":
        if args.scenario:
            delete_scenario_data(args.scenario, args.checkpoint, not args.yes)
        elif args.all:
            scenarios_names = data_path.get_all_scenarios_names()
            message = "Confirm deletion of all scenario. (y/n)"
            if not args.yes and input(message).lower() not in ("y", "yes"):
                print("User aborted deletion")
                return
            for scenario in scenarios_names:
                delete_scenario_data(scenario, ask_confirmation=False)
        else:
            raise ArgumentError(None, "This set of options is not valid")
    elif sub_command == "checkpoint":
        if args.action == "create":
            create_scenario_data_checkpoint(args.scenario, args.checkpoint)
        elif args.action == "load":
            load_scenario_data_checkpoint(args.scenario, args.checkpoint)
        elif args.action == "delete":
            delete_scenario_data(args.scenario, args.checkpoint)
        else:
            raise ArgumentError(None, f"Unkown checkpoint action: {args.action}")
    elif sub_command == "clone":
        clone_scenario_data(
            args.source_scenario,
            args.destination_scenario,
            not args.yes,
        )
    else:
        raise ArgumentError(None, f"Unkown command: {args.command}")
