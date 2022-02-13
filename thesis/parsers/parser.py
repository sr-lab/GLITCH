from thesis.repr.inter import *
from abc import ABC, abstractmethod

class Parser(ABC):
    @abstractmethod
    def parse(self, path: str) -> Module:
        pass

