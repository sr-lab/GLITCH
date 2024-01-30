from copy import deepcopy
from typing import List, Callable, Tuple
from z3 import (
    Solver,
    sat,
    If,
    StringVal,
    String,
    And,
    Int,
    Or,
    Sum,
    ModelRef,
    Z3PPObject,
)

from glitch.repair.interactive.filesystem import FileSystemState
from glitch.repair.interactive.tracer.transform import get_file_system_state
from glitch.repair.interactive.filesystem import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.default_values import DefaultValue

Fun = Callable[[PStatement], Z3PPObject]


class PatchSolver:
    @dataclass
    class __Funs:
        state_fun: Fun
        contents_fun: Fun
        mode_fun: Fun
        owner_fun: Fun

    def __init__(self, statement: PStatement, filesystem: FileSystemState):
        self.solver = Solver()
        self.statement = statement
        self.sum_var = Int("sum")
        self.unchanged = {}
        self.vars = {}
        self.holes = {}

        # FIXME: check the defaults
        self.__funs = PatchSolver.__Funs(
            lambda p: StringVal("file"),  # FIXME get value from default values
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

    def __get_default_fs(self):
        # Returns the current file system state for all the files affected by the script
        # TODO: For now we will consider only the files defined in the script
        fs = self.statement.to_filesystem()
        affected_files = fs.state.keys()
        return get_file_system_state(affected_files)

    def __collect_labels(self, statement: PStatement) -> List[str]:
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
        elif isinstance(statement, PLet):
            return [statement.label] + self.__collect_labels(statement.body)
        return []

    def __compile_expr(self, expr: PExpr):
        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return StringVal(expr.const.value)
        elif isinstance(expr, PEVar):
            self.vars[expr.id] = String(expr.id)
            return self.vars[expr.id]
        elif isinstance(expr, PEUndef):
            # NOTE: it is an arbitrary string to represent an undefined value
            return StringVal("glitch-undef")
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PEq):
            return self.__compile_expr(expr.lhs) == self.__compile_expr(expr.rhs)

        raise ValueError(f"Not supported {expr}")

    def __generate_hard_constraints(self, filesystem: FileSystemState):
        for path, state in filesystem.state.items():
            self.solver.add(self.__funs.state_fun(path) == StringVal(str(state)))
            if state.is_file():
                self.solver.add(
                    self.__funs.contents_fun(path) == StringVal(state.content)
                )
            if state.is_file() or state.is_dir():
                self.solver.add(self.__funs.mode_fun(path) == StringVal(state.mode))
                self.solver.add(self.__funs.owner_fun(path) == StringVal(state.owner))

    def __generate_soft_constraints(
        self, statement: PStatement, funs: __Funs
    ) -> Tuple[List[Z3PPObject], __Funs,]:
        # Avoids infinite recursion
        funs = deepcopy(funs)
        # NOTE: For now it doesn't make sense to update the funs for the
        # default values because the else will always be the default value
        previous_state_fun = funs.state_fun
        previous_contents_fun = funs.contents_fun
        previous_mode_fun = funs.mode_fun
        previous_owner_fun = funs.owner_fun
        constraints = []

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
            unchanged = self.unchanged[statement.label]
            constraints.append(
                Or(
                    And(unchanged == 1, var == self.__compile_expr(statement.expr)),
                    And(unchanged == 0, var == hole),
                )
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

            # NOTE: This works because the only constraints created should
            # always be added. Its kinda of an HACK
            for constraint in cons_constraints:
                # constraints.append(Or(Not(condition), And(condition, constraint)))
                constraints.append(constraint)
            for constraint in alt_constraints:
                constraints.append(constraint)
                # constraints.append(Or(condition, And(Not(condition), constraint)))

        return constraints, funs

    def solve(self) -> Optional[ModelRef]:
        lo, hi = 0, len(self.unchanged)
        model = None

        while lo < hi:
            mid = (lo + hi) // 2
            self.solver.push()
            self.solver.add(self.sum_var >= mid)
            if self.solver.check() == sat:
                lo = mid + 1
                model = self.solver.model()
            else:
                hi = mid
            self.solver.pop()

        # Combinatorial Sketching for Finite Programs by Solar-Lezama et al.

        # TODO: Get multiple solutions

        return model
