"""
AST generator/mutator for a minimal subset of Python.

Rules:
    * Strong, static typing. All methods must have correct type annotations.
    * For now, union types are not supported.
    * All expressions take the form of <var>.<method>(<args>).
    * All expressions must have a non-None return value. This means that
      standalone method calls like

      ```
      if thing.is_valid():
          thing.do_thing()
      ```

      are not possible. Instead, one would write (or generate) something like
      this:

      ```
      if thing.is_valid():
          result = thing.do_thing()
      ```

    * All loops are nested at most once. So a loop can be nested inside another
      loop, but the innermost loop can only contain "simple" statements.
    * Lists are not indexable by integer. They can only be looped over with a
      foreach loop.
"""

import ast
import inspect
import random

from copy import deepcopy
from dataclasses import dataclass
from typing import Type


class Bar:
    def __init__(self):
        pass

    def bar_method(self) -> bool:
        return True

class Foo:

    def __init__(self):
        pass

    def returns_int(self) -> int:
        return 1

    def returns_bool(self) -> bool:
        return True

    def returns_list_of_ints(self) -> list[int]:
        return [1, 2]

    def returns_list_of_bools(self) -> list[bool]:
        return [True]

    def complicated(self, b: bool, i: int) -> int:
        return 2

    def takes_list_of_ints(self, l: list[int]) -> bool:
        return True

    def returns_list_of_bars(self) -> list[Bar]:
        return [Bar()]


# DANGER: If we have a method that takes type X, but we have
# no terminals that can actually satisfy X, we enter an infinite recursive
# loop. Specifically in the case of variable assignment, because we will pick
# any expression without checking whether we can satisfy it.
# Suppose we decide to create a variable assignment statement.
# We call get_call_expressions() with type None, and it returns all possible
# X.Y() pairs, where X is some variable and Y is a method defined for type(X).
# If we pick, say, an expression with type `int` that takes `float`, we will
# then try to generate another expression whose type is `float`. The only
# available expression (if we have no terminals) is that same method. So you
# get:
# X.Y(<float>)
# X.Y(X.Y(<float>))
# X.Y(X.Y(X.Y(<float>)))
# and so on.
# One solution to this is to always have a terminal available for every type.
# A better solution is to figure out preemptively if we can actually satisfy
# the parameters of such an expression. I think we could do this by just
# checking if we have terminals with the proper type available. However, if
# there were no terminals available, we'd have to back out. So it's probably
# better to just have terminals available all the time.
def __make_dummy_func(name, params, return_annotation):
    parameters = [
        inspect.Parameter(
            pname, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=ptype
        )
        for pname, ptype in params
    ]

    sig = inspect.Signature(parameters, return_annotation=return_annotation)

    # Dummy function (does nothing but carries signature)
    def dummy(*args, **kwargs):
        pass

    dummy.__name__ = name
    dummy.__signature__ = sig

    return (name, dummy)


__DUNDER_METHOD_SIGNATURE_OVERRIDES = {
    int: [
        __make_dummy_func("__add__", [("a", int)], int),
        __make_dummy_func("__add__", [("a", float)], float),
    ],
    float: [],
}

__ALLOWED_DUNDER_METHODS_BY_TYPE = {}
for ty, methods in __DUNDER_METHOD_SIGNATURE_OVERRIDES.items():
    for name, _ in methods:
        __ALLOWED_DUNDER_METHODS_BY_TYPE.setdefault(ty, set()).add(name)


def _get_methods(ty):
    if ty not in __DUNDER_METHOD_SIGNATURE_OVERRIDES:
        return inspect.getmembers(ty, inspect.isfunction)

    return __DUNDER_METHOD_SIGNATURE_OVERRIDES[ty]


def is_allowed_method(var_type, method_name: str) -> bool:
    is_dunder_method = method_name.startswith("__") and method_name.endswith("__")
    is_allowed_dunder_method = (
        method_name in __ALLOWED_DUNDER_METHODS_BY_TYPE.setdefault(var_type, set())
    )
    return not is_dunder_method or is_allowed_dunder_method


class Scope:

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
        predicate = predicate or (lambda x: True)

        for var_name, var_type in self._vars.items():
            methods = [
                (var_name, method_name, method)
                for method_name, method in _get_methods(var_type)
                if is_allowed_method(var_type, method_name) and predicate(method)
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

    def get_terminals(self, term_type=None):
        if term_type is None:
            return [(var, ty) for var, ty in self._vars.items()]
        else:
            return [(var, ty) for var, ty in self._vars.items() if ty == term_type]


def get_container_inner_type(container_type):
    # Check if `list_type` is actually parametrized
    if not hasattr(container_type, "__origin__"):
        raise AttributeError(f"{container_type} is not a parametrized type!")

    args = getattr(container_type, "__args__", None)
    if not args:
        raise AttributeError(f"{container_type} does not have any argument types!")
    elif len(args) > 1:
        raise AttributeError(f"{container_type} is parametrized by more than one type!")

    return args[0]


MAX_SCOPES = 4
MAX_EXPR_DEPTH = 3

PROB_IF_STMT_CONTAINS_ELSE = 0.5
PROB_BOOL_EXPR_GETS_BOOL_OP = 0.2
PROB_OP_BOOL_EXPR_USES_NOT = 0.5


@dataclass
class NodeInfo:
    # NOTE: This cannot just be a reference to the Scope object that existed when this
    # node was created, because the Scope object might contain references to variables
    # that were defined after this node.
    scope: Scope
    expr_type: type


class ASTGenerator:

    def __init__(self):
        self.node_metadata = {}
        self.scopes = []
        self.expr_depth = 0
        self.var_idx = 0

        # Set up global scope
        self.enter_scope()
        self.add_var_to_current_scope("foo", Foo)

    def enter_scope(self) -> None:
        if not self.scopes:
            self.scopes.append(Scope())
        else:
            self.scopes.append(deepcopy(self.cur_scope()))

    def exit_scope(self) -> None:
        self.scopes.pop()

    def cur_scope(self) -> Scope:
        return self.scopes[-1]

    def get_var_name(self) -> str:
        name = f"v{self.var_idx}"
        self.var_idx += 1
        return name

    def add_var_to_current_scope(self, var_name: str, var_type: Type) -> None:
        # TODO: Maybe we should allow for actual values? Type is implicit.
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
        self.expr_depth += 1

        call_exprs = self.cur_scope().get_call_expressions(ty)
        terminals = self.cur_scope().get_terminals(ty)

        # If no options are available, fall back to gen_constant_with_type, which will
        # just pick a constant with type `ty` at random.
        if (not call_exprs and not terminals) or (self.expr_depth > MAX_EXPR_DEPTH):
            return self.gen_constant_with_type(ty)

        # Terminals have a 50% chance of being picked in the outermost scope, with
        # probability linearly increasing to 100% at maximum scope depth. If the
        # expression is already too nested, set the probability of a terminal to 100%.
        terminal_probability = (1 - 0.5) / MAX_SCOPES * len(self.scopes) + 0.5
        if self.expr_depth >= MAX_EXPR_DEPTH:
            terminal_probability = 1.0

        # Pick either a terminal or a call expression. Depending on terminal
        # availability, return either a constant or an actual terminal (i.e. a varname).
        # If method, then populate the method's arguments appropriately.
        if random.random() < terminal_probability and terminals:
            term_name, _ = random.choice(terminals)
            ret_node = ast.Name(id=term_name, ctx=ast.Load())
        elif call_exprs:
            var_name, method_name, method = random.choice(call_exprs)
            ret_node = self.gen_method_call(var_name, method_name, method)
        else:
            ret_node = self.gen_constant_with_type(ty)

        # Special case for bools, since and/or/not are not methods but control flow
        # operators handled directly in the interpreter. Bool expressions have a fixed
        # probability of being modified by some boolean operator.
        if (
            ty == bool
            and random.random() < PROB_BOOL_EXPR_GETS_BOOL_OP
            and self.expr_depth < MAX_EXPR_DEPTH
        ):
            bin_ops = [ast.And, ast.Or]

            if random.random() < PROB_OP_BOOL_EXPR_USES_NOT:
                ret_node = ast.UnaryOp(op=ast.Not(), operand=ret_node)
            else:
                ret_node = ast.BoolOp(
                    op=random.choice(bin_ops)(),
                    values=[ret_node, self.gen_expression_with_type(bool)],
                )

        self.expr_depth -= 1

        # Register the node:
        self.node_metadata[ret_node] = NodeInfo(
            scope=deepcopy(self.cur_scope()), expr_type=ty
        )

        return ret_node

    def gen_constant_with_type(self, ty):
        if getattr(ty, "__origin__", None) and ty.__origin__ == list:
            return ast.Constant(value=[])

        types = {
            bool: [True, False],
            float: [1.0],  # or maybe some generator function?
            int: [1, 2],
        }
        return ast.Constant(value=random.choice(types[ty]))

    def gen_if(self):

        if_stmt = ast.If(test=self.gen_expression_with_type(bool))
        self.enter_scope()
        if_stmt.body = [self.gen_statement()]

        if random.random() < PROB_IF_STMT_CONTAINS_ELSE:
            # Leave scope of "then" portion
            self.exit_scope()

            # Enter scope of the "else" portion
            self.enter_scope()
            if_stmt.orelse = [self.gen_statement()]
            self.exit_scope()
        else:
            self.exit_scope()

        return if_stmt

    def gen_variable_assignment(self):
        # NOTE: In the case of variable reassignment, there are certain conditions we
        # must always check. For example, if we are in a loop, the variable representing
        # the structure we are looping over _cannot_ be reassigned.
        lhs = self.get_var_name()

        # Generate an expression to assign to this variable
        # TODO: Better heuristics
        var_name, method_name, method = random.choice(
            self.cur_scope().get_call_expressions()
        )
        node = ast.Assign(
            targets=[ast.Name(id=lhs)],
            value=self.gen_method_call(var_name, method_name, method),
        )
        self.add_var_to_current_scope(lhs, inspect.signature(method).return_annotation)
        return node

    def gen_for_loop(self):
        # Get list of method calls that return some sort of list
        call_exprs = self.cur_scope().get_calls_with_predicate(
            lambda method: getattr(
                inspect.signature(method).return_annotation, "__origin__", None
            )
            == list
        )
        terminals = [
            (var_name, ty)
            for var_name, ty in self.cur_scope().get_terminals()
            if getattr(ty, "__origin__", None) == list
        ]

        # Set of all container types available to the generator at this point
        container_types = [
            inspect.signature(method).return_annotation for _, _, method in call_exprs
        ] + [ty for _, ty in terminals]

        # Choose a type to generate an expression for.
        container_type = random.choice(container_types)
        iterator_type = get_container_inner_type(container_type)

        # Generate an expression matching the container type:
        container_expr = self.gen_expression_with_type(container_type)

        self.enter_scope()
        loop_var = self.get_var_name()
        self.add_var_to_current_scope(loop_var, iterator_type)

        for_loop = ast.For(
            target=ast.Name(id=loop_var, ctx=ast.Store()),
            iter=container_expr,
            body=[self.gen_statement()],
            orelse=[],
        )

        self.exit_scope()
        return for_loop

    def gen_statement(self):
        non_complex_stmts = [self.gen_variable_assignment]

        complex_stmts = [
            self.gen_if,
            self.gen_for_loop,
        ]

        non_complex_prob = 0.5 + (1 - 0.5) * (len(self.scopes) / 4)

        stmt_func = random.choice(
            non_complex_stmts if random.random() < non_complex_prob else complex_stmts
        )
        return stmt_func()

    def gen_statements(self):
        return [self.gen_statement() for _ in range(random.randint(1, 3))]

    def gen_module(self):
        module_node = ast.Module(body=self.gen_statements(), type_ignores=[])
        ast.fix_missing_locations(module_node)
        return module_node


for i in range(10000):
    print(i)
    a = ASTGenerator()
    code = ast.unparse(a.gen_module())
    print(code)
    input()
    try:
        compile(code, "<text>", "exec")
    except Exception as e:
        print("THIS ONE BROKE")
        print(code)
        raise e
