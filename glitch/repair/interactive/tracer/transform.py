from typing import Set
from glitch.repair.interactive.tracer.model import *

def get_affected_paths(syscalls: List[Syscall]) -> Set[str]:
    paths: Set[str] = set()
    write_flags = [
        OpenFlag.O_WRONLY, OpenFlag.O_RDWR, OpenFlag.O_APPEND, 
        OpenFlag.O_CREAT, OpenFlag.O_TRUNC
    ]

    for syscall in syscalls:
        if (isinstance(syscall, SOpen) and 
                any(flag in syscall.flags for flag in write_flags)):
            paths.add(syscall.path)
        elif (isinstance(syscall, SOpenAt) and 
                any(flag in syscall.flags for flag in write_flags)):
            paths.add(syscall.path)
        elif isinstance(syscall, SRename):
            paths.add(syscall.oldpath)
            paths.add(syscall.newpath)
        elif isinstance(syscall, (SUnlink, SUnlinkAt, SRmdir, SMkdir, SMkdirAt)):
            paths.add(syscall.path)

    return paths
