from typing import Optional, Dict

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase

class Compiler:
    def __init__(self):
        pass

    def __compile_expr(self, expr: Optional[str], tech: Tech) -> PExpr:
        # FIXME to fix this I need to extend GLITCH's IR
        if expr is None:
            return None
        return PEConst(PStr(expr))

    def compile(self, script: UnitBlock, tech: Tech) -> PStatement:
        statement = PSkip()
        for atomic_unit in script.atomic_units:
            type = NamesDatabase.get_au_type(atomic_unit.type, tech)
            attributes: Dict[str, PExpr] = {}

            if type == "file":
                for attribute in atomic_unit.attributes:
                    attr_name = NamesDatabase.get_attr_name(attribute.name, type, tech)
                    if attr_name is not None:
                        attributes[attr_name] = self.__compile_expr(attribute.value, tech)

                if attributes["state"] == PEConst(PStr("present")):
                    statement = PSeq(statement, 
                                    PCreate(
                                        attributes["path"], 
                                        attributes["content"]
                                    )
                                )
                elif attributes["state"] == PEConst(PStr("absent")):
                    statement = PSeq(statement, PRm(attributes["path"]))
                elif attributes["state"] == PEConst(PStr("directory")):
                    statement = PSeq(statement, PMkdir(attributes["path"]))

                if attributes["owner"] is not None:
                    statement = PSeq(statement, PChown(attributes["path"], attributes["owner"]))
                if attributes["mode"] is not None:
                    statement = PSeq(statement, PChmod(attributes["path"], attributes["mode"]))
        
        return statement
                
                

