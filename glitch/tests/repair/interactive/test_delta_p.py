from glitch.parsers.cmof import PuppetParser
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.delta_p import *
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech
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
        labeled_script = GLITCHLabeler.label(puppet_parser)

        # Check labels
        i = 0
        for atomic_unit in labeled_script.script.atomic_units:
            for attribute in atomic_unit.attributes:
                assert labeled_script.get_label(attribute) == i
                i += 1

        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)

    assert statement == PSeq(
        PSeq(
            PSeq(
                PSkip(),
                PLet(
                    "state",
                    PEConst(PStr("present")),
                    2,
                    PLet(
                        "content",
                        PEConst(PStr("<html><body><h1>Hello World</h1></body></html>")),
                        1,
                        PCreate(
                            PEConst(PStr("/var/www/customers/public_html/index.php")),
                            PEConst(PStr("<html><body><h1>Hello World</h1></body></html>")),
                        ),
                    )
                ),
            ),
            PLet(
                "mode",
                PEConst(PStr("0755")),
                3,
                PChmod(
                    PEConst(PStr("/var/www/customers/public_html/index.php")),
                    PEConst(PStr("0755")),
                ),
            ),
        ),
        PLet(
            "owner",
            PEConst(PStr("web_admin")),
            4,
            PChown(
                PEConst(PStr("/var/www/customers/public_html/index.php")),
                PEConst(PStr("web_admin")),
            ),
        ),
    )


def test_delta_p_to_filesystem():
    statement = PSeq(
        PSeq(
            PSeq(
                PSkip(),
                PCreate(
                    PEConst(PStr("/var/www/customers/public_html/index.php")),
                    PEConst(PStr("<html><body><h1>Hello World</h1></body></html>")),
                ),
            ),
            PChown(
                PEConst(PStr("/var/www/customers/public_html/index.php")),
                PEConst(PStr("web_admin")),
            ),
        ),
        PChmod(
            PEConst(PStr("/var/www/customers/public_html/index.php")),
            PEConst(PStr("0755")),
        ),
    )

    fs = statement.to_filesystem()
    assert fs.state == {
        "/var/www/customers/public_html/index.php": File(
            "0755", "web_admin", "<html><body><h1>Hello World</h1></body></html>"
        )
    }