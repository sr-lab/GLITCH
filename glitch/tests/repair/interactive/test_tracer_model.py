from glitch.repair.interactive.tracer_model import *
from glitch.repair.interactive.tracer_parser import *

def test_tracer_model_rename():
    syscall = Syscall("rename", ["test", "test~"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SRename)
    assert typed_syscall.src == "test"
    assert typed_syscall.dst == "test~"

def test_tracer_model_open():
    syscall = Syscall("open", ["test", [OpenFlag.O_RDONLY]], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SOpen)
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == [OpenFlag.O_RDONLY]

def test_tracer_model_openat():
    syscall = Syscall("openat", ["/", "test", [OpenFlag.O_RDONLY]], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SOpenAt)
    assert typed_syscall.dirfd == "/"
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == [OpenFlag.O_RDONLY]

def test_tracer_model_stat():
    syscall = Syscall("stat", ["test", "0x7fffc2269490"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SStat)
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == "0x7fffc2269490"

def test_tracer_model_fstat():
    syscall = Syscall("fstat", ["3", "0x7fffc2269490"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SFStat)
    assert typed_syscall.fd == "3"
    assert typed_syscall.flags == "0x7fffc2269490"

def test_tracer_model_lstat():
    syscall = Syscall("lstat", ["test", "0x7fffc2269490"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SStat)
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == "0x7fffc2269490"

def test_tracer_model_newfstatat():
    syscall = Syscall("newfstatat", ["1", "test", "0x7fffc2269490", "0"], 0)
    typed_syscall = get_syscall_with_type(syscall)
    assert isinstance(typed_syscall, SFStatAt)
    assert typed_syscall.dirfd == "1"
    assert typed_syscall.path == "test"
    assert typed_syscall.flags == "0x7fffc2269490"
    assert typed_syscall.oredFlags == "0"