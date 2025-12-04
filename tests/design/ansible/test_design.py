from tests.design.design_helper import BaseDesignTest
from glitch.tech import Tech
from glitch.repr.inter import UNDEFINED_POSITION


class TestDesign(BaseDesignTest):
    TECH = Tech.ansible
    
    def test_ansible_long_statement(self) -> None:
        self._help_test(
            "tests/design/ansible/files/long_statement.yml",
            "tasks",
            "tests/design/ansible/design_ansible.ini",
            1,
            ["implementation_long_statement"],
            [16],
        )

    # Tabs
    def test_ansible_improper_alignment(self) -> None:
        self._help_test(
            "tests/design/ansible/files/improper_alignment.yml",
            "tasks",
            "tests/design/ansible/design_ansible.ini",
            4,
            [
                "design_multifaceted_abstraction",
                "implementation_improper_alignment",
                "implementation_improper_alignment",
                "implementation_improper_alignment",
            ],
            [2, 4, 5, 6],
        )

    def test_ansible_duplicate_block(self) -> None:
        self._help_test(
            "tests/design/ansible/files/duplicate_block.yml",
            "tasks",
            "tests/design/ansible/design_ansible.ini",
            4,
            [
                "design_duplicate_block",
                "design_duplicate_block",
                "design_duplicate_block",
                "design_duplicate_block",
            ],
            [2, 10, 25, 33],
        )

    def test_ansible_avoid_comments(self) -> None:
        self._help_test(
            "tests/design/ansible/files/avoid_comments.yml",
            "tasks",
            "tests/design/ansible/design_ansible.ini",
            1,
            [
                "design_avoid_comments",
            ],
            [11],
        )

    def test_ansible_long_resource(self) -> None:
        self._help_test(
            "tests/design/ansible/files/long_resource.yml",
            "tasks",
            "tests/design/ansible/design_ansible.ini",
            2,
            [
                "design_long_resource",
                "design_multifaceted_abstraction",
            ],
            [2, 2],
        )

    def test_ansible_multifaceted_abstraction(self) -> None:
        self._help_test(
            "tests/design/ansible/files/multifaceted_abstraction.yml",
            "tasks",
            "tests/design/ansible/design_ansible.ini",
            1,
            [
                "design_multifaceted_abstraction",
            ],
            [2, 2],
        )

    def test_ansible_too_many_variables(self) -> None:
        self._help_test(
            "tests/design/ansible/files/too_many_variables.yml",
            "script",
            "tests/design/ansible/design_ansible.ini",
            1,
            [
                "implementation_too_many_variables",
            ],
            [UNDEFINED_POSITION],
        )
