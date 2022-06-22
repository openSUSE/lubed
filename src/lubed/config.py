"""Interface to configuration files."""
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import textwrap
import pathlib
import configparser

import tomli


def load(filename: str) -> dict:
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return tomli.load(f)
    else:
        return {}


class OSCError(Exception):
    ...


def oscrc(apiurl: str, key: str) -> str:
    for file in (
        os.getenv("OSC_CONFIG", ""),
        "~/.oscrc",
        os.getenv("XDG_CONFI_HOME", "~/.config") + "/osc/oscrc",
    ):
        p = pathlib.Path(file)
        if p.exists():
            with p.open():
                osc_config = configparser.ConfigParser()
                osc_config.read(p)
                try:
                    return osc_config[apiurl][key]
                except KeyError as e:
                    raise OSCError(f"Key not in config: {e}")
    return ""


DEFAULTS = {
    "obs": {
        "api_baseurl": "https://api.opensuse.org",
        "bundle_project": "systemsmanagement:saltstack:bundle",
    },
    "github": {
        "repo": "SUSE/spacewalk",
        "column_id": 18813228,
        "issue": {
            "title": "Update Salt Bundle Depdencenies",
            "labels": ["ion-squad", "salt-bundle"],
            "body": textwrap.dedent(
                """\
        It's time to update all dependencies in the Salt Bundle.

        At the time of creating this card ($now), there have been these updates since $last_execution:

        $updates

        Please use `echo $last_execution_ts >.last_execution && lubed updates` for an up-to-date list.

        _This issue was generated automatically._
        """
            ),
        },
    },
}
