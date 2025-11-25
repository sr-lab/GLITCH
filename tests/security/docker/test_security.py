import os

from tests.security.security_helper import BaseSecurityTest
from glitch.parsers.docker import DockerParser
from glitch.tech import Tech


class TestSecurity(BaseSecurityTest):
    PARSER_CLASS = DockerParser
    TECH = Tech.docker

    def tearDown(self) -> None:
        super().tearDown()
        if os.path.exists("Dockerfile"):
            os.remove("Dockerfile")

    def test_docker_admin(self) -> None:
        self._help_test(
            "tests/security/docker/files/admin.Dockerfile",
            "script",
            2,
            ["sec_def_admin", "sec_def_admin"],
            [2, 4],
        )

    def test_docker_empty(self) -> None:
        self._help_test(
            "tests/security/docker/files/empty.Dockerfile", "script", 1, ["sec_empty_pass"], [4]
        )
        pass

    def test_docker_full_permission(self) -> None:
        self._help_test(
            "tests/security/docker/files/full_permission.Dockerfile",
            "script",
            1,
            ["sec_full_permission_filesystem"],
            [3],
        )

    def test_docker_hard_secret(self) -> None:
        self._help_test(
            "tests/security/docker/files/hard_secr.Dockerfile",
            "script",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [3, 3],
        )

    def test_docker_http(self) -> None:
        self._help_test(
            "tests/security/docker/files/http.Dockerfile", "script", 1, ["sec_https"], [5]
        )

    def test_docker_int_check(self) -> None:
        self._help_test(
            "tests/security/docker/files/int_check.Dockerfile",
            "script",
            1,
            ["sec_no_int_check"],
            [4],
        )

    def test_docker_inv_bind(self) -> None:
        self._help_test(
            "tests/security/docker/files/inv_bind.Dockerfile",
            "script",
            1,
            ["sec_invalid_bind"],
            [4],
        )

    def test_docker_non_official_image(self) -> None:
        self._help_test(
            "tests/security/docker/files/non_off_image.Dockerfile",
            "script",
            1,
            ["sec_non_official_image"],
            [1],
        )

    def test_docker_obs_command(self) -> None:
        self._help_test(
            "tests/security/docker/files/obs_command.Dockerfile",
            "script",
            1,
            ["sec_obsolete_command"],
            [4],
        )

    def test_docker_susp(self) -> None:
        self._help_test(
            "tests/security/docker/files/susp.Dockerfile", "script", 1, ["sec_susp_comm"], [3]
        )

    def test_docker_weak_crypt(self) -> None:
        self._help_test(
            "tests/security/docker/files/weak_crypt.Dockerfile",
            "script",
            1,
            ["sec_weak_crypt"],
            [8],
        )
