from glitch.tech import Tech
from glitch.parsers.parser import Parser
from glitch.repr.inter import UnitBlock, UnitBlockType

from glitch.repair.interactive.tracer.tracer import STrace
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.tracer.transform import (
    get_affected_paths,
    get_file_system_state,
)
from glitch.repair.interactive.solver import PatchSolver


def run_dejavu(path: str, pid: str, parser: Parser, type: UnitBlockType, tech: Tech):
    inter: UnitBlock | None = parser.parse_file(path, type)
    assert inter is not None
    labeled_script = GLITCHLabeler.label(inter, tech)
    statement = DeltaPCompiler().compile(labeled_script, tech)

    syscalls = STrace(pid).run()
    # FIXME: change workdir
    affected_paths = get_affected_paths("/home", syscalls)
    filesystem_state = get_file_system_state(affected_paths)

    solver = PatchSolver(statement, filesystem_state)
    patches = solver.solve()
    assert patches is not None

    for patch in patches:
        print(patch)
    p = int(input("Enter the patch number you wish to apply: "))

    # FIXME: Apply patch to actual textual script
    solver.apply_patch(patches[p], labeled_script)
