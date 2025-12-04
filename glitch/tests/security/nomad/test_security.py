import unittest

from glitch.analysis.security.visitor import SecurityVisitor
from glitch.parsers.nomad import NomadParser
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech
from typing import List


class TestSecurity(unittest.TestCase):
    def __help_test(
        self, path: str, n_errors: int, codes: List[str], lines: List[int]
    ) -> None:
        parser = NomadParser()
        inter = parser.parse(path, UnitBlockType.script, False)
        analysis = SecurityVisitor(Tech.nomad)
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

    def test_nomad_admin(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/admin.nomad",
            3,
            ["sec_def_admin", "sec_hard_secr", "sec_hard_user"],
            [29, 29, 29],
        )

    def test_nomad_empty(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/hard_secr/hard_secr_empty_password.nomad",
            1,
            ["sec_empty_pass"],
            [40],
        )

    def test_nomad_hard_secret(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/hard_secr/hard_secr_password.nomad",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [40, 40],
        )
        self.__help_test(
            "tests/security/nomad/files/hard_secr/hard_secr_secret.nomad",
            1,
            ["sec_hard_secr"],
            [40],
        )
        self.__help_test(
            "tests/security/nomad/files/hard_secr/hard_secr_user.nomad",
            2,
            ["sec_hard_secr", "sec_hard_user"],
            [40, 40],
        )

    def test_nomad_http(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/https_tls.nomad", 1, ["sec_https"], [40]
        )

    def test_nomad_inv_bind(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/invalid_bind.nomad",
            1,
            ["sec_invalid_bind"],
            [39],
        )

    def test_nomad_non_official_image(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/non_official_image.nomad",
            1,
            ["sec_non_official_image"],
            [31],
        )

    def test_nomad_susp(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/susp_comment.nomad", 1, ["sec_susp_comm"], [5]
        )

    def test_nomad_weak_crypt(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/weak_crypt.nomad",
            1,
            ["sec_weak_crypt"],
            [32],
        )

    def test_nomad_container_image_tag_smells(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/container_image_tag_smells/normal_tag_and_digest.nomad",
            0,
            [],
            [],
        )
        self.__help_test(
            "tests/security/nomad/files/container_image_tag_smells/normal_tag_and_no_digest.nomad",
            1,
            ["sec_image_integrity"],
            [31],
        )
        self.__help_test(
            "tests/security/nomad/files/container_image_tag_smells/no_tag_and_digest.nomad",
            0,
            [],
            [],
        )
        self.__help_test(
            "tests/security/nomad/files/container_image_tag_smells/no_tag_no_digest.nomad",
            1,
            ["sec_no_image_tag"],
            [31],
        )

        self.__help_test(
            "tests/security/nomad/files/container_image_tag_smells/unstable_tag_and_digest.nomad",
            1,
            ["sec_unstable_tag"],
            [31],
        )
        self.__help_test(
            "tests/security/nomad/files/container_image_tag_smells/unstable_tag_no_digest.nomad",
            2,
            ["sec_image_integrity", "sec_unstable_tag"],
            [31, 31],
        )

    def test_nomad_deprecated_official_img(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/deprecated_docker_official_image.nomad",
            1,
            ["sec_depr_off_imgs"],
            [31],
        )

    def test_nomad_missing_healthchecks(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/missing_healthchecks.nomad",
            1,
            ["arc_missing_healthchecks"],
            [21],
        )

    def test_nomad_privileged_container(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/priv_container.nomad",
            1,
            ["sec_privileged_containers"],
            [32],
        )

    def test_nomad_docker_socket_mounted(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/docker_socket_mounted.nomad",
            1,
            ["sec_mounted_docker_socket"],
            [33],
        )

    def test_nomad_no_log_aggregation(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/no_log_aggregation.nomad",
            1,
            ["arc_no_logging"],
            [27],
        )

    def test_nomad_multiple_services_per_deployment_unit(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/multiple_services_per_deployment_unit.nomad",
            4,
            [
                "arc_multiple_services",
                "sec_non_official_image",
                "arc_multiple_services",
                "sec_non_official_image",
            ],
            [57, 61, 69, 73],
        )

    def test_nomad_no_api_gateway(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/no_api_gateway.nomad",
            1,
            ["arc_no_apig"],
            [7],
        )

    def test_nomad_wobbly_service_interaction(self) -> None:
        self.__help_test(
            "tests/security/nomad/files/wobbly_service_interaction.nomad",
            1,
            ["arc_wobbly_service_interaction"],
            [24],
        )
