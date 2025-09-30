"""CLI entrypoint to lubed."""

# SPDX-License-Identifier: GPL-3.0-or-later
import os
import string
import time
from contextlib import suppress
from datetime import datetime

import click
import rich.box
import rich.console
import rich.table

from lubed import Timestamp, config, core, gh, obs

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
    with suppress(FileNotFoundError), open(
        last_timestamp_file, "r", encoding="utf-8"
    ) as f:
        if f.read() and not force:
            console.print(f"Use --force to override {last_timestamp_file}.")
            exit(3)
    now = Timestamp(time.time())
    with open(last_timestamp_file, "w", encoding="utf-8") as f:
        f.write(str(now))


@cli.command()
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default=os.path.dirname(__file__) + "/config.toml",
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
    conf = config.load(config_path)
    project_name = conf["obs"]["bundle_project"]
    api_url = conf["obs"]["api_baseurl"]
    try:
        credentials = config.credentials(api_url)
    except config.OSCError as e:
        console.print(f"Can't fall back to oscrc for authentication:\n{e}")
        exit(5)

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
            if "venv-salt-minion" in project_packages[project]:
                project_packages[project].remove("venv-salt-minion")

    table = rich.table.Table(
        title=f"Packages missing from {click.format_filename(config_path)}",
        box=rich.box.SIMPLE,
    )
    table.add_column("Project")
    table.add_column("Package")

    for project, packages in project_packages.items():
        for package in packages:
            if package not in conf["origins"]:
                table.add_row(project, package)
    console.print(table)


@cli.command()
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default=os.path.dirname(__file__) + "/config.toml",
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
    conf = config.load(config_path)
    project_name = conf["obs"]["bundle_project"]
    api_url = conf["obs"]["api_baseurl"]
    try:
        credentials = config.credentials(api_url)
    except config.OSCError as e:
        console.print(f"Can't fall back to oscrc for authentication:\n{e}")
        exit(5)

    with console.status("Gathering projects...", spinner="arc"):
        projects = [project_name] + obs.list_subprojects(
            project_name, credentials, api_url
        )

    table = rich.table.Table(box=rich.box.SIMPLE)
    table.add_column("Package")
    table.add_column("Project")

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
    default=os.path.dirname(__file__) + "/config.toml",
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
    with open(last_timestamp_file, "r", encoding="utf-8") as f:
        last_timestamp = Timestamp(f.read())
    conf = config.load(config_path)
    now = Timestamp(time.time())

    with console.status("Checking for updates...", spinner="arc"):
        try:
            updated_pkgs, failures = core.calculate_updated_packages(
                last_execution=last_timestamp, conf=conf
            )
        except RuntimeError as e:
            console.print(e)
            exit(5)

    _print_table(title="Packages Updated in Origin", packages=updated_pkgs)

    if failures:
        _print_table(title="Packages that Failed to Check", packages=failures)

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
    default=os.path.dirname(__file__) + "/config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--gh-token",
    envvar="GHTOKEN",
    help="GitHub OAuth token, can be passed via the environment variable GHTOKEN",
)
@click.option(
    "--no-update-timestamp",
    default=False,
    flag_value=True,
    help="Do not update the last execution timestamp.",
)
def create_issue(last_timestamp_file, config_path, gh_token, no_update_timestamp):
    """Create a GitHub issue which includes the list of needed updates."""
    with open(last_timestamp_file, "r", encoding="utf-8") as f:
        last_timestamp = Timestamp(f.read())
    conf = config.load(config_path)
    gh_repo = conf["github"]["repo"]
    gh_project_board_id = conf["github"]["project_board_id"]
    issue_title = conf["github"]["issue"]["title"]
    issue_body_template = string.Template(conf["github"]["issue"]["body"])
    issue_labels = conf["github"]["issue"]["labels"]

    now = Timestamp(time.time())
    now_human_readable = datetime.utcfromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%S")
    last_execution_human_readable = datetime.utcfromtimestamp(last_timestamp).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    if not gh_token:
        console.print("Please provide a GitHub OAuth token")
        exit(4)

    with console.status("Checking for updates...", spinner="arc"):
        try:
            updated_pkgs, failures = core.calculate_updated_packages(
                last_execution=last_timestamp, conf=conf
            )
        except RuntimeError as e:
            console.print(e)
            exit(5)

    issue_body = issue_body_template.substitute(
        {
            "last_execution": last_execution_human_readable,
            "updates": gh.format_updates_md(updated_pkgs, failures),
            "last_execution_ts": last_timestamp,
            "now": now_human_readable,
        }
    )

    with console.status("Creating issue...", spinner="arc"):
        issue = gh.create_issue_in_board(
            repo_name=gh_repo,
            title=issue_title,
            body=issue_body,
            label_names=issue_labels,
            gh_token=gh_token,
            board_id=gh_project_board_id,
        )

    console.print(f"View the issue at {issue.html_url}")
    _maybe_update_timestamp(no_update_timestamp, last_timestamp_file, now)


def _maybe_update_timestamp(no_update_timestamp, last_timestamp_file, current_time):
    if no_update_timestamp:
        exit(0)

    with open(last_timestamp_file, "w", encoding="utf-8") as f:
        f.write(str(current_time))


def _print_table(title: str, packages: list):
    table = rich.table.Table(
        "Bundle Package Name",
        "Origin Project Name",
        "Origin Package Name",
        title=title,
        box=rich.box.SIMPLE,
    )
    for package in packages:
        table.add_row(*package)

    console.print(table)
