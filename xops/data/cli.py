"""
author: EtWnn

This module contains the cli for the data subpackage
"""
from argparse import _SubParsersAction, ArgumentError, Namespace, RawDescriptionHelpFormatter
from importlib import resources
import json

from xops.data import io
from xops.config.config import Config
from xops.enums import NetworkEnum


def add_subparser(subparsers_action: _SubParsersAction):
    """
    Add the data subparser to a parser

    :param subparsers_action: subparsers interface for the parent parser
    :type subparsers_action: _SubParsersAction[ArgumentParser]
    """
    data_parser = subparsers_action.add_parser('data',
                                               formatter_class=RawDescriptionHelpFormatter)

    # create sub parser for data cli
    data_subparsers_actions = data_parser.add_subparsers(
        description=resources.read_text('xops.resources',
                                        'data_parser_help.txt'),
        dest='data_command')

    # add get command
    get_parser = data_subparsers_actions.add_parser('get')

    get_parser.add_argument('-n',
                            '--network',
                            help='Name of the network to use',
                            type=NetworkEnum,
                            required=True)

    get_parser.add_argument('-p',
                            '--path',
                            action='store_true',
                            help='Display the root path for the user data')

    get_parser.add_argument('-n',
                            '--names',
                            action='store_true',
                            help=('Display the names of all scenarios saved'
                                  ' for the specified network'))

    get_parser.add_argument('-s',
                            '--scenario',
                            help='Name of the scenario of which to display the content')

    # add delete command
    delete_parser = data_subparsers_actions.add_parser('delete')

    delete_parser.add_argument('-n',
                               '--network',
                               help='Name of the network to use',
                               type=NetworkEnum,
                               required=True)

    delete_parser.add_argument('-s',
                               '--scenario',
                               required=True,
                               help='Name of the scenario for the data deletion')

    delete_parser.add_argument('-a',
                               '--all',
                               action='store_true',
                               help='Delete all scenarios saved for the specified network')


def execute_cli(args: Namespace):
    """
    Execute the data cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != 'data':
        raise ValueError(f'Command data was expected, found {args.command}')
    io.initialize_data_folder()
    Config.set_network(args.network)

    sub_command = args.data_command

    if sub_command == 'get':
        if args.scenario:
            data = io.load_scenario_data(args.scenario)
            print(json.dumps(data, indent=4))
        elif args.names:
            scenarios_names = io.get_all_scenarios_names()
            data = {'names': sorted(scenarios_names)}
            print(json.dumps(data, indent=4))
        elif args.path:
            print(f'Root data path: {io.get_data_path()}')
        else:
            raise ArgumentError(None, 'This set of options is not valid')
    elif sub_command == 'delete':
        if args.scenario:
            io.delete_scenario_data(args.scenario)
        elif args.all:
            scenarios_names = io.get_all_scenarios_names()
            for scenario in scenarios_names:
                io.delete_scenario_data(scenario)
        else:
            raise ArgumentError(None, 'This set of options is not valid')
    else:
        raise ArgumentError(None, f'Unkown command: {args.command}')
