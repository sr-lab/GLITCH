import difflib
import subprocess

from copy import deepcopy
from typing import List
from glitch.tech import Tech
from glitch.parsers.parser import Parser
from glitch.repr.inter import UnitBlock, UnitBlockType
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.tracer.tracer import STrace
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.tracer.transform import (
    get_affected_paths,
    get_file_system_state,
)
from glitch.repair.interactive.solver import PatchSolver
from glitch.repair.interactive.compiler.names_database import NormalizationVisitor
from glitch.repair.interactive.delta_p import PStatement


def run_dejavu(path: str, pid: str, parser: Parser, type: UnitBlockType, tech: Tech):
    inter: UnitBlock | None = parser.parse_file(path, type)
    assert inter is not None
    NormalizationVisitor(tech).visit(inter)
    labeled_script = GLITCHLabeler.label(inter, tech)
    statement = DeltaPCompiler(labeled_script).compile()

    syscalls = STrace(pid).run()
    workdir = subprocess.check_output([f"pwdx {pid}"], shell=True)
    workdir = workdir.decode("utf-8").strip().split(": ")[1]
    sys_affected_paths = list(get_affected_paths(workdir, syscalls))

    for i, path in enumerate(sys_affected_paths):
        print(f"{i}: {path}")
    indexes = input(
        "Enter the indexes for the paths you wish to consider (separated by comma): "
    )
    path_indexes = list(map(int, indexes.split(",")))
    affected_paths: List[str] = [sys_affected_paths[i] for i in path_indexes]
    statement = PStatement.minimize(statement, list(set(affected_paths)))

    filesystem_state = get_file_system_state(set(affected_paths))

    solver = PatchSolver(statement, filesystem_state)
    patches = solver.solve()
    assert patches is not None

    with open(labeled_script.script.path) as f:
        original_file = f.read()

    for i, patch in enumerate(patches):
        copy_labeled_script = deepcopy(labeled_script)
        with NamedTemporaryFile(mode="w+") as f:
            f.write(original_file)
            f.flush()
            copy_labeled_script.script.path = f.name
            solver.apply_patch(patch, copy_labeled_script)

            f.seek(0, 0)
            patch_file = f.read()
            patch = difflib.unified_diff(
                original_file.splitlines(), patch_file.splitlines()
            )
            print("=" * 20 + f" Patch {i} " + "=" * 20)
            print(
                "".join(
                    [line + "\n" if not line.endswith("\n") else line for line in patch]
                )
            )
            print("=" * 49)
    p = int(input("Enter the patch number you wish to apply: "))

    solver.apply_patch(patches[p], labeled_script)
    print(f"Patch applied to file {labeled_script.script.path} successfully!")
