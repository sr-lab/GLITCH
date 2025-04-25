# type: ignore #TODO

import os
from typing import Any, List, Optional

from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import (
    MappingNode,
    Node,
)
from ruamel.yaml.tokens import Token

from glitch.exceptions import EXCEPTIONS, throw_exception
from glitch.parsers.yaml import YamlParser
from glitch.repr.inter import (
    AtomicUnit,
    Attribute,
    Comment,
    ElementInfo,
    Expr,
    Module,
    Project,
    String,
    UnitBlock,
    UnitBlockType,
)


class SwarmParser(YamlParser):
    """
    Stack/Compose YAML files parser
    """

    def parse_atomic_unit(
        self, type: str, unit_block: UnitBlock, dict: tuple[Any, Any], code: List[str]
    ) -> None:
        """
        Parses and creates AtomicUnits
        """

        def create_atomic_unit(
            start_line: Token | Node,
            end_line: Token | Node,
            type: str,
            name: str,
            code: List[str],
        ) -> AtomicUnit:
            name_info = ElementInfo(
                start_line.start_mark.line + 1,
                start_line.start_mark.column + 1,
                start_line.end_mark.line + 1,
                start_line.end_mark.column + 1,
                self._get_code(start_line, start_line, code),
            )
            str_name = String(name, name_info)

            au = AtomicUnit(str_name, type)
            au.line = start_line.start_mark.line + 1
            au.end_line = end_line.end_mark.line + 1
            au.end_column = end_line.end_mark.column + 1
            au.column = start_line.start_mark.column + 1
            au.code = self._get_code(start_line, end_line, code)
            return au

        au: AtomicUnit = create_atomic_unit(
            dict[0], dict[1], type[:-1], dict[0].value, code
        )
        au.attributes += self.__parse_attributes(dict[1], code)

        unit_block.add_atomic_unit(au)

    def __parse_attributes(self, val: Any, code: List[str]) -> List[Attribute]:
        """
        Parses the Attributes of an AtomicUnit
        """

        def create_attribute(token: Token | Node, name: str, value: Any) -> Attribute:
            info: ElementInfo = ElementInfo(
                token.start_mark.line + 1,
                token.start_mark.column + 1,
                token.end_mark.line + 1,
                token.end_mark.column + 1,
                self._get_code(token, token, code),
            )
            a: Attribute = Attribute(name, value, info)
            attributes.append(a)
            return a

        attributes: List[Attribute] = []

        if isinstance(val, MappingNode):
            for att in val.value:
                if isinstance(att, tuple):
                    att_value: Expr = self.get_value(att[1], code)
                    create_attribute(att[0], att[0].value, att_value)

        return attributes

    def parse_file(
        self, path: str, type: UnitBlockType = UnitBlockType.script
    ) -> Optional[UnitBlock]:
        """
        Parses a stack/compose file into a UnitBlock each with its respective
        AtomicUnits (each of the services,networks,volumes,configs and secrets)
        and their Attributes
        """
        try:
            with open(path, "r") as f:
                try:
                    parsed_file = YAML().compose(f)
                    f.seek(0, 0)
                    code: List[str] = f.readlines()
                    code.append("")
                    f.seek(0, 0)
                except:
                    throw_exception(EXCEPTIONS["DOCKER_SWARM_COULD_NOT_PARSE"], path)
                    return None
                if isinstance(parsed_file, MappingNode):
                    file_unit_block: UnitBlock = UnitBlock(
                        os.path.basename(os.path.normpath(path)), type
                    )
                    file_unit_block.path = path
                    if isinstance(parsed_file.value, list):
                        for field in parsed_file.value:
                            if field[0].value == "version":
                                expr: Expr = self.get_value(field[1], code)
                                info: ElementInfo = ElementInfo(
                                    field[0].start_mark.line + 1,
                                    field[0].start_mark.column + 1,
                                    field[1].end_mark.line + 1,
                                    field[1].end_mark.column + 1,
                                    self._get_code(field[0], field[1], code),
                                )
                                att: Attribute = Attribute(field[0].value, expr, info)
                                file_unit_block.add_attribute(att)
                            elif field[0].value in [
                                "services",
                                "networks",
                                "volumes",
                                "configs",
                                "secrets",
                            ]:
                                unit_block = UnitBlock(
                                    field[0].value, UnitBlockType.block
                                )
                                unit_block.line = field[0].start_mark.line
                                unit_block.column = field[0].start_mark.column
                                unit_block.end_line = field[0].end_mark.line
                                unit_block.end_column = field[0].end_mark.column

                                for unit in field[1].value:
                                    self.parse_atomic_unit(
                                        field[0].value, unit_block, unit, code
                                    )
                                file_unit_block.add_unit_block(unit_block)

                            else:
                                throw_exception(
                                    EXCEPTIONS["DOCKER_SWARM_COULD_NOT_PARSE"], path
                                )

                    for comment in self._get_comments(parsed_file, f):
                        c = Comment(comment[1])
                        c.line = comment[0]
                        c.code = code[c.line - 1]
                        file_unit_block.add_comment(c)
                file_unit_block.code = "".join(code)
                return file_unit_block
        except:
            throw_exception(EXCEPTIONS["DOCKER_SWARM_COULD_NOT_PARSE"], path)

    def parse_folder(self, path: str, root: bool = True) -> Optional[Project]:
        """
        Swarm doesn't have a standard/sample directory layout,
        but normally the stack/compose files are either at the root of
        a projects folder, all in a specific folder or a stack for
        different parts of the system are in each part subfolder
        we consider each subfolder a Module
        """
        if root:
            res: Project = Project(os.path.basename(os.path.normpath(path)))

            subfolders = [
                f.path
                for f in os.scandir(f"{path}")
                if f.is_dir() and not f.is_symlink()
            ]

            for d in subfolders:
                res.add_module(self.parse_module(d))

            files = [
                f.path
                for f in os.scandir(f"{path}")
                if f.is_file()
                and not f.is_symlink()
                and f.path.endswith((".yml", ".yaml"))
            ]

            for fi in files:
                res.add_block(self.parse_file(fi))
            return res
        else:
            return None

    def parse_module(self, path) -> Module:
        """
        We consider each subfolder of the Project folder a Module
        
        TODO:Think if it is worth considering searching for modules recursively
        as done for other languagues supported by GLITCH
        """
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)

        files = [
            f.path
            for f in os.scandir(f"{path}")
            if f.is_file() and not f.is_symlink() and f.path.endswith((".yml", ".yaml"))
        ]

        for fi in files:
            res.add_block(self.parse_file(fi))

        return res
