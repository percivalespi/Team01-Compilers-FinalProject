from colorama import init, Fore, Style
from pygments import lex
from pygments.lexers.c_cpp import CLexer

try:
    from src.Lexer.lexer import classify_token
except ImportError:
    from src.Lexer.lexer import classify_token

init(autoreset=True)

CATEGORY_COLORS = {
    'KEYWORD': Fore.CYAN,
    'IDENTIFIER': Fore.GREEN,
    'PUNCTUATION': Fore.YELLOW,
    'OPERATOR': Fore.MAGENTA,
    'CONSTANT': Fore.RED,
    'LITERAL': Fore.BLUE,
    'SPECIAL': Fore.RESET,
}


def group_tokens(tokens):
    grouped = {
        'KEYWORD': {},
        'IDENTIFIER': {},
        'PUNCTUATION': {},
        'OPERATOR': {},
        'CONSTANT': {},
        'LITERAL': {},
        'SPECIAL': {},
    }

    for category, value in tokens:
        if category in grouped:
            if value in grouped[category]:
                grouped[category][value] += 1
            else:
                grouped[category][value] = 1
        else:
            grouped[category] = {value: 1}

    return grouped


def print_grouped_tokens(tokens):
    if not tokens:
        print(Fore.RED + "No tokens to display.")
        return

    grouped_tokens = group_tokens(tokens)

    print("\n GROUPED TOKENS BY TYPE:\n")

    for category, token_counts in grouped_tokens.items():
        if token_counts:
            total_in_category = sum(token_counts.values())
            color = CATEGORY_COLORS.get(category, Fore.WHITE)

            print(f"{color}{Style.BRIGHT}{category} (Total = {total_in_category}):{Style.RESET_ALL}")

            for token, count in token_counts.items():
                print(f"\t{Style.BRIGHT}{token}{Style.RESET_ALL}: {count} times")

    print()
    print(f"{Style.BRIGHT} Total all tokens: {len(tokens)}{Style.RESET_ALL}\n")


def print_tokens_table(tokens: list):
    if not tokens:
        print(Fore.RED + "No tokens to display.")
        return

    print("\n" + "=" * 50)
    print(Style.BRIGHT + f"{'TOKEN TYPE':<15} | {'LEXEMS'}" + Style.RESET_ALL)
    print("=" * 50)

    for token_type, value in tokens:
        clean_value = value.replace('\n', '\\n').replace('\r', '\\r')
        color = CATEGORY_COLORS.get(token_type, Fore.WHITE)

        spaces = " " * (15 - len(token_type))
        print(f"{color}{token_type}{Style.RESET_ALL}{spaces} | {Style.BRIGHT}{clean_value}{Style.RESET_ALL}")

    print("=" * 50)
    print(Style.BRIGHT + f"Total tokens found: {len(tokens)}\n" + Style.RESET_ALL)


def print_color_legend():
    print(Style.BRIGHT + "Color Legend:" + Style.RESET_ALL)

    legend_items = []
    for category, color in CATEGORY_COLORS.items():
        item = f"{color}{Style.BRIGHT}[ {category} ]{Style.RESET_ALL}"
        legend_items.append(item)

    print("  " + "  ".join(legend_items))
    print("-" * 100)


def print_colored_code(source_code: str):
    print(Style.BRIGHT + "\n=== Source Code with the tokens highlighted ===\n" + Style.RESET_ALL)
    print_color_legend()

    c_lexer = CLexer()

    for token_type, value in lex(source_code, c_lexer):
        category = classify_token(token_type, value)

        if category in CATEGORY_COLORS:
            color = CATEGORY_COLORS[category]
            print(f"{color}{value}{Style.RESET_ALL}", end="")
        else:
            print(value, end="")

    print("\n" + "=" * 40)
