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
        assert len(ir.atomic_units[0].attributes) == 2
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
        assert ir.atomic_units[0].statements[0].name == "ObjectType.DYNAMIC"
        assert len(ir.atomic_units[0].statements[0].unit_blocks) == 1

        assert isinstance(ir.atomic_units[0].statements[0].unit_blocks[0], UnitBlock)
        assert ir.atomic_units[0].statements[0].unit_blocks[0].type == "block"
        assert ir.atomic_units[0].statements[0].unit_blocks[0].name == "ObjectType.CONTENT"
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
