from glitch.parsers.ansible import AnsibleParser
from glitch.repr.inter import *
from glitch.tests.parser.test_parser import TestParser


class TestAnsibleParser(TestParser):
    def test_ansible_parser_valid_tasks(self) -> None:
        """
        Value in another line
        String interpolation (Variable reference)
        In-line list
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/valid_tasks.yml", UnitBlockType.tasks
        )
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.tasks
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        self._check_value(
            ir.atomic_units[0].name, String, "Get machine-id", 2, 9, 2, 23
        )
        assert ir.atomic_units[0].type == "shell"
        assert len(ir.atomic_units[0].attributes) == 4

        assert ir.atomic_units[0].attributes[0].name == "shell"

        assert isinstance(ir.atomic_units[0].attributes[0].value, Sum)
        assert isinstance(ir.atomic_units[0].attributes[0].value.left, BinaryOperation)
        self._check_value(
            ir.atomic_units[0].attributes[0].value.left.left,
            String,
            'hostnamectl --machine="',
            4,
            5,
            4,
            28,
        )
        assert isinstance(
            ir.atomic_units[0].attributes[0].value.left.right, VariableReference
        )
        self._check_value(
            ir.atomic_units[0].attributes[0].value.left.right,
            VariableReference,
            "inventory_hostname",
            4,
            31,
            4,
            49,
        )
        assert isinstance(ir.atomic_units[0].attributes[0].value.right, String)
        self._check_value(
            ir.atomic_units[0].attributes[0].value.right,
            String,
            "\" status | awk '/Machine ID/ {print $3}'",
            4,
            52,
            4,
            92,
        )

        assert ir.atomic_units[0].attributes[0].line == 3
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 5
        assert ir.atomic_units[0].attributes[0].end_column == 1

        assert ir.atomic_units[0].attributes[1].name == "register"
        self._check_value(
            ir.atomic_units[0].attributes[1].value,
            String,
            "_container_machine_id",
            5,
            13,
            5,
            34,
        )
        assert ir.atomic_units[0].attributes[1].line == 5
        assert ir.atomic_units[0].attributes[1].column == 3
        assert ir.atomic_units[0].attributes[1].end_line == 5
        assert ir.atomic_units[0].attributes[1].end_column == 34

        assert ir.atomic_units[0].attributes[2].name == "delegate_to"
        self._check_value(
            ir.atomic_units[0].attributes[2].value,
            VariableReference,
            "physical_host",
            6,
            20,
            6,
            33,
        )
        assert ir.atomic_units[0].attributes[2].line == 6
        assert ir.atomic_units[0].attributes[2].column == 3
        assert ir.atomic_units[0].attributes[2].end_line == 6
        assert ir.atomic_units[0].attributes[2].end_column == 37

        assert ir.atomic_units[0].attributes[3].name == "test"
        assert isinstance(ir.atomic_units[0].attributes[3].value, Hash)
        assert len(ir.atomic_units[0].attributes[3].value.value) == 1
        assert (
            String("executable", ElementInfo(8, 5, 8, 15, "executable"))
            in ir.atomic_units[0].attributes[3].value.value
        )

        executable_value = (
            ir.atomic_units[0]
            .attributes[3]
            .value.value[String("executable", ElementInfo(8, 5, 8, 15, "executable"))]
        )
        assert isinstance(executable_value, Array)
        assert len(executable_value.value) == 2

        self._check_value(executable_value.value[0], String, "/bin/bash", 8, 18, 8, 29)
        self._check_value(executable_value.value[1], String, "/bin/shell", 8, 31, 8, 43)

    def test_ansible_parser_valid_playbook_vars(self) -> None:
        """
        String interpolation (Variable reference)
        String in another line
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/valid_playbook_vars.yml", UnitBlockType.script
        )
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert len(ir.unit_blocks[0].variables) == 2

        assert ir.unit_blocks[0].variables[0].name == "aqua_admin_password"
        assert isinstance(ir.unit_blocks[0].variables[0].value, FunctionCall)
        assert ir.unit_blocks[0].variables[0].value.name == "lookup"
        assert len(ir.unit_blocks[0].variables[0].value.args) == 2
        self._check_value(
            ir.unit_blocks[0].variables[0].value.args[0],
            String,
            "env",
            6,
            37,
            6,
            42,
        )
        self._check_value(
            ir.unit_blocks[0].variables[0].value.args[1],
            String,
            "AQUA_ADMIN_PASSWORD",
            6,
            44,
            6,
            65,
        )
        assert ir.unit_blocks[0].variables[0].line == 6
        assert ir.unit_blocks[0].variables[0].column == 5
        assert ir.unit_blocks[0].variables[0].end_line == 6
        assert ir.unit_blocks[0].variables[0].end_column == 70

        assert ir.unit_blocks[0].variables[1].name == "aqua_sso_client_secret"
        assert isinstance(ir.unit_blocks[0].variables[1].value, FunctionCall)
        assert ir.unit_blocks[0].variables[1].value.name == "lookup"
        assert len(ir.unit_blocks[0].variables[1].value.args) == 2
        self._check_value(
            ir.unit_blocks[0].variables[1].value.args[0],
            String,
            "env",
            8,
            18,
            8,
            23,
        )
        self._check_value(
            ir.unit_blocks[0].variables[1].value.args[1],
            String,
            "AQUA_SSO_CLIENT_SECRET",
            8,
            25,
            8,
            49,
        )
        assert ir.unit_blocks[0].variables[1].line == 7
        assert ir.unit_blocks[0].variables[1].column == 5
        assert ir.unit_blocks[0].variables[1].end_line == 9
        assert ir.unit_blocks[0].variables[1].end_column == 1

    def test_ansible_parser_valid_playbook_hierarchical_vars(self) -> None:
        """
        Hierarchical variables
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/valid_playbook_hierarchical_vars.yml",
            UnitBlockType.script,
        )
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert len(ir.unit_blocks[0].variables) == 1

        assert ir.unit_blocks[0].variables[0].name == "aqua_admin"
        assert isinstance(ir.unit_blocks[0].variables[0].value, Hash)
        assert ir.unit_blocks[0].variables[0].line == 6
        assert ir.unit_blocks[0].variables[0].column == 5
        assert ir.unit_blocks[0].variables[0].end_line == 7
        assert ir.unit_blocks[0].variables[0].end_column == 19

        assert (
            String("user", ElementInfo(7, 7, 7, 11, "user"))
            in ir.unit_blocks[0].variables[0].value.value
        )
        self._check_value(
            ir.unit_blocks[0]
            .variables[0]
            .value.value[String("user", ElementInfo(7, 7, 7, 11, "user"))],
            String,
            "test",
            7,
            13,
            7,
            19,
        )

    def test_ansible_parser_valid_playbook_vars_list(self) -> None:
        """
        Hierarchical variables with list
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/valid_playbook_vars_list.yml",
            UnitBlockType.script,
        )
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert len(ir.unit_blocks[0].variables) == 1

        assert isinstance(ir.unit_blocks[0].variables[0].value, Array)
        assert len(ir.unit_blocks[0].variables[0].value.value) == 2

        assert isinstance(ir.unit_blocks[0].variables[0].value.value[0], Hash)
        assert len(ir.unit_blocks[0].variables[0].value.value[0].value) == 1
        assert (
            String("user", ElementInfo(7, 9, 7, 13, "user"))
            in ir.unit_blocks[0].variables[0].value.value[0].value
        )
        self._check_value(
            ir.unit_blocks[0]
            .variables[0]
            .value.value[0]
            .value[String("user", ElementInfo(7, 9, 7, 13, "user"))],
            String,
            "test1",
            7,
            15,
            7,
            20,
        )

        assert isinstance(ir.unit_blocks[0].variables[0].value.value[1], Hash)
        assert len(ir.unit_blocks[0].variables[0].value.value[1].value) == 1
        assert (
            String("user", ElementInfo(8, 9, 8, 13, "user"))
            in ir.unit_blocks[0].variables[0].value.value[1].value
        )
        self._check_value(
            ir.unit_blocks[0]
            .variables[0]
            .value.value[1]
            .value[String("user", ElementInfo(8, 9, 8, 13, "user"))],
            String,
            "test2",
            8,
            15,
            8,
            20,
        )

    def test_ansible_parser_valid_vars(self) -> None:
        """
        In-line lists
        Regular lists
        Null
        Integer, Float and Boolean
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/valid_vars.yml", UnitBlockType.vars
        )
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.vars
        assert len(ir.variables) == 7

        assert ir.variables[0].name == "aqua_admin_users"
        self._check_value(
            ir.variables[0].value,
            Array,
            [
                String("test1", ElementInfo(3, 5, 3, 12, "test1")),
                String("test2", ElementInfo(4, 5, 4, 12, "test2")),
            ],
            3,
            3,
            5,
            1,
        )
        assert ir.variables[0].line == 2
        assert ir.variables[0].column == 1
        assert ir.variables[0].end_line == 5
        assert ir.variables[0].end_column == 1

        assert ir.variables[1].name == "aqua_admin_passwords"
        self._check_value(
            ir.variables[1].value,
            Array,
            [
                String("test1", ElementInfo(5, 24, 5, 31, "test1")),
                String("test2", ElementInfo(5, 33, 5, 40, "test2")),
            ],
            5,
            23,
            5,
            41,
        )
        assert ir.variables[1].line == 5
        assert ir.variables[1].column == 1
        assert ir.variables[1].end_line == 5
        assert ir.variables[1].end_column == 41

        assert ir.variables[2].name == "test"
        self._check_value(ir.variables[2].value, Null, None, 6, 7, 6, 8)

        assert ir.variables[3].name == "test_2"
        self._check_value(ir.variables[3].value, Null, None, 7, 9, 7, 13)

        assert ir.variables[4].name == "test_3"
        self._check_value(ir.variables[4].value, Float, 1.0, 8, 9, 8, 12)

    def test_ansible_parser_valid_vars_interpolation(self) -> None:
        """
        String interpolation with filter
        String interpolation with string/list inside
        String interpolation with sum
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/valid_vars_interpolation.yml",
            UnitBlockType.vars,
        )
        assert ir is not None

        assert len(ir.variables) == 4

        assert ir.variables[0].name == "with_filter"
        self._check_value(
            ir.variables[0].value,
            VariableReference,
            "var",
            2,
            18,
            2,
            21,
        )

        assert ir.variables[1].name == "with_string"
        self._check_value(
            ir.variables[1].value,
            String,
            "string",
            3,
            18,
            3,
            26,
        )

        assert ir.variables[2].name == "with_list"
        assert isinstance(ir.variables[2].value, Array)
        assert len(ir.variables[2].value.value) == 3
        self._check_value(
            ir.variables[2].value.value[0],
            Integer,
            1,
            4,
            17,
            4,
            18,
        )

        assert ir.variables[3].name == "with_sum"
        assert isinstance(ir.variables[3].value, Sum)
        assert isinstance(ir.variables[3].value.left, Sum)
        self._check_value(
            ir.variables[3].value.left.left,
            VariableReference,
            "var",
            5,
            15,
            5,
            18,
        )
        self._check_value(
            ir.variables[3].value.left.right,
            String,
            "string",
            5,
            21,
            5,
            29,
        )
        self._check_value(
            ir.variables[3].value.right,
            Integer,
            1,
            5,
            32,
            5,
            33,
        )

    def test_ansible_parser_node_not_supported(self) -> None:
        """
        This file used to throw node not supported
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/node_not_supported.yml",
            UnitBlockType.tasks,
        )
        assert ir is not None

    def test_ansible_parser_become(self) -> None:
        """
        Ensures that the type of the atomic unit is not become
        """
        p = AnsibleParser()
        ir = p.parse_file(
            "tests/parser/ansible/files/become.yml",
            UnitBlockType.tasks,
        )
        assert ir is not None
        assert len(ir.atomic_units) == 1
        assert ir.atomic_units[0].type == "command"
