from tests.design.design_helper import BaseDesignTest
from glitch.tech import Tech
from glitch.repr.inter import UNDEFINED_POSITION


class TestDesign(BaseDesignTest):
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
            [UNDEFINED_POSITION],
        )
