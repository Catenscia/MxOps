"""
author: Etienne Wallet

This module contains utils functions to interact with the chain-simulator
"""

from argparse import _SubParsersAction, ArgumentParser, Namespace
from importlib.resources import files
from pathlib import Path
import subprocess  # nosec
import time
from typing import Optional

import requests
import yaml
from multiversx_sdk.network_providers.errors import GenericError

from mxops.config.config import Config
from mxops.data import data_path
from mxops.utils.logger import get_logger
from mxops.enums import LogGroupEnum, NetworkEnum
from mxops.common.providers import MyProxyNetworkProvider

LOGGER = get_logger(LogGroupEnum.MSC)

MAX_STARTUP_RETRIES = 60  # Maximum seconds to wait for chain simulator to start

# NOTE: SERVICE_DEPENDENCIES must be kept in sync with the embedded docker-compose file
# at mxops/resources/chain_simulator_docker_compose.yaml. These are the logical
# dependencies needed for services to function, not just the docker-compose
# depends_on relationships.
SERVICE_DEPENDENCIES = {
    "redis": [],
    "postgres": [],
    "events-notifier": ["redis"],
    "elasticsearch": [],
    "elastic-indexer": ["elasticsearch"],
    "chain-simulator": ["elasticsearch", "events-notifier"],
    "api": ["elasticsearch", "redis"],
    "explorer": [],
    "lite-wallet": [],
}
ALL_SERVICES = list(SERVICE_DEPENDENCIES.keys())


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

    cs_parser.add_argument(
        "--services",
        nargs="+",
        choices=ALL_SERVICES,
        help="Services to include (whitelist)",
    )

    cs_parser.add_argument(
        "--exclude",
        nargs="+",
        choices=ALL_SERVICES,
        help="Services to exclude (blacklist)",
    )

    cs_parser.add_argument(
        "--no-auto-deps",
        action="store_true",
        help="Don't auto-include dependencies",
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
        services = getattr(args, "services", None)
        exclude = getattr(args, "exclude", None)
        auto_deps = not getattr(args, "no_auto_deps", False)
        start_chain_simulator(
            services=services, exclude=exclude, auto_include_dependencies=auto_deps
        )
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


def get_docker_compose_content() -> str:
    """
    Load docker-compose from custom path if configured, otherwise use embedded.

    :return: docker-compose file content
    :rtype: str
    """
    custom_path = Config.get_config().get("CHAIN_SIMULATOR_FULL_DOCKER_COMPOSE_PATH")

    if custom_path:  # User specified a custom path
        if custom_path.startswith("http"):
            LOGGER.info(f"Download the docker compose file from {custom_path}")
            try:
                response = requests.get(custom_path, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.exceptions.Timeout:
                raise RuntimeError(
                    f"Timeout downloading docker-compose from {custom_path}"
                ) from None
            except requests.exceptions.ConnectionError as e:
                raise RuntimeError(f"Failed to connect to {custom_path}: {e}") from None
            except requests.exceptions.HTTPError as e:
                raise RuntimeError(
                    f"HTTP error downloading docker-compose: {e}"
                ) from None
        else:
            LOGGER.info(f"Copying the docker compose file from {custom_path}")
            return Path(custom_path).read_text(encoding="utf-8")

    # Default: use embedded docker-compose
    LOGGER.info("Using embedded docker-compose file")
    docker_compose = files("mxops.resources").joinpath(
        "chain_simulator_docker_compose.yaml"
    )
    return docker_compose.read_text()


def resolve_services(
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    auto_include_dependencies: bool = True,
) -> list[str]:
    """
    Resolve which services to run, auto-including dependencies if requested.

    :param include: list of services to include (whitelist), defaults to all services
    :type include: Optional[list[str]]
    :param exclude: list of services to exclude (blacklist), defaults to None
    :type exclude: Optional[list[str]]
    :param auto_include_dependencies: whether to auto-include dependencies,
        defaults to True
    :type auto_include_dependencies: bool
    :return: list of services to run
    :rtype: list[str]
    :raises ValueError: if unknown service names are provided
    """
    # Validate service names
    if include is not None:
        unknown = set(include) - set(ALL_SERVICES)
        if unknown:
            raise ValueError(
                f"Unknown services: {unknown}. Valid services: {ALL_SERVICES}"
            )

    if exclude is not None:
        unknown = set(exclude) - set(ALL_SERVICES)
        if unknown:
            raise ValueError(
                f"Unknown services: {unknown}. Valid services: {ALL_SERVICES}"
            )

    # Start with all services or the specified whitelist
    if include is not None:
        services = set(include)
    else:
        services = set(ALL_SERVICES)

    # Auto-include dependencies recursively
    if auto_include_dependencies:
        to_process = list(services)
        while to_process:
            service = to_process.pop()
            for dep in SERVICE_DEPENDENCIES.get(service, []):
                if dep not in services:
                    services.add(dep)
                    to_process.append(dep)

    # Remove excluded services
    if exclude is not None:
        services -= set(exclude)

    return list(services)


def filter_docker_compose(content: str, services: list[str]) -> str:
    """
    Filter docker-compose to only include selected services.

    :param content: docker-compose file content
    :type content: str
    :param services: list of services to include
    :type services: list[str]
    :return: filtered docker-compose content
    :rtype: str
    """
    compose = yaml.safe_load(content)

    # Remove services not in the list
    services_to_remove = [s for s in compose.get("services", {}) if s not in services]
    for service in services_to_remove:
        del compose["services"][service]

    # Clean up depends_on references to removed services
    for service_config in compose.get("services", {}).values():
        if "depends_on" in service_config:
            depends_on = service_config["depends_on"]
            if isinstance(depends_on, list):
                service_config["depends_on"] = [d for d in depends_on if d in services]
                if not service_config["depends_on"]:
                    del service_config["depends_on"]
            elif isinstance(depends_on, dict):
                service_config["depends_on"] = {
                    k: v for k, v in depends_on.items() if k in services
                }
                if not service_config["depends_on"]:
                    del service_config["depends_on"]

    return yaml.dump(compose, default_flow_style=False, sort_keys=False)


def start_chain_simulator(
    services: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    auto_include_dependencies: bool = True,
):
    """
    Start the chain simulator

    :param services: list of services to include (whitelist), defaults to all services
    :type services: Optional[list[str]]
    :param exclude: list of services to exclude (blacklist), defaults to None
    :type exclude: Optional[list[str]]
    :param auto_include_dependencies: whether to auto-include dependencies,
        defaults to True
    :type auto_include_dependencies: bool
    """
    # Resolve which services to run
    resolved_services = resolve_services(
        include=services,
        exclude=exclude,
        auto_include_dependencies=auto_include_dependencies,
    )
    LOGGER.info(f"Starting services: {resolved_services}")

    # Load and filter docker-compose
    content = get_docker_compose_content()
    filtered_content = filter_docker_compose(content, resolved_services)

    # Write filtered compose to temp path
    file_path = get_docker_compose_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(filtered_content)

    LOGGER.info("Starting the chain simulator")
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

    # Only generate first epoch if chain-simulator service is included
    if "chain-simulator" in resolved_services:
        retry_count = 0
        proxy = MyProxyNetworkProvider()
        while retry_count < MAX_STARTUP_RETRIES:
            LOGGER.info("Generating the first epoch")
            try:
                proxy.generate_blocks_until_epoch(2)
                break
            except GenericError:  # node not ready yet
                retry_count += 1
                time.sleep(1)
        else:
            LOGGER.error(
                f"Chain simulator failed to start within {MAX_STARTUP_RETRIES} seconds"
            )
            return

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
