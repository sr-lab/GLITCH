import os
from typing import List, Optional

from glitch.parsers.yaml import YamlParser
from glitch.exceptions import EXCEPTIONS, throw_exception
from glitch.repr.inter import *
from ruamel.yaml.main import YAML
from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode, Node


class CloudFormationParser(YamlParser):
    def parse_file(self, path: str, type: UnitBlockType) -> Optional[UnitBlock]:
        try:
            with open(path) as f:
                parsed_file = YAML().compose(f)
                f.seek(0, 0)
                code = f.readlines()
                code.append("")
        except Exception:
            throw_exception(EXCEPTIONS["CF_COULD_NOT_PARSE"], path)
            return None

        if parsed_file is None or not isinstance(parsed_file, MappingNode):
            throw_exception(EXCEPTIONS["CF_COULD_NOT_PARSE"], path)
            return None

        unit_block = UnitBlock(path, type)
        unit_block.path = path

        for key, value in parsed_file.value:
            name = key.value
            if name == "Resources" and isinstance(value, MappingNode):
                self._parse_resources(value, code, unit_block)
            elif name == "Parameters" and isinstance(value, MappingNode):
                self._parse_parameters(value, code, unit_block)
            elif name == "Mappings" and isinstance(value, MappingNode):
                self._parse_mappings(value, code, unit_block)
            elif name == "Conditions" and isinstance(value, MappingNode):
                self._parse_conditions(value, code, unit_block)

        with open(path) as f:
            for comment in self._get_comments(parsed_file, f):
                c = Comment(comment[1])
                c.line = comment[0]
                c.code = code[c.line - 1]
                unit_block.add_comment(c)

        return unit_block

    def parse_module(self, path: str) -> Module:
        res = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        files = [
            f.path for f in os.scandir(path) if f.is_file() and not f.is_symlink()
        ]
        for f in files:
            if f.endswith((".yml", ".yaml")):
                unit_block = self.parse_file(f, UnitBlockType.unknown)
                if unit_block is not None:
                    res.add_block(unit_block)

        return res

    def parse_folder(self, path: str) -> Project:
        res = Project(os.path.basename(os.path.normpath(path)))
        res.add_module(self.parse_module(path))

        subfolders = [
            f.path for f in os.scandir(path) if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            aux = self.parse_folder(d)
            res.blocks += aux.blocks
            res.modules += aux.modules

        return res

    def _parse_resources(
        self, node: MappingNode, code: List[str], unit_block: UnitBlock
    ) -> None:
        for name_node, resource_node in node.value:
            if not isinstance(resource_node, MappingNode):
                continue
            au = self._parse_resource(name_node, resource_node, code)
            unit_block.add_atomic_unit(au)
            for dep in self._parse_depends_on(resource_node, code):
                unit_block.add_dependency(dep)

    def _parse_resource(
        self, name: ScalarNode, node: MappingNode, code: List[str]
    ) -> AtomicUnit:
        r_type = ""
        properties: Optional[MappingNode] = None

        for key, value in node.value:
            if key.value == "Type" and isinstance(value, ScalarNode):
                r_type = value.value
            elif key.value == "Properties" and isinstance(value, MappingNode):
                properties = value

        au = AtomicUnit(self.get_value(name, code), r_type)
        au.line = name.start_mark.line + 1
        au.column = name.start_mark.column + 1
        au.code = self._get_code(name, node, code)

        if properties is not None:
            for attr in self._parse_properties(properties, code):
                au.add_attribute(attr)

        return au

    def _parse_properties(
        self, node: MappingNode, code: List[str]
    ) -> List[Attribute]:
        attributes: List[Attribute] = []
        for key, value in node.value:
            attr_value = self.get_value(value, code)
            info = ElementInfo(
                key.start_mark.line + 1,
                key.start_mark.column + 1,
                value.end_mark.line + 1,
                value.end_mark.column + 1,
                self._get_code(key, value, code),
            )
            attributes.append(Attribute(key.value, attr_value, info))
        return attributes

    def _parse_parameters(
        self, node: MappingNode, code: List[str], unit_block: UnitBlock
    ) -> None:
        for name_node, param_node in node.value:
            if isinstance(param_node, MappingNode):
                var = self._parse_parameter(name_node, param_node, code)
                unit_block.add_variable(var)

    def _parse_parameter(
        self, name: ScalarNode, node: MappingNode, code: List[str]
    ) -> Variable:
        default_value: Expr = Null(
            ElementInfo(
                name.start_mark.line + 1,
                name.start_mark.column + 1,
                name.end_mark.line + 1,
                name.end_mark.column + 1,
                self._get_code(name, name, code),
            )
        )

        for key, value in node.value:
            if key.value == "Default":
                default_value = self.get_value(value, code)
                break

        info = ElementInfo(
            name.start_mark.line + 1,
            name.start_mark.column + 1,
            node.end_mark.line + 1,
            node.end_mark.column + 1,
            self._get_code(name, node, code),
        )

        return Variable(name.value, default_value, info)

    def _parse_mappings(
        self, node: MappingNode, code: List[str], unit_block: UnitBlock
    ) -> None:
        for name_node, mapping_node in node.value:
            if not isinstance(mapping_node, MappingNode):
                continue
            value = self.get_value(mapping_node, code)
            info = ElementInfo(
                name_node.start_mark.line + 1,
                name_node.start_mark.column + 1,
                mapping_node.end_mark.line + 1,
                mapping_node.end_mark.column + 1,
                self._get_code(name_node, mapping_node, code),
            )
            unit_block.add_variable(Variable(name_node.value, value, info))

    def _parse_conditions(
        self, node: MappingNode, code: List[str], unit_block: UnitBlock
    ) -> None:
        for name_node, cond_node in node.value:
            value = self.get_value(cond_node, code)
            info = ElementInfo(
                name_node.start_mark.line + 1,
                name_node.start_mark.column + 1,
                cond_node.end_mark.line + 1,
                cond_node.end_mark.column + 1,
                self._get_code(name_node, cond_node, code),
            )
            unit_block.add_variable(Variable(name_node.value, value, info))

    def _parse_depends_on(
        self, node: MappingNode, code: List[str]
    ) -> List[Dependency]:
        dependencies: List[Dependency] = []
        for key, value in node.value:
            if key.value != "DependsOn":
                continue
            if isinstance(value, ScalarNode):
                d = Dependency([value.value])
                d.line = value.start_mark.line + 1
                d.code = self._get_code(value, value, code)
                dependencies.append(d)
            elif isinstance(value, SequenceNode):
                for item in value.value:
                    if isinstance(item, ScalarNode):
                        d = Dependency([item.value])
                        d.line = item.start_mark.line + 1
                        d.code = self._get_code(item, item, code)
                        dependencies.append(d)
        return dependencies

    def get_value(self, value: Node, code: List[str]) -> Expr:
        if isinstance(value, ScalarNode) and value.tag in ("!Ref", "!ref"):
            info = ElementInfo(
                value.start_mark.line + 1,
                value.start_mark.column + 1,
                value.end_mark.line + 1,
                value.end_mark.column + 1,
                self._get_code(value, value, code),
            )
            return VariableReference(value.value, info)

        if isinstance(value, (ScalarNode, SequenceNode)) and value.tag in (
            "!GetAtt",
            "!getatt",
        ):
            return self._parse_getatt(value, code)

        if isinstance(value, MappingNode):
            for key, val in value.value:
                if not isinstance(key, ScalarNode):
                    continue
                if key.value == "Fn::GetAtt":
                    return self._parse_getatt(val, code)
                if key.value == "Ref" and isinstance(val, ScalarNode):
                    info = ElementInfo(
                        value.start_mark.line + 1,
                        value.start_mark.column + 1,
                        value.end_mark.line + 1,
                        value.end_mark.column + 1,
                        self._get_code(value, value, code),
                    )
                    return VariableReference(val.value, info)

        return super().get_value(value, code)

    def _parse_getatt(self, node: Node, code: List[str]) -> Access:
        resource = ""
        attribute = ""

        if isinstance(node, ScalarNode):
            parts = node.value.split(".", 1)
            resource = parts[0]
            attribute = parts[1] if len(parts) > 1 else ""
        elif isinstance(node, SequenceNode) and len(node.value) >= 2:
            if isinstance(node.value[0], ScalarNode):
                resource = node.value[0].value
            if isinstance(node.value[1], ScalarNode):
                attribute = node.value[1].value

        info = ElementInfo(
            node.start_mark.line + 1,
            node.start_mark.column + 1,
            node.end_mark.line + 1,
            node.end_mark.column + 1,
            self._get_code(node, node, code),
        )

        resource_info = ElementInfo(
            node.start_mark.line + 1,
            node.start_mark.column + 1,
            node.end_mark.line + 1,
            node.end_mark.column + 1,
            resource,
        )

        attr_info = ElementInfo(
            node.start_mark.line + 1,
            node.start_mark.column + 1,
            node.end_mark.line + 1,
            node.end_mark.column + 1,
            attribute,
        )

        return Access(
            info,
            VariableReference(resource, resource_info),
            String(attribute, attr_info),
        )
