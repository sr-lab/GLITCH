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
        assert ir.atomic_units[0].name == "bqowner"
        assert ir.atomic_units[0].type == "resource.google_service_account"

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
        assert ir.atomic_units[0].name == "bqowner"
        assert ir.atomic_units[0].type == "resource.google_service_account"

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
        assert ir.atomic_units[0].name == "example"
        assert ir.atomic_units[0].type == "resource.aws_instance"

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
        assert len(ir.atomic_units[0].attributes) == 1
        assert ir.atomic_units[0].name == "dataset"
        assert ir.atomic_units[0].type == "resource.google_bigquery_dataset"

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

    def test_terraform_parser_dict_value(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/dict_value_assign.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        assert ir.atomic_units[0].name == "dataset"
        assert ir.atomic_units[0].type == "resource.google_bigquery_dataset"

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
            String,
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
        assert len(ir.atomic_units[0].attributes) == 4
        assert ir.atomic_units[0].name == "bqowner"
        assert ir.atomic_units[0].type == "resource.google_service_account"

        assert ir.atomic_units[0].attributes[0].name == "keys[0]"
        assert ir.atomic_units[0].attributes[0].value == "value1"
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 2
        assert ir.atomic_units[0].attributes[0].end_column == 63

        assert ir.atomic_units[0].attributes[1].name == "keys[1][0]"
        assert ir.atomic_units[0].attributes[1].value == "1"
        assert ir.atomic_units[0].attributes[1].line == 2
        assert ir.atomic_units[0].attributes[1].column == 3
        assert ir.atomic_units[0].attributes[1].end_line == 2
        assert ir.atomic_units[0].attributes[1].end_column == 63

        assert ir.atomic_units[0].attributes[2].name == "keys[1][1]"
        assert ir.atomic_units[0].attributes[2].value == None
        assert ir.atomic_units[0].attributes[2].line == 2
        assert ir.atomic_units[0].attributes[2].column == 3
        assert ir.atomic_units[0].attributes[2].end_line == 2
        assert ir.atomic_units[0].attributes[2].end_column == 63
        assert len(ir.atomic_units[0].attributes[2].keyvalues) == 1

        assert ir.atomic_units[0].attributes[2].keyvalues[0].name == "key2"
        assert ir.atomic_units[0].attributes[2].keyvalues[0].value == "value2"
        assert ir.atomic_units[0].attributes[2].keyvalues[0].line == 2
        assert ir.atomic_units[0].attributes[2].keyvalues[0].column == 26
        assert ir.atomic_units[0].attributes[2].keyvalues[0].end_line == 2
        assert ir.atomic_units[0].attributes[2].keyvalues[0].end_column == 41

        assert ir.atomic_units[0].attributes[3].name == "keys[2]"
        assert ir.atomic_units[0].attributes[3].value == None
        assert ir.atomic_units[0].attributes[3].line == 2
        assert ir.atomic_units[0].attributes[3].column == 3
        assert ir.atomic_units[0].attributes[3].end_line == 2
        assert ir.atomic_units[0].attributes[3].end_column == 63
        assert len(ir.atomic_units[0].attributes[3].keyvalues) == 1

        assert ir.atomic_units[0].attributes[3].keyvalues[0].name == "key3"
        assert ir.atomic_units[0].attributes[3].keyvalues[0].value == "value3"
        assert ir.atomic_units[0].attributes[3].keyvalues[0].line == 2
        assert ir.atomic_units[0].attributes[3].keyvalues[0].column == 46
        assert ir.atomic_units[0].attributes[3].keyvalues[0].end_line == 2
        assert ir.atomic_units[0].attributes[3].keyvalues[0].end_column == 61

    def test_terraform_parser_dynamic_block(self) -> None:
        ir = self.__parse("tests/parser/terraform/files/dynamic_block.tf")
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert len(ir.atomic_units[0].attributes) == 1
        assert ir.atomic_units[0].name == "tfenvtest"
        assert ir.atomic_units[0].type == "resource.aws_elastic_beanstalk_environment"

        assert ir.atomic_units[0].attributes[0].name == "dynamic.setting"
        assert ir.atomic_units[0].attributes[0].value == None
        assert ir.atomic_units[0].attributes[0].line == 2
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 6
        assert ir.atomic_units[0].attributes[0].end_column == 4
        assert len(ir.atomic_units[0].attributes[0].keyvalues) == 1

        assert ir.atomic_units[0].attributes[0].keyvalues[0].name == "content"
        assert ir.atomic_units[0].attributes[0].keyvalues[0].value == None
        assert ir.atomic_units[0].attributes[0].keyvalues[0].line == 3
        assert ir.atomic_units[0].attributes[0].keyvalues[0].column == 5
        assert ir.atomic_units[0].attributes[0].keyvalues[0].end_line == 5
        assert ir.atomic_units[0].attributes[0].keyvalues[0].end_column == 6
        assert len(ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues) == 1

        assert (
            ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].name
            == "namespace"
        )
        assert (
            ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].value
            == '${setting.value["namespace"]}'
        )
        assert ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].line == 4
        assert ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].column == 7
        assert ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].end_line == 4
        assert (
            ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].end_column == 45
        )
        assert ir.atomic_units[0].attributes[0].keyvalues[0].keyvalues[0].has_variable

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
