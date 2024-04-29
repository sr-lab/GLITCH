import unittest

from glitch.parsers.gha import GithubActionsParser
from glitch.repr.inter import *


class TestGithubActionsParser(unittest.TestCase):
    def test_gha_valid_workflow(self) -> None:
        """
        run commands
        with
        runs-on
        """
        p = GithubActionsParser()
        ir = p.parse_file(
            "tests/parser/gha/files/valid_workflow.yml", UnitBlockType.script
        )

        assert ir is not None
        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        assert ir.name == "Run Python Tests"

        assert len(ir.attributes) == 1
        assert ir.attributes[0].name == "on"
        assert ir.attributes[0].value is None
        assert len(ir.attributes[0].keyvalues) == 2

        assert ir.attributes[0].keyvalues[0].name == "push"
        assert ir.attributes[0].keyvalues[0].value is None
        assert len(ir.attributes[0].keyvalues[0].keyvalues) == 1
        assert ir.attributes[0].keyvalues[0].keyvalues[0].name == "branches"
        assert ir.attributes[0].keyvalues[0].keyvalues[0].value == ["main"]
        assert (
            ir.attributes[0].keyvalues[0].keyvalues[0].code
            == "    branches:\n      - main\n  "
        )

        assert ir.attributes[0].keyvalues[1].name == "pull_request"
        assert ir.attributes[0].keyvalues[1].value is None
        assert len(ir.attributes[0].keyvalues[1].keyvalues) == 1
        assert ir.attributes[0].keyvalues[1].keyvalues[0].name == "branches"
        assert ir.attributes[0].keyvalues[1].keyvalues[0].value == ["main"]

        assert len(ir.unit_blocks) == 1
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert ir.unit_blocks[0].name == "build"

        assert len(ir.unit_blocks[0].attributes) == 1
        assert ir.unit_blocks[0].attributes[0].name == "runs-on"
        assert ir.unit_blocks[0].attributes[0].value == "ubuntu-latest"

        assert len(ir.unit_blocks[0].atomic_units) == 5

        assert ir.unit_blocks[0].atomic_units[0].name == ""
        assert ir.unit_blocks[0].atomic_units[0].type == "actions/checkout@v3"

        assert ir.unit_blocks[0].atomic_units[1].name == ""
        assert ir.unit_blocks[0].atomic_units[1].type == "ruby/setup-ruby@v1"
        assert len(ir.unit_blocks[0].atomic_units[1].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].name == "ruby-version"
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].value == "2.7.4"
        assert not ir.unit_blocks[0].atomic_units[1].attributes[0].has_variable

        assert ir.unit_blocks[0].atomic_units[2].name == "Install Python 3"
        assert ir.unit_blocks[0].atomic_units[2].type == "actions/setup-python@v4"
        assert len(ir.unit_blocks[0].atomic_units[2].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].name == "python-version"
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].value == "3.10.5"
        assert not ir.unit_blocks[0].atomic_units[2].attributes[0].has_variable

        assert ir.unit_blocks[0].atomic_units[3].name == "Install dependencies"
        assert ir.unit_blocks[0].atomic_units[3].type == "shell"
        assert len(ir.unit_blocks[0].atomic_units[3].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[3].attributes[0].name == "run"
        assert (
            ir.unit_blocks[0].atomic_units[3].attributes[0].value
            == "python -m pip install --upgrade pip\npython -m pip install -e .\n"
        )
        assert not ir.unit_blocks[0].atomic_units[3].attributes[0].has_variable

        assert ir.unit_blocks[0].atomic_units[4].name == "Run tests with pytest"
        assert ir.unit_blocks[0].atomic_units[4].type == "shell"
        assert len(ir.unit_blocks[0].atomic_units[4].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[4].attributes[0].name == "run"
        assert (
            ir.unit_blocks[0].atomic_units[4].attributes[0].value
            == "cd glitch\npython -m unittest discover tests"
        )
        assert not ir.unit_blocks[0].atomic_units[4].attributes[0].has_variable

    def test_gha_valid_workflow_2(self) -> None:
        """
        comments
        env (global)
        has_variable
        defaults (job)
        """
        p = GithubActionsParser()
        ir = p.parse_file(
            "tests/parser/gha/files/valid_workflow_2.yml", UnitBlockType.script
        )
        assert ir is not None
        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script

        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "build"
        assert ir.variables[0].value == "${{ github.workspace }}/build"
        assert ir.variables[0].has_variable

        assert len(ir.unit_blocks) == 1

        assert len(ir.unit_blocks[0].variables) == 1
        assert isinstance(ir.unit_blocks[0].variables[0], Variable)
        assert ir.unit_blocks[0].variables[0].name == "run"
        assert ir.unit_blocks[0].variables[0].value is None
        assert not ir.unit_blocks[0].variables[0].has_variable
        assert len(ir.unit_blocks[0].variables[0].keyvalues) == 1
        assert ir.unit_blocks[0].variables[0].keyvalues[0].name == "shell"
        assert ir.unit_blocks[0].variables[0].keyvalues[0].value == "powershell"

        assert len(ir.unit_blocks[0].atomic_units) == 4
        assert ir.unit_blocks[0].atomic_units[1].name == "Configure CMake"
        assert ir.unit_blocks[0].atomic_units[1].type == "shell"
        assert len(ir.unit_blocks[0].atomic_units[1].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].name == "run"
        assert (
            ir.unit_blocks[0].atomic_units[1].attributes[0].value
            == "cmake -B ${{ env.build }}"
        )
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].has_variable

        assert len(ir.comments) == 24

        assert (
            ir.comments[0].content
            == "# https://github.com/actions/starter-workflows/blob/main/code-scanning/msvc.yml"
        )
        assert ir.comments[0].line == 1

        assert ir.comments[9].content == "# for actions/checkout to fetch code"
        assert ir.comments[9].line == 31

    def test_gha_index_out_of_range(self) -> None:
        """
        This file previously gave an index out of range even though it is valid.
        """
        p = GithubActionsParser()
        ir = p.parse_file(
            "tests/parser/gha/files/index_out_of_range.yml", UnitBlockType.script
        )
        assert ir is not None
