int sumar(int a, int b) {
    return a + b;
}

void saludar() {
    printf("Hello World\n");
    return;
}

int main() {
    int x = 5;
    int y = 10;
    int resultado = sumar(x, y);
    saludar();
    printf("Result: %d\n", resultado);
    return 0;
}