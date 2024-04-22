import unittest

from glitch.analysis.design.visitor import DesignVisitor
from glitch.parsers.docker import DockerParser
from glitch.tech import Tech


class TestDesign(unittest.TestCase):
    def __help_test(self, path, n_errors: int, codes, lines) -> None:
        parser = DockerParser()
        inter = parser.parse(path, "script", False)
        analysis = DesignVisitor(Tech.docker)
        analysis.config("configs/default.ini")
        errors = list(
            filter(
                lambda e: e.code.startswith("design_")
                or e.code.startswith("implementation_"),
                set(analysis.check(inter)),
            )
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])

    def test_docker_long_statement(self) -> None:
        self.__help_test(
            "tests/design/docker/files/long_statement.Dockerfile",
            1,
            ["implementation_long_statement"],
            [4],
        )

    def test_docker_improper_alignment(self) -> None:
        # TODO: Fix smell, due to docker parsing method the attributes are not
        # detected in differents lines, making it impossible to trigger alignment
        pass
        # self.__help_test(
        #     "tests/design/docker/files/improper_alignment.Dockerfile",
        #     1,
        #     [
        #         "implementation_improper_alignment"
        #     ], [1]
        # )

    def test_docker_duplicate_block(self) -> None:
        self.__help_test(
            "tests/design/docker/files/duplicate_block.Dockerfile",
            2,
            [
                "design_duplicate_block",
                "design_duplicate_block",
            ],
            [1, 9],
        )

    def test_docker_avoid_comments(self) -> None:
        self.__help_test(
            "tests/design/docker/files/avoid_comments.Dockerfile",
            1,
            [
                "design_avoid_comments",
            ],
            [1],
        )

    def test_docker_too_many_variables(self) -> None:
        self.__help_test(
            "tests/design/docker/files/too_many_variables.Dockerfile",
            1,
            [
                "implementation_too_many_variables",
            ],
            [1],
        )
