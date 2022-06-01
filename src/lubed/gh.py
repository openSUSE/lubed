"""Interact with GitHub and create issues"""
from typing import List
import github


def create_issue_in_board(
    repo_name: str,
    title: str,
    body: str,
    gh_token: str,
    column_id: str,
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
    :returns:

    """
    client = github.Github(gh_token)

    issue = _create_issue(
        repo_name,
        title,
        body,
        client,
        label_names,
    )
    _add_issue_to_column(issue, column_id, client)
    return issue.html_url


def _add_issue_to_column(issue, column_id, client):
    column = client.get_project_column(column_id)
    column.create_card(content_id=issue.id, content_type="Issue")


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
