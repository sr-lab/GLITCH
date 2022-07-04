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
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
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

    def test_susp_comment(self):
        self.__help_test(
            "tests/security/ansible/files/susp.yml",
            "vars",
            1, ["sec_susp_comm"], [9]
        )

    def test_def_admin(self):
        self.__help_test(
            "tests/security/ansible/files/admin.yml",
            "tasks",
            3, ["sec_def_admin", "sec_hard_secr", "sec_hard_user"], [3, 3, 3]
        )

    def test_empt_pass(self):
        self.__help_test(
            "tests/security/ansible/files/empty.yml",
            "tasks",
            3, ["sec_empty_pass", "sec_hard_pass", "sec_hard_secr"], [8, 8, 8]
        )
