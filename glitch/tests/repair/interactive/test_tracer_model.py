from glitch.repair.interactive.tracer.model import *
from glitch.repair.interactive.tracer.parser import *


def test_tracer_model_rename() -> None:
    syscall = Syscall("rename", ["test", "test~"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SRename)
    assert typed_syscall.src == "test"
    assert typed_syscall.dst == "test~"


def test_tracer_model_open() -> None:
    syscall = Syscall("open", ["test", [OpenFlag.O_RDONLY]], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SOpen)
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == [OpenFlag.O_RDONLY]


def test_tracer_model_openat() -> None:
    syscall = Syscall("openat", ["/", "test", [OpenFlag.O_RDONLY]], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SOpenAt)
    assert typed_syscall.dirfd == "/"
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == [OpenFlag.O_RDONLY]


def test_tracer_model_stat() -> None:
    syscall = Syscall("stat", ["test", "0x7fffc2269490"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SStat)
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == "0x7fffc2269490"


def test_tracer_model_fstat() -> None:
    syscall = Syscall("fstat", ["3", "0x7fffc2269490"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SFStat)
    assert typed_syscall.fd == "3"
    assert typed_syscall.flags == "0x7fffc2269490"


def test_tracer_model_lstat() -> None:
    syscall = Syscall("lstat", ["test", "0x7fffc2269490"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SStat)
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == "0x7fffc2269490"


def test_tracer_model_newfstatat() -> None:
    syscall = Syscall("newfstatat", ["1", "test", "0x7fffc2269490", "0"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SFStatAt)
    assert typed_syscall.dirfd == "1"
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == "0x7fffc2269490"
    assert typed_syscall.oredFlags == "0"


def test_tracer_model_unlink() -> None:
    syscall = Syscall("unlink", ["test"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SUnlink)
    assert typed_syscall.path == "test"


def test_tracer_model_unlinkat() -> None:
    syscall = Syscall("unlinkat", ["1", "test", [UnlinkFlag.AT_REMOVEDIR]], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SUnlinkAt)
    assert typed_syscall.dirfd == "1"
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == [UnlinkFlag.AT_REMOVEDIR]


def test_tracer_model_mkdir() -> None:
    syscall = Syscall("mkdir", ["test", "0777"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SMkdir)
    assert typed_syscall.path == "test"
    assert typed_syscall.mode == "0777"


def test_tracer_model_mkdirat() -> None:
    syscall = Syscall("mkdirat", ["AT_FDCWD", "test", "0777"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SMkdirAt)
    assert typed_syscall.dirfd == "AT_FDCWD"
    assert typed_syscall.path == "test"
    assert typed_syscall.mode == "0777"


def test_tracer_model_rmdir() -> None:
    syscall = Syscall("rmdir", ["test"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SRmdir)
    assert typed_syscall.path == "test"


def test_tracer_model_chdir() -> None:
    syscall = Syscall("chdir", ["test"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SChdir)
    assert typed_syscall.path == "test"
