import textwrap

import pytest
from bundle_dep_notifier import collect


def test_parse_packages_response():
    example_response = textwrap.dedent(
        """\
        <directory count="2">
          <entry name="saltbundlepy"/>
          <entry name="saltbundlepy-cffi"/>
        </directory>
        """
    )

    assert collect._parse_packages_list(example_response) == [
        "saltbundlepy",
        "saltbundlepy-cffi",
    ]


@pytest.mark.parametrize(
    "last_check, expected", [(1000000000, True), (1700000000, False)])
def test_origin_was_update(last_check, expected):
    """The helper functions are called directly to avoid mocking."""
    example_response = textwrap.dedent(
        """\
        <directory name="salt" rev="404" vrev="12" srcmd5="bacfa8d9d6ac4edb6ac9388b54124e40">
          <serviceinfo code="succeeded" xsrcmd5="96cc430e75196ba3e6a0dab0658745e9"/>
          <entry name="3003.3-do-not-consider-skipped-targets-as-failed-for.patch" md5="386019f639fd0439a541a406cb996710" size="86662" mtime="1642780451"/>
          <entry name="3003.3-postgresql-json-support-in-pillar-423.patch" md5="6c20e166b0f636f47c6e72021307c316" size="41885" mtime="1642780451"/>
          <entry name="README.SUSE" md5="e654f059e54eafcb3bb1a9f77f6bc5e1" size="1086" mtime="1439233248"/>
          <entry name="_lastrevision" md5="62f7056590a6f08d79d9f3685b001319" size="40" mtime="1649762596"/>
          <entry name="_service" md5="fbd2103eae683a56776169d87ea1e897" size="742" mtime="1643196556"/>
        </directory>
        """
    )
    timestamps = collect._extract_package_timestamps(example_response)

    assert timestamps == [
        1642780451,
        1642780451,
        1439233248,
        1649762596,
        1643196556,
    ]

    assert collect._any_timestamp_is_newer(timestamps, last_check) == expected
