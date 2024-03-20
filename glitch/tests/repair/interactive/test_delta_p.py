from glitch.parsers.puppet import PuppetParser
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.delta_p import *
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech
from glitch.tests.repair.interactive.delta_p.delta_p_puppet_scripts import *
from tempfile import NamedTemporaryFile


def test_delta_p_compiler_puppet() -> None:
    puppet_script = """
    file { '/var/www/customers/public_html/index.php':
        path => '/var/www/customers/public_html/index.php',
        content => '<html><body><h1>Hello World</h1></body></html>',
        ensure => present,
        mode => '0755',
        owner => 'web_admin'
    }
    """

    with NamedTemporaryFile() as f:
        f.write(puppet_script.encode())
        f.flush()
        puppet_parser = PuppetParser().parse_file(f.name, UnitBlockType.script)
        labeled_script = GLITCHLabeler.label(puppet_parser, Tech.puppet)

        # Check labels
        i = 0
        for atomic_unit in labeled_script.script.atomic_units:
            for attribute in atomic_unit.attributes:
                assert labeled_script.get_label(attribute) == i
                i += 1

        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)

    assert statement == delta_p_puppet


def test_delta_p_compiler_puppet_2() -> None:
    puppet_script = """
    file {'/usr/sbin/policy-rc.d':
        ensure  => absent,
    }
    """

    with NamedTemporaryFile() as f:
        f.write(puppet_script.encode())
        f.flush()
        puppet_parser = PuppetParser().parse_file(f.name, UnitBlockType.script)
        labeled_script = GLITCHLabeler.label(puppet_parser, Tech.puppet)

        # Check labels
        i = 0
        for atomic_unit in labeled_script.script.atomic_units:
            for attribute in atomic_unit.attributes:
                assert labeled_script.get_label(attribute) == i
                i += 1

        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)

    assert statement == delta_p_puppet_2


def test_delta_p_compiler_puppet_if() -> None:
    puppet_script = """
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

    with NamedTemporaryFile() as f:
        f.write(puppet_script.encode())
        f.flush()
        ir = PuppetParser().parse_file(f.name, UnitBlockType.script)
        labeled_script = GLITCHLabeler.label(ir, Tech.puppet)
        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)

    assert statement == delta_p_puppet_if


def test_delta_p_compiler_puppet_default_state() -> None:
    puppet_script = """
file { '/root/.ssh/config':
  content => template('fuel/root_ssh_config.erb'),
  owner   => 'root',
  group   => 'root',
  mode    => '0600',
}
"""

    with NamedTemporaryFile() as f:
        f.write(puppet_script.encode())
        f.flush()
        ir = PuppetParser().parse_file(f.name, UnitBlockType.script)
        labeled_script = GLITCHLabeler.label(ir, Tech.puppet)
        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)
    assert statement == delta_p_puppet_default_state


def test_delta_p_to_filesystems() -> None:
    statement = delta_p_puppet
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert fss[0].state == {
        "/var/www/customers/public_html/index.php": File(
            "0755", "web_admin", "<html><body><h1>Hello World</h1></body></html>"
        )
    }


def test_delta_p_to_filesystems_2() -> None:
    statement = delta_p_puppet_2
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert fss[0].state == {"/usr/sbin/policy-rc.d": Nil()}


def test_delta_p_to_filesystems_if() -> None:
    statement = delta_p_puppet_if
    fss = statement.to_filesystems()
    assert len(fss) == 2
    assert fss[0].state == {"/usr/sbin/policy-rc.d": Nil()}
    assert fss[1].state == {"/usr/sbin/policy-rc.d": File(None, None, None)}


def test_delta_p_to_filesystems_default_state() -> None:
    statement = delta_p_puppet_default_state
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert fss[0].state == {
        "/root/.ssh/config": File(
            "0600", "root", "template('fuel/root_ssh_config.erb')"
        )
    }
