# SPDX-License-Identifier: GPL-3.0-or-later
from lubed import config
import textwrap
import pytest
import functools


@pytest.fixture
def oscrc_file(tmp_path):
    oscrc = tmp_path / ".oscrc"
    with oscrc.open("w") as f:
        f.write(
            textwrap.dedent(
                """\
            [general]
            [https://api.opensuse.org]
            user=myusername
            pass=mypassword
            """
            )
        )
    return str(oscrc)


@pytest.fixture
def oscrc_file_missing_password(tmp_path):
    oscrc = tmp_path / ".oscrc"
    with oscrc.open("w") as f:
        f.write(
            textwrap.dedent(
                """\
            [general]
            [https://api.opensuse.org]
            user=myusername
            """
            )
        )
    return str(oscrc)


def test_oscrc(oscrc_file, monkeypatch):
    monkeypatch.setenv("OSC_CONFIG", oscrc_file)

    assert config.oscrc("https://api.opensuse.org", "user") == "myusername"
    assert config.oscrc("https://api.opensuse.org", "pass") == "mypassword"


def test_oscrc_missing_credentials(oscrc_file_missing_password, monkeypatch):
    monkeypatch.setenv("OSC_CONFIG", oscrc_file_missing_password)

    with pytest.raises(config.OSCError):
        config.oscrc("https://api.opensuse.org", "user")
        config.oscrc("https://api.opensuse.org", "pass")
