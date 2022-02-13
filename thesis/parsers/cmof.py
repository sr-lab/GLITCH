import thesis.parsers.parser as p
import ruamel.yaml as yaml
from thesis.repr.inter import *

class AnsibleParser(p.Parser):
    def __extract_from_token(self, tl):
        assert isinstance(tl, list)
        res = []
        for t in tl:
            if t is None:
                continue
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

    def parse(self, path: str) -> Module:
        res: Module = Module("tst") #FIXME

        with open(path) as file:
            parsed_file = yaml.YAML().load(file)[0]
            unit_block = UnitBlock(parsed_file["name"])

            for task in parsed_file['tasks']:
                module: str = list(filter(lambda n: n != "name", task.keys()))[0]
                atomic_unit = AtomicUnit(module)
                for attribute in task[module].keys():
                    atomic_unit.add_attribute(Attribute(attribute, str(task[module][attribute])))
                unit_block.add_atomic_unit(atomic_unit)

            for comment in self.__get_yaml_comments(parsed_file):
                unit_block.add_comment(Comment(comment[1]))

            res.add_block(unit_block)

        return res
