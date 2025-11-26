from tests.security.security_helper import BaseSecurityTest
from glitch.parsers.chef import ChefParser
from glitch.tech import Tech


class TestSecurity(BaseSecurityTest):
    PARSER_CLASS = ChefParser
    TECH = Tech.chef

    def test_chef_http(self) -> None:
        self._help_test("tests/security/chef/files/http.rb", "script", 1, ["sec_https"], [3])

    def test_chef_susp_comment(self) -> None:
        self._help_test("tests/security/chef/files/susp.rb", "script", 1, ["sec_susp_comm"], [1])

    def test_chef_def_admin(self) -> None:
        self._help_test(
            "tests/security/chef/files/admin.rb",
            "script",
            2,
            ["sec_def_admin", "sec_hard_user"],
            [8, 8],
        )

    def test_chef_empt_pass(self) -> None:
        self._help_test(
            "tests/security/chef/files/empty.rb", "script", 1, ["sec_empty_pass"], [1]
        )

    def test_chef_weak_crypt(self) -> None:
        self._help_test(
            "tests/security/chef/files/weak_crypt.rb", "script", 1, ["sec_weak_crypt"], [4]
        )

    def test_chef_hard_secr(self) -> None:
        self._help_test(
            "tests/security/chef/files/hard_secr.rb",
            "script",
            1,
            ["sec_hard_pass"],
            [8],
        )

    def test_chef_invalid_bind(self) -> None:
        self._help_test(
            "tests/security/chef/files/inv_bind.rb", "script", 1, ["sec_invalid_bind"], [1]
        )

    def test_chef_int_check(self) -> None:
        self._help_test(
            "tests/security/chef/files/int_check.rb", "script", 1, ["sec_no_int_check"], [1]
        )

    def test_chef_missing_default(self) -> None:
        self._help_test(
            "tests/security/chef/files/missing_default.rb",
            "script",
            1,
            ["sec_no_default_switch"],
            [1],
        )

    def test_chef_full_permission(self) -> None:
        self._help_test(
            "tests/security/chef/files/full_permission.rb",
            "script",
            1,
            ["sec_full_permission_filesystem"],
            [3],
        )

    def test_chef_obs_command(self) -> None:
        self._help_test(
            "tests/security/chef/files/obs_command.rb", "script", 1, ["sec_obsolete_command"], [2]
        )
