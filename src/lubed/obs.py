"""OBS API mini client."""

# SPDX-License-Identifier: GPL-3.0-or-later
import functools
import urllib.parse
from typing import List, Tuple
from xml.etree import ElementTree

import requests

from lubed import OBSCredentials, Package, Timestamp


def list_packages(
    project_name: str,
    credentials: OBSCredentials,
    api_url: str = "https://api.opensuse.org",
) -> List[str]:
    """List all OBS packages in an OBS project.

    :param project_name: Name of OBS project
    :param credentials: OBS API credentials
    :param api_url: Base URL of the OBS API server, defaults to https://api.opensuse.org
    :return: List of package names
    """
    response_text = _query_packages_list(
        project_name=project_name,
        credentials=credentials,
        api_url=api_url,
    )

    return _parse_packages_list(response_text)


def package_was_updated(
    last_check: Timestamp,
    package: Package,
    credentials: OBSCredentials,
    api_url: str = "https://api.opensuse.org",
) -> Tuple[bool, bool]:
    """Check if an OBS package was changed since a known timestamp.

    :param last_check: Unix timestamp of the last check
    :param package: OBS package to check
    :param credentials: OBS API credentials
    :param api_url: Base URL of the OBS API server, defaults to https://api.opensuse.org
    :return:
        - package_updated: True if the package was updated, False otherwise
        - err: True if an error occurred during the verification, False otherwise
    """
    response_text, err = _query_package(
        package=package,
        credentials=credentials,
        api_url=api_url,
    )

    timestamps = _extract_package_timestamps(response_text)

    return _any_timestamp_is_newer(timestamps, last_check), err


def list_subprojects(
    project_name: str,
    credentials: OBSCredentials,
    api_url: str = "https://api.opensuse.org",
) -> List[str]:
    """List all OBS packages in an OBS project.

    :param project_name: Name of OBS project
    :param credentials: OBS API credentials
    :param api_url: Base URL of the OBS API server, defaults to https://api.opensuse.org
    :return: List of package names
    """
    response_text = _query_subprojects_list(
        project_name=project_name,
        credentials=credentials,
        api_url=api_url,
    )

    return _parse_subprojects_list(response_text)


def package_in_project(
    package_name: str, project_name: str, credentials: OBSCredentials, api_url: str
) -> bool:
    return _query_package(
        Package(name=package_name, project=project_name), credentials, api_url
    )[1]


@functools.lru_cache
def _query_subprojects_list(
    project_name: str, credentials: OBSCredentials, api_url: str
):
    try:
        url = f"{api_url}/search/project/id?match=" + urllib.parse.quote(
            f'starts_with(@name, "{project_name}")'
        )
        response = requests.get(url, auth=credentials.as_tuple())
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""


def _any_timestamp_is_newer(timestamps: List[Timestamp], base: Timestamp):
    return any(ts > base for ts in timestamps)


@functools.lru_cache
def _query_packages_list(
    project_name: str, credentials: OBSCredentials, api_url: str
) -> str:
    try:
        url = f"{api_url}/source/{project_name}"
        response = requests.get(url, auth=credentials.as_tuple())
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""


def _parse_packages_list(response_text: str) -> List[str]:
    if not response_text:
        return []

    root = ElementTree.fromstring(response_text)
    return [package.attrib["name"] for package in root.findall("./entry")]


def _parse_subprojects_list(response_text: str) -> List[str]:
    if not response_text:
        return []

    root = ElementTree.fromstring(response_text)
    return [package.attrib["name"] for package in root.findall("./project")]


def _extract_package_timestamps(response_text) -> List[Timestamp]:
    if not response_text:
        return []

    root = ElementTree.fromstring(response_text)
    return [Timestamp(package.attrib["mtime"]) for package in root.findall("./entry")]


@functools.lru_cache
def _query_package(
    package: Package,
    credentials: OBSCredentials,
    api_url: str,
) -> Tuple[str, bool]:
    try:
        url = f"{api_url}/source/{package.project}/{package.name}"
        response = requests.get(url, auth=credentials.as_tuple())
        response.raise_for_status()
        return response.text, False
    except requests.RequestException:
        return "", True
