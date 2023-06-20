"""
author: Etienne Wallet

This module implement an automatic layer on top of bump2version. It deduce the type of
version change needed using commits messages.
"""
from argparse import ArgumentParser, Namespace
import configparser
from enum import Enum
import re
import sys
from typing import Dict
import subprocess
import logging

logger = logging.getLogger("AutoBump")
logger.setLevel("DEBUG")


class ChangeType(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    RELEASE = "release"
    BUILD = "build"


def parse_version(version_str: str) -> Dict[ChangeType, str]:
    """
    Parse the version string according the the parse expression from the bumversion
    config file.

    :param version_str: version as a string
    :type version_str: str
    :return: dictionnary with version parts names and their values
    :rtype: Dict[ChangeType, str]
    """
    config_file = "setup.cfg"
    config = configparser.ConfigParser()
    config.read(config_file)
    parse_expr = config.get("bumpversion", "parse")
    version_parts = re.match(parse_expr, version_str).groupdict()
    return {ChangeType(k): v for k, v in version_parts.items()}


def get_commit_change_type(commits_messages: str) -> ChangeType:
    """
    Use regex to infer the type of version change induced by the commit messages.
    Conventional commits must be used:
    https://www.conventionalcommits.org/en/v1.0.0/

    :param commits_messages: concatenation of the commit message to take into account
    :type commits_messages: str
    :return: deduced version change
    :rtype: ChangeType
    """
    lower_messages = commits_messages.lower()
    if re.search(r"^breaking change:", lower_messages, flags=re.M) is not None:
        return ChangeType.MAJOR
    if re.search(r"^feat:", lower_messages, flags=re.M) is not None:
        return ChangeType.MINOR
    return ChangeType.PATCH


def get_change_to_apply(
    version_parts: Dict[ChangeType, str], commit_change_type: ChangeType
) -> ChangeType:
    """
    Figure out what version change needs to be applied depending on the type of commit
    change and the version number.
    The main logic is that if an identical or lower change type has already been made
    in the current release type, only the build version will be bumped.

    Examples:

    - 0.1.0 -(minor_change)-> 0.2.0-dev0 -(minor_change)-> 0.2.0-dev1
    - 0.1.0 -(minor_change)-> 0.2.0-dev0 -(patch_change)-> 0.2.0-dev1
    - 0.1.0 -(minor_change)-> 0.2.0-dev0 -(major_change)-> 1.0.0-dev0

    :param version_parts: dictionnary with version parts names and their values
    :type version_parts: Dict[ChangeType, str]
    :param commit_change_type: type of change induced by the commits
    :type commit_change_type: ChangeType
    :return: change to apply to the version
    :rtype: ChangeType
    """
    if version_parts[ChangeType.RELEASE] is None:
        if commit_change_type == ChangeType.BUILD:
            raise ValueError("Build can not be increased if release is None")
        return commit_change_type
    if (
        commit_change_type == ChangeType.MINOR
        and version_parts[ChangeType.RELEASE.PATCH] != "0"
    ):
        return ChangeType.MINOR
    if commit_change_type == ChangeType.MAJOR and (
        version_parts[ChangeType.RELEASE.MINOR] != "0"
        or version_parts[ChangeType.RELEASE.PATCH] != "0"
    ):
        return ChangeType.MAJOR
    return ChangeType.BUILD


def parse_args() -> Namespace:
    """
    Parse the user input arguments and return the resulting Namespace

    :return: result of the user inputs parsing
    :rtype: Namespace
    """
    parser = ArgumentParser()

    parser.add_argument(
        "target_branch",
        type=str,
        choices=["main", "develop"],
        help="target_branch for the PR",
    )

    parser.add_argument("version", type=str, help="current version before version bump")

    parser.add_argument(
        "commits_messages",
        type=str,
        help="concatenation of all commits messages to include in the version bum",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="do not apply any change to the version"
    )

    return parser.parse_args()


def main():
    """
    Figure out the version change to apply and execute bump2version accordingly
    """
    args = parse_args()
    logger.info(f"version retrieved: {args.version}\n")
    logger.info(f"commits messages:\n{args.commits_messages}\n")
    version_parts = parse_version(args.version)
    logger.info(f"version parts: {version_parts}")

    if args.target_branch == "main":
        change_to_apply = ChangeType.RELEASE
    else:
        commit_change_type = get_commit_change_type(args.commits_messages)
        logger.info(f"commit change type: {commit_change_type}")
        change_to_apply = get_change_to_apply(version_parts, commit_change_type)
    logger.info(f"change to apply: {change_to_apply}")

    commands = ["bump2version", "--verbose", "--commit", change_to_apply.value]
    if args.dry_run:
        commands.append("--dry-run")
    complete_process = subprocess.run(commands)
    sys.exit(complete_process.returncode)


if __name__ == "__main__":
    main()
