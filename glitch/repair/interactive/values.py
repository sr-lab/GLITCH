from glitch.repair.interactive.delta_p import *

UNDEF = "glitch-undef"


class DefaultValue:
    DEFAULT_MODE = PEConst(PStr("644"))
    DEFAULT_OWNER = PEConst(PStr("root"))
    DEFAULT_STATE = PEConst(PStr("present"))
    DEFAULT_CONTENT = PEUndef()
