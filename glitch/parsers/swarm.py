# type: ignore #TODO

import os
from typing import Any, List, Optional
import re
from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import (
    MappingNode,
    ScalarNode,
    SequenceNode,
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
    Hash,
    Module,
    Project,
    String,
    UnitBlock,
    UnitBlockType,
    Array,
    Dependency,
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

        def create_attribute(
            token: Token | Node | None, name: str, value: Any, _info: ElementInfo = None
        ) -> Attribute:
            if _info is not None and token is None:
                # HACK:  (Part of) Handling transforming attributes coming from ">>" inserts to normal attributes
                info = _info
            else:
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
                    if isinstance(att[1], ScalarNode) and att[1].tag.endswith("bool"):
                        # HACK: turn boolean scalar node values strings into
                        #  real booleans values for get_value method,
                        #  taking into account yaml 1.1 using the spec provided regexp (used by compose)

                        if re.match(
                            "y|Y|yes|Yes|YES|true|True|TRUE|on|On|ON", att[1].value
                        ):
                            att[1].value = True
                        elif re.match(
                            "n|N|no|No|NO|false|False|FALSE|off|Off|OFF", att[1].value
                        ):
                            att[1].value = False

                    att_value: Expr = self.get_value(att[1], code)
                    if att[0].value == "environment" and isinstance(
                        att[1], SequenceNode
                    ):
                        """
                        HACK: Converts all Sequence/Arrays environments to Hash
                        environment:
                            - VAR1=123
                            - VAR2=456
                        vs
                        environment:
                            VAR1 : 123
                            VAR2 : 456

                        """
                        fixed_env = {}
                        for elem in att_value.value:
                            elem_info: ElementInfo = ElementInfo.from_code_element(elem)
                            curr_str = elem.value
                            split_str = curr_str.split("=")
                            assert len(split_str) == 2
                            key, n_val = split_str

                            key_s = String(key, elem_info)
                            val_s = String(n_val, elem_info)
                            fixed_env[key_s] = val_s
                        att_info = ElementInfo.from_code_element(att_value)
                        att_value = Hash(fixed_env, att_info)
                    if isinstance(att[1], MappingNode):
                        # HACK:  Handle transforming attributes coming from ">>" inserts to normal attributes
                        if isinstance(att_value, Hash):
                            affected_keys = []
                            temp_store = {}

                            for k, v in att_value.value.items():
                                if k.value == "<<":
                                    affected_keys.append(k)
                                    for _k, _v in v.value.items():
                                        temp_store[_k] = _v

                            att_value.value.update(temp_store)

                            for elem in affected_keys:
                                att_value.value.pop(elem)
                if att[0].value == "<<" and isinstance(att_value, Hash):
                    # HACK:  Handle transforming attributes coming from ">>" inserts to normal attributes
                    for k, v in att_value.value.items():
                        create_attribute(
                            None, k.value, v, ElementInfo.from_code_element(v)
                        )
                else:
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
                includes = []
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
                    file_unit_block.path = os.path.abspath(path)
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
                            elif field[0].value == "include":
                                includes_temp = self.get_value(field[1], code).value

                                for elem in includes_temp:
                                    if isinstance(elem, String):
                                        includes.append(elem.value)
                                    elif isinstance(elem, Hash):
                                        for k, v in elem.value.items():
                                            if k.value == "path":
                                                includes.append(v.value)
                                for elem in includes:
                                    file_unit_block.add_dependency(Dependency([elem]))

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
                                unit_block.path = os.path.abspath(path)
                                unit_block.line = field[0].start_mark.line
                                unit_block.column = field[0].start_mark.column
                                unit_block.end_line = field[0].end_mark.line
                                unit_block.end_column = field[0].end_mark.column

                                for unit in field[1].value:
                                    self.parse_atomic_unit(
                                        field[0].value, unit_block, unit, code
                                    )
                                file_unit_block.add_unit_block(unit_block)

                            elif isinstance(field[0], ScalarNode) and isinstance(
                                field[1], MappingNode
                            ):
                                continue
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

                # FIXME: Handling the includes, might not be the best way
                for inc in includes:
                    curr_path = os.path.split(path)[0]
                    joint_path = os.path.normpath(os.path.join(curr_path, inc))
                    if os.path.exists(joint_path):
                        include_file_unit_block = self.parse_file(joint_path)

                        for ub in include_file_unit_block.unit_blocks:
                            for ub_curr in file_unit_block.unit_blocks:
                                if ub.name == ub_curr.name:
                                    for au in ub.atomic_units:
                                        ub_curr.add_atomic_unit(au)
                    else:
                        print(
                            f'Failed to parse include file expected at "{joint_path}". File not found.'
                        )

                to_extend: List[List[AtomicUnit, Attribute]] = []

                services = []
                for ub in file_unit_block.unit_blocks:
                    if ub.name == "services":
                        services = ub.atomic_units
                # FIXME: Handling the extends from the same file or from other files, might not be the best way
                for service in services:
                    for attribute in service.attributes:
                        if attribute.name == "extends":
                            deps = []
                            # if isinstance(attribute.value,String):
                            #    deps.append(attribute.value.value)
                            if isinstance(attribute.value, Hash):
                                # adds the name of file as a dependency
                                for k, v in attribute.value.value:
                                    if k.value == "file":
                                        deps.append(v.value)
                                        break

                            file_unit_block.add_dependency(Dependency(deps))
                            to_extend.append([service, attribute])
                            break

                for service_to, attribute in to_extend:
                    att: Attribute = attribute
                    service_from_list = []
                    service_from = ""

                    if isinstance(att.value, String):
                        service_from = att.value.value
                        service_from_list = services

                    elif isinstance(att.value, Hash):
                        hash_dict = att.value.value
                        file = ""
                        service_from = ""
                        for k, v in hash_dict.items():
                            if k.value == "file":
                                file = v.value
                            elif k.value == "service":
                                service_from = v.value
                        curr_path = os.path.split(path)[0]
                        joint_path = os.path.normpath(os.path.join(curr_path, file))
                        if os.path.exists(joint_path):
                            service_from_file_unit_block = self.parse_file(joint_path)
                            service_from_list = (
                                service_from_file_unit_block.atomic_units
                            )
                        else:
                            print(
                                f'Failed to parse extends file expected at "{joint_path}". File not found.'
                            )

                    for s in service_from_list:
                        if s.name.value == service_from:
                            att_names = [x.name for x in service_to.attributes]

                            for s_att in s.attributes:
                                if s_att.name in ["depends_on", "volumes_from"]:
                                    continue
                                elif s_att.name not in att_names:
                                    service_to.add_attribute(s_att)
                                elif s_att.name in att_names:
                                    for to_att in service_to.attributes:
                                        if to_att.name == s_att.name:
                                            if isinstance(to_att.value, Array):
                                                self.__handle_array(
                                                    s_att.value, to_att.value
                                                )
                                            elif isinstance(to_att.value, Hash):
                                                self.__handle_hash(
                                                    s_att.value, to_att.value
                                                )
                                            else:
                                                continue
                                            break
                            break

                return file_unit_block
        except:
            throw_exception(EXCEPTIONS["DOCKER_SWARM_COULD_NOT_PARSE"], path)

    def __handle_array(self, src: Array, dst: Array) -> None:
        temp = [elem for elem in src.value if elem not in dst.value]
        for elem in dst.value:
            temp.append(elem)
        dst.value = temp

    def __handle_hash(self, src: Hash, dst: Hash) -> None:
        for k, v in src.value.items():
            if k not in dst.value:
                dst.value[k] = v
            else:
                if isinstance(v, Array):
                    self.__handle_array(v, dst.value[k])
                elif isinstance(v, Hash):
                    self.__handle_hash(v, dst.value[k])

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

        TODO: Think if it is worth considering searching for modules recursively
        especially now since includes and extends from other YAMLs are now implemented

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
