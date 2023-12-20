import logging
from enum import Enum
from ply.lex import lex
from ply.yacc import yacc
from dataclasses import dataclass
from typing import Optional, List


class Statement:
    pass


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


@dataclass
class SStat(Statement):
    path: str
    flags: List[str]
    exitCode: int


@dataclass
class SFStat(Statement):
    fd: str
    flags: List[str]
    exitCode: int


@dataclass
class SFStatAt(Statement):
    dirfd: str
    path: str
    flags: List[str]
    oredFlags: List[str]
    exitCode: int


@dataclass
class SOpen(Statement):
    path: str
    flags: List[OpenFlag]
    mode: Optional[str]
    exitCode: int


@dataclass
class SOpenAt(Statement):
    dirfd: str
    path: str
    flags: List[OpenFlag]
    mode: Optional[str]
    exitCode: int


@dataclass
class SRename(Statement):
    src: str
    dst: str
    exitCode: int


@dataclass
class SUnknown(Statement):
    cmd: str
    args: List[str]
    exitCode: int


def parse_tracer_output(tracer_output: str, debug=False) -> Statement:
    verbs = {
        "open": "OPEN",
        "openat": "OPENAT",
        "stat": "STAT",
        "lstat": "LSTAT",
        "fstat": "FSTAT",
        "fstatat": "FSTATAT",
        "fstatat64": "FSTATAT64",
        "newfstatat": "NEWFSTATAT",
        "rename": "RENAME",
    }

    # Tokens defined as functions preserve order
    def t_ADDRESS(t):
        r"0[xX][0-9a-fA-F]+"
        return t
    
    def t_OBJECT(t):
        r"\{.*\}"
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
    
    def t_LPARENS(t):
        r"\("
        return t
    
    def t_RPARENS(t):
        r"\)"
        return t
    
    def t_POSITIVE_NUMBER(t):
        r"[0-9]+"
        return t
    
    def t_NEGATIVE_NUMBER(t):
        "-[0-9]+"
        return t

    def t_WORD(t):
        r"[a-zA-Z][a-zA-Z_]*"
        if t.value in [flag.name for flag in OpenFlag]:
            t.type = "OPEN_FLAG"
            t.value = OpenFlag[t.value]
        elif t.value in [flag.name for flag in ORedFlag]:
            t.type = "ORED_FLAG"
            t.value = ORedFlag[t.value]
        elif t.value == "AT_FDCWD":
            t.type = "AT_FDCWD"
        elif t.value in verbs.keys():
            t.type = verbs[t.value]
        return t

    def t_STRING(t):
        r"(\'([^\\]|(\\(\n|.)))*?\')|(\"([^\\]|(\\(\n|.)))*?\")"
        t.value = t.value[1:-1]
        t.lexer.lineno += t.value.count("\n")
        return t
    
    tokens = tuple(
        map(
            lambda token: token[2:], filter(
                lambda v: v.startswith("t_"), locals().keys()
            )
        ),
    ) + ("OPEN_FLAG", "ORED_FLAG", "AT_FDCWD") + tuple(verbs.values())

    t_ignore_ANY = r'[\t\ \n]'

    def t_ANY_error(t):
        logging.error(f'Illegal character {t.value[0]!r}.')
        t.lexer.skip(1)
        #TODO: REMOVE
        exit(-1)
    
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

    def p_statements_pid(p):
        r"statements : PID statement"
        p[0] = p[2]

    def p_statements_exit(p):
        r"statements : PID statement exit_message"
        p[0] = p[2]

    def p_statements_no_pid(p):
        r"statements : statement exit_message"
        p[0] = p[1]

    def p_statements(p):
        r"statements : statement"
        p[0] = p[1]

    def p_exit_message(p):
        r"exit_message : WORD LPARENS words RPARENS"
        p[0] = p[1]

    def p_words(p):
        r"words : words WORD"
        p[0] = p[1] + [p[2]]

    def p_words_single(p):
        r"words : WORD"
        p[0] = [p[1]]

    def p_statement_stat(p):
        r"statement : stat"
        p[0] = p[1]

    def p_statement_open(p):
        r"statement : open"
        p[0] = p[1]

    def p_statement_rename(p):
        r"statement : rename"
        p[0] = p[1]
    
    def p_statement_open_at(p):
        r"statement : open_at"
        p[0] = p[1]

    def p_statement_fstat(p):
        r"statement : fstat"
        p[0] = p[1]

    def p_statement_fstatat(p):
        r"statement : fstatat"
        p[0] = p[1]

    def p_statement_unknown(p):
        r"statement : unknown"
        p[0] = p[1]

    def p_open_flags_single(p):
        r"open_flags : OPEN_FLAG"
        p[0] = [p[1]]

    def p_open_flags(p):
        r"open_flags : OPEN_FLAG PIPE open_flags"
        p[0] = [p[1]] + p[3]

    def p_ored_flags_single(p):
        r"ored_flags : ORED_FLAG"
        p[0] = [p[1]]

    def p_ored_flags(p):
        r"ored_flags : ORED_FLAG PIPE ored_flags"
        p[0] = [p[1]]

    def p_ored_flags_integer(p):
        r"ored_flags : POSITIVE_NUMBER"
        p[0] = p[1]

    def p_terms(p):
        r"terms : terms COMMA term"
        p[0] = p[1] + [p[3]]

    def p_terms_single(p):
        r"terms : term"
        p[0] = [p[1]]

    def p_term_number(p):
        r"term : number"
        p[0] = p[1]

    def p_term_word(p):
        r"term : WORD"
        p[0] = p[1]

    def p_term_address(p):
        r"term : ADDRESS"
        p[0] = p[1]

    def p_term_object(p):
        r"term : OBJECT"
        p[0] = p[1]

    def p_term_string(p):
        r"term : STRING"
        p[0] = p[1]

    def p_stat(p):
        r"stat : STAT LPARENS STRING COMMA terms RPARENS EQUAL number"
        # STRING is PATH
        p[0] = SStat(p[3], p[5], int(p[8]))

    def p_stat_lstat(p):
        r"stat : LSTAT LPARENS STRING COMMA terms RPARENS EQUAL number"
        # STRING is PATH
        p[0] = SStat(p[3], p[5], int(p[8]))

    def p_fstat(p):
        r"fstat : FSTAT LPARENS POSITIVE_NUMBER COMMA terms RPARENS EQUAL number"
        p[0] = SFStat(p[3], p[5], int(p[8]))

    def p_fstatat(p):
        r"fstatat : fstatat_verb LPARENS dirfd COMMA STRING COMMA terms COMMA ored_flags RPARENS EQUAL number"
        # STRING is PATH
        p[0] = SFStatAt(p[3], p[5], p[7], p[9], int(p[12]))

    def p_open(p):
        r"open : OPEN LPARENS STRING COMMA open_flags RPARENS EQUAL number"
        # STRING is PATH
        p[0] = SOpen(p[3], p[5], None, int(p[8]))

    def p_open_mode(p):
        r"open : OPEN LPARENS STRING COMMA open_flags COMMA POSITIVE_NUMBER RPARENS EQUAL number"
        # The POSITIVE_NUMBER is the mode and STRING is PATH
        p[0] = SOpen(p[3], p[5], p[7], int(p[10]))

    def p_open_at(p):
        r"open_at : OPENAT LPARENS dirfd COMMA STRING COMMA open_flags RPARENS EQUAL number"
        # STRING is PATH
        p[0] = SOpenAt(p[3], p[5], p[7], None, int(p[10]))

    def p_open_at_mode(p):
        r"open_at : OPENAT LPARENS dirfd COMMA STRING COMMA open_flags COMMA POSITIVE_NUMBER RPARENS EQUAL number"
        # The POSITIVE_NUMBER is the mode and STRING is PATH
        p[0] = SOpenAt(p[3], p[5], p[7], p[9], int(p[12]))

    def p_rename(p):
        r"rename : RENAME LPARENS STRING COMMA STRING RPARENS EQUAL number"
        # STRING is PATH
        p[0] = SRename(p[3], p[5], int(p[8]))
    
    def p_unknown(p):
        r"unknown : WORD LPARENS terms RPARENS EQUAL number"
        p[0] = SUnknown(p[1], p[3], int(p[6]))

    def p_dirfd(p):
        r"dirfd : AT_FDCWD"
        p[0] = p[1]

    def p_dirfd_number(p):
        r"dirfd : POSITIVE_NUMBER"
        p[0] = p[1]

    def p_number(p):
        r"number : POSITIVE_NUMBER"
        p[0] = p[1]

    def p_number_negative(p):
        r"number : NEGATIVE_NUMBER"
        p[0] = p[1]

    def p_fstatat_verb(p):
        r"fstatat_verb : FSTATAT"
        p[0] = p[1]

    def p_fstatat_verb_64(p):
        r"fstatat_verb : FSTATAT64"
        p[0] = p[1]

    def p_fstatat_verb_new(p):
        r"fstatat_verb : NEWFSTATAT"
        p[0] = p[1]

    def p_error(p):
        logging.error(f'Syntax error at {p.value!r}')
        #TODO: REMOVE
        exit(-1)

    # Build the parser
    parser = yacc()
    return parser.parse(tracer_output)