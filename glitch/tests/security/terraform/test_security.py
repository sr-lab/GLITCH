import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.cmof import TerraformParser
from glitch.tech import Tech

class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors, codes, lines):
        parser = TerraformParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.terraform)
        analysis.config("configs/default.ini")
        errors = list(filter(lambda e: e.code.startswith('sec_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  

    def test_terraform_http(self):
        self.__help_test(
            "tests/security/terraform/files/http.tf",
            1, ["sec_https"], [2]
        )

    def test_terraform_susp_comment(self):
        self.__help_test(
            "tests/security/terraform/files/susp.tf",
            1, ["sec_susp_comm"], [8]
        )

    def test_terraform_def_admin(self):
        self.__help_test(
            "tests/security/terraform/files/admin.tf",
            3, ["sec_def_admin", "sec_hard_secr", "sec_hard_user"], [2, 2, 2]
        )

    def test_terraform_empt_pass(self):
        self.__help_test(
            "tests/security/terraform/files/empty.tf",
            3, ["sec_empty_pass", "sec_hard_pass", "sec_hard_secr"], [5, 5, 5]
        )

    def test_terraform_weak_crypt(self):
        self.__help_test(
            "tests/security/terraform/files/weak_crypt.tf",
            1, ["sec_weak_crypt"], [4]
        )

    def test_terraform_hard_secr(self):
        self.__help_test(
            "tests/security/terraform/files/hard_secr.tf",
            2, 
            ["sec_hard_pass", "sec_hard_secr"]
            , [5, 5]
        )

    def test_terraform_invalid_bind(self):
        self.__help_test(
            "tests/security/terraform/files/inv_bind.tf",
            1, ["sec_invalid_bind"], [14]
        )
