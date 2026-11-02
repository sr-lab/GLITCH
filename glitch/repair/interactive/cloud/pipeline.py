"""Run the CloudTrail → Cloud Control → InfraFix repair pipeline."""

from typing import List

from glitch.tech import Tech
from glitch.parsers.parser import Parser
from glitch.repr.inter import UnitBlockType
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.compiler.names_database import NormalizationVisitor
from glitch.repair.interactive.delta_p import PStatement
from glitch.repair.interactive.solver import PatchSolver, PatchApplier
from glitch.repair.interactive.system import SystemState

from glitch.repair.interactive.cloud.cloudtrail import (
    CloudTrailEvent,
    CloudTrailChangeDetector,
)
from glitch.repair.interactive.cloud.cloudcontrol import (
    CloudControlClient,
    build_system_state,
)


def run_cloud_repair(
    path: str,
    parser: Parser,
    tech: Tech,
    events: List[CloudTrailEvent],
    cloud_control: CloudControlClient,
) -> str:
    """Repair the template in place and return its updated content."""
    inter = parser.parse_file(path, UnitBlockType.script)
    assert inter is not None
    NormalizationVisitor(tech).visit(inter)
    labeled = GLITCHLabeler.label(inter, tech)
    statement = DeltaPCompiler(labeled).compile()

    changed = CloudTrailChangeDetector().detect(events)
    assert changed, "CloudTrail events did not identify any changed resource"

    system_state = SystemState()
    for resource in changed:
        live = cloud_control.get_resource(resource.type_name, resource.identifier)
        # TODO: Find the matching resource in the CloudFormation template (physical ID to logical ID).
        resource_state = build_system_state(
            resource.type_name, resource.identifier, live["Properties"], tech
        )
        system_state.state.update(resource_state.state)

    paths = list(system_state.state.keys())
    statement = PStatement.minimize(statement, paths)

    solver = PatchSolver(statement, system_state)
    patches = solver.solve()
    assert patches is not None and len(patches) > 0

    PatchApplier(solver).apply_patch(patches[0], labeled)

    with open(labeled.script.path) as f:
        return f.read()
