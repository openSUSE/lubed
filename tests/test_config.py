# SPDX-License-Identifier: GPL-3.0-or-later
from lubed import config
import textwrap
import pytest
import functools


def test_early_exit_missing_osc(monkeypatch):
    monkeypatch.setattr("lubed.config.HAS_OSC", False)

    with pytest.raises(config.OSCError):
        config.oscrc("https://api.opensuse.org", "user")


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
    return oscrc

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
    return oscrc


def test_oscrc(oscrc_file, monkeypatch):
    # inject the test oscrc into the osc.conf.get_config() call
    osc_get_config_testfile = functools.partial(
        config.osc.conf.get_config, override_conffile=oscrc_file
    )
    monkeypatch.setattr("lubed.config.osc.conf.get_config", osc_get_config_testfile)

    assert config.oscrc("https://api.opensuse.org", "user") == "myusername"
    assert config.oscrc("https://api.opensuse.org", "pass") == "mypassword"

def test_oscrc_missing_credentials(oscrc_file_missing_password, monkeypatch):
    # inject the test oscrc into the osc.conf.get_config() call
    osc_get_config_testfile = functools.partial(
        config.osc.conf.get_config, override_conffile=oscrc_file_missing_password
    )
    monkeypatch.setattr("lubed.config.osc.conf.get_config", osc_get_config_testfile)

    with pytest.raises(config.OSCError):
        config.oscrc("https://api.opensuse.org", "user")
        config.oscrc("https://api.opensuse.org", "pass")
