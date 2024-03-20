from glitch.repair.interactive.tracer.parser import *


def test_tracer_parser_rename() -> None:
    parsed = parse_tracer_output('[pid 18040] rename("test", "test~") = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "rename"
    assert parsed.args[0] == "test"
    assert parsed.args[1] == "test~"
    assert parsed.exitCode == 0


def test_tracer_parser_stat() -> None:
    parsed = parse_tracer_output(
        '[pid 255] stat("/usr/share/vim/vimfiles/after/scripts.vim", 0x7fffc2269490) = -1 ENOENT (No such file or directory)'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "stat"
    assert parsed.args[0] == "/usr/share/vim/vimfiles/after/scripts.vim"
    assert parsed.args[1] == "0x7fffc2269490"
    assert parsed.exitCode == -1


def test_tracer_parser_open() -> None:
    parsed = parse_tracer_output(
        '[pid 255] open("/lib/x86_64-linux-gnu/libpthread.so.0", O_RDONLY|O_CLOEXEC) = 3'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "open"
    assert parsed.args[0] == "/lib/x86_64-linux-gnu/libpthread.so.0"
    assert parsed.args[1] == [OpenFlag.O_RDONLY, OpenFlag.O_CLOEXEC]
    assert parsed.exitCode == 3


def test_tracer_parser_open_mode() -> None:
    parsed = parse_tracer_output(
        '[pid 105] open("/var/lib/apt/extended_states.tmp", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 25'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "open"
    assert parsed.args[0] == "/var/lib/apt/extended_states.tmp"
    assert parsed.args[1] == [OpenFlag.O_WRONLY, OpenFlag.O_CREAT, OpenFlag.O_TRUNC]
    assert parsed.args[2] == "0666"
    assert parsed.exitCode == 25


def test_tracer_parser_openat() -> None:
    parsed = parse_tracer_output(
        '[pid 33096] openat(AT_FDCWD, "/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc", O_RDONLY|O_CLOEXEC) = 3'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "openat"
    assert parsed.args[0] == "AT_FDCWD"
    assert (
        parsed.args[1]
        == "/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc"
    )
    assert parsed.args[2] == [OpenFlag.O_RDONLY, OpenFlag.O_CLOEXEC]
    assert parsed.exitCode == 3


def test_tracer_parser_openat_mode() -> None:
    parsed = parse_tracer_output(
        '[pid 33096] openat(AT_FDCWD, "/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc", O_RDONLY|O_CLOEXEC, 0666) = 3'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "openat"
    assert parsed.args[0] == "AT_FDCWD"
    assert (
        parsed.args[1]
        == "/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc"
    )
    assert parsed.args[2] == [OpenFlag.O_RDONLY, OpenFlag.O_CLOEXEC]
    assert parsed.args[3] == "0666"
    assert parsed.exitCode == 3


def test_tracer_parser_newfstatat() -> None:
    parsed = parse_tracer_output(
        '[pid 33096] newfstatat(AT_FDCWD, "/usr/lib/python3/dist-packages/mercurial/error.py", {st_dev=makedev(0x103, 0x3), st_ino=14852531, st_mode=S_IFREG|0644, st_nlink=1, st_uid=0, st_gid=0, st_blksize=4096, st_blocks=24, st_size=8377, st_atime=1684251578 /* 2023-05-16T16:39:38.917367753+0100 */, st_atime_nsec=917367753, st_mtime=1684251578 /* 2023-05-16T16:39:38.917367753+0100 */, st_mtime_nsec=917367753, st_ctime=1684251578 /* 2023-05-16T16:39:38.917367753+0100 */, st_ctime_nsec=917367753}, 0) = 0'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "newfstatat"
    assert parsed.args[0] == "AT_FDCWD"
    assert parsed.args[1] == "/usr/lib/python3/dist-packages/mercurial/error.py"
    assert parsed.args[2] == {
        "st_dev": Call("makedev", ["0x103", "0x3"]),
        "st_ino": "14852531",
        "st_mode": BinaryOperation("S_IFREG", "0644", "|"),
        "st_nlink": "1",
        "st_uid": "0",
        "st_gid": "0",
        "st_blksize": "4096",
        "st_blocks": "24",
        "st_size": "8377",
        "st_atime": "1684251578",
        "st_atime_nsec": "917367753",
        "st_mtime": "1684251578",
        "st_mtime_nsec": "917367753",
        "st_ctime": "1684251578",
        "st_ctime_nsec": "917367753",
    }
    assert parsed.args[3] == "0"
    assert parsed.exitCode == 0


def test_tracer_parser_newfstatat_empty_path() -> None:
    parsed = parse_tracer_output(
        '[pid 33096] newfstatat(3, "", {st_dev=makedev(0x103, 0x3), st_ino=14852531, st_mode=S_IFREG|0644, st_nlink=1, st_uid=0, st_gid=0, st_blksize=4096, st_blocks=24, st_size=8377, st_atime=1684251578 /* 2023-05-16T16:39:38.917367753+0100 */, st_atime_nsec=917367753, st_mtime=1684251578 /* 2023-05-16T16:39:38.917367753+0100 */, st_mtime_nsec=917367753, st_ctime=1684251578 /* 2023-05-16T16:39:38.917367753+0100 */, st_ctime_nsec=917367753}, AT_EMPTY_PATH) = 0'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "newfstatat"
    assert parsed.args[0] == "3"
    assert parsed.args[1] == ""
    assert parsed.args[2] == {
        "st_dev": Call("makedev", ["0x103", "0x3"]),
        "st_ino": "14852531",
        "st_mode": BinaryOperation("S_IFREG", "0644", "|"),
        "st_nlink": "1",
        "st_uid": "0",
        "st_gid": "0",
        "st_blksize": "4096",
        "st_blocks": "24",
        "st_size": "8377",
        "st_atime": "1684251578",
        "st_atime_nsec": "917367753",
        "st_mtime": "1684251578",
        "st_mtime_nsec": "917367753",
        "st_ctime": "1684251578",
        "st_ctime_nsec": "917367753",
    }
    assert parsed.args[3] == [ORedFlag.AT_EMPTY_PATH]
    assert parsed.exitCode == 0


def test_tracer_parser_no_pid() -> None:
    parsed = parse_tracer_output('openat(AT_FDCWD, "/dev/null", O_RDWR|O_NOCTTY) = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "openat"
    assert parsed.args[0] == "AT_FDCWD"
    assert parsed.args[1] == "/dev/null"
    assert parsed.args[2] == [OpenFlag.O_RDWR, OpenFlag.O_NOCTTY]
    assert parsed.exitCode == 0


def test_tracer_parser_write() -> None:
    parsed = parse_tracer_output('write(2, "o", 1) = 1')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "write"
    assert parsed.args == ["2", "o", "1"]
    assert parsed.exitCode == 1


def test_tracer_parser_execve() -> None:
    parsed = parse_tracer_output(
        'execve("/usr/bin/ls", ["ls"], ["SHELL=/bin/zsh", "LSCOLORS=Gxfxcxdxbxegedabagacad"]) = 0'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "execve"
    assert parsed.args == [
        "/usr/bin/ls",
        ["ls"],
        ["SHELL=/bin/zsh", "LSCOLORS=Gxfxcxdxbxegedabagacad"],
    ]
    assert parsed.exitCode == 0


def test_tracer_parser_faccessat2() -> None:
    parsed = parse_tracer_output(
        '[pid 47072] faccessat2(AT_FDCWD, "/usr/lib/command-not-found", X_OK, AT_EACCESS) = 0'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "faccessat2"
    assert parsed.args == [
        "AT_FDCWD",
        "/usr/lib/command-not-found",
        "X_OK",
        "AT_EACCESS",
    ]
    assert parsed.exitCode == 0


def test_tracer_parser_mkdirat() -> None:
    parsed = parse_tracer_output('[pid 36388] mkdirat(AT_FDCWD, "test23456", 0777) = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "mkdirat"
    assert parsed.args == ["AT_FDCWD", "test23456", "0777"]
    assert parsed.exitCode == 0


def test_tracer_parser_mkdir() -> None:
    parsed = parse_tracer_output('[pid 36388] mkdir("test23456", 0777) = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "mkdir"
    assert parsed.args == ["test23456", "0777"]
    assert parsed.exitCode == 0


def test_tracer_parser_rmdir() -> None:
    parsed = parse_tracer_output('[pid 36152] rmdir("test23456") = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "rmdir"
    assert parsed.args == ["test23456"]
    assert parsed.exitCode == 0


def test_tracer_parser_unlink() -> None:
    parsed = parse_tracer_output(
        '[pid 47072] unlink("/home/test/.zsh_history.LOCK") = 0'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "unlink"
    assert parsed.args == ["/home/test/.zsh_history.LOCK"]
    assert parsed.exitCode == 0


def test_tracer_parser_unlinkat() -> None:
    parsed = parse_tracer_output(
        '[pid 32850] unlinkat(AT_FDCWD, "test234", AT_REMOVEDIR) = 0'
    )
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "unlinkat"
    assert parsed.args == ["AT_FDCWD", "test234", [UnlinkFlag.AT_REMOVEDIR]]
    assert parsed.exitCode == 0


def test_tracer_parser_unlinkat_0() -> None:
    parsed = parse_tracer_output('[pid 32850] unlinkat(AT_FDCWD, "test234", 0) = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "unlinkat"
    assert parsed.args == ["AT_FDCWD", "test234", "0"]
    assert parsed.exitCode == 0


def test_tracer_parser_chdir() -> None:
    parsed = parse_tracer_output('[pid 32850] chdir("/home/test") = 0')
    assert isinstance(parsed, Syscall)
    assert parsed.cmd == "chdir"
    assert parsed.args == ["/home/test"]
    assert parsed.exitCode == 0
