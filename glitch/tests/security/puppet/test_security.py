import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.puppet import PuppetParser
from glitch.tech import Tech


class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors: int, codes, lines) -> None:
        parser = PuppetParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.puppet)
        analysis.config("configs/default.ini")
        errors = list(
            filter(lambda e: e.code.startswith("sec_"), set(analysis.check(inter)))
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])

    def test_puppet_http(self) -> None:
        self.__help_test("tests/security/puppet/files/http.pp", 1, ["sec_https"], [2])

    def test_puppet_susp_comment(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/susp.pp", 1, ["sec_susp_comm"], [19]
        )

    def test_puppet_def_admin(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/admin.pp",
            3,
            ["sec_def_admin", "sec_hard_secr", "sec_hard_user"],
            [7, 7, 7],
        )

    def test_puppet_empt_pass(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/empty.pp", 1, ["sec_empty_pass"], [1]
        )

    def test_puppet_weak_crypt(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/weak_crypt.pp", 1, ["sec_weak_crypt"], [12]
        )

    def test_puppet_hard_secr(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/hard_secr.pp",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [2, 2],
        )

    def test_puppet_invalid_bind(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/inv_bind.pp", 1, ["sec_invalid_bind"], [12]
        )

    def test_puppet_int_check(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/int_check.pp", 1, ["sec_no_int_check"], [5]
        )

    def test_puppet_missing_default(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/missing_default.pp",
            2,
            ["sec_no_default_switch", "sec_no_default_switch"],
            [2, 7],
        )

    def test_puppet_full_perm(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/full_permission.pp",
            1,
            ["sec_full_permission_filesystem"],
            [4],
        )

    def test_puppet_obs_command(self) -> None:
        self.__help_test(
            "tests/security/puppet/files/obs_command.pp",
            1,
            ["sec_obsolete_command"],
            [2],
        )
