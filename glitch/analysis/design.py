import json
import configparser
from glitch.analysis.rules import Error, RuleVisitor

from glitch.repr.inter import *

class DesignVisitor(RuleVisitor):
    @staticmethod
    def get_name() -> str:
        return "design"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        DesignVisitor.__EXEC = json.loads(config['design']['exec_atomic_units'])

    def check_module(self, m: Module) -> list[Error]:
        errors = super().check_module(m)
        # FIXME Needs to consider more things
        # if len(m.blocks) == 0:
        #     errors.append(Error('design_unnecessary_abstraction', m, m.path, repr(m)))
        return errors

    def check_unitblock(self, u: UnitBlock) -> list[Error]:
        def count_atomic_units(ub: UnitBlock):
            count_resources = len(ub.atomic_units)
            count_execs = 0
            for au in ub.atomic_units:
                if au.type in DesignVisitor.__EXEC:
                    count_execs += 1
            
            for unitblock in ub.unit_blocks:
                resources, execs = count_atomic_units(unitblock)
                count_resources += resources
                count_execs += execs

            return count_resources, count_execs

        errors = super().check_unitblock(u)
        total_resources, total_execs = count_atomic_units(u)

        if total_execs > 2 and (total_execs / total_resources) > 0.20:
            errors.append(Error('design_imperative_abstraction', u, u.path, repr(u)))

        # FIXME Needs to consider more things
        # if (len(u.statements) == 0 and len(u.atomic_units) == 0 and
        #         len(u.variables) == 0 and len(u.unit_blocks) == 0 and
        #             len(u.attributes) == 0):
        #     errors.append(Error('design_unnecessary_abstraction', u, u.path, repr(u)))

        return errors

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        return []

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return []

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return []

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        return []