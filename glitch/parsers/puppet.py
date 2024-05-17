import os
import re
import traceback
import copy
from puppetparser.parser import parse as parse_puppet  # type: ignore
import puppetparser.model as puppetmodel  # type: ignore
from glitch.exceptions import EXCEPTIONS, throw_exception

import glitch.parsers.parser as p
from glitch.repr.inter import *
from typing import List, Any, Dict, Callable


class PuppetParser(p.Parser):
    @staticmethod
    def __process_unitblock_component(
        ce: CodeElement | List[CodeElement], unit_block: UnitBlock
    ) -> None:
        def get_var(parent_name: str, vars: List[KeyValue]):
            for var in vars:
                if var.name == parent_name:
                    return var
            return None

        def add_variable_to_unit_block(
            variable: KeyValue, unit_block_vars: List[KeyValue]
        ) -> None:
            var_name = variable.name
            var = get_var(var_name, unit_block_vars)
            if var and isinstance(var.value, Null) and isinstance(variable.value, Null):
                for v in variable.keyvalues:
                    add_variable_to_unit_block(v, var.keyvalues)
            else:
                unit_block_vars.append(variable)

        if isinstance(ce, Dependency):
            unit_block.add_dependency(ce)
        elif isinstance(ce, Variable):
            add_variable_to_unit_block(ce, unit_block.variables)  # type: ignore
        elif isinstance(ce, AtomicUnit):
            unit_block.add_atomic_unit(ce)
        elif isinstance(ce, UnitBlock):
            unit_block.add_unit_block(ce)
        elif isinstance(ce, Attribute):
            unit_block.add_attribute(ce)
        elif isinstance(ce, ConditionalStatement):
            unit_block.add_statement(ce)
        elif isinstance(ce, UnitBlock):
            unit_block.add_unit_block(ce)
        elif isinstance(ce, list):
            for c in ce:
                PuppetParser.__process_unitblock_component(c, unit_block)

    @staticmethod
    def __get_code(ce: puppetmodel.CodeElement, code: List[str]) -> str:
        if ce.line == ce.end_line:
            res = code[ce.line - 1][max(0, ce.col - 1) : ce.end_col - 1]
        else:
            res = code[ce.line - 1]

        for line in range(ce.line, ce.end_line - 1):
            res += code[line]

        if ce.line != ce.end_line:
            res += code[ce.end_line - 1][: ce.end_col - 1]

        return res

    @staticmethod
    def __get_info(ce: puppetmodel.CodeElement, code: List[str]) -> ElementInfo:
        return ElementInfo(
            ce.line, ce.col, ce.end_line, ce.end_col, PuppetParser.__get_code(ce, code)
        )

    @staticmethod
    def __process_string_value(
        codeelement: puppetmodel.Value[str], path: str, code: List[str]
    ):
        def fix_info(e: CodeElement, line: int, col: int):
            e.line = line
            e.end_line = line
            e.column = e.column + col
            e.end_column = e.end_column + col
            for _, value in e.__dict__.items():
                if isinstance(value, CodeElement):
                    fix_info(value, line, col)

        interpolation = re.split(r"\$\{(.*?)\}", codeelement.value)
        if len(interpolation) == 1:
            return String(codeelement.value, PuppetParser.__get_info(codeelement, code))

        elements: List[Expr] = []
        info = PuppetParser.__get_info(codeelement, code)
        current_col = info.column

        for i in range(len(interpolation)):
            if i % 2 == 1:
                current_col += 2
                element, _ = parse_puppet(interpolation[i])
                assert len(element) == 1
                expr = PuppetParser.__process_codeelement(
                    element[0],
                    path,
                    interpolation[i].split("\n"),
                )
                fix_info(expr, codeelement.line, current_col)
                assert isinstance(expr, Expr)
                elements.append(expr)
                current_col += len(interpolation[i]) + 2
            elif interpolation[i] != "":
                elements.append(String(interpolation[i], info))
                current_col += len(interpolation[i])

        if len(elements) == 1:
            return elements[0]

        result = Sum(
            ElementInfo(
                info.line,
                info.column,
                elements[1].end_line,
                elements[1].end_column,
                PuppetParser.__get_code(codeelement, code),
            ),
            elements[0],
            elements[1],
        )
        for i in range(2, len(elements)):
            result = Sum(
                ElementInfo(
                    result.line,
                    result.column,
                    elements[i].end_line,
                    elements[i].end_column,
                    result.code,
                ),
                result,
                elements[i],
            )

        return result

    @staticmethod
    def __process_value(
        codeelement: puppetmodel.Value[Any], path: str, code: List[str]
    ) -> Expr:
        if isinstance(codeelement, puppetmodel.Hash):
            res_dict: Dict[Expr, Expr] = {}

            for key, value in codeelement.value.items():
                key = PuppetParser.__process_codeelement(key, path, code)
                value = PuppetParser.__process_codeelement(value, path, code)
                assert isinstance(key, Expr)
                assert isinstance(value, Expr)
                res_dict[key] = value

            return Hash(res_dict, PuppetParser.__get_info(codeelement, code))
        elif isinstance(codeelement, puppetmodel.Array):
            res_list: List[Expr] = []
            for value in codeelement.value:
                value = PuppetParser.__process_codeelement(value, path, code)
                assert isinstance(value, Expr)
                res_list.append(value)

            return Array(res_list, PuppetParser.__get_info(codeelement, code))
        elif isinstance(codeelement, puppetmodel.Id):
            return VariableReference(
                codeelement.value, PuppetParser.__get_info(codeelement, code)
            )
        elif isinstance(codeelement.value, str):
            return PuppetParser.__process_string_value(codeelement, path, code)
        elif isinstance(codeelement.value, bool):
            return Boolean(
                codeelement.value, PuppetParser.__get_info(codeelement, code)
            )
        elif isinstance(codeelement.value, int):
            return Integer(
                codeelement.value, PuppetParser.__get_info(codeelement, code)
            )
        elif isinstance(codeelement.value, float):
            return Float(codeelement.value, PuppetParser.__get_info(codeelement, code))
        else:
            return Null(info=PuppetParser.__get_info(codeelement, code))

    @staticmethod
    def __process_string(codeelement: puppetmodel.CodeElement | None) -> str:
        if codeelement is None:
            return ""
        elif isinstance(codeelement, puppetmodel.Value) and isinstance(codeelement.value, str):  # type: ignore
            return codeelement.value

        raise ValueError(f"Unsupported code element: {codeelement}")

    @staticmethod
    def __process_expr(
        codeelement: puppetmodel.CodeElement, path: str, code: List[str]
    ) -> Expr:
        expr = PuppetParser.__process_codeelement(codeelement, path, code)
        assert isinstance(expr, Expr)
        return expr

    @staticmethod
    def __process_conditional(
        codeelement: puppetmodel.If | puppetmodel.Unless, path: str, code: List[str]
    ) -> ConditionalStatement:
        if codeelement.condition is not None:
            condition = PuppetParser.__process_codeelement(
                codeelement.condition, path, code
            )
            assert isinstance(condition, Expr)
        else:
            condition = Null()

        condition_statement = ConditionalStatement(
            condition, ConditionalStatement.ConditionType.IF
        )

        for statement in codeelement.block:
            ce = PuppetParser.__process_codeelement(statement, path, code)
            condition_statement.add_statement(ce)

        if codeelement.elseblock is not None:
            else_statement = PuppetParser.__process_codeelement(
                codeelement.elseblock, path, code
            )
            assert isinstance(else_statement, ConditionalStatement)
            condition_statement.else_statement = else_statement

        return condition_statement

    @staticmethod
    def __process_dependency(
        codeelement: puppetmodel.Include | puppetmodel.Require | puppetmodel.Contain,
        path: str,
        code: List[str],
    ) -> Dependency:
        if isinstance(codeelement, puppetmodel.Include):
            deps = codeelement.inc
        elif isinstance(codeelement, puppetmodel.Require):
            deps = codeelement.req
        else:
            deps = codeelement.cont

        dependencies: List[str] = []
        for dep in deps:
            d = PuppetParser.__process_string(dep)
            dependencies.append(d)

        d = Dependency(dependencies)
        d.line, d.column = codeelement.line, codeelement.col
        d.code = PuppetParser.__get_code(codeelement, code)
        return d

    @staticmethod
    def __process_case_statement(
        codeelement: puppetmodel.Case, path: str, code: List[str]
    ) -> ConditionalStatement:
        control = PuppetParser.__process_codeelement(codeelement.control, path, code)
        assert isinstance(control, Expr)

        conditional_statements: List[ConditionalStatement] = []
        for match in codeelement.matches:
            condition: Expr = Null()

            for expression in match.expressions:
                right = PuppetParser.__process_codeelement(expression, path, code)
                assert isinstance(right, Expr)

                if not isinstance(right, String) or right.value != "default":
                    if condition == Null():
                        condition = Equal(
                            ElementInfo.from_code_element(right), control, right
                        )
                    else:
                        condition = Or(
                            ElementInfo(
                                condition.line,
                                condition.column,
                                right.end_line,
                                right.end_column,
                                PuppetParser.__get_code(match, code),
                            ),
                            condition,
                            Equal(ElementInfo.from_code_element(right), control, right),
                        )

            if condition == Null():
                conditional_statement = ConditionalStatement(
                    Null(), ConditionalStatement.ConditionType.SWITCH, True
                )
            else:
                conditional_statement = ConditionalStatement(
                    condition,
                    ConditionalStatement.ConditionType.SWITCH,
                )

            conditional_statement.line, conditional_statement.column = (
                match.line,
                match.col,
            )
            conditional_statement.end_line, conditional_statement.end_column = (
                match.end_line,
                match.end_col,
            )
            conditional_statement.code = PuppetParser.__get_code(match, code)

            for statement in match.block:
                ce = PuppetParser.__process_codeelement(statement, path, code)
                conditional_statement.add_statement(ce)

            conditional_statements.append(conditional_statement)

        for i in range(1, len(conditional_statements)):
            conditional_statements[i - 1].else_statement = conditional_statements[i]

        return conditional_statements[0]

    @staticmethod
    def __process_selector(
        codeelement: puppetmodel.Selector, path: str, code: List[str]
    ):
        control = PuppetParser.__process_codeelement(codeelement.control, path, code)
        assert isinstance(control, Expr)

        conditional_statements: List[ConditionalStatement] = []
        for key_element, value_element in codeelement.hash.value.items():
            right = PuppetParser.__process_codeelement(key_element, path, code)
            assert isinstance(right, Expr)
            value = PuppetParser.__process_codeelement(value_element, path, code)

            if isinstance(right, String) and right.value == "default":
                conditional_statement = ConditionalStatement(
                    Null(), ConditionalStatement.ConditionType.SWITCH, True
                )
            else:
                condition = Equal(ElementInfo.from_code_element(right), control, right)
                conditional_statement = ConditionalStatement(
                    condition,
                    ConditionalStatement.ConditionType.SWITCH,
                )

            conditional_statement.line, conditional_statement.column = (
                key_element.line,
                key_element.col,
            )
            conditional_statement.end_line, conditional_statement.end_column = (
                value_element.end_line,
                value_element.end_col,
            )
            conditional_statement.code = PuppetParser.__get_code(
                key_element, code
            ) + PuppetParser.__get_code(value_element, code)

            conditional_statement.add_statement(value)
            conditional_statements.append(conditional_statement)

        for i in range(1, len(conditional_statements)):
            conditional_statements[i - 1].else_statement = conditional_statements[i]

        return conditional_statements[0]

    @staticmethod
    def __process_operation(
        codeelement: puppetmodel.Operation, path: str, code: List[str]
    ):
        def unary_operation(type: Callable[[ElementInfo, Expr], Expr]) -> Expr:
            return type(
                PuppetParser.__get_info(codeelement, code),
                PuppetParser.__process_expr(codeelement.arguments[0], path, code),
            )

        def binary_operation(type: Callable[[ElementInfo, Expr, Expr], Expr]) -> Expr:
            return type(
                PuppetParser.__get_info(codeelement, code),
                PuppetParser.__process_expr(codeelement.arguments[0], path, code),
                PuppetParser.__process_expr(codeelement.arguments[1], path, code),
            )

        if codeelement.operator == "==":
            return binary_operation(Equal)
        elif codeelement.operator == "!=":
            return binary_operation(NotEqual)
        elif codeelement.operator == "and":
            return binary_operation(And)
        elif codeelement.operator == "or":
            return binary_operation(Or)
        elif codeelement.operator == "!":
            return unary_operation(Not)
        elif codeelement.operator == "[,]":
            # FIXME: Not yet supported
            return Null()
        elif codeelement.operator == "<":
            return binary_operation(LessThan)
        elif codeelement.operator == ">":
            return binary_operation(GreaterThan)
        elif codeelement.operator == "<=":
            return binary_operation(LessThanOrEqual)
        elif codeelement.operator == ">=":
            return binary_operation(GreaterThanOrEqual)
        elif codeelement.operator == "~=":
            # FIXME: Not yet supported
            return Null()
        elif codeelement.operator == "!~":
            # FIXME: Not yet supported
            return Null()
        elif codeelement.operator == "in":
            return binary_operation(In)
        elif codeelement.operator == "-" and len(codeelement.arguments) == 1:
            return unary_operation(Minus)
        elif codeelement.operator == "-" and len(codeelement.arguments) == 2:
            return binary_operation(Subtract)
        elif codeelement.operator == "+":
            return binary_operation(Sum)
        elif codeelement.operator == "/":
            return binary_operation(Divide)
        elif codeelement.operator == "*" and len(codeelement.arguments) == 1:
            # FIXME: Not yet supported
            return Null()
        elif codeelement.operator == "*" and len(codeelement.arguments) == 2:
            return binary_operation(Multiply)
        elif codeelement.operator == "%":
            return binary_operation(Modulo)
        elif codeelement.operator == ">>":
            return binary_operation(RightShift)
        elif codeelement.operator == "<<":
            return binary_operation(LeftShift)
        elif codeelement.operator == "[]" and len(codeelement.arguments) == 2:
            return binary_operation(Access)

        raise ValueError(f"Unsupported operation: {codeelement.operator}")

    @staticmethod
    def __process_unitblock(
        codeelement: puppetmodel.PuppetClass
        | puppetmodel.Node
        | puppetmodel.Function
        | puppetmodel.ResourceDeclaration,
        path: str,
        code: List[str],
        type: UnitBlockType,
    ) -> UnitBlock:
        unit_block: UnitBlock = UnitBlock(codeelement.name, type)

        if isinstance(codeelement, puppetmodel.Function):
            block = codeelement.body
        else:
            block = codeelement.block

        for ce in list(
            map(
                lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                block,
            )
        ):
            PuppetParser.__process_unitblock_component(ce, unit_block)

        unit_block.line, unit_block.column = codeelement.line, codeelement.col
        unit_block.code = PuppetParser.__get_code(codeelement, code)
        return unit_block

    @staticmethod
    def __process_codeelement(
        codeelement: puppetmodel.CodeElement, path: str, code: List[str]
    ) -> CodeElement:
        if isinstance(codeelement, puppetmodel.Value):
            return PuppetParser.__process_value(codeelement, path, code)  # type: ignore
        elif isinstance(codeelement, puppetmodel.Attribute):
            name = PuppetParser.__process_string(codeelement.key)
            value = PuppetParser.__process_codeelement(codeelement.value, path, code)
            assert isinstance(value, Expr)

            attribute = Attribute(
                name, value, PuppetParser.__get_info(codeelement, code)
            )
            return attribute
        elif isinstance(codeelement, puppetmodel.Resource):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_string(codeelement.title),
                PuppetParser.__process_string(codeelement.type),
            )
            for attr in codeelement.attributes:
                attr = PuppetParser.__process_codeelement(attr, path, code)
                assert isinstance(attr, Attribute)
                resource.add_attribute(attr)
            resource.line, resource.column = codeelement.line, codeelement.col
            resource.code = PuppetParser.__get_code(codeelement, code)
            return resource
        elif isinstance(codeelement, puppetmodel.ClassAsResource):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_string(codeelement.title), 
                "class"
            )
            for attr in codeelement.attributes:
                attr = PuppetParser.__process_codeelement(attr, path, code)
                assert isinstance(attr, Attribute)
                resource.add_attribute(attr)
            resource.line, resource.column = codeelement.line, codeelement.col
            resource.code = PuppetParser.__get_code(codeelement, code)
            return resource
        elif isinstance(codeelement, puppetmodel.ResourceDeclaration):
            unit_block: UnitBlock = PuppetParser.__process_unitblock(
                codeelement, path, code, UnitBlockType.definition
            )
            unit_block.path = path

            for p in codeelement.parameters:
                attr = PuppetParser.__process_codeelement(p, path, code)
                assert isinstance(attr, Attribute)
                unit_block.add_attribute(attr)

            return unit_block
        elif isinstance(codeelement, puppetmodel.Parameter):
            if codeelement.default is not None:
                value = PuppetParser.__process_codeelement(
                    codeelement.default, path, code
                )
                assert isinstance(value, Expr)
            else:
                value = Null()

            attribute = Attribute(
                codeelement.name, value, PuppetParser.__get_info(codeelement, code)
            )

            return attribute
        elif isinstance(codeelement, puppetmodel.Assignment):
            name = PuppetParser.__process_string(codeelement.name)
            value = PuppetParser.__process_codeelement(codeelement.value, path, code)
            assert isinstance(value, Expr)

            variable: Variable = Variable(
                name, value, PuppetParser.__get_info(codeelement, code)
            )
            return variable
        elif isinstance(codeelement, puppetmodel.PuppetClass):
            # FIXME there are components of the class that are not considered
            unit_block = PuppetParser.__process_unitblock(
                codeelement, path, code, UnitBlockType.definition
            )
            unit_block.path = path

            for p in codeelement.parameters:
                attr = PuppetParser.__process_codeelement(p, path, code)
                assert isinstance(attr, Attribute)
                unit_block.add_attribute(attr)

            return unit_block
        elif isinstance(codeelement, puppetmodel.Node):
            unit_block = PuppetParser.__process_unitblock(
                codeelement, path, code, UnitBlockType.block
            )
            unit_block.name = "node"
            return unit_block
        elif isinstance(codeelement, puppetmodel.Operation):
            return PuppetParser.__process_operation(codeelement, path, code)
        elif isinstance(codeelement, puppetmodel.Lambda):
            # FIXME Lambdas are not yet supported
            return Null()
        elif isinstance(codeelement, puppetmodel.FunctionCall):
            name = PuppetParser.__process_string(codeelement.name)

            args: List[Expr] = []
            for arg in codeelement.arguments:
                arg = PuppetParser.__process_codeelement(arg, path, code)
                assert isinstance(arg, Expr)
                args.append(arg)

            if codeelement.lamb is not None:
                lamb = PuppetParser.__process_codeelement(codeelement.lamb, path, code)
                assert isinstance(lamb, Expr)
                args.append(lamb)

            return FunctionCall(name, args, PuppetParser.__get_info(codeelement, code))
        elif isinstance(codeelement, puppetmodel.If):
            return PuppetParser.__process_conditional(codeelement, path, code)
        elif isinstance(codeelement, puppetmodel.Unless):
            conditional = PuppetParser.__process_conditional(codeelement, path, code)
            conditional.condition = Not(
                ElementInfo.from_code_element(conditional.condition),
                conditional.condition,
            )
            return conditional
        elif isinstance(
            codeelement, (puppetmodel.Include, puppetmodel.Require, puppetmodel.Contain)
        ):
            return PuppetParser.__process_dependency(codeelement, path, code)
        elif isinstance(
            codeelement,
            (puppetmodel.Debug, puppetmodel.Fail, puppetmodel.Realize, puppetmodel.Tag),
        ):
            # FIXME Ignored unsupported concepts
            return Null()
        elif isinstance(codeelement, puppetmodel.Match):
            raise ValueError("Matches should only appear in case statements")
        elif isinstance(codeelement, puppetmodel.Case):
            return PuppetParser.__process_case_statement(codeelement, path, code)
        elif isinstance(codeelement, puppetmodel.Selector):
            return PuppetParser.__process_selector(codeelement, path, code)
        elif isinstance(codeelement, puppetmodel.Reference):
            # FIXME: Reference not yet supported
            return Null()
        elif isinstance(codeelement, puppetmodel.Function):
            unit_block: UnitBlock = PuppetParser.__process_unitblock(
                codeelement, path, code, UnitBlockType.function
            )

            for p in codeelement.parameters:
                attr = PuppetParser.__process_codeelement(p, path, code)
                assert isinstance(attr, Attribute)
                unit_block.add_attribute(attr)

            return unit_block
        elif isinstance(codeelement, puppetmodel.ResourceCollector):
            # FIXME: Resource collectors not yet supported
            return Null()
        elif isinstance(codeelement, puppetmodel.ResourceExpression):
            unit_block = UnitBlock("resource_expression", UnitBlockType.block)
            unit_block.line, unit_block.column = codeelement.line, codeelement.col
            unit_block.code = PuppetParser.__get_code(codeelement, code)
            unit_block.end_line, unit_block.end_column = (
                codeelement.end_line,
                codeelement.end_col,
            )

            default_attributes: Dict[str, Attribute] = {}
            if codeelement.default is not None:
                default = PuppetParser.__process_codeelement(
                    codeelement.default, path, code
                )
                assert isinstance(default, AtomicUnit)
                for attr in default.attributes:
                    default_attributes[attr.name] = attr

            for rsc in codeelement.resources:
                resources: List[puppetmodel.Resource | puppetmodel.ClassAsResource] = []
                if isinstance(rsc.title, puppetmodel.Array):
                    for t in rsc.title.value:
                        r = copy.deepcopy(rsc)
                        assert isinstance(t, puppetmodel.Value)
                        r.title = t
                        resources.append(r)
                else:
                    resources.append(rsc)
                
                for rsc in resources:
                    au = PuppetParser.__process_codeelement(rsc, path, code)
                    assert isinstance(au, AtomicUnit)
                    attrs = list(map(lambda a: a.name, au.attributes))
                    # Add default attributes
                    for name, attr in default_attributes.items():
                        if name not in attrs:
                            au.add_attribute(attr)
                    unit_block.add_atomic_unit(au)

            return unit_block
        elif isinstance(codeelement, puppetmodel.Chaining):
            # FIXME: Chaining not yet supported
            return Null()

        raise ValueError(
            f"Unsupported code element: {codeelement} ({type(codeelement)})"
        )

    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                name_split = name.split(".")
                if len(name_split) == 2 and name_split[-1] == "pp":
                    res.add_block(
                        self.parse_file(os.path.join(root, name), UnitBlockType.script)
                    )

        return res

    def parse_file(self, path: str, type: UnitBlockType) -> UnitBlock:
        unit_block: UnitBlock = UnitBlock(os.path.basename(path), UnitBlockType.script)
        unit_block.path = path

        try:
            with open(path) as f:
                parsed_script, comments = parse_puppet(f.read())

                f.seek(0, 0)
                code = f.readlines()

                for c in comments:
                    comment = Comment(c.content)
                    comment.line = c.line
                    comment.code = "".join(code[c.line - 1 : c.end_line])
                    unit_block.add_comment(comment)

                for ce in parsed_script:
                    PuppetParser.__process_unitblock_component(
                        PuppetParser.__process_codeelement(ce, path, code),
                        unit_block,
                    )
        except Exception:
            traceback.print_exc()
            throw_exception(EXCEPTIONS["PUPPET_COULD_NOT_PARSE"], path)
        return unit_block

    def parse_folder(self, path: str) -> Project:
        res: Project = Project(os.path.basename(os.path.normpath(path)))

        if os.path.exists(f"{path}/modules") and not os.path.islink(f"{path}/modules"):
            subfolders = [
                f.path
                for f in os.scandir(f"{path}/modules")
                if f.is_dir() and not f.is_symlink()
            ]
            for m in subfolders:
                res.add_module(self.parse_module(m))

        for f in os.scandir(path):
            name_split = f.name.split(".")
            if f.is_file() and len(name_split) == 2 and name_split[-1] == "pp":
                res.add_block(self.parse_file(f.path, UnitBlockType.script))

        subfolders = [
            f.path for f in os.scandir(f"{path}") if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not in ["modules"]:
                aux = self.parse_folder(d)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res
