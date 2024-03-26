# type: ignore
# TODO: The file needs a refactor so the types make sense
import os
import re
import hcl2
import glitch.parsers.parser as p

from glitch.exceptions import EXCEPTIONS, throw_exception
from glitch.repr.inter import *
from typing import Sequence, List, Dict, Any


class TerraformParser(p.Parser):
    @staticmethod
    def __get_element_code(start_line: int, end_line: int, code: List[str]) -> str:
        lines = code[start_line - 1 : end_line]
        res = ""
        for line in lines:
            res += line
        return res

    def parse_keyvalues(
        self,
        unit_block: UnitBlock,
        keyvalues: Dict[Any, Any],
        code: List[str],
        type: str,
    ) -> List[KeyValue]:
        def create_keyvalue(start_line: int, end_line: int, name: str, value: str):
            has_variable = (
                ("${" in f"{value}") and ("}" in f"{value}") if value != None else False  # type: ignore
            )
            pattern = r"^[+-]?\d+(\.\d+)?$"
            if has_variable and re.match(pattern, re.sub(r"^\${(.*)}$", r"\1", value)):
                value = re.sub(r"^\${(.*)}$", r"\1", value)
                has_variable = False
            if value == "null":
                value = ""

            if isinstance(value, int):
                value = str(value)

            if type == "attribute":
                keyvalue = Attribute(str(name), value, has_variable)
            else:
                keyvalue = Variable(str(name), value, has_variable)

            keyvalue.line = start_line
            keyvalue.code = TerraformParser.__get_element_code(
                start_line, end_line, code
            )

            return keyvalue

        def process_list(name: str, value: str, start_line: int, end_line: int) -> None:
            for i, v in enumerate(value):
                if isinstance(v, dict):
                    k = create_keyvalue(start_line, end_line, name + f"[{i}]", None)  # type: ignore
                    k.keyvalues = self.parse_keyvalues(unit_block, v, code, type)
                    k_values.append(k)
                elif isinstance(v, list):
                    process_list(name + f"[{i}]", v, start_line, end_line)
                else:
                    k = create_keyvalue(start_line, end_line, name + f"[{i}]", v)
                    k_values.append(k)

        k_values: List[KeyValue] = []
        for name, keyvalue in keyvalues.items():
            if name == "__start_line__" or name == "__end_line__":
                continue

            if isinstance(
                keyvalue, dict
            ):  # Note: local values (variables) can only enter here
                value = keyvalue["value"]
                if isinstance(value, dict):  # (ex: labels = {})
                    k = create_keyvalue(
                        keyvalue["__start_line__"], keyvalue["__end_line__"], name, None  # type: ignore
                    )
                    k.keyvalues = self.parse_keyvalues(unit_block, value, code, type)
                    k_values.append(k)
                elif isinstance(value, list):  # (ex: x = [1,2,3])
                    process_list(
                        name,
                        value,
                        keyvalue["__start_line__"],
                        keyvalue["__end_line__"],
                    )
                else:  # (ex: x = 'test')
                    if value == None:  # (ex: x = null)
                        value = "null"
                    k = create_keyvalue(
                        keyvalue["__start_line__"],
                        keyvalue["__end_line__"],
                        name,
                        value,
                    )
                    k_values.append(k)
            elif isinstance(keyvalue, list) and type == "attribute":  # type: ignore
                # block (ex: access {} or dynamic setting {}; blocks of attributes; not allowed inside local values (variables))
                try:
                    for block_attributes in keyvalue:
                        k = create_keyvalue(
                            block_attributes["__start_line__"],
                            block_attributes["__end_line__"],
                            name,
                            None,
                        )
                        k.keyvalues = self.parse_keyvalues(
                            unit_block, block_attributes, code, type
                        )
                        k_values.append(k)
                except KeyError:
                    for block in keyvalue:
                        for block_name, block_attributes in block.items():
                            k = create_keyvalue(
                                block_attributes["__start_line__"],
                                block_attributes["__end_line__"],
                                f"{name}.{block_name}",
                                None,
                            )
                            k.keyvalues = self.parse_keyvalues(
                                unit_block, block_attributes, code, type
                            )
                            k_values.append(k)

        return k_values

    def parse_atomic_unit(
        self, type: str, unit_block: UnitBlock, dict, code: List[str]
    ) -> None:
        def create_atomic_unit(
            start_line: int, end_line: int, type: str, name: str, code: List[str]
        ) -> AtomicUnit:
            au = AtomicUnit(name, type)
            au.line = start_line
            au.code = TerraformParser.__get_element_code(start_line, end_line, code)
            return au

        def parse_resource() -> None:
            for resource_type, resource in dict.items():
                for name, attributes in resource.items():
                    au = create_atomic_unit(
                        attributes["__start_line__"],
                        attributes["__end_line__"],
                        f"{type}.{resource_type}",
                        name,
                        code,
                    )
                    au.attributes = self.parse_keyvalues(
                        unit_block, attributes, code, "attribute"
                    )
                    unit_block.add_atomic_unit(au)

        def parse_simple_unit() -> None:
            for name, attributes in dict.items():
                au = create_atomic_unit(
                    attributes["__start_line__"],
                    attributes["__end_line__"],
                    type,
                    name,
                    code,
                )
                au.attributes = self.parse_keyvalues(
                    unit_block, attributes, code, "attribute"
                )
                unit_block.add_atomic_unit(au)

        if type in ["resource", "data"]:
            parse_resource()
        elif type in ["variable", "module", "output"]:
            parse_simple_unit()

    def parse_comments(
        self, unit_block: UnitBlock, comments: Sequence[str], code: List[str]
    ) -> None:
        def create_comment(value: str, start_line: int, end_line: int, code: List[str]):
            c = Comment(value)
            c.line = start_line
            c.code = TerraformParser.__get_element_code(start_line, end_line, code)
            return c

        for comment in comments:
            unit_block.add_comment(
                create_comment(
                    comment["value"],
                    comment["__start_line__"],
                    comment["__end_line__"],
                    code,
                )
            )

    def parse_file(self, path: str, type: UnitBlockType) -> UnitBlock:
        unit_block = UnitBlock(path, type)
        unit_block.path = path
        try:
            with open(path) as f:
                parsed_hcl = hcl2.load(f, True)
                f.seek(0, 0)
                code = f.readlines()
                for key, value in parsed_hcl.items():
                    if key in ["resource", "data", "variable", "module", "output"]:
                        for v in value:
                            self.parse_atomic_unit(key, unit_block, v, code)
                    elif key == "__comments__":
                        self.parse_comments(unit_block, value, code)
                    elif key == "locals":
                        for local in value:
                            unit_block.variables += self.parse_keyvalues(
                                unit_block, local, code, "variable"
                            )
                    elif key in ["provider", "terraform"]:
                        continue
                    else:
                        throw_exception(EXCEPTIONS["TERRAFORM_COULD_NOT_PARSE"], path)
        except:
            throw_exception(EXCEPTIONS["TERRAFORM_COULD_NOT_PARSE"], path)
        return unit_block

    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        files = [
            f.path for f in os.scandir(f"{path}") if f.is_file() and not f.is_symlink()
        ]
        for f in files:
            unit_block = self.parse_file(f, UnitBlockType.unknown)
            res.add_block(unit_block)

        return res

    def parse_folder(self, path: str) -> Project:
        res: Project = Project(os.path.basename(os.path.normpath(path)))
        res.add_module(self.parse_module(path))

        subfolders = [
            f.path for f in os.scandir(f"{path}") if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            aux = self.parse_folder(d)
            res.blocks += aux.blocks
            res.modules += aux.modules

        return res
