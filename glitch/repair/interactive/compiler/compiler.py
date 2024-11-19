import random
import logging
from typing import Optional, Dict, Tuple, Type, Set

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock


class DeltaPCompiler:
    AU_TYPE_ATTRIBUTES = {
        "user": ["state"],
        "package": ["state"],
        "service": ["state", "enabled"],
        "aws_iam_role": ["state", "assume_role_policy"],
        "aws_instance": ["state", "instance_type", "availability_zone"],
        "aws_s3_bucket": ["state", "acl"],
    }

    def __init__(self, labeled_script: LabeledUnitBlock) -> None:
        self._sketched = -1
        self._literal = 0
        self._condition = 0
        self.scope: List[str] = []
        self.vars: Set[str] = set()
        self._labeled_script = labeled_script
        self.seen_resources: List[Tuple[List[str], str]] = []

    class _AtomicUnitCompiler:
        def __init__(self, name: str, compiler: "DeltaPCompiler", attributes: List[str]) -> None:
            self.__name = name
            self._compiler = compiler
            self.__attributes = attributes

        def compile(
            self,
            atomic_unit: AtomicUnit,
            attributes: "DeltaPCompiler._Attributes",
        ) -> PStatement:
            name = attributes["name"]
            if name == PEUndef():
                name = self._compiler._compile_expr(atomic_unit.name)
                self._compiler._labeled_script.add_location(atomic_unit, atomic_unit.name)
            path = PEBinOP(PAdd(), PEConst(PStr(self.__name + ":")), name)

            if self._compiler._check_seen_resource(path):
                return PSkip()

            name_attr = attributes.get_attribute("name")
            if name_attr is not None:
                self._compiler._labeled_script.add_location(atomic_unit, name_attr)
                self._compiler._labeled_script.add_location(name_attr, name_attr.value)

            statement = PSkip()
            for attribute in self.__attributes[::-1]:
                statement = PSeq(
                    self._compiler._handle_attr(atomic_unit, attributes, path, attribute),
                    statement,
                )

            return statement

    class _Attributes:
        def __init__(
            self, compiler: "DeltaPCompiler", au_type: str, tech: Tech
        ) -> None:
            self.__compiler = compiler
            self.__tech = tech
            self.__attributes: Dict[str, Tuple[PExpr, Attribute]] = {}

        def add_attribute(self, attribute: Attribute) -> None:
            expr = self.__compiler._compile_expr(attribute.value)
            self.__attributes[attribute.name] = (expr, attribute)

        def get_attribute(self, attr_name: str) -> Optional[Attribute]:
            return self.__attributes.get(attr_name, (None, None))[1]

        def get_attribute_value(self, attr_name: str) -> PExpr:
            default = PEUndef()
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
                if attr_name == "state":  # HACK
                    attr = Attribute(
                        attr_name,
                        String(
                            UNDEF,
                            ElementInfo.get_sketched(),
                        ),
                        ElementInfo.get_sketched(),
                    )
                else:
                    attr = Attribute(
                        attr_name,
                        Null(ElementInfo.get_sketched()),
                        ElementInfo.get_sketched(),
                    )

                label = self.__compiler._sketched
                self.__compiler._sketched -= 1
                self.add_attribute(attr)
            else:
                # HACK
                attr_value = self.get_attribute_value(attr_name)
                if attr_value == PEUnsupported():
                    if self.__compiler._labeled_script.has_label(attr.value):
                        label = self.__compiler._labeled_script.get_label(attr.value)
                    else:
                        label = self.__compiler._labeled_script.add_label(
                            f"literal-{self.__compiler._literal}", attr.value
                        )
                    self.__attributes[attr_name] = (
                        PRLet(
                            f"literal-{label}",
                            PEUndef(),
                            label,
                        ),
                        attr,
                    )
                    self.__compiler._literal += 1

                label = self.__compiler._labeled_script.get_label(attr)

            self.__compiler._labeled_script.add_location(atomic_unit, attr)
            self.__compiler._labeled_script.add_location(attr, attr.value)

            return (
                self.__compiler._get_attribute_name(
                    attr.name, attr, atomic_unit.type, self.__tech
                ),
                label,
            )

    def _get_scope_name(self, name: str):
        return ":dejavu:".join(self.scope + [name])

    def _get_attribute_name(
        self,
        attr_name: str,
        attribute: Attribute,
        au_type: str,
        tech: Tech,
    ) -> str:
        return self._get_scope_name(attr_name + "_" + str(hash(attribute)))
    
    def __has_var(self, id: str) -> bool:
        scopes = id.split(":dejavu:")
        while True:
            if ":dejavu:".join(scopes) in self.vars:
                return True
            if len(scopes) == 1:
                break
            scopes.pop(-2)

        return False
    
    def __get_prlet(self, expr: Expr, value: PExpr) -> PRLet:
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

    def _compile_expr(self, expr: Expr) -> PExpr:
        def binary_op(op: Type[PBinOp], left: Expr, right: Expr) -> PExpr:
            return PEBinOP(
                op(),
                self._compile_expr(left),
                self._compile_expr(right),
            )

        if isinstance(expr, String):
            value = PEConst(PStr(expr.value))
            return self.__get_prlet(expr, value)
        elif isinstance(expr, (Integer, Float, Complex)):
            value = PEConst(PStr(str(expr.value)))
            return self.__get_prlet(expr, value)
        elif isinstance(expr, Boolean):
            return self.__get_prlet(expr, PEConst(PBool(expr.value)))
        elif isinstance(expr, Null):
            return self.__get_prlet(expr, PEUndef())
        elif isinstance(expr, Not):
            return PEUnOP(PNot(), self._compile_expr(expr.expr))
        elif isinstance(expr, Minus):
            return PEUnOP(PNeg(), self._compile_expr(expr.expr))
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
        elif (
            isinstance(expr, VariableReference) 
            and self.__has_var(self._get_scope_name(expr.value))
        ):
            return PEVar(self._get_scope_name(expr.value))
        elif isinstance(expr, VariableReference): # undefined variable
            # HACK: this should be done in a different way but it is easier to
            # do this for now.
            if expr.value in ["present", "absent"]:
                return self._compile_expr(
                    String(expr.value, ElementInfo.from_code_element(expr))
                )
            return PEUnsupported()
        else:
            # TODO: Unsupported
            logging.warning(f"Unsupported expression, got {expr}")
            return PEUnsupported()
        
    def _check_seen_resource(
        self,
        path: PExpr
    ):
        # HACK: avoids some problems with duplicate atomic units
        # (it only considers the last one defined)
        path_str = PStatement.get_str(
            path, 
            {},
            ignore_vars = True # HACK: avoids having to get the vars
        )
        if path_str is not None:
            if (self.scope, path_str) in self.seen_resources:
                return True
            self.seen_resources.append(
                (self.scope.copy(), path_str)
            )
        return False
        
    def _handle_attr(
        self,
        atomic_unit: AtomicUnit,
        attributes: _Attributes,
        path: PExpr,
        attr: str
    ):
        attr_var, label = attributes.get_var(attr, atomic_unit)
        self.vars.add(attr_var)
        statement = PLet(
            attr_var,
            attributes[attr],
            label,
            PAttr(path, attr, PEVar(attr_var)),
        )
        return statement
    
    def __handle_file(
        self,
        atomic_unit: AtomicUnit,
        attributes: _Attributes,
    ) -> PStatement:
        path = attributes["path"]
        path_attr = attributes.get_attribute("path")
        if path_attr is not None:
            self._labeled_script.add_location(atomic_unit, path_attr)
            self._labeled_script.add_location(path_attr, path_attr.value)
        # The path may be defined as the name of the atomic unit
        if path == PEUndef():
            path = self._compile_expr(atomic_unit.name)
            self._labeled_script.add_location(atomic_unit, atomic_unit.name)

        if self._check_seen_resource(path):
            return PSkip()

        statement = self._handle_attr(atomic_unit, attributes, path, "state")
        statement = PSeq(
            statement,
            self._handle_attr(atomic_unit, attributes, path, "content")
        )
        statement = PSeq(
            statement,
            self._handle_attr(atomic_unit, attributes, path, "owner")
        )
        statement = PSeq(
            statement,
            self._handle_attr(atomic_unit, attributes, path, "mode")
        )

        return statement

    def __handle_defined_type(
        self,
        atomic_unit: AtomicUnit,
    ):
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
            self.vars.add(new_name)
            defined_attributes[new_name] = attr
            defined_attributes.pop(name)

        statement = self.__handle_unit_block(definition)

        # The scope is popped here since it allows variable references 
        # compiled from the attributes' values to have the outside scope
        self.scope.pop()

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

        return statement

    def __handle_atomic_unit(
        self,
        atomic_unit: AtomicUnit,
    ) -> PStatement:
        statement = PSkip()
        tech = self._labeled_script.tech
        attributes: DeltaPCompiler._Attributes = DeltaPCompiler._Attributes(
            self, atomic_unit.type, tech
        )

        if atomic_unit.type == "file":
            for attribute in atomic_unit.attributes:
                attributes.add_attribute(attribute)
            statement = PSeq(
                statement,
                self.__handle_file(atomic_unit, attributes),
            )
        elif atomic_unit.type in DeltaPCompiler.AU_TYPE_ATTRIBUTES:
            for attribute in atomic_unit.attributes:
                attributes.add_attribute(attribute)
            statement = DeltaPCompiler._AtomicUnitCompiler(
                atomic_unit.type,
                self,
                DeltaPCompiler.AU_TYPE_ATTRIBUTES[atomic_unit.type],
            ).compile(atomic_unit, attributes)
        # Defined type
        elif self._labeled_script.env.has_definition(atomic_unit.type):
            statement = PSeq(self.__handle_defined_type(atomic_unit), PSkip())

        return statement

    def __handle_conditional(
        self,
        conditional: ConditionalStatement,
    ) -> PStatement:
        self.scope += [f"condition{str(random.randint(0, 28021904))}"]
        body = PSkip()
        for stat in conditional.statements:
            body = PSeq(body, self.__handle_code_element(stat))
        self.scope.pop()

        else_statement = PSkip()
        if conditional.else_statement is not None:
            else_statement = self.__handle_conditional(conditional.else_statement)

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
        self.vars.add(name)
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

        # If we do not do this here, since we iterate over the statements
        # in reverse, the variables will not be defined when expressions are
        # compiled
        for variable in unit_block.variables:
            self.vars.add(self._get_scope_name(variable.name))

        for statement in statements:
            self._labeled_script.add_location(unit_block, statement)
            new_compiled = self.__handle_code_element(statement)
            if isinstance(new_compiled, PLet):
                new_compiled.body = compiled
                compiled = PSeq(new_compiled, PSkip())
            else:
                compiled = PSeq(new_compiled, compiled)

        return compiled

    def __handle_code_element(self, code_element: CodeElement) -> PStatement:
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
        else:
            logging.warning(f"Unsupported code element, got {code_element}")
            return PSkip()

    def compile(self) -> PStatement:
        script = self._labeled_script.script
        # TODO: Handle scopes
        return self.__handle_unit_block(script)