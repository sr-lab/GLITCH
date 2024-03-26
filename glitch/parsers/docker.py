import ast
import os.path
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union

import bashlex  # type: ignore
from dockerfile_parse import DockerfileParser

import glitch.parsers.parser as p
from glitch.exceptions import throw_exception, EXCEPTIONS
from glitch.repr.inter import *


@dataclass
class DFPStructure:
    content: str
    endline: int
    instruction: str
    startline: int
    value: str
    raw_content: str


class DockerParser(p.Parser):
    def parse_file(self, path: str, type: UnitBlockType) -> UnitBlock:
        try:
            with open(path) as f:
                file_lines = list(f)
                f.seek(0)
                dfp = DockerfileParser()
                dfp.content = f.read()
                structure = [
                    DFPStructure(
                        raw_content="".join(
                            file_lines[s["startline"] : s["endline"] + 1]
                        ),
                        **s,
                    )
                    for s in dfp.structure
                ]

                stage_indexes = [
                    i for i, e in enumerate(structure) if e.instruction == "FROM"
                ]
                if len(stage_indexes) > 1:
                    main_block = UnitBlock(os.path.basename(path), type)
                    main_block.code = dfp.content
                    stages = self.__get_stages(stage_indexes, structure)
                    for i, (name, s) in enumerate(stages):
                        unit_block = self.__parse_stage(
                            name, path, UnitBlockType.block, s
                        )
                        unit_block.line = structure[stage_indexes[i]].startline + 1
                        unit_block.code = "".join([struct.content for struct in s])
                        main_block.add_unit_block(unit_block)
                else:
                    self.__add_user_tag(structure)
                    main_block = self.__parse_stage(
                        dfp.baseimage, path, type, structure
                    )
                    main_block.line = (
                        structure[stage_indexes[0]].startline + 1
                        if stage_indexes
                        else 1
                    )
                    main_block.code = "".join([struct.content for struct in structure])

                main_block.path = path
                return main_block
        except Exception as e:
            throw_exception(EXCEPTIONS["DOCKER_UNKNOW_ERROR"], str(e))
            main_block = UnitBlock(os.path.basename(path), type)
            main_block.path = path
            return main_block

    def parse_folder(self, path: str) -> Project:
        project = Project(os.path.basename(os.path.normpath(path)))
        project.blocks, project.modules = self._parse_folder(path)
        return project

    def parse_module(self, path: str) -> Module:
        module = Module(os.path.basename(os.path.normpath(path)), path)
        module.blocks, module.modules = self._parse_folder(path)
        return module

    def _parse_folder(self, path: str) -> Tuple[List[UnitBlock], List[Module]]:
        files = [os.path.join(path, f) for f in os.listdir(path)]
        dockerfiles = [
            f
            for f in files
            if os.path.isfile(f) and "Dockerfile" in os.path.basename(f)
        ]
        modules = [
            f
            for f in files
            if os.path.isdir(f) and DockerParser._contains_dockerfiles(f)
        ]

        blocks = [self.parse_file(f, UnitBlockType.script) for f in dockerfiles]
        modules = [self.parse_module(f) for f in modules]
        return blocks, modules

    @staticmethod
    def _contains_dockerfiles(path: str) -> bool:
        if not os.path.exists(path):
            return False
        if not os.path.isdir(path):
            return "Dockerfile" in os.path.basename(path)
        for f in os.listdir(path):
            contains_dockerfiles = DockerParser._contains_dockerfiles(
                os.path.join(path, f)
            )
            if contains_dockerfiles:
                return True
        return False

    @staticmethod
    def __parse_stage(
        name: str, path: str, unit_type: UnitBlockType, structure: List[DFPStructure]
    ) -> UnitBlock:
        u = UnitBlock(name, unit_type)
        u.path = path
        for s in structure:
            try:
                DockerParser.__parse_instruction(s, u)
            except NotImplementedError:
                throw_exception(EXCEPTIONS["DOCKER_NOT_IMPLEMENTED"], s.content)
        return u

    @staticmethod
    def __parse_instruction(element: DFPStructure, unit_block: UnitBlock) -> None:
        instruction = element.instruction
        if instruction in ["ENV", "USER", "ARG", "LABEL"]:
            unit_block.variables += DockerParser.__create_variable_block(element)
        elif instruction == "COMMENT":
            c = Comment(element.value)
            c.line = element.startline + 1
            c.code = element.content
            unit_block.add_comment(c)
        elif instruction in ["RUN", "CMD", "ENTRYPOINT"]:
            try:
                c_parser = CommandParser(element)
                aus = c_parser.parse_command()
                unit_block.atomic_units += aus
            except Exception:
                throw_exception(EXCEPTIONS["SHELL_COULD_NOT_PARSE"], element.content)
        elif instruction == "ONBUILD":
            dfp = DockerfileParser()
            dfp.content = element.value
            element = DFPStructure(
                **dfp.structure[0], raw_content=dfp.structure[0]["content"]
            )
            DockerParser.__parse_instruction(element, unit_block)
        elif instruction == "COPY":
            au = AtomicUnit("", "copy")
            paths = [v for v in element.value.split(" ") if not v.startswith("--")]
            au.add_attribute(Attribute("src", str(paths[0:-1]), False))
            au.add_attribute(Attribute("dest", paths[-1], False))
            for attr in au.attributes:
                attr.code = element.content
                attr.line = element.startline + 1
            au.code = element.content
            au.line = element.startline + 1
            unit_block.add_atomic_unit(au)
        # TODO: Investigate keywords and parse them
        elif instruction in ["ADD", "VOLUME", "WORKDIR"]:
            pass
        elif instruction in ["STOPSIGNAL", "HEALTHCHECK", "SHELL"]:
            pass
        elif instruction == "EXPOSE":
            pass

    @staticmethod
    def __get_stages(
        stage_indexes: List[int], structure: List[DFPStructure]
    ) -> List[Tuple[str, List[DFPStructure]]]:
        stages: List[Tuple[str, List[DFPStructure]]] = []
        for i, stage_i in enumerate(stage_indexes):
            stage_image = structure[stage_i].value.split(" ")[0]
            stage_start = stage_i if i != 0 else 0
            stage_end = (
                len(structure) if i == len(stage_indexes) - 1 else stage_indexes[i + 1]
            )
            stages.append(
                (
                    stage_image,
                    DockerParser.__get_stage_structure(
                        structure, stage_start, stage_end
                    ),
                )
            )
        return stages

    @staticmethod
    def __get_stage_structure(
        structure: List[DFPStructure], stage_start: int, stage_end: int
    ):
        sub_structure = structure[stage_start:stage_end].copy()
        DockerParser.__add_user_tag(sub_structure)
        return sub_structure

    @staticmethod
    def __create_variable_block(element: DFPStructure) -> List[Variable]:
        variables: List[Variable] = []
        if element.instruction == "USER":
            variables.append(Variable("user-profile", element.value, False))
        elif element.instruction == "ARG":
            value = element.value.split("=")
            arg = value[0]
            default = value[1] if len(value) == 2 else None
            variables.append(Variable(arg, default if default else "ARG", True))
        elif element.instruction == "ENV":
            if "=" in element.value:
                # TODO: Improve code attribution for multiple values
                return DockerParser.__parse_multiple_key_value_variables(
                    element.content, element.startline
                )
            if len(element.value.split(" ")) != 2:
                raise NotImplementedError()
            env, value = element.value.split(" ")
            variables.append(Variable(env, value, value.startswith("$")))
        else:  # LABEL
            return DockerParser.__parse_multiple_key_value_variables(
                element.content, element.startline
            )

        for v in variables:
            if v.value == '""' or v.value == "''":
                v.value = ""
            v.line = element.startline + 1
            v.code = element.content
        return variables

    @staticmethod
    def __parse_multiple_key_value_variables(
        content: str, base_line: int
    ) -> List[Variable]:
        variables: List[Variable] = []
        for i, line in enumerate(content.split("\n")):
            for match in re.finditer(
                r"([\w_]*)=(?:(?:'|\")([\w\. <>@]*)(?:\"|')|([\w\.]*))", line
            ):
                value = match.group(2) or match.group(3) or ""
                v = Variable(match.group(1), value, value.startswith("$"))
                v.line = base_line + i + 1
                v.code = line
                variables.append(v)
        return variables

    @staticmethod
    def __add_user_tag(structure: List[DFPStructure]) -> None:
        if len([s for s in structure if s.instruction == "USER"]) > 0:
            return

        index, line = -1, 0
        for i, s in enumerate(structure):
            if s.instruction == "FROM":
                index = i
                line = s.startline
                break
        structure.insert(
            index + 1, DFPStructure("USER root", line, "USER", line, "root", "")
        )


@dataclass
class ShellCommand:
    sudo: bool
    command: str
    args: List[str]
    code: str
    options: Dict[str, Tuple[Union[str, bool, int, float], str]] = field(
        default_factory=dict
    )
    main_arg: Optional[str] = None
    line: int = -1

    def to_atomic_unit(self) -> AtomicUnit:
        au = AtomicUnit(self.main_arg, self.command)
        au.line = self.line
        au.code = self.code
        if self.sudo:
            sudo = Attribute("sudo", "True", False)
            sudo.code = "sudo"
            sudo.line = self.line
            au.add_attribute(sudo)
        for key, (value, _) in self.options.items():
            has_variable = "$" in value if isinstance(value, str) else False
            attr = Attribute(key, value, has_variable)  # type: ignore
            attr.code = self.code
            attr.line = self.line
            au.add_attribute(attr)
        return au


class CommandParser:
    def __init__(self, command: DFPStructure) -> None:
        value = (
            command.content.replace("RUN ", "")
            if command.instruction == "RUN"
            else command.value
        )
        if value.startswith("[") and value.endswith("]"):
            c_list = ast.literal_eval(value)
            value = " ".join(c_list)
        self.dfp_structure = command
        self.command = value
        self.line = command.startline + 1

    def parse_command(self) -> List[AtomicUnit]:
        # TODO: Fix get commands lines for scripts with multiline values
        commands = self.__get_sub_commands()
        aus: List[AtomicUnit] = []
        for line, c in commands:
            try:
                aus.append(self.__parse_single_command(c, line))
            except IndexError:
                throw_exception(EXCEPTIONS["SHELL_COULD_NOT_PARSE"].format(" ".join(c)))
        return aus

    def __parse_single_command(self, command: List[str], line: int) -> AtomicUnit:
        command, carriage_returns = CommandParser.__strip_shell_command(command)
        line += carriage_returns
        sudo = command[0] == "sudo"
        name_index = 0 if not sudo else 1
        command_type = command[name_index]
        if len(command) == name_index + 1:
            return ShellCommand(
                sudo=sudo,
                command=command_type,
                args=[],
                main_arg=command_type,
                line=line,
                code=self.dfp_structure.raw_content,
            ).to_atomic_unit()
        c = ShellCommand(
            sudo=sudo,
            command=command_type,
            args=command[name_index + 1 :],
            line=line,
            code=self.dfp_structure.raw_content,
        )
        CommandParser.__parse_shell_command(c)
        return c.to_atomic_unit()

    @staticmethod
    def __strip_shell_command(command: List[str]) -> Tuple[List[str], int]:
        non_empty_indexes = [
            i for i, c in enumerate(command) if c not in ["\n", "", " ", "\r"]
        ]
        if not non_empty_indexes:
            return ([], 0)
        start, end = non_empty_indexes[0], non_empty_indexes[-1]
        return command[start : end + 1], sum(1 for c in command if c == "\n")

    @staticmethod
    def __parse_shell_command(command: ShellCommand) -> None:
        if command.command == "chmod":
            reference = [arg for arg in command.args if "--reference" in arg]
            command.args = [arg for arg in command.args if not arg.startswith("-")]
            command.main_arg = command.args[-1]
            if reference:
                reference[0]
                command.options["reference"] = (reference.split("=")[1], reference)  # type: ignore
            else:
                command.options["mode"] = command.args[0], command.args[0]
        else:
            CommandParser.__parse_general_command(command)

    @staticmethod
    def __parse_general_command(command: ShellCommand) -> None:
        args = command.args.copy()
        # TODO: Solve issue where last argument is part of a parameter
        main_arg_index = -1 if not args[-1].startswith("-") else 0
        if len(args) >= 3 and args[-2].startswith("-") and not args[0].startswith("-"):
            main_arg_index = 0
        main_arg = args[main_arg_index]
        del args[main_arg_index]
        command.main_arg = main_arg

        for i, o in enumerate(args):
            if not o.startswith("-"):
                continue

            code = o
            o = o.lstrip("-")
            if "=" in o:
                option = o.split("=")
                command.options[option[0]] = option[1], code
                continue

            if len(args) == i + 1 or args[i + 1].startswith("-"):
                command.options[o] = True, code
            else:
                command.options[o] = args[i + 1], f"{code} {args[i+1]}"

    def __get_sub_commands(self) -> List[Tuple[int, List[str]]]:
        commands: List[Tuple[int, List[str]]] = []
        tmp: List[str] = []
        lines = (
            self.command.split("\n")
            if not self.__contains_multi_line_values(self.command)
            else [self.command]
        )
        current_line = self.line
        for i, line in enumerate(lines):
            for part in bashlex.split(line):  # type: ignore
                if part in ["&&", "&", "|", ";"]:
                    commands.append((current_line, tmp))
                    current_line = self.line + i
                    tmp = []
                    continue
                tmp.append(part)  # type: ignore
        commands.append((current_line, tmp))
        return commands

    @staticmethod
    def __contains_multi_line_values(command: str) -> bool:
        def is_multi_line_str(line: str) -> bool:
            return line.count('"') % 2 != 0 or line.count("'") % 2 != 0

        def has_open_parentheses(line: str) -> bool:
            return (
                line.count("(") != line.count(")")
                or line.count("[") != line.count("]")
                or line.count("{") != line.count("}")
            )

        lines = command.split("\n")
        return any(
            (is_multi_line_str(line) or has_open_parentheses(line)) for line in lines
        )
