import json
import jsonschema

from glitch.parsers.yaml import YamlParser
from typing import Optional
from glitch.repr.inter import *
from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import (
    Node,
    MappingNode,
)
from pkg_resources import resource_filename
from glitch.exceptions import EXCEPTIONS, throw_exception


class GithubActionsParser(YamlParser):
    def __init__(self):
        super().__init__({"variable_start_string": "${{"})

    def __parse_dict(self, node: Node) -> Dict[str, Node]:
        result: Dict[str, Node] = {}
        if isinstance(node, MappingNode):
            for key, value in node.value:
                result[key.value] = value
        return result

    def __parse_variable(self, key: Node, value: Node, lines: List[str]) -> Variable:
        var_value = self.get_value(value, lines)

        name = self._get_code(key, key, lines)
        code = self._get_code(key, value, lines)

        var = Variable(
            name,
            var_value,
            ElementInfo(
                key.start_mark.line + 1,
                key.start_mark.column + 1,
                value.end_mark.line + 1,
                value.end_mark.column + 1,
                code,
            ),
        )

        return var

    def __parse_attribute(self, key: Node, value: Node, lines: List[str]) -> Attribute:
        attr_value = self.get_value(value, lines)
        name = self._get_code(key, key, lines)
        code = self._get_code(key, value, lines)

        attr = Attribute(
            name,
            attr_value,
            ElementInfo(
                key.start_mark.line + 1,
                key.start_mark.column + 1,
                value.end_mark.line + 1,
                value.end_mark.column + 1,
                code,
            ),
        )

        return attr

    def __parse_job(self, key: Node, value: Node, lines: List[str]) -> UnitBlock:
        job = UnitBlock(key.value, UnitBlockType.block)
        job.line, job.column = key.start_mark.line + 1, key.start_mark.column + 1
        job.code = self._get_code(key, value, lines)

        for attr_key, attr_value in value.value:
            if attr_key.value == "steps":
                for step in attr_value.value:
                    step_dict: Dict[str, Node] = self.__parse_dict(step)
                    name = (
                        Null()
                        if "name" not in step_dict
                        else self.get_value(step_dict["name"], lines)
                    )
                    if "run" in step_dict:
                        au_type = "shell"
                    else:  # uses
                        au_type = self._get_code(
                            step_dict["uses"], step_dict["uses"], lines
                        )

                    au = AtomicUnit(name, au_type)
                    au.line, au.column = (
                        step.start_mark.line + 1,
                        step.start_mark.column + 1,
                    )
                    au.code = self._get_code(step, step, lines)

                    for key, value in step.value:
                        if key.value in ["with", "env"]:
                            for with_key, with_value in value.value:
                                au.add_attribute(
                                    self.__parse_attribute(with_key, with_value, lines)
                                )
                        elif key.value not in ["name", "uses"]:
                            au.add_attribute(self.__parse_attribute(key, value, lines))

                    job.add_atomic_unit(au)
                continue
            elif attr_key.value in ["env", "defaults"]:
                for env_key, env_value in attr_value.value:
                    job.add_variable(self.__parse_variable(env_key, env_value, lines))
            else:
                job.add_attribute(self.__parse_attribute(attr_key, attr_value, lines))

        return job

    def parse_file(self, path: str, type: UnitBlockType) -> Optional[UnitBlock]:
        schema = resource_filename("glitch.parsers", "resources/github_workflow.json")

        with open(path) as f:
            try:
                parsed_file = YAML().compose(f)
                f.seek(0, 0)
                lines = f.readlines()
            except:
                throw_exception(EXCEPTIONS["GHA_COULD_NOT_PARSE"], path)
                return None

        if parsed_file is None or not isinstance(parsed_file, MappingNode):
            throw_exception(EXCEPTIONS["GHA_COULD_NOT_PARSE"], path)
            return None

        with open(path) as f:
            with open(schema) as f_schema:
                schema = json.load(f_schema)
                yaml = YAML()
                try:
                    jsonschema.validate(yaml.load(f.read()), schema)  # type: ignore
                except jsonschema.ValidationError:
                    throw_exception(EXCEPTIONS["GHA_COULD_NOT_PARSE"], path)
                    return None

        parsed_file_value = self.__parse_dict(parsed_file)
        if "name" not in parsed_file_value:
            unit_block = UnitBlock("", type)
        else:
            unit_block = UnitBlock(
                self._get_code(
                    parsed_file_value["name"], parsed_file_value["name"], lines
                ),
                type,
            )
        unit_block.path = path

        for key, value in parsed_file.value:
            if key.value in ["env", "defaults"]:
                for env_key, env_value in value.value:
                    unit_block.add_variable(
                        self.__parse_variable(env_key, env_value, lines)
                    )
            if key.value == "jobs":
                for job_key, job_value in value.value:
                    job = self.__parse_job(job_key, job_value, lines)
                    unit_block.add_unit_block(job)
            elif key.value != "name":
                unit_block.add_attribute(self.__parse_attribute(key, value, lines))

        with open(path) as f:
            comments = list(self._get_comments(parsed_file, f))
            for comment in sorted(comments, key=lambda x: x[0]):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = lines[c.line - 1]
                unit_block.add_comment(c)

        return unit_block

    def parse_folder(self, path: str) -> Project:
        raise NotImplementedError("Not implemented yet")

    def parse_module(self, path: str) -> Module:
        raise NotImplementedError("Not implemented yet")
