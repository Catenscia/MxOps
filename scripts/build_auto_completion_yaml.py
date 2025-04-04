"""
using the content of the tests files all_steps.yaml and all_checks.yaml,
build the auto_completion yaml file for MxOpsHelper while preserving the
comments of the yaml file
"""

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from pathlib import Path


def convert_dict(data: CommentedMap):
    """
    Convert inplace the step or check into the format expected by the auto_completion program,
    preserving all comments.

    :param data: step or check as a CommentedMap
    :type data: ruamel.yaml.comments.CommentedMap
    """
    # Extract type and its comments
    element_type = data.pop("type")

    # Create a new CommentedMap for content
    content = CommentedMap()

    # Move all remaining keys to content, preserving comments
    for key in list(data.keys()):
        content[key] = data.pop(key)

    # Assign label and content
    data["label"] = element_type
    data["content"] = content

    # Preserve comments that were attached to the original mapping
    if hasattr(data, "ca") and data.ca.items:
        # Move comments from original keys to their new locations if needed
        for key, comment in list(data.ca.items.items()):
            if key not in data and key in content:
                content.ca.items[key] = comment
                del data.ca.items[key]


def main(steps_file_path: Path, checks_file_path: Path, output_file_path: Path):
    # Initialize YAML processor with comment preservation
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Load steps file
    with open(steps_file_path.as_posix(), "r") as file:
        steps_data = yaml.load(file)

    # Transform steps in place
    if steps_data and "steps" in steps_data:
        for step in steps_data["steps"]:
            convert_dict(step)

    # Load checks file
    with open(checks_file_path.as_posix(), "r") as file:
        checks_data = yaml.load(file)

    # Transform checks in place
    if checks_data and "checks" in checks_data:
        for check in checks_data["checks"]:
            convert_dict(check)

    # Combine into result, preserving the original structure
    result_data = CommentedMap()
    result_data["steps"] = steps_data.get("steps", []) if steps_data else []
    result_data["checks"] = checks_data.get("checks", []) if checks_data else []

    # Preserve top-level comments if they exist
    if hasattr(steps_data, "ca") and steps_data.ca.comment:
        result_data.ca.comment = steps_data.ca.comment

    # Write to output file
    with open(output_file_path.as_posix(), "w") as file:
        yaml.dump(result_data, file)

    print(f"Conversion complete. Check {output_file_path}")


if __name__ == "__main__":
    main(
        Path("tests/data/all_steps.yaml"),
        Path("tests/data/all_checks.yaml"),
        Path("temp/auto_completion.yaml"),
    )
