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
        labeled_script = GLITCHLabeler.label(puppet_parser, Tech.puppet)

        # Check labels
        i = 0
        for atomic_unit in labeled_script.script.atomic_units:
            for attribute in atomic_unit.attributes:
                assert labeled_script.get_label(attribute) == i
                i += 1

        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)

    assert statement == PSeq(
        lhs=PSkip(),
        rhs=PSeq(
            lhs=PSeq(
                lhs=PSeq(
                    lhs=PLet(
                        id="state-2",
                        expr=PEConst(const=PStr(value="present")),
                        label=2,
                        body=PIf(
                            pred=PEBinOP(
                                op=PEq(),
                                lhs=PEVar(id="state-2"),
                                rhs=PEConst(const=PStr(value="present")),
                            ),
                            cons=PCreate(
                                path=PEConst(
                                    const=PStr(
                                        value="/var/www/customers/public_html/index.php"
                                    )
                                )
                            ),
                            alt=PIf(
                                pred=PEBinOP(
                                    op=PEq(),
                                    lhs=PEVar(id="state-2"),
                                    rhs=PEConst(const=PStr(value="absent")),
                                ),
                                cons=PRm(
                                    path=PEConst(
                                        const=PStr(
                                            value="/var/www/customers/public_html/index.php"
                                        )
                                    )
                                ),
                                alt=PIf(
                                    pred=PEBinOP(
                                        op=PEq(),
                                        lhs=PEVar(id="state-2"),
                                        rhs=PEConst(const=PStr(value="directory")),
                                    ),
                                    cons=PMkdir(
                                        path=PEConst(
                                            const=PStr(
                                                value="/var/www/customers/public_html/index.php"
                                            )
                                        )
                                    ),
                                    alt=PSkip(),
                                ),
                            ),
                        ),
                    ),
                    rhs=PLet(
                        id="content-1",
                        expr=PEConst(
                            const=PStr(
                                value="<html><body><h1>Hello World</h1></body></html>"
                            )
                        ),
                        label=1,
                        body=PWrite(
                            path=PEConst(
                                const=PStr(
                                    value="/var/www/customers/public_html/index.php"
                                )
                            ),
                            content=PEVar(id="content-1"),
                        ),
                    ),
                ),
                rhs=PLet(
                    id="owner-4",
                    expr=PEConst(const=PStr(value="web_admin")),
                    label=4,
                    body=PChown(
                        path=PEConst(
                            const=PStr(value="/var/www/customers/public_html/index.php")
                        ),
                        owner=PEVar(id="owner-4"),
                    ),
                ),
            ),
            rhs=PLet(
                id="mode-3",
                expr=PEConst(const=PStr(value="0755")),
                label=3,
                body=PChmod(
                    path=PEConst(
                        const=PStr(value="/var/www/customers/public_html/index.php")
                    ),
                    mode=PEVar(id="mode-3"),
                ),
            ),
        ),
    )


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

    assert statement == PSeq(
        lhs=PSkip(),
        rhs=PSeq(
            lhs=PSeq(
                lhs=PSeq(
                    lhs=PLet(
                        id="state-0",
                        expr=PEConst(const=PStr(value="absent")),
                        label=0,
                        body=PIf(
                            pred=PEBinOP(
                                op=PEq(),
                                lhs=PEVar(id="state-0"),
                                rhs=PEConst(const=PStr(value="present")),
                            ),
                            cons=PCreate(
                                path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d"))
                            ),
                            alt=PIf(
                                pred=PEBinOP(
                                    op=PEq(),
                                    lhs=PEVar(id="state-0"),
                                    rhs=PEConst(const=PStr(value="absent")),
                                ),
                                cons=PRm(
                                    path=PEConst(
                                        const=PStr(value="/usr/sbin/policy-rc.d")
                                    )
                                ),
                                alt=PIf(
                                    pred=PEBinOP(
                                        op=PEq(),
                                        lhs=PEVar(id="state-0"),
                                        rhs=PEConst(const=PStr(value="directory")),
                                    ),
                                    cons=PMkdir(
                                        path=PEConst(
                                            const=PStr(value="/usr/sbin/policy-rc.d")
                                        )
                                    ),
                                    alt=PSkip(),
                                ),
                            ),
                        ),
                    ),
                    rhs=PLet(
                        id="sketched-content-1",
                        expr=PEUndef(),
                        label=1,
                        body=PWrite(
                            path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                            content=PEVar(id="sketched-content-1"),
                        ),
                    ),
                ),
                rhs=PLet(
                    id="sketched-owner-2",
                    expr=PEUndef(),
                    label=2,
                    body=PChown(
                        path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                        owner=PEVar(id="sketched-owner-2"),
                    ),
                ),
            ),
            rhs=PLet(
                id="sketched-mode-3",
                expr=PEUndef(),
                label=3,
                body=PChmod(
                    path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                    mode=PEVar(id="sketched-mode-3"),
                ),
            ),
        ),
    )


def test_delta_p_to_filesystem():
    statement = PSeq(
        PSeq(
            PSeq(
                PSeq(
                    PSkip(),
                    PCreate(
                        PEConst(PStr("/var/www/customers/public_html/index.php")),
                    ),
                ),
                PWrite(
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


def test_delta_p_to_filesystem_2():
    statement = PSeq(
        lhs=PSkip(),
        rhs=PLet(
            id="state-0",
            expr=PEConst(const=PStr(value="absent")),
            label=0,
            body=PIf(
                pred=PEBinOP(
                    op=PEq(),
                    lhs=PEVar(id="state-0"),
                    rhs=PEConst(const=PStr(value="present")),
                ),
                cons=PCreate(
                    path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                ),
                alt=PIf(
                    pred=PEBinOP(
                        op=PEq(),
                        lhs=PEVar(id="state-0"),
                        rhs=PEConst(const=PStr(value="absent")),
                    ),
                    cons=PRm(path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d"))),
                    alt=PIf(
                        pred=PEBinOP(
                            op=PEq(),
                            lhs=PEVar(id="state-0"),
                            rhs=PEConst(const=PStr(value="directory")),
                        ),
                        cons=PMkdir(
                            path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d"))
                        ),
                        alt=PSkip(),
                    ),
                ),
            ),
        ),
    )

    fs = statement.to_filesystem()
    assert fs.state == {"/usr/sbin/policy-rc.d": Nil()}
