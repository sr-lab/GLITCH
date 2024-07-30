from glitch.parsers.gha import GithubActionsParser
from glitch.repr.inter import *
from glitch.tests.parser.test_parser import TestParser


class TestGithubActionsParser(TestParser):
    def test_gha_parser_valid_workflow(self) -> None:
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
        assert isinstance(ir.attributes[0].value, Hash)
        assert ir.attributes[0].line == 2
        assert ir.attributes[0].end_line == 10
        assert ir.attributes[0].column == 1
        assert ir.attributes[0].end_column == 1
        assert len(ir.attributes[0].value.value) == 2

        assert (
            String("push", ElementInfo(3, 3, 3, 7, "push"))
            in ir.attributes[0].value.value
        )
        push = ir.attributes[0].value.value[
            String("push", ElementInfo(3, 3, 3, 7, "push"))
        ]
        assert isinstance(push, Hash)
        assert push.line == 4
        assert push.column == 5
        assert push.end_line == 6
        assert push.end_column == 3
        assert len(push.value) == 1

        assert (
            String("branches", ElementInfo(4, 5, 4, 13, "branches"))
            in push.value
        )
        branches = push.value[
            String("branches", ElementInfo(4, 5, 4, 13, "branches"))
        ]
        assert isinstance(branches, Array)
        assert len(branches.value) == 1
        self._check_value(
            branches.value[0],
            String,
            "main",
            5,
            9,
            5,
            13
        )

        assert (
            String("pull_request", ElementInfo(6, 3, 6, 15, "pull_request"))
            in ir.attributes[0].value.value
        )
        pull = ir.attributes[0].value.value[
            String("pull_request", ElementInfo(6, 3, 6, 15, "pull_request"))
        ]
        assert isinstance(pull, Hash)
        assert pull.line == 7
        assert pull.column == 5
        assert pull.end_line == 10
        assert pull.end_column == 1
        assert len(pull.value) == 1

        assert (
            String("branches", ElementInfo(7, 5, 7, 13, "branches"))
            in pull.value
        )
        branches = pull.value[
            String("branches", ElementInfo(7, 5, 7, 13, "branches"))
        ]
        assert isinstance(branches, Array)
        assert len(branches.value) == 1
        self._check_value(
            branches.value[0],
            String,
            "main",
            8,
            9,
            8,
            13
        )

        assert len(ir.unit_blocks) == 1
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert ir.unit_blocks[0].name == "build"

        assert len(ir.unit_blocks[0].attributes) == 1
        assert ir.unit_blocks[0].attributes[0].name == "runs-on"
        self._check_value(
            ir.unit_blocks[0].attributes[0].value,
            String,
            "ubuntu-latest",
            12,
            14,
            12,
            27
        )
        assert ir.unit_blocks[0].attributes[0].line == 12
        assert ir.unit_blocks[0].attributes[0].end_line == 12
        assert ir.unit_blocks[0].attributes[0].column == 5
        assert ir.unit_blocks[0].attributes[0].end_column == 27

        assert len(ir.unit_blocks[0].atomic_units) == 5

        assert ir.unit_blocks[0].atomic_units[0].name == Null()
        assert ir.unit_blocks[0].atomic_units[0].type == "actions/checkout@v3"

        assert ir.unit_blocks[0].atomic_units[1].name == Null()
        assert ir.unit_blocks[0].atomic_units[1].type == "ruby/setup-ruby@v1"
        assert len(ir.unit_blocks[0].atomic_units[1].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].name == "ruby-version"
        self._check_value(
            ir.unit_blocks[0].atomic_units[1].attributes[0].value,
            String,
            "2.7.4",
            17,
            25,
            17,
            32
        )
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].line == 17
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].end_line == 17
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].column == 11
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].end_column == 32

        self._check_value(
            ir.unit_blocks[0].atomic_units[2].name,
            String,
            "Install Python 3",
            18,
            15,
            18,
            31
        )
        assert ir.unit_blocks[0].atomic_units[2].type == "actions/setup-python@v4"
        assert len(ir.unit_blocks[0].atomic_units[2].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].name == "python-version"
        self._check_value(
            ir.unit_blocks[0].atomic_units[2].attributes[0].value,
            String,
            "3.10.5",
            21,
            27,
            21,
            33
        )
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].line == 21
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].end_line == 21
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].column == 11
        assert ir.unit_blocks[0].atomic_units[2].attributes[0].end_column == 33

        self._check_value(
            ir.unit_blocks[0].atomic_units[3].name,
            String,
            "Install dependencies",
            22,
            15,
            22,
            35
        )
        assert ir.unit_blocks[0].atomic_units[3].type == "shell"
        assert len(ir.unit_blocks[0].atomic_units[3].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[3].attributes[0].name == "run"
        self._check_value(
            ir.unit_blocks[0].atomic_units[3].attributes[0].value,
            String,
            "python -m pip install --upgrade pip\n          python -m pip install -e .",
            24,
            11,
            25,
            37
        )
        assert ir.unit_blocks[0].atomic_units[3].attributes[0].line == 23
        assert ir.unit_blocks[0].atomic_units[3].attributes[0].end_line == 26
        assert ir.unit_blocks[0].atomic_units[3].attributes[0].column == 9
        assert ir.unit_blocks[0].atomic_units[3].attributes[0].end_column == 1

        self._check_value(
            ir.unit_blocks[0].atomic_units[4].name,
            String,
            "Run tests with pytest",
            26,
            15,
            26,
            36
        )
        assert ir.unit_blocks[0].atomic_units[4].type == "shell"
        assert len(ir.unit_blocks[0].atomic_units[4].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[4].attributes[0].name == "run"
        self._check_value(
            ir.unit_blocks[0].atomic_units[4].attributes[0].value,
            String,
            "cd glitch\n          python -m unittest discover tests",
            28,
            11,
            29,
            44
        )
        assert ir.unit_blocks[0].atomic_units[4].attributes[0].line == 27
        assert ir.unit_blocks[0].atomic_units[4].attributes[0].end_line == 29
        assert ir.unit_blocks[0].atomic_units[4].attributes[0].column == 9
        assert ir.unit_blocks[0].atomic_units[4].attributes[0].end_column == 44

    def test_gha_parser_valid_workflow_2(self) -> None:
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
        self._check_binary_operation(
            ir.variables[0].value,
            Sum,
            Access(
                ElementInfo(23, 15, 23, 31, "github.workspace"),
                VariableReference("github", ElementInfo(23, 15, 23, 21, "github")),
                String("workspace", ElementInfo(23, 22, 23, 31, "workspace")),
            ),
            String("/build", ElementInfo(23, 34, 23, 40, "/build")),
            23,
            10,
            23,
            41
        )

        assert len(ir.unit_blocks) == 1

        assert len(ir.unit_blocks[0].variables) == 1
        assert isinstance(ir.unit_blocks[0].variables[0], Variable)
        assert ir.unit_blocks[0].variables[0].name == "run"
        assert isinstance(ir.unit_blocks[0].variables[0].value, Hash)
        assert len(ir.unit_blocks[0].variables[0].value.value) == 1
        assert (
            String("shell", ElementInfo(38, 9, 38, 14, "shell"))
            in ir.unit_blocks[0].variables[0].value.value
        )
        self._check_value(
            ir.unit_blocks[0].variables[0].value.value[
                String("shell", ElementInfo(38, 9, 38, 14, "shell"))
            ],
            String,
            "powershell",
            38,
            16,
            38,
            26
        )

        assert len(ir.unit_blocks[0].atomic_units) == 4
        self._check_value(
            ir.unit_blocks[0].atomic_units[1].name,
            String,
            "Configure CMake",
            44,
            15,
            44,
            30
        )
        assert ir.unit_blocks[0].atomic_units[1].type == "shell"
        assert len(ir.unit_blocks[0].atomic_units[1].attributes) == 1
        assert ir.unit_blocks[0].atomic_units[1].attributes[0].name == "run"
        self._check_binary_operation(
            ir.unit_blocks[0].atomic_units[1].attributes[0].value,
            Sum,
            String("cmake -B ", ElementInfo(45, 14, 45, 23, "cmake -B ")),
            Access(
                ElementInfo(45, 27, 45, 36, "cmake -B ${{ env.build }}"),
                VariableReference("env", ElementInfo(45, 27, 45, 30, "env")),
                String("build", ElementInfo(45, 31, 45, 36, "build"))
            ),
            45,
            14,
            45,
            39
        )

        assert len(ir.comments) == 24

        assert (
            ir.comments[0].content
            == "# https://github.com/actions/starter-workflows/blob/main/code-scanning/msvc.yml"
        )
        assert ir.comments[0].line == 1

        assert ir.comments[9].content == "# for actions/checkout to fetch code"
        assert ir.comments[9].line == 31

    def test_gha_parser_index_out_of_range(self) -> None:
        """
        This file previously gave an index out of range even though it is valid.
        """
        p = GithubActionsParser()
        ir = p.parse_file(
            "tests/parser/gha/files/index_out_of_range.yml", UnitBlockType.script
        )
        assert ir is not None
