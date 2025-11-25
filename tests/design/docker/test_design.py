from tests.design.design_helper import BaseDesignTest
from glitch.tech import Tech

class TestDesign(BaseDesignTest):
    TECH = Tech.docker

    def test_docker_long_statement(self) -> None:
        self._help_test(
            "tests/design/docker/files/long_statement.Dockerfile",
            "script",
            "configs/default.ini",
            1,
            ["implementation_long_statement"],
            [4],
        )

    def test_docker_improper_alignment(self) -> None:
        # TODO: Fix smell, due to docker parsing method the attributes are not
        # detected in differents lines, making it impossible to trigger alignment
        pass
        # self._help_test(
        #     "tests/design/docker/files/improper_alignment.Dockerfile",
        #     "script",
        #     "configs/default.ini",
        #     1,
        #     [
        #         "implementation_improper_alignment"
        #     ], [1]
        # )

    def test_docker_duplicate_block(self) -> None:
        self._help_test(
            "tests/design/docker/files/duplicate_block.Dockerfile",
            "script",
            "configs/default.ini",
            2,
            [
                "design_duplicate_block",
                "design_duplicate_block",
            ],
            [1, 9],
        )

    def test_docker_avoid_comments(self) -> None:
        self._help_test(
            "tests/design/docker/files/avoid_comments.Dockerfile",
            "script",
            "configs/default.ini",
            1,
            [
                "design_avoid_comments",
            ],
            [1],
        )

    def test_docker_too_many_variables(self) -> None:
        self._help_test(
            "tests/design/docker/files/too_many_variables.Dockerfile",
            "script",
            "configs/default.ini",
            1,
            [
                "implementation_too_many_variables",
            ],
            [1],
        )
