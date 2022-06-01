from dataclasses import dataclass

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
