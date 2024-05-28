from typing import Dict
from glitch.repr.inter import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.tech import Tech
from glitch.repair.interactive.compiler.environment import DefinedAtomicUnitEnv


class LabeledUnitBlock:
    def __init__(self, script: UnitBlock, tech: Tech) -> None:
        """Initializes a new instance of a labeled unit block.

        Args:
            script (UnitBlock): The script being labeled.
            tech (Tech): The tech being considered.

        Returns:
            LabeledUnitBlock: The labeled unit block.
        """
        self.script = script
        self.tech: Tech = tech
        self.env: DefinedAtomicUnitEnv = DefinedAtomicUnitEnv(script)
        self.__label = 0
        self.__label_to_var: Dict[int, str] = {}
        self.__codeelement_to_label: Dict[CodeElement, int] = {}
        self.__label_to_codeelement: Dict[int, CodeElement] = {}
        self.__location: Dict[CodeElement, CodeElement] = {}

    def add_label(
        self, name: str, codeelement: CodeElement, sketched: bool = False
    ) -> int:
        """Adds a label to the code element with the given name.

        Args:
            name (str): The name of the code element.
            codeelement (CodeElement): The code element to be labeled.
            sketched (bool): Whether the code element is sketched.

        Returns:
            int: The label of the code element.
        """
        self.__codeelement_to_label[codeelement] = self.__label
        self.__label_to_codeelement[self.__label] = codeelement
        var = f"{name}-{self.__label}"
        if not sketched:
            self.__label_to_var[self.__label] = var
        else:
            self.__label_to_var[self.__label] = f"sketched-{var}"
        self.__label += 1
        return self.__label - 1

    def add_location(self, location: CodeElement, codeelement: CodeElement) -> None:
        """Defines where a code element is defined in the script.

        Args:
            sketch_location (CodeElement): The code element where the code element is defined.
            codeelement (CodeElement): The code element.
        """
        if isinstance(codeelement, BinaryOperation):
            self.add_location(location, codeelement.left)
            self.add_location(location, codeelement.right)
        self.__location[codeelement] = location

    def get_label(self, codeelement: CodeElement) -> int:
        """Returns the label of the code element.

        Args:
            codeelement (CodeElement): The code element.

        Returns:
            int: The label of the code element.
        """
        return self.__codeelement_to_label[codeelement]

    def has_label(self, codeelement: CodeElement) -> bool:
        """Returns whether the code element has a label.

        Args:
            codeelement (CodeElement): The code element.

        Returns:
            bool: Whether the code element has a label.
        """
        return codeelement in self.__codeelement_to_label

    def get_codeelement(self, label: int) -> CodeElement:
        """Returns the code element with the given label.

        Args:
            label (int): The label of the code element.

        Returns:
            CodeElement: The code element with the given label.
        """
        return self.__label_to_codeelement[label]

    def remove_label(self, codeelement: CodeElement) -> None:
        """Removes the label of the code element.

        Args:
            codeelement (CodeElement): The code element.
        """
        label = self.get_label(codeelement)
        del self.__codeelement_to_label[codeelement]
        del self.__label_to_codeelement[label]
        del self.__label_to_var[label]

    def get_var(self, label: int) -> str:
        """Returns the variable with the given label.

        Args:
            label (int): The label of the variable.
        """
        return self.__label_to_var[label]

    def get_location(self, codeelement: CodeElement) -> CodeElement:
        """Returns the location where the sketched code element is defined.

        Args:
            codeelement (CodeElement): The sketched code element.

        Returns:
            CodeElement: The location where the sketched code element is defined.
        """
        return self.__location[codeelement]


class GLITCHLabeler:
    @staticmethod
    def label_attribute(
        labeled: LabeledUnitBlock, atomic_unit: AtomicUnit, attribute: Attribute
    ) -> None:
        """Labels an attribute.

        Args:
            labeled (LabeledUnitBlock): The labeled script.
            atomic_unit (AtomicUnit): The attribute's atomic unit.
            attribute (Attribute): The attribute.
        """
        type = NamesDatabase.get_au_type(atomic_unit.type, labeled.tech)
        name = NamesDatabase.get_attr_name(attribute.name, type, labeled.tech)
        labeled.add_label(name, attribute)  # type: ignore

    @staticmethod
    def label_atomic_unit(labeled: LabeledUnitBlock, atomic_unit: AtomicUnit) -> None:
        """Labels an atomic unit.

        Args:
            labeled (LabeledUnitBlock): The labeled script.
            atomic_unit (AtomicUnit): The atomic unit.
        """
        for attribute in atomic_unit.attributes:
            GLITCHLabeler.label_attribute(labeled, atomic_unit, attribute)

    @staticmethod
    def label_variable(labeled: LabeledUnitBlock, variable: Variable) -> None:
        """Labels a variable.

        Args:
            labeled (LabeledUnitBlock): The labeled script.
            variable (Variable): The variable.
        """
        labeled.add_label(variable.name, variable)

    @staticmethod
    def label_conditional(
        labeled: LabeledUnitBlock, conditional: ConditionalStatement
    ) -> None:
        """Labels a conditional statement.

        Args:
            labeled (LabeledUnitBlock): The labeled script.
            conditional (ConditionalStatement): The conditional statement.
        """
        for statement in conditional.statements:
            GLITCHLabeler.label_statement(labeled, statement)
        if conditional.else_statement is not None:
            GLITCHLabeler.label_conditional(labeled, conditional.else_statement)

    @staticmethod
    def label_unit_block(labeled: LabeledUnitBlock, unit_block: UnitBlock) -> None:
        """Labels a unit block.

        Args:
            labeled (LabeledUnitBlock): The labeled script.
            unit_block (UnitBlock): The unit block.
        """
        for statement in unit_block.statements:
            GLITCHLabeler.label_statement(labeled, statement)
        for atomic_unit in unit_block.atomic_units:
            GLITCHLabeler.label_atomic_unit(labeled, atomic_unit)
        for variable in unit_block.variables:
            GLITCHLabeler.label_variable(labeled, variable)
        for unit_block in unit_block.unit_blocks:
            GLITCHLabeler.label_unit_block(labeled, unit_block)

    @staticmethod
    def label_statement(labeled: LabeledUnitBlock, statement: CodeElement) -> None:
        """Labels a statement.

        Args:
            labeled (LabeledUnitBlock): The labeled script.
            statement (CodeElement): The statement.
        """
        if isinstance(statement, AtomicUnit):
            GLITCHLabeler.label_atomic_unit(labeled, statement)
        elif isinstance(statement, ConditionalStatement):
            GLITCHLabeler.label_conditional(labeled, statement)
        elif isinstance(statement, Variable):
            GLITCHLabeler.label_variable(labeled, statement)
        elif isinstance(statement, UnitBlock):
            GLITCHLabeler.label_unit_block(labeled, statement)

    @staticmethod
    def label(script: UnitBlock, tech: Tech) -> LabeledUnitBlock:
        """Labels a script.

        Args:
            script (UnitBlock): The script being labeled.
            tech (Tech): The tech being considered.

        Returns:
            LabeledUnitBlock: The labeled script.
        """
        labeled = LabeledUnitBlock(script, tech)
        GLITCHLabeler.label_unit_block(labeled, script)
        return labeled
