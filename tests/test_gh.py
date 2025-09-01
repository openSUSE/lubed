from lubed import gh
import textwrap


def test_format_table_md():
    updates = [
        ("saltbundlepy", "SUSE:SLE-15-SP6:Update", "python311"),
        ("saltbundlepy-cython", "SUSE:SLFO:Main", "python-Cython"),
    ]
    failures = [
        ("saltbundlepy-docker-pycreds", "openSUSE:Factory", "python-docker-pycreds")
    ]

    assert gh.format_updates_md(updates, failures) == textwrap.dedent(
        """\
        | Bundle Package Name | Origin Project Name | Origin Package Name |
        |---------------------|---------------------|---------------------|
        |saltbundlepy|SUSE:SLE-15-SP6:Update|python311|
        |saltbundlepy-cython|SUSE:SLFO:Main|python-Cython|

        Failed to check the following packages:
        | Bundle Package Name | Origin Project Name | Origin Package Name |
        |---------------------|---------------------|---------------------|
        |saltbundlepy-docker-pycreds|openSUSE:Factory|python-docker-pycreds|"""
    )
