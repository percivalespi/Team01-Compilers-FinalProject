"""
Unparser module: Converts the optimized AST back to readable C source code.

Formats the AST nodes into C code syntax, handling indentation and structure. 
"""

from typing import Optional
from ..Parser_SDT.ast_nodes import ASTNode

class CUnparser:
    def __init__(self):
        self.indent_level = 0

    def unparse(self, node: Optional[ASTNode]) -> str:
        if not node:
            return ""
        
        # Call the appropriate method based on the node kind
        method_name = f"_unparse_{node.kind}"
        unparse_method = getattr(self, method_name, self._unparse_default)
        return unparse_method(node)

    # Formarting variables, statements, expressions, etc. into C code

    def _indent(self) -> str:
        return "    " * self.indent_level

    def _unparse_default(self, node: ASTNode) -> str:
        return f"/* Nodo no soportado: {node.kind} */"

    def _unparse_program(self, node: ASTNode) -> str:
        return "\n\n".join(self.unparse(child) for child in node.children)

    def _unparse_function(self, node: ASTNode) -> str:
        func_type = node.value["type"]
        func_name = node.value["name"]
        params = self.unparse(node.children[0])
        body = self.unparse(node.children[1])
        return f"{func_type} {func_name}({params}) {body}"

    def _unparse_param_list(self, node: ASTNode) -> str:
        return ", ".join(self.unparse(child) for child in node.children)

    def _unparse_param(self, node: ASTNode) -> str:
        return f"{node.value['type']} {node.value['name']}"

    def _unparse_block(self, node: ASTNode) -> str:
        self.indent_level += 1
        stmts = "\n".join(f"{self._indent()}{self.unparse(child)}" for child in node.children)
        self.indent_level -= 1
        if stmts:
            return f"{{\n{stmts}\n{self._indent()}}}"
        return "{ }"

    def _unparse_declaration(self, node: ASTNode) -> str:
        decl = f"{node.value['type']} {node.value['name']}"
        if node.children:
            decl += f" = {self.unparse(node.children[0])}"
        return f"{decl};"

    def _unparse_assignment(self, node: ASTNode) -> str:
        name = node.value["name"]
        op = node.value.get("op", "=")
        val = self.unparse(node.children[0])
        return f"{name} {op} {val};"

    def _unparse_return(self, node: ASTNode) -> str:
        if node.children:
            return f"return {self.unparse(node.children[0])};"
        return "return;"

    def _unparse_if(self, node: ASTNode) -> str:
        cond = self.unparse(node.children[0])
        body = self.unparse(node.children[1])
        return f"if ({cond}) {body}"

    def _unparse_while(self, node: ASTNode) -> str:
        cond = self.unparse(node.children[0])
        body = self.unparse(node.children[1])
        return f"while ({cond}) {body}"

    def _unparse_for(self, node: ASTNode) -> str:
        init = self.unparse(node.children[0]).replace(";", "")
        cond = self.unparse(node.children[1])
        step = self.unparse(node.children[2]).replace(";", "")
        body = self.unparse(node.children[3])
        return f"for ({init}; {cond}; {step}) {body}"

    def _unparse_print_stmt(self, node: ASTNode) -> str:
        args = ", ".join(self.unparse(child) for child in node.children)
        return f"printf({args});"

    def _unparse_scan_stmt(self, node: ASTNode) -> str:
        fmt = self.unparse(node.children[0])
        var = self.unparse(node.children[1])
        return f"scanf({fmt}, &{var});"

    def _unparse_func_call(self, node: ASTNode) -> str:
        args = ", ".join(self.unparse(child) for child in node.children)
        call = f"{node.value}({args})"
        return call

    def _unparse_unary_stmt(self, node: ASTNode) -> str:
        name = node.value["name"]
        op = node.value["op"]
        pos = node.value.get("pos", "suffix")
        stmt = f"{op}{name}" if pos == "prefix" else f"{name}{op}"
        return f"{stmt};"

    def _unparse_binary_op(self, node: ASTNode) -> str:
        left = self.unparse(node.children[0])
        right = self.unparse(node.children[1])
        return f"({left} {node.value} {right})"

    def _unparse_unary_op(self, node: ASTNode) -> str:
        return f"({node.value}{self.unparse(node.children[0])})"

    def _unparse_identifier(self, node: ASTNode) -> str:
        return str(node.value)

    def _unparse_constant(self, node: ASTNode) -> str:
        return str(node.value)

    def _unparse_literal(self, node: ASTNode) -> str:
        return str(node.value)

    def _unparse_empty(self, node: ASTNode) -> str:
        return ""