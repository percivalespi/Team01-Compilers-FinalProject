from pygments import lex
from pygments.lexers.c_cpp import CLexer
from pygments.token import Token

# Mapping lexemes according to token classificactions
def classify_token(token, value):
    # Special Cases

    # Pygments does not classify '&' as an special token
    if value == '&':
        return 'SPECIAL'
    
    # Pygments does not classify this symbols as punctuation
    if value in ['(', ')', '{', '}', ',', ';']:
        return 'PUNCTUATION'

    # Clasification based on Pygments token types
    if token in Token.Keyword:
        return 'KEYWORD'
    elif token in Token.Name:
        return 'IDENTIFIER'
    elif token in Token.Literal.Number:
        return 'CONSTANT'
    elif (token in Token.Literal.String) or (token in Token.Literal):
        return 'LITERAL'
    elif token in Token.Operator:
        return 'OPERATOR'
    elif token in Token.Punctuation:
        return 'PUNCTUATION'
    
    return 'IGNORE'

def tokenize_code(code):
    c_lexer = CLexer()
    tokens_list = []

    # Temporal Buffer for literals 
    # Note: Pygments can split a string literal into multiple tokens
    literal_tmp = ""
    
    for token_type, value in lex(code, c_lexer):
        category = classify_token(token_type, value)

        # If we detect a fragment of a literal, it is save in the buffer
        if category == 'LITERAL':
            literal_tmp += value
            continue

        # Save literal fragments as a single literal token
        if literal_tmp:
            tokens_list.append(('LITERAL', literal_tmp))
            literal_tmp = ""

        # Ignore whitespaces
        if token_type in Token.Text and not value.strip():
            continue
            
        if category != 'IGNORE':
            tokens_list.append((category, value))
    
    # If the source code ends exactly with a string literal, empty the buffer one last time.
    if literal_tmp:
        tokens_list.append(('LITERAL', literal_tmp))

    return tokens_list
