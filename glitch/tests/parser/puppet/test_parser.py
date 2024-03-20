import unittest
from glitch.parsers.puppet import PuppetParser
from glitch.repr.inter import *


class TestPuppetParser(unittest.TestCase):
    def test_puppet_parser_if(self) -> None:
        unit_block = PuppetParser().parse_file("tests/parser/puppet/files/if.pp", None)
        assert len(unit_block.statements) == 1
        assert isinstance(unit_block.statements[0], ConditionalStatement)
        # FIXME: the expression should not be a string and or at least should be
        # equal to the script
        assert unit_block.statements[0].condition == "$x==absent"
        assert len(unit_block.statements[0].statements) == 1
        assert isinstance(unit_block.statements[0].statements[0], AtomicUnit)
        assert unit_block.statements[0].else_statement is not None
        assert isinstance(unit_block.statements[0].else_statement, ConditionalStatement)
        assert len(unit_block.statements[0].else_statement.statements) == 1
        assert isinstance(
            unit_block.statements[0].else_statement.statements[0], AtomicUnit
        )
