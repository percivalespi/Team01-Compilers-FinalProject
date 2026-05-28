# Module that combines the entire parsing and semantic analysis process
from typing import Any, Dict, List

import ply.yacc as yacc

from .Lexer.adapter import PlyLexerAdapter
from .Parser_SDT.grammar import GrammarRules
from .Lexer.lexer import tokenize_code
from .Parser_SDT.semantic import analyze_semantics
from .Optimizer.code_optimizer import ASTOptimzer
from .Optimizer.unparser import CUnparser
from .tac import TACGenerator
try:
    from .assembly_gen import AssemblyGenerator
except ImportError:
    pass # Ignoring if it does not exist

# Heriting from GrammarRules to access production rules and precedence
class ParserSDT(GrammarRules):
    def __init__(self) -> None:
        self.syntax_errors: List[str] = []
        # Create the LALR(1) parser using PLY.YACC with the production rules defined in GrammarRules
        self.parser = yacc.yacc(module=self, start="program", write_tables=False, debug=False)

    def parse(self, source_code: str) -> Dict[str, Any]:
        self.syntax_errors = []
        # Tokenize the source code using the lexer defined in lexer.py
        token_list = tokenize_code(source_code)
        # Create an adapter to convert the list of tokens into the format expected by PLY.YACC 
        adapter = PlyLexerAdapter(token_list, source_code=source_code)
        # Parse the tokens to generate the AST, while collecting syntax errors if any
        ast = self.parser.parse(lexer=adapter)

        result: Dict[str, Any] = {
            "tokens": token_list,
            "syntax_ok": len(self.syntax_errors) == 0 and ast is not None,
            "syntax_errors": self.syntax_errors,
            "ast": ast,
            "ast_dict": ast.to_dict() if ast else None,
            "ast_tree": "\n".join(ast.to_tree_lines()) if ast else "",
            "semantic_ok": False,
            "semantic_errors": [],
            "symbol_table": [],
            "sdt_trace": [],
            "optimized_code": None,
            "optimizations_count": 0,
            "tac_code": None,
            "asm_code": None,
        }

        # If syntax is valid, proceed to semantic analysis using the AST generated.
        if result["syntax_ok"]:
            semantic_ok, semantic_errors, symbol_table, sdt_trace = analyze_semantics(ast)
            result["semantic_ok"] = semantic_ok
            result["semantic_errors"] = semantic_errors
            result["symbol_table"] = symbol_table
            result["sdt_trace"] = sdt_trace

            # If semantics are valid, proceed to code optimization
            if semantic_ok:
                optimizer = ASTOptimzer()
                optimized_ast = optimizer.optimize(result["ast"])

                # Rebuild source code from the optimized AST
                unparser = CUnparser()
                optimized_code = unparser.unparse(optimized_ast)

                result["ast"] = optimized_ast
                result["ast_dict"] = optimized_ast.to_dict()
                result["optimized_code"] = optimized_code
                result["optimizations_count"] = optimizer.optimizations_applied

                # Generate intermediate code (TAC) from the optimized AST
                tac_gen = TACGenerator()
                tac_code_tuples = tac_gen.generate(optimized_ast)
                result["tac_code"] = tac_gen.format_tac()

                # Generate code Assembly from the TAC code
                asm_gen = AssemblyGenerator()
                result["asm_code"] = asm_gen.generate(tac_code_tuples)

            else:
                result["optimized_code"] = None
                result["optimizations_count"] = 0
       
        return result

def parse_source(source_code: str) -> Dict[str, Any]:
    parser = ParserSDT()
    return parser.parse(source_code)
