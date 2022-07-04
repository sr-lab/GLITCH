import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.cmof import ChefParser
from glitch.tech import Tech

class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors, codes, lines):
        parser = ChefParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.chef)
        analysis.config("configs/default.ini")
        errors = list(filter(lambda e: e.code.startswith('sec_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  
    
    def test_chef_http(self):
        self.__help_test(
            "tests/security/chef/files/http.rb",
            1, ["sec_https"], [3]
        )

    def test_chef_susp_comment(self):
        self.__help_test(
            "tests/security/chef/files/susp.rb",
            1, ["sec_susp_comm"], [1]
        )

    def test_chef_def_admin(self):
        self.__help_test(
            "tests/security/chef/files/admin.rb",
            3, ["sec_def_admin", "sec_hard_secr", "sec_hard_user"], [8, 8, 8]
        )

    def test_chef_empt_pass(self):
        self.__help_test(
            "tests/security/chef/files/empty.rb",
            3, ["sec_empty_pass", "sec_hard_pass", "sec_hard_secr"], [1, 1, 1]
        )

    def test_chef_weak_crypt(self):
        self.__help_test(
            "tests/security/chef/files/weak_crypt.rb",
            1, ["sec_weak_crypt"], [4]
        )

    def test_chef_hard_secr(self):
        self.__help_test(
            "tests/security/chef/files/hard_secr.rb",
            2, 
            ["sec_hard_pass", "sec_hard_secr"]
            , [8, 8]
        )

    def test_chef_invalid_bind(self):
        self.__help_test(
            "tests/security/chef/files/inv_bind.rb",
            1, ["sec_invalid_bind"], [7]
        )

    def test_chef_int_check(self):
        self.__help_test(
            "tests/security/chef/files/int_check.rb",
            1, ["sec_no_int_check"], [1]
        )

    def test_chef_missing_default(self):
        self.__help_test(
            "tests/security/chef/files/missing_default.rb",
            1, ["sec_no_default_switch"], [1]
        )