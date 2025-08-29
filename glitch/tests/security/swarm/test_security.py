import os
import unittest

from glitch.analysis.security.visitor import SecurityVisitor
from glitch.parsers.swarm import SwarmParser
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech
from typing import List


class TestSecurity(unittest.TestCase):
    def __help_test(
        self, path: str, n_errors: int, codes: List[str], lines: List[int]
    ) -> None:
        parser = SwarmParser()
        inter = parser.parse(path, UnitBlockType.script, False)
        analysis = SecurityVisitor(Tech.swarm)
        analysis.config("configs/default.ini")
        errors = list(
            filter(
                lambda e: e.code.startswith("sec_") or e.code.startswith("arc_"),
                set(analysis.check(inter)),
            )  # type: ignore
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])

    def test_swarm_admin(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/admin.yml",
            3,
            ["sec_def_admin", "sec_hard_secr", "sec_hard_user"],
            [8, 8, 8],
        )

    def test_swarm_empty(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/hard_secr/hard_secr_empty_password.yml",
            1,
            ["sec_empty_pass"],
            [8],
        )

    def test_swarm_hard_secret(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/hard_secr/hard_secr_password.yml",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [8, 8],
        )
        self.__help_test(
            "tests/security/swarm/files/hard_secr/hard_secr_secret.yml",
            1,
            ["sec_hard_secr"],
            [8],
        )
        self.__help_test(
            "tests/security/swarm/files/hard_secr/hard_secr_user.yml",
            2,
            ["sec_hard_secr", "sec_hard_user"],
            [8, 8],
        )

    def test_swarm_http(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/https_tls.yml", 1, ["sec_https"], [9]
        )

    def test_swarm_inv_bind(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/invalid_bind/invalid_bind_array.yml",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self.__help_test(
            "tests/security/swarm/files/invalid_bind/invalid_bind_exec_form.yml",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self.__help_test(
            "tests/security/swarm/files/invalid_bind/invalid_bind_hash.yml",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self.__help_test(
            "tests/security/swarm/files/invalid_bind/invalid_bind_string.yml",
            1,
            ["sec_invalid_bind"],
            [8],
        )

    def test_swarm_non_official_image(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/non_official_image.yml",
            1,
            ["sec_non_official_image"],
            [3],
        )

    def test_swarm_susp(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/susp_comment.yml", 1, ["sec_susp_comm"], [2]
        )

    def test_swarm_weak_crypt(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/weak_crypt/weak_crypt_string.yml",
            1,
            ["sec_weak_crypt"],
            [10],
        )
        self.__help_test(
            "tests/security/swarm/files/weak_crypt/weak_crypt_hash.yml",
            1,
            ["sec_weak_crypt"],
            [9],
        )
        self.__help_test(
            "tests/security/swarm/files/weak_crypt/weak_crypt_array.yml",
            1,
            ["sec_weak_crypt"],
            [11],
        )
        self.__help_test(
            "tests/security/swarm/files/weak_crypt/weak_crypt_array_exec_form.yml",
            1,
            ["sec_weak_crypt"],
            [9],
        )

    def test_swarm_container_image_tag_smells(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/container_image_tag_smells/normal_tag_and_digest.yml",
            0,
            [],
            [],
        )
        self.__help_test(
            "tests/security/swarm/files/container_image_tag_smells/normal_tag_and_no_digest.yml",
            1,
            ["sec_image_integrity"],
            [3],
        )
        self.__help_test(
            "tests/security/swarm/files/container_image_tag_smells/no_tag_and_digest.yml",
            0,
            [],
            [],
        )
        self.__help_test(
            "tests/security/swarm/files/container_image_tag_smells/no_tag_no_digest.yml",
            1,
            ["sec_no_image_tag"],
            [3],
        )

        self.__help_test(
            "tests/security/swarm/files/container_image_tag_smells/unstable_tag_and_digest.yml",
            1,
            ["sec_unstable_tag"],
            [3],
        )
        self.__help_test(
            "tests/security/swarm/files/container_image_tag_smells/unstable_tag_no_digest.yml",
            2,
            ["sec_image_integrity", "sec_unstable_tag"],
            [3, 3],
        )

    def test_swarm_deprecated_official_img(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/deprecated_docker_official_image.yml",
            1,
            ["sec_depr_off_imgs"],
            [3],
        )

    def test_swarm_missing_healthchecks(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/missing_healthchecks.yml",
            1,
            ["arc_missing_healthchecks"],
            [2],
        )

    def test_swarm_privileged_container(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/priv_container.yml",
            1,
            ["sec_privileged_containers"],
            [8],
        )

    def test_swarm_docker_socket_mounted(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/docker_socket_mounted.yml",
            1,
            ["sec_mounted_docker_socket"],
            [9],
        )

    def test_swarm_no_log_aggregation(self) -> None:
        self.__help_test(
            "tests/security/swarm/files/no_log_aggregation.yml",
            1,
            ["arc_no_logging"],
            [2],
        )
