from ast_generator import ASTGenerator
from mutator import Mutator

import ast

a = ASTGenerator()
m = Mutator()

tree = a.gen_code()
print("Before:")
print(ast.unparse(tree))
mutated_tree = m.mutate(tree)
print("\nAfter:")
print(ast.unparse(mutated_tree))