import os

from typing import Set
from glitch.repair.interactive.tracer.model import *

def get_affected_paths(workdir: str, syscalls: List[Syscall]) -> Set[str]:
    """Get all paths affected by the given syscalls.
    
    Args:
        workdir: The working directory of the process before the syscalls were executed.
        syscalls: The syscalls that were executed.

    Returns:
        Set[str]: A set of all paths affected by the given syscalls.
    """
    def abspath(workdir, path):
        if os.path.isabs(path):
            return path
        return os.path.realpath(os.path.join(workdir, path))
    
    paths: Set[str] = set()
    write_flags = [
        OpenFlag.O_WRONLY, OpenFlag.O_RDWR, OpenFlag.O_APPEND, 
        OpenFlag.O_CREAT, OpenFlag.O_TRUNC
    ]

    for syscall in syscalls:
        if (isinstance(syscall, SOpen) and 
                any(flag in syscall.flags for flag in write_flags)):
            paths.add(abspath(workdir, syscall.path))
        elif (isinstance(syscall, SOpenAt) and 
                any(flag in syscall.flags for flag in write_flags)):
            paths.add(abspath(workdir, syscall.path))
        elif isinstance(syscall, SRename):
            paths.add(abspath(workdir, syscall.src))
            paths.add(abspath(workdir, syscall.dst))
        elif isinstance(syscall, (SUnlink, SUnlinkAt, SRmdir, SMkdir, SMkdirAt)):
            paths.add(abspath(workdir, syscall.path))
        elif isinstance(syscall, SChdir):
            workdir = syscall.path

    return paths
