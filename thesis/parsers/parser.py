import os
from thesis.repr.inter import *
from abc import ABC, abstractmethod

class Parser(ABC):
    @abstractmethod
    def parse(self, path: str) -> Module:
        pass

    def parse_file_structure(self, folder, path):
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                folder.add_file(File(f))
            elif os.path.isdir(os.path.join(path, f)):
                new_folder = Folder(f)
                self.parse_file_structure(new_folder, os.path.join(path, f))
                folder.add_folder(new_folder)