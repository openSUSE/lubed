"""Interface to configuration files."""
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import textwrap

import tomli

try:
    import osc.conf
    import osc.oscerr

    HAS_OSC = True
except ImportError:
    HAS_OSC = False


def load(filename: str) -> dict:
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return tomli.load(f)
    else:
        return {}


class OSCError(Exception):
    ...


def oscrc(apiurl: str, key: str) -> str:
    if not HAS_OSC:
        raise OSCError("Can't import osc")

    try:
        osc.conf.get_config()
    except osc.oscerr.ConfigMissingCredentialsError:
        raise OSCError("No credentials available.")

    return osc.conf.config["api_host_options"][apiurl][key]


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
