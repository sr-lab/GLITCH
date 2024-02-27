from glitch.parsers.cmof import PuppetParser
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.delta_p import *
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech
from glitch.tests.repair.interactive.delta_p.delta_p_puppet_scripts import (
    delta_p_puppet,
    delta_p_puppet_2,
    delta_p_puppet_if
)
from tempfile import NamedTemporaryFile


def test_delta_p_compiler_puppet():
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


def test_delta_p_compiler_puppet_2():
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


def test_delta_p_compiler_puppet_if():
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


def test_delta_p_to_filesystems():
    statement = delta_p_puppet
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert fss[0].state == {
        "/var/www/customers/public_html/index.php": File(
            "0755", "web_admin", "<html><body><h1>Hello World</h1></body></html>"
        )
    }


def test_delta_p_to_filesystems_2():
    statement = delta_p_puppet_2
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert fss[0].state == {"/usr/sbin/policy-rc.d": Nil()}


def test_delta_p_to_filesystems_if():
    statement = delta_p_puppet_if
    fss = statement.to_filesystems()
    assert len(fss) == 2
    assert fss[0].state == {"/usr/sbin/policy-rc.d": Nil()}
    assert fss[1].state == {"/usr/sbin/policy-rc.d": File(None, None, None)}
