import thesis.parsers.parser as p
import ruamel.yaml as yaml
import os
from thesis.repr.inter import *

class AnsibleParser(p.Parser):
    def __extract_from_token(self, tl):
        assert isinstance(tl, list)
        res = []
        for t in tl:
            if t is None:
                continue
            if isinstance(t, list):
                res += self.__extract_from_token(t)
            else:
                res.append((t.start_mark.line, t.value))
        return res

    def __get_yaml_comments_aux(self, d):
        res = []

        if isinstance(d, dict):
            if d.ca.comment is not None:
                for l, c in self.__extract_from_token(d.ca.comment):
                    res.append((l, c))
            for key, val in d.items():
                for l, c in self.__get_yaml_comments_aux(val):
                    res.append((l, c))
                if key in d.ca.items:
                    for l, c in self.__extract_from_token(d.ca.items[key]):
                        res.append((l, c))
        elif isinstance(d, list):
            if d.ca.comment is not None:
                for l, c in self.__extract_from_token(d.ca.comment):
                    res.append((l, c))
            for idx, item in enumerate(d):
                for l, c in self.__get_yaml_comments_aux(item):
                    res.append((l, c))
                if idx in d.ca.items:
                    for l, c in self.__extract_from_token(d.ca.items[idx]):
                        res.append((l, c))

        return res

    def __get_yaml_comments(self, d):
        aux = self.__get_yaml_comments_aux(d)
        return list(filter(lambda c: "#" in c[1], \
            [(c[0] + 1, c[1].strip()) for c in aux]))

    def __parse_tasks(self, name, module, file):
        parsed_file = yaml.YAML().load(file)
        unit_block = UnitBlock(name)

        for task in parsed_file:
            if list(task.keys())[0] != "include":
                m: str = list(task.values())[1]
                atomic_unit = AtomicUnit(list(task.keys())[1])

                if (isinstance(m, str)):
                    atomic_unit.add_attribute(Attribute("", m))
                else:
                    for atr in m:
                        atomic_unit.add_attribute(Attribute(atr, m[atr]))
                unit_block.add_atomic_unit(atomic_unit)

        for comment in self.__get_yaml_comments(parsed_file):
           unit_block.add_comment(Comment(comment[1]))

        for task in parsed_file:
            if list(task.keys())[0] == "include":
                unit_block.add_dependency(list(task.values())[0])

        module.add_block(unit_block)

    def parse(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)))

        playbooks = [f for f in os.listdir(path + "/tasks") \
            if os.path.isfile(os.path.join(path + "/tasks", f))]
        for playbook in playbooks:
            with open(path + "/tasks/" + playbook) as file:
                self.__parse_tasks(playbook, res, file)

        return res
