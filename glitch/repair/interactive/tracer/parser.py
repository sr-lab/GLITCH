# pyright: reportUnusedFunction=false, reportUnusedVariable=false
import logging
from enum import Enum
from ply.lex import lex, LexToken
from ply.yacc import yacc, YaccProduction
from dataclasses import dataclass
from typing import List, Any


@dataclass
class Syscall:
    cmd: str
    args: List[Any]
    exitCode: int


@dataclass
class Call:
    cmd: str
    args: List[str]


@dataclass
class BinaryOperation:
    left: str
    right: str
    operation: str


class OpenFlag(Enum):
    O_APPEND = 1
    O_ASYNC = 2
    O_CLOEXEC = 3
    O_CREAT = 4
    O_DIRECT = 5
    O_DIRECTORY = 6
    O_DSYNC = 7
    O_EXCL = 8
    O_LARGEFILE = 9
    O_NOATIME = 10
    O_NOCTTY = 11
    O_NOFOLLOW = 12
    O_NONBLOCK = 13
    O_PATH = 14
    O_SYNC = 15
    O_TMPFILE = 16
    O_TRUNC = 17
    O_RDONLY = 18
    O_WRONLY = 19
    O_RDWR = 20


class ORedFlag(Enum):
    AT_EMPTY_PATH = 0
    AT_NO_AUTOMOUNT = 1
    AT_SYMLINK_NOFOLLOW = 2


class UnlinkFlag(Enum):
    AT_REMOVEDIR = 0


def parse_tracer_output(tracer_output: str, debug: bool = False) -> Syscall:
    # Tokens defined as functions preserve order
    def t_ADDRESS(t: LexToken):
        r"0[xX][0-9a-fA-F]+"
        return t

    def t_PID(t: LexToken):
        r"\[pid\s\d+\]"
        return t

    def t_COMMA(t: LexToken):
        r","
        return t

    def t_EQUAL(t: LexToken):
        r"="
        return t

    def t_PIPE(t: LexToken):
        r"\|"
        return t

    def t_LCURLY(t: LexToken):
        r"\{"
        return t

    def t_RCURLY(t: LexToken):
        r"\}"
        return t

    def t_LPARENS(t: LexToken):
        r"\("
        return t

    def t_RPARENS(t: LexToken):
        r"\)"
        return t

    def t_LPARENSR(t: LexToken):
        r"\["
        return t

    def t_RPARENSR(t: LexToken):
        r"\]"
        return t

    def t_POSITIVE_NUMBER(t: LexToken):
        r"[0-9]+"
        return t

    def t_NEGATIVE_NUMBER(t: LexToken):
        "-[0-9]+"
        return t

    def t_ID(t: LexToken):
        r"[a-zA-Z][a-zA-Z0-9_]*"
        if t.value in [flag.name for flag in OpenFlag]:
            t.type = "OPEN_FLAG"
            t.value = OpenFlag[t.value]  # type: ignore
        elif t.value in [flag.name for flag in ORedFlag]:
            t.type = "ORED_FLAG"
            t.value = ORedFlag[t.value]  # type: ignore
        elif t.value in [flag.name for flag in UnlinkFlag]:
            t.type = "UNLINK_FLAG"
            t.value = UnlinkFlag[t.value]  # type: ignore
        return t

    def t_STRING(t: LexToken):
        r"(\'([^\\]|(\\(\n|.)))*?\')|(\"([^\\]|(\\(\n|.)))*?\")"
        t.value = t.value[1:-1]
        t.lexer.lineno += t.value.count("\n")
        return t

    tokens = tuple(
        map(
            lambda token: token[2:],
            filter(lambda v: v.startswith("t_"), locals().keys()),
        ),
    ) + ("OPEN_FLAG", "ORED_FLAG", "UNLINK_FLAG")

    t_ignore_ANY = r"[\t\ \n]"

    def t_COMMENT(t: LexToken) -> None:
        r"/\*.*?\*/"
        # Ignore comments

    def t_ANY_error(t: LexToken) -> None:
        logging.error(f"Illegal character {t.value[0]!r}.")
        t.lexer.skip(1)

    lexer = lex()
    # Give the lexer some input
    lexer.input(tracer_output)

    # print tokens
    if debug:
        while True:
            tok = lexer.token()
            if not tok:
                break
            print(tok)

    def p_syscalls_pid(p: YaccProduction) -> None:
        r"syscalls : PID syscall"
        p[0] = p[2]

    def p_syscalls_exit(p: YaccProduction) -> None:
        r"syscalls : PID syscall exit_message"
        p[0] = p[2]

    def p_syscalls_no_pid(p: YaccProduction) -> None:
        r"syscalls : syscall exit_message"
        p[0] = p[1]

    def p_syscalls(p: YaccProduction) -> None:
        r"syscalls : syscall"
        p[0] = p[1]

    def p_exit_message(p: YaccProduction) -> None:
        r"exit_message : ID LPARENS ids RPARENS"
        p[0] = p[1]

    def p_ids(p: YaccProduction) -> None:
        r"ids : ids ID"
        p[0] = p[1] + [p[2]]

    def p_ids_single(p: YaccProduction) -> None:
        r"ids : ID"
        p[0] = [p[1]]

    def p_syscall(p: YaccProduction) -> None:
        r"syscall : ID LPARENS terms RPARENS EQUAL number"
        p[0] = Syscall(p[1], p[3], int(p[6]))

    def p_terms(p: YaccProduction) -> None:
        r"terms : terms COMMA term"
        p[0] = p[1] + [p[3]]

    def p_terms_single(p: YaccProduction) -> None:
        r"terms : term"
        p[0] = [p[1]]

    def p_term_number(p: YaccProduction) -> None:
        r"term : number"
        p[0] = p[1]

    def p_term_id(p: YaccProduction) -> None:
        r"term : ID"
        p[0] = p[1]

    def p_call(p: YaccProduction) -> None:
        r"term : ID LPARENS terms RPARENS"
        p[0] = Call(p[1], p[3])

    def p_term_address(p: YaccProduction) -> None:
        r"term : ADDRESS"
        p[0] = p[1]

    def p_term_string(p: YaccProduction) -> None:
        r"term : STRING"
        p[0] = p[1]

    def p_term_open_flags(p: YaccProduction) -> None:
        r"term : open_flags"
        p[0] = p[1]

    def p_term_ored_flags(p: YaccProduction) -> None:
        r"term : ored_flags"
        p[0] = p[1]

    def p_term_unlink_flags(p: YaccProduction) -> None:
        r"term : unlink_flags"
        p[0] = p[1]

    def p_term_list(p: YaccProduction) -> None:
        r"term : LPARENSR terms RPARENSR"
        p[0] = p[2]

    def p_term_dict(p: YaccProduction) -> None:
        r"term : LCURLY key_values RCURLY"
        p[0] = p[2]

    def p_term_or(p: YaccProduction) -> None:
        r"term : term PIPE term"
        p[0] = BinaryOperation(p[1], p[3], "|")

    def p_key_values(p: YaccProduction) -> None:
        r"key_values : key_values COMMA key_value"
        p[1].update({p[3][0]: p[3][1]})
        p[0] = p[1]

    def p_key_values_single(p: YaccProduction) -> None:
        r"key_values : key_value"
        p[0] = {p[1][0]: p[1][1]}

    def p_key_value(p: YaccProduction) -> None:
        r"key_value : ID EQUAL term"
        p[0] = (p[1], p[3])

    def p_number(p: YaccProduction) -> None:
        r"number : POSITIVE_NUMBER"
        p[0] = p[1]

    def p_number_negative(p: YaccProduction) -> None:
        r"number : NEGATIVE_NUMBER"
        p[0] = p[1]

    def p_open_flags_single(p: YaccProduction) -> None:
        r"open_flags : OPEN_FLAG"
        p[0] = [p[1]]

    def p_open_flags(p: YaccProduction) -> None:
        r"open_flags : open_flags PIPE OPEN_FLAG"
        p[0] = p[1] + [p[3]]

    def p_ored_flags_single(p: YaccProduction) -> None:
        r"ored_flags : ORED_FLAG"
        p[0] = [p[1]]

    def p_ored_flags(p: YaccProduction) -> None:
        r"ored_flags : ored_flags PIPE ORED_FLAG"
        p[0] = p[1] + [p[3]]

    def p_unlink_flags_single(p: YaccProduction) -> None:
        r"unlink_flags : UNLINK_FLAG"
        p[0] = [p[1]]

    def p_unlink_flags(p: YaccProduction) -> None:
        r"unlink_flags : unlink_flags PIPE UNLINK_FLAG"
        p[0] = p[1] + [p[3]]

    def p_error(p: YaccProduction) -> None:
        logging.error(f"Syntax error at {p.value!r}")

    # Build the parser
    parser = yacc()
    return parser.parse(tracer_output)
