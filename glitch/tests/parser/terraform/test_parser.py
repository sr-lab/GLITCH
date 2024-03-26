import unittest
from glitch.parsers.terraform import TerraformParser
from typing import Sequence


class TestTerraform(unittest.TestCase):
    def __help_test(self, path, attributes) -> None:
        unitblock = TerraformParser().parse_file(path, None)
        au = unitblock.atomic_units[0]
        self.assertEqual(str(au.attributes), attributes)

    def __help_test_comments(self, path, comments: Sequence[str]) -> None:
        unitblock = TerraformParser().parse_file(path, None)
        self.assertEqual(str(unitblock.comments), comments)

    def test_terraform_null_value(self) -> None:
        attributes = "[account_id:'']"
        self.__help_test(
            "tests/parser/terraform/files/null_value_assign.tf", attributes
        )

    def test_terraform_empty_string(self) -> None:
        attributes = "[account_id:'']"
        self.__help_test(
            "tests/parser/terraform/files/empty_string_assign.tf", attributes
        )

    def test_terraform_boolean_value(self) -> None:
        attributes = "[account_id:'True']"
        self.__help_test(
            "tests/parser/terraform/files/boolean_value_assign.tf", attributes
        )

    def test_terraform_multiline_string(self) -> None:
        attributes = "[user_data:'    #!/bin/bash\\n    sudo apt-get update\\n    sudo apt-get install -y apache2\\n    sudo systemctl start apache2']"
        self.__help_test(
            "tests/parser/terraform/files/multiline_string_assign.tf", attributes
        )

    def test_terraform_value_has_variable(self) -> None:
        attributes = "[access:None:[user_by_email:'${google_service_account.bqowner.email}'], test:'${var.value1}']"
        self.__help_test(
            "tests/parser/terraform/files/value_has_variable.tf", attributes
        )

    def test_terraform_dict_value(self) -> None:
        attributes = "[labels:None:[env:'default']]"
        self.__help_test(
            "tests/parser/terraform/files/dict_value_assign.tf", attributes
        )

    def test_terraform_list_value(self) -> None:
        attributes = "[keys[0]:'value1', keys[1][0]:'1', keys[1][1]:None:[key2:'value2'], keys[2]:None:[key3:'value3']]"
        self.__help_test(
            "tests/parser/terraform/files/list_value_assign.tf", attributes
        )

    def test_terraform_dynamic_block(self) -> None:
        attributes = "[dynamic.setting:None:[content:None:[namespace:'${setting.value[\"namespace\"]}']]]"
        self.__help_test("tests/parser/terraform/files/dynamic_block.tf", attributes)

    def test_terraform_comments(self) -> None:
        comments = "[#comment1\n, //comment2\n, /*comment3\n  default_table_expiration_ms = 3600000\n  \n  finish comment3 */, #comment4\n, #comment5\n, #comment inside dict\n, //comment2 inside dict\n]"
        self.__help_test_comments("tests/parser/terraform/files/comments.tf", comments)
