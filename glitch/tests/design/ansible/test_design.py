import unittest

from glitch.analysis.design import DesignVisitor
from glitch.parsers.cmof import AnsibleParser
from glitch.tech import Tech

class TestDesign(unittest.TestCase):
    def __help_test(self, path, type, n_errors, codes, lines):
        parser = AnsibleParser()
        inter = parser.parse(path, type, False)
        analysis = DesignVisitor(Tech.ansible)
        analysis.config("configs/default.ini")
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
            3, 
            [
                "implementation_improper_alignment", 
                "implementation_improper_alignment", 
                "implementation_improper_alignment"
            ], [4, 5, 6]
        )
