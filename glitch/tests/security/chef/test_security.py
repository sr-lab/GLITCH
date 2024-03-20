import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.chef import ChefParser
from glitch.tech import Tech


class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors: int, codes, lines) -> None:
        parser = ChefParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.chef)
        analysis.config("configs/default.ini")
        errors = list(
            filter(lambda e: e.code.startswith("sec_"), set(analysis.check(inter)))
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])

    def test_chef_http(self) -> None:
        self.__help_test("tests/security/chef/files/http.rb", 1, ["sec_https"], [3])

    def test_chef_susp_comment(self) -> None:
        self.__help_test("tests/security/chef/files/susp.rb", 1, ["sec_susp_comm"], [1])

    def test_chef_def_admin(self) -> None:
        self.__help_test(
            "tests/security/chef/files/admin.rb",
            3,
            ["sec_def_admin", "sec_hard_secr", "sec_hard_user"],
            [8, 8, 8],
        )

    def test_chef_empt_pass(self) -> None:
        self.__help_test(
            "tests/security/chef/files/empty.rb", 1, ["sec_empty_pass"], [1]
        )

    def test_chef_weak_crypt(self) -> None:
        self.__help_test(
            "tests/security/chef/files/weak_crypt.rb", 1, ["sec_weak_crypt"], [4]
        )

    def test_chef_hard_secr(self) -> None:
        self.__help_test(
            "tests/security/chef/files/hard_secr.rb",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [8, 8],
        )

    def test_chef_invalid_bind(self) -> None:
        self.__help_test(
            "tests/security/chef/files/inv_bind.rb", 1, ["sec_invalid_bind"], [7]
        )

    def test_chef_int_check(self) -> None:
        self.__help_test(
            "tests/security/chef/files/int_check.rb", 1, ["sec_no_int_check"], [1]
        )

    def test_chef_missing_default(self) -> None:
        self.__help_test(
            "tests/security/chef/files/missing_default.rb",
            1,
            ["sec_no_default_switch"],
            [2],
        )

    def test_chef_full_permission(self) -> None:
        self.__help_test(
            "tests/security/chef/files/full_permission.rb",
            1,
            ["sec_full_permission_filesystem"],
            [3],
        )

    def test_chef_obs_command(self) -> None:
        self.__help_test(
            "tests/security/chef/files/obs_command.rb", 1, ["sec_obsolete_command"], [2]
        )
