import unittest

from glitch.analysis.design.visitor import DesignVisitor
from glitch.tech import Tech

class BaseSecurityTest(unittest.TestCase):

    PARSER_CLASS = None   # subclass must override
    TECH = None           # subclass must override

    def setUp(self) -> None:
        """Skip tests if this is the base class being run directly"""
        if self.PARSER_CLASS is None or self.TECH is None:
            self.skipTest("BaseSecurityTest is abstract and should not be run directly")

    def _help_test(self, path: str, type: str, config: str, n_errors: int, codes: list[str], lines: list[int]) -> None:
        assert self.PARSER_CLASS is not None, "Subclasses must define PARSER_CLASS"
        assert self.TECH is not None, "Subclasses must define TECH"

        parser = self.PARSER_CLASS()
        inter = parser.parse(path, type, False)
        analysis = DesignVisitor(self.TECH)
        analysis.config(config)

        errors = list(
            filter(
                lambda e: e.code.startswith("design_")
                or e.code.startswith("implementation_"),
                set(analysis.check(inter)),
            )
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            if self.TECH == Tech.gha:
                self.assertEqual(errors[i].path, path)
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])