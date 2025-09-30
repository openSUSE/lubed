"""Interact with GitHub and create issues"""

# SPDX-License-Identifier: GPL-3.0-or-later
import textwrap
from typing import Any, Dict, List

import github
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


def assign_issue_to_board(
    issue_id: str,
    board_id: str,
    gh_token: str,
) -> Dict[str, Any]:
    """Assign issue to a project board.

    :param issue_id: Issue Node ID.
    :param board_id: Github Board (V2) Node ID.
    :param gh_token: GitHub OAuth token.
    :returns: GraphQL execution result.
    """
    client = _get_gql_client(gh_token)
    link_issue_project_gql = gql(
        """
    mutation($issue_id: ID!, $board_id: ID!) {
      addProjectV2ItemById(input:{contentId:$issue_id,projectId:$board_id}) {
        item {
          id
        }
      }
    }
    """
    )
    return client.execute(
        link_issue_project_gql,
        variable_values={
            "issue_id": issue_id,
            "board_id": board_id,
        },
    )


def get_issue_node_id(issue_num: int, repo_name: str, gh_token: str) -> str:
    """Get Issue node ID based on the issue's number within a project.

    :param issue_num: Number of the issue in a repository (visible in the issue URL).
    :param repo_name: "owner/repo" of the GitHub repo of the issue.
    :param gh_token: GitHub OAuth token.
    :returns: Issue Node ID useful for Github GraphQL API queries.
    """
    client = _get_gql_client(gh_token)
    issue_number_to_id = gql(
        """
    query getIssueId ($num: Int!, $owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $num) {
          id
        }
      }
    }
    """
    )

    owner, repo = repo_name.split("/")
    resp = client.execute(
        issue_number_to_id,
        variable_values={"owner": owner, "repo": repo, "num": issue_num},
    )

    return resp["repository"]["issue"]["id"]


def create_issue_in_board(
    repo_name: str,
    title: str,
    body: str,
    gh_token: str,
    board_id: str,
    label_names: List[str] = None,
):
    """Create an issue and add it to a column on a project board.

    :param repo_name: "owner/repo" of the GitHub repo that the issues will be created in.
    :param title: Issue title.
    :param body: Issue body.
    :param label_names: List of names of issue labels that are put on the newly created issue.
    :param gh_token: GitHub OAuth token.
    :param column_id: Id of the column that the issue will be added to. Click on
        the three dots on a column and copy its URL to see the unique id.
    :returns: :class:`github.Issue.Issue`

    """
    client = github.Github(gh_token)

    issue = _create_issue(
        repo_name,
        title,
        body,
        client,
        label_names,
    )

    issue_node_id = get_issue_node_id(issue.number, repo_name, gh_token)
    assign_issue_to_board(issue_node_id, board_id, gh_token)

    return issue


def _get_gql_client(gh_token: str):
    return Client(
        transport=AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={
                "Authorization": f"bearer {gh_token}",
                "Accept": "application/vnd.github.bane-preview+json",
            },
        ),
        fetch_schema_from_transport=True,
    )


def _create_issue(
    repo_name: str,
    title: str,
    body: str,
    client: github.Github,
    label_names: List[str] = None,
):
    if label_names is None:
        label_names = []

    repo = client.get_repo(repo_name)
    labels = [repo.get_label(l) for l in label_names]
    return repo.create_issue(title=title, body=body, labels=labels)


def format_updates_md(updates, failures):
    updates_header = textwrap.dedent(
        """\
        | Bundle Package Name | Origin Project Name | Origin Package Name |
        |---------------------|---------------------|---------------------|
        """
    )
    rows = [f"|{bundle}|{project}|{package}|" for bundle, project, package in updates]
    updates_str = updates_header + "\n".join(rows)

    if failures:
        rows = [
            f"|{bundle}|{project}|{package}|" for bundle, project, package in failures
        ]
        updates_str += "\n\n" + "Failed to check the following packages:\n"
        updates_str += updates_header
        updates_str += "\n".join(rows)
    return updates_str
