from tests.security.security_helper import BaseSecurityTest
from glitch.parsers.ansible import AnsibleParser
from glitch.tech import Tech

class TestSecurity(BaseSecurityTest):
    PARSER_CLASS = AnsibleParser
    TECH = Tech.ansible

    def test_ansible_http(self) -> None:
        self._help_test(
            "tests/security/ansible/files/http.yml", "tasks", 1, ["sec_https"], [4]
        )

    def test_ansible_susp_comment(self) -> None:
        self._help_test(
            "tests/security/ansible/files/susp.yml", "vars", 1, ["sec_susp_comm"], [9]
        )

    def test_ansible_def_admin(self) -> None:
        self._help_test(
            "tests/security/ansible/files/admin.yml",
            "tasks",
            3,
            ["sec_def_admin", "sec_hard_secr", "sec_hard_user"],
            [3, 3, 3],
        )

    def test_ansible_empt_pass(self) -> None:
        self._help_test(
            "tests/security/ansible/files/empty.yml",
            "tasks",
            1,
            ["sec_empty_pass"],
            [6],
        )

    def test_ansible_weak_crypt(self) -> None:
        self._help_test(
            "tests/security/ansible/files/weak_crypt.yml",
            "tasks",
            2,
            ["sec_weak_crypt", "sec_weak_crypt"],
            [4, 7],
        )

    def test_ansible_hard_secr(self) -> None:
        self._help_test(
            "tests/security/ansible/files/hard_secr.yml",
            "tasks",
            3,
            ["sec_hard_pass", "sec_hard_secr", "sec_hard_user"],
            [6, 6, 6],
        )

    def test_ansible_invalid_bind(self) -> None:
        self._help_test(
            "tests/security/ansible/files/inv_bind.yml",
            "tasks",
            1,
            ["sec_invalid_bind"],
            [5],
        )

    def test_ansible_int_check(self) -> None:
        self._help_test(
            "tests/security/ansible/files/int_check.yml",
            "tasks",
            1,
            ["sec_no_int_check"],
            [5],
        )

    def test_ansible_full_perm(self) -> None:
        self._help_test(
            "tests/security/ansible/files/full_permission.yml",
            "tasks",
            1,
            ["sec_full_permission_filesystem"],
            [7],
        )

    def test_ansible_obs_command(self) -> None:
        self._help_test(
            "tests/security/ansible/files/obs_command.yml",
            "tasks",
            1,
            ["sec_obsolete_command"],
            [2],
        )
