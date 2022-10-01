import os
import re
import tempfile
from puppetparser.parser import parse as parse_puppet
import puppetparser.model as puppetmodel
from string import Template
from pkg_resources import resource_filename
import ruamel.yaml as yaml
from ruamel.yaml import ScalarNode, MappingNode, SequenceNode, \
    CommentToken, CollectionNode
from glitch.exceptions import EXCEPTIONS, throw_exception

import glitch.parsers.parser as p
from glitch.repr.inter import *
from glitch.parsers.ripper_parser import parser_yacc
from glitch.helpers import remove_unmatched_brackets

class AnsibleParser(p.Parser):
    @staticmethod
    def __get_yaml_comments(d, file):
        def extract_from_token(tokenlist):
            res = []
            for token in tokenlist:
                if token is None:
                    continue
                elif isinstance(token, list):
                    res += extract_from_token(token)
                elif isinstance(token, CommentToken):
                    res.append((token.start_mark.line, token.value))
            return res

        def yaml_comments(d):
            res = []

            if isinstance(d, MappingNode):
                if d.comment is not None:
                    for line, comment in extract_from_token(d.comment):
                        res.append((line, comment))
                for _, val in d.value:
                    for line, comment in yaml_comments(val):
                        res.append((line, comment))
            elif isinstance(d, SequenceNode):
                if d.comment is not None:
                    for line, comment in extract_from_token(d.comment):
                        res.append((line, comment))
                for item in d.value:
                    for line, comment in yaml_comments(item):
                        res.append((line, comment))
            elif isinstance(d, ScalarNode):
                if d.comment is not None:
                    res = extract_from_token(d.comment)

            return res

        file.seek(0, 0)
        f_lines = file.readlines()

        comments = []
        for c_group in yaml_comments(d):
            line = c_group[0]
            c_group_comments = c_group[1].strip().split("\n")

            for i, comment in enumerate(c_group_comments):
                if comment == "": continue
                aux = line + i
                comment = comment.strip()

                while comment not in f_lines[aux]:
                    aux += 1
                comments.append((aux + 1, comment))      

        for i, line in enumerate(f_lines):
            if line.strip().startswith("#"):
                comments.append((i + 1, line.strip()))

        return set(comments)

    @staticmethod
    def __get_element_code(start_token, end_token, code):
        if isinstance(end_token, list) and len(end_token) > 0:
            end_token = end_token[-1]
        elif isinstance(end_token, list) or isinstance(end_token, str):
            end_token = start_token

        if start_token.start_mark.line == end_token.end_mark.line:
            res = code[start_token.start_mark.line][start_token.start_mark.column : end_token.end_mark.column]
        else:
            res = code[start_token.start_mark.line]
        
        for line in range(start_token.start_mark.line + 1, end_token.end_mark.line):
            res += code[line]
        
        if start_token.start_mark.line != end_token.end_mark.line:
            res += code[end_token.end_mark.line][:end_token.end_mark.column]

        return res

    @staticmethod
    def __parse_vars(unit_block, cur_name, token, code):
        def create_variable(name, value):
            has_variable = ("{{" in value) and ("}}" in value)
            if (value in ["null", "~"]): value = ""
            v = Variable(name, value, has_variable)
            v.line = token.start_mark.line + 1
            v.code = AnsibleParser.__get_element_code(token, value, code)
            v.code = ''.join(code[token.start_mark.line : token.end_mark.line + 1])
            unit_block.add_variable(v)

        if isinstance(token, MappingNode):
            for key, v in token.value:
                if hasattr(key, "value") and isinstance(key.value, str):
                    AnsibleParser.__parse_vars(unit_block, cur_name + key.value + ".", v, code)
                elif isinstance(key.value, MappingNode):
                    AnsibleParser.__parse_vars(unit_block, cur_name, key.value[0][0], code)
        elif isinstance(token, SequenceNode):
            value = []
            for i, v in enumerate(token.value):
                if isinstance(v, CollectionNode):
                    AnsibleParser.__parse_vars(unit_block, f"{cur_name[:-1]}[{i}].", v, code)
                else:
                    value.append(v.value)

            if (len(value) > 0):
                create_variable(cur_name[:-1], str(value))
        elif cur_name != "":
            create_variable(cur_name[:-1], str(token.value))

    @staticmethod
    def __parse_attribute(cur_name, token, val, code):
        def create_attribute(token, name, value):
            has_variable = ("{{" in value) and ("}}" in value)
            if (value in ["null", "~"]): value = ""
            a = Attribute(name, value, has_variable)
            a.line = token.start_mark.line + 1
            a.code = AnsibleParser.__get_element_code(token, val, code)
            attributes.append(a)

        attributes = []
        if isinstance(val, MappingNode):
            for aux, aux_val in val.value:
                attributes += AnsibleParser.__parse_attribute(f"{cur_name}.{aux.value}", 
                        aux, aux_val, code)
        elif isinstance(val, ScalarNode):
            create_attribute(token, cur_name, str(val.value))
        elif isinstance(val, SequenceNode):
            value = []
            for i, v in enumerate(val.value):
                if not isinstance(v, ScalarNode):
                    attributes += AnsibleParser.__parse_attribute(f"{cur_name}[{i}]", token, v, code)
                else:
                    value.append(v.value)

            if len(value) > 0:
                create_attribute(token, cur_name, str(value))

        return attributes

    @staticmethod
    def __parse_tasks(unit_block, tasks, code):
        for task in tasks.value:
            atomic_units, attributes = [], []
            type, name, line = "", "", 0
            is_block = False

            for key, val in task.value:
                # Dependencies
                # FIXME include roles
                if key.value == "include":
                    d = Dependency(val.value)
                    d.line = key.start_mark.line + 1
                    d.code = ''.join(code[key.start_mark.line : val.end_mark.line + 1])
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

                        names = [n.strip() for n in name.split(',')]
                        for name in names:
                            if name == "": continue
                            atomic_units.append(AtomicUnit(name, type))

                    if (isinstance(val, MappingNode)):
                        for atr, atr_val in val.value:
                            if (atr.value != "name"):
                                attributes += AnsibleParser.__parse_attribute(atr.value, atr, atr_val, code)
                    else:
                        attributes += AnsibleParser.__parse_attribute(key.value, key, val, code)

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
                        au.code = ''.join(code[au.line - 1 : au.attributes[-1].line])
                    else:
                        au.code = code[au.line - 1]
                    unit_block.add_atomic_unit(au)

            # Tasks without name
            if (len(atomic_units) == 0 and type != ""):
                au = AtomicUnit("", type)
                au.attributes = attributes
                au.line = line
                if len(au.attributes) > 0:
                    au.code = ''.join(code[au.line - 1 : au.attributes[-1].line])
                else:
                    au.code = code[au.line - 1]
                unit_block.add_atomic_unit(au)

    def __parse_playbook(self, name, file, parsed_file = None) -> UnitBlock:
        try:
            if parsed_file is None: parsed_file = yaml.YAML().compose(file)
            unit_block = UnitBlock(name, UnitBlockType.script)
            unit_block.path = file.name
            file.seek(0, 0)
            code = file.readlines()
            code.append("")  # HACK allows to parse code in the end of the file

            for p in parsed_file.value:
                # Plays are unit blocks inside a unit block
                play = UnitBlock("", UnitBlockType.block)
                play.path = file.name

                for key, value in p.value:
                    if (key.value == "name" and play.name == ""):
                        play.name = value.value
                    elif (key.value == "vars"):
                        AnsibleParser.__parse_vars(play, "", value, code)
                    elif (key.value in ["tasks", "pre_tasks", "post_tasks", "handlers"]):
                        AnsibleParser.__parse_tasks(play, value, code)
                    else:
                        play.attributes += AnsibleParser.__parse_attribute(key.value, key, value, code)

                unit_block.add_unit_block(play)

            for comment in AnsibleParser.__get_yaml_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_PLAYBOOK"], file.name)
            return None

    def __parse_tasks_file(self, name, file, parsed_file = None) -> UnitBlock:
        try:
            if parsed_file is None: parsed_file = yaml.YAML().compose(file)
            unit_block = UnitBlock(name, UnitBlockType.tasks)
            unit_block.path = file.name
            file.seek(0, 0)
            code = file.readlines()
            code.append("") # HACK allows to parse code in the end of the file

            if parsed_file is None:
                return unit_block

            AnsibleParser.__parse_tasks(unit_block, parsed_file, code)
            for comment in AnsibleParser.__get_yaml_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_TASKS_FILE"], file.name)
            return None

    def __parse_vars_file(self, name, file, parsed_file=None) -> UnitBlock:
        try:
            if parsed_file is None: parsed_file = yaml.YAML().compose(file)
            unit_block = UnitBlock(name, UnitBlockType.vars)
            unit_block.path = file.name
            file.seek(0, 0)
            code = file.readlines()
            code.append("")  # HACK allows to parse code in the end of the file

            if parsed_file is None:
                return unit_block

            AnsibleParser.__parse_vars(unit_block, "", parsed_file, code)
            for comment in AnsibleParser.__get_yaml_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_VARS_FILE"], file.name)
            return None

    @staticmethod
    def __apply_to_files(module, path, p_function):
        if os.path.exists(path) and os.path.isdir(path) \
                and not os.path.islink(path):
            files = [f for f in os.listdir(path) \
                if os.path.isfile(os.path.join(path, f))
                    and not f.startswith('.') and f.endswith(('.yml', '.yaml'))]
            for file in files:
                f_path = os.path.join(path, file)
                with open(f_path) as f:
                    unit_block = p_function(f_path, f)
                    if (unit_block is not None):
                        module.add_block(unit_block)

    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        AnsibleParser.__apply_to_files(res, f"{path}/tasks", self.__parse_tasks_file)
        AnsibleParser.__apply_to_files(res, f"{path}/handlers", self.__parse_tasks_file)
        AnsibleParser.__apply_to_files(res, f"{path}/vars", self.__parse_vars_file)
        AnsibleParser.__apply_to_files(res, f"{path}/defaults", self.__parse_vars_file)

        # Check subfolders
        subfolders = [f.path for f in os.scandir(f"{path}/") if f.is_dir() and not f.is_symlink()]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not \
                    in ["tasks", "handlers", "vars", "defaults"]:
                aux = self.parse_module(d)
                res.blocks += aux.blocks

        return res

    def parse_folder(self, path: str, root=True) -> Project:
        '''
        It follows the sample directory layout found in:
        https://docs.ansible.com/ansible/latest/user_guide/sample_setup.html#sample-directory-layout
        '''
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        if root:
            AnsibleParser.__apply_to_files(res, f"{path}", self.__parse_playbook)
        AnsibleParser.__apply_to_files(res, f"{path}/playbooks", self.__parse_playbook)
        AnsibleParser.__apply_to_files(res, f"{path}/group_vars", self.__parse_vars_file)
        AnsibleParser.__apply_to_files(res, f"{path}/host_vars", self.__parse_vars_file)
        AnsibleParser.__apply_to_files(res, f"{path}/tasks", self.__parse_tasks_file)

        if os.path.exists(f"{path}/roles") and not os.path.islink(f"{path}/roles"):
            subfolders = [f.path for f in os.scandir(f"{path}/roles") 
                if f.is_dir() and not f.is_symlink()]
            for m in subfolders:
                res.add_module(self.parse_module(m))

        # Check subfolders
        subfolders = [f.path for f in os.scandir(f"{path}") 
            if f.is_dir() and not f.is_symlink()]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not \
                    in ["playbooks", "group_vars", "host_vars", "tasks", "roles"]:
                aux = self.parse_folder(d, root=False)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res

    def parse_file(self, path: str, blocktype: UnitBlockType) -> UnitBlock:
        with open(path) as f:
            try:
                parsed_file = yaml.YAML().compose(f)
                f.seek(0, 0)
            except:
                throw_exception(EXCEPTIONS["ANSIBLE_COULD_NOT_PARSE"], path)
                return None

            if blocktype == UnitBlockType.unknown:
                if isinstance(parsed_file, MappingNode):
                    blocktype = UnitBlockType.vars
                elif isinstance(parsed_file, SequenceNode) and len(parsed_file.value) > 0 \
                        and isinstance(parsed_file.value[0], MappingNode):
                    hosts = False

                    for key in parsed_file.value[0].value:
                        if key[0].value == "hosts":
                            hosts = True
                            break
                    
                    blocktype = UnitBlockType.script if hosts else UnitBlockType.tasks
                elif isinstance(parsed_file, SequenceNode) and len(parsed_file.value) == 0:
                    blocktype = UnitBlockType.script
                else:
                    throw_exception(EXCEPTIONS["ANSIBLE_FILE_TYPE"], path)
                    return None
        
            if (blocktype == UnitBlockType.script):
                return self.__parse_playbook(path, f, parsed_file=parsed_file)
            elif (blocktype == UnitBlockType.tasks):
                return self.__parse_tasks_file(path, f, parsed_file=parsed_file)
            elif (blocktype == UnitBlockType.vars):
                return self.__parse_vars_file(path, f, parsed_file=parsed_file)

class ChefParser(p.Parser):
    class Node:
        id: str
        args: list

        def __init__(self, id, args) -> None:
            self.id = id
            self.args = args

        def __repr__(self) -> str:
            return str(self.id)

        def __iter__(self):
            return iter(self.args)

        def __reversed__(self):
            return reversed(self.args)

    @staticmethod
    def _check_id(ast, ids):
        return isinstance(ast, ChefParser.Node) and ast.id in ids

    @staticmethod
    def _check_node(ast, ids, size):
        return ChefParser._check_id(ast, ids) and len(ast.args) == size

    @staticmethod
    def _check_has_variable(ast):
        references = ["vcall", "call", "aref", "fcall", "var_ref"]
        if (ChefParser._check_id(ast, ["args_add_block"])):
            return ChefParser._check_id(ast.args[0][0], references)
        elif(ChefParser._check_id(ast, ["method_add_arg"])):
            return ChefParser._check_id(ast.args[0], references)
        elif (ChefParser._check_id(ast, ["arg_paren"])):
            return len(ast.args) > 0 and ChefParser._check_has_variable(ast.args[0])
        elif (ChefParser._check_node(ast, ["binary"], 3)):
            return ChefParser._check_has_variable(ast.args[0]) and \
                    ChefParser._check_has_variable(ast.args[2])
        else:
            return ChefParser._check_id(ast, references)

    @staticmethod
    def _get_content_bounds(ast, source):
        def is_bounds(l):
            return (isinstance(l, list) and len(l) == 2 and isinstance(l[0], int)
                    and isinstance(l[1], int))
        start_line, start_column = float('inf'), float('inf')
        end_line, end_column = 0, 0
        bounded_structures = \
            ["brace_block", "arg_paren", "string_literal", 
                "string_embexpr", "aref", "array", "args_add_block"]

        if (isinstance(ast, ChefParser.Node) and len(ast.args) > 0 and is_bounds(ast.args[-1])):
            start_line, start_column = ast.args[-1][0], ast.args[-1][1]
            # The second argument counting from the end has the content
            # of the node (variable name, string...)
            end_line, end_column = ast.args[-1][0], ast.args[-1][1] + len(ast.args[-2]) - 1

            # With identifiers we need to consider the : behind them
            if (ChefParser._check_id(ast, ["@ident"])
                and source[start_line - 1][start_column - 1] == ":"):
                start_column -= 1
            elif ChefParser._check_id(ast, ["@tstring_content"]):
                end_line += ast.args[0].count('\\n')

        elif isinstance(ast, (list, ChefParser.Node)):
            for arg in ast:
                bound = ChefParser._get_content_bounds(arg, source)
                if bound[0] < start_line: start_line = bound[0]
                if bound[1] < start_column: start_column = bound[1]
                if bound[2] > end_line: end_line = bound[2]
                if bound[3] > end_column: end_column = bound[3]

            # We have to consider extra characters which correspond
            # to enclosing characters of these structures
            if (start_line != float('inf') and ChefParser._check_id(ast, bounded_structures)):
                r_brackets = ['}', ')', ']', '"', '\'']
                # Add spaces/brackets in front of last token
                for i, c in enumerate(source[end_line - 1][end_column + 1:]):
                    if c in r_brackets:
                        end_column += i + 1
                        break
                    elif not c.isspace(): break

                l_brackets = ['{', '(', '[', '"', '\'']
                # Add spaces/brackets behind first token
                for i, c in enumerate(source[start_line - 1][:start_column][::-1]):
                    if c in l_brackets:
                        start_column -= i + 1
                        break
                    elif not c.isspace(): break

                if (ChefParser._check_id(ast, ['string_embexpr']) 
                        and source[start_line - 1][start_column] == "{" and
                        source[start_line - 1][start_column - 1] == "#"):
                    start_column -= 1

            # The original AST does not have the start column
            # of these refs. We need to consider the ::
            elif ChefParser._check_id(ast, ["top_const_ref"]):
                start_column -= 2

        return (start_line, start_column, end_line, end_column)

    @staticmethod
    def _get_content(ast, source):
        empty_structures = {
            'string_literal': "",
            'hash': "{}",
            'array': "[]"
        }

        if isinstance(ast, list):
            return ''.join(list(map(lambda a: ChefParser._get_content(a, source), ast)))

        if ((ast.id in empty_structures and len(ast.args) == 0) or
                (ast.id == 'string_literal' and len(ast.args[0].args) == 0)):
            return empty_structures[ast.id]

        bounds = ChefParser._get_content_bounds(ast, source)

        res = ""
        if bounds[0] == float('inf'):
            return res

        for l in range(bounds[0] - 1, bounds[2]):
            if bounds[0] - 1 == bounds[2] - 1:
                res += source[l][bounds[1]:bounds[3] + 1]
            elif l == bounds[2] - 1:
                res += source[l][:bounds[3] + 1]
            elif l == bounds[0] - 1:
                res += source[l][bounds[1]:]
            else:
                res += source[l]

        if ((ast.id == "method_add_block") and (ast.args[1].id == "do_block")):
            res += "\nend"

        res = res.strip()
        if res.startswith(('"', "'")) and res.endswith(('"', "'")):
            res = res[1:-1]
        
        return remove_unmatched_brackets(res)

    @staticmethod
    def _get_source(ast, source):
        bounds = ChefParser._get_content_bounds(ast, source)
        return ''.join(source[bounds[0] - 1 : bounds[2]])

    class Checker:
        def __init__(self, source):
            self.tests_ast_stack = []
            self.source = source

        def check(self):
            tests, ast = self.pop()
            for test in tests:
                if test(ast):
                    return True

            return False

        def check_all(self):
            status = True
            while (len(self.tests_ast_stack) != 0 and status):
                status = self.check()
            return status

        def push(self, tests, ast):
            self.tests_ast_stack.append((tests, ast))

        def pop(self):
            return self.tests_ast_stack.pop()

    class ResourceChecker(Checker):
        def __init__(self, atomic_unit, source, ast):
            super().__init__(source)
            self.push([self.is_block_resource,
                self.is_inline_resource], ast)
            self.atomic_unit = atomic_unit

        def is_block_resource(self, ast):
            if (ChefParser._check_node(ast, ["method_add_block"], 2) and
                ChefParser._check_node(ast.args[0], ["command"], 2)
                    and ChefParser._check_node(ast.args[1], ["do_block"], 1)):
                self.push([self.is_resource_body], ast.args[1])
                self.push([self.is_resource_def], ast.args[0])
                self.atomic_unit.code = ChefParser._get_content(ast, self.source)
                self.atomic_unit.line = ChefParser._get_content_bounds(ast, self.source)[0]
                return True
            return False

        def is_inline_resource(self, ast):
            if (ChefParser._check_node(ast, ["command"], 2) and
                ChefParser._check_id(ast.args[0], ["@ident"])
                    and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)):
                self.push([self.is_resource_body_without_attributes,
                    self.is_inline_resource_name], ast.args[1])
                self.push([self.is_resource_type], ast.args[0])
                self.atomic_unit.code = ChefParser._get_content(ast, self.source)
                self.atomic_unit.line = ChefParser._get_content_bounds(ast, self.source)[0]
                return True
            return False

        def is_resource_def(self, ast):
            if (ChefParser._check_node(ast.args[0], ["@ident"], 2)
                and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)):
                self.push([self.is_resource_name], ast.args[1])
                self.push([self.is_resource_type], ast.args[0])
                return True
            return False

        def is_resource_type(self, ast):
            if (isinstance(ast.args[0], str) and isinstance(ast.args[1], list) \
                and not ast.args[0] in ["action",
                                        "converge_by",
                                        "include_recipe",
                                        "deprecated_property_alias"]):
                if ast.args[0] == "define": return False
                self.atomic_unit.type = ast.args[0]
                return True
            return False

        def is_resource_name(self, ast):
            if (isinstance(ast.args[0][0], ChefParser.Node) and ast.args[1] is False):
                resource_id = ast.args[0][0]
                self.atomic_unit.name = ChefParser._get_content(resource_id, self.source)
                return True
            return False

        def is_inline_resource_name(self, ast):
            if (ChefParser._check_node(ast.args[0][0], ["method_add_block"], 2)
                and ast.args[1] is False):
                resource_id = ast.args[0][0].args[0]
                self.atomic_unit.name = ChefParser._get_content(resource_id, self.source)
                self.push([self.is_attribute], ast.args[0][0].args[1])
                return True
            return False

        def is_resource_body(self, ast):
            if ChefParser._check_id(ast.args[0], ["bodystmt"]):
                self.push([self.is_attribute], ast.args[0].args[0])
                return True
            return False

        def is_resource_body_without_attributes(self, ast):
            if (ChefParser._check_id(ast.args[0][0], ["string_literal"]) and ast.args[1] is False):
                self.atomic_unit.name = ChefParser._get_content(ast.args[0][0], self.source)
                return True
            return False

        def is_attribute(self, ast):
            if (ChefParser._check_node(ast, ["method_add_arg"], 2)
                    and ChefParser._check_id(ast.args[0], ["call"])):
                self.push([self.is_attribute], ast.args[0].args[0])
            elif ((ChefParser._check_id(ast, ["command", "method_add_arg"]) 
                        and ast.args[1] != []) or
                            (ChefParser._check_id(ast, ["method_add_block"]) and
                                ChefParser._check_id(ast.args[0], ["method_add_arg"]) and
                                    ChefParser._check_id(ast.args[1], ["brace_block", "do_block"]))):
                has_variable = ChefParser._check_has_variable(ast.args[1])
                value = ChefParser._get_content(ast.args[1], self.source)
                if value == "nil": 
                    value = ""
                    has_variable = False
                a = Attribute(ChefParser._get_content(ast.args[0], self.source),
                        value, has_variable)
                a.line = ChefParser._get_content_bounds(ast, self.source)[0]
                a.code = ChefParser._get_source(ast, self.source)
                self.atomic_unit.add_attribute(a)
            elif isinstance(ast, (ChefParser.Node, list)):
                for arg in reversed(ast):
                    self.push([self.is_attribute], arg)

            return True

    class VariableChecker(Checker):
        def __init__(self, source, ast):
            super().__init__(source)
            self.variables = []
            self.push([self.is_variable], ast)

        def is_variable(self, ast):
            def parse_variable(ast, key, current_name, value_ast):
                if ChefParser._check_node(value_ast, ["hash"], 1) \
                    and ChefParser._check_id(value_ast.args[0], ["assoclist_from_args"]):
                        for assoc in value_ast.args[0].args[0]:
                            parse_variable(ast, assoc.args[0], current_name + "." +
                                ChefParser._get_content(assoc.args[0], self.source), 
                                    assoc.args[1])
                else:
                    value = ChefParser._get_content(value_ast, self.source)
                    has_variable = ChefParser._check_has_variable(value_ast)
                    if value == "nil": 
                        value = ""
                        has_variable = False
                    variable = Variable(current_name, value, has_variable)
                    variable.line = ChefParser._get_content_bounds(key, self.source)[0]
                    variable.code = ChefParser._get_source(ast, self.source)
                    self.variables.append(variable)

            if ChefParser._check_node(ast, ["assign"], 2):
                name = ""
                names = ChefParser._get_content(ast.args[0], self.source).split("[")
                for n in names:
                    if n.endswith("]"):
                        n = n[:-1]
                    if (n.startswith("'") and n.endswith("'")) or \
                            (n.startswith('"') and n.endswith('"')):
                        name += n[1:-1]
                    elif n.startswith(":"):
                        name += n[1:]
                    else:
                        name += n

                    name += "."
                name = name[:-1]
                parse_variable(ast, ast.args[0], name, ast.args[1])
                return True

            return False

    class IncludeChecker(Checker):
        def __init__(self, source, ast):
            super().__init__(source)
            self.push([self.is_include], ast)
            self.code = ""

        def is_include(self, ast):
            if (ChefParser._check_node(ast, ["command"], 2) 
                    and ChefParser._check_id(ast.args[0], ["@ident"])
                        and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)):
                self.push([self.is_include_name], ast.args[1])
                self.push([self.is_include_type], ast.args[0])
                self.code = ChefParser._get_source(ast, self.source)
                return True
            return False

        def is_include_type(self, ast):
            if (isinstance(ast.args[0], str) and isinstance(ast.args[1], list)
                and ast.args[0] == "include_recipe"):
                return True
            return False

        def is_include_name(self, ast):
            if (ChefParser._check_id(ast.args[0][0], ["string_literal"]) and ast.args[1] is False):
                d = Dependency(ChefParser._get_content(ast.args[0][0], self.source))
                d.line = ChefParser._get_content_bounds(ast, self.source)[0]
                d.code = self.code
                self.include = d
                return True
            return False

    # FIXME only identifying case statement
    class ConditionChecker(Checker):
        def __init__(self, source, ast):
            super().__init__(source)
            self.push([self.is_case], ast)

        def is_case(self, ast):
            if ChefParser._check_node(ast, ["case"], 2):
                self.case_head = ChefParser._get_content(ast.args[0], self.source)
                self.condition = None
                self.push([self.is_case_condition], ast.args[1])
                return True
            elif ChefParser._check_node(ast, ["case"], 1):
                self.case_head = ""
                self.condition = None
                self.push([self.is_case_condition], ast.args[0])
                return True
            return False

        def is_case_condition(self, ast):
            if (ChefParser._check_node(ast, ["when"], 3) \
                    or ChefParser._check_node(ast, ["when"], 2)):
                if self.condition is None:
                    self.condition = ConditionStatement(
                        self.case_head + " == " + ChefParser._get_content(ast.args[0][0], self.source),
                        ConditionStatement.ConditionType.SWITCH
                    )
                    self.condition.code = ChefParser._get_source(ast, self.source)
                    self.condition.line = ChefParser._get_content_bounds(ast, self.source)[0] - 1
                    self.condition.repr_str = "case " + self.case_head
                    self.current_condition = self.condition
                else:
                    self.current_condition.else_statement = ConditionStatement(
                        self.case_head + " == " + ChefParser._get_content(ast.args[0][0], self.source),
                        ConditionStatement.ConditionType.SWITCH
                    )
                    self.current_condition = self.current_condition.else_statement
                    self.current_condition.code = ChefParser._get_source(ast, self.source)
                    self.current_condition.line = ChefParser._get_content_bounds(ast, self.source)[0]
                if (len(ast.args) == 3):
                    self.push([self.is_case_condition], ast.args[2])
                return True
            elif (ChefParser._check_node(ast, ["else"], 1)):
                self.current_condition.else_statement = ConditionStatement(
                    "",
                    ConditionStatement.ConditionType.SWITCH,
                    is_default=True
                )
                self.current_condition.else_statement.line = \
                        ChefParser._get_content_bounds(ast, self.source)[0]
                return True
            return False

    @staticmethod
    def __create_ast(l):
        args = []
        for el in l[1:]:
            if isinstance(el, list):
                if len(el) > 0 and isinstance(el[0], tuple) and el[0][0] == "id":
                    args.append(ChefParser.__create_ast(el))
                else:
                    arg = []
                    for e in el:
                        if isinstance(e, list) and isinstance(e[0], tuple) and e[0][0] == "id":
                            arg.append(ChefParser.__create_ast(e))
                        else:
                            arg.append(e)
                    args.append(arg)
            else:
                args.append(el)

        return ChefParser.Node(l[0][1], args)

    @staticmethod
    def __transverse_ast(ast, unit_block, source):
        if isinstance(ast, list):
            for arg in ast:
                if isinstance(arg, (ChefParser.Node, list)):
                    ChefParser.__transverse_ast(arg, unit_block, source)
        else:
            resource_checker = ChefParser.ResourceChecker(AtomicUnit("", ""), source, ast)
            if resource_checker.check_all():
                unit_block.add_atomic_unit(resource_checker.atomic_unit)
                return

            variable_checker = ChefParser.VariableChecker(source, ast)
            if variable_checker.check_all():
                for variable in variable_checker.variables:
                    unit_block.add_variable(variable)
                # variables might have resources associated to it
                ChefParser.__transverse_ast(ast.args[1], unit_block, source)
                return

            include_checker = ChefParser.IncludeChecker(source, ast)
            if include_checker.check_all():
                unit_block.add_dependency(include_checker.include)
                return

            if_checker = ChefParser.ConditionChecker(source, ast)
            if if_checker.check_all():
                unit_block.add_statement(if_checker.condition)
                # Check blocks inside
                ChefParser.__transverse_ast(ast.args[len(ast.args) - 1], unit_block, source)
                return

            for arg in ast.args:
                if isinstance(arg, (ChefParser.Node, list)):
                    ChefParser.__transverse_ast(arg, unit_block, source)

    @staticmethod
    def __parse_recipe(path, file) -> UnitBlock:
        with open(os.path.join(path, file)) as f:
            ripper = resource_filename("glitch.parsers", 'resources/comments.rb.template')
            ripper = open(ripper, "r")
            ripper_script = Template(ripper.read())
            ripper.close()
            ripper_script = ripper_script.substitute({'path': '\"' + os.path.join(path, file)+ '\"'})

            if "/attributes/" in path:
                unit_block: UnitBlock = UnitBlock(file, UnitBlockType.vars)
            else:
                unit_block: UnitBlock = UnitBlock(file, UnitBlockType.script)
            unit_block.path = os.path.join(path, file)
            
            try:
                source = f.readlines()
            except:
                    throw_exception(EXCEPTIONS["CHEF_COULD_NOT_PARSE"], os.path.join(path, file))

            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                tmp.write(ripper_script)
                tmp.flush()

                try:
                    p = os.popen('ruby ' + tmp.name)
                    script_ast = p.read()
                    p.close()
                    comments, _ = parser_yacc(script_ast)
                    if comments is not None: comments.reverse()

                    for comment, line in comments:
                        c = Comment(re.sub(r'\\n$', '', comment))
                        c.code = source[line - 1]
                        c.line = line
                        unit_block.add_comment(c)
                except:
                    throw_exception(EXCEPTIONS["CHEF_COULD_NOT_PARSE"], os.path.join(path, file))

            try:
                p = os.popen('ruby -r ripper -e \'file = \
                    File.open(\"' + os.path.join(path, file) + '\")\npp Ripper.sexp(file)\'')
                script_ast = p.read()
                p.close()
                _, program = parser_yacc(script_ast)
                ast = ChefParser.__create_ast(program)
                ChefParser.__transverse_ast(ast, unit_block, source)
            except:
                throw_exception(EXCEPTIONS["CHEF_COULD_NOT_PARSE"], os.path.join(path, file))

            return unit_block

    def parse_module(self, path: str) -> Module:
        def parse_folder(path: str):
            if os.path.exists(path):
                files = [f for f in os.listdir(path) \
                    if os.path.isfile(os.path.join(path, f))]
                for file in files:
                    res.add_block(self.__parse_recipe(path, file))

        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        parse_folder(path + "/resources/")
        parse_folder(path + "/recipes/")
        parse_folder(path + "/attributes/")
        parse_folder(path + "/definitions/")
        parse_folder(path + "/libraries/")
        parse_folder(path + "/providers/")

        return res

    def parse_file(self, path: str, type: UnitBlockType) -> UnitBlock:
        return self.__parse_recipe(os.path.dirname(path), os.path.basename(path))

    def parse_folder(self, path: str) -> Project:
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        res.add_module(self.parse_module(path))

        if (os.path.exists(f"{path}/cookbooks")):
            cookbooks = [f.path for f in os.scandir(f"{path}/cookbooks") 
                if f.is_dir() and not f.is_symlink()]
            for cookbook in cookbooks:
                res.add_module(self.parse_module(cookbook))

        subfolders = [f.path for f in os.scandir(f"{path}") 
            if f.is_dir() and not f.is_symlink()]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not \
                    in ["cookbooks", "resources", "attributes", "recipes", 
                        "definitions", "libraries", "providers"]:
                aux = self.parse_folder(d)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res

class PuppetParser(p.Parser):
    @staticmethod
    def __process_unitblock_component(ce, unit_block: UnitBlock):
        if isinstance(ce, Dependency):
            unit_block.add_dependency(ce)
        elif isinstance(ce, Variable):
            unit_block.add_variable(ce)
        elif isinstance(ce, AtomicUnit):
            unit_block.add_atomic_unit(ce)
        elif isinstance(ce, UnitBlock):
            unit_block.add_unit_block(ce)
        elif isinstance(ce, Attribute):
            unit_block.add_attribute(ce)
        elif isinstance(ce, ConditionStatement):
            unit_block.add_statement(ce)
        elif isinstance(ce, list):
            for c in ce:
                PuppetParser.__process_unitblock_component(c, unit_block)

    @staticmethod
    def __process_codeelement(codeelement, path, code):
        def get_code(ce):
            if ce.line == ce.end_line:
                res = code[ce.line - 1][ce.col - 1 : ce.end_col - 1]
            else:
                res = code[ce.line - 1]
            
            for line in range(ce.line, ce.end_line - 1):
                res += code[line]
            
            if ce.line != ce.end_line:
                res += code[ce.end_line - 1][:ce.end_col - 1]

            return res
        
        if (isinstance(codeelement, puppetmodel.Value)):
            if isinstance(codeelement, puppetmodel.Hash):
                res = {}

                for key, value in codeelement.value.items():
                    res[PuppetParser.__process_codeelement(key, path, code)] = \
                        PuppetParser.__process_codeelement(value, path, code)

                return res
            elif isinstance(codeelement, puppetmodel.Array):
                return str(PuppetParser.__process_codeelement(codeelement.value, path, code))
            elif codeelement.value == None:
                return ""
            return str(codeelement.value)
        elif (isinstance(codeelement, puppetmodel.Attribute)):
            name = PuppetParser.__process_codeelement(codeelement.key, path, code)
            if codeelement.value is not None:
                temp_value = PuppetParser.__process_codeelement(codeelement.value, path, code)
                value = "" if temp_value == "undef" else temp_value
            else:
                value = None
            has_variable = not isinstance(value, str) or value.startswith("$")
            attribute = Attribute(name, value, has_variable)
            attribute.line, attribute.column = codeelement.line, codeelement.col
            attribute.code = get_code(codeelement)
            return attribute
        elif (isinstance(codeelement, puppetmodel.Resource)):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_codeelement(codeelement.title, path, code), 
                PuppetParser.__process_codeelement(codeelement.type, path, code)
            )
            for attr in codeelement.attributes:
                resource.add_attribute(PuppetParser.__process_codeelement(attr, path, code))
            resource.line, resource.column = codeelement.line, codeelement.col
            resource.code = get_code(codeelement)
            return resource 
        elif (isinstance(codeelement, puppetmodel.ClassAsResource)):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_codeelement(codeelement.title, path, code), 
                "class"
            )
            for attr in codeelement.attributes:
                resource.add_attribute(PuppetParser.__process_codeelement(attr, path, code))
            resource.line, resource.column = codeelement.line, codeelement.col
            resource.code = get_code(codeelement)
            return resource 
        elif (isinstance(codeelement, puppetmodel.ResourceDeclaration)):
            unit_block: UnitBlock = UnitBlock(
                PuppetParser.__process_codeelement(codeelement.name, path, code),
                UnitBlockType.block
            )
            unit_block.path = path

            if (codeelement.block is not None):
                for ce in list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.block)):
                    PuppetParser.__process_unitblock_component(ce, unit_block)

            for p in codeelement.parameters:
                unit_block.add_attribute(PuppetParser.__process_codeelement(p, path, code))

            unit_block.line, unit_block.column = codeelement.line, codeelement.col
            unit_block.code = get_code(codeelement)

            return unit_block
        elif (isinstance(codeelement, puppetmodel.Parameter)):
            # FIXME Parameters are not yet supported
            name = PuppetParser.__process_codeelement(codeelement.name, path, code)
            if codeelement.default is not None:
                temp_value = PuppetParser.__process_codeelement(codeelement.default, path, code)
                value = "" if temp_value == "undef" else temp_value
            else:
                value = None
            has_variable = not isinstance(value, str) or temp_value.startswith("$") or \
                    codeelement.default is None
            attribute = Attribute(
                name,
                value,
                has_variable
            )
            attribute.line, attribute.column = codeelement.line, codeelement.col
            attribute.code = get_code(codeelement)
            return attribute
        elif (isinstance(codeelement, puppetmodel.Assignment)):
            name = PuppetParser.__process_codeelement(codeelement.name, path, code)
            temp_value = PuppetParser.__process_codeelement(codeelement.value, path, code)
            if not isinstance(temp_value, dict):
                if codeelement.value is not None:
                    value = "" if temp_value == "undef" else temp_value
                else:
                    value = None
                has_variable = not isinstance(value, str) or value.startswith("$")
                variable: Variable = Variable(name, value, has_variable)
                variable.line, variable.column = codeelement.line, codeelement.col
                variable.code = get_code(codeelement)
                return variable
            else:
                res = []
                for key, value in temp_value.items():
                    res.append(PuppetParser.__process_codeelement(
                            puppetmodel.Assignment(codeelement.line, codeelement.col, 
                                    codeelement.end_line, codeelement.end_col, name + "." + key, value), path, code))
                return res
        elif (isinstance(codeelement, puppetmodel.PuppetClass)):
            # FIXME there are components of the class that are not considered
            unit_block: UnitBlock = UnitBlock(
                PuppetParser.__process_codeelement(codeelement.name, path, code),
                UnitBlockType.block
            )
            unit_block.path = path

            if (codeelement.block is not None):
                for ce in list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.block)):
                    PuppetParser.__process_unitblock_component(ce, unit_block)

            for p in codeelement.parameters:
                unit_block.add_attribute(PuppetParser.__process_codeelement(p, path, code))

            unit_block.line, unit_block.column = codeelement.line, codeelement.col
            unit_block.code = get_code(codeelement)
            return unit_block
        elif (isinstance(codeelement, puppetmodel.Node)):
            # FIXME Nodes are not yet supported
            if (codeelement.block is not None):
                return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.block))
            else:
                return []
        elif (isinstance(codeelement, puppetmodel.Operation)):
            if len(codeelement.arguments) == 1:
                return codeelement.operator + \
                    PuppetParser.__process_codeelement(codeelement.arguments[0], path, code)
            elif codeelement.operator == "[]":
                return \
                    (PuppetParser.__process_codeelement(codeelement.arguments[0], path, code)
                        + "[" + 
                    ','.join(PuppetParser.__process_codeelement(codeelement.arguments[1], path, code))
                        + "]")
            elif len(codeelement.arguments) == 2:
                return \
                    (str(PuppetParser.__process_codeelement(codeelement.arguments[0], path, code))
                        + codeelement.operator + 
                    str(PuppetParser.__process_codeelement(codeelement.arguments[1], path, code)))
            elif codeelement.operator == "[,]":
                return \
                    (PuppetParser.__process_codeelement(codeelement.arguments[0], path, code)
                        + "[" +
                    PuppetParser.__process_codeelement(codeelement.arguments[1], path, code)
                        + "," + 
                    PuppetParser.__process_codeelement(codeelement.arguments[2], path, code)
                        + "]")
        elif (isinstance(codeelement, puppetmodel.Lambda)):
            # FIXME Lambdas are not yet supported
            if (codeelement.block is not None):
                args = []
                for arg in codeelement.parameters:
                    attr = PuppetParser.__process_codeelement(arg, path, code)
                    args.append(Variable(attr.name, "", True))
                return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.block)) + args
            else:
                return []
        elif (isinstance(codeelement, puppetmodel.FunctionCall)):
            # FIXME Function calls are not yet supported
            res = PuppetParser.__process_codeelement(codeelement.name, path, code) + "("
            for arg in codeelement.arguments:
                res += repr(PuppetParser.__process_codeelement(arg, path, code)) + ","
            res = res[:-1]
            res += ")"
            lamb = PuppetParser.__process_codeelement(codeelement.lamb, path, code)
            if lamb != "": return [res] + lamb 
            else: return res
        elif (isinstance(codeelement, puppetmodel.If)):
            # FIXME Conditionals are not yet supported
            res = list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), 
                    codeelement.block))
            if (codeelement.elseblock is not None):
                res += PuppetParser.__process_codeelement(codeelement.elseblock, path, code)
            return res
        elif (isinstance(codeelement, puppetmodel.Unless)):
            # FIXME Conditionals are not yet supported
            res = list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), 
                    codeelement.block))
            if (codeelement.elseblock is not None):
                res += PuppetParser.__process_codeelement(codeelement.elseblock, path, code)
            return res
        elif (isinstance(codeelement, puppetmodel.Include)):
            dependencies = []
            for inc in codeelement.inc:
                d = Dependency(PuppetParser.__process_codeelement(inc, path, code))
                d.line, d.column = codeelement.line, codeelement.col
                d.code = get_code(codeelement)
                dependencies.append(d)
            return dependencies
        elif (isinstance(codeelement, puppetmodel.Require)):
            dependencies = []
            for req in codeelement.req:
                d = Dependency(PuppetParser.__process_codeelement(req, path, code))
                d.line, d.column = codeelement.line, codeelement.col
                d.code = get_code(codeelement)
                dependencies.append(d)
            return dependencies
        elif (isinstance(codeelement, puppetmodel.Contain)):
            dependencies = []
            for cont in codeelement.cont:
                d = Dependency(PuppetParser.__process_codeelement(cont, path, code))
                d.line, d.column = codeelement.line, codeelement.col
                d.code = get_code(codeelement)
                dependencies.append(d)
            return dependencies
        elif (isinstance(codeelement, (puppetmodel.Debug, puppetmodel.Fail, puppetmodel.Realize, puppetmodel.Tag))):
            # FIXME Ignored unsupported concepts
            pass
        elif (isinstance(codeelement, puppetmodel.Match)):
            # FIXME Matches are not yet supported
            return [list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.block))]
        elif (isinstance(codeelement, puppetmodel.Case)):
            control = PuppetParser.__process_codeelement(codeelement.control, path, code)
            conditions = []

            for match in codeelement.matches:
                expressions = PuppetParser.__process_codeelement(match.expressions, path, code)
                for expression in expressions:
                    if expression != "default":
                        condition = ConditionStatement(control + "==" + expression, 
                            ConditionStatement.ConditionType.SWITCH, False)
                        condition.line, condition.column = match.line, match.col
                        conditions.append(condition)
                    else:
                        condition = ConditionStatement("", 
                            ConditionStatement.ConditionType.SWITCH, True)
                        condition.line, condition.column = match.line, match.col
                        conditions.append(condition)

            for i in range(1, len(conditions)):
                conditions[i - 1].else_statement = conditions[i]

            conditions[0].repr_str = "case " + control
            conditions[0].code = get_code(codeelement)
            return [conditions[0]] + \
                list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.matches))
        elif (isinstance(codeelement, puppetmodel.Selector)):
            control = PuppetParser.__process_codeelement(codeelement.control, path, code)
            conditions = []
        
            for key, value in codeelement.hash.value.items():
                key = PuppetParser.__process_codeelement(key, path, code)
                value = PuppetParser.__process_codeelement(value, path, code)

                if key != "default":
                    condition = ConditionStatement(control + "==" + key, 
                        ConditionStatement.ConditionType.SWITCH, False)
                    condition.line, condition.column = codeelement.hash.line, codeelement.hash.col
                    conditions.append(condition)
                else:
                    condition = ConditionStatement("", 
                        ConditionStatement.ConditionType.SWITCH, True)
                    condition.line, condition.column = codeelement.hash.line, codeelement.hash.col
                    conditions.append(condition)
                condition.add_statement(PuppetParser.__process_codeelement(codeelement.hash, path, code))
            for i in range(1, len(conditions)):
                conditions[i - 1].else_statement = conditions[i]

            conditions[0].code = get_code(codeelement)
            conditions[0].repr_str = control + "?"\
                + repr(PuppetParser.__process_codeelement(codeelement.hash, path, code))

            return conditions[0]
        elif (isinstance(codeelement, puppetmodel.Reference)):
            res = codeelement.type + "["
            for r in codeelement.references:
                temp = PuppetParser.__process_codeelement(r, path, code)
                res += "" if temp is None else temp
            res += "]"
            return res
        elif (isinstance(codeelement, puppetmodel.Function)):
            # FIXME Functions definitions are not yet supported
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement.body))
        elif (isinstance(codeelement, puppetmodel.ResourceCollector)):
            res = codeelement.resource_type + "<|"
            res += PuppetParser.__process_codeelement(codeelement.search, path, code) + "|>"
            return res
        elif (isinstance(codeelement, puppetmodel.ResourceExpression)):
            resources = []
            resources.append(PuppetParser.__process_codeelement(codeelement.default, path, code))
            for resource in codeelement.resources:
                resources.append(PuppetParser.__process_codeelement(resource, path, code))
            return resources
        elif (isinstance(codeelement, puppetmodel.Chaining)):
            # FIXME Chaining not yet supported
            res = []
            op1 = PuppetParser.__process_codeelement(codeelement.op1, path, code)
            op2 = PuppetParser.__process_codeelement(codeelement.op2, path, code)
            if isinstance(op1, list): res += op1 
            else: res.append(op1)
            if isinstance(op2, list): res += op2
            else: res.append(op2)
            return res
        elif (isinstance(codeelement, list)):
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path, code), codeelement))
        elif codeelement is None:
            return ""
        else:
            return codeelement
        
    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                name_split = name.split('.')
                if len(name_split) == 2 and name_split[-1] == "pp":
                    res.add_block(self.parse_file(os.path.join(root, name), ""))

        return res

    def parse_file(self, path: str, type: UnitBlockType) -> UnitBlock:
        unit_block: UnitBlock = UnitBlock(os.path.basename(path), UnitBlockType.script)
        unit_block.path = path
        
        try:
            with open(path) as f:
                parsed_script, comments = parse_puppet(f.read())

                f.seek(0, 0)
                code = f.readlines()

                for c in comments:
                    comment = Comment(c.content)
                    comment.line = c.line
                    comment.code = ''.join(code[c.line - 1 : c.end_line])
                    unit_block.add_comment(comment)

                PuppetParser.__process_unitblock_component(
                    PuppetParser.__process_codeelement(parsed_script, path, code),
                    unit_block
                )
        except:
           throw_exception(EXCEPTIONS["PUPPET_COULD_NOT_PARSE"], path)

        return unit_block

    def parse_folder(self, path: str) -> Project:
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        if os.path.exists(f"{path}/modules") and not os.path.islink(f"{path}/modules"):
            subfolders = [f.path for f in os.scandir(f"{path}/modules") 
                if f.is_dir() and not f.is_symlink()]
            for m in subfolders:
                res.add_module(self.parse_module(m))

        for f in os.scandir(path):
            name_split = f.name.split('.')
            if f.is_file() and len(name_split) == 2 and name_split[-1] == "pp":
                res.add_block(self.parse_file(f.path, ""))

        subfolders = [f.path for f in os.scandir(f"{path}") 
            if f.is_dir() and not f.is_symlink()]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not \
                    in ["modules"]:
                aux = self.parse_folder(d)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res
