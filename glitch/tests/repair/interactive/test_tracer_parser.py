from glitch.repair.interactive.tracer_parser import *

def test_tracer_parser_rename():
    parsed = parse_tracer_output('[pid 18040] rename("test", "test~") = 0')
    assert isinstance(parsed, SRename)
    assert parsed.src== 'test'
    assert parsed.dst == 'test~'
    assert parsed.exitCode == 0

def test_tracer_parser_stat():
    parsed = parse_tracer_output('[pid 255] stat("/usr/share/vim/vimfiles/after/scripts.vim", 0x7fffc2269490) = -1 ENOENT (No such file or directory)')
    assert isinstance(parsed, SStat)
    assert parsed.path == '/usr/share/vim/vimfiles/after/scripts.vim'
    assert parsed.flags == ['0x7fffc2269490']
    assert parsed.exitCode == -1

def test_tracer_parser_open():
    parsed = parse_tracer_output('[pid 255] open("/lib/x86_64-linux-gnu/libpthread.so.0", O_RDONLY|O_CLOEXEC) = 3')
    assert isinstance(parsed, SOpen)
    assert parsed.path == '/lib/x86_64-linux-gnu/libpthread.so.0'
    assert parsed.flags == [OpenFlag.O_RDONLY, OpenFlag.O_CLOEXEC]
    assert parsed.mode == None
    assert parsed.exitCode == 3

def test_tracer_parser_open_mode():
    parsed = parse_tracer_output('[pid 105] open("/var/lib/apt/extended_states.tmp", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 25')
    assert isinstance(parsed, SOpen)
    assert parsed.path == '/var/lib/apt/extended_states.tmp'
    assert parsed.flags == [OpenFlag.O_WRONLY, OpenFlag.O_CREAT, OpenFlag.O_TRUNC]
    assert parsed.mode == '0666'
    assert parsed.exitCode == 25

def test_tracer_parser_openat():
    parsed = parse_tracer_output('[pid 33096] openat(AT_FDCWD, "/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc", O_RDONLY|O_CLOEXEC) = 3')
    assert isinstance(parsed, SOpenAt)
    assert parsed.dirfd == 'AT_FDCWD'
    assert parsed.path == '/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc'
    assert parsed.flags == [OpenFlag.O_RDONLY, OpenFlag.O_CLOEXEC]
    assert parsed.mode == None
    assert parsed.exitCode == 3

def test_tracer_parser_openat_mode():
    parsed = parse_tracer_output('[pid 33096] openat(AT_FDCWD, "/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc", O_RDONLY|O_CLOEXEC, 0666) = 3')
    assert isinstance(parsed, SOpenAt)
    assert parsed.dirfd == 'AT_FDCWD'
    assert parsed.path == '/usr/lib/python3/dist-packages/mercurial/__pycache__/error.cpython-310.pyc'
    assert parsed.flags == [OpenFlag.O_RDONLY, OpenFlag.O_CLOEXEC]
    assert parsed.mode == "0666"
    assert parsed.exitCode == 3

def test_tracer_parser_newfstatat():
    parsed = parse_tracer_output('[pid 33096] newfstatat(AT_FDCWD, "/usr/lib/python3/dist-packages/mercurial/error.py", {st_mode=S_IFREG|0644, st_size=18314, ...}, 0) = 0')
    assert isinstance(parsed, SFStatAt)
    assert parsed.dirfd == 'AT_FDCWD'
    assert parsed.path == '/usr/lib/python3/dist-packages/mercurial/error.py'
    assert parsed.flags == ["{st_mode=S_IFREG|0644, st_size=18314, ...}"]
    assert parsed.oredFlags == "0"
    assert parsed.exitCode == 0

def test_tracer_parser_newfstatat_empty_path():
    parsed = parse_tracer_output('[pid 33096] newfstatat(3, "", {st_mode=S_IFREG|0644, st_size=13865, ...}, AT_EMPTY_PATH) = 0')
    assert isinstance(parsed, SFStatAt)
    assert parsed.dirfd == '3'
    assert parsed.path == ''
    assert parsed.flags == ["{st_mode=S_IFREG|0644, st_size=13865, ...}"]
    assert parsed.oredFlags == [ORedFlag.AT_EMPTY_PATH]
    assert parsed.exitCode == 0

def test_tracer_parser_no_pid():
    parsed = parse_tracer_output('openat(AT_FDCWD, "/dev/null", O_RDWR|O_NOCTTY) = 0')
    assert isinstance(parsed, SOpenAt)
    assert parsed.dirfd == 'AT_FDCWD'
    assert parsed.path == '/dev/null'
    assert parsed.flags == [OpenFlag.O_RDWR, OpenFlag.O_NOCTTY]
    assert parsed.mode == None
    assert parsed.exitCode == 0

def test_tracer_parser_unknown():
    parsed = parse_tracer_output('write(2, "o", 1) = 1')
    assert isinstance(parsed, SUnknown)
    assert parsed.cmd == "write"
    assert parsed.args == ["2", 'o', "1"]
    assert parsed.exitCode == 1