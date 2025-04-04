"""
author: Etienne Wallet

This module contains utils functions to interact with the chain-simulator
"""

from argparse import _SubParsersAction, ArgumentParser, Namespace
from pathlib import Path
import subprocess  # nosec
import time

import requests
from multiversx_sdk.network_providers.errors import GenericError

from mxops.config.config import Config
from mxops.data import data_path
from mxops.utils.logger import get_logger
from mxops.enums import LogGroupEnum, NetworkEnum
from mxops.common.providers import MyProxyNetworkProvider

LOGGER = get_logger(LogGroupEnum.MSC)


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
    Config.set_network(NetworkEnum.CHAIN_SIMULATOR)

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
        source_content = Path(source_path).read_text(encoding="utf-8")
    file_path = get_docker_compose_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
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
        LOGGER.info(line.rstrip("\n"))

    process.wait()

    if process.returncode != 0:
        LOGGER.error(
            f"Chain simulator process ended with return code {process.returncode}"
        )
        return

    # generate the first epoch
    proxy = MyProxyNetworkProvider()
    while True:
        LOGGER.info("Generating the first epoch")
        try:
            proxy.generate_blocks_until_epoch(2)
            break
        except GenericError:  # node not ready yet
            time.sleep(1)
    explorer_url = Config.get_config().get("EXPLORER_URL")
    LOGGER.info(
        f"chain simulator successfully started, check the explorer: {explorer_url}"
    )


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
        LOGGER.info(line.rstrip("\n"))

    process.wait()

    if process.returncode != 0:
        LOGGER.error(
            f"Chain simulator process ended with return code {process.returncode}"
        )
    else:
        LOGGER.info("chain simulator successfully stopped")
