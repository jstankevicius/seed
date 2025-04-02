import inspect
from typing import Type

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

    def get_terminals(self, term_type=None):
        if term_type is None:
            return [(var, ty) for var, ty in self._vars.items()]
        else:
            return [(var, ty) for var, ty in self._vars.items() if ty == term_type]
