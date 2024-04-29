import json
import configparser

from cmath import inf
from glitch.analysis.rules import Error, RuleVisitor
from glitch.tech import Tech
from glitch.repr.inter import *
from typing import List
from glitch.analysis.design.smell_checker import DesignSmellChecker


class DesignVisitor(RuleVisitor):
    def __init__(self, tech: Tech) -> None:
        super().__init__(tech)

        self.checkers: List[DesignSmellChecker] = []
        for child in DesignSmellChecker.__subclasses__():
            if (child.tech() is None and tech not in child.ignore_techs()) or (
                child.tech() is not None and child.tech() == tech
            ):
                self.checkers.append(child())

        if tech in [Tech.chef, Tech.puppet, Tech.ansible]:
            self.comment = "#"
        else:
            self.comment = "//"

        self.variable_stack: List[int] = []
        self.variables_names: List[str] = []
        self.first_code_line = inf

    @staticmethod
    def get_name() -> str:
        return "design"

    def config(self, config_path: str) -> None:
        config = configparser.ConfigParser()
        config.read(config_path)
        DesignVisitor.EXEC = json.loads(config["design"]["exec_atomic_units"])
        DesignVisitor.DEFAULT_VARIABLES = json.loads(
            config["design"]["default_variables"]
        )
        if "var_refer_symbol" not in config["design"]:
            DesignVisitor.VAR_REFER_SYMBOL = None
        else:
            DesignVisitor.VAR_REFER_SYMBOL = json.loads(  # type: ignore
                config["design"]["var_refer_symbol"]
            )

    def check_module(self, m: Module) -> list[Error]:
        errors = super().check_module(m)
        # FIXME Needs to consider more things
        # if len(m.blocks) == 0:
        #     errors.append(Error('design_unnecessary_abstraction', m, m.path, repr(m)))
        return errors

    def check_unitblock(self, u: UnitBlock, file: str) -> List[Error]:
        if u.path != "":
            with open(u.path, "r") as f:
                try:
                    code_lines = f.readlines()
                    f.seek(0, 0)
                except UnicodeDecodeError:
                    return []
        else:
            code_lines = []

        self.first_non_comm_line = inf
        for i, line in enumerate(code_lines):
            if not line.startswith(self.comment):
                self.first_non_comm_line = i + 1
                break

        self.variable_stack.append(len(self.variables_names))
        for attr in u.attributes:
            self.variables_names.append(attr.name)

        errors: List[Error] = []
        # The order is important
        for au in u.atomic_units:
            errors += self.check_atomicunit(au, file)
        for v in u.variables:
            errors += self.check_variable(v, file)
        for a in u.attributes:
            errors += self.check_attribute(a, file)
        for d in u.dependencies:
            errors += self.check_dependency(d, file)
        for s in u.statements:
            errors += self.check_element(s, file)
        for c in u.comments:
            errors += self.check_comment(c, file)

        # FIXME Needs to consider more things
        # if (len(u.statements) == 0 and len(u.atomic_units) == 0 and
        #         len(u.variables) == 0 and len(u.unit_blocks) == 0 and
        #             len(u.attributes) == 0):
        #     errors.append(Error('design_unnecessary_abstraction', u, file, repr(u)))

        for checker in self.checkers:
            checker.code_lines = code_lines
            checker.variables_names = self.variables_names
            errors += checker.check(u, file)

        # The unit blocks inside should only be considered after in order to
        # have the correct variables
        for ub in u.unit_blocks:
            errors += self.check_unitblock(ub, file)

        variable_size = self.variable_stack.pop()
        if variable_size == 0:
            self.variables_names = []
        else:
            self.variables_names = self.variables_names[:variable_size]

        return errors

    def check_condition(self, c: ConditionalStatement, file: str) -> list[Error]:
        return super().check_condition(c, file)

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file)
        for checker in self.checkers:
            errors += checker.check(au, file)
        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return []

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        self.variables_names.append(v.name)
        return []

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors: List[Error] = []
        if c.line >= self.first_non_comm_line:
            errors.append(Error("design_avoid_comments", c, file, repr(c)))
        return errors


# NOTE: in the end of the file to avoid circular import
# Imports all the classes defined in the __init__.py file
from glitch.analysis.design import *
