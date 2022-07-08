import unittest

from glitch.analysis.design import DesignVisitor
from glitch.parsers.cmof import ChefParser
from glitch.tech import Tech

class TestDesign(unittest.TestCase):
    def __help_test(self, path, n_errors, codes, lines):
        parser = ChefParser()
        inter = parser.parse(path, "script", False)
        analysis = DesignVisitor(Tech.chef)
        analysis.config("tests/design/chef/design_chef.ini")
        errors = list(filter(lambda e: e.code.startswith('design_') 
                or e.code.startswith('implementation_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  
    
    def test_chef_long_statement(self):
        self.__help_test(
            "tests/design/chef/files/long_statement.rb",
            1, ["implementation_long_statement"], [6]
        )

    def test_chef_improper_alignment(self):
        self.__help_test(
            "tests/design/chef/files/improper_alignment.rb",
            1, 
            [
                "implementation_improper_alignment"
            ], [1]
        )

    def test_chef_duplicate_block(self):
        self.__help_test(
            "tests/design/chef/files/duplicate_block.rb",
            4, 
            [
                "design_duplicate_block", 
                "implementation_long_statement", 
                "design_duplicate_block", 
                "implementation_long_statement", 
            ], [3, 4, 9, 10]
        )

    def test_chef_avoid_comments(self):
        self.__help_test(
            "tests/design/chef/files/avoid_comments.rb",
            1, 
            [
                "design_avoid_comments", 
            ], [7]
        )

    def test_chef_long_resource(self):
        self.__help_test(
            "tests/design/chef/files/long_resource.rb",
            1, 
            [
                "design_long_resource", 
            ], [1]
        )

    def test_chef_multifaceted_abstraction(self):
        self.__help_test(
            "tests/design/chef/files/multifaceted_abstraction.rb",
            1, 
            [
                "design_multifaceted_abstraction", 
            ], [1]
        )

    def test_chef_misplaced_attribute(self):
        self.__help_test(
            "tests/design/chef/files/misplaced_attribute.rb",
            1, 
            [
                "design_misplaced_attribute", 
            ], [1]
        )

    def test_chef_too_many_variables(self):
        self.__help_test(
            "tests/design/chef/files/too_many_variables.rb",
            1, 
            [
                "implementation_too_many_variables", 
            ], [-1]
        )

