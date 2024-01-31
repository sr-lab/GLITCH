from z3 import ModelRef
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.solver import PatchSolver
from glitch.repair.interactive.values import UNDEF
from glitch.parsers.cmof import PuppetParser, AnsibleParser
from glitch.parsers.parser import Parser
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

ansible_script_1 = """
---
- ansible.builtin.file:
    path: "/var/www/customers/public_html/index.php"
    state: file
    owner: "web_admin"
    mode: '0755'
"""

labeled_script = None
statement = None


def setup_patch_solver(
    script: str,
    parser: Parser,
    script_type: UnitBlockType,
    tech: Tech,
):
    global labeled_script, statement
    with NamedTemporaryFile() as f:
        f.write(script.encode())
        f.flush()
        parsed_file = parser.parse_file(f.name, script_type)
        labeled_script = GLITCHLabeler.label(parsed_file, tech)
        statement = DeltaPCompiler.compile(labeled_script, tech)


def patch_solver_apply(
    solver: PatchSolver, model: ModelRef, filesystem: FileSystemState, tech: Tech
):
    solver.apply_patch(model, labeled_script)
    statement = DeltaPCompiler.compile(labeled_script, tech)
    assert statement.to_filesystem().state == filesystem.state


# TODO: Refactor tests
# TODO: Remove sketched attributes that are not required
        
def test_patch_solver_mode():
    setup_patch_solver(
        puppet_script_1, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
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
    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_owner():
    setup_patch_solver(
        puppet_script_2, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
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
    assert model[solver.vars["state-0"]] == "present"
    assert model[solver.vars["sketched-content-2"]] == UNDEF
    assert model[solver.vars["sketched-owner-3"]] == UNDEF
    assert model[solver.vars["sketched-mode-4"]] == "0431"

    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_delete_file():
    setup_patch_solver(
        puppet_script_1, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
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
    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_remove_content():
    setup_patch_solver(
        puppet_script_1, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["/var/www/customers/public_html/index.php"] = File(
        mode="0755", owner="web_admin", content=None
    )

    solver = PatchSolver(statement, filesystem)
    model = solver.solve()

    assert model is not None
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[1]] == 0
    assert model[solver.unchanged[2]] == 1
    assert model[solver.unchanged[3]] == 1
    assert model[solver.unchanged[4]] == 1
    assert model[solver.vars["content-1"]] == UNDEF
    assert model[solver.vars["state-2"]] == "present"
    assert model[solver.vars["mode-3"]] == "0755"
    assert model[solver.vars["owner-4"]] == "web_admin"
    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_mode_ansible():
    setup_patch_solver(
        ansible_script_1, AnsibleParser(), UnitBlockType.tasks, Tech.ansible
    )
    filesystem = FileSystemState()
    filesystem.state["/var/www/customers/public_html/index.php"] = File(
        mode="0777",
        owner="web_admin",
        content=None,
    )

    solver = PatchSolver(statement, filesystem)
    model = solver.solve()
    assert model is not None
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[1]] == 1
    assert model[solver.unchanged[2]] == 1
    assert model[solver.unchanged[3]] == 0
    assert model[solver.unchanged[4]] == 1
    assert model[solver.vars["state-1"]] == "present"
    assert model[solver.vars["owner-2"]] == "web_admin"
    assert model[solver.vars["mode-3"]] == "0777"
    assert (
        model[solver.vars["sketched-content-4"]]
        == UNDEF
    )
    patch_solver_apply(solver, model, filesystem, Tech.ansible)
