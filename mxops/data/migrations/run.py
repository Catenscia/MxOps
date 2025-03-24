"""
author: Etienne Wallet

This module host functions to coordinate and run the migrations
"""

import importlib
import pkgutil

from mxops.data import path_versions
from mxops.data.path_versions.msc import version_name_to_version_path_name
from mxops.enums import LogGroupEnum
from mxops.utils.logger import get_logger


LOGGER = get_logger(LogGroupEnum.DATA)


def get_all_versions() -> list[str]:
    """
    Return all the existing data version, sorted from old to new

    :return: sorted versions
    :rtype: list[str]
    """
    versions = []
    for _, module_name, is_pkg in pkgutil.iter_modules(path_versions.__path__):
        if is_pkg:
            continue
        if not module_name.startswith("v"):
            continue
        module = importlib.import_module(f"mxops.data.path_versions.{module_name}")
        try:
            versions.append(module.VERSION)
        except AttributeError:
            pass
    versions.sort(key=lambda x: tuple(x.split(".")))
    return versions


def get_current_local_data_version(versions: list[str]) -> str | None:
    """
    Determine which version is the one currently saved
    Return None if no version is matched

    :param versions: all available versions
    :type versions: list[str]
    :return: version
    :rtype: str | None
    """
    for version in versions:
        module_name = version_name_to_version_path_name(version)
        module = importlib.import_module(f"mxops.data.path_versions.{module_name}")
        if module.is_current_saved_version():
            return version
    return None


def check_migrate_data():
    """
    Check the current data version and run the migration if needed
    """
    versions = get_all_versions()
    LOGGER.debug(f"Versions found: {versions}")
    current_saved_version = get_current_local_data_version(versions)
    if current_saved_version is None:
        LOGGER.debug("No data version match")
        return
    if current_saved_version == versions[-1]:
        LOGGER.debug("Current data version is the latest")
        return
    LOGGER.info("Current data version is not up to date. Migrating existing data")
    i = versions.index(current_saved_version)
    n_versions = len(versions)
    while i + 1 < n_versions:
        source_version = versions[i]
        dest_version = versions[i + 1]
        LOGGER.info(f"Migrating saved data from {source_version} to {dest_version}")
        module_name = (
            f"{version_name_to_version_path_name(source_version)}__to__"
            f"{version_name_to_version_path_name(dest_version)}"
        )
        LOGGER.debug(f"Migration module: {module_name}")
        module = importlib.import_module(f"mxops.data.migrations.{module_name}")
        module.migrate()
        LOGGER.info("Migration completed")
        i += 1
    last_version_module_name = version_name_to_version_path_name(versions[-1])
    last_version_module = importlib.import_module(
        f"mxops.data.path_versions.{last_version_module_name}"
    )
    last_version_module.register_as_current()
    LOGGER.info("All migrations completed")
