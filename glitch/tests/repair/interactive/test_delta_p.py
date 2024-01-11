from glitch.parsers.cmof import PuppetParser
from glitch.repair.interactive.compiler.compiler import Compiler
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
        statement = Compiler().compile(puppet_parser, Tech.puppet)

    assert statement == PSeq(
        PSeq(
            PSeq(
                PSkip(),
                PCreate(
                    PEConst(PStr('/var/www/customers/public_html/index.php')),
                    PEConst(PStr('<html><body><h1>Hello World</h1></body></html>'))
                )
            ),
            PChown(PEConst(PStr('/var/www/customers/public_html/index.php')), PEConst(PStr('web_admin')))
        ),
        PChmod(PEConst(PStr('/var/www/customers/public_html/index.php')), PEConst(PStr('0755')))
    )


def test_delta_p_to_filesystem():
    statement = PSeq(
        PSeq(
            PSeq(
                PSkip(),
                PCreate(
                    PEConst(PStr('/var/www/customers/public_html/index.php')),
                    PEConst(PStr('<html><body><h1>Hello World</h1></body></html>'))
                )
            ),
            PChown(PEConst(PStr('/var/www/customers/public_html/index.php')), PEConst(PStr('web_admin')))
        ),
        PChmod(PEConst(PStr('/var/www/customers/public_html/index.php')), PEConst(PStr('0755')))
    )

    fs = statement.to_filesystem()
    assert fs.state == {
        '/var/www/customers/public_html/index.php': File(
            '0755',
            'web_admin',
            '<html><body><h1>Hello World</h1></body></html>'
        )
    }
