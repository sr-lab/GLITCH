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
from glitch.parsers.ruby_parser import parser_yacc
from glitch.helpers import remove_unmatched_brackets

class AnsibleParser(p.Parser):
    def __get_yaml_comments(self, d, file):
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
    def __parse_vars(unit_block, cur_name, token):
        def create_variable(name, value):
            has_variable = ("{{" in value) and ("}}" in value)
            if (value in ["null", "~"]): value = ""
            v = Variable(name, value, has_variable)
            v.line = token.start_mark.line + 1
            unit_block.add_variable(v)
        
        if isinstance(token, MappingNode):
            for key, v in token.value:
                AnsibleParser.__parse_vars(unit_block, cur_name + key.value + ".", v)
        elif isinstance(token, SequenceNode):
            value = []
            for i, v in enumerate(token.value):
                if isinstance(v, CollectionNode):
                    AnsibleParser.__parse_vars(unit_block, f"{cur_name}[{i}].", v)
                else:
                    value.append(v.value)

            if (len(value) > 0):
                create_variable(cur_name, str(value))
        else:
            create_variable(cur_name[:-1], str(token.value))

    @staticmethod
    def __parse_attribute(cur_name, token, val):
        def create_attribute(token, name, value):
            has_variable = ("{{" in value) and ("}}" in value)
            if (value in ["null", "~"]): value = ""
            a = Attribute(name, value, has_variable)
            a.line = token.start_mark.line + 1
            attributes.append(a)

        attributes = []
        if isinstance(val, MappingNode):
            for aux, aux_val in val.value:
                attributes += AnsibleParser.__parse_attribute(f"{cur_name}.{aux.value}", 
                        aux, aux_val)
        elif isinstance(val, ScalarNode):
            create_attribute(token, cur_name, str(val.value))
        elif isinstance(val, SequenceNode):
            value = []
            for i, v in enumerate(val.value):
                if not isinstance(v, ScalarNode):
                    attributes += AnsibleParser.__parse_attribute(f"{cur_name}[{i}]", token, v)
                else:
                    value.append(v.value)

            if len(value) > 0:
                create_attribute(token, cur_name, str(value))
        return attributes

    @staticmethod
    def __parse_tasks(unit_block, tasks):
        for task in tasks.value:
            atomic_units, attributes = [], []
            type, line = "", 0
            is_block = False

            for key, val in task.value:
                # Dependencies
                if key.value == "include":
                    d = Dependency(val.value)
                    d.line = key.start_mark.line + 1
                    unit_block.add_dependency(d)
                    break
                if key.value in ["block", "always", "rescue"]:
                    is_block = True
                    size = len(unit_block.atomic_units)
                    AnsibleParser.__parse_tasks(unit_block, val)
                    created = len(unit_block.atomic_units) - size
                    atomic_units = unit_block.atomic_units[-created:]
                elif key.value != "name":
                    if type == "":
                        type = key.value
                        line = task.start_mark.line + 1

                    if (isinstance(val, MappingNode)):
                        for atr, atr_val in val.value:
                            if (atr.value == "name"):
                                names = [name.strip() for name in str(atr_val.value).split(',')]
                                for name in names:
                                    if name == "": continue
                                    atomic_units.append(AtomicUnit(name, type))
                            else:
                                attributes += AnsibleParser.__parse_attribute(atr.value, atr, atr_val)
                    else:
                        attributes += AnsibleParser.__parse_attribute(key.value, key, val)

            if is_block:
                for au in atomic_units:
                    au.attributes += attributes
                continue

            # If it was a task without a module we ignore it (e.g. dependency)
            for au in atomic_units:
                if au.type != "":
                    au.line = line
                    au.attributes = attributes.copy()
                    unit_block.add_atomic_unit(au)

            # Tasks without name
            if (len(atomic_units) == 0 and type != ""):
                au = AtomicUnit("", type)
                au.attributes = attributes
                au.line = line
                unit_block.add_atomic_unit(au)

    def __parse_playbook(self, name, file) -> UnitBlock:
        try:
            parsed_file = yaml.YAML().compose(file)
            unit_block = UnitBlock(name)
            unit_block.path = file.name

            for p in parsed_file.value:
                # Plays are unit blocks inside a unit block
                play = UnitBlock("")
                play.path = file.name

                for key, value in p.value:
                    if (key.value == "name" and play.name == ""):
                        play.name = value.value
                    elif (key.value == "vars"):
                        AnsibleParser.__parse_vars(play, "", value)
                    elif (key.value in ["tasks", "pre_tasks", "post_tasks", "handlers"]):
                        AnsibleParser.__parse_tasks(play, value)
                    else:
                        play.attributes += AnsibleParser.__parse_attribute(key.value, key, value)

                unit_block.add_unit_block(play)

            for comment in self.__get_yaml_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_PLAYBOOK"], file.name)
            return None

    def __parse_tasks_file(self, name, file) -> UnitBlock:
        try:
            parsed_file = yaml.YAML().compose(file)
            unit_block = UnitBlock(name)
            unit_block.path = file.name

            if parsed_file is None:
                return unit_block

            AnsibleParser.__parse_tasks(unit_block, parsed_file)
            for comment in self.__get_yaml_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
                unit_block.add_comment(c)

            return unit_block
        except:
            throw_exception(EXCEPTIONS["ANSIBLE_TASKS_FILE"], file.name)
            return None

    def __parse_vars_file(self, name, file) -> UnitBlock:
        try:
            parsed_file = yaml.YAML().compose(file)
            unit_block = UnitBlock(name)
            unit_block.path = file.name

            if parsed_file is None:
                return unit_block

            AnsibleParser.__parse_vars(unit_block, "", parsed_file)
            for comment in self.__get_yaml_comments(parsed_file, file):
                c = Comment(comment[1])
                c.line = comment[0]
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
        res: Module = Module(os.path.basename(os.path.normpath(path)))
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

    def parse_file(self, path: str, type: str) -> UnitBlock:
        with open(path) as f:
            if (type == "script"):
                return self.__parse_playbook(path, f)
            elif (type == "tasks"):
                return self.__parse_tasks_file(path, f)
            elif (type == "vars"):
                return self.__parse_vars_file(path, f)

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
            return ChefParser._check_has_variable(ast.args[0])
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
            res += "end"

        res = res.strip()
        if res.startswith(('"', "'")) and res.endswith(('"', "'")):
            res = res[1:-1]
        
        return remove_unmatched_brackets(res)

    class Checker:
        tests_ast_stack: list
        source: list

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
        atomic_unit: AtomicUnit

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
                                        "include_recipe",
                                        "deprecated_property_alias"]):
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
                                    ChefParser._check_id(ast.args[1], ["brace_block"]))):
                has_variable = ChefParser._check_has_variable(ast.args[1])
                a = Attribute(ChefParser._get_content(ast.args[0], self.source),
                        ChefParser._get_content(ast.args[1], self.source), has_variable)
                a.line = ChefParser._get_content_bounds(ast, self.source)[0]
                self.atomic_unit.add_attribute(a)
            elif isinstance(ast, (ChefParser.Node, list)):
                for arg in reversed(ast):
                    self.push([self.is_attribute], arg)

            return True

    class VariableChecker(Checker):
        variables: list[Variable]

        def __init__(self, source, ast):
            super().__init__(source)
            self.variables = []
            self.push([self.is_variable], ast)

        def is_variable(self, ast):
            def parse_variable(key, current_name, ast):
                if ChefParser._check_node(ast, ["hash"], 1) \
                    and ChefParser._check_id(ast.args[0], ["assoclist_from_args"]):
                        for assoc in ast.args[0].args[0]:
                            parse_variable(assoc.args[0], current_name + "." +
                                ChefParser._get_content(assoc.args[0], self.source), 
                                    assoc.args[1])
                else:
                    value = ChefParser._get_content(ast, self.source)
                    has_variable = ChefParser._check_has_variable(ast)
                    variable = Variable(current_name, value, has_variable)
                    variable.line = ChefParser._get_content_bounds(key, self.source)[0]
                    self.variables.append(variable)

            if ChefParser._check_node(ast, ["assign"], 2):
                name = ChefParser._get_content(ast.args[0], self.source)
                parse_variable(ast.args[0], name, ast.args[1])
                return True

            return False

    class IncludeChecker(Checker):
        include: Dependency

        def __init__(self, source, ast):
            super().__init__(source)
            self.push([self.is_include], ast)

        def is_include(self, ast):
            if (ChefParser._check_node(ast, ["command"], 2) 
                    and ChefParser._check_id(ast.args[0], ["@ident"])
                        and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)):
                self.push([self.is_include_name], ast.args[1])
                self.push([self.is_include_type], ast.args[0])
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
                self.include = d
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

            for arg in ast.args:
                if isinstance(arg, (ChefParser.Node, list)):
                    ChefParser.__transverse_ast(arg, unit_block, source)

    @staticmethod
    def __parse_recipe(path, file) -> UnitBlock:
        with open(path + file) as f:
            ripper = resource_filename("thesis.parsers", 'resources/comments.rb.template')
            ripper = open(ripper, "r")
            ripper_script = Template(ripper.read())
            ripper.close()
            ripper_script = ripper_script.substitute({'path': '\"' + path + file + '\"'})

            unit_block: UnitBlock = UnitBlock(file)
            unit_block.path = path + file
            source = f.readlines()

            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                tmp.write(ripper_script)
                tmp.flush()

                try:
                    script_ast = os.popen('ruby ' + tmp.name).read()
                    comments, _ = parser_yacc(script_ast)
                    if comments is not None: comments.reverse()

                    for comment, line in comments:
                        c = Comment(re.sub(r'\\n$', '', comment))
                        c.line = line
                        unit_block.add_comment(c)
                except:
                    throw_exception(EXCEPTIONS["CHEF_COULD_NOT_PARSE"], path + file)

            try:
                script_ast = os.popen('ruby -r ripper -e \'file = \
                    File.open(\"' + path + file + '\")\npp Ripper.sexp(file)\'').read()
                _, program = parser_yacc(script_ast)
                ast = ChefParser.__create_ast(program)
                ChefParser.__transverse_ast(ast, unit_block, source)
            except:
                throw_exception(EXCEPTIONS["CHEF_COULD_NOT_PARSE"], path + file)

            return unit_block

    def parse_module(self, path: str) -> Module:
        def parse_folder(path: str):
            if os.path.exists(path):
                files = [f for f in os.listdir(path) \
                    if os.path.isfile(os.path.join(path, f))]
                for file in files:
                    res.add_block(self.__parse_recipe(path, file))

        res: Module = Module(os.path.basename(os.path.normpath(path)))
        super().parse_file_structure(res.folder, path)

        parse_folder(path + "/resources/")
        parse_folder(path + "/recipes/")
        parse_folder(path + "/attributes/")
        parse_folder(path + "/definitions/")
        parse_folder(path + "/libraries/")
        parse_folder(path + "/providers/")

        return res

    def parse_file(self, path: str, type: str) -> UnitBlock:
        return self.__parse_recipe(os.path.dirname(path) + "/", os.path.basename(path))

    def parse_folder(self, path: str) -> Project:
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        res.add_module(self.parse_module(path))

        if (os.path.exists(f"{path}/cookbooks")):
            cookbooks = [f.path for f in os.scandir(f"{path}/cookbooks") 
                if f.is_dir() and not f.is_symlink()]
            for cookbook in cookbooks:
                res.add_module(self.parse_module(cookbook))

        return res

class PuppetParser(p.Parser):
    @staticmethod
    def __process_unitblock_component(ce, unit_block: UnitBlock):
        if isinstance(ce, Dependency):
            unit_block.add_dependency(ce)
        elif isinstance(ce, Variable):
            unit_block.add_dependency(ce)
        elif isinstance(ce, AtomicUnit):
            unit_block.add_atomic_unit(ce)
        elif isinstance(ce, UnitBlock):
            unit_block.add_unit_block(ce)
        elif isinstance(ce, Attribute):
            unit_block.add_unit_block(ce)
        elif isinstance(ce, list):
            for c in ce:
                PuppetParser.__process_unitblock_component(c, unit_block)

    @staticmethod
    def __process_codeelement(codeelement, path):
        if (isinstance(codeelement, puppetmodel.Value)):
            return str(codeelement.value)
        elif (isinstance(codeelement, puppetmodel.Attribute)):
            name = PuppetParser.__process_codeelement(codeelement.key, path)
            temp_value = PuppetParser.__process_codeelement(codeelement.value, path)
            value = "" if temp_value is None else temp_value
            has_variable = value.startswith("$")
            attribute = Attribute(name, value, has_variable)
            attribute.line, attribute.column = codeelement.line, codeelement.col
            return attribute
        elif (isinstance(codeelement, puppetmodel.Resource)):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_codeelement(codeelement.title, path), 
                PuppetParser.__process_codeelement(codeelement.type, path)
            )
            for attr in codeelement.attributes:
                resource.add_attribute(PuppetParser.__process_codeelement(attr, path))
            resource.line, resource.column = codeelement.line, codeelement.col
            return resource 
        elif (isinstance(codeelement, puppetmodel.ResourceDeclaration)):
            # FIXME Resource Declarations are not yet supported
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.block))
        elif (isinstance(codeelement, puppetmodel.Parameter)):
            # FIXME Parameters are not yet supported
            variable = Variable(
                PuppetParser.__process_codeelement(codeelement.name, path),
                PuppetParser.__process_codeelement(codeelement.default, path), 
                False
            )
            variable.line, variable.column = codeelement.line, codeelement.col
            return variable 
        elif (isinstance(codeelement, puppetmodel.Assignment)):
            name = PuppetParser.__process_codeelement(codeelement.name, path)
            temp_value = PuppetParser.__process_codeelement(codeelement.value, path)
            value = "" if temp_value is None else temp_value
            has_variable = value.startswith("$")
            variable: Variable = Variable(name, value, has_variable)
            variable.line, variable.column = codeelement.line, codeelement.col
            return variable
        elif (isinstance(codeelement, puppetmodel.PuppetClass)):
            # FIXME there are components of the class that are not considered
            unit_block: UnitBlock = UnitBlock(
                PuppetParser.__process_codeelement(codeelement.name, path)
            )
            unit_block.path = path

            if (codeelement.block is not None):
                for ce in list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.block)):
                    PuppetParser.__process_unitblock_component(ce, unit_block)

            for p in codeelement.parameters:
                unit_block.add_variable(PuppetParser.__process_codeelement(p, path))

            unit_block.line, unit_block.column = codeelement.line, codeelement.col
            return unit_block
        elif (isinstance(codeelement, puppetmodel.Node)):
            # FIXME Nodes are not yet supported
            if (codeelement.block is not None):
                return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.block))
            else:
                return []
        elif (isinstance(codeelement, puppetmodel.Operation)):
            if len(codeelement.arguments) == 1:
                return codeelement.operator + \
                    PuppetParser.__process_codeelement(codeelement.arguments[0], path)
            elif codeelement.operator == "[]":
                return \
                    (PuppetParser.__process_codeelement(codeelement.arguments[0], path)
                        + "[" + 
                    ','.join(PuppetParser.__process_codeelement(codeelement.arguments[1], path))
                        + "]")
            elif len(codeelement.arguments) == 2:
                return \
                    (PuppetParser.__process_codeelement(codeelement.arguments[0], path)
                        + codeelement.operator + 
                    PuppetParser.__process_codeelement(codeelement.arguments[1], path))
            elif codeelement.operator == "[,]":
                return \
                    (PuppetParser.__process_codeelement(codeelement.arguments[0], path)
                        + "[" +
                    PuppetParser.__process_codeelement(codeelement.arguments[1], path)
                        + "," + 
                    PuppetParser.__process_codeelement(codeelement.arguments[2], path)
                        + "]")
        elif (isinstance(codeelement, puppetmodel.Lambda)):
            # FIXME Lambdas are not yet supported
            if (codeelement.block is not None):
                return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.block))
            else:
                return []
        elif (isinstance(codeelement, puppetmodel.FunctionCall)):
            # FIXME Function calls are not yet supported
            res = PuppetParser.__process_codeelement(codeelement.name, path)
            for arg in codeelement.arguments:
                res += PuppetParser.__process_codeelement(arg, path)
            PuppetParser.__process_codeelement(codeelement.lamb, path) #FIXME
            return res
        elif (isinstance(codeelement, puppetmodel.If)):
            # FIXME Conditionals are not yet supported
            res = list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), 
                    codeelement.block))
            if (codeelement.elseblock is not None):
                res += PuppetParser.__process_codeelement(codeelement.elseblock, path)
            return res
        elif (isinstance(codeelement, puppetmodel.Unless)):
            # FIXME Conditionals are not yet supported
            res = list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), 
                    codeelement.block))
            if (codeelement.elseblock is not None):
                res += PuppetParser.__process_codeelement(codeelement.elseblock, path)
            return res
        elif (isinstance(codeelement, puppetmodel.Include)):
            dependencies = []
            for inc in codeelement.inc:
                d = Dependency(PuppetParser.__process_codeelement(inc, path))
                d.line, d.column = codeelement.line, codeelement.col
                dependencies.append(d)
            return dependencies
        elif (isinstance(codeelement, puppetmodel.Require)):
            dependencies = []
            for req in codeelement.req:
                d = Dependency(PuppetParser.__process_codeelement(req, path))
                d.line, d.column = codeelement.line, codeelement.col
                dependencies.append(d)
            return dependencies
        elif (isinstance(codeelement, puppetmodel.Contain)):
            dependencies = []
            for cont in codeelement.cont:
                d = Dependency(PuppetParser.__process_codeelement(cont, path))
                d.line, d.column = codeelement.line, codeelement.col
                dependencies.append(d)
            return dependencies
        elif (isinstance(codeelement, (puppetmodel.Debug, puppetmodel.Fail, puppetmodel.Realize, puppetmodel.Tag))):
            # FIXME Ignored unsupported concepts
            pass
        elif (isinstance(codeelement, puppetmodel.Match)):
            # FIXME Matches are not yet supported
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.block))
        elif (isinstance(codeelement, puppetmodel.Case)):
            # FIXME Conditionals are not yet supported
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.matches))
        elif (isinstance(codeelement, puppetmodel.Selector)):
            # FIXME Conditionals are not yet supported
            return PuppetParser.__process_codeelement(codeelement.control, path) + "?"\
                    + PuppetParser.__process_codeelement(codeelement.hash, path)
        elif (isinstance(codeelement, puppetmodel.Reference)):
            res = codeelement.type + "["
            for r in codeelement.references:
                temp = PuppetParser.__process_codeelement(r, path)
                res += "" if temp is None else temp
            res += "]"
            return res
        elif (isinstance(codeelement, puppetmodel.Function)):
            # FIXME Functions definitions are not yet supported
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement.body))
        elif (isinstance(codeelement, puppetmodel.ResourceCollector)):
            res = codeelement.resource_type + "<|"
            res += PuppetParser.__process_codeelement(codeelement.search, path) + "|>"
            return res
        elif (isinstance(codeelement, puppetmodel.ResourceExpression)):
            resources = []
            resources.append(PuppetParser.__process_codeelement(codeelement.default, path))
            for resource in codeelement.resources:
                resources.append(PuppetParser.__process_codeelement(resource, path))
            return resources
        elif (isinstance(codeelement, puppetmodel.Chaining)):
            # FIXME Chaining not yet supported
            res = []
            op1 = PuppetParser.__process_codeelement(codeelement.op1, path)
            op2 = PuppetParser.__process_codeelement(codeelement.op2, path)
            if isinstance(op1, list): res += op1 
            else: res.append(op1)
            if isinstance(op2, list): res += op2
            else: res.append(op2)
        elif (isinstance(codeelement, list)):
            return list(map(lambda ce: PuppetParser.__process_codeelement(ce, path), codeelement))
        elif (codeelement is None):
            return ""
        else:
            return codeelement
        
    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)))
        super().parse_file_structure(res.folder, path)

        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                name_split = name.split('.')
                if len(name_split) == 2 and name_split[-1].endswith('.pp'):
                    res.add_block(self.parse_file(os.path.join(root, name), ""))

        return res

    def parse_file(self, path: str, type: str) -> UnitBlock:
        unit_block: UnitBlock = UnitBlock(os.path.basename(path))
        unit_block.path = path
        
        try:
            with open(path) as f:
                parsed_script, comments = parse_puppet(f.read())
                for c in comments:
                    comment = Comment(c.content)
                    comment.line = c.line
                    unit_block.add_comment(comment)

                PuppetParser.__process_unitblock_component(
                    PuppetParser.__process_codeelement(parsed_script, path),
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
            if f.is_file() and len(name_split) == 2 and name_split[-1].endswith('.pp'):
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
