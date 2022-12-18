"""
author: Etienne Wallet

This module contains the cli for the execution subpackage
"""
from argparse import _SubParsersAction, Namespace
from pathlib import Path
from xops.config.config import Config
from xops.data import path
from xops.data.data import ScenarioData

from xops.enums import NetworkEnum
from xops.execution.scene import execute_directory, execute_scene
from xops import errors


def add_subparser(subparsers_action: _SubParsersAction):
    """
    Add the data subparser to a parser

    :param subparsers_action: subparsers interface for the parent parser
    :type subparsers_action: _SubParsersAction[ArgumentParser]
    """
    scenario_parser = subparsers_action.add_parser('execute')
    scenario_parser.add_argument('-s',
                                 '--scenario',
                                 type=str,
                                 required=True,
                                 help=('Name of the scenario in which the '
                                       'scene(s) will be executed'))
    scenario_parser.add_argument('-n',
                                 '--network',
                                 type=NetworkEnum,
                                 required=True,
                                 help=('Name of the network in which the '
                                       'scene(s) will be executed'))
    scenario_parser.add_argument('-f',
                                 '--file',
                                 type=Path,
                                 help='Path to a scene file to execute')
    scenario_parser.add_argument('-d',
                                 '--directory',
                                 type=Path,
                                 help=('Path to directory containing several '
                                       'scenes files to execute'))


def execute_cli(args: Namespace):
    """
    Execute the data cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != 'execute':
        raise ValueError(f'Command execute was expected, found {args.command}')

    path.initialize_data_folder()
    Config.set_network(args.network)
    try:
        ScenarioData.load_scenario(args.scenario)
    except errors.UnknownScenario:
        ScenarioData.create_scenario(args.scenario)
        ScenarioData.get().save()

    if args.file:
        execute_scene(args.file)
    elif args.directory:
        execute_directory(args.directory)
    else:
        raise ValueError('--file or --directory must be supplied')
