from typing import Optional, List, Tuple, Any
from .Parser_SDT.ast_nodes import ASTNode

class TACGenerator:
    def __init__(self):
        self.code: List[Tuple[str, Any, Any, Any]] = []
        self.temp_counter = 0
        self.label_counter = 0

    def _new_temp(self) -> str:
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def _new_label(self) -> str:
        l = f"L{self.label_counter}"
        self.label_counter += 1
        return l

    def _emit(self, op: str, arg1: Any = None, arg2: Any = None, result: Any = None):
        self.code.append((op, arg1, arg2, result))

    def generate(self, node: Optional[ASTNode]) -> List[Tuple[str, Any, Any, Any]]:
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0
        self._walk(node)
        return self.code

    def _walk(self, node: Optional[ASTNode]) -> Any:
        if not node:
            return None

        # Dinamic dispatcher
        method_name = f"_gen_{node.kind}"
        gen_method = getattr(self, method_name, self._gen_default)
        return gen_method(node)

    def _gen_default(self, node: ASTNode) -> None:
        # Next node if no specific generator is defined for this kind of node
        for child in node.children:
            self._walk(child)

    def _gen_program(self, node: ASTNode) -> None:
        for child in node.children:
            self._walk(child)

    def _gen_function(self, node: ASTNode) -> None:
        func_name = node.value["name"]
        self._emit("FUNC_BEGIN", func_name)
        
        param_list = node.children[0]
        if param_list and param_list.children:
            for i, param_node in enumerate(param_list.children):
                p_name = param_node.value["name"]
                # Emit instruction to receive parameter into a register or stack location
                self._emit("RECV_PARAM", p_name, i)
                
        self._walk(node.children[1])
        self._emit("FUNC_END", func_name)

    def _gen_block(self, node: ASTNode) -> None:
        for child in node.children:
            self._walk(child)

    def _gen_declaration(self, node: ASTNode) -> None:
        var_name = node.value["name"]
        if node.children:
            val = self._walk(node.children[0])
            self._emit("=", val, None, var_name)

    def _gen_assignment(self, node: ASTNode) -> None:
        var_name = node.value["name"]
        val = self._walk(node.children[0])
        op = node.value.get("op", "=")
        
        if op == "=":
            self._emit("=", val, None, var_name)
        else:
            # Handle compound operators (+=, -=)
            base_op = op[0] # 
            temp = self._new_temp()
            self._emit(base_op, var_name, val, temp)
            self._emit("=", temp, None, var_name)

    def _gen_binary_op(self, node: ASTNode) -> str:
        left = self._walk(node.children[0])
        right = self._walk(node.children[1])
        temp = self._new_temp()
        
        # Map logical operators 
        op = node.value
        self._emit(op, left, right, temp)
        return temp

    def _gen_unary_op(self, node: ASTNode) -> str:
        inner = self._walk(node.children[0])
        temp = self._new_temp()
        if node.value == "-":
            self._emit("UMINUS", inner, None, temp)
        elif node.value == "!":
            self._emit("NOT", inner, None, temp)
        return temp

    def _gen_unary_stmt(self, node: ASTNode) -> None:
        var_name = node.value["name"]
        op = node.value["op"] # "++" o "--"
        base_op = "+" if op == "++" else "-"
        temp = self._new_temp()
        self._emit(base_op, var_name, 1, temp)
        self._emit("=", temp, None, var_name)

    def _gen_constant(self, node: ASTNode) -> Any:
        return node.value

    def _gen_literal(self, node: ASTNode) -> Any:
        return node.value

    def _gen_identifier(self, node: ASTNode) -> str:
        return node.value

    def _gen_if(self, node: ASTNode) -> None:
        cond = self._walk(node.children[0])
        label_end = self._new_label()
        
        self._emit("IF_FALSE", cond, None, label_end)
        self._walk(node.children[1]) # If body
        self._emit("LABEL", label_end)

    def _gen_while(self, node: ASTNode) -> None:
        label_start = self._new_label()
        label_end = self._new_label()
        
        self._emit("LABEL", label_start)
        cond = self._walk(node.children[0])
        self._emit("IF_FALSE", cond, None, label_end)
        
        self._walk(node.children[1]) # While body
        self._emit("GOTO", label_start)
        self._emit("LABEL", label_end)

    def _gen_for(self, node: ASTNode) -> None:
        label_start = self._new_label()
        label_end = self._new_label()

        self._walk(node.children[0]) # Init
        self._emit("LABEL", label_start)
        
        if node.children[1] and node.children[1].kind != "empty":
            cond = self._walk(node.children[1])
            self._emit("IF_FALSE", cond, None, label_end)

        self._walk(node.children[3]) # Body
        
        if node.children[2] and node.children[2].kind != "empty":
            self._walk(node.children[2]) # Step
            
        self._emit("GOTO", label_start)
        self._emit("LABEL", label_end)

    def _gen_return(self, node: ASTNode) -> None:
        if node.children:
            val = self._walk(node.children[0])
            self._emit("RETURN", val)
        else:
            self._emit("RETURN")

    def _gen_func_call(self, node: ASTNode) -> str:
        func_name = node.value

        if func_name == "printf":
            self._gen_print_stmt(node)
            return self._new_temp() #
            
        if func_name == "scanf":
            self._gen_scan_stmt(node)
            return self._new_temp()

        args = []
        for child in node.children:
            args.append(self._walk(child))
            
        for arg in args:
            self._emit("PARAM", arg)
            
        temp = self._new_temp()
        self._emit("CALL", func_name, len(args), temp)
        return temp

    def _gen_print_stmt(self, node: ASTNode) -> None:
        # Basic format for printing
        fmt = self._walk(node.children[0])
        self._emit("PRINT_FMT", fmt)
        for child in node.children[1:]:
            val = self._walk(child)
            self._emit("PRINT_ARG", val)
        self._emit("CALL_PRINT")

    def _gen_scan_stmt(self, node: ASTNode) -> None:
        # Basic format for scanning input
        fmt = self._walk(node.children[0]) 
        self._emit("SCAN_FMT", fmt)
        
        # Strip '&' if it's a reference to a variable
        var_name = self._walk(node.children[1])
        if isinstance(var_name, str) and var_name.startswith("&"):
            var_name = var_name[1:]
            
        self._emit("SCAN_ARG", var_name)
        self._emit("CALL_SCAN")

    def format_tac(self) -> str:
        # Format the TAC code into a human-readable string representation
        lines = []
        for op, a1, a2, res in self.code:
            a1_str = str(a1) if a1 is not None else ""
            a2_str = str(a2) if a2 is not None else ""
            res_str = str(res) if res is not None else ""

            if op == "LABEL":
                lines.append(f"{a1_str}:")
            elif op == "FUNC_BEGIN":
                lines.append(f"\n{a1_str}:")
                lines.append(f"  BeginFunc")
            elif op == "RECV_PARAM":
                lines.append(f"  RecvParam {a1_str} from Reg[{a2_str}]")
            elif op == "FUNC_END":
                lines.append(f"  EndFunc")
            elif op == "IF_FALSE":
                lines.append(f"  IfFalse {a1_str} Goto {res_str}")
            elif op == "GOTO":
                lines.append(f"  Goto {a1_str}")
            elif op == "RETURN":
                lines.append(f"  Return {a1_str}".strip())
            elif op == "PARAM":
                lines.append(f"  Param {a1_str}")
            elif op == "CALL":
                lines.append(f"  {res_str} = Call {a1_str}, {a2_str}")
            elif op == "=":
                lines.append(f"  {res_str} = {a1_str}")
            elif op in ("PRINT_FMT", "PRINT_ARG", "CALL_PRINT", "SCAN_FMT", "SCAN_ARG", "CALL_SCAN"):
                lines.append(f"  {op} {a1_str}".strip())
            else:
                # Aritmethic or logical operations
                if a2 is not None:
                    lines.append(f"  {res_str} = {a1_str} {op} {a2_str}")
                else:
                    lines.append(f"  {res_str} = {op} {a1_str}")
        return "\n".join(lines)