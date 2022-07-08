import unittest

from glitch.analysis.design import DesignVisitor
from glitch.parsers.cmof import PuppetParser
from glitch.tech import Tech

class TestDesign(unittest.TestCase):
    def __help_test(self, path, n_errors, codes, lines):
        parser = PuppetParser()
        inter = parser.parse(path, "script", False)
        analysis = DesignVisitor(Tech.puppet)
        analysis.config("tests/design/puppet/design_puppet.ini")
        errors = list(filter(lambda e: e.code.startswith('design_') 
                or e.code.startswith('implementation_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  
    
    def test_puppet_long_statement(self):
        self.__help_test(
            "tests/design/puppet/files/long_statement.pp",
            1, ["implementation_long_statement"], [6]
        )

    def test_puppet_improper_alignment(self):
        self.__help_test(
            "tests/design/puppet/files/improper_alignment.pp",
            1, 
            [
                "implementation_improper_alignment"
            ], [1]
        )

    def test_puppet_duplicate_block(self):
        self.__help_test(
            "tests/design/puppet/files/duplicate_block.pp",
            2, 
            [
                "design_duplicate_block", 
                "design_duplicate_block", 
            ], [1, 10]
        )

    def test_puppet_avoid_comments(self):
        self.__help_test(
            "tests/design/puppet/files/avoid_comments.pp",
            1, 
            [
                "design_avoid_comments", 
            ], [5]
        )

    def test_puppet_long_resource(self):
        self.__help_test(
            "tests/design/puppet/files/long_resource.pp",
            1, 
            [
                "design_long_resource", 
            ], [1]
        )

    def test_puppet_multifaceted_abstraction(self):
        self.__help_test(
            "tests/design/puppet/files/multifaceted_abstraction.pp",
            2, 
            [
                "design_multifaceted_abstraction", 
                "implementation_long_statement"
            ], [1, 2]
        )

    def test_puppet_unguarded_variable(self):
        self.__help_test(
            "tests/design/puppet/files/unguarded_variable.pp",
            1, 
            [
                "implementation_unguarded_variable", 
            ], [12]
        )

    def test_puppet_misplaced_attribute(self):
        self.__help_test(
            "tests/design/puppet/files/misplaced_attribute.pp",
            1, 
            [
                "design_misplaced_attribute", 
            ], [1]
        )
    
    def test_puppet_too_many_variables(self):
        self.__help_test(
            "tests/design/puppet/files/too_many_variables.pp",
            1, 
            [
                "implementation_too_many_variables", 
            ], [1]
        )
