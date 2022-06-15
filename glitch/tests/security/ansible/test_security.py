import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.cmof import AnsibleParser
from glitch.tech import Tech

class TestSecurity(unittest.TestCase):
    def __help_test(self, path, type, n_errors, codes, lines):
        parser = AnsibleParser()
        inter = parser.parse(path, type, False)
        analysis = SecurityVisitor(Tech.ansible)
        analysis.config("configs/default.ini")
        errors = list(set(analysis.check(inter)))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  
    
    def test_http(self):
        self.__help_test(
            "tests/security/ansible/files/http.yml",
            "tasks",
            1, ["sec_https"], [4]
        )