from enum import Enum
from ply.lex import lex
from ply.yacc import yacc

class Statement:
    pass

class OpenFlag(Enum):
    O_RDONLY = 0
    O_WRONLY = 1
    O_RDWR = 2
    O_CREAT = 3
    O_DIRECTORY = 4
    O_EXCL = 5
    O_TRUNC = 6

def parse_tracer_output(tracer_output: str) -> Statement:
    def t_OPEN(t):
        r"open"
        t.v = t.value
        return t
    
    def t_STAT(t):
        r"stat"
        t.v = t.value
        return t
    
    def t_RENAME(t):
        r"rename"
        t.v = t.value
        return t
    
    def t_MODE(t):
        r"[0-9]+"
        t.v = t.value
        return t
    
    def t_NUMBER(t):
        "(-)?[0-9]+"
        t.v = int(t.value)
        return t
    
    def t_TERM(t):
        r"[^,\)]+"
        t.v = t.value
        return t

    def t_PATH(t):
        r'\"([^\\\n]|(\\.))*?\"'
        t.value = t.value[1:-1]
        return t
    
    def t_WORD(t):
        r"[a-zA-Z][a-zA-Z_]*"
        t.v = t.value
        return t
    
    def t_OPEN_FLAG(t):
        r"O_RDONLY|O_WRONLY|O_RDWR|O_CREAT|O_DIRECTORY|O_EXCL|O_TRUNC"
        t.v = OpenFlag[t.value]
        return t
    
    lexer = lex()
    # Give the lexer some input
    lexer.input(tracer_output)

    

    # Build the parser
    parser = yacc()
    return parser.parse(tracer_output)