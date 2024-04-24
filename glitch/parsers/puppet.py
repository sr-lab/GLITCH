# type: ignore
# TODO: The file needs a refactor so the types make sense
import os
import traceback
from puppetparser.parser import parse as parse_puppet
import puppetparser.model as puppetmodel
from glitch.exceptions import EXCEPTIONS, throw_exception

import glitch.parsers.parser as p
from glitch.repr.inter import *
from typing import List, Any, Tuple, Dict


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
            if var and var.value == None and variable.value == None:
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
        elif isinstance(ce, list):
            for c in ce:
                PuppetParser.__process_unitblock_component(c, unit_block)

    @staticmethod
    def __process_codeelement(
        codeelement: puppetmodel.CodeElement, path: str, code: List[str]
    ):
        def get_code(ce: puppetmodel.CodeElement):
            if ce.line == ce.end_line:
                res = code[ce.line - 1][max(0, ce.col - 1) : ce.end_col - 1]
            else:
                res = code[ce.line - 1]

            for line in range(ce.line, ce.end_line - 1):
                res += code[line]

            if ce.line != ce.end_line:
                res += code[ce.end_line - 1][: ce.end_col - 1]

            return res

        def process_hash_value(
            name: str, temp_value: Any
        ) -> Tuple[str, Dict[str, Any]]:
            if "[" in name and "]" in name:
                start = name.find("[") + 1
                end = name.find("]")
                key_name = name[start:end]
                name_without_key = name[: start - 1] + name[end + 1 :]
                n, d = process_hash_value(name_without_key, temp_value)
                if d == {}:
                    d[key_name] = temp_value
                    return n, d
                else:
                    new_d: Dict[str, Any] = {}
                    new_d[key_name] = d
                    return n, new_d
            else:
                return name, {}

        if isinstance(codeelement, puppetmodel.Value):
            if isinstance(codeelement, puppetmodel.Hash):
                res = {}

                for key, value in codeelement.value.items():
                    res[
                        PuppetParser.__process_codeelement(key, path, code)
                    ] = PuppetParser.__process_codeelement(value, path, code)

                return res
            elif isinstance(codeelement, puppetmodel.Array):
                return str(
                    PuppetParser.__process_codeelement(codeelement.value, path, code)
                )
            elif codeelement.value is None:
                return ""
            return str(codeelement.value)
        elif isinstance(codeelement, puppetmodel.Attribute):
            name = PuppetParser.__process_codeelement(codeelement.key, path, code)
            temp_value = PuppetParser.__process_codeelement(
                codeelement.value, path, code
            )
            value = "" if temp_value == "undef" else temp_value
            has_variable = not isinstance(value, str) or value.startswith("$")
            attribute = Attribute(name, value, has_variable)
            attribute.line, attribute.column = codeelement.line, codeelement.col
            attribute.code = get_code(codeelement)
            return attribute
        elif isinstance(codeelement, puppetmodel.Resource):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_codeelement(codeelement.title, path, code),
                PuppetParser.__process_codeelement(codeelement.type, path, code),
            )
            for attr in codeelement.attributes:
                resource.add_attribute(
                    PuppetParser.__process_codeelement(attr, path, code)
                )
            resource.line, resource.column = codeelement.line, codeelement.col
            resource.code = get_code(codeelement)
            return resource
        elif isinstance(codeelement, puppetmodel.ClassAsResource):
            resource: AtomicUnit = AtomicUnit(
                PuppetParser.__process_codeelement(codeelement.title, path, code),
                "class",
            )
            for attr in codeelement.attributes:
                resource.add_attribute(
                    PuppetParser.__process_codeelement(attr, path, code)
                )
            resource.line, resource.column = codeelement.line, codeelement.col
            resource.code = get_code(codeelement)
            return resource
        elif isinstance(codeelement, puppetmodel.ResourceDeclaration):
            unit_block: UnitBlock = UnitBlock(
                PuppetParser.__process_codeelement(codeelement.name, path, code),
                UnitBlockType.block,
            )
            unit_block.path = path

            if codeelement.block is not None:
                for ce in list(
                    map(
                        lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                        codeelement.block,
                    )
                ):
                    PuppetParser.__process_unitblock_component(ce, unit_block)

            for p in codeelement.parameters:
                unit_block.add_attribute(
                    PuppetParser.__process_codeelement(p, path, code)
                )

            unit_block.line, unit_block.column = codeelement.line, codeelement.col
            unit_block.code = get_code(codeelement)

            return unit_block
        elif isinstance(codeelement, puppetmodel.Parameter):
            # FIXME Parameters are not yet supported
            name = PuppetParser.__process_codeelement(codeelement.name, path, code)
            if codeelement.default is not None:
                temp_value = PuppetParser.__process_codeelement(
                    codeelement.default, path, code
                )
                value = "" if temp_value == "undef" else temp_value
            else:
                value = None
            has_variable = (
                not isinstance(value, str)
                or temp_value.startswith("$")
                or codeelement.default is None
            )
            attribute = Attribute(name, value, has_variable)
            attribute.line, attribute.column = codeelement.line, codeelement.col
            attribute.code = get_code(codeelement)
            return attribute
        elif isinstance(codeelement, puppetmodel.Assignment):
            name = PuppetParser.__process_codeelement(codeelement.name, path, code)
            temp_value = PuppetParser.__process_codeelement(
                codeelement.value, path, code
            )
            if "[" in name and "]" in name:
                name, temp_value = process_hash_value(name, temp_value)
            if not isinstance(temp_value, dict):
                if codeelement.value is not None:
                    value = "" if temp_value == "undef" else temp_value
                else:
                    value = None
                has_variable = not isinstance(value, str) or value.startswith("$")
                variable: Variable = Variable(name, value, has_variable)
                variable.line, variable.column = codeelement.line, codeelement.col
                variable.code = get_code(codeelement)
                return variable
            else:
                variable: Variable = Variable(name, None, False)
                variable.line, variable.column = codeelement.line, codeelement.col
                variable.code = get_code(codeelement)
                for key, value in temp_value.items():
                    variable.keyvalues.append(
                        PuppetParser.__process_codeelement(
                            puppetmodel.Assignment(
                                codeelement.line,
                                codeelement.col,
                                codeelement.end_line,
                                codeelement.end_col,
                                key,
                                value,
                            ),
                            path,
                            code,
                        )
                    )

                return variable
        elif isinstance(codeelement, puppetmodel.PuppetClass):
            # FIXME there are components of the class that are not considered
            unit_block: UnitBlock = UnitBlock(
                PuppetParser.__process_codeelement(codeelement.name, path, code),
                UnitBlockType.block,
            )
            unit_block.path = path

            if codeelement.block is not None:
                for ce in list(
                    map(
                        lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                        codeelement.block,
                    )
                ):
                    PuppetParser.__process_unitblock_component(ce, unit_block)

            for p in codeelement.parameters:
                unit_block.add_attribute(
                    PuppetParser.__process_codeelement(p, path, code)
                )

            unit_block.line, unit_block.column = codeelement.line, codeelement.col
            unit_block.code = get_code(codeelement)
            return unit_block
        elif isinstance(codeelement, puppetmodel.Node):
            # FIXME Nodes are not yet supported
            if codeelement.block is not None:
                return list(
                    map(
                        lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                        codeelement.block,
                    )
                )
            else:
                return []
        elif isinstance(codeelement, puppetmodel.Operation):
            if len(codeelement.arguments) == 1:
                return codeelement.operator + PuppetParser.__process_codeelement(
                    codeelement.arguments[0], path, code
                )
            elif codeelement.operator == "[]":
                return (
                    PuppetParser.__process_codeelement(
                        codeelement.arguments[0], path, code
                    )
                    + "["
                    + ",".join(
                        PuppetParser.__process_codeelement(
                            codeelement.arguments[1], path, code
                        )
                    )
                    + "]"
                )
            elif len(codeelement.arguments) == 2:
                return (
                    str(
                        PuppetParser.__process_codeelement(
                            codeelement.arguments[0], path, code
                        )
                    )
                    + codeelement.operator
                    + str(
                        PuppetParser.__process_codeelement(
                            codeelement.arguments[1], path, code
                        )
                    )
                )
            elif codeelement.operator == "[,]":
                return (
                    PuppetParser.__process_codeelement(
                        codeelement.arguments[0], path, code
                    )
                    + "["
                    + PuppetParser.__process_codeelement(
                        codeelement.arguments[1], path, code
                    )
                    + ","
                    + PuppetParser.__process_codeelement(
                        codeelement.arguments[2], path, code
                    )
                    + "]"
                )
        elif isinstance(codeelement, puppetmodel.Lambda):
            # FIXME Lambdas are not yet supported
            if codeelement.block is not None:
                args = []
                for arg in codeelement.parameters:
                    attr = PuppetParser.__process_codeelement(arg, path, code)
                    variable = Variable(attr.name, "", True)
                    variable.line = arg.line
                    variable.column = arg.col
                    args.append(Variable(variable))
                return (
                    list(
                        map(
                            lambda ce: PuppetParser.__process_codeelement(
                                ce, path, code
                            ),
                            codeelement.block,
                        )
                    )
                    + args
                )
            else:
                return []
        elif isinstance(codeelement, puppetmodel.FunctionCall):
            # FIXME Function calls are not yet supported
            res = PuppetParser.__process_codeelement(codeelement.name, path, code) + "("
            for arg in codeelement.arguments:
                res += repr(PuppetParser.__process_codeelement(arg, path, code)) + ","
            res = res[:-1]
            res += ")"
            lamb = PuppetParser.__process_codeelement(codeelement.lamb, path, code)
            if lamb != "":
                return [res] + lamb
            else:
                return res
        elif isinstance(codeelement, puppetmodel.If):
            condition = PuppetParser.__process_codeelement(
                codeelement.condition, path, code
            )
            condition = ConditionalStatement(
                condition, ConditionalStatement.ConditionType.IF
            )
            body = list(
                map(
                    lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                    codeelement.block,
                )
            )
            for statement in body:
                # FIXME: this should probably be more general (e.g. recursive lists)
                if isinstance(statement, list):
                    for s in statement:
                        condition.add_statement(s)
                # Avoids unsupported concepts
                elif statement is not None:
                    condition.add_statement(statement)

            if codeelement.elseblock is not None:
                condition.else_statement = PuppetParser.__process_codeelement(
                    codeelement.elseblock, path, code
                )
            return condition
        elif isinstance(codeelement, puppetmodel.Unless):
            # FIXME Unless is not yet supported
            res = list(
                map(
                    lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                    codeelement.block,
                )
            )
            if codeelement.elseblock is not None:
                res += PuppetParser.__process_codeelement(
                    codeelement.elseblock, path, code
                )
            return res
        elif isinstance(codeelement, puppetmodel.Include):
            dependencies = []
            for inc in codeelement.inc:
                d = Dependency(PuppetParser.__process_codeelement(inc, path, code))
                d.line, d.column = codeelement.line, codeelement.col
                d.code = get_code(codeelement)
                dependencies.append(d)
            return dependencies
        elif isinstance(codeelement, puppetmodel.Require):
            dependencies = []
            for req in codeelement.req:
                d = Dependency(PuppetParser.__process_codeelement(req, path, code))
                d.line, d.column = codeelement.line, codeelement.col
                d.code = get_code(codeelement)
                dependencies.append(d)
            return dependencies
        elif isinstance(codeelement, puppetmodel.Contain):
            dependencies = []
            for cont in codeelement.cont:
                d = Dependency(PuppetParser.__process_codeelement(cont, path, code))
                d.line, d.column = codeelement.line, codeelement.col
                d.code = get_code(codeelement)
                dependencies.append(d)
            return dependencies
        elif isinstance(
            codeelement,
            (puppetmodel.Debug, puppetmodel.Fail, puppetmodel.Realize, puppetmodel.Tag),
        ):
            # FIXME Ignored unsupported concepts
            pass
        elif isinstance(codeelement, puppetmodel.Match):
            # FIXME Matches are not yet supported
            return [
                list(
                    map(
                        lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                        codeelement.block,
                    )
                )
            ]
        elif isinstance(codeelement, puppetmodel.Case):
            control = PuppetParser.__process_codeelement(
                codeelement.control, path, code
            )
            conditions = []

            for match in codeelement.matches:
                expressions = PuppetParser.__process_codeelement(
                    match.expressions, path, code
                )
                for expression in expressions:
                    if expression != "default":
                        condition = ConditionalStatement(
                            control + "==" + expression,
                            ConditionalStatement.ConditionType.SWITCH,
                            False,
                        )
                        condition.line, condition.column = match.line, match.col
                        condition.code = get_code(match)
                        conditions.append(condition)
                    else:
                        condition = ConditionalStatement(
                            "", ConditionalStatement.ConditionType.SWITCH, True
                        )
                        condition.line, condition.column = match.line, match.col
                        condition.code = get_code(match)
                        conditions.append(condition)

            for i in range(1, len(conditions)):
                conditions[i - 1].else_statement = conditions[i]

            return [conditions[0]] + list(
                map(
                    lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                    codeelement.matches,
                )
            )
        elif isinstance(codeelement, puppetmodel.Selector):
            control = PuppetParser.__process_codeelement(
                codeelement.control, path, code
            )
            conditions = []

            for key_element, value_element in codeelement.hash.value.items():
                key = PuppetParser.__process_codeelement(key_element, path, code)
                value = PuppetParser.__process_codeelement(value_element, path, code)

                if key != "default":
                    condition = ConditionalStatement(
                        control + "==" + key,
                        ConditionalStatement.ConditionType.SWITCH,
                        False,
                    )
                    condition.line, condition.column = key_element.line, key_element.col
                    # HACK: the get_code function should be changed to receive a range
                    key_element.end_line, key_element.end_col = (
                        value_element.end_line,
                        value_element.end_col,
                    )
                    condition.code = get_code(key_element)
                    conditions.append(condition)
                else:
                    condition = ConditionalStatement(
                        "", ConditionalStatement.ConditionType.SWITCH, True
                    )
                    condition.line, condition.column = key_element.line, key_element.col
                    key_element.end_line, key_element.end_col = (
                        value_element.end_line,
                        value_element.end_col,
                    )
                    condition.code = get_code(key_element)
                    conditions.append(condition)

            for i in range(1, len(conditions)):
                conditions[i - 1].else_statement = conditions[i]

            return conditions[0]
        elif isinstance(codeelement, puppetmodel.Reference):
            res = codeelement.type + "["
            for r in codeelement.references:
                temp = PuppetParser.__process_codeelement(r, path, code)
                res += "" if temp is None else temp
            res += "]"
            return res
        elif isinstance(codeelement, puppetmodel.Function):
            # FIXME Functions definitions are not yet supported
            return list(
                map(
                    lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                    codeelement.body,
                )
            )
        elif isinstance(codeelement, puppetmodel.ResourceCollector):
            res = codeelement.resource_type + "<|"
            res += (
                PuppetParser.__process_codeelement(codeelement.search, path, code)
                + "|>"
            )
            return res
        elif isinstance(codeelement, puppetmodel.ResourceExpression):
            resources = []
            resources.append(
                PuppetParser.__process_codeelement(codeelement.default, path, code)
            )
            for resource in codeelement.resources:
                resources.append(
                    PuppetParser.__process_codeelement(resource, path, code)
                )
            return resources
        elif isinstance(codeelement, puppetmodel.Chaining):
            # FIXME Chaining not yet supported
            res = []
            op1 = PuppetParser.__process_codeelement(codeelement.op1, path, code)
            op2 = PuppetParser.__process_codeelement(codeelement.op2, path, code)
            if isinstance(op1, list):
                res += op1
            else:
                res.append(op1)
            if isinstance(op2, list):
                res += op2
            else:
                res.append(op2)
            return res
        elif isinstance(codeelement, list):
            return list(
                map(
                    lambda ce: PuppetParser.__process_codeelement(ce, path, code),
                    codeelement,
                )
            )
        elif codeelement is None:
            return ""
        else:
            return codeelement

    def parse_module(self, path: str) -> Module:
        res: Module = Module(os.path.basename(os.path.normpath(path)), path)
        super().parse_file_structure(res.folder, path)

        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                name_split = name.split(".")
                if len(name_split) == 2 and name_split[-1] == "pp":
                    res.add_block(self.parse_file(os.path.join(root, name), ""))

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

                PuppetParser.__process_unitblock_component(
                    PuppetParser.__process_codeelement(parsed_script, path, code),
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
                res.add_block(self.parse_file(f.path, ""))

        subfolders = [
            f.path for f in os.scandir(f"{path}") if f.is_dir() and not f.is_symlink()
        ]
        for d in subfolders:
            if os.path.basename(os.path.normpath(d)) not in ["modules"]:
                aux = self.parse_folder(d)
                res.blocks += aux.blocks
                res.modules += aux.modules

        return res
