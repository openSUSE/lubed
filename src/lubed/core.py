"""Core logic to compute the list of updated dependencies."""

from lubed import Package, config, git, obs


def calculate_updated_packages(last_execution, conf):
    api_url = conf["obs"]["api_baseurl"]
    gitserver_url = conf["obs"]["gitserver_baseurl"]
    git_managed_projects = conf["obs"]["git_managed_projects"]
    origins = conf["origins"]
    try:
        credentials = config.credentials(api_url)
    except config.OSCError as e:
        raise RuntimeError(
            f"Could not obtain credentials from osc config file:\n\t{e}"
        ) from e
    updates = []
    failures = []
    packages = {
        bundle_name: Package(
            project=p["project"],
            name=p["package"],
            git_managed=p["project"] in git_managed_projects,
        )
        for bundle_name, p in origins.items()
    }

    for bundle_name, package in packages.items():
        func = obs.package_was_updated
        if package.git_managed:
            func = git.package_was_updated

        updated, err = func(
            last_check=last_execution,
            package=package,
            credentials=credentials,
            api_url=api_url,
            gitserver_url=gitserver_url,
        )

        if err:
            failures.append((bundle_name, package.project, package.name))
        elif updated:
            updates.append((bundle_name, package.project, package.name))

    return updates, failures
