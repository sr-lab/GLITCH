import re
from typing import Any

def lex(
    module: Any = None,
    object: Any = None,
    debug: bool = False,
    optimize: bool = False,
    lextab: str = "lextab",
    reflags: int = int(re.VERBOSE),
    nowarn: bool = False,
    outputdir: str | None = None,
    debuglog: str | None = None,
    errorlog: str | None = None,
) -> Any: ...

class Lexer:
    lineno: int

    def begin(self, state: str) -> None: ...
    def skip(self, n: int) -> None: ...

class LexToken:
    value: str
    lexer: Lexer
    lexpos: int
    type: str
