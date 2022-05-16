from cmath import inf
import json
import re
import configparser
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker
from glitch.helpers import kmp_search
from glitch.tech import Tech

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

    def __init__(self, tech: Tech) -> None:
        super().__init__(tech)
        if tech == Tech.ansible:
            self.imp_align = DesignVisitor.AnsibleImproperAlignmentSmell()
        else:
            self.imp_align = DesignVisitor.ImproperAlignmentSmell()
        self.variables_names = []
        self.first_code_line = inf

    @staticmethod
    def get_name() -> str:
        return "design"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        DesignVisitor.__EXEC = json.loads(config['design']['exec_atomic_units'])
        DesignVisitor.__VAR_REFER_SYMBOL = json.loads(config['design']['var_refer_symbol'])

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

        self.variables_names = []
        self.__check_code(u)
        errors = super().check_unitblock(u)
        total_resources, total_execs = count_atomic_units(u)

        if total_execs > 2 and (total_execs / total_resources) > 0.20:
            errors.append(Error('design_imperative_abstraction', u, u.path, repr(u)))

        with open(u.path, "r") as f:
            code_lines = f.readlines()
            if len(u.variables) / len(code_lines) > 0.5:
                errors.append(Error('implementation_too_many_variables', u, u.path, repr(u)))

            if DesignVisitor.__VAR_REFER_SYMBOL != "":
                # FIXME could be improved if we considered strings as part of the model
                for i, l in enumerate(code_lines):
                    for tuple in re.findall(r'(\".*\")|(\'.*\')', l):
                        for string in tuple:
                            for var in self.variables_names:
                                if (DesignVisitor.__VAR_REFER_SYMBOL + var) in string[1:-1].split(' '):
                                    error = Error('implementation_unguarded_variable', u, u.path, string)
                                    error.line = i + 1
                                    errors.append(error)

            def get_line(i ,lines):
                for j, line in lines:
                    if i < j:
                        return line
            
            f.seek(0, 0)
            all_code = f.read()
            code = ""

            lines = []
            current_line = 1
            i = 0
            for c in all_code:
                if c == '\n':
                    lines.append((i, current_line))
                    current_line += 1
                elif not c.isspace():
                    code += c
                    i += 1

            size = len(code)
            checked = []
            i = 0
            while i < size - 150:
                if (i + 150) in checked:
                    i += 1
                    continue

                pattern = code[i : i + 150]
                found = kmp_search(pattern, code[i + 150:])
                if len(found) > 0:
                    line = get_line(i, lines)
                    error = Error('design_duplicate_block', u, u.path, code_lines[line - 1])
                    error.line = line
                    errors.append(error)

                    for f in found:
                        line = get_line(f + i + 150, lines)
                        error = Error('design_duplicate_block', u, u.path, code_lines[line - 1])
                        error.line = line
                        errors.append(error)
                        checked += list(range(f + i + 150, f + i + 300))

                    i += 150
                else:
                    i += 1

        # FIXME Needs to consider more things
        # if (len(u.statements) == 0 and len(u.atomic_units) == 0 and
        #         len(u.variables) == 0 and len(u.unit_blocks) == 0 and
        #             len(u.attributes) == 0):
        #     errors.append(Error('design_unnecessary_abstraction', u, u.path, repr(u)))

        for c in u.comments:
            errors += self.check_comment(c, u.path)

        return errors

    def check_condition(self, c: ConditionStatement, file: str) -> list[Error]:
        self.__check_code(c)
        return super().check_condition(c, file)

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        self.__check_code(au)
        errors = super().check_atomicunit(au, file) + self.__check_lines(au, au.code, file)
        errors += self.imp_align.check(au, file)
        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        self.__check_code(d)
        return self.__check_lines(d, d.code, file)

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        self.__check_code(a)
        return self.__check_lines(a, a.code, file)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        self.variables_names.append(v.name)
        self.__check_code(v)
        return self.__check_lines(v, v.code, file)

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors = self.__check_lines(c, c.code, file)
        if c.line >= self.first_code_line:
            errors.append(Error('design_avoid_comments', c, file, repr(c)))
        return errors

    def __check_lines(self, el, code, file):
        errors = []

        lines = code.split('\n')
        for l, line in enumerate(lines):
            if len(line) > 140:
                error = Error('implementation_long_statement', el, file, line)
                error.line = el.line + l
                errors.append(error)

        return errors

    def __check_code(self, ce: CodeElement):
        if ce.line != -1 and ce.line < self.first_code_line:
            self.first_code_line = ce.line