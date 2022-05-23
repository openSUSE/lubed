#!/usr/bin/python3
from dataclasses import dataclass

import tomli

Timestamp = int


@dataclass(frozen=True)
class Package:
    project: str
    name: str


@dataclass(frozen=True)
class OBSCredentials:
    username: str
    password: str

    def as_tuple(self):
        return (self.username, self.password)


def read_config(filename: str) -> dict:
    with open(filename, "rb") as f:
        return tomli.load(f)
