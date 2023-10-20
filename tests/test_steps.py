import os
from mxops.data.execution_data import ScenarioData
from mxops.execution.steps import PythonStep


def test_python_step():
    # Given
    scenario_data = ScenarioData.get()
    module_path = "./tests/data/custom_user_module.py"
    function = "set_contract_value"
    step_1 = PythonStep(
        module_path, function, ["my_test_contract", "my_test_key", "my_test_value"]
    )

    step_2 = PythonStep(
        module_path,
        function,
        keyword_arguments={
            "contract_id": "my_test_contract",
            "value_key": "my_test_key",
            "value": 4582,
        },
    )

    # When
    step_1.execute()
    value_1 = scenario_data.get_contract_value("my_test_contract", "my_test_key")
    os_value_1 = os.environ[f"MXOPS_{function.upper()}_RESULT"]
    step_2.execute()
    value_2 = scenario_data.get_contract_value("my_test_contract", "my_test_key")
    os_value_2 = os.environ[f"MXOPS_{function.upper()}_RESULT"]

    # Then
    assert value_1 == "my_test_value"
    assert os_value_1 == "my_test_value"
    assert value_2 == 4582
    assert os_value_2 == "4582"
