import ply.lex as lex
import ply.yacc as yacc
from src.js_parser import get_js_parser


# --- C Lexer ---
class CLexerConfig:
    tokens = ('INT', 'IF', 'PRINT', 'ID', 'NUMBER', 'EQUALS', 'LESS', 'SEMI', 'LBRACE', 'RBRACE', 'LPAREN', 'RPAREN')

    t_ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    t_NUMBER = r'\d+'
    t_EQUALS = r'='
    t_LESS = r'<'
    t_SEMI = r';'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_ignore = ' \t\n'

    def t_INT(self, t):
        r'int'
        return t

    def t_IF(self, t):
        r'if'
        return t

    def t_PRINT(self, t):
        r'print'
        return t

    def t_LBRACE(self, t):
        r'\{'
        return t

    def t_RBRACE(self, t):
        r'\}'
        return t

    def t_error(self, t):
        print(f"Illegal character: {t.value[0]}")
        t.lexer.skip(1)

    def build(self):
        return lex.lex(module=self)


# --- C Parser ---
class CParserConfig:
    def __init__(self):
        self.tokens = CLexerConfig.tokens
        self.precedence = (
            ('left', 'LESS'),
            ('left', 'EQUALS'),
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
        '''statement : INT ID EQUALS NUMBER SEMI'''
        p[0] = {"type": "Declaration", "var": p[2], "value": p[4]}

    def p_statement_if(self, p):
        '''statement : IF LPAREN ID LESS NUMBER RPAREN LBRACE statements RBRACE'''
        p[0] = {"type": "If", "condition": {"left": p[3], "op": p[4], "right": p[5]}, "body": p[8]}

    def p_statement_print(self, p):
        '''statement : PRINT LPAREN ID RPAREN SEMI'''
        p[0] = {"type": "Print", "value": {"type": "Var", "name": p[3]}}

    def p_error(self, p):
        if p:
            raise Exception(f"Syntax error at '{p.value}' on line {p.lineno}")
        else:
            raise Exception("Syntax error: Unexpected end of input")


# --- Semantic Analysis ---
def semantic_analysis(ast):
    variables = set()

    def check_node(node):
        if node["type"] == "Declaration":
            variables.add(node["var"])
        elif node["type"] == "If":
            if node["condition"]["left"] not in variables:
                raise Exception(f"Undefined variable: {node['condition']['left']}")
            for stmt in node["body"]:
                check_node(stmt)
        elif node["type"] == "Print":
            if node["value"]["name"] not in variables:
                raise Exception(f"Undefined variable: {node['value']['name']}")

    for stmt in ast["body"]:
        check_node(stmt)
    return ast


# --- Code Generators ---
def python_codegen(ast):
    code = ""
    indent = 0

    def gen_indent():
        return "    " * indent

    def gen_node(node):
        nonlocal code, indent
        if node["type"] == "Declaration":
            code += f"{gen_indent()}{node['var']} = {node['value']}\n"
        elif node["type"] == "If":
            code += f"{gen_indent()}if {node['condition']['left']} {node['condition']['op']} {node['condition']['right']}:\n"
            indent += 1
            for stmt in node["body"]:
                gen_node(stmt)
            indent -= 1
        elif node["type"] == "Print":
            code += f"{gen_indent()}print({node['value']['name']})\n"

    for stmt in ast["body"]:
        gen_node(stmt)
    return code


def typescript_codegen(ast):
    code = ""
    indent = 0

    def gen_indent():
        return "    " * indent

    def gen_node(node):
        nonlocal code, indent
        if node["type"] == "Declaration":
            code += f"{gen_indent()}let {node['var']}: number = {node['value']};\n"
        elif node["type"] == "If":
            code += f"{gen_indent()}if ({node['condition']['left']} {node['condition']['op']} {node['condition']['right']}) {{\n"
            indent += 1
            for stmt in node["body"]:
                gen_node(stmt)
            indent -= 1
            code += f"{gen_indent()}}}\n"
        elif node["type"] == "Print":
            code += f"{gen_indent()}console.log({node['value']['name']});\n"

    for stmt in ast["body"]:
        gen_node(stmt)
    return code


codegens = {
    "python": python_codegen,
    "typescript": typescript_codegen
}


# --- Main Function ---
def transpile(source_code, source_lang="c", target_lang="python"):
    if source_lang == "c":
        lexer = CLexerConfig().build()
        parser = yacc.yacc(module=CParserConfig(), debug=True)
    elif source_lang == "js":
        lexer, parser = get_js_parser()
    else:
        raise ValueError("Unsupported source language")

    lexer.input(source_code)
    ast = parser.parse(source_code, lexer=lexer)
    print("AST:", ast)  # Debug line
    checked_ast = semantic_analysis(ast)
    return codegens[target_lang](checked_ast)


if __name__ == "__main__":
    # Test C to Python
    c_code = """
    int x = 5;
    if (x < 10) {
        print(x);
    }
    """
    print("C to Python:")
    print(transpile(c_code, "c", "python"))

    # Test JS to TypeScript
    js_code = """
    var x = 5;
    if (x < 10) console.log(x);
    """
    print("\nJS to TypeScript:")
    print(transpile(js_code, "js", "typescript"))