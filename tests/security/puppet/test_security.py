from tests.security.security_helper import BaseSecurityTest
from glitch.tech import Tech


class TestSecurity(BaseSecurityTest):
    TECH = Tech.puppet

    def test_puppet_http(self) -> None:
        self._help_test(
            "tests/security/puppet/files/http.pp", "script", 1, ["sec_https"], [2]
        )

    def test_puppet_susp_comment(self) -> None:
        self._help_test(
            "tests/security/puppet/files/susp.pp", "script", 1, ["sec_susp_comm"], [19]
        )

    def test_puppet_def_admin(self) -> None:
        self._help_test(
            "tests/security/puppet/files/admin.pp",
            "script",
            2,
            ["sec_def_admin", "sec_hard_user"],
            [7, 7],
        )

    def test_puppet_empt_pass(self) -> None:
        self._help_test(
            "tests/security/puppet/files/empty.pp", "script", 1, ["sec_empty_pass"], [1]
        )

    def test_puppet_weak_crypt(self) -> None:
        self._help_test(
            "tests/security/puppet/files/weak_crypt.pp",
            "script",
            1,
            ["sec_weak_crypt"],
            [12],
        )

    def test_puppet_hard_secr(self) -> None:
        self._help_test(
            "tests/security/puppet/files/hard_secr.pp",
            "script",
            1,
            ["sec_hard_pass"],
            [2],
        )

    def test_puppet_invalid_bind(self) -> None:
        self._help_test(
            "tests/security/puppet/files/inv_bind.pp",
            "script",
            1,
            ["sec_invalid_bind"],
            [12],
        )

    def test_puppet_int_check(self) -> None:
        self._help_test(
            "tests/security/puppet/files/int_check.pp",
            "script",
            1,
            ["sec_no_int_check"],
            [5],
        )

    def test_puppet_missing_default(self) -> None:
        self._help_test(
            "tests/security/puppet/files/missing_default.pp",
            "script",
            2,
            ["sec_no_default_switch", "sec_no_default_switch"],
            [1, 6],
        )

    def test_puppet_full_perm(self) -> None:
        self._help_test(
            "tests/security/puppet/files/full_permission.pp",
            "script",
            1,
            ["sec_full_permission_filesystem"],
            [4],
        )

    def test_puppet_obs_command(self) -> None:
        self._help_test(
            "tests/security/puppet/files/obs_command.pp",
            "script",
            1,
            ["sec_obsolete_command"],
            [2],
        )
