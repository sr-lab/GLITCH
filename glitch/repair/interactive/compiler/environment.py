from typing import Dict
from glitch.repr.inter import *


class DefinedAtomicUnitEnv:
    def __init__(self, unit_block: UnitBlock) -> None:
        self.__atomic_units: Dict[str, UnitBlock] = {}
        self.__collect_definitions(unit_block)
        
    def __collect_definitions(self, unit_block: UnitBlock) -> None:
        for ub in unit_block.unit_blocks:
            if ub.type == UnitBlockType.definition:
                assert ub.name is not None
                self.__atomic_units[ub.name] = ub
                self.__collect_definitions(ub)  

    def has_definition(self, name: str) -> bool:
        return name in self.__atomic_units