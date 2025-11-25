from tests.design.design_helper import BaseDesignTest
from glitch.tech import Tech

class TestDesign(BaseDesignTest):
    TECH = Tech.puppet

    def test_puppet_long_statement(self) -> None:
        self._help_test(
            "tests/design/puppet/files/long_statement.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            ["implementation_long_statement"],
            [6],
        )

    def test_puppet_improper_alignment(self) -> None:
        self._help_test(
            "tests/design/puppet/files/improper_alignment.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            ["implementation_improper_alignment"],
            [1],
        )

    def test_puppet_duplicate_block(self) -> None:
        self._help_test(
            "tests/design/puppet/files/duplicate_block.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            2,
            [
                "design_duplicate_block",
                "design_duplicate_block",
            ],
            [1, 10],
        )

    def test_puppet_avoid_comments(self) -> None:
        self._help_test(
            "tests/design/puppet/files/avoid_comments.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            [
                "design_avoid_comments",
            ],
            [5],
        )

    def test_puppet_long_resource(self) -> None:
        self._help_test(
            "tests/design/puppet/files/long_resource.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            [
                "design_long_resource",
            ],
            [1],
        )

    def test_puppet_multifaceted_abstraction(self) -> None:
        self._help_test(
            "tests/design/puppet/files/multifaceted_abstraction.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            2,
            ["design_multifaceted_abstraction", "implementation_long_statement"],
            [1, 2],
        )

    def test_puppet_unguarded_variable(self) -> None:
        self._help_test(
            "tests/design/puppet/files/unguarded_variable.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            [
                "implementation_unguarded_variable",
            ],
            [12],
        )

    def test_puppet_misplaced_attribute(self) -> None:
        self._help_test(
            "tests/design/puppet/files/misplaced_attribute.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            [
                "design_misplaced_attribute",
            ],
            [1],
        )

    def test_puppet_too_many_variables(self) -> None:
        self._help_test(
            "tests/design/puppet/files/too_many_variables.pp",
            "script",
            "tests/design/puppet/design_puppet.ini",
            1,
            [
                "implementation_too_many_variables",
            ],
            [1],
        )
