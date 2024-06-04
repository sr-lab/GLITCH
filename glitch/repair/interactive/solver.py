import z3
import sys
import uuid
import time
import logging
import glitch.repr.inter as inter

from copy import deepcopy
from typing import List, Callable, Tuple, Any
from z3 import (
    Solver,
    sat,
    If,
    IntVal,
    Bool,
    And,
    Not,
    Int,
    Or,
    Sum,
    Concat,
    StringVal,
    ModelRef,
    Context,
    ExprRef,
)

from glitch.repair.interactive.filesystem import FileSystemState
from glitch.repair.interactive.filesystem import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.values import DefaultValue, UNDEF, UNSUPPORTED
from glitch.repair.interactive.compiler.labeler import LabeledUnitBlock
from glitch.repr.inter import (
    Attribute,
    AtomicUnit,
    CodeElement,
    ElementInfo,
    Variable,
    UnitBlock,
)
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
        debug: bool = False,
    ) -> None:
        self.solver = Solver(ctx=ctx)
        self.debug = debug
        if self.debug:
            self.solver.add = lambda c: self.solver.assert_and_track(c, str(c) + f" ({str(uuid.uuid4())})")  # type: ignore

        self.timeout = timeout
        self.statement = statement
        self.sum_var = Int("sum")
        self.unchanged: Dict[int, ExprRef] = {}
        self.vars: Dict[str, ExprRef] = {}
        self.holes: Dict[str, ExprRef] = {}

        self.possible_strings = self.__get_all_strings(statement)
        self.possible_strings += self.__get_all_strings(filesystem)
        self.possible_strings += [UNDEF, UNSUPPORTED, "", "nil", "file", "dir"]

        # FIXME: check the defaults
        self.__funs = PatchSolver.__Funs(
            lambda p: StringVal(UNDEF),
            lambda p: self.__compile_expr(DefaultValue.DEFAULT_CONTENT)[0],
            lambda p: self.__compile_expr(DefaultValue.DEFAULT_MODE)[0],
            lambda p: self.__compile_expr(DefaultValue.DEFAULT_OWNER)[0],
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

    def __const_string(self, name: str) -> ExprRef:
        var = z3.String(name)
        self.solver.add(Or(*[var == s for s in set(self.possible_strings)]))
        return var

    def __get_all_strings(self, object: Any) -> List[str]:
        result: List[str] = []

        def handle_string(str: str):
            result.append(str)
            result.extend(str.split(":"))

        if getattr(object, "__dict__", None) is None:
            if isinstance(object, (list, set)):
                for val in object:  # type: ignore
                    if isinstance(val, str):
                        handle_string(val)
                    result += self.__get_all_strings(val)
            elif isinstance(object, dict):
                for key, val in object.items():  # type: ignore
                    if isinstance(val, str):
                        handle_string(val)
                    if isinstance(key, str):
                        handle_string(key)
                    result += self.__get_all_strings(key)
                    result += self.__get_all_strings(val)
            return result

        for _, val in object.__dict__.items():
            if isinstance(val, str):
                handle_string(val)
            else:
                result += self.__get_all_strings(val)
        return result

    def __collect_labels(self, statement: PStatement | PExpr) -> List[int]:
        if isinstance(statement, PSeq):
            return self.__collect_labels(statement.lhs) + self.__collect_labels(
                statement.rhs
            )
        elif isinstance(statement, (PCreate, PWrite, PChmod, PChown)):
            labels = []
            if isinstance(statement, PWrite):
                labels = self.__collect_labels(statement.content)
            elif isinstance(statement, PChmod):
                labels = self.__collect_labels(statement.mode)
            elif isinstance(statement, PChown):
                labels = self.__collect_labels(statement.owner)
            return labels + self.__collect_labels(statement.path)
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
        elif isinstance(statement, PEBinOP):
            return self.__collect_labels(statement.lhs) + self.__collect_labels(
                statement.rhs
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

    def __compile_expr(self, expr: PExpr) -> Tuple[ExprRef, List[ExprRef]]:
        constraints: List[ExprRef] = []

        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return StringVal(expr.const.value), constraints
        elif isinstance(expr, PEConst) and isinstance(expr.const, PNum):
            return StringVal(str(expr.const.value)), constraints
        elif isinstance(expr, PEVar) and expr.id.startswith("dejavu-condition-"):
            self.vars[expr.id] = Bool(expr.id)
            return self.vars[expr.id], constraints
        elif isinstance(expr, PEVar) and expr.id in self.vars:
            return self.vars[expr.id], constraints
        elif isinstance(expr, PEVar):
            self.vars[expr.id] = self.__const_string(expr.id)
            return self.vars[expr.id], constraints
        elif isinstance(expr, PEUndef):
            # NOTE: it is an arbitrary string to represent an undefined value
            return StringVal(UNDEF), constraints
        elif isinstance(expr, PRLet):
            if expr.id in self.vars:
                return self.vars[expr.id], constraints
            constraints, _ = self.__generate_soft_constraints(expr, self.__funs)
            return self.vars[expr.id], constraints
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PEq):
            lhs, lhs_constraints = self.__compile_expr(expr.lhs)
            rhs, rhs_constraints = self.__compile_expr(expr.rhs)
            return lhs == rhs, lhs_constraints + rhs_constraints
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PAdd):
            lhs, lhs_constraints = self.__compile_expr(expr.lhs)
            rhs, rhs_constraints = self.__compile_expr(expr.rhs)
            return Concat(lhs, rhs), lhs_constraints + rhs_constraints

        logging.warning(f"Unsupported expression: {expr}")
        return StringVal(UNSUPPORTED), constraints

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
            path, constraints = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("dir"), previous_state_fun(p)
            )
        elif isinstance(statement, PCreate):
            path, constraints = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("file"), previous_state_fun(p)
            )
        elif isinstance(statement, PWrite):
            path, constraints = self.__compile_expr(statement.path)
            content, content_constraints = self.__compile_expr(statement.content)
            constraints += content_constraints
            funs.contents_fun = lambda p: If(
                p == path,
                content,
                previous_contents_fun(p),
            )
        elif isinstance(statement, PRm):
            path, constraints = self.__compile_expr(statement.path)
            funs.state_fun = lambda p: If(
                p == path, StringVal("nil"), previous_state_fun(p)
            )
        elif isinstance(statement, PCp):
            src, src_constraints = self.__compile_expr(statement.src)
            constraints += src_constraints
            dst, dest_constraints = self.__compile_expr(statement.dst)
            constraints += dest_constraints

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
            path, constraints = self.__compile_expr(statement.path)
            mode, mode_constraints = self.__compile_expr(statement.mode)
            constraints += mode_constraints
            funs.mode_fun = lambda p: If(
                p == path,
                mode,
                previous_mode_fun(p),
            )
        elif isinstance(statement, PChown):
            path, constraints = self.__compile_expr(statement.path)
            owner, owner_constraints = self.__compile_expr(statement.owner)
            constraints += owner_constraints
            funs.owner_fun = lambda p: If(
                p == path,
                owner,
                previous_owner_fun(p),
            )
        elif isinstance(statement, PSeq):
            lhs_constraints, funs = self.__generate_soft_constraints(
                statement.lhs, funs
            )
            constraints += lhs_constraints
            rhs_constraints, funs = self.__generate_soft_constraints(
                statement.rhs, funs
            )
            constraints += rhs_constraints
        elif isinstance(statement, PRLet):
            hole, var = self.__const_string(
                f"loc-{statement.label}"
            ), self.__const_string(statement.id)
            self.holes[f"loc-{statement.label}"] = hole
            self.vars[statement.id] = var
            unchanged = self.unchanged[statement.label]
            value, constraints = self.__compile_expr(statement.expr)
            self.solver.add(
                Or(
                    And(unchanged == 1, var == value),
                    And(unchanged == 0, var == hole),
                )
            )
        elif isinstance(statement, PLet):
            if statement.id in self.vars:
                var = self.vars[statement.id]
            else:
                var = self.__const_string(statement.id)
                self.vars[statement.id] = var
            hole = self.__const_string(f"loc-{statement.id}-{statement.label}")
            self.holes[f"loc-{statement.label}"] = hole

            value, constraints = self.__compile_expr(statement.expr)
            constraints.append(var == value)
            constraints.append(var == hole)
            expr_constraints, funs = self.__generate_soft_constraints(
                statement.expr, funs
            )
            constraints += expr_constraints
            body_constraints, funs = self.__generate_soft_constraints(
                statement.body, funs
            )
            constraints += body_constraints
        elif isinstance(statement, PIf):
            condition, constraints = self.__compile_expr(statement.pred)

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
                if self.debug:
                    print(self.solver.unsat_core(), file=sys.stderr)
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

        labeled_script.add_label(attribute.name, attribute)

    def __delete_code_element(
        self, labeled_script: LabeledUnitBlock, ce: CodeElement
    ):
        path = labeled_script.script.path
        with open(path, "r") as f:
            lines = f.readlines()

        line = ce.line - 1
        lines[line] = (
            lines[line][: ce.column - 1] + lines[line][ce.end_column :]
        )
        if lines[line].strip() == "":
            lines.pop(line)

        with open(path, "w") as f:
            f.writelines(lines)

    def __delete_attribute(
        self,
        labeled_script: LabeledUnitBlock,
        ce: AtomicUnit | UnitBlock,
        attribute: Attribute,
    ) -> None:
        labeled_script.remove_label(attribute)
        if attribute in ce.attributes:
            ce.attributes.remove(attribute)
        self.__delete_code_element(labeled_script, attribute)

    def __delete_variable(
        self,
        labeled_script: LabeledUnitBlock,
        ce: UnitBlock,
        variable: Variable,
    ):
        labeled_script.remove_label(variable)
        if variable in ce.variables:
            ce.variables.remove(variable)
        self.__delete_code_element(labeled_script, variable)
    
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
            if old_line[start:end].startswith('"') or codeelement.code.startswith('"'):
                value = f'"{value}"'
            elif old_line[start:end].startswith("'") or codeelement.code.startswith(
                "'"
            ):
                value = f"'{value}'"
            if old_line[end - 1] == "\n":
                value = f"{value}\n"
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

        # Track attributes that became undefined
        for hole in self.holes:
            var = self.holes[hole]
            if model_ref[var].as_string() == UNDEF:  # type: ignore
                if hole.rsplit("-", 1)[0].endswith("-"):  # Avoid sketches
                    continue
                label = int(hole.rsplit("-", 1)[-1])
                if label not in self.unchanged:  # Make sure it is not a literal
                    changed.append((label, model_ref[var]))

        changed_elements: List[
            Tuple[inter.String | inter.Null | inter.KeyValue, str, ElementInfo]
        ] = []

        for change in changed:
            label, value = change
            value = value.as_string()
            codeelement = labeled_script.get_codeelement(label)

            assert isinstance(codeelement, (inter.Expr, inter.KeyValue))
            if not isinstance(codeelement, (inter.String, inter.Null, inter.KeyValue)):
                # HACK: This allows to fix unsupported expressions
                codeelement = inter.String(
                    value, ElementInfo.from_code_element(codeelement)
                )
                codeelement.code = "''"

            if isinstance(codeelement, inter.KeyValue) and value == UNDEF:
                changed_elements.append(
                    (codeelement, value, ElementInfo.from_code_element(codeelement))
                )
                continue

            kv = labeled_script.get_location(codeelement)
            if not self.__is_sketch(codeelement) or isinstance(kv, Variable):
                changed_elements.append(
                    (codeelement, value, ElementInfo.from_code_element(codeelement))
                )
            elif isinstance(kv, Attribute):
                au = labeled_script.get_location(kv)
                assert isinstance(au, AtomicUnit)
                info = ElementInfo.from_code_element(au.attributes[-1])
                info.line, info.column = info.line + 1, 0
                changed_elements.append((codeelement, value, info))

        # The sort is necessary to avoid problems in the textual changes
        changed_elements.sort(key=lambda x: (x[2].line, x[2].column), reverse=True)

        deleted_kvs: List[inter.KeyValue] = []
        for changed_element, value, _ in changed_elements:
            # Deleted Elements
            if value == UNDEF and not self.__is_sketch(changed_element):
                if isinstance(changed_element, inter.KeyValue):
                    kv = changed_element
                else:
                    kv = labeled_script.get_location(changed_element)
                    assert isinstance(kv, inter.KeyValue)
                
                ce = labeled_script.get_location(kv)
                assert isinstance(ce, (AtomicUnit, UnitBlock))

                if kv not in deleted_kvs:
                    if isinstance(kv, Attribute):
                        self.__delete_attribute(labeled_script, ce, kv)
                    elif isinstance(kv, Variable):
                        assert isinstance(ce, UnitBlock)
                        self.__delete_variable(labeled_script, ce, kv)
                    deleted_kvs.append(kv)
            # Modified elements
            elif value != UNDEF and not isinstance(changed_element, inter.KeyValue):
                ce = labeled_script.get_location(changed_element)
                if isinstance(ce, Attribute):
                    attr = ce
                    ce = labeled_script.get_location(attr)
                    assert isinstance(ce, (AtomicUnit, UnitBlock))

                    if isinstance(ce, AtomicUnit) and self.__is_sketch(changed_element):
                        self.__add_sketch_attribute(
                            labeled_script, attr, ce, value, labeled_script.tech
                        )
                    else:
                        if isinstance(ce, AtomicUnit):
                            au_type = NamesDatabase.get_au_type(
                                ce.type, labeled_script.tech
                            )
                            attr_name = NamesDatabase.get_attr_name(
                                attr.name, au_type, labeled_script.tech
                            )
                            value = NamesDatabase.reverse_attr_value(
                                value,
                                attr_name,
                                au_type,
                                labeled_script.tech,
                            )
                        changed_element.value = value
                        attr.value = changed_element
                        self.__modify_codeelement(
                            labeled_script, changed_element, changed_element.value
                        )
                elif isinstance(ce, Variable):
                    changed_element.value = value
                    self.__modify_codeelement(labeled_script, changed_element, value)
