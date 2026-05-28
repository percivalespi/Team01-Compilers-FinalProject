import copy
from typing import Optional, List, Dict, Any
from ..Parser_SDT.ast_nodes import ASTNode, make_node

class ASTOptimzer:
    def __init__(self):
        self.optimizations_applied = 0

    def optimize(self, node: Optional[ASTNode]) -> Optional[ASTNode]:
        if not node:
            return node

        # Recursively optimize child nodes first (bottom-up)
        optimized_children = []
        for child in node.children:
            opt_child = self.optimize(child)
            # Avoid adding None children if optimization
            if opt_child is not None:
                optimized_children.append(opt_child)
        node.children = optimized_children
        result_node = node
        if node.kind == "binary_op":
            result_node = self._optimize_binary_op(node)
        elif node.kind == "for":
            result_node = self._optimize_for_loop(node)

        # If the optimization returned None, it means the original node should be kept
        return result_node if result_node is not None else node
    
    def _optimize_binary_op(self, node: ASTNode) -> ASTNode:
        left = node.children[0]
        right = node.children[1]
        op = node.value

        # -------------------------- Optimization: Constant folding --------------------------
        if left.kind == "constant" and right.kind == "constant":
            try:
                # Convert to float if it has a decimal point, otherwise keep as int
                l_val = float(left.value) if '.' in str(left.value) else int(left.value)
                r_val = float(right.value) if '.' in str(right.value) else int(right.value)
                
                result = None
                if op == '+': result = l_val + r_val
                elif op == '-': result = l_val - r_val
                elif op == '*': result = l_val * r_val
                elif op == '/': result = l_val / r_val if r_val != 0 else None
                elif op == '%': result = l_val % r_val if r_val != 0 else None

                if result is not None:
                    self.optimizations_applied += 1
                    # Keep as int if the result without decimals
                    if isinstance(result, float) and result.is_integer():
                        result = int(result)
                    # Return a new constant node that replaces the subtree
                    return make_node("constant", value=result, lineno=node.lineno)
            except Exception:
                # In case of any error just return the original node
                pass
        
        # -------------------------- Optimization: Algebraic simplification --------------------------
        if op == '+':
            # Simplify: 0 + x -> x
            if left.kind == "constant" and float(left.value) == 0:
                self.optimizations_applied += 1
                return right  
            # Simplify: x + 0 -> x
            if right.kind == "constant" and float(right.value) == 0:
                self.optimizations_applied += 1
                return left   
        elif op == '*':
            # Simplify: 1 * x -> x
            if left.kind == "constant" and float(left.value) == 1:
                self.optimizations_applied += 1
                return right
            # Simplify: x * 1 -> x
            if right.kind == "constant" and float(right.value) == 1:
                self.optimizations_applied += 1
                return left 
            # Simplify: x * 0 -> 0
            if (left.kind == "constant" and float(left.value) == 0) or (right.kind == "constant" and float(right.value) == 0):
                self.optimizations_applied += 1
                return make_node("constant", value=0, lineno=node.lineno)

    def _optimize_for_loop(self, node: ASTNode) -> ASTNode:
        # -------------------------- Optimization: Loop unrolling (FOR) --------------------------

        # Structure of for loop node -> [init, condition, step, block]
        if len(node.children) != 4:
            return node  
        
        init, cond, step, body = node.children

        try:
            # Validate Init
            if init.kind not in ("declaration", "assignment") or not init.children:
                return node
            if init.children[0].kind != "constant":
                return node
            
            var_name = init.value["name"]
            start_val = int(init.children[0].value)

            # Validate Condition
            if cond.kind != "binary_op" or cond.value not in ('<', '<=', '>', '>='):
                return node
            if cond.children[0].kind != "identifier" or cond.children[0].value != var_name:
                return node
            if cond.children[1].kind != "constant":
                return node
            
            limit_val = int(cond.children[1].value)
            rel_op = cond.value

            # Validate Step
            if step.kind != "unary_stmt" or step.value.get("name") != var_name:
                return node
            
            step_op = step.value.get("op")
            if step_op not in ('++', '--'):
                return node

            # Unroll the loop by simulating its execution at compile time
            current_val = start_val
            unrolled_statements = []
            max_unroll = 200 # Limit to prevent infinite loops
            iterations = 0

            while True:
                # Check the loop condition
                if rel_op == '<' and not (current_val < limit_val): break
                if rel_op == '<=' and not (current_val <= limit_val): break
                if rel_op == '>' and not (current_val > limit_val): break
                if rel_op == '>=' and not (current_val >= limit_val): break

                # Prevent infinite unrolling
                if iterations >= max_unroll:
                    return node 

                # Replace occurrences of the loop variable in the body with the current value
                body_copy = copy.deepcopy(body.children)
                unrolled_statements.extend(body_copy)

                # Execute the step
                if step_op == '++': current_val += 1
                if step_op == '--': current_val -= 1
                iterations += 1

            self.optimizations_applied += 1
            
            # Replace the original for loop with the unrolled statements
            return make_node("block", children=unrolled_statements, lineno=node.lineno)
        except Exception:
            # If any part of the loop is not analyzable, return the original node
            return node