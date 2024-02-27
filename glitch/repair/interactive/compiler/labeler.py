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
        self.__sketch_location: Dict[CodeElement, CodeElement] = {}

    def add_label(
        self, name: str, codeelement: CodeElement, sketched: bool = False
    ) -> int:
        self.__codeelement_to_label[codeelement] = self.__label
        self.__label_to_codeelement[self.__label] = codeelement
        var = f"{name}-{self.__label}"
        if not sketched:
            self.__label_to_var[self.__label] = var
        else:
            self.__label_to_var[self.__label] = f"sketched-{var}"
        self.__label += 1
        return self.__label - 1
    
    def add_sketch_location(
        self, sketch_location: CodeElement, codeelement: CodeElement
    ):
        self.__sketch_location[codeelement] = sketch_location

    def get_label(self, codeelement: CodeElement) -> int:
        return self.__codeelement_to_label[codeelement]

    def get_codeelement(self, label: int) -> CodeElement:
        return self.__label_to_codeelement[label]

    def get_var(self, label: int) -> str:
        return self.__label_to_var[label]
    
    def get_sketch_location(self, codeelement: CodeElement) -> CodeElement:
        return self.__sketch_location[codeelement]


class GLITCHLabeler:
    def label_atomic_unit(
        labeled: LabeledUnitBlock, atomic_unit: AtomicUnit, tech: Tech
    ):
        type = NamesDatabase.get_au_type(atomic_unit.type, tech)
        for attribute in atomic_unit.attributes:
            name = NamesDatabase.get_attr_name(attribute.name, type, tech)
            labeled.add_label(name, attribute)

    def label_variable(labeled: LabeledUnitBlock, variable: Variable):
        labeled.add_label(variable.name, variable)

    def label_conditional(
        labeled: LabeledUnitBlock, conditional: ConditionStatement, tech: Tech
    ):
        for statement in conditional.statements:
            if isinstance(statement, AtomicUnit):
                GLITCHLabeler.label_atomic_unit(labeled, statement, tech)
            elif isinstance(statement, ConditionStatement):
                GLITCHLabeler.label_conditional(labeled, statement, tech)
            elif isinstance(statement, Variable):
                GLITCHLabeler.label_variable(labeled, statement)

        if conditional.else_statement is not None:
            GLITCHLabeler.label_conditional(
                labeled, conditional.else_statement, tech
            )

    @staticmethod
    def label(script: UnitBlock, tech: Tech) -> LabeledUnitBlock:
        labeled = LabeledUnitBlock(script)

        for statement in script.statements:
            if isinstance(statement, ConditionStatement):
                GLITCHLabeler.label_conditional(labeled, statement, tech)

        for atomic_unit in script.atomic_units:
            GLITCHLabeler.label_atomic_unit(labeled, atomic_unit, tech)

        for variable in script.variables:
            GLITCHLabeler.label_variable(labeled, variable)

        return labeled
