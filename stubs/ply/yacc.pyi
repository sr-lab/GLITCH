from typing import Any

def yacc(
    method: str = "LALR",
    debug: bool = True,
    module: Any = None,
    tabmodule: str = "parsetab",
    start: Any = None,
    check_recursion: bool = True,
    optimize: bool = False,
    write_tables: bool = True,
    debugfile: str = "parser.out",
    outputdir: str | None = None,
    debuglog: str | None = None,
    errorlog: str | None = None,
    picklefile: str | None = None,
) -> Any: ...

class YaccProduction:
    value: str

    def __getitem__(self, n: int) -> Any: ...
    def __setitem__(self, n: int, v: Any) -> Any: ...
    def lineno(self, n: int) -> int: ...
    def lexpos(self, n: int) -> int: ...
    def set_lineno(self, n: int, lineno: int) -> None: ...
