import os
import re
import tempfile
from string import Template
import ruamel.yaml as yaml
from pkg_resources import resource_filename

import thesis.parsers.parser as p
from thesis.repr.inter import *
from thesis.parsers.ruby_parser import parser_yacc
from thesis.helpers import remove_unmatched_brackets

class AnsibleParser(p.Parser):
    def __get_yaml_comments(self, d):
        def extract_from_token(tokenlist):
            res = []
            for token in tokenlist:
                if token is None:
                    continue
                if isinstance(token, list):
                    res += extract_from_token(token)
                else:
                    res.append((token.start_mark.line, token.value))
            return res

        def yaml_comments(d):
            res = []

            if isinstance(d, dict):
                if d.ca.comment is not None:
                    for line, comment in extract_from_token(d.ca.comment):
                        res.append((line, comment))
                for key, val in d.items():
                    for line, comment in yaml_comments(val):
                        res.append((line, comment))
                    if key in d.ca.items:
                        for line, comment in extract_from_token(d.ca.items[key]):
                            res.append((line, comment))
            elif isinstance(d, list):
                if d.ca.comment is not None:
                    for line, comment in extract_from_token(d.ca.comment):
                        res.append((line, comment))
                for idx, item in enumerate(d):
                    for line, comment in yaml_comments(item):
                        res.append((line, comment))
                    if idx in d.ca.items:
                        for line, comment in extract_from_token(d.ca.items[idx]):
                            res.append((line, comment))

            return res

        return list(filter(lambda c: "#" in c[1], \
            [(c[0] + 1, c[1].strip()) for c in yaml_comments(d)]))

    def __parse_playbook(self, module, name, file):
        parsed_file = yaml.YAML().load(file)
        unit_block = UnitBlock(name)

        if parsed_file is None:
            module.add_block(unit_block)
            return

        for task in parsed_file:
            atomic_units = []
            attributes = []
            type = ""

            for key, val in task.items():
                # Dependencies
                if key == "include":
                    unit_block.add_dependency(val)
                    break

                if key != "name":
                    if type == "":
                        type = key

                    if isinstance(val, (list, str)):
                        attributes.append(Attribute(key, str(val)))
                    else:
                        for atr in val:
                            if (atr == "name"):
                                names = [name.strip() for name in str(val[atr]).split(',')]
                                for name in names:
                                    if name == "": continue
                                    atomic_units.append(AtomicUnit(name, type))
                            else:
                                attributes.append(Attribute(atr, str(val[atr])))

            # If it was a task without a module we ignore it (e.g. dependency)
            for au in atomic_units:
                if au.type != "":
                    au.attributes = attributes.copy()
                    unit_block.add_atomic_unit(au)

            # Tasks without name
            if (len(atomic_units) == 0 and type != ""):
                au = AtomicUnit("", type)
                au.attributes = attributes
                unit_block.add_atomic_unit(au)

        for comment in self.__get_yaml_comments(parsed_file):
            unit_block.add_comment(Comment(comment[1]))

        module.add_block(unit_block)

    def __parse_vars(self, module, name, file):
        def parse_var(cur_name, vmap):
            for key, val in vmap.items():
                if isinstance(val, dict):
                    parse_var(cur_name + key + ".", val)
                else:
                    unit_block.add_variable(Variable(cur_name + key, str(val)))

        parsed_file = yaml.YAML().load(file)
        unit_block = UnitBlock(name)

        if parsed_file is None:
            module.add_block(unit_block)
            return

        parse_var("", parsed_file)
        module.add_block(unit_block)

    def parse_module(self, path: str) -> Module:
        def parse_folder(folder, p_function):
            files = [f for f in os.listdir(path + folder) \
                if os.path.isfile(os.path.join(path + folder, f))]
            for file in files:
                with open(path + folder + file) as f:
                    p_function(res, folder + file, f)

        res: Module = Module(os.path.basename(os.path.normpath(path)))
        super().parse_file_structure(res.folder, path)

        parse_folder("/tasks/", self.__parse_playbook)
        parse_folder("/handlers/", self.__parse_playbook)
        parse_folder("/vars/", self.__parse_vars)
        parse_folder("/defaults/", self.__parse_vars)

        return res

    def parse_folder(self, path: str) -> Module:
        res: Module = Module("")

        files = []
        for (dirpath, _, filenames) in os.walk(path):
            filenames = filter(lambda f: f.endswith('.yml'), filenames)
            files += [os.path.join(dirpath, file) for file in filenames]

        for file in files:
            with open(file) as f:
                self.__parse_playbook(res, file, f)

        return res
        

    def parse_file(self, path: str) -> Module:
        res: Module = Module("")
        with open(path) as f:
            self.__parse_playbook(res, path, f)

        return res

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
    def __get_content_bounds(ast, source):
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
                bound = ChefParser.__get_content_bounds(arg, source)
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
            'string_literal': "''",
            'hash': "{}",
            'array': "[]"
        }

        if ((ast.id in empty_structures and len(ast.args) == 0) or
                (ast.id == 'string_literal' and len(ast.args[0].args) == 0)):
            return empty_structures[ast.id]

        bounds = ChefParser.__get_content_bounds(ast, source)

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

        return remove_unmatched_brackets(res.strip())

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
                return True
            return False

        def is_inline_resource(self, ast):
            if (ChefParser._check_node(ast, ["command"], 2) and
                ChefParser._check_id(ast.args[0], ["@ident"])
                    and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)):
                self.push([self.is_resource_body_without_attributes,
                    self.is_inline_resource_name], ast.args[1])
                self.push([self.is_resource_type], ast.args[0])
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
                self.atomic_unit.add_attribute(
                    Attribute(ChefParser._get_content(ast.args[0], self.source),
                        ChefParser._get_content(ast.args[1], self.source)))
            elif isinstance(ast, (ChefParser.Node, list)):
                for arg in reversed(ast):
                    self.push([self.is_attribute], arg)

            return True

    class VariableChecker(Checker):
        variable: Variable

        def __init__(self, source, ast):
            super().__init__(source)
            self.variable = Variable("", "")
            self.push([self.is_variable], ast)

        def is_variable(self, ast):
            if ChefParser._check_node(ast, ["assign"], 2):
                self.variable.name = ChefParser._get_content(ast.args[0], self.source)
                self.variable.value = ChefParser._get_content(ast.args[1], self.source)
                return True
            return False

    class IncludeChecker(Checker):
        include: str

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
                self.include = ChefParser._get_content(ast.args[0][0], self.source)
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
                unit_block.add_variable(variable_checker.variable)
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
    def __parse_recipe(path, file, module):
        with open(path + file) as f:
            ripper = resource_filename("thesis.parsers", 'resources/comments.rb.template')
            ripper = open(ripper, "r")
            ripper_script = Template(ripper.read())
            ripper.close()
            ripper_script = ripper_script.substitute({'path': '\"' + path + file + '\"'})

            unit_block: UnitBlock = UnitBlock(file)
            source = f.readlines()

            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                tmp.write(ripper_script)
                tmp.flush()

                script_ast = os.popen('ruby ' + tmp.name).read()
                comments, _ = parser_yacc(script_ast)

                for comment in comments:
                    unit_block.add_comment(Comment(re.sub(r'\\n$', '', comment)))

            script_ast = os.popen('ruby -r ripper -e \'file = \
                File.open(\"' + path + file + '\")\npp Ripper.sexp(file)\'').read()
            _, program = parser_yacc(script_ast)
            
            ast = ChefParser.__create_ast(program)
            ChefParser.__transverse_ast(ast, unit_block, source)
            module.add_block(unit_block)

    def parse_module(self, path: str) -> Module:
        def parse_folder(path: str):
            if os.path.exists(path):
                files = [f for f in os.listdir(path) \
                    if os.path.isfile(os.path.join(path, f))]
                for file in files:
                    self.__parse_recipe(path, file, res)

        res: Module = Module(os.path.basename(os.path.normpath(path)))
        super().parse_file_structure(res.folder, path)

        parse_folder(path + "/resources/")
        parse_folder(path + "/recipes/")
        parse_folder(path + "/attributes/")
        parse_folder(path + "/definitions/")
        parse_folder(path + "/libraries/")
        parse_folder(path + "/providers/")

        return res

    def parse_file(self, path: str) -> Module:
        res: Module = Module("")
        self.__parse_recipe(os.path.dirname(path) + "/", os.path.basename(path), res)
        return res

    def parse_folder(self, path: str) -> Module:
        res: Module = Module("")

        files = []
        for (dirpath, _, filenames) in os.walk(path):
            filenames = filter(lambda f: f.endswith('.rb'), filenames)
            files += [os.path.join(dirpath, file) for file in filenames]

        for file in files:
            self.__parse_recipe(os.path.dirname(file) + "/", os.path.basename(file), res)

        return res
