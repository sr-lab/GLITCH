import os

from glitch.parsers.yaml import YamlParser
from typing import List, TextIO, Any, Optional, Callable
from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import (
    Node,
    ScalarNode,
    MappingNode,
    SequenceNode,
    CollectionNode,
)
from ruamel.yaml.tokens import Token
from glitch.exceptions import EXCEPTIONS, throw_exception
from glitch.repr.inter import *


class AnsibleParser(YamlParser):
    @staticmethod
    def __parse_vars(
        unit_block: UnitBlock,
        cur_name: str,
        node: Node,
        code: List[str],
        child: bool = False,
    ) -> List[Variable]:
        def create_variable(
            token: Token | Node, name: str, value: str | None, child: bool = False
        ) -> Variable:
            has_variable = (
                (("{{" in value) and ("}}" in value)) if value != None else False
            )
            if value in ["null", "~"]:
                value = ""
            v = Variable(name, value, has_variable)
            v.line = token.start_mark.line + 1
            v.column = token.start_mark.column + 1
            if value == None:
                v.code = AnsibleParser._get_code(token, token, code)
            else:
                v.code = AnsibleParser._get_code(token, value, code)
            v.code = "".join(code[token.start_mark.line : token.end_mark.line + 1])

            variables.append(v)
            if not child:
                unit_block.add_variable(v)
            return v

        variables: List[Variable] = []
        if isinstance(node, MappingNode):
            if cur_name == "":
                for key, v in node.value:
                    if hasattr(key, "value") and isinstance(key.value, str):
                        AnsibleParser.__parse_vars(
                            unit_block, key.value, v, code, child
                        )
                    elif isinstance(key.value, MappingNode):
                        AnsibleParser.__parse_vars(
                            unit_block, cur_name, key.value[0][0], code, child  # type: ignore
                        )
            else:
                var = create_variable(node, cur_name, None, child)
                for key, v in node.value:
                    if hasattr(key, "value") and isinstance(key.value, str):
                        var.keyvalues += AnsibleParser.__parse_vars(
                            unit_block, key.value, v, code, True
                        )
                    elif isinstance(key.value, MappingNode):
                        var.keyvalues += AnsibleParser.__parse_vars(
                            unit_block, cur_name, key.value[0][0], code, True  # type: ignore
                        )
        elif isinstance(node, ScalarNode):
            create_variable(node, cur_name, str(node.value), child)
        elif isinstance(node, SequenceNode):
            value: List[Any] = []
            for i, val in enumerate(node.value):
                if isinstance(val, CollectionNode):
                    variables += AnsibleParser.__parse_vars(
                        unit_block, f"{cur_name}[{i}]", val, code, child
                    )
                else:
                    value.append(val.value)

            if len(value) > 0 and isinstance(node.value[-1], (Node, Token)):
                create_variable(node.value[-1], cur_name, str(value), child)

        return variables

    @staticmethod
    def __parse_attribute(
        cur_name: str, token: Token | Node, val: Any, code: List[str]
    ) -> List[Attribute]:
        def create_attribute(token: Token | Node, name: str, value: Any) -> Attribute:
            has_variable = (
                (("{{" in value) and ("}}" in value)) if value != None else False
            )
            if value in ["null", "~"]:
                value = ""
            a = Attribute(name, value, has_variable)
            a.line = token.start_mark.line + 1
            a.column = token.start_mark.column + 1
            if val == None:
                a.code = AnsibleParser._get_code(token, token, code)
            else:
                a.code = AnsibleParser._get_code(token, val, code)
            attributes.append(a)

            return a

        attributes: List[Attribute] = []
        if isinstance(val, MappingNode):
            attribute = create_attribute(token, cur_name, None)
            aux_attributes: List[KeyValue] = []
            for aux, aux_val in val.value:
                aux_attributes += AnsibleParser.__parse_attribute(
                    f"{aux.value}", aux, aux_val, code
                )
            attribute.keyvalues = aux_attributes
        elif isinstance(val, ScalarNode):
            create_attribute(token, cur_name, str(val.value))
        elif isinstance(val, SequenceNode):
            value: List[Any] = []
            for i, v in enumerate(val.value):
                if not isinstance(v, ScalarNode):
                    attributes += AnsibleParser.__parse_attribute(
                        f"{cur_name}[{i}]", v, v, code
                    )
                else:
                    value.append(v.value)

            if len(value) > 0:
                create_attribute(token, cur_name, str(value))

        return attributes

    @staticmethod
    def __parse_tasks(unit_block: UnitBlock, tasks: Node, code: List[str]) -> None:
        for task in tasks.value:
            atomic_units: List[AtomicUnit] = []
            attributes: List[Attribute] = []
            type, name, line = "", "", 0
            is_block = False

            for key, val in task.value:
                # Dependencies
                # FIXME include roles
                if key.value == "include":
                    d = Dependency(val.value)
                    d.line = key.start_mark.line + 1
                    d.code = "".join(code[key.start_mark.line : val.end_mark.line + 1])
                    unit_block.add_dependency(d)
                    break
                if key.value in ["block", "always", "rescue"]:
                    is_block = True
                    size = len(unit_block.atomic_units)
                    AnsibleParser.__parse_tasks(unit_block, val, code)
                    created = len(unit_block.atomic_units) - size
                    atomic_units = unit_block.atomic_units[-created:]
                elif key.value == "name":
                    name = val.value
                elif key.value != "name":
                    if type == "":
                        type = key.value
                        line = task.start_mark.line + 1

                        names: List[str] = [n.strip() for n in name.split(",")]
                        for name in names:
                            if name == "":
                                continue
                            atomic_units.append(AtomicUnit(name, type))

                    if isinstance(val, MappingNode):
                        for atr, atr_val in val.value:
                            if atr.value != "name":
                                attributes += AnsibleParser.__parse_attribute(
                                    atr.value, atr, atr_val, code
                                )
                    else:
                        attributes += AnsibleParser.__parse_attribute(
                            key.value, key, val, code
                        )

            if is_block:
                for au in atomic_units:
                    au.attributes += attributes
                continue

            # If it was a task without a module we ignore it (e.g. dependency)
            for au in atomic_units:
                if au.type != "":
                    au.line = line
                    au.attributes = attributes.copy()
                    if len(au.attributes) > 0:
                        au.code = "".join(code[au.line - 1 : au.attributes[-1].line])
                    else:
                        au.code = code[au.line - 1]
                    unit_block.add_atomic_unit(au)

            # Tasks without name
            if len(atomic_units) == 0 and type != "":
                au = AtomicUnit("", type)
                au.attributes = attributes
                au.line = line
                if len(au.attributes) > 0:
                    au.code = "".join(code[au.line - 1 : au.attributes[-1].line])
                else:
                    au.code = code[au.line - 1]
                unit_block.add_atomic_unit(au)

    def __parse_playbook(
        self, name: str, file: TextIO, parsed_file: Optional[Node] = None
    ) -> Optional[UnitBlock]:
        try:
            if parsed_file is None:
                parsed_file = YAML().compose(file)
            unit_block = UnitBlock(name, UnitBlockType.script)
            unit_block.path = file.name
            file.seek(0, 0)
            code = file.readlines()
            code.append("")  # HACK allows to parse code in the end of the file

            if parsed_file is None:
                return unit_block

            for p in parsed_file.value:
                # Plays are unit blocks inside a unit block
                play = UnitBlock("", UnitBlockType.block)
                play.path = file.name

                for key, value in p.value:
                    if key.value == "name" and play.name == "":
                        play.name = value.value
                    elif key.value == "vars":
                        AnsibleParser.__parse_vars(play, "", value, code)
                    elif key.value in ["tasks", "pre_tasks", "post_tasks", "handlers"]:
                        AnsibleParser.__parse_tasks(play, value, code)
                    else:
                        play.attributes += AnsibleParser.__parse_attribute(
                            key.value, key, value, code
                        )

                unit_block.add_unit_block(play)

            for comment in AnsibleParser._get_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_PLAYBOOK"], file.name)
            return None

    def __parse_tasks_file(
        self, name: str, file: TextIO, parsed_file: Optional[Node] = None
    ) -> Optional[UnitBlock]:
        try:
            if parsed_file is None:
                parsed_file = YAML().compose(file)
            unit_block = UnitBlock(name, UnitBlockType.tasks)
            unit_block.path = file.name
            file.seek(0, 0)
            code = file.readlines()
            code.append("")  # HACK allows to parse code in the end of the file

            if parsed_file is None:
                return unit_block

            AnsibleParser.__parse_tasks(unit_block, parsed_file, code)
            for comment in AnsibleParser._get_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_TASKS_FILE"], file.name)
            return None

    def __parse_vars_file(
        self, name: str, file: TextIO, parsed_file: Optional[Node] = None
    ) -> Optional[UnitBlock]:
        try:
            if parsed_file is None:
                parsed_file = YAML().compose(file)
            unit_block = UnitBlock(name, UnitBlockType.vars)
            unit_block.path = file.name
            file.seek(0, 0)
            code = file.readlines()
            code.append("")  # HACK allows to parse code in the end of the file

            if parsed_file is None:
                return unit_block

            AnsibleParser.__parse_vars(unit_block, "", parsed_file, code)
            for comment in AnsibleParser._get_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_VARS_FILE"], file.name)
            return None

    @staticmethod
    def __apply_to_files(
        module: Module | Project,
        path: str,
        p_function: Callable[[str, TextIO], Optional[UnitBlock]],
    ) -> None:
        if os.path.exists(path) and os.path.isdir(path) and not os.path.islink(path):
            files = [
                f
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
                and not f.startswith(".")
                and f.endswith((".yml", ".yaml"))
            ]
            for file in files:
                f_path = os.path.join(path, file)
                with open(f_path) as f:
                    unit_block = p_function(f_path, f)
                    if unit_block is not None:
                        module.add_block(unit_block)

    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        AnsibleParser.__apply_to_files(res, f"{path}/tasks", self.__parse_tasks_file)
        AnsibleParser.__apply_to_files(res, f"{path}/handlers", self.__parse_tasks_file)
        AnsibleParser.__apply_to_files(res, f"{path}/vars", self.__parse_vars_file)
        AnsibleParser.__apply_to_files(res, f"{path}/defaults", self.__parse_vars_file)

        # Check subfolders
        subfolders = [
            f.path for f in os.scandir(f"{path}/") if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not in [
                "tasks",
                "handlers",
                "vars",
                "defaults",
            ]:
                aux = self.parse_module(d)
                res.blocks += aux.blocks

        return res

    def parse_folder(self, path: str, root: bool = True) -> Project:
        """
        It follows the sample directory layout found in:
        https://docs.ansible.com/ansible/latest/user_guide/sample_setup.html#sample-directory-layout
        """
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        if root:
            AnsibleParser.__apply_to_files(res, f"{path}", self.__parse_playbook)
        AnsibleParser.__apply_to_files(res, f"{path}/playbooks", self.__parse_playbook)
        AnsibleParser.__apply_to_files(
            res, f"{path}/group_vars", self.__parse_vars_file
        )
        AnsibleParser.__apply_to_files(res, f"{path}/host_vars", self.__parse_vars_file)
        AnsibleParser.__apply_to_files(res, f"{path}/tasks", self.__parse_tasks_file)

        if os.path.exists(f"{path}/roles") and not os.path.islink(f"{path}/roles"):
            subfolders = [
                f.path
                for f in os.scandir(f"{path}/roles")
                if f.is_dir() and not f.is_symlink()
            ]
            for m in subfolders:
                res.add_module(self.parse_module(m))

        # Check subfolders
        subfolders = [
            f.path for f in os.scandir(f"{path}") if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not in [
                "playbooks",
                "group_vars",
                "host_vars",
                "tasks",
                "roles",
            ]:
                aux = self.parse_folder(d, root=False)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res

    def parse_file(self, path: str, type: UnitBlockType) -> Optional[UnitBlock]:
        with open(path) as f:
            try:
                parsed_file = YAML().compose(f)
                f.seek(0, 0)
            except:
                throw_exception(EXCEPTIONS["ANSIBLE_COULD_NOT_PARSE"], path)
                return None

            if type == UnitBlockType.unknown:
                if isinstance(parsed_file, MappingNode):
                    type = UnitBlockType.vars
                elif (
                    isinstance(parsed_file, SequenceNode)
                    and len(parsed_file.value) > 0
                    and isinstance(parsed_file.value[0], MappingNode)
                ):
                    hosts = False

                    for key in parsed_file.value[0].value:
                        if key[0].value == "hosts":
                            hosts = True
                            break

                    type = UnitBlockType.script if hosts else UnitBlockType.tasks
                elif (
                    isinstance(parsed_file, SequenceNode)
                    and len(parsed_file.value) == 0
                ):
                    type = UnitBlockType.script
                else:
                    throw_exception(EXCEPTIONS["ANSIBLE_FILE_TYPE"], path)
                    return None

            if type == UnitBlockType.script:
                return self.__parse_playbook(path, f, parsed_file=parsed_file)
            elif type == UnitBlockType.tasks:
                return self.__parse_tasks_file(path, f, parsed_file=parsed_file)
            elif type == UnitBlockType.vars:
                return self.__parse_vars_file(path, f, parsed_file=parsed_file)
