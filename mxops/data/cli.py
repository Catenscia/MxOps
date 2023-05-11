"""
author: Etienne Wallet

This module contains the cli for the data subpackage
"""
from argparse import _SubParsersAction, ArgumentError, Namespace, RawDescriptionHelpFormatter
from importlib import resources
import json

from mxops.data import path
from mxops.config.config import Config
from mxops.data.data import ScenarioData, delete_scenario_data
from mxops.enums import parse_network_enum


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
        description=resources.read_text('mxops.resources',
                                        'data_parser_help.txt'),
        dest='data_command')

    # add get command
    get_parser = data_subparsers_actions.add_parser('get')

    get_parser.add_argument('-n',
                            '--network',
                            help='Name of the network to use',
                            type=parse_network_enum,
                            required=True)

    get_parser.add_argument('-p',
                            '--path',
                            action='store_true',
                            help='Display the root path for the user data')

    get_parser.add_argument('-l',
                            '--list',
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
                               type=parse_network_enum,
                               required=True)

    delete_parser.add_argument('-s',
                               '--scenario',
                               help='Name of the scenario for the data deletion')

    delete_parser.add_argument('-a',
                               '--all',
                               action='store_true',
                               help='Delete all scenarios saved for the specified network')

    delete_parser.add_argument('-y',
                               '--yes',
                               action='store_true',
                               help='Skip confirmation step')


def execute_cli(args: Namespace):  # pylint: disable=R0912
    """
    Execute the data cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != 'data':
        raise ValueError(f'Command data was expected, found {args.command}')
    path.initialize_data_folder()
    Config.set_network(args.network)

    sub_command = args.data_command

    if sub_command == 'get':
        if args.scenario:
            ScenarioData.load_scenario(args.scenario)
            print(json.dumps(ScenarioData.get().to_dict(), indent=4))
        elif args.list:
            scenarios_names = path.get_all_scenarios_names()
            data = {'names': sorted(scenarios_names)}
            print(json.dumps(data, indent=4))
        elif args.path:
            print(f'Root data path: {path.get_data_path()}')
        else:
            raise ArgumentError(None, 'This set of options is not valid')
    elif sub_command == 'delete':
        if args.scenario:
            delete_scenario_data(args.scenario, not args.yes)
        elif args.all:
            scenarios_names = path.get_all_scenarios_names()
            message = 'Confirm deletion of all scenario. (y/n)'
            if not args.yes or input(message).lower() not in ('y', 'yes'):
                print('User aborted deletion')
                return
            for scenario in scenarios_names:
                delete_scenario_data(scenario, False)
        else:
            raise ArgumentError(None, 'This set of options is not valid')
    else:
        raise ArgumentError(None, f'Unkown command: {args.command}')
