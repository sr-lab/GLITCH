import json
import jsonschema

from glitch.parsers.yaml import YamlParser
from typing import Optional
from glitch.repr.inter import *
from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import (
    Node,
    ScalarNode,
    MappingNode,
    SequenceNode,
    CollectionNode,
)
from pkg_resources import resource_filename
from glitch.exceptions import EXCEPTIONS, throw_exception


class GithubActionsParser(YamlParser):
    @staticmethod
    def __get_value(node: Node) -> Any:
        if isinstance(node, ScalarNode):
            return node.value
        elif isinstance(node, MappingNode):
            return {
                GithubActionsParser.__get_value(key): GithubActionsParser.__get_value(
                    value
                )
                for key, value in node.value
            }
        elif isinstance(node, SequenceNode):
            return [GithubActionsParser.__get_value(value) for value in node.value]
        elif isinstance(node, CollectionNode):
            return node.value
        else:
            return None

    @staticmethod
    def __parse_variable(key: Node, value: Node, lines: List[str]) -> Variable:
        vars: List[KeyValue] = []

        if isinstance(value, MappingNode):
            var_value = None
            for k, v in value.value:
                vars.append(GithubActionsParser.__parse_variable(k, v, lines))
        else:
            var_value = GithubActionsParser.__get_value(value)

        var = Variable(GithubActionsParser.__get_value(key), var_value, False)
        if isinstance(var.value, str):
            var.has_variable = "${{" in var.value
        var.line, var.column = key.start_mark.line + 1, key.start_mark.column + 1
        var.code = GithubActionsParser._get_code(key, value, lines)
        for child in vars:
            var.keyvalues.append(child)

        return var

    @staticmethod
    def __parse_attribute(key: Node, value: Node, lines: List[str]) -> Attribute:
        attrs: List[KeyValue] = []

        if isinstance(value, MappingNode):
            attr_value = None
            for k, v in value.value:
                attrs.append(GithubActionsParser.__parse_attribute(k, v, lines))
        else:
            attr_value = GithubActionsParser.__get_value(value)

        attr = Attribute(GithubActionsParser.__get_value(key), attr_value, False)
        if isinstance(attr.value, str):
            attr.has_variable = "${{" in attr.value
        attr.line, attr.column = key.start_mark.line + 1, key.start_mark.column + 1
        attr.code = GithubActionsParser._get_code(key, value, lines)
        for child in attrs:
            attr.keyvalues.append(child)

        return attr

    def __parse_job(self, key: Node, value: Node, lines: List[str]) -> UnitBlock:
        job = UnitBlock(key.value, UnitBlockType.block)
        job.line, job.column = key.start_mark.line + 1, key.start_mark.column + 1
        job.code = GithubActionsParser._get_code(key, value, lines)

        for attr_key, attr_value in value.value:
            if attr_key.value == "steps":
                for step in attr_value.value:
                    step_dict = self.__get_value(step)
                    name = "" if "name" not in step_dict else step_dict["name"]
                    if "run" in step_dict:
                        au_type = "shell"
                    else:  # uses
                        au_type = step_dict["uses"]

                    au = AtomicUnit(name, au_type)
                    au.line, au.column = (
                        step.start_mark.line + 1,
                        step.start_mark.column + 1,
                    )
                    au.code = GithubActionsParser._get_code(step, step, lines)

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

        parsed_file_value = self.__get_value(parsed_file)
        if "name" not in parsed_file_value:
            unit_block = UnitBlock("", type)
        else:
            unit_block = UnitBlock(parsed_file_value["name"], type)
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
            comments = list(GithubActionsParser._get_comments(parsed_file, f))
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
