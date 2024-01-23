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


class PatchSolver:
    __DEFAULT_MODE = "644"  # FIXME: what is the default mode?
    __DEFAULT_OWNER = "root"  # FIXME: what is the default owner?

    def __init__(self, statement: PStatement, filesystem: FileSystemState):
        self.solver = Solver()
        self.statement = statement
        self.sum_var = Int("sum")
        self.unchanged = {}
        self.vars = {}
        self.holes = {}

        # default_fs = self.__get_default_fs()

        # NOTE: Right now having the default filesystem does not make sense
        # for me because the functions will be overrided by the constraints
        # in the file anyway

        self.state_fun = lambda p: StringVal(str(Nil()))
        # for file, state in default_fs.state.items():
        #     self.state_fun = lambda p: If(
        #         p == file, StringVal(str(state)), self.state_fun(p)
        #     )

        self.contents_fun = lambda p: StringVal("")
        # for file, state in default_fs.state.items():
        #     if state.is_file():
        #         self.contents_fun = lambda p: If(
        #             p == file, StringVal(state.content), self.contents_fun(p)
        #         )
        #     elif state.is_dir():
        #         self.contents_fun = lambda p: If(p == file, "", self.contents_fun(p))

        self.mode_fun = lambda p: StringVal(PatchSolver.__DEFAULT_MODE)
        # for file, state in default_fs.state.items():
        #     if state.is_file() or state.is_dir():
        #         self.mode_fun = lambda p: If(
        #             p == file, StringVal(state.mode), self.mode_fun(p)
        #         )

        self.owner_fun = lambda p: StringVal(PatchSolver.__DEFAULT_OWNER)
        # for file, state in default_fs.state.items():
        #     if state.is_file() or state.is_dir():
        #         self.owner_fun = lambda p: If(
        #             p == file, StringVal(state.owner), self.owner_fun(p)
        #         )

        labels = self.__collect_labels(statement)
        for label in labels:
            self.unchanged[label] = Int(f"unchanged-{label}")

        (
            self.state_fun,
            self.contents_fun,
            self.mode_fun,
            self.owner_fun,
        ) = self.__generate_soft_constraints(
            self.statement,
            self.state_fun,
            self.contents_fun,
            self.mode_fun,
            self.owner_fun,
        )
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
        elif isinstance(statement, PLet):
            return [statement.label] + self.__collect_labels(statement.body)
        return []
        # TODO if

    def __compile_expr(self, expr: PExpr):
        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return StringVal(expr.const.value)
        elif isinstance(expr, PEVar):
            self.vars[expr.id] = String(expr.id)
            return self.vars[expr.id]
        raise ValueError(f"Not supported {expr}")

    def __generate_hard_constraints(self, filesystem: FileSystemState):
        for path, state in filesystem.state.items():
            self.solver.add(self.state_fun(path) == StringVal(str(state)))
            if state.is_file():
                self.solver.add(self.contents_fun(path) == StringVal(state.content))
            if state.is_file() or state.is_dir():
                self.solver.add(self.mode_fun(path) == StringVal(state.mode))
                self.solver.add(self.owner_fun(path) == StringVal(state.owner))

    def __generate_soft_constraints(
        self,
        statement: PStatement,
        state_fun: Callable[[PStatement], Z3PPObject],
        contents_fun: Callable[[PStatement], Z3PPObject],
        mode_fun: Callable[[PStatement], Z3PPObject],
        owner_fun: Callable[[PStatement], Z3PPObject],
    ) -> Tuple[
        Callable[[PStatement], Z3PPObject],
        Callable[[PStatement], Z3PPObject],
        Callable[[PStatement], Z3PPObject],
        Callable[[PStatement], Z3PPObject],
    ]:
        # NOTE: For now it doesn't make sense to update the funs for the
        # default values because the else will always be the default value
        previous_state_fun = state_fun
        previous_contents_fun = contents_fun
        previous_mode_fun = mode_fun
        previous_owner_fun = owner_fun

        if isinstance(statement, PSkip):
            pass
        elif isinstance(statement, PMkdir):
            # FIXME: Problem this creates infinite recursion
            path = self.__compile_expr(statement.path)
            state_fun = lambda p: If(p == path, StringVal("dir"), previous_state_fun(p))
        elif isinstance(statement, PCreate):
            path = self.__compile_expr(statement.path)
            state_fun = lambda p: If(
                p == path, StringVal("file"), previous_state_fun(p)
            )
            contents_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.content),
                previous_contents_fun(p),
            )
        elif isinstance(statement, PRm):
            path = self.__compile_expr(statement.path)
            state_fun = lambda p: If(p == path, StringVal("nil"), previous_state_fun(p))
        elif isinstance(statement, PCp):
            dst, src = self.__compile_expr(statement.dst), self.__compile_expr(
                statement.src
            )
            state_fun = lambda p: If(
                p == dst, previous_state_fun(src), previous_state_fun(p)
            )
            contents_fun = lambda p: If(
                p == dst,
                previous_contents_fun(src),
                previous_contents_fun(p),
            )
            mode_fun = lambda p: If(
                p == dst, previous_mode_fun(src), previous_mode_fun(p)
            )
            owner_fun = lambda p: If(
                p == dst, previous_owner_fun(src), previous_owner_fun(p)
            )
        elif isinstance(statement, PChmod):
            path = self.__compile_expr(statement.path)
            mode_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.mode),
                previous_mode_fun(p),
            )
        elif isinstance(statement, PChown):
            path = self.__compile_expr(statement.path)
            owner_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.owner),
                previous_owner_fun(p),
            )
        elif isinstance(statement, PSeq):
            state_fun, contents_fun, mode_fun, owner_fun = self.__generate_soft_constraints(
                statement.lhs, state_fun, contents_fun, mode_fun, owner_fun
            )
            state_fun, contents_fun, mode_fun, owner_fun = self.__generate_soft_constraints(
                statement.rhs, state_fun, contents_fun, mode_fun, owner_fun
            )
        elif isinstance(statement, PLet):
            hole, var = String(f"loc-{statement.label}"), String(statement.id)
            self.holes[f"loc-{statement.label}"] = hole
            self.vars[statement.id] = var
            unchanged = self.unchanged[statement.label]
            self.solver.add(
                Or(
                    And(unchanged == 1, var == self.__compile_expr(statement.expr)),
                    And(unchanged == 0, var == hole),
                )
            )
            state_fun, contents_fun, mode_fun, owner_fun = self.__generate_soft_constraints(
                statement.body, state_fun, contents_fun, mode_fun, owner_fun
            )
        elif isinstance(statement, PIf):
            # TODO
            pass

        return state_fun, contents_fun, mode_fun, owner_fun

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

        return model
