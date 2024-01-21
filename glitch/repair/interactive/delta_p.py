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
    def __get_str(self, expr: PExpr) -> Optional[str]:
        if isinstance(expr, PEConst) and isinstance(expr.const, PStr):
            return expr.const.value
        # FIXME: Change exception type
        raise ValueError(f"Expected string, got {expr}")

    def to_filesystem(self, fs: Optional[FileSystemState] = None) -> FileSystemState:
        if fs is None:
            fs = FileSystemState()
        
        if isinstance(self, PSkip):
            return fs
        elif isinstance(self, PMkdir):
            fs.state[self.__get_str(self.path)] = Dir(None, None)
        elif isinstance(self, PCreate):
            fs.state[self.__get_str(self.path)] = File(None, None, self.__get_str(self.content))
        elif isinstance(self, PRm):
            fs.state[self.__get_str(self.path)] = Nil()
        elif isinstance(self, PCp):
            fs.state[self.__get_str(self.dst)] = fs.state[self.__get_str(self.src)]
        elif isinstance(self, PChmod):
            path, mode = self.__get_str(self.path), self.__get_str(self.mode)
            if isinstance(fs.state[path], (File, Dir)):
                fs.state[path].mode = mode
            else:
                raise ValueError(f"Expected file or directory, got {fs.state[path]}")
        elif isinstance(self, PChown):
            path, owner = self.__get_str(self.path), self.__get_str(self.owner)
            if isinstance(fs.state[path], (File, Dir)):
                fs.state[path].owner = owner
            else:
                raise ValueError(f"Expected file or directory, got {fs.state[path]}")
        elif isinstance(self, PSeq):
            fs = self.lhs.to_filesystem(fs)
            fs = self.rhs.to_filesystem(fs)
        elif isinstance(self, PLet):
            # TODO
            pass
        elif isinstance(self, PIf):
            # TODO
            pass

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