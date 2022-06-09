"""CLI entrypoint to lubed."""
# SPDX-License-Identifier: GPL-3.0-or-later
import string
import os
import textwrap
import time
from collections import ChainMap
from datetime import datetime

import click
import rich.console
import rich.table

from lubed import OBSCredentials, Package, Timestamp, config, gh, obs

console = rich.console.Console()


@click.group()
def cli():
    ...


@cli.command()
@click.option("--last-timestamp-file", type=click.Path(), default=".last_execution")
@click.option(
    "--force",
    default=False,
    flag_value=True,
    help="Override existing --last-timestamp-file",
)
def init(last_timestamp_file, force):
    """Initialize the last-timestamp-file with the current time."""
    with open(last_timestamp_file, "r") as f:
        if f.read() and not force:
            console.print(f"Use --force to override {last_timestamp_file}.")
            exit(3)
    now = Timestamp(time.time())
    with open(last_timestamp_file, "w") as f:
        f.write(str(now))


@cli.command()
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default="config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--search-subprojects",
    default=False,
    flag_value=True,
    help="Include all subprojects.",
)
@click.option(
    "--exclude-subproject",
    default=(),
    multiple=True,
    help="Exclude all subprojects that contain the specified string. Can be used multiple times.",
)
def not_in_conf(config_path, search_subprojects, exclude_subproject) -> None:
    """List packages missing from the [origins] table in the config file."""
    conf = ChainMap(config.load(config_path), config.DEFAULTS)
    project_name = conf["obs"]["bundle_project"]
    api_url = conf["obs"]["api_baseurl"]
    obs_username = os.getenv("OBSUSER")
    obs_password = os.getenv("OBSPASSWD")
    try:
        if not obs_username:
            obs_username = config.oscrc(api_url, "user")

        if not obs_password:
            obs_password = config.oscrc(api_url, "pass")
    except config.OSCError as e:
        console.print(f"Can't fall back to oscrc for authentication:\n{e}")
        exit(5)

    credentials = OBSCredentials(obs_username, obs_password)

    with console.status("Gathering projects...", spinner="arc"):
        projects = [project_name]
        if search_subprojects:
            projects.extend(obs.list_subprojects(project_name, credentials, api_url))

    project_packages = {}
    with console.status("Gathering packages...", spinner="arc"):
        for project in projects:
            if any(excluded in project for excluded in exclude_subproject):
                continue
            project_packages.setdefault(project, []).extend(
                obs.list_packages(project, credentials, api_url)
            )

    table = rich.table.Table(
        title=f"Packages missing from {click.format_filename(config_path)}"
    )
    table.add_column("Project")
    table.add_column("Packages")

    for project, packages in project_packages.items():
        for package in packages:
            if package not in conf["origins"]:
                table.add_row(project, package)
    console.print(table)


@cli.command()
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default="config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--exclude-subproject",
    default=(),
    multiple=True,
    help="Exclude all subprojects that contain the specified string. Can be used multiple times.",
)
@click.argument("packages", nargs=-1)
def subprojects_containing(config_path, exclude_subproject, packages) -> None:
    """List all subprojects that contain the specified packages."""
    conf = ChainMap(config.load(config_path), config.DEFAULTS)
    project_name = conf["obs"]["bundle_project"]
    api_url = conf["obs"]["api_baseurl", "https://api.opensuse.org"]
    obs_username = os.getenv("OBSUSER")
    obs_password = os.getenv("OBSPASSWD")
    try:
        if not obs_username:
            obs_username = config.oscrc(api_url, "user")

        if not obs_password:
            obs_password = config.oscrc(api_url, "pass")
    except config.OSCError as e:
        console.print(f"Can't fall back to oscrc for authentication:\n{e}")
        exit(5)
    credentials = OBSCredentials(obs_username, obs_password)
    with console.status("Gathering projects...", spinner="arc"):
        projects = [project_name] + obs.list_subprojects(
            project_name, credentials, api_url
        )

    table = rich.table.Table()
    table.add_column("Package")
    table.add_column("Projects")

    with console.status("Checking projects for packages...", spinner="arc"):
        for package in packages:
            for project in projects:
                if any(excluded in project for excluded in exclude_subproject):
                    continue

                if obs.package_in_project(package, project, credentials, api_url):
                    table.add_row(package, project)
    console.print(table)


@cli.command()
@click.option(
    "--last-timestamp-file",
    type=click.Path(),
    default=".last_execution",
    help="File containing the last execution time in Unix time format.",
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default="config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--no-update-timestamp",
    default=False,
    flag_value=True,
    help="Do not update the last execution timestamp.",
)
def updates(last_timestamp_file, config_path, no_update_timestamp) -> None:
    """List all packages that were updated in their origin since last execution."""
    with open(last_timestamp_file, "r") as f:
        last_timestamp = Timestamp(f.read())
    conf = ChainMap(config.load(config_path), config.DEFAULTS)
    api_url = conf["obs"]["api_baseurl"]
    origins = conf["origins"]
    obs_username = os.getenv("OBSUSER")
    obs_password = os.getenv("OBSPASSWD")
    try:
        if not obs_username:
            obs_username = config.oscrc(api_url, "user")

        if not obs_password:
            obs_password = config.oscrc(api_url, "pass")
    except config.OSCError as e:
        console.print(f"Can't fall back to oscrc for authentication:\n{e}")
        exit(5)
    credentials = OBSCredentials(obs_username, obs_password)
    now = Timestamp(time.time())

    with console.status("Checking for updates...", spinner="arc"):
        updates = _calculate_updated_packages(
            last_timestamp, origins, credentials, api_url
        )

    table = rich.table.Table(title="Packages Updated in Origin")
    table.add_column("Bundle Package Name")
    table.add_column("Origin Project Name")
    table.add_column("Origin Package Name")
    for updated_package in updates:
        table.add_row(*updated_package)
    console.print(table)

    _maybe_update_timestamp(no_update_timestamp, last_timestamp_file, now)


@cli.command()
@click.option(
    "--last-timestamp-file",
    type=click.Path(),
    default=".last_execution",
    help="File containing the last execution time in Unix time format.",
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default="config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--gh-token",
    envvar="GHTOKEN",
    help="GitHub OAuth token, can be passed via the environment variable GHTOKEN",
)
def create_issue(last_timestamp_file, config_path, gh_token):
    """Create a GitHub issue which includes the list of needed updates."""
    with open(last_timestamp_file, "r") as f:
        last_timestamp = Timestamp(f.read())
    conf = ChainMap(config.load(config_path), config.DEFAULTS)
    api_url = conf["obs"]["api_baseurl"]
    gh_repo = conf["github"]["repo"]
    gh_column_id = conf["github"]["column_id"]
    issue_title = conf["github"]["issue"]["title"]
    issue_body_template = string.Template(conf["github"]["issue"]["body"])
    issue_labels = conf["github"]["issue"]["labels"]
    origins = conf["origins"]
    obs_username = os.getenv("OBSUSER")
    obs_password = os.getenv("OBSPASSWD")
    try:
        if not obs_username:
            obs_username = config.oscrc(api_url, "user")

        if not obs_password:
            obs_password = config.oscrc(api_url, "pass")
    except config.OSCError as e:
        console.print(f"Can't fall back to oscrc for authentication:\n{e}")
        exit(5)
    credentials = OBSCredentials(obs_username, obs_password)
    now = Timestamp(time.time())
    now_human_readable = datetime.utcfromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%S")
    last_execution_human_readable = datetime.utcfromtimestamp(last_timestamp).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    if not gh_token:
        console.print("Please provide a GitHub OAuth token")
        exit(4)

    with console.status("Checking for updates...", spinner="arc"):
        updates = _calculate_updated_packages(
            last_timestamp, origins, credentials, api_url
        )

    updates_header = textwrap.dedent(
        """\
        | Bundle Package Name | Origin Project Name | Origin Package Name |
        |---------------------|---------------------|---------------------|
        """
    )
    rows = [f"|{bundle}|{project}|{package}|" for bundle, project, package in updates]
    updates_str = updates_header + "\n".join(rows)

    issue_body = issue_body_template.substitute(
        {
            "last_execution": last_execution_human_readable,
            "updates": updates_str,
            "last_execution_ts": last_timestamp,
            "now": now_human_readable,
        }
    )

    with console.status("Creating issue...", spinner="arc"):
        url = gh.create_issue_in_board(
            repo_name=gh_repo,
            title=issue_title,
            body=issue_body,
            label_names=issue_labels,
            gh_token=gh_token,
            column_id=gh_column_id,
        )
    console.print(f"View the issue at {url}")


def _calculate_updated_packages(last_execution, origins, credentials, api_url):
    updates = []
    packages = {
        bundle_name: Package(project=p["project"], name=p["package"])
        for bundle_name, p in origins.items()
    }

    for bundle_name, package in packages.items():
        if obs.package_was_updated(last_execution, package, credentials, api_url):
            updates.append((bundle_name, package.project, package.name))

    return updates


def _maybe_update_timestamp(no_update_timestamp, last_timestamp_file, current_time):
    if no_update_timestamp:
        exit(0)

    with open(last_timestamp_file, "w") as f:
        f.write(str(current_time))
