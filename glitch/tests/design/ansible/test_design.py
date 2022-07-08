import unittest

from glitch.analysis.design import DesignVisitor
from glitch.parsers.cmof import AnsibleParser
from glitch.tech import Tech

class TestDesign(unittest.TestCase):
    def __help_test(self, path, type, n_errors, codes, lines):
        parser = AnsibleParser()
        inter = parser.parse(path, type, False)
        analysis = DesignVisitor(Tech.ansible)
        analysis.config("tests/design/ansible/design_ansible.ini")
        errors = list(filter(lambda e: e.code.startswith('design_') 
                or e.code.startswith('implementation_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  
    
    def test_ansible_long_statement(self):
        self.__help_test(
            "tests/design/ansible/files/long_statement.yml",
            "tasks",
            1, ["implementation_long_statement"], [16]
        )

    # Tabs
    def test_ansible_improper_alignment(self):
        self.__help_test(
            "tests/design/ansible/files/improper_alignment.yml",
            "tasks",
            4, 
            [
                "design_multifaceted_abstraction",
                "implementation_improper_alignment", 
                "implementation_improper_alignment", 
                "implementation_improper_alignment"
            ], [2, 4, 5, 6]
        )

    def test_ansible_duplicate_block(self):
        self.__help_test(
            "tests/design/ansible/files/duplicate_block.yml",
            "tasks",
            4, 
            [
                "design_duplicate_block", 
                "design_duplicate_block", 
                "design_duplicate_block", 
                "design_duplicate_block", 
            ], [2, 10, 25, 33]
        )

    def test_ansible_avoid_comments(self):
        self.__help_test(
            "tests/design/ansible/files/avoid_comments.yml",
            "tasks",
            1, 
            [
                "design_avoid_comments", 
            ], [11]
        )

    def test_ansible_long_resource(self):
        self.__help_test(
            "tests/design/ansible/files/long_resource.yml",
            "tasks",
            2, 
            [
                "design_long_resource", 
                "design_multifaceted_abstraction", 
            ], [2, 2]
        )

    def test_ansible_multifaceted_abstraction(self):
        self.__help_test(
            "tests/design/ansible/files/multifaceted_abstraction.yml",
            "tasks",
            1, 
            [
                "design_multifaceted_abstraction", 
            ], [2, 2]
        )

    def test_ansible_too_many_variables(self):
        self.__help_test(
            "tests/design/ansible/files/too_many_variables.yml",
            "script",
            1, 
            [
                "implementation_too_many_variables", 
            ], [-1]
        )
