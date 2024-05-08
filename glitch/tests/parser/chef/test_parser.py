import unittest
from glitch.parsers.chef import ChefParser
from glitch.repr.inter import *


class TestChefParser(unittest.TestCase):
    def test_chef_parser_valid_manifest(self) -> None:
        p = ChefParser()
        ir = p.parse_file("tests/parser/chef/files/valid_manifest.rb", UnitBlockType.script)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.variables) == 1
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "my_home"
        assert ir.variables[0].value == "/home/test"
        assert ir.variables[0].line == 1
        assert ir.variables[0].column == 1
        assert ir.variables[0].end_line == 1
        assert ir.variables[0].end_column == 23

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert ir.atomic_units[0].name == "create ssh keypair for #{new_resource.username}"
        assert ir.atomic_units[0].type == "execute"
        assert len(ir.atomic_units[0].attributes) == 3
        
        assert isinstance(ir.atomic_units[0].attributes[0], Attribute)
        assert ir.atomic_units[0].attributes[0].name == "user"
        assert ir.atomic_units[0].attributes[0].value == "new_resource.username"
        assert ir.atomic_units[0].attributes[0].line == 4
        assert ir.atomic_units[0].attributes[0].column == 5
        assert ir.atomic_units[0].attributes[0].end_line == 4
        assert ir.atomic_units[0].attributes[0].end_column == 36

        assert isinstance(ir.atomic_units[0].attributes[1], Attribute)
        assert ir.atomic_units[0].attributes[1].name == "command"
        assert ir.atomic_units[0].attributes[1].value == ".gsub(/^ +/, '')\n      ssh-keygen -t dsa -f #{my_home}/.ssh/id_dsa -N '' \\\n        -C '#{new_resource.username}@#{fqdn}-#{Time.now.strftime('%FT%T%z')}'\n      chmod 0600 #{my_home}/.ssh/id_dsa\n      chmod 0644 #{my_home}/.ssh/id_dsa.pub\n"
        assert ir.atomic_units[0].attributes[1].line == 5
        assert ir.atomic_units[0].attributes[1].column == 5
        assert ir.atomic_units[0].attributes[1].end_line == 9
        assert ir.atomic_units[0].attributes[1].end_column == 45

        assert isinstance(ir.atomic_units[0].attributes[2], Attribute)
        assert ir.atomic_units[0].attributes[2].name == "action"
        assert ir.atomic_units[0].attributes[2].value == ":nothing"
        assert ir.atomic_units[0].attributes[2].line == 11
        assert ir.atomic_units[0].attributes[2].column == 5
        assert ir.atomic_units[0].attributes[2].end_line == 11
        assert ir.atomic_units[0].attributes[2].end_column == 23
