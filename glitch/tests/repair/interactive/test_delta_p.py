import unittest

from glitch.parsers.puppet import PuppetParser
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.names_database import NormalizationVisitor
from glitch.repair.interactive.delta_p import *
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech
from glitch.tests.repair.interactive.delta_p.delta_p_puppet_scripts import *
from tempfile import NamedTemporaryFile
from glitch.repair.interactive.values import UNDEF


class TestDeltaPCompilerPuppet(unittest.TestCase):
    def setUp(self):
        DeltaPCompiler._condition = 0  # type: ignore
        DeltaPCompiler._literal = 0  # type: ignore
        DeltaPCompiler._sketched = -1  # type: ignore

    def test_delta_p_compiler_puppet(self) -> None:
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
            ir = PuppetParser().parse_file(f.name, UnitBlockType.script)
            assert ir is not None
            NormalizationVisitor(Tech.puppet).visit(ir)
            labeled_script = GLITCHLabeler.label(ir, Tech.puppet)

            # Check labels
            i = 0
            for atomic_unit in labeled_script.script.atomic_units:
                for attribute in atomic_unit.attributes:
                    assert labeled_script.get_label(attribute) == i
                    i += 1

            statement = DeltaPCompiler(labeled_script).compile()

        assert statement == delta_p_puppet

    def test_delta_p_compiler_puppet_2(self) -> None:
        puppet_script = """
        file {'/usr/sbin/policy-rc.d':
            ensure  => absent,
        }
        """

        with NamedTemporaryFile() as f:
            f.write(puppet_script.encode())
            f.flush()
            ir = PuppetParser().parse_file(f.name, UnitBlockType.script)
            assert ir is not None
            NormalizationVisitor(Tech.puppet).visit(ir)
            labeled_script = GLITCHLabeler.label(ir, Tech.puppet)

            # Check labels
            i = 0
            for atomic_unit in labeled_script.script.atomic_units:
                for attribute in atomic_unit.attributes:
                    assert labeled_script.get_label(attribute) == i
                    i += 1

            statement = DeltaPCompiler(labeled_script).compile()

        assert statement == delta_p_puppet_2

    def test_delta_p_compiler_puppet_default_state(self) -> None:
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
            assert ir is not None
            NormalizationVisitor(Tech.puppet).visit(ir)
            labeled_script = GLITCHLabeler.label(ir, Tech.puppet)
            statement = DeltaPCompiler(labeled_script).compile()

        assert statement == delta_p_puppet_default_state


def test_delta_p_to_filesystems() -> None:
    statement = delta_p_puppet
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert len(fss[0].state) == 1
    assert "/var/www/customers/public_html/index.php" in fss[0].state
    assert fss[0].state["/var/www/customers/public_html/index.php"].attrs["state"] == "present"
    assert fss[0].state["/var/www/customers/public_html/index.php"].attrs["mode"] == "0755"
    assert fss[0].state["/var/www/customers/public_html/index.php"].attrs["owner"] == "web_admin"
    assert fss[0].state["/var/www/customers/public_html/index.php"].attrs["content"] == "<html><body><h1>Hello World</h1></body></html>"


def test_delta_p_to_filesystems_2() -> None:
    statement = delta_p_puppet_2
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert len(fss[0].state) == 1
    assert "/usr/sbin/policy-rc.d" in fss[0].state
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["state"] == "absent"
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["mode"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["owner"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["content"] == UNDEF


def test_delta_p_to_filesystems_if() -> None:
    statement = delta_p_puppet_if
    fss = statement.to_filesystems()
    assert len(fss) == 2
    assert len(fss[0].state) == 1
    assert "/usr/sbin/policy-rc.d" in fss[0].state
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["state"] == "absent"
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["mode"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["owner"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["content"] == UNDEF

    assert len(fss[1].state) == 1
    assert "/usr/sbin/policy-rc.d" in fss[1].state
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["state"] == "present"
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["mode"] == UNDEF
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["owner"] == UNDEF
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["content"] == UNDEF

