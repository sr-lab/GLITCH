from glitch.repair.interactive.delta_p import *


def test_delta_p_minimize_let() -> None:
    statement = PLet(
        "x",
        "test1",
        1,
        PCreate(PEConst(const=PStr(value="test23456"))),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_seq() -> None:
    statement = PSeq(
        PCreate(PEConst(const=PStr(value="test1"))),
        PCreate(PEConst(const=PStr(value="test2"))),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PCreate)
    assert minimized.path == PEConst(const=PStr(value="test1"))

    minimized = PStatement.minimize(statement, ["test2"])
    assert isinstance(minimized, PCreate)
    assert minimized.path == PEConst(const=PStr(value="test2"))

    minimized = PStatement.minimize(statement, ["test3"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_if() -> None:
    statement = PIf(
        PBool(True),
        PCreate(PEConst(const=PStr(value="test2"))),
        PCreate(PEConst(const=PStr(value="test3"))),
    )

    minimized = PStatement.minimize(statement, ["test2"])
    assert isinstance(minimized, PIf)
    assert minimized == PIf(
        PBool(True), PCreate(PEConst(const=PStr(value="test2"))), PSkip()
    )

    minimized = PStatement.minimize(statement, ["test3"])
    assert isinstance(minimized, PIf)
    assert minimized == PIf(
        PBool(True), PSkip(), PCreate(PEConst(const=PStr(value="test3")))
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PSkip)
