import os
import pytest
import shutil
import tempfile

from glitch.repair.interactive.tracer.transform import (
    get_affected_paths,
    get_file_system_state,
)
from glitch.repair.interactive.tracer.model import *
from glitch.repair.interactive.filesystem import *


def test_get_affected_paths() -> None:
    sys_calls = [
        SOpen("open", ["file1", [OpenFlag.O_WRONLY]], 0),
        SOpenAt("openat", ["0", "file2", [OpenFlag.O_WRONLY]], 0),
        SRename("rename", ["file3", "file8"], 0),
        SUnlink("unlink", ["file7"], 0),
        SUnlinkAt("unlinkat", ["0", "file2"], 0),
        SRmdir("rmdir", ["file1"], 0),
        SMkdir("mkdir", ["file5"], 0),
        SChdir("chdir", ["workdir2"], 0),
        SMkdirAt("mkdirat", ["0", "file1"], 0),
    ]

    assert get_affected_paths("workdir", sys_calls) == {
        os.path.realpath(os.path.join("workdir", "file1")),
        os.path.realpath(os.path.join("workdir2", "file1")),
        os.path.realpath(os.path.join("workdir", "file2")),
        os.path.realpath(os.path.join("workdir", "file3")),
        os.path.realpath(os.path.join("workdir", "file5")),
        os.path.realpath(os.path.join("workdir", "file7")),
        os.path.realpath(os.path.join("workdir", "file8")),
    }


dir1 = ""
file2 = ""
file3 = ""
temp_dir = None


@pytest.fixture
def setup_file_system():
    global dir1, file2, file3, temp_dir
    temp_dir = tempfile.TemporaryDirectory()
    dir1 = os.path.join(temp_dir.name, "dir1")
    file2 = os.path.join(dir1, "file2")
    file3 = os.path.join(dir1, "file3")
    os.mkdir(dir1)
    os.chmod(dir1, 0o775)
    with open(file2, "w"):
        os.chmod(file2, 0o664)
    with open(file3, "w"):
        os.chmod(file3, 0o664)
    yield


@pytest.fixture
def teardown_file_system():
    yield
    shutil.rmtree(temp_dir.name)


def test_get_file_system_state(setup_file_system, teardown_file_system) -> None:
    file4 = os.path.join(dir1, "file4")

    files = {dir1, file2, file3, file4}
    fs_state = get_file_system_state(files)

    assert fs_state.state == {
        dir1: Dir("775", os.getlogin()),
        file2: File("664", os.getlogin(), ""),
        file3: File("664", os.getlogin(), ""),
        file4: Nil(),
    }
