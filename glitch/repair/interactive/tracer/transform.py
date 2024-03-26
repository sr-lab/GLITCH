import os
from pwd import getpwuid
from typing import Set, Callable

from glitch.repair.interactive.tracer.model import *
from glitch.repair.interactive.filesystem import *


def get_affected_paths(workdir: str, syscalls: List[Syscall]) -> Set[str]:
    """Get all paths affected by the given syscalls.

    Args:
        workdir: The working directory of the process before the syscalls were executed.
        syscalls: The syscalls that were executed.

    Returns:
        Set[str]: A set of all paths affected by the given syscalls.
    """

    def abspath(workdir: str, path: str):
        if os.path.isabs(path):
            return path
        return os.path.realpath(os.path.join(workdir, path))

    paths: Set[str] = set()
    write_flags = [
        OpenFlag.O_WRONLY,
        OpenFlag.O_RDWR,
        OpenFlag.O_APPEND,
        OpenFlag.O_CREAT,
        OpenFlag.O_TRUNC,
    ]

    for syscall in syscalls:
        if isinstance(syscall, SOpen) and any(
            flag in syscall.flags for flag in write_flags
        ):
            paths.add(abspath(workdir, syscall.path))
        elif isinstance(syscall, SOpenAt) and any(
            flag in syscall.flags for flag in write_flags
        ):
            paths.add(abspath(workdir, syscall.path))
        elif isinstance(syscall, SRename):
            paths.add(abspath(workdir, syscall.src))
            paths.add(abspath(workdir, syscall.dst))
        elif isinstance(syscall, (SUnlink, SUnlinkAt, SRmdir, SMkdir, SMkdirAt)):
            paths.add(abspath(workdir, syscall.path))
        elif isinstance(syscall, SChdir):
            workdir = syscall.path

    return paths


def get_file_system_state(files: Set[str]) -> FileSystemState:
    """Get the file system state from the given set of files.

    Args:
        files: A set of files.

    Returns:
        FileSystemState: The file system state.
    """
    fs = FileSystemState()
    get_owner: Callable[[str], str] = lambda f: getpwuid(os.stat(f).st_uid).pw_name
    get_mode: Callable[[str], str] = lambda f: oct(os.stat(f).st_mode & 0o777)[2:]

    for file in files:
        if not os.path.exists(file):
            fs.state[file] = Nil()
        elif os.path.isdir(file):
            fs.state[file] = Dir(get_mode(file), get_owner(file))
        elif os.path.isfile(file):
            with open(file, "rb") as f:
                bytes = f.read()
                try:
                    content = bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content = bytes.hex()
                fs.state[file] = File(get_mode(file), get_owner(file), content)

    return fs
