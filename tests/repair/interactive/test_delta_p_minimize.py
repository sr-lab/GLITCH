from glitch.repair.interactive.delta_p import *


def test_delta_p_minimize_let() -> None:
    statement = PLet(
        "x",
        PEConst(const=PStr(value="test1")),
        1,
        PAttr(
            PEConst(const=PStr(value="test23456")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_seq() -> None:
    statement = PSeq(
        PAttr(
            PEConst(const=PStr(value="test1")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
        PAttr(
            PEConst(const=PStr(value="test2")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PAttr)
    assert minimized.path == PEConst(const=PStr(value="test1"))

    minimized = PStatement.minimize(statement, ["test2"])
    assert isinstance(minimized, PAttr)
    assert minimized.path == PEConst(const=PStr(value="test2"))

    minimized = PStatement.minimize(statement, ["test3"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_if() -> None:
    statement = PIf(
        PEConst(const=PBool(True)),
        PAttr(
            PEConst(const=PStr(value="test2")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
        PAttr(
            PEConst(const=PStr(value="test3")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
    )

    minimized = PStatement.minimize(statement, ["test2"])
    assert isinstance(minimized, PIf)
    assert minimized == PIf(
        PEConst(const=PBool(True)),
        PAttr(
            PEConst(const=PStr(value="test2")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
        PSkip(),
    )

    minimized = PStatement.minimize(statement, ["test3"])
    assert isinstance(minimized, PIf)
    assert minimized == PIf(
        PEConst(const=PBool(True)),
        PSkip(),
        PAttr(
            PEConst(const=PStr(value="test3")),
            "state",
            PEConst(const=PStr(value="present")),
        ),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_with_add() -> None:
    statement = PAttr(
        PEBinOP(
            PAdd(), PEConst(const=PStr(value="ola")), PEConst(const=PStr(value="2"))
        ),
        "state",
        PEConst(const=PStr(value="present")),
    )

    minimized = PStatement.minimize(statement, ["ola2"])
    assert minimized == statement

    minimized = PStatement.minimize(statement, ["ola3"])
    assert isinstance(minimized, PSkip)
