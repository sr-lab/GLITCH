import json
import configparser
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker

from glitch.repr.inter import *

class DesignVisitor(RuleVisitor):
    class ImproperAlignmentSmell(SmellChecker):
        def check(self, element: AtomicUnit, file: str):
            identation = None
            improper_alignment = False
            for a in element.attributes:
                first_line = a.code.split("\n")[0]
                curr_id = len(first_line) - len(first_line.lstrip())

                if ("\t" in first_line):
                    improper_alignment = True
                    break
                elif (identation is None):
                    identation = curr_id
                elif (identation != curr_id):
                    improper_alignment = True
                    break

            if improper_alignment:
                return [Error('implementation_improper_alignment', element, file, repr(element))]

            return []
    
    class AnsibleImproperAlignmentSmell(SmellChecker):
        # YAML does not allow improper alignments (it also would have problems with generic attributes for all modules)
        def check(self, element: AtomicUnit, file: str):
            return []

    def __init__(self, tech) -> None:
        super().__init__(tech)
        if tech == "ansible":
            self.imp_align = DesignVisitor.AnsibleImproperAlignmentSmell()
        else:
            self.imp_align = DesignVisitor.ImproperAlignmentSmell()

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

        with open(u.path, "r") as f:
            if len(u.variables) / len(f.readlines()) > 0.5:
                errors.append(Error('implementation_too_many_variables', u, u.path, repr(u)))

        # FIXME Needs to consider more things
        # if (len(u.statements) == 0 and len(u.atomic_units) == 0 and
        #         len(u.variables) == 0 and len(u.unit_blocks) == 0 and
        #             len(u.attributes) == 0):
        #     errors.append(Error('design_unnecessary_abstraction', u, u.path, repr(u)))

        return errors

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file) + self.__check_lines(au, au.code, file)
        errors += self.imp_align.check(au, file)
        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return self.__check_lines(d, d.code, file)

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return self.__check_lines(a, a.code, file)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return self.__check_lines(v, v.code, file)

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        return self.__check_lines(c, c.code, file)

    def __check_lines(self, el, code, file):
        errors = []

        lines = code.split('\n')
        for l, line in enumerate(lines):
            if len(line) > 140:
                error = Error('implementation_long_statement', el, file, line)
                error.line = el.line + l
                errors.append(error)

        return errors