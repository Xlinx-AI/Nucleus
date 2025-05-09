"""
Validation utilities for tool classes, including attribute and code checks.

"""

import ast
import inspect

class JuniorNodeChecker(ast.NodeVisitor):
    """
    Walks through AST nodes to find all names and checks for forbidden stuff.
    """
    def __init__(self, forbidden_names):
        self.forbidden_names = set(forbidden_names)
        self.found = set()

    def visit_Name(self, node):
        if node.id in self.forbidden_names:
            self.found.add(node.id)
        self.generic_visit(node)

def validate_tool_structure(cls, forbidden=None):
    """
    Validates that a class does not contain forbidden attributes or names.
    """
    forbidden = forbidden or []
    source = None
    try:
        source = inspect.getsource(cls)
    except Exception as e:
        print(f"Could not get source for validation: {e}")
        return False

    tree = ast.parse(source)
    checker = JuniorNodeChecker(forbidden)
    checker.visit(tree)
    if checker.found:
        print(f"Forbidden names found: {checker.found}")
        return False
    return True

# Extended: validate_tool_attributes from core
class MethodChecker(ast.NodeVisitor):
    def __init__(self, class_attributes):
        self.undefined_names = set()
        self.class_attributes = class_attributes
        self.errors = []

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            if not (
                node.id == "self"
                or node.id in self.class_attributes
                or node.id in dir(__builtins__)
            ):
                self.errors.append(f"Name '{node.id}' is undefined.")

def validate_tool_attributes(cls):
    """
    Checks that a Tool class matches the following pattern:
    - Has a docstring
    - Has attributes: name, description, inputs, output_type
    - All input args are in the forward() signature
    - All used names are defined
    """
    errors = []
    doc = inspect.getdoc(cls)
    if not doc:
        errors.append(f"Tool {cls.__name__} missing docstring.")
    for attr in ["name", "description", "inputs", "output_type"]:
        if not hasattr(cls, attr):
            errors.append(f"Tool {cls.__name__} missing attribute: {attr}")
    if hasattr(cls, "forward"):
        sig = inspect.signature(cls.forward)
        if "self" not in sig.parameters:
            errors.append("forward() must have 'self' as first parameter.")
        for name in getattr(cls, "inputs", {}).keys():
            if name not in sig.parameters:
                errors.append(f"Input '{name}' missing in forward() signature.")
    source = inspect.getsource(cls)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            checker = MethodChecker(set(getattr(cls, "inputs", {}).keys()))
            checker.visit(node)
            errors += checker.errors
    if errors:
        raise ValueError("Tool validation failed:\n" + "\n".join(errors))