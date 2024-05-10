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
