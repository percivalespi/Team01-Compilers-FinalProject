int sumar(int a, int b) {
    if (b == 0) {
        return a;
    } 
    return sumar(a + 1, b - 1);
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
