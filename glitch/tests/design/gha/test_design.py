import unittest

from glitch.analysis.design.visitor import DesignVisitor
from glitch.analysis.rules import Error
from glitch.parsers.gha import GithubActionsParser
from glitch.tech import Tech
from glitch.repr.inter import UnitBlockType
from typing import List


class TestDesign(unittest.TestCase):
    def __help_test(
        self, path: str, n_errors: int, codes: List[str], lines: List[int]
    ) -> None:
        parser = GithubActionsParser()
        inter = parser.parse(path, UnitBlockType.script, False)
        assert inter is not None
        analysis = DesignVisitor(Tech.gha)
        analysis.config("configs/default.ini")
        errors: List[Error] = list(set(analysis.check(inter)))
        errors = list(
            filter(
                lambda e: e.code.startswith("design_")
                or e.code.startswith("implementation_"),
                errors,
            )
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].path, path)
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])

    # NOTE: This test also verifies if the paths of errors in inner Unit Blocks
    # are correctly reported.
    def test_gha_too_many_variables(self) -> None:
        self.__help_test(
            "tests/design/gha/files/too_many_variables.yml",
            1,
            [
                "implementation_too_many_variables",
            ],
            [10],
        )
