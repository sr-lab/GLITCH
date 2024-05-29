import os
import sys
import re
import tempfile
import glitch.parsers.parser as p

from string import Template
from pkg_resources import resource_filename
from typing import Any, List, Tuple, Callable
from glitch.repr.inter import *
from glitch.parsers.ripper_parser import parser_yacc
from glitch.helpers import remove_unmatched_brackets
from glitch.exceptions import EXCEPTIONS, throw_exception

ChefValue = Tuple[str, str] | str | int | bool | List["ChefValue"]


class AddArgs(Value):
    def __init__(self, value: List[Expr], info: ElementInfo) -> None:
        super().__init__(info, value)


class ChefParser(p.Parser):
    """
    https://kddnewton.com/ripper-docs/events
    """

    __ADD = [
        "args_add_star",
        "args_add",
        "qwords_add",
        "qsymbols_add",
        "words_add",
        "symbols_add",
        "word_add",
        "stmts_add",
        "mrhs_add",
        "mrhs_add_star",
        "mrhs_new_from_args",
        "string_add",
        "xstring_add",
        "regexp_add",
    ]

    class Node:
        def __init__(self, id: str, args: List[Any]) -> None:
            self.id: str = id
            self.args: List[Any] = args

        def __repr__(self) -> str:
            return str(self.id)

        def as_dict(self) -> Dict[str, Any]:
            def parse_args(args: List[Any]) -> List[Any]:
                res: List[Any] = []
                for arg in args:
                    if isinstance(arg, ChefParser.Node):
                        res.append(arg.as_dict())
                    elif isinstance(arg, list):
                        res.append(parse_args(arg))  # type: ignore
                    else:
                        res.append(arg)
                return res

            return {"id": self.id, "args": parse_args(self.args)}

        def __iter__(self):
            return iter(self.args)

        def __reversed__(self):
            return reversed(self.args)

    @staticmethod
    def _check_id(ast: Any, ids: List[Any]) -> bool:
        return isinstance(ast, ChefParser.Node) and ast.id in ids

    @staticmethod
    def _check_node(ast: Any, ids: List[Any], size: int) -> bool:
        return ChefParser._check_id(ast, ids) and len(ast.args) == size

    @staticmethod
    def _check_has_variable(ast: Node) -> bool:
        references = ["vcall", "call", "aref", "fcall", "var_ref"]
        if ChefParser._check_id(ast, ["args_add_block"]):
            return ChefParser._check_id(ast.args[0][0], references)
        elif ChefParser._check_id(ast, ["method_add_arg"]):
            return ChefParser._check_id(ast.args[0], references)
        elif ChefParser._check_id(ast, ["arg_paren"]):
            return len(ast.args) > 0 and ChefParser._check_has_variable(ast.args[0])
        elif ChefParser._check_node(ast, ["binary"], 3):
            return ChefParser._check_has_variable(
                ast.args[0]
            ) and ChefParser._check_has_variable(ast.args[2])
        else:
            return ChefParser._check_id(ast, references)

    @staticmethod
    def _get_content_bounds(ast: Any, source: List[str]) -> Tuple[int, int, int, int]:
        def is_bounds(l: Any) -> bool:
            return (
                isinstance(l, list)
                and len(l) == 2  # type: ignore
                and isinstance(l[0], int)
                and isinstance(l[1], int)
            )

        start_line, start_column = sys.maxsize, sys.maxsize
        end_line, end_column = 0, 0
        bounded_structures: Dict[str, Tuple[str, str]] = {
            "brace_block": ("{", "}"),
            "arg_paren": ("(", ")"),
            "paren": ("(", ")"),
            "string_embexpr": ("{", "}"),
            "aref": ("", "]"),
            "aref_field": ("", "]"),
            "array": ("[", "]"),
            "hash": ("{", "}"),
            "xstring_literal": ("`", "`"),
            "defined": ("", ")"),
        }

        if ChefParser._check_node(ast, ["@tstring_content"], 2):
            lines = bytes(ast.args[0], "utf-8").decode("unicode_escape")
            lines = lines.split("\n")
            lines = [l + "\n" for l in lines[:-1]] + [lines[-1]]
            if lines[-1] == "":
                lines.pop()

            start_line, start_column = ast.args[1][0], ast.args[1][1]
            end_line = start_line + len(lines) - 1

            if len(lines) == 1:
                end_column = start_column + len(lines[-1]) - 1
            else:
                end_column = len(lines[-1]) - 1
        elif (
            isinstance(ast, ChefParser.Node)
            and len(ast.args) > 0
            and is_bounds(ast.args[-1])
        ):
            start_line, start_column = ast.args[-1][0], ast.args[-1][1]
            # The second argument counting from the end has the content
            # of the node (variable name, string...)
            end_line, end_column = (
                ast.args[-1][0],
                # The parser returns \n as two different characters
                ast.args[-1][1] + len(ast.args[-2].replace("\\n", "\n")) - 1,
            )

            # With identifiers we need to consider the : behind them
            if (
                ChefParser._check_id(ast, ["@ident"])
                and source[start_line - 1][start_column - 1] == ":"
            ):
                start_column -= 1
        elif isinstance(ast, (list, ChefParser.Node)):
            for arg in ast:
                bound = ChefParser._get_content_bounds(arg, source)
                if bound[0] < start_line:
                    start_line = bound[0]
                    start_column = bound[1]
                if bound[0] == start_line and bound[1] < start_column:
                    start_column = bound[1]
                if bound[2] > end_line:
                    end_line = bound[2]
                    end_column = bound[3]
                if bound[2] == end_line and bound[3] > end_column:
                    end_column = bound[3]
            # We have to consider extra characters which correspond
            # to enclosing characters of these structures
            if start_line != sys.maxsize and ChefParser._check_id(
                ast, list(bounded_structures.keys())
            ):
                l_bracket = bounded_structures[ast.id][0]
                r_bracket = bounded_structures[ast.id][1]

                next_lines = source[end_line - 1 :]
                next_lines[0] = next_lines[0][end_column + 1 :]
                next_lines = "".join(next_lines)
                # Add spaces/brackets in front of last token
                for c in next_lines:
                    if c == r_bracket:
                        end_column += 1
                        break
                    elif c == "\n":
                        end_line += 1
                        end_column = -1
                    else:
                        end_column += 1

                previous_lines = source[:start_line]
                previous_lines[-1] = previous_lines[-1][:start_column]
                previous_lines = "".join(previous_lines)[::-1]
                # Add spaces/brackets behind first token
                for c in previous_lines:
                    if l_bracket == "":
                        break
                    elif c == l_bracket:
                        start_column -= 1
                        break
                    elif c == "\n":
                        start_line -= 1
                        start_column = len(source[start_line - 1]) - 1
                    else:
                        start_column -= 1

                if ChefParser._check_id(ast, ["string_embexpr"]):
                    start_column -= 1
            # The original AST does not have the start column
            # of these refs. We need to consider the ::
            elif ChefParser._check_id(ast, ["top_const_ref", "top_const_field"]):
                start_column -= 2
            # String literal is a special case since it can be unbounded in heredocs
            elif (
                ChefParser._check_id(ast, ["string_literal"])
                and start_line != sys.maxsize
                and source[start_line - 1][start_column - 1] in ["'", '"']
                and source[end_line - 1][end_column + 1] in ["'", '"']
            ):
                start_column -= 1
                end_column += 1

        return (start_line, start_column, end_line, end_column)

    @staticmethod
    def _get_info(ast: Any, source: List[str]) -> ElementInfo:
        bounds = ChefParser._get_content_bounds(ast, source)
        return ElementInfo(
            bounds[0],
            bounds[1] + 1,
            bounds[2],
            # We are considering a start at 0 and the index to be inclusive
            # so we need to add 2 to the end column since
            # we want it to start at 1 and be exclusive
            bounds[3] + 2,
            ChefParser._get_content(ast, source),
        )

    @staticmethod
    def _get_content(ast: Any, source: List[str]) -> str:
        empty_structures = {"string_literal": "", "hash": "{}", "array": "[]"}

        if isinstance(ast, list):
            return "".join(list(map(lambda a: ChefParser._get_content(a, source), ast)))  # type: ignore

        if (ast.id in empty_structures and len(ast.args) == 0) or (
            ast.id == "string_literal" and len(ast.args[0].args) == 0
        ):
            return empty_structures[ast.id]

        bounds = ChefParser._get_content_bounds(ast, source)

        res = ""
        if bounds[0] == sys.maxsize:
            return res

        for l in range(bounds[0] - 1, bounds[2]):
            if bounds[0] - 1 == bounds[2] - 1:
                res += source[l][bounds[1] : bounds[3] + 1]
            elif l == bounds[2] - 1:
                res += source[l][: bounds[3] + 1]
            elif l == bounds[0] - 1:
                res += source[l][bounds[1] :]
            else:
                res += source[l]

        if (ast.id == "method_add_block") and (ast.args[1].id == "do_block"):
            res += "\nend"

        if res.startswith(('"', "'", "`")) and res.endswith(('"', "'", "`")):
            res = res[1:-1]

        return remove_unmatched_brackets(res)

    @staticmethod
    def __get_add_args(ast: Node, source: List[str]) -> List[Expr]:
        current = ast
        curr_args: List[Expr] = []

        while ChefParser._check_id(current, ChefParser.__ADD):
            if len(current.args) == 2:
                value = ChefParser._get_value(current.args[1], source)
                if value is not None:
                    curr_args.append(value)
            current = current.args[0]

        curr_args = list(reversed(curr_args))
        return curr_args

    @staticmethod
    def __parse_assoc_hash(ast: Node, source: List[str]) -> Dict[Expr, Expr]:
        hash_args: Dict[Expr, Expr] = {}
        for arg in ast.args[0]:
            if ChefParser._check_id(arg, ["assoc_new"]):
                key = ChefParser._get_value(arg.args[0], source)
                value = ChefParser._get_value(arg.args[1], source)
                assert key is not None
                assert value is not None
                hash_args[key] = value
            elif ChefParser._check_id(arg, ["assoc_splat"]):
                # FIXME: not supported
                key = ChefParser._get_value(arg.args[0], source)
                assert key is not None
                hash_args[key] = key
        return hash_args

    @staticmethod
    def __parse_binary(ast: Node, source: List[str], info: ElementInfo) -> Expr:
        left = ChefParser._get_value(ast.args[0], source)
        right = ChefParser._get_value(ast.args[2], source)
        assert left is not None
        assert right is not None
        op = ast.args[1][1]

        match op:
            case "+":
                return Sum(info, left, right)
            case "-":
                return Subtract(info, left, right)
            case "*":
                return Multiply(info, left, right)
            case "/":
                return Divide(info, left, right)
            case "%":
                return Modulo(info, left, right)
            case "**":
                return Power(info, left, right)
            case "==":
                return Equal(info, left, right)
            case "!=":
                return NotEqual(info, left, right)
            case ">":
                return GreaterThan(info, left, right)
            case "<":
                return LessThan(info, left, right)
            case ">=":
                return GreaterThanOrEqual(info, left, right)
            case "<=":
                return LessThanOrEqual(info, left, right)
            case "<=>":
                # TODO
                return Null()
            case "===":
                return Equal(info, left, right)
            case "&":
                return BitwiseAnd(info, left, right)
            case "|":
                return BitwiseOr(info, left, right)
            case "^":
                return BitwiseXor(info, left, right)
            case "<<":
                return LeftShift(info, left, right)
            case ">>":
                return RightShift(info, left, right)
            case "and" | '"&&"':
                return And(info, left, right)
            case "or" | '"||"':
                return Or(info, left, right)
            case "=~":
                # TODO: Unsupported operation
                return Null()
            case _:
                raise ValueError(f"Unknown binary operator {op}")

    @staticmethod
    def __parse_unary(ast: Node, source: List[str], info: ElementInfo) -> Expr:
        arg = ChefParser._get_value(ast.args[1], source)
        assert arg is not None
        op = ast.args[0][1]

        match op:
            case "!" | "not":
                return Not(info, arg)
            case "-@":
                return Minus(info, arg)
            case _:
                raise ValueError(f"Unknown unary operator {op}")

    @staticmethod
    def __parse_if_expr(ast: Any, source: List[str]) -> Expr | None:
        predicate = ChefParser._get_value(ast.args[0], source)
        assert predicate is not None
        true_part = ChefParser._get_value(ast.args[1], source)
        assert true_part is not None
        true_statement = ConditionalStatement(
            predicate,
            ConditionalStatement.ConditionType.IF,
        )
        true_statement.add_statement(true_part)
        if len(ast.args) == 3:
            false_part = ChefParser._get_value(ast.args[2], source)
            assert false_part is not None
            false_statement = ConditionalStatement(
                Null(), ConditionalStatement.ConditionType.IF, is_default=True
            )
            true_statement.else_statement = false_statement
            false_statement.add_statement(false_part)
        return true_statement

    @staticmethod
    def _get_value(ast: Any, source: List[str]) -> Expr | None:
        NEW = [
            "args_new",
            "qwords_new",
            "qsymbols_new",
            "words_new",
            "symbols_new",
            "word_new",
            "stmts_new",
        ]

        content = ChefParser._get_content(ast, source)
        info = ChefParser._get_info(ast, source)

        if ChefParser._check_id(
            ast,
            [
                "dyna_symbol",
                "@tstring_content",
                "@label",
            ],
        ):
            return String(content, info)
        elif ChefParser._check_id(ast, ["string_content"]):
            return String("", info)
        elif ChefParser._check_node(
            ast, ["string_literal", "xstring_literal"], 1
        ) or ChefParser._check_node(ast, ["regexp_literal"], 2):
            value = ChefParser._get_value(ast.args[0], source)
            assert value is not None
            value.line, value.column = info.line, info.column
            value.end_line, value.end_column = info.end_line, info.end_column
            return value
        elif ChefParser._check_id(ast, ["@int"]):
            if "o" in content:
                return Integer(int(content, 8), info)
            return Integer(int(content), info)
        elif ChefParser._check_id(ast, ["@imaginary"]):
            return Complex(complex(content.replace("i", "j")), info)
        elif ChefParser._check_id(ast, ["@float"]):
            return Float(float(content), info)
        elif ChefParser._check_id(ast, ["@rational"]):
            return Float(float(content[:-1]), info)
        elif ChefParser._check_id(ast, ["binary"]):
            return ChefParser.__parse_binary(ast, source, info)
        elif ChefParser._check_node(ast, ["string_concat"], 2):
            left = ChefParser._get_value(ast.args[0], source)
            right = ChefParser._get_value(ast.args[1], source)
            assert left is not None
            assert right is not None
            return Sum(info, left, right)
        elif ChefParser._check_id(ast, ["unary"]):
            return ChefParser.__parse_unary(ast, source, info)
        elif ChefParser._check_node(ast, ["rescue_mod"], 2):
            value = ChefParser._get_value(ast.args[0], source)
            default = ChefParser._get_value(ast.args[1], source)
            assert isinstance(value, Expr)
            assert isinstance(default, Expr)
            cond = NotEqual(info, value, Null())
            true = ConditionalStatement(cond, ConditionalStatement.ConditionType.IF)
            true.add_statement(value)
            false = ConditionalStatement(
                Null(), ConditionalStatement.ConditionType.IF, is_default=True
            )
            false.add_statement(default)
            true.else_statement = false
            return true
        elif ChefParser._check_id(ast, ["dot2", "dot3"]):
            left = ChefParser._get_value(ast.args[0], source)
            right = ChefParser._get_value(ast.args[1], source)
            assert left is not None
            assert right is not None
            return FunctionCall("range", [left, right], info)
        elif ChefParser._check_id(ast, ["array"]):
            if len(ast.args) == 0:
                return Array([], info)
            value = ChefParser._get_value(ast.args[0], source)
            assert value is not None
            if isinstance(value, AddArgs):
                return Array(value.value, info)
            else:
                return Array([value], info)
        elif ChefParser._check_node(ast, ["ifop"], 3) or ChefParser._check_node(
            ast, ["if_mod", "unless_mod"], 2
        ):
            expr = ChefParser.__parse_if_expr(ast, source)
            assert isinstance(expr, ConditionalStatement)
            if ChefParser._check_id(ast, ["unless_mod"]):
                expr.condition = Not(info, expr.condition)
            return expr
        elif ChefParser._check_id(ast, ["bare_assoc_hash"]):
            hash_args: Dict[Expr, Expr] = ChefParser.__parse_assoc_hash(ast, source)
            return Hash(hash_args, info)
        elif ChefParser._check_id(ast, ["hash"]):
            if ast.args == []:
                return Hash({}, info)
            elif len(ast.args) == 1 and ChefParser._check_node(
                ast.args[0], ["assoclist_from_args"], 1
            ):
                hash_args: Dict[Expr, Expr] = ChefParser.__parse_assoc_hash(
                    ast.args[0], source
                )
                return Hash(hash_args, info)
        elif ChefParser._check_id(
            ast,
            [
                "vcall",
                "symbol_literal",
                "@ident",
                "fcall",
                "string_embexpr",
                "var_field",
                "var_ref",
                "string_dvar",
                "const_path_ref",
                "top_const_ref",
                "top_const_field",
            ],
        ):
            if content.startswith("#{") and content.endswith("}"):
                content = content[2:-1]
                info = ElementInfo(
                    info.line,
                    info.column + 2,
                    info.end_line,
                    info.end_column - 1,
                    content,
                )
            return VariableReference(content, info)
        elif ChefParser._check_id(ast, ["case"]):
            c = ChefParser.CaseChecker(source, ast)
            c.check_all()
            return c.condition
        elif ChefParser._check_id(ast, ["defined", "next", "super", "zsuper"]):
            if len(ast.args) != 0:
                value = ChefParser._get_value(ast.args[0], source)
                assert value is not None
                value = [value]
            else:
                value = []
            return FunctionCall(ast.id, value, info)
        elif ChefParser._check_id(ast, ["aref", "aref_field"]) and len(ast.args) == 2:
            ref = ChefParser._get_value(ast.args[0], source)
            assert ref is not None
            index = ChefParser._get_value(ast.args[1], source)
            assert index is not None
            return Access(info, ref, index)
        elif ChefParser._check_node(ast, ["call"], 3):
            receiver = ChefParser._get_value(ast.args[0], source)
            assert receiver is not None
            method = ChefParser._get_value(ast.args[2], source)
            assert isinstance(method, VariableReference)
            return MethodCall(receiver, method.value, [], info)
        elif ChefParser._check_node(ast, ["command_call"], 4):
            receiver = ChefParser._get_value(ast.args[0], source)
            assert receiver is not None
            method = ChefParser._get_value(ast.args[2], source)
            assert isinstance(method, VariableReference)

            args = ChefParser._get_value(ast.args[3], source)
            assert args is not None
            if not isinstance(args, AddArgs):
                args = [args]
            else:
                args = args.value

            return MethodCall(receiver, method.value, args, info)
        elif ChefParser._check_id(ast, ["args_add_block"]):
            value = ChefParser._get_value(ast.args[0], source)
            assert value is not None
            return value
        elif ChefParser._check_node(
            ast, ["word_add", "string_add", "regexp_add", "xstring_add"], 2
        ):
            args = ChefParser.__get_add_args(ast, source)
            if len(args) == 1:
                return args[0]
            sum_args = Sum(info, args[0], args[1])
            for i in range(2, len(args)):
                sum_args = Sum(info, sum_args, args[i])
            return sum_args
        elif ChefParser._check_node(ast, ChefParser.__ADD, 2):
            args = ChefParser.__get_add_args(ast, source)
            if len(args) == 1:
                return args[0]
            return AddArgs(args, info)
        elif ChefParser._check_node(ast, ["arg_paren", "arg_ambiguous"], 1):
            return ChefParser._get_value(ast.args[0], source)
        elif ChefParser._check_node(ast, ["paren"], 1):
            value = ChefParser._get_value(ast.args[0], source)
            assert value is not None
            if isinstance(value, AddArgs) and len(value.value) == 1:
                return value.value[0]
            return value
        elif ChefParser._check_id(ast, ["@period"]) or ast == []:
            return None
        elif ChefParser._check_node(ast, ["method_add_arg", "command"], 2):
            method = ChefParser._get_value(ast.args[0], source)
            args = ChefParser._get_value(ast.args[1], source)
            assert args is not None
            if not isinstance(args, AddArgs):
                args = [args]
            else:
                args = args.value

            if isinstance(method, VariableReference):
                return FunctionCall(method.value, args, info)

            assert isinstance(method, MethodCall)
            method.args = args

            return method
        elif ChefParser._check_id(
            ast,
            [
                "args_forward",
                "until_mod",
                "while_mod",
                "hshptn",
                "do_block",
                "brace_block",
                "method_add_block",
                "begin",
            ],
        ):
            # FIXME: Not supported
            return Null(info)
        elif ChefParser._check_id(ast, NEW):
            return Null(info)

        raise ValueError(f"Unknown ast type {ast.id}: {content} {info} {len(ast.args)}")

    class Checker:
        def __init__(self, source: List[str]) -> None:
            self.tests_ast_stack: List[Tuple[List[Callable[[Any], bool]], Any]] = []
            self.source = source

        def check(self) -> bool:
            tests, ast = self.pop()
            for test in tests:
                if test(ast):
                    return True

            return False

        def check_all(self):
            status = True
            while len(self.tests_ast_stack) != 0 and status:
                status = self.check()
            return status

        def push(self, tests: List[Callable[[Any], bool]], ast: Any) -> None:
            self.tests_ast_stack.append((tests, ast))

        def pop(self):
            return self.tests_ast_stack.pop()

    class ResourceChecker(Checker):
        def __init__(
            self, atomic_unit: AtomicUnit, source: List[str], ast: Any
        ) -> None:
            super().__init__(source)
            self.push([self.is_block_resource, self.is_inline_resource], ast)
            self.atomic_unit = atomic_unit

        def is_block_resource(self, ast: Any) -> bool:
            if (
                ChefParser._check_node(ast, ["method_add_block"], 2)
                and ChefParser._check_node(ast.args[0], ["command"], 2)
                and ChefParser._check_node(ast.args[1], ["do_block"], 1)
            ):
                self.push([self.is_resource_body], ast.args[1])
                self.push([self.is_resource_def], ast.args[0])
                self.atomic_unit.code = ChefParser._get_content(ast, self.source)
                self.atomic_unit.line = ChefParser._get_content_bounds(
                    ast, self.source
                )[0]
                return True
            return False

        def is_inline_resource(self, ast: Any) -> bool:
            if (
                ChefParser._check_node(ast, ["command"], 2)
                and ChefParser._check_id(ast.args[0], ["@ident"])
                and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)
            ):
                self.push(
                    [
                        self.is_resource_body_without_attributes,
                        self.is_inline_resource_name,
                    ],
                    ast.args[1],
                )
                self.push([self.is_resource_type], ast.args[0])
                self.atomic_unit.code = ChefParser._get_content(ast, self.source)
                self.atomic_unit.line = ChefParser._get_content_bounds(
                    ast, self.source
                )[0]
                return True
            return False

        def is_resource_def(self, ast: Any) -> bool:
            if ChefParser._check_node(
                ast.args[0], ["@ident"], 2
            ) and ChefParser._check_node(ast.args[1], ["args_add_block"], 2):
                self.push([self.is_resource_name], ast.args[1])
                self.push([self.is_resource_type], ast.args[0])
                return True
            return False

        def is_resource_type(self, ast: "ChefParser.Node") -> bool:
            if (
                isinstance(ast.args[0], str)
                and isinstance(ast.args[1], list)
                and not ast.args[0]
                in [
                    "action",
                    "converge_by",
                    "include_recipe",
                    "deprecated_property_alias",
                ]
            ):
                if ast.args[0] == "define":
                    return False
                self.atomic_unit.type = ast.args[0]
                return True
            return False

        def is_resource_name(self, ast: "ChefParser.Node") -> bool:
            if ChefParser._check_id(ast, ["args_add_block"]) and ast.args[1] is False:
                resource_id = ast.args[0]
                self.atomic_unit.name = ChefParser._get_content(
                    resource_id, self.source
                )
                return True
            return False

        def is_inline_resource_name(self, ast: "ChefParser.Node") -> bool:
            if (
                ChefParser._check_node(ast.args[0].args[0], ["method_add_block"], 2)
                and ast.args[1] is False
            ):
                resource_id = ast.args[0].args[0].args[0]
                self.atomic_unit.name = ChefParser._get_content(
                    resource_id, self.source
                )
                self.push([self.is_attribute], ast.args[0].args[0].args[1])
                return True
            return False

        def is_resource_body(self, ast: "ChefParser.Node") -> bool:
            if ChefParser._check_id(ast.args[0], ["bodystmt"]):
                self.push([self.is_attribute], ast.args[0].args[0])
                return True
            return False

        def is_resource_body_without_attributes(self, ast: "ChefParser.Node") -> bool:
            if (
                ChefParser._check_id(ast.args[0].args[0], ["string_literal"])
                and ast.args[1] is False
            ):
                self.atomic_unit.name = ChefParser._get_content(
                    ast.args[0].args[0], self.source
                )
                return True
            return False

        def is_attribute(self, ast: Any) -> bool:
            if ChefParser._check_node(
                ast, ["method_add_arg"], 2
            ) and ChefParser._check_id(ast.args[0], ["call"]):
                self.push([self.is_attribute], ast.args[0].args[0])
            elif (
                ChefParser._check_id(ast, ["command", "method_add_arg"])
                and ast.args[1] != []
            ) or (
                ChefParser._check_id(ast, ["method_add_block"])
                and ChefParser._check_id(ast.args[0], ["method_add_arg"])
                and ChefParser._check_id(ast.args[1], ["brace_block", "do_block"])
            ):
                value = ChefParser._get_value(ast.args[1], self.source)
                assert value is not None
                info = ChefParser._get_info(ast, self.source)

                a = Attribute(
                    ChefParser._get_content(ast.args[0], self.source),
                    value,
                    info,
                )
                self.atomic_unit.add_attribute(a)
            elif isinstance(ast, (ChefParser.Node, list)):
                for arg in reversed(ast):  # type: ignore
                    self.push([self.is_attribute], arg)

            return True

    class VariableChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.variables: List[Variable] = []
            self.push([self.is_variable], ast)

        def is_variable(self, ast: Any) -> bool:
            def create_variable(
                key: Any,
                value_ast: Any,
                name: str,
                value: Expr,
            ):
                bounds = ChefParser._get_content_bounds(key, self.source)
                bounds_value = ChefParser._get_content_bounds(value_ast, self.source)

                code = ChefParser._get_content(key, self.source)
                variable = Variable(
                    name,
                    value,
                    ElementInfo(
                        bounds[0],
                        bounds[1] + 1,
                        bounds_value[2],
                        # We are considering a start at 0 and the index to be inclusive
                        # so we need to add 2 to the end column since
                        # we want it to start at 1 and be exclusive
                        bounds_value[3] + 2,
                        code,
                    ),
                )
                return variable

            def handle_assign_node(name_ast: Any, value_ast: Any):
                name = ChefParser._get_content(name_ast, self.source)
                value = ChefParser._get_value(value_ast, self.source)
                assert value is not None
                variable = create_variable(name_ast, ast, name, value)
                self.variables.append(variable)

            if ChefParser._check_node(ast, ["assign", "massign"], 2):
                handle_assign_node(ast.args[0], ast.args[1])
                return True
            elif ChefParser._check_node(ast, ["opassign"], 3):
                handle_assign_node(ast.args[0], ast.args[2])
                name = ChefParser._get_value(ast.args[0], self.source)
                assert name is not None
                op = ast.args[1].args[0]

                def binary(type: Callable[[ElementInfo, Expr, Expr], Expr]) -> Expr:
                    return type(
                        ElementInfo.from_code_element(self.variables[-1]),
                        name,
                        self.variables[-1].value,
                    )

                match op:
                    case "||=":
                        value = ChefParser._get_value(ast.args[0], self.source)
                        assert isinstance(value, Expr)
                        cond = NotEqual(
                            ElementInfo.from_code_element(self.variables[-1]),
                            value,
                            Null(),
                        )
                        true = ConditionalStatement(
                            cond, ConditionalStatement.ConditionType.IF
                        )
                        true.add_statement(value)
                        false = ConditionalStatement(
                            Null(),
                            ConditionalStatement.ConditionType.IF,
                            is_default=True,
                        )
                        false.add_statement(name)
                        true.else_statement = false
                        self.variables[-1].value = true
                    case "+=":
                        self.variables[-1].value = binary(Sum)
                    case "-=":
                        self.variables[-1].value = binary(Subtract)
                    case "*=":
                        self.variables[-1].value = binary(Multiply)
                    case "/=":
                        self.variables[-1].value = binary(Divide)
                    case "%=":
                        self.variables[-1].value = binary(Modulo)
                    case "**=":
                        self.variables[-1].value = binary(Power)
                    case _:
                        raise ValueError(f"Unknown operator {op}")

                return True

            return False

    class IncludeChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.push([self.is_include], ast)
            self.code = ""

        def is_include(self, ast: Any) -> bool:
            if (
                ChefParser._check_node(ast, ["command"], 2)
                and ChefParser._check_id(ast.args[0], ["@ident"])
                and ChefParser._check_node(ast.args[1], ["args_add_block"], 2)
            ):
                self.push([self.is_include_name], ast.args[1])
                self.push([self.is_include_type], ast.args[0])
                self.code = ChefParser._get_content(ast, self.source)
                return True
            return False

        def is_include_type(self, ast: "ChefParser.Node") -> bool:
            if (
                isinstance(ast.args[0], str)
                and isinstance(ast.args[1], list)
                and ast.args[0] == "include_recipe"
            ):
                return True
            return False

        def is_include_name(self, ast: "ChefParser.Node") -> bool:
            if (
                ChefParser._check_id(ast.args[0].args[0], ["string_literal"])
                and ast.args[1] is False
            ):
                d = Dependency([ChefParser._get_content(ast.args[0][0], self.source)])
                d.line = ChefParser._get_content_bounds(ast, self.source)[0]
                d.code = self.code
                self.include = d
                return True
            return False

    class CaseChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.current_condition = None
            self.condition = None
            self.push([self.is_case], ast)

        def is_case(self, ast: Any) -> bool:
            if ChefParser._check_node(ast, ["case"], 2):
                case_head = ChefParser._get_value(ast.args[0], self.source)
                assert isinstance(case_head, Expr)
                self.case_head: Expr = case_head
                self.current_condition = None
                self.push([self.is_case_condition], ast.args[1])
                return True
            elif ChefParser._check_node(ast, ["case"], 1):
                self.case_head = Null()
                self.current_condition = None
                self.push([self.is_case_condition], ast.args[0])
                return True
            return False

        def is_case_condition(self, ast: Any) -> bool:
            if ChefParser._check_node(ast, ["when", "in"], 3) or ChefParser._check_node(
                ast, ["when", "in"], 2
            ):
                info = ChefParser._get_info(ast, self.source)
                value = ChefParser._get_value(ast.args[0], self.source)
                assert isinstance(value, Expr)

                if self.condition is None:
                    self.condition = ConditionalStatement(
                        Equal(info, self.case_head, value),
                        ConditionalStatement.ConditionType.SWITCH,
                    )
                    self.condition.code = ChefParser._get_content(ast, self.source)
                    self.condition.line = ChefParser._get_content_bounds(
                        ast, self.source
                    )[0]
                    self.current_condition = self.condition
                elif self.current_condition is not None:
                    self.current_condition.else_statement = ConditionalStatement(
                        Equal(info, self.case_head, value),
                        ConditionalStatement.ConditionType.SWITCH,
                    )
                    self.current_condition = self.current_condition.else_statement
                    self.current_condition.code = ChefParser._get_content(
                        ast, self.source
                    )
                    self.current_condition.line = ChefParser._get_content_bounds(
                        ast, self.source
                    )[0]
                if len(ast.args) == 3:
                    self.push([self.is_case_condition], ast.args[2])
                return True
            elif (
                ChefParser._check_node(ast, ["else"], 1)
                and self.current_condition is not None
            ):
                self.current_condition.else_statement = ConditionalStatement(
                    Null(), ConditionalStatement.ConditionType.SWITCH, is_default=True
                )
                self.current_condition.else_statement.code = ChefParser._get_content(
                    ast, self.source
                )
                self.current_condition.else_statement.line = (
                    ChefParser._get_content_bounds(ast, self.source)[0]
                )
                return True
            return False

    class IfChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.current_condition = None
            self.condition = None
            self.push([self.is_if], ast)

        def get_statements(self, ast: Any, cond: ConditionalStatement) -> None:
            assert self.condition is not None
            # Check blocks inside
            for arg in ast.args:
                if ChefParser._check_id(arg, ["stmts_add"]):
                    ChefParser._transverse_ast(arg, cond, self.source)

        def is_if(self, ast: Any) -> bool:
            if ChefParser._check_node(
                ast, ["if", "unless"], 2
            ) or ChefParser._check_node(ast, ["if", "unless"], 3):
                condition = ChefParser._get_value(ast.args[0], self.source)
                assert isinstance(condition, Expr)
                if ChefParser._check_id(ast, ["unless"]):
                    condition = Not(ElementInfo.from_code_element(condition), condition)
                self.condition = ConditionalStatement(
                    condition, ConditionalStatement.ConditionType.IF
                )
                self.condition.code = ChefParser._get_content(ast, self.source)
                self.condition.line = ChefParser._get_content_bounds(ast, self.source)[
                    0
                ]
                self.current_condition = self.condition
                if ChefParser._check_node(ast, ["if", "unless"], 3):
                    self.push([self.is_if_condition], ast.args[2])
                self.get_statements(ast, self.condition)
                return True
            return False

        def is_if_condition(self, ast: Any) -> bool:
            if (
                ChefParser._check_node(ast, ["elsif"], 2)
                or ChefParser._check_node(ast, ["elsif"], 3)
            ) and self.current_condition is not None:
                condition = ChefParser._get_value(ast.args[0], self.source)
                assert isinstance(condition, Expr)
                new_condition = ConditionalStatement(
                    condition, ConditionalStatement.ConditionType.IF
                )
                new_condition.code = ChefParser._get_content(ast, self.source)
                new_condition.line = ChefParser._get_content_bounds(ast, self.source)[0]
                self.get_statements(ast, new_condition)
                self.current_condition.else_statement = new_condition
                self.current_condition = new_condition
                if ChefParser._check_node(ast, ["elsif"], 3):
                    self.push([self.is_if_condition], ast.args[2])
                return True
            elif (
                ChefParser._check_node(ast, ["else"], 1)
                and self.current_condition is not None
            ):
                new_condition = ConditionalStatement(
                    Null(), ConditionalStatement.ConditionType.IF, is_default=True
                )
                new_condition.code = ChefParser._get_content(ast, self.source)
                new_condition.line = ChefParser._get_content_bounds(ast, self.source)[0]
                self.get_statements(ast, new_condition)
                self.current_condition.else_statement = new_condition
                return True
            return False

    class ClassChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.push([self.is_class], ast)
            self.unit_block = None

        def is_class(self, ast: Any) -> bool:
            if ChefParser._check_node(
                ast, ["class", "sclass"], 2
            ) or ChefParser._check_node(ast, ["class"], 3):
                name = ChefParser._get_content(ast.args[0], self.source)
                self.class_name = name
                self.unit_block = UnitBlock(name, UnitBlockType.definition)
                if len(ast.args) == 2:
                    self.push([self.is_class_body], ast.args[1])
                else:
                    self.push([self.is_class_body], ast.args[2])
                return True
            return False

        def is_class_body(self, ast: Any) -> bool:
            if ChefParser._check_id(ast, ["bodystmt"]):
                assert self.unit_block is not None
                ChefParser._transverse_ast(ast, self.unit_block, self.source)
                return True
            return False

    class DefChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.push([self.is_def], ast)
            self.unit_block = None

        def is_def(self, ast: Any) -> bool:
            if ChefParser._check_node(ast, ["def"], 2) or ChefParser._check_node(
                ast, ["def"], 3
            ):
                name = ChefParser._get_content(ast.args[0], self.source)
                self.unit_block = UnitBlock(name, UnitBlockType.definition)
                if len(ast.args) == 2:
                    self.push([self.is_def_body], ast.args[1])
                else:
                    self.push([self.is_def_body], ast.args[2])
                return True
            elif ChefParser._check_node(ast, ["defs"], 4) or ChefParser._check_node(
                ast, ["defs"], 5
            ):
                target = ChefParser._get_content(ast.args[0], self.source)
                op = ChefParser._get_content(ast.args[1], self.source)
                method = ChefParser._get_content(ast.args[2], self.source)
                name = target + op + method
                self.unit_block = UnitBlock(name, UnitBlockType.definition)
                if len(ast.args) == 4:
                    self.push([self.is_def_body], ast.args[3])
                else:
                    self.push([self.is_def_body], ast.args[4])
                return True

            return False

        def is_def_body(self, ast: Any) -> bool:
            if ChefParser._check_id(ast, ["bodystmt"]):
                assert self.unit_block is not None
                ChefParser._transverse_ast(ast, self.unit_block, self.source)
                return True
            return False

    class ModuleChecker(Checker):
        def __init__(self, source: List[str], ast: Any) -> None:
            super().__init__(source)
            self.push([self.is_module], ast)
            self.unit_block = None

        def is_module(self, ast: Any) -> bool:
            if ChefParser._check_node(ast, ["module"], 2):
                name = ChefParser._get_content(ast.args[0], self.source)
                self.unit_block = UnitBlock(name, UnitBlockType.block)
                self.push([self.is_module_body], ast.args[1])
                return True

            return False

        def is_module_body(self, ast: Any) -> bool:
            if ChefParser._check_id(ast, ["bodystmt"]):
                assert self.unit_block is not None
                ChefParser._transverse_ast(ast, self.unit_block, self.source)
                return True
            return False

    @staticmethod
    def __create_ast(l: List[ChefValue | "ChefParser.Node"]) -> "ChefParser.Node":
        args: List[Any] = []
        for el in l[1:]:
            if isinstance(el, list):
                if len(el) > 0 and isinstance(el[0], tuple) and el[0][0] == "id":
                    args.append(ChefParser.__create_ast(el))  # type: ignore
                else:
                    arg: List["ChefParser.Node" | ChefValue] = []
                    for e in el:
                        if (
                            isinstance(e, list)
                            and isinstance(e[0], tuple)
                            and e[0][0] == "id"
                        ):
                            arg.append(ChefParser.__create_ast(e))  # type: ignore
                        else:
                            arg.append(e)
                    args.append(arg)
            else:
                args.append(el)

        return ChefParser.Node(l[0][1], args)  # type: ignore

    @staticmethod
    def _transverse_ast(
        ast: Any, st: UnitBlock | ConditionalStatement, source: List[str]
    ) -> None:
        if isinstance(ast, list):
            for arg in ast:  # type: ignore
                if isinstance(arg, (ChefParser.Node, list)):
                    ChefParser._transverse_ast(arg, st, source)
        else:
            resource_checker = ChefParser.ResourceChecker(
                AtomicUnit("", ""), source, ast
            )
            if resource_checker.check_all():
                if isinstance(st, UnitBlock):
                    st.add_atomic_unit(resource_checker.atomic_unit)
                else:
                    st.add_statement(resource_checker.atomic_unit)
                return

            variable_checker = ChefParser.VariableChecker(source, ast)
            if variable_checker.check_all():
                for variable in variable_checker.variables:
                    if isinstance(st, UnitBlock):
                        st.add_variable(variable)
                    else:
                        st.add_statement(variable)
                return

            include_checker = ChefParser.IncludeChecker(source, ast)
            if include_checker.check_all():
                if isinstance(st, UnitBlock):
                    st.add_dependency(include_checker.include)
                else:
                    st.add_statement(include_checker.include)
                return

            if_checkers = [
                ChefParser.CaseChecker(source, ast),
                ChefParser.IfChecker(source, ast),
            ]
            for if_checker in if_checkers:
                if if_checker.check_all():
                    if if_checker.condition is not None:
                        st.add_statement(if_checker.condition)
                        return

            block_checkers = [
                ChefParser.ClassChecker(source, ast),
                ChefParser.DefChecker(source, ast),
                ChefParser.ModuleChecker(source, ast),
            ]
            for checker in block_checkers:
                if checker.check_all():
                    assert checker.unit_block is not None
                    if isinstance(st, UnitBlock):
                        st.add_unit_block(checker.unit_block)
                    else:
                        st.add_statement(checker.unit_block)
                    return

            for arg in ast.args:
                if isinstance(arg, (ChefParser.Node, list)):
                    ChefParser._transverse_ast(arg, st, source)

    @staticmethod
    def __parse_recipe(path: str, file: str) -> UnitBlock | None:
        with open(os.path.join(path, file)) as f:
            ripper = resource_filename(
                "glitch.parsers", "resources/comments.rb.template"
            )
            ripper = open(ripper, "r")
            ripper_script = Template(ripper.read())
            ripper.close()
            ripper_script = ripper_script.substitute(
                {"path": '"' + os.path.join(path, file) + '"'}
            )

            if "/attributes/" in path:
                unit_block: UnitBlock = UnitBlock(file, UnitBlockType.vars)
            else:
                unit_block: UnitBlock = UnitBlock(file, UnitBlockType.script)
            unit_block.path = os.path.join(path, file)

            try:
                source = f.readlines()
            except:
                throw_exception(
                    EXCEPTIONS["CHEF_COULD_NOT_PARSE"], os.path.join(path, file)
                )
                return None

            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                tmp.write(ripper_script)
                tmp.flush()

                try:
                    p = os.popen("ruby " + tmp.name)
                    script_ast = p.read()
                    p.close()
                    comments, _ = parser_yacc(script_ast)
                    if comments is not None:
                        comments.reverse()

                    for comment, line in comments:
                        c = Comment(re.sub(r"\\n$", "", comment))
                        c.code = source[line - 1]
                        c.line = line
                        unit_block.add_comment(c)
                except:
                    throw_exception(
                        EXCEPTIONS["CHEF_COULD_NOT_PARSE"], os.path.join(path, file)
                    )
                    return None

            try:
                p = os.popen(
                    "ruby -r ripper -e 'file = \
                    File.open(\""
                    + os.path.join(path, file)
                    + "\")\npp Ripper.sexp_raw(file)'"
                )
                script_ast = p.read()
                p.close()
                _, program = parser_yacc(script_ast)
                ast = ChefParser.__create_ast(program)
                ChefParser._transverse_ast(ast, unit_block, source)
            except:
                throw_exception(
                    EXCEPTIONS["CHEF_COULD_NOT_PARSE"], os.path.join(path, file)
                )
                return None

            return unit_block

    def parse_module(self, path: str) -> Module:
        def parse_folder(path: str) -> None:
            if os.path.exists(path):
                files = [
                    f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
                ]
                for file in files:
                    recipe = self.__parse_recipe(path, file)
                    if recipe is not None:
                        res.add_block(recipe)

        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        parse_folder(path + "/resources/")
        parse_folder(path + "/recipes/")
        parse_folder(path + "/attributes/")
        parse_folder(path + "/definitions/")
        parse_folder(path + "/libraries/")
        parse_folder(path + "/providers/")

        return res

    def parse_file(self, path: str, type: UnitBlockType) -> UnitBlock | None:
        return self.__parse_recipe(os.path.dirname(path), os.path.basename(path))

    def parse_folder(self, path: str) -> Project:
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        res.add_module(self.parse_module(path))

        if os.path.exists(f"{path}/cookbooks"):
            cookbooks = [
                f.path
                for f in os.scandir(f"{path}/cookbooks")
                if f.is_dir() and not f.is_symlink()
            ]
            for cookbook in cookbooks:
                res.add_module(self.parse_module(cookbook))

        subfolders = [
            f.path for f in os.scandir(f"{path}") if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not in [
                "cookbooks",
                "resources",
                "attributes",
                "recipes",
                "definitions",
                "libraries",
                "providers",
            ]:
                aux = self.parse_folder(d)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res
