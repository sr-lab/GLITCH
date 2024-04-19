import json
import jsonschema
import glitch.parsers.parser as p

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
from ruamel.yaml.tokens import Token
from pkg_resources import resource_filename


class GithubActionsParser(p.Parser):
    @staticmethod
    def __get_value(
        node: Node
    ) -> Any:
        if isinstance(node, ScalarNode):
            return node.value
        elif isinstance(node, MappingNode):
            return {
                GithubActionsParser.__get_value(key): GithubActionsParser.__get_value(value)
                for key, value in node.value
            }
        elif isinstance(node, SequenceNode):
            return [GithubActionsParser.__get_value(value) for value in node.value]
        elif isinstance(node, CollectionNode):
            return node.value
        else:
            return None

    # TODO: refactor to be in parent class of Ansible and GithubActions
    @staticmethod
    def __get_code(
        start_token: Token | Node,
        end_token: List[Token | Node] | Token | Node | str,
        code: List[str],
    ):
        if isinstance(end_token, list) and len(end_token) > 0:
            end_token = end_token[-1]
        elif isinstance(end_token, list) or isinstance(end_token, str):
            end_token = start_token

        if start_token.start_mark.line == end_token.end_mark.line:
            res = code[start_token.start_mark.line][
                start_token.start_mark.column : end_token.end_mark.column
            ]
        else:
            res = code[start_token.start_mark.line]

        for line in range(start_token.start_mark.line + 1, end_token.end_mark.line):
            res += code[line]

        if start_token.start_mark.line != end_token.end_mark.line:
            res += code[end_token.end_mark.line][: end_token.end_mark.column]

        return res
    
    @staticmethod
    def __parse_attribute(key: Node, value: Node, lines: List[str]) -> Attribute:
        attrs: List[KeyValue] = []

        if isinstance(value, MappingNode):
            attr_value = None
            for k, v in value.value:
                attrs.append(
                    GithubActionsParser.__parse_attribute(k, v, lines)
                )
        else:
            attr_value = GithubActionsParser.__get_value(value)

        attr = Attribute(
            GithubActionsParser.__get_value(key), 
            attr_value,
            False # FIXME
        )
        attr.line, attr.column = key.start_mark.line, key.start_mark.column
        attr.code = GithubActionsParser.__get_code(
            key, value, lines
        )
        for child in attrs:
            attr.keyvalues.append(child)

        return attr
    
    def __parse_job(self, key: Node, value: Node, lines: List[str]) -> UnitBlock:
        job = UnitBlock(key.value, UnitBlockType.block)
        job.line, job.column = key.start_mark.line, key.start_mark.column
        job.code = self.__get_code(key, value, lines)

        for attr_key, attr_value in value.value:
            if attr_key.value == "steps":
                for step in attr_value.value:
                    step_dict = self.__get_value(step)
                    name = "" if "name" not in step_dict else step_dict["name"]
                    if "run" in step_dict:
                        au_type = "shell"
                    else: # uses
                        au_type = step_dict["uses"]

                    au = AtomicUnit(name, au_type)
                    au.line, au.column = step.start_mark.line, step.start_mark.column
                    au.code = self.__get_code(step, step, lines)

                    for key, value in step.value:
                        if key.value in ["with", "env"]:
                            for with_key, with_value in value.value:
                                au.add_attribute(
                                    self.__parse_attribute(
                                        with_key, 
                                        with_value, 
                                        lines
                                    )
                                )
                        elif key.value not in ["name", "uses"]:
                            au.add_attribute(
                                self.__parse_attribute(
                                    key, 
                                    value,
                                    lines
                                )
                            )

                    job.add_atomic_unit(au)
                continue

            # TODO: Add env and defaults
            job.add_attribute(self.__parse_attribute(attr_key, attr_value, lines))

        return job

    def parse_file(self, path: str, type: UnitBlockType) -> Optional[UnitBlock]:
        schema = resource_filename(
            "glitch.parsers", "resources/github_workflow.json"
        )

        with open(path) as f:
            try:
                parsed_file = YAML().compose(f)
                f.seek(0, 0)
                lines = f.readlines()
            except:
                # TODO: Add logging
                return None
        
        if parsed_file is None or not isinstance(parsed_file, MappingNode):
            # TODO: Add logging
            return None
        
        with open(path) as f:
            with open(schema) as f_schema:
                schema = json.load(f_schema)
                # TODO: catch exception
                yaml = YAML()
                jsonschema.validate(yaml.load(f.read()), schema) # type: ignore

        parsed_file_value = self.__get_value(parsed_file)
        if "name" not in parsed_file_value:
            unit_block = UnitBlock(path, type)
        else:
            unit_block = UnitBlock(parsed_file_value["name"], type)

        for key, value in parsed_file.value:
            # TODO: Add env and defaults
            if key.value == "jobs":
                for job_key, job_value in value.value:
                    job = self.__parse_job(job_key, job_value, lines)
                    unit_block.add_unit_block(job)
                continue
            elif key.value != "name":
                unit_block.add_attribute(
                    self.__parse_attribute(key, value, lines)
                )

        return unit_block

    def parse_folder(self, path: str) -> Project:
        raise NotImplementedError("Not implemented yet")

    def parse_module(self, path: str) -> Module:
        raise NotImplementedError("Not implemented yet")
