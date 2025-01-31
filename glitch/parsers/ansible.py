import os

from glitch.parsers.yaml import YamlParser
from typing import List, TextIO, Any, Optional, Callable
from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import (
    Node,
    MappingNode,
    SequenceNode,
)
from ruamel.yaml.tokens import Token
from glitch.exceptions import EXCEPTIONS, throw_exception
from glitch.repr.inter import *


class AnsibleParser(YamlParser):
    __TASK_PARAMS = [
        "ansible.builtin.include",
        "any_errors_fatal",
        "ansible.legacy.include",
        "args",
        "async",
        "become",
        "become_exe",
        "become_flags",
        "become_method",
        "become_user",
        "changed_when",
        "collections",
        "connection",
        "debugger",
        "delegate_facts",
        "deletage_to",
        "diff",
        "environment",
        "failed_when",
        "ignore_errors",
        "ignore_unreachable",
        "include",
        "listen",
        "local_action",
        "loop",
        "loop_control",
        "module_defaults",
        "notify",
        "poll",
        "port",
        "register",
        "remote_user",
        "retries",
        "run_once",
        "tags",
        "throttle",
        "timeout",
        "until",
        "vars",
        "when",
        "with_dict" "with_fileglob",
        "with_filetree",
        "with_first_found",
        "with_indexed_items",
        "with_ini",
        "with_inventory_hostnames",
        "with_items",
        "with_lines",
        "with_random_choice",
        "with_sequence",
        "with_subelements",
        "with_together",
    ]

    def __init__(self) -> None:
        super().__init__()

    def __create_variable(
        self,
        token: Token | Node,
        val_node: Node,
        value: Expr,
        name: str,
        code: List[str],
    ) -> Variable:
        if isinstance(value, Null):
            v_code = self._get_code(token, token, code)
        else:
            v_code = self._get_code(token, val_node, code)
        v_code = "".join(code[token.start_mark.line : token.end_mark.line + 1])
        info = ElementInfo(
            token.start_mark.line + 1,
            token.start_mark.column + 1,
            val_node.end_mark.line + 1,
            val_node.end_mark.column + 1,
            v_code,
        )
        return Variable(name, value, info)

    def __parse_vars(self, node: MappingNode, code: List[str]) -> List[Variable]:
        variables: List[Variable] = []

        for key, val in node.value:
            name = key.value
            value = self.get_value(val, code)
            v = self.__create_variable(key, val, value, name, code)
            variables.append(v)

        return variables

    def __create_attribute(
        self,
        token: Token | Node,
        name: str,
        value: Expr,
        val_node: Node,
        code: List[str],
    ) -> Attribute:
        if isinstance(value, Null):
            a_code = self._get_code(token, token, code)
        else:
            a_code = self._get_code(token, val_node, code)

        info = ElementInfo(
            token.start_mark.line + 1,
            token.start_mark.column + 1,
            val_node.end_mark.line + 1,
            val_node.end_mark.column + 1,
            a_code,
        )

        return Attribute(name, value, info)

    def __parse_attribute(
        self, name: str, token: Token | Node, val: Any, code: List[str]
    ) -> Attribute:
        v = self.get_value(val, code)
        return self.__create_attribute(token, name, v, val, code)

    def __parse_tasks(
        self, unit_block: UnitBlock, tasks: Node, code: List[str]
    ) -> None:
        for task in tasks.value:
            atomic_units: List[AtomicUnit] = []
            attributes: List[Attribute] = []
            type, name, line = "", Null(), 0
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
                    self.__parse_tasks(unit_block, val, code)
                    created = len(unit_block.atomic_units) - size
                    atomic_units = unit_block.atomic_units[-created:]
                elif key.value == "name":
                    name = self.get_value(val, code)
                elif key.value != "name":
                    if type == "" and key.value not in AnsibleParser.__TASK_PARAMS:
                        type = key.value
                        line = task.start_mark.line + 1

                        if isinstance(name, Array):
                            for n in name.value:
                                atomic_units.append(AtomicUnit(n, type))
                        else:
                            atomic_units.append(AtomicUnit(name, type))

                    if isinstance(val, MappingNode) and key.value == type:
                        for atr, atr_val in val.value:
                            attributes.append(
                                self.__parse_attribute(atr.value, atr, atr_val, code)
                            )
                    else:
                        attributes.append(
                            self.__parse_attribute(key.value, key, val, code)
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
                au = AtomicUnit(Null(), type)
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
                        vars = self.__parse_vars(value, code)
                        for v in vars:
                            play.add_variable(v)
                    elif key.value in ["tasks", "pre_tasks", "post_tasks", "handlers"]:
                        self.__parse_tasks(play, value, code)
                    else:
                        play.attributes.append(
                            self.__parse_attribute(key.value, key, value, code)
                        )

                unit_block.add_unit_block(play)

            for comment in self._get_comments(parsed_file, file):
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

            self.__parse_tasks(unit_block, parsed_file, code)
            for comment in self._get_comments(parsed_file, file):
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

            assert isinstance(parsed_file, MappingNode)
            vars = self.__parse_vars(parsed_file, code)
            for v in vars:
                unit_block.add_variable(v)
            for comment in self._get_comments(parsed_file, file):
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
