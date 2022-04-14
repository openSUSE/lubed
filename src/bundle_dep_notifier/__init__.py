#!/usr/bin/python3
import os
import time
from . import collect

def real_test():
    # Poor man's integration test
    creds = collect.Credentials(os.getenv("OBSUSER", ""), os.getenv("OBSPASSWD", ""))
    test_origin = collect.Origin("home:agraul", "emacs-pgtk-nativecomp")
    print(collect.list_packages(test_origin.project, creds))
    assert (
        collect.origin_was_updated(collect.Timestamp(time.time()), test_origin, creds)
        is False
    )
    assert collect.origin_was_updated(collect.Timestamp(0), test_origin, creds) is True
