import time

from copy import deepcopy
from typing import List, Callable, Tuple, Any
from z3 import (
    Solver,
    sat,
    If,
    StringVal,
    IntVal,
    String,
    Bool,
    And,
    Not,
    Int,
    Or,
    Sum,
    ModelRef,
    Context,
    ExprRef,
)

from glitch.repair.interactive.filesystem import FileSystemState
from glitch.repair.interactive.filesystem import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.values import DefaultValue, UNDEF
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock
from glitch.repr.inter import Attribute, AtomicUnit, CodeElement, Block
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.names_database import NamesDatabase

Fun = Callable[[ExprRef], ExprRef]


class PatchSolver:
    @dataclass
    class __Funs:
        state_fun: Fun
        contents_fun: Fun
        mode_fun: Fun
        owner_fun: Fun

    def __init__(
        self,
        statement: PStatement,
        filesystem: FileSystemState,
        timeout: int = 180,
        ctx: Optional[Context] = None,
    ) -> None:
        # FIXME: the filesystem in here should be generated from
        # checking the affected paths in statement
        self.solver = Solver(ctx=ctx)
        self.timeout = timeout
        self.statement = statement
        self.sum_var = Int("sum")
        self.unchanged: Dict[int, ExprRef] = {}
        self.vars: Dict[str, ExprRef] = {}
        self.holes: Dict[str, ExprRef] = {}

        # FIXME: check the defaults
        self.__funs = PatchSolver.__Funs(
            lambda p: StringVal(UNDEF),
            lambda p: self.__compile_expr(DefaultValue.DEFAULT_CONTENT),
            lambda p: self.__compile_expr(DefaultValue.DEFAULT_MODE),
            lambda p: self.__compile_expr(DefaultValue.DEFAULT_OWNER),
        )

        # TODO?: We might want to use the default file system state to update
        # the funs
        # default_fs = self.__get_default_fs()

        labels = self.__collect_labels(statement)
        for label in labels:
            self.unchanged[label] = Int(f"unchanged-{label}")

        constraints, self.__funs = self.__generate_soft_constraints(
            self.statement, self.__funs
        )
        for constraint in constraints:
            self.solver.add(constraint)

        self.__generate_hard_constraints(filesystem)

        self.solver.add(Sum(list(self.unchanged.values())) == self.sum_var)

    def __collect_labels(self, statement: PStatement | PExpr) -> List[int]:
        if isinstance(statement, PSeq):
            return self.__collect_labels(statement.lhs) + self.__collect_labels(
                statement.rhs
            )
        elif isinstance(statement, PIf):
            return (
                self.__collect_labels(statement.pred)
                + self.__collect_labels(statement.cons)
                + self.__collect_labels(statement.alt)
            )
        elif isinstance(statement, PLet) and isinstance(statement.label, int):
            return [statement.label] + self.__collect_labels(statement.body)
        return []

    def __compile_expr(self, expr: PExpr) -> ExprRef:
        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return StringVal(expr.const.value)
        elif isinstance(expr, PEVar) and expr.id.startswith("dejavu-condition-"):
            self.vars[expr.id] = Bool(expr.id)
            return self.vars[expr.id]
        elif isinstance(expr, PEVar):
            self.vars[expr.id] = String(expr.id)
            return self.vars[expr.id]
        elif isinstance(expr, PEUndef):
            # NOTE: it is an arbitrary string to represent an undefined value
            return StringVal(UNDEF)
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PEq):
            return self.__compile_expr(expr.lhs) == self.__compile_expr(expr.rhs)

        raise ValueError(f"Not supported {expr}")

    def __generate_hard_constraints(self, filesystem: FileSystemState) -> None:
        for path, state in filesystem.state.items():
            self.solver.add(
                self.__funs.state_fun(StringVal(path)) == StringVal(str(state))
            )
            content, mode, owner = UNDEF, UNDEF, UNDEF

            if isinstance(state, File):
                content = UNDEF if state.content is None else state.content
            if isinstance(state, File) or isinstance(state, Dir):
                mode = UNDEF if state.mode is None else state.mode
                owner = UNDEF if state.owner is None else state.owner

            self.solver.add(
                self.__funs.contents_fun(StringVal(path)) == StringVal(content)
            )
            self.solver.add(self.__funs.mode_fun(StringVal(path)) == StringVal(mode))
            self.solver.add(self.__funs.owner_fun(StringVal(path)) == StringVal(owner))

    def __generate_soft_constraints(
        self, statement: PStatement, funs: __Funs
    ) -> Tuple[List[ExprRef], __Funs,]:
        # Avoids infinite recursion
        funs = deepcopy(funs)
        # NOTE: For now it doesn't make sense to update the funs for the
        # default values because the else will always be the default value
        previous_state_fun = funs.state_fun
        previous_contents_fun = funs.contents_fun
        previous_mode_fun = funs.mode_fun
        previous_owner_fun = funs.owner_fun
        constraints: List[ExprRef] = []

        if isinstance(statement, PMkdir):
            path = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("dir"), previous_state_fun(p)
            )
        elif isinstance(statement, PCreate):
            path = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("file"), previous_state_fun(p)
            )
        elif isinstance(statement, PWrite):
            path = self.__compile_expr(statement.path)
            funs.contents_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.content),
                previous_contents_fun(p),
            )
        elif isinstance(statement, PRm):
            path = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("nil"), previous_state_fun(p)
            )
        elif isinstance(statement, PCp):
            dst, src = self.__compile_expr(statement.dst), self.__compile_expr(
                statement.src
            )
            funs.state_fun = lambda p: If(
                p == dst, previous_state_fun(src), previous_state_fun(p)
            )
            funs.contents_fun = lambda p: If(
                p == dst,
                previous_contents_fun(src),
                previous_contents_fun(p),
            )
            funs.mode_fun = lambda p: If(
                p == dst, previous_mode_fun(src), previous_mode_fun(p)
            )
            funs.owner_fun = lambda p: If(
                p == dst, previous_owner_fun(src), previous_owner_fun(p)
            )
        elif isinstance(statement, PChmod):
            path = self.__compile_expr(statement.path)
            funs.mode_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.mode),
                previous_mode_fun(p),
            )
        elif isinstance(statement, PChown):
            path = self.__compile_expr(statement.path)
            funs.owner_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.owner),
                previous_owner_fun(p),
            )
        elif isinstance(statement, PSeq):
            self.__generate_soft_constraints(statement.lhs, funs)
            lhs_constraints, funs = self.__generate_soft_constraints(
                statement.lhs, funs
            )
            constraints += lhs_constraints
            rhs_constraints, funs = self.__generate_soft_constraints(
                statement.rhs, funs
            )
            constraints += rhs_constraints
        elif isinstance(statement, PLet):
            hole, var = String(f"loc-{statement.label}"), String(statement.id)
            self.holes[f"loc-{statement.label}"] = hole
            self.vars[statement.id] = var
            unchanged = self.unchanged[statement.label]  # type: ignore
            constraints.append(
                Or(  # type: ignore
                    And(unchanged == 1, var == self.__compile_expr(statement.expr)),  # type: ignore
                    And(unchanged == 0, var == hole),  # type: ignore
                )  # type: ignore
            )
            body_constraints, funs = self.__generate_soft_constraints(
                statement.body, funs
            )
            constraints += body_constraints
        elif isinstance(statement, PIf):
            condition = self.__compile_expr(statement.pred)

            cons_constraints, cons_funs = self.__generate_soft_constraints(
                statement.cons, funs
            )
            alt_constraints, alt_funs = self.__generate_soft_constraints(
                statement.alt, funs
            )

            funs.state_fun = lambda p: If(
                condition, cons_funs.state_fun(p), alt_funs.state_fun(p)
            )
            funs.contents_fun = lambda p: If(
                condition, cons_funs.contents_fun(p), alt_funs.contents_fun(p)
            )
            funs.mode_fun = lambda p: If(
                condition, cons_funs.mode_fun(p), alt_funs.mode_fun(p)
            )
            funs.owner_fun = lambda p: If(
                condition, cons_funs.owner_fun(p), alt_funs.owner_fun(p)
            )

            for label in self.__collect_labels(statement.cons):
                self.solver.add(Or(condition, self.unchanged[label] == 1))
            for label in self.__collect_labels(statement.alt):
                self.solver.add(Or(Not(condition), self.unchanged[label] == 1))

            # NOTE: This works because the only constraints created should
            # always be added. Its kinda of an HACK
            for constraint in cons_constraints:
                # constraints.append(Or(Not(condition), And(condition, constraint)))
                constraints.append(constraint)
            for constraint in alt_constraints:
                constraints.append(constraint)
                # constraints.append(Or(condition, And(Not(condition), constraint)))

        return constraints, funs

    def solve(self) -> Optional[List[ModelRef]]:
        models: List[ModelRef] = []

        start = time.time()
        elapsed = 0

        while True and elapsed < self.timeout:
            lo, hi = 0, len(self.unchanged) + 1
            model = None

            while lo < hi and elapsed < self.timeout:
                mid = (lo + hi) // 2
                self.solver.push()
                self.solver.add(self.sum_var >= IntVal(mid))
                if self.solver.check() == sat:
                    lo = mid + 1
                    model = self.solver.model()
                    self.solver.pop()
                    elapsed = time.time() - start
                    continue
                else:
                    hi = mid
                self.solver.pop()
                elapsed = time.time() - start

            elapsed = time.time() - start
            if model is None:
                break

            models.append(model)
            # Removes conditional variables that were not used
            dvars = filter(lambda v: model[v] is not None, self.vars.values())  # type: ignore
            self.solver.add(Not(And([v == model[v] for v in dvars])))

        if elapsed >= self.timeout:
            return None
        return models

    @staticmethod
    def __find_atomic_unit(
        labeled_script: LabeledUnitBlock, attribute: Attribute
    ) -> Optional[AtomicUnit]:
        def aux_find_atomic_unit(code_element: CodeElement) -> Optional[AtomicUnit]:
            if (
                isinstance(code_element, AtomicUnit)
                and attribute in code_element.attributes
            ):
                return code_element
            elif isinstance(code_element, Block):
                for statement in code_element.statements:
                    result = aux_find_atomic_unit(statement)
                    if result is not None:
                        return result
            return None

        code_elements = (
            labeled_script.script.statements + labeled_script.script.atomic_units
        )
        for code_element in code_elements:
            result = aux_find_atomic_unit(code_element)
            if result is not None:
                return result

        raise ValueError(f"Attribute {attribute} not found in the script")

    # TODO: improve way to identify sketch
    def __is_sketch(self, codeelement: CodeElement) -> bool:
        return codeelement.line < 0 and codeelement.column < 0

    def apply_patch(
        self, model_ref: ModelRef, labeled_script: LabeledUnitBlock
    ) -> None:
        changed: List[Tuple[int, Any]] = []

        for label, unchanged in self.unchanged.items():
            if model_ref[unchanged] == 0:  # type: ignore
                hole = self.holes[f"loc-{label}"]
                changed.append((label, model_ref[hole]))

        for change in changed:
            label, value = change
            value = value.as_string()
            codeelement = labeled_script.get_codeelement(label)
            if not isinstance(codeelement, Attribute):
                continue

            if self.__is_sketch(codeelement):
                atomic_unit = labeled_script.get_sketch_location(codeelement)
                if not isinstance(atomic_unit, AtomicUnit):
                    raise RuntimeError("Atomic unit not found")

                atomic_unit_type = NamesDatabase.get_au_type(
                    atomic_unit.type, labeled_script.tech
                )
                name = NamesDatabase.reverse_attr_name(
                    codeelement.name, atomic_unit_type, labeled_script.tech
                )
                codeelement.name = name
                atomic_unit.attributes.append(codeelement)
                # Remove sketch label and add regular label
                labeled_script.remove_label(codeelement)
                GLITCHLabeler.label_attribute(labeled_script, atomic_unit, codeelement)
            else:
                atomic_unit = PatchSolver.__find_atomic_unit(
                    labeled_script, codeelement
                )

            # Remove attributes that are not defined
            if value == UNDEF and isinstance(atomic_unit, AtomicUnit):
                atomic_unit.attributes.remove(codeelement)
                labeled_script.remove_label(codeelement)
            elif isinstance(atomic_unit, AtomicUnit):
                codeelement.value = NamesDatabase.reverse_attr_value(
                    value, codeelement.name, atomic_unit.type, labeled_script.tech
                )
