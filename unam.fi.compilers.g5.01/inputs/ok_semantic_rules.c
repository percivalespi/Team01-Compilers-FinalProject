int main() {
    int x = 1;
    float y = 2;
    char c = 'a';
    x = x + 1;
    y = y + x;
    if (x < y && y > 0) {
        x += 1;
    }
    printf("%d %f %c", x, y, c);
    scanf("%d", &x);
    return 0;
}
