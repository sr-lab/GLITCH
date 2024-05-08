import unittest

from glitch.parsers.ansible import AnsibleParser
from glitch.repr.inter import *


class TestAnsibleParser(unittest.TestCase):
    def test_ansible_parser_valid_tasks(self) -> None:
        p = AnsibleParser()
        ir = p.parse_file("tests/parser/ansible/files/valid_tasks.yml", UnitBlockType.tasks)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.tasks
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert ir.atomic_units[0].name == "Get machine-id"
        assert ir.atomic_units[0].type == "shell"
        assert len(ir.atomic_units[0].attributes) == 4

        assert ir.atomic_units[0].attributes[0].name == "shell"
        assert ir.atomic_units[0].attributes[0].value == "hostnamectl --machine=\"{{ inventory_hostname }}\" status | awk '/Machine ID/ {print $3}'"
        assert ir.atomic_units[0].attributes[0].line == 3
        assert ir.atomic_units[0].attributes[0].column == 3
        assert ir.atomic_units[0].attributes[0].end_line == 5
        assert ir.atomic_units[0].attributes[0].end_column == 1

        assert ir.atomic_units[0].attributes[1].name == "register"
        assert ir.atomic_units[0].attributes[1].value == "_container_machine_id"
        assert ir.atomic_units[0].attributes[1].line == 5
        assert ir.atomic_units[0].attributes[1].column == 3
        assert ir.atomic_units[0].attributes[1].end_line == 5
        assert ir.atomic_units[0].attributes[1].end_column == 34

        assert ir.atomic_units[0].attributes[2].name == "delegate_to"
        assert ir.atomic_units[0].attributes[2].value == "{{ physical_host }}"
        assert ir.atomic_units[0].attributes[2].line == 6
        assert ir.atomic_units[0].attributes[2].column == 3
        assert ir.atomic_units[0].attributes[2].end_line == 6
        assert ir.atomic_units[0].attributes[2].end_column == 37

        assert ir.atomic_units[0].attributes[3].name == "test"
        assert ir.atomic_units[0].attributes[3].value == None
        assert ir.atomic_units[0].attributes[3].line == 7
        assert ir.atomic_units[0].attributes[3].column == 3
        assert ir.atomic_units[0].attributes[3].end_line == 8
        assert ir.atomic_units[0].attributes[3].end_column == 26
        assert len(ir.atomic_units[0].attributes[3].keyvalues) == 1

        assert ir.atomic_units[0].attributes[3].keyvalues[0].name == "executable"
        assert ir.atomic_units[0].attributes[3].keyvalues[0].value == "/bin/bash"
        assert ir.atomic_units[0].attributes[3].keyvalues[0].line == 8
        assert ir.atomic_units[0].attributes[3].keyvalues[0].column == 5
        assert ir.atomic_units[0].attributes[3].keyvalues[0].end_line == 8
        assert ir.atomic_units[0].attributes[3].keyvalues[0].end_column == 26
    
    def test_ansible_parser_valid_playbook_vars(self) -> None:
        p = AnsibleParser()
        ir = p.parse_file("tests/parser/ansible/files/valid_playbook_vars.yml", UnitBlockType.script)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert len(ir.unit_blocks[0].variables) == 2

        assert ir.unit_blocks[0].variables[0].name == "aqua_admin_password"
        assert ir.unit_blocks[0].variables[0].value == "{{ lookup('env', 'AQUA_ADMIN_PASSWORD') }}"
        assert ir.unit_blocks[0].variables[0].line == 6
        assert ir.unit_blocks[0].variables[0].column == 5
        assert ir.unit_blocks[0].variables[0].end_line == 6
        assert ir.unit_blocks[0].variables[0].end_column == 70

        assert ir.unit_blocks[0].variables[1].name == "aqua_sso_client_secret"
        assert ir.unit_blocks[0].variables[1].value == "\"{{ lookup('env', 'AQUA_SSO_CLIENT_SECRET') }}\""
        assert ir.unit_blocks[0].variables[1].line == 7
        assert ir.unit_blocks[0].variables[1].column == 5
        assert ir.unit_blocks[0].variables[1].end_line == 9
        assert ir.unit_blocks[0].variables[1].end_column == 1

    def test_ansible_parser_valid_playbook_hierarchical_vars(self) -> None:
        p = AnsibleParser()
        ir = p.parse_file("tests/parser/ansible/files/valid_playbook_hierarchical_vars.yml", UnitBlockType.script)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert len(ir.unit_blocks[0].variables) == 1

        assert ir.unit_blocks[0].variables[0].name == "aqua_admin"
        assert ir.unit_blocks[0].variables[0].value == None
        assert ir.unit_blocks[0].variables[0].line == 6
        assert ir.unit_blocks[0].variables[0].column == 5
        assert ir.unit_blocks[0].variables[0].end_line == 7
        assert ir.unit_blocks[0].variables[0].end_column == 53
        assert len(ir.unit_blocks[0].variables[0].keyvalues) == 1

        assert ir.unit_blocks[0].variables[0].keyvalues[0].name == "user"
        assert ir.unit_blocks[0].variables[0].keyvalues[0].value == "{{ lookup('env', 'AQUA_ADMIN_USER') }}"
        assert ir.unit_blocks[0].variables[0].keyvalues[0].line == 7
        assert ir.unit_blocks[0].variables[0].keyvalues[0].column == 7
        assert ir.unit_blocks[0].variables[0].keyvalues[0].end_line == 7
        assert ir.unit_blocks[0].variables[0].keyvalues[0].end_column == 53

    def test_ansible_parser_valid_playbook_vars_list(self) -> None:
        p = AnsibleParser()
        ir = p.parse_file("tests/parser/ansible/files/valid_playbook_vars_list.yml", UnitBlockType.script)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert len(ir.unit_blocks[0].variables) == 2

        assert ir.unit_blocks[0].variables[0].name == "aqua_admin_users[0]"
        assert ir.unit_blocks[0].variables[0].value == None
        assert len(ir.unit_blocks[0].variables[0].keyvalues) == 1
        assert ir.unit_blocks[0].variables[0].keyvalues[0].name == "user"
        assert ir.unit_blocks[0].variables[0].keyvalues[0].value == "test1"
        assert ir.unit_blocks[0].variables[0].keyvalues[0].line == 7
        assert ir.unit_blocks[0].variables[0].keyvalues[0].column == 9
        assert ir.unit_blocks[0].variables[0].keyvalues[0].end_line == 7
        assert ir.unit_blocks[0].variables[0].keyvalues[0].end_column == 20

        assert ir.unit_blocks[0].variables[1].name == "aqua_admin_users[1]"
        assert ir.unit_blocks[0].variables[1].value == None
        assert len(ir.unit_blocks[0].variables[1].keyvalues) == 1
        assert ir.unit_blocks[0].variables[1].keyvalues[0].name == "user"
        assert ir.unit_blocks[0].variables[1].keyvalues[0].value == "test2"
        assert ir.unit_blocks[0].variables[1].keyvalues[0].line == 8
        assert ir.unit_blocks[0].variables[1].keyvalues[0].column == 9
        assert ir.unit_blocks[0].variables[1].keyvalues[0].end_line == 8
        assert ir.unit_blocks[0].variables[1].keyvalues[0].end_column == 20

    def test_ansible_parser_valid_vars(self) -> None:
        p = AnsibleParser()
        ir = p.parse_file("tests/parser/ansible/files/valid_vars.yml", UnitBlockType.vars)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.vars
        assert len(ir.variables) == 1

        assert ir.variables[0].name == "aqua_admin_users"
        assert ir.variables[0].value == "['test1', 'test2']"
        assert ir.variables[0].line == 2
        assert ir.variables[0].column == 1
        assert ir.variables[0].end_line == 4
        assert ir.variables[0].end_column == 12

