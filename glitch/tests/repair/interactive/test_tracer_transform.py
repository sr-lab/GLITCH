import os
import pytest
import shutil
import tempfile

from glitch.repair.interactive.tracer.transform import (
    get_affected_paths,
    get_file_system_state,
)
from glitch.repair.interactive.tracer.model import *
from glitch.repair.interactive.system import *
from glitch.repair.interactive.values import UNDEF


def test_get_affected_paths() -> None:
    sys_calls: List[Syscall] = [
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
    assert temp_dir is not None
    shutil.rmtree(temp_dir.name)


def test_get_file_system_state(setup_file_system, teardown_file_system) -> None: # type: ignore
    file4 = os.path.join(dir1, "file4")

    files = {dir1, file2, file3, file4}
    fs_state = get_file_system_state(files)

    assert len(fs_state.state) == 4

    assert dir1 in fs_state.state
    assert fs_state.state[dir1].attrs["state"] == "directory"
    assert fs_state.state[dir1].attrs["mode"] == "0775"
    assert fs_state.state[dir1].attrs["owner"] == os.getlogin()

    assert file2 in fs_state.state
    assert fs_state.state[file2].attrs["state"] == "present"
    assert fs_state.state[file2].attrs["mode"] == "0664"
    assert fs_state.state[file2].attrs["owner"] == os.getlogin()
    assert fs_state.state[file2].attrs["content"] == ""

    assert file3 in fs_state.state
    assert fs_state.state[file3].attrs["state"] == "present"
    assert fs_state.state[file3].attrs["mode"] == "0664"
    assert fs_state.state[file3].attrs["owner"] == os.getlogin()
    assert fs_state.state[file3].attrs["content"] == ""

    assert file4 in fs_state.state
    assert fs_state.state[file4].attrs["state"] == "absent"
    assert fs_state.state[file4].attrs["mode"] == UNDEF
    assert fs_state.state[file4].attrs["owner"] == UNDEF
    assert fs_state.state[file4].attrs["content"] == UNDEF
