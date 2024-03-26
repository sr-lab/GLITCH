from typing import Optional, Dict, Tuple

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock
from glitch.repair.interactive.values import DefaultValue


class DeltaPCompiler:
    _sketched = -1
    _condition = 0

    class __Attributes:
        def __init__(self, au_type: str, tech: Tech) -> None:
            self.au_type = NamesDatabase.get_au_type(au_type, tech)
            self.__tech = tech
            self.__attributes: Dict[str, Tuple[PExpr, Attribute]] = {}

        def add_attribute(self, attribute: Attribute) -> None:
            attr_name = NamesDatabase.get_attr_name(
                attribute.name, self.au_type, self.__tech
            )

            self.__attributes[attr_name] = (  # type: ignore
                DeltaPCompiler._compile_expr(
                    NamesDatabase.get_attr_value(
                        attribute.value,  # type: ignore
                        attr_name,
                        self.au_type,
                        self.__tech,
                    ),
                    self.__tech,
                ),
                attribute,
            )

        def get_attribute(self, attr_name: str) -> Optional[Attribute]:
            return self.__attributes.get(attr_name, (None, None))[1]

        def get_attribute_value(self, attr_name: str) -> PExpr:
            default = PEUndef()
            if attr_name == "state":
                default = DefaultValue.DEFAULT_STATE
            elif attr_name == "mode":
                default = DefaultValue.DEFAULT_MODE
            elif attr_name == "owner":
                default = DefaultValue.DEFAULT_OWNER
            elif attr_name == "content":
                default = DefaultValue.DEFAULT_CONTENT

            return self.__attributes.get(attr_name, (default, None))[0]

        def __getitem__(self, key: str) -> PExpr:
            return self.get_attribute_value(key)

        def create_label_var_pair(
            self,
            attr_name: str,
            atomic_unit: AtomicUnit,
            labeled_script: LabeledUnitBlock,
        ) -> Tuple[int, str]:
            attr = self.get_attribute(attr_name)

            if attr is not None:
                label = labeled_script.get_label(attr)
            else:
                # Creates sketched attribute
                if attr_name == "state" and isinstance(
                    DefaultValue.DEFAULT_STATE.const, PStr
                ):  # HACK
                    attr = Attribute(
                        attr_name, DefaultValue.DEFAULT_STATE.const.value, False
                    )
                else:
                    attr = Attribute(attr_name, PEUndef(), False)  # type: ignore

                attr.line, attr.column = (
                    DeltaPCompiler._sketched,
                    DeltaPCompiler._sketched,
                )
                DeltaPCompiler._sketched -= 1
                labeled_script.add_sketch_location(atomic_unit, attr)
                self.add_attribute(attr)
                label = labeled_script.add_label(attr_name, attr, sketched=True)

            return label, labeled_script.get_var(label)

    @staticmethod
    def _compile_expr(expr: Optional[str], tech: Tech) -> Optional[PExpr]:
        # FIXME to fix this I need to extend GLITCH's IR
        if expr is None:
            return None
        if isinstance(expr, PEUndef):
            return expr

        return PEConst(PStr(expr))

    @staticmethod
    def __handle_file(
        atomic_unit: AtomicUnit,
        attributes: __Attributes,
        labeled_script: LabeledUnitBlock,
    ) -> PStatement:
        path = attributes["path"]
        # The path may be defined as the name of the atomic unit
        if path == PEUndef():
            path = PEConst(PStr(atomic_unit.name))  # type: ignore

        state_label, state_var = attributes.create_label_var_pair(
            "state", atomic_unit, labeled_script
        )
        statement = PLet(
            state_var,
            attributes["state"],
            state_label,
            PIf(
                PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("present"))),
                PCreate(path),
                PIf(
                    PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("absent"))),
                    PRm(path),
                    PIf(
                        PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("directory"))),
                        PMkdir(path),
                        PSkip(),
                    ),
                ),
            ),
        )

        content_label, content_var = attributes.create_label_var_pair(
            "content", atomic_unit, labeled_script
        )
        statement = PSeq(
            statement,
            PLet(
                content_var,
                attributes["content"],
                content_label,
                PWrite(path, PEVar(content_var)),
            ),
        )

        owner_label, owner_var = attributes.create_label_var_pair(
            "owner", atomic_unit, labeled_script
        )
        statement = PSeq(
            statement,
            PLet(
                owner_var,
                attributes["owner"],
                owner_label,
                PChown(path, PEVar(owner_var)),
            ),
        )

        mode_label, mode_var = attributes.create_label_var_pair(
            "mode", atomic_unit, labeled_script
        )
        statement = PSeq(
            statement,
            PLet(
                mode_var,
                attributes["mode"],
                mode_label,
                PChmod(path, PEVar(mode_var)),
            ),
        )

        return statement

    @staticmethod
    def __handle_atomic_unit(
        statement: PStatement,
        atomic_unit: AtomicUnit,
        tech: Tech,
        labeled_script: LabeledUnitBlock,
    ) -> PStatement:
        attributes: DeltaPCompiler.__Attributes = DeltaPCompiler.__Attributes(
            atomic_unit.type, tech
        )
        if attributes.au_type == "file":
            for attribute in atomic_unit.attributes:
                attributes.add_attribute(attribute)
            statement = PSeq(
                statement,
                DeltaPCompiler.__handle_file(atomic_unit, attributes, labeled_script),
            )
        return statement

    @staticmethod
    def __handle_conditional(
        conditional: ConditionalStatement, tech: Tech, labeled_script: LabeledUnitBlock
    ) -> PStatement:
        body = PSkip()
        for stat in conditional.statements:
            if isinstance(stat, AtomicUnit):
                body = DeltaPCompiler.__handle_atomic_unit(
                    body, stat, tech, labeled_script
                )
            elif isinstance(stat, ConditionalStatement):
                body = PSeq(
                    body,
                    DeltaPCompiler.__handle_conditional(stat, tech, labeled_script),
                )

        else_statement = PSkip()
        if conditional.else_statement is not None:
            else_statement = DeltaPCompiler.__handle_conditional(
                conditional.else_statement, tech, labeled_script
            )

        DeltaPCompiler._condition += 1
        return PIf(
            # FIXME: This creates a placeholder since we will branch every time
            # There are cases that we can infer the value of the condition
            # The creation of these variables should be done in the solver
            PEVar(f"dejavu-condition-{DeltaPCompiler._condition}"),
            body,
            else_statement,
        )

    @staticmethod
    def compile(labeled_script: LabeledUnitBlock, tech: Tech) -> PStatement:
        statement = PSkip()
        script = labeled_script.script

        # TODO: Handle variables
        # TODO: Handle scopes
        # TODO: The statements will not be in the correct order

        for stat in script.statements:
            if isinstance(stat, ConditionalStatement):
                statement = PSeq(
                    statement,
                    DeltaPCompiler.__handle_conditional(stat, tech, labeled_script),
                )

        for atomic_unit in script.atomic_units:
            statement = DeltaPCompiler.__handle_atomic_unit(
                statement, atomic_unit, tech, labeled_script
            )

        return statement
