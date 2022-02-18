import thesis.parsers.parser as p
import ruamel.yaml as yaml
import os
from thesis.repr.inter import *

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
            atomic_unit = AtomicUnit("")

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
        pass
