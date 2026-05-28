# Grammar rules adapting to PLY format, and building the AST using the make_node function from ast_nodes.py

from typing import List

from .ast_nodes import make_node

class GrammarRules:
    tokens = (
        "INT",
        "FLOAT",
        "DOUBLE",
        "CHAR",
        "IF",
        "WHILE",
        "FOR",
        "PRINTF",
        "SCANF",
        "IDENTIFIER",
        "VALUE_NUM",
        "VALUE_CHAR",
        "TEXT_STRING",
        "ASSIGN",
        "ADD_ASSIGN",
        "SUB_ASSIGN",
        "DIV_ASSIGN",
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        "MOD",
        "EQ",
        "NE",
        "LT",
        "GT",
        "LE",
        "GE",
        "AND",
        "OR",
        "NOT",
        "INC",
        "DEC",
        "SEMICOLON",
        "COMMA",
        "LPAREN",
        "RPAREN",
        "LBRACE",
        "RBRACE",
        "AMPERSAND",
        "VOID",
        "RETURN",
    )

    precedence = (
        ("left", "OR"),
        ("left", "AND"),
        ("nonassoc", "EQ", "NE", "LT", "GT", "LE", "GE"),
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE", "MOD"),
        ("right", "NOT"),
    )

    # Modify for support function calls
    def p_program(self, p):
        "program : ext_decl_list"
        p[0] = make_node("program", children=p[1])

    # Modify for support function calls
    def p_ext_decl_list_recursive(self, p):
        "ext_decl_list : ext_decl_list ext_decl"
        p[0] = p[1] + ([p[2]] if p[2] else [])

    def p_ext_decl_list_single(self, p):
        "ext_decl_list : ext_decl"
        p[0] = [p[1]] if p[1] else []

    def p_ext_decl(self, p):
        """ext_decl : function_def
                    | decl_num
                    | decl_char"""
        p[0] = p[1]

    def p_function_def(self, p):
        "function_def : type_num IDENTIFIER LPAREN param_list RPAREN LBRACE stmt_list RBRACE"
        p[0] = make_node("function", value={"name": p[2], "type": p[1]}, children=[p[4], make_node("block", children=p[7], lineno=p.lineno(6))])

    def p_function_def_void(self, p):
        "function_def : VOID IDENTIFIER LPAREN param_list RPAREN LBRACE stmt_list RBRACE"
        p[0] = make_node("function", value={"name": p[2], "type": "void"}, children=[p[4], make_node("block", children=p[7], lineno=p.lineno(6))])

    def p_param_list(self, p):
        """param_list : param_list_nonempty
                      | empty"""
        p[0] = make_node("param_list", children=p[1] if p[1] else [])

    def p_param_list_nonempty_recursive(self, p):
        "param_list_nonempty : param_list_nonempty COMMA param"
        p[0] = p[1] + [p[3]]

    def p_param_list_nonempty_single(self, p):
        "param_list_nonempty : param"
        p[0] = [p[1]]

    def p_param(self, p):
        """param : type_num IDENTIFIER
                 | type_char IDENTIFIER"""
        p[0] = make_node("param", value={"name": p[2], "type": p[1]})

    def p_stmt_list_recursive(self, p):
        "stmt_list : stmt_list stmt"
        p[0] = p[1] + ([p[2]] if p[2] else [])

    def p_stmt_list_single(self, p):
        "stmt_list : stmt"
        p[0] = [p[1]] if p[1] else []

    def p_stmt(self, p):
        """stmt : decl_num
                | decl_char
                | assign_stmt
                | if_stmt
                | while_stmt
                | for_stmt
                | print_stmt
                | scan_stmt
                | unary_stmt
                | return_stmt
                | func_call_stmt"""
        p[0] = p[1]

    def p_return_stmt_expr(self, p):
        "return_stmt : RETURN math_expr SEMICOLON"
        p[0] = make_node("return", children=[p[2]], lineno=p.lineno(1))

    def p_return_stmt_empty(self, p):
        "return_stmt : RETURN SEMICOLON"
        p[0] = make_node("return", lineno=p.lineno(1))
        
    def p_func_call_stmt(self, p):
        "func_call_stmt : IDENTIFIER LPAREN arg_list RPAREN SEMICOLON"
        p[0] = make_node("func_call", value=p[1], children=p[3], lineno=p.lineno(1))

    def p_decl_num_plain(self, p):
        "decl_num : type_num IDENTIFIER SEMICOLON"
        p[0] = make_node("declaration", value={"name": p[2], "type": p[1]}, lineno=p.lineno(2))

    def p_decl_num_init(self, p):
        "decl_num : type_num IDENTIFIER ASSIGN math_expr SEMICOLON"
        p[0] = make_node(
            "declaration",
            value={"name": p[2], "type": p[1]},
            children=[p[4]],
            lineno=p.lineno(2),
        )

    def p_decl_char_plain(self, p):
        "decl_char : type_char IDENTIFIER SEMICOLON"
        p[0] = make_node("declaration", value={"name": p[2], "type": p[1]}, lineno=p.lineno(2))

    def p_decl_char_init(self, p):
        "decl_char : type_char IDENTIFIER ASSIGN VALUE_CHAR SEMICOLON"
        p[0] = make_node(
            "declaration",
            value={"name": p[2], "type": p[1]},
            children=[make_node("literal", value=p[4], lineno=p.lineno(4))],
            lineno=p.lineno(2),
        )

    def p_assign_stmt_math(self, p):
        "assign_stmt : IDENTIFIER assign_expr_op math_expr SEMICOLON"
        p[0] = make_node(
            "assignment",
            value={"name": p[1], "op": p[2]},
            children=[p[3]],
            lineno=p.lineno(1),
        )

    def p_type_num(self, p):
        """type_num : INT
                    | FLOAT
                    | DOUBLE"""
        p[0] = p[1]

    def p_type_char(self, p):
        "type_char : CHAR"
        p[0] = p[1]

    def p_if_stmt(self, p):
        "if_stmt : IF LPAREN cond RPAREN LBRACE stmt_list RBRACE"
        p[0] = make_node(
            "if",
            children=[p[3], make_node("block", children=p[6], lineno=p.lineno(5))],
            lineno=p.lineno(1),
        )

    def p_while_stmt(self, p):
        "while_stmt : WHILE LPAREN cond RPAREN LBRACE stmt_list RBRACE"
        p[0] = make_node(
            "while",
            children=[p[3], make_node("block", children=p[6], lineno=p.lineno(5))],
            lineno=p.lineno(1),
        )

    def p_for_stmt(self, p):
        "for_stmt : FOR LPAREN for_init SEMICOLON for_cond SEMICOLON for_step RPAREN LBRACE stmt_list RBRACE"
        p[0] = make_node(
            "for",
            children=[p[3], p[5], p[7], make_node("block", children=p[10], lineno=p.lineno(9))],
            lineno=p.lineno(1),
        )

    def p_for_init_decl_plain(self, p):
        "for_init : type_num IDENTIFIER"
        p[0] = make_node("declaration", value={"name": p[2], "type": p[1]}, lineno=p.lineno(2))

    def p_for_init_decl_init(self, p):
        "for_init : type_num IDENTIFIER ASSIGN math_expr"
        p[0] = make_node(
            "declaration",
            value={"name": p[2], "type": p[1]},
            children=[p[4]],
            lineno=p.lineno(2),
        )

    def p_for_init_assign(self, p):
        "for_init : IDENTIFIER assign_expr_op math_expr"
        p[0] = make_node(
            "assignment",
            value={"name": p[1], "op": p[2]},
            children=[p[3]],
            lineno=p.lineno(1),
        )

    def p_for_init_empty(self, p):
        "for_init : empty"
        p[0] = make_node("empty")

    def p_for_cond_expr(self, p):
        "for_cond : cond"
        p[0] = p[1]

    def p_for_cond_empty(self, p):
        "for_cond : empty"
        p[0] = make_node("empty")

    def p_for_step_prefix(self, p):
        "for_step : inc_dec_op IDENTIFIER"
        p[0] = make_node("unary_stmt", value={"name": p[2], "op": p[1], "pos": "prefix"}, lineno=p.lineno(2))

    def p_for_step_suffix(self, p):
        "for_step : IDENTIFIER inc_dec_op"
        p[0] = make_node("unary_stmt", value={"name": p[1], "op": p[2], "pos": "suffix"}, lineno=p.lineno(1))

    def p_for_step_assign(self, p):
        "for_step : IDENTIFIER assign_expr_op math_expr"
        p[0] = make_node(
            "assignment",
            value={"name": p[1], "op": p[2]},
            children=[p[3]],
            lineno=p.lineno(1),
        )

    def p_for_step_empty(self, p):
        "for_step : empty"
        p[0] = make_node("empty")

    def p_print_stmt(self, p):
        "print_stmt : PRINTF LPAREN print_args RPAREN SEMICOLON"
        p[0] = make_node("print_stmt", children=p[3], lineno=p.lineno(1))

    def p_print_args_text(self, p):
        "print_args : TEXT_STRING"
        p[0] = [make_node("literal", value=p[1], lineno=p.lineno(1))]

    def p_print_args_text_ids(self, p):
        "print_args : TEXT_STRING COMMA id_list"
        p[0] = [make_node("literal", value=p[1], lineno=p.lineno(1))] + p[3]

    def p_scan_stmt(self, p):
        "scan_stmt : SCANF LPAREN TEXT_STRING COMMA AMPERSAND IDENTIFIER RPAREN SEMICOLON"
        p[0] = make_node(
            "scan_stmt",
            children=[
                make_node("literal", value=p[3], lineno=p.lineno(3)),
                make_node("identifier", value=p[6], lineno=p.lineno(6)),
            ],
            lineno=p.lineno(1),
        )

    def p_id_list_recursive(self, p):
        "id_list : id_list COMMA IDENTIFIER"
        p[0] = p[1] + [make_node("identifier", value=p[3], lineno=p.lineno(3))]

    def p_id_list_single(self, p):
        "id_list : IDENTIFIER"
        p[0] = [make_node("identifier", value=p[1], lineno=p.lineno(1))]

    def p_unary_stmt_prefix(self, p):
        "unary_stmt : inc_dec_op IDENTIFIER SEMICOLON"
        p[0] = make_node("unary_stmt", value={"name": p[2], "op": p[1], "pos": "prefix"}, lineno=p.lineno(2))

    def p_unary_stmt_suffix(self, p):
        "unary_stmt : IDENTIFIER inc_dec_op SEMICOLON"
        p[0] = make_node("unary_stmt", value={"name": p[1], "op": p[2], "pos": "suffix"}, lineno=p.lineno(1))

    def p_inc_dec_op(self, p):
        """inc_dec_op : INC
                      | DEC"""
        p[0] = p[1]

    def p_assign_expr_op(self, p):
        """assign_expr_op : ASSIGN
                          | ADD_ASSIGN
                          | SUB_ASSIGN
                          | DIV_ASSIGN"""
        p[0] = p[1]

    def p_math_expr_binop(self, p):
        """math_expr : math_expr PLUS math_expr
                     | math_expr MINUS math_expr
                     | math_expr TIMES math_expr
                     | math_expr DIVIDE math_expr
                     | math_expr MOD math_expr"""
        p[0] = make_node("binary_op", value=p[2], children=[p[1], p[3]], lineno=p.lineno(2))

    def p_math_expr_id(self, p):
        "math_expr : IDENTIFIER"
        p[0] = make_node("identifier", value=p[1], lineno=p.lineno(1))

    def p_math_expr_func_call(self, p):
        "math_expr : IDENTIFIER LPAREN arg_list RPAREN"
        p[0] = make_node("func_call", value=p[1], children=p[3], lineno=p.lineno(1))
        
    def p_arg_list(self, p):
        """arg_list : arg_list_nonempty
                    | empty"""
        p[0] = p[1] if p[1] else []

    def p_arg_list_nonempty_recursive(self, p):
        "arg_list_nonempty : arg_list_nonempty COMMA math_expr"
        p[0] = p[1] + [p[3]]

    def p_arg_list_nonempty_single(self, p):
        "arg_list_nonempty : math_expr"
        p[0] = [p[1]]

    def p_math_expr_num(self, p):
        "math_expr : VALUE_NUM"
        p[0] = make_node("constant", value=p[1], lineno=p.lineno(1))

    def p_math_expr_char(self, p):
        "math_expr : VALUE_CHAR"
        p[0] = make_node("constant_char", value=p[1], lineno=p.lineno(1))

    def p_math_expr_group(self, p):
        "math_expr : LPAREN math_expr RPAREN"
        p[0] = p[2]

    def p_cond_or(self, p):
        "cond : cond OR cond"
        p[0] = make_node("binary_op", value="||", children=[p[1], p[3]], lineno=p.lineno(2))

    def p_cond_and(self, p):
        "cond : cond AND cond"
        p[0] = make_node("binary_op", value="&&", children=[p[1], p[3]], lineno=p.lineno(2))

    def p_cond_rel(self, p):
        "cond : math_expr rel_op math_expr"
        p[0] = make_node("binary_op", value=p[2], children=[p[1], p[3]], lineno=p.lineno(2))

    def p_cond_not(self, p):
        "cond : NOT cond"
        p[0] = make_node("unary_op", value="!", children=[p[2]], lineno=p.lineno(1))

    def p_cond_group(self, p):
        "cond : LPAREN cond RPAREN"
        p[0] = p[2]

    def p_cond_math_expr(self, p):
        "cond : math_expr"
        p[0] = p[1]

    def p_cond_char_literal(self, p):
        "cond : VALUE_CHAR"
        p[0] = make_node("literal", value=p[1], lineno=p.lineno(1))

    def p_rel_op(self, p):
        """rel_op : EQ
                  | NE
                  | LT
                  | GT
                  | LE
                  | GE"""
        p[0] = p[1]

    
    # Rule for epsilon (empty) productions
    def p_empty(self, p):
        "empty :"
        p[0] = None

    # Error rule for syntax errors (obligatory for PLY to handle syntax errors gracefully)
    def p_error(self, p):
        if p:
            # List the syntax error with token value, type and line number
            self.syntax_errors.append(
                f"Syntax error near '{p.value}' (token {getattr(p, 'type', 'UNKNOWN')}) at line {getattr(p, 'lineno', 0)}"
            )
        else:
            self.syntax_errors.append("Syntax error at end of input")
