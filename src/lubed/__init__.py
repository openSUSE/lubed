"""Common data structurs for package lubed."""
# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass

Timestamp = int


@dataclass(frozen=True)
class Package:
    project: str
    name: str
    git_managed: bool


@dataclass(frozen=True)
class OBSCredentials:
    username: str
    password: str

    def as_tuple(self):
        return (self.username, self.password)
