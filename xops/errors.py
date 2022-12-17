"""
author: Etienne Wallet

Errors used in the xOps package
"""
from erdpy.transactions import Transaction

from xops.utils.msc import get_proxy_tx_link

#############################################################
#
#                   Data Managment Errors
#
#############################################################

class UnknownScenario(Exception):
    """
    To be raised when a specified scenario is not found
    """

    def __init__(self, scenario_name: str) -> None:
        message = (f'Scenario {scenario_name} is unkown')
        super().__init__(message)


class UnloadedScenario(Exception):
    """
    To be raised when the scenario data was asked before being loaded
    """

    def __init__(self) -> None:
        message = (f'Scenario data was not loaded')
        super().__init__(message)


class UnknownContract(Exception):
    """
    To be raised when a specified contract is not found is a scenario
    """

    def __init__(self, scenario_name: str, contract_id: str) -> None:
        message = (f'Contract {contract_id} is unkown in '
                   f'scenario {scenario_name}')
        super().__init__(message)


class ContractIdAlreadyExists(Exception):
    """
    To be raised when there is a conflict with contract id
    """

    def __init__(self, contract_id: str) -> None:
        message = f'Contract id {contract_id} already exists'
        super().__init__(message)


class ScenarioNameAlreadyExists(Exception):
    """
    To be raised when there is a conflict with scenario name
    """

    def __init__(self, scenario_name: str) -> None:
        message = f'Scenario name {scenario_name} already exists'
        super().__init__(message)


class WrongScenarioDataReference(Exception):
    """
    To be raised when a reference to some scenario data could not
    be parsed correctly
    """

    def __init__(self) -> None:
        message = ('Scenario data reference must have the format '
                   r'"%contract_id%valuekey[:optional_format]"')
        super().__init__(message)
