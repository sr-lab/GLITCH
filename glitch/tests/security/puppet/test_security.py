import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.cmof import PuppetParser
from glitch.tech import Tech

class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors, codes, lines):
        parser = PuppetParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.puppet)
        analysis.config("configs/default.ini")
        errors = list(filter(lambda e: e.code.startswith('sec_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  
    
    def test_puppet_http(self):
        self.__help_test(
            "tests/security/puppet/files/http.pp",
            1, ["sec_https"], [2]
        )

    def test_puppet_susp_comment(self):
        self.__help_test(
            "tests/security/puppet/files/susp.pp",
            1, ["sec_susp_comm"], [19]
        )

    def test_puppet_def_admin(self):
        self.__help_test(
            "tests/security/puppet/files/admin.pp",
            3, ["sec_def_admin", "sec_hard_secr", "sec_hard_user"], [7, 7, 7]
        )

    def test_puppet_empt_pass(self):
        self.__help_test(
            "tests/security/puppet/files/empty.pp",
            3, ["sec_empty_pass", "sec_hard_pass", "sec_hard_secr"], [1, 1, 1]
        )

    def test_puppet_weak_crypt(self):
        self.__help_test(
            "tests/security/puppet/files/weak_crypt.pp",
            1, ["sec_weak_crypt"], [12]
        )

    def test_puppet_hard_secr(self):
        self.__help_test(
            "tests/security/puppet/files/hard_secr.pp",
            2, 
            ["sec_hard_pass", "sec_hard_secr"]
            , [2, 2]
        )

    def test_puppet_invalid_bind(self):
        self.__help_test(
            "tests/security/puppet/files/inv_bind.pp",
            1, ["sec_invalid_bind"], [12]
        )

    def test_puppet_int_check(self):
        self.__help_test(
            "tests/security/puppet/files/int_check.pp",
            1, ["sec_no_int_check"], [5]
        )

    def test_puppet_missing_default(self):
        self.__help_test(
            "tests/security/puppet/files/missing_default.pp",
            1, ["sec_no_default_switch"], [1]
        )