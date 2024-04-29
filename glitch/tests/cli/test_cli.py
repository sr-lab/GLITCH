import csv
import subprocess
import glitch.__main__ as glitch

from typing import Callable, Set, Tuple, List
from glitch.tech import Tech
from tempfile import NamedTemporaryFile


def test_cli_help():
    run = subprocess.run(["glitch", "--help"], capture_output=True)
    assert run.returncode == 0


def test_cli_get_paths():
    __get_paths_and_title: Callable[[str, str, Tech], Tuple[Set[str], str]] = getattr(
        glitch, "__get_paths_and_title"
    )
    paths, title = __get_paths_and_title(
        "module", "tests/cli/resources/chef_project", Tech.chef
    )
    assert paths == {"tests/cli/resources/chef_project"}
    assert title == "ANALYZING MODULE"

    paths, title = __get_paths_and_title("dataset", "tests/cli/resources/", Tech.chef)
    assert paths == {"tests/cli/resources/chef_project"}
    assert title == "ANALYZING SUBFOLDERS"

    paths, title = __get_paths_and_title(
        "include-all", "tests/cli/resources/chef_project", Tech.chef
    )
    assert paths == {"tests/cli/resources/chef_project/test.rb"}

    paths, title = __get_paths_and_title(
        "project", "tests/cli/resources/chef_project", Tech.chef
    )
    assert paths == {"tests/cli/resources/chef_project"}


def test_cli_analyze():
    with NamedTemporaryFile() as f:
        run = subprocess.run(
            [
                "glitch",
                "--tech",
                "chef",
                "--folder-strategy",
                "include-all",
                "--csv",
                "tests/cli/resources/chef_project",
                f.name,
            ],
            capture_output=True,
        )
        assert run.returncode == 0

        rows: List[List[str]] = []
        with open(f.name, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)

        assert len(rows) == 3
        assert rows[0] == [
            "tests/cli/resources/chef_project/test.rb",
            "8",
            "sec_def_admin",
            "user:'root'",
            "-",
        ]
        assert rows[1] == [
            "tests/cli/resources/chef_project/test.rb",
            "8",
            "sec_hard_secr",
            "user:'root'",
            "-",
        ]
        assert rows[2] == [
            "tests/cli/resources/chef_project/test.rb",
            "8",
            "sec_hard_user",
            "user:'root'",
            "-",
        ]
