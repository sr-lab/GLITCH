from glitch.parsers.puppet import PuppetParser
from glitch.repr.inter import *
from glitch.tests.parser.test_parser import TestParser


class TestPuppetParser(TestParser):
    def test_puppet_parser_if(self) -> None:
        """
        If | Resource | Attribute | str | VariableReference | Assignment
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/if.pp", UnitBlockType.script
        )
        assert len(unit_block.statements) == 1
        assert isinstance(unit_block.statements[0], ConditionalStatement)
        self._check_binary_operation(
            unit_block.statements[0].condition,
            Equal,
            VariableReference("x", ElementInfo(5, 4, 5, 6, "$x")),
            String("absent", ElementInfo(5, 10, 5, 18, "absent")),
            5,
            4,
            5,
            18,
        )

        assert len(unit_block.statements[0].statements) == 1
        assert isinstance(unit_block.statements[0].statements[0], AtomicUnit)
        atomic_unit = unit_block.statements[0].statements[0]
        assert len(atomic_unit.attributes) == 1
        assert atomic_unit.attributes[0].name == "ensure"
        self._check_value(
            atomic_unit.attributes[0].value, VariableReference, "absent", 7, 20, 7, 26
        )
        assert atomic_unit.attributes[0].line == 7
        assert atomic_unit.attributes[0].end_line == 7
        assert atomic_unit.attributes[0].column == 9
        assert atomic_unit.attributes[0].end_column == 26

        assert unit_block.statements[0].else_statement is not None
        assert isinstance(unit_block.statements[0].else_statement, ConditionalStatement)

        assert len(unit_block.statements[0].else_statement.statements) == 1
        assert isinstance(
            unit_block.statements[0].else_statement.statements[0], AtomicUnit
        )
        atomic_unit = unit_block.statements[0].else_statement.statements[0]
        assert len(atomic_unit.attributes) == 1
        assert atomic_unit.attributes[0].name == "ensure"
        self._check_value(
            atomic_unit.attributes[0].value,
            VariableReference,
            "present",
            11,
            20,
            11,
            27,
        )
        assert atomic_unit.attributes[0].line == 11
        assert atomic_unit.attributes[0].end_line == 11
        assert atomic_unit.attributes[0].column == 9
        assert atomic_unit.attributes[0].end_column == 27

        assert len(unit_block.variables) == 1
        assert unit_block.variables[0].name == "test"
        self._check_value(
            unit_block.variables[0].value, String, "\n    test 123\n", 1, 9, 3, 7
        )
        assert unit_block.variables[0].line == 1
        assert unit_block.variables[0].end_line == 3
        assert unit_block.variables[0].column == 1
        assert unit_block.variables[0].end_column == 7

    def test_puppet_parser_defined_resource(self) -> None:
        """
        User-defined Resource | Function Call | Resource Reference
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/defined_resource.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert isinstance(unit_block, UnitBlock)
        assert len(unit_block.unit_blocks) == 1

        assert unit_block.unit_blocks[0].type == UnitBlockType.definition
        assert unit_block.unit_blocks[0].name == "apache::vhost"
        assert len(unit_block.unit_blocks[0].attributes) == 2

        assert unit_block.unit_blocks[0].attributes[0].name == "port"
        assert unit_block.unit_blocks[0].attributes[0].value == Null()

        assert unit_block.unit_blocks[0].attributes[1].name == "servername"
        self._check_value(
            unit_block.unit_blocks[0].attributes[1].value,
            VariableReference,
            "title",
            3,
            27,
            3,
            33,
        )

        assert len(unit_block.unit_blocks[0].atomic_units) == 1
        assert isinstance(unit_block.unit_blocks[0].atomic_units[0].name, Sum)

        assert unit_block.unit_blocks[0].atomic_units[0].type == "file"

        attribute = unit_block.unit_blocks[0].atomic_units[0].attributes[4]
        assert attribute.name == "content"
        self._check_value(attribute.value, FunctionCall, "template", 12, 16, 12, 57)
        assert isinstance(attribute.value, FunctionCall)
        assert len(attribute.value.args) == 1
        self._check_value(
            attribute.value.args[0],
            String,
            "apache/vhost-default.conf.erb",
            12,
            25,
            12,
            56,
        )

        # TODO: Support resource reference
        attribute = unit_block.unit_blocks[0].atomic_units[0].attributes[5]
        assert attribute.name == "require"
        self._check_value(attribute.value, Null, None, 4294967296, 4294967296, 4294967296, 4294967296)

    def test_puppet_parser_class(self) -> None:
        """
        Class | str
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/class.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert isinstance(unit_block, UnitBlock)
        assert len(unit_block.unit_blocks) == 1

        assert unit_block.unit_blocks[0].type == UnitBlockType.definition
        assert unit_block.unit_blocks[0].name == "apache"
        assert len(unit_block.unit_blocks[0].attributes) == 1

        assert isinstance(unit_block.unit_blocks[0].attributes[0], Attribute)
        assert unit_block.unit_blocks[0].attributes[0].name == "version"
        self._check_value(
            unit_block.unit_blocks[0].attributes[0].value,
            String,
            "latest",
            1,
            33,
            1,
            41,
        )

        assert len(unit_block.unit_blocks[0].atomic_units) == 1
        self._check_value(
            unit_block.unit_blocks[0].atomic_units[0].name,
            VariableReference,
            "httpd",
            2,
            13,
            2,
            19,
        )
        assert unit_block.unit_blocks[0].atomic_units[0].type == "package"
        assert isinstance(
            unit_block.unit_blocks[0].atomic_units[0].attributes[0].value,
            VariableReference,
        )

    def test_puppet_parser_values(self) -> None:
        """
        String interpolation | Integer | Float | Bool | Null | Array | Hash
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/values.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert isinstance(unit_block, UnitBlock)
        assert len(unit_block.variables) == 8

        assert unit_block.variables[0].name == "x"

        assert unit_block.variables[1].name == "y"
        self._check_value(unit_block.variables[1].value, Integer, 2, 2, 6, 2, 7)

        assert unit_block.variables[2].name == "string_interpolation"
        self._check_binary_operation(
            unit_block.variables[2].value,
            Sum,
            Sum(
                ElementInfo(3, 28, 3, 35, ""),
                VariableReference("x", ElementInfo(3, 28, 3, 30, "x")),
                VariableReference("y", ElementInfo(3, 33, 3, 35, "y")),
            ),
            String(" World", ElementInfo(3, 36, 3, 42, " World")),
            3,
            25,
            3,
            43,
        )
        assert isinstance(unit_block.variables[2].value, Sum)
        self._check_binary_operation(
            unit_block.variables[2].value.left,
            Sum,
            VariableReference("x", ElementInfo(3, 28, 3, 30, "$x")),
            VariableReference("y", ElementInfo(3, 33, 3, 35, "$y")),
            3,
            28,
            3,
            35,
        )

        assert unit_block.variables[3].name == "z"
        self._check_value(unit_block.variables[3].value, Float, 2.0, 4, 6, 4, 9)

        assert unit_block.variables[4].name == "w"
        self._check_value(unit_block.variables[4].value, Boolean, True, 5, 6, 5, 10)

        assert unit_block.variables[5].name == "h"
        self._check_value(unit_block.variables[5].value, Null, None, 6, 6, 6, 11)

        assert unit_block.variables[6].name == "a"
        assert isinstance(unit_block.variables[6].value, Array)
        assert len(unit_block.variables[6].value.value) == 3
        self._check_value(
            unit_block.variables[6].value.value[0], Integer, 1, 7, 7, 7, 8
        )
        self._check_value(
            unit_block.variables[6].value.value[1], Integer, 2, 7, 10, 7, 11
        )
        self._check_value(
            unit_block.variables[6].value.value[2], Integer, 3, 7, 13, 7, 14
        )

        assert unit_block.variables[7].name == "hash"
        assert isinstance(unit_block.variables[7].value, Hash)
        assert len(unit_block.variables[7].value.value) == 2

    def test_puppet_parser_node(self) -> None:
        """
        Node | Include | Require | Contain | Debug/Fail/Realize/Tag
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/node.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert isinstance(unit_block, UnitBlock)
        assert len(unit_block.unit_blocks) == 1

        assert unit_block.unit_blocks[0].type == UnitBlockType.block
        assert unit_block.unit_blocks[0].name == "node"

        assert len(unit_block.unit_blocks[0].dependencies) == 3
        assert unit_block.unit_blocks[0].dependencies[0].names == ["common"]
        assert unit_block.unit_blocks[0].dependencies[1].names == ["apache"]
        assert unit_block.unit_blocks[0].dependencies[2].names == ["squid"]

        assert len(unit_block.unit_blocks[0].statements) == 0

    def test_puppet_parser_unless(self) -> None:
        """
        Unless
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/unless.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert len(unit_block.statements) == 1

        assert isinstance(unit_block.statements[0], ConditionalStatement)
        assert isinstance(unit_block.statements[0].condition, Not)
        self._check_binary_operation(
            unit_block.statements[0].condition.expr,
            GreaterThan,
            VariableReference("x", ElementInfo(1, 8, 1, 10, "$x")),
            Integer(1073741824, ElementInfo(1, 13, 1, 23, "1073741824")),
            1,
            8,
            1,
            23,
        )
        assert len(unit_block.statements[0].statements) == 1
        assert isinstance(unit_block.statements[0].statements[0], Variable)

    def test_puppet_parser_case(self) -> None:
        """
        Case | Resource Collector | Chaining
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/case.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert len(unit_block.statements) == 1

        assert isinstance(unit_block.statements[0], ConditionalStatement)
        assert isinstance(unit_block.statements[0].condition, Or)

        assert isinstance(unit_block.statements[0].condition.left, Equal)
        assert isinstance(unit_block.statements[0].condition.left.left, Access)
        assert isinstance(unit_block.statements[0].condition.left.right, String)

        assert isinstance(unit_block.statements[0].condition.right, Equal)
        assert isinstance(unit_block.statements[0].condition.right.left, Access)
        assert isinstance(unit_block.statements[0].condition.right.right, String)

        assert len(unit_block.statements[0].statements) == 2
        assert isinstance(unit_block.statements[0].statements[0], Null)
        assert isinstance(unit_block.statements[0].statements[1], AtomicUnit)

        assert isinstance(unit_block.statements[0].else_statement, ConditionalStatement)
        assert isinstance(unit_block.statements[0].else_statement.condition, Null)
        assert len(unit_block.statements[0].else_statement.statements) == 1
        assert isinstance(unit_block.statements[0].else_statement.statements[0], Null)

    def test_puppet_parser_selector(self) -> None:
        """
        Selector | Function
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/selector.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert len(unit_block.unit_blocks) == 1

        assert unit_block.unit_blocks[0].type == UnitBlockType.function

        unit_block = unit_block.unit_blocks[0]
        assert len(unit_block.variables) == 1

        assert isinstance(unit_block.variables[0].value, ConditionalStatement)
        assert isinstance(unit_block.variables[0].value.condition, Equal)

        assert isinstance(
            unit_block.variables[0].value.condition.left, VariableReference
        )
        assert isinstance(unit_block.variables[0].value.condition.right, String)

        assert len(unit_block.variables[0].value.statements) == 1
        assert isinstance(unit_block.variables[0].value.statements[0], String)

        assert unit_block.variables[0].value.else_statement is not None
        assert isinstance(
            unit_block.variables[0].value.else_statement, ConditionalStatement
        )
        assert isinstance(unit_block.variables[0].value.else_statement.condition, Null)
        assert len(unit_block.variables[0].value.else_statement.statements) == 1
        assert isinstance(
            unit_block.variables[0].value.else_statement.statements[0], String
        )

    def test_puppet_parser_special_resources(self) -> None:
        """
        Class as resource | Resource expressions
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/special_resource.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert len(unit_block.atomic_units) == 3
        assert len(unit_block.unit_blocks) == 3

        self._check_value(
            unit_block.atomic_units[0].name, String, "apache", 1, 8, 1, 16
        )
        assert unit_block.atomic_units[0].type == "class"
        assert len(unit_block.atomic_units[0].attributes) == 1
        assert unit_block.atomic_units[0].attributes[0].name == "version"
        self._check_value(
            unit_block.atomic_units[0].attributes[0].value,
            String,
            "2.2.21",
            2,
            14,
            2,
            22,
        )

        assert (
            unit_block.atomic_units[1].type
            == "Exec <| title == 'modprobe nf_conntrack_proto_sctp' |>"
        )
        assert unit_block.atomic_units[2].type == "Exec"

        assert unit_block.unit_blocks[0].type == UnitBlockType.block
        assert unit_block.unit_blocks[0].name == "resource_expression"
        assert len(unit_block.unit_blocks[0].atomic_units) == 2
        self._check_value(
            unit_block.unit_blocks[0].atomic_units[0].name,
            String,
            "apache-2",
            6,
            3,
            6,
            13,
        )
        assert unit_block.unit_blocks[0].atomic_units[0].type == "class"
        self._check_value(
            unit_block.unit_blocks[0].atomic_units[1].name,
            String,
            "apache-3",
            9,
            3,
            9,
            13,
        )
        assert unit_block.unit_blocks[0].atomic_units[1].type == "class"

        assert unit_block.unit_blocks[1].type == UnitBlockType.block
        assert unit_block.unit_blocks[1].name == "resource_expression"
        assert len(unit_block.unit_blocks[1].atomic_units) == 2

        self._check_value(
            unit_block.unit_blocks[1].atomic_units[0].name,
            String,
            "ssh_host_dsa_key",
            19,
            4,
            19,
            22,
        )
        assert len(unit_block.unit_blocks[1].atomic_units[0].attributes) == 3
        assert unit_block.unit_blocks[1].atomic_units[0].attributes[0].name == "ensure"
        self._check_value(
            unit_block.unit_blocks[1].atomic_units[0].attributes[0].value,
            VariableReference,
            "file",
            15,
            15,
            15,
            19,
        )
        assert unit_block.unit_blocks[1].atomic_units[0].attributes[1].name == "owner"
        self._check_value(
            unit_block.unit_blocks[1].atomic_units[0].attributes[1].value,
            String,
            "root",
            16,
            15,
            16,
            21,
        )
        assert unit_block.unit_blocks[1].atomic_units[0].attributes[2].name == "mode"
        self._check_value(
            unit_block.unit_blocks[1].atomic_units[0].attributes[2].value,
            String,
            "0600",
            17,
            15,
            17,
            21,
        )

        self._check_value(
            unit_block.unit_blocks[1].atomic_units[1].name,
            String,
            "ssh_config",
            22,
            4,
            22,
            16,
        )
        assert len(unit_block.unit_blocks[1].atomic_units[1].attributes) == 4
        assert unit_block.unit_blocks[1].atomic_units[1].attributes[0].name == "mode"
        self._check_value(
            unit_block.unit_blocks[1].atomic_units[1].attributes[0].value,
            String,
            "0644",
            23,
            14,
            23,
            20,
        )
        assert unit_block.unit_blocks[1].atomic_units[1].attributes[1].name == "group"

        assert isinstance(unit_block.unit_blocks[2], UnitBlock)
        assert unit_block.unit_blocks[2].type == UnitBlockType.block
        assert unit_block.unit_blocks[2].name == "resource_expression"
        assert len(unit_block.unit_blocks[2].atomic_units) == 2

        self._check_value(
            unit_block.unit_blocks[2].atomic_units[0].name,
            String,
            "armitage",
            28,
            12,
            28,
            22,
        )
        self._check_value(
            unit_block.unit_blocks[2].atomic_units[1].name,
            String,
            "metasploit",
            28,
            24,
            28,
            36,
        )

    def test_puppet_parser_operations(self) -> None:
        """
        All operations
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/operations.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert len(unit_block.variables) == 19
        for i in range(18):
            assert unit_block.variables[i].name == f"x"
        assert isinstance(unit_block.variables[0].value, Equal)
        assert isinstance(unit_block.variables[1].value, NotEqual)
        assert isinstance(unit_block.variables[2].value, And)
        assert isinstance(unit_block.variables[3].value, Or)
        assert isinstance(unit_block.variables[4].value, Not)
        assert isinstance(unit_block.variables[5].value, LessThan)
        assert isinstance(unit_block.variables[6].value, LessThanOrEqual)
        assert isinstance(unit_block.variables[7].value, GreaterThan)
        assert isinstance(unit_block.variables[8].value, GreaterThanOrEqual)
        assert isinstance(unit_block.variables[9].value, In)
        assert isinstance(unit_block.variables[10].value, Subtract)
        assert isinstance(unit_block.variables[11].value, Sum)
        assert isinstance(unit_block.variables[12].value, Multiply)
        assert isinstance(unit_block.variables[13].value, Divide)
        assert isinstance(unit_block.variables[14].value, Modulo)
        assert isinstance(unit_block.variables[15].value, RightShift)
        assert isinstance(unit_block.variables[16].value, LeftShift)
        assert isinstance(unit_block.variables[17].value, Access)

    def test_puppet_parser_edge_case(self) -> None:
        """
        The name _user_owner used to crash the parser
        """
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/edge_case.pp", UnitBlockType.script
        )
        assert unit_block is not None
        assert len(unit_block.unit_blocks) == 1
