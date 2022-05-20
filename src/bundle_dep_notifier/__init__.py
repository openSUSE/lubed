#!/usr/bin/python3
import os
import time
from . import obs
import tomli


def read_config(filename: str) -> dict:
    with open(filename, "rb") as f:
        return tomli.load(f)

def real_test():
    # Poor man's integration test
    creds = obs.Credentials(os.getenv("OBSUSER", ""), os.getenv("OBSPASSWD", ""))
    test_origin = obs.Package("home:agraul", "emacs-pgtk-nativecomp")
    print(obs.list_packages(test_origin.project, creds))
    assert (
        obs.package_was_updated(obs.Timestamp(time.time()), test_origin, creds) is False
    )
    assert obs.package_was_updated(obs.Timestamp(0), test_origin, creds) is True
