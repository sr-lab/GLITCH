import time
import glitch.repr.inter as inter

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
from glitch.repr.inter import Attribute, AtomicUnit, CodeElement, ElementInfo
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.repair.interactive.compiler.template_database import TemplateDatabase
from glitch.tech import Tech

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

        labels = list(set(self.__collect_labels(statement)))
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
        elif isinstance(statement, (PCreate, PWrite, PChmod, PChown)):
            return self.__collect_labels(statement.path)
        elif isinstance(statement, PIf):
            return (
                self.__collect_labels(statement.pred)
                + self.__collect_labels(statement.cons)
                + self.__collect_labels(statement.alt)
            )
        elif isinstance(statement, PRLet):
            return [statement.label]
        elif isinstance(statement, PLet):
            return self.__collect_labels(statement.body) + self.__collect_labels(
                statement.expr
            )
        return []

    def __collect_vars(self, statement: PStatement | PExpr) -> List[str]:
        if isinstance(statement, PSeq):
            return self.__collect_vars(statement.lhs) + self.__collect_vars(
                statement.rhs
            )
        elif isinstance(statement, (PCreate, PWrite, PChmod, PChown)):
            return self.__collect_vars(statement.path)
        elif isinstance(statement, PIf):
            return (
                self.__collect_vars(statement.pred)
                + self.__collect_vars(statement.cons)
                + self.__collect_vars(statement.alt)
            )
        elif isinstance(statement, PLet):
            return (
                [statement.id]
                + self.__collect_vars(statement.body)
                + self.__collect_vars(statement.expr)
            )
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
        elif isinstance(expr, PRLet):
            if expr.id in self.vars:
                return self.vars[expr.id]
            var = String(expr.id)
            self.vars[expr.id] = var
            return var
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
        self, statement: PStatement | PExpr, funs: __Funs
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
            path_constraints, _ = self.__generate_soft_constraints(statement.path, funs)
            constraints += path_constraints
            path = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("file"), previous_state_fun(p)
            )
        elif isinstance(statement, PWrite):
            path_constraints, _ = self.__generate_soft_constraints(statement.path, funs)
            constraints += path_constraints
            path = self.__compile_expr(statement.path)
            funs.contents_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.content),
                previous_contents_fun(p),
            )
        elif isinstance(statement, PRm):
            path_constraints, _ = self.__generate_soft_constraints(statement.path, funs)
            constraints += path_constraints
            path = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("nil"), previous_state_fun(p)
            )
        elif isinstance(statement, PCp):
            src_constraints, _ = self.__generate_soft_constraints(statement.src, funs)
            constraints += src_constraints
            dest_constraints, _ = self.__generate_soft_constraints(statement.dst, funs)
            constraints += dest_constraints

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
            path_constraints, _ = self.__generate_soft_constraints(statement.path, funs)
            constraints += path_constraints
            path = self.__compile_expr(statement.path)
            funs.mode_fun = lambda p: If(
                p == path,
                self.__compile_expr(statement.mode),
                previous_mode_fun(p),
            )
        elif isinstance(statement, PChown):
            path_constraints, _ = self.__generate_soft_constraints(statement.path, funs)
            constraints += path_constraints
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
        elif isinstance(statement, PRLet):
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
        elif isinstance(statement, PLet):
            var = String(statement.id)
            self.vars[statement.id] = var
            constraints.append(var == self.__compile_expr(statement.expr))
            expr_constraints, funs = self.__generate_soft_constraints(
                statement.expr, funs
            )
            constraints += expr_constraints
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

            # It allows to fix variables in the unchosen branch
            unchanged = True
            for label in self.__collect_labels(statement.cons):
                unchanged = And(unchanged, self.unchanged[label] == 1)
            self.solver.add(Or(condition, unchanged))

            fixed_vars = True
            for var in self.__collect_vars(statement.cons):
                fixed_vars = And(fixed_vars, self.vars[var] == "")
            self.solver.add(Or(condition, fixed_vars))

            unchanged = True
            for label in self.__collect_labels(statement.alt):
                unchanged = And(unchanged, self.unchanged[label] == 1)
            self.solver.add(Or(Not(condition), unchanged))

            fixed_vars = True
            for var in self.__collect_vars(statement.alt):
                fixed_vars = And(fixed_vars, self.vars[var] == "")
            self.solver.add(Or(Not(condition), fixed_vars))

            for constraint in cons_constraints:
                constraints.append(Or(Not(condition), And(condition, constraint)))
            for constraint in alt_constraints:
                constraints.append(Or(condition, And(Not(condition), constraint)))

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

    # TODO: improve way to identify sketch
    def __is_sketch(self, codeelement: CodeElement) -> bool:
        return codeelement.line < 0 and codeelement.column < 0

    def __add_sketch_attribute(
        self,
        labeled_script: LabeledUnitBlock,
        attribute: Attribute,
        atomic_unit: AtomicUnit,
        value: str,
        tech: Tech,
    ) -> None:
        is_string = attribute.name != "state"
        au_type = NamesDatabase.get_au_type(atomic_unit.type, tech)
        name = NamesDatabase.reverse_attr_name(
            attribute.name, au_type, labeled_script.tech
        )
        value = NamesDatabase.reverse_attr_value(
            value,
            NamesDatabase.get_attr_name(attribute.name, au_type, labeled_script.tech),
            au_type,
            labeled_script.tech,
        )
        attribute.name = name
        atomic_unit.attributes.append(attribute)

        path = labeled_script.script.path

        old_value = attribute.value
        assert old_value is not None
        attribute.value = inter.String(
            value,
            ElementInfo.from_code_element(old_value),
        )  # FIXME

        with open(path, "r") as f:
            lines = f.readlines()

        last_attribute = None
        for attr in atomic_unit.attributes:
            if not self.__is_sketch(attr):
                last_attribute = attr
        assert last_attribute is not None
        line = last_attribute.line + 1
        attribute.line = line
        col = len(lines[line - 2]) - len(lines[line - 2].lstrip())
        new_line = TemplateDatabase.get_template(attribute, tech)
        value = value if not is_string else f"'{value}'"
        new_line = col * " " + new_line.format(attribute.name, value)
        lines.insert(line - 1, new_line)

        with open(path, "w") as f:
            f.writelines(lines)

    def __delete_attribute(
        self,
        labeled_script: LabeledUnitBlock,
        atomic_unit: AtomicUnit,
        attribute: Attribute,
    ) -> None:
        labeled_script.remove_label(attribute)
        if attribute in atomic_unit.attributes:
            atomic_unit.attributes.remove(attribute)

        path = labeled_script.script.path
        with open(path, "r") as f:
            lines = f.readlines()

        line = attribute.line - 1
        lines[line] = (
            lines[line][: attribute.column - 1] + lines[line][attribute.end_column :]
        )
        if lines[line].strip() == "":
            lines.pop(line)

        with open(path, "w") as f:
            f.writelines(lines)

    def __modify_codeelement(
        self,
        labeled_script: LabeledUnitBlock,
        codeelement: CodeElement,
        value: str,
    ):
        with open(labeled_script.script.path, "r") as f:
            lines = f.readlines()
            old_line = lines[codeelement.line - 1]
            start = codeelement.column - 1
            end = codeelement.end_column - 1
            if old_line[start:end].startswith('"'):
                value = f'"{value}"'
            elif old_line[start:end].startswith("'"):
                value = f"'{value}'"
            new_line = old_line[:start] + value + old_line[end:]
            lines[codeelement.line - 1] = new_line

        with open(labeled_script.script.path, "w") as f:
            f.writelines(lines)

    def apply_patch(
        self, model_ref: ModelRef, labeled_script: LabeledUnitBlock
    ) -> None:
        changed: List[Tuple[int, Any]] = []

        for label, unchanged in self.unchanged.items():
            if model_ref[unchanged] == 0:  # type: ignore
                hole = self.holes[f"loc-{label}"]
                changed.append((label, model_ref[hole]))

        added_elements: List[Tuple[inter.String | inter.Null, str]] = []
        deleted_elements: List[Tuple[inter.String | inter.Null, str]] = []

        for change in changed:
            label, value = change
            value = value.as_string()
            codeelement = labeled_script.get_codeelement(label)

            assert isinstance(codeelement, (inter.String, inter.Null))
            if value == UNDEF:
                deleted_elements.append((codeelement, value))
            else:
                added_elements.append((codeelement, value))

        # The sort is necessary to avoid problems in the textual changes
        deleted_elements.sort(key=lambda x: (x[0].line, x[0].column), reverse=True)
        added_elements.sort(key=lambda x: (x[0].line, x[0].column))

        for added_element, value in added_elements:
            attr = labeled_script.get_sketch_location(added_element)
            assert isinstance(attr, Attribute)
            atomic_unit = labeled_script.get_sketch_location(attr)
            assert isinstance(atomic_unit, AtomicUnit)

            if self.__is_sketch(added_element):
                self.__add_sketch_attribute(
                    labeled_script, attr, atomic_unit, value, labeled_script.tech
                )
            else:
                au_type = NamesDatabase.get_au_type(
                    atomic_unit.type, labeled_script.tech
                )
                attr_name = NamesDatabase.get_attr_name(
                    attr.name, au_type, labeled_script.tech
                )
                added_element.value = NamesDatabase.reverse_attr_value(
                    value,
                    attr_name,
                    au_type,
                    labeled_script.tech,
                )
                self.__modify_codeelement(
                    labeled_script, added_element, added_element.value
                )

        for deleted_element, value in deleted_elements:
            attr = labeled_script.get_sketch_location(deleted_element)
            assert isinstance(attr, Attribute)
            atomic_unit = labeled_script.get_sketch_location(attr)
            assert isinstance(atomic_unit, AtomicUnit)
            self.__delete_attribute(labeled_script, atomic_unit, attr)
