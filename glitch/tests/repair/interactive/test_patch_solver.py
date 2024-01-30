from z3 import ModelRef
from tempfile import NamedTemporaryFile

from glitch.repair.interactive.delta_p import *
from glitch.repair.interactive.solver import PatchSolver
from glitch.parsers.cmof import PuppetParser
from glitch.repair.interactive.compiler.labeler import GLITCHLabeler
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler
from glitch.repr.inter import UnitBlockType
from glitch.tech import Tech


statement = PSeq(
    PSeq(
        PSeq(
            PSkip(),
            PLet(
                "state-2",
                PEConst(PStr("present")),
                2,
                PIf(
                    PEBinOP(PEq(), PEVar("state-2"), PEConst(PStr("present"))),
                    PLet(
                        "content-1",
                        PEConst(PStr("<html><body><h1>Hello World</h1></body></html>")),
                        1,
                        PCreate(
                            PEConst(PStr("/var/www/customers/public_html/index.php")),
                            PEVar("content-1"),
                        ),
                    ),
                    PIf(
                        PEBinOP(PEq(), PEVar("state-2"), PEConst(PStr("absent"))),
                        PRm(PEConst(PStr("/var/www/customers/public_html/index.php"))),
                        PIf(
                            PEBinOP(
                                PEq(), PEVar("state-2"), PEConst(PStr("directory"))
                            ),
                            PMkdir(
                                PEConst(
                                    PStr("/var/www/customers/public_html/index.php")
                                )
                            ),
                            PSkip(),
                        ),
                    ),
                ),
            ),
        ),
        PLet(
            "mode-3",
            PEConst(PStr("0755")),
            3,
            PChmod(
                PEConst(PStr("/var/www/customers/public_html/index.php")),
                PEVar("mode-3"),
            ),
        ),
    ),
    PLet(
        "owner-4",
        PEConst(PStr("web_admin")),
        4,
        PChown(
            PEConst(PStr("/var/www/customers/public_html/index.php")),
            PEVar("owner-4"),
        ),
    ),
)


def patch_solver_apply(solver: PatchSolver, model: ModelRef, filesystem: FileSystemState):
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
        solver.apply_patch(model, labeled_script)
        statement = DeltaPCompiler.compile(labeled_script, Tech.puppet)
        assert statement.to_filesystem().state == filesystem.state


def test_patch_solver_mode():
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
    patch_solver_apply(solver, model, filesystem)


def test_patch_solver_delete_file():
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
    patch_solver_apply(solver, model, filesystem)
