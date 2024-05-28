import copy
import random
from typing import Optional, Dict, Tuple, Type

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock
from glitch.repair.interactive.values import DefaultValue


class DeltaPCompiler:
    _sketched = -1
    _literal = 0
    _condition = 0

    class __Attributes:
        def __init__(self, au_type: str, tech: Tech) -> None:
            self.au_type = NamesDatabase.get_au_type(au_type, tech)
            self.__tech = tech
            self.__attributes: Dict[str, Tuple[PExpr, Attribute]] = {}

        def add_attribute(
            self, attribute: Attribute, labeled_script: LabeledUnitBlock, tvars: Dict[str, str]
        ) -> None:
            attr_name = NamesDatabase.get_attr_name(
                attribute.name, self.au_type, self.__tech
            )

            attribute.value = NamesDatabase.get_attr_value(
                attribute.value, attr_name, self.au_type, self.__tech
            )
            expr = DeltaPCompiler._compile_expr(attribute.value, labeled_script, tvars)
            self.__attributes[attr_name] = (expr, attribute)

        def get_attribute(self, attr_name: str) -> Optional[Attribute]:
            return self.__attributes.get(attr_name, (None, None))[1]

        def get_attribute_value(self, attr_name: str) -> PExpr:
            default = PEUndef()
            if attr_name == "state":
                default = DefaultValue.DEFAULT_STATE
            elif attr_name == "mode":
                default = DefaultValue.DEFAULT_MODE
            elif attr_name == "owner":
                default = DefaultValue.DEFAULT_OWNER
            elif attr_name == "content":
                default = DefaultValue.DEFAULT_CONTENT

            return self.__attributes.get(attr_name, (default, None))[0]

        def __getitem__(self, key: str) -> PExpr:
            return self.get_attribute_value(key)

        def get_var(
            self,
            attr_name: str,
            atomic_unit: AtomicUnit,
            labeled_script: LabeledUnitBlock,
            tvars: Dict[str, str],
        ) -> str:
            attr = self.get_attribute(attr_name)

            if attr is None:
                # Creates sketched attribute
                if attr_name == "state" and isinstance(
                    DefaultValue.DEFAULT_STATE.const, PStr
                ):  # HACK
                    attr = Attribute(
                        attr_name,
                        String(
                            DefaultValue.DEFAULT_STATE.const.value,
                            ElementInfo(
                                DeltaPCompiler._sketched,
                                DeltaPCompiler._sketched,
                                DeltaPCompiler._sketched,
                                DeltaPCompiler._sketched,
                                "",
                            ),
                        ),
                        ElementInfo(
                            DeltaPCompiler._sketched - 1,
                            DeltaPCompiler._sketched - 1,
                            DeltaPCompiler._sketched - 1,
                            DeltaPCompiler._sketched - 1,
                            "",
                        ),
                    )
                else:
                    attr = Attribute(
                        attr_name,
                        Null(
                            ElementInfo(
                                DeltaPCompiler._sketched,
                                DeltaPCompiler._sketched,
                                DeltaPCompiler._sketched,
                                DeltaPCompiler._sketched,
                                "",
                            )
                        ),
                        ElementInfo(
                            DeltaPCompiler._sketched - 1,
                            DeltaPCompiler._sketched - 1,
                            DeltaPCompiler._sketched - 1,
                            DeltaPCompiler._sketched - 1,
                            "",
                        ),
                    )

                DeltaPCompiler._sketched -= 2
                self.add_attribute(attr, labeled_script, tvars)

            labeled_script.add_location(atomic_unit, attr)
            labeled_script.add_location(attr, attr.value)
            return DeltaPCompiler._get_attribute_name(
                attr.name,
                attr, 
                self.au_type, 
                self.__tech
            )

    @staticmethod
    def _get_attribute_name(
        attr_name: str,
        attribute: Attribute,
        au_type: str,
        tech: Tech,
    ) -> str:
        name = NamesDatabase.get_attr_name(attr_name, au_type, tech)
        return name + "_" + str(hash(attribute)) + str(random.randint(0, 28021904))
    
    @staticmethod
    def _compile_expr(expr: Expr, labeled_script: LabeledUnitBlock, tvars: Dict[str, str]) -> PExpr:
        def binary_op(op: Type[PBinOp], left: Expr, right: Expr) -> PExpr:
            return PEBinOP(
                op(),
                DeltaPCompiler._compile_expr(left, labeled_script, tvars),
                DeltaPCompiler._compile_expr(right, labeled_script, tvars),
            )

        if isinstance(expr, String):
            value = PEConst(PStr(expr.value))

            if labeled_script.has_label(expr):
                label = labeled_script.get_label(expr)
            else:
                literal_name = f"literal-{DeltaPCompiler._literal}"
                label = labeled_script.add_label(literal_name, expr)
                DeltaPCompiler._literal += 1

            return PRLet(
                f"literal-{label}",
                value,
                label,
            )
        elif isinstance(expr, (Integer, Float, Complex)):
            return PEConst(PNum(expr.value))
        elif isinstance(expr, Boolean):
            return PEConst(PBool(expr.value))
        elif isinstance(expr, Null):
            if labeled_script.has_label(expr):
                label = labeled_script.get_label(expr)
            else:
                literal_name = f"literal-{DeltaPCompiler._literal}"
                label = labeled_script.add_label(literal_name, expr)
                DeltaPCompiler._literal += 1

            return PRLet(
                f"literal-{label}",
                PEUndef(),
                label,
            )
        elif isinstance(expr, Not):
            return PEUnOP(
                PNot(), DeltaPCompiler._compile_expr(expr.expr, labeled_script, tvars)
            )
        elif isinstance(expr, Minus):
            return PEUnOP(
                PNeg(), DeltaPCompiler._compile_expr(expr.expr, labeled_script, tvars)
            )
        elif isinstance(expr, Or):
            return binary_op(POr, expr.left, expr.right)
        elif isinstance(expr, And):
            return binary_op(PAnd, expr.left, expr.right)
        elif isinstance(expr, Sum):
            return binary_op(PAdd, expr.left, expr.right)
        elif isinstance(expr, Equal):
            return binary_op(PEq, expr.left, expr.right)
        elif isinstance(expr, NotEqual):
            return PEUnOP(PNot(), binary_op(PEq, expr.left, expr.right))
        elif isinstance(expr, LessThan):
            return binary_op(PLt, expr.left, expr.right)
        elif isinstance(expr, LessThanOrEqual):
            return PEBinOP(
                POr(),
                binary_op(PLt, expr.left, expr.right),
                binary_op(PEq, expr.left, expr.right),
            )
        elif isinstance(expr, GreaterThan):
            return binary_op(PGt, expr.left, expr.right)
        elif isinstance(expr, GreaterThanOrEqual):
            return PEBinOP(
                POr(),
                binary_op(PGt, expr.left, expr.right),
                binary_op(PEq, expr.left, expr.right),
            )
        elif isinstance(expr, Subtract):
            return binary_op(PSub, expr.left, expr.right)
        elif isinstance(expr, Multiply):
            return binary_op(PMultiply, expr.left, expr.right)
        elif isinstance(expr, Divide):
            return binary_op(PDivide, expr.left, expr.right)
        elif isinstance(expr, Modulo):
            return binary_op(PMod, expr.left, expr.right)
        elif isinstance(expr, Power):
            return binary_op(PPower, expr.left, expr.right)
        elif isinstance(expr, VariableReference):
            if expr.value in tvars:
                return PEVar(tvars[expr.value])
            return PEVar(expr.value)
        elif isinstance(
            expr,
            (
                Hash,
                Array,
                FunctionCall,
                MethodCall,
                In,
                RightShift,
                LeftShift,
                Access,
                BitwiseAnd,
                BitwiseOr,
                BitwiseXor,
            ),
        ):
            # TODO: Unsupported
            return PEUndef()

        raise RuntimeError(f"Unsupported expression, got {expr}")

    @staticmethod
    def __handle_file(
        atomic_unit: AtomicUnit,
        attributes: __Attributes,
        labeled_script: LabeledUnitBlock,
        tvars: Dict[str, str],
    ) -> PStatement:
        path = attributes["path"]
        path_attr = attributes.get_attribute("path")
        if path_attr is not None:
            labeled_script.add_location(atomic_unit, path_attr)
            labeled_script.add_location(path_attr, path_attr.value)
        # The path may be defined as the name of the atomic unit
        if path == PEUndef():
            path = PEConst(PStr(atomic_unit.name))  # type: ignore

        state_var = attributes.get_var("state", atomic_unit, labeled_script, tvars)
        statement = PLet(
            state_var,
            attributes["state"],
            PIf(
                PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("present"))),
                PCreate(path),
                PIf(
                    PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("absent"))),
                    PRm(path),
                    PIf(
                        PEBinOP(PEq(), PEVar(state_var), PEConst(PStr("directory"))),
                        PMkdir(path),
                        PSkip(),
                    ),
                ),
            ),
        )

        content_var = attributes.get_var("content", atomic_unit, labeled_script, tvars)
        statement = PSeq(
            statement,
            PLet(
                content_var,
                attributes["content"],
                PWrite(path, PEVar(content_var)),
            ),
        )

        owner_var = attributes.get_var("owner", atomic_unit, labeled_script, tvars)
        statement = PSeq(
            statement,
            PLet(
                owner_var,
                attributes["owner"],
                PChown(path, PEVar(owner_var)),
            ),
        )

        mode_var = attributes.get_var("mode", atomic_unit, labeled_script, tvars)
        statement = PSeq(
            statement,
            PLet(
                mode_var,
                attributes["mode"],
                PChmod(path, PEVar(mode_var)),
            ),
        )

        return statement

    @staticmethod
    def __handle_atomic_unit(
        atomic_unit: AtomicUnit,
        labeled_script: LabeledUnitBlock,
        tvars: Dict[str, str],
    ) -> PStatement:
        statement = PSkip()
        tech = labeled_script.tech
        attributes: DeltaPCompiler.__Attributes = DeltaPCompiler.__Attributes(
            atomic_unit.type, tech
        )
        if attributes.au_type == "file":
            for attribute in atomic_unit.attributes:
                attributes.add_attribute(attribute, labeled_script, tvars)
            statement = PSeq(
                statement,
                DeltaPCompiler.__handle_file(atomic_unit, attributes, labeled_script, tvars),
            )
        # Defined type
        elif labeled_script.env.has_definition(atomic_unit.type):
            definition = labeled_script.env.get_definition(atomic_unit.type)
            new_tvars = copy.deepcopy(tvars)

            defined_attributes: Dict[str, Attribute] = {}
            for attr in atomic_unit.attributes:
                if labeled_script.tech == Tech.puppet:
                    name = f"${attr.name}"
                else:
                    name = attr.name
                defined_attributes[name] = attr
                
            for attr in definition.attributes:
                if attr.name not in defined_attributes:
                    defined_attributes[attr.name] = attr

            for name, attr in list(defined_attributes.items()):
                new_name = DeltaPCompiler._get_attribute_name(
                    name, attr, definition.type, tech
                )
                defined_attributes[new_name] = attr
                defined_attributes.pop(name)

                if labeled_script.tech == Tech.puppet:
                    new_tvars[name[1:]] = new_name
                new_tvars[name] = new_name

            statement = DeltaPCompiler.__handle_unit_block(
                definition, 
                labeled_script,
                new_tvars
            )

            for name, attr in defined_attributes.items():
                value = DeltaPCompiler._compile_expr(attr.value, labeled_script, new_tvars)
                labeled_script.add_location(attr, attr.value)
                labeled_script.add_location(atomic_unit, attr)
                statement = PLet(
                    name,
                    value,
                    statement,
                )
            
            statement = PSeq(statement, PSkip())

        return statement

    @staticmethod
    def __handle_conditional(
        conditional: ConditionalStatement, 
        labeled_script: LabeledUnitBlock,
        tvars: Dict[str, str],
    ) -> PStatement:
        body = PSkip()
        for stat in conditional.statements:
            body = PSeq(
                body, DeltaPCompiler.__handle_code_element(stat, labeled_script, tvars)
            )

        else_statement = PSkip()
        if conditional.else_statement is not None:
            else_statement = DeltaPCompiler.__handle_conditional(
                conditional.else_statement, labeled_script, tvars
            )

        DeltaPCompiler._condition += 1
        return PIf(
            # FIXME: This creates a placeholder since we will branch every time
            # There are cases that we can infer the value of the condition
            # The creation of these variables should be done in the solver
            PEVar(f"dejavu-condition-{DeltaPCompiler._condition}"),
            body,
            else_statement,
        )

    @staticmethod
    def __handle_variable(
        variable: Variable, 
        labeled_script: LabeledUnitBlock,
        tvars: Dict[str, str],
    ) -> PStatement:
        if variable.name in tvars:
            name = tvars[variable.name]
        else:
            name = variable.name
        statement = PLet(
            name,
            DeltaPCompiler._compile_expr(variable.value, labeled_script, tvars),
            PSkip(),
        )
        labeled_script.add_location(variable, variable.value)
        return statement

    @staticmethod
    def __handle_unit_block(
        unit_block: UnitBlock, 
        labeled_script: LabeledUnitBlock,
        tvars: Dict[str, str],
    ) -> PStatement:
        compiled = PSkip()
        statements: List[CodeElement] = (
            unit_block.statements
            + unit_block.atomic_units
            + unit_block.variables
            + unit_block.unit_blocks
        )
        statements.sort(key=lambda x: (x.line, x.column), reverse=True)

        for statement in statements:
            new_compiled = DeltaPCompiler.__handle_code_element(
                statement, labeled_script, tvars
            )
            if isinstance(new_compiled, PLet):
                new_compiled.body = compiled
                compiled = PSeq(new_compiled, PSkip())
            else:
                compiled = PSeq(new_compiled, compiled)

        return compiled

    @staticmethod
    def __handle_code_element(
        code_element: CodeElement, labeled_script: LabeledUnitBlock, tvars: Dict[str, str]
    ) -> PStatement:
        if isinstance(code_element, AtomicUnit):
            return DeltaPCompiler.__handle_atomic_unit(code_element, labeled_script, tvars)
        elif isinstance(code_element, ConditionalStatement):
            return DeltaPCompiler.__handle_conditional(code_element, labeled_script, tvars)
        elif isinstance(code_element, Variable):
            return DeltaPCompiler.__handle_variable(code_element, labeled_script, tvars)
        elif (
            isinstance(code_element, UnitBlock)
            and code_element.type == UnitBlockType.definition
        ):
            return PSkip()
        elif isinstance(code_element, UnitBlock):
            return DeltaPCompiler.__handle_unit_block(code_element, labeled_script, tvars)

        raise RuntimeError(f"Unsupported code element, got {code_element}")

    @staticmethod
    def compile(labeled_script: LabeledUnitBlock) -> PStatement:
        script = labeled_script.script
        # TODO: Handle scopes
        return DeltaPCompiler.__handle_unit_block(script, labeled_script, {})
