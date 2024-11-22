import z3
import re
import subprocess
import tempfile
import time
import random
import string
import logging
import glitch.repr.inter as inter

from copy import deepcopy
from typing import List, Callable, Tuple, Any, Literal
from z3 import (
    Solver,
    If,
    IntVal,
    BoolVal,
    Bool,
    And,
    Not,
    Int,
    Or,
    Sum,
    Concat,
    StringVal,
    SeqRef,
    Context,
    ExprRef,
)

from glitch.repair.interactive.system import SystemState
from glitch.repair.interactive.system import *
from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.values import UNDEF, UNSUPPORTED
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


class PatchSolver:
    def __init__(
        self,
        statement: PStatement,
        filesystem: SystemState,
        timeout: int = 180,
        memory_limit: int = 1024 * 1024,
        ctx: Optional[Context] = None,
        debug: bool = False,
    ) -> None:
        if ctx is None:
            self.ctx = z3.Context()
        self.debug = debug
        self.memory_limit = memory_limit
        self.constraints: List[ExprRef] = []
        self.timeout = timeout
        self.statement = statement
        self.sum_var = Int("sum", ctx=self.ctx)
        self.unchanged: Dict[int, ExprRef] = {}
        self.vars: Dict[str, ExprRef] = {}
        self.holes: Dict[str, ExprRef] = {}

        self.possible_strings = GetStringsVisitor().visit(statement)
        for path, state in filesystem.state.items():
            self.possible_strings.append(path)
            for key, value in state.attrs.items():
                self.possible_strings.append(key)
                self.possible_strings.append(value)
        self.possible_strings += [
            UNDEF, UNSUPPORTED, "", "absent", "present", "directory"
        ]
        for i in range(len(self.possible_strings)):
            self.possible_strings += self.possible_strings[i].split(":")
        self.possible_strings = list(set(self.possible_strings))

        # FIXME: check the defaults
        self.__funs: Dict[str, Callable[[ExprRef], ExprRef]] = {}

        labels = list(set(self.__collect_labels(statement)))
        for label in labels:
            self.unchanged[label] = Int(f"unchanged-{label}", ctx=self.ctx)

        constraints, self.__funs = self.__generate_soft_constraints(
            self.statement, self.__funs
        )
        self.constraints += constraints

        self.__generate_hard_constraints(filesystem)

        self.constraints.append(Sum(list(self.unchanged.values())) == self.sum_var)

    def __get_var(self, id: str) -> Optional[ExprRef]:
        scopes = id.split(":dejavu:")
        while True:
            if ":dejavu:".join(scopes) in self.vars:
                return self.vars[":dejavu:".join(scopes)]
            if len(scopes) == 1:
                break
            scopes.pop(-2)

        return None

    def __const_string(self, name: str) -> ExprRef:
        var = z3.String(name, ctx=self.ctx)
        self.constraints.append(Or(*[var == s for s in self.possible_strings]))
        return var
    
    def __collect_labels(self, statement: PStatement | PExpr) -> List[int]:
        if isinstance(statement, PSeq):
            return self.__collect_labels(statement.lhs) + self.__collect_labels(
                statement.rhs
            )
        elif isinstance(statement, PAttr):
            return (
                self.__collect_labels(statement.path) +
                self.__collect_labels(statement.value)
            )
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
        elif isinstance(statement, PAttr):
            return self.__collect_vars(statement.path) + self.__collect_vars(
                statement.value
            )
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
            return StringVal(expr.const.value, ctx=self.ctx), constraints
        elif isinstance(expr, PEConst) and isinstance(expr.const, PBool):
            return StringVal(str(expr.const.value).lower(), ctx=self.ctx), constraints
        # TODO: add scope handling. 
        elif isinstance(expr, PEVar) and expr.id.startswith("dejavu-condition-"):
            self.vars[expr.id] = Bool(expr.id, ctx=self.ctx)
            return self.vars[expr.id], constraints
        elif isinstance(expr, PEVar) and self.__get_var(expr.id) is not None:
            var = self.__get_var(expr.id)
            assert var is not None
            return var, constraints
        elif isinstance(expr, PEVar):
            self.vars[expr.id] = self.__const_string(expr.id)
            return self.vars[expr.id], constraints
        elif isinstance(expr, PEUndef):
            # NOTE: it is an arbitrary string to represent an undefined value
            return StringVal(UNDEF, ctx=self.ctx), constraints
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
            if (isinstance(lhs, SeqRef) and lhs.as_string() == UNSUPPORTED) or (
                isinstance(rhs, SeqRef) and rhs.as_string() == UNSUPPORTED
            ):
                return StringVal(UNSUPPORTED, ctx=self.ctx), lhs_constraints + rhs_constraints
            return Concat(lhs, rhs), lhs_constraints + rhs_constraints

        logging.warning(f"Unsupported expression: {expr}")
        return StringVal(UNSUPPORTED, ctx=self.ctx), constraints

    def __generate_hard_constraints(self, filesystem: SystemState) -> None:
        for path, state in filesystem.state.items():
            for key, value in state.attrs.items():
                self.constraints.append(
                    self.__funs[key](StringVal(path, ctx=self.ctx)) == StringVal(value, ctx=self.ctx)
                )

    def __generate_soft_constraints(
        self, statement: PStatement | PExpr, funs: Dict[str, Callable[[ExprRef], ExprRef]]
    ) -> Tuple[List[ExprRef], Dict[str, Callable[[ExprRef], ExprRef]],]:
        # Avoids infinite recursion
        previous_funs = deepcopy(funs)
        funs = deepcopy(funs)
        constraints: List[ExprRef] = []

        if isinstance(statement, PAttr):
            path, constraints = self.__compile_expr(statement.path)
            value, value_constraints = self.__compile_expr(statement.value)
            constraints += value_constraints

            if statement.attr not in previous_funs:
                previous_funs[statement.attr] = lambda p: StringVal(UNDEF, ctx=self.ctx)
            funs[statement.attr] = lambda p: If(
                p == path, value, previous_funs[statement.attr](p), ctx=self.ctx
            )
        elif isinstance(statement, PCp):
            src, src_constraints = self.__compile_expr(statement.src)
            constraints += src_constraints
            dst, dest_constraints = self.__compile_expr(statement.dst)
            constraints += dest_constraints

            funs["state"] = lambda p: If(
                p == dst, previous_funs["state"](src), previous_funs["state"](p), ctx=self.ctx
            )
            funs["content"] = lambda p: If(
                p == dst,
                previous_funs["content"](src),
                previous_funs["content"](p),
                ctx=self.ctx
            )
            funs["mode"] = lambda p: If(
                p == dst, previous_funs["mode"](src), previous_funs["mode"](p), ctx=self.ctx
            )
            funs["owner"] = lambda p: If(
                p == dst, previous_funs["owner"](src), previous_funs["owner"](p), ctx=self.ctx
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
            self.constraints.append(
                Or(
                    And(unchanged == 1, var == value),
                    And(unchanged == 0, var == hole),
                )
            )
        elif isinstance(statement, PLet):
            if statement.id in self.vars:
                var = self.vars[statement.id]
            else:
                var = z3.String(statement.id, ctx=self.ctx)
                self.vars[statement.id] = var
            hole = z3.String(f"loc-{statement.id}-{statement.label}", ctx=self.ctx)
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

            keys = list(funs.keys()) + list(cons_funs.keys()) + list(alt_funs.keys())
            for key in keys:
                if key not in cons_funs:
                    cons_funs[key] = lambda p: StringVal(UNDEF, ctx=self.ctx)
                if key not in alt_funs:
                    alt_funs[key] = lambda p: StringVal(UNDEF, ctx=self.ctx)
                cons = cons_funs[key]
                alt = alt_funs[key]

                # The default attributes are required due to Python's deep binding
                funs[key] = lambda p, cons=cons, alt=alt: If(
                    condition, cons(p), alt(p), ctx=self.ctx
                )
            
            # It allows to fix variables in the unchosen branch
            labels_cons = self.__collect_labels(statement.cons)
            labels_alt = self.__collect_labels(statement.alt)

            unchanged = True
            for label in set(labels_cons) - set(labels_alt):
                unchanged = And(unchanged, self.unchanged[label] == 1)
            self.constraints.append(Or(condition, unchanged))

            unchanged = True
            for label in set(labels_alt) - set(labels_cons):
                unchanged = And(unchanged, self.unchanged[label] == 1)
            self.constraints.append(Or(Not(condition), unchanged))

            vars_cons = self.__collect_vars(statement.cons)
            vars_alt = self.__collect_vars(statement.alt)

            fixed_vars = True
            for var in set(vars_cons) - set(vars_alt):
                fixed_vars = And(fixed_vars, self.vars[var] == "")
            self.constraints.append(Or(condition, fixed_vars))

            fixed_vars = True
            for var in set(vars_alt) - set(vars_cons):
                fixed_vars = And(fixed_vars, self.vars[var] == "")
            self.constraints.append(Or(Not(condition), fixed_vars))

            for constraint in cons_constraints:
                constraints.append(Or(Not(condition), And(condition, constraint)))
            for constraint in alt_constraints:
                constraints.append(Or(condition, And(Not(condition), constraint)))

        return constraints, funs
    
    def __decode_smtlib2_string(self, string: str) -> str:
        """
        Converts SMTLIB2-style Unicode escape sequences in a string to their respective characters.
        
        Parameters:
            string (str): The input string containing SMTLIB2-style Unicode escapes.
            
        Returns:
            str: The decoded string.
        """
        def unicode_replacer(match) -> str: # type: ignore
            hex_value = match.group(1) # type: ignore
            return chr(int(hex_value, 16)) # type: ignore
        
        # Replace all matches in the string
        return re.sub(r'\\u\{([0-9A-Fa-f]+)\}', unicode_replacer, string) # type: ignore

    def __parse_z3_output(self, z3_output: str) -> Dict[str, Any]:
        define_fun_pattern = re.compile(r'\(define-fun (\S+) \(\) (\S+)\n\s+(.+?)\)', re.DOTALL)
        parsed_data: Dict[str, Any] = {}

        for match in define_fun_pattern.finditer(z3_output):
            name = match.group(1)
            if name.startswith("|") and name.endswith("|"):
                name = name[1:-1]
            datatype = match.group(2)
            value = match.group(3).strip()
            
            if datatype == "String":
                # Replace Z3 double-escaped quotes (e.g., "") with single quotes (")
                value = value.replace('""', '"')
                value = value.strip('"')
            elif datatype == "Int":
                value = int(value)
            elif datatype == "Bool" and value == "true":
                value = True
            elif datatype == "Bool" and value == "false":
                value = False
            
            parsed_data[name] = value

        return parsed_data
    


    def __add_named_to_assertions(self, smtlib_code: str) -> Tuple[str, Dict[str, str]]:
        def generate_random_name(length: int = 10):
            return "A" + ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        result: List[str] = []
        names_to_assertions: Dict[str, str] = {}
        stack: List[int] = []
        start_index = None
        inside_assert = False
        i = 0

        while i < len(smtlib_code):
            char = smtlib_code[i]

            if char == '(':
                stack.append(i)
                if not inside_assert and smtlib_code[i:i+7] == "(assert":
                    start_index = i
                    inside_assert = True

            elif char == ')':
                stack.pop()
                if inside_assert and not stack:
                    assert_content = smtlib_code[start_index + 7:i].strip()
                    random_name = generate_random_name()
                    names_to_assertions[random_name] = assert_content
                    transformed_assert = f"(assert (! {assert_content} :named {random_name}))"
                    result.append(transformed_assert)
                    start_index = None
                    inside_assert = False
                    i += 1
                    continue

            if not inside_assert:
                result.append(char)
            i += 1

        return ''.join(result), names_to_assertions
    
    def __run_z3(self, smt2: str, timeout: int) -> str:
        temp = tempfile.NamedTemporaryFile(mode="w+")
        temp.write(smt2)
        temp.flush()
        result = subprocess.run(
            f"ulimit -v {self.memory_limit} && timeout {timeout} z3 -smt2 -model {temp.name}",
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode == 124:
            raise TimeoutError("Solver timed out")
        elif result.returncode in [137, 139]:  
            raise MemoryError("Solver ran out of memory")
        temp.close()
        return result.stdout

    def __run_solver(self, timeout: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        solver = Solver(ctx=self.ctx)
        for constraint in self.constraints:
            solver.add(constraint)

        output = self.__run_z3(solver.to_smt2(), timeout)
        result = output.split("\n")[0]
        if result.strip() == "sat":
            model = output.split("\n", 1)[1]
            model = self.__decode_smtlib2_string(model)
            res: Dict[str, Any] = self.__parse_z3_output(model)

            return True, res
        elif result.strip() == "unsat" and self.debug:
            smt2, names_to_assertions = self.__add_named_to_assertions(solver.to_smt2())
            smt2 = "(set-option :produce-unsat-cores true)\n" + smt2 + "\n(get-unsat-core)"
            output = self.__run_z3(smt2, timeout)
            unsat_core = output.split("\n", 1)[1].strip()[1:-1].split(" ")
            print("=== Unsat core: ===")
            for name in unsat_core:
                print(names_to_assertions[name])
            print("===================")

        return False, None
    
    def __get_solver_value(self, value: Any) -> ExprRef | bool:
        if isinstance(value, str):
            return StringVal(value, ctx=self.ctx)
        elif isinstance(value, int):
            return IntVal(value, ctx=self.ctx)
        elif isinstance(value, bool):
            return BoolVal(value, ctx=self.ctx)
        raise ValueError(f"Unsupported value type: {type(value)}")

    def solve(self) -> List[Dict[str, Any]]:
        models: List[Dict[str, Any]] = []

        start = time.time()
        while True and time.time() - start < self.timeout:
            lo, hi = 0, len(self.unchanged) + 1
            model = None

            while lo < hi and time.time() - start < self.timeout:
                mid = (lo + hi) // 2
                self.constraints.append(self.sum_var >= IntVal(mid, ctx=self.ctx))
                sat, o_model = self.__run_solver(self.timeout - int(time.time() - start))
                if sat:
                    lo = mid + 1
                    model = o_model
                    self.constraints.pop()
                    continue
                else:
                    hi = mid

                self.constraints.pop()

            if model is None:
                break

            models.append(model)
            # Removes conditional variables that were not used
            dvars = list(filter(
                lambda v: str(v) in model, self.vars.values() # type: ignore
            ))

            self.constraints.append(Not(And([v == self.__get_solver_value(model[str(v)]) for v in dvars])))

        if time.time() - start >= self.timeout:
            raise TimeoutError("Solver timed out")

        return models


@dataclass
class PatchChange:
    value: str
    codeelement: CodeElement
    type: Literal["add_sketch", "delete", "modify"]
    info: ElementInfo


class PatchApplier:
    def __init__(self, solver: PatchSolver) -> None:
        self.unchanged = solver.unchanged
        self.holes = solver.holes

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
        # FIXME: There should be a way to change the way we apply the patch
        # according to the technology
        if tech == Tech.terraform and attribute.name == "state":
            return

        name, _ = NamesDatabase.get_attr_pair(
            inter.String(value, ElementInfo(-1, -1, -1, -1, "")),
            attribute.name, 
            atomic_unit.type, 
            tech
        )
        # FIXME
        is_string = (
            name not in ["state", "enabled"] 
            and value not in ["true", "false"]
        )
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
        if last_attribute is None:
            line = atomic_unit.line + 1
            col = 2
        else:
            line = last_attribute.line + 1
            col = len(lines[line - 2]) - len(lines[line - 2].lstrip())
        attribute.line = line
        new_line = TemplateDatabase.get_template(attribute, tech)
        if tech == Tech.terraform:
            value = value if not is_string else f'"{value}"'
        else:
            value = value if not is_string else f"'{value}'"
        new_line = col * " " + new_line.format(attribute.name, value)
        lines.insert(line - 1, new_line)
        if not lines[line - 2].endswith("\n"):
            lines[line - 2] =  lines[line - 2] + "\n"
        with open(path, "w") as f:
            f.writelines(lines)

        labeled_script.add_label(attribute.name, attribute)

    def __delete_code_element(self, labeled_script: LabeledUnitBlock, ce: CodeElement):
        path = labeled_script.script.path
        with open(path, "r") as f:
            lines = f.readlines()

        line = ce.line - 1
        lines[line] = lines[line][: ce.column - 1] + lines[line][ce.end_column :]
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
        if attribute in ce.attributes:
            ce.attributes.remove(attribute)
        self.__delete_code_element(labeled_script, attribute)

    def __delete_variable(
        self,
        labeled_script: LabeledUnitBlock,
        ce: UnitBlock,
        variable: Variable,
    ):
        if variable in ce.variables:
            ce.variables.remove(variable)
        self.__delete_code_element(labeled_script, variable)

    def __modify_codeelement(
        self,
        labeled_script: LabeledUnitBlock,
        codeelement: CodeElement,
        value: str,
        tech: Tech,
    ):
        with open(labeled_script.script.path, "r") as f:
            lines = f.readlines()

            old_line = lines[codeelement.line - 1]
            start = codeelement.column - 1

            if codeelement.line != codeelement.end_line:
                # Cute the other lines
                lines = lines[: codeelement.line] + lines[codeelement.end_line :]
                end = len(old_line) - 1
            else:
                end = codeelement.end_column - 1

            if (
                value not in ["true", "false"] # FIXME
                and (old_line[start:end].startswith('"') or codeelement.code.startswith('"'))
                and (old_line[start:end].endswith('"') or codeelement.code.endswith('"'))
            ):
                value = f'"{value}"'
            elif (
                value not in ["true", "false"] # FIXME
                and (old_line[start:end].startswith("'") or codeelement.code.startswith("'"))
                and (old_line[start:end].endswith("'") or codeelement.code.endswith("'"))
            ):
                value = f"'{value}'"
            elif len(value.split("\n")) > 1:
                value = TemplateDatabase.get_template_for_multiline_string(tech).format(
                    value
                )

            if old_line[end - 1] == "\n":
                value = f"{value}\n"
            new_line = old_line[:start] + value + old_line[end:]
            lines[codeelement.line - 1] = new_line

        with open(labeled_script.script.path, "w") as f:
            f.writelines(lines)
    
    def get_changes(
        self, model_ref: Dict[str, Any], labeled_script: LabeledUnitBlock
    ) -> List[PatchChange]:
        changed: List[Tuple[int, Any]] = []

        for label, unchanged in self.unchanged.items():
            if model_ref[str(unchanged)] == 0:  # type: ignore
                changed.append((label, model_ref[f"loc-{label}"]))

        # Track attributes that became undefined
        for hole in self.holes:
            var = str(self.holes[hole])
            if model_ref[var] == UNDEF:  # type: ignore
                if hole.rsplit("-", 1)[0].endswith("-"):  # Avoid sketches
                    continue
                label = int(hole.rsplit("-", 1)[-1])
                if label not in self.unchanged:  # Make sure it is not a literal
                    changed.append((label, model_ref[var]))

        changes: List[PatchChange] = []

        for change in changed:
            label, value = change
            value = value
            codeelement = labeled_script.get_codeelement(label)

            assert isinstance(codeelement, (inter.Expr, inter.KeyValue))
            if not isinstance(codeelement, (inter.String, inter.Null, inter.KeyValue)):
                # HACK: This allows to fix unsupported expressions
                codeelement = inter.String(
                    value, ElementInfo.from_code_element(codeelement)
                )
                codeelement.code = "''"

            info = ElementInfo.from_code_element(codeelement)
            if value == UNDEF:
                changes.append(PatchChange(value, codeelement, "delete", info))
                continue
            
            kv = labeled_script.get_location(codeelement)
            if not self.__is_sketch(codeelement) or isinstance(kv, Variable):
                changes.append(PatchChange(value, codeelement, "modify", info))
            elif self.__is_sketch(codeelement) and isinstance(kv, Attribute):
                au = labeled_script.get_location(kv)
                assert isinstance(au, AtomicUnit)
                if len(au.attributes) == 0:
                    info = ElementInfo.from_code_element(au)
                else:
                    info = ElementInfo.from_code_element(au.attributes[-1])
                changes.append(PatchChange(value, codeelement, "add_sketch", info))

        # The sort is necessary to avoid problems in the textual changes
        changes.sort(key=lambda x: (x.info.line, x.info.column), reverse=True)
        return changes

    def reverse_changes(
        self, labeled_script: LabeledUnitBlock, changes: List[PatchChange]
    ) -> None:
        def reverse(value: str, attr: str, loc_loc: AtomicUnit) -> Tuple[str, str]:
            attr_name = NamesDatabase.reverse_attr_name(
                attr, loc_loc.type, labeled_script.tech
            )
            value = NamesDatabase.reverse_attr_value(
                value,
                attr,
                loc_loc.type,
                labeled_script.tech,
            )
            return attr_name, value

        for change in changes:
            if isinstance(change.codeelement, (inter.String, inter.Null)):
                loc = labeled_script.get_location(change.codeelement)
                if isinstance(loc, Attribute):
                    loc_loc = labeled_script.get_location(loc)
                    if isinstance(loc_loc, AtomicUnit):
                        loc.name, change.value = reverse(
                            change.value, loc.name, loc_loc
                        )
                elif isinstance(loc, AtomicUnit):
                    # Only for paths in the name
                    _, change.value = reverse(
                        change.value, "path", loc
                    )
                    loc.name = inter.String(change.value, change.info)

    def apply_patch(
        self, model_ref: Dict[str, Any], labeled_script: LabeledUnitBlock
    ) -> None:
        changed_elements = self.get_changes(model_ref, labeled_script)
        self.reverse_changes(labeled_script, changed_elements)
        deleted_kvs: List[inter.KeyValue] = []

        for ce in changed_elements:
            # Deleted Elements
            if ce.type == "delete":
                if isinstance(ce.codeelement, inter.KeyValue):
                    loc = ce.codeelement
                else:
                    loc = labeled_script.get_location(ce.codeelement)
                    assert isinstance(loc, inter.KeyValue)

                loc_loc = labeled_script.get_location(loc)
                assert isinstance(loc_loc, (AtomicUnit, UnitBlock))

                if loc not in deleted_kvs:
                    if isinstance(loc, Attribute):
                        self.__delete_attribute(labeled_script, loc_loc, loc)
                    elif isinstance(loc, Variable):
                        assert isinstance(loc_loc, UnitBlock)
                        self.__delete_variable(labeled_script, loc_loc, loc)
                    deleted_kvs.append(loc)
            # Modified elements
            elif ce.type == "modify":
                loc = labeled_script.get_location(ce.codeelement)
                if isinstance(ce.codeelement, inter.Null):
                    ce.codeelement = inter.String(ce.value, ce.info)
                    # HACK: Allows to add quotes in the modify_codeelement func
                    ce.codeelement.code = "\"\""  
                assert isinstance(ce.codeelement, inter.String)

                if isinstance(loc, Attribute):
                    ce.codeelement.value = ce.value
                    loc.value = ce.codeelement
                    self.__modify_codeelement(
                        labeled_script, ce.codeelement, ce.value, labeled_script.tech
                    )
                elif isinstance(loc, Variable):
                    ce.codeelement.value = ce.value
                    self.__modify_codeelement(labeled_script, ce.codeelement, ce.value, labeled_script.tech)
                elif isinstance(loc, AtomicUnit):
                    ce.codeelement.value = ce.value
                    loc.name = ce.codeelement
                    self.__modify_codeelement(labeled_script, ce.codeelement, ce.value, labeled_script.tech)
            elif ce.type == "add_sketch":
                loc = labeled_script.get_location(ce.codeelement)
                assert isinstance(loc, Attribute)
                loc_loc = labeled_script.get_location(loc)
                assert isinstance(loc_loc, AtomicUnit)
                self.__add_sketch_attribute(
                    labeled_script, loc, loc_loc, ce.value, labeled_script.tech
                ) 
