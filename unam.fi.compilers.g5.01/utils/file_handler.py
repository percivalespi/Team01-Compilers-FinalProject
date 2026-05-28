import os
import json

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read(), None
    except FileNotFoundError:
        return "", f"The file '{file_path}' was not found"
    except Exception as e:
        return "", str(e)


def export_tokens(tokens, output_path, grouped_tokens, analysis_result=None):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Syntax & Semantic Analyzer - Report\n")
            f.write("=" * 50 + "\n\n")

            f.write("Lexical Analysis - Results\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total tokens found: {len(tokens)}\n\n\n")
            f.write(f"{'TOKEN TYPE':<20} | {'LEXEMS'}\n")
            f.write("-" * 50 + "\n")

            for token_type, value in tokens:
                clean_value = value.replace('\n', '\\n').replace('\r', '\\r')
                f.write(f"{token_type:<20} | {clean_value}\n")

            f.write("=" * 50 + "\n")

            f.write("GROUPED TOKENS BY TYPE\n")
            f.write("=" * 50 + "\n")

            for category, token_counts in grouped_tokens.items():
                if token_counts:
                    total_in_category = sum(token_counts.values())
                    f.write(f"{category} (Total: {total_in_category}):\n")

                    for token, count in token_counts.items():
                        f.write(f"    {token}: {count}\n")

                    f.write("\n")

            f.write(f"Total tokens found: {len(tokens)}\n\n\n")

            f.write("Syntax & Semantic Analysis - Results\n")
            f.write("=" * 50 + "\n")

            if analysis_result is None:
                f.write("Syntax analysis: NOT EXECUTED\n")
                f.write("Semantic analysis (SDT): NOT EXECUTED\n")
            else:
                syntax_ok = analysis_result.get("syntax_ok", False)
                semantic_ok = analysis_result.get("semantic_ok", False)

                f.write(f"Syntax analysis: {'VALID' if syntax_ok else 'INVALID'}\n")
                f.write(f"Semantic analysis (SDT): {'VALID' if semantic_ok else 'INVALID'}\n")

                syntax_errors = analysis_result.get("syntax_errors", [])
                semantic_errors = analysis_result.get("semantic_errors", [])

                if syntax_errors:
                    f.write("\nSyntax Errors:\n")
                    for err in syntax_errors:
                        f.write(f"  - {err}\n")

                if semantic_errors:
                    f.write("\nSemantic Errors:\n")
                    for err in semantic_errors:
                        f.write(f"  - {err}\n")

            f.write("\n" + "=" * 50 + "\n")
            return None

    except Exception as e:
        return str(e)


def export_ast_json(ast_dict, output_path):
    """Exports the AST dictionary to a formatted JSON file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ast_dict, f, indent=4, ensure_ascii=False)
        
        return None  # No error
    except Exception as e:
        return str(e)