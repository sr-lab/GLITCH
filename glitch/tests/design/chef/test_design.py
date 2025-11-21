from glitch.tests.design.design_helper import BaseSecurityTest
from glitch.parsers.chef import ChefParser
from glitch.tech import Tech

class TestDesign(BaseSecurityTest):
    PARSER_CLASS = ChefParser
    TECH = Tech.chef

    def test_chef_long_statement(self) -> None:
        self._help_test(
            "tests/design/chef/files/long_statement.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            ["implementation_long_statement"],
            [6],
        )

    def test_chef_improper_alignment(self) -> None:
        self._help_test(
            "tests/design/chef/files/improper_alignment.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            ["implementation_improper_alignment"],
            [1],
        )

    def test_chef_duplicate_block(self) -> None:
        self._help_test(
            "tests/design/chef/files/duplicate_block.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            4,
            [
                "design_duplicate_block",
                "implementation_long_statement",
                "design_duplicate_block",
                "implementation_long_statement",
            ],
            [3, 4, 9, 10],
        )

    def test_chef_avoid_comments(self) -> None:
        self._help_test(
            "tests/design/chef/files/avoid_comments.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            [
                "design_avoid_comments",
            ],
            [7],
        )

    def test_chef_long_resource(self) -> None:
        self._help_test(
            "tests/design/chef/files/long_resource.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            [
                "design_long_resource",
            ],
            [1],
        )

    def test_chef_multifaceted_abstraction(self) -> None:
        self._help_test(
            "tests/design/chef/files/multifaceted_abstraction.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            [
                "design_multifaceted_abstraction",
            ],
            [1],
        )

    def test_chef_misplaced_attribute(self) -> None:
        self._help_test(
            "tests/design/chef/files/misplaced_attribute.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            [
                "design_misplaced_attribute",
            ],
            [1],
        )

    def test_chef_too_many_variables(self) -> None:
        self._help_test(
            "tests/design/chef/files/too_many_variables.rb",
            "script",
            "tests/design/chef/design_chef.ini",
            1,
            [
                "implementation_too_many_variables",
            ],
            [-33550336],
        )
