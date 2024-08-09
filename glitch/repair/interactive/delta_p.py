import logging
from dataclasses import dataclass
from abc import ABC
from typing import Optional, List, Union, Callable

from glitch.repair.interactive.filesystem import *


class PConst(ABC):
    pass


@dataclass
class PStr(PConst):
    value: str


@dataclass
class PNum(PConst):
    value: int | float


@dataclass
class PBool(PConst):
    value: bool


class PExpr(ABC):
    pass


@dataclass
class PEUndef(PExpr):
    pass


@dataclass
class PEUnsupported(PExpr):
    pass


@dataclass
class PEConst(PExpr):
    const: PConst


@dataclass
class PEVar(PExpr):
    id: str


@dataclass
class PEUnOP(PExpr):
    op: "PUnOp"
    operand: PExpr


@dataclass
class PEBinOP(PExpr):
    op: "PBinOp"
    lhs: PExpr
    rhs: PExpr


@dataclass
class PUnOp(ABC):
    pass


@dataclass
class PNot(PUnOp):
    pass


@dataclass
class PNeg(PUnOp):
    pass


@dataclass
class PFile(PUnOp):
    pass


@dataclass
class PDir(PUnOp):
    pass


@dataclass
class PDefined(PUnOp):
    pass


class PBinOp(ABC):
    pass


@dataclass
class PAnd(PBinOp):
    pass


@dataclass
class POr(PBinOp):
    pass


@dataclass
class PEq(PBinOp):
    pass


@dataclass
class PLt(PBinOp):
    pass


@dataclass
class PGt(PBinOp):
    pass


@dataclass
class PAdd(PBinOp):
    pass


@dataclass
class PSub(PBinOp):
    pass


@dataclass
class PMultiply(PBinOp):
    pass


@dataclass
class PDivide(PBinOp):
    pass


@dataclass
class PMod(PBinOp):
    pass


@dataclass
class PPower(PBinOp):
    pass


class PStatement(ABC):
    def __get_var(self, id: str, vars: Dict[str, PExpr]) -> Optional[PExpr]:
        scopes = id.split("::")
        while True:
            if "::".join(scopes) in vars:
                return vars["::".join(scopes)]
            if len(scopes) == 1:
                break
            scopes.pop(-2)

        return None

    def __get_str(self, expr: PExpr, vars: Dict[str, PExpr]) -> Optional[str]:
        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return expr.const.value
        elif isinstance(expr, PEConst) and isinstance(expr.const, PNum):
            return str(expr.const.value)
        elif isinstance(expr, PEVar) and self.__get_var(expr.id, vars) is not None:
            res = self.__get_var(expr.id, vars)
            assert res is not None
            return self.__get_str(res, vars)
        elif isinstance(expr, PRLet):
            return self.__get_str(expr.expr, vars)
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PAdd):
            lhs = self.__get_str(expr.lhs, vars)
            rhs = self.__get_str(expr.rhs, vars)
            if lhs is None or rhs is None:
                return None
            return lhs + rhs
        elif isinstance(expr, PEUndef):
            return None
        else:
            logging.warning(f"Unsupported expression, got {expr}")
            return None

    def __eval(self, expr: PExpr, vars: Dict[str, PExpr]) -> PExpr | None:
        if isinstance(expr, PEVar) and expr.id.startswith("dejavu-condition"):
            return expr
        if isinstance(expr, PEVar) and self.__get_var(expr.id, vars) is not None:
            res = self.__get_var(expr.id, vars)
            assert res is not None
            return self.__eval(res, vars)
        elif isinstance(expr, PRLet):
            return self.__eval(expr.expr, vars)
        elif isinstance(expr, PEUndef) or isinstance(expr, PEConst):
            # NOTE: it is an arbitrary string to represent an undefined value
            return expr
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PEq):
            if self.__eval(expr.lhs, vars) == self.__eval(expr.rhs, vars):
                return PEConst(PBool(True))
            else:
                return PEConst(PBool(False))

        return None
        # TODO: Add support for other operators and expressions

    @staticmethod
    def minimize(statement: "PStatement", considered_paths: List[str]) -> "PStatement":
        """Minimize the statement by removing all the paths that are not in the
        list of considered paths. This method is used to minimize the
        statements that are not relevant to the current repair.

        Args:
            statement (PStatement): The statement to minimize.
            considered_paths (List[str]): The list of paths that are relevant
                to the current repair.

        Returns:
            PStatement: The minimized statement.
        """

        def minimize_aux(
            statement: "PStatement", considered_paths: List[str], vars: Dict[str, PExpr]
        ) -> "PStatement":
            if isinstance(statement, (PMkdir, PCreate, PRm, PWrite, PChmod, PChown)):
                path = statement.__get_str(statement.path, vars)
                if path not in considered_paths:
                    return PSkip()
                else:
                    return statement
            elif isinstance(statement, PCp):
                src = statement.__get_str(statement.src, vars)
                dst = statement.__get_str(statement.dst, vars)
                if src not in considered_paths and dst not in considered_paths:
                    return PSkip()
                else:
                    return statement
            elif isinstance(statement, PSeq):
                lhs = minimize_aux(statement.lhs, considered_paths, vars)
                rhs = minimize_aux(statement.rhs, considered_paths, vars)
                if not isinstance(lhs, PSkip) and not isinstance(rhs, PSkip):
                    return PSeq(lhs, rhs)
                elif isinstance(lhs, PSkip):
                    return rhs
                elif isinstance(rhs, PSkip):
                    return lhs
            elif isinstance(statement, PLet):
                vars[statement.id] = statement.expr
                body = minimize_aux(statement.body, considered_paths, vars)
                if not isinstance(body, PSkip):
                    return PLet(
                        statement.id,
                        statement.expr,
                        statement.label,
                        body,
                    )
            elif isinstance(statement, PIf):
                cons = minimize_aux(statement.cons, considered_paths, vars)
                alt = minimize_aux(statement.alt, considered_paths, vars)
                if not isinstance(cons, PSkip) or not isinstance(alt, PSkip):
                    return PIf(
                        statement.pred,
                        cons,
                        alt,
                    )

            return PSkip()

        return minimize_aux(statement, considered_paths, {})

    def to_filesystems(
        self,
        fss: Union[FileSystemState, List[FileSystemState]] = [],
        vars: Optional[Dict[str, PExpr]] = None,
    ) -> List[FileSystemState]:
        if isinstance(fss, FileSystemState):
            fss = [fss.copy()]
        elif fss == []:
            fss = [FileSystemState()]

        if vars is None:
            vars = {}

        res_fss: List[FileSystemState] = []
        for fs in fss:
            get_str: Callable[[PExpr], Optional[str]] = lambda expr: self.__get_str(expr, vars)

            if isinstance(self, (PMkdir, PCreate, PRm, PWrite, PChmod, PChown)):
                path = get_str(self.path)
                if path is None:
                    continue
            else:
                path = ""

            if isinstance(self, PSkip):
                pass
            elif isinstance(self, PMkdir):
                fs.state[path] = Dir(None, None)
            elif isinstance(self, PCreate):
                fs.state[path] = File(None, None, None)
            elif isinstance(self, PWrite):
                content = get_str(self.content)
                file = fs.state.get(path)
                if isinstance(file, File):
                    file.content = content
            elif isinstance(self, PRm):
                fs.state[path] = Nil()
            elif isinstance(self, PCp):
                try:
                    dst, src = get_str(self.dst), get_str(self.src)
                    if dst is None or src is None:
                        continue
                    fs.state[dst] = fs.state[src]
                except ValueError:
                    logging.warning(f"Invalid path: {self.src} {self.dst}")
                    continue
            elif isinstance(self, PChmod):
                mode = get_str(self.mode)
                file = fs.state.get(path)
                if isinstance(file, (File, Dir)):
                    file.mode = mode
            elif isinstance(self, PChown):
                owner = get_str(self.owner)
                file = fs.state.get(path)
                if isinstance(file, (File, Dir)):
                    file.owner = owner
            elif isinstance(self, PSeq):
                fss_lhs = self.lhs.to_filesystems(fs, vars)
                for fs_lhs in fss_lhs:
                    res_fss.extend(self.rhs.to_filesystems(fs_lhs, vars))
                continue
            elif isinstance(self, PLet):
                vars[self.id] = self.expr
                fss_body = self.body.to_filesystems(fs, vars)
                res_fss.extend(fss_body)
                continue
            elif isinstance(self, PIf):
                eval_pred = self.__eval(self.pred, vars)
                cons_fss = self.cons.to_filesystems(fs, vars)
                alt_fss = self.alt.to_filesystems(fs, vars)

                if eval_pred == PEConst(PBool(True)):
                    res_fss.extend(cons_fss)
                elif eval_pred == PEConst(PBool(False)):
                    res_fss.extend(alt_fss)
                else:
                    if self.cons != PSkip():
                        res_fss.extend(cons_fss)
                    if self.alt != PSkip():
                        res_fss.extend(alt_fss)
                    if self.cons == PSkip() and self.alt == PSkip():
                        res_fss.append(fs)
                continue

            res_fss.append(fs)

        return res_fss


@dataclass
class PSkip(PStatement):
    pass


@dataclass
class PMkdir(PStatement):
    path: PExpr


@dataclass
class PWrite(PStatement):
    path: PExpr
    content: PExpr


@dataclass
class PCreate(PStatement):
    path: PExpr


@dataclass
class PRm(PStatement):
    path: PExpr


@dataclass
class PCp(PStatement):
    src: PExpr
    dst: PExpr


@dataclass
class PChmod(PStatement):
    path: PExpr
    mode: PExpr


@dataclass
class PChown(PStatement):
    path: PExpr
    owner: PExpr


@dataclass
class PSeq(PStatement):
    lhs: PStatement
    rhs: PStatement


@dataclass
class PLet(PExpr, PStatement):
    id: str
    expr: PExpr
    label: int
    body: PStatement


@dataclass
class PRLet(PExpr):
    id: str
    expr: PExpr
    label: int


@dataclass
class PIf(PStatement):
    pred: PExpr
    cons: PStatement
    alt: PStatement


class GetStringsVisitor:
    def visit(self, statement: PStatement | PExpr | PConst) -> List[str]:
        if isinstance(statement, PEBinOP):
            return self.visit_binop(statement)
        elif isinstance(statement, PEUnOP):
            return self.visit_unop(statement)
        elif isinstance(statement, PMkdir):
            return self.visit_mkdir(statement)
        elif isinstance(statement, PWrite):
            return self.visit_write(statement)
        elif isinstance(statement, PCreate):
            return self.visit_create(statement)
        elif isinstance(statement, PRm):
            return self.visit_rm(statement)
        elif isinstance(statement, PCp):
            return self.visit_cp(statement)
        elif isinstance(statement, PChmod):
            return self.visit_chmod(statement)
        elif isinstance(statement, PChown):
            return self.visit_chown(statement)
        elif isinstance(statement, PSeq):
            return self.visit_seq(statement)
        elif isinstance(statement, PLet):
            return self.visit_let(statement)
        elif isinstance(statement, PRLet):
            return self.visit_rlet(statement)
        elif isinstance(statement, PIf):
            return self.visit_if(statement)
        elif isinstance(statement, PEConst):
            return self.visit_const(statement)

        return []

    def visit_binop(self, binop: PEBinOP):
        return self.visit(binop.lhs) + self.visit(binop.rhs)
    
    def visit_unop(self, unop: PEUnOP):
        return self.visit(unop.operand)
    
    def visit_mkdir(self, stat: PMkdir):
        return self.visit(stat.path)
    
    def visit_write(self, stat: PWrite):
        return self.visit(stat.path) + self.visit(stat.content)

    def visit_create(self, stat: PCreate):
        return self.visit(stat.path)
    
    def visit_rm(self, stat: PRm):
        return self.visit(stat.path)
    
    def visit_cp(self, stat: PCp):
        return self.visit(stat.src) + self.visit(stat.dst)
    
    def visit_chmod(self, stat: PChmod):
        return self.visit(stat.path) + self.visit(stat.mode)
    
    def visit_chown(self, stat: PChown):
        return self.visit(stat.path) + self.visit(stat.owner)
    
    def visit_seq(self, stat: PSeq):
        return self.visit(stat.lhs) + self.visit(stat.rhs)
    
    def visit_let(self, stat: PLet):
        return self.visit(stat.expr) + self.visit(stat.body)
    
    def visit_rlet(self, stat: PRLet):
        return self.visit(stat.expr)
    
    def visit_if(self, stat: PIf):
        return (
            self.visit(stat.pred) +
            self.visit(stat.cons) + 
            self.visit(stat.alt)
        )

    def visit_const(self, const: PEConst) -> List[str]:
        if isinstance(const.const, PStr):
            return [const.const.value]
        return []
