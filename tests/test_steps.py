from typing import Any
from mxops import errors
from mxops.data.execution_data import ScenarioData
from mxops.execution.steps import LoopStep, PythonStep, SetVarsStep


def test_python_step():
    # Given
    scenario_data = ScenarioData.get()
    module_path = "./tests/data/custom_user_module.py"
    function = "set_contract_value"
    step_1 = PythonStep(
        module_path,
        function,
        ["my_test_contract", "my_test_key", "my_test_value"],
        print_result=True,
        result_save_key="result_1",
    )

    step_2 = PythonStep(
        module_path,
        function,
        keyword_arguments={
            "contract_id": "my_test_contract",
            "value_key": "my_test_key",
            "value": 4582,
        },
        print_result=True,
        result_save_key="result_2",
    )

    # When
    step_1.execute()
    value_1 = scenario_data.get_contract_value("my_test_contract", "my_test_key")
    scenario_value_1 = scenario_data.get_value("result_1")
    step_2.execute()
    value_2 = scenario_data.get_contract_value("my_test_contract", "my_test_key")
    scenario_value_2 = scenario_data.get_value("result_2")

    # Then
    assert value_1 == "my_test_value"
    assert scenario_value_1 == "my_test_value"
    assert value_2 == 4582
    assert scenario_value_2 == 4582


def test_direct_set_vars_step():
    # Given
    scenario_data = ScenarioData.get()
    variables = {
        "int-var": 1,
        "str-var": "hello",
        "list-var": [1, 2, "a", [1, 3]],
        "dict-var": {"a": 23, 23: ["a", 124]},
    }
    step = SetVarsStep(variables)

    # When
    step.execute()

    # Then
    saved_values = {key: scenario_data.get_value(key) for key in variables}
    assert variables == saved_values


def test_reference_set_vars_step():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("reg-list", [1, 2, 3])
    scenario_data.set_value("reg-name", "bob")
    scenario_data.set_value("reg-value", 1)
    variables = {
        "int-var": "%reg-value",
        "str-var": "%reg-name",
        "list-var": [1, 2, "a", "%reg-list"],
        "dict-var": {"%reg-name": 23, 23: ["%reg-name", "%reg-list"]},
    }
    step = SetVarsStep(variables)

    # When
    step.execute()

    # Then
    expected_result = {
        "int-var": 1,
        "str-var": "bob",
        "list-var": [1, 2, "a", [1, 2, 3]],
        "dict-var": {"bob": 23, 23: ["bob", [1, 2, 3]]},
    }
    saved_values = {key: scenario_data.get_value(key) for key in variables}
    assert expected_result == saved_values


def register_value_in_list(value: Any):
    scenario_data = ScenarioData.get()
    try:
        register_list = scenario_data.get_value("register_list")
    except errors.WrongDataKeyPath:
        register_list = []
    register_list.append(value)
    scenario_data.set_value("register_list", register_list)


def test_loop_step_from_scenario_data_list():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("var_list", [1, 2, 4])
    loop_step = LoopStep(
        steps=[
            PythonStep("./tests/test_steps.py", "register_value_in_list", ["%loop_var"])
        ],
        var_name="loop_var",
        var_list="%var_list",
    )

    # When
    for step in loop_step.generate_steps():
        step.execute()

    # Then
    assert scenario_data.get_value("register_list") == [1, 2, 4]
