# Semantic analysis module for the compiler
from typing import Any, Dict, List, Optional

from .ast_nodes import ASTNode

# SymbolTable class to manage variable declarations and scopes
class SymbolTable:
    def __init__(self) -> None:
        self.scopes: List[Dict[str, Any]] = [{}]
        self.history: List[Dict[str, Any]] = []

    # Create a new scope by pushing a new dictionary onto the stack
    def enter_scope(self) -> None:
        self.scopes.append({})
    # Exit the current scope by popping the top dictionary from the stack
    def exit_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()

    # Declare a variable in the current scope. Returns False if redeclaration occurs.
    def declare(self, name: str, var_type: Any) -> bool:
        current = self.scopes[-1]
        if name in current:
            return False
        current[name] = var_type

        scope_level = len(self.scopes) - 1
        scope_label = "Global" if scope_level == 0 else f"Local"

        self.history.append({
            "identifier": name,
            "type": str(var_type) if not isinstance(var_type, dict) else var_type,
            "scope": scope_label,
        })

        return True
    
    # Get the type of a variable by looking it up through the scopes from innermost to outermost.
    def lookup(self, name: str) -> Optional[Any]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # Get a merged snapshot of all scopes for reporting purposes
    def snapshot(self) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for scope in self.scopes:
            merged.update(scope)
        return merged
    
    # Export the full declaration history
    def get_history(self) -> List[Dict[str, Any]]:
        return self.history


# Semantic Rules Implementation

def _infer_literal_type(value: str) -> str:
    value = value.strip()
    if value.startswith("'") and value.endswith("'"):
        return "char"
    if value.startswith('"') and value.endswith('"'):
        return "string"
    return "string"


def _infer_constant_type(value: str) -> str:
    return "float" if "." in str(value) else "int"


def _is_numeric(t: str) -> bool:
    return t in {"int", "float", "double", "char"}


def _is_logical_evaluable(t: str) -> bool:
    return t in {"bool", "int", "float", "double", "char"}


def _compatible_assign(target: str, source: str) -> bool:
    if target == source:
        return True
    if target == "double" and source in {"float", "int", "char"}:
        return True
    if target == "float" and source in {"int", "char"}:
        return True
    if target == "int" and source == "char":
        return True
    return False


def _extract_format_specifiers(raw_literal: str) -> List[str]:
    text = raw_literal.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]

    specs: List[str] = []
    i = 0
    while i < len(text):
        if text[i] == "%":
            if i + 1 < len(text) and text[i + 1] == "%":
                i += 2
                continue
            if i + 1 < len(text):
                spec = text[i + 1]
                if spec in {"d", "i", "f", "c", "s"}:
                    specs.append(spec)
                i += 2
                continue
        i += 1
    return specs


def _format_compatible(var_type: str, spec: str) -> bool:
    if spec in {"d", "i"}:
        return var_type == "int"
    if spec == "f":
        return var_type in {"float", "double"}
    if spec == "c":
        return var_type == "char"
    if spec == "s":
        return var_type == "string"
    return False

# Function to perform semantic analysis on the AST
def analyze_semantics(ast: ASTNode):
    table = SymbolTable()
    errors: List[str] = []
    trace: List[Dict[str, Any]] = []
    step = 0

    # Trace function to log semantic analysis steps with node information and symbol table state
    def add_trace(action: str, node: Optional[ASTNode], status: str = "INFO", detail: str = "") -> None:
        nonlocal step
        step += 1
        trace.append(
            {
                "step": step,
                "action": action,
                "node": node.kind if node else "None",
                "line": node.lineno if node else 0,
                "status": status,
                "detail": detail,
                "symbols": table.snapshot(),
            }
        )

    # Apply semantic rules recursively to the AST nodes.
    def expr_type(node: ASTNode) -> str:
        if node.kind == "identifier":
            found = table.lookup(node.value)
            if not found:
                errors.append(f"Semantic error: variable '{node.value}' not declared at line {node.lineno}")
                add_trace("expr_type", node, "ERROR", f"Identifier '{node.value}' not declared")
                return "error"
            if isinstance(found, dict) and found.get("type") == "function":
                errors.append(f"Semantic error: function '{node.value}' used as a variable at line {node.lineno}")
                add_trace("expr_type", node, "ERROR", f"Function '{node.value}' used as variable")
                return "error"
            add_trace("expr_type", node, "OK", f"Identifier '{node.value}' resolved as '{found}'")
            return found

        if node.kind == "func_call":
            found = table.lookup(node.value)
            if not found:
                errors.append(f"Semantic error: function '{node.value}' not declared at line {node.lineno}")
                add_trace("expr_type", node, "ERROR", f"Function '{node.value}' not declared")
                return "error"
            if not isinstance(found, dict) or found.get("type") != "function":
                errors.append(f"Semantic error: '{node.value}' is not a function at line {node.lineno}")
                add_trace("expr_type", node, "ERROR", f"'{node.value}' is not a function")
                return "error"
            
            expected_args = found["params"]
            if len(node.children) != len(expected_args):
                errors.append(f"Semantic error: function '{node.value}' expects {len(expected_args)} args, got {len(node.children)} at line {node.lineno}")
                add_trace("expr_type", node, "ERROR", "Argument count mismatch")
                return "error"

            for i, arg_node in enumerate(node.children):
                arg_t = expr_type(arg_node)
                if arg_t != "error" and not _compatible_assign(expected_args[i], arg_t):
                    errors.append(f"Semantic error: argument {i+1} of '{node.value}' expected {expected_args[i]}, got {arg_t} at line {node.lineno}")
                    add_trace("expr_type", node, "ERROR", f"Argument {i+1} type mismatch")
            
            add_trace("expr_type", node, "OK", f"Function call '{node.value}' resolves to '{found['return']}'")
            return found["return"]

        if node.kind == "constant":
            inferred = _infer_constant_type(str(node.value))
            add_trace("expr_type", node, "OK", f"Constant inferred as '{inferred}'")
            return inferred

        if node.kind == "literal":
            inferred = _infer_literal_type(str(node.value))
            add_trace("expr_type", node, "OK", f"Literal inferred as '{inferred}'")
            return inferred

        if node.kind == "unary_op":
            inner = expr_type(node.children[0])
            if node.value == "-":
                if not _is_numeric(inner):
                    errors.append(f"Semantic error: unary '-' requires numeric operand at line {node.lineno}")
                    add_trace("expr_type", node, "ERROR", "Unary '-' with non-numeric operand")
                    return "error"
                add_trace("expr_type", node, "OK", f"Unary '-' result type '{inner}'")
                return inner
            if node.value == "!":
                if not _is_logical_evaluable(inner):
                    errors.append(f"Semantic error: unary '!' invalid operand at line {node.lineno}")
                    add_trace("expr_type", node, "ERROR", "Unary '!' with invalid operand")
                    return "error"
                add_trace("expr_type", node, "OK", "Unary '!' result type 'bool'")
                return "bool"

        if node.kind == "binary_op":
            left_t = expr_type(node.children[0])
            right_t = expr_type(node.children[1])
            op = node.value

            if op in {"+", "-", "*", "/", "%"}:
                if not (_is_numeric(left_t) and _is_numeric(right_t)):
                    errors.append(f"Semantic error: arithmetic op '{op}' expects numeric types at line {node.lineno}")
                    add_trace("expr_type", node, "ERROR", f"Arithmetic op '{op}' with invalid operand types")
                    return "error"
                if "float" in {left_t, right_t}:
                    add_trace("expr_type", node, "OK", f"Arithmetic op '{op}' inferred as 'float'")
                    return "float"
                add_trace("expr_type", node, "OK", f"Arithmetic op '{op}' inferred as 'int'")
                return "int"

            if op in {"<", "<=", ">", ">="}:
                if not (_is_numeric(left_t) and _is_numeric(right_t)):
                    errors.append(f"Semantic error: relational op '{op}' expects numeric types at line {node.lineno}")
                    add_trace("expr_type", node, "ERROR", f"Relational op '{op}' with invalid operand types")
                    return "error"
                add_trace("expr_type", node, "OK", f"Relational op '{op}' inferred as 'bool'")
                return "bool"

            if op in {"==", "!="}:
                if left_t == right_t:
                    add_trace("expr_type", node, "OK", f"Equality op '{op}' inferred as 'bool'")
                    return "bool"
                if _is_numeric(left_t) and _is_numeric(right_t):
                    add_trace("expr_type", node, "OK", f"Equality op '{op}' inferred as 'bool' for numeric operands")
                    return "bool"
                errors.append(f"Semantic error: equality op '{op}' has incompatible types at line {node.lineno}")
                add_trace("expr_type", node, "ERROR", f"Equality op '{op}' with incompatible types")
                return "error"

            if op in {"&&", "||"}:
                valid_left = _is_logical_evaluable(left_t)
                valid_right = _is_logical_evaluable(right_t)
                if not (valid_left and valid_right):
                    errors.append(f"Semantic error: logical op '{op}' has invalid operands at line {node.lineno}")
                    add_trace("expr_type", node, "ERROR", f"Logical op '{op}' with invalid operand types")
                    return "error"
                add_trace("expr_type", node, "OK", f"Logical op '{op}' inferred as 'bool'")
                return "bool"

        add_trace("expr_type", node, "WARN", "Type inference returned 'error'")
        return "error"

    current_function_return_type = None

    # Auxiliary function to check if a "return" node exists in a branch of the AST
    def has_return(n: Optional[ASTNode]) -> bool:
        if not n:
            return False
        if n.kind == "return":
            return True
        for child in n.children:
            if has_return(child):
                return True
        return False

    # Recursive function to walk the AST and apply semantic rules, while logging the process in the trace.
    def walk(node: Optional[ASTNode]) -> None:
        nonlocal current_function_return_type
        if node is None:
            return

        add_trace("visit", node, "INFO", "Visiting node")

        if node.kind == "program":
            for child in node.children:
                walk(child)
            return

        if node.kind == "function":
            func_name = node.value["name"]
            ret_type = str(node.value["type"]).lower()
            
            param_list_node = node.children[0]
            params = []
            for param_node in param_list_node.children:
                params.append(str(param_node.value["type"]).lower())
                
            func_info = {"type": "function", "return": ret_type, "params": params}
            if not table.declare(func_name, func_info):
                errors.append(f"Semantic error: function '{func_name}' already declared at line {node.lineno}")
                table.scopes[-1][func_name] = func_info
                add_trace("declare", node, "ERROR", f"Redeclaration of function '{func_name}'")
            else:
                add_trace("declare", node, "OK", f"Declared function '{func_name}' returning '{ret_type}'")
            
            table.enter_scope()
            for param_node in param_list_node.children:
                p_name = param_node.value["name"]
                p_type = str(param_node.value["type"]).lower()
                table.declare(p_name, p_type)
                
            prev_ret_type = current_function_return_type
            current_function_return_type = ret_type
            
            # 1. Se evalúa todo el cuerpo de la función
            walk(node.children[1]) # The block
            
            # --- NUEVO CÓDIGO ---
            # 2. Comprobamos si la función no es void y si carece de un nodo return
            if ret_type != "void" and not has_return(node.children[1]):
                errors.append(f"Semantic error: non-void function '{func_name}' is missing a return statement at line {node.lineno}")
                add_trace("visit", node, "ERROR", f"Missing return in non-void function '{func_name}'")
            # --------------------
            
            current_function_return_type = prev_ret_type
            table.exit_scope()
            return

        if node.kind == "return":
            # Handle return statements with respect to the current function's return type
            if current_function_return_type is None:
                errors.append(f"Semantic error: 'return' outside of a function at line {node.lineno}")
                add_trace("visit", node, "ERROR", "Return outside function")
                return

            if node.children:
                ret_t = expr_type(node.children[0])
                # Check for void function returning a value or return type mismatch
                if current_function_return_type == "void":
                    errors.append(f"Semantic error: void function cannot return a value at line {node.lineno}")
                    add_trace("visit", node, "ERROR", "Void function returning value")
                elif ret_t != "error" and not _compatible_assign(current_function_return_type, ret_t):
                    errors.append(f"Semantic error: return type mismatch, expected {current_function_return_type} but got {ret_t} at line {node.lineno}")
                    add_trace("visit", node, "ERROR", "Return type mismatch")
            else:
                if current_function_return_type != "void":
                    errors.append(f"Semantic error: non-void function must return a value at line {node.lineno}")
                    add_trace("visit", node, "ERROR", "Missing return value")
            return
            
        if node.kind == "func_call":
            expr_type(node)
            return

        if node.kind == "empty":
            return

        if node.kind == "block":
            table.enter_scope()
            for child in node.children:
                walk(child)
            table.exit_scope()
            return

        if node.kind == "declaration":
            name = node.value["name"]
            var_type = str(node.value["type"]).lower()

            # Current semantic policy intentionally skips redeclaration checks.
            if not table.declare(name, var_type):
                table.scopes[-1][name] = var_type
                add_trace("declare", node, "INFO", f"Redeclaration for '{name}' ignored")
            else:
                add_trace("declare", node, "OK", f"Declared '{name}' as '{var_type}'")

            if node.children:
                assigned_t = expr_type(node.children[0])
                if assigned_t != "error" and not _compatible_assign(var_type, assigned_t):
                    errors.append(
                        f"Semantic error: cannot assign '{assigned_t}' to '{var_type}' at line {node.lineno}"
                    )
                    add_trace("assign_check", node, "ERROR", f"Cannot assign '{assigned_t}' to '{var_type}'")
                elif assigned_t != "error":
                    add_trace("assign_check", node, "OK", f"Assigned '{assigned_t}' to '{var_type}'")
            return

        if node.kind == "declaration_list":
            for decl in node.children:
                walk(decl)
            return

        if node.kind == "assignment":
            name = node.value["name"]
            assign_op = node.value.get("op", "=")
            target = table.lookup(name)
            if not target:
                errors.append(f"Semantic error: variable '{name}' not declared at line {node.lineno}")
                add_trace("assignment", node, "ERROR", f"Variable '{name}' not declared")
                return
            source_t = expr_type(node.children[0])
            if source_t != "error" and assign_op == "=" and not _compatible_assign(target, source_t):
                errors.append(
                    f"Semantic error: cannot assign '{source_t}' to '{target}' at line {node.lineno}"
                )
                add_trace("assignment", node, "ERROR", f"Cannot assign '{source_t}' to '{target}'")
            elif source_t != "error" and assign_op in {"+=", "-=", "/="}:
                if not (_is_numeric(target) and _is_numeric(source_t)):
                    errors.append(
                        f"Semantic error: '{assign_op}' expects numeric types at line {node.lineno}"
                    )
                    add_trace("assignment", node, "ERROR", f"Operator '{assign_op}' with non-numeric types")
                else:
                    add_trace("assignment", node, "OK", f"Applied '{assign_op}' with numeric operands")
            elif source_t != "error":
                add_trace("assignment", node, "OK", f"Assigned '{source_t}' to '{target}'")
            return

        if node.kind == "scan_stmt":
            fmt_node = node.children[0] if node.children else None
            scan_id = node.children[1].value if len(node.children) > 1 else None
            if scan_id and not table.lookup(scan_id):
                errors.append(f"Semantic error: variable '{scan_id}' not declared at line {node.lineno}")
                add_trace("scan", node, "ERROR", f"Scan target '{scan_id}' not declared")
                return

            scan_type = table.lookup(scan_id) if scan_id else None
            specs = _extract_format_specifiers(str(fmt_node.value)) if fmt_node else []

            if len(specs) != 1:
                errors.append(f"Semantic error: scanf expects exactly one format specifier at line {node.lineno}")
                add_trace("scan", node, "ERROR", "scanf format must contain exactly one specifier")
                return

            if scan_type and not _format_compatible(scan_type, specs[0]):
                errors.append(
                    f"Semantic error: scanf format '%{specs[0]}' incompatible with '{scan_type}' at line {node.lineno}"
                )
                add_trace("scan", node, "ERROR", f"scanf spec '%{specs[0]}' incompatible with '{scan_type}'")
                return

            add_trace("scan", node, "OK", f"Scan target '{scan_id}' with format '%{specs[0]}' is valid")
            return

        if node.kind == "unary_stmt":
            name = node.value.get("name") if isinstance(node.value, dict) else None
            found = table.lookup(name) if name else None
            if not found:
                errors.append(f"Semantic error: variable '{name}' not declared at line {node.lineno}")
                add_trace("unary", node, "ERROR", f"Unary target '{name}' not declared")
                return
            if not _is_numeric(found):
                errors.append(f"Semantic error: unary op requires numeric variable at line {node.lineno}")
                add_trace("unary", node, "ERROR", f"Unary op on non-numeric type '{found}'")
                return
            add_trace("unary", node, "OK", f"Unary operation valid for '{name}'")
            return

        if node.kind == "print_stmt":
            if not node.children:
                errors.append(f"Semantic error: printf missing arguments at line {node.lineno}")
                add_trace("print", node, "ERROR", "printf missing format string")
                return

            fmt_node = node.children[0]
            arg_nodes = node.children[1:]
            specs = _extract_format_specifiers(str(fmt_node.value))

            if len(specs) != len(arg_nodes):
                errors.append(
                    f"Semantic error: printf expected {len(specs)} args but got {len(arg_nodes)} at line {node.lineno}"
                )
                add_trace("print", node, "ERROR", "printf argument count mismatch")
                return

            for spec, arg_node in zip(specs, arg_nodes):
                if arg_node.kind != "identifier":
                    errors.append(f"Semantic error: printf only accepts identifiers in argument list at line {node.lineno}")
                    add_trace("print", node, "ERROR", "printf argument is not an identifier")
                    return

                arg_type = table.lookup(arg_node.value)
                if not arg_type:
                    errors.append(
                        f"Semantic error: variable '{arg_node.value}' not declared at line {arg_node.lineno}"
                    )
                    add_trace("print", node, "ERROR", f"printf argument '{arg_node.value}' not declared")
                    return

                if not _format_compatible(arg_type, spec):
                    errors.append(
                        f"Semantic error: printf format '%{spec}' incompatible with '{arg_type}' at line {node.lineno}"
                    )
                    add_trace("print", node, "ERROR", f"printf spec '%{spec}' incompatible with '{arg_type}'")
                    return

            add_trace("print", node, "OK", "printf arguments validated")
            return

        if node.kind in {"if", "if_else", "while"}:
            cond_t = expr_type(node.children[0])
            if not _is_logical_evaluable(cond_t):
                errors.append(f"Semantic error: invalid condition type at line {node.lineno}")
                add_trace("condition", node, "ERROR", f"Invalid condition type '{cond_t}'")
            else:
                add_trace("condition", node, "OK", f"Condition type '{cond_t}' accepted")
            for child in node.children[1:]:
                walk(child)
            return

        if node.kind == "for":
            table.enter_scope()
            add_trace("scope", node, "INFO", "Enter for-scope")
            init_node, cond_node, update_node, body_node = node.children
            walk(init_node)
            if cond_node and cond_node.kind != "empty":
                cond_t = expr_type(cond_node)
                if not _is_logical_evaluable(cond_t):
                    errors.append(f"Semantic error: invalid for-condition type at line {node.lineno}")
                    add_trace("condition", node, "ERROR", f"Invalid for-condition type '{cond_t}'")
                else:
                    add_trace("condition", node, "OK", f"For-condition type '{cond_t}' accepted")
            if update_node and update_node.kind != "empty":
                walk(update_node)
            walk(body_node)
            table.exit_scope()
            add_trace("scope", node, "INFO", "Exit for-scope")
            return

        if node.kind == "return":
            if node.children:
                ret_t = expr_type(node.children[0])
                add_trace("return", node, "OK" if ret_t != "error" else "ERROR", f"Return expression type '{ret_t}'")
            else:
                add_trace("return", node, "OK", "Return without expression")
            return

        for child in node.children:
            walk(child)

    walk(ast)
    # Return a full history of symbol declarations and semantic analysis steps for reporting purposes.
    return len(errors) == 0, errors, table.get_history(), trace
