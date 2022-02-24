from ply.lex import lex
from ply.yacc import yacc

def parser_yacc(script_ast):
        tokens = ('LPAREN', 'RPAREN', 'STRING', 'ID', 'INTEGER', 
            'TRUE', 'FALSE')
        states = (
            ('string', 'exclusive'),
            ('id', 'exclusive'),
        )

        t_LPAREN = r'\['
        t_RPAREN = r'\]'
        t_TRUE = r'true'
        t_FALSE = r'false'
        t_ignore_ANY = r'[nil\,\ \n]'

        def t_INTEGER(t):
            r'[0-9]+'
            t.value = int(t.value)
            return t

        def t_begin_string(t):
            r'\"'
            t.lexer.begin('string')

        def t_string_end(t):
            r'\"'
            t.lexer.begin('INITIAL')

        def t_string_STRING(t):
            r'[^"]+'
            return t

        def t_begin_id(t):
            r'\:'
            t.lexer.begin('id')

        def t_id_end(t):
            r'\,'
            t.lexer.begin('INITIAL')

        def t_id_ID(t):
            r'[^,]+'
            return t

        def t_ANY_error(t):
            print(f'Illegal character {t.value[0]!r}.')
            t.lexer.skip(1)

        lexer = lex()
        # Give the lexer some input
        lexer.input(script_ast)

        def p_list(p):
            r'list : LPAREN args RPAREN'
            p[0] = p[2]

        def p_args_value(p):
            r'args : value args'
            p[0] = [p[1]] + p[2]

        def p_args_list(p):
            r'args : list args'
            p[0] = [p[1]] + p[2]

        def p_args_empty(p):
            r'args : empty'
            p[0] = []

        def p_empty(p):
            r'empty : '

        def p_value_string(p):
            r'value : STRING'
            p[0] = p[1]

        def p_value_integer(p):
            r'value : INTEGER'
            p[0] = p[1]

        def p_value_false(p):
            r'value : FALSE'
            p[0] = False
        
        def p_value_true(p):
            r'value : TRUE'
            p[0] = True

        def p_value_id(p):
            r'value : ID'
            p[0] = ("id", p[1]) #FIXME

        def p_error(p):
            print(f'Syntax error at {p.value!r}')

        # Build the parser
        parser = yacc()
        return parser.parse(script_ast)