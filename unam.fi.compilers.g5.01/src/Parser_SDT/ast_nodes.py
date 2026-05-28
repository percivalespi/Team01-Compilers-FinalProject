# ASTNode class representing a node in the Abstract Syntax Tree (AST)

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Factory Pattern for creating AST nodes using the make_node function
@dataclass
class ASTNode:
    # Attributes of the ASTNode
    kind: str
    value: Any = None
    children: List["ASTNode"] = field(default_factory=list)
    lineno: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "lineno": self.lineno,
            "children": [child.to_dict() for child in self.children],
        }

    def to_tree_lines(self, level: int = 0) -> List[str]:
        indent = "  " * level
        label = f"{self.kind}"
        if self.value is not None:
            label += f" value={self.value}"
        if self.lineno:
            label += f" line={self.lineno}"

        lines = [f"{indent}- {label}"]
        for child in self.children:
            lines.extend(child.to_tree_lines(level + 1))
        return lines


def make_node(kind: str, value: Any = None, children: Optional[List[ASTNode]] = None, lineno: int = 0) -> ASTNode:
    return ASTNode(kind=kind, value=value, children=children or [], lineno=lineno)
