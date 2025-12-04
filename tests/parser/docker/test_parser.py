import unittest
from glitch.parsers.docker import DockerParser
from glitch.repr.inter import *

# TODO: The Docker Parser needs a serious refactor.
# We need to rethink the way in which the Dockerfile is parsed to the
# intermediate representation. And also fix the parsing bugs.


class TestDockerParser(unittest.TestCase):
    @unittest.skip("Incorrectly parsed")
    def test_docker_parser_valid_file(self) -> None:
        p = DockerParser()
        ir = p.parse_file("tests/parser/docker/files/Dockerfile", UnitBlockType.script)
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script

        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block

    @unittest.skip("Incorrectly parsed")
    def test_docker_parser_valid_file_2(self) -> None:
        p = DockerParser()
        ir = p.parse_file(
            "tests/parser/docker/files/2.Dockerfile", UnitBlockType.script
        )
        assert ir is not None

        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script

        assert len(ir.unit_blocks) == 1
        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
