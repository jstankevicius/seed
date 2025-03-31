# Allowed operations:
# arithmetic, logical comparisons
# foreach loops
# function calls, obviously (actions)
# dictionary element access (accessing the state of the game)
# should be able to randomly generate an element to access (should be
# a primitive like an int, not another dictionary. so if nested and we
# pick an element that happens to be a dict, just keep picking them
# until we get an int)
# can the entire state of the game really be represented with ints?
# floats are probably good too
# before feeding the agent some info we probably need to "help" it along
# by doing some transformations.
# Some games require the agent to always make a valid move. What do we do
# if the agent ends up with no-op logic?
# pprint(ast.dump(ast.parse(CODE)))
# print(ast.unparse(ast.parse(CODE)))

# let's do something small and simple first. We have a dictionary (state),
# some operations, and some functions available to us. Can we generate a
# valid (i.e. parseable) piece of code for it at random?

# Maybe we pick from a set of grammatical rules and then
# fill in that rule? E.g. we pick "if <expr> then <statements>".
# We'd need <expr>, so we generate one, and <statements>, so we
# generate some.


# game api methods should be helpful and should answer very specific questions. For
# example, instead of returning a system's coordinates, the API could tell the agent if
# this system is reachable given their current technological capabilities. If it's
# reachable, how long would it take to get there? We shouldn't rely on the agent to
# create complex logical expressions.
# I guess the principles of good API design apply here. If this were a game, this would
# be (I imagine) like making mods very easy to make.
class System:
    _coordinates: tuple[int, int]

    def __init__(self, x: int, y: int):
        self._coordinates = (x, y)


class Galaxy:

    _systems: list[System]

    def __init__(self):
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
        return None


# Some variables need to be available to the "compiler" at the top
# level. Just the variable representing the game state would be fine.

# Simple case:
# Take all methods of G that do not require any arguments at all. Pick one at random. If
# it returns a value of any non-None type, assign the return value to a variable and add
# that variable to the current environment.
G = Galaxy()

# statements:
# if <expr>:
# method calls:
#   type None are statements
#   non-None are used in expressions
#   when creating method call, check method's type signature. For a type T, check all
#   available methods that return T and pick one at random.

import random
import inspect
from typing import Type
from copy import deepcopy


class Scope:

    _vars: dict[str, Type]

    def __init__(self):
        self._vars = {}

    def add_var(self, var_name: str, var_type: Type) -> None:
        if var_name in self._vars:
            raise RuntimeError(
                f"{var_name} has already been defined in this scope;"
                f" its type is {self._vars[var_name].__name__}!"
            )

        self._vars[var_name] = var_type

    def get_calls_with_predicate(self, predicate):
        res = []

        for var_name, var_type in self._vars.items():
            methods = [
                (var_name, method_name, method)
                for method_name, method in inspect.getmembers(
                    var_type, inspect.isfunction
                )
                if not (method_name.startswith("__") and method_name.endswith("__"))
                and predicate(method)
            ]

            res.extend(methods)

        return res

    def get_call_expressions(self, expr_type=None):
        return self.get_calls_with_predicate(
            predicate=lambda method: (
                inspect.signature(method).return_annotation == expr_type
                if expr_type
                else inspect.signature(method).return_annotation != None
            )
        )

    def get_call_statements(self):
        return self.get_calls_with_predicate(
            predicate=lambda method: inspect.signature(method).return_annotation == None
        )


class CodeGenerator:

    # scope stack
    # each scope maps a variable name to its type
    scopes: list[Scope]

    def __init__(self):
        self.scopes = []

        # Set up global scope
        self.enter_scope()
        self.add_var_to_current_scope("G", Galaxy)
        self.add_var_to_current_scope("G", Galaxy)

    def enter_scope(self) -> None:
        if not self.scopes:
            self.scopes.append(Scope())
        else:
            self.scopes.append(deepcopy(self.scopes[-1]))

    def add_var_to_current_scope(self, var_name: str, var_type: Type) -> None:
        self.scopes[-1].add_var(var_name, var_type)

    def gen_expression_with_type(self, ty: Type):
        print("type:", ty)
        # Look in the current semantic environment and find objects and those objects'
        # methods that return `ty`.
        # Those methods take either 0 or more than 0 arguments.
        # If the number of arguments is 0, return `obj.method()`.
        # If the number of arguments is > 0, generate subexpressions whose types
        # correspond to each of the parameters of the method.
        pass

    def gen_method(self):
        """Look at available simulation objects in the current semantic environment and
        attempt to generate a random valid method call."""

        # Choose random object
        # TODO: Better heuristics
        # TODO: We actually can't do that, because we're assuming that any object has
        # at least one method of the appropriate type. We should have a map of object +
        # method with a type annotation and pick a method from there.
        obj_name = random.choice(list(self._env.keys()))
        obj_type = self._env[obj_name]

        cur_scope = self.scopes[-1]

        # Choose a "registered" method from that object
        name, method = self.pick_method(obj_type)

        # Populate that method's arguments with expressions whose return types match its
        # signature
        signature = inspect.signature(method)
        for name, param in signature.parameters.items():
            if name == "self":
                continue

            self.gen_expression_with_type(param.annotation)

        print(method)

    def gen_method_statement(self):
        # Generate a method call that does not return any value
        print(self.scopes[-1].get_call_expressions())
        print(self.scopes[-1].get_call_statements())
        pass

    def gen_method_expression(self):
        # Generate a method call whose value is then immediately used
        pass

    def gen_statement(self):
        possible_statements = [self.gen_method_statement]
        random.choice(possible_statements)()

    def gen_code(self):
        for _ in range(1):
            self.gen_statement()


cg = CodeGenerator()
cg.gen_code()
