int main() {
    int x;
    printf("Ingrese un numero: ");
    scanf("%d", &x);
    if (x == 0) {
        x = 1;
    }
    printf("Tu numero es: %d \n", x);
    return 0;
}