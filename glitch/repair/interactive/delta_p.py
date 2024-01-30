from dataclasses import dataclass
from abc import ABC
from typing import Optional

from glitch.repair.interactive.filesystem import *


class PConst(ABC):
    pass


@dataclass
class PStr(PConst):
    value: str


@dataclass
class PNum(PConst):
    value: int


@dataclass
class PBool(PConst):
    value: bool


class PExpr(ABC):
    pass


@dataclass
class PEUndef(PExpr):
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
    value: PExpr


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
class PConcat(PBinOp):
    pass


class PStatement(ABC):
    def __get_str(self, expr: PExpr, vars: Dict[str, PExpr]) -> Optional[str]:
        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return expr.const.value
        elif isinstance(expr, PEVar):
            return self.__get_str(vars[expr.id], vars)

        # FIXME: Change exception type
        raise RuntimeError(f"Unsupported expression, got {expr}")

    def __eval(self, expr: PExpr, vars: Dict[str, PExpr]) -> PExpr:
        if isinstance(expr, PEVar):
            return self.__eval(vars[expr.id], vars)
        elif isinstance(expr, PEUndef) or isinstance(expr, PEConst):
            # NOTE: it is an arbitrary string to represent an undefined value
            return expr
        elif isinstance(expr, PEBinOP) and isinstance(expr.op, PEq):
            if self.__eval(expr.lhs, vars) == self.__eval(expr.rhs, vars):
                return PEConst(PBool(True))
            else:
                return PEConst(PBool(False))
        # TODO: Add support for other operators and expressions

    def to_filesystem(
        self,
        fs: Optional[FileSystemState] = None,
        vars: Optional[Dict[str, PExpr]] = None,
    ) -> FileSystemState:
        if fs is None:
            fs = FileSystemState()
        if vars is None:
            vars = {}

        get_str = lambda expr: self.__get_str(expr, vars)

        if isinstance(self, PSkip):
            return fs
        elif isinstance(self, PMkdir):
            fs.state[get_str(self.path)] = Dir(None, None)
        elif isinstance(self, PCreate):
            fs.state[get_str(self.path)] = File(
                None, None, get_str(self.content)
            )
        elif isinstance(self, PRm):
            fs.state[get_str(self.path)] = Nil()
        elif isinstance(self, PCp):
            fs.state[get_str(self.dst)] = fs.state[get_str(self.src)]
        elif isinstance(self, PChmod):
            path, mode = get_str(self.path), get_str(self.mode)
            if isinstance(fs.state[path], (File, Dir)):
                fs.state[path].mode = mode
        elif isinstance(self, PChown):
            path, owner = get_str(self.path), get_str(self.owner)
            if isinstance(fs.state[path], (File, Dir)):
                fs.state[path].owner = owner
        elif isinstance(self, PSeq):
            fs = self.lhs.to_filesystem(fs, vars)
            fs = self.rhs.to_filesystem(fs, vars)
        elif isinstance(self, PLet):
            vars[self.id] = self.expr
            fs = self.body.to_filesystem(fs, vars)
        elif isinstance(self, PIf):
            eval_pred = self.__eval(self.pred, vars)
            if eval_pred == PEConst(PBool(True)):
                fs = self.cons.to_filesystem(fs, vars)
            elif eval_pred == PEConst(PBool(False)):
                fs = self.alt.to_filesystem(fs, vars)
            else:
                raise RuntimeError(f"Expected boolean, got {eval_pred}")

        return fs


@dataclass
class PSkip(PStatement):
    pass


@dataclass
class PMkdir(PStatement):
    path: PExpr


@dataclass
class PCreate(PStatement):
    path: PExpr
    content: PExpr


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
class Chmod(PStatement):
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
class PLet(PStatement):
    id: str
    expr: PExpr
    label: Optional[int]
    body: PStatement


@dataclass
class PIf(PStatement):
    pred: PExpr
    cons: PStatement
    alt: PStatement
