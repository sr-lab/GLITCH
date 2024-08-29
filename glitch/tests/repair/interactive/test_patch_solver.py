import os
import unittest
from z3 import ModelRef
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.solver import PatchSolver, PatchApplier
from glitch.repair.interactive.values import UNDEF
from glitch.parsers.puppet import PuppetParser
from glitch.parsers.ansible import AnsibleParser
from glitch.parsers.chef import ChefParser
from glitch.parsers.parser import Parser
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repr.inter import UnitBlockType
from glitch.repair.interactive.compiler.names_database import NormalizationVisitor
from glitch.tech import Tech


def get_default_file_state():
    state = State()
    state.attrs["mode"] = UNDEF
    state.attrs["owner"] = UNDEF
    state.attrs["state"] = "present"
    state.attrs["content"] = UNDEF
    return state


def get_nil_file_state():
    state = State()
    state.attrs["mode"] = UNDEF
    state.attrs["owner"] = UNDEF
    state.attrs["state"] = "absent"
    state.attrs["content"] = UNDEF
    return state


class TestPatchSolver(unittest.TestCase):
    def setUp(self):
        self.f = NamedTemporaryFile(mode="w+")
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
        NormalizationVisitor(tech).visit(parsed_file)
        self.labeled_script = GLITCHLabeler.label(parsed_file, tech)
        self.statement = DeltaPCompiler(self.labeled_script).compile()

    def _patch_solver_apply(
        self,
        solver: PatchSolver,
        model: ModelRef,
        filesystem: SystemState,
        tech: Tech,
        final_file_content: str,
        n_filesystems: int = 1,
    ) -> None:
        assert self.labeled_script is not None
        PatchApplier(solver).apply_patch(model, self.labeled_script)
        NormalizationVisitor(tech).visit(self.labeled_script.script)
        statement = DeltaPCompiler(self.labeled_script).compile()
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

    def test_patch_solver_puppet_link(self) -> None:
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = State()
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["state"] = "link"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0755"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "web_admin"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
            file { '/var/www/customers/public_html/index.php':
                path => '/var/www/customers/public_html/index.php',
                ensure => link,
                mode => '0755',
                owner => 'web_admin'
            }
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_remove_content(self) -> None:
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = get_default_file_state()
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["state"] = "present"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0755"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "web_admin"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 4
        assert model[solver.unchanged[5]] == 1
        assert model[solver.unchanged[6]] == 0
        assert model[solver.unchanged[7]] == 1
        assert model[solver.unchanged[8]] == 1
        assert model[solver.vars["content_20672"]] == UNDEF
        assert model[solver.vars["state_14450"]] == "present"
        assert model[solver.vars["mode_18972"]] == "0755"
        assert model[solver.vars["owner_30821"]] == "web_admin"

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
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = State()
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["state"] = "present"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0777"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "web_admin"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = "<html><body><h1>Hello World</h1></body></html>"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 4
        assert model[solver.unchanged[5]] == 1
        assert model[solver.unchanged[6]] == 1
        assert model[solver.unchanged[7]] == 1
        assert model[solver.unchanged[8]] == 0
        assert (
            model[solver.vars["content_20672"]]
            == "<html><body><h1>Hello World</h1></body></html>"
        )
        assert model[solver.vars["state_14450"]] == "present"
        assert model[solver.vars["mode_18972"]] == "0777"
        assert model[solver.vars["owner_30821"]] == "web_admin"

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
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = get_nil_file_state()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 1
        assert model[solver.unchanged[5]] == 1
        assert model[solver.unchanged[6]] == 0
        assert model[solver.unchanged[7]] == 0
        assert model[solver.unchanged[8]] == 0
        assert model[solver.unchanged[9]] == 0
        assert model[solver.vars["content_20672"]] == UNDEF
        assert model[solver.vars["state_14450"]] == "absent"
        assert model[solver.vars["mode_18972"]] == UNDEF
        assert model[solver.vars["owner_30821"]] == UNDEF

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
        filesystem = SystemState()
        filesystem.state["/etc/icinga2/conf.d/test.conf"] = get_nil_file_state()
        filesystem.state["/etc/icinga2/conf.d/test.conf"].attrs["state"] = "present"
        filesystem.state["/etc/icinga2/conf.d/test.conf"].attrs["owner"] = "new"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 4
        assert model[solver.vars["state_3159"]] == "present"
        assert model[solver.vars["content_16"]] == UNDEF
        assert model[solver.vars["owner_256"]] == "new"
        assert model[solver.vars["mode_1296"]] == UNDEF

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
        filesystem = SystemState()
        filesystem.state["test1"] = get_nil_file_state()
        filesystem.state["test1"].attrs["state"] = "present"
        filesystem.state["test1"].attrs["owner"] = "new"
        filesystem.state["test2"] = get_nil_file_state()
        filesystem.state["test2"].attrs["state"] = "present"
        filesystem.state["test2"].attrs["mode"] = "0666"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 2
        model = models[0]
        assert model[solver.sum_var] == 8

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
        filesystem = SystemState()
        
        filesystem.state["/usr/sbin/policy-rc.d"] = get_nil_file_state()
        filesystem.state["/usr/sbin/policy-rc.d"].attrs["state"] = "present"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 2

        assert models[0][solver.sum_var] == 10
        assert models[0][solver.vars["dejavu-condition-1"]]
        assert not models[0][solver.vars["dejavu-condition-2"]]

        assert models[1][solver.sum_var] == 9
        assert not models[1][solver.vars["dejavu-condition-1"]]
        assert models[1][solver.vars["dejavu-condition-2"]]

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
                content => 'test',
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
        filesystem = SystemState()
        filesystem.state["/etc/dhcp/dhclient-enter-hooks"] = get_nil_file_state()

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


class TestPatchSolverPuppetScript6(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_6 = """
            define apache::vhost (
                String[1] $servername = "test",
                String[1] $owner = "owner-test",
            ) {
                file { "${servername}.conf":
                    ensure  => file,
                    owner   => $owner,
                    group   => 'www',
                    mode    => '0644',
                    content => 'test',
                }
            }

            apache::vhost { 'test_vhost':
            }

            apache::vhost { 'test_vhost_2':
                servername => "test2",
                owner => 'new_owner',
            }
        """
        self._setup_patch_solver(puppet_script_6, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_defined_resource_delete(self) -> None:
        filesystem = SystemState()
        filesystem.state["test.conf"] = get_nil_file_state()
        filesystem.state["test2.conf"] = get_nil_file_state()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 4

        result = """
            define apache::vhost (
                String[1] $servername = "test",
            ) {
                file { "${servername}.conf":
                    ensure  => absent,
                    group   => 'www',
                }
            }

            apache::vhost { 'test_vhost':
            }

            apache::vhost { 'test_vhost_2':
                servername => "test2",
            }
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_defined_resource_change_owner(self) -> None:
        filesystem = SystemState()
        filesystem.state["test.conf"] = get_default_file_state()
        filesystem.state["test.conf"].attrs["owner"] = "owner-test"
        filesystem.state["test.conf"].attrs["mode"] = "0644"
        filesystem.state["test.conf"].attrs["content"] = "test"

        filesystem.state["test2.conf"] = get_default_file_state()
        filesystem.state["test2.conf"].attrs["owner"] = "owner-test2"
        filesystem.state["test2.conf"].attrs["mode"] = "0644"
        filesystem.state["test2.conf"].attrs["content"] = "test"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 4

        result = """
            define apache::vhost (
                String[1] $servername = "test",
                String[1] $owner = "owner-test",
            ) {
                file { "${servername}.conf":
                    ensure  => file,
                    owner   => $owner,
                    group   => 'www',
                    mode    => '0644',
                    content => 'test',
                }
            }

            apache::vhost { 'test_vhost':
            }

            apache::vhost { 'test_vhost_2':
                servername => "test2",
                owner => 'owner-test2',
            }
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript7(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_7 = """
$old_config = loadyamlv2('/etc/fuel/cluster/astute.yaml.old','notfound')

# If it's a redeploy and the file exists we can proceed
if($old_config != 'notfound')
{
  $old_gw_type = $old_config['midonet']['gateway_type']
  if ($old_gw_type == 'bgp') {

    file { 'delete router interfaces script':
      ensure  => present,
      path    => '/tmp/delete_router_interfaces_bgp.sh',
      content => template('/etc/fuel/plugins/midonet-9.2/puppet/templates/delete_router_interfaces_bgp.sh.erb'),
    }
  }
}
"""
        self._setup_patch_solver(puppet_script_7, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_inner_if(self) -> None:
        filesystem = SystemState()
        
        filesystem.state["/tmp/delete_router_interfaces_bgp.sh"] = get_nil_file_state()
        filesystem.state["/tmp/delete_router_interfaces_bgp.sh"].attrs["state"] = "present"
        filesystem.state["/tmp/delete_router_interfaces_bgp.sh"].attrs["content"] = "test"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
$old_config = loadyamlv2('/etc/fuel/cluster/astute.yaml.old','notfound')

# If it's a redeploy and the file exists we can proceed
if($old_config != 'notfound')
{
  $old_gw_type = $old_config['midonet']['gateway_type']
  if ($old_gw_type == 'bgp') {

    file { 'delete router interfaces script':
      ensure  => present,
      path    => '/tmp/delete_router_interfaces_bgp.sh',
      content => 'test',
    }
  }
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript8(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_8 = """$gitrevision = '$Id$'

file { '/var/lib/puppet/gitrevision.txt' :
  ensure  => 'present',
  owner   => 'root',
  group   => 'root',
  mode    => '0444',
  content => $gitrevision,
  require => File['/var/lib/puppet'],
}
        """
        self._setup_patch_solver(puppet_script_8, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_delete_variable(self) -> None:
        filesystem = SystemState()
        filesystem.state["/var/lib/puppet/gitrevision.txt"] = get_nil_file_state()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
file { '/var/lib/puppet/gitrevision.txt' :
  ensure  => 'absent',
  group   => 'root',
  require => File['/var/lib/puppet'],
}
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript9(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_9 = """
user { 'mysql':
    ensure => present,
}
"""
        self._setup_patch_solver(puppet_script_9, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_user_delete(self) -> None:
        filesystem = SystemState()
        filesystem.state["user:mysql"] = State()
        filesystem.state["user:mysql"].attrs["state"] = "absent"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
user { 'mysql':
    ensure => absent,
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript10(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_10 = """
file { '/etc/plumgrid':
  ensure  =>  directory,
  mode    =>  0755,
}
"""
        self._setup_patch_solver(puppet_script_10, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_integer_mode(self) -> None:
        filesystem = SystemState()
        filesystem.state["/etc/plumgrid"] = get_nil_file_state()
        filesystem.state["/etc/plumgrid"].attrs["state"] = "present"
        filesystem.state["/etc/plumgrid"].attrs["mode"] = "0756"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
file { '/etc/plumgrid':
  ensure  =>  present,
  mode    =>  0756,
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript11(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_11 = """
file { '/usr/local/bin':
  ensure    => 'directory',
  owner     => $boxen_user,
  group     => 'staff',
  mode      => '0755'
}   
"""
        self._setup_patch_solver(puppet_script_11, UnitBlockType.script, Tech.puppet)

    #@unittest.skip("Not implemented yet")
    def test_patch_solver_puppet_variable_undefined(self) -> None:
        # The problem is that there is no literal to repair and so
        # the solver isn't able to get a solution
        filesystem = SystemState()
        filesystem.state["/usr/local/bin"] = State()
        filesystem.state["/usr/local/bin"].attrs["state"] = "directory"
        filesystem.state["/usr/local/bin"].attrs["mode"] = "0755"
        filesystem.state["/usr/local/bin"].attrs["owner"] = "test"
        filesystem.state["/usr/local/bin"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
file { '/usr/local/bin':
  ensure    => 'directory',
  owner     => 'test',
  group     => 'staff',
  mode      => '0755'
}   
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    
class TestPatchSolverPuppetScript12(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_12 = """
$data_dir = '/etc/hiera'
file { 'hiera_data_dir' :
  ensure => 'directory',
  path   => $data_dir,
  mode   => '0751',
}
"""
        self._setup_patch_solver(puppet_script_12, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_path_variable(self) -> None:
        filesystem = SystemState()
        filesystem.state["/etc/hiera"] = State()
        filesystem.state["/etc/hiera"].attrs["state"] = "directory"
        filesystem.state["/etc/hiera"].attrs["mode"] = "0751"
        filesystem.state["/etc/hiera"].attrs["owner"] = UNDEF
        filesystem.state["/etc/hiera"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
$data_dir = '/etc/hiera'
file { 'hiera_data_dir' :
  ensure => 'directory',
  path   => $data_dir,
  mode   => '0751',
}
"""     
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript13(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_13 = """
define nginx($includes) {
  file { $includes:
    ensure  => directory,
    mode    => '0644',
    owner   => 'root',
    group   => 'root',
  }
}

$includedir = '/etc/nginx/includes'
nginx { 'nginx':
  includes => $includedir,
}
"""
        self._setup_patch_solver(puppet_script_13, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_defined_resource_var_path(self):
        filesystem = SystemState()
        filesystem.state["/etc/nginx/includes"] = State()
        filesystem.state["/etc/nginx/includes"].attrs["state"] = "directory"
        filesystem.state["/etc/nginx/includes"].attrs["mode"] = "0751"
        filesystem.state["/etc/nginx/includes"].attrs["owner"] = "root"
        filesystem.state["/etc/nginx/includes"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
define nginx($includes) {
  file { $includes:
    ensure  => directory,
    mode    => '0751',
    owner   => 'root',
    group   => 'root',
  }
}

$includedir = '/etc/nginx/includes'
nginx { 'nginx':
  includes => $includedir,
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript14(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_14 = """
$::bind::params::binduser          = 'bind'

define bind() {
    file {'/var/named/chroot/var/log/named':
        ensure  => directory,
        owner   => $::bind::params::binduser,
        group   => $::bind::params::bindgroup,
        mode    => '0770',
        seltype => 'var_log_t',
    }
}

bind { 'bind':
}
"""
        self._setup_patch_solver(puppet_script_14, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_defined_resource_change_outside_owner(self):
        filesystem = SystemState()
        filesystem.state["/var/named/chroot/var/log/named"] = State()
        filesystem.state["/var/named/chroot/var/log/named"].attrs["state"] = "directory"
        filesystem.state["/var/named/chroot/var/log/named"].attrs["mode"] = "0770"
        filesystem.state["/var/named/chroot/var/log/named"].attrs["owner"] = "new-owner"
        filesystem.state["/var/named/chroot/var/log/named"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
$::bind::params::binduser          = 'new-owner'

define bind() {
    file {'/var/named/chroot/var/log/named':
        ensure  => directory,
        owner   => $::bind::params::binduser,
        group   => $::bind::params::bindgroup,
        mode    => '0770',
        seltype => 'var_log_t',
    }
}

bind { 'bind':
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript15(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_15 = """
package { 'openssl':
  ensure => installed,
  name   => 'openssl',
}
"""
        self._setup_patch_solver(puppet_script_15, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_remove_package(self):
        filesystem = SystemState()
        filesystem.state["package:openssl"] = State()
        filesystem.state["package:openssl"].attrs["state"] = "absent"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
package { 'openssl':
  ensure => absent,
  name   => 'openssl',
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_latest_package(self):
        filesystem = SystemState()
        filesystem.state["package:openssl"] = State()
        filesystem.state["package:openssl"].attrs["state"] = "latest"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
package { 'openssl':
  ensure => latest,
  name   => 'openssl',
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_purge_package(self):
        filesystem = SystemState()
        filesystem.state["package:openssl"] = State()
        filesystem.state["package:openssl"].attrs["state"] = "purged"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
package { 'openssl':
  ensure => purged,
  name   => 'openssl',
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_disabled_package(self):
        filesystem = SystemState()
        filesystem.state["package:openssl"] = State()
        filesystem.state["package:openssl"].attrs["state"] = "disabled"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
package { 'openssl':
  ensure => disabled,
  name   => 'openssl',
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript16(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_16 = """
service { 'openssl':
  ensure => running,
  name   => 'openssl',
}
"""
        self._setup_patch_solver(puppet_script_16, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_stop_service(self):
        filesystem = SystemState()
        filesystem.state["service:openssl"] = State()
        filesystem.state["service:openssl"].attrs["state"] = "stop"
        filesystem.state["service:openssl"].attrs["enabled"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
service { 'openssl':
  ensure => stopped,
  name   => 'openssl',
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)

    def test_patch_solver_puppet_enable_service(self):
        filesystem = SystemState()
        filesystem.state["service:openssl"] = State()
        filesystem.state["service:openssl"].attrs["state"] = "start"
        filesystem.state["service:openssl"].attrs["enabled"] = "true"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        result = """
service { 'openssl':
  ensure => running,
  name   => 'openssl',
  enable => true,
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result)


class TestPatchSolverPuppetScript17(TestPatchSolver):
    def setUp(self):
        super().setUp()
        puppet_script_17 = """
$::bind::params::packagenameprefix = 'bind9'

define bind::package (
  $packagenameprefix = $::bind::params::packagenameprefix,
  $packagenamesuffix = '',
) {
    package { "$packagenameprefix$packagenamesuffix":
        ensure => present
    }
}

if $chroot == 'true' {
    bind::package { 'bind::package':
        packagenamesuffix => "-chroot"
    }
} else {
    bind::package { 'bind::package':
        packagenamesuffix => ""
    }
}
"""
        self._setup_patch_solver(puppet_script_17, UnitBlockType.script, Tech.puppet)

    def test_patch_solver_puppet_if_with_defined(self):
        filesystem = SystemState()
        filesystem.state["package:$packagenameprefix$packagenamesuffix"] = State()
        filesystem.state["package:$packagenameprefix$packagenamesuffix"].attrs["state"] = "latest"

        assert self.statement is not None
        self.statement = PStatement.minimize(
            self.statement, 
            ["package:$packagenameprefix$packagenamesuffix"]
        )
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 2
        result = """
$::bind::params::packagenameprefix = 'bind9'

define bind::package (
  $packagenameprefix = $::bind::params::packagenameprefix,
  $packagenamesuffix = '',
) {
    package { "$packagenameprefix$packagenamesuffix":
        ensure => latest
    }
}

if $chroot == 'true' {
    bind::package { 'bind::package':
        packagenamesuffix => "-chroot"
    }
} else {
    bind::package { 'bind::package':
        packagenamesuffix => ""
    }
}
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.puppet, result, n_filesystems=2)

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
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = get_default_file_state()
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0777"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "web_admin"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]

        result = """
---
- ansible.builtin.file:
    path: "/var/www/customers/public_html/index.php"
    state: file
    owner: "web_admin"
    mode: '0777'
"""
        self._patch_solver_apply(solver, model, filesystem, Tech.ansible, result)


class TestPatchSolverAnsibleScript2(TestPatchSolver):
    def setUp(self):
        super().setUp()
        self.ansible_script_2 = """
---
- host: localhost
  vars:
    name: index.php
    owner: admin
  tasks:
    - ansible.builtin.file:
        path: "/var/www/customers/public_html/{{ name }}"
        state: file
        owner: "web_{{ owner }}"
        mode: '0755'
"""
        self._setup_patch_solver(
            self.ansible_script_2, UnitBlockType.script, Tech.ansible
        )

    def test_patch_solver_ansible_owner(self) -> None:
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = get_default_file_state()
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0755"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "web_user"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 6
        model = models[0]
        assert model[solver.sum_var] == 5
        assert model[solver.unchanged[8]] == 1
        assert model[solver.unchanged[9]] == 1
        assert model[solver.unchanged[10]] == 0
        assert model[solver.unchanged[11]] == 1
        assert model[solver.unchanged[12]] == 1
        assert model[solver.unchanged[13]] == 0
        assert model[solver.unchanged[14]] == 1
        assert model[solver.vars["state_18000"]] == "present"
        assert model[solver.vars["owner_35937"]] == "web_user"
        assert model[solver.vars["mode_27216"]] == "0755"
        assert model[solver.vars["content_16"]] == UNDEF

        result = """
---
- host: localhost
  vars:
    name: index.php
    owner: 
  tasks:
    - ansible.builtin.file:
        path: "/var/www/customers/public_html/{{ name }}"
        state: file
        owner: "web_user{{ owner }}"
        mode: '0755'
"""
        check = False
        for model in models:
            try:
                self._patch_solver_apply(
                    solver, model, filesystem, Tech.ansible, result
                )
                check = True
                break
            except AssertionError:
                check = False
                with open(self.f.name, "w") as f:
                    f.write(self.ansible_script_2)
        assert check


class TestPatchSolverAnsibleScript3(TestPatchSolver):
    def setUp(self):
        super().setUp()
        ansible_script_3 = """---
- name: Add the user 'johnd'
  ansible.builtin.user:
    name: johnd
"""
        self._setup_patch_solver(ansible_script_3, UnitBlockType.unknown, Tech.ansible)

    def test_patch_solver_ansible_user_delete(self) -> None:
        filesystem = SystemState()
        filesystem.state["user:johnd"] = State()
        filesystem.state["user:johnd"].attrs["state"] = "absent"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        self.statement.to_filesystems()
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: Add the user 'johnd'
  ansible.builtin.user:
    name: johnd
    state: absent
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)


class TestPatchSolverAnsibleScript4(TestPatchSolver):
    def setUp(self):
        super().setUp()
        ansible_script_4 = """---
- name: Version
  hosts: debian
  vars:
    tests_dir: /molecule/symfony_cli/version
  tasks:
    - name: Clean tests dir  # noqa risky-file-permissions
      file:
        path: "{{ tests_dir }}"
        state: "{{ item }}"
      loop: [absent, directory]
"""
        self._setup_patch_solver(ansible_script_4, UnitBlockType.script, Tech.ansible)

    @unittest.skip("Not supported yet")
    def test_patch_solver_ansible_item(self) -> None:
        filesystem = SystemState()
        filesystem.state["/molecule/symfony_cli/version"] = get_nil_file_state()
        filesystem.state["/molecule/symfony_cli/version"].attrs["state"] = "directory"
        filesystem.state["/molecule/symfony_cli/version"].attrs["mode"] = "0755"
        filesystem.state["/molecule/symfony_cli/version"].attrs["owner"] = UNDEF
        filesystem.state["/molecule/symfony_cli/version"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: Version
  hosts: debian
  vars:
    tests_dir: /molecule/symfony_cli/version
  tasks:
    - name: Clean tests dir  # noqa risky-file-permissions
      file:
        path: "{{ tests_dir }}"
        state: "directory"
        mode: "0755"
      loop: [absent, directory]
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)


class TestPatchSolverAnsibleScript5(TestPatchSolver):
    def setUp(self):
        super().setUp()
        ansible_script_5 = """---
- name: "INITIAL SETUP"
  hosts: games.infra.netsoc.co
  become: yes
  tasks:
    - name: "Make /netsoc only readable by root"
      file:
        path: "/netsoc"
        owner: root
        group: root
        mode: '1770'

- name: Ensure Minecraft Servers
  hosts: games.infra.netsoc.co
  roles:
    - role: minecraft
      vars:
        mount: "/netsoc/minecraft"
"""
        self._setup_patch_solver(ansible_script_5, UnitBlockType.script, Tech.ansible)

    def test_patch_solver_ansible_unit_block(self) -> None:
        filesystem = SystemState()
        filesystem.state["/netsoc"] = get_nil_file_state()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: "INITIAL SETUP"
  hosts: games.infra.netsoc.co
  become: yes
  tasks:
    - name: "Make /netsoc only readable by root"
      file:
        path: "/netsoc"
        group: root
        state: absent

- name: Ensure Minecraft Servers
  hosts: games.infra.netsoc.co
  roles:
    - role: minecraft
      vars:
        mount: "/netsoc/minecraft"
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)


class TestPatchSolverAnsibleScript6(TestPatchSolver):
    def setUp(self):
        super().setUp()
        ansible_script_6 = """---
- name: Install ntpdate
  ansible.builtin.package:
    name: ntpdate
    state: present
"""
        self._setup_patch_solver(ansible_script_6, UnitBlockType.tasks, Tech.ansible)

    def test_patch_solver_ansible_remove_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:ntpdate"] = State()
        filesystem.state["package:ntpdate"].attrs["state"] = "absent"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: Install ntpdate
  ansible.builtin.package:
    name: ntpdate
    state: absent
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)

    def test_patch_solver_ansible_latest_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:ntpdate"] = State()
        filesystem.state["package:ntpdate"].attrs["state"] = "latest"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: Install ntpdate
  ansible.builtin.package:
    name: ntpdate
    state: latest
""" 
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)


class TestPatchSolverAnsibleScript7(TestPatchSolver):
    def setUp(self):
        super().setUp()
        ansible_script_7 = """---
- name: Start service httpd, if not started
  ansible.builtin.service:
    name: httpd
    state: started
"""
        self._setup_patch_solver(ansible_script_7, UnitBlockType.tasks, Tech.ansible)

    def test_patch_solver_ansible_stop_service(self) -> None:
        filesystem = SystemState()
        filesystem.state["service:httpd"] = State()
        filesystem.state["service:httpd"].attrs["state"] = "stop"
        filesystem.state["service:httpd"].attrs["enabled"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: Start service httpd, if not started
  ansible.builtin.service:
    name: httpd
    state: stopped
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)

    def test_patch_solver_ansible_enable_service(self) -> None:
        filesystem = SystemState()
        filesystem.state["service:httpd"] = State()
        filesystem.state["service:httpd"].attrs["state"] = "start"
        filesystem.state["service:httpd"].attrs["enabled"] = "true"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """---
- name: Start service httpd, if not started
  ansible.builtin.service:
    name: httpd
    state: started
    enabled: true
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.ansible, result)


class TestPatchSolverChefScript1(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_1 = """
        file '/tmp/something' do
            mode '0755'
            action :create_if_missing
        end
        """
        self._setup_patch_solver(chef_script_1, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_mode(self) -> None:
        filesystem = SystemState()
        filesystem.state["/tmp/something"] = get_default_file_state()
        filesystem.state["/tmp/something"].attrs["mode"] = "0777"
        filesystem.state["/tmp/something"].attrs["owner"] = UNDEF
        filesystem.state["/tmp/something"].attrs["content"] = UNDEF

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 4
        assert model[solver.vars["mode_2808"]] == "0777"
        assert model[solver.vars["state_7904"]] == "present"
        assert model[solver.vars["content_16"]] == UNDEF
        assert model[solver.vars["owner_256"]] == UNDEF

        result = """
        file '/tmp/something' do
            mode '0777'
            action :create_if_missing
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)

    def test_patch_solver_chef_delete(self) -> None:
        filesystem = SystemState()
        filesystem.state["/tmp/something"] = get_nil_file_state()

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 3
        assert model[solver.vars["mode_2808"]] == UNDEF
        assert model[solver.vars["state_7904"]] == "absent"
        assert model[solver.vars["content_16"]] == UNDEF
        assert model[solver.vars["owner_256"]] == UNDEF

        result = """
        file '/tmp/something' do
            action :delete
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)

    @unittest.skip("Not implemented yet")
    def test_patch_solver_chef_modify_to_directory(self) -> None:
        filesystem = SystemState()
        filesystem.state["/tmp/something"] = get_nil_file_state()
        filesystem.state["/tmp/something"].attrs["state"] = "directory"
        filesystem.state["/tmp/something"].attrs["mode"] = "0777"

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


class TestPatchSolverChefScript2(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_2 = """
        directory '/tmp/something' do
            action :delete
        end
        """
        self._setup_patch_solver(chef_script_2, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_directory(self) -> None:
        filesystem = SystemState()
        filesystem.state["/tmp/something"] = get_nil_file_state()
        filesystem.state["/tmp/something"].attrs["state"] = "present"
        filesystem.state["/tmp/something"].attrs["mode"] = "0777"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 3
        assert model[solver.vars["state_3159"]] == "present"
        assert model[solver.vars["content_16"]] == UNDEF
        assert model[solver.vars["owner_256"]] == UNDEF
        assert model[solver.vars["mode_1296"]] == "0777"

        result = """
        directory '/tmp/something' do
            action :create
            mode '0777'
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)


class TestPatchSolverChefScript3(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_2 = """
        user 'test' do
            name   'test'
            action :create
        end
        """
        self._setup_patch_solver(chef_script_2, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_user_delete(self) -> None:
        filesystem = SystemState()
        filesystem.state["user:test"] = State()
        filesystem.state["user:test"].attrs["state"] = "absent"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
        user 'test' do
            name   'test'
            action :delete
        end
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)

    def test_patch_solver_chef_user_change(self) -> None:
        filesystem = SystemState()
        filesystem.state["user:test2"] = State()
        filesystem.state["user:test2"].attrs["state"] = "present"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
        user 'test' do
            name   'test2'
            action :create
        end
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)


class TestPatchSolverChefScript4(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_1 = """
        y = '0755'
        x = y

        file '/tmp/something' do
            mode x
            action :nothing
        end
        """
        self._setup_patch_solver(chef_script_1, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_variable_mode(self):
        filesystem = SystemState()
        filesystem.state["/tmp/something"] = get_nil_file_state()
        filesystem.state["/tmp/something"].attrs["state"] = "present"
        filesystem.state["/tmp/something"].attrs["mode"] = "0777"

        assert self.statement is not None
        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1
        model = models[0]
        assert model[solver.sum_var] == 4
        assert model[solver.vars["x"]] == "0777"
        assert model[solver.vars["y"]] == "0777"
        assert model[solver.vars["mode_8892"]] == "0777"
        assert model[solver.vars["state_17836"]] == "present"
        assert model[solver.vars["content_16"]] == UNDEF
        assert model[solver.vars["owner_256"]] == UNDEF

        result = """
        y = '0777'
        x = y

        file '/tmp/something' do
            mode x
            action :nothing
        end
        """
        self._patch_solver_apply(solver, model, filesystem, Tech.chef, result)


class TestPatchSolverChefScript5(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_2 = """
file '/var/www/customers/public_html/index.php' do
    content '<html>This is a placeholder for the home page.</html>'
    mode '0755'
    owner 'web_admin'
    group 'web_admin'
end

file '/var/www/customers/public_html/index2.php' do
    content '<html>This is a placeholder for the home page.</html>'
    mode '0755'
    owner 'web_admin'
    group 'web_admin'
end
        """
        self._setup_patch_solver(chef_script_2, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_minimize(self) -> None:
        filesystem = SystemState()
        filesystem.state["/var/www/customers/public_html/index.php"] = get_default_file_state()
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0755"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "test"
        filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = "<html>This is a placeholder for the home page.</html>"
        
        filesystem.state["/var/www/customers/public_html/index2.php"] = State()
        filesystem.state["/var/www/customers/public_html/index2.php"].attrs["state"] = UNDEF
        filesystem.state["/var/www/customers/public_html/index2.php"].attrs["mode"] = "0755"
        filesystem.state["/var/www/customers/public_html/index2.php"].attrs["owner"] = "web_admin"
        filesystem.state["/var/www/customers/public_html/index2.php"].attrs["content"] = "<html>This is a placeholder for the home page.</html>"

        assert self.statement is not None
        self.statement: PStatement = PStatement.minimize(
            self.statement, ["/var/www/customers/public_html/index.php"]
        )
        minimized_filesystem = SystemState()
        minimized_filesystem.state["/var/www/customers/public_html/index.php"] = get_default_file_state()
        minimized_filesystem.state["/var/www/customers/public_html/index.php"].attrs["mode"] = "0755"
        minimized_filesystem.state["/var/www/customers/public_html/index.php"].attrs["owner"] = "test"
        minimized_filesystem.state["/var/www/customers/public_html/index.php"].attrs["content"] = "<html>This is a placeholder for the home page.</html>"

        solver = PatchSolver(self.statement, minimized_filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
file '/var/www/customers/public_html/index.php' do
    content '<html>This is a placeholder for the home page.</html>'
    mode '0755'
    owner 'test'
    group 'web_admin'
    action :create
end

file '/var/www/customers/public_html/index2.php' do
    content '<html>This is a placeholder for the home page.</html>'
    mode '0755'
    owner 'web_admin'
    group 'web_admin'
end
        """
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)


class TestPatchSolverChefScript6(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_6 = """
test_user = 'leia'
test_user_home = "/home/#{test_user}"

directory "#{test_user_home}/.ssh" do
  mode '0700'
  owner test_user
  group test_user
end
"""
        self._setup_patch_solver(chef_script_6, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_vars(self) -> None:
        filesystem = SystemState()
        filesystem.state["/home/leia/.ssh"] = get_default_file_state()
        filesystem.state["/home/leia/.ssh"].attrs["mode"] = "0766"
        filesystem.state["/home/leia/.ssh"].attrs["owner"] = "leia"
        filesystem.state["/home/leia/.ssh"].attrs["content"] = "leia"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
test_user = 'leia'
test_user_home = "/home/#{test_user}"

directory "#{test_user_home}/.ssh" do
  mode '0766'
  owner test_user
  group test_user
  action :create
  content 'leia'
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)


class TestPatchSolverChefScript7(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_7 = """
package 'tar' do
  action :install
end
"""
        self._setup_patch_solver(chef_script_7, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_remove_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:tar"] = State()
        filesystem.state["package:tar"].attrs["state"] = "absent"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
package 'tar' do
  action :remove
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)

    def test_patch_solver_chef_latest_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:tar"] = State()
        filesystem.state["package:tar"].attrs["state"] = "latest"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
package 'tar' do
  action :upgrade
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)


class TestPatchSolverChefScript8(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_8 = """
package 'tar' do
  action :purge
end
"""
        self._setup_patch_solver(chef_script_8, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_create_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:tar"] = State()
        filesystem.state["package:tar"].attrs["state"] = "present"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
package 'tar' do
  action :install
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)

    def test_patch_solver_chef_reconfig_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:tar"] = State()
        filesystem.state["package:tar"].attrs["state"] = "reconfig"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
package 'tar' do
  action :reconfig
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)

    def test_patch_solver_chef_nothing_package(self) -> None:
        filesystem = SystemState()
        filesystem.state["package:tar"] = State()
        filesystem.state["package:tar"].attrs["state"] = "nothing"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
package 'tar' do
  action :nothing
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)


class TestPatchSolverChefScript9(TestPatchSolver):
    def setUp(self):
        super().setUp()
        chef_script_9 = """
service 'example_service' do
  action :start
end
"""
        self._setup_patch_solver(chef_script_9, UnitBlockType.script, Tech.chef)

    def test_patch_solver_chef_stop_service(self) -> None:
        filesystem = SystemState()
        filesystem.state["service:example_service"] = State()
        filesystem.state["service:example_service"].attrs["state"] = "stop"
        filesystem.state["service:example_service"].attrs["enabled"] = UNDEF
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
service 'example_service' do
  action :stop
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)

    def test_patch_solver_chef_enable_service(self) -> None:
        filesystem = SystemState()
        filesystem.state["service:example_service"] = State()
        filesystem.state["service:example_service"].attrs["state"] = UNDEF
        filesystem.state["service:example_service"].attrs["enabled"] = "true"
        assert self.statement is not None

        solver = PatchSolver(self.statement, filesystem)
        models = solver.solve()
        assert models is not None
        assert len(models) == 1

        result = """
service 'example_service' do
  action :enable
end
"""
        self._patch_solver_apply(solver, models[0], filesystem, Tech.chef, result)
