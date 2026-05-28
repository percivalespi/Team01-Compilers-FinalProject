section .data
    fmt_print_0 db "Hello World", 10, "", 0
    fmt_print_1 db "Result: %lld", 10, "", 0

section .text
global main
extern printf
extern scanf
extern exit

sumar:
    push rbp
    mov rbp, rsp
    sub rsp, 512
    mov qword [rbp - 8], rdi
    mov qword [rbp - 16], rsi
    mov rax, qword [rbp - 8]
    mov rbx, qword [rbp - 16]
    add rax, rbx
    mov qword [rbp - 24], rax
    mov rax, qword [rbp - 24]
    jmp end_sumar
end_sumar:
    mov rsp, rbp
    pop rbp
    ret

saludar:
    push rbp
    mov rbp, rsp
    sub rsp, 512
    lea rdi, [rel fmt_print_0]
    mov al, 0
    call printf
    jmp end_saludar
end_saludar:
    mov rsp, rbp
    pop rbp
    ret

main:
    push rbp
    mov rbp, rsp
    sub rsp, 512
    mov rax, 5
    mov qword [rbp - 8], rax
    mov rax, 10
    mov qword [rbp - 16], rax
    mov rdi, qword [rbp - 8]
    mov rsi, qword [rbp - 16]
    call sumar
    mov qword [rbp - 24], rax
    mov rax, qword [rbp - 24]
    mov qword [rbp - 32], rax
    call saludar
    mov qword [rbp - 40], rax
    lea rdi, [rel fmt_print_1]
    mov rsi, qword [rbp - 32]
    mov al, 0
    call printf
    mov rax, 0
    jmp end_main
end_main:
    mov rsp, rbp
    pop rbp
    ret
