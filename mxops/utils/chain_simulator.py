from argparse import _SubParsersAction, ArgumentParser, Namespace
from pathlib import Path
import subprocess  # nosec
import sys

import requests

from mxops.config.config import Config
from mxops.data.cli import data_path
from mxops.utils.logger import get_logger

LOGGER = get_logger("CHAIN SIMULATOR")


def add_subparser(subparsers_action: _SubParsersAction):
    """
    Add the chain simulator subparser to a parser

    :param subparsers_action: subparsers interface for the parent parser
    :type subparsers_action: _SubParsersAction[ArgumentParser]
    """
    cs_parser: ArgumentParser = subparsers_action.add_parser("chain-simulator")

    cs_parser.add_argument(
        "action",
        choices=["start", "stop"],
    )


def execute_cli(args: Namespace):  # pylint: disable=R0912
    """
    Execute the chain simulator cli by following the given parsed arguments

    :param args: parsed arguments
    :type args: Namespace
    """
    if args.command != "chain-simulator":
        raise ValueError(f"Command chain-simulator was expected, found {args.command}")

    if args.action == "start":
        fetch_and_save_docker_compose()
        start_chain_simulator()
    if args.action == "stop":
        stop_chain_simulator()


def get_docker_compose_path() -> Path:
    """
    Return the path where to save or read the docker compose file

    :return: path to the docker compose file
    :rtype: Path
    """
    root_folder_path = data_path.get_mxops_data_path()
    return root_folder_path / "chain_simulator_docker_compose.yaml"


def fetch_and_save_docker_compose():
    """
    Fetch the docker compose file to launch the full chain simulator setup
    and save it within mxops files
    """
    source_path = Config.get_config().get("CHAIN_SIMULATOR_FULL_DOCKER_COMPOSE_PATH")
    if source_path.startswith("http"):
        LOGGER.info(f"Download the docker compose file from {source_path}")
        response = requests.get(source_path, timeout=5)
        response.raise_for_status()
        source_content = response.text
    else:
        LOGGER.info(f"Copying the docker compose file from {source_path}")
        source_content = Path(source_path).read_text()
    file_path = get_docker_compose_path()
    file_path.write_text(source_content)


def start_chain_simulator():
    """
    Start the chain simulator
    """
    LOGGER.info("Starting the chain simulator")
    file_path = get_docker_compose_path()
    process = subprocess.Popen(  # nosec
        ["docker", "compose", "-f", file_path.as_posix(), "up", "-d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
    )

    for line in iter(process.stderr.readline, ""):
        print(line, end="", file=sys.stderr)

    process.wait()

    if process.returncode != 0:
        print(
            "Error: chain simulator process ended with return code "
            f"{process.returncode}"
        )
    else:
        LOGGER.info("chain simulator successfully started")


def stop_chain_simulator():
    """
    Stop the chain simulator
    """
    LOGGER.info("Stopping the chain simulator")
    file_path = get_docker_compose_path()
    process = subprocess.Popen(  # nosec
        ["docker", "compose", "-f", file_path.as_posix(), "down"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
    )

    for line in iter(process.stderr.readline, ""):
        print(line, end="", file=sys.stderr)

    process.wait()

    if process.returncode != 0:
        print(
            "Error: chain simulator process ended with return code "
            f"{process.returncode}"
        )
    else:
        LOGGER.info("chain simulator successfully stopped")
