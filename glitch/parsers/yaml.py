import glitch.parsers.parser as p

from typing import List, Tuple, TextIO, Union
from ruamel.yaml.nodes import Node, MappingNode, SequenceNode, ScalarNode
from ruamel.yaml.tokens import Token, CommentToken
from abc import ABC


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
