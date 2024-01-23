from typing import Optional, Dict, Tuple

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock


class DeltaPCompiler:
    @staticmethod
    def __compile_expr(expr: Optional[str], tech: Tech) -> PExpr:
        # FIXME to fix this I need to extend GLITCH's IR
        if expr is None:
            return None
        return PEConst(PStr(expr))

    @staticmethod
    def __handle_attribute(
        attr_name: str,
        attributes: Dict[str, Tuple[PExpr, Attribute]],
        labeled_script: LabeledUnitBlock,
    ) -> PStatement:
        def process_var(attr: str):
            label = labeled_script.get_label(attributes[attr][1])
            var = f"{attr}-{label}"
            return label, var

        match attr_name:
            case "state":
                state_label, state_var = process_var("state")
                content_label, content_var = process_var("content")
                return PLet(
                    state_var,
                    attributes["state"][0],
                    state_label,
                    PIf(PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("present"))),
                        PLet(
                            content_var,
                            attributes["content"][0],
                            content_label,
                            PCreate(attributes["path"][0], PEVar(content_var)),
                        ),
                        PIf(PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("absent"))),
                            PRm(attributes["path"][0]),
                            PIf(PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("directory"))),
                                PMkdir(attributes["path"][0]),
                                PSkip()
                            )
                        )
                    )
                )
            case "owner":
                # TODO: this should use a is_defined
                owner_label, owner_var = process_var("owner")
                return PLet(
                    owner_var,
                    attributes["owner"][0],
                    owner_label,
                    PChown(attributes["path"][0], PEVar(owner_var)),
                )
            case "mode":
                # TODO: this should use a is_defined
                mode_label, mode_var = process_var("mode")
                return PLet(
                    mode_var,
                    attributes["mode"][0],
                    mode_label,
                    PChmod(attributes["path"][0], PEVar(mode_var)),
                )

        return None

    @staticmethod
    def compile(labeled_script: LabeledUnitBlock, tech: Tech) -> PStatement:
        statement = PSkip()
        script = labeled_script.script

        # TODO: Handle variables
        # TODO: Handle scopes
        for atomic_unit in script.atomic_units:
            type = NamesDatabase.get_au_type(atomic_unit.type, tech)
            attributes: Dict[str, Tuple[PExpr, Attribute]] = {}

            if type == "file":
                for attribute in atomic_unit.attributes:
                    attr_name = NamesDatabase.get_attr_name(attribute.name, type, tech)
                    if attr_name is not None:
                        attributes[attr_name] = (
                            DeltaPCompiler.__compile_expr(attribute.value, tech),
                            attribute,
                        )

                for attribute in atomic_unit.attributes:
                    attr_name = NamesDatabase.get_attr_name(attribute.name, type, tech)
                    attr_statement = DeltaPCompiler.__handle_attribute(
                        attr_name, attributes, labeled_script
                    )
                    if attr_statement is not None:
                        statement = PSeq(statement, attr_statement)

        return statement
