from typing import Dict
from glitch.repr.inter import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.tech import Tech


class LabeledUnitBlock:
    def __init__(self, script: UnitBlock):
        self.script = script
        self.__label = 0
        self.__label_to_var: Dict[int, str] = {}
        self.__codeelement_to_label: Dict[CodeElement, int] = {}
        self.__label_to_codeelement: Dict[int, CodeElement] = {}

    def add_label(self, name: str, codeelement: CodeElement, sketched: bool = False) -> int:
        self.__codeelement_to_label[codeelement] = self.__label
        self.__label_to_codeelement[self.__label] = codeelement
        var = f"{name}-{self.__label}"
        if not sketched:
            self.__label_to_var[self.__label] = var
        else:
            self.__label_to_var[self.__label] = f"sketched-{var}"
        self.__label += 1
        return self.__label - 1

    def get_label(self, codeelement: CodeElement) -> int:
        return self.__codeelement_to_label[codeelement]

    def get_codeelement(self, label: int) -> CodeElement:
        return self.__label_to_codeelement[label]

    def get_var(self, label: int) -> str:
        return self.__label_to_var[label]


class GLITCHLabeler:
    @staticmethod
    def label(script: UnitBlock) -> LabeledUnitBlock:
        labeled = LabeledUnitBlock(script)

        for atomic_unit in script.atomic_units:
            for attribute in atomic_unit.attributes:
                # FIXME: Puppet
                name = NamesDatabase.get_attr_name(attribute.name, atomic_unit.type, Tech.puppet)
                labeled.add_label(name, attribute)

        for variable in script.variables:
            labeled.add_label(variable.name, variable)

        return labeled
