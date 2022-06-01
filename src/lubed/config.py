import tomli
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
        "bundle_project": "systemsmanagement:saltstack:bundle"
    },
    "github": {
        "repo": "SUSE/spacewalk",
        "column_id": 18813228
    }
}
