import unittest
from glitch.parsers.puppet import PuppetParser
from glitch.repr.inter import *


class TestPuppetParser(unittest.TestCase):
    def test_puppet_parser_if(self) -> None:
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/if.pp", UnitBlockType.script
        )

        assert len(unit_block.statements) == 1
        assert isinstance(unit_block.statements[0], ConditionalStatement)
        # FIXME: the expression should not be a string and or at least should be
        # equal to the script
        assert unit_block.statements[0].condition == "$x==absent"

        assert len(unit_block.statements[0].statements) == 1
        assert isinstance(unit_block.statements[0].statements[0], AtomicUnit)
        atomic_unit = unit_block.statements[0].statements[0]
        assert len(atomic_unit.attributes) == 1
        assert atomic_unit.attributes[0].name == "ensure"
        assert atomic_unit.attributes[0].value == "absent"
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
        assert atomic_unit.attributes[0].value == "present"
        assert atomic_unit.attributes[0].line == 11
        assert atomic_unit.attributes[0].end_line == 11
        assert atomic_unit.attributes[0].column == 9
        assert atomic_unit.attributes[0].end_column == 27

        assert len(unit_block.variables) == 1
        assert unit_block.variables[0].name == "$test"
        assert unit_block.variables[0].value == "\n    test 123\n"
        assert unit_block.variables[0].line == 1
        assert unit_block.variables[0].end_line == 3
        assert unit_block.variables[0].column == 1
        assert unit_block.variables[0].end_column == 7

    def test_puppet_parser_defined_resource(self) -> None:
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/defined_resource.pp", UnitBlockType.script
        )

        assert unit_block is not None
        assert isinstance(unit_block, UnitBlock)
        assert len(unit_block.unit_blocks) == 1

        assert unit_block.unit_blocks[0].type == UnitBlockType.definition
        assert unit_block.unit_blocks[0].name == "apache::vhost"
        assert len(unit_block.unit_blocks[0].attributes) == 2

        assert unit_block.unit_blocks[0].attributes[0].name == "$port"
        assert unit_block.unit_blocks[0].attributes[0].value == None

        assert unit_block.unit_blocks[0].attributes[1].name == "$servername"
        assert unit_block.unit_blocks[0].attributes[1].value == "$title"

        assert len(unit_block.unit_blocks[0].atomic_units) == 1
        assert (
            unit_block.unit_blocks[0].atomic_units[0].name
            == "${vhost_dir}/${servername}.conf"
        )
        assert unit_block.unit_blocks[0].atomic_units[0].type == "file"

    def test_puppet_parser_class(self) -> None:
        unit_block = PuppetParser().parse_file(
            "tests/parser/puppet/files/class.pp", UnitBlockType.script
        )

        assert unit_block is not None
        assert isinstance(unit_block, UnitBlock)
        assert len(unit_block.unit_blocks) == 1

        assert unit_block.unit_blocks[0].type == UnitBlockType.definition
        assert unit_block.unit_blocks[0].name == "apache"
        assert len(unit_block.unit_blocks[0].attributes) == 1

        assert unit_block.unit_blocks[0].attributes[0].name == "$version"
        assert unit_block.unit_blocks[0].attributes[0].value == "latest"

        assert len(unit_block.unit_blocks[0].atomic_units) == 1
        assert unit_block.unit_blocks[0].atomic_units[0].name == "httpd"
        assert unit_block.unit_blocks[0].atomic_units[0].type == "package"
