import os
import unittest
from z3 import ModelRef
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.solver import PatchSolver
from glitch.repair.interactive.values import UNDEF
from glitch.parsers.puppet import PuppetParser
from glitch.parsers.ansible import AnsibleParser
from glitch.parsers.chef import ChefParser
from glitch.parsers.parser import Parser
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech


class TestPatchSolver(unittest.TestCase):
    def setUp(self):
        self.f = NamedTemporaryFile(mode="w+")
        DeltaPCompiler._condition = 0  # type: ignore
        self.labeled_script = None
        self.statement = None

    def tearDown(self) -> None:
        self.f.close()
        assert not os.path.exists(self.f.name)

    def __get_parser(self, tech: Tech) -> Parser:
        if tech == Tech.puppet:
            return PuppetParser()
        elif tech == Tech.ansible:
            return AnsibleParser()
        elif tech == Tech.chef:
            return ChefParser()
        else:
            raise ValueError("Invalid tech")

    def _setup_patch_solver(
        self,
        script: str,
        script_type: UnitBlockType,
        tech: Tech,
    ) -> None:
        self.f.write(script)
        self.f.flush()
        parser = self.__get_parser(tech)
        parsed_file = parser.parse_file(self.f.name, script_type)
        assert parsed_file is not None
        self.labeled_script = GLITCHLabeler.label(parsed_file, tech)
        self.statement = DeltaPCompiler.compile(self.labeled_script, tech)

    def _patch_solver_apply(
        self,
        solver: PatchSolver,
        model: ModelRef,
        filesystem: FileSystemState,
        tech: Tech,
        final_file_content: str,
        n_filesystems: int = 1,
    ) -> None:
        assert self.labeled_script is not None
        solver.apply_patch(model, self.labeled_script)
        statement = DeltaPCompiler.compile(self.labeled_script, tech)
        filesystems = statement.to_filesystems()
        assert len(filesystems) == n_filesystems
        assert any(fs.state == filesystem.state for fs in filesystems)
        with open(self.f.name) as f:
            assert final_file_content == f.read()


class TestPatchSolverPuppetScript1(TestPatchSolver):
    def setUp(self) -> None:
        super().setUp()
        puppet_script_1 = """
            file { '/var/www/customers/public_html/index.php':
                path => '/var/www/customers/public_html/index.php',
                content => '<html><body><h1>Hello World</h1></body></html>',
                ensure => present,
                mode => '0755',
                owner => 'web_admin'
            }
        """
        self._setup_patch_solver(puppet_script_1, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_remove_content(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = File(
            mode="0755", owner="web_admin", content=None
        )

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
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

        result = """
            file { '/var/www/customers/public_html/index.php':
                path => '/var/www/customers/public_html/index.php',
                ensure => present,
                mode => '0755',
                owner => 'web_admin'
            }
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_mode(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = File(
            mode="0777",
            owner="web_admin",
            content="<html><body><h1>Hello World</h1></body></html>",
        )

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
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

        result = """
            file { '/var/www/customers/public_html/index.php':
                path => '/var/www/customers/public_html/index.php',
                content => '<html><body><h1>Hello World</h1></body></html>',
                ensure => present,
                mode => '0777',
                owner => 'web_admin'
            }
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_delete_file(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = Nil()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
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

        result = """
            file { '/var/www/customers/public_html/index.php':
                path => '/var/www/customers/public_html/index.php',
                ensure => absent,
            }
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript2(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_2 = """
            file { '/etc/icinga2/conf.d/test.conf':
            ensure => file,
            tag    => 'icinga2::config::file',
            }
        """
        self._setup_patch_solver(puppet_script_2, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_owner(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/etc/icinga2/conf.d/test.conf"] = File(None, "new", None)

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
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

        result = """
            file { '/etc/icinga2/conf.d/test.conf':
            ensure => file,
            tag    => 'icinga2::config::file',
            owner => 'new',
            }
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript3(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_3 = """
            file { 'test1':
                ensure => file,
            }

            file { 'test2':
                ensure => file,
            }
        """
        self._setup_patch_solver(puppet_script_3, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_two_files(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["test1"] = File(None, "new", None)
        filesystem.state["test2"] = File("0666", None, None)

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 6

        result = """
            file { 'test1':
                ensure => file,
                owner => 'new',
            }

            file { 'test2':
                ensure => file,
                mode => '0666',
            }
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript4(TestPatchSolver):
    def setUp(self):
        super().setUp()
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
        self._setup_patch_solver(puppet_script_4, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_if(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/usr/sbin/policy-rc.d"] = File(None, None, None)

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
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

        result = """
            if $x == 'absent' {
                file {'/usr/sbin/policy-rc.d':
                    ensure  => present,
                }
            } else {
                file {'/usr/sbin/policy-rc.d':
                    ensure  => present,
                }
            }
        """
        self._patch_solver_apply(
            solver, models[1], filesystem, Tech.puppet, result, n_filesystems=2
        )


class TestPatchSolverPuppetScript5(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_5 = """
            file { '/etc/dhcp/dhclient-enter-hooks':
                content => template('fuel/dhclient-enter-hooks.erb'),
                owner   => 'root',
                group   => 'root',
                mode    => '0755',
            }
        """
        self._setup_patch_solver(puppet_script_5, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_new_attribute_difficult_name(self) -> None:
        """
        This test requires the solver to create a new attribute "state".
        However, the attribute "state" should be called "ensure" in Puppet,
        so it is required to do the translation back.
        """
        filesystem = FileSystemState()
        filesystem.state["/etc/dhcp/dhclient-enter-hooks"] = Nil()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
            file { '/etc/dhcp/dhclient-enter-hooks':
                group   => 'root',
                ensure => absent,
            }
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverAnsibleScript1(TestPatchSolver):
    def setUp(self):
        super().setUp()
        ansible_script_1 = """
---
- ansible.builtin.file:
    path: "/var/www/customers/public_html/index.php"
    state: file
    owner: "web_admin"
    mode: '0755'
"""
        self._setup_patch_solver(ansible_script_1, UnitBlockType.tasks, Tech.ansible)

    def test_patch_solver_ansible_mode(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = File(
            mode="0777",
            owner="web_admin",
            content=None,
        )

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
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

        result = """
---
- ansible.builtin.file:
    path: "/var/www/customers/public_html/index.php"
    state: file
    owner: "web_admin"
    mode: '0777'
"""
        self._patch_solver_apply(solver, model, filesystem, Tech.ansible, result)


class TestPatchSolverChefScript1(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_1 = """
        file '/tmp/something' do
            mode '0755'
        end
        """
        self._setup_patch_solver(chef_script_1, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_mode(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/tmp/something"] = File(
            mode="0777",
            owner=None,
            content=None,
        )

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 3
        assert model[solver.unchanged[0]] == 0
        assert model[solver.unchanged[1]] == 1
        assert model[solver.unchanged[2]] == 1
        assert model[solver.unchanged[3]] == 1
        assert model[solver.vars["mode-0"]] == "0777"
        assert model[solver.vars["sketched-state-1"]] == "present"
        assert model[solver.vars["sketched-content-2"]] == UNDEF
        assert model[solver.vars["sketched-owner-3"]] == UNDEF

        result = """
        file '/tmp/something' do
            mode '0777'
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)

    def test_patch_solver_chef_delete(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/tmp/something"] = Nil()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 2
        assert model[solver.unchanged[0]] == 0
        assert model[solver.unchanged[1]] == 0
        assert model[solver.unchanged[2]] == 1
        assert model[solver.unchanged[3]] == 1
        assert model[solver.vars["mode-0"]] == UNDEF
        assert model[solver.vars["sketched-state-1"]] == "absent"
        assert model[solver.vars["sketched-content-2"]] == UNDEF
        assert model[solver.vars["sketched-owner-3"]] == UNDEF

        result = """
        file '/tmp/something' do
            action :delete
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)

    @unittest.skip("Not implemented yet")
    def test_patch_solver_chef_directory(self) -> None:
        filesystem = FileSystemState()
        filesystem.state["/tmp/something"] = Dir(
            mode="0777",
            owner=None,
        )

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 2
        assert model[solver.unchanged[0]] == 0
        assert model[solver.unchanged[1]] == 0
        assert model[solver.unchanged[2]] == 1
        assert model[solver.unchanged[3]] == 1
        assert model[solver.vars["mode-0"]] == "0777"
        assert model[solver.vars["sketched-state-1"]] == "directory"
        assert model[solver.vars["sketched-content-2"]] == UNDEF
        assert model[solver.vars["sketched-owner-3"]] == UNDEF

        result = """
        directory '/tmp/something' do
            mode '0777'
            action :create
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)
