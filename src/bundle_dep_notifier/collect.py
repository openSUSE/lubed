from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

import requests

Timestamp = int


@dataclass(frozen=True)
class Origin:
    project: str
    package: str


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str

    def as_tuple(self):
        return (self.username, self.password)

def list_packages(
    project_name: str,
    credentials: Credentials,
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


def origin_was_updated(
    last_check: Timestamp,
    origin: Origin,
    credentials: Credentials,
    api_url: str = "https://api.opensuse.org",
) -> bool:
    """Check if an OBS package was changed since a known timestamp.

    :param last_check: Unix timestamp of the last check
    :param origin: OBS package to check
    :param credentials: OBS API credentials
    :param api_url: Base URL of the OBS API server, defaults to https://api.opensuse.org
    :return: True if the package was updated, False otherwise
    """
    response_text = _query_origin(
        origin=origin,
        credentials=credentials,
        api_url=api_url,
    )

    timestamps = _extract_package_timestamps(response_text)

    return _any_timestamp_is_newer(timestamps, last_check)


def _any_timestamp_is_newer(timestamps: List[Timestamp], base: Timestamp):
    return any(ts > base for ts in timestamps)


def _query_packages_list(
    project_name: str, credentials: Credentials, api_url: str
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


def _extract_package_timestamps(response_text) -> List[Timestamp]:
    if not response_text:
        return []

    root = ElementTree.fromstring(response_text)
    return [Timestamp(package.attrib["mtime"]) for package in root.findall("./entry")]


def _query_origin(
    origin: Origin,
    credentials: Credentials,
    api_url: str,
) -> str:
    try:
        url = f"{api_url}/source/{origin.project}/{origin.package}"
        response = requests.get(url, auth=credentials)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""
