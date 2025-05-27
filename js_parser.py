import ply.lex as lex
import ply.yacc as yacc

# --- JS Lexer ---
class JSLexerConfig:
    tokens = ('VAR', 'IF', 'CONSOLE', 'DOT', 'LOG', 'ID', 'NUMBER', 'EQUALS', 'LESS', 'SEMI', 'LPAREN', 'RPAREN', 'PLUS', 'LBRACE', 'RBRACE')

    # Token definitions
    t_ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    t_NUMBER = r'\d+'
    t_EQUALS = r'='
    t_LESS = r'<'
    t_SEMI = r';'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_PLUS = r'\+'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_ignore = ' \t\n'

    def t_VAR(self, t):
        r'var'
        return t

    def t_IF(self, t):
        r'if'
        return t

    def t_CONSOLE(self, t):
        r'console'
        return t

    def t_DOT(self, t):
        r'\.'
        return t

    def t_LOG(self, t):
        r'log'
        return t

    def t_error(self, t):
        print(f"Illegal character: {t.value[0]}")
        t.lexer.skip(1)

    def build(self):
        return lex.lex(module=self)

# --- JS Parser ---
class JSParserConfig:
    def __init__(self):
        self.tokens = JSLexerConfig.tokens
        self.precedence = (
            ('left', 'LESS'),
            ('left', 'PLUS'),
            ('left', 'DOT'),
        )

    def p_program(self, p):
        '''program : statements'''
        p[0] = {"type": "Program", "body": p[1]}

    def p_statements(self, p):
        '''statements : statement
                      | statements statement
                      | '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]] if len(p) == 3 else []

    def p_statement_declaration(self, p):
        '''statement : VAR ID EQUALS expression SEMI'''
        p[0] = {"type": "Declaration", "var": p[2], "value": p[4]}

    def p_expression(self, p):
        '''expression : NUMBER
                      | ID
                      | ID PLUS ID
                      | ID PLUS NUMBER'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = {"left": p[1], "op": p[2], "right": p[3]}

    def p_statement_if(self, p):
        '''statement : IF LPAREN ID LESS NUMBER RPAREN statement
                     | IF LPAREN ID LESS NUMBER RPAREN LBRACE statements RBRACE'''
        if len(p) == 8:
            p[0] = {"type": "If", "condition": {"left": p[3], "op": p[4], "right": p[5]}, "body": [p[7]]}
        else:
            p[0] = {"type": "If", "condition": {"left": p[3], "op": p[4], "right": p[5]}, "body": p[8]}

    def p_statement_print(self, p):
        '''statement : CONSOLE DOT LOG LPAREN ID RPAREN SEMI'''
        p[0] = {"type": "Print", "value": {"type": "Var", "name": p[5]}}

    def p_error(self, p):
        if p:
            raise Exception(f"Syntax error at '{p.value}' on line {p.lineno}")
        else:
            raise Exception("Syntax error: Unexpected end of input")
