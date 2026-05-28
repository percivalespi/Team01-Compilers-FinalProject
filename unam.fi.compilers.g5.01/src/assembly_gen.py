import os
from typing import List, Tuple, Any

# Generates x86-64 assembly code from Three-Address Code (TAC) tuples
class AssemblyGenerator:
    def __init__(self):
        self.data_section = []
        self.text_section = []
        self.strings = {}
        self.str_counter = 0

        self.var_offsets = {}
        self.current_offset = 0
        self.current_func = ""  # Track current function name for unique labels

        # Registers for passing parameters in System V AMD64 ABI
        self.param_regs = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]

    def _get_string_label(self, text: str) -> str:
        for label, val in self.strings.items():
            if val == text:
                return label
        label = f"fmt_{self.str_counter}"
        self.str_counter += 1
        self.strings[label] = text
        return label

    def _get_offset(self, var_name: str) -> int:
        if var_name not in self.var_offsets:
            # QWORD = 8 bytes, 
            self.current_offset += 8 
            self.var_offsets[var_name] = self.current_offset
        return self.var_offsets[var_name]

    def _is_int(self, val: Any) -> bool:
        try:
            int(val)
            return True
        except (ValueError, TypeError):
            return False

    def _load(self, reg: str, val: Any) -> str:
        # Load value into register
        if self._is_int(val):
            return f"    mov {reg}, {val}"
        else:
            offset = self._get_offset(str(val))
            return f"    mov {reg}, qword [rbp - {offset}]"

    def _store(self, val: Any, reg: str) -> str:
        # Store a register value in a memory variable
        offset = self._get_offset(str(val))
        return f"    mov qword [rbp - {offset}], {reg}"

    def generate(self, tac_code: List[Tuple[str, Any, Any, Any]]) -> str:
        self.text_section = []
        self.data_section = []
        self.call_args = []

        self.print_args = []
        self.scan_args = []
        self.current_print_fmt = ""
        self.current_scan_fmt = ""

        for op, arg1, arg2, res in tac_code:

            if op == "FUNC_BEGIN":
                self.current_offset = 0
                self.var_offsets = {}
                self.current_func = arg1  # Track function name for unique .end label
                self.text_section.append(f"{arg1}:")
                self.text_section.append("    push rbp")
                self.text_section.append("    mov rbp, rsp")
                # Allocate 512 bytes for local variables
                # Stack 16-byte aligned for calls (printf)
                self.text_section.append("    sub rsp, 512")

            elif op == "FUNC_END":
                self.text_section.append(f"end_{arg1}:")
                self.text_section.append("    mov rsp, rbp")
                self.text_section.append("    pop rbp")
                self.text_section.append("    ret\n")

            elif op == "=":
                self.text_section.append(self._load("rax", arg1))
                self.text_section.append(self._store(res, "rax"))

            elif op in ("+", "-", "*"):
                self.text_section.append(self._load("rax", arg1))
                self.text_section.append(self._load("rbx", arg2))
                if op == "+": self.text_section.append("    add rax, rbx")
                if op == "-": self.text_section.append("    sub rax, rbx")
                if op == "*": self.text_section.append("    imul rax, rbx")
                self.text_section.append(self._store(res, "rax"))

            elif op in ("/", "%"):
                self.text_section.append(self._load("rax", arg1))
                self.text_section.append(self._load("rbx", arg2))
                self.text_section.append("    cqo") 
                self.text_section.append("    idiv rbx")
                if op == "/":
                    self.text_section.append(self._store(res, "rax")) 
                else:
                    self.text_section.append(self._store(res, "rdx")) 

            elif op in ("==", "!=", "<", "<=", ">", ">="):
                self.text_section.append(self._load("rax", arg1))
                self.text_section.append(self._load("rbx", arg2))
                self.text_section.append("    cmp rax, rbx")
                
                if op == "==": self.text_section.append("    sete al")
                if op == "!=": self.text_section.append("    setne al")
                if op == "<":  self.text_section.append("    setl al")
                if op == "<=": self.text_section.append("    setle al")
                if op == ">":  self.text_section.append("    setg al")
                if op == ">=": self.text_section.append("    setge al")
                
                # Clean the register RAX
                self.text_section.append("    movzx rax, al") 
                self.text_section.append(self._store(res, "rax"))

            elif op == "LABEL":
                self.text_section.append(f"{arg1}:")

            elif op == "GOTO":
                self.text_section.append(f"    jmp {arg1}")

            elif op == "IF_FALSE":
                self.text_section.append(self._load("rax", arg1))
                self.text_section.append("    cmp rax, 0")
                self.text_section.append(f"    je {res}")

            elif op == "RETURN":
                if arg1 is not None:
                    self.text_section.append(self._load("rax", arg1))
                # Jump to function epilogue (unique label per function)
                self.text_section.append(f"    jmp end_{self.current_func}")

            elif op == "RECV_PARAM":
                var_name = arg1 # Name of the variable
                param_index = arg2 # Index of the parameter
                if param_index < len(self.param_regs):
                    reg = self.param_regs[param_index] # Obtiene rdi, rsi, etc.
                    self.text_section.append(self._store(var_name, reg))

            elif op == "PARAM":
                self.call_args.append(arg1)

            elif op == "CALL":
                # Load args into registers according to System V AMD64 ABI
                for i, p_arg in enumerate(self.call_args):
                    if i < len(self.param_regs):
                        reg = self.param_regs[i]
                        self.text_section.append(self._load(reg, p_arg))
                
                # Clear the call arguments for future calls
                self.call_args = []
                
                # 3. Call the function
                self.text_section.append(f"    call {arg1}")
                
                # 4. Capture the return value if needed
                if res is not None:
                    self.text_section.append(self._store(res, "rax"))

            elif op == "PRINT_FMT":
                # Generate the label directly and inject it into the data section
                fmt_label = f"fmt_print_{len(self.data_section)}"
                
                nasm_str = arg1.replace('\\n', '", 10, "')

                nasm_str = nasm_str.replace('%d', '%lld')
                
                self.data_section.append(f'{fmt_label} db {nasm_str}, 0')
                self.current_print_fmt = fmt_label
                self.print_args = []

            elif op == "PRINT_ARG":
                self.print_args.append(arg1)

            elif op == "CALL_PRINT":
                if not self.current_print_fmt:
                    raise RuntimeError("Error")
                    
                # Load the format string label created in PRINT_FMT
                self.text_section.append(f"    lea rdi, [rel {self.current_print_fmt}]")
                
                # Load arguments into registers according to System V AMD64 ABI
                for i, p_arg in enumerate(self.print_args):
                    if i + 1 < len(self.param_regs):
                        reg = self.param_regs[i + 1]
                        self.text_section.append(self._load(reg, p_arg))
                        
                self.text_section.append("    mov al, 0") 
                self.text_section.append("    call printf")
                
                # Clear state variables after calling
                self.print_args = []
                self.current_print_fmt = ""

            elif op == "SCAN_FMT":
                fmt_label = f"fmt_scan_{len(self.data_section)}"
                
                nasm_str = arg1.replace('\\n', '", 10, "')

                nasm_str = nasm_str.replace('%d', '%lld')
                
                self.data_section.append(f'{fmt_label} db {nasm_str}, 0')
                self.current_scan_fmt = fmt_label
                self.scan_args = []

            elif op == "SCAN_ARG":
                self.scan_args.append(arg1)

            elif op == "CALL_SCAN":
                # Validate that a format string exists
                if not self.current_scan_fmt:
                    raise RuntimeError("Error.")

                # Load the format string label created in SCAN_FMT
                self.text_section.append(f"    lea rdi, [rel {self.current_scan_fmt}]")
                expected_args = len(self.scan_args)
                
                for i, s_arg in enumerate(self.scan_args):
                    if i + 1 < len(self.param_regs):
                        reg = self.param_regs[i + 1] 
                        var_offset = self._get_offset(s_arg)
                        self.text_section.append(f"    lea {reg}, [rbp - {var_offset}]")
                
                # Clear AL and OS call
                self.text_section.append("    mov al, 0")
                self.text_section.append("    call scanf")
                
                # Runtime check: scanf should return the number of items successfully read in RAX.
                # If RAX != expected_args, it means the user inputted text instead of a number.
                lbl_ok = f"scanf_ok_{len(self.text_section)}"
                self.text_section.append(f"    cmp rax, {expected_args}")
                self.text_section.append(f"    je {lbl_ok}")
                
                # Handling error: Setup string and exit.
                # Use a general error string if not defined yet.
                err_label = "err_scanf_msg"
                if not any(err_label in d for d in self.data_section):
                    self.data_section.append(f'{err_label} db "Runtime Error: Invalid input format. Expected an integer.", 10, 0')
                
                self.text_section.append(f"    lea rdi, [rel {err_label}]")
                self.text_section.append("    mov al, 0")
                self.text_section.append("    call printf")
                self.text_section.append("    mov edi, 1")  # exit code 1
                self.text_section.append("    call exit")
                self.text_section.append(f"{lbl_ok}:")
                
                # Clear state variables after calling
                self.scan_args = []
                self.current_scan_fmt = ""

        return self._build_file()

    def _build_file(self) -> str:
        lines = []
        lines.append("section .data")

        # Add any static data to the data section
        if self.data_section:
            for data_line in self.data_section:
                lines.append(f"    {data_line}")
        else:
            lines.append("    ; No static data")

        # Section code
        lines.append("")
        lines.append("section .text")
        lines.append("global main")
        lines.append("extern printf")
        lines.append("extern scanf")
        lines.append("extern exit")
        lines.append("")

        for text_line in self.text_section:
            lines.append(text_line)
            
        # Join all lines into a single string with newlines
        return "\n".join(lines)