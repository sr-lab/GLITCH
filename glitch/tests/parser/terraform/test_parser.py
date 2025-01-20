from glitch.parsers.terraform import TerraformParser
from glitch.repr.inter import *
from glitch.tests.parser.test_parser import TestParser


class TestTerraform(TestParser):
    def __parse(self, path: str) -> UnitBlock:
        p = TerraformParser()
        ir = p.parse_file(path, UnitBlockType.script)
        assert ir is not None
        assert isinstance(ir, UnitBlock)
        return ir

    def test_terraform_parser_null_value(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/null_value_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        self._check_value(ir.atomic_units[0].name, String, "bqowner", 1, 35, 1, 44)
        assert ir.atomic_units[0].type == "google_service_account"

        assert ir.atomic_units[0].attributes[0].name == "account_id"
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 2
        assert ir.atomic_units[0].attributes[0].end_column == 20
        assert isinstance(ir.atomic_units[0].attributes[0].value, Null)
        assert ir.atomic_units[0].attributes[0].value.line == 2
        assert ir.atomic_units[0].attributes[0].value.column == 16
        assert ir.atomic_units[0].attributes[0].value.end_line == 2
        assert ir.atomic_units[0].attributes[0].value.end_column == 20

    def test_terraform_parser_empty_string(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/empty_string_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        self._check_value(
            ir.atomic_units[0].name, String, "bqowner", 1, 35, 1, 44
        )
        assert ir.atomic_units[0].type == "google_service_account"

        assert ir.atomic_units[0].attributes[0].name == "account_id"
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 2
        assert ir.atomic_units[0].attributes[0].end_column == 18
        self._check_value(
            ir.atomic_units[0].attributes[0].value, String, "", 2, 16, 2, 18
        )

    def test_terraform_parser_boolean_value(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/boolean_value_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        self._check_value(
            ir.atomic_units[0].name, String, "bqowner", 1, 35, 1, 44
        )
        assert ir.atomic_units[0].type == "google_service_account"

        assert ir.atomic_units[0].attributes[0].name == "account_id"

        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 2
        assert ir.atomic_units[0].attributes[0].end_column == 20
        self._check_value(
            ir.atomic_units[0].attributes[0].value, Boolean, True, 2, 16, 2, 20
        )

    def test_terraform_parser_multiline_string(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/multiline_string_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        self._check_value(
            ir.atomic_units[0].name, String, "example", 1, 25, 1, 34
        )
        assert ir.atomic_units[0].type == "aws_instance"

        assert ir.atomic_units[0].attributes[0].name == "user_data"
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 7
        assert ir.atomic_units[0].attributes[0].end_column == 6
        self._check_value(
            ir.atomic_units[0].attributes[0].value,
            String,
            "    #!/bin/bash\n    sudo apt-get update\n    sudo apt-get install -y apache2\n    sudo systemctl start apache2",
            2,
            19,
            7,
            6,
        )

    def test_terraform_parser_value_has_variable(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/value_has_variable.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 3
        self._check_value(
            ir.atomic_units[0].name, String, "dataset", 1, 36, 1, 45
        )
        assert ir.atomic_units[0].type == "google_bigquery_dataset"

        assert ir.atomic_units[0].attributes[0].name == "test"
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 2
        assert ir.atomic_units[0].attributes[0].end_column == 31
        self._check_binary_operation(
            ir.atomic_units[0].attributes[0].value,
            Sum,
            String("test ", ElementInfo(2, 12, 2, 17, "test ")),
            Access(
                ElementInfo(2, 19, 2, 29, "var.value1"),
                VariableReference("var", ElementInfo(2, 19, 2, 22, "var")),
                VariableReference("value1", ElementInfo(2, 23, 2, 29, "value1")),
            ),
            2,
            11,
            2,
            31,
        )

        assert ir.atomic_units[0].attributes[1].name == "test2"
        assert ir.atomic_units[0].attributes[1].line == 3
        assert ir.atomic_units[0].attributes[1].column == 3
        assert ir.atomic_units[0].attributes[1].end_line == 3
        assert ir.atomic_units[0].attributes[1].end_column == 36
        self._check_binary_operation(
            ir.atomic_units[0].attributes[1].value,
            Sum,
            String("test ", ElementInfo(3, 12, 3, 17, "test ")),
            Access(
                ElementInfo(3, 22, 3, 32, "var.value2"),
                VariableReference("var", ElementInfo(3, 22, 3, 25, "var")),
                VariableReference("value2", ElementInfo(2, 26, 3, 32, "value2")),
            ),
            3,
            11,
            3,
            36,
        )

        assert isinstance(ir.atomic_units[0].attributes[2].value, Sum)   

    def test_terraform_parser_dict_value(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/dict_value_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        self._check_value(
            ir.atomic_units[0].name, String, "dataset", 1, 36, 1, 45
        )
        assert ir.atomic_units[0].type == "google_bigquery_dataset"

        assert ir.atomic_units[0].attributes[0].name == "labels"
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 4
        assert ir.atomic_units[0].attributes[0].end_column == 4
        assert isinstance(ir.atomic_units[0].attributes[0].value, Hash)
        assert ir.atomic_units[0].attributes[0].value.line == 2
        assert ir.atomic_units[0].attributes[0].value.column == 12
        assert ir.atomic_units[0].attributes[0].value.end_line == 4
        assert ir.atomic_units[0].attributes[0].value.end_column == 4
        assert len(ir.atomic_units[0].attributes[0].value.value) == 1
        self._check_value(
            list(ir.atomic_units[0].attributes[0].value.value.items())[0][0],
            VariableReference,
            "env",
            3,
            5,
            3,
            8,
        )
        self._check_value(
            list(ir.atomic_units[0].attributes[0].value.value.items())[0][1],
            String,
            "default",
            3,
            11,
            3,
            20,
        )

    def test_terraform_parser_list_value(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/list_value_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        self._check_value(
            ir.atomic_units[0].name, String, "bqowner", 1, 35, 1, 44
        )
        assert ir.atomic_units[0].type == "google_service_account"

        assert ir.atomic_units[0].attributes[0].name == "keys"
        assert isinstance(ir.atomic_units[0].attributes[0].value, Array)
        assert len(ir.atomic_units[0].attributes[0].value.value) == 3
        
        self._check_value(
            ir.atomic_units[0].attributes[0].value.value[0],
            String,
            "value1",
            2, 11, 2, 19
        )
        assert isinstance(ir.atomic_units[0].attributes[0].value.value[1], Array)
        assert isinstance(ir.atomic_units[0].attributes[0].value.value[2], Hash)

    def test_terraform_parser_dynamic_block(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/dynamic_block.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        self._check_value(
            ir.atomic_units[0].name, String, "tfenvtest", 1, 46, 1, 57
        )
        assert ir.atomic_units[0].type == "aws_elastic_beanstalk_environment"
        assert len(ir.atomic_units[0].statements) == 1

        assert isinstance(ir.atomic_units[0].statements[0], UnitBlock)
        assert ir.atomic_units[0].statements[0].type == "block"
        assert ir.atomic_units[0].statements[0].name == "dynamic"
        assert len(ir.atomic_units[0].statements[0].unit_blocks) == 1

        assert isinstance(ir.atomic_units[0].statements[0].unit_blocks[0], UnitBlock)
        assert ir.atomic_units[0].statements[0].unit_blocks[0].type == "block"
        assert ir.atomic_units[0].statements[0].unit_blocks[0].name == "content"
        assert len(ir.atomic_units[0].statements[0].unit_blocks[0].attributes) == 1

        assert ir.atomic_units[0].statements[0].unit_blocks[0].attributes[0].name == "namespace"        

    def test_terraform_parser_comments(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/comments.tf")
        assert len(ir.comments) == 7

        assert ir.comments[0].content == "#comment1\n"
        assert ir.comments[0].line == 1

        assert ir.comments[1].content == "//comment2\n"
        assert ir.comments[1].line == 2

        assert (
            ir.comments[2].content
            == "/*comment3\n  default_table_expiration_ms = 3600000\n  \n  finish comment3 */"
        )
        assert ir.comments[2].line == 4

        assert ir.comments[3].content == "#comment4\n"
        assert ir.comments[3].line == 7

        assert ir.comments[4].content == "#comment5\n"
        assert ir.comments[4].line == 9

        assert ir.comments[5].content == "#comment inside dict\n"
        assert ir.comments[5].line == 12

        assert ir.comments[6].content == "//comment2 inside dict\n"
        assert ir.comments[6].line == 13

    def test_terraform_parser_operations(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/operations.tf")
        assert len(ir.atomic_units) == 1
        assert len(ir.atomic_units[0].attributes) == 15
       
        self._check_binary_operation(
            ir.atomic_units[0].attributes[0].value,
            Sum,
            Float(1.3, ElementInfo(2, 9, 2, 12, "1.3")),
            Float(1.4, ElementInfo(2, 15, 2, 18, "1.4")),
            2,
            9,
            2,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[1].value,
            Subtract,
            Float(1.3, ElementInfo(3, 9, 3, 12, "1.3")),
            Float(1.4, ElementInfo(3, 15, 3, 18, "1.4")),
            3,
            9,
            3,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[2].value,
            Multiply,
            Float(1.3, ElementInfo(4, 9, 4, 12, "1.3")),
            Float(1.4, ElementInfo(4, 15, 4, 18, "1.4")),
            4,
            9,
            4,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[3].value,
            Divide,
            Float(1.3, ElementInfo(5, 9, 5, 12, "1.3")),
            Float(1.4, ElementInfo(5, 15, 5, 18, "1.4")),
            5,
            9,
            5,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[4].value,
            Modulo,
            Float(1.3, ElementInfo(6, 9, 6, 12, "1.3")),
            Float(1.4, ElementInfo(6, 15, 6, 18, "1.4")),
            6,
            9,
            6,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[5].value,
            And,
            Float(1.3, ElementInfo(7, 9, 7, 12, "1.3")),
            Float(1.4, ElementInfo(7, 16, 7, 19, "1.4")),
            7,
            9,
            7,
            19
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[6].value,
            Or,
            Float(1.3, ElementInfo(8, 8, 8, 11, "1.3")),
            Float(1.4, ElementInfo(8, 15, 8, 18, "1.4")),
            8,
            8,
            8,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[7].value,
            Equal,
            Float(1.3, ElementInfo(9, 8, 9, 11, "1.3")),
            Float(1.4, ElementInfo(9, 15, 9, 18, "1.4")),
            9,
            8,
            9,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[8].value,
            NotEqual,
            Float(1.3, ElementInfo(10, 8, 10, 11, "1.3")),
            Float(1.4, ElementInfo(10, 15, 10, 18, "1.4")),
            10,
            8,
            10,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[9].value,
            GreaterThan,
            Float(1.3, ElementInfo(11, 8, 11, 11, "1.3")),
            Float(1.4, ElementInfo(11, 14, 11, 17, "1.4")),
            11,
            8,
            11,
            17
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[10].value,
            LessThan,
            Float(1.3, ElementInfo(12, 8, 12, 11, "1.3")),
            Float(1.4, ElementInfo(12, 14, 12, 17, "1.4")),
            12,
            8,
            12,
            17
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[11].value,
            GreaterThanOrEqual,
            Float(1.3, ElementInfo(13, 8, 13, 11, "1.3")),
            Float(1.4, ElementInfo(13, 15, 13, 18, "1.4")),
            13,
            8,
            13,
            18
        )
        self._check_binary_operation(
            ir.atomic_units[0].attributes[12].value,
            LessThanOrEqual,
            Float(1.3, ElementInfo(14, 8, 14, 11, "1.3")),
            Float(1.4, ElementInfo(14, 15, 14, 18, "1.4")),
            14,
            8,
            14,
            18
        )
        assert isinstance(ir.atomic_units[0].attributes[13].value, Not)
        self._check_value(
            ir.atomic_units[0].attributes[13].value.expr,
            Boolean,
            True,
            15, 10, 15, 14
        )
        assert isinstance(ir.atomic_units[0].attributes[14].value, Minus)
        self._check_value(
            ir.atomic_units[0].attributes[14].value.expr,
            Float,
            1.3,
            16, 12, 16, 15
        )

    def test_terraform_parser_conditional(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/conditional.tf")
        assert len(ir.atomic_units) == 1
        assert len(ir.atomic_units[0].attributes) == 1

        assert isinstance(ir.atomic_units[0].attributes[0].value, ConditionalStatement)
        assert ir.atomic_units[0].attributes[0].value.line == 2
        assert ir.atomic_units[0].attributes[0].value.column == 16
        assert ir.atomic_units[0].attributes[0].value.end_line == 2
        assert ir.atomic_units[0].attributes[0].value.end_column == 61

        assert isinstance(ir.atomic_units[0].attributes[0].value.condition, Access)
        assert len(ir.atomic_units[0].attributes[0].value.statements) == 1
        assert isinstance(ir.atomic_units[0].attributes[0].value.statements[0], String)

        assert isinstance(ir.atomic_units[0].attributes[0].value.else_statement, ConditionalStatement)
        assert len(ir.atomic_units[0].attributes[0].value.else_statement.statements) == 1
        assert isinstance(ir.atomic_units[0].attributes[0].value.else_statement.statements[0], Null)

    def test_terraform_parser_function_call(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/function_call.tf")
        assert len(ir.atomic_units) == 1
        assert len(ir.atomic_units[0].attributes) == 2
        assert isinstance(ir.atomic_units[0].attributes[0].value, FunctionCall)
        assert isinstance(ir.atomic_units[0].attributes[1].value, FunctionCall)

    def test_terraform_parser_recursive_blocks(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/recursive_blocks.tf")
        assert len(ir.unit_blocks) == 1
        assert len(ir.unit_blocks[0].variables) == 1
        assert ir.unit_blocks[0].variables[0].name == "tags"

    def test_terraform_parser_block_with_attribute(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/block_with_attribute.tf")
        assert len(ir.atomic_units) == 1
        assert len(ir.atomic_units[0].statements) == 1
        assert len(ir.atomic_units[0].attributes) == 1
