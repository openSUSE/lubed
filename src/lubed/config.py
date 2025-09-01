"""Interface to lubed configuration.

Most users of this module only need two functions:
- load(<filename>) to obtain the full config
- credentials(<apiurl>) to obtain OBS credentials for an API server
"""

# SPDX-License-Identifier: GPL-3.0-or-later

import configparser
import os
import pathlib

import tomli

from lubed import OBSCredentials


def load(filename: str) -> dict:
    """Read a TOML config file."""
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return tomli.load(f)
    else:
        return {}


def credentials(apiurl: str) -> OBSCredentials:
    """Read credentials from environment variables or an oscrc.

    The environment variables are:
    - OBSUSER for the username
    - OBSPASSWD for the password

    Reading from an oscrc only works if the password is listed in clear text. It's
    recommended to use environment variables.

    Args:
      apiurl: OBS API url, used to read the credentials from the correct section in an
        oscrc.
    Returns:
      OBSCredentials
    Raises:
      OSCError
    """
    obs_username = os.getenv("OBSUSER")
    obs_password = os.getenv("OBSPASSWD")
    if not obs_username:
        obs_username = oscrc(apiurl, "user")

    if not obs_password:
        obs_password = oscrc(apiurl, "pass")

    return OBSCredentials(obs_username, obs_password)


class OSCError(Exception):
    ...


def oscrc(apiurl: str, key: str) -> str:
    for file in (
        os.getenv("OSC_CONFIG"),
        "~/.oscrc",
        os.getenv("XDG_CONFIG_HOME", "~/.config") + "/osc/oscrc",
    ):
        if file is None:
            continue

        p = pathlib.Path(file).expanduser()
        if p.exists():
            with p.open(encoding="utf-8"):
                osc_config = configparser.ConfigParser()
                osc_config.read(p)
                try:
                    return osc_config[apiurl][key].strip()
                except KeyError as e:
                    raise OSCError(f"Key '{e}' not found in config.") from e
    else:
        raise OSCError("Could not find oscrc file.")
