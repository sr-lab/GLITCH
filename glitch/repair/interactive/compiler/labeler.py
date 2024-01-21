from typing import Dict
from glitch.repr.inter import *


class LabeledUnitBlock:
    def __init__(self, script: UnitBlock):
        self.script = script
        self.__label = 0
        self.__codeelement_to_label: Dict[CodeElement, int] = {}
        self.__label_to_codeelement: Dict[int, CodeElement] = {}

    def add_label(self, codeelement: CodeElement):
        self.__codeelement_to_label[codeelement] = self.__label
        self.__label_to_codeelement[self.__label] = codeelement
        self.__label += 1

    def get_label(self, codeelement: CodeElement) -> int:
        return self.__codeelement_to_label[codeelement]
    
    def get_codeelement(self, label: int) -> CodeElement:
        return self.__label_to_codeelement[label]


class GLITCHLabeler:
    @staticmethod
    def label(script: UnitBlock) -> LabeledUnitBlock:
        labeled = LabeledUnitBlock(script)

        for atomic_unit in script.atomic_units:
            for attribute in atomic_unit.attributes:
                labeled.add_label(attribute)

        for variable in script.variables:
            labeled.add_label(variable)

        return labeled