from typing import Dict, Optional
from dataclasses import dataclass


class State:
    def is_dir(self) -> bool:
        return isinstance(self, Dir)

    def is_file(self) -> bool:
        return isinstance(self, File)

    def __str__(self) -> str:
        return self.__class__.__name__.lower()


@dataclass
class File(State):
    mode: Optional[str]
    owner: Optional[str]
    content: Optional[str]


@dataclass
class Dir(State):
    mode: Optional[str]
    owner: Optional[str]


@dataclass
class Nil(State):
    pass


class FileSystemState:
    def __init__(self):
        self.state: Dict[str, State] = {}
