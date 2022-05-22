import os
from abc import ABC, abstractmethod

from glitch.repr.inter import *

class Stats(ABC):
    def compute(self, c):
        if isinstance(c, Project):
            self.compute_project(c)
        elif isinstance(c, Module):
            self.compute_module(c)
        elif isinstance(c, UnitBlock):
            self.compute_unitblock(c)
        if isinstance(c, AtomicUnit):
            self.compute_atomicunit(c)
        elif isinstance(c, Dependency):
            self.compute_dependency(c)
        elif isinstance(c, Attribute):
            self.compute_attribute(c)
        elif isinstance(c, Variable):
            self.compute_variable(c)
        elif isinstance(c, ConditionStatement):
            self.compute_condition(c)
        elif isinstance(c, Comment):
            self.compute_comment(c)
        elif isinstance(c, dict):
            for k, v in c.items():
                self.compute(k)
                self.compute(v)

    @abstractmethod
    def compute_project(self, p: Project):
        pass

    @abstractmethod
    def compute_module(self, m: Module):
        pass

    @abstractmethod
    def compute_unitblock(self, u: UnitBlock):
        pass

    @abstractmethod
    def compute_atomicunit(self, au: AtomicUnit):
        pass

    @abstractmethod
    def compute_dependency(self, d: Dependency):
        pass

    @abstractmethod
    def compute_attribute(self, a: Attribute):
        pass

    @abstractmethod
    def compute_variable(self, v: Variable):
        pass

    @abstractmethod
    def compute_condition(self, c: ConditionStatement):
        pass

    @abstractmethod
    def compute_comment(self, c: Comment):
        pass

class FileStats(Stats):
    def __init__(self) -> None:
        super().__init__()
        self.files = set()
        self.loc = 0

    def compute_project(self, p: Project):
        for m in p.modules:
            self.compute(m)
        for u in p.blocks:
            self.compute(u)

    def compute_module(self, m: Module):
        for u in m.blocks:
            self.compute(u)
        if os.path.isfile(m.path) and m.path not in self.files:
            self.files.add(m.path)
            with open(m.path, "r") as f:
                self.loc += len(f.readlines())

    def compute_unitblock(self, u: UnitBlock):
        for ub in u.unit_blocks:
            self.compute(ub)
        if os.path.isfile(u.path) and u.path not in self.files:
            self.files.add(u.path)
            with open(u.path, "r") as f:
                try:
                    self.loc += len(f.readlines())
                except UnicodeDecodeError:
                    pass

    def compute_atomicunit(self, au: AtomicUnit):
        pass

    def compute_dependency(self, d: Dependency):
        pass

    def compute_attribute(self, a: Attribute):
        pass

    def compute_variable(self, v: Variable):
        pass

    def compute_condition(self, c: ConditionStatement):
        pass

    def compute_comment(self, c: Comment):
        pass