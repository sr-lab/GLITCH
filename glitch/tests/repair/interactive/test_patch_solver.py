from z3 import ModelRef
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.solver import PatchSolver
from glitch.repair.interactive.values import UNDEF
from glitch.parsers.puppet import PuppetParser
from glitch.parsers.ansible import AnsibleParser
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

puppet_script_3 = """
file { 'test1':
    ensure => file,
}

file { 'test2':
    ensure => file,
}
"""

puppet_script_4 = """
if $x == 'absent' {
    file {'/usr/sbin/policy-rc.d':
        ensure  => absent,
    }
} else {
    file {'/usr/sbin/policy-rc.d':
        ensure  => present,
    }
}
"""

puppet_script_5 = """
file { '/etc/dhcp/dhclient-enter-hooks':
  content => template('fuel/dhclient-enter-hooks.erb'),
  owner   => 'root',
  group   => 'root',
  mode    => '0755',
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
) -> None:
    global labeled_script, statement
    DeltaPCompiler._condition = 0
    with NamedTemporaryFile() as f:
        f.write(script.encode())
        f.flush()
        parsed_file = parser.parse_file(f.name, script_type)
        labeled_script = GLITCHLabeler.label(parsed_file, tech)
        statement = DeltaPCompiler.compile(labeled_script, tech)


def patch_solver_apply(
    solver: PatchSolver,
    model: ModelRef,
    filesystem: FileSystemState,
    tech: Tech,
    n_filesystems: int = 1,
) -> None:
    solver.apply_patch(model, labeled_script)
    statement = DeltaPCompiler.compile(labeled_script, tech)
    filesystems = statement.to_filesystems()
    assert len(filesystems) == n_filesystems
    assert any(fs.state == filesystem.state for fs in filesystems)


# TODO: Refactor tests


def test_patch_solver_if() -> None:
    setup_patch_solver(
        puppet_script_4, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["/usr/sbin/policy-rc.d"] = File(None, None, None)

    solver = PatchSolver(statement, filesystem)
    models = solver.solve()
    assert len(models) == 2

    assert models[0][solver.sum_var] == 8
    assert models[0][solver.vars["dejavu-condition-1"]]
    assert not models[0][solver.vars["dejavu-condition-2"]]
    assert models[0][solver.vars["state-0"]] == "absent"
    assert models[0][solver.vars["state-1"]] == "present"

    assert models[1][solver.sum_var] == 7
    assert not models[1][solver.vars["dejavu-condition-1"]]
    assert models[1][solver.vars["dejavu-condition-2"]]
    assert models[1][solver.vars["state-0"]] == "present"
    assert models[1][solver.vars["state-1"]] == "present"

    patch_solver_apply(solver, models[0], filesystem, Tech.puppet, n_filesystems=2)


def test_patch_solver_mode() -> None:
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
    models = solver.solve()
    assert len(models) == 1
    model = models[0]
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


def test_patch_solver_owner() -> None:
    setup_patch_solver(
        puppet_script_2, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["/etc/icinga2/conf.d/test.conf"] = File(None, "new", None)
    solver = PatchSolver(statement, filesystem)
    models = solver.solve()
    assert len(models) == 1
    model = models[0]
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[0]] == 1
    assert model[solver.unchanged[2]] == 1
    assert model[solver.unchanged[3]] == 0
    assert model[solver.unchanged[4]] == 1
    assert model[solver.vars["state-0"]] == "present"
    assert model[solver.vars["sketched-content-2"]] == UNDEF
    assert model[solver.vars["sketched-owner-3"]] == "new"
    assert model[solver.vars["sketched-mode-4"]] == UNDEF

    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_two_files() -> None:
    setup_patch_solver(
        puppet_script_3, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["test1"] = File(None, "new", None)
    filesystem.state["test2"] = File("0666", None, None)
    solver = PatchSolver(statement, filesystem)
    models = solver.solve()
    assert len(models) == 1
    model = models[0]
    assert model[solver.sum_var] == 6

    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_delete_file() -> None:
    setup_patch_solver(
        puppet_script_1, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["/var/www/customers/public_html/index.php"] = Nil()

    solver = PatchSolver(statement, filesystem)
    models = solver.solve()
    assert len(models) == 1
    model = models[0]
    assert model[solver.sum_var] == 0
    assert model[solver.unchanged[1]] == 0
    assert model[solver.unchanged[2]] == 0
    assert model[solver.unchanged[3]] == 0
    assert model[solver.unchanged[4]] == 0
    assert model[solver.vars["content-1"]] == UNDEF
    assert model[solver.vars["state-2"]] == "absent"
    assert model[solver.vars["mode-3"]] == UNDEF
    assert model[solver.vars["owner-4"]] == UNDEF
    patch_solver_apply(solver, model, filesystem, Tech.puppet)


def test_patch_solver_remove_content() -> None:
    setup_patch_solver(
        puppet_script_1, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["/var/www/customers/public_html/index.php"] = File(
        mode="0755", owner="web_admin", content=None
    )

    solver = PatchSolver(statement, filesystem)
    models = solver.solve()
    assert len(models) == 1
    model = models[0]
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


def test_patch_solver_mode_ansible() -> None:
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
    models = solver.solve()
    assert len(models) == 1
    model = models[0]
    assert model[solver.sum_var] == 3
    assert model[solver.unchanged[1]] == 1
    assert model[solver.unchanged[2]] == 1
    assert model[solver.unchanged[3]] == 0
    assert model[solver.unchanged[4]] == 1
    assert model[solver.vars["state-1"]] == "present"
    assert model[solver.vars["owner-2"]] == "web_admin"
    assert model[solver.vars["mode-3"]] == "0777"
    assert model[solver.vars["sketched-content-4"]] == UNDEF
    patch_solver_apply(solver, model, filesystem, Tech.ansible)


def test_patch_solver_new_attribute_difficult_name() -> None:
    """
    This test requires the solver to create a new attribute "state".
    However, the attribute "state" should be called "ensure" in Puppet,
    so it is required to do the translation back.
    """
    setup_patch_solver(
        puppet_script_5, PuppetParser(), UnitBlockType.script, Tech.puppet
    )
    filesystem = FileSystemState()
    filesystem.state["/etc/dhcp/dhclient-enter-hooks"] = Nil()

    solver = PatchSolver(statement, filesystem)
    models = solver.solve()
    assert len(models) == 1
    patch_solver_apply(solver, models[0], filesystem, Tech.puppet)
