import ast
import random
import copy

class Mutator(ast.NodeTransformer):
    """
    A skeleton AST mutator that traverses an arbitrary AST.
    Mutations are applied based on a given mutation_rate.
    """
    def __init__(self, mutation_rate: float = 0.1) -> None:
        """
        :param mutation_rate: Probability (0.0 to 1.0) that a node will be mutated.
        """
        super().__init__()
        self.mutation_rate = mutation_rate
    
    def generic_visit(self, node: ast.AST) -> ast.AST:
        # Optionally mutate the current node.
        node = self.maybe_mutate(node)
        return super().generic_visit(node)
    
    def maybe_mutate(self, node: ast.AST) -> ast.AST:
        """
        Decide whether to mutate the given node.
        """
        if random.random() < self.mutation_rate:
            return self.mutate_node(node)
        return node
    
    def mutate_node(self, node: ast.AST) -> ast.AST:
        """
        Apply a mutation to the given node.
        This is a placeholder method.
        Override this method with specific mutation logic.
        """
        # Example: if the node is an If statement, you could mutate its test.
        # For now, return the node unmodified.
        return node
    
    def mutate(self, tree: ast.AST) -> ast.AST:
        """
        Creates a deep copy of the tree, applies mutations, and returns the mutated AST.
        """
        tree_copy = copy.deepcopy(tree)
        return self.visit(tree_copy)