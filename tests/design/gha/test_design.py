from tests.design.design_helper import BaseSecurityTest
from glitch.parsers.gha import GithubActionsParser
from glitch.tech import Tech


class TestDesign(BaseSecurityTest):
    PARSER_CLASS = GithubActionsParser
    TECH = Tech.gha

    # NOTE: This test also verifies if the paths of errors in inner Unit Blocks
    # are correctly reported.
    def test_gha_too_many_variables(self) -> None:
        self._help_test(
            "tests/design/gha/files/too_many_variables.yml",
            "script",
            "configs/default.ini",
            1,
            [
                "implementation_too_many_variables",
            ],
            [10],
        )
