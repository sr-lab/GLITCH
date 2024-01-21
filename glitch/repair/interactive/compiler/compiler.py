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
        let = lambda attr_name, body: PLet(
            attr_name,
            attributes[attr_name][0],
            labeled_script.get_label(attributes[attr_name][1]),
            body,
        )

        match attr_name, attributes[attr_name][0]:
            case "state", PEConst(PStr("present")):
                return let(
                    attr_name,
                    let(
                        "content",
                        PCreate(attributes["path"][0], attributes["content"][0]),
                    ),
                )
            case "state", PEConst(PStr("absent")):
                return let(attr_name, PRm(attributes["path"][0]))
            case "state", PEConst(PStr("directory")):
                return let(attr_name, PMkdir(attributes["path"][0]))
            case "owner", _:
                return let(
                    attr_name, PChown(attributes["path"][0], attributes["owner"][0])
                )
            case "mode", _:
                return let(
                    attr_name, PChmod(attributes["path"][0], attributes["mode"][0])
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
