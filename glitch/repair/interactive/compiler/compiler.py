import random
from typing import Optional, Dict, Tuple, Type

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock
from glitch.repair.interactive.values import DefaultValue


class DeltaPCompiler:
    def __init__(self, labeled_script: LabeledUnitBlock) -> None:
        self._sketched = -1
        self._literal = 0
        self._condition = 0
        self.scope: List[str] = []
        self._labeled_script = labeled_script

    class __Attributes:
        def __init__(self, compiler: "DeltaPCompiler", au_type: str, tech: Tech) -> None:
            self.au_type = NamesDatabase.get_au_type(au_type, tech)
            self.__compiler = compiler
            self.__tech = tech
            self.__attributes: Dict[str, Tuple[PExpr, Attribute]] = {}

        def add_attribute(
            self, attribute: Attribute
        ) -> None:
            attr_name = NamesDatabase.get_attr_name(
                attribute.name, self.au_type, self.__tech
            )

            attribute.value = NamesDatabase.get_attr_value(
                attribute.value, attr_name, self.au_type, self.__tech
            )
            expr = self.__compiler._compile_expr(attribute.value)
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
        ) -> Tuple[str, int]:
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
                                self.__compiler._sketched,
                                self.__compiler._sketched,
                                self.__compiler._sketched,
                                self.__compiler._sketched,
                                "",
                            ),
                        ),
                        ElementInfo(
                            self.__compiler._sketched - 1,
                            self.__compiler._sketched - 1,
                            self.__compiler._sketched - 1,
                            self.__compiler._sketched - 1,
                            "",
                        ),
                    )
                else:
                    attr = Attribute(
                        attr_name,
                        Null(
                            ElementInfo(
                                self.__compiler._sketched,
                                self.__compiler._sketched,
                                self.__compiler._sketched,
                                self.__compiler._sketched,
                                "",
                            )
                        ),
                        ElementInfo(
                            self.__compiler._sketched - 1,
                            self.__compiler._sketched - 1,
                            self.__compiler._sketched - 1,
                            self.__compiler._sketched - 1,
                            "",
                        ),
                    )

                label = self.__compiler._sketched
                self.__compiler._sketched -= 2
                self.add_attribute(attr)
            else:
                label = self.__compiler._labeled_script.get_label(attr)

            self.__compiler._labeled_script.add_location(atomic_unit, attr)
            self.__compiler._labeled_script.add_location(attr, attr.value)

            return self.__compiler._get_attribute_name(
                attr.name,
                attr, 
                self.au_type, 
                self.__tech
            ), label

    def _get_scope_name(self, name: str):
        return "::".join(self.scope + [name])

    def _get_attribute_name(
        self,
        attr_name: str,
        attribute: Attribute,
        au_type: str,
        tech: Tech,
    ) -> str:
        name = NamesDatabase.get_attr_name(attr_name, au_type, tech)
        return self._get_scope_name(name + "_" + str(hash(attribute)))
    
    def _compile_expr(self, expr: Expr) -> PExpr:
        def binary_op(op: Type[PBinOp], left: Expr, right: Expr) -> PExpr:
            return PEBinOP(
                op(),
                self._compile_expr(left),
                self._compile_expr(right),
            )

        if isinstance(expr, String):
            value = PEConst(PStr(expr.value))

            if self._labeled_script.has_label(expr):
                label = self._labeled_script.get_label(expr)
            else:
                literal_name = f"literal-{self._literal}"
                label = self._labeled_script.add_label(literal_name, expr)
                self._literal += 1

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
            if self._labeled_script.has_label(expr):
                label = self._labeled_script.get_label(expr)
            else:
                literal_name = f"literal-{self._literal}"
                label = self._labeled_script.add_label(literal_name, expr)
                self._literal += 1

            return PRLet(
                f"literal-{label}",
                PEUndef(),
                label,
            )
        elif isinstance(expr, Not):
            return PEUnOP(
                PNot(), self._compile_expr(expr.expr)
            )
        elif isinstance(expr, Minus):
            return PEUnOP(
                PNeg(), self._compile_expr(expr.expr)
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
            return PEVar(self._get_scope_name(expr.value))
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

    def __handle_file(
        self,
        atomic_unit: AtomicUnit,
        attributes: __Attributes,
    ) -> PStatement:
        path = attributes["path"]
        path_attr = attributes.get_attribute("path")
        if path_attr is not None:
            self._labeled_script.add_location(atomic_unit, path_attr)
            self._labeled_script.add_location(path_attr, path_attr.value)
        # The path may be defined as the name of the atomic unit
        if path == PEUndef():
            path = PEConst(PStr(atomic_unit.name))  # type: ignore

        state_var, label = attributes.get_var("state", atomic_unit)
        statement = PLet(
            state_var,
            attributes["state"],
            label,
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

        content_var, label = attributes.get_var("content", atomic_unit)
        statement = PSeq(
            statement,
            PLet(
                content_var,
                attributes["content"],
                label,
                PWrite(path, PEVar(content_var)),
            ),
        )

        owner_var, label = attributes.get_var("owner", atomic_unit)
        statement = PSeq(
            statement,
            PLet(
                owner_var,
                attributes["owner"],
                label,
                PChown(path, PEVar(owner_var)),
            ),
        )

        mode_var, label = attributes.get_var("mode", atomic_unit)
        statement = PSeq(
            statement,
            PLet(
                mode_var,
                attributes["mode"],
                label,
                PChmod(path, PEVar(mode_var)),
            ),
        )

        return statement

    def __handle_atomic_unit(
        self,
        atomic_unit: AtomicUnit,
    ) -> PStatement:
        statement = PSkip()
        tech = self._labeled_script.tech
        attributes: DeltaPCompiler.__Attributes = DeltaPCompiler.__Attributes(
            self, atomic_unit.type, tech
        )
        if attributes.au_type == "file":
            for attribute in atomic_unit.attributes:
                attributes.add_attribute(attribute)
            statement = PSeq(
                statement,
                self.__handle_file(atomic_unit, attributes),
            )
        # Defined type
        elif self._labeled_script.env.has_definition(atomic_unit.type):
            definition = self._labeled_script.env.get_definition(atomic_unit.type)
            self.scope += [f"defined_resource{str(random.randint(0, 28021904))}"]

            defined_attributes: Dict[str, Tuple[Attribute, bool]] = {}
            for attr in atomic_unit.attributes:
                defined_attributes[attr.name] = (attr, False)
                
            for attr in definition.attributes:
                if attr.name not in defined_attributes:
                    defined_attributes[attr.name] = (attr, True)

            for name, attr in list(defined_attributes.items()):
                new_name = self._get_scope_name(name)
                defined_attributes[new_name] = attr
                defined_attributes.pop(name)

            statement = self.__handle_unit_block(
                definition
            )

            for name, t in defined_attributes.items():
                attr, in_ub = t
                value = self._compile_expr(attr.value) 
                self._labeled_script.add_location(attr, attr.value)
                if in_ub:
                    self._labeled_script.add_location(definition, attr)
                else:
                    self._labeled_script.add_location(atomic_unit, attr)
                statement = PLet(
                    name,
                    value,
                    self._labeled_script.get_label(attr),
                    statement,
                )
            
            statement = PSeq(statement, PSkip())
            self.scope.pop()
        
        return statement

    def __handle_conditional(
        self,
        conditional: ConditionalStatement, 
    ) -> PStatement:
        body = PSkip()
        for stat in conditional.statements:
            body = PSeq(
                body, self.__handle_code_element(stat)
            )

        else_statement = PSkip()
        if conditional.else_statement is not None:
            else_statement = self.__handle_conditional(
                conditional.else_statement
            )

        self._condition += 1
        return PIf(
            # FIXME: This creates a placeholder since we will branch every time
            # There are cases that we can infer the value of the condition
            # The creation of these variables should be done in the solver
            PEVar(f"dejavu-condition-{self._condition}"),
            body,
            else_statement,
        )

    def __handle_variable(
        self,
        variable: Variable, 
    ) -> PStatement:
        name = self._get_scope_name(variable.name)
        statement = PLet(
            name,
            self._compile_expr(variable.value),
            self._labeled_script.get_label(variable),
            PSkip(),
        )
        self._labeled_script.add_location(variable, variable.value)
        return statement

    def __handle_unit_block(
        self,
        unit_block: UnitBlock, 
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
            new_compiled = self.__handle_code_element(
                statement
            )
            if isinstance(new_compiled, PLet):
                new_compiled.body = compiled
                compiled = PSeq(new_compiled, PSkip())
            else:
                compiled = PSeq(new_compiled, compiled)

        return compiled

    def __handle_code_element(
        self, code_element: CodeElement
    ) -> PStatement:
        if isinstance(code_element, AtomicUnit):
            return self.__handle_atomic_unit(code_element)
        elif isinstance(code_element, ConditionalStatement):
            return self.__handle_conditional(code_element)
        elif isinstance(code_element, Variable):
            return self.__handle_variable(code_element)
        elif (
            isinstance(code_element, UnitBlock)
            and code_element.type == UnitBlockType.definition
        ):
            return PSkip()
        elif isinstance(code_element, UnitBlock):
            return self.__handle_unit_block(code_element)

        raise RuntimeError(f"Unsupported code element, got {code_element}")

    def compile(self) -> PStatement:
        script = self._labeled_script.script
        # TODO: Handle scopes
        return self.__handle_unit_block(script)
