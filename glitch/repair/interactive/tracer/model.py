from dataclasses import dataclass
from typing import Optional, List, Union

from glitch.repair.interactive.tracer.parser import (
    Syscall,
    OpenFlag,
    ORedFlag,
    UnlinkFlag,
)


def get_syscall_with_type(syscall: Syscall) -> Syscall:
    """Transforms a syscall into a more specific type.

    Args:
        syscall: The syscall to transform.

    Returns:
        Syscall: The transformed syscall.
    """
    verbs = {
        "open": "SOpen",
        "openat": "SOpenAt",
        "stat": "SStat",
        "lstat": "SStat",
        "fstat": "SFStat",
        "fstatat": "SFStatAt",
        "fstatat64": "SFStatAt",
        "newfstatat": "SFStatAt",
        "rename": "SRename",
        "mkdir": "SMkdir",
        "mkdirat": "SMkdirAt",
        "rmdir": "SRmdir",
        "unlink": "SUnlink",
        "unlinkat": "SUnlinkAt",
        "chdir": "SChdir",
    }
    if syscall.cmd in verbs:
        return globals()[verbs[syscall.cmd]](
            syscall.cmd, syscall.args, syscall.exitCode
        )
    return syscall


@dataclass
class SChdir(Syscall):
    @property
    def path(self) -> str:
        return self.args[0]


@dataclass
class SStat(Syscall):
    @property
    def path(self) -> str:
        return self.args[0]

    @property
    def flags(self) -> List[str]:
        return self.args[1]


@dataclass
class SFStat(Syscall):
    @property
    def fd(self) -> str:
        return self.args[0]

    @property
    def flags(self) -> List[str]:
        return self.args[1]


@dataclass
class SFStatAt(Syscall):
    @property
    def dirfd(self) -> str:
        return self.args[0]

    @property
    def path(self) -> str:
        return self.args[1]

    @property
    def flags(self) -> List[str]:
        return self.args[2]

    @property
    def oredFlags(self) -> Union[List[ORedFlag], str]:
        return self.args[3]


@dataclass
class SOpen(Syscall):
    @property
    def path(self) -> str:
        return self.args[0]

    @property
    def flags(self) -> List[OpenFlag]:
        return self.args[1]

    @property
    def mode(self) -> Optional[str]:
        if len(self.args) == 2:
            return None
        return self.args[2]


@dataclass
class SOpenAt(Syscall):
    @property
    def dirfd(self) -> str:
        return self.args[0]

    @property
    def path(self) -> str:
        return self.args[1]

    @property
    def flags(self) -> List[OpenFlag]:
        return self.args[2]

    @property
    def mode(self) -> Optional[str]:
        if len(self.args) == 3:
            return None
        return self.args[3]


@dataclass
class SRename(Syscall):
    @property
    def src(self) -> str:
        return self.args[0]

    @property
    def dst(self) -> str:
        return self.args[1]


@dataclass
class SMkdir(Syscall):
    @property
    def path(self) -> str:
        return self.args[0]

    @property
    def mode(self) -> Optional[str]:
        if len(self.args) == 1:
            return None
        return self.args[1]


@dataclass
class SMkdirAt(Syscall):
    @property
    def dirfd(self) -> str:
        return self.args[0]

    @property
    def path(self) -> str:
        return self.args[1]

    @property
    def mode(self) -> Optional[str]:
        if len(self.args) == 2:
            return None
        return self.args[2]


@dataclass
class SRmdir(Syscall):
    @property
    def path(self) -> str:
        return self.args[0]


class SUnlink(Syscall):
    @property
    def path(self) -> str:
        return self.args[0]


class SUnlinkAt(Syscall):
    @property
    def dirfd(self) -> str:
        return self.args[0]

    @property
    def path(self) -> str:
        return self.args[1]

    @property
    def flags(self) -> Union[List[UnlinkFlag], str]:
        return self.args[2]
