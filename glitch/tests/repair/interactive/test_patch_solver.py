from z3 import ModelRef
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.solver import PatchSolver
from glitch.parsers.cmof import PuppetParser
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech

puppet_script_1 = """
file { '/var/www/customers/public_html/index.php':
    path => '/var/www/customers/public_html/index.php',
    content => '<html><body><h1>Hello World</h1></body></html>',
    ensure => present,
    mode => '0755',
    owner => 'web_admin'
}
"""

puppet_script_2 = """
    file { '/etc/icinga2/conf.d/test.conf':
    ensure => file,
    tag    => 'icinga2::config::file',
    }
"""

labeled_script = None
statement = None

def setup_patch_solver(
    puppet_script: str, 
):
    global labeled_script, statement
    with NamedTemporaryFile() as f:
        f.write(puppet_script.encode())
        f.flush()
        puppet_parser = PuppetParser().parse_file(f.name, UnitBlockType.script)
        labeled_script = GLITCHLabeler.label(puppet_parser)
        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)


def patch_solver_apply(solver: PatchSolver, model: ModelRef, filesystem: FileSystemState):
        solver.apply_patch(model, labeled_script)
        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)
        assert statement.to_filesystem().state == filesystem.state

# TODO: Refactor tests
# TODO: Remove attributes that are not required (sketched)
        
def test_patch_solver_mode():
    setup_patch_solver(puppet_script_1)
    filesystem = FileSystemState()
    filesystem.state["/var/www/customers/public_html/index.php"] = File(
        mode="0777",
        owner="web_admin",
        content="<html><body><h1>Hello World</h1></body></html>",
    )

    solver = PatchSolver(statement, filesystem)
    model = solver.solve()
    assert model is not None
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[1]] == 1
    assert model[solver.unchanged[2]] == 1
    assert model[solver.unchanged[3]] == 0
    assert model[solver.unchanged[4]] == 1
    assert (
        model[solver.vars["content-1"]]
        == "<html><body><h1>Hello World</h1></body></html>"
    )
    assert model[solver.vars["state-2"]] == "present"
    assert model[solver.vars["mode-3"]] == "0777"
    assert model[solver.vars["owner-4"]] == "web_admin"
    patch_solver_apply(solver, model, filesystem)


def test_patch_solver_owner():
    setup_patch_solver(puppet_script_2)
    filesystem = FileSystemState()
    filesystem.state["/etc/icinga2/conf.d/test.conf"] = File("0431", None, None)
    solver = PatchSolver(statement, filesystem)
    model = solver.solve()
    assert model is not None
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[0]] == 1
    assert model[solver.unchanged[2]] == 1
    assert model[solver.unchanged[3]] == 1
    assert model[solver.unchanged[4]] == 0
    assert (
        model[solver.vars["state-0"]]
        == "present"
    )
    assert model[solver.vars["state-0"]] == "present"
    assert model[solver.vars["sketched-content-2"]] == "glitch-undef"
    assert model[solver.vars["sketched-owner-3"]] == "glitch-undef"
    assert model[solver.vars["sketched-mode-4"]] == "0431"

    patch_solver_apply(solver, model, filesystem)


def test_patch_solver_delete_file():
    setup_patch_solver(puppet_script_1)
    filesystem = FileSystemState()
    filesystem.state["/var/www/customers/public_html/index.php"] = Nil()

    # TODO: For this to work I need to change the way ensures are handled
    # The author of the paper uses the construct If to do this
    # I have to decide if I want to do that or not
    # I think it is possible to do it in a simpler way, similar
    # to the other cases

    solver = PatchSolver(statement, filesystem)
    model = solver.solve()
    assert model is not None
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[1]] == 1
    assert model[solver.unchanged[2]] == 0
    assert model[solver.unchanged[3]] == 1
    assert model[solver.unchanged[4]] == 1
    assert (
        model[solver.vars["content-1"]]
        == "<html><body><h1>Hello World</h1></body></html>"
    )
    assert model[solver.vars["state-2"]] == "absent"
    assert model[solver.vars["mode-3"]] == "0755"
    assert model[solver.vars["owner-4"]] == "web_admin"
    patch_solver_apply(solver, model, filesystem)
