import jinja2
import jinja2.nodes
import glitch.parsers.parser as p

from typing import List, Tuple, TextIO, Union, Any
from ruamel.yaml.nodes import Node, MappingNode, SequenceNode, ScalarNode
from ruamel.yaml.tokens import Token, CommentToken
from jinja2 import Environment
from abc import ABC

from glitch.repr.inter import *


RecursiveTokenList = List[Union[Token, "RecursiveTokenList", None]]


class YamlParser(p.Parser, ABC):
    @staticmethod
    def _get_code(
        start_token: Token | Node,
        end_token: List[Token | Node] | Token | Node | str,
        code: List[str],
    ) -> str:
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

        # The end_mark.column > 0 avoids cases where the end token is in the last line
        # leading to a index out of range error
        if (
            start_token.start_mark.line != end_token.end_mark.line
            and end_token.end_mark.column > 0
        ):
            res += code[end_token.end_mark.line][: end_token.end_mark.column]

        return res

    @staticmethod
    def _get_comments(d: Node, file: TextIO) -> set[Tuple[int, str]]:
        """Extracts comments from a YAML file and returns a set of tuples with the line number and the comment itself.

        Args:
            d (Node): The root node of the YAML file.
            file (TextIO): The file object of the YAML file.

        Returns:
            set[Tuple[int, str]]: A set of tuples with the line number and the comment itself.
        """

        def extract_from_token(tokenlist: RecursiveTokenList) -> List[Tuple[int, str]]:
            res: List[Tuple[int, str]] = []
            for token in tokenlist:
                if token is None:
                    continue
                elif isinstance(token, list):
                    res += extract_from_token(token)
                elif isinstance(token, CommentToken):
                    res.append((token.start_mark.line, token.value))
            return res

        def yaml_comments(d: Node) -> List[Tuple[int, str]]:
            res: List[Tuple[int, str]] = []

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

        comments: List[Tuple[int, str]] = []
        for c_group in yaml_comments(d):
            line = c_group[0]
            c_group_comments = c_group[1].strip().split("\n")

            for i, comment in enumerate(c_group_comments):
                if comment == "":
                    continue
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
    def __parse_jinja_node(node: jinja2.nodes.Node, info: ElementInfo) -> Expr:
        if isinstance(node, jinja2.nodes.TemplateData):
            return String(node.data, info)
        elif isinstance(node, jinja2.nodes.Name):
            return VariableReference(node.name, info)
        elif isinstance(node, jinja2.nodes.Const):
            if isinstance(node.value, str):
                return String(node.value, info)
            elif isinstance(node.value, int):
                return Integer(node.value, info)
            elif isinstance(node.value, float):
                return Float(node.value, info)
            elif isinstance(node.value, bool):
                return Boolean(node.value, info)
            else:
                raise ValueError("Const not supported")
        elif isinstance(node, jinja2.nodes.Call):
            assert isinstance(node.node, jinja2.nodes.Name)
            return FunctionCall(node.node.name, [
                YamlParser.__parse_jinja_node(arg, info) for arg in node.args
            ], info) # type: ignore
        elif isinstance(node, jinja2.nodes.Filter):
            assert node.node is not None
            return YamlParser.__parse_jinja_node(node.node, info)
        elif isinstance(node, jinja2.nodes.List):
            return Array([YamlParser.__parse_jinja_node(n, info) for n in node.items], info) # type: ignore
        elif isinstance(node, jinja2.nodes.Add):
            return Sum(info, YamlParser.__parse_jinja_node(node.left, info), YamlParser.__parse_jinja_node(node.right, info))
        else:
            print(node)
            raise ValueError("Node not supported")
        

    @staticmethod
    def __parse_string(v: str, info: ElementInfo) -> Expr:
        """
        Parses a string to the intermediate representation and unrolls
        the interpolation.
        """
        if v in ["null", "~"]:
            return Null(info)

        jinja_nodes = list(Environment().parse(v).body[0].iter_child_nodes())

        for node in jinja_nodes[::-1]:
            if isinstance(node, jinja2.nodes.TemplateData) and node.data.strip() == "\"":
                jinja_nodes.remove(node)

        if len(jinja_nodes) > 1:
            parts: List[Expr] = []
            for node in jinja_nodes:
                parts.append(YamlParser.__parse_jinja_node(node, info))

            expr = Sum(info, parts[0], parts[1])
            for part in parts[2:]:
                expr = Sum(info, expr, part)
                
            return expr
        elif len(jinja_nodes) == 1:
            return YamlParser.__parse_jinja_node(jinja_nodes[0], info)
        
        raise ValueError("No Jinja nodes found")

    @staticmethod
    def get_value(value: Node, code: List[str]) -> Expr:
        info = ElementInfo(
            value.start_mark.line + 1,
            value.start_mark.column + 1,
            value.end_mark.line + 1,
            value.end_mark.column + 1,
            YamlParser._get_code(value, value, code),
        )
        v: Any = value.value

        if isinstance(v, bool) and value.tag.endswith("bool"):
            return Boolean(bool(v), info)
        elif isinstance(v, str) and value.tag.endswith("int"):
            return Integer(int(v), info)
        elif isinstance(v, str) and value.tag.endswith("float"):
            return Float(float(v), info)
        elif isinstance(v, str):
            return YamlParser.__parse_string(v, info)
        elif v is None:
            return Null(info)
        elif isinstance(v, list):
            return Array([YamlParser.get_value(val, code) for val in v], info) # type: ignore
        elif isinstance(v, dict):
            return Hash(
                {
                    YamlParser.get_value(key, code): YamlParser.get_value(val, code) # type: ignore
                    for key, val in v.items() # type: ignore
                },
                info,
            )
        else:
            raise ValueError(f"Unknown value type: {type(v)}")
