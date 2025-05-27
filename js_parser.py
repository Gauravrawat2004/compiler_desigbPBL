import ply.lex as lex
import ply.yacc as yacc
from src.js_parser import JSLexerConfig, JSParserConfig

# --- C Lexer ---
class CLexerConfig:
    tokens = ('INT', 'IF', 'PRINTF', 'ID', 'NUMBER', 'EQUALS', 'LESS', 'SEMI', 'LBRACE', 'RBRACE', 'LPAREN', 'RPAREN', 'PLUS', 'MINUS', 'INCLUDE', 'STRING', 'COMMA', 'HEADER', 'MAIN')

    t_ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    t_NUMBER = r'\d+'
    t_EQUALS = r'='
    t_LESS = r'<'
    t_SEMI = r';'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_COMMA = r','
    t_ignore = ' \t'

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_INCLUDE(self, t):
        r'\#include'
        return t

    def t_HEADER(self, t):
        r'<\w+\.\w+>'
        return t

    def t_STRING(self, t):
        r'"[^"]*"'
        t.value = t.value[1:-1].replace('\\n', '')  # Remove quotes and \n
        return t

    def t_INT(self, t):
        r'int'
        return t

    def t_IF(self, t):
        r'if'
        return t

    def t_PRINTF(self, t):
        r'printf'
        return t

    def t_MAIN(self, t):
        r'main'
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
            ('left', 'PLUS', 'MINUS'),
            ('left', 'EQUALS'),
        )

    def p_program(self, p):
        '''program : directives statements'''
        p[0] = {"type": "Program", "directives": p[1], "body": p[2]}

    def p_directives(self, p):
        '''directives : directive
                      | directives directive
                      | '''
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = []

    def p_directive(self, p):
        '''directive : INCLUDE HEADER'''
        p[0] = {"type": "Include", "value": f"{p[1]}{p[2]}"}

    def p_statements(self, p):
        '''statements : statement
                      | statements statement
                      | '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]] if len(p) == 3 else []

    def p_statement_declaration(self, p):
        '''statement : INT ID EQUALS expression SEMI'''
        p[0] = {"type": "Declaration", "var": p[2], "value": p[4]}

    def p_expression(self, p):
        '''expression : NUMBER
                      | ID
                      | ID PLUS ID
                      | ID PLUS NUMBER
                      | ID MINUS ID
                      | ID MINUS NUMBER'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = {"left": p[1], "op": p[2], "right": p[3]}

    def p_statement_if(self, p):
        '''statement : IF LPAREN ID LESS NUMBER RPAREN LBRACE statements RBRACE'''
        p[0] = {"type": "If", "condition": {"left": p[3], "op": p[4], "right": p[5]}, "body": p[8]}

    def p_statement_main(self, p):
        '''statement : INT MAIN LPAREN RPAREN LBRACE statements RBRACE'''
        p[0] = {"type": "Main", "body": p[6]}

    def p_statement_printf(self, p):
        '''statement : PRINTF LPAREN STRING COMMA ID RPAREN SEMI'''
        p[0] = {"type": "Printf", "format": p[3], "value": {"type": "Var", "name": p[5]}}

    def p_error(self, p):
        if p:
            raise Exception(f"Syntax error at '{p.value}' on line {p.lineno}")
        else:
            raise Exception("Syntax error: Unexpected end of input")

# --- Semantic Analysis ---
def semantic_analysis(ast):
    variables = {}  # Store variable values

    def check_node(node):
        if node["type"] == "Declaration":
            if isinstance(node["value"], dict):  # Handle expressions
                left = node["value"]["left"]
                right = node["value"]["right"]
                # Evaluate left operand
                if isinstance(left, str) and left.isdigit():  # Check if it's a number literal
                    left_val = int(left)
                else:
                    if left not in variables:
                        raise Exception(f"Undefined variable: {left}")
                    left_val = variables[left]
                # Evaluate right operand
                if isinstance(right, str) and right.isdigit():  # Check if it's a number literal
                    right_val = int(right)
                else:
                    if right not in variables:
                        raise Exception(f"Undefined variable: {right}")
                    right_val = variables[right]
                # Evaluate the expression
                if node["value"]["op"] == "+":
                    node["computed_value"] = left_val + right_val
                elif node["value"]["op"] == "-":
                    node["computed_value"] = left_val - right_val
                else:
                    raise Exception(f"Unsupported operator: {node['value']['op']}")
            else:
                node["computed_value"] = int(node["value"])  # Simple number
            variables[node["var"]] = node["computed_value"]
        elif node["type"] == "If":
            if node["condition"]["left"] not in variables:
                raise Exception(f"Undefined variable: {node['condition']['left']}")
            for stmt in node["body"]:
                check_node(stmt)
        elif node["type"] == "Main":
            for stmt in node["body"]:
                check_node(stmt)
        elif node["type"] == "Printf":
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
            code += f"{gen_indent()}{node['var']} = {node['computed_value']}\n"
        elif node["type"] == "If":
            code += f"{gen_indent()}if {node['condition']['left']} {node['condition']['op']} {node['condition']['right']}:\n"
            indent += 1
            for stmt in node["body"]:
                gen_node(stmt)
            indent -= 1
        elif node["type"] == "Main":
            for stmt in node["body"]:
                gen_node(stmt)
        elif node["type"] == "Printf":
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
            code += f"{gen_indent()}let {node['var']}: number = {node['computed_value']};\n"
        elif node["type"] == "If":
            code += f"{gen_indent()}if ({node['condition']['left']} {node['condition']['op']} {node['condition']['right']}) {{\n"
            indent += 1
            for stmt in node["body"]:
                gen_node(stmt)
            indent -= 1
            code += f"{gen_indent()}}}\n"
        elif node["type"] == "Main":
            code += f"{gen_indent()}function main() {{\n"
            indent += 1
            for stmt in node["body"]:
                gen_node(stmt)
            indent -= 1
            code += f"{gen_indent()}}}\n"
            code += f"{gen_indent()}main();\n"
        elif node["type"] == "Printf":
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
        lexer = JSLexerConfig().build()
        parser = yacc.yacc(module=JSParserConfig(), debug=True)
    else:
        raise ValueError("Unsupported source language")

    lexer.input(source_code)
    ast = parser.parse(source_code, lexer=lexer)
    print("AST:", ast)  # Debug line
    checked_ast = semantic_analysis(ast)
    return codegens[target_lang](checked_ast)

# --- Test Code ---
if __name__ == "__main__":
    # Test C to Python
    c_code = """
    #include<stdio.h>
    int main() {
        int a = 15;
        int b = 25;
        int sum = a + b;
        int diff = b - a;
        int flag = 0;
        if (sum < 50) {
            int temp = sum + 10;
            if (temp < 60) {
                printf("%d\\n", temp);
                if (diff < 15) {
                    int result = temp - diff;
                    printf("%d\\n", result);
                }
            }
            printf("%d\\n", sum);
        }
        if (flag < 1) {
            printf("%d\\n", flag);
        }
    }
    """
    print("C to Python:")
    print(transpile(c_code, "c", "python"))

    # Test JS to TypeScript
    js_code = """
    var x = 10;
    var y = 20;
    var z = x + y;
    var flag = 1;
    if (z < 50) {
        var temp = z + 5;
        if (temp < 40) {
            console.log(temp);
        }
        console.log(z);
    }
    if (flag < 2) {
        console.log(flag);
    }
    """
    print("\nJS to TypeScript:")
    print(transpile(js_code, "js", "typescript"))
