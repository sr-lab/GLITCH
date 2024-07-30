import jinja2
import jinja2.nodes
import glitch.parsers.parser as p

from typing import List, Tuple, TextIO, Union, Any
from ruamel.yaml.nodes import Node, MappingNode, SequenceNode, ScalarNode
from ruamel.yaml.tokens import Token, CommentToken
from jinja2 import Environment
from abc import ABC
from copy import deepcopy

from glitch.repr.inter import *


RecursiveTokenList = List[Union[Token, "RecursiveTokenList", None]]


class YamlParser(p.Parser, ABC):
    def __init__(self, options: dict[str, Any] = {}):
        self.env = Environment(**options)

    def _get_code(
        self,
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

    def _get_comments(self, d: Node, file: TextIO) -> set[Tuple[int, str]]:
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
    
    def __get_content(self, info: ElementInfo, code: List[str]) -> str:
        content = code[info.line - 1: info.end_line]
        if info.line == info.end_line:
            content[0] = content[0][info.column - 1: info.end_column - 1]
        else:
            content[0] = content[0][info.column - 1:]
            content[-1] = content[-1][: info.end_column - 1]
        content = "".join(content)

        if content.startswith("|"):
            content = content[1:]
            info.column += 1
        if content.startswith(">-"):
            content = content[2:]
            info.column += 2

        l_rmvd = content[:len(content) - len(content.lstrip())]
        content = content.lstrip()
        for c in l_rmvd:
            if c == "\n":
                info.line += 1
                info.column = 1
            else:
                info.column += 1

        r_rmvd = content[len(content.rstrip()):]
        content = content.rstrip()
        for c in r_rmvd[::-1]:
            if c == "\n" and info.end_line > info.line:
                info.end_line -= 1
                info.end_column = len(code[info.end_line - 1])
            elif info.end_line > info.line:
                info.end_column -= 1

        return content

    def __parse_jinja_node(self, node: jinja2.nodes.Node, base_info: ElementInfo) -> Expr:
        info = deepcopy(base_info)
        code = base_info.code.split("\n")

        info.line = base_info.line + node.lineno - 1
        info.end_line = base_info.line + (node.end_lineno - node.lineno)
        code = code[node.lineno - 1 : node.end_lineno]

        info.column = base_info.column + node.col
        if info.line == info.end_line:
            info.end_column = base_info.column + node.end_col
        else:
            info.end_column = node.end_col + 1

        code[0] = code[0][node.col :]
        code[-1] = code[-1][: node.end_col]
        info.code = "\n".join(code)

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
            if isinstance(node.node, jinja2.nodes.Name):
                return FunctionCall(
                    node.node.name,
                    [self.__parse_jinja_node(arg, base_info) for arg in node.args],
                    info,
                )  # type: ignore
            else:
                # TODO: When the node is for instance a Getattr
                return Null()
        elif isinstance(node, jinja2.nodes.Filter):
            assert node.node is not None
            return self.__parse_jinja_node(node.node, base_info)
        elif isinstance(node, jinja2.nodes.List):
            return Array([self.__parse_jinja_node(n, base_info) for n in node.items], base_info)  # type: ignore
        elif isinstance(node, jinja2.nodes.Add):
            return Sum(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )
        elif isinstance(node, jinja2.nodes.Getattr):
            attr_info = deepcopy(info)
            attr_info.column = info.end_column - len(node.attr)
            return Access(
                info,
                self.__parse_jinja_node(node.node, base_info),
                String(node.attr, attr_info),
            )
        elif isinstance(node, jinja2.nodes.Getitem):
            return Access(
                info,
                self.__parse_jinja_node(node.node, base_info),
                self.__parse_jinja_node(node.arg, base_info),
            )
        elif isinstance(node, jinja2.nodes.Div):
            return Divide(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )
        elif isinstance(node, jinja2.nodes.Or):
            return Or(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )
        elif isinstance(node, jinja2.nodes.Mul):
            return Multiply(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )

        elif isinstance(node, jinja2.nodes.Tuple):
            return Array(
                [self.__parse_jinja_node(n, base_info) for n in node.items], info
            )
        elif isinstance(node, jinja2.nodes.Dict):
            value: Dict[Expr, Expr] = {}
            for item in node.items:
                value[
                    self.__parse_jinja_node(item.key, base_info)
                ] = self.__parse_jinja_node(item.value, base_info)
            return Hash(value, info)
        elif isinstance(node, jinja2.nodes.Not):
            return Not(info, self.__parse_jinja_node(node.node, base_info))
        elif isinstance(node, jinja2.nodes.Sub):
            return Subtract(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )
        elif isinstance(node, jinja2.nodes.Mod):
            return Modulo(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )
        elif isinstance(node, jinja2.nodes.CondExpr):
            c = ConditionalStatement(
                self.__parse_jinja_node(node.test, base_info),
                ConditionalStatement.ConditionType.IF,
            )
            c.add_statement(self.__parse_jinja_node(node.expr1, base_info))
            if node.expr2 is not None:
                c.else_statement = ConditionalStatement(
                    Null(), ConditionalStatement.ConditionType.IF, is_default=True
                )
                c.else_statement.add_statement(
                    self.__parse_jinja_node(node.expr2, base_info)
                )
            return c
        elif isinstance(node, jinja2.nodes.Assign):
            return Assign(
                info,
                self.__parse_jinja_node(node.target, base_info),
                self.__parse_jinja_node(node.node, base_info),
            )
        elif isinstance(node, jinja2.nodes.And):
            return And(
                info,
                self.__parse_jinja_node(node.left, base_info),
                self.__parse_jinja_node(node.right, base_info),
            )
        elif isinstance(node, jinja2.nodes.Concat):
            c = Null()
            for n in node.nodes:
                c = Sum(info, c, self.__parse_jinja_node(n, base_info))
            return c
        elif isinstance(node, jinja2.nodes.Not):
            return Not(info, self.__parse_jinja_node(node.node, base_info))
        elif isinstance(
            node,
            (
                jinja2.nodes.Compare,
                jinja2.nodes.Test,
                jinja2.nodes.Slice,
                jinja2.nodes.Output,
                jinja2.nodes.FloorDiv,
                jinja2.nodes.For,
                jinja2.nodes.If,
            ),
        ):
            # TODO Support these nodes
            return Null()
        else:
            raise ValueError(f"Node not supported {node}")

    def __parse_string(self, v: str, info: ElementInfo) -> Expr:
        """
        Parses a string to the intermediate representation and unrolls
        the interpolation.
        """
        if v in ["null", "~"]:
            return Null(info)
        quotes = v.startswith(("'", '"')) and v.endswith(("'", '"'))

        jinja_nodes = list(self.env.parse(v).body[0].iter_child_nodes())

        for node in jinja_nodes[::-1]:
            if isinstance(node, jinja2.nodes.TemplateData) and node.data.strip() in ["'", '"']:
                jinja_nodes.remove(node)

        if len(jinja_nodes) > 1:
            parts: List[Expr] = []
            for node in jinja_nodes:
                parts.append(self.__parse_jinja_node(node, info))

            if (
                isinstance(parts[0], String) 
                and quotes
                and parts[0].value.startswith(("'", '"'))
            ):
                parts[0].value = parts[0].value[1:]
                parts[0].column += 1

            if (
                isinstance(parts[-1], String) 
                and quotes
                and parts[-1].value.endswith(("'", '"'))
            ):
                parts[-1].value = parts[-1].value[:-1]
                parts[-1].end_column -= 1

            expr = Sum(
                info, 
                parts[0], 
                parts[1]
            )
            for part in parts[2:]:
                expr = Sum(                
                    info,
                    expr, 
                    part
                )

            return expr
        elif len(jinja_nodes) == 1:
            expr = self.__parse_jinja_node(jinja_nodes[0], info)
            if (
                isinstance(expr, String) 
                and quotes 
                and expr.value.startswith(("'", '"'))
                and expr.value.endswith(("'", '"'))
            ):
                expr.value = expr.value[1:-1]
            return expr

        raise ValueError("No Jinja nodes found")

    def get_value(self, value: Node, code: List[str]) -> Expr:
        info = ElementInfo(
            value.start_mark.line + 1,
            value.start_mark.column + 1,
            value.end_mark.line + 1,
            value.end_mark.column + 1,
            self._get_code(value, value, code),
        )
        v: Any = value.value

        if isinstance(v, bool) and value.tag.endswith("bool"):
            return Boolean(bool(v), info)
        elif isinstance(v, str) and value.tag.endswith("int"):
            return Integer(int(v), info)
        elif isinstance(v, str) and value.tag.endswith("float"):
            return Float(float(v), info)
        elif isinstance(v, str):
            content = self.__get_content(info, code)
            return self.__parse_string("".join(content), info)
        elif v is None:
            return Null(info)
        elif isinstance(value, MappingNode) and isinstance(v, list):
            return Hash(
                {
                    self.get_value(key, code): self.get_value(val, code) # type: ignore
                    for key, val in v # type: ignore
                },
                info,
            )
        elif isinstance(v, list):
            return Array([self.get_value(val, code) for val in v], info) # type: ignore
        elif isinstance(v, dict):
            return Hash(
                {
                    self.get_value(key, code): self.get_value(val, code)  # type: ignore
                    for key, val in v.items()  # type: ignore
                },
                info,
            )
        else:
            raise ValueError(f"Unknown value type: {type(v)}")
