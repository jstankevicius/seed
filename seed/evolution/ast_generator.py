# TODO:
# * support more statment types
#   -> for loops (requires properly dealing with lists)
# * generating integer constants where ints are needed
# * cross-over/mutation for ASTs
# * a simple game to use as a benchmark and a corresponding fitness function

# perf:
# * parallelization -- run simulation on multiple processes
# * research how to generate less stupid code
#   -> part of this will be accomplished by using parsimony pressure
import ast
import inspect
import random

from copy import deepcopy
from pprint import pprint
from typing import Type

from scope import Scope


class System:
    _coordinates: tuple[int, int]

    def __init__(self, x: int, y: int):
        self._coordinates = (x, y)

    def is_friendly(self) -> bool:
        return True


class Galaxy:

    _systems: list[System]

    def __init__(self):
        self._id = random.randint(1, 100)
        self._systems = []

    def other_systems(self) -> list[System]:
        return self._systems

    def my_system(self) -> System:
        return System(0, 0)

    def is_reachable(self, system: System) -> bool:
        return True

    def num_ships(self) -> int:
        return 100

    def num_resources(self) -> int:
        return 200

    def asdf(self) -> None:
        print("hello from asdf()!", self._id)
        return None


class ASTGenerator:

    # scope stack
    # each scope maps a variable name to its type
    scopes: list[Scope]

    def __init__(self):
        self.scopes = []

        # Set up global scope
        self.enter_scope()
        self.add_var_to_current_scope("G", Galaxy)

    def enter_scope(self) -> None:
        if not self.scopes:
            self.scopes.append(Scope())
        else:
            self.scopes.append(deepcopy(self.cur_scope()))

    def exit_scope(self) -> None:
        self.scopes.pop()

    def cur_scope(self) -> Scope:
        return self.scopes[-1]

    def add_var_to_current_scope(self, var_name: str, var_type: Type) -> None:
        self.cur_scope().add_var(var_name, var_type)

    def gen_method_call(self, var_name, method_name, method):
        method_arg_types = [
            arg_type.annotation
            for arg_type in inspect.signature(method).parameters.values()
        ]
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id=var_name, ctx=ast.Load()),
                attr=method_name,
                ctx=ast.Load(),
            ),
            args=[
                self.gen_expression_with_type(arg_type)
                for arg_type in method_arg_types
                if arg_type != inspect._empty  # don't generate if no parameters
            ],
            keywords=[],
        )

    def gen_expression_with_type(self, ty: Type):
        call_exprs = self.cur_scope().get_call_expressions(ty)
        terminals = self.cur_scope().get_terminals(ty)

        if not call_exprs and not terminals:
            raise RuntimeError(f"No valid expressions of type {ty.__name__} exist!")

        # Pick either a function or a terminal. If terminal, return immediately.
        # XXX: Adjust this. Terminals should become overwhelmingly likely the deeper
        # the tree is.
        terminal_probability = 0.5 + (1 - 0.5) * (len(self.scopes) / 4)
        if random.random() < terminal_probability and terminals:
            term_name, _ = random.choice(terminals)
            return ast.Name(id=term_name, ctx=ast.Load())
        else:
            # If function, for each of its arguments call gen_expression_with_type
            var_name, method_name, method = random.choice(call_exprs)
            return self.gen_method_call(var_name, method_name, method)

    def gen_method_statement(self):
        # Generate a method call that does not return any value
        method_stmts = self.cur_scope().get_call_statements()

        var_name, method_name, method = random.choice(method_stmts)
        return self.gen_method_call(var_name, method_name, method)

    def gen_if(self):
        self.enter_scope()
        if_stmt = ast.If(
            test=self.gen_expression_with_type(bool),
            body=[self.gen_statement()],
            orelse=[self.gen_statement()],
        )
        self.exit_scope()

        return if_stmt

    def gen_variable_assignment(self):
        lhs = f"v{random.randint(1000, 9999)}"

        # Generate an expression to assign to this variable
        # TODO: Better heuristics
        var_name, method_name, method = random.choice(
            self.cur_scope().get_call_expressions()
        )
        self.add_var_to_current_scope(lhs, inspect.signature(method).return_annotation)
        return ast.Assign(
            targets=[ast.Name(id=lhs)],
            value=self.gen_method_call(var_name, method_name, method),
        )

    def gen_statement(self):
        non_complex_stmts = [self.gen_method_statement, self.gen_variable_assignment]

        complex_stmts = [
            self.gen_if,
        ]

        non_complex_prob = 0.5 + (1 - 0.5) * (len(self.scopes) / 4)
        stmt_func = random.choice(
            non_complex_stmts if random.random() < non_complex_prob else complex_stmts
        )
        return stmt_func()

    def gen_statements(self):
        return [self.gen_statement() for _ in range(random.randint(1, 3))]

    def gen_code(self):
        module_node = ast.Module(body=self.gen_statements(), type_ignores=[])
        ast.fix_missing_locations(module_node)
        return module_node
