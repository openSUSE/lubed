import time

import click
import rich
import rich.table

from lubed import Package, Timestamp, obs, read_config


@click.group()
def cli():
    ...


@cli.command()
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default="config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--obs-username",
    envvar="OBSUSER",
    help="OBS API username, can be passed via the environment variable OBSUSER as well.",
)
@click.option(
    "--obs-password",
    envvar="OBSPASSWD",
    help="OBS API password, can be passed via the environment variable OBSPASSWD as well.",
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
def list_missing_packages(
    config_path, obs_username, obs_password, search_subprojects, exclude_subproject
) -> None:
    """List packages missing from the [origins] table in the config file."""
    conf = read_config(config_path)
    project_name = conf["bundle_project"]
    api_url = conf.get("api_baseurl", "https://api.opensuse.org")
    credentials = obs.OBSCredentials(obs_username, obs_password)
    projects = [project_name]
    if search_subprojects:
        projects.extend(obs.list_subprojects(project_name, credentials, api_url))

    project_packages = {}
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
    rich.print(table)


@cli.command()
@click.option(
    "--last-timestamp-file",
    type=click.Path(),
    default=".last_timestamp",
    help="File containing the last execution time in Unix time format.",
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False),
    default="config.toml",
    help="Config file location, TOML format",
)
@click.option(
    "--obs-username",
    envvar="OBSUSER",
    help="OBS API username, can be passed via the environment variable OBSUSER as well.",
)
@click.option(
    "--obs-password",
    envvar="OBSPASSWD",
    help="OBS API password, can be passed via the environment variable OBSPASSWD as well.",
)
@click.option(
    "--no-update-timestamp",
    default=False,
    flag_value=True,
    help="Do not update the last execution timestamp.",
)
def list_updated_packages(
    last_timestamp_file, config_path, obs_username, obs_password, no_update_timestamp
) -> None:
    """List all packages that were updated in their origin since last execution."""
    with open(last_timestamp_file, "r") as f:
        last_timestamp = Timestamp(f.read())
    conf = read_config(config_path)
    credentials = obs.OBSCredentials(obs_username, obs_password)

    table = rich.table.Table(title="Packages Updated in Origin")
    table.add_column("Bundle Package Name")
    table.add_column("Origin Project Name")
    table.add_column("Origin Package Name")

    packages = {
        bundle_name: Package(project=p["project"], name=p["package"])
        for bundle_name, p in conf["origins"].items()
    }

    for bundle_name, package in packages.items():
        if obs.package_was_updated(
            last_timestamp,
            package,
            credentials,
            conf.get("api_baseurl", "https://api.opensuse.org"),
        ):
            table.add_row(bundle_name, package.project, package.name)

    rich.print(table)
    if no_update_timestamp:
        exit(0)

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
    "--obs-username",
    envvar="OBSUSER",
    help="OBS API username, can be passed via the environment variable OBSUSER as well.",
)
@click.option(
    "--obs-password",
    envvar="OBSPASSWD",
    help="OBS API password, can be passed via the environment variable OBSPASSWD as well.",
)
@click.option(
    "--exclude-subproject",
    default=(),
    multiple=True,
    help="Exclude all subprojects that contain the specified string. Can be used multiple times.",
)
@click.argument("packages", nargs=-1)
def list_subprojects_for_packages(
    config_path, obs_username, obs_password, exclude_subproject, packages
) -> None:
    """List all subprojects that contain the specified packages."""
    conf = read_config(config_path)
    project_name = conf["bundle_project"]
    api_url = conf.get("api_baseurl", "https://api.opensuse.org")
    credentials = obs.OBSCredentials(obs_username, obs_password)
    projects = [project_name] + obs.list_subprojects(project_name, credentials, api_url)

    table = rich.table.Table()
    table.add_column("Package")
    table.add_column("Projects")

    for package in packages:
        for project in projects:
            if any(excluded in project for excluded in exclude_subproject):
                continue

            if obs.package_in_project(package, project, credentials, api_url):
                table.add_row(package, project)
    rich.print(table)


@cli.command()
@click.option("--last-timestamp-file", type=click.Path(), default=".last_timestamp")
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
            click.echo(f"Use --force to override {last_timestamp_file}.")
            exit(3)
    now = Timestamp(time.time())
    with open(last_timestamp_file, "w") as f:
        f.write(str(now))
