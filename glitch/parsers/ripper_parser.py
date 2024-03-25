# pyright: reportUnusedFunction=false, reportUnusedVariable=false
from ply.lex import lex, LexToken
from ply.yacc import yacc, YaccProduction


def parser_yacc(script_ast: str):
    tokens = (
        "LPAREN",
        "RPAREN",
        "STRING",
        "ID",
        "INTEGER",
        "TRUE",
        "FALSE",
        "COMMENT",
        "PLUS",
    )
    states = (("id", "exclusive"),)

    t_LPAREN = r"\["
    t_RPAREN = r"\]"
    t_TRUE = r"true"
    t_FALSE = r"false"
    t_ignore_ANY = r"[nil\,\ \n]"
    t_PLUS = r"\+"

    def t_INTEGER(t: LexToken):
        r"[0-9]+"
        t.value = int(t.value)  # type: ignore
        return t

    def t_STRING(t: LexToken):
        r"\"([^\\\n]|(\\.))*?\" "
        t.value = t.value[1:-1]
        return t

    def t_begin_id(t: LexToken) -> None:
        r"\:"
        t.lexer.begin("id")

    def t_id_end(t: LexToken) -> None:
        r"[\,]"
        t.lexer.begin("INITIAL")

    def t_id_RPAREN(t: LexToken):
        r"\]"
        t.lexer.begin("INITIAL")
        return t

    def t_id_COMMENT(t: LexToken):
        r"@comment"
        return t

    def t_id_ID(t: LexToken):
        r"[^,\]]+"
        return t

    def t_ANY_error(t: LexToken) -> None:
        print(f"Illegal character {t.value[0]!r}.")
        t.lexer.skip(1)

    lexer = lex()
    # Give the lexer some input
    lexer.input(script_ast)

    def p_program(p: YaccProduction) -> None:
        r"program : comments list"
        p[0] = (p[1], p[2])

    def p_comments(p: YaccProduction) -> None:
        r"comments : comments comment"
        p[0] = [p[2]] + p[1]

    def p_comments_empty(p: YaccProduction) -> None:
        r"comments : empty"
        p[0] = []

    def p_comment(p: YaccProduction) -> None:
        r"comment : LPAREN COMMENT STRING LPAREN INTEGER INTEGER RPAREN RPAREN"
        p[0] = (p[3], p[5])

    def p_list(p: YaccProduction) -> None:
        r"list : LPAREN args RPAREN"
        p[0] = p[2]

    def p_args_value(p: YaccProduction) -> None:
        r"args : value args"
        p[0] = [p[1]] + p[2]

    def p_args_list(p: YaccProduction) -> None:
        r"args : list args"
        p[0] = [p[1]] + p[2]

    def p_args_empty(p: YaccProduction) -> None:
        r"args : empty"
        p[0] = []

    def p_empty(p: YaccProduction) -> None:
        r"empty :"

    def p_value_string(p: YaccProduction) -> None:
        r"value : string"
        p[0] = p[1]

    def p_multi_string(p: YaccProduction) -> None:
        r"string : STRING PLUS string"
        p[0] = p[1] + p[3]

    def p_string(p: YaccProduction) -> None:
        r"string : STRING"
        p[0] = p[1]

    def p_value_integer(p: YaccProduction) -> None:
        r"value : INTEGER"
        p[0] = p[1]

    def p_value_false(p: YaccProduction) -> None:
        r"value : FALSE"
        p[0] = False

    def p_value_true(p: YaccProduction) -> None:
        r"value : TRUE"
        p[0] = True

    def p_value_id(p: YaccProduction) -> None:
        r"value : ID"
        p[0] = ("id", p[1])  # FIXME

    def p_error(p: YaccProduction) -> None:
        print(f"Syntax error at {p.value!r}")

    # Build the parser
    parser = yacc()
    return parser.parse(script_ast)
