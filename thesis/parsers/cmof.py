import thesis.parsers.parser as p
import ruamel.yaml as yaml
import os
from thesis.repr.inter import *
from thesis.parsers.ruby_parser import parser_yacc

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

    def __parse_tasks(self, module, name, file):
        parsed_file = yaml.YAML().load(file)
        unit_block = UnitBlock(name)

        if (parsed_file == None):
            module.add_block(unit_block)
            return

        for task in parsed_file:
            atomic_unit = AtomicUnit("", "") #FIXME type

            for key, val in task.items():
                # Dependencies
                if key == "include":
                    unit_block.add_dependency(val)
                    break

                if key != "name":
                    if atomic_unit.name == "":
                        atomic_unit.name = key

                    if (isinstance(val, str) or isinstance(val, list)):
                        atomic_unit.add_attribute(Attribute(key, str(val)))
                    else:
                        for atr in val:
                            atomic_unit.add_attribute(Attribute(atr, str(val[atr])))

            # If it was a task without a module we ignore it (e.g. dependency)
            if atomic_unit.name != "":
                unit_block.add_atomic_unit(atomic_unit)

        for comment in self.__get_yaml_comments(parsed_file):
           unit_block.add_comment(Comment(comment[1]))

        module.add_block(unit_block)

    def __parse_vars(self, module, name, file):
        def parse_var(cur_name, map):
            for key, val in map.items():
                if isinstance(val, dict):
                    parse_var(cur_name + key + ".", val)
                else:
                    unit_block.add_variable(Variable(cur_name + key, str(val)))

        parsed_file = yaml.YAML().load(file)
        unit_block = UnitBlock(name)

        if (parsed_file == None):
            module.add_block(unit_block)
            return

        parse_var("", parsed_file)
        module.add_block(unit_block)

    def __parse_file_structure(self, folder, path):
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                folder.add_file(File(f))
            elif os.path.isdir(os.path.join(path, f)):
                new_folder = Folder(f)
                self.__parse_file_structure(new_folder, os.path.join(path, f))
                folder.add_folder(new_folder)

    def parse(self, path: str) -> Module:
        def parse_folder(folder, p_function):
            files = [f for f in os.listdir(path + folder) \
                if os.path.isfile(os.path.join(path + folder, f))]
            for file in files:
                with open(path + folder + file) as f:
                    p_function(res, folder + file, f)

        res: Module = Module(os.path.basename(os.path.normpath(path)))
        self.__parse_file_structure(res.folder, path)

        parse_folder("/tasks/", self.__parse_tasks)
        parse_folder("/handlers/", self.__parse_tasks)
        parse_folder("/vars/", self.__parse_vars)
        parse_folder("/defaults/", self.__parse_vars)

        return res

class ChefParser(p.Parser):
    def parse(self, path: str) -> Module:
        class Node:
            id: str
            args: list

            def __init__(self, id, args) -> None:
                self.id = id
                self.args = args

            def __repr__(self) -> str:
                return str(self.id)

        def create_ast(l):
            args = []
            for el in l[1:]:
                if isinstance(el, list): 
                    if len(el) > 0 and isinstance(el[0], tuple) and el[0][0] == "id": #FIXME
                        args.append(create_ast(el))
                    else:
                        arg = []
                        for e in el:
                            if isinstance(e, list) and isinstance(e[0], tuple) and e[0][0] == "id":
                                arg.append(create_ast(e))
                            else:
                                arg.append(e)
                        args.append(arg)
                else:
                    args.append(el)

            return Node(l[0][1], args)

        def get_content_bounds(ast):
            start_line = float('inf')
            start_column = float('inf')
            end_line = 0
            end_column = 0

            if (isinstance(ast, list)):
                for arg in ast:
                    bound = get_content_bounds(arg)
                    if bound[0] < start_line:
                        start_line = bound[0]
                    if bound[1] < start_column:
                        start_column = bound[1]
                    if bound[2] > end_line:
                        end_line = bound[2]
                    if bound[3] > end_column:
                        end_column = bound[3]
            elif (isinstance(ast, Node) and isinstance(ast.args[-1], list) and 
                len(ast.args[-1]) == 2 and isinstance(ast.args[-1][0], int)
                    and isinstance(ast.args[-1][1], int)):
                start_line = ast.args[-1][0]
                start_column = ast.args[-1][1]
                end_line = ast.args[-1][0]
                end_column = ast.args[-1][1] + len(ast.args[-2])
            elif isinstance(ast, Node):
                for arg in ast.args:
                    bound = get_content_bounds(arg)
                    if bound[0] < start_line:
                        start_line = bound[0]
                    if bound[1] < start_column:
                        start_column = bound[1]
                    if bound[2] > end_line:
                        end_line = bound[2]
                    if bound[3] > end_column:
                        end_column = bound[3]

                if (ast.id == "string_literal" or ast.id == "string_embexpr" or ast.id == "brace_block" or ast.id == "arg_paren"):
                    end_column += 1
                elif (ast.id == "top_const_ref"):
                    start_column -= 1

            return (start_line, start_column, end_line, end_column)

        def get_content(ast):
            bounds = get_content_bounds(ast)

            res = ""
            if (bounds[0] == float('inf')):
                return res

            for l in range(bounds[0] - 1, bounds[2]):
                if (bounds[0] - 1 == bounds[2] - 1):
                    res += lines[l][bounds[1] - 1:bounds[3]]
                elif (l == bounds[2] - 1):
                    res += lines[l][:bounds[3]]
                elif (l == bounds[0] - 1):
                    res += lines[l][bounds[1] - 1:]
                else:
                    res += lines[l]

            return res.strip()

        def parse_resource(ast):
            def parse_attributes(ast):
                if (isinstance(ast, Node) and (ast.id == "command" or ast.id == "method_add_arg")):
                    atomic_unit.add_attribute(Attribute(get_content(ast.args[0]),
                        get_content(ast.args[1])))
                elif (isinstance(ast, Node) and ast.id == "method_add_block" and ast.args[0].id 
                    == "method_add_arg" and ast.args[1].id == "brace_block"):
                    atomic_unit.add_attribute(Attribute(get_content(ast.args[0]),
                        get_content(ast.args[1])))
                elif isinstance(ast, Node):
                    for arg in ast.args:
                        parse_attributes(arg)
                elif isinstance(ast, list):
                    for arg in ast:
                        parse_attributes(arg)
                

            atomic_unit = AtomicUnit("", "")
            if (isinstance(ast, Node) and ast.id == "method_add_block" and len(ast.args) == 2 
                and isinstance(ast.args[0], Node) and ast.args[0].id == "command"
                    and isinstance(ast.args[0], Node) and ast.args[1].id == "do_block"):
                command = ast.args[0]
                do_block = ast.args[1]

                if (len(command.args) == 2 
                    and isinstance(command.args[0], Node) and command.args[0].id == "@ident" 
                    and len(command.args[0].args) == 2
                        and isinstance(command.args[1], Node) and command.args[1].id == "args_add_block" 
                        and len(command.args[1].args) == 2):
                    ident = command.args[0]
                    add_block = command.args[1]

                    if (isinstance(ident.args[0], str) and isinstance(ident.args[1], list)):
                        atomic_unit.type = ident.args[0]
                    else:
                        return (False, atomic_unit)

                    if (len(add_block.args) == 2 and isinstance(add_block.args[0][0], Node) and add_block.args[1] == False
                        and atomic_unit.type != "action"):
                        resource_id = add_block.args[0][0]
                        atomic_unit.name = get_content(resource_id)
                    else:
                        return (False, atomic_unit)
                else:
                    return (False, atomic_unit)

                if (len(do_block.args) == 1 
                    and isinstance(do_block.args[0], Node) and do_block.args[0].id == "bodystmt"):
                    parse_attributes(do_block.args[0].args[0])
                else:
                    return (False, atomic_unit)
            else:
                return (False, atomic_unit)

            return (True, atomic_unit)

        def get_resources(ast):
            if (isinstance(ast, list)):
                for arg in ast:
                    if (isinstance(arg, Node) or isinstance(arg, list)):
                        get_resources(arg)
            else:
                is_resource, resource = parse_resource(ast)
                if (is_resource):
                    unit_block.add_atomic_unit(resource)
                else:
                    for arg in ast.args:
                        if (isinstance(arg, Node) or isinstance(arg, list)):
                            get_resources(arg)

        script_ast = os.popen('ruby -r ripper -e \'file = \
            File.open(\"' + path + '\")\npp Ripper.sexp(file)\'').read()

        f = open(path, "r")
        lines = f.readlines()

        res: Module = Module("Test")
        unit_block: UnitBlock = UnitBlock("Test")

        get_resources(create_ast(parser_yacc(script_ast)))
        res.add_block(unit_block)

        return res

        