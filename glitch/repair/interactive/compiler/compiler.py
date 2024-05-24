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
            self, attribute: Attribute, labeled_script: LabeledUnitBlock
        ) -> None:
            attr_name = NamesDatabase.get_attr_name(
                attribute.name, self.au_type, self.__tech
            )

            attribute.value = NamesDatabase.get_attr_value(
                attribute.value, attr_name, self.au_type, self.__tech
            )
            expr = DeltaPCompiler._compile_expr(attribute.value, labeled_script)
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
        ) -> str:
            attr = self.get_attribute(attr_name)
            name = NamesDatabase.get_attr_name(attr_name, self.au_type, self.__tech)

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
                self.add_attribute(attr, labeled_script)

            labeled_script.add_sketch_location(atomic_unit, attr)
            labeled_script.add_sketch_location(attr, attr.value)
            return name + "_" + str(hash(attr))

    @staticmethod
    def _compile_expr(expr: Expr, labeled_script: LabeledUnitBlock) -> PExpr:
        def binary_op(op: Type[PBinOp], left: Expr, right: Expr) -> PExpr:
            return PEBinOP(
                op(),
                DeltaPCompiler._compile_expr(left, labeled_script),
                DeltaPCompiler._compile_expr(right, labeled_script),
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
                PNot(), DeltaPCompiler._compile_expr(expr.expr, labeled_script)
            )
        elif isinstance(expr, Minus):
            return PEUnOP(
                PNeg(), DeltaPCompiler._compile_expr(expr.expr, labeled_script)
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
    ) -> PStatement:
        path = attributes["path"]
        # The path may be defined as the name of the atomic unit
        if path == PEUndef():
            path = PEConst(PStr(atomic_unit.name))  # type: ignore

        state_var = attributes.get_var("state", atomic_unit, labeled_script)
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

        content_var = attributes.get_var("content", atomic_unit, labeled_script)
        statement = PSeq(
            statement,
            PLet(
                content_var,
                attributes["content"],
                PWrite(path, PEVar(content_var)),
            ),
        )

        owner_var = attributes.get_var("owner", atomic_unit, labeled_script)
        statement = PSeq(
            statement,
            PLet(
                owner_var,
                attributes["owner"],
                PChown(path, PEVar(owner_var)),
            ),
        )

        mode_var = attributes.get_var("mode", atomic_unit, labeled_script)
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
        statement: PStatement,
        atomic_unit: AtomicUnit,
        tech: Tech,
        labeled_script: LabeledUnitBlock,
    ) -> PStatement:
        attributes: DeltaPCompiler.__Attributes = DeltaPCompiler.__Attributes(
            atomic_unit.type, tech
        )
        if attributes.au_type == "file":
            for attribute in atomic_unit.attributes:
                attributes.add_attribute(attribute, labeled_script)
            statement = PSeq(
                statement,
                DeltaPCompiler.__handle_file(atomic_unit, attributes, labeled_script),
            )
        # Defined type
        elif labeled_script.env.has_definition(atomic_unit.type):
            # TODO
            pass

        return statement

    @staticmethod
    def __handle_conditional(
        conditional: ConditionalStatement, tech: Tech, labeled_script: LabeledUnitBlock
    ) -> PStatement:
        body = PSkip()
        for stat in conditional.statements:
            if isinstance(stat, AtomicUnit):
                body = DeltaPCompiler.__handle_atomic_unit(
                    body, stat, tech, labeled_script
                )
            elif isinstance(stat, ConditionalStatement):
                body = PSeq(
                    body,
                    DeltaPCompiler.__handle_conditional(stat, tech, labeled_script),
                )

        else_statement = PSkip()
        if conditional.else_statement is not None:
            else_statement = DeltaPCompiler.__handle_conditional(
                conditional.else_statement, tech, labeled_script
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
    def compile(labeled_script: LabeledUnitBlock, tech: Tech) -> PStatement:
        statement = PSkip()
        script = labeled_script.script

        # TODO: Handle variables
        # TODO: Handle scopes
        # TODO: The statements will not be in the correct order

        for stat in script.statements:
            if isinstance(stat, ConditionalStatement):
                statement = PSeq(
                    statement,
                    DeltaPCompiler.__handle_conditional(stat, tech, labeled_script),
                )

        for atomic_unit in script.atomic_units:
            statement = DeltaPCompiler.__handle_atomic_unit(
                statement, atomic_unit, tech, labeled_script
            )

        return statement
