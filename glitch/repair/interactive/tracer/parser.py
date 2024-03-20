import logging
from enum import Enum
from ply.lex import lex
from ply.yacc import yacc
from dataclasses import dataclass
from typing import List


@dataclass
class Syscall:
    cmd: str
    args: List[str]
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
    def t_ADDRESS(t):
        r"0[xX][0-9a-fA-F]+"
        return t

    def t_PID(t):
        r"\[pid\s\d+\]"
        return t

    def t_COMMA(t):
        r","
        return t

    def t_EQUAL(t):
        r"="
        return t

    def t_PIPE(t):
        r"\|"
        return t

    def t_LCURLY(t):
        r"\{"
        return t

    def t_RCURLY(t):
        r"\}"
        return t

    def t_LPARENS(t):
        r"\("
        return t

    def t_RPARENS(t):
        r"\)"
        return t

    def t_LPARENSR(t):
        r"\["
        return t

    def t_RPARENSR(t):
        r"\]"
        return t

    def t_POSITIVE_NUMBER(t):
        r"[0-9]+"
        return t

    def t_NEGATIVE_NUMBER(t):
        "-[0-9]+"
        return t

    def t_ID(t):
        r"[a-zA-Z][a-zA-Z0-9_]*"
        if t.value in [flag.name for flag in OpenFlag]:
            t.type = "OPEN_FLAG"
            t.value = OpenFlag[t.value]
        elif t.value in [flag.name for flag in ORedFlag]:
            t.type = "ORED_FLAG"
            t.value = ORedFlag[t.value]
        elif t.value in [flag.name for flag in UnlinkFlag]:
            t.type = "UNLINK_FLAG"
            t.value = UnlinkFlag[t.value]
        return t

    def t_STRING(t):
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

    def t_COMMENT(t) -> None:
        r"/\*.*?\*/"
        # Ignore comments

    def t_ANY_error(t) -> None:
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

    def p_syscalls_pid(p) -> None:
        r"syscalls : PID syscall"
        p[0] = p[2]

    def p_syscalls_exit(p) -> None:
        r"syscalls : PID syscall exit_message"
        p[0] = p[2]

    def p_syscalls_no_pid(p) -> None:
        r"syscalls : syscall exit_message"
        p[0] = p[1]

    def p_syscalls(p) -> None:
        r"syscalls : syscall"
        p[0] = p[1]

    def p_exit_message(p) -> None:
        r"exit_message : ID LPARENS ids RPARENS"
        p[0] = p[1]

    def p_ids(p) -> None:
        r"ids : ids ID"
        p[0] = p[1] + [p[2]]

    def p_ids_single(p) -> None:
        r"ids : ID"
        p[0] = [p[1]]

    def p_syscall(p) -> None:
        r"syscall : ID LPARENS terms RPARENS EQUAL number"
        p[0] = Syscall(p[1], p[3], int(p[6]))

    def p_terms(p) -> None:
        r"terms : terms COMMA term"
        p[0] = p[1] + [p[3]]

    def p_terms_single(p) -> None:
        r"terms : term"
        p[0] = [p[1]]

    def p_term_number(p) -> None:
        r"term : number"
        p[0] = p[1]

    def p_term_id(p) -> None:
        r"term : ID"
        p[0] = p[1]

    def p_call(p) -> None:
        r"term : ID LPARENS terms RPARENS"
        p[0] = Call(p[1], p[3])

    def p_term_address(p) -> None:
        r"term : ADDRESS"
        p[0] = p[1]

    def p_term_string(p) -> None:
        r"term : STRING"
        p[0] = p[1]

    def p_term_open_flags(p) -> None:
        r"term : open_flags"
        p[0] = p[1]

    def p_term_ored_flags(p) -> None:
        r"term : ored_flags"
        p[0] = p[1]

    def p_term_unlink_flags(p) -> None:
        r"term : unlink_flags"
        p[0] = p[1]

    def p_term_list(p) -> None:
        r"term : LPARENSR terms RPARENSR"
        p[0] = p[2]

    def p_term_dict(p) -> None:
        r"term : LCURLY key_values RCURLY"
        p[0] = p[2]

    def p_term_or(p) -> None:
        r"term : term PIPE term"
        p[0] = BinaryOperation(p[1], p[3], "|")

    def p_key_values(p) -> None:
        r"key_values : key_values COMMA key_value"
        p[1].update({p[3][0]: p[3][1]})
        p[0] = p[1]

    def p_key_values_single(p) -> None:
        r"key_values : key_value"
        p[0] = {p[1][0]: p[1][1]}

    def p_key_value(p) -> None:
        r"key_value : ID EQUAL term"
        p[0] = (p[1], p[3])

    def p_number(p) -> None:
        r"number : POSITIVE_NUMBER"
        p[0] = p[1]

    def p_number_negative(p) -> None:
        r"number : NEGATIVE_NUMBER"
        p[0] = p[1]

    def p_open_flags_single(p) -> None:
        r"open_flags : OPEN_FLAG"
        p[0] = [p[1]]

    def p_open_flags(p) -> None:
        r"open_flags : open_flags PIPE OPEN_FLAG"
        p[0] = p[1] + [p[3]]

    def p_ored_flags_single(p) -> None:
        r"ored_flags : ORED_FLAG"
        p[0] = [p[1]]

    def p_ored_flags(p) -> None:
        r"ored_flags : ored_flags PIPE ORED_FLAG"
        p[0] = p[1] + [p[3]]

    def p_unlink_flags_single(p) -> None:
        r"unlink_flags : UNLINK_FLAG"
        p[0] = [p[1]]

    def p_unlink_flags(p) -> None:
        r"unlink_flags : unlink_flags PIPE UNLINK_FLAG"
        p[0] = p[1] + [p[3]]

    def p_error(p) -> None:
        logging.error(f"Syntax error at {p.value!r}")

    # Build the parser
    parser = yacc()
    return parser.parse(tracer_output)
