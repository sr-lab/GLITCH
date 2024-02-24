from glitch.repair.interactive.delta_p import *

def test_delta_p_minimize_let():
    statement = PLet(
        "x",
        "test1",
        1,
        PCreate("test23456"),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_seq():
    statement = PSeq(
        PCreate("test1"),
        PCreate("test2"),
    )

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PCreate)
    assert minimized.path == "test1"

    minimized = PStatement.minimize(statement, ["test2"])
    assert isinstance(minimized, PCreate)
    assert minimized.path == "test2"

    minimized = PStatement.minimize(statement, ["test3"])
    assert isinstance(minimized, PSkip)


def test_delta_p_minimize_if():
    statement = PIf(
        PBool(True),
        PCreate("test2"),
        PCreate("test3"),
    )

    minimized = PStatement.minimize(statement, ["test2"])
    assert isinstance(minimized, PIf)
    assert minimized == PIf(PBool(True), PCreate("test2"), PSkip())

    minimized = PStatement.minimize(statement, ["test3"])
    assert isinstance(minimized, PIf)
    assert minimized == PIf(PBool(True), PSkip(), PCreate("test3"))

    minimized = PStatement.minimize(statement, ["test1"])
    assert isinstance(minimized, PSkip)


