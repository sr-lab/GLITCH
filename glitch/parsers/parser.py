import os
from glitch.repr.inter import *
from abc import ABC, abstractmethod
from typing import Optional

from glitch.repr.inter import UnitBlockType


class Parser(ABC):
    def parse(
        self, path: str, type: UnitBlockType, is_module: bool
    ) -> Optional[Module | Project | UnitBlock]:
        if is_module:
            return self.parse_module(path)
        elif os.path.isfile(path):
            return self.parse_file(path, type)
        else:
            return self.parse_folder(path)

    @abstractmethod
    def parse_file(self, path: str, type: UnitBlockType) -> Optional[UnitBlock]:
        pass

    @abstractmethod
    def parse_folder(self, path: str) -> Project:
        pass

    @abstractmethod
    def parse_module(self, path: str) -> Module:
        pass

    def parse_file_structure(self, folder: Folder, path: str) -> None:
        for f in os.listdir(path):
            if os.path.islink(os.path.join(path, f)):
                continue
            elif os.path.isfile(os.path.join(path, f)):
                folder.add_file(File(f))
            elif os.path.isdir(os.path.join(path, f)):
                new_folder = Folder(f)
                self.parse_file_structure(new_folder, os.path.join(path, f))
                folder.add_folder(new_folder)
