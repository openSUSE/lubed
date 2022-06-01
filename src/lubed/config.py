import tomli
import textwrap
import os


def load(filename: str) -> dict:
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return tomli.load(f)
    else:
        return {}


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
