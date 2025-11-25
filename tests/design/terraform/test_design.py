from glitch.tests.design.design_helper import BaseSecurityTest
from glitch.parsers.terraform import TerraformParser
from glitch.tech import Tech


class TestDesign(BaseSecurityTest):
    PARSER_CLASS = TerraformParser
    TECH = Tech.terraform

    def test_terraform_long_statement(self) -> None:
        self._help_test(
            "tests/design/terraform/files/long_statement.tf",
            "script",
            "configs/default.ini",
            1,
            ["implementation_long_statement"],
            [6],
        )

    def test_terraform_improper_alignment(self) -> None:
        self._help_test(
            "tests/design/terraform/files/improper_alignment.tf",
            "script",
            "configs/default.ini",
            1,
            ["implementation_improper_alignment"],
            [1],
        )

    def test_terraform_duplicate_block(self) -> None:
        self._help_test(
            "tests/design/terraform/files/duplicate_block.tf",
            "script",
            "configs/default.ini",
            2,
            [
                "design_duplicate_block",
                "design_duplicate_block",
            ],
            [1, 10],
        )

    def test_terraform_avoid_comments(self) -> None:
        self._help_test(
            "tests/design/terraform/files/avoid_comments.tf",
            "script",
            "configs/default.ini",
            2,
            [
                "design_avoid_comments",
                "design_avoid_comments",
            ],
            [2, 8],
        )

    def test_terraform_too_many_variables(self) -> None:
        self._help_test(
            "tests/design/terraform/files/too_many_variables.tf",
            "script",
            "configs/default.ini",
            1,
            [
                "implementation_too_many_variables",
            ],
            [-1],
        )
