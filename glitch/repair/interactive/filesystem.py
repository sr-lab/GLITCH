from typing import Dict
from dataclasses import dataclass

class State:
    def is_dir(self) -> bool:
        return isinstance(self, Dir)
    
    def is_file(self) -> bool:
        return isinstance(self, File)


@dataclass
class File(State):
    mode: str
    owner: str
    content: str


@dataclass
class Dir(State):
    mode: str
    owner: str


@dataclass
class Nil(State):
    pass


class FileSystemState:
    def __init__(self):
        self.state: Dict[str, State] = {}